"""Bug PO thật thấy (24/08): giao diện báo "Xác thực thành công" nhưng agent
vẫn nói/hành xử như CHƯA xác thực ngay lượt kế tiếp.

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI.** Cùng khuôn `test_a2_dong_y_truoc_khi_tao_ve.py`.
> ⚠️ **TỐN TIỀN** — tối đa 4 lượt LLM thật (2 ca × 2 lượt). Mặc định TẮT, bật
> bằng `FIN05_ALLOW_PAID_CALLS=1`.

## Root cause THẬT (Coder, 24/08, commit `5e8deb6`) — khác giả thuyết ban đầu

Giả thuyết ban đầu (PO thật, đọc code frontend): `verifyOtp()` vứt
`access_token` mới, tin nhắn sau vẫn mang token CŨ. Coder đo trực tiếp và
bác bỏ: `otp_verified_at` LUÔN tươi khi kiểm tra thật, không phải cookie/token.

Cơ chế thật: khách chạm dữ liệu nhạy cảm TRƯỚC khi xác thực → tool lỗi vì
thiếu OTP → agent báo cần xác thực → khách xác thực xong → frontend TỰ GỬI
LẠI đúng câu hỏi cũ (`pendingStarterRef`, luồng chip) → agent TRƯỚC ĐÂY
KHÔNG gọi lại tool đã lỗi, chỉ lặp lại kết luận CŨ từ trí nhớ hội thoại (dựa
vào ToolMessage lỗi trong lịch sử, không tra lại). Vá `prompt.py` bước 5:
tool vừa lỗi vì OTP + khách gửi lại yêu cầu tương tự ⟹ agent PHẢI gọi lại
tool, không tự kết luận từ trí nhớ.

## Hai chiều đối chứng (Coder gợi ý, PO-agent giao Tester viết)

    PHẢI RETRY       lượt 1 (chưa OTP) lỗi tool ⟹ xác thực ⟹ gửi lại CÙNG câu
                      ⟹ tool_calls lượt 2 PHẢI chứa lại ĐÚNG tool đã lỗi.
    KHÔNG CHẶN NHẦM   lượt 2 hỏi chuyện KHÁC (không liên quan lỗi OTP trước)
                      ⟹ KHÔNG bị ép gọi lại tool CŨ một cách máy móc — chỉ
                      cần không hồi quy hành vi bình thường (có reply thật).

Viết SAU khi Coder đã vá (khác A2 — A2 viết TRƯỚC để không phản chiếu bản
vá). Ở đây bản vá đã landed và Coder tự verify 3/3 trên container riêng —
vai trò của ca này là GIỮ hành vi đó lại như cổng hồi quy, viết từ ĐẶC TẢ
Coder khai (không đọc `prompt.py`), không phải xác nhận Coder đúng hay sai.
"""
from __future__ import annotations

import json
import subprocess
import uuid

import pytest

from tests._docker_co_mat import container_song
from tests._dong_bang import LY_DO, dang_dong_bang
from tests._ton_tien import duoc_phep_ton_tien, reason_text

CT = "fin05do-backend-1"
API = "http://localhost:8010"

CAU_NHAY_CAM = "Tôi bị trừ tiền 500 nghìn hôm qua, kiểm tra giúp tôi giao dịch đó."
CAU_KHONG_LIEN_QUAN = "Phí rút tiền về ngân hàng bên bạn tính thế nào vậy?"


