"""GĐ2 — cổng envelope `tool_calls`: KHÔNG BAO GIỜ `null` vượt qua BIÊN
(`POST /agent/chat`), dù tầng TRONG (`run_agent_turn`) có một ngoại lệ CÓ
CHỦ ĐÍCH. Viết TỪ ĐẶC TẢ Lead khai 19/08, không đọc thân hàm `src/`.

Nguồn đặc tả (đúng một, không tự thêm):
  · docs/giao-viec/2026-08-19-gd2-envelope-null-va-e2e-ui.md
  · Quyết định hoà giải của Lead 19/08 (chuyển qua tin nhắn, không có file
    riêng — ghi lại nguyên văn ở đây vì đây là NGUỒN SỰ THẬT cho file này):

        TẦNG TRONG (`run_agent_turn` gọi trực tiếp):
          nhẹ · 2 fallback nhà-cung-cấp · nặng  → tool_calls là MẢNG
          vòng-lặp-tool/timeout (GraphRecursionError/FutureTimeoutError)
                                                 → tool_calls là None
                                                   (NGOẠI LỆ CÓ CHỦ ĐÍCH —
                                                   test_fallback_khong_goi_bo_loc.py
                                                   ::test_tool_calls_la_none_chu_khong_phai_rong
                                                   ĐÃ canh ca này, KHÔNG đụng)
        TẦNG BIÊN (`POST /agent/chat`, đọc RAW JSON qua HTTP):
          MỌI đường, KHÔNG NGOẠI LỆ → tool_calls là MẢNG. `null` không bao
          giờ được vượt biên — chuẩn hoá ngay trước return ở route
          (main.py:609), KHÔNG sửa lại :999.

Vì sao HAI TẦNG không mâu thuẫn nhau: `None` mang thông tin thật ("không
khôi phục được", khác `[]` = "quan sát thật: không gọi tool nào") — có giá
trị cho log/checkpoint/người đọc sự cố. Nhưng client KHÔNG làm gì khác được
với "không biết", và JSON `null` gặp `.length` là TypeError — đây chính là
sự cố PO thật vấp. Giữ ý nghĩa ở TRONG, khoá kiểu ở BIÊN.

🔴 RÀNG BUỘC PO-agent (nhắc lại nguyên văn, ÁP CHO CHÍNH CỔNG NÀY): "đọc RAW
JSON và assert tool_calls LÀ MẢNG THEO KIỂU; cấm mọi `or []` / `.get(x, [])`
trong chính cổng — dụng cụ đo không được mang đúng cái lỗi nó đi tìm."
⟹ Mọi assertion trong file này dùng `isinstance(x, list)` sau khi đọc
`raw["tool_calls"]` trực tiếp (KeyError nếu thiếu khoá — không `.get()`),
KHÔNG BAO GIỜ so bằng độ dài hay coalesce trước khi kiểm tra kiểu.

Đường "nặng" hạnh phúc (:1230) KHÔNG được Coder chạm (đã đúng từ trước) và
đòi một agent giả trả về trạng thái thành công đầy đủ — seam đó CHƯA CÓ tiền
lệ trong tests/ (khác GraphRecursionError đã có sẵn ở
test_fallback_khong_goi_bo_loc.py). KHÔNG đoán hình dạng state cần thiết —
để SKIP kèm lý do; đường nặng được phủ bởi 3 case E2E "câu giao dịch đường
nặng" tốn token ở tầng ② (Lead: "3 case E2E đường nặng chính là smoke cho
ảnh mới"), không phải trách nhiệm của cổng 0-token này.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Tầng BIÊN — client chung, cùng khuôn tests/test_api/test_authz_matrix.py
# ---------------------------------------------------------------------------
@pytest.fixture()
def client(sample_db, monkeypatch):
    from src.api.deps import get_session
    from src.api.main import app

    def _override_session():
        try:
            yield sample_db
            sample_db.commit()
        except Exception:
            sample_db.rollback()
            raise

    app.dependency_overrides[get_session] = _override_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def customer_headers():
    from src.auth import create_access_token

    token = create_access_token(user_id="USR-A", role="customer")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tầng TRONG — gọi thẳng run_agent_turn, cùng khuôn
# tests/test_security/test_fallback_khong_goi_bo_loc.py
# ---------------------------------------------------------------------------
CAU_DON = "alo"  # đúng hằng số T1 dùng làm câu đường nhẹ chuẩn (0 token),
                 # đã có tiền lệ ở tests/test_bat_bien_dinh_tuyen_duong_nhe.py


def test_trong_duong_nhe_tool_calls_la_mang(sample_db):
    import src.agents.graph as graph_module

    ket_qua = graph_module.run_agent_turn(sample_db, user_id="USR-A", message=CAU_DON)
    assert isinstance(ket_qua["tool_calls"], list), (
        f"Đường nhẹ (T1, câu {CAU_DON!r}) trả tool_calls={ket_qua.get('tool_calls')!r} "
        "— không phải MẢNG. Đây đúng dòng :639 Coder đang vá."
    )


class _AgentNoTungRecursion:
    """Cùng fake agent với test_fallback_khong_goi_bo_loc.py — tái dùng
    đúng seam đã có tiền lệ, không tự chế seam mới."""

    class _State:
        values: dict = {}

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        from langgraph.errors import GraphRecursionError

        raise GraphRecursionError("giả lập vòng lặp tool — ép vào nhánh :999")


def test_trong_vong_lap_tool_van_giu_none_co_chu_dich(sample_db, monkeypatch):
    """NGOẠI LỆ CÓ CHỦ ĐÍCH — đối chứng ÂM cho cổng này, KHÔNG phải test
    trùng lặp với test_fallback_khong_goi_bo_loc.py.

    Lý do cần ca này Ở ĐÂY: nếu cổng envelope chỉ toàn ca "phải là mảng", nó
    sẽ không phân biệt được "đã hiểu ngoại lệ có chủ đích" với "quên mất
    :999 tồn tại". Một cổng chỉ có ca dương thì một bản vá quá tay (đổi luôn
    :999 sang mảng, xoá mất phân biệt None/[]) sẽ ĐI QUA cổng này mà không
    ai biết — đúng Luật A vế im lúc bình thường, còn vế KÊU nằm ở
    test_tool_calls_la_none_chu_khong_phai_rong (file kia), file này chỉ
    xác nhận lại từ góc nhìn "hợp đồng envelope tổng" không vô tình nuốt nó.
    """
    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "_build_agent", lambda *a, **kw: _AgentNoTungRecursion())
    ket_qua = graph_module.run_agent_turn(
        sample_db, user_id="USR-A", message="tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"
    )
    assert ket_qua.get("tool_calls") is None, (
        f"Tầng TRONG đường vòng-lặp-tool/timeout trả tool_calls="
        f"{ket_qua.get('tool_calls')!r} — PHẢI là None (ngoại lệ có chủ đích). "
        "Nếu ca này đỏ vì tool_calls giờ là [], nghĩa là :999 đã bị đổi sang "
        "mảng — SAI quyết định Lead 19/08, đi hỏi lại trước khi đổi cổng này."
    )


# ---------------------------------------------------------------------------
# Hai đường fallback NHÀ CUNG CẤP (:789 RateLimitError · :906 APIError khác
# RateLimitError). [ĐO] Lead 19/08, đọc src/agents/graph.py:24-30/733/819:
#     RateLimitError (con) PHẢI bắt TRƯỚC APIError (cha) — đảo thứ tự thì
#     :789 không bao giờ chạy, và lỗi đó KHÔNG CÓ TRIỆU CHỨNG (cả hai đường
#     đều trả [] + HTTP 200). Ca `test_trong_ratelimiterror_di_dung_duong_789`
#     dưới đây CHÍNH LÀ cổng canh việc đó — không phải test thừa.
# ---------------------------------------------------------------------------
def _httpx_request():
    import httpx

    return httpx.Request("POST", "https://api.openai.com/v1/chat/completions")


def _rate_limit_error():
    import httpx
    import openai

    req = _httpx_request()
    resp = httpx.Response(429, request=req, json={"error": {"message": "rate limited"}})
    return openai.RateLimitError("rate limited", response=resp, body=None)


def _api_connection_error():
    """APIError KHÔNG PHẢI RateLimitError — [ĐO] MRO xác nhận
    APIConnectionError không kế thừa RateLimitError, đúng ca ⑨06 cần."""
    import openai

    return openai.APIConnectionError(message="Connection error.", request=_httpx_request())


class _AgentNemLoi:
    class _State:
        values: dict = {}

    def __init__(self, loi: Exception):
        self._loi = loi

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        raise self._loi


@pytest.mark.parametrize(
    "dung_loi,ten_ca",
    [
        pytest.param(_rate_limit_error, "ratelimiterror_789", id="rate_limit_error_duong_789"),
        pytest.param(_api_connection_error, "apiconnectionerror_906", id="api_connection_error_duong_906"),
    ],
)
def test_trong_fallback_nha_cung_cap_tool_calls_la_mang(sample_db, monkeypatch, dung_loi, ten_ca):
    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "_build_agent", lambda *a, **kw: _AgentNemLoi(dung_loi()))
    ket_qua = graph_module.run_agent_turn(
        sample_db, user_id="USR-A", message="tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"
    )
    assert isinstance(ket_qua.get("tool_calls"), list), (
        f"[{ten_ca}] tầng TRONG đường fallback nhà cung cấp trả tool_calls="
        f"{ket_qua.get('tool_calls')!r} — không phải MẢNG. Đúng dòng Coder đang vá."
    )


def test_trong_ratelimiterror_di_dung_duong_789_khong_lot_vao_906():
    """Ca canh THỨ TỰ except — lỗi không triệu chứng nếu sai (Lead 19/08).

    RateLimitError là CON của APIError. Nếu ai đảo thứ tự hai khối `except`
    (APIError lên trước RateLimitError), khối APIError sẽ NUỐT luôn
    RateLimitError vì Python khớp except theo isinstance — và envelope vẫn
    trả [] + HTTP 200 ở CẢ HAI đường, nên KHÔNG CÓ TRIỆU CHỨNG nào lộ ra
    ngoài chính đoạn code nào chạy. Cổng phải-là-mảng ở trên KHÔNG bắt được
    lỗi này (cả hai đường đều đúng kiểu). Ca này bắt bằng cách khác: kiểm
    tra QUAN HỆ KẾ THỪA giữa hai exception, không phụ thuộc code chạy đường
    nào — nếu quan hệ ấy đổi (vd SDK đổi MRO ở bản nâng cấp), ca này đỏ TRƯỚC
    khi ai kịp đảo except dựa trên giả định sai.
    """
    import openai

    assert issubclass(openai.RateLimitError, openai.APIError), (
        "openai.RateLimitError không còn là con của openai.APIError — "
        "giả định thứ tự except (:733 trước :819) không còn đúng, cần "
        "Coder rà lại graph.py trước khi tin ca fallback ở trên."
    )
    assert not issubclass(openai.APIConnectionError, openai.RateLimitError), (
        "openai.APIConnectionError giờ LÀ RateLimitError — ca :906 ở trên "
        "đang không đo đúng nhánh nó tưởng đang đo."
    )


@pytest.mark.skip(
    reason=(
        "Đường nặng (:1230, KHÔNG bị Coder chạm) đòi seam agent-giả-trả-về-"
        "trạng-thái-THÀNH-CÔNG — chưa có tiền lệ trong tests/ (khác "
        "GraphRecursionError đã có sẵn). Không đoán hình dạng state cần "
        "thiết mà không đọc src/. Đường này được phủ bởi 3 case E2E 'câu "
        "giao dịch đường nặng' tốn token (phần ②) — smoke thật cho ảnh mới, "
        "đúng phân công Lead 19/08. KHÔNG ĐO ĐƯỢC ở đây, không phải bỏ sót."
    )
)
def test_trong_duong_nang_tool_calls_la_mang():
    pass


# ---------------------------------------------------------------------------
# Tầng BIÊN — đúng con bug PO thật vấp: null KHÔNG được vượt qua route,
# BẤT KỂ tầng trong trả gì.
# ---------------------------------------------------------------------------
def test_bien_duong_nhe_tool_calls_la_mang(client, customer_headers):
    resp = client.post("/agent/chat", json={"message": CAU_DON}, headers=customer_headers)
    assert resp.status_code == 200, f"Đường nhẹ trả {resp.status_code}, không phải 200: {resp.text[:300]}"
    raw = resp.json()
    assert isinstance(raw["tool_calls"], list), (
        f"[RAW JSON] tool_calls={raw['tool_calls']!r} qua route /agent/chat cho câu "
        f"{CAU_DON!r} — không phải MẢNG. Đúng ca PO thật gõ 'chào bạn' và UI vỡ."
    )


def test_bien_vong_lap_tool_khong_de_null_vuot_bien(client, customer_headers, monkeypatch):
    """Ca QUAN TRỌNG NHẤT file này — chứng minh chuẩn hoá ở BIÊN (main.py:609)
    THẬT SỰ chặn được đúng đường mà tầng TRONG cố ý để None.

    Không có ca này thì tầng TRONG (test ở trên: tool_calls=None đúng ý) và
    tầng BIÊN (route trả mảng) là HAI PHÁT BIỂU RỜI NHAU — không có gì buộc
    chúng phải khớp nhau qua đúng MỘT nhánh mã. Ca này ép nhánh :999 CHẠY
    QUA ĐÚNG ROUTE THẬT, không phải gọi run_agent_turn trực tiếp rồi suy diễn
    route cũng vậy.
    """
    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "_build_agent", lambda *a, **kw: _AgentNoTungRecursion())
    resp = client.post(
        "/agent/chat",
        json={"message": "tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"},
        headers=customer_headers,
    )
    assert resp.status_code == 200, f"Đường vòng-lặp-tool trả {resp.status_code}: {resp.text[:300]}"
    raw = resp.json()
    assert isinstance(raw["tool_calls"], list), (
        f"[RAW JSON] tool_calls={raw['tool_calls']!r} qua route /agent/chat trên "
        "đường vòng-lặp-tool (:999) — VẪN null vượt biên dù tầng TRONG cố ý trả "
        "None. Chuẩn hoá ở main.py:609 CHƯA chặn được đúng đường PO thật vấp — "
        "đây chính là nhánh gây UI vỡ ('Có lỗi khi kết nối trợ lý')."
    )


@pytest.mark.parametrize(
    "dung_loi,ten_ca",
    [
        pytest.param(_rate_limit_error, "ratelimiterror_789", id="rate_limit_error_duong_789"),
        pytest.param(_api_connection_error, "apiconnectionerror_906", id="api_connection_error_duong_906"),
    ],
)
def test_bien_fallback_nha_cung_cap_tool_calls_la_mang(client, customer_headers, monkeypatch, dung_loi, ten_ca):
    import src.agents.graph as graph_module

    monkeypatch.setattr(graph_module, "_build_agent", lambda *a, **kw: _AgentNemLoi(dung_loi()))
    resp = client.post(
        "/agent/chat",
        json={"message": "tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"},
        headers=customer_headers,
    )
    assert resp.status_code == 200, f"[{ten_ca}] trả {resp.status_code}: {resp.text[:300]}"
    raw = resp.json()
    assert isinstance(raw["tool_calls"], list), (
        f"[{ten_ca}][RAW JSON] tool_calls={raw['tool_calls']!r} qua route /agent/chat "
        "— không phải MẢNG."
    )
