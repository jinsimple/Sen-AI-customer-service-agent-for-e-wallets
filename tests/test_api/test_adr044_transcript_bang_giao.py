"""ADR-044 (`docs/DECISIONS.md`, land `427ebe6`, PO thật duyệt trực tiếp) —
CSKH đọc được hội thoại bot↔khách của vé mình xử lý, qua route MỚI
`GET /tickets/{ticket_id}/transcript`.

Bốn ca ①②③ viết TỪ CONTRACT (ADR-044 mục "Quyết định") TRƯỚC KHI Coder code
route + migration — khuôn "cổng nghiệm thu dựng sẵn" (GĐ2.5/GĐ3). Route land
`e1db3af`, xác nhận độc lập 4/4 xanh (host + trong container ảnh `c5a9eef`).

Schema response THẬT, xác nhận với Coder (không còn giả định):
`{"transcript": [{"vai":..., "noi_dung":..., "co_goi_tool": bool}] | null,
"ly_do": str | null, "handoff_at": iso | null, "chi_so_bang_giao": int | null}`.

Ca ④ (thêm 20/08) — hồi quy cho phát hiện Review, viết SAU khi route land,
seam do Coder khai trực tiếp (không đoán)."""
from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from src.agents.tools.customer_tools import build_customer_tools
from src.api.deps import get_session
from src.api.main import app
from src.auth import create_access_token
from src.db.models import Ticket
from src.tools.create_ticket import create_ticket


@pytest.fixture()
def client(sample_db):
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


def _cskh_headers() -> dict[str, str]:
    token = create_access_token(user_id="USR-CSKH", role="cskh")
    return {"Authorization": f"Bearer {token}"}


def _make_ticket(sample_db) -> str:
    r = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="to_bank",
        description_raw="test ADR-044", trans_id="TXN-0002",
    )
    sample_db.commit()
    return r["ticket_id"]


# ── ① GUARD CHÍNH — route KHÔNG BAO GIỜ nhận thread_id từ client ───────────


def test_route_bo_qua_thread_id_client_gui_kem_qua_query(client, sample_db):
    """Không cần biết response schema đầy đủ — chỉ cần chứng minh THAM SỐ
    thread_id do client gửi KHÔNG làm thay đổi kết quả trả về. Đây là phép
    thử seam-agnostic: xanh dù Coder đặt tên field response là gì, vì nó so
    sánh HAI response với nhau, không ghim vào nội dung cụ thể của một bên."""
    ticket_id = _make_ticket(sample_db)
    headers = _cskh_headers()

    r_that = client.get(f"/tickets/{ticket_id}/transcript", headers=headers)
    r_bi_chen = client.get(
        f"/tickets/{ticket_id}/transcript",
        params={"thread_id": "ATTACKER-EVIL-THREAD-KHONG-CO-THAT"},
        headers=headers,
    )

    assert r_that.status_code == 200, (
        f"Route chưa tồn tại hoặc lỗi khác — status {r_that.status_code}, "
        f"KHÔNG kết luận gì về guard từ ca này cho tới khi route trả 200 thật: {r_that.text[:200]}"
    )
    assert r_bi_chen.status_code == r_that.status_code
    assert r_bi_chen.json() == r_that.json(), (
        "Response THAY ĐỔI khi client gửi kèm thread_id lạ trong query — route đang đọc "
        "thread_id từ client thay vì LUÔN suy từ ticket.complaint.thread_id trong DB. "
        "Đây chính là guard ADR-044 mục 3 yêu cầu (\"route không được âm thầm trở thành "
        "'đọc thread_id trần' trá hình dưới lốt 'đọc theo ticket'\")."
    )


def test_route_bo_qua_thread_id_client_gui_kem_qua_header(client, sample_db):
    """Cùng ca trên, vector khác: header tuỳ ý (kiểu client tự chế
    'X-Thread-Id') thay vì query — guard phải chặn CẢ HAI đường, không chỉ
    một đường nhìn thấy trước."""
    ticket_id = _make_ticket(sample_db)
    headers = _cskh_headers()

    r_that = client.get(f"/tickets/{ticket_id}/transcript", headers=headers)
    r_bi_chen = client.get(
        f"/tickets/{ticket_id}/transcript",
        headers={**headers, "X-Thread-Id": "ATTACKER-EVIL-THREAD-QUA-HEADER"},
    )

    assert r_that.status_code == 200, f"status {r_that.status_code}: {r_that.text[:200]}"
    assert r_bi_chen.status_code == r_that.status_code
    assert r_bi_chen.json() == r_that.json(), (
        "Response THAY ĐỔI khi client gửi kèm thread_id lạ qua HEADER — cùng lỗ với ca "
        "query ở trên, vector khác."
    )


