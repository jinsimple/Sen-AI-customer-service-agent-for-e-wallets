"""Giai đoạn 3 (observability checklist) — verify PII scrubbing THẬT (engine
Presidio + underthesea, xem src/observability/pii.py), không suy luận từ đọc
code. Bài test bắt buộc theo đúng checklist: chạy CHỈ regex trên câu có tên
người → xác nhận tên LỌT; chạy pipeline đầy đủ → xác nhận bắt được — đồng
thời ghi nhận trung thực giới hạn thật còn lại (nếu có). Test check TÊN ĐÃ
BIẾN MẤT khỏi output, KHÔNG check đúng 1 nhãn cụ thể (vd [PERSON]) — nhãn
loại NER cho tiếng Việt không ổn định, chính xác của mask quan trọng hơn tên
nhãn hiển thị."""
from __future__ import annotations

from src.observability.pii import scrub_pii, scrub_regex


def test_regex_only_catches_structured_pii():
    text = "SĐT của tôi là 0901234567, email a@b.com, CCCD 001234567890."
    out = scrub_regex(text)
    assert "0901234567" not in out
    assert "a@b.com" not in out
    assert "001234567890" not in out
    assert "[PHONE]" in out
    assert "[EMAIL]" in out
    assert "[ID_NUMBER]" in out


def test_regex_only_does_not_touch_transaction_id():
    """Mã giao dịch có tiền tố chữ (TXN.../TCK...) là ID nội bộ CẦN giữ
    nguyên trong log để còn tra cứu được — không phải PII."""
    text = "Giao dịch TXN20260810000123 và ticket TCK-abc123def456 đã tạo."
    out = scrub_regex(text)
    assert "TXN20260810000123" in out
    assert "TCK-abc123def456" in out


def test_regex_only_lets_free_form_name_leak():
    """ĐÚNG kịch bản checklist yêu cầu: câu có tên người nhưng KHÔNG có SĐT/
    email/CCCD nào — layer regex đơn thuần KHÔNG bắt được, tên bị LỌT
    nguyên văn. Đây chính là lý do phải có thêm lớp NER."""
    text = "Tôi chuyển nhầm cho Trần Thị Bích 270.000 đồng vào chiều qua."
    out = scrub_regex(text)
    assert "Trần Thị Bích" in out, "Case này PHẢI lọt ở regex-only để chứng minh cần lớp NER"


def test_hybrid_catches_name_that_regex_alone_missed():
    text = "Tôi chuyển nhầm cho Trần Thị Bích 270.000 đồng vào chiều qua."
    out = scrub_pii(text, purpose="log")
    assert "Trần Thị Bích" not in out
    assert out != text, "Phải có ít nhất 1 chỗ bị che (nhãn cụ thể không quan trọng, xem docstring)"


def test_hybrid_still_catches_structured_pii_too():
    text = "Anh Phạm Minh Tuấn, SĐT 0901234567, CCCD 001234567890 vừa gọi."
    out = scrub_pii(text, purpose="log")
    assert "Phạm Minh Tuấn" not in out
    assert "0901234567" not in out
    assert "001234567890" not in out


def test_underthesea_catches_case_spacy_alone_used_to_miss():
    """2026-08-11: thêm `_VietnameseNameRecognizer` (underthesea) làm lớp bổ
    sung cho SpacyRecognizer — case này TRƯỚC ĐÓ là "known gap" ghi nhận
    trung thực (spaCy đa ngôn ngữ bỏ sót hoàn toàn), giờ verify THẬT đã bắt
    được, không còn là gap nữa. Nếu assertion này fail nghĩa là
    underthesea/dependency liên quan có vấn đề — không phải quay lại trạng
    thái "known gap" cũ mà cần điều tra lại."""
    text = "Anh Lê Hoàng Nam vừa gọi điện phàn nàn về phí giao dịch."
    out = scrub_pii(text, purpose="log")
    assert "Lê Hoàng Nam" not in out


def test_underthesea_catches_compound_name_with_title():
    """Tên ghép dài + có chức danh xen giữa — case khác hẳn case trên, kiểm
    underthesea cụ thể (không tái dùng case đã biết)."""
    text = "Chị Nguyễn Thị Thanh Hường - Trưởng phòng CSKH - đã duyệt hồ sơ."
    out = scrub_pii(text, purpose="log")
    assert "Nguyễn Thị Thanh Hường" not in out


def test_underthesea_does_not_false_positive_on_internal_ids_or_abbreviations():
    """PHÁT HIỆN THẬT lúc verify underthesea.ner(): gán nhãn B-PER (sai) cho
    mã giao dịch có tiền tố+số (TXN.../TCK...) và viết tắt toàn hoa (CCCD) —
    xem _plausible_person_span() trong pii.py. Test này xác nhận filter hoạt
    động: KHÔNG được để lộ nghĩa là hỏng filter, làm mất khả năng tra cứu ID
    nội bộ (đây là guarantee đã có từ trước, thêm underthesea không được phá
    vỡ)."""
    text = "Giao dịch TXN20260810000123 và ticket TCK-abc123def456 đã tạo."
    out = scrub_pii(text, purpose="log")
    assert "TXN20260810000123" in out
    assert "TCK-abc123def456" in out


def test_underthesea_still_documented_gap_when_both_recognizers_miss():
    """Chưa tìm được case nào CẢ HAI recognizer (SpacyRecognizer +
    underthesea) cùng bỏ sót tại thời điểm 2026-08-11 — "Trần Thị Bích" từng
    là ví dụ (underthesea bỏ sót) nhưng SpacyRecognizer đã bắt riêng, nên
    pipeline gộp vẫn che đúng. Test này giữ nguyên tinh thần minh bạch: nếu
    sau này phát hiện case cả 2 cùng bỏ sót, thêm test ghi nhận trung thực
    tại đây thay vì im lặng bỏ qua — hiện tại xác nhận pipeline gộp vẫn che
    đúng case đã biết underthesea một mình bỏ sót."""
    text = "Tôi chuyển nhầm cho Trần Thị Bích 270.000 đồng vào chiều qua."
    out = scrub_pii(text, purpose="log")
    assert "Trần Thị Bích" not in out


def test_presidio_catches_pii_types_beyond_original_scope():
    """Giá trị thật của việc chuyển sang Presidio (quyết định 2026-08-10, lý
    do: dữ liệu khách hàng tương lai có thể có nhiều loại PII khác ngoài SĐT/
    CCCD/tên) — verify bằng 1 loại KHÔNG hề nằm trong bộ regex tự viết trước
    đó: địa chỉ ví crypto (CryptoRecognizer có sẵn trong catalog Presidio)."""
    text = "Ví bitcoin của tôi là 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 bị mất tiền."
    out = scrub_pii(text, purpose="log")
    assert "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" not in out


def test_scrub_pii_falls_back_to_regex_when_presidio_unavailable(monkeypatch):
    """Graceful-degrade — thiếu presidio-analyzer/model NER KHÔNG được crash
    app, phải rơi về lớp regex tối thiểu. Mô phỏng bằng monkeypatch thay vì
    gỡ cài đặt thật (nhanh, không ảnh hưởng môi trường test khác)."""
    import src.observability.pii as pii_module

    monkeypatch.setattr(pii_module, "_load_analyzer_log", lambda: None)
    text = "SĐT của tôi là 0901234567, email a@b.com."
    out = pii_module.scrub_pii(text, purpose="log")
    assert "0901234567" not in out
    assert "a@b.com" not in out
