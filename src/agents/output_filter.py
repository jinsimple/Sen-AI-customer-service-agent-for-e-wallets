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

import json
import logging
import re
import unicodedata

from src.agents import khop_cum as KC  # noqa: N812 — KC là bí danh CỐ Ý (module khớp-cụm dùng dày đặc, xem ADR-023)
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
# F-27 — NEO VÀO NGỮ CẢNH HẠN, KHÔNG neo vào từ khoá kỹ thuật.
# Bản trước đòi reply phải có chữ "otp"/"ma duyet" mới soi con số:
#   "Mã OTP duyệt hết hạn sau 10 phút"                  -> chặn
#   "Sếp duyệt phải xin mã riêng, hết hạn sau 10 phút"  -> LỌT
# Cùng một con số cấu hình (RESOLUTION_APPROVAL_OTP_FRESH_MINUTES), nhưng cách
# thứ hai mới là cách agent nói TỰ NHIÊN NHẤT — prompt còn dặn tránh thuật ngữ
# kỹ thuật. Mẫu neo vào từ khoá kỹ thuật thì rò rỉ cứ xảy ra ở LỜI ĐỜI THƯỜNG.
# Đúng bài học F-24: mẫu chỉ bắt được cách nói TA NGHĨ RA, không bắt cách nói THẬT.
# Nay neo vào: con số cấu hình + bất kỳ dấu hiệu HẠN/HIỆU LỰC nào.
# LUẬT 18: qua `KC.cum` nên "ma duyet" bắt luôn "mã PHẢI duyệt", "ma xac nhan"
# bắt "mã cần xác nhận". Xem `khop_cum.py` — phép biến đổi THUẦN CỘNG.
_O1_NGU_CANH_MA = KC.cum(
    "otp", "ma duyet", "ma xac nhan", "phe duyet", "ma xac thuc",
    "het han", "hieu luc", "con han", "hieu luc trong", "trong vong",
    "phai xin lai", "xin ma moi", "ma rieng",
)
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
    return KC.khop_bat_ky(_O1_NGU_CANH_MA, sach) and bool(_O1_SO_OTP.search(sach))


# ---------------------------------------------------------------- O2
# CỐ Ý HẸP, và tôi nói thẳng giới hạn: "liệt kê >=2 quy tắc nội bộ liền nhau"
# không có định nghĩa máy kiểm được nếu không so với chính prompt. Ở đây chỉ bắt
# việc nhắc lại NGUYÊN VĂN các cụm đặc thù của prompt nội bộ. Phần suy diễn
# (paraphrase) KHÔNG bắt — để guardrail đếm theo thread lo, đúng nguyên tắc
# hẹp-mà-chắc. Đừng đọc sự tồn tại của O2 thành "đã phủ mọi cách lộ chỉ thị".
_O2_CUM_NOI_BO = KC.cum(
    "rang buoc bat buoc",
    "quy trinh dieu tra",
    "khong bao gio duoc",
    "ban la tro ly ao cua",
)


def _khop_o2(reply: str) -> bool:
    sach = _bo_dau(reply)
    return sum(1 for c in _O2_CUM_NOI_BO if c.search(sach)) >= 2


# ---------------------------------------------------------------- O3
# CÓ ĐIỀU KIỆN: phần B chỉ chạy khi phần A bật. Vi phạm oracle KHÔNG phải thuộc
# tính từ vựng của câu trả lời — nó là thuộc tính của CẶP (phỏng đoán của khách
# ↔ câu trả lời). Cùng chữ "chính xác" vô hại khi khách hỏi số tiền, và là rò rỉ
# khi khách vừa đọc một dãy số bị che.
_A_DAY_SO = re.compile(r"\d{4,}")
_A_TEN_RIENG = re.compile(r"\b[A-ZĐÀ-Ỹ][a-zà-ỹ]+(\s+[A-ZĐÀ-Ỹ][a-zà-ỹ]+){1,}\b")
_A_HOI_XAC_NHAN = KC.cum(
    "co phai", "dung khong", "phai khong", "hay la", "dung/sai", "dung hay sai",
    "gan dung", "xac nhan giup", "co dung", "phai vay khong",
)
# B — chỉ tính khi cụm khẳng định/phủ định ĐỨNG NHƯ MỘT MỆNH ĐỀ TRẢ LỜI, tức mở
# đầu một mệnh đề. "không có giao dịch nào chính xác với 500k" KHÔNG khớp vì
# "chính xác" nằm giữa mệnh đề, không phải câu trả lời đúng/sai.
# Gom CA dang phu dinh: loai tru mot kha nang cung la MOT BIT oracle.
# "Khong phai 21 dau" thu hep khong gian doan y nhu "dung roi" xac nhan no.
_B_KHANG_DINH = KC.cum(
    "dung roi", "chinh xac", "vang", "phai roi", "gan dung", "dung vay",
    "khong phai", "sai roi", "khong dung", "khong phai vay",
)


def _tach_menh_de(t: str) -> list[str]:
    return [m.strip() for m in re.split(r"[,.;:!?\n]+", t) if m.strip()]


