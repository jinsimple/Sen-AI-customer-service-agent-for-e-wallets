"""Cổng hành vi O3 sau bản vá A+B — viết TỪ ĐẶC TẢ, không đọc src/.

Nguồn đặc tả (đúng ba, không tự thêm):
  · brief `docs/giao-viec/2026-08-18-team-o3-demo-len-main.md` mục 2-QA/QC (5 nhóm ca)
  · PO-agent bổ sung 19/08 (chuẩn thuận từ định hạng Bảo Mật): ca ⑥ — echo trong
    payload LỖI không phải nguồn hợp lệ
  · `docs/security/spec-sua-O3-O4-va-corpus-tan-cong.md` §1.2 (luật xuất xứ:
    nguồn gồm tool lượt này VÀ các lượt trước cùng hội thoại + lời khách)

Giao diện lấy bằng introspection RUNTIME (inspect.signature — tiền lệ
`do_loc_dau_ra_offline.py` và test O2), không mở file src/ nào:

    loc_dau_ra(reply, *, nguon, tin_nhan_khach="", loi_khach="",
               thread_id="", correlation_id=None) -> (reply_moi, [nhóm])

Quy ước "bị chặn" = reply_moi != reply (bộ lọc thay câu). Quy ước ráp `nguon`
= json.dumps từng kết quả tool, nối "\\n" — cùng `nguon_tu_payload()` của
eval/do_loc_dau_ra_offline.py (đã khai ở đó: quy ước này CHƯA đối chiếu đường
sản xuất; các ca cần đường ráp THẬT nằm ở phần seam bên dưới, không giả lập).

Vì sao file này không tự lừa mình (Luật 1 + Luật A):
  · Nếu bộ lọc thành no-op, mọi ca PHẢI-QUA xanh oan — nhưng các ca PHẢI-CHẶN
    trong CÙNG file sẽ đỏ ⟹ suite vẫn phân biệt được "lọc đúng" với "lọc chết".
  · Chiều KÊU có đối chứng dương cùng họ (token có trong nguồn → QUA) để chứng
    minh chặn là do THIẾU XUẤT XỨ, không phải chặn mọi token.
  · Ca ③⑥ dùng seam THẬT (`rap_nguon_o3`, hợp đồng Lead chuyển 19/08) thay vì
    nguồn tự chế — đo tầng lọc với nguồn tự chế là đo một ĐẠI DIỆN trên giả
    định chưa kiểm (Luật R④). Seam không gọi được ⟹ SKIP "KHÔNG ĐO ĐƯỢC".
  · [ĐO] tự bắt 19/08: ToolMessage thiếu `name=` làm `rap_nguon_o3` trả
    `luot_truoc: []` LUÔN — mọi ca PHẢI-CHẶN xanh vì lý do SAI (seam chết,
    không phải Đ1 đúng). Sửa bằng cách LUÔN gắn `name=` khi dựng ToolMessage
    trong file này, và LUÔN có ≥1 ca đối chứng dương đi kèm mỗi nhóm ca chặn.
  · Ca ⑧ (dict thiếu khoá `status` → PHẢI CHẶN) đã RÚT 19/08: tiền đề sai —
    [ĐO] Lead, get_customer_history/create_ticket/request_human_handoff
    THÀNH CÔNG BÌNH THƯỜNG không có `status` top-level; chặn nó là loại
    payload hợp lệ của 3/5 tool. Ca ⑪⑫⑬ thay vào, đúng hình dạng payload
    THẬT của ba tool đó — bộ ③⑥⑦⑨ + đối chứng dương cũ chỉ phủ
    lookup_transaction (2/5 tool CÓ status), nên không nói được gì về
    get_customer_history — đúng tool đứng sau câu verify demo.

thread_id mỗi ca một cái riêng — tránh trạng thái tích luỹ theo thread
(artifact 27→5→0 ngày 15/08 sinh ra đúng từ việc dùng chung thread khi replay).
"""
from __future__ import annotations

import json
import uuid

import pytest

try:
    from src.agents.output_filter import loc_dau_ra
