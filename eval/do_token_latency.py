#!/usr/bin/env python3
"""Đo TOKEN + LATENCY của đường agent thật, bằng một BỘ LỆNH CỐ ĐỊNH.

    python eval/do_token_latency.py             # 1 lượt mỗi câu
    python eval/do_token_latency.py --lap 3     # 3 lượt, in trung vị + dải
    python eval/do_token_latency.py --nhom ngan # chỉ nhóm câu ngắn

## Vì sao phải là bộ lệnh CỐ ĐỊNH, phiên bản hoá

T3 đo được `input/lượt 19,4k → 14,7k` **trên câu do người đo tự nghĩ ra**. Con
số đó không sai, nhưng nó **không so được với bất cứ lượt đo nào khác** — lần
sau đổi câu là đổi thước, và mọi so sánh trước/sau biến thành so hai thứ khác
nhau. Đó là lý do coder KHÔNG tuyên bố đạt mục tiêu `<30k` dù đã giảm 24%.

Bộ lệnh nằm ở `eval/bo_lenh_do.jsonl`, có `phien_ban`. **Đổi một dòng phải
tăng phiên bản**, và script từ chối so hai lượt khác phiên bản.

## Dải phải phủ, không được chỉ đo câu dễ

    ngan  1-2 bước ReAct                     — sàn của dải
    dai   điều tra nhiều bước                — dạng lượt phình 47-84k hồi T1
    ve    tạo ticket                         — nhánh có hậu quả, qua OTP step-up

Đo mỗi câu ngắn rồi lấy trung bình sẽ cho một con số **đẹp và vô dụng**: cái
đang đe doạ trần TPM là lượt DÀI, và nó bị pha loãng mất.

## Nguồn số: `usage` trong phản hồi, KHÔNG bới log

`/api/agent-chat` trả thẳng `{input_tokens, output_tokens, total_tokens,
cached_input_tokens}`. Bới log để đếm lượt gọi LLM là đo gián tiếp một thứ đã
có sẵn ở dạng trực tiếp — và log thì bay theo container (bài học 16/08).

## HAI CHẾ ĐỘ — và vì sao gộp chúng lại là sai

    --che-do rieng   mỗi câu một PHIÊN MỚI  → chi phí của CÂU
    --che-do don     cả bộ trong MỘT phiên  → chi phí của LƯỢT THỨ N

Bản đầu của script này chỉ có một chế độ: chạy cả bộ trong một phiên. Kết quả
tăng đơn điệu `N1 13,8k → V1 34,4k`, và tôi suýt báo cáo *"V1 là lượt nặng
nhất, 34,4k"*.

**Sai.** Chạy ĐẢO thứ tự thì con số vẫn tăng đơn điệu — theo **vị trí**, không
theo câu:

    xuôi:  N1 13,8k  N2 16,9k  N3 20,3k  D1 24,1k  D2 28,3k  D3 32,2k  V1 34,4k
    ngược: V1  6,2k  D3 14,5k  D2  8,3k  D1 18,7k  N3 21,5k  N2 23,7k  N1 26,7k
    riêng: mỗi câu một phiên → TẤT CẢ nằm trong 6,2k–15,7k

⟹ Thứ tôi tưởng là "câu nặng" thật ra là **lịch sử hội thoại cộng dồn**. Con số
34,4k không thuộc về V1; nó thuộc về **lượt thứ 7**.

Cả hai đều cần, và phải đọc khác nhau:
- `rieng` trả lời *"câu này tốn bao nhiêu"* — dùng để so trước/sau một đòn tối ưu.
- `don` trả lời *"hội thoại phình tới đâu"* — đây mới là thứ chạm trần TPM, và
  là dạng lượt 47–84k hồi T1.

Một con số `<30k` không có nghĩa gì nếu không nói nó thuộc chế độ nào.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import subprocess
import sys
import time
import warnings

warnings.filterwarnings("ignore")

GOC = pathlib.Path(__file__).resolve().parent.parent
BO_LENH = GOC / "eval" / "bo_lenh_do.jsonl"
BASE = os.environ.get("FIN05_BASE_URL", "https://localhost")
SO_KHACH = os.environ.get("FIN05_TEST_CUSTOMER_PHONE", "0974000145")
MAT_KHAU = os.environ.get("FIN05_TEST_PASSWORD", "Demo@123")


# ===========================================================================
# CỔNG ĐÓNG BĂNG LLM — dùng chung hạn mức TPM với 3 phiên khác + PO thật
# ===========================================================================


def cong_dong_bang(ly_do_can_llm: str) -> None:
    """Từ chối chạy khi đang đóng băng LLM. Đặt `FIN05_DONG_BANG_LLM=1` để bật.

    VÌ SAO LÀ CƠ CHẾ CHỨ KHÔNG PHẢI LỜI HỨA: đo được 16/08 — **một người, 21
    lượt, 2 phút** đẩy org tới `193.274/200.000 TPM`. Trần đó dùng chung giữa
    4 phiên Claude và PO thật. Nếu tôi chạy bộ đo trong lúc PO thật quay video
    demo, họ ăn 429 **giữa video** — và 429 hiện ra tới khách dưới dạng HTTP
    500 màn hình trắng (finding chưa vá lúc viết dòng này).

    Một lời hứa "tôi sẽ không chạy" không sống sót qua một phiên bị nén ngữ
    cảnh hay một người khác chạy lại lệnh trong lịch sử shell. Cổng thì có.
    """
    if os.environ.get("FIN05_DONG_BANG_LLM", "").strip() not in ("", "0", "false"):
        sys.exit(
            "🧊 ĐANG ĐÓNG BĂNG LLM — không chạy.\n"
            f"   Lệnh này cần model để: {ly_do_can_llm}\n"
            "   Trần TPM dùng chung với 3 phiên khác + PO thật; đo được một người\n"
            "   21 lượt/2 phút đã đẩy org tới 193k/200k, và 429 ra tới khách\n"
            "   thành HTTP 500.\n"
            "   Bỏ đóng băng: unset FIN05_DONG_BANG_LLM"
        )


def _chay(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:  # noqa: BLE001
        return "?"


def in_nhan(phien_ban: str) -> None:
    import hashlib

    h = hashlib.sha256()
    for p in sorted((GOC / "src").rglob("*.py")):
        h.update(p.read_bytes())
    print("=" * 74)
    print("ĐO TOKEN + LATENCY — nhãn vật")
    print("=" * 74)
    print(f"  bo_lenh            {phien_ban}   ← đổi phiên bản = đổi thước, KHÔNG so được")
    print(f"  commit             {_chay(['git', '-C', str(GOC), 'rev-parse', '--short', 'HEAD'])}")
    print(f"  he_thong           {h.hexdigest()[:12]}")
    print(f"  luc                {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    for ten, c in (("backend", "fin05-backend-1"), ("frontend", "fin05-frontend-1")):
        print(f"  {ten}_image{' ' * (11 - len(ten))}"
              f"{(_chay(['docker', 'inspect', c, '--format', '{{.Image}}']) or '?')[7:19]}")
        print(f"  {ten}_started{' ' * (9 - len(ten))}"
              f"{_chay(['docker', 'inspect', c, '--format', '{{.State.StartedAt}}'])[:19]}")
    kho = _chay(["docker", "exec", "fin05-backend-1", "sh", "-c",
                 "cd /app && python scripts/kho_rag.py nhan"]).splitlines()
    print(f"  kho                {kho[0].strip() if kho else '?'}")


def dang_nhap(httpx):
    c = httpx.Client(verify=False, timeout=600)
    r = c.post(f"{BASE}/api/session", json={"phone": SO_KHACH, "password": MAT_KHAU})
    r.raise_for_status()
    vai = r.json().get("role")
    if vai != "customer":
        sys.exit(f"🔴 tài khoản {SO_KHACH} có vai {vai!r}, cần 'customer' — /api/agent-chat sẽ trả 403")
    return c


def mo_otp(c) -> bool:
    """OTP PHIÊN LÀM VIỆC (ràng buộc cứng 4 — KHÔNG phải OTP giao dịch)."""
    r = c.post(f"{BASE}/api/otp/request", json={})
    if r.status_code != 200:
        print(f"  ⚠️  otp/request {r.status_code}: {r.text[:120]}")
        return False
    j = r.json()
    ma = j.get("otp_code")
    if not ma:
        print("  ⚠️  môi trường này KHÔNG trả mã OTP — nhóm 'dai'/'ve' sẽ không đo được")
        return False
    v = c.post(f"{BASE}/api/otp/verify",
               json={"session_id": j.get("session_id"), "otp_code": ma})
    if v.status_code != 200:
        print(f"  ⚠️  otp/verify {v.status_code}: {v.text[:160]}")
        return False
    print(f"  ✅ OTP phiên đã xác thực ({j.get('session_id')})")
    return True


def mot_luot(c, cau: str) -> dict:
    t0 = time.perf_counter()
    r = c.post(f"{BASE}/api/agent-chat", json={"message": cau})
    giay = time.perf_counter() - t0
    if r.status_code != 200:
        return {"loi": f"HTTP {r.status_code}: {r.text[:120]}", "giay": giay}
    j = r.json()
    u = j.get("usage") or {}
    return {
        "giay": giay,
        "vao": u.get("input_tokens"),
        "ra": u.get("output_tokens"),
        "cache": u.get("cached_input_tokens"),
        "tool": len(j.get("tool_calls") or []),
        "ve": bool(j.get("ticket_id")),
        "dai_dap": len(str(j.get("reply") or "")),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lap", type=int, default=1)
    ap.add_argument("--nhom", choices=["ngan", "dai", "ve"], default=None)
    ap.add_argument("--che-do", choices=["rieng", "don"], default="rieng",
                    help="rieng = mỗi câu một phiên mới (chi phí của CÂU); "
                         "don = cả bộ trong một phiên (chi phí của LƯỢT THỨ N)")
    a = ap.parse_args()
    cong_dong_bang("gọi /api/agent-chat cho từng câu trong bộ lệnh")

    dong = [json.loads(l) for l in BO_LENH.read_text(encoding="utf-8").splitlines() if l.strip()]
    phien_ban = dong[0]["phien_ban"]
    lenh = [d for d in dong[1:] if not a.nhom or d["nhom"] == a.nhom]

    import httpx

    in_nhan(phien_ban)
    print(f"  chế độ            {a.che_do}"
          + ("   (mỗi câu MỘT PHIÊN MỚI — chi phí của CÂU)" if a.che_do == "rieng"
             else "   (cả bộ MỘT PHIÊN — chi phí của LƯỢT THỨ N, số tăng theo vị trí)"))

    def moi_phien():
        cc = dang_nhap(httpx)
        return cc, (mo_otp(cc) if any(d["can_otp"] for d in lenh) else True)

    c, co_otp = moi_phien()

    # LẶP: ở chế độ `don`, lặp phải bọc NGOÀI cả dãy — lặp mỗi câu 3 lần trong
    # cùng phiên sẽ biến bộ 7 câu thành hội thoại 21 lượt, tức đo một thứ khác
    # hẳn. Ở `rieng` thì lặp trong hay ngoài đều như nhau vì mỗi lượt một phiên.
    thu = {d["id"]: [] for d in lenh}
    for _ in range(a.lap):
        if a.che_do == "don":
            c.close()
            c, co_otp = moi_phien()
        for d in lenh:
            if a.che_do == "rieng":
                c.close()
                c, co_otp = moi_phien()
            if d["can_otp"] and not co_otp:
                thu[d["id"]].append({"loi": "chưa mở được OTP phiên"})
                continue
            thu[d["id"]].append(mot_luot(c, d["cau"]))

    print(f"\n{'id':<4}{'nhóm':<6}{'giây':>7}{'vào':>9}{'ra':>7}{'cache':>8}{'tool':>6}  vé")
    print("-" * 74)
    ket = []
    for d in lenh:
        luot = thu[d["id"]]
        loi = [x["loi"] for x in luot if "loi" in x]
        if loi:
            print(f"{d['id']:<4}{d['nhom']:<6}   KHÔNG ĐO ĐƯỢC: {loi[0]}")
            ket.append({**d, "khong_do_duoc": loi[0]})
            continue
        g = lambda k: [x[k] for x in luot if x.get(k) is not None]  # noqa: E731
        tv = lambda k: statistics.median(g(k)) if g(k) else None    # noqa: E731
        print(f"{d['id']:<4}{d['nhom']:<6}{tv('giay'):>7.1f}{tv('vao'):>9,.0f}"
              f"{tv('ra'):>7,.0f}{tv('cache'):>8,.0f}{tv('tool'):>6.0f}"
              f"  {'✓' if any(x['ve'] for x in luot) else ''}")
        if a.lap > 1:
            print(f"      dải vào {min(g('vao')):,.0f}–{max(g('vao')):,.0f}"
                  f"  ·  dải giây {min(g('giay')):.1f}–{max(g('giay')):.1f}"
                  f"  ·  tool {min(g('tool'))}–{max(g('tool'))}")
        ket.append({**d, "luot": luot, "tv_vao": tv("vao"), "tv_giay": tv("giay")})
    c.close()

    do_duoc = [k for k in ket if "khong_do_duoc" not in k]
    if do_duoc:
        print("-" * 74)
        for nhom in ("ngan", "dai", "ve"):
            n = [k for k in do_duoc if k["nhom"] == nhom]
            if n:
                print(f"  {nhom:<5} input/lượt trung vị {statistics.median([k['tv_vao'] for k in n]):>8,.0f}"
                      f"  ·  cao nhất {max(k['tv_vao'] for k in n):>8,.0f}"
                      f"  ·  latency trung vị {statistics.median([k['tv_giay'] for k in n]):>5.1f}s")
        cao = max(do_duoc, key=lambda k: k["tv_vao"])
        if a.che_do == "don":
            print(f"\n  TRẦN ĐẠT TỚI: {cao['tv_vao']:,.0f} input token ở lượt thứ "
                  f"{[k['id'] for k in do_duoc].index(cao['id']) + 1}/{len(do_duoc)}."
                  "\n  Con số này thuộc VỊ TRÍ lượt, KHÔNG thuộc câu — chạy đảo thứ tự thì"
                  " nó đi theo vị trí. Đây là số chạm trần TPM.")
        else:
            print(f"\n  CÂU NẶNG NHẤT: {cao['id']} — {cao['tv_vao']:,.0f} input token"
                  " (phiên sạch, không lịch sử)."
                  "\n  Dùng số này để so TRƯỚC/SAU một đòn tối ưu; đừng dùng nó đoán trần TPM.")
    chua = [k["id"] for k in ket if "khong_do_duoc" in k]
    if chua:
        print(f"\n  ⚠️  KHÔNG ĐO ĐƯỢC: {chua} — số trên KHÔNG phủ nhóm này, đừng đọc thành toàn bộ dải.")
    ra = GOC / "eval" / "do_token_latency.json"
    ra.write_text(json.dumps({"phien_ban": phien_ban, "ket": ket}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    print(f"\n→ {ra.relative_to(GOC)}")


if __name__ == "__main__":
    main()
