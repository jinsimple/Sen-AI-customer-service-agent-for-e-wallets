"""GĐ3 — cổng xoay 0-token, phần vòng lặp xoay thật (`run_agent_turn` +
`_chay_luot_voi_xoay`, `src/agents/graph.py`). Viết TỪ HỢP ĐỒNG Coder khai
qua tin nhắn 19/08 (chữ ký `_chay_luot_voi_xoay`, cách giả lập lỗi quota,
2 trường mới `model`/`models_da_thu` trong dict trả về của `run_agent_turn`)
— KHÔNG đọc `src/`.

🔴 ĐỎ CÓ LÝ DO — "bộ phận đang được nối" (Coder: "Đang implement phần này
ngay"), KHÔNG phải "rào mạng" (AUTH-008) và KHÔNG phải "chưa tồn tại"
(llm_pool.py lúc `34a6363`, nay đã xanh). CHƯA CHẠY file này — chỉ
syntax-check. Chờ Coder báo xong.

Seam tái dùng (đã có tiền lệ, KHÔNG tự chế):
    `_build_agent` giờ nhận thêm kwarg `model` — patch theo `model` được
    truyền vào để phân biệt lần gọi (chữ ký Coder xác nhận: lỗi ở model
    ĐẦU, trả lời ở model THỨ HAI — patch dựa trên GIÁ TRỊ `model` kwarg,
    không dựa trên SỐ LẦN gọi, để không lệ thuộc thứ tự gọi thật).
    Agent "trả lời bình thường": `.get_state()` → object có `.values={}`,
    `.invoke()` → `{"messages": []}` — hình dạng tối thiểu ĐÃ CÓ tiền lệ
    chạy được thật ở `tests/test_api/test_agent_chat_limits.py::_RecursionLimitCapturingAgent`
    (KHÔNG phải tôi tự đoán — đây là seam duy nhất trong `tests/` từng
    chứng minh `run_agent_turn` không crash trên invoke() thành công giả).
    Agent "lỗi quota": `.invoke()` raise `openai.PermissionDeniedError`
    (status 403) với message chứa "quota" — theo đúng ví dụ Coder cho.
"""
from __future__ import annotations

import httpx
import openai
import pytest


def _http_request() -> httpx.Request:
    return httpx.Request("POST", "https://api.deepseek.com/v1/chat/completions")


def _loi_quota(message: str = "insufficient_quota: request exceeds current quota") -> openai.PermissionDeniedError:
    resp = httpx.Response(403, request=_http_request(), json={"error": {"message": message}})
    return openai.PermissionDeniedError(message, response=resp, body=None)


def _loi_quota_chuoi_la_nhung_status_code_403(message: str = "Lỗi không xác định XYZ-123") -> openai.PermissionDeniedError:
    """Cùng status_code=403 nhưng CHUỖI KHÔNG khớp bất kỳ từ khoá quota quen
    thuộc nào — ca "status_code ưu tiên" cần đúng hình dạng này."""
    resp = httpx.Response(403, request=_http_request(), json={"error": {"message": message}})
    return openai.PermissionDeniedError(message, response=resp, body=None)


def _loi_khong_phai_quota() -> openai.APIConnectionError:
    """APIError nhưng KHÔNG phải quota — 'timeout/lỗi mạng' thường, không
    status_code 403, message không chứa từ khoá quota nào. Đây là exception
    ĐÃ CÓ TIỀN LỆ trong test_gd2_tool_calls_khong_null.py (:906)."""
    return openai.APIConnectionError(message="Connection error.", request=_http_request())


class _AgentNemLoi:
    class _State:
        values: dict = {}

    def __init__(self, loi: Exception):
        self._loi = loi

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        raise self._loi


class _AgentTraLoiBinhThuong:
    """Hình dạng invoke() thành công tối thiểu — tiền lệ
    `_RecursionLimitCapturingAgent` (test_agent_chat_limits.py)."""

    class _State:
        values: dict = {}

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        return {"messages": []}


def _fake_build_agent(*, loi_theo_model: dict[str, Exception]):
    """`_build_agent(session, *, user_id, customer_name, otp_verified_at,
    guard=None, model=...)` — patch dựa trên GIÁ TRỊ `model` kwarg nhận
    được, không dựa trên thứ tự gọi."""

    def _ham(session, *, user_id, customer_name, otp_verified_at, guard=None, model=None):
        if model in loi_theo_model:
            return _AgentNemLoi(loi_theo_model[model])
        return _AgentTraLoiBinhThuong()

    return _ham


CAU = "tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"
MODEL_A = "model-a"
MODEL_B = "model-b"
MODEL_C = "model-c"


@pytest.fixture(autouse=True)
def _be_gia_lap(monkeypatch):
    from src.agents import llm_pool

    monkeypatch.setattr(llm_pool, "LLM_MODEL_POOL", [MODEL_A, MODEL_B, MODEL_C])
    yield


def test_xoay_dung_thu_tu_uu_tien_khi_gap_loi_quota(sample_db, monkeypatch):
    """A lỗi quota, B trả lời bình thường ⟹ model đã trả lời = B (không phải
    A — cũng không phải hằng LLM_MODEL cấu hình, đúng ca Lead thêm), và
    models_da_thu ghi ĐÚNG THỨ TỰ đã thử: [A, B]."""
    import src.agents.graph as graph_module

    monkeypatch.setattr(
        graph_module, "_build_agent",
        _fake_build_agent(loi_theo_model={MODEL_A: _loi_quota()}),
    )
    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU)

    assert ket_qua.get("model") == MODEL_B, (
        f"model đã trả lời phải là {MODEL_B!r} (model B thật sự invoke thành công), "
        f"đo được {ket_qua.get('model')!r}"
    )
    assert ket_qua.get("models_da_thu") == [MODEL_A, MODEL_B], (
        f"models_da_thu phải liệt kê ĐÚNG THỨ TỰ đã thử kể cả lần hỏng, "
        f"đo được {ket_qua.get('models_da_thu')!r}"
    )