except ImportError:
    pytest.skip(
        "Bộ lọc đầu ra chưa import được từ host — 'chưa đo được', KHÔNG phải 'đạt'.",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Nguồn dùng chung: payload tool THÀNH CÔNG của "lượt này"
# ---------------------------------------------------------------------------
_KET_QUA_TOOL_LUOT_NAY: list[dict] = [
    {
        "status": "success",
        "transaction_id": "TXN20260801000596",
        "amount": 1100000,
        "created_at": "2026-08-01T10:15:00",
        # SĐT đã qua scrub TRƯỚC khi vào hội thoại — nguồn chỉ có bản che.
        "customer_phone": "091*****78",
    },
    {
        "status": "success",
        "transaction_id": "TXN20260802000601",
        "amount": 262000,
        "created_at": "2026-08-02T09:00:00",
    },
]


def _rap_nguon(ket_qua: list[dict]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in ket_qua)


_NGUON = _rap_nguon(_KET_QUA_TOOL_LUOT_NAY)
_KHACH = "Cho mình xem hai giao dịch gần đây với."  # không chứa chữ số nào


def _goi(reply: str, nguon: str = _NGUON, khach: str = _KHACH):
    moi, nhom = loc_dau_ra(
        reply,
        nguon=nguon,
        tin_nhan_khach=khach,
        thread_id=f"O3GATE-{uuid.uuid4().hex[:12]}",
    )
    return moi, nhom


# ===========================================================================
# Ca ① — NGÀY viết bằng chấm / gạch / khoảng trắng PHẢI QUA
# (không dãy lạ nào khác trong reply; cơ chế lỗi cũ: dấu phân cách văn xuôi
#  dán 01.08.2026 thành dãy ma 01082026 không có trong nguồn)
# ===========================================================================
@pytest.mark.parametrize(
    "reply",
    [
        pytest.param("Giao dịch gần nhất của bạn được thực hiện ngày 01.08.2026 nhé.", id="ngay_dau_cham"),
        pytest.param("Giao dịch gần nhất của bạn được thực hiện ngày 01-08-2026 nhé.", id="ngay_dau_gach"),
        pytest.param("Giao dịch gần nhất của bạn được thực hiện ngày 01 08 2026 nhé.", id="ngay_khoang_trang"),
    ],
)
def test_ngay_cham_gach_khoang_trang_phai_qua(reply: str):
    moi, nhom = _goi(reply)
    assert moi == reply, (
        f"CHẶN OAN ngày hợp lệ (nhóm={nhom}). Cơ chế lỗi #1 của brief: "
        "dấu phân cách văn xuôi bị dán thành dãy ma ≥7 chữ số."
    )


# ===========================================================================
# Ca ② — HAI số tiền hợp lệ cạnh nhau, ngăn bằng ", " PHẢI QUA
# (cả hai đều có trong tool payload; cơ chế lỗi cũ: dán qua ", " thành
#  1100000262000 — số không tồn tại ở đâu)
# ===========================================================================
def test_hai_so_tien_hop_le_canh_nhau_phai_qua():
    reply = "Hai khoản gần nhất của bạn là 1.100.000, 262.000 — cả hai đều đã hoàn tất."
    moi, nhom = _goi(reply)
    assert moi == reply, (
        f"CHẶN OAN hai số tiền đều có trong nguồn (nhóm={nhom}). "
        "Cơ chế lỗi #2 của brief: dán qua ', ' thành 1100000262000."
    )


# ===========================================================================
# Ca ④ — CHIỀU KÊU (Luật A — thiếu là cổng rỗng)
# ===========================================================================
def test_so_bay_chu_so_lien_khong_co_trong_nguon_phai_chan():
    reply = "Số dư hiện tại của bạn là 9876543 đồng."
    moi, nhom = _goi(reply)
    assert moi != reply, (
        "Số 9876543 (7 chữ số, viết liền) không truy vết được về nguồn nào "
        "mà vẫn QUA — chiều bắt-bịa của O3 đã bị nới (bẫy B↔F brief cảnh báo)."
    )


def test_sdt_da_bi_scrub_khoi_tool_result_phai_chan():
    """Nguồn CHỈ có bản che `091*****78`. Reply lộ số đầy đủ.

    Bẫy thiết kế mà ca này canh: MỌI mảnh số của một SĐT đã che ('091', '78')
    đều là chuỗi con của số đầy đủ theo cấu tạo — một luật xuất xứ so-chuỗi-con
    hai chiều KHÔNG có ngưỡng độ dài tối thiểu cho dãy nguồn sẽ hợp thức hoá
    đúng số bị che. Brief mục 2-QA/QC dòng 4 đòi CHẶN, không thoả hiệp.
    """
    reply = "Số điện thoại nhận OTP của bạn là 0912345678 nhé."
    moi, nhom = _goi(reply)
    assert moi != reply, (
        "SĐT đầy đủ 0912345678 QUA trong khi nguồn chỉ có bản che 091*****78 — "
        "mảnh số của bản che đang được dùng làm xuất xứ cho số nguyên vẹn."
    )


def test_token_dinh_danh_noi_bo_khong_co_trong_nguon_phai_chan():
    reply = "Hồ sơ của bạn mang mã tham chiếu nội bộ TR-8F3A2B91, mình đã kiểm tra rồi."
    moi, nhom = _goi(reply)
    assert moi != reply, (
        "Token chữ-số TR-8F3A2B91 không có trong nguồn nào mà vẫn QUA — "
        "kênh _TOKEN_MA (so khớp tuyệt đối) không còn canh."
    )


def test_doi_chung_duong_token_co_trong_nguon_phai_qua():
    """Đối chứng dương của họ token: chặn ở trên phải vì THIẾU XUẤT XỨ,
    không phải vì bộ lọc chặn mọi token chữ-số."""
    reply = "Mã giao dịch của bạn là TXN20260801000596, đã hoàn tất từ 01/08."
    moi, nhom = _goi(reply)
    assert moi == reply, (
        f"Token có thật trong nguồn cũng bị chặn (nhóm={nhom}) — "
        "nếu ca này đỏ cùng ca trên thì bộ lọc đang chặn theo HÌNH DẠNG, "
        "không theo XUẤT XỨ, và hai ca của họ token không nói được gì về nhau."
    )


# ===========================================================================
# Ca ⑤ — GHÉP ①+④: chặn vì SỐ BỊA, không phải vì ngày.
# Cặp đối chứng trong cùng một test để quy được nguyên nhân: cùng câu, chỉ
# khác đúng một dãy số bịa. Control QUA + condition CHẶN ⟹ thứ bị chặn là số
# bịa. (Không đọc được "lý do" từ giao diện nên nguyên nhân chứng minh bằng
# hiệu của cặp, không bằng lời bộ lọc.)
# ===========================================================================
def test_ghep_ngay_hop_le_va_so_bia_chan_vi_so_bia():
    control = "Giao dịch ngày 01.08.2026 của bạn đã hoàn tất."
    condition = "Giao dịch ngày 01.08.2026 của bạn có mã đối soát 9876543."

    moi_control, nhom_control = _goi(control)
    assert moi_control == control, (
        f"Control (chỉ có ngày) bị chặn (nhóm={nhom_control}) — ca ghép không "
        "phân định được nguyên nhân khi chính ngày còn bị chặn oan (xem ca ①)."
    )

    moi_cond, _nhom = _goi(condition)
    assert moi_cond != condition, (
        "Reply chứa số bịa 9876543 viết liền mà vẫn QUA — chiều bắt-bịa hỏng "
        "ngay trong ca có mặt định dạng ngày hợp lệ."
    )


# ===========================================================================
# Ca ③' — guard TẦNG LỌC cho ca ③ (phát biểu đúng tầng, không thay ca ③):
# khi kênh `nguon` ĐÃ gồm payload tool lượt trước, tầng lọc không được tự
# thêm logic "chỉ lượt này" mà chặn lại.
# ===========================================================================
def test_nguon_da_gom_payload_luot_truoc_thi_tang_loc_khong_chan():
    nguon_gom_lich_su = _rap_nguon(
        _KET_QUA_TOOL_LUOT_NAY
        + [{"status": "success", "transaction_id": "TXN20260715000111", "amount": 5450000}]
    )
    reply = "Như mình đã tra giúp bạn lúc nãy, khoản TXN20260715000111 là 5.450.000 đồng."
    moi, nhom = _goi(reply, nguon=nguon_gom_lich_su)
    assert moi == reply, (
        f"Nguồn đã chứa kết quả tool lượt trước mà tầng lọc vẫn chặn (nhóm={nhom}) "
        "— lọc đang phân biệt 'lượt' bằng thứ gì đó ngoài kênh nguon."
    )



# ===========================================================================
# Ca ③ + ⑥ + kiểm-AIMessage + ⑦⑧⑨ + đối chứng dương — đo qua HÀM RÁP NGUỒN
# THẬT (bản vá A, graph). Giao diện là HỢP ĐỒNG do Lead chuyển 19/08, Coder
# không được đổi:
#
#     src/agents/graph.py::rap_nguon_o3(all_messages: list,
#                                        tool_calls_out: list[dict]) -> str
#
# Trả về chuỗi JSON hình dạng {"luot_nay": [...], "luot_truoc": [...]}.
#   luot_nay   = kết quả tool lượt hiện tại (giữ nguyên hình dạng cũ, gồm args)
#   luot_truoc = CHỈ phần `result` của ToolMessage các lượt trước; KHÔNG gom
#                `args` (tham số model tự đặt không phải nguồn hợp lệ); KHÔNG
#                gom AIMessage. Payload lịch sử bị loại nếu: không parse được
#                JSON · parse ra không phải dict · thuộc nhánh lỗi.
#
# Đây là tầng quyết định của các hành vi:
#   ③    kết quả tool THÀNH CÔNG của lượt trước  → là nguồn        → PHẢI QUA
#   ⑥    echo số bịa trong payload tool LỖI      → KHÔNG là nguồn  → PHẢI CHẶN
#   Ⓐ    lời agent cũ (AIMessage)                → KHÔNG là nguồn  → PHẢI CHẶN
#   ⑦⑧⑨  payload méo (JSON hỏng · thiếu status · không phải dict) → PHẢI CHẶN
#   Đ     status ∈ {found, not_found, multiple_matches}            → PHẢI QUA
#
# Nếu import graph hoặc gọi seam thất bại ⟹ SKIP "KHÔNG ĐO ĐƯỢC", không giả
# định hợp đồng đã đổi và không tự nới cho xanh.
# ===========================================================================
def _ham_rap_nguon_o3():
    import importlib

    try:
        g = importlib.import_module("src.agents.graph")
    except Exception as e:  # noqa: BLE001 — import graph cần env đầy đủ
        pytest.skip(
            f"Không import được src.agents.graph từ host ({type(e).__name__}: {e}) "
            "— các ca dùng seam KHÔNG ĐO ĐƯỢC, không phải đạt."
        )
    ham = getattr(g, "rap_nguon_o3", None)
    if not callable(ham):
        pytest.skip(
            "src.agents.graph.rap_nguon_o3 chưa tồn tại — hợp đồng do Lead khai "
            "19/08 chưa land trong cây làm việc. KHÔNG ĐO ĐƯỢC, không phải đạt."
        )
    return ham


def _rap_qua_seam(all_messages, tool_calls_out=()) -> str:
    ham = _ham_rap_nguon_o3()
    try:
        kq = ham(all_messages, list(tool_calls_out))
    except TypeError as e:
        pytest.skip(
            f"rap_nguon_o3 không nhận (all_messages, tool_calls_out) như hợp đồng "
            f"đã khai ({e}) — chữ ký đã đổi, cần Coder khai lại qua Lead. "
            "KHÔNG ĐO ĐƯỢC, không phải đạt."
        )
    if not isinstance(kq, str):
        pytest.skip(
            f"rap_nguon_o3 trả về {type(kq).__name__}, không phải chuỗi JSON như "
            "hợp đồng đã khai — KHÔNG ĐO ĐƯỢC, không phải đạt."
        )
    return kq


def _lich_su_hoi_thoai():
    """Hội thoại 2 lượt: lượt 1 có tool; lượt 2 (đang lọc) KHÔNG gọi tool."""
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    return [
        HumanMessage(content="Cho mình xem giao dịch hồi giữa tháng 7 với."),
        AIMessage(content="", tool_calls=[{
            "name": "lookup_transaction",
            "args": {"transaction_id": "TXN20260715000111"},
            "id": "call_1",
        }]),
        ToolMessage(
            content=json.dumps(
                {"status": "found", "transaction_id": "TXN20260715000111", "amount": 5450000},
                ensure_ascii=False,
            ),
            tool_call_id="call_1",
            name="lookup_transaction",
        ),
        # Lời agent cũ có chứa một dãy số KHÔNG truy vết được (đã lọt lượt đó
        # hoặc diễn giải) — không được trở thành nguồn cho lượt sau.
        AIMessage(content="Khoản đó phía đối tác ghi nhận lúc 14:05, mã nội bộ 7654321."),
        # Lượt 1b: model tự bịa tham số → tool trả LỖI, echo lại tham số.
        AIMessage(content="", tool_calls=[{
            "name": "lookup_transaction",
            "args": {"transaction_id": "8887776655"},
            "id": "call_2",
        }]),
        ToolMessage(
            content=json.dumps(
                {"status": "error", "message": "Không tìm thấy giao dịch 8887776655"},
                ensure_ascii=False,
            ),
            tool_call_id="call_2",
            name="lookup_transaction",
        ),
        HumanMessage(content="Vậy khoản giữa tháng 7 đó bao nhiêu tiền nhỉ?"),
    ]


_KHACH_LUOT_SAU = "Vậy khoản giữa tháng 7 đó bao nhiêu tiền nhỉ?"


def test_ca3_so_tu_ket_qua_tool_luot_truoc_phai_qua():
    nguon = _rap_qua_seam(_lich_su_hoi_thoai())
    reply = "Khoản TXN20260715000111 của bạn là 5.450.000 đồng nhé."
    moi, nhom = _goi(reply, nguon=nguon, khach=_KHACH_LUOT_SAU)
    assert moi == reply, (
        f"CHẶN OAN (nhóm={nhom}): kết quả tool THÀNH CÔNG của lượt trước không "
        "vào kênh nguồn — đúng cơ chế lỗi #3 của brief, bản vá A chưa phủ."
    )


def test_ca6_echo_so_bia_trong_payload_loi_khong_phai_nguon_phai_chan():
    nguon = _rap_qua_seam(_lich_su_hoi_thoai())
    reply = "Mình kiểm tra rồi, giao dịch 8887776655 của bạn đang được xử lý."
    moi, _nhom = _goi(reply, nguon=nguon, khach=_KHACH_LUOT_SAU)
    assert moi != reply, (
        "Số 8887776655 do model TỰ BỊA làm tham số, chỉ tồn tại trong echo của "
        "payload LỖI, mà vẫn QUA — kênh nguồn đang gom cả nhánh lỗi. Đặc tả "
        "PO-agent 19/08: kết quả tool THÀNH CÔNG mới là nguồn hợp lệ."
    )


def test_loi_agent_cu_trong_lich_su_khong_phai_nguon_phai_chan():
    nguon = _rap_qua_seam(_lich_su_hoi_thoai())
    reply = "Như mình nói lúc nãy, mã nội bộ của khoản đó là 7654321."
    moi, _nhom = _goi(reply, nguon=nguon, khach=_KHACH_LUOT_SAU)
    assert moi != reply, (
        "Dãy 7654321 chỉ tồn tại trong AIMessage cũ (lời agent) mà vẫn QUA — "
        "kênh nguồn đang gom nhầm AIMessage, đúng điểm Review được giao soi "
        "(brief mục 2-Review): lời agent KHÔNG phải nguồn hợp lệ."
    )


# ===========================================================================
# Ca ⑦⑨ — hai hình dạng méo mà mọi vị ngữ hợp lý (allow-list hay deny-list
# đúng chữ "error") đều phải loại: JSON hỏng · parse ra không phải dict.
#
# 🔴 RÚT ca ⑧ (19/08, Lead): kỳ vọng cũ "dict thiếu khoá `status` → PHẢI
# CHẶN" SAI tiền đề. [ĐO] Lead, 5/5 tool: top-level `status` trên đường
# THÀNH CÔNG chỉ có ở lookup_transaction/search_policy — get_customer_history/
# create_ticket/request_human_handoff THÀNH CÔNG BÌNH THƯỜNG không có
# `status` top-level. Chặn "thiếu status" là loại sạch payload hợp lệ của
# 3/5 tool khỏi kênh nguồn — đúng con bug ta đang chữa, không phải test nó.
# Vị ngữ đúng ở kênh nguồn là deny-list `status == "error"` (cố ý cho
# dict-thiếu-status đi qua); rủi ro "nhánh lỗi mới quên status" được canh ở
# TẦNG TOOL bằng ca ⑩, không phải ở kênh nguồn — đúng lớp, đừng gộp lại.
# ===========================================================================
def _lich_su_voi_payload_meo(payload_content: str, tool_call_id: str = "call_x"):
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    return [
        HumanMessage(content="Tra giúp mình giao dịch hôm qua với."),
        AIMessage(content="", tool_calls=[{
            "name": "lookup_transaction",
            "args": {"transaction_id": "TXN20260818000777"},
            "id": tool_call_id,
        }]),
        ToolMessage(content=payload_content, tool_call_id=tool_call_id, name="lookup_transaction"),
        HumanMessage(content="Vậy số đó là bao nhiêu nhỉ?"),
    ]


@pytest.mark.parametrize(
    "payload_content,day_so,id_ca",
    [
        pytest.param(
            '{"status": "success", "transaction_id": "TXN2026081800',  # cụt, JSON hỏng
            "5566778899",
            "ca7_json_hong",
            id="ca7_payload_khong_parse_duoc",
        ),
        pytest.param(
            json.dumps([{"amount": 5566778899}], ensure_ascii=False),  # parse ra LIST
            "5566778899",
            "ca9_khong_phai_dict",
            id="ca9_payload_khong_phai_dict",
        ),
    ],
)
def test_payload_meo_mo_khong_duoc_lam_nguon(payload_content: str, day_so: str, id_ca: str):
    noi_dung = payload_content
    if id_ca == "ca7_json_hong":
        # dãy số nằm trong phần chuỗi thô, sau chỗ JSON đã hỏng
        noi_dung = payload_content + f'0777", "amount": {day_so}'
    nguon = _rap_qua_seam(_lich_su_voi_payload_meo(noi_dung))
    reply = f"Giao dịch của bạn có giá trị {day_so} đồng nhé."
    moi, _nhom = _goi(reply, nguon=nguon, khach="Vậy số đó là bao nhiêu nhỉ?")
    assert moi != reply, (
        f"Dãy {day_so} chỉ tồn tại trong payload MÉO ({id_ca}) mà vẫn QUA — "
        "Đ1 đang thi hành dạng deny-list (`status == \"error\"`), fail-OPEN. "
        "Đặc tả Lead 19/08: allow-list {found, not_found, multiple_matches}."
    )


@pytest.mark.parametrize(
    "status,payload,day_so",
    [
        pytest.param(
            "found",
            {"status": "found", "transaction_id": "TXN20260818000777", "amount": 3210000},
            "3.210.000", id="duong_found",
        ),
        pytest.param(
            "not_found",
            {"status": "not_found", "message": "Không có giao dịch nào khớp"},
            "TXN20260818000777", id="duong_not_found_van_truy_ve_tham_so_hop_le",
        ),
        pytest.param(
            "multiple_matches",
            {"status": "multiple_matches",
             "candidates": [{"transaction_id": "TXN20260818000777", "amount": 3210000},
                            {"transaction_id": "TXN20260818000778", "amount": 990000}]},
            "3.210.000", id="duong_multiple_matches",
        ),
    ],
)
def test_doi_chung_duong_ba_status_hop_le_phai_qua(status: str, payload: dict, day_so: str):
    """Luật A vế một — cổng phải IM lúc bình thường.

    Thiếu ba ca này thì ⑦⑧⑨ không phân biệt được "Đ1 chặt đúng" với "bản vá A
    bị vô hiệu hoá hoàn toàn" (mọi payload lịch sử đều rớt ⟹ mọi ca chặn đều
    xanh vì lý do sai).

    `not_found` dùng chính mã giao dịch KHÁCH/tham số hợp lệ để tránh phụ thuộc
    echo tham số — [ĐO] Lead: nhánh này trả dict trần, KHÔNG echo tham số model
    tự đặt; nên nguồn hợp lệ của nó đến từ lời khách trong hội thoại.
    """
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    cau_khach = "Cho mình hỏi giao dịch TXN20260818000777 với."
    messages = [
        HumanMessage(content=cau_khach),
        AIMessage(content="", tool_calls=[{
            "name": "lookup_transaction",
            "args": {"transaction_id": "TXN20260818000777"},
            "id": "call_ok",
        }]),
        ToolMessage(content=json.dumps(payload, ensure_ascii=False), tool_call_id="call_ok", name="lookup_transaction"),
        HumanMessage(content="Số tiền là bao nhiêu nhỉ?"),
    ]
    nguon = _rap_qua_seam(messages)
    reply = f"Giao dịch bạn hỏi là {day_so} nhé."
    moi, nhom = _goi(reply, nguon=nguon, khach=cau_khach)
    assert moi == reply, (
        f"CHẶN OAN trên nhánh status={status} (nhóm={nhom}) — allow-list đang "
        "loại cả payload HỢP LỆ, hoặc bản vá A không gom được lịch sử. Nếu ca "
        "này đỏ thì ⑦⑧⑨ xanh không chứng minh được gì."
    )


# ===========================================================================
# Ca ⑪⑫⑬ — hình dạng payload THẬT của 3/5 tool KHÔNG có `status` top-level
# trên đường thành công (Lead 19/08, đo trực tiếp — contracts/agent-tools.yaml
# SAI ở đúng chỗ này cho create_ticket/request_human_handoff, finding drift
# của Bảo Mật, không dùng contract làm đặc tả ở đây).
#
# 🔴 VÌ SAO BA CA NÀY QUAN TRỌNG HƠN CẢ BỘ CŨ: ③⑥⑦⑨ + 3 đối chứng dương đều
# chạy trên DUY NHẤT hình dạng lookup_transaction (2/5 tool CÓ status). Một
# vị ngữ kiểu "admit chỉ khi có status hợp lệ" sẽ xanh tuyệt đối trên bộ đó
# mà vẫn loại sạch payload thật của get_customer_history/create_ticket/
# request_human_handoff — đúng nhóm câu verify "xem giao dịch gần đây" của
# Lead mục 2. Thiếu ba ca này, 19/20 xanh không chứng minh được gì ở đúng
# trục quan trọng nhất (Luật E: nhánh không bao giờ bắn = nhánh chưa kiểm).
# ===========================================================================
def test_ca11_get_customer_history_thanh_cong_khong_status_top_level_phai_qua():
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    payload = {
        "user_id": "USR-A", "kyc_level": "verified",
        "wallets": [{"wallet_id": "900000000001", "status": "active"}],
        "recent_transactions": [
            {"trans_id": "TXN20260818000999", "amount": 4750000, "status": "found"},
        ],
        "complaint_count_90d": 0, "complaints_tong": 0, "complaints": [],
    }
    cau_khach = "Cho mình xem giao dịch gần đây với."
    messages = [
        HumanMessage(content=cau_khach),
        AIMessage(content="", tool_calls=[{
            "name": "get_customer_history", "args": {}, "id": "call_gch",
        }]),
        ToolMessage(content=json.dumps(payload, ensure_ascii=False),
                    tool_call_id="call_gch", name="get_customer_history"),
        HumanMessage(content="Giao dịch gần nhất là bao nhiêu vậy?"),
    ]
    nguon = _rap_qua_seam(messages)
    reply = "Giao dịch gần nhất TXN20260818000999 của bạn là 4.750.000 đồng nhé."
    moi, nhom = _goi(reply, nguon=nguon, khach=cau_khach)
    assert moi == reply, (
        f"CHẶN OAN (nhóm={nhom}): payload get_customer_history THÀNH CÔNG "
        "(không có `status` top-level, đúng hình dạng thật) không vào được "
        "kênh nguồn — đây chính là tool đứng sau câu verify demo."
    )


def test_ca12_create_ticket_thanh_cong_khong_status_top_level_phai_qua():
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    payload = {
        "complaint_id": "CMP-QAGATE-01", "ticket_id": "TCK20260819000321",
        "priority": "normal", "sla_due_at": "2026-08-22T00:00:00",
        "should_escalate": False, "escalation_target": None,
        "tool_result_id": "TR-QAGATE01",
    }
    cau_khach = "Tôi muốn khiếu nại giao dịch chưa nhận được tiền."
    messages = [
        HumanMessage(content=cau_khach),
        AIMessage(content="", tool_calls=[{
            "name": "create_ticket", "args": {}, "id": "call_ct",
        }]),
        ToolMessage(content=json.dumps(payload, ensure_ascii=False),
                    tool_call_id="call_ct", name="create_ticket"),
        HumanMessage(content="Mã hồ sơ của tôi là gì vậy?"),
    ]
    nguon = _rap_qua_seam(messages)
    reply = "Mã hồ sơ của bạn là TCK20260819000321, mình đã ghi nhận rồi nhé."
    moi, nhom = _goi(reply, nguon=nguon, khach=cau_khach)
    assert moi == reply, (
        f"CHẶN OAN (nhóm={nhom}): payload create_ticket THÀNH CÔNG (không có "
        "`status` top-level, đúng hình dạng thật) không vào được kênh nguồn."
    )


def test_ca13_request_human_handoff_thanh_cong_khong_status_top_level_phai_qua():
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    payload = {
        "ticket_id": "TCK20260819000322",
        "human_handoff_requested": True, "created_new_ticket": True,
    }
    cau_khach = "Cho mình nói chuyện với người thật với."
    messages = [
        HumanMessage(content=cau_khach),
        AIMessage(content="", tool_calls=[{
            "name": "request_human_handoff", "args": {"reason": cau_khach}, "id": "call_hh",
        }]),
        ToolMessage(content=json.dumps(payload, ensure_ascii=False),
                    tool_call_id="call_hh", name="request_human_handoff"),
        HumanMessage(content="Mã hồ sơ để mình theo dõi là gì vậy?"),
    ]
    nguon = _rap_qua_seam(messages)
    reply = "Mã hồ sơ để bạn theo dõi là TCK20260819000322 nhé."
    moi, nhom = _goi(reply, nguon=nguon, khach=cau_khach)
    assert moi == reply, (
        f"CHẶN OAN (nhóm={nhom}): payload request_human_handoff THÀNH CÔNG "
        "(không có `status` top-level, đúng hình dạng thật) không vào được "
        "kênh nguồn."
    )


# ===========================================================================
# Ca ⑩ — INV: mọi đường trả về lỗi của mọi tool đều mang status=="error"
# (Lead 19/08, Review đề nghị). Đ1 hôm nay đúng nhờ QUAN SÁT (8/8 điểm lỗi
# hiện có mang khoá đó), không nhờ ÉP BUỘC — một nhánh lỗi mới quên `status`
# sẽ lọt vào nguồn trong im lặng nếu allow-list chỉ kiểm "không nằm trong 3
# giá trị tốt" bằng cách đọc SAI khoá.
#
# Dựng từ contracts/agent-tools.yaml (5 tool + output.status enum) + trigger
# lỗi đã có TIỀN LỆ trong tests/test_tools/*.py (raw layer ném ToolError cho
# đúng input này) — KHÔNG đọc file src/, chỉ tái dùng input đã công khai
# trong vùng ghi của chính tester.
#
# ⚠️ Nghịch lý Lead khai: contracts/agent-tools.yaml:94,106 khai output.status
# cho create_ticket/request_human_handoff mà CODE KHÔNG PHÁT (finding riêng
# của Bảo Mật, ngoài phạm vi hôm nay). Ca ⑩ với hai tool đó CHỈ đòi vế AN
# TOÀN của Đ1 — kết quả lỗi không được mang MỘT TRONG BA giá trị tốt — KHÔNG
# đòi đúng chữ "error". Neo vào HÀNH VI THẬT, không neo vào contract ở đây.
# ===========================================================================
_GIA_TRI_TOT_O3 = {"found", "not_found", "multiple_matches"}


def _goi_tool_va_quan_sat(tools: dict, ten: str, dau_vao: dict):
    """Gọi .invoke() thật, không giả định raise hay return — ghi lại CẢ HAI
    khả năng để assertion tự chọn, đúng nếp Luật H (ba trạng thái)."""
    try:
        kq = tools[ten].invoke(dau_vao)
    except Exception as e:  # noqa: BLE001 — quan sát hành vi thật của tool
        return {"_ngoai_le": f"{type(e).__name__}: {e}"}
    return kq if isinstance(kq, dict) else {"_khong_phai_dict": kq}


def test_ca10_moi_nhanh_loi_that_khong_lam_lot_gia_tri_tot_vao_nguon(sample_db):
    from datetime import datetime, timezone

    from src.agents.tools.customer_tools import build_customer_tools

    now = datetime.now(timezone.utc).timestamp()
    tools_a = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=now)}

    # Trigger lỗi cho tool contract khai KHỚP code, KHÔNG cần mạng — đòi đúng
    # status=="error". `search_policy` CỐ Ý loại khỏi ca này: nhánh lỗi của nó
    # chỉ trigger được qua lời gọi embedding thật, vi phạm yêu cầu "0 token
    # LLM" của brief (mục 1) — đo nó thuộc phạm vi khác, không phải Đ1 hôm nay.
    ca_khop_code = [
        ("lookup_transaction", {}),  # contract: thiếu cả trans_id/rec_code/phone+amount → error
    ]
    loi_thieu_error = []
    for ten, dau_vao in ca_khop_code:
        kq = _goi_tool_va_quan_sat(tools_a, ten, dau_vao)
        if kq.get("status") != "error":
            loi_thieu_error.append((ten, dau_vao, kq))
    assert not loi_thieu_error, (
        "Tool khai KHỚP code trong contract nhưng nhánh lỗi không trả đúng "
        f"status=='error': {loi_thieu_error}"
    )

    # get_customer_history: user không tồn tại — trigger đã có tiền lệ ở
    # tests/test_tools/test_get_customer_history.py::test_unknown_user_id_raises
    # (raw layer ném ToolError cho USR-NOPE). Build riêng một bộ tool cho user giả.
    try:
        tools_gia = {
            t.name: t for t in build_customer_tools(
                sample_db, user_id="USR-QAGATE-KHONG-TON-TAI", otp_verified_at=now,
            )
        }
        kq_gch = _goi_tool_va_quan_sat(tools_gia, "get_customer_history", {})
    except Exception as e:  # noqa: BLE001 — build_customer_tools tự nó có thể ném
        kq_gch = {"_ngoai_le_luc_build": f"{type(e).__name__}: {e}"}
    assert kq_gch.get("status") == "error", (
        f"get_customer_history với user không tồn tại không trả status=='error': {kq_gch}"
    )

    # create_ticket / request_human_handoff — Bảo Mật: contract lệch code,
    # finding riêng, KHÔNG thuộc phạm vi hôm nay. Ca ⑩ chỉ đòi vế AN TOÀN của
    # Đ1: kết quả lỗi không được trùng một trong ba giá trị TỐT.
    ca_lech_contract = [
        ("create_ticket", {
            "complaint_type": "money_not_received", "scope": "internal_wallet",
            "description_raw": "ca10 gate — khong dung that",
            "trans_id": "TXN-QAGATE-KHONG-TON-TAI",
        }),
        ("request_human_handoff", {"reason": ""}),
    ]
    lot_gia_tri_tot = []
    for ten, dau_vao in ca_lech_contract:
        kq = _goi_tool_va_quan_sat(tools_a, ten, dau_vao)
        if kq.get("status") in _GIA_TRI_TOT_O3:
            lot_gia_tri_tot.append((ten, dau_vao, kq))
    assert not lot_gia_tri_tot, (
        "VI PHẠM AN TOÀN Đ1: nhánh lỗi của tool trả một trong ba giá trị TỐT "
        f"({_GIA_TRI_TOT_O3}) — allow-list sẽ coi đây là nguồn hợp lệ: {lot_gia_tri_tot}"
    )


