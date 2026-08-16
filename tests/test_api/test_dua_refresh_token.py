"""Phiên hết hạn sau khi NGỒI YÊN — và một cổng cho giả thuyết ĐÃ BỊ BÁC.

## ⚠️ LỊCH SỬ: file này từng canh một bug KHÔNG TỒN TẠI. Đọc trước khi sửa.

Ban đầu file dựng để tái lập giả thuyết **đua refresh token** (hai request đồng
thời cùng dùng một refresh token dùng-một-lần → AUTH5-03 thu hồi cả family →
phiên chết). Giả thuyết đó **BỊ BÁC bằng đo** (16/08):

    Pha D  đua sau hết hạn, mỗi racer giữ Set-Cookie như trình duyệt
           -> một racer trả cookie mới; dùng cookie đó: 200 · 200  (PHIÊN SỐNG)
    tầng-0 một request client sạch -> rotated=1 · revoked=0
           (cặp "rotated 10 ↔ revoked 10" trước đó là TỔNG TÍCH LUỸ của nhiều
            lượt probe song song, không phải quan hệ nhân quả)

Và "phiên chết hẳn" quan sát được ở lượt đầu là **hiện vật của harness tester**:
racer gửi cookie bằng `-H` mà không `-c`, nên vứt cookie mới, rồi kiểm bằng jar
ôm refresh token đã tiêu. Ghi lại vì bài học đắt hơn kết quả: **một phép đo
không giữ Set-Cookie thì không mô phỏng được trình duyệt.**

## Cơ chế THẬT, tái lập được (16/08, có nhãn vật)

    VẬT: backend a216b98c1b79 (có tầng-0) · frontend chưa vá · stack demo

    t+0     mở /chat -> 2 request -> 200 (cookie tươi)
            NGỒI YÊN 16 phút, trang KHÔNG bắn request nào
    t+961   thao tác đầu -> POST /api/agent-chat -> 401
            màn hình: "Có lỗi: Phiên đăng nhập đã hết hạn"
    t+1047  gõ lại      -> 200 · 200 · ws-ticket 200 (handoff chạy)
    tầng-0: rotated=1 · revoked=0

Cookie mới nằm trên RESPONSE của chính lượt 401, nên **request kế mới dùng được**
— khiếm khuyết ở `proxy.ts`, không phải đua, không phải thu hồi.

Chi tiết cơ chế coder đọc từ `src/auth.py:134-155` + `proxy.ts`:

    refresh token DÙNG-MỘT-LẦN. Request refresh thứ nhất rotate xong đánh dấu
    `rotated=True` giữ 60 giây; request thứ hai dùng CÙNG token trong 60s đó bị
    AUTH5-03 coi là dấu hiệu đánh cắp -> THU HỒI CẢ FAMILY, gồm cả cặp token mà
    đứa thứ nhất vừa phát. Và `refreshSessionIfNeeded` (BFF) KHÔNG có state dùng
    chung giữa các request đồng thời.

⟹ Hai request bất kỳ chồng nhau trong cửa sổ `REFRESH_MARGIN_SECONDS = 120`
  trước hết hạn là đủ trúng. Không cần trùng mili-giây.

## VÌ SAO FILE NÀY ĐÒI MỘT INSTANCE RIÊNG — đọc trước khi "dọn cho gọn"

TTL access token thật là **15 phút** (tester đo 15,0 phút, ĐỒNG NHẤT cả 4 role —
không phân tầng). Cửa sổ gia hạn chỉ mở ở **phút 13**. Nên một ca chạy trên
stack thường tốn **~13 phút chờ**.

    Một nhánh không chạy NHANH được cũng là một nhánh KHÔNG AI CANH.

Đó là Luật 14 áp cho chiều THỜI GIAN: CI sẽ không bao giờ chạy một ca 13 phút,
nên lớp lỗi này sẽ vĩnh viễn chỉ tái lập được thủ công — tức vĩnh viễn không có
ai gác. Vì vậy PO-agent duyệt **instance TTL ngắn là HẠ TẦNG ĐO BẮT BUỘC** cho
vùng auth, không phải tiện ích:

    docker compose -p fin05test  +  JWT_ACCESS_EXPIRE_MINUTES=1
    -> mỗi lần lặp ~40 giây thay vì ~13 phút

## CÁCH CHẠY

    FIN05_TEST_BASE_URL=https://localhost:8443 pytest tests/test_api/test_dua_refresh_token.py

Thiếu biến đó thì file **skip có thông báo rõ** — và `test_ly_do_skip_phai_that`
bên dưới canh chính cơ chế skip ấy (Luật 6: một `skip` phải TỰ CHỨNG MINH lý do
là thật; skip vì "chưa có hạ tầng" hợp lệ, skip vì gõ sai biến thì KHÔNG).

## ⚠️ KHOẢNG CÁCH GIỮA HAI REQUEST Ở ĐÂY **KHÔNG** DÙNG ĐỂ ĐỊNH NGƯỠNG

Nếu ai đó lấy số đo được ở đây làm `N` cho một grace-window: **ĐỪNG**.

Harness này bắn hai tiến trình/luồng riêng, nên khoảng cách nó đo là **độ trễ
spawn của máy chạy test**, không phải khoảng cách hai request của TRÌNH DUYỆT
đến được server. `N` nới lỏng một control chống đánh cắp token (AUTH5-03); lấy
`N` từ hiện vật của công cụ đo là **hạ bảo mật dựa trên cách đo**, không dựa
trên sản phẩm.

`N` phải lấy từ **dấu thời gian SERVER-SIDE** (log `auth.py:150`). PO-agent đã
chốt như vậy. Số ở đây, nếu in ra, chỉ là **giới hạn trên thô của harness**.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import pytest

BASE = os.environ.get("FIN05_TEST_BASE_URL", "").rstrip("/")
KHACH = ("0974000145", "Demo@123")
TTL_TOI_DA_GIAY = 120  # instance đo phải có TTL NGẮN; 15 phút thật là không đo được


def _giai_ma_exp(cookie_val: str) -> tuple[int, int]:
    """Trả (iat, exp) của access token trong cookie phiên."""
    d = json.loads(urllib.parse.unquote(cookie_val))
    than = d["access_token"].split(".")[1]
    pl = json.loads(base64.urlsafe_b64decode(than + "=" * (-len(than) % 4)))
    return pl["iat"], pl["exp"]


def _yeu_cau_ha_tang():
    if not BASE:
        pytest.skip(
            "Chưa có instance TTL ngắn: đặt FIN05_TEST_BASE_URL trỏ tới stack có "
            "JWT_ACCESS_EXPIRE_MINUTES=1. CHƯA ĐO ĐƯỢC, không phải 'đạt'. "
            "Chạy trên stack thường sẽ tốn ~13 phút/ca — xem docstring đầu file.",
            allow_module_level=True,
        )


# ===========================================================================
# Luật 6 áp cho chính file này — skip phải TỰ CHỨNG MINH
# ===========================================================================


def test_ly_do_skip_phai_that():
    """Chạy LUÔN. Phân biệt "chưa có hạ tầng" với "gõ sai biến / trỏ nhầm stack".

    Skip vì thiếu NĂNG LỰC là hợp lệ. Skip vì **dây nối sai** thì không — và hai
    thứ đó nhìn từ report giống hệt nhau. Đây đúng ca F-CI-3: hai bộ test skip
    im lặng suốt hai ngày vì đoán sai một cái tên.
    """
    if not BASE:
        pytest.skip("FIN05_TEST_BASE_URL chưa đặt — chưa có hạ tầng đo. Đúng nghĩa skip.")

    httpx = pytest.importorskip("httpx")
    with httpx.Client(verify=False, timeout=30) as c:
        r = c.post(f"{BASE}/api/session", json={"phone": KHACH[0], "password": KHACH[1]})
        assert r.status_code == 200, (
            f"Trỏ tới {BASE} nhưng đăng nhập trả {r.status_code} — instance sai hoặc "
            "chưa lên. Đây là BUG CỦA DÂY NỐI, không phải thiếu hạ tầng."
        )
        iat, exp = _giai_ma_exp(r.cookies.get("fin05_session", ""))

    ttl = exp - iat
    assert ttl <= TTL_TOI_DA_GIAY, (
        f"Instance ở {BASE} có TTL {ttl}s ({ttl/60:.1f} phút) — ĐÂY LÀ STACK THƯỜNG, "
        f"không phải instance đo. Mỗi ca sẽ tốn ~{(ttl-120)/60:.0f} phút chờ và CI sẽ "
        "không bao giờ chạy nó. Dựng stack riêng với JWT_ACCESS_EXPIRE_MINUTES=1."
    )


# ===========================================================================
# Phép tái lập
# ===========================================================================


def _phien_moi(httpx):
    c = httpx.Client(verify=False, timeout=40)
    r = c.post(f"{BASE}/api/session", json={"phone": KHACH[0], "password": KHACH[1]})
    assert r.status_code == 200
    _, exp = _giai_ma_exp(r.cookies.get("fin05_session", ""))
    return c, exp


def _cho_toi_cua_so(exp: int, truoc_giay: int = 60):
    """Chờ tới khi còn `truoc_giay` giây trước hết hạn — TRONG ngưỡng 120s."""
    import time

    while time.time() < exp - truoc_giay:
        time.sleep(0.5)


def _goi(client, cookie_header: str | None = None):
    h = {"Cookie": cookie_header} if cookie_header else {}
    return client.post(f"{BASE}/api/tools/customer-history", json={}, headers=h).status_code


@pytest.mark.slow
def test_hai_request_dong_thoi_trong_cua_so_gia_han_khong_giet_phien():
    """ĐUA không được giết phiên — cổng giữ một TÍNH CHẤT ĐANG ĐÚNG.

    ⚠️ Đây KHÔNG còn là ca tái lập bug (giả thuyết đua đã bị bác — xem docstring
    đầu file). Nó ở lại vì lý do khác: **đua-không-giết-phiên là tính chất hiện
    đang đúng và chưa ai canh.** Một bản vá single-flight/grace về sau, hoặc một
    thay đổi ở AUTH5-03, có thể phá nó mà không ai biết.

    Giữ một tính chất đang đúng có người canh ≠ giữ một ca tái lập bug. Đừng xoá
    vì "bug không có thật" — thứ nó canh mới là thật.

    ## Điểm phân xử nằm ở REQUEST THỨ BA, không ở hai request đua

    Có HAI khiếm khuyết khác nhau trong vùng này và chúng cho triệu chứng gần
    giống nhau — assert phải tách được:

    | Triệu chứng | Cơ chế | Mức |
    |---|---|---|
    | 401 rồi request kế **200** | cookie mới đặt trên RESPONSE, handler đọc cookie từ REQUEST (`proxy.ts:112`) | nhẹ — bấm lại là chạy |
    | 401 rồi **401 mãi** | thu hồi CẢ FAMILY theo AUTH5-03 | nặng — phiên chết hẳn |

    Chỉ cái thứ hai khớp triệu chứng PO thật gặp (*"chết đúng lúc bấm gặp người
    thật"*). Nên ca này gọi lại **ba lần** sau cú đua: một 401 đơn lẻ rồi hồi
    phục KHÔNG làm ca này đỏ; chết hẳn thì mới đỏ.
    """
    _yeu_cau_ha_tang()
    httpx = pytest.importorskip("httpx")
    c, exp = _phien_moi(httpx)
    ck = f"fin05_session={c.cookies.get('fin05_session')}"
    _cho_toi_cua_so(exp)

    with ThreadPoolExecutor(max_workers=2) as ex:
        ma = [f.result() for f in [ex.submit(_goi, c, ck), ex.submit(_goi, c, ck)]]

    sau = [_goi(c) for _ in range(3)]
    assert any(m == 200 for m in sau), (
        f"PHIÊN CHẾT HẲN sau cú đua. Hai request đua: {ma}; ba lượt sau: {sau} — "
        "không lượt nào hồi phục. Đây là thu-hồi-family (AUTH5-03), không phải "
        "khiếm khuyết cookie-trên-response. Người dùng thật bị đăng xuất giữa phiên."
    )
    c.close()


@pytest.mark.slow
def test_doi_chung_hai_request_tuan_tu_van_song():
    """ĐỐI CHỨNG — chứng minh ĐUA là điều kiện cần, không phải chỉ "hết hạn".

    Thiếu ca này thì một lần đỏ ở ca trên không phân biệt được "đua giết phiên"
    với "hễ chạm cửa sổ gia hạn là hỏng". Luật 2 ở chiều KỊCH BẢN: hai ca chỉ
    khác nhau ở tính ĐỒNG THỜI, nên chênh lệch kết quả quy được về đúng nó.
    """
    _yeu_cau_ha_tang()
    httpx = pytest.importorskip("httpx")
    c, exp = _phien_moi(httpx)
    _cho_toi_cua_so(exp)

    ma = [_goi(c) for _ in range(3)]
    assert any(m == 200 for m in ma), (
        f"Ngay cả TUẦN TỰ cũng chết: {ma}. Vấn đề KHÔNG phải đua — nó rộng hơn, "
        "và ca đua ở trên không còn quy được nhân quả."
    )
    c.close()


@pytest.mark.slow
def test_doi_chung_handoff_ngay_sau_dang_nhap_phai_dat():
    """ĐỐI CHỨNG THỨ HAI — bug là hàm của THỜI GIAN, không phải của luồng handoff.

    Dữ kiện đời thật (PO thật, 16/08): trước demo họ chạy **trọn kịch bản KỂ CẢ
    live-chat/handoff và ĐẠT**; sau đó đăng xuất hẳn, để một tiếng, đăng nhập
    TƯƠI, demo thật -> chết đúng ở handoff.

    ⟹ Biến duy nhất giữa hai lần là **thời gian từ đăng nhập tới lúc handoff**:
      lần test một mình lướt nhanh (< cửa sổ gia hạn) · lần demo có người nói
      chậm (> cửa sổ). Đời thật vô tình cho ta một cặp đối chứng hoàn chỉnh.

    Ca này là **nửa "không chặn nhầm"** của cặp: nếu nó cũng đỏ thì luồng handoff
    hỏng nói chung, và hai ca đua ở trên **không còn quy được nhân quả về thời
    gian** nữa. Thiếu nó, một bản vá siết tay ở luồng handoff vẫn làm mọi ca kia
    xanh mà không sửa đúng thứ hỏng.

    (Cũng loại luôn nghi vấn "phiên cũ để rác": PO đăng xuất hẳn nên family là
    mới sạch — trục stale-session không cần đo, tiết kiệm một chiều.)
    """
    _yeu_cau_ha_tang()
    httpx = pytest.importorskip("httpx")
    c, exp = _phien_moi(httpx)

    # KHÔNG chờ — gọi ngay khi token còn tươi nguyên.
    ma = [_goi(c) for _ in range(3)]
    assert all(m == 200 for m in ma), (
        f"Handoff hỏng NGAY khi phiên còn tươi: {ma}. Vậy bug KHÔNG phải hàm của "
        "thời gian, và hai ca đua ở trên mất khả năng quy nhân quả — điều tra lại "
        "từ đầu thay vì vá single-flight."
    )
    c.close()
