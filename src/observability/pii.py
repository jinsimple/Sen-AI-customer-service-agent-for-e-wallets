"""PII scrubbing — BẮT BUỘC chạy TRƯỚC KHI dữ liệu được log hay gửi lên
backend trace (Jaeger) — Giai đoạn 3 checklist observability. Áp dụng cho mọi
văn bản tự do có thể chứa PII trước khi đưa vào JSON log hay span attribute:
tin nhắn khách hàng, reply agent, args/kết quả tool.

Dùng **Microsoft Presidio** (`presidio-analyzer`) làm engine chính — quyết
định 2026-08-10, thay cho quyết định trước đó (spaCy gọi thẳng): sản phẩm
nhận diện khách hàng sẽ mở rộng thêm nhiều loại PII theo thời gian (số thẻ,
IBAN, ví crypto, IP...), Presidio có sẵn catalog recognizer cho các loại đó —
thêm 1 loại PII mới về sau chỉ cần đăng ký thêm 1 `PatternRecognizer`, không
phải tự viết regex quét thủ công từng loại. Presidio tự dùng spaCy làm NLP
engine bên trong (vẫn model `xx_ent_wiki_sm` đã verify trước đó), gắn thêm
sẵn EmailRecognizer/PhoneRecognizer/IbanRecognizer/CryptoRecognizer/
IpRecognizer/UrlRecognizer/DateRecognizer — không cần tự viết cho các loại
"tương lai" đó nữa.

CHỈ dùng `presidio-analyzer` (phát hiện), KHÔNG dùng `presidio-anonymizer`
(che/thay thế) — lý do thật phát hiện lúc cài: `presidio-anonymizer` ép
`cryptography<49.0.0`, ĐÈ xuống bản có 3 CVE đã biết (PYSEC-2026-3552/3553/
3554), trong khi dự án đang dùng `cryptography>=50.0.0` cho mã hoá field tại
chỗ (`src/db/crypto_types.py`). Tự làm phần thay thế ký tự (đã có sẵn, verify
kỹ) rẻ hơn nhiều so với đánh đổi 1 lỗ hổng đã biết trong thư viện mã hoá cốt
lõi — không đáng.

Vẫn giữ 1 `PatternRecognizer` tự viết cho SĐT/CCCD/CMND/số tài khoản VN
(Presidio không có sẵn recognizer riêng cho định dạng VN) — đăng ký CHUNG vào
1 `AnalyzerEngine` với các recognizer có sẵn, không phải 2 tầng tách rời như
thiết kế trước.

**NER tên người tiếng Việt (quyết định 2026-08-11, sau khi phát hiện gap
thật ở bản trước):** `SpacyRecognizer` bên trong Presidio dùng model đa ngôn
ngữ nhỏ (`xx_ent_wiki_sm`) — KHÔNG chuyên tiếng Việt, bỏ sót nhiều tên người
tiếng Việt (case cụ thể: "Anh Lê Hoàng Nam..." — xem lịch sử
tests/test_observability/test_pii.py). Thêm `_VietnameseNameRecognizer`
(`EntityRecognizer` tự viết, gọi `underthesea.ner()`) làm lớp BỔ SUNG cho
`SpacyRecognizer`, KHÔNG thay thế — 2 recognizer chạy song song, kết quả gộp
qua `_merge_overlapping` sẵn có. underthesea bắt được case spaCy bỏ sót,
nhưng PHÁT HIỆN THẬT lúc verify: gán nhãn B-PER (sai) cho vài chuỗi không
phải tên người — mã giao dịch có tiền tố+số (`TXN20260810000123`) và viết
tắt toàn hoa (`CCCD`). Lọc 2 loại false-positive này bằng quy tắc đơn giản,
không phải danh sách tiền tố cứng (tên người tiếng Việt thật không chứa chữ
số, và không toàn hoa) — xem `_plausible_person_span()`.

PHÁT HIỆN THẬT khi verify (xem tests/test_observability/test_pii.py) — ghi
lại trung thực, không tô hồng:
  - `SpacyRecognizer` gán SAI NHÃN loại thực thể cho tên người (ra
    LOCATION/ORGANIZATION thay vì PERSON) khá thường xuyên. Vì mục tiêu là
    CHE (không phải phân loại), scrubber che theo ĐÚNG loại Presidio trả về
    (không ép về PERSON) — chấp nhận over-redact, không nới lỏng để giảm
    false positive, đúng nguyên tắc checklist Giai đoạn 3.
  - underthesea vẫn bỏ sót một số tên (case "Trần Thị Bích" — nhưng case này
    ĐÃ được `SpacyRecognizer` bắt riêng, nên pipeline gộp vẫn che đúng; đây
    là ví dụ cụ thể cho lý do giữ CẢ HAI recognizer thay vì thay thế nhau).
    Chưa có case nào cả 2 recognizer cùng bỏ sót được ghi nhận tại thời điểm
    này — nếu phát sinh, cập nhật ghi chú này, không âm thầm giữ nguyên.
  - Graceful-degrade: thiếu `presidio-analyzer`/`underthesea` (chưa cài) hoặc
    model NER thất bại lúc load → rơi về CHỈ lớp regex VN (SĐT/CCCD/email cơ
    bản tự viết) thay vì crash toàn app. `_VietnameseNameRecognizer` load lỗi
    riêng không kéo sập cả `AnalyzerEngine` — vẫn còn `SpacyRecognizer` +
    catalog Presidio khác hoạt động bình thường.
"""
from __future__ import annotations