# ── ② Vé cũ (không có thread_id) ⟹ transcript null KÈM LÝ DO ───────────────


def test_ve_khong_co_thread_id_tra_transcript_null_kem_ly_do(client, sample_db):
    """`create_ticket` hiện tại (TRƯỚC khi Coder nối thread_id qua 4 tầng
    theo ADR-044 mục 1) không có tham số thread_id nào — mọi ticket tạo qua
    đường THẬT hôm nay tự nhiên rơi đúng vào ca "vé cũ". Không seed giả,
    dùng đúng trạng thái tự nhiên của hệ thống trước migration."""
    ticket_id = _make_ticket(sample_db)
    headers = _cskh_headers()

    r = client.get(f"/tickets/{ticket_id}/transcript", headers=headers)
    assert r.status_code == 200, f"status {r.status_code}: {r.text[:200]}"
    body = r.json()

    assert body.get("transcript") is None, (
        f"Vé không có thread_id (tạo trước migration) phải trả transcript=null — "
        f"TUYỆT ĐỐI KHÔNG được đoán theo mốc thời gian gần nhất (ADR-044 mục 2). "
        f"Đo được: {body.get('transcript')!r}"
    )
    # Không ghim tên trường lý do cụ thể (chưa biết) — chỉ đòi một dấu hiệu
    # RÕ RÀNG khác None/rỗng đâu đó trong response giải thích vì sao null.
    co_ly_do = any(
        isinstance(v, str) and len(v.strip()) > 0
        for k, v in body.items()
        if k != "transcript" and ("ly_do" in k.lower() or "reason" in k.lower())
    )
    assert co_ly_do, (
        f"transcript=null nhưng KHÔNG thấy trường lý do nào (khoá chứa 'ly_do'/'reason') "
        f"trong response — \"không biết\" phải hiện ra CÓ LÝ DO, không phải một null trơ trụi "
        f"mà CSKH không phân biệt được với lỗi hệ thống. Response đầy đủ: {body!r}"
    )


# ── ③ handoff_at ghi ĐÚNG LÚC bàn giao, không phải lúc tạo ticket ──────────


def test_handoff_at_ghi_dung_luc_bang_giao_khong_phai_luc_tao_ticket(sample_db):
    """Test ở tầng SERVICE (`request_human_handoff` tool, gọi `flag_human_handoff`
    bên trong) — không cần route/HTTP, `Ticket.handoff_at` là cột DB mới,
    kiểm trực tiếp qua sample_db. Tách THỜI ĐIỂM tạo ticket khỏi thời điểm
    bàn giao bằng cách gọi hai bước CÁCH NHAU, không đo cùng một dấu thời
    gian cho cả hai (nếu không, ca này không phân biệt được "ghi lúc tạo"
    với "ghi lúc bàn giao" — hai giá trị trùng nhau tình cờ)."""
    luc_tao = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="to_bank",
        description_raw="test ADR-044 handoff_at", trans_id="TXN-0002",
    )
    sample_db.commit()
    ticket_id = luc_tao["ticket_id"]

    ticket_truoc_bang_giao = sample_db.get(Ticket, ticket_id)
    assert getattr(ticket_truoc_bang_giao, "handoff_at", "THIEU_COT") is None, (
        "Ticket vừa tạo (CHƯA bàn giao) đã có handoff_at khác None — cột đang bị set sai thời điểm, "
        "hoặc (nếu attr không tồn tại) migration Ticket.handoff_at chưa land."
    )

    truoc_khi_goi = dt.datetime.utcnow()
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=None)}
    tools["request_human_handoff"].invoke(
        {"reason": "Muốn nói chuyện trực tiếp", "ticket_id": ticket_id}
    )
    sau_khi_goi = dt.datetime.utcnow()

    sample_db.expire_all()  # Luật 19 — đọc lại từ DB, không đọc bộ nhớ cache của session
    ticket_sau_bang_giao = sample_db.get(Ticket, ticket_id)
    assert ticket_sau_bang_giao.handoff_at is not None, "handoff_at vẫn None SAU khi đã gọi request_human_handoff."
    assert truoc_khi_goi <= ticket_sau_bang_giao.handoff_at <= sau_khi_goi, (
        f"handoff_at={ticket_sau_bang_giao.handoff_at} nằm NGOÀI khoảng thời gian thực gọi "
        f"flag_human_handoff ({truoc_khi_goi} .. {sau_khi_goi}) — nghi ghi nhầm mốc (vd mốc tạo "
        f"ticket) thay vì mốc bàn giao thật."
    )


