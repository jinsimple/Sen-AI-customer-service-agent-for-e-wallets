"""Không một thông tin định danh nào của khách được rời hệ thống lên LLM.

VÌ SAO CÓ FILE NÀY
------------------
Rà soát 2026-08-13 phát hiện: họ tên thật và số điện thoại của khách đi thẳng
vào payload gửi OpenAI, không qua bất kỳ bước che nào. `src/observability/
pii.py` chỉ làm sạch LOG — không chạm prompt.

Đây là OWASP **LLM02:2025 Sensitive Information Disclosure** (hạng mục nhảy từ
#6 lên #2 trong bảng 2025), và chạm nghĩa vụ **NĐ 13/2023 Điều 25** về chuyển
dữ liệu cá nhân công dân Việt Nam ra nước ngoài — gọi OpenAI API chính là
chuyển dữ liệu ra nước ngoài.

Ghi nhận phần ĐÃ ĐÚNG, không được làm hỏng khi vá: thông tin BÊN THỨ BA đã
được che chuẩn (BR-06 `_party_info` + `masking.py`), kèm `_enforce_requester_
is_party` chặn tra chéo. Test dưới đây canh cả hai chiều.

NGUYÊN TẮC CỦA BỘ TEST NÀY
--------------------------
Không tin vào lời hứa "đã che rồi". Dựng payload THẬT như lúc chạy production,
rồi quét bằng dữ liệu PII đã biết trước. Có mặt = ĐỎ.

CHẠY:  pytest tests/test_security/test_pii_khong_ro_ri_len_llm.py -v
"""

from __future__ import annotations

import datetime as dt
import json
import re

from src.agents.prompt import build_system_prompt

# PII của user seed trong tests/conftest.py::sample_db — giá trị biết trước để
# quét. KHÔNG dùng regex đoán mò: quét đúng chuỗi đã biết cho kết quả nhị phân,
# không có vùng xám "có thể là PII".
PII_KHACH = {
    "họ tên": "Nguyễn Văn A",
    "số điện thoại": "0901000001",
}
PII_NGUOI_KHAC = {
    "họ tên bên thứ ba": "Trần Thị B",
    "SĐT bên thứ ba": "0901000002",
}


def _quet(noi_dung: str, can_tim: dict[str, str]) -> list[str]:
    """Trả danh sách nhãn PII tìm thấy nguyên văn trong chuỗi."""
    return [nhan for nhan, gia_tri in can_tim.items() if gia_tri and gia_tri in noi_dung]


# ===========================================================================
# 1. SYSTEM PROMPT — phần gửi lại ở MỌI vòng gọi LLM
# ===========================================================================

def test_system_prompt_khong_chua_ho_ten_that_cua_khach():
    """Agent KHÔNG cần biết khách tên gì để điều tra giao dịch.

    Xưng "quý khách" là đủ. Nhét họ tên thật vào system prompt vừa là PII rời
    hệ thống ở MỌI vòng gọi, vừa tốn token vô ích — hai vấn đề cùng một chỗ.
    """
    prompt = build_system_prompt(
        current_time=dt.datetime(2026, 8, 13, 10, 0, 0),
        customer_name=PII_KHACH["họ tên"],
    )
    lot = _quet(prompt, PII_KHACH)
    assert not lot, (
        f"System prompt chứa PII nguyên văn: {lot}\n"
        f"Đây là dữ liệu rời hệ thống lên OpenAI ở MỌI vòng gọi LLM.\n"
        "→ Bỏ họ tên khỏi prompt (dùng 'quý khách'), hoặc bút danh hoá trước khi gửi."
    )


def test_system_prompt_van_dung_duoc_khi_khong_co_ten():
    """Bỏ tên đi thì prompt vẫn phải mạch lạc, không để lại chỗ trống kỳ quặc."""
    prompt = build_system_prompt(current_time=dt.datetime(2026, 8, 13, 10, 0, 0), customer_name="")
    assert "{" not in prompt or "{{" in prompt, "Còn placeholder chưa thay trong prompt"
    assert len(prompt) > 500, "Prompt rỗng bất thường"


# ===========================================================================
# 2. KẾT QUẢ TOOL — phần đi vào hội thoại gửi LLM
# ===========================================================================

def _goi_tool(sample_db, ten_tool: str, tham_so: dict, otp_fresh: bool = True):
    """Gọi tool đúng như agent gọi lúc chạy thật."""
    from src.agents.tools.customer_tools import build_customer_tools

    otp = dt.datetime.utcnow().timestamp() if otp_fresh else None
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-A", otp_verified_at=otp)}
    assert ten_tool in tools, f"Không có tool {ten_tool}"
    return tools[ten_tool].invoke(tham_so)