def _song() -> bool:
    return container_song(CT)


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not duoc_phep_ton_tien(),
                       reason=reason_text(60_000, "tối đa 4 lượt chat thật qua /agent/chat, 2 ca")),
    pytest.mark.skipif(not _song(), reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def _login_khong_otp() -> str:
    """Đăng nhập, CỐ Ý KHÔNG xác thực OTP — token có otp_verified_at=None,
    đúng trạng thái khách MỚI bắt đầu hành trình, chưa chạm dữ liệu nhạy cảm
    lần nào. Tái hiện đúng kịch bản gốc: tool phải lỗi OTP Ở LƯỢT ĐẦU."""
    code = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"r=c.post('{API}/auth/login',json={{'phone':'0387000001','password':'Demo@123'}});"
        "print(r.json()['access_token'])"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", code],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"đăng nhập hỏng: {(r.stderr or r.stdout)[-400:]}"
    return r.stdout.strip().splitlines()[-1]


def _xac_thuc_otp(login_token: str) -> str:
    """OTP verify cho MỘT token login đã có sẵn — trả `access_token` MỚI đã
    otp_verified. Tách riêng khỏi `_login_khong_otp()` để test tự kiểm soát
    ĐÚNG THỜI ĐIỂM xác thực (giữa lượt 1 lỗi OTP và lượt 2 gửi lại) — đúng
    thứ tự sự kiện thật đã gây ra bug."""
    code = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"h={{'Authorization':'Bearer '+{login_token!r}}};"
        f"r=c.post('{API}/auth/otp/request',headers=h);"
        "sid=r.json()['session_id'];code=r.json()['otp_code'];"
        f"r=c.post('{API}/auth/otp/verify',headers=h,json={{'session_id':sid,'otp_code':code}});"
        "assert r.json().get('otp_verified') is True, 'OTP verify thất bại: '+r.text;"
        "print(r.json()['access_token'])"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", code],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"OTP verify hỏng: {(r.stderr or r.stdout)[-400:]}"
    return r.stdout.strip().splitlines()[-1]


def _chat(sentence: str, token: str, thread: str) -> dict:
    # thread_id trong body vô hại nhưng KHÔNG phải cơ chế nối lượt thật —
    # nối lượt thật = dùng LẠI cùng token (main.py suy thread từ user_id:iat
    # của JWT, ADR-044) — đúng khuôn test_a2_dong_y_truoc_khi_tao_ve.py.
    code = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"h={{'Authorization':'Bearer '+{token!r}}};"
        f"r=c.post('{API}/agent/chat',json={{'message':{sentence!r},'thread_id':{thread!r}}},headers=h);"
        "print(json.dumps({'http':r.status_code,'than':r.json()},ensure_ascii=False))"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", code],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"gọi chat hỏng: {(r.stderr or r.stdout)[-400:]}"
    j = json.loads(r.stdout.strip().splitlines()[-1])
    tc = j["than"].get("tool_calls") or []
    return {
        "tra": j,
        "tool": [x.get("tool_name") for x in tc],
        "tool_calls_day_du": tc,
        "reply": j["than"].get("reply") or "",
    }


def _co_loi_otp(tool_calls_day_du: list[dict]) -> bool:
    """Ít nhất một tool result trong lượt này báo lỗi thiếu/hết hạn OTP —
    đọc TRỰC TIẾP payload thật (result.status/message), không đoán từ câu
    chữ reply."""
    for tc in tool_calls_day_du:
        outcome = tc.get("result") or {}
        if isinstance(outcome, dict) and outcome.get("status") == "error" and "OTP" in str(outcome.get("message", "")):
            return True
    return False


def test_sau_otp_verify_gui_lai_cau_cu_phai_goi_lai_tool_da_loi():
    """PHẢI RETRY — đúng kịch bản gốc: lượt 1 (chưa OTP) tool lỗi ⟹ xác thực
    OTP ⟹ gửi lại ĐÚNG câu cũ, CÙNG thread ⟹ lượt 2 PHẢI gọi lại tool đã lỗi
    (không chỉ lặp kết luận cũ từ trí nhớ hội thoại)."""
    th = f"OTPRETRY-{uuid.uuid4().hex[:8]}"
    tok_chua_otp = _login_khong_otp()

    luot1 = _chat(CAU_NHAY_CAM, tok_chua_otp, th)
    if not _co_loi_otp(luot1["tool_calls_day_du"]):
        pytest.skip(
            f"Lượt 1 không gặp lỗi OTP nào (tool={luot1['tool']!r}) — không đúng nhánh cần cho ca "
            "này, không quan sát được. Có thể agent chưa gọi tool nhạy cảm ở lượt đầu."
        )
    tool_da_loi = {
        tc["tool_name"] for tc in luot1["tool_calls_day_du"]
        if isinstance(tc.get("result"), dict) and tc["result"].get("status") == "error"
        and "OTP" in str(tc["result"].get("message", ""))
    }

    tok_moi = _xac_thuc_otp(tok_chua_otp)
    luot2 = _chat(CAU_NHAY_CAM, tok_moi, th)

    assert tool_da_loi & set(luot2["tool"]), (
        f"Lượt 1 tool lỗi OTP: {tool_da_loi!r}. Sau khi xác thực OTP + gửi lại ĐÚNG câu cũ, "
        f"lượt 2 KHÔNG gọi lại tool nào trong số đó (tool lượt 2: {luot2['tool']!r}).\n"
        f"  reply lượt 2: {luot2['reply'][:300]}\n"
        "Đây chính là bug PO thật thấy: agent lặp lại kết luận cũ từ trí nhớ thay vì tra lại "
        "sau khi khách vừa xác thực xong (5e8deb6 vá đúng chỗ này)."
    )


def test_sau_otp_verify_hoi_chuyen_khac_khong_bi_ep_goi_lai_tool_cu():
    """KHÔNG CHẶN NHẦM — lượt 2 đổi hẳn sang hỏi CHUYỆN KHÔNG LIÊN QUAN tới
    lỗi OTP ở lượt 1 (không phải chính sách chung chung — RAG có thể chưa
    nạp trên một số ngăn, tránh nhầm 'không có câu trả lời' với 'bị ép gọi
    lại tool cũ'). Bản vá không được biến thành 'cứ sau lỗi OTP là gọi lại
    tool bất kể câu hỏi mới là gì' — chỉ cần KHÔNG hồi quy: có reply thật,
    không lỗi cứng."""
    th = f"OTPRETRY-{uuid.uuid4().hex[:8]}"
    tok_chua_otp = _login_khong_otp()

    luot1 = _chat(CAU_NHAY_CAM, tok_chua_otp, th)
    if not _co_loi_otp(luot1["tool_calls_day_du"]):
        pytest.skip(
            f"Lượt 1 không gặp lỗi OTP nào (tool={luot1['tool']!r}) — không đúng nhánh cần cho ca "
            "này, không quan sát được."
        )

    tok_moi = _xac_thuc_otp(tok_chua_otp)
    luot2 = _chat(CAU_KHONG_LIEN_QUAN, tok_moi, th)

    assert luot2["tra"]["http"] < 500, (
        f"HTTP {luot2['tra']['http']} khi hỏi chuyện không liên quan sau lỗi OTP trước đó — "
        f"không được lỗi cứng: {luot2['reply'][:200]}"
    )
    assert luot2["reply"].strip(), (
        "Reply RỖNG khi hỏi chuyện không liên quan sau lỗi OTP trước đó — bản vá 'gọi lại tool "
        "đã lỗi' có thể đang ép nhầm sang MỌI câu hỏi kế tiếp, không chỉ câu TRÙNG với câu đã lỗi."
    )
