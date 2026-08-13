"""R4 — fan-out liên worker, tầng WebSocket, NHIỀU PHIÊN.

Lý do cần bổ sung cho test Playwright: mỗi phiên chat là MỘT cặp kết nối
(khách, CSKH) nằm trên một cặp worker cố định. Nhắn 100 tin trong 1 phiên
vẫn chỉ kiểm đúng 1 cặp worker đó. Script này mở N phiên độc lập → lấy mẫu
nhiều cặp worker khác nhau, mỗi phiên nhắn >=5 tin MỖI CHIỀU xen kẽ.

Tin nào không tới trong TIMEOUT giây = mất tin = BLOCKER demo.
"""
import asyncio
import json
import ssl
import sys

import httpx
import websockets

BASE = "https://localhost"
WS = "wss://localhost/ws/live-chat"
TICKET_ID = "TCK-00002"
PW = "Demo@123"
CUST = "0974000145"
CSKH = "0353000201"
ROUNDS = 5
TIMEOUT = 10
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


async def mint(cli, path, body, label):
    for _ in range(30):
        r = cli.post(f"{BASE}{path}", json=body)
        if r.status_code == 200 and "ws_ticket" in r.json():
            return r.json()
        await asyncio.sleep(15 if r.status_code == 429 else 2)
    raise RuntimeError(f"{label}: không cấp được vé")


async def wait_for(ws, needle, timeout, log):
    loop = asyncio.get_event_loop()
    end = loop.time() + timeout
    hits = 0
    try:
        while loop.time() < end:
            f = json.loads(await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - loop.time())))
            log.append(f)
            if needle in str(f.get("content", "")):
                hits += 1
                # đọc thêm 1.5s để bắt bản lặp (vọng Redis) nếu có
                end = min(end, loop.time() + 1.5)
    except (TimeoutError, websockets.ConnectionClosed):
        pass
    return hits


async def session(n, cust, staff):
    jc = await mint(cust, "/api/live-chat/ws-ticket", {"ticket_id": TICKET_ID}, "khach")
    js = await mint(staff, "/api/live-chat/staff-ws-ticket", {}, "cskh")
    chs = jc["chat_session_id"]
    async with websockets.connect(f"{WS}?ticket={jc['ws_ticket']}", ssl=ctx) as cws, \
               websockets.connect(f"{WS}?ticket={js['ws_ticket']}", ssl=ctx) as sws:
        clog, slog = [], []
        staff.post(f"{BASE}/api/live-chat/sessions/{chs}/claim")
        await wait_for(sws, "__none__", 2, slog)  # xả frame claim/backlog

        missing, dup = [], []
        for i in range(1, ROUNDS + 1):
            m = f"s{n}-cskh-{i}"
            await sws.send(json.dumps({"type": "send_message", "chat_session_id": chs, "content": m}))
            h = await wait_for(cws, m, TIMEOUT, clog)
            if h == 0:
                missing.append(m)
            elif h > 1:
                dup.append(f"{m}×{h}")

            m = f"s{n}-khach-{i}"
            await cws.send(json.dumps({"type": "send_message", "chat_session_id": chs, "content": m}))
            h = await wait_for(sws, m, TIMEOUT, slog)
            if h == 0:
                missing.append(m)
            elif h > 1:
                dup.append(f"{m}×{h}")

        staff.post(f"{BASE}/api/live-chat/sessions/{chs}/close")
    return {"phien": n, "chat_session_id": chs, "mat_tin": missing, "lap_tin": dup}


async def main(n_sessions):
    with httpx.Client(verify=False, timeout=60) as cust, httpx.Client(verify=False, timeout=60) as staff:
        cust.post(f"{BASE}/api/session", json={"phone": CUST, "password": PW}).raise_for_status()
        staff.post(f"{BASE}/api/session", json={"phone": CSKH, "password": PW}).raise_for_status()
        results = []
        for n in range(1, n_sessions + 1):
            try:
                r = await session(n, cust, staff)
            except Exception as e:
                r = {"phien": n, "loi": repr(e)[:160]}
            results.append(r)
            print(json.dumps(r, ensure_ascii=False), flush=True)
            await asyncio.sleep(3)
    tong = sum(len(r.get("mat_tin", [])) for r in results)
    lap = sum(len(r.get("lap_tin", [])) for r in results)
    loi = [r for r in results if r.get("loi")]
    print(f"\nTỔNG: {n_sessions} phiên × {ROUNDS} tin/chiều = {n_sessions*ROUNDS*2} tin · "
          f"MẤT {tong} · LẶP {lap} · phiên lỗi {len(loi)}")

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 6))
