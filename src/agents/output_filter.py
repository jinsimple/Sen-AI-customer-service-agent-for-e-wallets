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
# Ngu canh kich hoat cho con so hieu luc: khong chi chu "otp". "Ma duyet cua sep
# het han 10 phut" khong co chu OTP nhung lo dung con so cau hinh
# RESOLUTION_APPROVAL_OTP_FRESH_MINUTES.
_O1_NGU_CANH_MA = ["otp", "ma duyet", "ma xac nhan", "phe duyet", "ma xac thuc"]
# NGUONG NOI BO dang "vuot nguong N trieu". Ca nay dac biet: 10 trieu la nguong
# SINH TRAC HOC (QD 2345/QD-NHNN), KHONG phai nguong gian lan — hien phap §8 ghi
# ro. Agent noi cau do vua ro cau hinh noi bo VUA SAI LUAT, nen chan la dung ca
# hai mat.
_O1_NGUONG_TIEN = re.compile(r"\b(vuot |tren |qua )?nguong\s*\d+\s*(trieu|tr|nghin|k)\b")


def _khop_o1(reply: str) -> bool:
    if any(r.search(reply) for r in _O1_MA):
        return True
    sach = _bo_dau(reply)
    if _O1_NGUONG_TIEN.search(sach):
        return True
    return any(k in sach for k in _O1_NGU_CANH_MA) and bool(_O1_SO_OTP.search(sach))


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
# Gom CA dang phu dinh: loai tru mot kha nang cung la MOT BIT oracle.
# "Khong phai 21 dau" thu hep khong gian doan y nhu "dung roi" xac nhan no.
_B_KHANG_DINH = [
    "dung roi", "chinh xac", "vang", "phai roi", "gan dung", "dung vay",
    "khong phai", "sai roi", "khong dung", "khong phai vay",
]


def _tach_menh_de(t: str) -> list[str]:
    return [m.strip() for m in re.split(r"[,.;:!?\n]+", t) if m.strip()]


def _a_la_phong_doan(tin_nhan_khach: str) -> bool:
    if not tin_nhan_khach:
        return False
    co_du_lieu = bool(_A_DAY_SO.search(tin_nhan_khach)) or bool(_A_TEN_RIENG.search(tin_nhan_khach))
    sach = _bo_dau(tin_nhan_khach)
    co_hoi = any(k in sach for k in _A_HOI_XAC_NHAN)
    return co_du_lieu and co_hoi


# LUAT XUAT XU — thay han danh sach tien to _MA_HE_THONG cua 7ee2ab5.
#
# Vi sao bo danh sach: no la DAP CHUOT. PO do ra hai lo chi trong mot vong:
#   - thieu "RC" -> RC00000051 (bien lai cua CHINH KHACH) bi chan oan
#   - smuggling: dan tien to chu vao so dien thoai ("SDT0387000001") la thoat
# Them RC vao danh sach chi va ca thu nhat va KHONG cham ca thu hai — ngay mai
# lai thieu mot tien to khac. Danh sach tien to hong theo ban chat: no chan theo
# HINH DANG, ma hinh dang thi ke tan cong chon duoc.
#
# Luat xuat xu chan theo NGUON: moi day >=7 chu so agent noi ra phai truy duoc
# ve mot ket qua tool cua luot nay, hoac ve chinh loi khach da go. Dong ca hai
# lo tren ma khong liet ke gi:
#   RC00000051 khach vua go -> co trong nguon -> QUA
#   SDT0387000001           -> SDT da bi scrub khoi tool result -> CHAN
# Va no TRUNG KHIT rang buoc cung 3 (so agent noi phai truy duoc toi tool that),
# nen mot phep kiem chan duoc ca ORACLE lan BIA SO.
#
# CA BIEN, ghi ro de khong ai "sua cho xanh": so agent TU CONG (tong hai giao
# dich) BI CHAN vi khong nguon nao chua no. Do la TINH NANG dung rang buoc 3.
_DAY_SO = re.compile(r"\d[\d.,\s]{5,}\d|\d{7,}")
# Ca OR-F03 cua tester: "43a5940" la LAT CAT cua tool_result_id "TR-43a5940ecd78"
# — dinh danh NOI BO cua bo do, khong bao gio duoc phat ra cho khach. No khong
# phai day so thuan (co chu xen giua) nen luat chi-soi-chu-so mu hoan toan voi no.
# Mo rong: moi TOKEN chu-so tron dai >=7 va CO it nhat mot chu so. Nguong 7 +
# bat buoc co chu so de tu tieng Viet thuong khong lot vao (khong tu nao vua dai
# >=7 vua chua chu so).
_TOKEN_MA = re.compile(r"[A-Za-z0-9]{7,}")


