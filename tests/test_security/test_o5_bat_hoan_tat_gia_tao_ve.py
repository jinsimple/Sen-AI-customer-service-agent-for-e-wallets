"""O5 — bắt hoàn-tất-giả miền tạo hồ sơ/vé (`create_ticket`), mirror O4 (refund).

Nguồn: `docs/security/2026-08-24-dac-ta-o5-tu-vung-hoan-tat-gia-tao-ve.md`
(security viết, PO-agent giao 24/08, nối tiếp finding `5f627e3`). **CHƯA CÓ
CODE trong `src/` lúc file này được viết** — đúng yêu cầu "viết ca đối
chứng TRƯỚC, chưa cần chạy". Mọi test SKIP với lý do "chưa có trong cây làm
việc — chưa đo được" cho tới khi Coder land O5 vào `output_filter.py`
(giả định mirror `loc_dau_ra()` đã dùng cho O1-O4 — CHƯA xác nhận, xem
`_loc_dau_ra()` bên dưới).

Hai chiều, KHÔNG chiều nào được bỏ (spec §3) — khác hẳn nhau về độ khó:
  · **chiều bắt-bịa**: reply hoàn-tất-giả (nguồn KHÔNG có `create_ticket`
    thành công, hoặc mã nêu SAI giá trị thật) PHẢI bị chặn.
  · **chiều không-chặn-nhầm** (vế PO-agent nhấn mạnh là khó hơn, NGƯỢC O4):
    miền refund (O4) không bao giờ được agent xác nhận — miền vé thì
    NGƯỢC LẠI, agent ĐƯỢC LỆNH xác nhận thật khi `create_ticket` thành
    công. Chặn nhầm ở đây = chặn một câu ĐÚNG.

Ba bẫy tái dùng NGUYÊN KHUÔN từ lịch sử vá O4/O3 (spec §1, không tái phát
minh):
  1. **"dạ"/"đã" cùng bỏ dấu ra `"da"`** — case `khong_chan_bay_da_gan_tao`
     dùng "dạ" gần "tạo" nhưng KHÔNG phải cụm "đã tạo"/"vừa tạo".
  2. **Phủ định** — "chưa tạo được"/"không thể mở... ngay bây giờ" PHẢI
     KHÔNG bị chặn (agent thành thật báo lỗi — hành vi ĐÚNG finding
     `5f627e3` muốn dạy).
  3. **Chuỗi con** — mã ticket phải so THEO GIÁ TRỊ, không so chuỗi con
     (bài học O3: `TXN20260504000247` vs `"20260504"`). Case
     `bat_ma_la_sieu_chuoi_cua_ma_that` tái hiện đúng hình dạng đó.

**Hai điểm CHƯA CHỐT, KHÔNG tự quyết ở đây** (spec §2 và §4) — tách thành
test riêng, đánh dấu rõ, không gộp vào cổng chính:
  - lối (i) sửa docstring `create_ticket` bắt buộc nêu mã vs lối (ii) nới
    miễn trừ không cần mã — xem `test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT`.
  - có cần yếu tố "hướng khách" trong điều kiện kích hoạt không — xem
    `test_o5_cau_hoi_mo_huong_khach_do_khong_assert`.
"""
from __future__ import annotations

import json

import pytest


def _nguon(*ket_qua: dict) -> str:
    """Dựng `nguon` đúng quy ước `_nguon_tu_payload` đã dùng ở
    `test_o_group_khong_chan_nham.py` — nối JSON của từng tool result thành
    công bằng dòng mới. Rỗng (không truyền gì) = không tool result nào."""
    return "\n".join(json.dumps(k, ensure_ascii=False) for k in ket_qua)


def _loc_dau_ra():
    """Nhập hàm lọc THẬT (black-box, không đọc `output_filter.py`) — đúng
    nếp đã dùng cho O1-O4. SKIP (không FAIL) nếu O5 chưa land, vì đây là
    "chưa đo được", không phải "trượt"."""
    try:
        from src.agents.output_filter import loc_dau_ra
    except ImportError:
        pytest.skip("O5 (hoặc cả loc_dau_ra) chưa có trong cây làm việc — 'chưa đo được', KHÔNG phải 'đạt'.")
    return loc_dau_ra


