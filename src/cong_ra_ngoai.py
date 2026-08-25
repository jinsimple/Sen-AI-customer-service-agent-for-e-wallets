"""CỔNG RA NGOÀI — chốt chặn + bộ đếm cho MỌI lời gọi tới nhà cung cấp LLM.

VÌ SAO TỒN TẠI (§5.F, 18/08/2026)
---------------------------------
Hai nguồn ĐỘC LẬP cùng chỉ vào một lỗ trong cùng một ngày:

    tester   phép dò "vô hiệu hoá hậu quả trước" trên 620/620 ca -> bắt đúng
             MỘT lời gọi rời máy: POST api.openai.com/v1/embeddings, nguồn
             `tests/test_api/test_injection.py` — file KHÔNG có cổng nào
    coder    dựng ca nghiệm thu, gọi `search_policy` -> đi thẳng ra OpenAI,
             chặn lại bởi khoá giả (401). Khoá thật thì đó là tiền ngoài A3.

Ba lớp giữ hoá đơn đang có **không lớp nào** chặn được hai đường trên:

    ① FIN05_CHO_PHEP_TON_TIEN   là `skipif` NẰM TRONG FILE TEST
                                -> file test quên khai thì không có gì bắn
    ② .DANG-DONG-BANG-LLM       PO thật quyết 18/08: bỏ hẳn (video demo xong)
    ③ PHAN_LUONG_BAT            chỉ định tuyến lượt CHAT

⟹ Chốt chặn phải nằm ở nơi **MỌI lời gọi đi qua**, không nằm trong `tests/`.

🔴 VÌ SAO Ở TẦNG TRANSPORT, KHÔNG Ở `_khoa_cho_nha_cung_cap()`
--------------------------------------------------------------
Tôi (coder) đề xuất `_khoa_cho_nha_cung_cap()` trước, và nó SAI. [ĐO] hàm đó
được gọi **đúng hai lần, ở mức module** (`config.py:283` và `:303`) — nó CẤP
KHOÁ, không phải chốt chặn lời gọi. Bộ đếm cắm ở đó sẽ **mãi mãi bằng 2 và
trông như đang đếm**, tức đúng loại dụng cụ nói dối mà dự án đang đi vá.

Sai lầm: cả hai đường (chat + embedding) cùng CHẠM hàm đó, nên tôi kết luận cả
hai ĐI QUA nó. *Cùng chạm một lần* ≠ *đi qua mỗi lần* — **Luật G**.

Seam đúng, [ĐO] chứ không suy (openai 3.0.0 · httpx 0.28.1): cả `ChatOpenAI`
lẫn `OpenAIEmbeddings` đều nhận `http_client` ⟹ **một `httpx.Client` dùng
chung** là nơi duy nhất mọi lời gọi thật sự đi qua.

⭐ Và nó thấy **request THẬT TRÊN DÂY**, kể cả lượt **SDK tự retry**
(`max_retries=2`, `graph.py`). Mọi bộ đếm đặt TRÊN SDK ghi **1** cho **3** lần
bắn ra — đếm thiếu đúng loại lượt đắt nhất, cùng hình dạng bẫy
`so_luot_goi_model = 0` (STATE §8).

⚠️ ĐƯỜNG EMBEDDING KHÔNG ĐI QUA `graph.py`
------------------------------------------
`search_policy` -> `search_policy_text` -> `store.search` -> `embed_query` ->
nhà cung cấp. Một chốt chặn chỉ cắm ở đường chat sẽ để lọt **đúng đường ít
cổng nhất** — và đó chính là đường cả tester lẫn coder đâm vào. Vì vậy ca
nghiệm thu BẮT BUỘC chạy trên đường embedding, **không suy từ đường chat**.

HAI CƠ CHẾ, KHÔNG PHẢI MỘT
---------------------------
    CỜ CHO PHÉP (nhị phân)  -> CHẶN ngay, KHÔNG cần con số nào
    BỘ ĐẾM BA RỔ (số)       -> ĐẾM ngay, KHÔNG ngưỡng

Lỗ §5.F là câu **có/không** (*"có lời gọi nào ra Internet ngoài ý định không"*),
không phải câu **bao nhiêu**. Ngược lại, đặt NGƯỠNG bây giờ là đặt theo số tự
bịa — A3 là *"chưa nạp gì"*, **không phải một hạn mức thành số** — và một cổng
đã bị nới một lần thì không ai tin nó nữa. Đếm trước cho ta MẪU SỐ THẬT để sau
đặt ngưỡng có căn cứ.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

import httpx

from src.config import LLM_BASE_URL, TRAN_TOKEN_LLM_MOI_NGAY
from src.dau_ma_nguon import bam_ma_nguon
from src.observability.so_usage import ghi_usage
from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.cong_ra_ngoai")

# Sổ RIÊNG, cùng volume với `usage.jsonl` — KHÔNG chung file.
# `usage.jsonl` là *một dòng một LƯỢT CHAT*; sổ này là *một dòng một REQUEST
# HTTP*. Khác hạt, khác dân số — xem docstring `ghi_usage`.
DUONG_SO_CONG = Path(os.environ.get("DUONG_SO_CONG_RA_NGOAI", "/app/logs/cong_ra_ngoai.jsonl"))

BIEN_CO = "FIN05_CHO_PHEP_GOI_RA_NGOAI"
_TAT = {"", "0", "false", "no", "off"}


class GoiRaNgoaiBiChanError(RuntimeError):
    """Một lời gọi tới nhà cung cấp bị chặn TRƯỚC khi ra dây.

    Ném chứ không trả rỗng: một lời gọi bị chặn mà trả về "không có kết quả"
    là **không phân biệt được** với một lời gọi thật sự không tìm thấy gì —
    đúng lớp lỗi `except InvalidToken` của `crypto_types` và đúng ràng buộc
    cứng 3 (*không tra được thì phải NÓI RÕ là không tra được*).
    """


def la_bi_chan(loi: BaseException | None, sau_toi_da: int = 8) -> bool:
    """Lỗi này (hoặc nguyên nhân của nó) có phải do CHỐT CHẶN không?

    🔴 PHẢI DÙNG HÀM NÀY, ĐỪNG `isinstance` TRỰC TIẾP — và đây là lý do, đo
    thật chứ không phải phòng xa:

        [ĐO] store.search(...) với cờ TẮT
             nơi gọi thấy   : openai.APIConnectionError — "Connection error."
             __cause__      : src.cong_ra_ngoai.GoiRaNgoaiBiChanError
             bộ đếm         : bi_chan +3, da_phat 0

    SDK của nhà cung cấp **bọc mọi lỗi transport** thành `APIConnectionError`.
    Nên ở nơi gọi, một lượt **bị ta cố ý chặn** trông **y hệt** một lượt **đứt
    mạng thật**. Người debug đọc *"Connection error"* rồi đi tìm lỗi mạng,
    trong khi sự thật là một cái cổng của chính ta đang đóng.

    Đó là **Luật H ở tầng ta không sửa được**: nhánh lỗi in ra KẾT LUẬN
    (*"mất kết nối"*) thay vì TRIỆU CHỨNG (*"bị chốt chặn từ chối"*). Ta không
    đổi được SDK, nên việc phải làm là **để sự thật với tới được** — chuỗi
    `__cause__` giữ nguyên lỗi gốc, và hàm này là đường đi tới nó.

    ⚠️ Kèm một tính chất đã đo, không phải bug: SDK **thử lại 3 lần** vào một
    cổng đã đóng (`max_retries=2` + lần đầu) ⟹ một lời gọi bị chặn sinh **3**
    dòng `bi_chan` và **3** dòng log. Tốn 0 đồng, nhưng ai đọc bộ đếm phải biết
    `bi_chan` đếm **lượt RA DÂY BỊ CHẶN**, không phải **lượt gọi của người dùng**.
    """
    cur, n = loi, 0
    while cur is not None and n < sau_toi_da:
        if isinstance(cur, GoiRaNgoaiBiChanError):
            return True
        cur = cur.__cause__ or cur.__context__
        n += 1
    return False


def _khai_tuong_minh() -> bool | None:
    """`None` = KHÔNG KHAI (khác hẳn "khai là tắt"). Ba trạng thái, không hai."""
    v = os.environ.get(BIEN_CO)
    if v is None:
        return None
    return v.strip().lower() not in _TAT


# ---------------------------------------------------------------------------
# TRẦN CHI TIÊU TỐI GIẢN (GĐ3, PO thật chốt 19/08 — `876a240`)
#
# 🔴 CHỈ token model CHAT (LLM), KHÔNG bao gồm chi tiêu embedding — dù cả hai
# đi CÙNG transport này (`http_client_dung_chung()` dùng chung cho `ChatOpenAI`
# lẫn `OpenAIEmbeddings`). Lý do KHÔNG gộp: embedding KHÁC nhà cung cấp
# (`EMBEDDING_BASE_URL` != `LLM_BASE_URL`, xem config.py) — cộng token của hai
# nhà cung cấp vào một trần là cộng hai đơn vị khác nhau rồi so với một ngưỡng,
# ra một con số TRÔNG hợp lệ mà không có nghĩa gì. Tên biến `TRAN_TOKEN_LLM_
# MOI_NGAY` tự khai giới hạn này — ĐÚNG BẰNG CẤU TRÚC, không chỉ bằng tên:
# `cong_chi_tieu()` HIỆN TẠI có ĐÚNG MỘT điểm gọi trong repo, tại
# `src/agents/graph.py::_ghi_so` (đường LLM) — `src/rag/store.py` (đường
# embedding) không gọi hàm này ở đâu cả.
#
# 🔴 SẼ THÀNH HAI, có chủ đích (PO-agent chốt 19/08, sau ping thăm dò deepseek
# thật): hàm ping khai bể (`MODEL_POOL_PING`, CHƯA VIẾT — chờ QA/QC đổi cổng
# đếm-điểm-gọi từ ĐẾM SỐ sang DANH SÁCH TÊN trước) SẼ là điểm gọi thứ hai —
# ping cũng tiêu tiền thật, không đi qua trần thì trần nói dối đúng lúc
# `MODEL_POOL_PING=eager` đốt hạn ngạch nhanh nhất (crashloop = ping dồn dập).
# Khi hàm ping tồn tại, danh sách hợp lệ là { `_ghi_so`, <tên hàm ping cố
# định> } — KHÔNG phải "đếm == 2", đúng bài học "chốt bằng TÊN, không bằng
# SỐ" đã dùng cho cổng nhập bể.
#
# FAIL-CLOSED khi Redis lỗi — NGƯỢC với `llm_pool.py` (fail-open) và
# `thread_signals.py` (fail-open) một cách CÓ CHỦ ĐÍCH: đây là cơ chế BẢO VỆ
# TIỀN, không phải tiện ích né lỗi. Không đọc được trạng thái chi tiêu ⟹
# KHÔNG BIẾT có đang vượt trần không ⟹ coi như CÓ vượt, chặn. Đọc sai theo
# hướng ngược lại (coi như chưa vượt) biến một sự cố hạ tầng thành chi tiêu
# KHÔNG GIỚI HẠN — đúng thất bại một trần chi tiêu tồn tại để ngăn.
#
# CỬA SỔ ĐUA — khai, không phải sửa: `cho_phep_goi_ra_ngoai()` đọc tổng TRƯỚC
# khi gọi, `cong_chi_tieu()` cộng vào SAU khi lượt xong. Nhiều lượt đồng thời
# có thể cùng đọc "chưa vượt" rồi cùng gọi, tổng thật vượt trần một quãng.
# Chấp nhận được cho trần THEO NGÀY (sai số nhỏ so với quy mô một ngày) — ghi
# ra để người sau không tưởng nhầm là bug khi phát hiện lại.
_KHOA_CHI_TIEU_PREFIX = "fin05:chi_tieu_llm_token:"
# TTL rộng hơn 1 ngày để không xoá nhầm giữa lúc đọc/ghi lệch múi giờ nhẹ —
# khoá đã mang NGÀY trong tên nên không tái dùng, TTL chỉ để tự dọn rác.
_TTL_CHI_TIEU_GIAY = 3 * 24 * 3600

# Đếm LƯỢT (không phải token — token chính là thứ không đọc được), song song
# với bộ đếm chi tiêu. Lead đo 19/08: `graph.py` đã ghi cờ `token_khong_doc_
# duoc` vào sổ usage.jsonl từ bản vá None-vs-0, nhưng KHÔNG NƠI NÀO ĐỌC nó —
# một trạng thái được ghi mà không ai theo dõi có cùng tác dụng với không ghi.
# Bộ đếm này biến nó thành MỘT CON SỐ đọc được cùng chỗ với trần chi tiêu,
# không phải một cờ nằm chờ ai đó tình cờ mở log lên đọc.
_KHOA_KHONG_DOC_DUOC_PREFIX = "fin05:chi_tieu_llm_khong_doc_duoc:"


def _khoa_chi_tieu_hom_nay() -> str:
    return f"{_KHOA_CHI_TIEU_PREFIX}{datetime.now(UTC).strftime('%Y%m%d')}"


def _khoa_khong_doc_duoc_hom_nay() -> str:
    return f"{_KHOA_KHONG_DOC_DUOC_PREFIX}{datetime.now(UTC).strftime('%Y%m%d')}"


def ghi_nhan_chi_tieu_khong_doc_duoc() -> None:
    """+1 vào bộ đếm LƯỢT "gọi model rồi, không đọc được token" HÔM NAY.

    KHÔNG cộng vào trần chi tiêu (không có số để cộng) — đây là dụng cụ QUAN
    SÁT, không phải một cơ chế chặn thứ hai. Đọc `so_luot_khong_doc_duoc_
    hom_nay()` để biết điểm mù của trần đang nở tới đâu trong ngày.

    Redis lỗi -> log cảnh báo, KHÔNG raise — cùng triết lý `cong_chi_tieu()`.
    """
    try:
        client = get_default_client()
        khoa = _khoa_khong_doc_duoc_hom_nay()
        client.incrby(khoa, 1)
        client.expire(khoa, _TTL_CHI_TIEU_GIAY)
    except Exception as e:  # noqa: BLE001
        _logger.warning("ghi_nhan_khong_doc_duoc_that_bai", extra={"loi": repr(e)})


def so_luot_khong_doc_duoc_hom_nay() -> int | None:
    """Bao nhiêu lượt HÔM NAY đã gọi model mà không đọc được token.

    `None` = không đọc được (Redis lỗi) — KHÁC `0` = đọc được và đúng là
    chưa có lượt nào, cùng quy ước "None khác 0" xuyên suốt file này.
    """
    try:
        raw = get_default_client().get(_khoa_khong_doc_duoc_hom_nay())
    except Exception as e:  # noqa: BLE001
        _logger.warning("doc_khong_doc_duoc_that_bai", extra={"loi": repr(e)})
        return None
    return int(raw) if raw else 0


def cong_chi_tieu(tokens: int | None) -> None:
    """Cộng `tokens` vào tổng chi tiêu LLM HÔM NAY (UTC). Gọi cho MỌI lượt
    LLM (kể cả lượt hỏng), KHÔNG gọi cho lượt embedding (xem khối comment
    phía trên) — thiết kế để gọi vô điều kiện từ `graph._ghi_so`, hàm ĐÃ chạy
    trên cả 5 đường trả về (nhẹ · 3 fallback · nặng).

    🔴 `tokens=None` (không phải `0`) nghĩa KHÔNG ĐỌC ĐƯỢC — cùng quy ước
    "None khác 0" đã dùng xuyên `graph.py`/`so_usage.py`. Bỏ qua CÓ Ý, không
    phải lỗi: một lượt hỏng-không-biết-tốn-bao-nhiêu (timeout/đứt mạng) không
    thể cộng một con số không tồn tại vào trần mà không tự bịa số — đây là
    GIỚI HẠN ĐÃ KHAI của bản "trần tối giản" (PO `876a240` cố ý không dựng hệ
    cost-guard đầy đủ), không phải khoảng trống bị bỏ sót.

    Redis lỗi -> log cảnh báo, KHÔNG raise: một lượt đã tính tiền RỒI không
    được phép hỏng vì ghi sổ thất bại (đúng hợp đồng của `ghi_usage`, cùng
    file này gọi ngay bên dưới) — mất một dòng cộng dồn không mất tiền đã tiêu.
    """
    if tokens is None:
        _logger.info("cong_chi_tieu_bo_qua_khong_biet")
        return
    if tokens <= 0:
        return
    try:
        client = get_default_client()
        khoa = _khoa_chi_tieu_hom_nay()
        client.incrby(khoa, tokens)
        client.expire(khoa, _TTL_CHI_TIEU_GIAY)
    except Exception as e:  # noqa: BLE001
        _logger.warning("cong_chi_tieu_that_bai", extra={"tokens": tokens, "loi": repr(e)})


def _duoi_tran_chi_tieu_hom_nay() -> bool:
    """Tổng chi tiêu LLM hôm nay còn DƯỚI trần không?

    `TRAN_TOKEN_LLM_MOI_NGAY is None` (biến rỗng/thiếu) ⟹ luôn `True` — KHÔNG
    giới hạn, đúng hành vi trước khi có trần này.

    FAIL-CLOSED: Redis lỗi ⟹ `False` (coi như ĐÃ vượt) — xem lý do ở khối
    comment đầu mục "TRẦN CHI TIÊU" phía trên. Đây là hàm DUY NHẤT trong file
    này đảo ngược triết lý fail-open của các cơ chế phụ trợ khác — cố ý.
    """
    if TRAN_TOKEN_LLM_MOI_NGAY is None:
        return True
    try:
        raw = get_default_client().get(_khoa_chi_tieu_hom_nay())
        da_tieu = int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning("doc_chi_tieu_that_bai_coi_nhu_vuot_tran", extra={"loi": repr(e)})
        return False
    return da_tieu < TRAN_TOKEN_LLM_MOI_NGAY


def cho_phep_goi_ra_ngoai() -> tuple[bool, str]:
    """Có được phép gọi ra nhà cung cấp không, VÀ vì sao — trả cả hai.

    Trả kèm LÝ DO là bắt buộc, không phải tiện tay: một cờ chỉ trả `True/False`
    thì lúc điều tra ta biết *"bị chặn"* mà không biết *"chặn theo lời khai hay
    theo suy đoán"* — và suy đoán sai thì phải sửa suy đoán, còn lời khai sai
    thì phải sửa `.env`. Hai việc khác nhau.

    🔴 MẶC ĐỊNH LÀ **TỪ CHỐI** (đảo 18/08, Giai đoạn 2 ②).

    Bản đầu mặc định CHO PHÉP, và lý do khi đó đúng: ba container đang chạy
    không có `FIN05_CHO_PHEP_GOI_RA_NGOAI` trong `Config.Env`, mà biến môi
    trường **ghim lúc TẠO container** (STATE §9) ⟹ mặc-định-từ-chối sẽ **giết
    sản phẩm** ngay khi ảnh được dựng lại.

    Điều kiện ấy nay đã được gỡ: `docker-compose.yml` khai
    `FIN05_CHO_PHEP_GOI_RA_NGOAI: ${…:-1}` cho service `backend`, và [ĐO]
    `docker compose config` nội suy ra `"1"` ở **cả ba** ngăn xếp.

    🔴 THỨ TỰ MỘT CHIỀU (ADR-035) — người sau đọc dòng này trước khi đảo lại:
        dán compose mà chưa đảo mặc định  ->  VÔ HẠI
        đảo mặc định mà chưa dán compose  ->  SẢN PHẨM CHẾT ở lần dựng tới
    Ai revert một trong hai nửa **phải revert nửa kia trước**, không phải sau.

    VÌ SAO ĐẢO — nó đóng lỗ CUỐI, và đó là lỗ tôi tự đâm vào:

        giai đoạn 1   pytest ✅ · lượt chat ✅ · script nháp ❌
        giai đoạn 2   cả ba ✅

    Script nháp chạy `python x.py` **không phân biệt được với sản phẩm** — nên
    thứ duy nhất phân biệt được là **sản phẩm TỰ KHAI mình là sản phẩm**
    (compose đặt cờ), còn mọi thứ không khai thì mặc định **không được tiêu
    tiền**. Đây là fail-closed đúng nghĩa: cùng nếp `dau_ma_nguon.py`
    (`.bam_ma_nguon` rỗng ⟹ TỪ CHỐI khởi động).

    ⚠️ Nhánh `suy_tu_pytest` GIỮ NGUYÊN dù mặc định đã là từ chối. Nó không còn
    cần cho việc CHẶN, nhưng nó vẫn mang một thứ khác: **LÝ DO**. Một lượt bị
    chặn dưới pytest và một lượt bị chặn vì thiếu khai là hai chuyện khác nhau
    lúc điều tra, và sổ `cong_ra_ngoai.jsonl` ghi lại `ly_do` đó. Gộp chúng
    thành một là mất một trạng thái — ba trạng thái, không phải hai.
    """
    khai = _khai_tuong_minh()
    if khai is not None:
        # Trần chi tiêu là chốt ĐỘC LẬP, đứng SAU lời khai cho phép — một lời
        # khai `=1` mở đường CHO PHÉP về nguyên tắc, nhưng KHÔNG mua quyền
        # vượt trần đã tự đặt. Chỉ hỏi Redis khi nhánh này CÓ THỂ trả True —
        # nhánh False (khai=0) không cần biết trần, kết quả đã là chặn.
        if khai and not _duoi_tran_chi_tieu_hom_nay():
            return False, "tran_chi_tieu"
        return khai, "khai_tuong_minh"
    # `pytest` trong `sys.modules` = đang chạy dưới bộ test. Đây là SUY ĐOÁN,
    # không phải lời khai — nên nó được ghi nhãn khác, và nó đứng SAU lời khai
    # tường minh (ai cần chạy test tốn tiền thật thì khai `=1`).
    if "pytest" in sys.modules:
        return False, "suy_tu_pytest"
    # Không ai khai gì ⟹ TỪ CHỐI. Sản phẩm khai qua compose; thứ không khai thì
    # không được tiêu tiền.
    return False, "mac_dinh_tu_choi"


# ---------------------------------------------------------------------------
# BỘ ĐẾM BA RỔ — `so_luot_da_phat`
#
# 🔴 BA RỔ NÀY KHÔNG PHẢI `hit · miss · hỏng`. Security xin ba rổ đó cho tầng
# CACHE; tầng transport **không đếm được `hit`** vì theo đúng định nghĩa, một
# cache hit KHÔNG BAO GIỜ chạm tới transport. Đếm nó ở đây sẽ cho một cột `hit`
# **hằng 0** — lại đúng một dụng cụ nói dối. Khi có cache, `hit` đếm ở tầng
# cache, và đó là **NGUỒN ĐỘC LẬP** với bộ đếm này (Luật D: hai nguồn thật,
# không phải một biến viết hai lần).
#
# Ba rổ ĐÚNG cho tầng này, theo thứ transport thật sự phân biệt được:
_dem: dict[str, int] = {"da_phat": 0, "bi_chan": 0, "hong": 0}
_khoa_dem = threading.Lock()


def so_luot_da_phat() -> dict[str, int]:
    """Ảnh chụp bộ đếm. BA MẪU SỐ RIÊNG — người đọc **không được** cộng lại.

        da_phat   ra tới dây VÀ có response (mọi status)  -> CÓ THỂ tính tiền
        bi_chan   cờ từ chối, KHÔNG ra dây                -> chắc chắn 0 đồng
        hong      ra dây rồi lỗi (timeout · đứt · ta bỏ)  -> 🔴 KHÔNG ĐỌC ĐƯỢC

    🔴 `hong` là rổ dễ bị bóp thành 0 nhất và là rổ quan trọng nhất.
    [ĐO STATE §6.⓷] `14:26:44` ta bỏ request → `14:26:45.335` DashScope trả
    **HTTP 200 trọn vẹn, 1,2s SAU**: nhà cung cấp tính theo thứ họ SINH, không
    theo thứ ta ĐỌC. ⟹ một lượt trong rổ `hong` **có thể đã tốn tiền và ta
    không có cách nào biết**. Nó KHÔNG phải 0, nó là *"không đọc được"*.

    ⟹ **KHÔNG `sum(... or 0)`.** Cộng ba rổ lại là biến *"không biết"* thành
    một con số trông chắc chắn — đúng lỗi §8 mà dự án đã trả giá.
    """
    with _khoa_dem:
        return dict(_dem)


def _ghi_ro(ro: str, *, host: str | None = None, duong: str | None = None,
            ly_do: str | None = None) -> None:
    """Tăng bộ đếm trong tiến trình VÀ ghi một dòng vào SỔ TRÊN VOLUME.

    🔴 VÌ SAO CẦN CẢ HAI, và vì sao bộ đếm một mình là KHÔNG ĐỦ — tôi (coder)
    land bộ đếm sáng 18/08 rồi tự bác cách nó được mô tả:

        [ĐO] docker-entrypoint.sh:16   UVICORN_WORKERS mặc định 4
             ⟹ BỐN tiến trình ⟹ BỐN bộ đếm độc lập, không cái nào biết cái nào
             ⟹ cả bốn về 0 mỗi lần recreate
             ⟹ không endpoint, không file ⟹ KHÔNG đọc được từ ngoài tiến trình

    PO-agent đã định ghi nó vào STATE là *"mốc nền đầu tiên của dự án"*. Sai —
    và nó là **đúng loại con số trông hợp lệ** mà dự án đã trả giá (§8).

    Sổ trên named volume đóng cả ba khoảng cách: **gộp được 4 worker** (cùng
    ghi một file), **sống qua recreate**, **đọc được từ ngoài**. Và nó làm được
    thứ một endpoint KHÔNG làm được — endpoint chỉ trả con số của **một** worker
    ngẫu nhiên mà **trông như** trả toàn bộ.

    Bộ đếm trong RAM vẫn giữ: nó là thứ **ca đối chứng** đọc được ngay trong
    cùng tiến trình, không phải đi mở file.
    """
    with _khoa_dem:
        _dem[ro] += 1
    # `ghi_usage` có hợp đồng "KHÔNG BAO GIỜ làm hỏng lượt vì lỗi ghi sổ" —
    # nên gọi thẳng, không bọc thêm try: bọc chồng là giấu mất cảnh báo-một-lần
    # của chính nó.
    ghi_usage(
        {
            "ts": datetime.now(UTC).isoformat(),
            "ro": ro,
            # host + PATH thôi. 🔴 KHÔNG query string: một số nhà cung cấp mang
            # tham số ở đó, và dựng một đường rò vào log NGAY TRONG cơ chế sinh
            # ra để chặn rò là hỏng theo cách buồn cười nhất.
            "host": host,
            "duong": duong,
            "ly_do": ly_do,
            "bam_ma_nguon": bam_ma_nguon(),
            # PID để tách lại BỐN worker. Thiếu nó thì sổ gộp được nhưng không
            # bao giờ tách lại được — và "gộp mà không tách lại được" là cách
            # một dân số pha tạp hình thành.
            "pid": os.getpid(),
        },
        duong=DUONG_SO_CONG,
    )


class _TransportCoChotChan(httpx.BaseTransport):
    """Bọc transport thật: hỏi cờ TRƯỚC khi ra dây, rồi ghi rổ theo kết cục.

    Thứ tự BẮT BUỘC là hỏi-rồi-mới-gửi. Gửi rồi mới hỏi thì tiền đã tiêu, và
    cả cơ chế này chỉ còn là một cái sổ.
    """

    def __init__(self, that: httpx.BaseTransport) -> None:
        self._that = that

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        # [ĐO 26/08] `LLM_BASE_URL` trống KHÔNG chặn gì ở `_khoa_cho_nha_cung_cap`
        # (nó chỉ hỏi "ĐÍCH có đổi không", base_url=None ⟹ chưa đổi ⟹ không raise)
        # — nhưng SDK vẫn tự chọn đích mặc định (api.openai.com thật) và
        # `LLM_MODEL` rơi về `OPENAI_MODEL`. Ba cái rơi cùng hướng ⟹ lời gọi
        # THÀNH CÔNG tới một nhà cung cấp khác, không một dòng lỗi. Chốt ở đây
        # vì đây là nơi biết ĐÍCH THẬT (`request.url.path`), không phải suy từ
        # cờ môi trường — CI và production đọc cờ giống hệt nhau, chỉ đích
        # lúc sắp gửi mới khác. Loại trừ `/embeddings`: rơi về OpenAI ở đó là
        # CÓ CHỦ Ý (EMBEDDING_BASE_URL trống mặc định), chặn cả cụm là gãy RAG.
        if not LLM_BASE_URL and not request.url.path.endswith("/embeddings"):
            _ghi_ro("bi_chan", host=request.url.host, duong=request.url.path,
                    ly_do="llm_base_url_trong")
            _logger.error(
                "goi_ra_ngoai_dich_roi_mac_dinh",
                extra={"host": request.url.host, "duong": request.url.path},
            )
            raise GoiRaNgoaiBiChanError(
                f"Lời gọi chat tới {request.url.host}{request.url.path} bị "
                f"CHẶN: LLM_BASE_URL trống. Không đặt LLM_BASE_URL, SDK rơi "
                f"về đích mặc định (OpenAI thật) thay vì nhà cung cấp đã "
                f"ghim — đúng loại rò tiền + đo nhầm model mà cơ chế này "
                f"sinh ra để chặn. Đặt LLM_BASE_URL tường minh trước khi "
                f"gọi chat thật."
            )
        cho_phep, ly_do = cho_phep_goi_ra_ngoai()
        if not cho_phep:
            _ghi_ro("bi_chan", host=request.url.host, duong=request.url.path, ly_do=ly_do)
            # KHÔNG log URL đầy đủ: query string của một số nhà cung cấp mang
            # tham số, và ta không muốn dựng thêm một đường rò vào log ngay
            # trong cơ chế sinh ra để chặn rò.
            _logger.error(
                "goi_ra_ngoai_bi_chan",
                extra={"host": request.url.host, "duong": request.url.path, "ly_do": ly_do},
            )
            raise GoiRaNgoaiBiChanError(
                f"Lời gọi tới {request.url.host}{request.url.path} bị CHẶN "
                f"({ly_do}). Đây là chốt chặn chi phí ở tầng transport: mọi lời "
                f"gọi tới nhà cung cấp LLM/embedding đều đi qua đây. "
                f"Cần gọi thật thì đặt {BIEN_CO}=1 — và biết rằng nó TỐN TIỀN."
            )
        try:
            phan_hoi = self._that.handle_request(request)
        except Exception:
            # Ra dây rồi mới hỏng ⟹ KHÔNG BIẾT có tốn tiền không. Vào rổ `hong`,
            # KHÔNG vào `da_phat` (nói quá) và KHÔNG bỏ qua (nói thiếu).
            _ghi_ro("hong", host=request.url.host, duong=request.url.path)
            raise
        _ghi_ro("da_phat", host=request.url.host, duong=request.url.path)
        return phan_hoi

    def close(self) -> None:
        self._that.close()


_client: httpx.Client | None = None
_khoa_client = threading.Lock()


def http_client_dung_chung() -> httpx.Client:
    """`httpx.Client` DÙNG CHUNG cho cả `ChatOpenAI` lẫn `OpenAIEmbeddings`.

    MỘT client cho cả hai là điều kiện để bộ đếm và cờ có ý nghĩa: hai client
    riêng = hai bộ đếm riêng = không ai trả lời được *"tổng cộng đã phát bao
    nhiêu lượt ra ngoài"*, đúng câu §5.F cần trả lời.

    `httpx.Client` an toàn giữa các thread; dựng một lần cho cả tiến trình.
    """
    global _client
    if _client is None:
        with _khoa_client:
            if _client is None:
                _client = httpx.Client(transport=_TransportCoChotChan(httpx.HTTPTransport()))
    return _client