def _cac_day_so(text: str, *, cho_phep_phan_cach: bool = True) -> set[str]:
    """Mọi dãy số / mã trong text.

    `cho_phep_phan_cach` — KHÁC NHAU giữa VĂN XUÔI và JSON, và đây là chỗ dễ sai:

    · VĂN XUÔI (câu trả lời của agent, lời khách gõ): PHẢI cho phép, vì cùng một
      số viết mỗi nơi một kiểu — tool trả `262000`, người viết `262.000đ`.
    · JSON (payload tool): PHẢI CẤM. Dấu phẩy trong JSON là DẤU PHÂN CÁCH TRƯỜNG,
      không phải dấu ngăn hàng nghìn. Cho phép thì `{"amounts": [262000, 1100]}`
      bị gộp thành `2620001100` — một con số KHÔNG TỒN TẠI ở đâu cả, nhưng lại
      được nạp vào tập NGUỒN HỢP LỆ. Agent bịa đúng chuỗi đó là qua.
      Đo thật: đúng ca này LỌT ở bản 3e7ac21.
      Cùng họ bẫy F của tester (số bịa "truy vết được" nhờ trùng một mảnh của
      nguồn), nhưng vắt qua RANH GIỚI HAI TRƯỜNG thay vì nằm trong một giá trị.
    """
    ra = set()
    mau = _DAY_SO if cho_phep_phan_cach else re.compile(r"\d{7,}")
    for m in mau.finditer(text or ""):
        so = re.sub(r"[.,\s]", "", m.group())
        if len(so) >= 7:
            ra.add(so)
    for m in _TOKEN_MA.finditer(text or ""):
        tok = m.group()
        if any(c.isdigit() for c in tok):
            ra.add(tok.lower())
    return ra


def _khop_o3(reply: str, tin_nhan_khach: str, nguon: str, loi_khach: str = "") -> bool:
    # nguon = payload tool (JSON) -> trích NGHIÊM, không cho dấu phân cách gộp số.
    # loi_khach + tin_nhan_khach = văn xuôi -> trích THOÁNG, chấp nhận "262.000đ".
    hop_le = (
        _cac_day_so(nguon, cho_phep_phan_cach=False)
        | _cac_day_so(tin_nhan_khach)
        | _cac_day_so(loi_khach)
    )
    for so in _cac_day_so(reply):
        # SO THEO GIA TRI, KHONG so chuoi con — bay F cua tester.
        # Ban dau toi so `so in g or g in so` de "tool tra so dai hon ma agent
        # chi doc mot phan" van qua. Nhung chinh no mo mot cua BIA SO MOI:
        # "20260504" la CHUOI CON cua trans_id that TXN20260504000247, nen mot
        # con so agent bia ra van "truy vet duoc" chi vi no tinh co la tien to
        # cua mot ma that. Do that: LOT.
        # Bay B (dinh dang) va bay F (chuoi con) KEO NGUOC NHAU — noi de cuu B
        # lam do F, siet de cuu F lam do B. Loi ra: chuan hoa DINH DANG (bo dau
        # phan cach) de cuu B, nhung so KHOP TUYET DOI de dong F.
        if so not in hop_le:
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
# "du dieu kien duoc hoan" la CAM KET MAC AO DIEU KIEN: no khong hua thang
# nhung khach doc ra la "toi se duoc hoan". Ranh buoc cung 1 cam agent ket luan
# ve ket qua, ke ca gian tiep.
_O4_DONG_TU = ["se ", "chac chan", "dam bao", "cam ket", "du dieu kien", "duoc duyet"]
_O4_TIEN = ["hoan tien", "hoan lai", "hoan", "tra lai", "boi hoan", "nhan lai tien", "nhan duoc tien", "ve vi", "vao vi", "vao tai khoan"]
_O4_HUONG_KHACH = ["ban", "anh", "chi", "minh", "cua ban", "quy khach"]