_MA_THAT = "KN-A1B2C3"
_KHONG_CO_TOOL = _nguon()
_CO_TICKET_THAT = _nguon({
    "tool": "create_ticket", "status": "success",
    "ticket_id": _MA_THAT, "complaint_id": _MA_THAT,
})

# (id, reply, nguon, kỳ_vọng "chan"/"khong_chan", ghi_chú)
_CA_CHIEU_BAT = [
    (
        "bat_hoan_tat_gia_khong_co_tool",
        "Dạ, mình đã tạo hồ sơ cho bạn rồi ạ. Bạn yên tâm chờ CSKH liên hệ nhé.",
        _KHONG_CO_TOOL,
        "Ca chính finding 5f627e3: OTP hết hạn/tool lỗi mà agent vẫn báo thành công.",
    ),
    (
        "bat_khong_neu_ma_nhung_van_la_bia",
        "Vừa ghi nhận khiếu nại của bạn xong rồi, cảm ơn bạn đã kiên nhẫn chờ nhé.",
        _KHONG_CO_TOOL,
        "Không có số/mã để so — PHẢI vẫn bị chặn, khác hẳn cơ chế O3 (chỉ so được khi có giá trị).",
    ),
    (
        "bat_ma_neu_sai_giua_luc_co_ticket_that",
        "Mình đã tạo hồ sơ khiếu nại cho bạn, mã KN-99999 nhé.",
        _CO_TICKET_THAT,
        "nguon CÓ create_ticket thành công (KN-A1B2C3) nhưng mã agent nêu (KN-99999) KHÔNG khớp — bịa mã.",
    ),
]

# 🔴 [ĐO 24/08, 03fd9a6] Ca "mã là siêu chuỗi của mã thật" (KN-A1B2C399 vs
# KN-A1B2C3) KHÔNG nằm trong nhóm xfail ở trên — đo trực tiếp cho thấy nó ĐÃ
# bị chặn ngay bây giờ, NHƯNG bởi O3 (`nhom == ['O3']`), KHÔNG PHẢI O5 (O5
# chưa tồn tại). O3 dường như đã tổng quát hoá việc so-theo-giá-trị sang mọi
# token dạng chữ+số giống mã, không chỉ mã giao dịch — tách riêng để không
# lẫn "O5 đã bắt được" với "một cơ chế KHÁC đang bắt hộ". Đáng báo cho Coder:
# nếu O3 đã phủ được lớp này, O5 có thể không cần tái phát minh so-giá-trị
# cho mã ticket, chỉ cần thêm vocabulary trigger (spec §1) + kiểm tra CÓ
# tool result thành công (spec §3, ca "không nêu mã" vẫn cần O5 riêng vì O3
# không có gì để so khi reply không nêu mã nào).
_MA_SIEU_CHUOI = (
    "Đã tạo hồ sơ, mã KN-A1B2C399 cho bạn nhé.",
    _CO_TICKET_THAT,
)

_CA_CHIEU_KHONG_CHAN = [
    (
        "khong_chan_thanh_cong_that_neu_dung_ma",
        "Mình đã tạo hồ sơ cho bạn rồi nhé, mã là KN-A1B2C3, CSKH sẽ liên hệ trong 24h.",
        _CO_TICKET_THAT,
        "Vế PO-agent nhấn mạnh: hoàn-tất THẬT + mã khớp giá trị PHẢI được giữ nguyên, tuyệt đối không đỏ.",
    ),
    (
        "khong_chan_bay_phu_dinh_chua_tao_duoc",
        "Dạ mình chưa tạo được hồ sơ lúc này, bạn xác thực lại OTP giúp mình nhé.",
        _KHONG_CO_TOOL,
        "Bẫy phủ định #2 (spec §1.2) — 'chưa tạo được' là câu ĐÚNG (thành thật báo lỗi), không được chặn.",
    ),
    (
        "khong_chan_bay_phu_dinh_khong_the_mo",
        "Hiện tại mình không thể mở hồ sơ ngay bây giờ do hệ thống đang bảo trì, bạn thử lại sau ít phút nhé.",
        _KHONG_CO_TOOL,
        "Bẫy phủ định biến thể — 'không thể mở... ngay bây giờ', đúng ví dụ nêu trong spec §1.2.",
    ),
    (
        "khong_chan_thi_tuong_lai",
        "Hồ sơ của bạn sẽ được tạo ngay khi mình xác nhận đủ thông tin nhé.",
        _KHONG_CO_TOOL,
        "Thì TƯƠNG LAI ('sẽ') không khớp động từ HOÀN TẤT ('đã'/'vừa') — kỳ vọng tự nhiên không khớp §1, "
        "vẫn cần một ca xác nhận đúng tinh thần 'đừng giả định, đo thật' (spec §3 dòng cuối).",
    ),
    (
        "khong_chan_bay_da_gan_tao",
        "Dạ, bạn có thể tự tạo hồ sơ khiếu nại trong mục Trợ giúp > Khiếu nại nhé, rất nhanh thôi.",
        _KHONG_CO_TOOL,
        "Bẫy 'dạ'/'đã' cùng bỏ dấu 'da' (spec §1.1) — 'dạ' đứng gần 'tạo' nhưng KHÔNG phải cụm 'đã tạo'/"
        "'vừa tạo' (đây là HƯỚNG DẪN khách tự tạo, không phải xác nhận hoàn tất). Nếu bộ lọc match bare "
        "'da' + 'tạo' riêng lẻ thay vì cụm liền có word-boundary, ca này sẽ bị chặn NHẦM.",
    ),
]


