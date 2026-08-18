"""Bất biến cho LỚP ĐỊNH TUYẾN — viết TRƯỚC cài đặt, chạy SAU khi có dấu.

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI.**
> ⚠️ **TỐN TIỀN** — ~14K token (lượt nhẹ 0đ, lượt đối chứng đầy đủ). Mặc định
> TẮT, bật bằng `FIN05_CHO_PHEP_TON_TIEN=1`.

    Một lượt đi ĐƯỜNG NHẸ không được tạo bản ghi nghiệp vụ nào:
        Δcomplaints = 0 · Δtickets = 0

Nếu một lượt **cần** tạo bản ghi thì tự nó đã không phải lượt đơn — việc nó đi
được đường nhẹ **chính là** bằng chứng phân loại sai.

## Lịch sử của chính file này, giữ lại vì nó là bài học

Bản đầu (17/08) **không chạy được**, và tôi ghi rõ vì sao thay vì viết đại: khi
đó phản hồi **không có trường nào** nói lượt đó đi đường nào ⟹ `Δ = 0` không
phân biệt được *"đường nhẹ không ghi"* với *"đường đầy đủ không có gì để ghi"*.
`Δ = 0` là **trạng thái thường trực** — đại đa số lượt chat không tạo vé, bất
kể đường nào. Assertion trùng trạng thái mặc định, đúng Luật 1.

Đề nghị của tôi lúc đó là **dấu tường minh**; nó được chọn và cài. Giờ có
`duong` trong phản hồi, ba test dưới đây mới có nghĩa.

> Vế đáng nhớ: **một bất biến không đo được thì đừng viết assertion cho nó** —
> viết ra chỗ đứt, `skip` với lý do là thiếu NĂNG LỰC thật, rồi đòi cái còn
> thiếu.

## Vì sao `Δresolutions` không có mặt ở đây

`resolutions` sinh khi `supervisor` duyệt (ràng buộc cứng 1), **không** sinh từ
một lượt chat ⟹ nó bằng 0 ở **mọi** đường, luôn luôn. Một vế **luôn đúng vì lý
do cấu trúc** làm bất biến **trông chắc hơn thực tế**. Bất biến này có HAI vế.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from tests._docker_co_mat import co_docker
from tests._dong_bang import LY_DO, dang_dong_bang
from tests._ton_tien import duoc_phep_ton_tien, ly_do

BANG = ("complaints", "tickets")
CT = "fin05do-backend-1"
PG = "fin05do-postgres-1"
API = "http://localhost:8010"
CAU_DON = "alo"
CAU_NGHIEP_VU = "cho em gặp người thật"  # → request_human_handoff → TẠO VÉ


def _stack_song() -> bool:
    # 🔴 CHẶN TRƯỚC: hàm này chạy trong biểu thức `skipif`, tức LÚC IMPORT.
    # Máy không có `docker` thì `subprocess` ném FileNotFoundError trong lúc
    # pytest THU THẬP ⟹ `Interrupted`, và kết quả của MỌI ca khác biến mất.
    # Đo được 18/08: 634 ca thu thập được → 0 ca chạy, chỉ vì thiếu một tệp
    # nhị phân. Trạng thái đúng là SKIP KÈM LÝ DO, không phải 'tệp này hỏng'.
    if not co_docker():
        return False
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={CT}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not duoc_phep_ton_tien(),
                       reason=ly_do(14_000, "1 lượt nhẹ 0 token + 1 lượt đầy đủ")),
    pytest.mark.skipif(not _stack_song(),
                       reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} — phép đo này GHI, "
                              "không chạy trên ngăn xếp dùng chung (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def _dem() -> dict[str, int]:
    sql = " UNION ALL ".join(f"SELECT '{b}',count(*) FROM {b}" for b in BANG)
    r = subprocess.run(["docker", "exec", PG, "psql", "-U", "fin05", "-d", "fin05", "-tAc", sql],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"không đếm được: {(r.stderr or r.stdout)[:200]}"
    return {dg.split("|")[0]: int(dg.split("|")[1]) for dg in r.stdout.splitlines() if "|" in dg}


def _chat(cau: str) -> dict:
    ma = (
        "import httpx,json;"
        "c=httpx.Client(timeout=300);"
        f"r=c.post('{API}/auth/login',json={{'phone':'0387000001','password':'Demo@123'}});"
        "h={'Authorization':'Bearer '+r.json()['access_token']};"
        f"r=c.post('{API}/agent/chat',json={{'message':{cau!r}}},headers=h);"
        "print(json.dumps({'http':r.status_code,'than':r.json()},ensure_ascii=False))"
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", ma],
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, f"gọi chat hỏng: {(r.stderr or r.stdout)[-400:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def hai_luot():
    """Bắn ĐÚNG HAI lượt cho cả ba test — lượt nhẹ 0 token, lượt đầy đủ 1 lượt LLM.

    `scope="module"` cố ý: ba test dùng chung hai lượt này. Bắn lại mỗi test là
    tiêu hạn mức cho cùng một quan sát, và tệ hơn — mỗi lần bắn là một lần GHI
    vào hệ (Luật 15), nên số lần bắn phải là số ít nhất đủ dùng.
    """
    ra = {}
    for ten, cau in (("nhe", CAU_DON), ("day_du", CAU_NGHIEP_VU)):
        t = _dem()
        j = _chat(cau)
        s = _dem()
        ra[ten] = {"tra": j, "truoc": t, "sau": s,
                   "delta": {k: s[k] - t[k] for k in t}}
    return ra


def test_luot_don_di_duong_NHE(hai_luot):
    """Điều kiện tiên quyết: `"alo"` phải THỰC SỰ đi đường nhẹ.

    Tách khỏi test Δ bên dưới vì nếu ca này hỏng thì Δ=0 ở dưới **không chứng
    minh gì** — nó chỉ nói "một lượt đường đầy đủ tình cờ không tạo vé".
    """
    o = hai_luot["nhe"]
    assert o["tra"]["http"] == 200, f"HTTP {o['tra']['http']}"
    assert o["tra"]["than"].get("duong") == "nhe", (
        f"{CAU_DON!r} đi {o['tra']['than'].get('duong')!r}, không phải 'nhe' — "
        "mọi assertion Δ bên dưới mất nghĩa."
    )
    u = o["tra"]["than"].get("usage") or {}
    assert u.get("so_luot_goi_model") == 0, f"đường nhẹ vẫn gọi model: {u}"
    assert (u.get("total_tokens") or 0) == 0, f"đường nhẹ vẫn tiêu token: {u}"


def test_duong_NHE_khong_tao_ban_ghi_nghiep_vu(hai_luot):
    """🔴 BẤT BIẾN CHÍNH: đường nhẹ ⟹ Δcomplaints = Δtickets = 0."""
    d = hai_luot["nhe"]["delta"]
    assert d == {k: 0 for k in BANG}, (
        f"đường nhẹ ĐÃ GHI vào bảng nghiệp vụ: {d}\n"
        "Một lượt cần tạo bản ghi thì tự nó đã không phải lượt đơn — việc nó đi "
        "được đường nhẹ chính là bằng chứng phân loại sai."
    )


def test_DOI_CHUNG_duong_day_du_VAN_tao_duoc_ban_ghi(hai_luot):
    """🔴 VẾ BẮT BUỘC (Luật 2) — thiếu nó thì bất biến trên vô nghĩa.

    Một cài đặt *"chặn mọi ghi"* làm test trên xanh **kể cả khi nó chặn nhầm cả
    đường đầy đủ** — tức chặn nhầm đúng những khiếu nại thật. Ca này chứng minh
    `Δ ≠ 0` **vẫn đạt tới được**.
    """
    o = hai_luot["day_du"]
    assert o["tra"]["than"].get("duong") == "day_du", (
        f"{CAU_NGHIEP_VU!r} đi {o['tra']['than'].get('duong')!r} — ca đối chứng "
        "không đi đúng đường thì nó không đối chứng cho cái gì cả."
    )
    d = o["delta"]
    assert sum(d.values()) > 0, (
        f"đường ĐẦY ĐỦ cũng KHÔNG ghi gì: {d}\n"
        "⟹ bất biến ở test trên xanh vì guardrail chặn TẤT CẢ, không phải vì nó "
        "chặn đúng chỗ. Không phân biệt được hai thứ đó thì cả bộ vô nghĩa."
    )


def test_dau_duong_PHAN_BIET_duoc_hai_duong(hai_luot):
    """Bản thân DẤU ĐƯỜNG cũng phải được canh (Luật 7 — thước cũng cần canh).

    Dấu luôn trả `"day_du"` ⟹ test đường-nhẹ đỏ vì lý do sai. Dấu luôn trả
    `"nhe"` ⟹ ca đối chứng đỏ vì lý do sai. Cả hai chế độ hỏng đều làm bộ test
    nói về một thứ khác thứ nó tưởng đang đo.
    """
    a = hai_luot["nhe"]["tra"]["than"].get("duong")
    b = hai_luot["day_du"]["tra"]["than"].get("duong")
    assert a != b, f"dấu `duong` trả CÙNG một giá trị {a!r} cho cả hai đường"
    assert {a, b} == {"nhe", "day_du"}, f"giá trị lạ: {a!r} · {b!r}"