import functools
import logging
import re

_logger = logging.getLogger("fin05.observability.pii")

# --- Regex fallback (KHÔNG cần Presidio) — dùng khi presidio-analyzer chưa
# cài/lỗi load, giữ tối thiểu 3 loại PII cấu trúc rõ nhất. -------------------
_FALLBACK_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_FALLBACK_PHONE_RE = re.compile(r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)")
_FALLBACK_ID_RE = re.compile(r"(?<![\w-])\d{9,19}(?!\d)")


def scrub_regex(text: str) -> str:
    """Chỉ lớp regex — dùng riêng trong test để CHỨNG MINH vì sao cần lớp NER
    (tên người tự do sẽ LỌT qua lớp này), và làm fallback khi Presidio không
    khả dụng. KHÔNG dùng trực tiếp cho log thật (dùng `scrub_pii`)."""
    out = _FALLBACK_EMAIL_RE.sub("[EMAIL]", text)
    out = _FALLBACK_PHONE_RE.sub("[PHONE]", out)
    out = _FALLBACK_ID_RE.sub("[ID_NUMBER]", out)
    return out


# SĐT/CCCD/CMND/số tài khoản VN — Presidio không có sẵn recognizer riêng cho
# định dạng VN, đăng ký thêm vào registry chung. Cùng pattern đã verify ở
# bản trước (giữ nguyên ID nội bộ có tiền tố chữ như TXN.../TCK... không bị
# che — đó là mã tra cứu, không phải PII).
#
# Trần trên 14 -> 19 (ADR-024, đo khi làm scrub-tại-điểm-ghi cho `resolutions.
# note`): "thẻ 9704123456789012" (16 số) lọt nguyên vẹn qua bản trần-14 — không
# recognizer nào của Presidio bắt số thẻ không đúng định dạng Luhn/BIN chuẩn
# quốc tế thay nó. 19 là độ dài tối đa của số thẻ theo ISO/IEC 7812; số tài
# khoản ngân hàng VN (tới 14 số) vẫn nằm trong khoảng cũ nên không đổi hành vi.
_VN_PHONE_REGEX = r"(?<![\w-])(?:\+84|0)\d{9}(?!\d)"
_VN_ID_REGEX = r"(?<![\w-])\d{9,19}(?!\d)"

# Nhãn NER "tự do" — đoán loại thực thể từ NGỮ CẢNH (SpacyRecognizer/
# underthesea), khác nhãn PHI-NER khớp theo REGEX có cấu trúc (VN_PHONE_
# NUMBER/VN_ID_NUMBER/EMAIL_ADDRESS/IBAN_CODE/...). Chỉ nhóm NÀY mới được áp
# `_plausible_person_span` (Bảo Mật 19/08) — "MISC" là nhãn spaCy chưa map
# được của Presidio (log cảnh báo "Entity MISC is not mapped..." đã thấy
# trong sổ), vẫn là một dự đoán NER, không phải khớp cấu trúc, nên vẫn thuộc
# nhóm này.
_NHAN_NER_TU_DO = {"PERSON", "LOCATION", "ORGANIZATION", "PERSON_VN", "MISC"}


# Đại từ nhân xưng + xưng hô tiếng Việt — KHÔNG phải tên người, dù NER hay
# gán nhãn B-PER. Phát hiện thật 2026-08-13 lúc đo scrub trên tin nhắn khách:
# "tôi chuyển 5tr cho số 09..." bị biến thành "[PERSON] chuyển ..." làm agent
# mất luôn chủ ngữ của câu. Đây là danh sách ĐÓNG (đại từ tiếng Việt là tập
# hữu hạn, không sinh thêm), khác với quy tắc chung ở _plausible_person_span.
_DAI_TU_KHONG_PHAI_TEN = {
    "tôi", "tui", "mình", "em", "anh", "chị", "cô", "chú", "bác", "ông", "bà",
    "con", "cháu", "bạn", "cậu", "tớ", "ta", "họ", "nó", "ai",
}


