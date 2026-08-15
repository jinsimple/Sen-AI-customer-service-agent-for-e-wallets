"""Bẫy G — nhánh fallback KHÔNG được để origin-rule chặn mất câu trả lời.

═══ VÌ SAO TEST NÀY GỌI ĐƯỜNG THẬT, KHÔNG GỌI `loc_dau_ra(nguon=None)`

Ban đầu tôi đưa ca này vào corpus đơn vị dưới dạng một lời gọi
`loc_dau_ra(reply, nguon=None)` và kỳ vọng "không chấm được". PO chặn đúng: đó
là kiểm **một lời gọi tổng hợp không tồn tại trên đường chạy thật**. Coder khai
rằng nhánh fallback KHÔNG hề gọi bộ lọc; nếu đúng thì lời gọi kia đo một tình
huống không bao giờ xảy ra, và nó sẽ xanh (hoặc đỏ) vì lý do chẳng liên quan gì
tới an toàn của sản phẩm.

**Và không được tin lời khai đó.** Cách kiểm đúng là chạy `run_agent_turn` cho
nổ đúng nhánh fallback rồi đọc **envelope thật** nó trả ra.

═══ ĐIỀU ĐANG CANH

Trên nhánh fallback:
    `tool_calls`   = None  -> KHÔNG khôi phục được (khác `[]` = không gọi tool nào)
    `loc_dau_ra`   = []    -> bộ lọc KHÔNG chạy, nên không nhóm nào khớp

Nếu một ngày ai đó nối bộ lọc vào cả nhánh fallback mà quên rằng `tool_calls`
ở đó là None, origin-rule sẽ đọc None thành "nguồn rỗng" và **chặn mọi số trong
mọi câu fallback** — kể cả mã ticket mà khách cần để theo dõi khiếu nại. Đó
đúng là hình dạng bug 27/96, lần thứ ba trong cùng một ngày:

    lần 1  O3 nuốt mã giao dịch trong câu tra cứu
    lần 2  O4 nuốt câu từ chối cam kết mà ràng buộc 1 bắt agent phải nói
    lần 3  (ca này) origin-rule nuốt mã ticket trong câu bàn giao

Ba lần cùng một họ: **một bộ lọc an toàn xoá mất đúng thứ khách cần nhất.**
"""
from __future__ import annotations

import pytest

pytest.importorskip("langgraph", reason="cần langgraph để giả lập nhánh fallback")

from langgraph.errors import GraphRecursionError  # noqa: E402


class _AgentNoTungRecursion:
    """Agent giả luôn ném GraphRecursionError — ép đúng nhánh fallback."""

    class _State:
        values: dict = {}

    def get_state(self, config):
        return self._State()

    def invoke(self, *a, **kw):
        raise GraphRecursionError("giả lập vòng lặp tool — ép vào nhánh fallback")


@pytest.fixture()
def envelope_fallback(sample_db, monkeypatch):
    import src.agents.graph as graph_module

    def _fake_build_agent(session, *, user_id, customer_name, otp_verified_at, guard=None):
        return _AgentNoTungRecursion()

    monkeypatch.setattr(graph_module, "_build_agent", _fake_build_agent)
    return graph_module.run_agent_turn(
        sample_db, user_id="USR-A", message="tôi bị trừ tiền hai lần mà không nhớ mã giao dịch"
    )


def test_fallback_khong_bi_bo_loc_chan(envelope_fallback):
    """`loc_dau_ra` phải là `[]` — bộ lọc KHÔNG chạy trên nhánh này.

    `[]` ở đây nghĩa là "không nhóm nào khớp vì bộ lọc không được gọi", và đó
    là thiết kế đúng: nhánh fallback không có `result["messages"]` để lần ra
    nguồn, nên mọi phán quyết xuất xứ ở đây đều là đoán mò.
    """
    assert envelope_fallback.get("loc_dau_ra") == [], (
        f"Nhánh fallback trả loc_dau_ra={envelope_fallback.get('loc_dau_ra')!r} — bộ lọc "
        "ĐANG chạy trên nhánh không có nguồn để đối chiếu. Kiểm ngay xem origin-rule "
        "có đọc tool_calls=None thành 'nguồn rỗng' rồi chặn sạch số hay không."
    )


def test_fallback_van_giu_duoc_ma_ticket_cho_khach(envelope_fallback):
    """Vế NGƯỜI DÙNG của cùng một chuyện — và là vế dễ quên nhất.

    Test trên nói "bộ lọc không chạy". Test này nói vì sao điều đó quan trọng:
    câu fallback tồn tại để **giao lại cho người thật**, và thứ duy nhất làm nó
    có ích là **mã ticket khách cầm đi theo dõi**. Một câu bàn giao không có mã
    là một ngõ cụt lịch sự.

    Không gộp vào test trên: `loc_dau_ra == []` vẫn đúng trong khi mã ticket đã
    biến mất vì một lý do khác (fallback không tạo ticket, hoặc mã bị scrub).
    Hai thứ hỏng độc lập thì phải đỏ độc lập.
    """
    assert envelope_fallback.get("ticket_id"), (
        "Nhánh fallback không tạo ticket — câu bàn giao thành ngõ cụt, khách "
        "không có gì để theo dõi khiếu nại."
    )
    assert str(envelope_fallback["ticket_id"]) in envelope_fallback.get("reply", ""), (
        f"Mã ticket {envelope_fallback['ticket_id']!r} KHÔNG xuất hiện trong câu trả lời:\n"
        f"  {envelope_fallback.get('reply', '')!r}\n"
        "Khách được bảo 'sẽ chuyển cho chuyên viên' mà không cầm được mã nào."
    )


def test_tool_calls_la_none_chu_khong_phai_rong(envelope_fallback):
    """Ba trạng thái, không phải hai — và đây là chỗ đã tốn của đội một vòng.

        []    -> quan sát thật: agent không gọi tool nào
        [...] -> quan sát thật: đây là danh sách
        None  -> KHÔNG khôi phục được (chỉ nhánh fallback)

    Đo được 15/08: 4/5 bản ghi có `tool_calls` rỗng KHÔNG hề đi qua fallback,
    nên `[]` không suy ngược ra fallback. Giữ `None` tách khỏi `[]` là điều
    kiện để mọi bộ chấm downstream phân biệt được "không có" với "không biết".
    """
    assert envelope_fallback.get("tool_calls", "THIEU") is None, (
        f"tool_calls={envelope_fallback.get('tool_calls', 'THIEU')!r} trên nhánh fallback. "
        "Phải là None ('không khôi phục được'), không phải [] ('không gọi tool nào') "
        "và cũng không được thiếu khoá."
    )
