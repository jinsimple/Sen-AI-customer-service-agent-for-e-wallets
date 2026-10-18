"""⑮ — ba test đơn vị RẺ (Review đề xuất, PO duyệt 25/08, commit `3df67ea`).

> ✅ **0 lượt LLM, 0 DB, 0 Redis, 0 docker** — chạy được từ bất cứ máy nào có
> `src/` cài đặt được (`pip install -r requirements.txt`).

Ba mục, tăng dần mức "đáng giá":
1. `la_khieu_nai_ca_nhan` — hàm quyết định cổng ④ (OTP cho NHÓM B) có bắn không.
2. `_otp_fresh(None, …)` phải trả `False` — khách CHƯA TỪNG xác thực.
3. 🔴 **Mục đáng giá nhất:** bất biến *"mọi call site production của
   `run_agent_turn` phải truyền `otp_verified_at` tường minh"* — introspect
   AST thật trên `src/`, đúng idiom `tests/test_invariants.py` (đọc app/mã
   nguồn thật, không suy luận từ trí nhớ). Hôm nay đúng MỘT call site
   (`src/api/main.py`) và nó đúng — nhưng không cổng nào canh việc ai đó
   thêm call site THỨ HAI mà quên truyền, và lúc ấy sentinel `_ALWAYS_FRESH`
   (`src/agents/graph.py`) sẽ coi như khách ĐÃ xác thực.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from src.agents.triage import is_personal_complaint
from src.agents.tools.customer_tools import _otp_fresh

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"
# File ĐỊNH NGHĨA `run_agent_turn` — loại khỏi quét call site để không tự bắt
# chính chữ ký hàm/lời gọi đệ quy nội bộ module (phạm vi khác với "call site
# production gọi VÀO agent từ tầng ngoài", đúng thứ bất biến này canh).
FILE_DINH_NGHIA = SRC / "agents" / "graph.py"


# ---------------------------------------------------------------------------
# 1. la_khieu_nai_ca_nhan — hộp đen, dùng lại corpus đã có nguồn gốc rõ
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sentence,mong", [
    # Dương — khiếu nại cá nhân THẬT (nguồn: eval/bo_ca_am_thu_slot_dot2.json
    # DOT2-DUONG-01, đã xác nhận đi thu_slot trên phan_luong() thật 25/08).
    ("tôi chuyển nhầm tiền cho người lạ rồi, không nhớ chuyển bao nhiêu", True),
    ("tôi bị trừ tiền", True),
    # Âm — câu hỏi CHÍNH SÁCH chung, không mô tả giao dịch của khách (nguồn:
    # tests/test_1a_luat_hoi_prompt.py::test_r1_cau_hoi_chinh_sach_khong_bi_hoi_slot).
    ("Phí chuyển tiền trong ví là bao nhiêu vậy?", False),
    ("tôi cần rút tiền, thủ tục thế nào", False),
])
def test_la_khieu_nai_ca_nhan_phan_biet_dung_khieu_nai_voi_cau_hoi_chinh_sach(sentence, mong):
    """Cổng ④ chỉ được bắn cho khiếu nại cá nhân (Q1) — câu hỏi chính sách
    chung phải đi qua KHÔNG bị OTP chặn."""
    assert is_personal_complaint(sentence) is mong, (
        f"la_khieu_nai_ca_nhan({sentence!r}) = {not mong}, mong {mong}"
    )


# ---------------------------------------------------------------------------
# 2. _otp_fresh(None, …) → False
# ---------------------------------------------------------------------------

def test_otp_fresh_none_la_chua_tung_xac_thuc_khong_phai_da_het_han():
    """`None` (chưa từng có `otp_verified_at`) và một mốc thời gian ĐÃ QUA
    HẠN là hai trạng thái khác nhau về Ý NGHĨA (chưa từng xác thực vs đã
    từng nhưng cũ) nhưng phải cho CÙNG kết luận: không fresh. Test này canh
    riêng nhánh `None` — nhánh dễ bị bỏ sót nhất vì không phải một con số để
    so sánh, mà là một GIÁ TRỊ VẮNG MẶT."""
    assert _otp_fresh(None, 15) is False


# ---------------------------------------------------------------------------
# 3. 🔴 Bất biến — mọi call site production của run_agent_turn truyền
#    otp_verified_at tường minh
# ---------------------------------------------------------------------------

def _goi_truc_tiep(node: ast.Call) -> bool:
    """`run_agent_turn(...)` — gọi thẳng bằng tên."""
    fn = node.func
    return getattr(fn, "id", None) == "run_agent_turn" or getattr(fn, "attr", None) == "run_agent_turn"


def _tim_call_sites(cay: ast.AST, duong_dan: str) -> list[tuple[int, list[str]]]:
    """Trả `[(dòng, [tên keyword đã truyền]), ...]` cho MỌI cách một call
    node có thể "là" một lượt gọi `run_agent_turn`:
      (a) gọi thẳng — `run_agent_turn(session, otp_verified_at=..., ...)`
      (b) gọi GIÁN TIẾP qua wrapper — `run_agent_turn` xuất hiện như một
          ĐỐI SỐ (tên trần, không gọi) của một call khác, kiểu
          `_handle_tool_error(run_agent_turn, session, otp_verified_at=...)`
          — hình dạng THẬT đang dùng ở `src/api/main.py` hôm nay. Bỏ sót
          nhánh (b) thì bất biến này MÙ với chính call site duy nhất nó
          phải canh."""
    outcome = []
    for node in ast.walk(cay):
        if not isinstance(node, ast.Call):
            continue
        if _goi_truc_tiep(node):
            ten_kw = [kw.arg for kw in node.keywords if kw.arg]
            outcome.append((node.lineno, ten_kw))
            continue
        # (b) run_agent_turn nằm TRẦN trong danh sách đối số của call này
        co_ten_tran = any(
            isinstance(a, ast.Name) and a.id == "run_agent_turn" for a in node.args
        )
        if co_ten_tran:
            ten_kw = [kw.arg for kw in node.keywords if kw.arg]
            outcome.append((node.lineno, ten_kw))
    return outcome


def test_moi_call_site_production_truyen_otp_verified_at_tuong_minh():
    """🔴 Mục đáng giá nhất của ⑮. Quét AST THẬT trên toàn bộ `.py` dưới
    `src/` (trừ file định nghĩa `run_agent_turn`) — không đọc từ trí nhớ,
    không tin danh sách "một call site" đã biết. Nếu ai thêm call site thứ
    hai mà quên `otp_verified_at=`, sentinel `_ALWAYS_FRESH` (`graph.py`) sẽ
    coi khách như ĐÃ xác thực — đúng lỗ ràng buộc cứng 4 mà ④ dựng ra để vá.
    """
    tat_ca: list[tuple[str, int, list[str]]] = []
    for p in SRC.rglob("*.py"):
        if p == FILE_DINH_NGHIA:
            continue
        cay = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        for line, kw in _tim_call_sites(cay, str(p)):
            tat_ca.append((str(p.relative_to(SRC.parent)), line, kw))

    # Luật A (đối chứng THUẬN): cổng phải KÊU khi thứ nó canh KHÔNG CÒN TỒN
    # TẠI — nếu quét ra 0 call site, bất biến "mọi call site đều đúng" đạt
    # MỘT CÁCH RỖNG (vacuously true), và test xanh không còn nói lên điều gì.
    assert tat_ca, (
        "Quét KHÔNG thấy call site production nào của run_agent_turn — "
        "hoặc route gọi agent đã đổi cách gọi (khác cả (a) lẫn (b) test này "
        "biết nhận diện), hoặc bất biến này đã mù. Cả hai đều phải ĐIỀU TRA, "
        "không phải coi đây là 'đạt'."
    )

    thieu = [(f, d, kw) for f, d, kw in tat_ca if "otp_verified_at" not in kw]
    assert not thieu, (
        f"{len(thieu)}/{len(tat_ca)} call site KHÔNG truyền `otp_verified_at=` tường minh:\n"
        + "\n".join(f"  {f}:{d}  (keywords đã truyền: {kw})" for f, d, kw in thieu)
        + "\nThiếu tham số này ⟹ sentinel `_ALWAYS_FRESH` coi khách như ĐÃ xác thực OTP."
    )
