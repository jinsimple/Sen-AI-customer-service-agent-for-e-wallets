"""Lọc ĐẦU RA O1–O4 — lưới cuối, chạy trên `reply` trước khi trả về khách.

NGUYÊN TẮC BẤT ĐỐI XỨNG (security §4.1, đừng chép nhầm từ chỗ khác):
với scrub PII ĐẦU VÀO dự án đã chốt "che nhầm còn hơn để lọt". Nguyên tắc đó
**KHÔNG chuyển sang đây**. Ở đầu ra, một dương tính giả âm thầm thay câu trả
lời ĐÚNG bằng câu mẫu — tức làm hỏng đúng thứ khách cần. Nên lọc đầu ra phải
**HẸP MÀ CHẮC**; phần rộng để guardrail đếm tín hiệu theo thread lo (nó chỉ
đếm, không chặn câu).

Hệ quả trực tiếp lên cách viết: mỗi nhóm dưới đây đều được thiết kế để **bỏ
sót có kiểm soát** hơn là bắt nhầm. Ai muốn siết rộng hơn phải mang số ca âm
tính tới trước.
"""
from __future__ import annotations

import logging
import re
import unicodedata

from src.services import thread_signals

_logger = logging.getLogger("fin05.output_filter")

CAU_AN_TOAN = (
    "Xin lỗi, phần này mình không trả lời trực tiếp được. Để đảm bảo an toàn "
    "thông tin cho bạn, mình chuyển sang chuyên viên hỗ trợ nhé."
)


def _bo_dau(t: str) -> str:
    t = t.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------- O1
# Ngưỡng/tín hiệu NỘI BỘ. Hẹp: chỉ mã và tên biến có hình dạng đặc thù, không
# đoán theo ngữ nghĩa.
_O1_MA = [
    re.compile(r"\bFS-\d+\b", re.IGNORECASE),
    re.compile(r"\bOTP_[A-Z_]{3,}\b"),
    re.compile(r"\b(RESOLUTION_APPROVAL_OTP_FRESH_MINUTES|OTP_VIEW_MAX_MINUTES|OTP_STEPUP_FRESH_MINUTES)\b"),
]
# Con số hiệu lực OTP — CHỈ tính khi câu đang nói về OTP. "15 phút" trong câu
# nói về thời gian tra soát là vô hại; cùng con số đó cạnh chữ OTP là lộ cấu hình.
_O1_SO_OTP = re.compile(r"\b(12\s*(gio|tieng)|15\s*phut|10\s*phut)\b")


def _khop_o1(reply: str) -> bool:
    if any(r.search(reply) for r in _O1_MA):
        return True
    sach = _bo_dau(reply)
    return "otp" in sach and bool(_O1_SO_OTP.search(sach))


# ---------------------------------------------------------------- O2
# CỐ Ý HẸP, và tôi nói thẳng giới hạn: "liệt kê >=2 quy tắc nội bộ liền nhau"
# không có định nghĩa máy kiểm được nếu không so với chính prompt. Ở đây chỉ bắt
# việc nhắc lại NGUYÊN VĂN các cụm đặc thù của prompt nội bộ. Phần suy diễn
# (paraphrase) KHÔNG bắt — để guardrail đếm theo thread lo, đúng nguyên tắc
# hẹp-mà-chắc. Đừng đọc sự tồn tại của O2 thành "đã phủ mọi cách lộ chỉ thị".
_O2_CUM_NOI_BO = [
    "rang buoc bat buoc",
    "quy trinh dieu tra",
    "khong bao gio duoc",
    "ban la tro ly ao cua",
]


def _khop_o2(reply: str) -> bool:
    sach = _bo_dau(reply)
    return sum(1 for c in _O2_CUM_NOI_BO if c in sach) >= 2