# ===========================================================================
# Ca ⑭ — GIỚI HẠN CÒN LẠI đã khai của mẫu `_DAY_SO` mới (Lead 19/08, đối
# chiếu độc lập với phát hiện của PO-agent): số BỊA viết bằng phân cách TRỘN
# (`2.500 000` — chấm rồi space, không đồng nhất) rơi khỏi tập trích hoàn
# toàn, QUA bộ lọc. Đây là THU HẸP so với đường nền (mẫu gốc bắt được), có
# khai, chấp nhận đánh đổi để đóng hai ca chặn oan ①②.
#
# xfail(strict=True), KHÔNG bỏ qua: ca thường sẽ đỏ ngay hôm nay, phá tiêu
# chí cổng-xanh của đường găng — nhưng một dòng comment không làm ai đỏ khi
# mẫu bị "tối ưu" lại sau này. strict=True buộc ngày lỗ được vá thì XPASS
# ⟹ cổng đỏ ⟹ còi báo "cập nhật sổ, gỡ khai giới hạn" (đúng bài học
# INV-15/F-18: kiểm tên constraint không đủ, phải có thứ đỏ ở chỗ không sửa
# được bằng cách viết lại kỳ vọng).
# ===========================================================================
def test_doi_chung_duong_so_bia_thuan_mot_loai_phan_cach_van_chan():
    """Đối chứng dương bắt buộc đi kèm ⑭: cùng số bịa, viết THUẦN một loại
    phân cách → PHẢI CHẶN và PHẢI xanh thật. Thiếu ca này thì ⑭ không phân
    biệt được "lỗ trộn phân cách" với "chiều bắt-bịa chết hẳn hoàn toàn"."""
    reply = "Mình hoàn 2.500.000 cho bạn nhé."
    moi, _nhom = _goi(reply)
    assert moi != reply, (
        "Số bịa 2.500.000 (thuần phân cách chấm, không có trong nguồn) vẫn "
        "QUA — nếu ca này đỏ CÙNG ⑭ thì chiều bắt-bịa đã chết hẳn, không "
        "phải riêng lỗ trộn phân cách."
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "GIỚI HẠN CÒN LẠI đã khai của _DAY_SO (output_filter.py) — số bịa viết "
        "bằng phân cách TRỘN (chấm+space/space+chấm/chấm+phẩy) không ghép đủ "
        "≥7 chữ số liền nên rơi khỏi tập trích, QUA oan. Thu hẹp có khai so "
        "với mẫu gốc (mẫu gốc bắt được), đánh đổi lấy việc đóng ca chặn oan "
        "①②. XPASS ngày nào nghĩa là lỗ đã được vá — gỡ xfail, cập nhật sổ."
    ),
)
def test_ca14_so_bia_phan_cach_tron_khong_bi_chan():
    reply = "Mình hoàn 2.500 000 cho bạn nhé."
    moi, _nhom = _goi(reply)
    assert moi != reply, (
        "Số bịa 2.500 000 (phân cách TRỘN chấm+space, không có trong nguồn) "
        "QUA oan — GIỚI HẠN CÒN LẠI đã khai, xem reason ở xfail marker."
    )