def _cat_gon_dai_tu(text: str, start: int, end: int, label: str) -> tuple[int, int, str] | None:
    """Cắt đại từ/động từ thừa ở HAI ĐẦU span nhãn PERSON, trả None nếu rỗng.

    VÌ SAO CẦN (đo thật 2026-08-13 trên tin nhắn khách):
    NER tiếng Việt gán nhãn cho CỤM NHIỀU TỪ, không phải đúng tên: "tôi bị"
    -> PERSON, "anh bị trừ" -> PERSON, "chị" -> ORGANIZATION. Che nguyên cụm
    làm câu mất chủ ngữ ("[PERSON] trừ tiền 2 lần") — agent không còn hiểu ai
    làm gì. Lọc theo chuỗi khớp chính xác KHÔNG ăn vì span là "tôi bị" chứ
    không phải "tôi".

    Cắt gọn thay vì bỏ cả span để giữ đúng hai chiều: "anh Huy" -> vẫn che
    "Huy" (tên thật) nhưng trả lại "anh" cho câu.

    CHỈ áp dụng cho nhãn người — không đụng SĐT/CCCD/email (đó là PII cứng,
    không có chuyện cắt gọn).
    """
    if "PERSON" not in label.upper() and "ORGANIZATION" not in label.upper():
        return (start, end, label)

    span = text[start:end]
    # Cắt từ đầu
    while True:
        m = re.match(r"^\s*(\w+)", span)
        if not m or m.group(1).lower() not in _DAI_TU_KHONG_PHAI_TEN:
            break
        start += m.end()
        span = text[start:end]
    # Cắt từ cuối: bỏ token cuối nếu là đại từ hoặc từ nối thường gặp
    while True:
        m = re.search(r"(\w+)\s*$", span)
        if not m or m.group(1).lower() not in _DAI_TU_KHONG_PHAI_TEN | _TU_NOI_THUONG_GAP:
            break
        end -= len(span) - m.start()
        span = text[start:end]

    span = text[start:end].strip()
    if not span or span.lower() in _DAI_TU_KHONG_PHAI_TEN | _TU_NOI_THUONG_GAP:
        return None
    # Căn lại biên sau khi strip
    lech_trai = len(text[start:end]) - len(text[start:end].lstrip())
    return (start + lech_trai, start + lech_trai + len(span), label)


# Động từ/từ nối hay bị NER gộp nhầm vào span tên người trong câu khiếu nại.
_TU_NOI_THUONG_GAP = {"bị", "trừ", "là", "cho", "của", "đã", "được", "vừa", "chuyển", "nhận"}


# Từ tiếng Việt THÔNG THƯỜNG (không phải đại từ) từng bị NER gán nhầm nhãn
# người/tổ chức — phát hiện thật 19/08 (PO thật test kịch bản A): "Mã giao
# dịch..." bị gán B-PER, agent nhận "[PERSON_VN] giao dịch..." mất luôn chủ
# ngữ. 🔴 DANH SÁCH MỞ — khác `_DAI_TU_KHONG_PHAI_TEN` (đại từ là tập HỮU HẠN,
# liệt kê hết được): "từ thường bị NER nhận nhầm" thì KHÔNG hữu hạn, sẽ còn
# phát sinh case mới ngoài "mã". Phát hiện case mới -> THÊM VÀO ĐÂY, không âm
# thầm bỏ qua (đúng cam kết đã viết cho _DAI_TU_KHONG_PHAI_TEN ở trên, Bảo
# Mật 19/08 nhắc lại rõ trong docs/security/2026-08-19-gd4-dinh-hang-scrub-
# pii-model-input.md).
# CẬP NHẬT 19/08 (chiều): PO-agent [ĐO] "Giao dịch bị treo mấy ngày rồi" ->
# "ngày" gán LOCATION — câu KHÔNG mã, KHÔNG số, KHÔNG tên, chứng minh đây
# không phải phạm vi hẹp "mã giao dịch" mà là NER bóp méo từ tiếng Việt đời
# thường nói chung. Coder tự đo thêm, thấy "tuần" (viết hoa đầu câu) cũng gán
# PERSON — thêm CẢ HAI, đúng cam kết ở trên. QA/QC đang dựng corpus đo tỉ lệ
# trước/sau trên golden_set.jsonl — case mới từ đó sẽ vào đây tiếp.
_TU_THUONG_BI_NHAN_NHAM_LA_TEN = {"mã", "ngày", "tuần"}