# ── ④ Ca hồi quy — checkpoint kết thúc NGAY SAU ToolMessage bàn giao ───────
#
# Phát hiện Review 20/08: `ToolMessage(name="request_human_handoff")` là
# message CUỐI checkpoint (lượt bị cắt trước khi model sinh câu xác nhận)
# ⟹ vạch phân cách "— khách yêu cầu gặp người thật tại đây —" không bao giờ
# đặt được. Coder tái hiện thật (seed checkpoint), quyết định KHÔNG vá logic
# (vá phải ĐOÁN vị trí vạch — đoán sai còn tệ hơn không có vạch), chỉ khai
# vào docstring `src/agents/graph.py::doc_transcript_bang_giao`, đoạn
# "(b) ĐÃ KHAI 20/08 (Review phát hiện...)". Ca này khoá đúng hành vi ĐÃ
# QUYẾT — nếu sau này ai "tiện tay" vá bằng cách đoán vị trí vạch, ca phải
# ĐỎ, buộc họ đọc lại vì sao đội cố ý không đoán.

from types import SimpleNamespace  # noqa: E402

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402


def test_checkpoint_ket_thuc_ngay_sau_toolmessage_bang_giao_khong_co_vach(client, sample_db, monkeypatch):
    thread_id = "THREAD-HOI-QUY-VACH-PHAN-CACH"
    tao = create_ticket(
        sample_db, user_id="USR-A", complaint_type="wrong_recipient", scope="to_bank",
        description_raw="test hồi quy vạch phân cách", trans_id="TXN-0002",
        thread_id=thread_id,
    )
    ticket_id = tao["ticket_id"]
    ticket = sample_db.get(Ticket, ticket_id)
    ticket.handoff_at = dt.datetime.utcnow()  # mô phỏng ĐÃ bàn giao
    sample_db.commit()

    messages = [
        HumanMessage(content="Toi muon gap nguoi that"),
        AIMessage(content="", tool_calls=[{"name": "request_human_handoff", "args": {}, "id": "call_1"}]),
        ToolMessage(content="{}", name="request_human_handoff", tool_call_id="call_1"),
        # KHÔNG AIMessage nào sau — đúng ca Review: checkpoint kết thúc NGAY SAU tool.
    ]
    fake_tuple = SimpleNamespace(checkpoint={"channel_values": {"messages": messages}})
    monkeypatch.setattr("src.agents.graph._CHECKPOINTER.get_tuple", lambda config: fake_tuple)

    r = client.get(f"/tickets/{ticket_id}/transcript", headers=_cskh_headers())
    assert r.status_code == 200, f"status {r.status_code}: {r.text[:300]}"
    body = r.json()

    assert body.get("chi_so_bang_giao") is None, (
        f"chi_so_bang_giao phải là None khi checkpoint kết thúc ngay sau ToolMessage bàn giao "
        f"(không có AIMessage xác nhận theo sau để đặt vạch) — đúng quyết định CÓ CHỦ ĐÍCH "
        f"không đoán vị trí. Đo được: {body.get('chi_so_bang_giao')!r}"
    )
    transcript = body.get("transcript") or []
    assert transcript, "transcript rỗng — ca này cần ÍT NHẤT có lượt để kiểm co_goi_tool, không chỉ kiểm chi_so_bang_giao."
    assert all(luot.get("co_goi_tool") is False for luot in transcript), (
        f"Vế Review NHẤN MẠNH (không phải chỉ trùng ca chi_so_bang_giao=None đã có): "
        f"KHÔNG lượt nào được đánh dấu co_goi_tool=True dù tool request_human_handoff đã chạy "
        f"THẬT trong checkpoint — CSKH đọc transcript sẽ không thấy dấu hiệu nào tool đã chạy. "
        f"transcript: {transcript!r}"
    )