def _a_la_phong_doan(tin_nhan_khach: str) -> bool:
    if not tin_nhan_khach:
        return False
    co_du_lieu = bool(_A_DAY_SO.search(tin_nhan_khach)) or bool(_A_TEN_RIENG.search(tin_nhan_khach))
    sach = _bo_dau(tin_nhan_khach)
    co_hoi = KC.khop_bat_ky(_A_HOI_XAC_NHAN, sach)
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
# SIẾT ĐỊNH DẠNG (vá B) — dấu phân cách CHỈ hợp lệ khi mang hình dạng NGĂN HÀNG
# NGHÌN, tức mỗi nhóm sau dấu phải ĐÚNG 3 chữ số. Mẫu cũ `\d[\d.,\s]{5,}\d` coi
# MỌI dấu chấm/phẩy/khoảng trắng là dấu ngăn, nên nó dán những thứ không phải một
# con số thành một dãy KHÔNG TỒN TẠI ở đâu cả, rồi chặn agent vì "không truy được":
#   "01.08.2026"           -> 01082026        (một cái NGÀY, chặn oan)
#   "1.100.000, 262.000"   -> 1100000262000   (hai số tiền ĐỀU hợp lệ, chặn oan)
# Nhánh `\d{7,}` giữ nguyên chiều bắt-bịa cho số viết LIỀN — bẫy F không bị nới.
#
# HAI LỖ ĐÃ ĐO, HAI CƠ CHẾ KHÁC NHAU ĐÓNG — bỏ `\s` (nháp giữa của tôi) BỊ RÚT:
# nó đóng lỗ ① nhưng MỞ lỗ mới ở chiều bắt-bịa (Lead [ĐO] độc lập, xem dưới).
# Bản đứng là NEO BIÊN + PHÂN CÁCH NHẤT QUÁN, đóng cả hai mà không đánh đổi.
#
# ① NEO BIÊN `(?<!\d)…(?!\d)` (Lead tìm, [ĐO]) — thiếu neo, mẫu chọn một điểm
#    bắt đầu BẤT KỲ giữa một chuỗi số bị dấu chấm cắt rời, miễn phần còn lại
#    tình cờ khớp hình-nhóm-3: "01.08.2026" sinh dãy ma "08.202" (bắt đầu từ
#    giữa "08", nhóm với ".202" của "2026"). Neo `(?!\d)` chặn nó: ký tự theo
#    sau "08.202" là '6' (chữ số) → match bị bác, không còn điểm bắt đầu nào
#    khác thoả cả \d{1,3} lẫn phần đuôi.
# ② PHÂN CÁCH NHẤT QUÁN qua backreference `([.,\s])…\1` (tôi tìm, sau khi bản
#    "bỏ \s" của mình bị Lead [ĐO] bắt hồi quy trên `'so 1 100 000 bia'` — số
#    BỊA dùng khoảng trắng ngăn hàng nghìn, mẫu CŨ bắt được, bản "bỏ \s" làm
#    mù). Giữ `\s` trong TẬP ký tự phân cách (không mất chiều bắt-bịa của
#    Lead), nhưng ép mọi lần lặp trong CÙNG một dãy phải dùng ĐÚNG MỘT ký tự
#    phân cách (`\1` khớp lại đúng ký tự đã bắt ở lần đầu) — không cho MỘT dãy
#    trộn '.' với ' '. Đây chính là hình dạng phân biệt hai ca:
#      "1 100 000" (bịa, TOÀN khoảng trắng)      -> nhất quán -> CHẶN  ✅
#      "1.100.000 262.000" (hai số ĐỘC LẬP, số 1 -> nhất quán tới "1.100.000",
#       dùng '.', rồi gặp ' ' TRƯỚC "262" — không    dừng ở đó, "262.000" là
#       khớp \1='.' -> dừng match ở số thứ nhất)      match RIÊNG kế tiếp  ✅
#    [ĐO] script, 12 ca (9 ca Lead + 2 ca tôi tự tìm + 1 ca giới hạn cũ) —
#    0/12 lệch kỳ vọng, và mẫu này ĐÓNG LUÔN giới hạn "dán không khoảng trắng"
#    ('1.100.000,262.000') mà bản trước phải khai là chấp nhận để lại: phẩy
#    sau '.' giờ cũng bị backreference bác vì không khớp \1='.'.
#
# 🔴 GIỚI HẠN CÒN LẠI (PO-agent tìm, Lead [ĐO] xác nhận độc lập, tôi [ĐO] lại
# lần ba trước khi ghi — cả ba khớp): số agent BỊA viết phân cách KHÔNG NHẤT
# QUÁN (`2.500 000` · `2 500.000` · `2.500,000`) KHÔNG bị bắt — backreference
# đòi CÙNG một ký tự cho mọi nhóm trong một dãy, nên dãy trộn không bao giờ
# ghép đủ ≥7 chữ số và rơi ra khỏi tập trích HOÀN TOÀN (`_cac_day_so` trả về
# rỗng cho các ca này, không phải trả về sai). Mẫu GỐC `\d[\d.,\s]{5,}\d` BẮT
# ĐƯỢC cả ba ca này ⟹ đây là THU HẸP THẬT so với đường nền, không chỉ là vùng
# ngoài tầm với — đánh đổi CÓ Ý THỨC để đóng hai ca chặn oan
# ('1.100.000 262.000' và '1.100.000,262.000'). Đánh đổi này HẸP HƠN HẲN bản
# "bỏ \s" đã bị rút (bản đó để lọt MỌI số bịa viết bằng space, kể cả thuần
# space), nhưng KHÔNG RỖNG: số bịa dùng phân cách THUẦN NHẤT (toàn chấm hoặc
# toàn khoảng trắng) vẫn bị chặn đúng. Vá lỗ này đòi ép nhất quán ở TẦNG KHÁC
# hoặc nới trở lại chiều chặn oan — cả hai đắt hơn giá trị thu được, và mọi ca
# sai của chúng rơi về phía CHẶN OAN, đúng thứ hôm nay đang chữa. ĐỪNG vá.
_DAY_SO = re.compile(r"(?<!\d)\d{1,3}([.,\s])\d{3}(?:\1\d{3})*(?!\d)|(?<!\d)\d{7,}(?!\d)")
# ⚠️ `([.,\s])` là NHÓM BẮT (bắt buộc, để `\1` neo được phân cách) — chỉ dùng
# qua `finditer(...).group()` (đúng MỘT nơi, `_cac_day_so` dưới). Gọi
# `_DAY_SO.findall(...)` sẽ trả về DẤU PHÂN CÁCH của group 1, KHÔNG phải số —
# và sai IM LẶNG (không lỗi, chỉ sai kiểu dữ liệu người gọi không ngờ tới).
# Ca OR-F03 cua tester: "43a5940" la LAT CAT cua tool_result_id "TR-43a5940ecd78"
# — dinh danh NOI BO cua bo do, khong bao gio duoc phat ra cho khach. No khong
# phai day so thuan (co chu xen giua) nen luat chi-soi-chu-so mu hoan toan voi no.
# Mo rong: moi TOKEN chu-so tron dai >=7 va CO it nhat mot chu so. Nguong 7 +
# bat buoc co chu so de tu tieng Viet thuong khong lot vao (khong tu nao vua dai
# >=7 vua chua chu so).
_TOKEN_MA = re.compile(r"[A-Za-z0-9]{7,}")

