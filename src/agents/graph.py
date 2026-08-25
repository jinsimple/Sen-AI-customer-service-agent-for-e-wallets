"""LangGraph agent cho luồng khiếu nại lõi (PRD §6) — entrypoint duy nhất
`run_agent_turn()`, gọi từ `POST /agent/chat` (src/api/main.py).

Lưu ý API: `langgraph.prebuilt.create_react_agent` đã deprecated ở bản
langgraph 1.2.10/langchain 1.3.14 đang cài — dùng `langchain.agents.create_agent`
thay thế (tham số prompt tên là `system_prompt`, không phải `prompt`)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from openai import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from opentelemetry.trace import Status, StatusCode
from sqlalchemy.orm import Session

from src.agents import llm_pool
from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.agents.output_filter import loc_dau_ra, tin_hieu_lo_chi_thi
from src.agents.phan_luong import (
    BAM_LUAT,
    DUONG_DAY_DU,
    DUONG_NHE,
    DUONG_THU_SLOT,
    HOI_SANG_LOC_LUA_DAO,
    HOI_THIEU_SO_TIEN,
    HOI_THOI_GIAN_VA_SO_TIEN,
    TEN_TIN_HIEU_1B,
    TRA_LOI_NHE,
    co_du_de_thu_hep,
    la_khieu_nai_ca_nhan,
    la_tra_loi_khang_dinh,
    phan_luong,
)
from src.agents.prompt import bam_mau_prompt, build_system_prompt
from src.agents.tools.customer_tools import TurnGuard, _otp_fresh, build_customer_tools
from src.config import (
    AGENT_TURN_TIMEOUT_SECONDS,
    CONG_OTP_NHOM_B_BAT,
    CONG_T0_BAT,
    DATABASE_URL,
    DB_KIND,
    KENH_HO_TRO_KHAC,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    OPENAI_MAX_RETRIES,
    OPENAI_TIMEOUT_SECONDS,
    OTP_VIEW_MAX_MINUTES,
    PHAN_LUONG_BAT,
    SUY_LUAN_BAT,
)
from src.cong_ra_ngoai import cong_chi_tieu, ghi_nhan_chi_tieu_khong_doc_duoc, http_client_dung_chung
from src.dau_ma_nguon import CACH_BAM, nhan_luc_dung
from src.db.models import Complaint, Ticket, User
from src.observability.langchain_callback import OTelTracingCallbackHandler
from src.observability.pii import scrub_pii
from src.observability.so_usage import ghi_usage
from src.observability.tracing import get_tracer
from src.services.complaint_intake import flag_human_handoff, hop_nhat_tin_hieu_gian_lan
from src.services.emotion_signals import danh_gia_luot
from src.services.thread_signals import dat_lai as xoa_tin_hieu
from src.services.thread_signals import doc_hoac_khong_ro as doc_tin_hieu
from src.services.thread_signals import tang as tang_tin_hieu
from src.tools.base import ToolError

_tracer = get_tracer("fin05.agent")
_logger = logging.getLogger("fin05.agents.graph")

# CONSUME-002 (FIN05_QA_TestCases.jsonl, OWASP LLM10:2025 Unbounded
# Consumption) — mặc định thật của langgraph đang cài (xác nhận trực tiếp
# `langgraph._internal._config.DEFAULT_RECURSION_LIMIT`) là 10007 bước, thực
# chất tương đương KHÔNG có giới hạn (đốt hết ngân sách OpenAI/timeout rất
# lâu trước khi chạm ngưỡng đó nếu agent kẹt vòng lặp gọi tool mơ hồ liên
# tục). 20 đủ cho vài vòng ReAct thật (LLM suy luận + gọi tool xen kẽ), thấp
# hơn nhiều để chặn lặp vô hạn.
_AGENT_RECURSION_LIMIT = 20


class TraLoiRongError(RuntimeError):
    """Model trả nội dung rỗng vì HẾT TRẦN TOKEN — lỗi cấu hình của TA.

    Có lớp riêng để bộ đo phân biệt được nó với mọi lỗi khác. Nuốt nó thành
    một câu trả lời rỗng nghĩa là thước sẽ ghi "model trả lời kém" cho một
    lỗi hạ tầng của chính ta — tính nhầm lỗi của mình thành lỗi nhà cung cấp.
    """

# JSON schema của 5 tool gửi kèm MỌI lượt gọi model — hằng số, đo 2026-08-16.
# Đổi khi thêm/bớt tool. Xem giải thích ở chỗ dựng `usage["input_chars"]`.
_CHARS_TOOL_SCHEMA = 6773

# Số tool bind ở lần dựng agent gần nhất trong tiến trình này. Ghi bởi tầng
# DỰNG REQUEST, không phải bởi tầng quyết định — xem chú thích tại chỗ gán.
_SO_TOOL_GUI = 0

# Suy luận có BẬT ở lần dựng model gần nhất không — đọc ngược từ đối tượng
# model, không từ config. Xem chú thích tại chỗ gán.
_SUY_LUAN_GUI = True

# ═══ CỔNG THU SLOT SAU KHI XÁC THỰC OTP GIỮA HỘI THOẠI ═══════════════════
# (scratchpad/nhap-cong-thu-slot-sau-otp.md, Lead 24/08, PO thật đề xuất,
# PO-agent duyệt cả 4 mục)
#
# VẤN ĐỀ: sau khi khách xác thực OTP giữa hội thoại, frontend TỰ GỬI LẠI câu
# đã bị chặn (ChatClient.tsx::submitOtp() -> pendingStarterRef). `5e8deb6`
# dạy model GỌI LẠI tool thay vì lặp kết luận cũ từ trí nhớ — vá TRIỆU
# CHỨNG, giữ nguyên làm LƯỚI ĐỠ (model không nghe luật thì vẫn có lưới này
# nếu resend đã đủ slot). Cổng này BỎ HẲN tình huống phải trông cậy vào việc
# model "nhớ đúng": hỏi thêm slot bằng cơ chế TẤT ĐỊNH trước, rồi gọi model
# ĐÚNG MỘT lần với đủ dữ liệu.
#
# KHOÁ RIÊNG, TUYỆT ĐỐI KHÔNG dùng chung `TEN_TIN_HIEU_1B` — Lead phản biện
# khung PO-agent nghiêng về ban đầu ("reset mốc S7 = điểm bắt đầu mới"):
# reset ĐÚNG KHOÁ S7 sẽ cho 1B bắn LẦN THỨ HAI trong cùng hội thoại ở một
# lượt sau KHÔNG liên quan gì cổng này — đúng thứ S7 (giới hạn 1 lần/hội
# thoại của 1B) sinh ra để cấm. Khoá dưới đây ĐỘC LẬP hoàn toàn với 1B; đừng
# "tối ưu" bằng cách gộp hai khoá dù tên nghe giống nhau.
_TEN_TIN_HIEU_OTP_RESEND = "otp_resend_da_hoi"

# ⑭ (25/08) — BẰNG CHỨNG PHÍA SERVER rằng thread này TỪNG bị cổng OTP chặn.
# KHÁC hẳn `_TEN_TIN_HIEU_OTP_RESEND` ở trên (thứ đó ghi "T0 ĐÃ HỎI rồi"). Hai
# khoá, hai câu hỏi khác nhau — đừng gộp dù tên nghe gần nhau.
_TEN_TIN_HIEU_DA_BI_OTP_CHAN = "da_bi_otp_chan"

# ⑨ — "đã hỏi câu sàng lọc lừa đảo cho thread này rồi". Một lần/hội thoại.
_TEN_TIN_HIEU_DA_HOI_SANG_LOC = "da_hoi_sang_loc"
DUONG_OTP_RESEND_THU_SLOT = "otp_resend_thu_slot"
DUONG_CAN_OTP = "can_otp"
DUONG_FS13_BAN_GIAO = "fs13_ban_giao"

# Slot mục tiêu là MÃ GIAO DỊCH HOẶC MỐC THỜI GIAN — KHÁC 1B (số tiền là
# slot bắt buộc của 1B). Lý do: 1B áp cho lượt ĐẦU TIÊN chưa biết gì; cổng
# này áp cho điểm khách đã mô tả đủ để model quyết định gọi tool (đó là lý
# do tool chạy và bị OTP chặn) — cái còn thiếu là thứ giúp tool THU HẸP
# xuống một kết quả, đúng vai trò mã/ngày (số tiền nhiều khả năng ĐÃ có
# trong câu, vì đó là chi tiết khách hay kể đầu tiên).

# ── ⑧ · K3 — HAI CÂU CHỐNG MẠO DANH CSKH ────────────────────────────────────
# Phiếu "OTP trước token" ⑧. Hằng số, 0 token, KHÔNG giao model diễn đạt —
# cùng lệ ADR-048 ("một dòng TẤT ĐỊNH chèn sau khi tool trả về; không đặt cược
# an toàn vào việc model nghe lời").
#
# 🔴 K3 đo được: dự án ép rất chặt việc bot KHÔNG hỏi OTP giao dịch, nhưng
# chưa chỗ nào bắt bot NÓI CHO KHÁCH BIẾT nó sẽ không bao giờ hỏi. Khách vừa
# bị lừa một lần rồi thì lần thứ hai kẻ giả CSKH gọi tới, thứ duy nhất bảo vệ
# họ là việc họ ĐÃ ĐƯỢC NGHE câu này từ CSKH thật.
#
# ⚠️ ĐỔI XƯNG HÔ so với nguyên văn phiếu — khai để không ai tưởng chép sót:
# phiếu viết "chị" vì trích thẳng kịch bản chuyên gia (khách trong kịch bản là
# nữ). Hằng số này bắn cho MỌI khách, và hệ thống KHÔNG biết giới tính khách
# (`customer_name` cố ý không đưa lên LLM, PII-OK ở dưới). Dùng "bạn"/"mình"
# — đúng xưng hô mọi hằng số khác của module này đã dùng. Nội dung, thứ tự vế
# và điểm gắn giữ nguyên 100% theo phiếu.
#
# 🔴 CHÈN SAU `loc_dau_ra()`, CÓ CHỦ ĐÍCH — không phải tiện tay.
#
# [ĐO 24/08] chạy `loc_dau_ra()` thẳng trên CẢ HAI hằng số: **cả hai QUA
# ĐƯỢC**, không nhóm O nào khớp. Nói cách khác, hôm nay dời điểm chèn lên
# trước bộ lọc KHÔNG gây hỏng — tôi đã viết ngược điều này ở bản nháp, phép
# đo bác lại, giữ lại số đo thay vì lập luận.
#
# Vẫn chèn SAU, vì lý do khác và bền hơn:
#   ① Hai câu này là văn bản của TA, đã soát, KHÔNG chứa chữ số nào — cho bộ
#     lọc kiểm chúng là tốn công kiểm thứ đã biết đúng.
#   ② Biên an toàn MỎNG theo hướng có thật: câu thứ hai chứa "sẽ" (đã nằm
#     trong `_O4_DONG_TU`) đứng cùng mệnh đề với "lấy lại tiền". Nó chưa khớp
#     CHỈ vì `_O4_TIEN` hiện không có cụm "lấy lại tiền" (có "nhận lại tiền").
#     Thêm đúng một cụm vào `_O4_TIEN` — việc O4 hoàn toàn có thể làm sau này
#     — là bản vá an toàn tự xoá chính nó, IM LẶNG, không cổng nào đỏ.
# ⟹ Chèn sau bộ lọc làm ② không thể xảy ra, thay vì canh chừng nó mãi.
CANH_BAO_OTP_PHIEN = (
    "Mình nói rõ để bạn yên tâm: đây là mã xác thực phiên hỗ trợ, không phải "
    "mã OTP giao dịch — mình không bao giờ hỏi mã OTP giao dịch hay mật khẩu "
    "ví của bạn."
)
# 🔴 THÊM HAI DẠNG 25/08 (Review tìm, PO xếp "làm ngay"). Bản đầu chỉ có BA lưới
# (OTP · mật khẩu · chuyển tiền). Thiếu **phí xử lý/xác minh** và **cài app điều
# khiển từ xa** — hai chiêu phổ biến nhất ở ví điện tử VN.
#
# Vì sao thiếu ĐÚNG hai cái đó lại nguy nhất: **chính ta vừa dựng sân khấu cho
# chúng.** Bot vừa nói với một người NGHI BỊ LỪA rằng *"sẽ có chuyên viên liên hệ
# lại"* — khách nay ĐANG CHỜ một cuộc gọi và không phân biệt được thật giả.
#   · "nộp phí xác minh 50k là em đẩy lệnh hoàn tiền ngay"  ← khách ĐANG CHỜ hoàn
#     tiền, số tiền NHỎ ⟹ hàng rào tâm lý thấp nhất
#   · "anh cài app này để em vào máy hỗ trợ"                ← khách ĐANG MONG được hỗ trợ
# Ba chiêu đã có đều đòi khách làm một việc NGHE ĐÃ ĐÁNG NGỜ. Hai chiêu này nghe
# HOÀN TOÀN HỢP LÝ trong đúng bối cảnh ta vừa tạo ra.
#
# Gộp thành MỘT câu, không tách dòng: cảnh báo dài thì khách không đọc — và một
# cảnh báo không được đọc hỏng y như không có.
# Mệnh đề cuối ("kể cả khi họ nói là để lấy lại tiền cho bạn") vô hiệu hoá đúng
# CÁI CỚ mà cả năm chiêu đều mượn, thay vì liệt kê thêm chiêu thứ sáu.
CANH_BAO_KHONG_AI_GOI_DIEN = (
    "Một lưu ý để bạn giữ an toàn: sẽ không có ai từ ví gọi điện yêu cầu bạn "
    "chuyển tiền, nộp phí xử lý, cài ứng dụng điều khiển từ xa, hay cung cấp "
    "mật khẩu và mã OTP — kể cả khi họ nói là để lấy lại tiền cho bạn."
)

# ④ · câu của cổng OTP tất định. Ghép sẵn câu chống mạo danh ⑧ (K3) — ĐÂY mới là
# "lượt 1" mà phiếu nói tới: điểm đầu tiên khách được yêu cầu xác thực. Ghép ngay
# ở hằng số chứ không qua `_them_canh_bao_mao_danh()`: đường này KHÔNG đi qua bộ
# lọc nên không có chỗ "chèn sau", và ghép cứng làm nó hiển nhiên khi đọc.
_CAN_XAC_THUC_OTP = (
    "Dạ để tra cứu giao dịch của bạn thì mình cần bạn xác thực OTP phiên làm "
    "việc trước nhé.\n\n" + CANH_BAO_OTP_PHIEN
)

# ① (PO thật thu hẹp 25/08) — khách XÁC NHẬN có người hướng dẫn chuyển khoản.
# PO nguyên văn: *"không cần làm sâu, chỉ cần BÁO SẼ CÓ CHUYÊN GIA LIÊN HỆ là đủ."*
#
# Hai việc, không hơn:
#   ① NGỪNG đường khuyên chuyển-nhầm — đạt bằng cách KHÔNG gọi model lượt này.
#      Cấm bằng lời thì model vẫn có thể nói; không chạy thì nó không nói được.
#   ② báo sẽ có chuyên viên liên hệ + bàn giao người thật.
#
# 🔴 CÂU K3 GHÉP VÀO ĐÂY LÀ BẮT BUỘC, KHÔNG PHẢI TRANG TRÍ. Ta vừa nói với một
# người NGHI BỊ LỪA rằng "sẽ có người liên hệ lại" — đó chính là câu kẻ lừa đảo
# cần để gọi lần hai ("em ở bộ phận xử lý khiếu nại đây"). Báo sẽ có người gọi
# mà không kèm câu này là tự tay dọn đường cho vòng lừa thứ hai.
_FS13_BAN_GIAO = (
    "Cảm ơn bạn đã cho mình biết. Trường hợp này mình chuyển ngay cho chuyên "
    "viên hỗ trợ xử lý trực tiếp, sẽ có người liên hệ lại với bạn.\n\n"
    + CANH_BAO_KHONG_AI_GOI_DIEN
)

# Neo nhận diện "câu này đã có sẵn trong lời model" — tránh nói hai lần. Chọn
# cụm ĐỦ DÀI và ĐẶC HIỆU (đúng bài học "sao"/"mất" của 1B): "OTP" trần khớp cả
# câu model đang giải thích chuyện khác.
_NEO_DA_CO_CANH_BAO = (
    "không bao giờ hỏi mã otp giao dịch",
    "không có ai từ ví gọi điện",
)


def _them_canh_bao_mao_danh(reply: str, *, co_loi_otp: bool, ticket_id: str | None) -> str:
    """Chèn câu chống mạo danh vào CUỐI `reply` — hàm THUẦN, dễ kiểm.

    `co_loi_otp`: lượt này có tool nào bị cổng OTP chặn không (khách đang ở
    đúng thời điểm được yêu cầu xác thực — điểm gắn "lượt 1" của phiếu).
    `ticket_id`: có mã hồ sơ để báo không (điểm gắn "lượt 8").

    KHÔNG chèn nếu model đã tự nói ý đó — nói hai lần làm câu cảnh báo trông
    như văn bản máy dán vào, và khách sẽ học cách bỏ qua nó.
    """
    if not isinstance(reply, str):
        return reply
    thap = reply.lower()
    them: list[str] = []
    if co_loi_otp and _NEO_DA_CO_CANH_BAO[0] not in thap:
        them.append(CANH_BAO_OTP_PHIEN)
    if ticket_id is not None and _NEO_DA_CO_CANH_BAO[1] not in thap:
        them.append(CANH_BAO_KHONG_AI_GOI_DIEN)
    if not them:
        return reply
    return (reply.rstrip() + "\n\n" + "\n\n".join(them)).strip()


# Kích thước lược đồ tool ĐO ĐƯỢC ở lần dựng gần nhất — thay hằng số gõ tay.
_CHARS_TOOL_SCHEMA_THAT = _CHARS_TOOL_SCHEMA

def _giay_cho_lai(loi: Exception) -> float | None:
    """Moi so giay nha cung cap BAO, khong tu doan.

    OpenAI tra nguyen van "Please try again in 1.381s" trong than loi. Doc
    dung so do de noi voi khach, thay vi bia mot con so nghe hop ly — cung
    tinh than rang buoc cung 3: con so noi ra phai co nguon.

    Khong tra duoc thi tra None, va cau tra loi noi "sau it giay" thay vi mot
    con so gia.
    """
    m = re.search(r"try again in ([0-9.]+)s", str(loi))
    return float(m.group(1)) if m else None


# ═══ Phân loại lỗi NHÀ CUNG CẤP ════════════════════════════════════════════
#
# `APIError` là ranh giới CHÍNH XÁC của họ này: mọi lỗi nhà cung cấp đều kế
# thừa nó (đã kiểm cây thừa kế trên openai==3.0.0 đang chạy: 401/403/400/404/
# 429/5xx đi qua APIStatusError, timeout/rớt mạng đi qua APIConnectionError,
# cả hai đều dưới APIError), và KHÔNG lỗi nào của ta lọt vào. Bắt rộng hơn
# (`Exception`) sẽ nuốt cả bug của chính mình thành "hệ thống bận".
#
# VÌ SAO CẦN: trước bản này `except` khoá vào ĐÚNG MỘT TÊN — `RateLimitError`.
# Nhưng thứ cần xử lý không phải một tên, mà là TRẠNG THÁI "nhà cung cấp không
# phục vụ lượt này". 429 chỉ là một trong các cách họ từ chối; 6 lớp còn lại
# rơi thẳng ra HTTP 500 trần. tester quan sát được trên đường thật khi hạn mức
# Qwen cạn giữa buổi: hết giờ -> 200 + vé fallback, nhưng 403 -> 500, không vé,
# không gì cả.
#
# ⚠️ TUYỆT ĐỐI KHÔNG nối họ này vào nhánh fallback-TẠO-VÉ bên dưới. Lý do đã
# đúng với 429 (chú thích ở nhánh đó), và MẠNH HƠN với 401/403: hết hạn mức là
# hỏng TOÀN CỤC, nó đánh mọi khách cùng lúc ⟹ tạo vé nghĩa là một vé cho mỗi
# khách đang online. Trong buổi 150 người đó là 150 vé ma trong một phút, cho
# những khiếu nại KHÔNG TỒN TẠI — và làm loãng đúng hàng chờ mà vé "AI bó tay"
# cần được nhìn thấy.

# Bốn lớp mà KHÁCH THỬ LẠI BAO NHIÊU LẦN CŨNG KHÔNG HẾT — phải có người xử.
# 400/404 là lỗi CỦA TA (sai model/tham số), không phải sự cố nhà cung cấp;
# xếp chung ở đây vì đứng từ phía khách chúng giống hệt nhau: chờ không hết.
_LOI_CAN_CAN_THIEP = (
    AuthenticationError,      # 401 khoá sai / vừa xoay / hết hạn
    PermissionDeniedError,    # 403 hết hạn mức HOẶC sai quyền
    BadRequestError,          # 400 lỗi của ta
    NotFoundError,            # 404 lỗi của ta
)

# Dấu hiệu "hết tiền" trong thân thông báo. CỐ Ý chỉ dùng cho MỘT trường log,
# không bao giờ cho thứ khách nhìn thấy:
#   `403 free quota exhausted` của DashScope CÙNG LỚP PermissionDeniedError với
#   403 sai quyền. Tách hai ca bắt buộc phải so chuỗi -> mong manh theo từng
#   nhà cung cấp, và hỏng IM LẶNG khi họ đổi câu chữ.
#   Luật: một phép phân biệt MONG MANH chỉ được điều khiển hậu quả RẺ. Sai ở
#   đây tốn một nhãn log lệch (tự lộ ngay khi người vận hành mở ra xem). Nếu
#   nó điều khiển "khách thấy gì" thì một lần đổi câu chữ = khách nhận 500.
_DAU_HIEU_HET_HAN_MUC = ("quota", "exhaust", "insufficient", "balance", "arrear", "unpurchased")


def _mo_ta_loi_nha_cung_cap(loi: APIError, *, model: str = LLM_MODEL) -> dict[str, object]:
    """Trường để hồi cứu sự cố. KHÔNG chứa thân thông báo thô.

    Thân thô có thể mang khoá hoặc định danh nội bộ; ta chỉ rút ra một cờ
    boolean từ nó. Đủ để người vận hành biết "hết tiền hay sai khoá", không đủ
    để rò thứ gì ra log.

    `model`: model ĐANG ĐƯỢC THỬ khi lỗi này xảy ra (GĐ3 — vòng xoay truyền
    tường minh). Mặc định `LLM_MODEL` chỉ để không vỡ caller cũ không xoay.
    """
    than = (str(getattr(loi, "message", "") or str(loi))).lower()
    return {
        "lop_loi": type(loi).__name__,
        "ma_trang_thai": getattr(loi, "status_code", None),
        # GĐ3 — GIẢ ĐỊNH, không phải bất biến: mọi model trong LLM_MODEL_POOL
        # dùng CHUNG `LLM_BASE_URL` (đúng cho bể deepseek hôm nay, cùng tài
        # khoản DashScope). Nếu sau này bể có model KHÁC base_url, trường này
        # sẽ sai theo đúng kiểu lỗi vừa vá cho `model` — hồi cứu ĐÚNG model
        # NHƯNG SAI nhà cung cấp. Ghi ra để người thêm model-khác-base_url
        # biết phải sửa CHỖ NÀY, không phát hiện lại từ đầu.
        "nha_cung_cap": LLM_BASE_URL or "openai",
        "model": model,
        "can_can_thiep": isinstance(loi, _LOI_CAN_CAN_THIEP),
        "co_dau_hieu_het_han_muc": any(d in than for d in _DAU_HIEU_HET_HAN_MUC),
        # `request_id` của nhà cung cấp: CHÍNH thứ bộ phận hỗ trợ của họ hỏi khi
        # ta khiếu nại hoá đơn/hạn mức — không có nó thì hồi cứu với họ là bất
        # khả (security ④). Không phải bí mật, không phải PII. CHỈ dùng trong hồ
        # sơ nội bộ, KHÔNG bao giờ đưa ra khách.
        "request_id_ncc": getattr(loi, "request_id", None),
    }


def _ghi_so(kq: dict, thread_id: str | None, user_id: str) -> None:
    """Ghi MỘT dòng sổ usage cho MỌI đường ra của `run_agent_turn`.

    Đặt ở một hàm vì bài học vừa trả giá: bản đầu tôi gắn `ghi_usage` ngay
    trước `return` cuối cùng — và MỌI đường fallback (429 · lỗi nhà cung cấp ·
    hết giờ · recursion) `return` SỚM, không bao giờ tới đó. Sổ kế toán vắng
    mặt đúng những lượt HỎNG, tức nó đếm thiếu số lượt và đọc thành "ít lượt
    hơn thực tế" chứ không thành một khoảng trống nhìn thấy được.

    Cùng hình dạng với ca `flag_human_handoff` sáng nay: một cơ chế đúng, gắn
    đúng chỗ nó được nghĩ ra, và không ai đi tìm chỗ thứ hai cùng lớp. Ở đây
    "chỗ thứ hai" là bốn `return` khác.

    `ly_do_fallback` lấy TỪ CHÍNH dict trả về, không dựng lại — hai nguồn sẽ
    lệch nhau, và lệch trong im lặng.
    """
    u = kq.get("usage") or {}
    # GĐ3 — trần chi tiêu tối giản (876a240). Gọi VÔ ĐIỀU KIỆN — hàm tự bỏ
    # qua khi `total_tokens is None` (đường fallback "không đọc được"), nên
    # đặt Ở ĐÂY (chạy trên CẢ 5 đường ra) đúng bằng thiết kế của chính hàm
    # này, không phải một lựa chọn riêng cho GĐ3. KHÔNG cộng lượt embedding —
    # xem docstring cong_chi_tieu().
    cong_chi_tieu(u.get("total_tokens"))
    # Lead đo 19/08: cờ `token_khong_doc_duoc` được GHI vào sổ usage.jsonl
    # nhưng không ai ĐỌC nó — trạng thái ghi-mà-không-ai-theo-dõi có cùng tác
    # dụng với không ghi. Đếm riêng (LƯỢT, không phải token — token đúng là
    # thứ không đọc được) để điểm mù của trần trở thành một con số đọc được.
    if u.get("token_khong_doc_duoc"):
        ghi_nhan_chi_tieu_khong_doc_duoc()
    ghi_usage({
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "thread_id": thread_id or user_id,
        # GĐ3 (876a240) — model THẬT đã trả lời/đang thử lượt này, ĐỌC TỪ
        # `kq` (mỗi đường trả về của run_agent_turn tự khai field này), KHÔNG
        # phải hằng số toàn cục `LLM_MODEL`. Sau khi xoay, model trả lời có
        # thể KHÁC model đã ghim — một hằng số ở đây sẽ ghi sai NGAY LƯỢT
        # XOAY ĐẦU TIÊN, và sổ này là "chứng từ đối soát hoá đơn" (PO
        # 876a240) — sai ở đây là mù hoàn toàn khi cần đối soát.
        "model": kq.get("model"),
        "models_da_thu": kq.get("models_da_thu"),
        # ĐO Ở ĐÂU. tester phải loại trừ ngăn xếp ttl bằng đường gián tiếp vì
        # "không bản ghi nào ghi URL của lượt đo" — cùng họ với mốc-thời-gian
        # của security. Một con số không tự khai NÓ ĐO Ở ĐÂU thì lần sau lại
        # phải điều tra như lần này.
        "base_url": LLM_BASE_URL or "openai",
        # VẬT nào sinh ra số này — KÈM cách băm, vì một chuỗi 12 hex không tự
        # khai nguồn gốc của nó. 17/08 đã mất một vòng vì tôi so md5 với sha256
        # của người khác rồi kết luận ".env đổi 4 lần". Sổ này được đọc lại sau
        # nhiều tháng, là chỗ tệ nhất để bỏ nhãn.
        "bam_ma_nguon": nhan_luc_dung(),
        "cach_bam": CACH_BAM,
        "so_luot_goi_model": u.get("so_luot_goi_model"),
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        # Review đo 19/08: field này TỪNG KHÔNG BAO GIỜ ra được `usage.jsonl`
        # — có mặt trong `kq["usage"]["total_tokens"]` (dùng cho `cong_chi_tieu`)
        # nhưng chưa từng được liệt vào dict truyền cho `ghi_usage`, ở BẤT KỲ
        # phiên bản nào (không phải chuyện schema cũ/mới — claim ban đầu của
        # tôi SAI, Review sửa). Không có dòng này thì sổ "chứng từ đối soát"
        # không cách nào lộ ra một lượt đã bị guard None-vs-0 (:1318) chạm tới.
        "total_tokens": u.get("total_tokens"),
        "token_khong_doc_duoc": u.get("token_khong_doc_duoc"),
        "cached_input_tokens": u.get("cached_input_tokens"),
        "reasoning_tokens": u.get("reasoning_tokens"),
        "input_chars": u.get("input_chars"),
        "so_tool_call": len(kq.get("tool_calls") or []),
        "ly_do_fallback": kq.get("ly_do_fallback"),
        # Ba trường TRIỆU CHỨNG, luôn có mặt (None ở lượt thường) — khoá thiếu
        # và khoá null đọc khác nhau ở mọi công cụ phân tích, và "thiếu khoá"
        # sẽ bị đọc thành "chưa bao giờ hỏng".
        "lop_loi_ncc": (kq.get("trieu_chung") or {}).get("lop_loi_ncc"),
        "ma_trang_thai_ncc": (kq.get("trieu_chung") or {}).get("ma_trang_thai_ncc"),
        "giay_da_troi": (kq.get("trieu_chung") or {}).get("giay_da_troi"),
        "duong": kq.get("duong"),
        "so_tool_schema_gui": u.get("so_tool_schema_gui"),
        # TRẠNG THÁI THẬT của lượt, không phải giá trị cờ config — nếu không có
        # trường này thì dòng R2 và R3 trong sổ KHÔNG phân biệt được khi đọc
        # lại sau nhiều tháng, mà sổ sinh ra để được đọc lại sau nhiều tháng.
        "suy_luan_gui": u.get("suy_luan_gui"),
        "co_ticket": bool(kq.get("ticket_id")),
    })


def _ly_do_fallback(loi: Exception) -> str:
    """Phân loại vì sao rơi vào fallback. Trả chuỗi, không bao giờ None.

    Nhánh mặc định `"khac"` là CÓ CHỦ ĐÍCH dù hôm nay nó không bao giờ bắn (chỉ
    có đúng một `except` dẫn tới fallback). Nó tồn tại cho NGÀY ai đó thêm đường
    fallback thứ ba mà quên khai: tester nhận được một giá trị lạ nhìn thấy ngay,
    thay vì một khoảng trống mà họ sẽ đọc nhầm thành "lượt bình thường".

    LƯU Ý cho người đọc biên bản: 429 quá tải HIỆN ĐANG đội lốt `"timeout"` —
    thời gian ngủ theo `retry_after` ăn vào ngân sách AGENT_TURN_TIMEOUT_SECONDS
    nên một lỗi tự-phục-hồi-được hiện ra như hết giờ. Tách nó cần một giá trị
    `"qua_tai"` và phải bắt RateLimitError ở tầng này — việc riêng, đã vào hồ sơ
    pilot, KHÔNG làm ở commit này.
    """
    if isinstance(loi, FutureTimeoutError):
        return "timeout"
    if isinstance(loi, GraphRecursionError):
        return "recursion_limit"
    return "khac"


def _trieu_chung_loi(loi: BaseException | None) -> dict[str, object]:
    """TRIỆU CHỨNG của lỗi, tách khỏi KẾT LUẬN về lỗi (Luật H).

    Vì sao cần, bằng ca thật: sổ ghi `ly_do_fallback = "nha_cung_cap_can_can_thiep"`.
    Đó là một KẾT LUẬN — nó nói *phải làm gì*, không nói *nhà cung cấp đã trả
    lời gì*. Hai sự cố khác hẳn nhau (`401` khoá sai · `403` hết hạn ngạch ·
    `404` sai tên model) đổ chung vào một nhãn, và cách xử ba ca đó KHÁC NHAU
    hoàn toàn — một cái nạp tiền, một cái sửa khoá, một cái sửa cấu hình.
    Người trực sự cố đọc sổ sẽ không phân biệt được, và sẽ đi thử cả ba.

    ⟹ Mã trạng thái đi VÀO SỔ, cạnh kết luận, không thay thế nó. Hai trường,
    hai câu hỏi: *"nhà cung cấp nói gì"* và *"ai phải làm gì"*.

    🔴 `None` ở đây nghĩa **KHÔNG ĐỌC ĐƯỢC** (lỗi không mang mã trạng thái —
    hết giờ, vòng lặp), KHÔNG phải "mã 0". Cùng quy ước với `input_tokens`.
    """
    if loi is None:
        return {"lop_loi_ncc": None, "ma_trang_thai_ncc": None}
    ma = getattr(loi, "status_code", None)
    return {
        "lop_loi_ncc": type(loi).__name__,
        # ép về int hoặc None — vài SDK trả chuỗi, và một chuỗi lọt vào sổ sẽ
        # làm mọi phép lọc `>= 500` im lặng trả rỗng thay vì báo lỗi.
        "ma_trang_thai_ncc": int(ma) if isinstance(ma, (int, str)) and str(ma).isdigit() else None,
    }


def _reply_goc_cho_eval(reply_goc: str, nhom_khop: list[str]) -> dict:
    """Câu TRƯỚC KHI LỌC — chỉ khi bật cờ, chỉ khi thật sự có chặn.

    Vì sao tester cần: `loc_dau_ra=["O3"]` cho biết bộ lọc ĐÃ chặn, nhưng không
    cho biết chặn ĐÚNG hay siết NHẦM. Không đọc được thứ bị nuốt thì mọi ca bị
    chặn đều "đạt" theo bộ chấm (câu an toàn không vi phạm bất biến nào), và
    lượt "sau" trông đẹp hơn lượt "trước" trong khi bộ lọc có thể đang siết nhầm
    hàng loạt — confound hướng-có-lợi, loại nguy hiểm nhất.

    Vì sao KHÔNG bật mặc định: câu này chính là thứ bộ lọc tồn tại để không cho
    ra ngoài. Ship nó trong envelope production là tự mở lại đúng cái cửa vừa
    đóng, và nó sẽ chảy tiếp vào log/trace/bên thứ ba. Fail-closed: thiếu biến
    môi trường thì KHÔNG trả.
    """
    if os.environ.get("FIN05_EVAL_GIU_REPLY_GOC") != "1" or not nhom_khop:
        return {}
    return {"reply_truoc_loc": reply_goc}


def _nang_uu_tien_theo_cam_xuc(session: Session, *, ticket_id: str) -> None:
    """ES bật -> nâng `complaints.priority`, TRẦN LÀ `high`. CHỈ NÂNG.

    KHÔNG BAO GIỜ lên `critical`: mức đó thuộc về FS-06 (nghi gian lận). Cho bức
    xúc leo lên cùng mức nghi gian lận là làm hỏng ĐÚNG hàng đợi quan trọng nhất
    — người trực hết phân biệt được "khẩn vì rủi ro tiền" với "khẩn vì khách
    đang giận", và họ sẽ mất niềm tin vào chính cái nhãn critical.

    KHÔNG BAO GIỜ HẠ: ES tắt ở lượt sau không có nghĩa vấn đề nhẹ đi. Hạ xuống
    là xoá dấu vết một lần khách đã căng, mà CSKH cần thấy điều đó khi mở hồ sơ.
    """
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None or complaint.priority in ("high", "critical"):
        return
    complaint.priority = "high"
    session.flush()


def _build_checkpointer():
    """Nơi lưu bộ nhớ hội thoại của agent — quyết định KIẾN TRÚC, không chỉ kỹ thuật.

    TRƯỚC 2026-08-13: `MemorySaver()` giữ toàn bộ hội thoại trong RAM của MỘT
    process. Hệ quả kéo dài suốt dự án:
      - Backend BẮT BUỘC chạy đúng 1 worker (ghi rõ trong Dockerfile). Máy 10
        vCPU chỉ dùng được 1 — lãng phí 90% năng lực, và 150 người dùng đồng
        thời chia chung một event loop duy nhất.
      - Restart backend = MỌI khách mất sạch ngữ cảnh giữa chừng. Với buổi test
        150 người, một lần deploy/crash là hỏng cả buổi.

    PostgresSaver đưa state ra ngoài process (đúng nguyên tắc "stateless
    processes" của 12-Factor), mở đường cho multi-worker VÀ giúp hội thoại sống
    sót qua restart.

    FALLBACK CÓ CHỦ ĐÍCH, KHÔNG IM LẶNG: test chạy trên SQLite (conftest tạo
    engine tạm riêng mỗi test) — PostgresSaver không chạy được ở đó. Rơi về
    MemorySaver khi DB không phải Postgres là ĐÚNG cho test, nhưng phải GHI LOG
    rõ ràng, không lặp lại bài học DATABASE_URL (ADR-013): một fallback im lặng
    từng làm hệ thống âm thầm tách đôi database.

    🔴 RACE dưới multi-worker trên DB RỖNG [ĐO DevOps 20/08]: hàm này chạy lại
    ở MỖI process import `graph` — tức MỖI uvicorn worker (module-level
    singleton, không phải chạy một lần cho cả app). `saver.setup()` bên dưới
    CHỈ idempotent khi tuần tự; N worker cùng gọi CREATE TABLE lần đầu (chưa
    ai thấy bảng tồn tại) đụng `UniqueViolation` trên `pg_type` (Postgres tự
    đăng ký row type cho mỗi bảng mới). Bắt buộc: entrypoint phải "hâm nóng"
    lược đồ MỘT LẦN, TUẦN TỰ, TRƯỚC khi spawn worker nào — vd
    `python -c "import src.agents.graph as g; g.close_checkpointer()"` ngay
    sau `alembic upgrade head`. Sau bước đó, `saver.setup()` ở mỗi worker mới
    thật sự là no-op (lược đồ đã có, không còn CREATE nào để đua) — ĐÚNG như
    chú thích "idempotent" ở dòng gọi `saver.setup()` bên dưới, nhưng chỉ khi
    có bước hâm nóng này đi trước, không phải tính chất tự thân của nó.

    Xem ADR-014.
    """
    if DB_KIND != "postgresql":
        _logger.warning(
            "checkpointer_in_memory",
            extra={"db_kind": DB_KIND, "ly_do": "DB không phải Postgres — hội thoại "
                   "chỉ nằm trong RAM, mất khi restart, KHÔNG chạy được multi-worker. "
                   "Bình thường với test/SQLite; nếu thấy dòng này ở production là SAI."},
        )
        return MemorySaver()

    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg_pool import ConnectionPool

    # DATABASE_URL ở dạng SQLAlchemy (postgresql+psycopg2://) — psycopg3 mà
    # langgraph dùng cần dạng chuẩn (postgresql://). Đổi ở đây thay vì bắt
    # người vận hành khai 2 biến dễ lệch nhau.
    conninfo = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
    pool = ConnectionPool(
        conninfo=conninfo,
        max_size=_CHECKPOINT_POOL_MAX,
        # autocommit BẮT BUỘC: PostgresSaver tự quản giao dịch của nó, để
        # psycopg mở transaction ngầm sẽ giữ khoá và treo khi nhiều worker ghi.
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=True,
    )
    saver = PostgresSaver(pool)
    saver.setup()  # idempotent CHỈ khi entrypoint đã hâm nóng lược đồ trước — xem docstring hàm này
    global _CHECKPOINT_POOL
    _CHECKPOINT_POOL = pool  # giữ tham chiếu để đóng sạch lúc shutdown
    _logger.info("checkpointer_postgres", extra={"pool_max": _CHECKPOINT_POOL_MAX})
    return saver


def close_checkpointer() -> None:
    """Đóng pool của checkpointer — gọi từ FastAPI shutdown (src/api/main.py).

    ConnectionPool của psycopg chạy thread nền; không đóng tường minh thì lúc
    interpreter thoát sẽ ném `PythonFinalizationError: cannot join thread at
    interpreter shutdown` (đã gặp thật lúc verify). Với server chạy dài thì
    lỗi này chỉ bẩn log lúc tắt, nhưng graceful shutdown là yêu cầu bắt buộc
    của checklist đóng gói production — và pool không đóng còn giữ kết nối
    Postgres cho tới khi TCP timeout, ăn vào max_connections khi deploy liên tục.
    """
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL is not None:
        try:
            _CHECKPOINT_POOL.close()
            _logger.info("checkpointer_pool_closed")
        except Exception as e:  # noqa: BLE001 — shutdown không được ném lỗi ra ngoài
            _logger.warning("checkpointer_pool_close_failed", extra={"loi": repr(e)})
        finally:
            _CHECKPOINT_POOL = None


# Pool riêng cho checkpointer, TÁCH khỏi pool của SQLAlchemy: hai thứ này có
# nhịp truy cập khác nhau (checkpoint ghi mỗi bước ReAct, ORM đọc/ghi nghiệp vụ)
# và gộp chung sẽ làm nghẽn lẫn nhau. Tổng kết nối = workers x (pool ORM + pool
# này) phải nhỏ hơn max_connections của Postgres (mặc định 100).
_CHECKPOINT_POOL_MAX = int(os.environ.get("CHECKPOINT_POOL_MAX", "5"))
_CHECKPOINT_POOL = None  # gán trong _build_checkpointer(), đóng ở close_checkpointer()

# Singleton module-level: agent được build lại mỗi request (session/tools gắn
# với request đó), nhưng checkpointer dùng chung 1 instance nên lịch sử hội
# thoại nối tiếp được qua nhiều request cùng thread_id.
_CHECKPOINTER = _build_checkpointer()


def doc_transcript_bang_giao(thread_id: str) -> dict[str, object] | None:
    """ADR-044 — đọc hội thoại bot↔khách của MỘT thread cho route
    `GET /tickets/{ticket_id}/transcript` (src/api/main.py). Đọc qua
    `checkpointer.get_tuple()` — KHÔNG parse thẳng bảng `checkpoint_*`
    (chi tiết triển khai của LangGraph, đổi giữa các phiên bản, ADR-044
    mục 5).

    Trả `None` khi thread_id KHÔNG có checkpoint nào — route phía trên tự
    diễn giải thành "không tra được" kèm lý do, hàm này KHÔNG tự bịa lý do
    (tách rõ trách nhiệm: hàm này chỉ đọc, route quyết định thông điệp).

    PII: checkpoint lưu bản ĐÃ SCRUB (`HumanMessage` dựng từ `scrub_pii(...,
    muc_dich="model_input")` tại :790) — hàm này KHÔNG scrub lại, đúng
    ADR-044 mục "PII — GIẢI XONG bằng phép đo". Nhãn che SAI (vd
    `[PERSON_VN]` thay từ khách gõ thật, trước bản vá D') vẫn còn nguyên
    trong checkpoint CŨ — route/UI phải tự khai điều này, hàm này không
    sửa ngược bằng chứng.

    Trả `{"luot": [...], "chi_so_bang_giao": int | None}`.
      - `luot`: mỗi lượt là `vai` ("khach"/"bot") + `noi_dung` + `co_goi_tool`
        (bot đã gọi tool ngay trước khi sinh câu trả lời này hay chỉ là lời
        thoại suông — CSKH cần phân biệt câu nào dựa trên dữ liệu thật).
      - `chi_so_bang_giao`: chỉ số (0-based) của LƯỢT CUỐI CÙNG "phía trên
        vạch" — tức lượt bot xác nhận NGAY SAU khi tool `request_human_
        handoff` chạy. UI vẽ vạch phân cách ngay sau lượt này. `None` nếu
        hội thoại KHÔNG có lần gọi `request_human_handoff` nào (transcript
        đọc được nhưng chưa từng bàn giao — vd CSKH tự mở vé, không qua
        yêu cầu của khách). KHÔNG dùng `handoff_at` (mốc DB) để suy ra vị
        trí này — không có timestamp per-message để so khớp, dùng đúng SỰ
        KIỆN sinh ra bàn giao (lời gọi tool) chính xác hơn một phép so mốc
        thời gian gián tiếp.

        HAI ca đặc biệt cùng cho `chi_so_bang_giao=None` dù `handoff_at` (DB)
        có giá trị — route/UI xử lý GIỐNG NHAU (hiện note thay vì vạch), nhưng
        NGUYÊN NHÂN khác nhau, đừng gộp khi đọc/giải thích lại:

        (a) ĐÃ KHAI 19/08 (PO-agent phát hiện, không phải bug): vé sinh từ
            nhánh timeout/bỏ lượt — `flag_human_handoff(...)` gọi THẲNG,
            KHÔNG qua tool `request_human_handoff` mà LLM gọi. Transcript
            KHÔNG có `ToolMessage` tên đó ở đâu cả — tự nhất quán, không một
            dấu vết nào của bàn giao trong hội thoại.

        (b) ĐÃ KHAI 20/08 (Review phát hiện khi soát toàn chuỗi): tool
            `request_human_handoff` ĐƯỢC LLM gọi THẬT (`ToolMessage` có mặt
            trong checkpoint), nhưng nó là message CUỐI CÙNG — lượt bị cắt
            (timeout/lỗi) ngay sau khi tool chạy xong, TRƯỚC khi model kịp
            sinh `AIMessage` xác nhận có nội dung. Vòng lặp dưới đây kết thúc
            với cờ `vua_goi_handoff=True` còn treo, chưa từng được gán vào
            `chi_so_bang_giao` vì không có lượt bot nào đứng sau để nhận nó.
            KHÁC ca (a) ở chỗ: có BẰNG CHỨNG THẬT tool đã chạy, nhưng bằng
            chứng đó không bao giờ gắn được vào một lượt hiển thị (`co_goi_
            tool` chỉ gắn cho AIMessage kế tiếp — ở đây không có) — CSKH
            không thấy badge nào cho đúng lần gọi này, kể cả khi các lượt
            TRƯỚC đó trong cùng hội thoại có badge cho tool khác. Không vá
            bằng cách đoán vị trí vạch — sẽ thay một khoảng trống trung thực
            bằng một phỏng đoán."""
    tuple_ = _CHECKPOINTER.get_tuple({"configurable": {"thread_id": thread_id}})
    if tuple_ is None:
        return None
    messages = (tuple_.checkpoint.get("channel_values") or {}).get("messages") or []

    luot: list[dict[str, object]] = []
    co_tool_tu_luot_truoc = False
    vua_goi_handoff = False
    chi_so_bang_giao: int | None = None
    for m in messages:
        if isinstance(m, ToolMessage):
            co_tool_tu_luot_truoc = True
            if m.name == "request_human_handoff":
                vua_goi_handoff = True
            continue
        if isinstance(m, HumanMessage):
            luot.append({"vai": "khach", "noi_dung": str(m.content), "co_goi_tool": False})
            co_tool_tu_luot_truoc = False
        elif isinstance(m, AIMessage):
            noi_dung = str(m.content or "")
            if not noi_dung.strip():
                # AIMessage rỗng nội dung (chỉ mang tool_calls, chưa có lời
                # thoại) — không phải một LƯỢT hội thoại, bỏ qua. Cờ
                # co_tool_tu_luot_truoc đã lên True ở nhánh ToolMessage phía
                # trên khi tool đó thực thi xong.
                continue
            luot.append({"vai": "bot", "noi_dung": noi_dung, "co_goi_tool": co_tool_tu_luot_truoc})
            co_tool_tu_luot_truoc = False
            if vua_goi_handoff:
                chi_so_bang_giao = len(luot) - 1
                vua_goi_handoff = False
    return {"luot": luot, "chi_so_bang_giao": chi_so_bang_giao}

# Sentinel — phân biệt "không truyền otp_verified_at" (backward-compat: coi như
# vừa xác thực XONG, dùng bởi eval harness/test hiện có vốn giả định "khách đã
# xác thực OTP trước khi vào chat") với "truyền None thật" (current_user thật
# CHƯA TỪNG xác thực — /agent/chat luôn truyền tường minh, xem src/api/main.py).
# Tính "now" lúc GỌI HÀM (không phải lúc module nạp) để không lệch thời gian
# nếu test suite chạy lâu.
_ALWAYS_FRESH = object()


# ---------------------------------------------------------------- nguồn O3
# Nhánh LỖI của tool bị loại khỏi nguồn (điều kiện Đ1 của Bảo Mật,
# docs/security/2026-08-18-dinh-hang-ban-va-A-o3-toolmessage-lich-su.md §3):
# nhánh error echo nguyên văn THAM SỐ DO MODEL TỰ ĐẶT (vd
# `create_ticket.py:42 "complaint_type không hợp lệ: {complaint_type}"`), nên
# một mã/số agent BỊA ở lượt N-1, tool từ chối, echo nó vào ToolMessage — nếu
# nhánh đó lọt vào nguồn thì lượt N nhắc lại đúng mã bịa ấy sẽ được O3 coi là
# "đã truy được về tool", cấp giấy thông hành vĩnh viễn cho một số KHÔNG THẬT.
#
# ĐÃ TỪNG là allow-list `status in {found, not_found, multiple_matches}` —
# RÚT, vì tiền đề sai: Lead [ĐO] 3/5 tool (get_customer_history · create_ticket
# · request_human_handoff) KHÔNG có khoá `status` ở TOP-LEVEL trên đường THÀNH
# CÔNG (status nằm lồng trong từng phần tử, hoặc không tồn tại). Allow-list
# theo đúng chữ sẽ loại sạch payload thành công của CẢ BA tool đó khỏi nguồn —
# và `get_customer_history` chính là tool đứng sau câu verify "xem giao dịch
# gần đây", nên bản vá sẽ KHÔNG chữa được ca nó dựng ra để chữa.
# `contracts/agent-tools.yaml:65,94,106` cũng khai `output.status` cho CẢ BA
# tool đó (`get_customer_history`/`create_ticket`/`request_human_handoff`) mà
# runtime KHÔNG phát — allow-list cũ tin đúng nguồn sự thật của dự án, và
# nguồn đó LỆCH runtime. Không ai chế ra tiền đề sai từ không khí: đây là hạng
# mù ADR-027 — checker `test_invariants` so KHAI-BÁO với KHAI-BÁO (contract ↔
# CHECK constraint/route), chưa bao giờ so contract với PAYLOAD THẬT lúc chạy.
#
# Deny-list `status == "error"` — vị ngữ này NEO VÀO HÀNH VI QUAN SÁT ĐƯỢC,
# KHÔNG NEO VÀO CONTRACT (bài học vừa trả giá ở trên).
#
# [ĐO] 19/08, `grep -rn '"status": "error"' src/agents/tools/customer_tools.py`
# → 9 điểm trả lỗi (`:597 :601 :637 :819 :840 :873 :919 :947 :997`), 0 payload
# thành công mang khoá này. `:637` là hằng số `_CHI_THI_DUNG_LAP` DÙNG LẠI, trả
# về ở `:777` (chỉ thị dừng livelock) — không phải `return {...}` inline, nên
# nó lọt khỏi BA lần quét độc lập trước đó (Review, Lead, tôi) cùng đếm ra 8:
# cả ba đều quét theo hình dạng `return {...}`, không theo hình dạng hằng số.
#
# Con số trên là ẢNH CHỤP, SẼ LỆCH LẠI khi có tool thứ 6 hoặc một nhánh lỗi
# mới (đúng Luật N: một con số ĐẾM phải kèm phép đếm; đúng Luật P: con số làm
# cũ phải niêm, không phải mốc neo vĩnh viễn). Thứ giữ tính chất này đúng VỀ
# SAU là ca ⑩ của QA/QC (canh mọi đường trả lỗi thật đều mang `status:"error"`)
# — KHÔNG phải dòng comment này.
_TRANG_THAI_LOI_TOOL = "error"

# Tool được gom kết quả LỊCH SỬ vào nguồn. Khai TƯỜNG MINH ở đúng một chỗ để
# thu hẹp phạm vi sau này là sửa một dòng, không phải đọc lại vòng lặp: Bảo Mật
# đã cân trục "payload có echo tham số model tự đặt không" và chỉ ra nhánh error
# là kênh rửa số bịa (đóng bằng allow-list trên), nhưng nếu trục ấy được cân lại
# cho tool GHI thì chỗ sửa là dòng dưới.
TOOL_GOM_LICH_SU = frozenset({
    "lookup_transaction",
    "get_customer_history",
    "create_ticket",
    "request_human_handoff",
    "search_policy",
})


def rap_nguon_o3(all_messages: list, tool_calls_out: list[dict]) -> str:
    """Ráp kênh NGUỒN (JSON) cho luật xuất xứ của O3.

    Gồm HAI phần, và ranh giới giữa chúng là có chủ đích:

    · `tool_calls_out` — kết quả tool của LƯỢT NÀY, giữ nguyên hình dạng cũ
      (gồm cả `args`).
    · kết quả tool của các LƯỢT TRƯỚC trong cùng hội thoại — CHỈ phần `result`,
      **không** gom `args`. Ràng buộc cứng 3 đòi số agent nói ra truy được về
      một kết quả tool CÓ THẬT; `args` là tham số MODEL TỰ ĐẶT, không phải thứ
      hệ thống trả về. Gom nó là để model tự cấp căn cứ cho chính nó, xuyên
      lượt — đúng cửa rửa số mà Đ1 đóng, chỉ đi bằng trường khác.

    KHÔNG gom `AIMessage`: lời agent không phải nguồn hợp lệ, gom vào là O3 tự
    chứng thực đầu ra của chính mình.

    Vì sao cần phần lịch sử (bản vá A): kênh nguồn cũ chỉ nạp payload của lượt
    hiện tại, nên một lượt agent trả lời từ trí nhớ (không gọi lại tool) làm mọi
    mã/số đã tra ở lượt trước thành "không truy được" -> O3 chặn OAN. Ràng buộc
    cứng 3 nói "một kết quả tool có thật", KHÔNG nói "của lượt này".
    """
    lich_su: list[dict] = []
    for m in all_messages:
        if not isinstance(m, ToolMessage):
            continue
        if getattr(m, "name", None) not in TOOL_GOM_LICH_SU:
            continue
        try:
            payload = json.loads(m.content)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue  # không parse được -> KHÔNG phải nguồn (fail-closed)
        if not isinstance(payload, dict):
            continue
        if payload.get("status") == _TRANG_THAI_LOI_TOOL:
            continue
        lich_su.append(payload)
    return json.dumps(
        {"luot_nay": tool_calls_out, "luot_truoc": lich_su},
        ensure_ascii=False,
        default=str,
    )


def _build_agent(
    session: Session,
    *,
    user_id: str,
    customer_name: str,
    otp_verified_at: float | None,
    guard: TurnGuard | None = None,
    # ADR-044 — thread_id HIỆU LỰC của lượt này (đã áp `or user_id` ở caller,
    # xem run_agent_turn), luồn xuống build_customer_tools để tool
    # create_ticket ghi vào Complaint.thread_id lúc TẠO. None = caller cũ
    # (test/eval) không truyền — Complaint.thread_id NULL, đúng thiết kế
    # "NULLABLE VĨNH VIỄN" của migration a8b9c0d1e2f3, không phải lỗi.
    thread_id: str | None = None,
    # GĐ3 (876a240) — tên MODEL cho lượt này, KHÔNG phải hằng số toàn cục.
    # Mặc định `LLM_MODEL` giữ NGUYÊN hành vi cũ cho mọi caller không truyền
    # (test/eval hiện có). Vòng xoay nằm INLINE trong `run_agent_turn` (không
    # phải một hàm riêng `_chay_luot_voi_xoay` — tên đó từng khai cho QA/QC
    # qua tin nhắn 19/08 rồi KHÔNG triển khai đúng như vậy, xem sửa sai đã báo
    # Lead/QA/QC cùng ngày), truyền tường minh từng phần tử của
    # `LLM_MODEL_POOL` — đây là ĐIỂM SPY QA/QC dùng để giả lập lỗi quota mà
    # không tốn token thật (patch theo giá trị `model` nhận được để phân biệt
    # lần gọi thứ mấy).
    model: str = LLM_MODEL,
):
    chat_model = ChatOpenAI(
        # LLM_* fallback ve OPENAI_* (src/config.py) -> khong dat gi thi hanh vi
        # y het truoc. `base_url=None` la mac dinh cua SDK, khong phai mot gia
        # tri dac biet can xu ly rieng.
        #
        # `http_client` DUNG CHUNG voi duong embedding (src/rag/store.py) —
        # xem src/cong_ra_ngoai.py. Day la noi DUY NHAT moi loi goi ra nha cung
        # cap di qua, nen no la cho duy nhat co cho chot chan + bo dem. Dat o
        # tang nay con thay ca luot SDK TU RETRY (max_retries duoi day): dem o
        # tang tren SDK ghi 1 cho 3 lan ban ra day.
        http_client=http_client_dung_chung(),
        model=model,
        temperature=0.2,
        api_key=LLM_API_KEY,
        # GĐ3: mọi model trong LLM_MODEL_POOL dùng CHUNG base_url/api_key —
        # cùng tài khoản DashScope, không đổi biên dữ-liệu-rời-hạ-tầng (Bảo
        # Mật đã xác nhận cho bể deepseek). Đổi nhà cung cấp GIỮA các model
        # trong MỘT bể ngoài phạm vi GĐ3.
        base_url=LLM_BASE_URL,
        # Chỉ truyền khi CÓ đặt — `max_tokens=None` và "không truyền" khác nhau
        # ở một số client. Xem LLM_MAX_TOKENS trong config.py.
        **({"max_tokens": LLM_MAX_TOKENS} if LLM_MAX_TOKENS else {}),
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
        # T3 · chỉ TRUYỀN khi TẮT. Không truyền gì khi bật = hành vi cũ y hệt,
        # không phải "truyền enable_thinking=True" (hai thứ đó khác nhau ở một
        # số nhà cung cấp, và ta không có lý do để thử).
        **({} if SUY_LUAN_BAT else {"extra_body": {"enable_thinking": False}}),
    )
    # Đọc NGƯỢC ra từ đối tượng vừa dựng, KHÔNG đọc lại biến config: nếu tên
    # tham số sai thì `extra_body` sẽ không bám vào model, mà biến config vẫn
    # nói "đã tắt". Quan sát hiện vật, đừng tin lời khai — cùng nguyên tắc dấu
    # `duong` và `so_tool_schema_gui`.
    global _SUY_LUAN_GUI
    _SUY_LUAN_GUI = not bool((getattr(chat_model, "extra_body", None) or {}).get("enable_thinking") is False)
    tools = build_customer_tools(
        session, user_id=user_id, otp_verified_at=otp_verified_at, guard=guard, thread_id=thread_id
    )
    # Số lược đồ tool THẬT SỰ bind vào lời gọi. Lấy từ chính danh sách vừa
    # dựng, KHÔNG gõ tay — `_CHARS_TOOL_SCHEMA = 6773` phía trên là hằng số
    # người phải nhớ cập nhật, và ta không thêm cái thứ hai cùng loại.
    #
    # Trường này đến từ cơ chế KHÁC với quyết định phân luồng, nên hai thứ
    # không thể cùng nói dối một lúc: dấu `duong` kẹt ở "day_du" trong khi số
    # này = 0 là mâu thuẫn tự lộ, và ngược lại.
    global _SO_TOOL_GUI, _CHARS_TOOL_SCHEMA_THAT
    _SO_TOOL_GUI = len(tools)
    # Kích thước lược đồ ĐO TỪ CHÍNH LƯỢC ĐỒ, không gõ tay. `_CHARS_TOOL_SCHEMA
    # = 6773` phía trên kèm chú thích "đổi khi thêm/bớt tool" — một con số
    # NGƯỜI PHẢI NHỚ cập nhật, tức nó sẽ hỏng im lặng vào ngày có tool thứ sáu.
    # Đo payload thật 17/08: 6.773 ký tự — hằng số ĐÚNG hôm nay, và đúng do
    # người, không do cơ chế.
    try:
        from langchain_core.utils.function_calling import convert_to_openai_tool
        _CHARS_TOOL_SCHEMA_THAT = len(json.dumps(
            [convert_to_openai_tool(t) for t in tools], ensure_ascii=False))
    except Exception:  # noqa: BLE001 — số đo hỏng không được làm chết lượt chat
        _CHARS_TOOL_SCHEMA_THAT = _CHARS_TOOL_SCHEMA
    # KHÔNG truyền customer_name — họ tên thật không được rời hệ thống lên LLM
    # (ADR-010). Giữ tham số ở chữ ký hàm để không vỡ caller cũ.
    system_prompt = build_system_prompt(current_time=dt.datetime.utcnow())
    return create_agent(chat_model, tools, system_prompt=system_prompt, checkpointer=_CHECKPOINTER)


def run_agent_turn(
    session: Session,
    *,
    user_id: str,
    message: str,
    thread_id: str | None = None,
    otp_verified_at: float | None = _ALWAYS_FRESH,
    vua_xac_thuc_de_gui_lai: bool = False,
) -> dict[str, Any]:
    """`otp_verified_at`: timestamp (epoch giây) lúc xác thực OTP+câu hỏi bảo
    mật gần nhất (src/auth.py) — truyền THẬT từ current_user.otp_verified_at ở
    /agent/chat (src/api/main.py), có thể là None nếu khách CHƯA TỪNG xác thực.
    Không truyền tham số này (mặc định `_ALWAYS_FRESH`) nghĩa là coi như vừa
    xác thực XONG — để KHÔNG phá vỡ eval/golden_set.jsonl + adversarial_set
    hiện có: các case đó vốn giả định "khách đã xác thực OTP trước khi vào
    chat" (đúng câu mở đầu system prompt), không phải kiểm tra luồng OTP —
    luồng OTP thật được test riêng ở tests/test_api/test_otp.py +
    frontend/e2e/auth.spec.ts.

    `vua_xac_thuc_de_gui_lai`: cờ TƯỜNG MINH từ frontend (KHÔNG suy từ mốc
    giờ), báo lượt này là ChatClient.tsx::submitOtp() TỰ GỬI LẠI câu đã bị
    chặn OTP trước đó (`pendingStarterRef`) — xem cổng thu-slot-sau-OTP ngay
    dưới. `False` mặc định giữ hành vi cũ nguyên vẹn cho mọi caller khác
    (eval/golden_set, test, mọi lượt chat bình thường)."""
    if otp_verified_at is _ALWAYS_FRESH:
        otp_verified_at = dt.datetime.utcnow().timestamp()

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    # Đặt lại đầu MỖI lượt: hai biến này là toàn cục cấp module (ghi ở
    # `_build_agent`). Không đặt lại thì một `return` sớm xảy ra TRƯỚC khi agent
    # được dựng sẽ báo giá trị của LƯỢT TRƯỚC — một con số hợp lý và sai.
    # `None` ở đây là CỐ Ý: nó nói "chưa dựng agent", khác hẳn `0` nghĩa là
    # "đã dựng, không gửi tool nào".
    global _SO_TOOL_GUI, _CHARS_TOOL_SCHEMA_THAT
    _SO_TOOL_GUI = None
    _CHARS_TOOL_SCHEMA_THAT = None

    # ── ⑭ · CỜ CLIENT PHẢI CÓ BẰNG CHỨNG PHÍA SERVER ────────────────────────
    # 🔴 LỖ ĐÃ ĐO (Review tìm, PO tái lập bằng gọi thẳng API, Coder xác nhận lại
    # bằng đọc mã): `vua_xac_thuc_de_gui_lai` là cờ do CLIENT tự khai, và cả BA
    # cổng tất định đều dùng nó theo hướng "True ⟹ BỎ QUA".
    #     :928  T0   True ⟹ vào T0, mà câu có bất kỳ chữ số nào là rơi thẳng xuống model
    #     :986  ④    `and not vua_xac_thuc_de_gui_lai`  ⟹ bỏ qua
    #     :1035 T1   `if not vua_xac_thuc_de_gui_lai`   ⟹ bỏ qua
    # ⟹ MỘT cờ tắt được CẢ BA. Client bất kỳ (curl/Postman) với JWT hợp lệ nhưng
    # CHƯA OTP, đặt cờ=true trên mọi request, đi thẳng vào lượt model đầy đủ.
    #
    # ✅ KHÔNG lộ dữ liệu — tầng tool đọc `otp_verified_at` từ JWT, không đọc cờ
    #    này. Ràng buộc cứng 4 KHÔNG thủng.
    # 🔴 NHƯNG đây đúng kịch bản 49.700–71.600 token mà ④ sinh ra để triệt. Và nó
    #    KHÔNG chỉ là chi phí: trần thật của hệ là TPM (STATE §6.⓵), mà TPM là
    #    hạn ngạch DÙNG CHUNG — một client lạm dụng ăn vào phần của MỌI khách
    #    khác. Đó là KHẢ DỤNG, không phải hoá đơn.
    #
    # Bản vá: cờ chỉ có hiệu lực khi server TỰ BIẾT thread này từng bị chặn.
    # Dùng lại `thread_signals` (không dựng cơ chế thứ hai).
    #
    # 🔴 HƯỚNG AN TOÀN: `doc_tin_hieu` là `doc_hoac_khong_ro` — Redis lỗi trả
    # None. `None` và `0` ĐỀU coi là KHÔNG có bằng chứng ⟹ cờ bị bỏ qua ⟹ cổng
    # tất định chạy bình thường. Sai về phía RẺ, không sai về phía đắt. Hỏng
    # Redis làm khách bị hỏi lại một lượt (phiền), KHÔNG mở cổng cho ai.
    #
    # Vì sao khoá theo thread SỐNG SÓT qua bước xác thực: `/auth/otp/verify` cấp
    # lại token GIỮ NGUYÊN `iat` gốc (src/auth.py::create_access_token) đúng để
    # `thread_id = user_id:iat` không đổi giữa chừng hội thoại.
    _tid_bang_chung = thread_id or user_id
    _co_bang_chung_bi_chan = doc_tin_hieu(_TEN_TIN_HIEU_DA_BI_OTP_CHAN, _tid_bang_chung) not in (None, 0)
    if vua_xac_thuc_de_gui_lai and not _co_bang_chung_bi_chan:
        _logger.info(
            "agent_turn_co_resend_khong_co_bang_chung",
            extra={"user_id": user_id, "thread_id": _tid_bang_chung},
        )
    vua_xac_thuc_de_gui_lai = vua_xac_thuc_de_gui_lai and _co_bang_chung_bi_chan

    # ── ⑨ + MẢNH 4 · THU NHẬN CÂU TRẢ LỜI SÀNG LỌC ──────────────────────────
    # Lượt TRƯỚC đã hỏi câu sàng lọc (tín hiệu thread). Lượt này là câu trả lời.
    #
    # Đây là mảnh KHÔNG AI TÍNH GIÁ trong phiếu gốc: trước bản này
    # `engine.evaluate()` chỉ được gọi ĐÚNG MỘT LẦN, với `description_raw` lúc
    # tạo vé. FS-13 dù tồn tại cũng chỉ bắt được ca khách tự khai ngay trong mô
    # tả đầu — mà khách gọi việc của mình là "chuyển nhầm" thì không bao giờ
    # chạm tới. Tức tín hiệu chỉ bật khi ta đã không cần nó.
    #
    # HAI nguồn, hợp nhất:
    #   ① `la_tra_loi_khang_dinh` — khách nói CÓ. Đó CHÍNH LÀ ngữ nghĩa FS-13,
    #      suy ra từ NGỮ CẢNH HỎI-ĐÁP, không cần câu trả lời chứa từ khoá nào.
    #   ② `engine.evaluate()` trên chính câu ấy — bắt câu trả lời giàu hơn
    #      ("có, người ta gọi điện bảo em chuyển") và cả FS-09.
    #
    # XOÁ tín hiệu sau khi xử: một lần hỏi, một lần thu. Không xoá thì mọi lượt
    # sau đều chạy lại một truy vấn DB không đổi kết quả.
    # KHÔNG chặn lượt: đây là GHI NHẬN, không phải cổng. Hỏng thì lượt vẫn chạy.
    _tid_sl_thu = thread_id or user_id
    if doc_tin_hieu(_TEN_TIN_HIEU_DA_HOI_SANG_LOC, _tid_sl_thu) not in (None, 0):
        try:
            _gop = hop_nhat_tin_hieu_gian_lan(
                session,
                thread_id=_tid_sl_thu,
                utterance_text=message,
                them_ma=["FS-13"] if la_tra_loi_khang_dinh(message) else None,
            )
            # 🔴 XOÁ SAU KHI MERGE THÀNH CÔNG, không trước (Review bắt, PO chốt).
            # Bản đầu xoá TRƯỚC `try` — merge ném lỗi thì lượt vẫn chạy (đúng)
            # nhưng lời khai "có người hướng dẫn em chuyển" MẤT VĨNH VIỄN, không
            # lượt nào thử lại. Đúng luật bất đối xứng đã viết ở bộ dò khẳng định,
            # khác miền:
            #   xoá SAU  ⟹ merge hỏng thì hỏi lại khách một lần.    Phiền.
            #   xoá TRƯỚC ⟹ merge hỏng thì MẤT lời khai bị lừa đảo. Hỏng thật.
            #
            # KHÔNG có vòng lặp hỏi mãi: cổng HỎI đòi tín hiệu == 0, mà tín hiệu
            # chỉ về 0 khi merge XONG. Tín hiệu còn 1 ⟹ không hỏi lại, chỉ thử
            # merge lại mỗi lượt. Retry bị chặn trên bởi số lượt khách còn chat,
            # không phải một vòng lặp trong một lượt.
            xoa_tin_hieu(_TEN_TIN_HIEU_DA_HOI_SANG_LOC, _tid_sl_thu)
            _logger.info(
                "agent_turn_thu_sang_loc_lua_dao",
                extra={"user_id": user_id, "thread_id": _tid_sl_thu,
                       "tin_hieu_sau_gop": _gop},
            )
            # ① — FS-13 bật ⟹ DỪNG LƯỢT, không gọi model. Bàn giao ở TẦNG
            # SERVICE (`flag_human_handoff`), KHÔNG qua tool của AI — đúng ràng
            # buộc cứng 2: leo thang không bao giờ do AI tự gọi.
            if _gop is not None and "FS-13" in _gop:
                _tk = None
                try:
                    _tk = flag_human_handoff(
                        session, user_id=user_id,
                        reason="Khách xác nhận có người hướng dẫn chuyển khoản "
                               "(FS-13) — cần chuyên viên liên hệ trực tiếp.",
                        thread_id=_tid_sl_thu,
                    ).get("ticket_id")
                except Exception:  # noqa: BLE001
                    _logger.exception(
                        "agent_turn_fs13_ban_giao_loi",
                        extra={"user_id": user_id, "thread_id": _tid_sl_thu},
                    )
                _kq_fs13 = {
                    "reply": _FS13_BAN_GIAO,
                    "tool_calls": [], "ticket_id": _tk, "should_escalate": False,
                    "model": None, "models_da_thu": [],
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                              "cached_input_tokens": 0, "reasoning_tokens": 0,
                              "input_chars": 0, "so_luot_goi_model": 0,
                              "so_tool_schema_gui": 0, "chars_tool_schema_moi_luot": 0,
                              "suy_luan_gui": None},
                    "loc_dau_ra": [],
                    "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                    "goi_y_handoff": True,
                    "ly_do_fallback": None,
                    "duong": DUONG_FS13_BAN_GIAO,
                }
                _ghi_so(_kq_fs13, thread_id, user_id)
                return _kq_fs13
        except Exception:  # noqa: BLE001 — ghi nhận KHÔNG được làm hỏng lượt chat
            _logger.exception(
                "agent_turn_thu_sang_loc_loi",
                extra={"user_id": user_id, "thread_id": _tid_sl_thu},
            )

    # ── T0 · CỔNG THU SLOT SAU KHI XÁC THỰC OTP ─────────────────────────────
    # Chạy TRƯỚC phan_luong() (1B), độc lập với `PHAN_LUONG_BAT` — quyết định
    # "gọi model với gì" ở đây khác hẳn quyết định "lượt này cần bộ đồ nghề
    # nào" của 1B. Khi cờ này bật, lượt này KHÔNG đi qua nhe/thu_slot/day_du
    # của 1B — resend-sau-OTP luôn là một khiếu nại thật (đó là lý do tool bị
    # OTP chặn), không bao giờ hợp lệ để đi DUONG_NHE hay bị 1B hỏi lại số
    # tiền theo slot khác.
    # 🔴 Đ4 (phiếu "OTP trước token" ⑦) — cổng này nay có CÔNG TẮC RIÊNG
    # `CONG_T0_BAT` (mặc định BẬT, xem src/config.py). Trước bản vá, tắt
    # `PHAN_LUONG_BAT` để chữa cháy vẫn để T0 chạy, và KHÔNG tín hiệu nào báo.
    # Nhận diện trong sổ: `duong=otp_resend_thu_slot` ⟹ T0 đã xử lý lượt này.
    if CONG_T0_BAT and vua_xac_thuc_de_gui_lai:
        _tid_hieu_qua_otp = thread_id or user_id
        if doc_tin_hieu(_TEN_TIN_HIEU_OTP_RESEND, _tid_hieu_qua_otp) == 0 and not co_du_de_thu_hep(message):
            tang_tin_hieu(_TEN_TIN_HIEU_OTP_RESEND, _tid_hieu_qua_otp)
            _logger.info(
                "agent_turn_otp_resend_thu_slot",
                extra={"user_id": user_id, "thread_id": _tid_hieu_qua_otp},
            )
            _kq_otp_resend = {
                "reply": HOI_THOI_GIAN_VA_SO_TIEN,
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                # Cùng nguyên tắc DUONG_NHE/DUONG_THU_SLOT — không gọi model
                # nào, None/0 là SỰ THẬT, không phải "không đọc được".
                "model": None,
                "models_da_thu": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                          "cached_input_tokens": 0, "reasoning_tokens": 0,
                          "input_chars": 0, "so_luot_goi_model": 0,
                          "so_tool_schema_gui": 0,
                          "chars_tool_schema_moi_luot": 0,
                          "suy_luan_gui": None},
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": None,
                "duong": DUONG_OTP_RESEND_THU_SLOT,
            }
            _ghi_so(_kq_otp_resend, thread_id, user_id)
            return _kq_otp_resend
        # Đủ điều kiện (có mã/thời gian) HOẶC đã hỏi rồi ở một lượt resend
        # trước đó trong hội thoại này (khách xác thực OTP nhiều lần) — KHÔNG
        # tăng tín hiệu (chỉ tăng ở nhánh hỏi phía trên), rơi thẳng xuống
        # luồng model đầy đủ bên dưới với `message` NGUYÊN VĂN, bỏ qua 1B.

    # ── ④ · CỔNG OTP TẤT ĐỊNH CHO NHÓM B ────────────────────────────────────
    # Bất biến của đợt: KHÔNG lượt nào tốn token trước khi OTP xác thực xong.
    # Lượt khiếu nại cá nhân mà OTP chưa tươi thì CHẮC CHẮN bị tầng tool chặn —
    # gọi model cho nó là trả tiền để tự khám phá một sự thật tầng này đã biết.
    # [ĐO, customer_tools.py:620-629 tự khai] lượt ấy tốn 8 tool call · 46 giây ·
    # 49.700–71.600 token, và sổ ghi `total_tokens = 0`.
    #
    # Q1 (PO chốt): CHỈ áp cho NHÓM B. Câu hỏi chính sách KHÔNG bị chặn —
    # `search_policy` vốn đã được miễn OTP.
    #
    # 🔴 KHÔNG PHẢI LỚP BẢO MẬT — xem chú thích `CONG_OTP_NHOM_B_BAT` ở
    # src/config.py. Dùng ngưỡng XEM (12h), CỐ Ý lỏng bằng tầng tool chứ không
    # chặt hơn. Gỡ chốt ở tool vì "đã có cổng này" là mở ràng buộc cứng 4.
    #
    # Đặt SAU T0 (lượt resend-sau-OTP đã xác thực rồi, không rơi vào đây) và
    # TRƯỚC T1 — muộn hơn là đã tiêu mất thứ định tiết kiệm.
    #
    # 🔴 AM-01 tạm còn `nhom_b=True` ⟹ một lớp câu hỏi chính sách bị chặn. Đây
    # là lỗ ĐÃ TRACKED của NHÓM B chảy xuống, KHÔNG phải hồi quy do ④ gây ra;
    # tự đóng khi ③ vòng 2 (trục thể câu) land. Lead duyệt land trước, 25/08.
    if (
        CONG_OTP_NHOM_B_BAT
        and not vua_xac_thuc_de_gui_lai
        # TÁI DÙNG `_otp_fresh` của tầng tool — KHÔNG viết định nghĩa thứ hai
        # về "còn tươi". Hai định nghĩa của cùng một vật sẽ lệch nhau, và lệch
        # trong im lặng (cùng lý do `bam_ma_nguon` vs `BUILD_COMMIT` đã có).
        # Cổng này chặn ⟹ tool cũng sẽ chặn: một nguồn, không thể lệch.
        and not _otp_fresh(otp_verified_at, OTP_VIEW_MAX_MINUTES)
        and la_khieu_nai_ca_nhan(message)
    ):
        _logger.info(
            "agent_turn_can_otp",
            extra={"user_id": user_id, "thread_id": thread_id or user_id,
                   "bam_luat": BAM_LUAT},
        )
        _kq_can_otp = {
            "reply": _CAN_XAC_THUC_OTP,
            # 🔴 HỢP ĐỒNG VỚI CLIENT (Lead duyệt 25/08): client mở hộp thoại OTP
            # bằng `duong === "can_otp"`, KHÔNG bằng câu chữ tiếng Việt của
            # `reply`. Trước ④, hai đường kích OTP của ChatClient.tsx đều đọc
            # `tool_calls`/`ticket_id` — mà mọi đường 0-token đều trả rỗng, nên
            # thêm cổng này mà không thêm khoá là để khách vào ngõ cụt.
            "tool_calls": [],
            "ticket_id": None,
            "should_escalate": False,
            "model": None,
            "models_da_thu": [],
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                      "cached_input_tokens": 0, "reasoning_tokens": 0,
                      "input_chars": 0, "so_luot_goi_model": 0,
                      "so_tool_schema_gui": 0,
                      "chars_tool_schema_moi_luot": 0,
                      "suy_luan_gui": None},
            "loc_dau_ra": [],
            "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
            "goi_y_handoff": False,
            "ly_do_fallback": None,
            "duong": DUONG_CAN_OTP,
        }
        # ⑭ — ghi BẰNG CHỨNG: thread này vừa bị cổng OTP chặn thật. Lượt sau
        # client mới được quyền đặt `vua_xac_thuc_de_gui_lai`.
        tang_tin_hieu(_TEN_TIN_HIEU_DA_BI_OTP_CHAN, thread_id or user_id)
        _ghi_so(_kq_can_otp, thread_id, user_id)
        return _kq_can_otp

    # ── T1 · PHÂN LUỒNG ─────────────────────────────────────────────────────
    # Sau cờ, MẶC ĐỊNH TẮT. Tắt thì hàm này chạy y hệt trước khi có nhánh này.
    #
    # Đường nhẹ TRẢ NGAY, KHÔNG chạm model, KHÔNG chạm tool, KHÔNG ghi bản ghi
    # nghiệp vụ nào. Đó là toàn bộ điểm của nó: rẻ hơn mọi model rẻ, vì không
    # có model nào.
    #
    # Đặt SAU khi nạp `user` (cần user tồn tại thật) và TRƯỚC mọi thứ khác —
    # đặt muộn hơn là đã tiêu mất thứ ta định tiết kiệm.
    if not vua_xac_thuc_de_gui_lai and PHAN_LUONG_BAT:
        _duong, _ly_do_duong = phan_luong(message)
        if _duong == DUONG_NHE:
            _logger.info(
                "agent_turn_duong_nhe",
                extra={"user_id": user_id, "thread_id": thread_id or user_id,
                       "ly_do": _ly_do_duong, "bam_luat": BAM_LUAT},
            )
            _kq_nhe = {
                "reply": TRA_LOI_NHE,
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                # GĐ3 — đường nhẹ KHÔNG gọi model nào (định tuyến trước khi
                # chạm LLM) ⟹ None/rỗng là SỰ THẬT, không phải "không đọc được".
                "model": None,
                "models_da_thu": [],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                          "cached_input_tokens": 0, "reasoning_tokens": 0,
                          "input_chars": 0, "so_luot_goi_model": 0,
                          # Hai trường ĐẾM cùng tầng với `so_luot_goi_model`.
                          # tester sập bẫy hai-tầng: `.get()` trên khoá không
                          # tồn tại trả None, y hệt khoá tồn tại mang None.
                          # `duong` GIỮ top-level — nó là NHÃN, không phải số đo.
                          "so_tool_schema_gui": 0,
                          "chars_tool_schema_moi_luot": 0,
                          "suy_luan_gui": None},
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": None,
                # Dấu do TẦNG NÀY ghi, từ thứ nó THẬT SỰ gửi đi (không gửi gì).
                # `so_tool_schema_gui` đến từ một cơ chế KHÁC với quyết định
                # phân luồng, nên một điểm hỏng không giả được cả hai: dấu kẹt
                # "day_du" mà số này = 0 là mâu thuẫn tự lộ.
                "duong": DUONG_NHE,
            }
            _ghi_so(_kq_nhe, thread_id, user_id)
            return _kq_nhe

        elif _duong == DUONG_THU_SLOT:
            # 1B — cổng thu slot tất định (docs/giao-viec/2026-08-24-luong-
            # chatbot-1A-1B.md). Trạng thái "đã hỏi lần nào chưa" sống ở TẦNG
            # GỌI này (Redis, thread_signals.py) — phan_luong.py là hàm THUẦN,
            # không side-effect. Tối đa MỘT LẦN hỏi mỗi hội thoại (mục 5): đã
            # hỏi rồi thì KHÔNG return sớm ở đây nữa, rơi thẳng xuống đường
            # đầy đủ bên dưới như một lượt day_du bình thường — GHÉP lại lời
            # kể gốc + câu trả lời của khách là việc của model đọc lịch sử
            # hội thoại, tầng tất định này không có khả năng ghép ngữ cảnh
            # liên-lượt (đúng bất biến "phân loại theo TỪNG LƯỢT").
            #
            # 🔴 Review bắt 24/08: dùng `doc_hoac_khong_ro()` (KHÔNG phải
            # `doc()`) — `== 0` CHỈ đúng khi Redis xác nhận "chưa hỏi thật".
            # Redis lỗi trả `None`, `None == 0` là `False` ⟹ KHÔNG bắn, rơi
            # xuống day_du — đúng hướng an toàn của module này ("nghi ngờ
            # thì đi ĐẦY ĐỦ"). Dùng `doc()` thường (gộp lỗi vào 0) sẽ làm
            # Redis chết ⟹ gate coi mọi lượt là lần đầu ⟹ bắn lặp lại.
            _tid_hieu_qua = thread_id or user_id
            if doc_tin_hieu(TEN_TIN_HIEU_1B, _tid_hieu_qua) == 0:
                tang_tin_hieu(TEN_TIN_HIEU_1B, _tid_hieu_qua)
                # R1 (1A) chốt 24/08: cổng CHỈ hỏi ĐÚNG MỘT thứ — số tiền là
                # slot bắt buộc duy nhất (xem chú thích HOI_THIEU_SO_TIEN),
                # nên không còn cần boc_slot(message) ở đây để chọn mẫu.
                _reply_slot = HOI_THIEU_SO_TIEN
                _logger.info(
                    "agent_turn_duong_thu_slot",
                    extra={"user_id": user_id, "thread_id": _tid_hieu_qua,
                           "ly_do": _ly_do_duong, "bam_luat": BAM_LUAT},
                )
                _kq_slot = {
                    "reply": _reply_slot,
                    "tool_calls": [],
                    "ticket_id": None,
                    "should_escalate": False,
                    # Cùng nguyên tắc DUONG_NHE — không gọi model nào, None/0
                    # là SỰ THẬT, không phải "không đọc được".
                    "model": None,
                    "models_da_thu": [],
                    "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                              "cached_input_tokens": 0, "reasoning_tokens": 0,
                              "input_chars": 0, "so_luot_goi_model": 0,
                              "so_tool_schema_gui": 0,
                              "chars_tool_schema_moi_luot": 0,
                              "suy_luan_gui": None},
                    "loc_dau_ra": [],
                    "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                    "goi_y_handoff": False,
                    "ly_do_fallback": None,
                    # 🔴 Nhãn RIÊNG, KHÔNG dùng chung "nhe" — thiếu nhãn này
                    # thì không đếm được tần suất cổng bắn/lượt trong
                    # usage.jsonl, dự báo giảm token (1B.5) không kiểm chứng
                    # được (yêu cầu PO-agent, mục 1 nháp 1B).
                    "duong": DUONG_THU_SLOT,
                }
                _ghi_so(_kq_slot, thread_id, user_id)
                return _kq_slot

    # ES-xx (ADR-022) — tính TRƯỚC khi gọi agent, trên tin nhắn khách, ở TẦNG
    # SERVICE. Không gọi LLM, không đi vào prompt, không thêm bước nào.
    #
    # Đặt ở ĐÂY chứ không phải sau khi có reply là có chủ đích: tính sau thì vẫn
    # đúng nghĩa "không vào prompt", nhưng mất khả năng bật gợi ý NGAY ở lượt
    # đang xảy ra — mà toàn bộ giá trị của ES là đưa người bực sang người thật
    # SỚM, không phải một lượt sau.
    #
    # Cố ý KHÔNG đưa nhãn cảm xúc vào prompt: agent sẽ NÓI RA cảm nhận đó, tức
    # khẳng định một kết luận tâm lý về một con người dựa trên bộ phân loại có
    # thể sai — trái tinh thần ràng buộc cứng 3 (mọi điều agent khẳng định phải
    # truy được về dữ liệu thật; cảm xúc suy đoán không phải dữ liệu thật).
    tin_hieu_cam_xuc = danh_gia_luot(message, thread_id or user_id)

    # 1 guard cho MỖI lượt (không phải global) — bàn giao `session` giữa luồng
    # chính và luồng nền khi lượt bị bỏ rơi vì timeout, xem TurnGuard (QA-12).
    guard = TurnGuard()
    agent = _build_agent(
        session, user_id=user_id, customer_name=None, otp_verified_at=otp_verified_at, guard=guard,  # PII-OK: cố ý truyền None, không đưa họ tên lên LLM
        thread_id=thread_id or user_id,
    )
    # thread_id mặc định = user_id (hành vi thật, không đổi). eval/_harness.py
    # truyền thread_id riêng biệt mỗi case để cô lập bộ nhớ hội thoại
    # (checkpointer module-level dùng chung — nếu không cô lập, nhiều case
    # cùng user_id trong 1 lần chạy eval sẽ nối tiếp hội thoại của nhau).
    config = {"configurable": {"thread_id": thread_id or user_id}}

    # `agent` ở trên CHỈ để đọc state trước lượt — KHÔNG phụ thuộc model nào
    # (checkpoint là lịch sử hội thoại, không phải hiện vật của một model cụ
    # thể) nên KHÔNG cần rebuild theo từng lần xoay bên dưới.
    state_before = agent.get_state(config)
    prev_len = len(state_before.values.get("messages", [])) if state_before.values else 0

    # GĐ3 (876a240) — BỂ MODEL + XOAY. `models_da_thu` liệt kê MỌI model đã
    # thử trong lượt này theo thứ tự (kể cả lần bị từ chối) — nhà cung cấp
    # tính tiền CẢ LẦN THẤT BẠI, "chứng từ đối soát hoá đơn" (876a240) phải
    # ghi đủ, không chỉ ghi model cuối cùng trả lời.
    models_da_thu: list[str] = []
    model_dang_thu = llm_pool.model_dau_luot()

    # Span gốc "agent_turn" — 1 lượt chat là 1 vòng lặp ReAct nhiều bước (LLM
    # generation + tool call xen kẽ), KHÔNG PHẢI 1 khối duy nhất (Giai đoạn 1
    # checklist observability). `callbacks=[handler]` (KHÔNG dùng
    # `.configurable`) tạo span con cho MỖI vòng gọi LLM/tool bên trong, tự
    # nối cây cha-con qua context OTel hiện hành (span gốc đang active).
    with _tracer.start_as_current_span("agent_turn") as root_span:
        root_span.set_attribute("fin05.user_id", user_id)
        root_span.set_attribute("fin05.thread_id", thread_id or user_id)
        root_span.set_attribute("fin05.otp_verified", otp_verified_at is not None)

        # GĐ3 — VÒNG XOAY. Bọc quanh build-agent + invoke, KHÔNG bọc quanh ba
        # nhánh except hiện có bên dưới: nhánh rotatable (APIError mang tín
        # hiệu hết hạn ngạch, CÒN model khác trong bể) được xử lý Ở ĐÂY rồi
        # `continue`; mọi nhánh KHÔNG rotatable (429 · lỗi không-phải-quota ·
        # bể đã cạn · timeout/recursion) `raise` NGUYÊN VẸN ra ngoài vòng lặp
        # để BA except hiện có xử lý Y HỆT trước GĐ3 — không đổi hành vi cho
        # các ca đó, chỉ THÊM một đường rẽ mới trước khi tới chúng.
        model_da_tra_loi: str | None = None
        try:
            while True:
                agent = _build_agent(
                    session, user_id=user_id, customer_name=None,  # PII-OK: luôn None, họ tên không rời hệ thống (ADR-010)
                    otp_verified_at=otp_verified_at, guard=guard, model=model_dang_thu,
                    thread_id=thread_id or user_id,
                )
                models_da_thu.append(model_dang_thu)

                def _invoke():
                    return agent.invoke(
                        # GĐ4 (Bảo Mật 19/08): muc_dich="model_input" — registry
                        # HẸP (D'), không nạp Spacy/Date/Phone-generic. Xem
                        # docstring src/observability/pii.py.
                        {"messages": [HumanMessage(content=scrub_pii(message, muc_dich="model_input") or message)]},
                        config={
                            **config,
                            "callbacks": [OTelTracingCallbackHandler()],
                            "recursion_limit": _AGENT_RECURSION_LIMIT,
                        },
                    )

                # AGENT_TURN_TIMEOUT_SECONDS — OPENAI_TIMEOUT_SECONDS chỉ chặn
                # TỪNG lượt gọi OpenAI riêng lẻ; 1 lượt /agent/chat có thể cần
                # NHIỀU lượt gọi xen kẽ với tool (ReAct), nên tổng thời gian
                # vẫn có thể vượt xa (đo thật: 70s cho 1 request) nếu không
                # chặn RIÊNG ở đây. Chạy trong thread riêng để
                # `.result(timeout=...)` trả lỗi có kiểm soát cho client kịp
                # lúc. CỐ Ý KHÔNG dùng `with ThreadPoolExecutor(...) as
                # executor:` — `__exit__` mặc định gọi `shutdown(wait=True)`,
                # tức BLOCK tới khi thread dở xong mới thoát `with`, xoá sạch
                # tác dụng của timeout. `shutdown(wait=False)` khi timeout:
                # không huỷ được lượt gọi OpenAI đang chạy dở bên dưới (Python
                # không kill thread được), nhưng trả quyền điều khiển lại cho
                # client NGAY, không đợi. Một executor MỚI mỗi lần thử — dùng
                # lại executor cũ sau khi nó đã `shutdown` là lỗi.
                executor = ThreadPoolExecutor(max_workers=1)
                # Mốc để sổ trả lời được "lượt này CHẠY BAO LÂU rồi mới hỏng".
                # Thiếu nó thì nhãn `timeout` là một lời khẳng định KHÔNG KIỂM
                # ĐƯỢC: một lượt bỏ cuộc tức thì và một lượt chạy trọn 45 giây
                # trông y hệt nhau trong sổ. Có nó thì
                # `giay_da_troi ≈ AGENT_TURN_TIMEOUT_SECONDS` là bằng chứng
                # nhãn ĐÚNG, còn `0,4 giây` là bằng chứng nhãn SAI.
                _bat_dau = time.monotonic()
                try:
                    result = executor.submit(_invoke).result(timeout=AGENT_TURN_TIMEOUT_SECONDS)
                    model_da_tra_loi = model_dang_thu
                    break
                except RateLimitError:
                    # 429 KHÔNG BAO GIỜ xoay — nghẽn thoáng qua, không phải
                    # "hết token" (ràng buộc PO 876a240). Ném nguyên vẹn cho
                    # except RateLimitError bên ngoài xử lý y hệt trước GĐ3.
                    raise
                except APIError as e:
                    executor.shutdown(wait=False)
                    mo_ta = _mo_ta_loi_nha_cung_cap(e, model=model_dang_thu)
                    # Ràng buộc PO 876a240: ưu tiên `status_code` khi nhà
                    # cung cấp CÓ trả — 403 luôn coi là quota bất kể câu chữ,
                    # KHÔNG phụ thuộc thuần vào khớp chuỗi mong manh
                    # (`co_dau_hieu_het_han_muc`, xem cảnh báo tại chỗ khai
                    # nó). Chỉ dựa vào chuỗi khi KHÔNG có status_code — một số
                    # lỗi transport không mang mã trạng thái.
                    la_quota = mo_ta["ma_trang_thai"] == 403 or (
                        mo_ta["ma_trang_thai"] is None and bool(mo_ta["co_dau_hieu_het_han_muc"])
                    )
                    if not la_quota:
                        raise  # lỗi không-phải-quota — KHÔNG xoay, đường cũ
                    llm_pool.danh_dau_can(model_dang_thu)
                    model_ke = llm_pool.model_dau_luot(da_thu=set(models_da_thu))
                    if model_ke is None:
                        # BỂ CẠN TOÀN PHẦN — ném NGUYÊN VẸN lỗi quota cuối
                        # cùng cho except APIError bên ngoài. Đây CHÍNH LÀ
                        # thông điệp "cần can thiệp" đã có (không hứa mốc thời
                        # gian, chỉ đường sang kênh khác) — bể cạn toàn phần
                        # về bản chất LÀ "nhà cung cấp từ chối liên tục",
                        # không cần một thông điệp/cơ chế thứ hai.
                        raise
                    model_dang_thu = model_ke
                    continue
                # GraphRecursionError/FutureTimeoutError: không có except nào
                # ở TẦNG NÀY bắt chúng — chúng propagate thẳng ra try bên
                # ngoài, đúng hành vi cũ (không xoay trên timeout/recursion).
        except RateLimitError as e:
            # 429 quá tải nhà cung cấp. TRƯỚC BẢN NÀY nó không nằm trong tuple
            # `except` dưới -> rơi thẳng ra ngoài thành HTTP 500, khách nhận
            # `{"detail":"Internal Server Error"}` trong khi OpenAI đã nói rõ
            # "try again in 1.381s". Đo thật: tester chạy `--lap 3` là tái hiện.
            #
            # NHÁNH RIÊNG, KHÔNG dùng chung với timeout/recursion bên dưới —
            # khác nhau ở chỗ QUAN TRỌNG NHẤT: nhánh kia TẠO TICKET bàn giao
            # người thật, đúng cho ca agent bó tay. 429 thì không: nó là nghẽn
            # thoáng qua, tự hết sau vài giây. Tạo ticket cho nó nghĩa là mỗi
            # phút cao điểm đổ một nắm ticket ma lên CSKH cho những khiếu nại
            # KHÔNG TỒN TẠI — và khách vẫn chưa được trả lời.
            #
            # Không ngủ-rồi-thử-lại ở đây: `openai` SDK đã tự retry
            # OPENAI_MAX_RETRIES lần theo đúng `Retry-After` của nhà cung cấp
            # TRƯỚC KHI ném lên tới đây. Ngủ thêm ở tầng này chỉ ăn vào ngân
            # sách AGENT_TURN_TIMEOUT_SECONDS rồi biến 429 thành timeout —
            # đúng cái nhầm lẫn `_ly_do_fallback` đã cảnh báo.
            executor.shutdown(wait=False)
            # ĐÍNH CHÍNH commit 8a30238 (message của nó dễ đọc sai, không sửa
            # lịch sử được): cụm "không đẻ ticket ma" ở đó mô tả việc nhánh NÀY
            # tránh làm, KHÔNG phải một bug đã từng xảy ra rồi được chặn. Trước
            # bản vá, 429 rơi thẳng ra 500 và chưa bao giờ chạm nhánh fallback
            # -> chưa từng tạo ticket nào qua đường đó.
            #
            # ⚠️ NHƯNG có một đường ticket-ma THẬT mà nhánh này KHÔNG đóng: khi
            # SDK ngủ theo `Retry-After` rồi TỔNG vượt AGENT_TURN_TIMEOUT_SECONDS,
            # ta nhận FutureTimeoutError chứ không phải RateLimitError -> rơi
            # xuống nhánh dưới -> nhánh ĐÓ CÓ tạo ticket. Tức 429 đủ chậm vẫn đẻ
            # ticket như cũ. Đã vào sổ là F-33b.
            #
            # AI MỞ F-33b: bịt ở đây là bịt NHẦM CHỖ. Chỗ cần bịt nằm ở nhánh
            # timeout, hoặc ở tương quan OPENAI_MAX_RETRIES x
            # AGENT_TURN_TIMEOUT_SECONDS. Và F-33c (lưu `ly_do_fallback` vào bản
            # ghi) là điều kiện để câu "429 có đẻ ticket không" trả lời được
            # bằng MỘT truy vấn — hôm nay không trả lời được, vì 15 complaint
            # fallback trong DB dùng CHUNG một văn bản lý do cho cả timeout lẫn
            # recursion.
            giay = _giay_cho_lai(e)
            _logger.warning(
                "agent_turn_qua_tai",
                extra={
                    "user_id": user_id,
                    "thread_id": thread_id or user_id,
                    "retry_after_giay": giay,
                    "so_lan_sdk_da_thu": OPENAI_MAX_RETRIES,
                },
            )
            root_span.set_attribute("fin05.qua_tai", True)
            khuyen = f" sau khoảng {giay:.0f} giây" if giay else " sau ít giây"
            _kq = {
                "reply": (
                    "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                    f"Bạn nhắn lại giúp mình{khuyen} nhé — tin nhắn của bạn "
                    "chưa bị mất gì cả."
                ),
                "tool_calls": [],
                # GĐ3 — 429 KHÔNG xoay (ràng buộc PO), nên model_dang_thu ở
                # đây LUÔN là model DUY NHẤT đã thử cho lượt này.
                "model": model_dang_thu,
                "models_da_thu": list(models_da_thu),
                "ticket_id": None,
                "should_escalate": False,
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": "qua_tai",
                # KẾT LUẬN ở trên, TRIỆU CHỨNG ở đây — không cái nào thay được cái nào.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
            executor.shutdown(wait=True)  # thread thật sự đã xong lúc .result() trả về, wait=True không tốn gì thêm
        except APIError as e:
            # Mọi cách từ chối CÒN LẠI của nhà cung cấp. `RateLimitError` đã
            # được bắt ở trên — nó là CON của APIError, nên thứ tự hai nhánh
            # này KHÔNG hoán đổi được: đảo lại thì 429 bị nuốt vào đây và mất
            # thông điệp `retry_after` cụ thể mà nhà cung cấp đã nói rõ.
            #
            # HAI TRỤC ĐỘC LẬP, không phải hai đầu của một trục:
            #   trục KHÁCH     — mềm 8/8, không bao giờ 500 trần. Kể cả 400/404
            #                    (bug của ta): khách không đáng nhận 500 vì bug
            #                    của ta.
            #   trục VẬN HÀNH  — mức ồn đặt riêng. error cho ca cần người xử,
            #                    warning cho ca tự hết.
            # Ghép hai trục làm một sinh ra CẢ HAI lỗi sai: nổ to thì khách
            # nhận 500 (đúng ca hôm nay), êm thì vận hành không biết khoá sai.
            executor.shutdown(wait=False)
            mo_ta = _mo_ta_loi_nha_cung_cap(e, model=model_dang_thu)
            can_thiep = bool(mo_ta["can_can_thiep"])
            # HAI TÊN SỰ KIỆN RIÊNG, không phải một tên với một trường phân
            # loại. Lý do (security ①): có tên riêng thì `grep` ra được ngay hôm
            # nay, và ngày ai đó gắn cảnh báo thật thì gắn vào tên — không phải
            # sửa code. Một tên chung + trường lọc bắt người dựng cảnh báo phải
            # biết trường đó tồn tại.
            ten_su_kien = (
                "agent_turn_ncc_can_can_thiep" if can_thiep else "agent_turn_ncc_thoang_qua"
            )
            ghi = _logger.error if can_thiep else _logger.warning
            ghi(
                ten_su_kien,
                extra={
                    "user_id": user_id,
                    # correlation_id: nối sự cố với SỐ PHIÊN bị ảnh hưởng mà
                    # không lưu nội dung nào (security ④).
                    "thread_id": thread_id or user_id,
                    **mo_ta,
                },
            )
            # Bề mặt máy-đọc-được THỨ HAI, và là bề mặt DUY NHẤT truy vấn được
            # hôm nay: span Jaeger. Đã nối sẵn, không cần route mới (thêm route
            # = đổi contract), không phơi trạng thái vận hành ra `/health` công
            # khai — `lop_loi_cuoi="AuthenticationError"` trên một endpoint
            # không xác thực chính là báo cho người ngoài biết khoá ta đang hỏng.
            root_span.set_attribute("fin05.su_kien", ten_su_kien)
            root_span.set_attribute("fin05.loi_nha_cung_cap", str(mo_ta["lop_loi"]))
            root_span.set_attribute("fin05.can_can_thiep", can_thiep)
            root_span.set_attribute("fin05.het_han_muc", bool(mo_ta["co_dau_hieu_het_han_muc"]))
            if can_thiep:
                # Span ĐỎ, không chỉ là span có tag. Jaeger lọc theo `error=true`
                # mặc định; một tag tự đặt thì người trực phải biết trước tên nó.
                root_span.set_status(Status(StatusCode.ERROR, ten_su_kien))
                root_span.record_exception(e)

            # HAI CÂU KHÁC NHAU, và khác nhau ở đúng chỗ có hậu quả. Gộp lại là
            # bảo khách "thử lại sau ít phút" trong khi sự thật là "hết tiền,
            # thử lại bao nhiêu lần cũng không hết".
            #
            # Ba điều CẢ HAI câu cố ý KHÔNG nói:
            #  · không "chưa cho phép truy cập" — agent từng nói vậy rồi xin mã
            #    giao dịch, đẩy khách đi làm một việc vô ích (quan sát ⑤).
            #  · không "đã ghi nhận"/"CSKH sẽ liên hệ" — nhánh này KHÔNG tạo vé
            #    nào. Hứa một bản ghi không tồn tại là loại bịa tệ nhất: khách
            #    NGỒI CHỜ một cuộc gọi không bao giờ tới.
            #  · không mã lỗi, không tên nhà cung cấp — vô ích với khách, và lộ
            #    hạ tầng.
            #
            # Chuỗi là HẰNG SỐ ở tầng code, KHÔNG nhờ model sinh: model vừa
            # hỏng mới rơi vào đây, nhờ nó viết câu xin lỗi là phụ thuộc đúng
            # thứ vừa gãy.
            # Nhóm CẦN CAN THIỆP: KHÔNG hứa mốc thời gian (thử lại có thể
            # không giúp gì trong nhiều giờ) VÀ phải chỉ đường sang kênh khác.
            # Đây là ĐIỀU KIỆN của security ③, không phải tuỳ chọn: ta cố ý
            # không ghi lại lượt này, mà cái giá của việc mất dấu KHÔNG đồng
            # đều — mất một khách hỏi phí thì giá ≈ 0, mất một khách đang định
            # BÁO GIAN LẬN thì giá cao và nhạy thời gian. Ta không phân biệt
            # được vì agent hỏng TRƯỚC khi phân loại. Lối đi cho người thật là
            # biện pháp duy nhất còn lại — nó biến "ta mất dấu khách" thành
            # "khách vẫn còn đường".
            reply = (
                "Xin lỗi bạn, hệ thống đang gặp sự cố kỹ thuật nên tạm thời "
                "chưa xử lý được yêu cầu này. Nếu việc của bạn cần xử lý ngay, "
                f"bạn liên hệ {KENH_HO_TRO_KHAC} giúp mình nhé."
                if can_thiep else
                "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                "Bạn nhắn lại giúp mình sau ít phút nhé — tin nhắn của bạn "
                "chưa bị mất gì cả."
            )
            _kq = {
                "reply": reply,
                "tool_calls": [],
                # GĐ3 — nhánh này CŨNG là đích của "bể cạn toàn phần" (mọi
                # model trong LLM_MODEL_POOL đều bị đánh dấu cạn trong lượt
                # này). `models_da_thu` khi đó có ĐỦ mọi model đã thử, không
                # chỉ model cuối — đúng yêu cầu "chứng từ đối soát" (876a240).
                "model": None,  # KHÔNG model nào trả lời thành công ở nhánh này
                "models_da_thu": list(models_da_thu),
                "ticket_id": None,          # CỐ Ý: xem chú thích ở _LOI_CAN_CAN_THIEP
                "should_escalate": False,
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                # Hai giá trị RIÊNG, không gộp: câu hỏi vận hành "sự cố này tự
                # hết hay cần người xử" phải trả lời được bằng một truy vấn.
                "ly_do_fallback": (
                    "nha_cung_cap_can_can_thiep" if can_thiep else "nha_cung_cap_thoang_qua"
                ),
                # 🔴 Hai nhãn trên là KẾT LUẬN ("ai phải làm gì"). Chúng gộp
                # `401` khoá sai · `403` hết hạn ngạch · `404` sai tên model
                # vào MỘT chuỗi — ba sự cố cần ba cách xử khác hẳn nhau.
                # Mã trạng thái đi kèm ở đây để sổ trả lời được câu thứ hai:
                # "nhà cung cấp đã nói gì". Giữ NGUYÊN hai nhãn cũ vì có test
                # đang khẳng định chúng — đổi tên là việc phải đi qua tester.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
        except (GraphRecursionError, FutureTimeoutError) as e:
            # wait=False luôn an toàn ở đây: nếu thread đã xong (nhánh
            # GraphRecursionError) thì trả về ngay lập tức; nếu chưa (nhánh
            # timeout thật) thì không chờ, đúng mục đích.
            executor.shutdown(wait=False)
            # Vòng lặp ReAct vượt quá _AGENT_RECURSION_LIMIT HOẶC vượt trần
            # thời gian tổng (thật sự xảy ra — không phải lý thuyết, xem case
            # CONSUME-002) — KHÔNG để lỗi rơi ra ngoài thành 500, chuyển hẳn
            # cho người xử lý thay vì treo vô thời hạn/crash. root_span vẫn
            # ghi nhận đúng (context manager tự đóng dù có exception), chỉ
            # không có span con của lượt hỏng.
            is_timeout = isinstance(e, FutureTimeoutError)
            _logger.warning(
                "agent_turn_timeout" if is_timeout else "agent_recursion_limit_reached",
                extra={"user_id": user_id, "thread_id": thread_id or user_id},
            )
            root_span.set_attribute("fin05.recursion_limit_reached", not is_timeout)
            root_span.set_attribute("fin05.turn_timeout", is_timeout)
            # Bàn giao session lại cho luồng này TRƯỚC KHI ghi (QA-12). Đặt cờ
            # rồi mới giành khoá: tool call dở dang (nếu có) chạy nốt xong mới
            # nhả khoá, và mọi tool call SAU đó thấy cờ nên từ chối chạm DB —
            # luồng nền bị bỏ rơi không thể sinh ticket thứ hai cho cùng lượt
            # chat này nữa (đo thật: 4/4 case từng sinh ticket ma).
            #
            # Ghi bằng CHÍNH `session` được tiêm, không mở session thứ hai:
            # mở connection thứ hai vào cùng DB trong khi connection thứ nhất
            # đang giữ transaction ghi dở là nguyên nhân "database is locked"
            # (QA-12) — và cũng thừa, vì sau khi giành được khoá thì session
            # này đã an toàn tuyệt đối. Dùng session được tiêm cũng chính là
            # thứ giữ QA-10: ticket luôn nằm đúng DB mà caller chỉ định.
            guard.abandoned.set()
            with guard.lock:
                handoff = flag_human_handoff(
                    session,
                    user_id=user_id,
                    reason="Hệ thống AI gặp khó khăn khi xử lý yêu cầu này (vòng lặp tra cứu không ra kết quả rõ ràng) — cần chuyên viên hỗ trợ trực tiếp.",
                    thread_id=thread_id or user_id,
                )
                # Commit tường minh: khách vừa được báo mã ticket này, nên nó
                # PHẢI tồn tại thật, không phụ thuộc caller có commit hay
                # không (eval harness rollback giữa các case) — báo mã ticket
                # không tra được chính là bịa số liệu, ràng buộc cứng #3.
                session.commit()
            _kq = {
                "reply": "Mình chưa tra được yêu cầu này, để mình chuyển cho chuyên viên hỗ trợ trực tiếp nhé — mã ticket của bạn là "
                + handoff["ticket_id"]
                + ".",
                # GĐ3 — timeout/recursion KHÔNG xoay (ràng buộc PO), nên chỉ
                # có ĐÚNG MỘT model bị thử cho lượt này.
                "model": model_dang_thu,
                "models_da_thu": list(models_da_thu),
                # `None`, KHÔNG phải `[]`. Đây là bản vá cho một lời nói dối của
                # dữ liệu: `[]` nghĩa là "không tool nào được gọi", mà ở nhánh
                # này ta KHÔNG BIẾT — `_invoke` đã ném lỗi nên không có
                # `result["messages"]` để đọc. Khôi phục từ checkpointer thì
                # phải đọc trong lúc luồng nền vẫn đang ghi, đúng race đã gây ra
                # QA-12; không đáng đổi.
                # Trước bản vá này, tester đọc `[]` như quan sát thật và suýt
                # kết luận "agent không gọi tool nào" cho những ca đã chạy tool.
                # `null` = "không khôi phục được", khác hẳn `[]` = "không có".
                "tool_calls": None,
                "ticket_id": handoff["ticket_id"],
                "should_escalate": False,
                # Bốn số 0 này là "KHÔNG ĐO ĐƯỢC", không phải "đo được 0" —
                # `_invoke` đã ném lỗi SAU khi model có thể đã chạy và đã tốn
                # token thật. Cùng loại phân biệt mà `tool_calls: None` ở trên
                # cố ý giữ. Chưa đổi sang None vì có consumer đang cộng dồn
                # trực tiếp; nhưng ai dựng test/dashboard chi phí trên trường
                # này phải biết: lượt fallback ÂM THẦM báo thiếu tiền đã tiêu,
                # và một assertion `usage == 0` sẽ xanh ở CẢ HAI nghĩa.
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                # Câu fallback do CHÍNH TA viết, không qua LLM -> không cần lọc.
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                # Lượt rơi fallback vẫn phải mang tín hiệu: khách bực mà hệ
                # thống lại lỗi chính là lúc CẦN người thật nhất.
                "goi_y_handoff": bool(tin_hieu_cam_xuc),
                # DẤU HIỆU DƯƠNG DỨT KHOÁT của fallback. Tester dùng đúng trường
                # này để loại ca khỏi phép so-cặp, nên nó gánh phần định nghĩa
                # tập-loại-trừ của phép đo — KHÔNG được set nhầm ở đường thường.
                # Trước đây họ phải nhận diện bằng chữ ký chuỗi trong `reply`,
                # thứ trôi được sau một lần sửa câu chữ.
                "ly_do_fallback": _ly_do_fallback(e),
                # `giay_da_troi` là thứ làm nhãn `timeout` KIỂM ĐƯỢC thay vì
                # phải tin. Không có nó, "timeout" chỉ là tên của một nhánh mã.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
    all_messages = result["messages"]
    turn_messages = all_messages[prev_len:]

    reply = ""
    ly_do_dung = None
    for m in reversed(turn_messages):
        if isinstance(m, AIMessage) and not m.tool_calls:
            reply = m.content
            ly_do_dung = (getattr(m, "response_metadata", None) or {}).get("finish_reason")
            break

    # KÊU khi model trả nội dung RỖNG. Trước bản này `reply` nhận "" và đi
    # thẳng ra khách: màn hình trắng, HTTP 200, không lỗi, không log.
    # Ca sinh ra nó: model có reasoning tiêu hết trần token vào phần suy nghĩ
    # rồi không còn chỗ sinh nội dung. Không vá được bằng đoán trần — vá bằng
    # cách làm nhánh im lặng KÊU LÊN, rồi mới biết có cần chỉnh trần không.
    if not str(reply).strip():
        _logger.warning(
            "agent_reply_rong",
            extra={
                "user_id": user_id,
                "thread_id": thread_id or user_id,
                "model": model_da_tra_loi,
                "so_message_luot_nay": len(turn_messages),
                "finish_reason": ly_do_dung,
                "ghi_chu": "Content rỗng nhưng KHÔNG phải do hết trần — chưa rõ nguyên nhân.",
            },
        )

    tool_msgs_by_id = {m.tool_call_id: m for m in turn_messages if isinstance(m, ToolMessage)}
    tool_calls_out: list[dict] = []
    ticket_id = None
    should_escalate = None
    co_loi_otp_trong_luot = False
    loai_khieu_nai = None

    for m in turn_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            tm = tool_msgs_by_id.get(call["id"])
            if tm is None:
                continue
            try:
                payload = json.loads(tm.content)
            except (json.JSONDecodeError, TypeError):
                payload = {"raw": tm.content}
            tool_calls_out.append({"tool_name": call["name"], "args": call["args"], "result": payload})
            if call["name"] == "create_ticket" and "ticket_id" in payload:
                ticket_id = payload["ticket_id"]
                should_escalate = payload.get("should_escalate")
                # ⑨ — loại khiếu nại đọc từ `args`, KHÔNG từ `result`: payload
                # trả về của create_ticket (src/tools/create_ticket.py:110-118)
                # CỐ Ý không mang `complaint_type`. Ai đọc `result` sẽ thấy
                # None và tưởng cơ chế này bất khả thi.
                loai_khieu_nai = (call.get("args") or {}).get("complaint_type")
            # ⑧ · điểm gắn "lượt 1" — lượt này có tool nào bị CỔNG OTP chặn
            # không. Đọc GIÁ TRỊ TRẢ VỀ, không bắt exception: hai lỗi OTP
            # `return` một dict, KHÔNG raise (customer_tools.py:596-613) —
            # cùng cái bẫy `_CHI_THI_DUNG_LAP` đã ghi lại ở đó.
            # Khớp theo `loai` TRƯỚC (có cấu trúc, GĐ2.5 dựng riêng để client
            # khỏi phụ thuộc câu chữ), rồi mới tới neo tiếng Việt cho nhánh
            # `_OTP_REQUIRED_ERROR` — nhánh CỐ Ý không có `loai` (xem chú
            # thích tại chỗ), nên neo chuỗi là đường DUY NHẤT còn lại.
            if isinstance(payload, dict) and payload.get("status") == "error":
                if payload.get("loai") == "otp_het_tuoi" or "xác thực" in str(payload.get("message", "")):
                    co_loi_otp_trong_luot = True

    if ticket_id is not None:
        write_investigation_logs_for_ticket(session, ticket_id=ticket_id, all_messages=all_messages)
        if tin_hieu_cam_xuc:
            _nang_uu_tien_theo_cam_xuc(session, ticket_id=ticket_id)

    # Token usage cộng dồn của LƯỢT NÀY (mọi vòng gọi model bên trong, kể cả
    # vòng gọi tool trung gian) — dùng để đo cost thật (eval/measure_quality.py),
    # KHÔNG ảnh hưởng contract cũ (chỉ thêm key mới, không đổi key sẵn có).
    # T1 — `cached_tokens` là thứ DUY NHẤT nói prompt-cache có ăn hay không.
    # Trước bản này không ai biết cache đang hit 0% hay 50%; suy luận từ tài
    # liệu OpenAI không thay được số đo (và suy luận đó đã sai một lần: mốc
    # thời gian HH:MM nằm ở ký tự 233/16.082 khiến prefix ổn định chỉ ~68
    # token, dưới hẳn ngưỡng 1024 — cache chắc chắn hit 0%).
    # `input_chars` — đại lượng BẤT BIẾN QUA TOKENIZER.
    #
    # Vì sao cần: token của hai nhà cung cấp KHÔNG so được với nhau (tokenizer
    # khác nhau, tiếng Việt là chỗ lệch nhiều nhất), nên chuỗi đo T1->T3 sẽ
    # ĐỨT ngay khi đổi model. Ký tự thì không đổi.
    #
    # ⚠️ ĐẾM ĐÚNG NHỮNG GÌ, KHAI RÕ Ở ĐÂY để nó không thành một "chỉ số một
    # phần trông như đại lượng bất biến":
    #     CÓ    system prompt (15.094 ký tự) + toàn bộ message của mỗi lượt
    #           gọi model, cộng dồn qua các bước ReAct — đúng phần biến thiên
    #     KHÔNG JSON schema của 5 tool = 6.773 ký tự, HẰNG SỐ mỗi lượt gọi
    #
    # Phần thiếu là hằng số ĐO ĐƯỢC, không phải ẩn số: ai cần tổng tuyệt đối
    # thì cộng `6773 × số_luot_goi_model`. Ghi con số ra đây thay vì im lặng
    # bỏ qua — một khoảng trống có tên thì trừ được, không tên thì không.
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "input_chars": 0,
        # ĐẾM LỜI GỌI **ĐÃ TRẢ VỀ**, không phải đã phát — nó chỉ tăng khi một
        # `AIMessage` có `usage_metadata`, tức chỉ khi nhà cung cấp đã đáp.
        # Khai ở đây vì tên trường không nói ra điều đó, và một trường không
        # khai nó đếm gì thì MỌI giá trị của nó đều mơ hồ, kể cả giá trị đúng.
        "so_luot_goi_model": 0,
        # BA trạng thái của token, KHÔNG hai (Lead đo 19/08: 4 lượt CÓ gọi
        # model mà tokens vẫn ghi 0 — "đã gọi, nhà cung cấp không báo số",
        # KHÔNG PHẢI "0 đồng"). `False` = mọi lượt gọi trong turn này đều có
        # số hợp lệ; `True` = ÍT NHẤT một lượt model đã đáp nhưng không có
        # total_tokens — cong_chi_tieu() đọc cờ này để KHÔNG cộng 0 im lặng.
        "token_khong_doc_duoc": False,
        "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
        "so_tool_schema_gui": _SO_TOOL_GUI,
        "suy_luan_gui": _SUY_LUAN_GUI,
        # Danh tính CHỈ DẪN của lượt này. Prompt đã render đổi mỗi phút (có
        # ngày/giờ), nên "cùng một prompt" giữa hai đợt đo là GIẢ ĐỊNH chứ
        # không phải sự kiện — trừ khi so băm MẪU. Trả sẵn để không ai phải
        # nhớ ghi, và để một cặp trước/sau bắc qua hai mẫu khác nhau LỘ RA.
        "bam_mau_prompt": bam_mau_prompt(),
    }
    _ky_tu_he_thong = len(build_system_prompt(current_time=dt.datetime.utcnow()))
    for m in turn_messages:
        meta = isinstance(m, AIMessage) and getattr(m, "usage_metadata", None)
        if meta:
            # Mỗi AIMessage có usage_metadata = MỘT lượt gọi model. Input của
            # lượt đó là system prompt + mọi message đứng TRƯỚC nó. Dựng lại từ
            # `all_messages` thay vì chặn ở tầng model: chặn được thì chính xác
            # hơn, nhưng phải vá vào thư viện — không đáng cho một chỉ số đo.
            j = all_messages.index(m)
            usage["so_luot_goi_model"] += 1
            usage["input_chars"] += _ky_tu_he_thong + sum(
                len(str(getattr(x, "content", "") or "")) for x in all_messages[:j]
            )
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                usage[k] += meta.get(k, 0) or 0
            # Model ĐÃ đáp (ta đang trong nhánh `meta` truthy) nhưng không báo
            # total_tokens -> "không đọc được", không phải "0 đồng" thật. Cờ
            # NÀY giữ trạng thái thứ ba lại, phép cộng `or 0` ở trên vẫn giữ
            # nguyên (Lead: đừng đổi vòng lặp, sẽ hỏng lượt vì lỗi ghi sổ).
            if not meta.get("total_tokens"):
                usage["token_khong_doc_duoc"] = True
            # LangChain gom chi tiết provider vào `input_token_details`; OpenAI
            # đặt phần đã cache ở khoá `cache_read`. Đọc phòng thủ vì tên khoá
            # là hợp đồng của provider, không phải của ta.
            # Token SUY NGHĨ của model reasoning nằm ở `output_token_details`,
            # KHÔNG phải `input_token_details`. Nó được tính vào `output_tokens`
            # nên hoá đơn không sai — nhưng không tách ra thì không ai biết bao
            # nhiêu tiền đang trả cho phần khách không bao giờ đọc.
            usage["reasoning_tokens"] += (meta.get("output_token_details") or {}).get("reasoning", 0) or 0
            chi_tiet = meta.get("input_token_details") or {}
            usage["cached_input_tokens"] += chi_tiet.get("cache_read", 0) or 0

    # Lead đo 19/08: `meta.get(k, 0) or 0` ở trên bóp "không đọc được" thành 0
    # NGAY TRONG vòng lặp — nhưng `cong_chi_tieu()` (graph._ghi_so) vốn đã
    # đúng cho ca này, chỉ là đường `None` của nó không bao giờ tới được vì
    # usage khởi tạo bằng 0, không phải None (graph.py:1242). Vá Ở ĐÂY, sau
    # vòng lặp, KHÔNG sửa `cong_chi_tieu`: nếu model ĐÃ đáp (so_luot_goi_model
    # > 0) mà tổng token vẫn 0 sau khi cộng hết mọi lượt — nghĩa là KHÔNG một
    # lượt nào báo số, không phải "0 đồng" — trả `None` để rơi đúng nhánh
    # `cong_chi_tieu_bo_qua_khong_biet` đã có sẵn thay vì bị nuốt ở nhánh
    # `tokens <= 0` câm lặng của `cong_chi_tieu`.
    if usage["so_luot_goi_model"] > 0 and usage["total_tokens"] == 0:
        usage["input_tokens"] = None
        usage["output_tokens"] = None
        usage["total_tokens"] = None

    # 🔴 Hai GIỚI HẠN Lead khai 19/08 — cả hai là LỰA CHỌN, không phải sót:
    #
    # ① Ca "biết MỘT PHẦN" (nhiều lượt gọi/turn — hình dạng vòng xoay tạo ra):
    #    model A báo 20.000 token, model B (đã xoay sang) không báo gì. Guard
    #    trên chỉ bắn khi TỔNG = 0 — ở đây tổng = 20.000 ≠ 0, guard im, phần
    #    của B KHÔNG BAO GIỜ vào trần. Đánh đổi CÓ Ý: đếm phần biết còn hơn bỏ
    #    cả lượt. Cờ `token_khong_doc_duoc` (per-call, xem trên) vẫn lên `True`
    #    nên vẫn TRUY ĐƯỢC qua bộ đếm `so_luot_khong_doc_duoc_hom_nay()` — chỉ
    #    là phần thiếu không cộng dồn được vào số tiền, vì không có số để cộng.
    #
    # ② Ca "không biết CHÚT NÀO nhưng có MỘT PHẦN field đã biết": test thật đo
    #    được — `{"input_tokens":120,"output_tokens":0,"total_tokens":0}` — cả
    #    BA field về `None`, kể cả `input_tokens=120` nhà cung cấp ĐÃ báo. Đây
    #    là CHIỀU NGƯỢC của lỗi vừa vá (biến ĐÃ BIẾT thành KHÔNG BIẾT), chấp
    #    nhận CÓ Ý: một khối usage_metadata báo dở thì tin cả khối cũng khó,
    #    và giữ input_tokens riêng lẻ không giúp `cong_chi_tieu()` (nó cần
    #    total_tokens) — không phải bỏ sót.
    #
    # Cả hai đủ để "trần tối giản" (PO 876a240) chấp nhận sai số nhỏ, có KHAI,
    # có TRUY ĐƯỢC (bộ đếm `khong_doc_duoc`) — không phải để dựng thêm cơ chế.

    # HAI ca rỗng KHÁC HẲN NHAU, cố ý không gộp:
    #   rỗng + finish_reason="length" -> model tiêu hết trần token vào phần suy
    #       nghĩ thầm, không còn chỗ sinh nội dung. Đây là hỏng CẤU HÌNH CỦA TA,
    #       sửa được bằng LLM_MAX_TOKENS. Phải NỔ: để nó đi tiếp thì bộ đo ghi
    #       một lỗi hạ tầng của ta thành "model trả lời kém" (Luật 1c).
    #   rỗng vì lý do khác -> chưa biết. Cảnh báo, không đoán, không nuốt.
    if not str(reply).strip() and ly_do_dung == "length":
        _logger.error(
            "agent_reply_rong_het_tran",
            extra={
                "user_id": user_id,
                "model": model_da_tra_loi,
                "finish_reason": ly_do_dung,
                "reasoning_tokens": usage["reasoning_tokens"],
                "output_tokens": usage["output_tokens"],
                "llm_max_tokens": LLM_MAX_TOKENS,
            },
        )
        raise TraLoiRongError(
            f"Model {model_da_tra_loi} tra noi dung RONG voi finish_reason=length — "
            f"tran token bi phan suy nghi an het ({usage['reasoning_tokens']}/"
            f"{usage['output_tokens']} token dau ra la reasoning). "
            f"Nang LLM_MAX_TOKENS (hien {LLM_MAX_TOKENS})."
        )

    # NGUỒN TRUY VẾT cho luật xuất xứ của O3: mọi mã/dãy số >=7 ký tự agent nói
    # ra phải có mặt ở một trong hai nơi này — nếu không thì nó ở đâu ra?
    #   · kết quả tool của lượt này VÀ của các lượt trước (`rap_nguon_o3`)
    #   · mọi lời KHÁCH đã gõ trong hội thoại — không chỉ lượt hiện tại, vì
    #     khách có thể đọc mã biên lai ở lượt 1 rồi agent nhắc lại ở lượt 3
    # Đây là ràng buộc cứng 3 viết thành một phép kiểm chạy được.
    # TÁCH HAI KÊNH NGUỒN — không gộp thành một chuỗi. Payload tool là JSON nên
    # dấu phẩy trong đó là DẤU PHÂN CÁCH TRƯỜNG; lời khách là văn xuôi nên dấu
    # phẩy/chấm là dấu ngăn hàng nghìn. Gộp chung rồi trích bằng một luật thì một
    # trong hai kênh chắc chắn bị hiểu sai — và hiểu sai ở kênh JSON đẻ ra số
    # KHÔNG TỒN TẠI trong tập nguồn hợp lệ.
    nguon_tool = rap_nguon_o3(all_messages, tool_calls_out)
    loi_khach = " ".join(
        m.content for m in all_messages if isinstance(m, HumanMessage) and isinstance(m.content, str)
    )
    reply_da_loc, nhom_khop = loc_dau_ra(
        reply,
        nguon=nguon_tool,
        loi_khach=loi_khach,
        tin_nhan_khach=message,
        thread_id=thread_id or user_id,
    )
    # O2 ĐẾM-TRƯỚC-CHẶN-SAU (security, docs/security/mo-neo-quy-trinh-cho-O2.md,
    # PO duyệt) — CHẠY TRÊN `reply` GỐC, không phải `reply_da_loc`. Mật độ liệt
    # kê là tín hiệu về HÀNH VI của agent (đang đọc lại nội quy hay không), độc
    # lập với việc O1-O4 có chặn câu đó hay không — trộn hai thứ sẽ làm phân
    # phối mật độ mù chính câu bị O3/O4 thay bằng CAU_AN_TOAN.
    #
    # Trước bản này hàm KHÔNG CÓ call site nào ở đường chạy thật (chỉ tests/ và
    # eval/) — mệnh đề "đếm trước, nâng lên chặn khi thấy rò" tới giờ rỗng trong
    # production. Trả qua ENVELOPE (không chỉ ghi Redis) vì cùng lý do ba trường
    # chẩn đoán bên dưới: eval gọi thẳng graph, Redis là fakeredis per-process,
    # nên bộ đếm vô hình với người đo nếu chỉ ghi Redis.
    # ⑭ — đường THỨ HAI sinh bằng chứng: lượt này model đã chạy và TOOL bị cổng
    # OTP chặn. Phủ ca ④ không bắn (vd câu không thuộc NHÓM B nhưng model vẫn
    # quyết gọi tool) — thiếu nhánh này thì luồng resend hợp lệ của khách sẽ bị
    # chính ⑭ chặn nhầm.
    if co_loi_otp_trong_luot:
        tang_tin_hieu(_TEN_TIN_HIEU_DA_BI_OTP_CHAN, thread_id or user_id)

    # ⑧ · K3 — chèn SAU bộ lọc. Xem chú thích tại `_them_canh_bao_mao_danh`
    # về lý do KHÔNG được dời lên trước.
    reply_da_loc = _them_canh_bao_mao_danh(
        reply_da_loc, co_loi_otp=co_loi_otp_trong_luot, ticket_id=ticket_id
    )

    # ⑨ · K2 — CÂU SÀNG LỌC LỪA ĐẢO, tất định, 0 token.
    # Điều kiện bắn ĐỌC TỪ TẦNG NÀY, không giao model quyết: vé vừa tạo có
    # `complaint_type == "wrong_recipient"`, và thread chưa từng được hỏi.
    # Chuyên gia đòi hỏi ở MỌI ca chuyển nhầm — kể cả ca trông rõ ràng, vì
    # chính ca rõ ràng mới là ca hay bị bỏ qua.
    # Chèn SAU bộ lọc, cùng lý do ⑧ (xem chú thích ở `_them_canh_bao_mao_danh`).
    if ticket_id is not None and loai_khieu_nai == "wrong_recipient":
        _tid_sl = thread_id or user_id
        if doc_tin_hieu(_TEN_TIN_HIEU_DA_HOI_SANG_LOC, _tid_sl) == 0:
            tang_tin_hieu(_TEN_TIN_HIEU_DA_HOI_SANG_LOC, _tid_sl)
            reply_da_loc = (reply_da_loc.rstrip() + "\n\n" + HOI_SANG_LOC_LUA_DAO).strip()
    tin_hieu_lo_chi_thi_ket_qua = tin_hieu_lo_chi_thi(reply, thread_id=thread_id or user_id)
    _kq_cuoi = {
        "reply": reply_da_loc,
        "tool_calls": tool_calls_out,
        # GĐ3 (876a240) — model ĐÃ TRẢ LỜI thật (không phải LLM_MODEL hằng
        # số) + MỌI model đã thử trong lượt này theo thứ tự, kể cả lần bị
        # nhà cung cấp từ chối (nhà cung cấp tính tiền CẢ lần thất bại —
        # "chứng từ đối soát hoá đơn" phải ghi đủ, không chỉ model cuối).
        "model": model_da_tra_loi,
        "models_da_thu": list(models_da_thu),
        "ticket_id": ticket_id,
        "should_escalate": should_escalate,
        "usage": usage,
        # BỐN trường CHẨN ĐOÁN (`tin_hieu_lo_chi_thi` thêm ở Luật 18). Không
        # phải tiện tay: eval KHÔNG sinh một dòng log nào (runner gọi thẳng
        # graph, logging_config chưa từng khởi tạo) và Redis là fakeredis
        # per-process — nên log + bộ đếm của bộ lọc VÔ HÌNH với người đo. Thiếu
        # chúng thì O1/O3/O4 cùng ra một câu an toàn giống hệt nhau, đúng họ
        # "hai trạng thái đội chung một vỏ"; và trước Luật 18, mật độ liệt kê
        # còn tệ hơn — không chỉ vô hình mà CHƯA TỪNG được tính ở đường thật.
        "loc_dau_ra": nhom_khop,
        "tin_hieu_lo_chi_thi": tin_hieu_lo_chi_thi_ket_qua,
        # ES-xx -> FRONTEND render nút "gặp người thật". KHÔNG tự gọi
        # request_human_handoff: quyền quyết định gặp người là của KHÁCH
        # (CTRL-001 / ISO-IEC 25059), hệ thống chỉ ĐỀ NGHỊ.
        "goi_y_handoff": bool(tin_hieu_cam_xuc),
        "duong": DUONG_DAY_DU,
        "ly_do_fallback": None,  # TƯỜNG MINH null, KHÔNG thiếu key — thiếu key
        # không phân biệt được với "bản cũ chưa có trường này".
        **_reply_goc_cho_eval(reply, nhom_khop),
    }
    _ghi_so(_kq_cuoi, thread_id, user_id)
    return _kq_cuoi
