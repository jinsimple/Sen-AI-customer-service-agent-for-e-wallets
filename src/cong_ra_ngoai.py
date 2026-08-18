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

import httpx

_logger = logging.getLogger("fin05.cong_ra_ngoai")

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


def cho_phep_goi_ra_ngoai() -> tuple[bool, str]:
    """Có được phép gọi ra nhà cung cấp không, VÀ vì sao — trả cả hai.

    Trả kèm LÝ DO là bắt buộc, không phải tiện tay: một cờ chỉ trả `True/False`
    thì lúc điều tra ta biết *"bị chặn"* mà không biết *"chặn theo lời khai hay
    theo suy đoán"* — và suy đoán sai thì phải sửa suy đoán, còn lời khai sai
    thì phải sửa `.env`. Hai việc khác nhau.

    🔴 MẶC ĐỊNH KHÔNG THỂ LÀ TỪ-CHỐI-TẤT-CẢ ở giai đoạn này. Ba container đang
    chạy không có `FIN05_CHO_PHEP_GOI_RA_NGOAI` trong `Config.Env`, và biến môi
    trường **ghim lúc TẠO container** (STATE §9) ⟹ mặc-định-từ-chối sẽ GIẾT sản
    phẩm ngay khi ảnh được dựng lại. Đó là đổi hành vi sản phẩm để vá một lỗ
    của công cụ đo — không đánh đổi được.

    ⚠️ HẠN CHẾ KHAI TRƯỚC — bản này KHÔNG phủ script nháp chạy `python x.py`:
    nó không phân biệt được với sản phẩm. Phủ nó cần ĐẢO mặc định thành từ chối
    + compose khai `=1`, tức **giai đoạn 2, sau lần dựng ảnh**.

        giai đoạn 1 (bản này)   pytest ✅ · lượt chat ✅ · script nháp ❌
        giai đoạn 2 (sau dựng)  đảo mặc định + compose khai =1  ⟹ cả ba ✅

    Viết ra vì **một bản vá được mô tả rộng hơn thứ nó làm chính là cách một lỗ
    được coi như đã đóng.**
    """
    khai = _khai_tuong_minh()
    if khai is not None:
        return khai, "khai_tuong_minh"
    # `pytest` trong `sys.modules` = đang chạy dưới bộ test. Đây là SUY ĐOÁN,
    # không phải lời khai — nên nó được ghi nhãn khác ở dòng trên, và nó đứng
    # sau lời khai tường minh (ai cần chạy test tốn tiền thật thì khai `=1`).
    if "pytest" in sys.modules:
        return False, "suy_tu_pytest"
    return True, "mac_dinh_cho_phep"


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


def _ghi_ro(ro: str) -> None:
    with _khoa_dem:
        _dem[ro] += 1


class _TransportCoChotChan(httpx.BaseTransport):
    """Bọc transport thật: hỏi cờ TRƯỚC khi ra dây, rồi ghi rổ theo kết cục.

    Thứ tự BẮT BUỘC là hỏi-rồi-mới-gửi. Gửi rồi mới hỏi thì tiền đã tiêu, và
    cả cơ chế này chỉ còn là một cái sổ.
    """

    def __init__(self, that: httpx.BaseTransport) -> None:
        self._that = that

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        cho_phep, ly_do = cho_phep_goi_ra_ngoai()
        if not cho_phep:
            _ghi_ro("bi_chan")
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
            _ghi_ro("hong")
            raise
        _ghi_ro("da_phat")
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