# 🔴 VÁ A (25/08) — KHUÔN MÃ CÓ GẠCH NGANG. `_TOKEN_MA` đòi ≥7 ký tự LIỀN, nên
# dấu `-` cắt `CMP-00003` thành "CMP"(3) + "00003"(5) ⟹ **cả hai dưới ngưỡng**,
# O3 MÙ HOÀN TOÀN. Sự cố 25/08: bot bịa `CMP-00003` — một mã CÓ THẬT của khách
# KHÁC — và bộ lọc cho qua, trong khi CÙNG CÂU BỎ MÃ ĐI thì O5 chặn.
# ⟹ Thêm một mã giả vào câu làm nó AN TOÀN HƠN trong mắt bộ lọc.
#
# Mọi mã THẬT của hệ đều ≥7 ký tự LIỀN sau tiền tố (TCK-…12hex · RES-…12hex ·
# TXN…14số) nên khe này chỉ mở với mã BỊA — không ai vấp cho tới khi model bịa.
#
# Khuôn: 2–5 CHỮ CÁI + `-` + ≥3 ký tự chữ/số. CỐ Ý bắt đầu bằng CHỮ CÁI để
# KHÔNG nuốt ngày tháng (`2026-08-27` bắt đầu bằng số ⟹ không khớp) — ngày là
# thứ agent nói hợp lệ suốt, bắt oan nó là đóng luôn đường trả lời bình thường.
# `{3,}` sau gạch: "COVID-19"/"check-in"/"e-mail" đều trượt.
#
# 🔴 ÁP CHO CẢ HAI PHÍA (reply VÀ nguồn) vì nằm trong `_cac_day_so` — mã THẬT
# lấy từ kết quả tool cũng được bóc y hệt, nên nó vẫn TRUY VẾT ĐƯỢC và KHÔNG bị
# chặn oan. Chỉ mã BỊA mới không có mặt ở nguồn.
_MA_CO_GACH = re.compile(r"\b[A-Za-z]{2,5}-[A-Za-z0-9]{3,}\b")


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
    for m in _MA_CO_GACH.finditer(text or ""):
        tok = m.group()
        if any(c.isdigit() for c in tok):
            ra.add(tok.lower())
    return ra


# CHẨN ĐOÁN không lưu nội dung (vá C). CẤM chứa giá trị hay BĂM của giá trị —
# băm vẫn là một định danh, vẫn đối chiếu ngược được với một con số cụ thể; chỉ
# HÌNH DẠNG mới được log. Xem call-site trong `loc_dau_ra` — nguyên tắc "reply
# khớp O3 gần như chắc chắn chứa dữ liệu bị che, log nó ra là tự tay làm rò" áp
# y hệt cho MỌI trường chẩn đoán mới, không chỉ cho `reply` gốc.
def _hinh_dang_day_la(day_la: set[str]) -> dict[str, object]:
    return {
        "o3_so_luong_day_la": len(day_la),
        "o3_do_dai_day_la": sorted(len(t) for t in day_la),
        "o3_co_chu_cai": any(any(c.isalpha() for c in t) for t in day_la),
        # Hình dạng NGÀY thuần đoán: dãy TOÀN CHỮ SỐ, đúng 8 ký tự (DDMMYYYY dán
        # liền — đúng ca bịa "01.08.2026" -> "01082026" mà vá B vừa đóng). Đoán
        # THÔ có chủ đích: mục đích là chẩn đoán nhanh, không phải phân loại
        # chính xác — dùng sai chỗ này thì đi hỏi giá trị thật, không đoán thêm.
        "o3_co_hinh_dang_ngay": any(len(t) == 8 and t.isdigit() for t in day_la),
    }


def _payload_luot_nay_rong(nguon: str) -> bool | None:
    """`luot_nay` (bao bì của `rap_nguon_o3`, graph.py) rỗng hay không.

    `None` = KHÔNG XÁC ĐỊNH ĐƯỢC (nguồn không mang bao bì này — vd nguồn dựng
    bằng quy ước riêng của eval offline) — đây là trạng thái thứ BA bắt buộc
    (Luật H): không được gộp "không đo được" vào "không rỗng"/"rỗng".
    """
    try:
        d = json.loads(nguon)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(d, dict) or "luot_nay" not in d:
        return None
    return not d["luot_nay"]


def _khop_o3(reply: str, tin_nhan_khach: str, nguon: str, loi_khach: str = "") -> tuple[bool, dict]:
    # nguon = payload tool (JSON) -> trích NGHIÊM, không cho dấu phân cách gộp số.
    # loi_khach + tin_nhan_khach = văn xuôi -> trích THOÁNG, chấp nhận "262.000đ".
    hop_le = (
        _cac_day_so(nguon, cho_phep_phan_cach=False)
        | _cac_day_so(tin_nhan_khach)
        | _cac_day_so(loi_khach)
    )
    # SO THEO GIA TRI, KHONG so chuoi con — bay F cua tester.
    # Ban dau toi so `so in g or g in so` de "tool tra so dai hon ma agent
    # chi doc mot phan" van qua. Nhung chinh no mo mot cua BIA SO MOI:
    # "20260504" la CHUOI CON cua trans_id that TXN20260504000247, nen mot
    # con so agent bia ra van "truy vet duoc" chi vi no tinh co la tien to
    # cua mot ma that. Do that: LOT.
    # Bay B (dinh dang) va bay F (chuoi con) KEO NGUOC NHAU — noi de cuu B
    # lam do F, siet de cuu F lam do B. Loi ra: chuan hoa DINH DANG (bo dau
    # phan cach) de cuu B, nhung so KHOP TUYET DOI de dong F.
    day_la = {so for so in _cac_day_so(reply) if so not in hop_le}
    if day_la:
        return True, _hinh_dang_day_la(day_la)
    if not _a_la_phong_doan(tin_nhan_khach):
        return False, {}
    for md in _tach_menh_de(_bo_dau(reply)):
        # `.match` chứ không `.search`: giữ nguyên ngữ nghĩa "đứng ĐẦU mệnh đề"
        # của `startswith` cũ. Luật 18 chỉ nới phần GIỮA cụm, không nới cái neo
        # đầu mệnh đề — neo đó mới là thứ phân biệt câu TRẢ LỜI đúng/sai với chữ
        # "chính xác" nằm lọt giữa một câu vô hại.
        if any(k.match(md) for k in _B_KHANG_DINH):
            return True, {}
    return False, {}