def _plausible_person_span(span: str) -> bool:
    """Lọc false-positive THẬT phát hiện lúc verify underthesea.ner() trên dữ
    liệu của dự án: mã giao dịch/ticket nội bộ (vd `TXN20260810000123`, tiền
    tố new_id() + số, xem src/tools/base.py::new_id) và viết tắt toàn hoa (vd
    `CCCD`) đôi lúc bị gán nhãn B-PER sai. Tên người tiếng Việt thật KHÔNG
    chứa chữ số và KHÔNG viết toàn hoa — quy tắc chung, không phải danh sách
    tiền tố ID cứng (không cần cập nhật khi có prefix ID mới).

    Bảo Mật 19/08 (df186c0): trước đây hàm này CHỈ áp cho `underthesea.ner()`
    (`_underthesea_person_spans` dưới) — `SpacyRecognizer` của Presidio chạy
    KHÔNG lọc, nên "TXN...352" gán LOCATION/MISC lọt nguyên vẹn thành
    `[LOCATION]`. `scrub_pii()` giờ áp hàm này cho MỌI recognizer trả nhãn NER
    TỰ DO (xem `_NHAN_NER_TU_DO`), không riêng underthesea — ĐÂY LÀ SỬA MỘT MÔ
    TẢ SAI BẢN CHẤT, không phải nới lỏng: quy tắc chỉ loại span CHƯA TỪNG LÀ
    PII (có số/toàn hoa/đại từ/từ thường gặp), không đụng quyết định "che
    theo đúng loại Presidio trả về dù có thể sai LOẠI" cho PII THẬT."""
    if any(ch.isdigit() for ch in span):
        return False
    if span.isupper():
        return False
    sach = span.strip().lower()
    if sach in _DAI_TU_KHONG_PHAI_TEN:
        return False
    if sach in _TU_THUONG_BI_NHAN_NHAM_LA_TEN:
        return False
    return True


def _underthesea_person_spans(text: str) -> list[tuple[int, int, str]]:
    """underthesea.ner() trả token (có thể ghép nhiều từ, vd 'Lê Hoàng Nam')
    dưới dạng chuỗi CON của text gốc (không word-segment bằng dấu '_') — map
    lại offset ký tự bằng con trỏ tuần tự (`str.find` từ vị trí sau token
    trước), đúng thứ tự token trả về. Bỏ qua token không tìm thấy (không nên
    xảy ra trong thực nghiệm, nhưng an toàn hơn là tính sai offset)."""
    from underthesea import ner as underthesea_ner

    spans: list[tuple[int, int, str]] = []
    cursor = 0
    for token, _pos, _chunk, ner_tag in underthesea_ner(text):
        idx = text.find(token, cursor)
        if idx == -1:
            continue
        end = idx + len(token)
        if ner_tag in ("B-PER", "I-PER") and _plausible_person_span(token):
            spans.append((idx, end, "PERSON_VN"))
        cursor = end
    return spans


class _VietnameseNameRecognizer:
    """`presidio_analyzer.EntityRecognizer` tự viết bọc `underthesea.ner()` —
    lớp NER tiếng Việt chuyên biệt BỔ SUNG cho `SpacyRecognizer` (đa ngôn ngữ,
    xem docstring module), không thay thế. Đăng ký riêng, tách khỏi try/except
    chính của `_load_analyzer()` — thiếu `underthesea`/lỗi load KHÔNG được
    kéo sập toàn bộ AnalyzerEngine (vẫn còn SpacyRecognizer + catalog khác)."""

    def __new__(cls):
        from presidio_analyzer import EntityRecognizer, RecognizerResult

        class _Impl(EntityRecognizer):
            def load(self) -> None:  # underthesea tự lazy-load model bên trong
                pass

            def analyze(self, text, entities, nlp_artifacts=None):
                return [
                    RecognizerResult(entity_type="PERSON_VN", start=start, end=end, score=0.75)
                    for start, end, _label in _underthesea_person_spans(text)
                ]

        return _Impl(supported_entities=["PERSON_VN"], supported_language="vi", name="VietnameseNameRecognizer")