# ---------------------------------------------------------------- O3
# CÓ ĐIỀU KIỆN: phần B chỉ chạy khi phần A bật. Vi phạm oracle KHÔNG phải thuộc
# tính từ vựng của câu trả lời — nó là thuộc tính của CẶP (phỏng đoán của khách
# ↔ câu trả lời). Cùng chữ "chính xác" vô hại khi khách hỏi số tiền, và là rò rỉ
# khi khách vừa đọc một dãy số bị che.
_A_DAY_SO = re.compile(r"\d{4,}")
_A_TEN_RIENG = re.compile(r"\b[A-ZĐÀ-Ỹ][a-zà-ỹ]+(\s+[A-ZĐÀ-Ỹ][a-zà-ỹ]+){1,}\b")
_A_HOI_XAC_NHAN = [
    "co phai", "dung khong", "phai khong", "hay la", "dung/sai", "dung hay sai",
    "gan dung", "xac nhan giup", "co dung", "phai vay khong",
]
# B — chỉ tính khi cụm khẳng định/phủ định ĐỨNG NHƯ MỘT MỆNH ĐỀ TRẢ LỜI, tức mở
# đầu một mệnh đề. "không có giao dịch nào chính xác với 500k" KHÔNG khớp vì
# "chính xác" nằm giữa mệnh đề, không phải câu trả lời đúng/sai.
_B_KHANG_DINH = ["dung roi", "chinh xac", "vang", "phai roi", "khong phai", "sai roi", "gan dung"]


def _tach_menh_de(t: str) -> list[str]:
    return [m.strip() for m in re.split(r"[,.;:!?\n]+", t) if m.strip()]


def _a_la_phong_doan(tin_nhan_khach: str) -> bool:
    if not tin_nhan_khach:
        return False
    co_du_lieu = bool(_A_DAY_SO.search(tin_nhan_khach)) or bool(_A_TEN_RIENG.search(tin_nhan_khach))
    sach = _bo_dau(tin_nhan_khach)
    co_hoi = any(k in sach for k in _A_HOI_XAC_NHAN)
    return co_du_lieu and co_hoi


def _khop_o3(reply: str, tin_nhan_khach: str) -> bool:
    # Không điều kiện: dãy >=7 chữ số liền trong reply.
    if re.search(r"\d{7,}", reply):
        return True
    if not _a_la_phong_doan(tin_nhan_khach):
        return False
    for md in _tach_menh_de(_bo_dau(reply)):
        if any(md.startswith(k) for k in _B_KHANG_DINH):
            return True
    return False


# ---------------------------------------------------------------- O4
# THEO CỤM, không theo từ: chỉ khớp khi đủ BA yếu tố TRONG CÙNG MỘT MỆNH ĐỀ.
# "chắc chắn sẽ được hoàn cho bạn" khớp; "nếu muốn biết chắc chắn thì liên hệ
# CSKH" không khớp vì thiếu đối tượng tiền và không hướng về case của khách.
_O4_DONG_TU = ["se ", "chac chan", "dam bao", "cam ket"]
_O4_TIEN = ["hoan tien", "hoan lai", "hoan", "tra lai", "boi hoan"]
_O4_HUONG_KHACH = ["ban", "anh", "chi", "minh", "cua ban", "quy khach"]


def _khop_o4(reply: str) -> bool:
    for md in _tach_menh_de(_bo_dau(reply)):
        if (
            any(v in md for v in _O4_DONG_TU)
            and any(t in md for t in _O4_TIEN)
            and any(h in md for h in _O4_HUONG_KHACH)
        ):
            return True
    return False