# ---------------------------------------------------------------- O4
# THEO CỤM, không theo từ: chỉ khớp khi đủ BA yếu tố TRONG CÙNG MỘT MỆNH ĐỀ.
# "chắc chắn sẽ được hoàn cho bạn" khớp; "nếu muốn biết chắc chắn thì liên hệ
# CSKH" không khớp vì thiếu đối tượng tiền và không hướng về case của khách.
# "du dieu kien duoc hoan" la CAM KET MAC AO DIEU KIEN: no khong hua thang
# nhung khach doc ra la "toi se duoc hoan". Ranh buoc cung 1 cam agent ket luan
# ve ket qua, ke ca gian tiep.
_O4_DONG_TU = ["se ", "chac chan", "dam bao", "cam ket", "du dieu kien", "duoc duyet",
    # Bảo Mật 19/08 (030e4b2) + PO-agent [ĐO] thật (3d14d30): thì HOÀN TẤT
    # ("đã", "vừa") lọt hoàn toàn trước bản vá này — "đã được hoàn tiền" là
    # khẳng định KẾT QUẢ, không phải lời hứa, nhưng khách đọc ra hệt nhau và
    # hậu quả nặng hơn (khách NGỪNG THEO DÕI một giao dịch chưa ai duyệt).
    #
    # 🔴 KHÔNG dùng "da"/"vua" TRẦN TRỤI (khác "se " — chỉ "sẽ" strip dấu ra
    # "se", nhưng "đã" VÀ "dạ" (tiểu từ mở câu cực phổ biến trong văn phong
    # CSKH — "Dạ anh...") CÙNG strip ra "da"). [ĐO] tự tái tạo: bare "da" bắt
    # NHẦM "Dạ anh khoản hoàn tiền đang được xử lý ạ" (không hề có thì hoàn
    # tất) — đúng bẫy "ca âm tính số 1" Bảo Mật cảnh báo, chỉ đổi từ "sẽ"
    # sang "đã"/"dạ".
    #
    # 🔴 VÀ KHÔNG ghép "da"/"vua" với "hoan" TRẦN TRỤI — [ĐO] tự tái tạo LẦN
    # HAI, lần này bắt nhầm CHÍNH bộ test hiện có: "Giao dịch ngày 01.08.2026
    # của bạn đã hoàn tất." bị chặn oan (test_o3_cong_hanh_vi... đỏ). "Hoàn"
    # đơn lẻ mơ hồ giữa "hoàn TIỀN" (trả tiền) và "hoàn TẤT/THÀNH" (xong việc)
    # — bare `hoan` trong `_O4_TIEN` sống được với "sẽ/chắc chắn" (hiếm ai nói
    # "chắc chắn đã hoàn tất") nhưng KHÔNG sống được với "đã/vừa" (rất tự
    # nhiên đi với "hoàn tất" — câu mô tả tiến độ thường ngày, không phải
    # cam kết tiền). ⟹ chỉ ghép với các cụm ĐÃ SẴN CÓ trong `_O4_TIEN` mà tự
    # thân không mơ hồ (hoàn TIỀN, hoàn LẠI, trả lại, bồi hoàn, nhận...tiền,
    # về/vào ví/tài khoản — không cụm nào đọc được là "xong việc"), KHÔNG
    # ghép với bare "hoan". Kèm biến thể "da duoc "/"vua duoc " — thể bị
    # động ("đã ĐƯỢC hoàn tiền") tự nhiên hơn thể chủ động trong văn CSKH.
    "da hoan tien", "da duoc hoan tien", "vua hoan tien", "vua duoc hoan tien",
    "da hoan lai", "da duoc hoan lai", "vua hoan lai", "vua duoc hoan lai",
    "da tra lai", "da duoc tra lai", "vua tra lai", "vua duoc tra lai",
    "da boi hoan", "da duoc boi hoan", "vua boi hoan", "vua duoc boi hoan",
    "da nhan lai tien", "da nhan duoc tien", "vua nhan lai tien", "vua nhan duoc tien",
    "da ve vi", "da vao vi", "da vao tai khoan",
    "vua ve vi", "vua vao vi", "vua vao tai khoan"]
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