# PHỦ ĐỊNH — vế tôi bỏ quên, và nó làm O4 phạt agent vì TUÂN LỆNH.
# Ràng buộc cứng 1 bắt agent phải nói "mình không tự quyết được việc hoàn tiền".
# Câu từ chối đó dùng ĐÚNG BỘ TỪ như câu cam kết, chỉ khác một chữ phủ định:
#     "chắc chắn bạn SẼ được hoàn"                        -> cam kết, phải chặn
#     "mình KHÔNG THỂ xác nhận chắc chắn bạn sẽ được hoàn" -> từ chối, phải cho qua
# Cụm 3-yếu-tố khớp y hệt nhau ở cả hai. Đo thật: 96/463 lần chặn là O4, và
# trong đó có những câu agent đang từ chối cam kết đúng như được lệnh.
# Đây đúng bẫy "ca âm tính số 1" mà security viết cho O2 — phạt agent vì tuân
# lệnh — chỉ là nó xuất hiện ở O4.
_O4_PHU_DINH = ["khong", "chua", "khong the", "chua the", "khong bao gio"]


def _vi_tri_dau(md: str, tokens: list[str]) -> int | None:
    """Vị trí sớm nhất của một token, khớp theo RANH GIỚI TỪ.

    Khớp chuỗi con là nguồn dương-tính-giả lớn nhất của O4, và nó âm thầm:
    `"hoan"` nằm gọn trong `"khoang"` (kh-OAN-g), nên câu vô hại "phản hồi lại
    bạn trong KHOẢNG thời gian đến 14/09" bị tính là có "đối tượng tiền". Bốn
    trong năm ca chặn nhầm còn lại đều do đúng chữ này.
    """
    vt = [m.start() for t in tokens for m in [re.search(rf"\b{re.escape(t.strip())}\b", md)] if m]
    return min(vt) if vt else None


def _khop_o4(reply: str) -> bool:
    for md in _tach_menh_de(_bo_dau(reply)):
        # Mệnh đề có phủ định -> BỎ QUA. Đánh đổi có chủ đích theo nguyên tắc
        # hẹp-mà-chắc của lọc đầu ra: bỏ sót một cam kết viết lắt léo còn hơn
        # xoá một câu từ chối đúng chuẩn mực. Cắt mệnh đề theo dấu câu nên
        # "không có gì phải lo, bạn chắc chắn sẽ được hoàn" vẫn bị bắt ở vế sau.
        if any(p in md for p in _O4_PHU_DINH):
            continue
        vt_dong_tu = _vi_tri_dau(md, _O4_DONG_TU)
        vt_tien = _vi_tri_dau(md, _O4_TIEN)
        vt_huong = _vi_tri_dau(md, _O4_HUONG_KHACH)
        if vt_dong_tu is None or vt_tien is None or vt_huong is None:
            continue
        # THỨ TỰ mới là thứ phân biệt LỜI HỨA với MÔ TẢ QUY TRÌNH — ba yếu tố có
        # mặt là chưa đủ:
        #   "bạn SẼ được HOÀN tiền"              -> động từ TRƯỚC tiền = lời hứa
        #   "quyết định HOÀN tiền SẼ phụ thuộc"  -> tiền TRƯỚC động từ = mô tả
        # Câu thứ hai là agent làm ĐÚNG ràng buộc cứng 1 (không hứa, chuyển
        # người quyết). Bản trước xoá nó — tức phạt agent vì tuân lệnh, đúng bẫy
        # "ca âm tính số 1" mà security viết cho O2, tái xuất ở O4.
        if vt_dong_tu < vt_tien:
            return True
    return False


# ---------------------------------------------------------------- công khai
def loc_dau_ra(
    reply: str,
    *,
    nguon: str,
    tin_nhan_khach: str = "",
    loi_khach: str = "",
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
    if _khop_o3(reply, tin_nhan_khach, nguon, loi_khach):
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