def test_khong_xoay_tren_loi_khong_phai_quota(sample_db, monkeypatch):
    """Lỗi APIError KHÔNG phải quota (timeout/connection) ⟹ KHÔNG được xoay
    — đi đường cũ y hệt trước GĐ3 (đã canh ở test_gd2_tool_calls_khong_null.py,
    ca này canh thêm góc 'không bị xoay vòng xử lý').

    Đối chứng NGẦM quan trọng: nếu bản vá lỡ coi MỌI APIError là tín hiệu
    quota (quá rộng), ca này sẽ đỏ vì model bị xoay sang B dù lẽ ra phải giữ
    nguyên đường lỗi cũ — đây chính là Luật 2 (đừng vá quá rộng) áp cho xoay."""
    import src.agents.graph as graph_module

    monkeypatch.setattr(
        graph_module, "_build_agent",
        _fake_build_agent(loi_theo_model={MODEL_A: _loi_khong_phai_quota()}),
    )
    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU)

    # Đường lỗi-không-phải-quota đã có tiền lệ trả tool_calls là MẢNG (GĐ2).
    # Nếu bị coi nhầm là tín hiệu quota, models_da_thu sẽ có 2 phần tử thay
    # vì đường lỗi cũ (không xoay) không tạo trường này hoặc chỉ có 1.
    models_da_thu = ket_qua.get("models_da_thu")
    assert models_da_thu is None or models_da_thu == [MODEL_A], (
        f"lỗi không-phải-quota KHÔNG được kích hoạt xoay, đo được models_da_thu={models_da_thu!r}"
    )


def test_status_code_uu_tien_hon_khop_chuoi(sample_db, monkeypatch):
    """Exception status_code=403 nhưng CHUỖI không khớp từ khoá quota quen
    thuộc nào ⟹ vẫn phải được coi là tín hiệu quota (ưu tiên status_code khi
    nhà cung cấp CÓ trả, theo ràng buộc PO 19/08) ⟹ vẫn xoay sang B."""
    import src.agents.graph as graph_module

    monkeypatch.setattr(
        graph_module, "_build_agent",
        _fake_build_agent(loi_theo_model={MODEL_A: _loi_quota_chuoi_la_nhung_status_code_403()}),
    )
    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU)

    assert ket_qua.get("model") == MODEL_B, (
        "status_code=403 phải được coi là tín hiệu quota DÙ chuỗi lỗi lạ — "
        f"đo được model={ket_qua.get('model')!r}, models_da_thu={ket_qua.get('models_da_thu')!r}"
    )
    assert ket_qua.get("models_da_thu") == [MODEL_A, MODEL_B]


def test_khong_xoay_thi_models_da_thu_dung_mot_phan_tu(sample_db, monkeypatch):
    """Ca ĐỐI CHỨNG (Luật A) — lượt không xoay (model đầu trả lời ngay)
    ⟹ models_da_thu đúng 1 phần tử = model đó, model == phần tử đó. Thiếu
    ca này thì 2 ca "xoay" ở trên có thể xanh dù models_da_thu LUÔN có 2
    phần tử bất kể có lỗi hay không (bug ngược — xoay giả vờ)."""
    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent(loi_theo_model={}))
    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU)

    assert ket_qua.get("model") == MODEL_A
    assert ket_qua.get("models_da_thu") == [MODEL_A], (
        f"lượt không xoay phải có models_da_thu đúng 1 phần tử, đo được {ket_qua.get('models_da_thu')!r}"
    )


def test_be_can_toan_phan_moi_model_deu_loi_quota(sample_db, monkeypatch):
    """CẢ BA model đều lỗi quota ⟹ bể cạn toàn phần. Theo Coder: rơi vào
    `_BeCanToanPhanError`, `run_agent_turn` bắt riêng, KHÔNG để lộ ra ngoài
    (không crash 500) — cùng dạng "cần can thiệp" đã có tiền lệ ở đường
    vòng-lặp-tool/timeout (GĐ2: tool_calls=None, KHÔNG phải mảng rỗng).

    Không giả định nội dung thông điệp cụ thể (tránh bẫy F-31/F-32 dò chuỗi,
    xem eval/KE-HOACH-DO-DOI-MODEL.md §1.4) — chỉ canh HAI điều có hợp đồng
    rõ: models_da_thu phủ ĐỦ cả bể, và không crash (có trả về, không raise
    ra ngoài run_agent_turn)."""
    import src.agents.graph as graph_module

    monkeypatch.setattr(
        graph_module, "_build_agent",
        _fake_build_agent(loi_theo_model={
            MODEL_A: _loi_quota(), MODEL_B: _loi_quota(), MODEL_C: _loi_quota(),
        }),
    )
    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU)

    assert set(ket_qua.get("models_da_thu") or []) == {MODEL_A, MODEL_B, MODEL_C}, (
        f"bể cạn toàn phần phải để lại dấu vết ĐÃ THỬ CẢ BA model trong "
        f"models_da_thu, đo được {ket_qua.get('models_da_thu')!r}"
    )
    assert ket_qua.get("model") is None, (
        f"không model nào trả lời thành công ⟹ model phải là None, đo được {ket_qua.get('model')!r}"
    )