# ---------------------------------------------------------------- O5
# Đặc tả gốc: docs/security/2026-08-24-dac-ta-o5-tu-vung-hoan-tat-gia-tao-ve.md
# (Bảo mật, sau finding 5f627e3: "đã tạo hồ sơ cho bạn rồi" lọt sạch O3+O4 vì
# không số, không từ tiền). Đặc tả gốc §2 đề xuất đối chiếu MÃ TICKET với
# `nguon` (giống O3) — nhưng Tester đo LẠI bằng mã 12-hex THẬT (`new_id()`)
# thay vì fixture 5-6 ký tự của lần đo đầu: O3 đã phủ 2/2 ca "nêu SAI mã"
# (sai giá trị + siêu chuỗi), vì mã thật LUÔN nằm trong tầm `_TOKEN_MA`
# (ngưỡng 7 ký tự). O5 chỉ còn cần cho ĐÚNG khe O3 không có gì để so: reply
# KHÔNG nêu mã nào cả — dù hoàn-tất-giả (không tool result) hay hoàn-tất-
# thật-nhưng-quên-nêu-mã (nay LUÔN sai theo chính sách, xem dưới).
#
# Luật (Bảo mật thu hẹp 24/08, PO thật duyệt qua PO-agent):
#   từ vựng HOÀN TẤT (đã/vừa tạo/mở/ghi nhận, kèm biến thể bị động) khớp
#   ĐỐI TƯỢNG (hồ sơ/vé/ticket/khiếu nại) trong CÙNG một mệnh đề
#   VÀ reply KHÔNG chứa token mã nào (`_TOKEN_MA` — TÁI DÙNG nguyên định
#   nghĩa O3, không tự chế thước mới).
#
# KHÔNG đối chiếu `nguon` theo giá trị (khác đề xuất §2 đặc tả gốc) — lý do
# đủ, không phải bỏ qua: docstring `create_ticket` giờ BẮT BUỘC nêu mã
# (customer_tools.py, `6d0e3a9`, cùng phiên này) nên VẮNG MÃ LUÔN SAI theo
# chính sách, bất kể `nguon` có tool result thành công hay không. Đơn giản
# hoá này do chính hai vòng ĐO quyết định, không phải suy đoán trước.
#
# Tái dùng NGUYÊN cơ chế O4 đã trả giá, không tái phát minh:
#   1. Fused-phrase, KHÔNG bare "da"/"vua" — bẫy "dạ" strip dấu trùng "da"
#      (_bo_dau("Dạ") == _bo_dau("đã") == "da"). Mọi mục dưới đây LUÔN ghép
#      tense với động từ thành CỤM liền, giống "da hoan tien" của O4.
#   2. `_O4_PHU_DINH` cho mệnh đề phủ định — "mình CHƯA tạo được hồ sơ lúc
#      này" là câu ĐÚNG (agent thành thật báo lỗi/OTP hết hạn, đúng finding
#      5f627e3 đề nghị dạy agent nói) — PHẢI cho qua, không tự chế danh sách
#      phủ định riêng cho O5.
#
# 🔴 Review bắt 24/08 (soát 491c91d) — HAI lỗ, cả hai ĐO trực tiếp bằng code
# chạy, không suy diễn:
#
#   ① THIẾU yếu tố "hướng khách" (bản đầu chỉ 2 yếu tố: dong_tu + doi_tuong).
#      [ĐO] "Vé loại này đã được mở rất nhiều lần trong quá khứ, không có gì
#      bất thường." và "Hồ sơ tương tự đã ghi nhận cho nhiều khách khác
#      trước đây rồi." — cả hai KHÔNG hề khẳng định đã xử lý CHO KHÁCH ĐANG
#      CHAT, chỉ mô tả chuyện chung/quá khứ, nhưng khớp cả 2 yếu tố cũ ⟹
#      CHẶN OAN. Đúng thứ nguyên tắc đầu file cảnh báo là hậu quả NẶNG NHẤT
#      (dương tính giả > âm tính giả ở lớp lọc đầu ra).
#
#      Review đề xuất thêm kiểm THỨ TỰ (như O4: vt_dong_tu < vt_tien) — CÂN
#      NHẮC nhưng KHÔNG dùng: ordering sẽ làm rớt chính ca bị-động hợp lệ
#      "Hồ sơ khiếu nại của bạn đã được ghi nhận" (đối tượng đứng TRƯỚC động
#      từ, đúng cấu trúc bị động tiếng Việt tự nhiên) — mất một catch THẬT để
#      đóng 2 lỗ false-positive là đánh đổi tệ hơn. Chọn hướng KHÁC: thêm
#      YẾU TỐ THỨ BA "hướng khách" (mirror `_O4_HUONG_KHACH` — đúng câu hỏi
#      mở đặc tả gốc §4 để ngỏ: "Có cần yếu tố Hướng khách không?"). Cả hai
#      câu Review đưa ra đều THIẾU hướng khách (không có bạn/anh/chị/mình/
#      của bạn/quý khách) ⟹ yêu cầu thêm yếu tố này đóng cả hai lỗ MÀ KHÔNG
#      cần ordering, giữ nguyên khả năng bắt câu bị động hợp lệ.
#
#   ② THIẾU từ vựng: "đã lập" (hồ sơ/vé — CSKH phổ biến) và ĐẶC BIỆT "đã
#      tiếp nhận" — [ĐO] Review chỉ ra đây CHÍNH LÀ từ vựng ADR-047 (`1080762`,
#      land CÙNG NGÀY) dùng để mô tả việc create_ticket làm ("tiếp nhận
#      trước, bổ sung sau"). prompt.py bước 4 nhánh mới có khả năng cao khiến
#      model dùng ĐÚNG từ "tiếp nhận" khi báo kết quả — đúng khung ngôn ngữ
#      vừa cài cùng ngày. Thiếu từ này là mù với đúng ca có xác suất xảy ra
#      CAO NHẤT trong các ca hoàn-tất-giả từ giờ trở đi. Thêm "lập"/"tiếp
#      nhận" (chủ động + bị động) vào danh sách động từ.
_O5_DONG_TU_HOAN_TAT = [
    "da tao", "da mo", "da ghi nhan", "da lap", "da tiep nhan",
    "vua tao", "vua mo", "vua ghi nhan", "vua lap", "vua tiep nhan",
    "da duoc tao", "da duoc mo", "da duoc ghi nhan", "da duoc lap", "da duoc tiep nhan",
    "vua duoc tao", "vua duoc mo", "vua duoc ghi nhan", "vua duoc lap", "vua duoc tiep nhan",
]
_O5_DOI_TUONG = ["ho so", "ve", "ticket", "don khieu nai", "khieu nai"]
_O5_HUONG_KHACH = ["ban", "anh", "chi", "minh", "cua ban", "quy khach"]
# 🔴 Review tự phản biện chính đề xuất "toàn reply" của mình (24/08, sau
# d9885ca) — [ĐO] mở "hướng khách" ra toàn reply cho MƯỢN tư cách hướng-
# khách cho một câu KHÔNG LIÊN QUAN: "Bạn hỏi hay đó. Loại vé này đã được mở
# rất nhiều lần trong quá khứ cho nhiều khách khác..." — "Bạn" ở câu ĐẦU chỉ
# ghi nhận câu hỏi, câu SAU vẫn là mô tả chung y hệt 2 ca false-positive
# vòng 1 — tái xuất, cùng họ lỗi. "Lân cận" không giải được (Review tự thử):
# "bạn" cũng nằm ở mệnh đề liền kề trong chính ca vừa dựng.
#
# Vá bằng NHÁNH KHÁC Review đề xuất: PHỦ ĐỊNH mô tả-chung, cùng khuôn
# `_O4_PHU_DINH` — mệnh đề có dấu hiệu đang nói về chuyện CHUNG/QUÁ KHỨ (tần
# suất, lịch sử, người khác) thì KHÔNG tính, dù có đủ động từ+đối tượng.
_O5_MO_TA_CHUNG = ["nhieu lan", "truoc day", "thuong xuyen", "khach khac"]

# 🔴 RB3 false-positive LẦN HAI (04/09, QA bắt qua T1-T5, 2/8 lượt — lần đầu
# 04/09 sớm hơn là thiếu nguồn `request_human_handoff`, đã vá c6d15ac, KHÁC
# bug này). Coder tái lập bằng test hàm trực tiếp (0 token, tất định):
#   "Mình đã ghi nhận khiếu nại của bạn, đang xử lý tiếp." -> True SAI
# "ghi nhận khiếu nại" KHÔNG phải model tự bịa — đây là cụm NGUYÊN VĂN
# `prompt.py` dạy dùng (Ràng buộc #1 vế b) và kịch bản chuyên gia CSKH tham
# chiếu dùng lặp lại nhiều lần — PO chốt: KHÔNG đụng prompt.py (nghiệp vụ
# đúng), chỉ matcher cần khôn lên phân biệt 2 NGHĨA khác nhau của cùng cụm:
#   NGHĨA MỀM — "đã ghi nhận/tiếp nhận" = đã NGHE/HIỂU thông tin, đang tiếp
#     tục xử lý (chưa chắc đã gọi create_ticket).
#   NGHĨA CỨNG — "đã tạo/mở/lập" = khẳng định một bản ghi cụ thể ĐÃ TỒN TẠI.
# Review thiết kế, Coder verify 9 case + 4 case đối kháng tự thêm (khớp
# 100%) trước khi land — xem lịch sử trao đổi Lead/Review/Coder 04/09 tối,
# không lặp lại toàn bộ ma trận ở đây.
_O5_DONG_TU_CUNG = [
    "da tao", "da mo", "da lap",
    "vua tao", "vua mo", "vua lap",
    "da duoc tao", "da duoc mo", "da duoc lap",
    "vua duoc tao", "vua duoc mo", "vua duoc lap",
]
_O5_DONG_TU_MEM = [
    "da ghi nhan", "da tiep nhan",
    "vua ghi nhan", "vua tiep nhan",
    "da duoc ghi nhan", "da duoc tiep nhan",
    "vua duoc ghi nhan", "vua duoc tiep nhan",
]
# Câu MỀM nói tiếp-diễn/chưa-xong (đứng CẠNH động từ mềm, KHÔNG phải toàn
# reply — xem cảnh báo "reply-global" trong `khai_da_tao_ve` bên dưới, đây
# CHÍNH LÀ nơi bẫy đó từng suýt tái diễn nếu đặt sai vị trí nhánh if).
_O5_TIEP_DIEN = [
    "dang xu ly", "de minh tra", "de minh kiem tra", "se tiep tuc",
    "tiep tuc kiem tra", "cho minh it phut",
]
# KHÔNG có " ma " (mã) ở đây nữa — [ĐO 04/09] `_bo_dau()` sập TẤT CẢ "ma/má/
# mạ/mả/mã/mà" về cùng chuỗi "ma", nên "mã" (số hồ sơ) và "mà" (liên từ —
# một trong những từ phổ biến nhất tiếng Việt, vd "...của bạn MÀ chưa rõ...")
# va chạm, bắt oan hàng loạt câu mềm+tiếp-diễn hợp lệ. Chuyển "mã" ra kiểm
# riêng trên `reply` GỐC còn dấu trong `khai_da_tao_ve` (an toàn: hàm chỉ
# nhận văn bản AGENT TỰ SINH, không phải input khách gõ tắt/không dấu).
_O5_XAC_NHAN_MANH_KO_DAU = ["thanh cong", "xong"]