def test_lookup_transaction_khong_tra_ve_pii_cua_chinh_khach(sample_db):
    """Kết quả tool đi thẳng vào hội thoại LLM — không được mang PII nguyên văn.

    Số tiền/mã GD/thời gian là dữ liệu NGHIỆP VỤ agent cần để làm việc, giữ lại.
    Họ tên và số điện thoại thì KHÔNG cần — agent không dùng chúng để suy luận
    gì cả, chỉ đọc rồi nhắc lại. Đúng nguyên tắc tối thiểu hoá dữ liệu của
    OWASP LLM02:2025.
    """
    ket_qua = _goi_tool(sample_db, "lookup_transaction", {"trans_id": "TXN-0001"})
    noi_dung = json.dumps(ket_qua, ensure_ascii=False)

    lot = _quet(noi_dung, PII_KHACH)
    assert not lot, (
        f"Kết quả lookup_transaction chứa PII nguyên văn của khách: {lot}\n"
        f"Payload: {noi_dung[:400]}\n"
        "→ Bút danh hoá trước khi đưa vào hội thoại gửi LLM."
    )


def test_get_customer_history_khong_tra_ve_pii(sample_db):
    ket_qua = _goi_tool(sample_db, "get_customer_history", {"days": 90})
    noi_dung = json.dumps(ket_qua, ensure_ascii=False)
    lot = _quet(noi_dung, PII_KHACH)
    assert not lot, (
        f"get_customer_history chứa PII nguyên văn: {lot}\n{noi_dung[:400]}"
    )


# ===========================================================================
# 3. CHIỀU NGƯỢC LẠI — phần ĐÃ LÀM ĐÚNG, canh không bị phá khi vá
# ===========================================================================

def test_van_giu_nguyen_viec_che_thong_tin_ben_thu_ba(sample_db):
    """BR-06 đã che tên/SĐT/STK bên thứ ba — vá PII chính chủ KHÔNG được làm hỏng."""
    ket_qua = _goi_tool(sample_db, "lookup_transaction", {"trans_id": "TXN-0001"})
    noi_dung = json.dumps(ket_qua, ensure_ascii=False)
    lot = _quet(noi_dung, PII_NGUOI_KHAC)
    assert not lot, (
        f"RÒ RỈ BÊN THỨ BA: {lot} — đây là vi phạm PDPA nghiêm trọng hơn cả PII "
        f"chính chủ, vì khách không có quyền biết thông tin người khác.\n{noi_dung[:400]}"
    )


def test_du_lieu_nghiep_vu_van_con_du_de_agent_lam_viec(sample_db):
    """Che PII KHÔNG được che luôn thứ agent cần — nếu không agent hết tra cứu được.

    Đây là test đối trọng: chống bản vá quá tay kiểu "che sạch cho an toàn"
    rồi agent không còn dữ liệu nào để trả lời khách.
    """
    ket_qua = _goi_tool(sample_db, "lookup_transaction", {"trans_id": "TXN-0001"})
    assert ket_qua.get("status") in ("found", "not_found", "multiple_matches"), (
        f"Tool hỏng sau khi che PII: {ket_qua}"
    )
    if ket_qua.get("status") == "found":
        txn = ket_qua.get("transaction") or {}
        assert txn.get("amount") is not None, "Mất số tiền — agent không còn gì để đối chiếu"
        assert txn.get("trans_id") or txn.get("id"), "Mất mã giao dịch — không trích dẫn được"


# ===========================================================================
# 4. CHỐNG THOÁI HOÁ — bộ test này phải quét ĐÚNG thứ thật sự gửi đi
# ===========================================================================

def test_khong_con_duong_nao_khac_dua_pii_len_llm():
    """Quét mã nguồn: không nơi nào ghép PII vào prompt ngoài đường đã kiểm.

    Canh trường hợp ai đó thêm một chỗ mới nhét `full_name`/`phone` vào prompt
    mà quên rằng dữ liệu đó rời hệ thống.
    """
    from pathlib import Path

    goc = Path(__file__).resolve().parent.parent.parent
    nghi_van = re.compile(r"(customer_name|full_name|\.phone)\s*[,)=]")
    vi_pham = []
    for p in (goc / "src" / "agents").rglob("*.py"):
        for i, dong in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if nghi_van.search(dong) and "# PII-OK:" not in dong:
                vi_pham.append(f"{p.relative_to(goc)}:{i}: {dong.strip()[:90]}")
    assert not vi_pham, (
        "Có chỗ đưa PII vào tầng agent (nơi dữ liệu rời hệ thống lên LLM):\n  "
        + "\n  ".join(vi_pham)
        + "\n→ Nếu đã bút danh hoá và cố ý, đánh dấu '# PII-OK: <lý do>' ở cuối dòng."
    )
