"""Giai đoạn 3 (observability checklist) — verify PII scrubbing THẬT (engine
Presidio, xem src/observability/pii.py), không suy luận từ đọc code. Bài test
bắt buộc theo đúng checklist: chạy CHỈ regex trên câu có tên người → xác nhận
tên LỌT; chạy pipeline đầy đủ (Presidio) → xác nhận bắt được — đồng thời ghi
nhận trung thực giới hạn thật của model NER đa ngôn ngữ nhỏ bên trong
Presidio (bỏ sót 1 số tên, gán nhãn loại không đáng tin). Test check TÊN ĐÃ
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
    out = scrub_pii(text)
    assert "Trần Thị Bích" not in out
    assert out != text, "Phải có ít nhất 1 chỗ bị che (nhãn cụ thể không quan trọng, xem docstring)"


def test_hybrid_still_catches_structured_pii_too():
    text = "Anh Phạm Minh Tuấn, SĐT 0901234567, CCCD 001234567890 vừa gọi."
    out = scrub_pii(text)
    assert "Phạm Minh Tuấn" not in out
    assert "0901234567" not in out
    assert "001234567890" not in out


def test_hybrid_known_gap_documented_not_silently_claimed_fixed():
    """Giới hạn THẬT của model NER đa ngôn ngữ nhỏ — ghi nhận trung thực
    thay vì báo cáo hybrid bắt được 100% tên tiếng Việt. Case này model
    KHÔNG nhận diện được span thực thể nào — nếu spaCy sau này cập nhật và
    bắt được case này, test sẽ tự fail và cần cập nhật lại docstring/ghi
    chú giới hạn ở src/observability/pii.py cho khớp thực tế mới."""
    text = "Anh Lê Hoàng Nam vừa gọi điện phàn nàn về phí giao dịch."
    out = scrub_pii(text)
    assert "Lê Hoàng Nam" in out, (
        "Nếu assertion này fail nghĩa là NER đã bắt được case trước đây bị bỏ sót — "
        "cập nhật lại ghi chú giới hạn trong src/observability/pii.py, đừng chỉ xoá test."
    )


def test_presidio_catches_pii_types_beyond_original_scope():
    """Giá trị thật của việc chuyển sang Presidio (quyết định 2026-08-10, lý
    do: dữ liệu khách hàng tương lai có thể có nhiều loại PII khác ngoài SĐT/
    CCCD/tên) — verify bằng 1 loại KHÔNG hề nằm trong bộ regex tự viết trước
    đó: địa chỉ ví crypto (CryptoRecognizer có sẵn trong catalog Presidio)."""
    text = "Ví bitcoin của tôi là 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 bị mất tiền."
    out = scrub_pii(text)
    assert "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" not in out


def test_scrub_pii_falls_back_to_regex_when_presidio_unavailable(monkeypatch):
    """Graceful-degrade — thiếu presidio-analyzer/model NER KHÔNG được crash
    app, phải rơi về lớp regex tối thiểu. Mô phỏng bằng monkeypatch thay vì
    gỡ cài đặt thật (nhanh, không ảnh hưởng môi trường test khác)."""
    import src.observability.pii as pii_module

    monkeypatch.setattr(pii_module, "_load_analyzer", lambda: None)
    text = "SĐT của tôi là 0901234567, email a@b.com."
    out = pii_module.scrub_pii(text)
    assert "0901234567" not in out
    assert "a@b.com" not in out