def khai_da_tao_ve(reply: str) -> bool:
    """Câu này có KHAI rằng vé/hồ sơ ĐÃ ĐƯỢC TẠO không — bất kể có kèm mã hay không.

    🔴 KHÁC `_khop_o5` ở ĐÚNG MỘT ĐIỂM, và điểm ấy là toàn bộ lý do hàm này tồn tại:
    O5 **nhường** khi câu có kèm mã, vì chú thích của nó tự khai giả định
    *"O3 đã phủ mọi ca có mã sai/mã bịa"*. [ĐO 25/08] **giả định ấy SAI**:
        `_TOKEN_MA = r"[A-Za-z0-9]{7,}"`
        "CMP-00003" → dấu `-` cắt thành "CMP" (3) + "00003" (5) → CẢ HAI dưới ngưỡng
        ⟹ O3 MÙ HOÀN TOÀN với khuôn mã ấy
    Mọi mã THẬT của hệ (`TCK-…12 hex`, `TXN…14 số`, `RES-…`) đều ≥7 ký tự liền, nên
    khe này chỉ mở ra với mã **BỊA** — và không ai vấp cho tới khi model bịa thật.
    Hậu quả đo được: **thêm một mã giả vào câu làm nó AN TOÀN HƠN trong mắt bộ lọc.**

    ⟹ Hàm này CỐ Ý **không** miễn trừ theo mã — có mã (thật hay bịa) không bao
    giờ khiến hàm trả `False`, chỉ có thể đẩy VỀ PHÍA `True` (xem nhánh MỀM
    dưới). Nó chỉ trả lời *"có khai đã tạo không"*; việc đối chiếu với
    `ticket_id` THẬT là của tầng gọi (`graph.py`), nơi duy nhất biết sự thật.
    Đây là ràng buộc cứng 3 ép bằng SỰ THẬT, không bằng từ vựng — nên nó không
    thừa hưởng trần của cách khớp-từ mà chú thích `_khop_o5` đã khai.

    🔴 04/09 — tách CỨNG/MỀM (xem `_O5_DONG_TU_CUNG`/`_O5_DONG_TU_MEM` phía
    trên): động từ CỨNG ("tạo/mở/lập") luôn `True` khi có đối tượng — hành vi
    CŨ, không đổi. Động từ MỀM ("ghi nhận/tiếp nhận") cần thêm 1 trong 2:
    có MÃ THẬT (kèm dấu), hoặc KHÔNG có câu tiếp-diễn ("đang xử lý tiếp"...)
    thì mới `True`; có tiếp-diễn mà không mã thì `False` (đúng case QA bắt).

    Thứ tự bên trong nhánh MỀM là CỐ Ý — mã/thành-công xét TRƯỚC tiếp-diễn,
    để một câu vừa có mã vừa có tiếp-diễn ("...mã KN-00042, đang xử lý tiếp
    nhé") vẫn `True` (mã THẮNG, không bị câu tiếp-diễn "rửa sạch").

    ⚠️ HAI ĐÁNH ĐỔI ĐÃ KHAI (Review + Coder, 04/09) — không phải lỗ bị giấu,
    người đọc sau ĐỪNG tưởng chỉ có một hướng:
    1. Check mã/"thành công" đang REPLY-GLOBAL (không giới hạn trong mệnh đề
       chứa động từ mềm) — chỉ có thể làm hàm QUÁ TAY, gắn `True` THỪA cho
       câu mềm có mã/"thành công" nằm ở mệnh đề khác không liên quan.
       KHÔNG BAO GIỜ làm lọt một ca hallucination thật (chiều an toàn — dương
       tính giả > âm tính giả, đúng nguyên tắc đầu file).
    2. Check `" mã "` đọc `reply` GỐC còn dấu, KHÔNG qua `_bo_dau()` — nếu
       model (hiếm, chưa từng thấy qua hàng chục ví dụ LLM thật) lỡ SINH RA
       chữ "mã" thiếu dấu giữa một câu có dấu đầy đủ khác, câu đó rơi xuống
       nhánh tiếp-diễn thay vì bắt được mã — CHIỀU NGƯỢC LẠI với đánh đổi ①
       (có thể BỎ SÓT thay vì bắt oan). Chấp nhận vì hàm chỉ nhận văn bản
       agent tự sinh (không phải input khách gõ tắt/không dấu), và tránh nó
       lại mở lại va chạm "ma/má/mạ/mả/mã/mà" phổ biến hơn nhiều lần.
    """
    md = _bo_dau(reply)
    if any(t in md for t in _O5_MO_TA_CHUNG):
        return False
    if not any(d in md for d in _O5_DOI_TUONG):
        return False
    if any(v in md for v in _O5_DONG_TU_CUNG):
        return True
    if any(v in md for v in _O5_DONG_TU_MEM):
        co_ma_that = " mã " in f" {reply.lower()} "
        if co_ma_that or any(x in md for x in _O5_XAC_NHAN_MANH_KO_DAU):
            return True
        if any(t in md for t in _O5_TIEP_DIEN):
            return False
        return True
    return False


