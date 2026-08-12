#!/usr/bin/env python3
"""FIN05-StressTest-Plan-v4 6.3 — load test cho `/ws/live-chat` (WebSocket 2
chiều thời gian thực, `src/api/live_chat_ws.py`). `tests/load/locustfile.py`
(D1-D3/D6, dùng Locust) CHỈ tải được các route REST (`/api/*` qua BFF) —
Locust không hỗ trợ giao thức WebSocket thật (chỉ hỗ trợ HTTP/HTTP2 native,
mở rộng WS cần plugin bên thứ ba không có sẵn trong dự án). Script RIÊNG
này dùng thư viện `websockets` (đã có sẵn qua uvicorn[standard], transitive
— tương tự `locust` cũng KHÔNG khai báo tường minh trong requirements.txt,
xem quy ước đã có) để tải trực tiếp tầng WS.

QUAN TRỌNG — khác `tests/load/locustfile.py`: script này gọi THẲNG FastAPI
(`BACKEND_URL`, mặc định :8010), KHÔNG qua Next.js/Caddy — vì `/ws/live-chat`
chỉ được Caddy proxy đúng khi chạy `docker compose up` thật (xem
`frontend/playwright.livechat.config.ts`), còn mục tiêu ở đây là đo tải tầng
WS/ConnectionManager (`src/api/live_chat_ws.py`) độc lập, không lẫn độ trễ
proxy. Muốn đo qua Caddy thật, đổi `--backend-url` thành `wss://localhost`
(cần `--insecure` vì chứng chỉ tự ký, xem code bên dưới).

Trước khi chạy tải thật, PHẢI có sẵn N ticket THẬT do N khách hàng KHÁC NHAU
sở hữu (`open_chat_session` — src/services/live_chat.py dòng 34 — từ chối
thẳng nếu ticket không thuộc về customer_id đang mở chat, đúng thiết kế,
không phải hạn chế của script). Dùng `--seed N` để tự tạo N ticket thật qua
ĐÚNG service thật (`create_ticket_with_fraud_check`, không qua AI/OTP — cùng
cách tiếp cận `scripts/seed_demo_scenarios.py` đã dùng, KHÔNG tự chế fixture
riêng) trước khi chạy tải.

Dùng:
    # Bước 1 — tạo N ticket thật (ghi vào data/app.db đang chạy), IN RA
    # danh sách (phone, ticket_id) — lưu lại để tái dùng cho lần chạy sau
    # (không cần seed lại mỗi lần đo tải).
    python scripts/load/ws_live_chat_load.py --seed 20 --out /tmp/ws_tickets.json

    # Bước 2 — chạy tải THẬT (CHỈ chạy thủ công/nightly, không tự động
    # trong CI — cùng nguyên tắc D3 soak test của locustfile.py):
    python scripts/load/ws_live_chat_load.py --tickets /tmp/ws_tickets.json \\
        --messages-per-client 20 --rate 1.0

    # Debug nhanh (không phải load test thật):
    python scripts/load/ws_live_chat_load.py --seed 3 --messages-per-client 3 --rate 2
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

BACKEND_URL_DEFAULT = "http://localhost:8010"


# ---------------------------------------------------------------------------
# Bước seed — tạo N ticket thật, KHÔNG qua AI/OTP (tốn kém/không xác định
# nếu load test tự phụ thuộc vào OpenAI thật chỉ để có dữ liệu setup).
# ---------------------------------------------------------------------------


def seed_tickets(n: int) -> list[dict]:
    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from src.db.models import Ticket, Transaction, User, Wallet
    from src.db.session import get_engine
    from src.services.complaint_intake import create_ticket_with_fraud_check
    from src.services.live_chat import open_chat_session

    engine = get_engine()
    session = sessionmaker(bind=engine, future=True)()

    customers = session.scalars(select(User).where(User.role == "customer")).all()
    if len(customers) < n:
        raise SystemExit(f"Chỉ có {len(customers)} customer trong DB, không đủ {n} — giảm --seed hoặc seed thêm data.")

    out = []
    for user in customers[:n]:
        wallet = session.scalars(select(Wallet).where(Wallet.user_id == user.user_id)).first()
        trans_id = None
        if wallet:
            txn = session.scalars(
                select(Transaction)
                .where((Transaction.send_wal_id == wallet.wallet_id) | (Transaction.rec_wal_id == wallet.wallet_id))
                .limit(1)
            ).first()
            trans_id = txn.trans_id if txn else None

        result = create_ticket_with_fraud_check(
            session,
            user_id=user.user_id,
            complaint_type="money_not_received",
            scope="internal_wallet",
            description_raw="(seed cho ws_live_chat_load.py) khách yêu cầu hỗ trợ trực tiếp",
            trans_id=trans_id,
        )
        ticket_id = result["ticket_id"]
        # Human handoff request thật — set human_handoff_requested=True để
        # giống hệt trạng thái 1 ticket đã có customer bấm "gặp người thật"
        # trước khi mở ws-ticket (đúng luồng thật, không tự chế state giả).
        ticket = session.get(Ticket, ticket_id)
        ticket.human_handoff_requested = True
        session.commit()

        # open_chat_session cần chạy 1 lần TRƯỚC khi client thật gọi REST
        # /live-chat/ws-ticket không bắt buộc — route đó tự gọi lại
        # open_chat_session() (idempotent, tái dùng session waiting/active
        # đã có, xem docstring hàm) — seed ở đây chỉ để CHẮC CHẮN ticket sẵn
        # sàng, không phụ thuộc thứ tự gọi.
        open_chat_session(session, ticket_id=ticket_id, customer_id=user.user_id)
        session.commit()

        out.append({"phone": user.phone, "ticket_id": ticket_id, "user_id": user.user_id})

    session.close()
    return out


# ---------------------------------------------------------------------------
# Bước tải — mỗi "client" ảo: login thật (JWT thật) -> ws-ticket thật (vé
# dùng 1 lần) -> connect WS thật -> gửi N tin nhắn theo nhịp --rate. KHÔNG đo
# latency round-trip per-message ở đây: ConnectionManager không echo tin
# nhắn lại về CHÍNH người gửi (chỉ gửi tới phía CÒN LẠI của phiên — CSKH/
# supervisor), nên phía customer-only này (script không mô phỏng staff join)
# không có cách nào khớp 1 frame nhận về với đúng 1 message đã gửi để đo độ
# trễ có ý nghĩa. Số liệu thu được: có kết nối/gửi thành công hay không, tỷ
# lệ lỗi — đủ để trả lời câu hỏi tải chính (ConnectionManager có sập/rớt kết
# nối hàng loạt dưới N client đồng thời hay không), đúng phạm vi 6.3.
# ---------------------------------------------------------------------------


@dataclass
class ClientStats:
    connected: bool = False
    sent: int = 0
    received: int = 0
    errors: list[str] = field(default_factory=list)


async def _run_one_client(
    *, backend_url: str, insecure: bool, phone: str, ticket_id: str, n_messages: int, rate: float
) -> ClientStats:
    import httpx
    import websockets

    stats = ClientStats()
    http_scheme = "https" if backend_url.startswith("https") or backend_url.startswith("wss") else "http"
    base = backend_url.replace("wss://", f"{http_scheme}://").replace("ws://", f"{http_scheme}://")

    try:
        async with httpx.AsyncClient(base_url=base, verify=not insecure, timeout=15.0) as http:
            login_resp = await http.post("/auth/login", json={"phone": phone, "role": "customer"})
            login_resp.raise_for_status()
            token = login_resp.json()["access_token"]

            ticket_resp = await http.post(
                "/live-chat/ws-ticket",
                json={"ticket_id": ticket_id},
                headers={"Authorization": f"Bearer {token}"},
            )
            ticket_resp.raise_for_status()
            ws_ticket = ticket_resp.json()["ws_ticket"]
            chat_session_id = ticket_resp.json()["chat_session_id"]
    except Exception as e:  # setup lỗi (login/ws-ticket) — tính là 1 client fail, không chặn các client khác
        stats.errors.append(f"setup: {e!r}")
        return stats

    ws_scheme = "wss" if http_scheme == "https" else "ws"
    ws_url = f"{ws_scheme}://{base.split('://', 1)[1]}/ws/live-chat?ticket={ws_ticket}"

    try:
        async with websockets.connect(ws_url, open_timeout=15) as ws:
            stats.connected = True
            interval = 1.0 / rate if rate > 0 else 0.0

            async def _receiver():
                try:
                    async for _raw in ws:
                        stats.received += 1
                except Exception:
                    pass

            recv_task = asyncio.create_task(_receiver())
            for i in range(n_messages):
                sent_at = time.monotonic()
                try:
                    await ws.send(
                        json.dumps(
                            {
                                "type": "send_message",
                                "chat_session_id": chat_session_id,
                                "content": f"[load-test] tin nhắn số {i + 1}/{n_messages} lúc {sent_at:.3f}",
                            }
                        )
                    )
                    stats.sent += 1
                except Exception as e:
                    stats.errors.append(f"send#{i}: {e!r}")
                    break
                if interval:
                    await asyncio.sleep(interval)
            # Cho server 1 khoảng nghỉ để phát hết message còn treo trước khi đóng
            await asyncio.sleep(min(3.0, interval * 3 + 1))
            recv_task.cancel()
    except Exception as e:
        stats.errors.append(f"ws: {e!r}")

    return stats


async def run_load(
    tickets: list[dict], *, backend_url: str, insecure: bool, n_messages: int, rate: float
) -> list[ClientStats]:
    tasks = [
        _run_one_client(
            backend_url=backend_url,
            insecure=insecure,
            phone=t["phone"],
            ticket_id=t["ticket_id"],
            n_messages=n_messages,
            rate=rate,
        )
        for t in tickets
    ]
    return await asyncio.gather(*tasks)


def print_report(results: list[ClientStats]) -> None:
    n = len(results)
    n_connected = sum(1 for r in results if r.connected)
    total_sent = sum(r.sent for r in results)
    total_received = sum(r.received for r in results)
    n_with_errors = sum(1 for r in results if r.errors)

    print(f"\n=== Kết quả load test /ws/live-chat ({n} client ảo) ===", file=sys.stderr)
    print(f"Kết nối thành công: {n_connected}/{n}", file=sys.stderr)
    print(f"Tổng tin nhắn gửi: {total_sent}, tổng frame nhận về: {total_received}", file=sys.stderr)
    print(f"Client gặp lỗi: {n_with_errors}/{n}", file=sys.stderr)
    if n_with_errors:
        print("Chi tiết lỗi (tối đa 10 dòng đầu):", file=sys.stderr)
        shown = 0
        for r in results:
            for e in r.errors:
                if shown >= 10:
                    break
                print(f"  - {e}", file=sys.stderr)
                shown += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=0, help="Tạo N ticket thật rồi thoát (không chạy tải)")
    parser.add_argument("--out", type=str, default=None, help="Ghi danh sách ticket vừa seed ra file JSON")
    parser.add_argument("--tickets", type=str, default=None, help="File JSON (phone, ticket_id) để chạy tải")
    parser.add_argument("--backend-url", type=str, default=BACKEND_URL_DEFAULT)
    parser.add_argument("--insecure", action="store_true", help="Bỏ verify TLS (dùng khi target Caddy chứng chỉ tự ký)")
    parser.add_argument("--messages-per-client", type=int, default=10)
    parser.add_argument("--rate", type=float, default=1.0, help="Số tin nhắn/giây mỗi client (mặc định 1/s)")
    args = parser.parse_args()

    if args.seed:
        tickets = seed_tickets(args.seed)
        print(f"Đã seed {len(tickets)} ticket thật.", file=sys.stderr)
        if args.out:
            Path(args.out).write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Đã ghi {args.out}", file=sys.stderr)
        else:
            print(json.dumps(tickets, ensure_ascii=False, indent=2))
        return 0

    if not args.tickets:
        parser.error("cần --seed N (để tạo ticket) hoặc --tickets FILE (để chạy tải với ticket đã có)")

    tickets = json.loads(Path(args.tickets).read_text(encoding="utf-8"))
    results = asyncio.run(
        run_load(
            tickets,
            backend_url=args.backend_url,
            insecure=args.insecure,
            n_messages=args.messages_per_client,
            rate=args.rate,
        )
    )
    print_report(results)
    n_connected = sum(1 for r in results if r.connected)
    return 0 if n_connected == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