@functools.lru_cache(maxsize=1)
def _load_analyzer():
    """Lazy singleton — chỉ dựng AnalyzerEngine lúc thật sự cần (nạp model
    NER tốn vài trăm ms). Trả None nếu presidio-analyzer/spaCy/model chưa
    sẵn sàng — PHẢI graceful-degrade về regex fallback, không crash app."""
    try:
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "vi", "model_name": "xx_ent_wiki_sm"}],
            }
        ).create_engine()

        registry = RecognizerRegistry(supported_languages=["vi"])
        # Catalog có sẵn của Presidio cho "vi" — Email/Phone/Iban/Crypto/Ip/
        # Url/Date/MedicalLicense/MacAddress + SpacyRecognizer (NER tên
        # người/tổ chức/địa danh) — đây chính là phần "tương lai có thêm
        # nhiều loại PII khác" không cần tự viết regex riêng cho từng loại.
        registry.load_predefined_recognizers(languages=["vi"], nlp_engine=nlp_engine)
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity="VN_PHONE_NUMBER",
                supported_language="vi",
                patterns=[Pattern(name="vn_phone", regex=_VN_PHONE_REGEX, score=0.9)],
            )
        )
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity="VN_ID_NUMBER",
                supported_language="vi",
                patterns=[Pattern(name="vn_id", regex=_VN_ID_REGEX, score=0.6)],
            )
        )
        try:
            registry.add_recognizer(_VietnameseNameRecognizer())
        except Exception as e:  # thiếu underthesea — KHÔNG kéo sập cả analyzer
            _logger.warning("pii_underthesea_unavailable_spacy_only", extra={"error": repr(e)})
        return AnalyzerEngine(nlp_engine=nlp_engine, registry=registry, supported_languages=["vi"])
    except Exception as e:  # thiếu presidio-analyzer, thiếu spaCy, hoặc thiếu model
        _logger.warning("pii_presidio_unavailable_fallback_regex_only", extra={"error": repr(e)})
        return None


def _merge_overlapping(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    """Presidio có thể trả nhiều recognizer TRÙNG/CHỒNG lấn 1 vùng ký tự (vd
    EMAIL_ADDRESS chồng URL trên phần domain) — gộp thành 1 khối để tránh xử
    lý 2 lần đè lên nhau làm hỏng offset khi thay chuỗi. Gộp nhãn loại lại
    (an toàn hơn chọn 1 loại) — đúng nguyên tắc "che nhầm còn hơn để lọt"."""
    if not spans:
        return []
    spans = sorted(spans, key=lambda s: s[0])
    merged = [spans[0]]
    for start, end, label in spans[1:]:
        last_start, last_end, last_label = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end), f"{last_label}/{label}" if label not in last_label else last_label)
        else:
            merged.append((start, end, label))
    return merged


def scrub_pii(text: str | None) -> str | None:
    """DÙNG HÀM NÀY cho mọi log/span attribute có khả năng chứa văn bản tự do
    của khách/agent. Presidio (đủ khả dụng) hoặc regex fallback (xem
    docstring module)."""
    if not text:
        return text

    analyzer = _load_analyzer()
    if analyzer is None:
        return scrub_regex(text)

    results = analyzer.analyze(text=text, language="vi")
    if not results:
        return text

    raw_spans = [(r.start, r.end, r.entity_type) for r in results]
    # Bảo Mật 19/08 (df186c0): áp `_plausible_person_span` cho MỌI recognizer
    # trả nhãn NER TỰ DO (đoán theo ngữ cảnh — PERSON/LOCATION/ORGANIZATION/
    # MISC của SpacyRecognizer, PERSON_VN của underthesea), KHÔNG riêng
    # underthesea như trước. CỐ Ý KHÔNG áp cho nhãn PHI-NER (VN_PHONE_NUMBER/
    # VN_ID_NUMBER/EMAIL_ADDRESS/IBAN_CODE/...): các recognizer đó match theo
    # REGEX có cấu trúc — số/chữ hoa là TÍN HIỆU ĐÚNG của chúng, không phải
    # nhiễu như với NER. Áp nhầm sang nhóm này sẽ tự vô hiệu hoá chính
    # recognizer đang bảo vệ PII thật (số điện thoại/CCCD toàn chữ số).
    raw_spans = [
        (start, end, label)
        for start, end, label in raw_spans
        if label not in _NHAN_NER_TU_DO or _plausible_person_span(text[start:end])
    ]
    raw_spans = [s for s in (_cat_gon_dai_tu(text, *s) for s in raw_spans) if s]
    if not raw_spans:
        return text

    spans = _merge_overlapping(raw_spans)
    chars = list(text)
    for start, end, label in sorted(spans, key=lambda s: s[0], reverse=True):
        chars[start:end] = list(f"[{label}]")
    return "".join(chars)