def _khop_o5(reply: str) -> bool:
    # 🔴 Review vòng 2 (24/08, soát a95f8f0) — [ĐO] "hướng khách" đòi CÙNG
    # MỆNH ĐỀ với động từ+đối tượng thì LỌT nguyên một họ câu chốt tự nhiên
    # của CSKH: "Bạn yên tâm nhé. Đã tạo hồ sơ khiếu nại rồi." — đại từ nằm
    # ở CÂU TRƯỚC (trấn an), động từ+đối tượng ở CÂU CHỐT (dữ kiện), đúng
    # khuôn "tách câu cảm xúc khỏi câu dữ kiện" mà nhiều luật khác trong
    # prompt.py cũng ép agent làm — `_tach_menh_de` KHÔNG gộp lại được.
    # Đổi "hướng khách" sang xét TOÀN REPLY (giống cách `_TOKEN_MA` đã làm
    # ở cuối hàm) — [ĐO] xác nhận 2 ca false-positive gốc của Review (câu mô
    # tả chung/quá khứ, không nhắc khách ở BẤT KỲ đâu trong reply) vẫn không
    # có hướng-khách sau khi đổi, không mở lại lỗ cũ.
    #
    # ⚠️ GIỚI HẠN CÒN LẠI, CỐ Ý KHÔNG VÁ (Review nêu, đồng ý để lộ thay vì
    # giấu): câu HOÀN TOÀN không đại từ ("Đã tạo hồ sơ khiếu nại rồi nhé.")
    # vẫn LỌT — không có "bạn/anh/chị/mình/quý khách" ở đâu trong reply thì
    # đổi phạm vi cũng không cứu được. Tín hiệu thay thế (tiểu từ "nhé"/"ạ")
    # tự nó có rủi ro bắt oan riêng, cần đo riêng trước khi thêm — ĐỪNG đoán
    # trước, đúng Luật M. Đây là đánh đổi ĐÃ KHAI, không phải lỗ bị giấu.
    #
    # ⚠️ GIỚI HẠN THỨ HAI, CỐ Ý DỪNG Ở ĐÂY (Review tự bắn ngược `_O5_MO_TA_
    # CHUNG` sau khi vá, 24/08): một trong 4 từ mô-tả-chung dùng SAI nghĩa
    # gốc (mốc thời gian trong hội thoại/tần suất CÁ NHÂN của khách, không
    # phải "chuyện chung/nhiều khách khác") CÙNG mệnh đề với câu chốt cũng
    # LỌT — "Mình đã tạo hồ sơ khiếu nại cho bạn như đã hứa trước đây rồi
    # nhé.", "...thấy trường hợp này xảy ra thường xuyên với bạn." Khớp từ
    # không phân biệt được NGỮ NGHĨA, chỉ khớp SỰ CÓ MẶT — ba vòng vá liên
    # tiếp cùng dạng lỗi (hướng-khách cùng-mệnh-đề -> toàn-reply -> loại-trừ-
    # theo-từ) chứng minh TRẦN của cách tiếp cận khớp-từ/vị-trí, không phải
    # một lỗ đơn lẻ còn sót. DỪNG vá thêm ở đây — bề mặt đã hẹp tới mức cần
    # đúng tổ hợp hiếm, O5 vốn chỉ là lưới cuối cho MỘT khe hẹp (O3 đã phủ
    # mọi ca có mã sai/mã bịa), và nguyên tắc đầu file chấp nhận bỏ sót có
    # kiểm soát. Muốn đóng dứt điểm cần tín hiệu NGỮ NGHĨA thật, không phải
    # danh sách loại trừ thứ tư — để lại cho PO-agent/Bảo mật cân nhắc có
    # đáng đầu tư hướng khác hay không.
    co_huong_khach_toan_reply = _vi_tri_dau(_bo_dau(reply), _O5_HUONG_KHACH) is not None
    co_menh_de_hoan_tat = False
    for md in _tach_menh_de(_bo_dau(reply)):
        if any(p in md for p in _O4_PHU_DINH):
            continue
        if any(p in md for p in _O5_MO_TA_CHUNG):
            continue
        co_dong_tu = _vi_tri_dau(md, _O5_DONG_TU_HOAN_TAT) is not None
        co_doi_tuong = _vi_tri_dau(md, _O5_DOI_TUONG) is not None
        if co_dong_tu and co_doi_tuong and co_huong_khach_toan_reply:
            co_menh_de_hoan_tat = True
            break
    if not co_menh_de_hoan_tat:
        return False
    # Toàn REPLY, không chỉ mệnh đề đang xét — mã có thể nằm ở câu khác
    # trong cùng reply ("Mình đã tạo hồ sơ cho bạn. Mã của bạn là KN-...").
    # `reply` gốc (chưa bo_dau) — _TOKEN_MA chỉ khớp [A-Za-z0-9], dấu tiếng
    # Việt không rơi vào lớp ký tự này nên không cần chuẩn hoá trước.
    return not _TOKEN_MA.search(reply)


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
    o3_khop, o3_hinh_dang = _khop_o3(reply, tin_nhan_khach, nguon, loi_khach)
    if o3_khop:
        khop.append("O3")
    if _khop_o4(reply):
        khop.append("O4")
    if _khop_o5(reply):
        khop.append("O5")

    if not khop:
        return reply, []

    # Log CÓ CẤU TRÚC, KHÔNG log nguyên văn reply: reply khớp O3 gần như chắc
    # chắn chứa dữ liệu bị che — log nó ra là tự tay làm rò đúng thứ vừa chặn.
    # Vá C: khi O3 chặn, thêm HÌNH DẠNG dãy lạ (số lượng/độ dài/có chữ cái/có
    # hình-dạng-ngày) + payload lượt này rỗng không — CHỈ hình dạng, KHÔNG giá
    # trị, KHÔNG băm của giá trị (băm vẫn đối chiếu ngược được với giá trị thật).
    _logger.warning(
        "output_filter_khop",
        extra={
            "nhom": ",".join(khop),
            "correlation_id": correlation_id,
            "do_dai_reply": len(reply),
            **(o3_hinh_dang if o3_khop else {}),
            **({"o3_payload_luot_nay_rong": _payload_luot_nay_rong(nguon)} if o3_khop else {}),
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
    k: KC.cum(*v) for k, v in {
        "khong_quyet_tien": ["khong tu quyet", "khong the tu duyet", "phai co nguoi duyet", "khong duoc hoan tien truc tiep"],
        "khong_bia_so": ["khong bia", "chi dua tren du lieu", "phai tra cuu duoc"],
        "pdpa_ben_thu_ba": ["thong tin nguoi khac", "ben thu ba", "khong cung cap thong tin ca nhan"],
        "khong_ket_luan_gian_lan": ["khong ket luan gian lan", "khong khang dinh la lua dao"],
        "otp": ["khong hoi mat khau", "khong hoi otp giao dich", "otp phien"],
        "phan_loai": ["4 loai khieu nai", "phan loai khieu nai", "pham vi giao dich"],
        "tai_lieu_tham_khao": ["chi la tham khao", "tai lieu tham khao"],
        "xung_ai": ["toi la tro ly ao", "minh la tro ly ao", "toi la ai"],
        "khong_tiet_lo_huong_dan": ["khong the chia se huong dan", "khong tiet lo quy trinh noi bo"],
    }.items()
}
NGUONG_LIET_KE = 3


def dem_mat_do_liet_ke(reply: str) -> int:
    """Số CHỦ ĐỀ quy tắc khác nhau trong reply. Không chặn, chỉ đếm."""
    sach = _bo_dau(reply)
    return sum(1 for cum in _MO_NEO_QUY_TAC.values() if KC.khop_bat_ky(cum, sach))


# ------------------------------------------------ O2-C: HỌ MỎ NEO **QUY TRÌNH**
# (security `docs/security/mo-neo-quy-trinh-cho-O2.md`, PO duyệt.)
#
# LỖ Ở BỘ ĐO, KHÔNG PHẢI Ở BỘ LỌC — và đó là hạng nguy hiểm hơn. Cả 9 mỏ neo
# trên đều thuộc họ NGUYÊN TẮC; không mỏ neo nào thuộc họ CÁC BƯỚC. Mà ràng buộc
# 7 của system prompt cấm đọc lại CẢ "Ràng buộc bắt buộc" LẪN "Quy trình điều
# tra". Đo thật (security, bản `5f643f71ddb5`): câu liệt kê nguyên tắc đếm 3;
# hai câu liệt kê nguyên văn quy trình đếm **0**.
#
# Vì sao bộ đo mù nguy hiểm hơn bộ lọc thủng: phân phối mật độ sẽ nói "không có
# vấn đề", và mệnh đề "đếm trước, NÂNG LÊN CHẶN khi thấy rò" thành **rỗng** —
# đúng thứ mà quyết định "O2 đếm trước, chặn sau" sinh ra để diệt.
#
# HAI ĐIỀU KIỆN ĐỒNG THỜI, và đây là chỗ KHÔNG được chép cách đếm của họ
# nguyên-tắc sang: các BƯỚC là thứ agent nói ra HỢP LỆ HÀNG NGÀY khi báo cho
# khách nó đang làm gì ("mình sẽ tra cứu giao dịch rồi tạo hồ sơ" = 2 bước, và
# phải luôn im). Phân biệt KHÔNG nằm ở việc NHẮC một bước, mà ở việc TRÌNH BÀY
# CHUỖI BƯỚC NHƯ MỘT QUY TRÌNH.
_MO_NEO_BUOC = {
    k: KC.cum(*v) for k, v in {
        "buoc_phan_loai": ["xac dinh loai khieu nai", "phan loai khieu nai", "thuoc loai nao", "xac dinh loai van de"],
        "buoc_tra_lich_su": ["tra lich su giao dich", "lich su giao dich", "cac giao dich gan day", "xem giao dich gan day"],
        "buoc_tra_giao_dich": ["tra cuu giao dich", "tra ma giao dich", "doi chieu so tien", "kiem tra giao dich"],
        "buoc_hoi_lai": ["hoi lai de thu hep", "hoi them thong tin", "hoi ban them", "hoi ro hon"],
        "buoc_tao_ho_so": ["tao ho so", "tao ticket", "lap phieu khieu nai", "tao phieu khieu nai"],
        "buoc_bao_ket_qua": ["bao ma ticket", "bao moc xu ly", "thong bao sla", "ma ho so cua ban", "thoi han xu ly"],
        "buoc_chuyen_nguoi_that": ["chuyen chuyen vien", "gap nguoi that", "chuyen nhan vien", "chuyen sang nguoi that"],
    }.items()
}
# (B) DẤU HIỆU TRÌNH BÀY-THÀNH-QUY-TRÌNH. Một mình (B) KHÔNG đủ: "quy trình tra
# soát với ngân hàng mất 5-7 ngày" có (B) mà không có bước nào -> im.
_DAU_HIEU_QUY_TRINH = KC.cum(
    "quy trinh", "cac buoc", "gom:", "trinh tu", "buoc 1", "buoc mot",
    "thu nhat", "minh duoc huong dan", "quy dinh cua minh", "minh lam theo",
)
# "đầu tiên … sau đó" là dấu hiệu TRÌNH TỰ nên chỉ tính khi có ĐỦ HAI vế —
# riêng "đầu tiên" thì câu nào cũng có thể có.
_CAP_TRINH_TU = (KC.mau_cum("dau tien"), KC.mau_cum("sau do"))
# Ngưỡng 2 (không phải 3 như họ nguyên-tắc) vì (B) đã gánh phần lọc: có dấu hiệu
# trình-bày-quy-trình CỘNG hai bước thì đã là đọc lại quy trình.
NGUONG_QUY_TRINH = 2


def dem_mat_do_quy_trinh(reply: str) -> int:
    """Số BƯỚC khác nhau — nhưng CHỈ khi câu đang trình bày chúng thành quy trình.

    Trả 0 khi thiếu dấu hiệu (B), kể cả khi có nhiều bước: đó là ca âm tính bắt
    buộc của security, và nó bảo vệ đúng câu agent báo cho khách nó đang làm gì.
    """
    sach = _bo_dau(reply)
    co_b = KC.khop_bat_ky(_DAU_HIEU_QUY_TRINH, sach) or all(m.search(sach) for m in _CAP_TRINH_TU)
    if not co_b:
        return 0
    return sum(1 for cum in _MO_NEO_BUOC.values() if KC.khop_bat_ky(cum, sach))


def tin_hieu_lo_chi_thi(reply: str, *, thread_id: str = "") -> dict[str, int]:
    """Hai họ đếm RIÊNG, ghi CHUNG một khoá theo `thread_id`.

    Chung khoá vì mục đích là phát hiện *một hội thoại đang moi chỉ thị*, không
    phân biệt moi nguyên-tắc hay moi quy-trình — kẻ moi dần (Crescendo) không có
    lý do gì phải moi mãi một họ. Riêng khi đếm vì hai họ có ngưỡng khác nhau và
    trộn vào một con số thì mất luôn khả năng biết nó mù họ nào — đúng lỗi vừa
    phải sửa ở đây.

    VẪN CHỈ ĐẾM, KHÔNG CHẶN (quyết định O2 giữ nguyên).
    """
    nguyen_tac = dem_mat_do_liet_ke(reply)
    quy_trinh = dem_mat_do_quy_trinh(reply)
    if thread_id and (nguyen_tac >= NGUONG_LIET_KE or quy_trinh >= NGUONG_QUY_TRINH):
        thread_signals.tang("OUT-LO-CHI-THI", thread_id)
    return {"nguyen_tac": nguyen_tac, "quy_trinh": quy_trinh}
