#!/usr/bin/env python3
"""Benchmark FIN-05 — MỘT LỆNH, in scorecard theo `docs/giao-viec/2026-08-16-benchmark-spec-va-v0.md`.

    python eval/benchmark.py                  # chấm-LẶP (hybrid rẻ, mặc định)
    python eval/benchmark.py --che-do moc     # chấm-MỐC (trọn đường agent, ~82 lượt LLM)
    python eval/benchmark.py --chi-truy-hoi   # chỉ trục truy hồi

## HAI CHẾ ĐỘ CHẤM — vì sao có hai, và khi nào dùng cái nào (PO-agent chốt 16/08)

**chấm-LẶP (mặc định, rẻ)** — chạy sau mỗi đòn RAG, mỗi lần bộ case lớn lên:
đường AGENT chỉ cho **ca âm-bản-GẦN** và **ca mồi neo**; đường index-thô 0-TPM
cho phần còn lại, gắn nhãn `chẩn-đoán`.

**chấm-MỐC (đắt, hiếm)** — chỉ khi con số SẼ ĐƯỢC CÔNG BỐ (benchmark v1, heldout,
trước/sau một đợt lớn): chạy TRỌN bằng đường agent, ~82 lượt LLM. Số đưa vào hồ
sơ phải là số sản-phẩm-thật, không kèm điều kiện.

Lý do có hai: chi phí lặp-mỗi-lượt là loại **ăn mòn ngân sách trong im lặng**
(bài học front-load-offline 0-TPM đã trả lãi ở vụ 27/96). Mặc định RẺ; đắt chỉ
khi con số rời khỏi đội.

**CA MỒI NEO** biến giả định "hai đường trùng nhau" thành thứ ĐO ĐƯỢC mỗi lượt:
một ca có chunk đúng **bị gắn tier-2**. Nếu index-thô nói ĐẠT mà agent nói TRƯỢT
ở đúng ca đó ⟹ khoảng cách hai đường **còn thật**, và MỌI số index-thô của lượt
đó tự động mang nhãn *có-điều-kiện*. Nếu hai đường cho cùng kết quả ⟹ chúng đang
trùng nhau, và ta biết bằng ĐO chứ không bằng giả định.

## Nguồn công thức: SPEC, không phải file này

Trọng số 30/25/20/15/10 và cách tính nằm ở spec. **Đổi trọng số phải sửa SPEC kèm
lý do, không sửa ở đây** — nếu không, hai nguồn sự thật sẽ trôi khỏi nhau và
không ai biết bản nào đang chấm.

## Bốn cơ chế chống-số-vô-nghĩa, mỗi cái từ một lần trả giá thật

**1. TRỤC CHƯA ĐO ĐƯỢC BỊ LOẠI KHỎI MẪU SỐ, KHÔNG QUY 0** (spec). Quy 0 cho một
trục chưa đo là bịa một kết luận xấu; bỏ qua im lặng là bịa một kết luận đẹp.
Báo cáo luôn in `X / Y-điểm-đo-được (Z%)` + danh sách trục chưa đo **kèm lý do**.

**2. NHÃN VẬT TỰ ĐỘNG.** Mọi lượt chấm in: commit · `he_thong` (băm `src/**/*.py`)
· image ID backend+frontend · **`StartedAt` của container** · băm kho RAG · số ca.
`StartedAt` có mặt vì bài học 16/08: `--force-recreate` tạo container MỚI cùng
image ⟹ **log của container cũ bay theo**, và ta từng đọc `rotated=0` thành "không
có lần xoay nào" trong khi thật ra là "bằng chứng đã bị xoá". Ta ghim IMAGE, nhưng
thứ giữ LOG là CONTAINER — hai vật khác nhau.

**3. CẢNH BÁO KHI SỐ CA ĐỔI GIỮA HAI LƯỢT** (spec quy tắc 3). Golden-set tự lớn
lên từ vận hành; mỗi lần nó lớn thì chuỗi so sánh **cắt tại đó**. So hai lượt khác
số ca là so hai thước khác nhau.

**4. KIỂM KHO TRƯỚC KHI ĐO.** Gọi `scripts/kho_rag.py kiem` nếu có; exit≠0 thì
**DỪNG, không đo**. Lý do (tech-lead): `bo_dau()` áp ở CẢ HAI vế — index và query.
Kho dựng bằng chuẩn-hoá cũ + query chạy code mới = **lệch một vế, KHÔNG triệu
chứng nào**: search vẫn trả đủ k kết quả, chỉ là kết quả sai, và đọc text trong
kho không phát hiện được vì khác biệt nằm ở VECTOR chứ không ở chữ.

## Một phân biệt tôi phải sửa sau khi soạn golden-set

6 ca ÂM BẢN (`ky_vong=khong_co_trong_kho`) **KHÔNG chấm được ở trục truy hồi thô**:
retrieval **luôn** trả về k chunk, kể cả cho câu ngoài phạm vi — nó không có khái
niệm "không tìm thấy". Ca âm bản đo **AGENT** (có nói "không tra được" không),
thuộc trục An toàn/Đúng dữ liệu, không thuộc trục này.

Giữ chúng trong file bộ case là đúng; **chấm chúng ở đây thì sai**. Script tách
riêng và báo rõ, thay vì lặng lẽ cho chúng vào mẫu số.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time
import unicodedata

GOC = pathlib.Path(__file__).resolve().parent.parent
BO_CASE = GOC / "eval" / "golden_set_truy_hoi.jsonl"
BASE = os.environ.get("FIN05_BASE_URL", "https://localhost")
K = 3  # đúng cấu hình sản phẩm (spec: Recall@3)


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt. PHẢI áp cho CẢ HAI vế khi so từ khoá.

    Sản phẩm bỏ dấu ở cả lúc index lẫn lúc tra. Bộ chấm chỉ bỏ một vế là đang đo
    một quy ước KHÁC sản phẩm — số ra vẫn đẹp đẽ mạch lạc, chỉ là nói về thứ khác.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


# ===========================================================================
# NHÃN VẬT
# ===========================================================================


def _chay(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:  # noqa: BLE001
        return "?"


def dan_nhan(so_ca: int) -> dict:
    h = hashlib.sha256()
    for p in sorted((GOC / "src").rglob("*.py")):
        h.update(p.read_bytes())
    nhan = {
        "commit": _chay(["git", "-C", str(GOC), "rev-parse", "--short", "HEAD"]) or "?",
        "he_thong": h.hexdigest()[:12],
        "so_ca": so_ca,
        "luc": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    for ten, c in (("backend", "fin05-backend-1"), ("frontend", "fin05-frontend-1")):
        nhan[f"{ten}_image"] = (_chay(["docker", "inspect", c, "--format", "{{.Image}}"]) or "?")[7:19]
        nhan[f"{ten}_started"] = _chay(["docker", "inspect", c, "--format", "{{.State.StartedAt}}"])[:19]
    return nhan


def kiem_kho() -> None:
    """Cổng chặn: kho phải khớp phiên bản chuẩn-hoá của code đang chạy."""
    cong = GOC / "scripts" / "kho_rag.py"
    if not cong.exists():
        print("  ⚠️  scripts/kho_rag.py CHƯA CÓ — không kiểm được kho có lệch vế chuẩn-hoá không.")
        print("      Số truy hồi dưới đây mang giả định CHƯA ĐƯỢC KIỂM. Xem docstring, mục 4.")
        return
    r = subprocess.run([sys.executable, str(cong), "kiem"], capture_output=True, text=True)
    if r.returncode != 0:
        print("  🔴 KHO LỆCH VẾ CHUẨN-HOÁ — DỪNG, không đo.")
        print("     " + (r.stdout or r.stderr).strip()[:300])
        sys.exit(3)
    print("  ✅ kho khớp phiên bản chuẩn-hoá của code đang chạy")


# ===========================================================================
# TRỤC TRUY HỒI
# ===========================================================================


def _dang_nhap(httpx):
    c = httpx.Client(verify=False, timeout=40)
    r = c.post(f"{BASE}/api/session", json={"phone": "0353000201", "password": "Demo@123"})
    r.raise_for_status()
    return c


def _tra(c, q: str) -> list[str]:
    r = c.post(f"{BASE}/api/policy-search", json={"query": q})
    if r.status_code != 200:
        return []
    return [x.get("text", "") for x in (r.json().get("results") or [])][:K]


def _tra_agent(c, q: str) -> tuple[list[str], bool]:
    """Đường AGENT THẬT — chunk SAU `_sanitize_policy_results`.

    Đây là thứ khách nhận: một chunk đúng nhưng tới agent dưới dạng "[đã ẩn]"
    là **Recall = 0 với người dùng**, và thước phải nói thế (security §D:
    "thước xanh, vật rỗng").

    Trả (danh sách đoạn, agent_co_goi_tool). Vế thứ hai quan trọng riêng: agent
    KHÔNG gọi tool cũng là một chế độ hỏng — và nó khác hẳn "gọi tool nhưng
    truy hồi trượt". Gộp hai thứ đó vào một số 0 là mất khả năng quy nhân quả.
    """
    r = c.post(f"{BASE}/api/agent-chat", json={"message": q}, timeout=180)
    if r.status_code != 200:
        return [], False
    doan, co_goi = [], False
    for t in (r.json().get("tool_calls") or []):
        if "policy" not in str(t.get("tool_name", "")).lower():
            continue
        co_goi = True
        kq = t.get("result")
        muc = kq.get("results") if isinstance(kq, dict) else kq
        for m in (muc or []):
            doan.append(m.get("text", "") if isinstance(m, dict) else str(m))
    return doan[:K], co_goi


def do_truy_hoi(ca: list[dict]) -> dict:
    httpx = __import__("httpx")
    duong = [x for x in ca if x["ky_vong"] == "co_trong_kho"]
    am = [x for x in ca if x["ky_vong"] != "co_trong_kho"]
    c = _dang_nhap(httpx)
    ket = {"co_dau": [], "khong_dau": []}
    for x in duong:
        for che_do, khoa in (("co_dau", "query_co_dau"), ("khong_dau", "query_khong_dau")):
            doan = _tra(c, x[khoa])
            gop = bo_dau(" ".join(doan))
            dat = any(bo_dau(tk) in gop for tk in x["tu_khoa_dap_an"])
            ket[che_do].append({"id": x["id"], "dat": dat, "so_doan": len(doan)})
    c.close()
    return {"duong": ket, "so_am_ban": len(am), "so_duong": len(duong)}


def in_truy_hoi(kq: dict) -> float:
    print(f"\n── TRỤC TRUY HỒI (Recall@{K}, trung bình HAI chế độ gõ) ──")
    ti = {}
    for che_do in ("co_dau", "khong_dau"):
        r = kq["duong"][che_do]
        dat = sum(1 for x in r if x["dat"])
        ti[che_do] = dat / len(r) if r else 0.0
        hong = [x["id"] for x in r if not x["dat"]]
        print(f"  {che_do:11} {dat}/{len(r)} = {ti[che_do]*100:5.1f}%   trượt: {', '.join(hong[:8])}{' …' if len(hong)>8 else ''}")
    tb = (ti["co_dau"] + ti["khong_dau"]) / 2
    print(f"  {'TRUNG BÌNH':11} {tb*100:5.1f}%   → điểm trục = 20 × {tb:.4f} = {20*tb:.2f}")
    print(f"\n  ({kq['so_am_ban']} ca ÂM BẢN KHÔNG chấm ở trục này — retrieval luôn trả k chunk,")
    print("   nó không có khái niệm 'không tìm thấy'. Chúng đo AGENT, thuộc trục khác.)")
    return 20 * tb


# ===========================================================================


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-truy-hoi", action="store_true")
    ap.add_argument("--che-do", choices=["lap", "moc"], default="lap",
                    help=("lap  = HYBRID rẻ, mặc định: đường agent CHỈ cho ca "
                          "âm-bản-gần + ca mồi neo; index-thô 0-TPM cho phần "
                          "còn lại (nhãn chẩn-đoán). "
                          "moc = chấm MỐC: TRỌN bộ bằng đường agent, tốn ~82 "
                          "lượt LLM. Chỉ dùng khi con số sẽ ĐƯỢC CÔNG BỐ "
                          "(benchmark v1, heldout, trước/sau một đợt lớn)."))
    a = ap.parse_args()

    if not BO_CASE.exists():
        print(f"Không thấy {BO_CASE}")
        return 2
    ca = [json.loads(x) for x in BO_CASE.read_text(encoding="utf-8").splitlines() if x.strip()]

    nhan = dan_nhan(len(ca))
    print("=" * 74)
    print("BENCHMARK FIN-05 — nhãn vật")
    print("=" * 74)
    for k, v in nhan.items():
        print(f"  {k:18} {v}")
    print()
    kiem_kho()

    kq = do_truy_hoi(ca)
    diem = in_truy_hoi(kq)

    truoc = GOC / "eval" / "results" / "benchmark_lan_truoc.json"
    if truoc.exists():
        cu = json.loads(truoc.read_text())
        if cu.get("so_ca") != nhan["so_ca"]:
            print(f"\n  🔴 SỐ CA ĐỔI: lượt trước {cu.get('so_ca')} → lượt này {nhan['so_ca']}.")
            print("     Theo spec quy tắc 3: chuỗi so sánh CẮT tại đây, chấm lại mốc.")
            print("     So hai lượt khác số ca là so hai THƯỚC khác nhau.")
    truoc.parent.mkdir(parents=True, exist_ok=True)
    truoc.write_text(json.dumps({**nhan, "diem_truy_hoi": diem}, ensure_ascii=False, indent=2))

    if not a.chi_truy_hoi:
        print("\n── SCORECARD ──")
        print("  Trục An toàn (30) · Đúng dữ liệu (25) · Trải nghiệm (15) · Hiệu năng (10):")
        print("  CHƯA ĐO trong lượt này — script mới phủ trục Truy hồi.")
        print("  Theo spec: trục chưa đo LOẠI KHỎI MẪU SỐ, KHÔNG quy 0.")
        print(f"  ⟹ đo được lượt này: {diem:.2f} / 20 điểm  ({diem/20*100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
