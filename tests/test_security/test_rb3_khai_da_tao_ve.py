"""RB3 (`khai_da_tao_ve`, output_filter.py) — cổng hồi quy thật cho matcher.

Trước 04/09 hàm này KHÔNG có test riêng nào (khác O2/O3/O5 đều có file test
độc lập) — đúng lỗ khiến false-positive lần hai (QA bắt qua T1-T5) không ai
bắt trước khi tới tay QA. File này đóng lỗ đó.

Nguồn ca: trao đổi Lead/Review/Coder 04/09 tối — Review thiết kế 9 case gốc
(8 ma trận + case va chạm "mà"/"mã"), Coder tự thêm 4 case đối kháng trước
khi land. Cả 13 case đã verify khớp bản code thật trước khi commit."""
from __future__ import annotations

import pytest

from src.agents.output_filter import claims_ticket_created

_CA_KHONG_CHAN = [
    ("ghi_nhan_thong_tin_khong_phai_khieu_nai",
     "Mình đã ghi nhận thông tin bạn vừa cung cấp, để mình tra tiếp nhé."),
    ("tiep_nhan_thong_tin_khong_phai_khieu_nai",
     "Mình đã tiếp nhận thông tin bạn báo, để mình kiểm tra kỹ hơn giúp bạn."),
    ("mem_tiep_dien_khong_ma_finding_qa_04_09",
     "Mình đã ghi nhận khiếu nại của bạn, đang xử lý tiếp."),
    ("va_cham_ma_lien_tu_voi_ma_ma_so",
     "Mình đã ghi nhận khiếu nại của bạn mà chưa rõ số tiền, đang xử lý tiếp nhé."),
    ("mem_thieu_doi_tuong_khieu_nai",
     "Mình đã ghi nhận yêu cầu của bạn, đang xử lý tiếp."),
    ("mo_ta_chung_khong_tinh_du_co_dong_tu_cung",
     "Trước đây mình đã tạo hồ sơ khiếu nại nhiều lần cho khách khác rồi."),
]

_CA_PHAI_CHAN = [
    ("hallucination_goc_25_08",
     "Đã tạo hồ sơ khiếu nại thành công với mã CMP-00003."),
    ("mem_co_ma_that_va_tiep_dien_ma_thang",
     "Mình đã ghi nhận khiếu nại của bạn với mã KN-00042, đang xử lý tiếp cho bạn nhé."),
    ("mem_khong_ma_khong_tiep_dien_mac_dinh_cu",
     "Mình đã ghi nhận khiếu nại của bạn, sẽ có nhân viên liên hệ sớm nhé."),
    ("cung_verb_khong_bi_tiep_dien_rua",
     "Đã tạo hồ sơ khiếu nại rồi, đang xử lý tiếp cho bạn."),
    ("mem_ma_o_xa_van_thang",
     "Mình đã tiếp nhận khiếu nại này, đang xử lý tiếp, mã KN-00099 đây bạn."),
    ("cung_verb_reply_global_2_cau_khong_bi_rua",
     "Đã tạo hồ sơ khiếu nại cho bạn. Mình đang xử lý tiếp các bước sau nhé."),
    ("mem_tu_ngay_mai_khong_phai_ma_that_van_mac_dinh_true",
     "Mình đã ghi nhận khiếu nại của bạn, ngày mai sẽ có người liên hệ."),
    # RB3 lần 3 (05/09, QA tái lập 2/2 lần thật, bước TRA CỨU, xem
    # tests/test_agents/test_rb3_gate_cau_truc.py) — matcher ĐÚNG khi đánh
    # giá RIÊNG câu này (đây LÀ một khai-đã-tạo/mã lẫn lộn thật: "Mã giao
    # dịch" của GIAO DỊCH + "đã ghi nhận" nói về TIỀN, không phải hồ sơ).
    # Cái SAI không nằm ở matcher — nằm ở việc RB3 gọi matcher cho một lượt
    # CHỈ lookup, không hề đề xuất tạo vé. Vá ở CỔNG (graph.py), KHÔNG vá
    # matcher — giữ case này ở `_CA_PHAI_CHAN` để khoá lại hiểu đúng đó,
    # tránh ai sau này "sửa" matcher theo hướng làm mất lớp bảo vệ cấu trúc.
    ("mem_de_nghi_hoi_y_lookup_step_rb3_lan_3",
     "Mình đã tra được đúng giao dịch bạn nói, bạn đối chiếu giúp mình nhé:\n\n"
     "- **Mã giao dịch:** TXN20260728000108\n"
     "- **Trạng thái phía hệ thống:** thành công — tiền đã ghi nhận chuyển vào ví người nhận\n\n"
     "Bạn cho mình xác nhận: mình tạo hồ sơ khiếu nại \"tiền chưa về\" cho giao dịch này "
     "để chuyển chuyên viên CSKH xử lý, được không ạ?"),
]


@pytest.mark.parametrize("cid,reply", _CA_KHONG_CHAN, ids=[c[0] for c in _CA_KHONG_CHAN])
def test_rb3_khong_duoc_chan_nham(cid, reply):
    assert claims_ticket_created(reply) is False, f"[{cid}] bắt oan: {reply!r}"


@pytest.mark.parametrize("cid,reply", _CA_PHAI_CHAN, ids=[c[0] for c in _CA_PHAI_CHAN])
def test_rb3_phai_chan(cid, reply):
    assert claims_ticket_created(reply) is True, f"[{cid}] bỏ sót: {reply!r}"
