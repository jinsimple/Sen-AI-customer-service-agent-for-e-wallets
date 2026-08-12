"""FIN05-StressTest-Plan-v2 ST2-B-07 — `CLARIFY_QUESTION_MAX_ROUNDS` (2,
src/config.py:29) KHÔNG được enforce bởi code (không có counter/vòng lặp
chặn cứng ở `src/agents/graph.py`) — chỉ là 1 CHỈ THỊ trong system prompt
(`src/agents/prompt.py::build_system_prompt`, dòng "hỏi lại tối đa {max_rounds}
lần"), agent (LLM) tự tuân theo, KHÔNG có gì bảo đảm bằng code.

Test này CHỈ verify được phần WIRING xác định (config → prompt thật gửi cho
model đúng số vòng, không lệch pha nếu ai đó đổi CLARIFY_QUESTION_MAX_ROUNDS
mà quên cập nhật chỗ khác) — KHÔNG thể verify LLM có THẬT SỰ dừng hỏi sau
đúng N vòng hay không bằng test nhanh/mock, vì đó là hành vi ngôn ngữ tự
nhiên hoàn toàn phụ thuộc model thật. Việc đó cần 1 case eval multi-turn
gọi OpenAI thật (cùng dạng eval/adversarial_set.jsonl), CHƯA thêm ở đây —
ghi rõ như giới hạn đã biết, không giả vờ đã test đủ."""
from __future__ import annotations

import datetime as dt

from src.agents.prompt import build_system_prompt
from src.config import CLARIFY_QUESTION_MAX_ROUNDS


def test_system_prompt_embeds_the_configured_clarify_round_limit():
    prompt = build_system_prompt(current_time=dt.datetime.utcnow(), customer_name="Khách Test")

    needle = f"tối đa {CLARIFY_QUESTION_MAX_ROUNDS}"
    assert needle in prompt, (
        f"System prompt không chứa đúng '{needle}' — CLARIFY_QUESTION_MAX_ROUNDS "
        "(src/config.py) và văn bản prompt thật (src/agents/prompt.py) đã lệch "
        "pha. LƯU Ý: đây chỉ xác nhận WIRING, không xác nhận LLM thật có tuân "
        "theo chỉ thị này hay không — cần eval multi-turn thật để verify hành "
        "vi (xem docstring module)."
    )
    assert prompt.count(str(CLARIFY_QUESTION_MAX_ROUNDS)) >= 2, (
        "Prompt gốc dùng {max_rounds} ở 2 chỗ khác nhau (dòng 45 và có thể "
        "nơi khác) — nếu chỉ còn 1 chỗ, khả năng 1 vị trí đã bị sửa/xoá "
        "nhầm khi chỉnh sửa prompt."
    )