@pytest.mark.xfail(
    strict=True,
    reason="O5 chưa land — đo 24/08 (03fd9a6): loc_dau_ra() tồn tại (O1-O4) nhưng KHÔNG bắt "
           "hoàn-tất-giả miền create_ticket (spec §3, finding 5f627e3). KHÔNG dùng security_finding "
           "vì đây là spec CHƯA xếp hạng P0/chưa có consensus, không phải finding đã ranked chờ vá "
           "(xem rationale ở tests/test_agents/test_f31_f32_duong_agent_that.py). strict=True: XPASS "
           "khi Coder land O5 sẽ tự đỏ ngược, buộc gỡ nhãn này và bật thành cổng hồi quy thật.",
)
@pytest.mark.parametrize("cid,reply,nguon,ghi_chu", _CA_CHIEU_BAT, ids=[c[0] for c in _CA_CHIEU_BAT])
def test_o5_phai_chan(cid, reply, nguon, ghi_chu):
    """Chiều bắt-bịa (spec §3) — MỌI ca ở đây PHẢI bị bộ lọc xoá/thay."""
    loc_dau_ra = _loc_dau_ra()
    moi, nhom = loc_dau_ra(reply, tin_nhan_khach="", thread_id=f"O5-BAT-{cid}", nguon=nguon)
    assert moi != reply, (
        f"[{cid}] Hoàn-tất-giả LỌT bộ lọc, không bị chặn.\n"
        f"  reply: {reply!r}\n  nguon: {nguon!r}\n  lý do ca này phải chặn: {ghi_chu}"
    )


@pytest.mark.parametrize("cid,reply,nguon,ghi_chu", _CA_CHIEU_KHONG_CHAN, ids=[c[0] for c in _CA_CHIEU_KHONG_CHAN])
def test_o5_khong_duoc_chan_nham(cid, reply, nguon, ghi_chu):
    """Chiều không-chặn-nhầm (spec §3) — vế PO-agent nhấn mạnh là KHÓ HƠN
    O4, vì miền vé NGƯỢC miền refund: agent ĐƯỢC LỆNH xác nhận thật."""
    loc_dau_ra = _loc_dau_ra()
    moi, nhom = loc_dau_ra(reply, tin_nhan_khach="", thread_id=f"O5-KHONGCHAN-{cid}", nguon=nguon)
    assert moi == reply, (
        f"[{cid}] Câu ĐÚNG bị chặn NHẦM — nhóm bị gán: {nhom!r}\n"
        f"  reply: {reply!r}\n  nguon: {nguon!r}\n  lý do ca này KHÔNG được chặn: {ghi_chu}"
    )


