"""Quét TOÀN BỘ cặp vai × trang của giao diện, đối chiếu `contracts/authority-matrix.yaml`.

VÌ SAO CÓ TEST NÀY (lệnh PO 14/08): đã hai lần cùng một lớp lỗi lọt tới tay
người dùng — **guard route frontend HẸP HƠN contract**:
  1. Sếp không vào được `/policy-lookup` (đã vá `d0baf35`) trong khi
     `POST /policy-search` cho `[cskh, supervisor]`.
  2. CSKH không vào được `/report` trong khi `GET /reports/summary` cũng cho
     `[cskh, supervisor]`.
Cả hai đều bị phát hiện do có người TÌNH CỜ bấm phải. Hai lần là một pattern,
nên chuyển sang cho máy quét: mọi ô của ma trận đều được kiểm mỗi lần chạy.

Chiều NGƯỢC LẠI cũng được canh (guard RỘNG hơn contract = lỗ hổng thật, nặng
hơn nhiều): vai không có quyền mà mở được trang thì test đỏ ngay.

CÁCH ĐO: guard là **redirect 307 phía server** (đã xác minh 14/08 bằng curl:
`/report` với phiên CSKH → `307 → /dashboard`), nên chỉ cần HTTP + cookie,
không cần trình duyệt — nhanh và tất định.

CẦN STACK DOCKER SỐNG (`docker compose up -d`). Không tới được thì test tự
`skip` chứ không đỏ giả — cùng cách `tests/test_security/test_dependency_audit.py`
xử lý khi thiếu `pip-audit`.
"""
from __future__ import annotations

import pytest
import yaml

from tests._suite_day_du import can_ha_tang

httpx = pytest.importorskip("httpx")

BASE = "https://localhost"
MAT_KHAU_DEMO = "Demo@123"

# 4 tài khoản demo dùng chung mật khẩu (xem scripts/gen_dataset.py::TEST_ACCOUNT_USER_IDS).
SDT_THEO_VAI = {
    "customer": "0387000001",
    "cskh": "0353000201",
    "supervisor": "0905000205",
    "partner_admin": "0900000001",
}

# Trang giao diện -> route backend quyết định quyền vào trang đó.
# ĐÂY LÀ PHẦN CẦN NGƯỜI ĐỌC DUYỆT (ánh xạ trang→route là suy luận sản phẩm,
# không tự suy ra được từ contract) — để lộ thiên ở đây thay vì giấu trong
# code, ai đổi cũng thấy. Vai được vào trang = `roles` của route tương ứng
# trong contracts/authority-matrix.yaml.
TRANG_THEO_ROUTE = {
    "/chat": "POST /agent/chat",
    "/dashboard": "GET /tickets",
    "/report": "GET /reports/summary",
    "/policy-lookup": "POST /policy-search",
    "/knowledge": "GET /policy-docs",
    # `/approve` CỐ Ý neo vào route DUYỆT (supervisor), không neo vào
    # `GET /resolutions` (cskh cũng đọc được): mục đích của trang là RA QUYẾT
    # ĐỊNH chạm tiền, mở cho cskh là mời duyệt vượt quyền — ràng buộc cứng 1.
    "/approve": "POST /resolutions/{resolution_id}/approve",
}


def _roles_tu_contract() -> dict[str, list[str]]:
    with open("contracts/authority-matrix.yaml", encoding="utf-8") as f:
        mat = yaml.safe_load(f)
    return {r["route"]: (r.get("roles") or []) for r in mat["routes"]}


ROLES_ROUTE = _roles_tu_contract()


def _cho_phep(trang: str, vai: str) -> bool:
    route = TRANG_THEO_ROUTE[trang]
    assert route in ROLES_ROUTE, f"{route} không còn trong authority-matrix — ánh xạ trang đã lỗi thời"
    return vai in ROLES_ROUTE[route]


@pytest.fixture(scope="module")
def phien_theo_vai():
    """Đăng nhập 1 lần cho mỗi vai (rate-limit đăng nhập là 10/phút/số điện
    thoại — đừng đăng nhập lại cho từng ô của ma trận)."""
    try:
        httpx.get(f"{BASE}/login", verify=False, timeout=5)
    except Exception as e:  # noqa: BLE001
        can_ha_tang(
            f"Không tới được stack Docker ở {BASE} ({e!r})",
            cach_dung="`docker compose up -d`",
            allow_module_level=True,
        )

    phien = {}
    for vai, sdt in SDT_THEO_VAI.items():
        cli = httpx.Client(verify=False, timeout=30, follow_redirects=False)
        r = cli.post(f"{BASE}/api/session", json={"phone": sdt, "password": MAT_KHAU_DEMO})
        assert r.status_code == 200, f"đăng nhập {vai} ({sdt}) thất bại: {r.status_code} {r.text[:120]}"
        phien[vai] = cli
    yield phien
    for cli in phien.values():
        cli.close()


@pytest.mark.parametrize("trang", sorted(TRANG_THEO_ROUTE))
@pytest.mark.parametrize("vai", sorted(SDT_THEO_VAI))
def test_guard_trang_khop_authority_matrix(vai, trang, phien_theo_vai):
    """Mỗi ô của ma trận vai × trang: guard giao diện phải khớp ĐÚNG contract.

    - Contract cho phép mà trang chặn  -> chức năng chết âm thầm (2 lần đã xảy ra).
    - Contract cấm mà trang cho vào    -> lỗ hổng phân quyền.
    """
    cho_phep = _cho_phep(trang, vai)
    resp = phien_theo_vai[vai].get(f"{BASE}{trang}")
    vao_duoc = resp.status_code == 200
    dich = resp.headers.get("location", "")

    if cho_phep:
        assert vao_duoc, (
            f"'{vai}' PHẢI vào được {trang} theo contract "
            f"({TRANG_THEO_ROUTE[trang]} cho {ROLES_ROUTE[TRANG_THEO_ROUTE[trang]]}), "
            f"nhưng bị chặn: HTTP {resp.status_code} -> {dich or '(không rõ)'}. "
            f"Đây là lớp lỗi 'guard frontend hẹp hơn contract'."
        )
    else:
        assert not vao_duoc, (
            f"'{vai}' KHÔNG được phép vào {trang} theo contract "
            f"({TRANG_THEO_ROUTE[trang]} chỉ cho {ROLES_ROUTE[TRANG_THEO_ROUTE[trang]]}), "
            f"nhưng vẫn mở được (HTTP 200) — lỗ hổng phân quyền ở tầng giao diện."
        )
