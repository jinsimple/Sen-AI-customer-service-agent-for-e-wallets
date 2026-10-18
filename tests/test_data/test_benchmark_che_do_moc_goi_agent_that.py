"""Bug PO-agent đo 19/08: `eval/benchmark.py --che-do moc` từng KHÔNG gọi
`_tra_agent()` — tham số CLI `che_do` tồn tại đúng hình thức ở argparse
nhưng `do_truy_hoi()` không hề đọc nó, luôn dùng `_tra()` (đường
`/api/policy-search` trực tiếp) bất kể `--che-do` là gì. `--che-do moc` ra
CÙNG SỐ với mặc định `lap` — một số đo đường rẻ nhưng mang nhãn "đường agent
thật" nếu không ai phát hiện trước khi dán vào hồ sơ.

Ca ĐỐI CHỨNG DƯƠNG theo đúng yêu cầu PO-agent: khẳng định `_tra_agent` THẬT
SỰ được gọi khi `che_do="moc"` — không chỉ khẳng định output đúng hình dạng.
Nếu sau này ai gỡ lời gọi ra lần nữa (hoặc quên nối `che_do` ở một chỗ khác),
ca này phải ĐỎ ngay, không lặp lại đúng lỗi này lần nữa trong im lặng.

0 token — toàn bộ HTTP call (`_dang_nhap`/`canary_kho`/`_tra`/`_tra_agent`)
đều monkeypatch, không có request thật nào rời máy."""
from __future__ import annotations

from tests._eval_co_mat import doi_hoi_eval

doi_hoi_eval()

from eval import benchmark  # noqa: E402

_CASE_MAU = [
    {
        "id": "CASE-MAU-001",
        "ky_vong": "co_trong_kho",
        "query_co_dau": "hạn mức chuyển tiền một ngày là bao nhiêu",
        "query_khong_dau": "han muc chuyen tien mot ngay la bao nhieu",
        "tu_khoa_dac_trung": ["hạn mức"],
        "tu_khoa_phu": [],
        "nguon": {"tai_lieu": "MoMo_ToS"},
    },
]


def _vo_hieu_hoa_dang_nhap_va_canary(monkeypatch):
    # _dang_nhap/canary_kho gọi HTTP thật lúc do_truy_hoi() khởi động — không
    # liên quan gì tới câu hỏi "che_do có được đọc không", vô hiệu hoá để ca
    # này không phụ thuộc một ngăn xếp đang chạy.
    monkeypatch.setattr(benchmark, "_dang_nhap", lambda httpx: _FakeClient())
    monkeypatch.setattr(benchmark, "canary_kho", lambda c: None)


class _FakeClient:
    def close(self):
        pass


def test_che_do_moc_goi_dung_tra_agent_khong_phai_tra(monkeypatch):
    """Ca chính — đối chứng DƯƠNG bắt buộc theo yêu cầu PO-agent."""
    _vo_hieu_hoa_dang_nhap_va_canary(monkeypatch)

    goi_tra_agent: list[str] = []
    goi_tra: list[str] = []

    def _fake_tra_agent(c, q):
        goi_tra_agent.append(q)
        return (["hạn mức chuyển tiền một ngày là 20 triệu đồng"], True)

    def _fake_tra(c, q, k=None):
        goi_tra.append(q)
        return ["không nên gọi nhánh này khi che_do=moc"]

    monkeypatch.setattr(benchmark, "_tra_agent", _fake_tra_agent)
    monkeypatch.setattr(benchmark, "_tra", _fake_tra)

    benchmark.do_truy_hoi(_CASE_MAU, che_do="moc")

    assert len(goi_tra_agent) == 2, (
        f"che_do='moc' phải gọi _tra_agent() cho CẢ HAI biến thể co_dau/khong_dau của mỗi ca dương "
        f"(1 ca dương x 2 biến thể = 2 lần) — đo được {len(goi_tra_agent)} lần: {goi_tra_agent!r}"
    )
    assert goi_tra == [], (
        f"che_do='moc' KHÔNG được gọi _tra() (đường index-thô rẻ) — đây chính là bug 19/08 "
        f"(cờ tồn tại đúng hình thức nhưng không có tác dụng). Đã gọi: {goi_tra!r}"
    )


def test_che_do_lap_mac_dinh_van_goi_tra_khong_phai_tra_agent(monkeypatch):
    """Ca ĐỐI CHỨNG ÂM (Luật A) — không có nó, ca trên có thể xanh vì
    `do_truy_hoi` LUÔN gọi cả hai hàm bất kể `che_do`, không thật sự rẽ
    nhánh. Mặc định `che_do="lap"` phải giữ NGUYÊN hành vi cũ."""
    _vo_hieu_hoa_dang_nhap_va_canary(monkeypatch)

    goi_tra_agent: list[str] = []
    goi_tra: list[str] = []
    monkeypatch.setattr(benchmark, "_tra_agent", lambda c, q: (goi_tra_agent.append(q), ([], True))[1])
    monkeypatch.setattr(benchmark, "_tra", lambda c, q, k=None: (goi_tra.append(q), [])[1])

    benchmark.do_truy_hoi(_CASE_MAU)  # không truyền che_do -> mặc định "lap"

    assert goi_tra_agent == [], f"che_do mặc định (lap) KHÔNG được gọi _tra_agent(). Đã gọi: {goi_tra_agent!r}"
    assert len(goi_tra) == 2, f"che_do mặc định (lap) phải gọi _tra() cho cả hai biến thể. Đo được: {goi_tra!r}"


def test_khong_goi_tool_duoc_ghi_nhan_khi_agent_khong_goi_policy_search():
    """`_tra_agent` trả `co_goi=False` (agent không gọi tool) là MỘT chế độ
    hỏng khác hẳn "gọi tool nhưng truy hồi trượt" (docstring `_tra_agent` đã
    nêu) — `do_truy_hoi` phải giữ lại danh sách này để `main()` báo cáo,
    không được nuốt mất trong biến cục bộ."""
    import pytest

    monkeypatch = pytest.MonkeyPatch()
    try:
        _vo_hieu_hoa_dang_nhap_va_canary(monkeypatch)
        monkeypatch.setattr(benchmark, "_tra_agent", lambda c, q: ([], False))

        res = benchmark.do_truy_hoi(_CASE_MAU, che_do="moc")

        assert res.get("khong_goi_tool") == ["CASE-MAU-001", "CASE-MAU-001"], (
            f"Cả hai biến thể co_dau/khong_dau của CASE-MAU-001 đều phải xuất hiện trong "
            f"khong_goi_tool khi _tra_agent luôn trả co_goi=False. Đo được: {res.get('khong_goi_tool')!r}"
        )
    finally:
        monkeypatch.undo()
