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


# ===========================================================================
# 5. ĐẦU VÀO — tin nhắn khách TỰ GÕ (lỗ hổng lớn nhất, vá 2026-08-13)
# ===========================================================================
#
# Bản vá trước chỉ chặn PII trong KẾT QUẢ TOOL. Nhưng khách gõ thẳng PII của
# CHÍNH MÌNH vào ô chat ("mình là Bách, sđt 0987654321") thì nó đi nguyên văn
# lên OpenAI — dù tài khoản đăng nhập là tài khoản seed giả.
#
# Chuẩn ngành fintech 2026 yêu cầu gate CẢ ĐẦU VÀO lẫn đầu ra, không chỉ đầu ra.
# Tái dùng src/observability/pii.py (regex + Presidio + underthesea) vốn đã có
# sẵn nhưng trước đây chỉ chạy cho LOG.

from src.observability.pii import scrub_pii  # noqa: E402


def test_dau_vao_che_ho_ten_va_sdt_khach_tu_go():
    """Khách tự khai PII trong tin nhắn -> phải bị che trước khi rời hệ thống."""
    goc = "mình là Bách, sđt 0987654321, bị trừ tiền 2 lần"
    sach = scrub_pii(goc, muc_dich="model_input")
    assert "0987654321" not in sach, f"SĐT lọt lên LLM: {sach}"
    assert "Bách" not in sach, f"Họ tên lọt lên LLM: {sach}"


def test_dau_vao_giu_nguyen_du_lieu_nghiep_vu():
    """Test đối trọng — che quá tay thì agent hết tra cứu được.

    Mã giao dịch, mã biên lai và SỐ TIỀN là thứ agent bắt buộc phải thấy để
    gọi tool. Che nhầm chúng còn tệ hơn không che gì: agent không tra được,
    khách không được giải quyết, mà PII thì vẫn có thể lọt chỗ khác.
    """
    truong_hop = [
        ("mã giao dịch TXN20260810000001 chưa về tiền", "TXN20260810000001"),
        ("biên lai RC-0001 bị lỗi", "RC-0001"),
        ("tôi chuyển 5000000 hôm qua", "5000000"),
        ("chuyển nhầm 270k cho bạn", "270k"),
    ]
    for goc, phai_con in truong_hop:
        sach = scrub_pii(goc, muc_dich="model_input")
        assert phai_con in sach, (
            f"Che quá tay — mất dữ liệu nghiệp vụ {phai_con!r}\n  gốc:  {goc}\n  sau: {sach}"
        )


def test_dai_tu_nhan_xung_khong_bi_coi_la_ten_nguoi():
    """'tôi'/'mình'/'em' là đại từ, không phải tên — che đi thì mất chủ ngữ.

    Phát hiện thật lúc đo: "tôi chuyển 5tr cho số 09..." thành "[PERSON] chuyển
    5tr cho số [VN_PHONE]" — agent mất luôn thông tin ai là người chuyển.
    """
    for dai_tu in ("tôi", "mình", "em", "anh", "chị"):
        cau = f"{dai_tu} bị trừ tiền 2 lần"
        sach = scrub_pii(cau, muc_dich="model_input")
        assert sach.startswith(dai_tu), f"Đại từ {dai_tu!r} bị che nhầm: {sach}"


def test_duong_gui_llm_that_su_di_qua_scrub():
    """Canh đúng ĐƯỜNG THẬT, không chỉ canh hàm scrub_pii chạy được.

    Test 3 hàm trên chứng minh scrub_pii đúng; test này chứng minh nó ĐƯỢC GỌI
    ở đúng chỗ tin nhắn rời hệ thống (src/agents/graph.py). Thiếu test này thì
    ai đó gỡ lời gọi ra, 3 test kia vẫn xanh.
    """
    from pathlib import Path

    goc = Path(__file__).resolve().parent.parent.parent
    src = (goc / "src" / "agents" / "graph.py").read_text(encoding="utf-8")
    assert "scrub_pii(message, muc_dich=" in src, (
        "Tin nhắn khách KHÔNG còn đi qua scrub_pii trước khi vào HumanMessage — "
        "PII khách tự gõ sẽ rời hệ thống nguyên văn."
    )


# ===========================================================================
# 6. ĐỊNH DANH TRỰC TIẾP (user_id/wallet_id) — bút danh hoá ≠ ẩn danh hoá
# ===========================================================================
#
# user_id/wallet_id trông như chuỗi vô nghĩa nhưng nối ngược về một người cụ
# thể được, nên VẪN là dữ liệu cá nhân theo GDPR và tinh thần NĐ 13/2023.
# Agent không cần chúng: build_customer_tools đóng cứng user_id qua closure.

def test_dinh_danh_truc_tiep_bi_che_truoc_khi_len_llm(sample_db):
    ket_qua = _goi_tool(sample_db, "lookup_transaction", {"trans_id": "TXN-0001"})
    noi_dung = json.dumps(ket_qua, ensure_ascii=False)
    assert "USR-A" not in noi_dung, f"user_id lọt lên LLM: {noi_dung[:300]}"
    assert "900000000001" not in noi_dung, f"wallet_id lọt nguyên văn: {noi_dung[:300]}"


def test_che_dinh_danh_khong_pha_lop_chan_tra_cheo_atlas_001(sample_db):
    """Thứ tự BẮT BUỘC: _enforce_requester_is_party TRƯỚC, scrub SAU.

    `_enforce_requester_is_party` ĐỌC `wallet_id` từ kết quả tool để xác minh
    người hỏi có thực sự là một bên của giao dịch. Nếu che wallet_id TRƯỚC khi
    nó chạy, hàm đó nhìn thấy chuỗi đã bị che, không khớp được với ví của ai
    cả — lớp chặn tra chéo ATLAS-001 hỏng ÂM THẦM mà mọi test PII vẫn xanh.

    Dùng USR-CSKH — user KHÔNG phải bên nào của TXN-0001 (giao dịch đó là
    USR-A → USR-B, cả hai đều là bên hợp lệ nên không dùng để test chặn được;
    đây là lỗi giả định thật mình mắc lúc viết test lần đầu, ghi lại để phiên
    sau không lặp).
    """
    from src.agents.tools.customer_tools import build_customer_tools

    otp = dt.datetime.utcnow().timestamp()
    tools = {t.name: t for t in build_customer_tools(sample_db, user_id="USR-CSKH", otp_verified_at=otp)}
    ket_qua = tools["lookup_transaction"].invoke({"trans_id": "TXN-0001"})

    assert ket_qua.get("status") != "found", (
        "USR-CSKH (không phải bên nào của giao dịch) vẫn tra ra được — lớp chặn "
        "ATLAS-001 đã hỏng.\n"
        "Nguyên nhân thường gặp: che wallet_id TRƯỚC khi _enforce_requester_is_party chạy.\n"
        f"Kết quả: {json.dumps(ket_qua, ensure_ascii=False)[:300]}"
    )


def test_chinh_chu_van_tra_duoc_giao_dich_cua_minh(sample_db):
    """Đối trọng cho test trên — che định danh không được chặn nhầm chính chủ."""
    ket_qua = _goi_tool(sample_db, "lookup_transaction", {"trans_id": "TXN-0001"})
    assert ket_qua.get("status") == "found", (
        f"Chính chủ USR-A KHÔNG tra được giao dịch của mình — che quá tay: {ket_qua}"
    )