# ---------------------------------------------------------------- công khai
def loc_dau_ra(
    reply: str,
    *,
    tin_nhan_khach: str = "",
    thread_id: str = "",
    correlation_id: str | None = None,
) -> tuple[str, list[str]]:
    """Trả (reply_da_loc, danh_sach_nhom_khop).

    Khớp -> THAY bằng câu an toàn có nghĩa, KHÔNG im lặng cắt bỏ: khách nhận câu
    cụt còn khó hiểu hơn bị từ chối tử tế.
    """
    if not reply:
        return reply, []

    khop = []
    if _khop_o1(reply):
        khop.append("O1")
    if _khop_o2(reply):
        khop.append("O2")
    if _khop_o3(reply, tin_nhan_khach):
        khop.append("O3")
    if _khop_o4(reply):
        khop.append("O4")

    if not khop:
        return reply, []

    # Log CÓ CẤU TRÚC, KHÔNG log nguyên văn reply: reply khớp O3 gần như chắc
    # chắn chứa dữ liệu bị che — log nó ra là tự tay làm rò đúng thứ vừa chặn.
    _logger.warning(
        "output_filter_khop",
        extra={
            "nhom": ",".join(khop),
            "correlation_id": correlation_id,
            "do_dai_reply": len(reply),
        },
    )
    # Đếm theo thread — dùng CHUNG hạ tầng với ES-xx (5a) và guardrail 5c.
    # Nhiều lần khớp trong một hội thoại chính là dấu hiệu Crescendo đang chạy.
    if thread_id:
        for nhom in khop:
            thread_signals.tang(f"OUT-{nhom}", thread_id)

    return CAU_AN_TOAN, khop


# ---------------------------------------------------------------- O2-B: ĐẾM
# MẬT ĐỘ LIỆT KÊ — ĐẾM, KHÔNG CHẶN (security quyết, PO duyệt).
#
# Giải đúng chỗ tôi từng nói "không định nghĩa máy-kiểm-được": thay vì so ngữ
# nghĩa với prompt (bất khả), ĐẾM SỐ CHỦ ĐỀ quy tắc KHÁC NHAU xuất hiện trong
# một reply, qua danh sách mỏ neo CỐ ĐỊNH.
#
# Vì sao ngưỡng 3 chứ không phải 1: ràng buộc 7 cấm LIỆT KÊ BỘ quy tắc, KHÔNG
# cấm tiết lộ MỘT giới hạn. Agent còn được LỆNH nói ra giới hạn của mình (ràng
# buộc 1+8) — "mình không tự quyết được việc hoàn tiền" là câu ĐÚNG NGHIỆP VỤ,
# phải nói. 1-2 mỏ neo = giải thích bình thường; >=3 trong một reply = hành vi
# đọc thuộc lòng nội quy, đó mới là thứ đáng đếm.
#
# ĐẾM chứ không CHẶN: chặn ở đây là chặn đúng câu agent giải thích giới hạn cho
# khách — hỏng khả dụng ngay chỗ sản phẩm cần nhất. Nhiều lần đếm trong một hội
# thoại mới là tín hiệu (Crescendo moi dần), và đó là việc của guardrail
# đếm-theo-thread, không phải của bộ lọc câu.
_MO_NEO_QUY_TAC = {
    "khong_quyet_tien": ["khong tu quyet", "khong the tu duyet", "phai co nguoi duyet", "khong duoc hoan tien truc tiep"],
    "khong_bia_so": ["khong bia", "chi dua tren du lieu", "phai tra cuu duoc"],
    "pdpa_ben_thu_ba": ["thong tin nguoi khac", "ben thu ba", "khong cung cap thong tin ca nhan"],
    "khong_ket_luan_gian_lan": ["khong ket luan gian lan", "khong khang dinh la lua dao"],
    "otp": ["khong hoi mat khau", "khong hoi otp giao dich", "otp phien"],
    "phan_loai": ["4 loai khieu nai", "phan loai khieu nai", "pham vi giao dich"],
    "tai_lieu_tham_khao": ["chi la tham khao", "tai lieu tham khao"],
    "xung_ai": ["toi la tro ly ao", "minh la tro ly ao", "toi la ai"],
    "khong_tiet_lo_huong_dan": ["khong the chia se huong dan", "khong tiet lo quy trinh noi bo"],
}
NGUONG_LIET_KE = 3


def dem_mat_do_liet_ke(reply: str) -> int:
    """Số CHỦ ĐỀ quy tắc khác nhau trong reply. Không chặn, chỉ đếm."""
    sach = _bo_dau(reply)
    return sum(1 for cum in _MO_NEO_QUY_TAC.values() if any(m in sach for m in cum))
