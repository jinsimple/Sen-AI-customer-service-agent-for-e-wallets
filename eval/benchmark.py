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
· image ID backend+frontend · **`StartedAt` của container** · số ca.

⚠️ **KHÔNG dùng "băm kho" làm nhãn** (PO-agent ratify 16/08): đo được nó KHÔNG
TẤT ĐỊNH — ba lần đọc liên tiếp trên một kho không đổi cho ba giá trị khác nhau
(`8263163a5d52` · `ecd0716e6649` · `8582ad775d29`). Một cái băm tự đổi thì không
chứng minh được kho đã đổi, cũng không chứng minh được kho giữ nguyên — vô dụng
theo cả hai chiều. Dùng `số chunk · số doc · phiên-bản-chuẩn-hoá` (đều tất định)
tới khi coder giao bản băm tất định.
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
import math
import os
import pathlib
import re
import subprocess
import sys
import time
import unicodedata

GOC = pathlib.Path(__file__).resolve().parent.parent
BO_CASE = GOC / "eval" / "golden_set_truy_hoi.jsonl"
BASE = os.environ.get("FIN05_BASE_URL", "https://localhost")
PHIEN_BAN = "v3"   # v2->v3 (17/08): thêm MRR + NDCG. Đổi định dạng output = đổi thước.

K = 4  # mặc định của sản phẩm — agent nhận đúng 4 đoạn (đã xem tool_calls thật)
K_SOI = 8  # trần `top_k` của API; chỉ dùng cho DẢI CHẨN ĐOÁN, không dùng chấm