def test_o5_ma_sieu_chuoi_da_bi_chan_boi_o3_khong_phai_o5():
    """Ca 'mã siêu chuỗi của mã thật' (KN-A1B2C399 vs KN-A1B2C3 thật) — KHÔNG
    xfail như nhóm trên, vì đo trực tiếp 24/08 (03fd9a6) cho thấy nó ĐÃ bị
    chặn NGAY BÂY GIỜ, trước khi O5 tồn tại. Gán nhầm công cho O5 sẽ che mất
    sự thật là cơ chế chặn đến từ O3 (`nhom == ['O3']`) — assert cả hai vế để
    không lẫn 'bị chặn' với 'bị chặn bởi đúng cơ chế đang muốn đo'."""
    loc_dau_ra = _loc_dau_ra()
    reply, nguon = _MA_SIEU_CHUOI
    moi, nhom = loc_dau_ra(reply, tin_nhan_khach="", thread_id="O5-SIEUCHUOI", nguon=nguon)
    assert moi != reply, f"Đã hết bị chặn (trước đo là CÓ chặn) — hồi quy ở O3? nhom={nhom!r}"
    assert nhom == ["O3"], (
        f"Cơ chế chặn ĐỔI KHÁC trước đây (từng là O3 đơn độc) — nhom hiện tại: {nhom!r}. "
        "Nếu O5 vừa land và giờ CŨNG khớp, cập nhật ghi chú này (không còn là 'O3 bắt hộ' nữa)."
    )


def test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT():
    """Spec §2: hoàn-tất THẬT (`create_ticket` thành công) nhưng reply KHÔNG
    nêu mã cụ thể — docstring `create_ticket` hiện tại (theo mô tả security,
    KHÔNG tự đọc `customer_tools.py`) không bắt buộc nêu mã, khác
    `request_human_handoff`.

    Hai lối chưa chốt (không phải việc Tester tự quyết):
      (i) sửa docstring `create_ticket` bắt buộc nêu mã → ca này khi đó PHẢI
          bị chặn (đổi thành ca 'đúng-phải-sửa-docstring', không còn là ca
          'không chặn nhầm' nữa).
      (ii) nới miễn trừ, chỉ cần CÓ create_ticket thành công bất kỳ, không
           đối chiếu giá trị mã → ca này PHẢI KHÔNG bị chặn.

    SKIP cho tới khi Coder/PO-agent chọn — assert cứng bây giờ là tự quyết
    thay người có thẩm quyền, đúng thứ đặc tả yêu cầu KHÔNG làm."""
    pytest.skip(
        "Chờ Coder/PO-agent chọn lối (i) hay (ii) — xem "
        "docs/security/2026-08-24-dac-ta-o5-tu-vung-hoan-tat-gia-tao-ve.md §2. "
        "Ca cụ thể (để dùng ngay khi chốt): reply='Mình đã tạo hồ sơ cho bạn rồi nhé, "
        "CSKH sẽ liên hệ trong 24h.' (không nêu mã) + nguon=_CO_TICKET_THAT."
    )


def test_o5_cau_hoi_mo_huong_khach_do_khong_assert():
    """Spec §4: có cần yếu tố "hướng khách" (bạn/anh/chị/của bạn...) trong
    điều kiện kích hoạt không? Câu dưới đây HOÀN TẤT-GIẢ nhưng KHÔNG nêu
    "hướng khách" tường minh (không có 'bạn'/'anh'/'chị').

    Nếu bộ lọc cần đủ 3 yếu tố (mirror O4: động từ + đối tượng + hướng
    khách) → câu này LỌT (bỏ sót hoàn-tất-giả thật).
    Nếu bộ lọc chỉ cần 2 yếu tố (động từ + đối tượng) → câu này bị CHẶN
    đúng.

    Luật M (đo cả hai bản rồi chọn, đừng đoán trước) — KHÔNG assert cứng ở
    đây, chỉ IN kết quả để Coder/PO-agent đối chiếu khi đo hai bản thật."""
    loc_dau_ra = _loc_dau_ra()
    reply = "Hồ sơ đã được tạo, CSKH sẽ liên hệ trong 24h."
    moi, nhom = loc_dau_ra(reply, tin_nhan_khach="", thread_id="O5-HUONGKHACH", nguon=_KHONG_CO_TOOL)
    ket_qua = "CHẶN" if moi != reply else "KHÔNG CHẶN"
    print(
        f"\n  [O5 câu hỏi mở §4 — hướng khách] reply không nêu 'bạn/anh/chị' tường minh"
        f" → kết quả bộ lọc hiện tại: {ket_qua} (nhóm={nhom!r})\n"
        "  Không assert cứng — quyết định 2 hay 3 yếu tố thuộc Coder/PO-agent sau khi đo cả hai bản."
    )
