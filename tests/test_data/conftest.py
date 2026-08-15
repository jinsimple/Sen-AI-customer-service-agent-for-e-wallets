"""Fixture dùng chung cho các test canh trên ARTIFACT của bộ đo.

Một số lỗi của bộ đo chỉ hiện ra trong bản ghi kết quả, không hiện trong hàm
nào cả — vd lỗi 15/08: việc GÁN TRẠNG THÁI nằm trong vòng lặp `run()`, nên
unit test của hàm chấm không bao giờ chạm tới. Với loại lỗi đó, thứ đáng canh
là chính file raw đã lưu.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_THU_MUC_KET_QUA = Path(__file__).resolve().parents[2] / "eval" / "results"


@pytest.fixture(scope="session")
def ban_ghi_adversarial() -> list[dict]:
    """Mọi bản ghi adversarial đã lưu, gắn thêm `_ten_file` để truy ngược.

    SKIP (không phải PASS) khi chưa có file nào: một máy CI sạch không có
    `eval/results/`, và "không có dữ liệu để kiểm" phải nói là chưa kiểm được
    chứ không được đọc thành đã kiểm xong.
    """
    files = sorted(_THU_MUC_KET_QUA.glob("adversarial_run_*_raw.json"))
    if not files:
        pytest.skip("Chưa có bản ghi adversarial nào trong eval/results/ — chưa đo được.")
    ban_ghi: list[dict] = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            pytest.fail(f"{f.name} hỏng định dạng JSON ({e}) — bản ghi hỏng thì không kiểm được gì.")
        for r in d:
            ban_ghi.append({**r, "_ten_file": f.name})
    return ban_ghi