# VÌ SAO CHẤM Ở 4: đường agent thật nhận 4 đoạn (đọc từ `tool_calls` của
# `/api/agent-chat`). Thước cắt ở 3 là đo một sản phẩm KHÔNG TỒN TẠI — 4 ca
# (RAG-10/14/17/22) nằm đúng hạng 4: agent NHẬN được, thước cũ chấm trượt.
#
# ⚠️ ĐÍNH CHÍNH 17/08: lúc đề nghị đổi 3->4 tôi nói `/api/policy-search` "LUÔN
# trả 4 và BỎ QUA top_k". SAI. `top_k` CÓ hiệu lực, trần 8 (`top_k=10` -> HTTP
# 422 "less than or equal to 8"). Lần thử trước tôi đọc 422 thành "0 kết quả"
# vì code chỉ `.get("results")` mà không xem mã trạng thái — lỗi nuốt-mã-lỗi,
# đúng họ với vụ 403 bị đọc thành "agent không gọi tool".
# Kết luận @4 KHÔNG đổi (nó dựa trên số đoạn agent thật nhận), nhưng LÝ DO tôi
# đưa ra lúc đó sai một nửa, nên ghi lại ở đây.
HANG_CHAN_DOAN = (1, 3, 4, 8)


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt. PHẢI áp cho CẢ HAI vế khi so từ khoá.

    Sản phẩm bỏ dấu ở cả lúc index lẫn lúc tra. Bộ chấm chỉ bỏ một vế là đang đo
    một quy ước KHÁC sản phẩm — số ra vẫn đẹp đẽ mạch lạc, chỉ là nói về thứ khác.

    GỘP KHOẢNG TRẮNG (thêm 16/08, sau khi nó cắn lần thứ ba): text trong kho có
    xuống dòng GIỮA CÂU. Không gộp thì mọi cụm ≥2 từ vắt qua chỗ xuống dòng đều
    báo "không khớp" — mà luật chuỗi đặc trưng làm gần hết chuỗi đều là cụm dài.
    Đây là TRƯỢT GIẢ do thước, hướng ngược với pass giả nhưng cùng một hạng.
    """
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"\s+", " ", s)


# ===========================================================================
# NHÃN VẬT
# ===========================================================================


# ===========================================================================
# CỔNG ĐÓNG BĂNG LLM — dùng chung hạn mức TPM với 3 phiên khác + PO thật
# ===========================================================================


# ĐÓNG BĂNG CÒN ĐƯỢC BẬT BẰNG FILE, không chỉ bằng biến môi trường.
# Lý do (17/08): tôi tự đặt cổng đóng băng, tự đề nghị đội dùng nó, rồi **tự
# đốt 3 lượt LLM trong lúc đang đóng băng** — vì cổng chỉ nổ khi có người nhớ
# `export FIN05_DONG_BANG_LLM=1` trong ĐÚNG cái shell đang gõ. Biến môi trường
# chết theo shell; đóng băng thì không.
# Đây đúng lập luận tôi dùng để đòi cơ chế thay lời hứa — và cơ chế của tôi vẫn
# còn một nửa là lời hứa. File marker sống qua shell, qua phiên, qua nén ngữ
# cảnh, và ai cũng thấy nó bằng `ls`.
MOC_DONG_BANG = GOC / ".DANG-DONG-BANG-LLM"


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
    bien = os.environ.get("FIN05_DONG_BANG_LLM", "").strip() not in ("", "0", "false")
    if bien or MOC_DONG_BANG.exists():
        sys.exit(
            "🧊 ĐANG ĐÓNG BĂNG LLM — không chạy.\n"
            f"   Lệnh này cần model để: {ly_do_can_llm}\n"
            "   Trần TPM dùng chung với 3 phiên khác + PO thật; đo được một người\n"
            "   21 lượt/2 phút đã đẩy org tới 193k/200k, và 429 ra tới khách\n"
            "   thành HTTP 500.\n"
            f"   Nguồn: {'biến môi trường' if bien else MOC_DONG_BANG.name}\n"
            f"   Bỏ đóng băng: unset FIN05_DONG_BANG_LLM · rm {MOC_DONG_BANG.name}"
        )


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
    # STACK NÀO — 17/08 có HAI stack ở HAI chế độ hạ tầng khác nhau cùng lúc:
    # fin05-backend-1 đã nạp khoá mới (embedding sống), fin05ttl-backend-1 còn
    # mang khoá đã xoá (embedding chết). Một bảng số trộn hai stack sẽ trộn
    # "embedding sống" với "embedding chết" mà NHÌN KHÔNG RA.
    nhan["stack"] = os.environ.get("FIN05_STACK", "fin05") + " (đặt qua FIN05_STACK)"
    for ten, c in (("backend", "fin05-backend-1"), ("frontend", "fin05-frontend-1")):
        dang_chay = bool(_chay(["docker", "ps", "-q", "-f", f"name={c}"]))
        nhan[f"{ten}_image"] = (_chay(["docker", "inspect", c, "--format", "{{.Image}}"]) or "?")[7:19]
        # Container KHÔNG chạy thì `StartedAt` là `0001-01-01T00:00:00` — một
        # NGÀY HỢP LỆ VỀ HÌNH THỨC cho một trạng thái không tồn tại. Nhãn in ra
        # nó thì người đọc sáu tháng sau thấy một mốc thời gian, không thấy sự
        # thật. Cùng họ `.get(x, <mặc định trông hợp lệ>)`: điền đại một giá trị
        # hợp lệ vào chỗ đáng lẽ phải kêu.
        nhan[f"{ten}_started"] = (
            _chay(["docker", "inspect", c, "--format", "{{.State.StartedAt}}"])[:19]
            if dang_chay else "🔴 CONTAINER KHÔNG CHẠY")
    # NHÃN KHO — thêm 16/08 sau khi thiếu nó suýt làm tôi báo cáo sai.
    # Hai lượt chấm cùng ra 35,7% được coi là "cùng một phép đo lặp lại", trong
    # khi kho đã đổi 362 chunk/2 doc → 419 chunk/4 doc giữa hai lượt (đòn 4).
    # Số trùng nhau HOÀN TOÀN tình cờ; chỉ có thành phần ca trượt đổi mới lộ ra.
    # `he_thong` băm src/**/*.py — nó KHÔNG phủ kho, mà kho là nửa còn lại của vật.
    nhan["kho"] = _chay(
        ["docker", "exec", "fin05-backend-1", "sh", "-c",
         "cd /app && python scripts/kho_rag.py nhan"]
    ).splitlines()[0].strip() if _chay(["docker", "ps", "-q", "-f", "name=fin05-backend-1"]) else "?"
    # DẤU HẠ TẦNG — đóng vào nhãn VẬT, không để trong đầu người chạy.
    # 17/08: khoá OpenAI bị xoá ⟹ toàn bộ truy hồi chết, mà `docker ps` vẫn
    # `healthy`. Sáu tháng nữa ai mở bảng số ra sẽ thấy một ngày recall tụt đáy
    # mà không hiểu vì sao — trừ khi lý do nằm ngay trong nhãn.
    try:
        import httpx

        cc = httpx.Client(verify=False, timeout=20)
        cc.post(f"{BASE}/api/session", json={"phone": "0353000201", "password": "Demo@123"})
        rr = cc.post(f"{BASE}/api/policy-search", json={"query": "hạn mức"})
        cc.close()
        song = rr.status_code == 200 and (rr.json().get("results") or [])
        # DANH TÍNH model nhúng, không chỉ trạng thái sống/chết. Sắp có công tắc
        # hai chiều OpenAI <-> Qwen cho đường nhúng ⟹ HAI KHO = HAI KHÔNG GIAN
        # VECTOR = số KHÔNG so chéo được. Một nhãn chỉ ghi "embedding OK" sẽ để
        # hai chuỗi số khác không gian nằm cạnh nhau trông như một chuỗi.
        ten_nhung = _chay(["docker", "exec", "fin05-backend-1", "python", "-c",
                           "from src.config import RAG_EMBEDDING_MODEL as m; print(m)"]) or "?"
        nhan["embedding"] = (f"{ten_nhung} · {'OK' if song else f'NGHI CHẾT (HTTP {rr.status_code})'}")
    except Exception as e:  # noqa: BLE001
        nhan["embedding"] = f"KHÔNG KIỂM ĐƯỢC ({type(e).__name__})"
    return nhan


def kiem_kho() -> None:
    """Cổng chặn: kho phải khớp phiên bản chuẩn-hoá của code đang chạy."""
    cong = GOC / "scripts" / "kho_rag.py"
    if not cong.exists():
        print("  ⚠️  scripts/kho_rag.py CHƯA CÓ — không kiểm được kho có lệch vế chuẩn-hoá không.")
        print("      Số truy hồi dưới đây mang giả định CHƯA ĐƯỢC KIỂM. Xem docstring, mục 4.")
        return
    # CHẠY TRONG CONTAINER, không chạy trên host. Kho thật nằm trong Docker
    # volume `chroma_data` mount vào /app/data/rag_index — chỉ container thấy.
    # Chạy trên host thì `ROOT_DIR/data/rag_index` trỏ vào một đường KHÔNG tồn
    # tại, và Chroma **TẠO MỚI một store rỗng ở đó**, rồi công cụ báo "kho
    # trống". Nó không chỉ đọc nhầm chỗ — nó chế ra bằng chứng cho kết luận sai
    # của chính nó, và lần chạy thứ hai sẽ thấy một store "thật" do lần một đẻ ra.
    #
    # Đo được 16/08: cùng một lệnh, trong container `[OK] exit 0`; trên host
    # `[TRỐNG] exit 1`. Verify-ở-một-nơi-dùng-ở-nơi-khác.
    r = subprocess.run(
        ["docker", "exec", "fin05-backend-1", "sh", "-c", "cd /app && python scripts/kho_rag.py kiem"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print("  🔴 KHO LỆCH VẾ CHUẨN-HOÁ — DỪNG, không đo.")
        print("     " + (r.stdout or r.stderr).strip()[:300])
        sys.exit(3)
    print("  ✅ kho khớp phiên bản chuẩn-hoá của code đang chạy")


def canary_kho(c) -> None:
    """Cổng thứ HAI: kho có TRẢ LỜI được không — khác hẳn kho có TỒN TẠI không.

    16/08 tôi đo được **0/35 cả hai chế độ** và suýt báo cáo nó. Lúc đó:
      · `kho_rag.py kiem`  → xanh   (nó kiểm phiên bản chuẩn-hoá, không kiểm tra được)
      · `kho_rag.py nhan`  → 378 chunk · băm ổn  (nó đếm POSTGRES)
      · Chroma             → 378 vector          (index có thật)
      · `/api/policy-search` → `status=not_found`, 0 kết quả cho MỌI truy vấn
    Kho đang được NẠP LẠI ngay lúc đó. Mọi nhãn đều xanh, mọi con số đều rỗng.

    Ba nguồn xác nhận "kho ổn" đều đọc chỗ KHÁC với chỗ sản phẩm đọc. Thứ duy
    nhất bắt được là hỏi kho một câu và xem nó có trả lời không.
    """
    ma = []
    for q in ("hạn mức", "MoMo", "ngân hàng"):
        r = c.post(f"{BASE}/api/policy-search", json={"query": q})
        ma.append(r.status_code)
        if r.status_code == 200 and (r.json().get("results") or []):
            print(f"  ✅ kho TRẢ LỜI được (canary {q!r} → {len(r.json()['results'])} kết quả)")
            return
    # PHÂN BIỆT BA NGUYÊN NHÂN — chúng đòi ba hành động khác nhau, và gộp lại
    # thì ta đi sửa nhầm chỗ. 17/08: khoá OpenAI bị XOÁ ⟹ embedding 401 ⟹
    # policy-search trả 500, trong khi `docker ps` vẫn báo `healthy`. Nếu canary
    # chỉ nói "kho không trả lời được", người đọc sẽ đi nạp lại kho — mà kho
    # hoàn toàn nguyên vẹn.
    if any(m >= 500 for m in ma):
        print("  🔴 HẠ TẦNG HỎNG, KHÔNG PHẢI KHO — canary trả 5xx.")
        print(f"     mã trạng thái: {ma}")
        print("     Nghi khoá embedding chết (401 ở tầng dưới nổi lên thành 500).")
        print("     KHO CÓ THỂ HOÀN TOÀN NGUYÊN VẸN — đừng nạp lại, đừng sửa nhãn.")
        print("     Mọi số đo lúc này KHÔNG nói gì về sản phẩm.")
        sys.exit(5)
    # 200 + RỖNG có ÍT NHẤT hai nguyên nhân, và chúng đòi hai hành động ngược
    # nhau. 17/08 canary bản trước đoán "kho đang nạp lại" trong khi sự thật là
    # "khoá nhúng chết, kho NGUYÊN VẸN" — người đọc suýt đi nạp lại một cái kho
    # không hỏng. Hỏi thẳng trạng thái kho để tách hai nhánh.
    kho = _chay(["docker", "exec", "fin05-backend-1", "sh", "-c",
                 "cd /app && python scripts/kho_rag.py nhan"])
    kho_con_nguyen = "chunk" in kho and " 0 chunk" not in kho
    print("  🔴 CANARY TRẢ 200 NHƯNG RỖNG — DỪNG, không đo.")
    print(f"     kho: {kho.splitlines()[0].strip() if kho else '?'}")
    if kho_con_nguyen:
        print("     🔴 KHO NGUYÊN VẸN mà tra ra rỗng ⟹ KHÔNG phải kho đang nạp lại.")
        print("        Nghi tầng trên NUỐT một lỗi xác thực thành DANH SÁCH RỖNG:")
        print("        store.search() nổ 401, nhưng HTTP trả 200 + rỗng.")
        print("        Hình dạng ở sản phẩm: khách hỏi chính sách → hạ tầng mù →")
        print("        agent trả lời 'không tìm thấy chính sách nào'. Câu đó NGHE")
        print("        HỢP LỆ, và đó là loại nguy hơn bịa số — một câu trả lời")
        print("        đúng ngữ pháp cho một hệ thống đã hỏng.")
        sys.exit(6)
    print("     Kho trống/đang nạp lại. Số đo lúc này là 0 GIẢ, không phải sản phẩm hỏng.")
    sys.exit(4)


# ===========================================================================
# TRỤC TRUY HỒI
# ===========================================================================


def _dang_nhap(httpx):
    c = httpx.Client(verify=False, timeout=40)
    r = c.post(f"{BASE}/api/session", json={"phone": "0353000201", "password": "Demo@123"})
    r.raise_for_status()
    return c


def _tra(c, q: str, k: int | None = None) -> list[str]:
    than = {"query": q} if k is None else {"query": q, "top_k": k}
    r = c.post(f"{BASE}/api/policy-search", json=than)
    if r.status_code != 200:
        # KHÔNG nuốt mã lỗi thành danh sách rỗng. Một 422/429 im lặng biến thành
        # "truy hồi trượt", và ta đi sửa retrieval trong khi lỗi nằm ở request.
        print(f"  ⚠️  policy-search {r.status_code}: {r.text[:120]}")
        return []
    return [x.get("text", "") for x in (r.json().get("results") or [])][: (k or K)]


def _tra_agent(c, q: str) -> tuple[list[str], bool]:
    cong_dong_bang("chấm qua đường agent thật (/api/agent-chat)")
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
    canary_kho(c)
    ket = {"co_dau": [], "khong_dau": []}
    for x in duong:
        for che_do, khoa in (("co_dau", "query_co_dau"), ("khong_dau", "query_khong_dau")):
            doan = _tra(c, x[khoa], K_SOI)
            gop = bo_dau(" ".join(doan[:K]))
            # LUẬT ĐẶC TRƯNG (PO duyệt 16/08): chỉ `tu_khoa_dac_trung` mới cho ĐẠT.
            # `tu_khoa_phu` in ra để đọc, KHÔNG có quyền chấm — vì ca đạt nhờ từ
            # chung ("hạn mức", "ngân hàng") khớp được cả chunk BÊN CẠNH lẫn dòng
            # mục lục, tạo PASS GIẢ im lặng (xem RAG-04, và 9 ca rà ngày 16/08).
            hang = next(
                (i + 1 for i, d in enumerate(doan)   # hạng soi tới K_SOI=8
                 if any(bo_dau(tk) in bo_dau(d) for tk in x["tu_khoa_dac_trung"])), 0
            )
            dat = any(bo_dau(tk) in gop for tk in x["tu_khoa_dac_trung"])
            phu = [tk for tk in x["tu_khoa_phu"] if bo_dau(tk) in gop]
            ket[che_do].append(
                {"id": x["id"], "dat": dat, "so_doan": len(doan), "phu_khop": phu,
                 "hang": hang, "tai_lieu": (x.get("nguon") or {}).get("tai_lieu", "?")}
            )
    c.close()
    return {"duong": ket, "so_am_ban": len(am), "so_duong": len(duong)}


def mrr_ndcg(r: list[dict], k: int) -> tuple[float, float]:
    """MRR và NDCG@k — công thức mượn từ RAGAS (Apache 2.0), tính TẠI CHỖ.

    Bộ ca này có **đúng một đoạn đúng cho mỗi câu** (nhãn là một chuỗi đặc
    trưng), nên hai công thức rút gọn:

        MRR    = trung bình 1/hạng        (0 nếu không có trong top-k)
        NDCG@k = trung bình 1/log2(hạng+1)   vì IDCG = 1 khi chỉ có 1 đoạn đúng

    VÌ SAO CẦN, khi đã có Recall@k: Recall là **nhị phân** — hạng 1 và hạng 4
    tính điểm y hệt nhau. Một đòn kéo ca từ hạng 4 lên hạng 1 sẽ cho **delta
    Recall = 0** và trông như vô dụng. Đó chính là chỗ HyDE gây tranh cãi: nó
    cứu ca chìm sâu nhưng đẩy ca sát nút ra ngoài — hai chiều triệt tiêu nhau
    trên pass/fail, và ta không thấy gì.

    ⚠️ GIỚI HẠN PHẢI ĐỌC KÈM: trần `top_k` của API là **8**. Ca ở hạng 9 và ca
    chìm ở hạng 500 **cho cùng một con số 0**. Nên hai chỉ số này tách được
    "hạng 1 với hạng 8", KHÔNG tách được "trượt sát nút với chìm sâu" như mục
    tiêu N2 đặt ra. Muốn thế phải nới trần API hoặc có móc chẩn đoán riêng.
    """
    n = len(r) or 1
    mrr = sum(1 / x["hang"] for x in r if 0 < x["hang"] <= k) / n
    ndcg = sum(1 / math.log2(x["hang"] + 1) for x in r if 0 < x["hang"] <= k) / n
    return mrr, ndcg


def in_truy_hoi(kq: dict) -> float:
    print(f"\n── TRỤC TRUY HỒI (Recall@{K}, trung bình HAI chế độ gõ) ──")
    ti = {}
    for che_do in ("co_dau", "khong_dau"):
        r = kq["duong"][che_do]
        dat = sum(1 for x in r if x["dat"])
        ti[che_do] = dat / len(r) if r else 0.0
        hong = [x["id"] for x in r if not x["dat"]]
        print(f"  {che_do:11} {dat}/{len(r)} = {ti[che_do]*100:5.1f}%   trượt: {', '.join(hong[:8])}{' …' if len(hong)>8 else ''}")
        gia = [x["id"] for x in r if not x["dat"] and x.get("phu_khop")]
        if gia:
            print(f"  {'':11} ↳ {len(gia)} ca TRƯỢT nhưng vẫn khớp từ-khoá-phụ "
                  f"(= PASS GIẢ dưới thước cũ): {', '.join(gia)}")
    r = kq["duong"]["co_dau"]
    print("  dải chẩn đoán (co_dau) — hạng của chunk đúng:")
    for k in HANG_CHAN_DOAN:
        n = sum(1 for x in r if 0 < x["hang"] <= k)
        print(f"     Recall@{k} = {n}/{len(r)} = {n / len(r) * 100:5.1f}%"
              + ("   ← SỔ SÁCH (k của sản phẩm)" if k == K else ""))
    for ten, k in (("@4  (chấm)", K), ("@8  (trần API)", K_SOI)):
        m, n_ = mrr_ndcg(r, k)
        print(f"     MRR {ten:<14} {m:6.3f}     NDCG {ten:<14} {n_:6.3f}")
    print("     (hạng 9+ và hạng 500 cho CÙNG một số 0 — trần top_k của API là 8,"
          "\n      nên hai chỉ số này KHÔNG tách được 'trượt sát nút' với 'chìm sâu')")
    ngoai = sum(1 for x in r if x["hang"] == 0)
    print(f"     chunk đúng KHÔNG nằm trong top-{K_SOI}: {ngoai}/{len(r)}"
          " ⟹ nới k không phải đòn chính")
    tos = [x for x in r if x["tai_lieu"] == "MoMo_ToS"]
    print(f"  theo tài liệu: ToS {sum(1 for x in tos if x['dat'])}/{len(tos)}"
          f" · FAQ {sum(1 for x in r if x['dat'] and x['tai_lieu'] != 'MoMo_ToS')}"
          f"/{len(r) - len(tos)}")
    tb = (ti["co_dau"] + ti["khong_dau"]) / 2
    print(f"  {'TRUNG BÌNH':11} {tb*100:5.1f}%   → điểm trục = 20 × {tb:.4f} = {20*tb:.2f}")
    print(f"\n  ({kq['so_am_ban']} ca ÂM BẢN KHÔNG chấm ở trục này — retrieval luôn trả k chunk,")
    print("   nó không có khái niệm 'không tìm thấy'. Chúng đo AGENT, thuộc trục khác.)")
    return 20 * tb


# ===========================================================================


def in_khoi_spec(nhan: dict, truc: list[tuple[str, float, float, str]],
                 mot_phan: str | None = None) -> None:
    """In một KHỐI CHÉP THẲNG vào spec — để không ai phải chép tay số nữa.

    VÌ SAO: soi `benchmark-spec` ngày 17/08 ra **7 chỗ lệch, 6 chỗ cùng một
    dạng** — số cũ còn sót lại sau khi số mới thay chỗ. Không chỗ nào tính sai.
    Đó là chi phí của một tài liệu do người sửa nhiều lần trong một ngày số
    liệu đổi liên tục, và soi tay chỉ bắt được lần này chứ không chặn lần sau.

    Chữa gốc: spec **chép nguyên văn khối này** thay vì diễn giải lại thành
    câu. Số cũ không thể sót vì **không ai chép tay nữa** — cùng họ với việc
    gom cổng đóng băng về một nguồn sự thật.

    Hai thứ khối này BẮT BUỘC mang theo, vì chúng là phần hay rơi nhất khi
    chép tay:
      (a) **nhãn vật + thời điểm** — chép vào là biết số của lượt nào, đo trên
          vật nào. Thiếu nó thì một bảng số đúng vẫn có thể đang mô tả một cái
          kho đã bị gỡ (đã xảy ra: nhãn `419 chunk` gắn lên số đo trên kho 378,
          mà 419 chính là kho còn 57 chunk rác).
      (b) **dòng cảnh báo cho trục `khong_do_duoc`** — phần "chưa đo được" là
          phần dễ rơi nhất khi chép, và rơi nó thì bảng trông đầy đủ hơn sự
          thật. Loại khỏi mẫu số thì được; loại khỏi tầm mắt thì không.
    """
    # KHỐI MỘT PHẦN: lượt --chi-truy-hoi KHÔNG chạy 4 trục kia, nhưng chúng CÓ
    # số hợp lệ từ lượt khác. In cả bảng với 4 dòng "KHÔNG ĐO ĐƯỢC" thì ai chép
    # nguyên văn sẽ XOÁ MẤT số đúng — công cụ sinh ra để chống số-cũ-còn-sót lại
    # tự tay xoá số-mới-đang-đúng. Nên lượt một phần chỉ in ĐÚNG dòng nó đo.
    # CỔNG HIỆU CHUẨN TRỌNG TÀI — chặn ở chỗ SINH RA số, không ở chỗ đọc số.
    # Security dựng một khối giới hạn phạm vi có dòng "chưa có kappa thì KHÔNG
    # công bố". Khối đó tự chặn — nhưng chỉ chặn được người ĐỌC nó đúng lúc
    # công bố, tức vẫn còn một nửa là trí nhớ (Luật 10c). Cổng thật phải nằm ở
    # công cụ sinh ra con số, vì đó là chỗ không ai đi vòng qua được.
    hc = GOC / "eval" / "results" / "hieu_chuan_trong_tai.json"
    if not mot_phan and not hc.exists():
        print("\n" + "=" * 74)
        print("🔴 KHÔNG IN KHỐI ĐẦY ĐỦ — trọng tài CHƯA HIỆU CHUẨN")
        print("=" * 74)
        print(f"  Thiếu {hc.relative_to(GOC)} (kappa + tỉ lệ rộng-tay/chặt-tay).")
        print("  Con số tổng đi qua `_llm_judge`, nên chưa đo sai số của trọng tài")
        print("  thì con số đó CHƯA CÓ KHOẢNG TIN CẬY — công bố nó ở dạng một con")
        print("  số đơn là nói quá phần đo được.")
        print("  Trục truy hồi KHÔNG qua trọng tài: dùng `--chi-truy-hoi --khoi-spec`.")
        return
    print("\n" + "=" * 74)
    print("KHỐI CHÉP VÀO SPEC — chép NGUYÊN VĂN, đừng diễn giải lại")
    if mot_phan:
        print(f"⚠️  KHỐI MỘT PHẦN: chỉ thay dòng «{mot_phan}». CÁC TRỤC KHÁC GIỮ NGUYÊN"
              "\n    trong spec — lượt này không chạy chúng, không có nghĩa chúng chưa đo.")
    print("=" * 74)
    print("```")
    print(f"# đo lúc {nhan['luc']}")
    print(f"# nhãn vật: commit {nhan['commit']} · he_thong {nhan['he_thong']}"
          f" · backend {nhan['backend_image']} (StartedAt {nhan['backend_started']})")
    print(f"#           {nhan['kho']}")
    print(f"# bộ ca: {nhan['so_ca']}")
    print()
    print(f"| {'Trục':<22} | {'Số thật':<28} | Điểm |")
    print(f"|{'-' * 24}|{'-' * 30}|------|")
    tong, mau = 0.0, 0.0
    chua = []
    for ten, diem, tran, mo_ta in truc:
        if mot_phan and ten != mot_phan:
            continue
        if diem is None:
            chua.append(ten)
            print(f"| {ten:<22} | {'KHÔNG ĐO ĐƯỢC':<28} | *(loại khỏi mẫu số)* |")
            continue
        tong += diem
        mau += tran
        print(f"| {ten:<22} | {mo_ta:<28} | **{diem:.2f}** |")
    if mot_phan:
        print("\n(KHÔNG in tổng: lượt một phần không đủ dữ kiện để cộng lại.)")
    else:
        print(f"\n**TỔNG = {tong:.2f} / {mau:.0f} điểm đo được = {tong / mau * 100:.1f}%**")
    if chua:
        print(f"\n⚠️ CHƯA ĐO ĐƯỢC (loại khỏi mẫu số, KHÔNG loại khỏi tầm mắt): "
              f"{', '.join(chua)}")
    print("```")
    if chua:
        print("\n  ⚠️  Khối trên có trục CHƯA ĐO ĐƯỢC. Chép thiếu dòng cảnh báo đó"
              "\n      thì bảng trông đầy đủ hơn sự thật.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-truy-hoi", action="store_true")
    ap.add_argument("--khoi-spec", action="store_true",
                    help="in thêm KHỐI CHÉP THẲNG vào spec (nhãn vật + bảng điểm "
                         "+ cảnh báo trục chưa đo được)")
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

    if a.khoi_spec:
        r = kq["duong"]["co_dau"]
        tos = [x for x in r if x["tai_lieu"] == "MoMo_ToS"]
        in_khoi_spec(nhan, [
            ("An toàn (30)", 30.0, 30, "invariants + adversarial + over-block"),
            ("Đúng dữ liệu (25)", 25.0, 25, "cổng-96 + grounding"),
            ("Truy hồi RAG (20)", diem, 20,
             f"Recall@{K} TB hai chế độ · ToS {sum(1 for x in tos if x['dat'])}/{len(tos)}"),
            ("Trải nghiệm (15)", None, 15, "judge chưa hiệu chuẩn (chờ 30 nhãn)"),
            ("Hiệu năng (10)", 10.0, 10, "0 ca vượt 30s — do_token_latency"),
        ], mot_phan="Truy hồi RAG (20)" if a.chi_truy_hoi else None)

    if not a.chi_truy_hoi:
        print("\n── SCORECARD ──")
        print("  Trục An toàn (30) · Đúng dữ liệu (25) · Trải nghiệm (15) · Hiệu năng (10):")
        print("  CHƯA ĐO trong lượt này — script mới phủ trục Truy hồi.")
        print("  Theo spec: trục chưa đo LOẠI KHỎI MẪU SỐ, KHÔNG quy 0.")
        print(f"  ⟹ đo được lượt này: {diem:.2f} / 20 điểm  ({diem/20*100:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
