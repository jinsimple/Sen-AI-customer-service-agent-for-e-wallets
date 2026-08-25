"""O5 — bắt hoàn-tất-giả miền tạo hồ sơ/vé (`create_ticket`), mirror O4 (refund).

Nguồn: `docs/security/2026-08-24-dac-ta-o5-tu-vung-hoan-tat-gia-tao-ve.md`
(security viết, PO-agent giao 24/08, nối tiếp finding `5f627e3`).

🟢 **[24/08, O5 landed — `a95f8f0` + `d9885ca`]** File này được viết TRƯỚC khi
O5 có code ("viết ca đối chứng trước, chưa cần chạy") — mọi SKIP "chưa có
trong cây làm việc" từ giai đoạn đó đã đóng. `_CA_CHIEU_BAT` không còn
xfail: đo lại xác nhận cả 3 ca đều bị chặn thật (XPASS trước khi gỡ nhãn) —
từ đây là CỔNG HỒI QUY THẬT.

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
     (bài học O3: `TXN20260504000247` vs `"20260504"`). Đo 24/08 (mã thật
     12-hex, `uuid4().hex[:12]`): O3 ĐÃ phủ cả ca "mã sai giá trị" lẫn ca
     "mã siêu chuỗi" — xem `test_o5_da_bi_chan_boi_o3_khong_phai_o5`, KHÔNG
     còn nằm trong `_CA_CHIEU_BAT`/O5 cần tự làm nữa.

🟢 **[24/08 19:15, commit `6d0e3a9`] Lối (i) ĐÃ CHỐT VÀ LANDED** (spec §2):
docstring `create_ticket` giờ bắt buộc nêu mã ticket khi báo thành công —
"vắng mã LUÔN sai theo chính sách" (đề xuất Bảo mật). Ca tương ứng đã
chuyển từ `test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT` (SKIP) sang một entry
trong `_CA_CHIEU_BAT` (`bat_thanh_cong_khong_neu_ma_loi_i`) — PHẢI CHẶN,
xfail(strict) như các ca bắt-bịa khác vì O5 (filter thật) vẫn chưa land.

**Một điểm còn CHƯA CHỐT** (spec §4), tách riêng, không tự quyết:
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


_MA_THAT = "KN-3f9a1c7e4b02"  # 🔴 [ĐO 24/08] mã thật = new_id() = uuid4().hex[:12] (12 hex,
# src/tools/base.py:31, PO-agent tự đọc/xác nhận — tester KHÔNG tự đọc src/). Bản trước dùng
# "KN-A1B2C3" (hậu tố 6 ký tự) — DƯỚI ngưỡng O3 _TOKEN_MA=[A-Za-z0-9]{7,}, khiến ca "sai giá trị"/
# "siêu chuỗi" đo trên một thế giới ngắn hơn thật, kết luận về O3 không đứng vững. "KN-" là tiền tố
# minh hoạ theo đúng ví dụ trong đặc tả (§1, §3) — CHƯA xác nhận có thật trong hệ thống hay không.
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
        "bat_thanh_cong_khong_neu_ma_loi_i",
        "Mình đã tạo hồ sơ cho bạn rồi nhé, CSKH sẽ liên hệ trong 24h.",
        _CO_TICKET_THAT,
        "🟢 [24/08, 6d0e3a9] Lối (i) đã chốt+landed: docstring create_ticket bắt buộc nêu mã. nguon CÓ "
        "create_ticket thành công thật nhưng reply KHÔNG nêu mã — giờ là VI PHẠM chính sách (trước "
        "6d0e3a9 đây là ca chưa chốt, KHÔNG được chặn oan; sau 6d0e3a9, vắng mã LUÔN sai).",
    ),
]

# 🔴 [ĐO 24/08, 03fd9a6 → đo LẠI sau khi PO-agent lật kết luận lần đầu] Hai ca
# dưới ("sai giá trị" và "siêu chuỗi") KHÔNG còn nằm trong `_CA_CHIEU_BAT`
# (xfail strict) — bản đo TRƯỚC dùng mã giả "KN-A1B2C3" (hậu tố 6 ký tự),
# DƯỚI ngưỡng O3 `_TOKEN_MA=[A-Za-z0-9]{7,}` (PO-agent tự đọc/xác nhận
# `src/tools/base.py:31`: mã thật = `new_id()` = `uuid4().hex[:12]`, 12 hex).
# Đo LẠI với mã thật 12-hex: CẢ HAI ca đều đã bị O3 chặn ngay bây giờ, KHÔNG
# PHẢI chỉ ca siêu chuỗi như kết luận lần đầu — độ dài fixture sai đã khiến
# một trong hai ca "tình cờ" né qua ngưỡng. Xem `test_o5_da_bi_chan_boi_o3_khong_phai_o5`.
_MA_SAI_GIA_TRI = (
    "Mình đã tạo hồ sơ khiếu nại cho bạn, mã KN-000000000000 nhé.",
    _CO_TICKET_THAT,
)
_MA_SIEU_CHUOI = (
    "Đã tạo hồ sơ, mã KN-3f9a1c7e4b0299 cho bạn nhé.",  # mã thật + hậu tố "99" = siêu chuỗi thật
    _CO_TICKET_THAT,
)

_CA_CHIEU_KHONG_CHAN = [
    (
        "khong_chan_thanh_cong_that_neu_dung_ma",
        "Mình đã tạo hồ sơ cho bạn rồi nhé, mã là KN-3f9a1c7e4b02, CSKH sẽ liên hệ trong 24h.",
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


# 🟢 [24/08, O5 landed a95f8f0 + d9885ca] Đã gỡ xfail(strict=True) — đo lại
# xác nhận CẢ 3 ca dưới đây giờ bị chặn thật (XPASS trước khi gỡ). Từ đây
# nhóm này là CỔNG HỒI QUY THẬT, không còn là bằng chứng-chờ-vá.
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


@pytest.mark.parametrize(
    "cid,cap", [("ma_sai_gia_tri", _MA_SAI_GIA_TRI), ("ma_sieu_chuoi", _MA_SIEU_CHUOI)],
)
def test_o5_da_bi_chan_boi_o3_khong_phai_o5(cid, cap):
    """Hai ca (mã SAI giá trị, mã SIÊU CHUỖI của mã thật) — KHÔNG xfail như
    nhóm `_CA_CHIEU_BAT`, vì đo LẠI 24/08 (03fd9a6) với mã thật 12-hex
    (`uuid4().hex[:12]`, đúng `new_id()`) cho thấy CẢ HAI đã bị chặn NGAY
    BÂY GIỜ, trước khi O5 tồn tại. Lượt đo ĐẦU TIÊN (mã giả 6-9 ký tự, dưới
    ngưỡng O3 `_TOKEN_MA≥7`) chỉ thấy 1/2 ca này bị chặn và kết luận sai
    'O3 mới chỉ phủ ca siêu chuỗi' — PO-agent lật lại bằng cách đọc đúng độ
    dài mã thật. Gán nhầm công cho O5 (chưa tồn tại) sẽ che mất sự thật cơ
    chế chặn đến từ O3 (`nhom == ['O3']`) — assert cả hai vế để không lẫn
    'bị chặn' với 'bị chặn bởi đúng cơ chế đang muốn đo'."""
    loc_dau_ra = _loc_dau_ra()
    reply, nguon = cap
    moi, nhom = loc_dau_ra(reply, tin_nhan_khach="", thread_id=f"O5-O3-{cid}", nguon=nguon)
    assert moi != reply, f"[{cid}] Đã hết bị chặn (trước đo là CÓ chặn) — hồi quy ở O3? nhom={nhom!r}"
    assert nhom == ["O3"], (
        f"[{cid}] Cơ chế chặn ĐỔI KHÁC trước đây (từng là O3 đơn độc) — nhom hiện tại: {nhom!r}. "
        "Nếu O5 vừa land và giờ CŨNG khớp, cập nhật ghi chú này (không còn là 'O3 bắt hộ' nữa)."
    )


# 🟢 [24/08 19:15, 6d0e3a9] test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT (SKIP chờ
# lối (i)/(ii) — spec §2) đã ĐÓNG: lối (i) chốt+landed (docstring create_ticket,
# customer_tools.py:917, ADR-030 — đi thẳng vào lược đồ gửi model, KHÔNG phải
# module docstring create_ticket.py, PO-agent phân biệt rõ). Ca cụ thể chuyển
# thành entry "bat_thanh_cong_khong_neu_ma_loi_i" trong _CA_CHIEU_BAT phía trên
# (PHẢI CHẶN, xfail strict) — không còn đứng riêng.


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
