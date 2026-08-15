"""Canh việc bản ghi raw LƯU payload tool — điều kiện để chấm lại được.

═══ VÌ SAO TEST NÀY TỒN TẠI

Ngày 15/08, cổng chặn-nhầm mạnh nhất của dự án (96 câu reply THẬT của agent)
bị **tắt** — không phải vì bộ lọc hỏng, mà vì bản ghi raw chỉ lưu **TÊN** tool
chứ không lưu kết quả. Luật xuất xứ cần biết số trong câu trả lời có truy được
về một kết quả tool hay không; không có kết quả tool trong bản ghi thì không
phép chấm lại nào ngoài lượt chạy thật làm được, và một lượt chạy thật thì tốn
TPM — đúng ràng buộc khan hiếm nhất của dự án.

Cùng một hình dạng đã xuất hiện trước đó ở `so_lieu_dung_tham_chieu`: chấm lại
transcript cũ luôn trả "KHÔNG CHẤM ĐƯỢC" vì thiếu đúng dữ liệu này.

**Luật 5, dạng thao tác: cái gì bộ chấm ĐỌC để phán quyết thì bản ghi phải LƯU.**

═══ VÌ SAO THÊM TRƯỜNG MỚI, KHÔNG SỬA TRƯỜNG CŨ

File raw cũ đã ghi `tool_calls` là danh sách TÊN. Đổi nó thành danh sách dict
sẽ làm một khoá mang hai nghĩa tuỳ ngày ghi, và mọi phép chấm lại phải đoán
đang đọc file đời nào. Đó đúng họ lỗi đã tốn của đội cả buổi hôm nay — `[]` vs
`None`, "không có" vs "không biết". Với trường mới, file cũ chỉ đơn giản là
**thiếu khoá**: một trạng thái đọc được rõ ràng, không mơ hồ.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

_GOC = Path(__file__).resolve().parents[2]


def _khoa_duoc_ghi(duong_dan: Path, ten_ham: str) -> set[str]:
    """Đọc AST, lấy mọi khoá chuỗi của các dict literal trong một hàm.

    Đọc AST chứ không chạy hàm: cả hai hàm này đều gọi agent thật (tốn TPM) nên
    không test được bằng cách chạy. Cùng cách `tests/test_invariants.py` moi
    CheckConstraint — introspect thay vì tin vào việc đọc bằng mắt.
    """
    cay = ast.parse(duong_dan.read_text(encoding="utf-8"))
    for node in ast.walk(cay):
        if isinstance(node, ast.FunctionDef) and node.name == ten_ham:
            return {
                k.value
                for d in ast.walk(node)
                if isinstance(d, ast.Dict)
                for k in d.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
    pytest.fail(f"Không tìm thấy hàm {ten_ham}() trong {duong_dan.name}")


@pytest.mark.parametrize(
    "tep,ham",
    [("run_adversarial_set.py", "run"), ("measure_quality.py", "run")],
    ids=["bo_doi_khang", "bo_golden"],
)
def test_raw_luu_payload_tool_day_du(tep: str, ham: str):
    """Cả hai bộ đo phải ghi `tool_calls_day_du` vào bản ghi raw."""
    khoa = _khoa_duoc_ghi(_GOC / "eval" / tep, ham)
    assert "tool_calls_day_du" in khoa, (
        f"eval/{tep}::{ham}() không ghi `tool_calls_day_du` vào raw.\n"
        "Thiếu nó thì luật xuất xứ và `so_lieu_dung_tham_chieu` KHÔNG chấm lại "
        "được trên bản ghi cũ — mọi lần kiểm phải chạy agent thật, tốn TPM."
    )


@pytest.mark.parametrize(
    "tep,ham",
    [("run_adversarial_set.py", "run"), ("measure_quality.py", "run")],
    ids=["bo_doi_khang", "bo_golden"],
)
def test_van_giu_truong_ten_tool_cu(tep: str, ham: str):
    """Vế Luật 2 — trường mới KHÔNG được thay chỗ trường cũ.

    Thiếu ca này thì một bản "dọn dẹp" đổi `tool_calls` thành payload đầy đủ
    vẫn xanh ở test trên, và mọi file raw đã lưu bỗng mang một khoá hai nghĩa.
    Hai trường cùng tồn tại là chủ đích, không phải trùng lặp cần gộp.
    """
    khoa = _khoa_duoc_ghi(_GOC / "eval" / tep, ham)
    assert "tool_calls" in khoa, (
        f"eval/{tep}::{ham}() không còn ghi `tool_calls` (danh sách TÊN). "
        "File raw cũ dùng khoá này; bỏ nó đi là làm gãy mọi phép đọc lịch sử."
    )


def test_bo_cham_doc_gi_thi_ban_ghi_luu_nay(monkeypatch):
    """Nối thẳng nguyên tắc vào một phép kiểm chạy được, không chỉ là lời văn.

    `_grounding_digit_runs` ĐỌC payload tool để dựng tập số có căn cứ. Test này
    khẳng định nó thật sự đọc payload chứ không chỉ đọc tên — tức chứng minh
    `tool_calls_day_du` là thứ BẮT BUỘC phải lưu, không phải lưu cho dư.
    """
    import sys

    sys.path.insert(0, str(_GOC))
    from eval.measure_quality import _grounding_digit_runs

    day_du = [{"tool_name": "lookup_transaction",
               "tool_result": {"transaction": {"amount": 167000}}}]
    chi_ten = [{"tool_name": "lookup_transaction"}]

    co_can_cu = _grounding_digit_runs(day_du, [])
    khong_can_cu = _grounding_digit_runs(chi_ten, [])

    assert "167000" in co_can_cu, (
        "Bộ chấm KHÔNG rút được số từ payload đầy đủ — kiểm lại giả định của "
        f"test này trước khi kết luận về bản ghi. Nhận: {sorted(co_can_cu)}"
    )
    assert "167000" not in khong_can_cu, (
        "Bộ chấm rút được '167000' từ bản ghi CHỈ CÓ TÊN TOOL — nếu vậy thì "
        "nó đang lấy số từ đâu đó khác, và cả lập luận 'phải lưu payload' cần "
        f"xem lại. Nhận: {sorted(khong_can_cu)}"
    )
    assert inspect.signature(_grounding_digit_runs).parameters, "hàm không nhận tham số nào"
