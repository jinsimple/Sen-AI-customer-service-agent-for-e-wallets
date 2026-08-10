"""Case QA (FIN05_QA_TestCases.jsonl) không áp dụng cho phạm vi sản phẩm hiện
tại — giữ lại bằng `pytest.mark.skip` (không xoá hẳn) để còn dấu vết nếu sau
này sản phẩm bổ sung tính năng liên quan, đúng quyết định đã chốt khi thích
ứng bộ test (docs/TESTING.md)."""
import pytest


@pytest.mark.skip(
    reason=(
        "COMP-002: ngưỡng xác thực sinh trắc học (QĐ 2345/QĐ-NHNN, 10tr/lần-"
        "20tr/ngày) không khớp bất kỳ cơ chế nào đang có trong sản phẩm — "
        "FS-06/FS-08 (src/tools/fraud_policy.py, scripts/fraud_engine.py) dùng "
        "tham số hoàn toàn khác (drain_ratio, daily_outbound_min), sản phẩm "
        "không có xác thực sinh trắc học. Bỏ qua có chủ đích, không phải bug."
    )
)
def test_comp_002_biometric_threshold_not_applicable():
    pass
