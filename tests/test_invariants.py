"""tests/test_invariants.py — ràng buộc cứng FIN-05, dạng test chạy được thật.

KHÁC BIỆT CỐT LÕI so với cách viết test bất biến thông thường
------------------------------------------------------------
Cách thường gặp là quét `src/` bằng regex tìm tên hàm nghi vấn
(`def .*refund.*`, `def .*lock_wallet.*`). Cách đó tạo ra XANH GIẢ: nếu code
đặt tên khác (ở đây là `approve_resolution`, không phải `execute_refund`), regex
không khớp gì cả và test pass — pass vì KHÔNG TÌM THẤY GÌ ĐỂ KIỂM, không phải
vì code đúng. Một hàm mới vi phạm HITL vẫn lọt qua trọn vẹn.

File này làm ngược lại: **introspect thứ đang chạy thật rồi so khớp với
`contracts/`**.

  - Thẩm quyền  → đọc `app.routes`, lấy `allowed_roles` từ closure của
                  `require_role()` lúc runtime, so từng route với contract.
  - Trạng thái  → đọc `CheckConstraint` thật trong `src/db/models.py`,
                  so tập giá trị với contract.
  - Tool        → gọi thẳng `build_customer_tools()`, so tên tool với contract.

Hệ quả: thêm 1 route, đổi 1 guard, thêm 1 giá trị status, đổi tên 1 tool mà
quên cập nhật `contracts/` → ĐỎ NGAY. Không ai phải nhớ nhắc ai.

KHÔNG CÓ pytest.skip Ở ĐÂY. Thiếu contract, thiếu bảng, thiếu tool = ĐỎ, không
phải bỏ qua. Skip im lặng chính là cách một bộ test bất biến chết dần mà không
ai biết.

Nếu test đỏ: hoặc code sai, hoặc contract sai. KHÔNG sửa file này cho khớp code
— quay lại quy trình đổi contract ở CLAUDE.md §3.

CHẠY:  pytest tests/test_invariants.py -v
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
MODELS_PY = ROOT / "src" / "db" / "models.py"

# Phiên bản contract mà bộ test này được viết dựa trên.
# Lấy giá trị mới bằng: python scripts/check_contracts.py --stamp <file>
CONTRACT_VERSION = {
    "authority-matrix.yaml": "b185242c0d53",  # v2.1.0 — ADR-044 (GET /tickets/{ticket_id}/transcript)
    "resolution-state-machine.yaml": "a39f2b84ec5d",  # v2.5.0 — ADR-024 (resolutions.note + note_flagged + INV-17)
    "agent-tools.yaml": "df6e7c9353d3",  # v2.2.0 — ADR-051 create_ticket HAI THÌ (+input `xac_nhan`, output dict→chuỗi)
}


# ===========================================================================
# Tiện ích nạp contract — thiếu file là ĐỎ, không skip
# ===========================================================================

def load_contract(name: str) -> dict:
    path = CONTRACTS / name
    assert path.exists(), (
        f"Thiếu contract {name}. Đây là nguồn sự thật của dự án — "
        f"không có nó thì tester/security đang làm việc trên thông tin rỗng."
    )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def authority() -> dict:
    return load_contract("authority-matrix.yaml")


@pytest.fixture(scope="module")
def fsm() -> dict:
    return load_contract("resolution-state-machine.yaml")


@pytest.fixture(scope="module")
def tools_contract() -> dict:
    return load_contract("agent-tools.yaml")


# ===========================================================================
# Introspect APP ĐANG CHẠY — nguồn sự thật phía code
# ===========================================================================

def _roles_from_dependency(dep) -> list[str] | None:
    """Moi `allowed_roles` ra khỏi closure của require_role(*allowed_roles).

    `require_role` trả về hàm nội bộ tên `_dep`; các role được giữ trong
    closure cell chứ không phải attribute, nên phải đọc qua __closure__.
    """
    if getattr(dep, "__name__", "") != "_dep":
        return None
    if not getattr(dep, "__closure__", None):
        return None
    free = dep.__code__.co_freevars
    cells = {k: c.cell_contents for k, c in zip(free, dep.__closure__)}
    roles = cells.get("allowed_roles")
    return sorted(roles) if roles else None


def _live_routes() -> dict[str, dict]:
    """Bảng route THẬT của app đang chạy: {"POST /path": {roles, extra}}."""
    from src.api.main import app

    out: dict[str, dict] = {}
    for r in app.routes:
        if not hasattr(r, "endpoint"):
            continue
        if r.path.startswith(("/openapi", "/docs", "/redoc")):
            continue
        methods = sorted(r.methods - {"HEAD", "OPTIONS"}) if hasattr(r, "methods") else ["WS"]

        roles: list[str] | None = None
        extra: list[str] = []
        for _, p in inspect.signature(r.endpoint).parameters.items():
            if p.default is inspect.Parameter.empty:
                continue
            dep = getattr(p.default, "dependency", None)
            if dep is None:
                continue
            found = _roles_from_dependency(dep)
            if found:
                roles = found
            name = getattr(dep, "__name__", "")
            if name in ("require_otp_verified", "get_current_user"):
                extra.append(name)

        for m in methods:
            out[f"{m} {r.path}"] = {"roles": roles, "extra": sorted(set(extra))}
    return out


def _contract_routes(authority: dict) -> dict[str, dict]:
    return {
        entry["route"]: {
            "roles": entry.get("roles", []),
            "extra": sorted(entry.get("extra", [])),
            "cham_tien": bool(entry.get("cham_tien")),
        }
        for entry in authority["routes"]
    }


def _normalize_live_roles(info: dict) -> list[str]:
    """Đưa dạng runtime về đúng từ vựng contract."""
    if info["roles"] is not None:
        return info["roles"]
    if "get_current_user" in info["extra"]:
        return ["any_authenticated"]
    return []


# ===========================================================================
# BẤT BIẾN LỚP 0 — contract có khớp app đang chạy không
# Đây là test quan trọng nhất file này. Mọi test còn lại chỉ có ý nghĩa khi
# test này xanh, vì nếu contract đã lệch code thì kiểm contract là kiểm hư không.
# ===========================================================================

def test_authority_matrix_khop_app_dang_chay(authority):
    """INV-00 · contracts/authority-matrix.yaml phải khớp CHÍNH XÁC app.routes."""
    live = _live_routes()
    contract = _contract_routes(authority)

    thieu_trong_contract = sorted(set(live) - set(contract))
    thua_trong_contract = sorted(set(contract) - set(live))

    loi = []
    if thieu_trong_contract:
        loi.append(
            "Route CÓ trong code nhưng THIẾU trong contract "
            "(ai đó thêm route mà không cập nhật nguồn sự thật):\n    "
            + "\n    ".join(thieu_trong_contract)
        )
    if thua_trong_contract:
        loi.append(
            "Route CÓ trong contract nhưng KHÔNG còn trong code "
            "(contract đang mô tả thứ đã bị xoá):\n    "
            + "\n    ".join(thua_trong_contract)
        )

    for key in sorted(set(live) & set(contract)):
        thuc_te = _normalize_live_roles(live[key])
        khai_bao = sorted(contract[key]["roles"])
        if thuc_te != khai_bao:
            loi.append(f"{key}: code cho phép {thuc_te}, contract khai báo {khai_bao}")

        extra_live = [e for e in live[key]["extra"] if e == "require_otp_verified"]
        extra_ct = [e for e in contract[key]["extra"] if e == "require_otp_verified"]
        if extra_live != extra_ct:
            loi.append(f"{key}: OTP step-up — code {extra_live}, contract {extra_ct}")

    assert not loi, (
        "CONTRACT ĐÃ LỆCH KHỎI CODE ĐANG CHẠY:\n\n  "
        + "\n\n  ".join(loi)
        + "\n\n→ Đây chính là loại lệch khiến tester/security làm việc trên thông tin chết."
        "\n→ Sửa contracts/authority-matrix.yaml (kèm ADR), KHÔNG sửa test này."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 1 — HITL tuyệt đối
# ===========================================================================

def test_inv01_route_cham_tien_chi_supervisor(authority):
    """INV-01 · mọi route cham_tien=true chỉ được mở cho đúng supervisor."""
    vi_pham = [
        f"{e['route']}: roles={e.get('roles')}"
        for e in authority["routes"]
        if e.get("cham_tien") and sorted(e.get("roles", [])) != ["supervisor"]
    ]
    assert not vi_pham, (
        "Route chạm tiền mở cho role khác supervisor:\n  "
        + "\n  ".join(vi_pham)
        + "\nVi phạm HITL tuyệt đối (CLAUDE.md §2.1, ADR-002)."
    )


def test_inv02_khong_route_cham_tien_nao_mo_cho_customer_hoac_cskh(authority):
    """INV-02 · AI gọi tool dưới danh nghĩa customer → chặn customer là chặn AI."""
    xau = [
        f"{e['route']}: {r}"
        for e in authority["routes"]
        if e.get("cham_tien")
        for r in e.get("roles", [])
        if r in ("customer", "cskh", "any_authenticated")
    ]
    assert not xau, f"Route chạm tiền lọt cho role không được phép: {xau}"


def test_inv03_route_duyet_reject_khong_bao_gio_mo_cho_cskh(authority):
    """INV-03 · CSKH điều tra và đề xuất, KHÔNG quyết."""
    ct = _contract_routes(authority)
    for key, info in ct.items():
        if re.search(r"/resolutions/\{[^}]+\}/(approve|reject)$", key):
            assert info["roles"] == ["supervisor"], (
                f"{key} mở cho {info['roles']} — CSKH không được duyệt/từ chối "
                "(CLAUDE.md §2.2)."
            )


def test_inv04_tham_quyen_khong_phu_thuoc_han_muc_tien(authority):
    """INV-04 · 'ngoài thẩm quyền' định nghĩa theo ROLE, không theo số tiền."""
    cam = re.compile(r"(han_muc|limit|threshold|nguong_tien|max_amount)", re.I)
    xau = [
        f"{e['route']}: {k}"
        for e in authority["routes"]
        for k in e.keys()
        if cam.search(str(k))
    ]
    assert not xau, (
        f"Route có điều kiện theo hạn mức tiền: {xau}. "
        "Thẩm quyền phải theo role. Muốn đổi → ghi ADR trước (PRD §4.6)."
    )


def test_inv11_partner_admin_chi_cham_duoc_policy_docs(authority):
    """INV-11 · least-privilege cho vai đối tác — không chạm ticket/tiền/khách."""
    ngoai_pham_vi = [
        e["route"]
        for e in authority["routes"]
        if "partner_admin" in e.get("roles", [])
        and not e["route"].split(" ", 1)[1].startswith("/policy-docs")
    ]
    assert not ngoai_pham_vi, (
        f"partner_admin chạm được route ngoài /policy-docs: {ngoai_pham_vi}. "
        "Vai đối tác không được thấy dữ liệu khách hàng."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 1 (lớp DB) — HITL ép ở tầng database, không chỉ tầng code
# ===========================================================================

def _check_constraints() -> dict[str, str]:
    """Đọc mọi CheckConstraint(name=...) thật trong models.py qua AST.

    Dùng AST thay vì regex: bắt đúng cấu trúc lời gọi, không ăn nhầm chuỗi
    trong docstring/comment.
    """
    tree = ast.parse(MODELS_PY.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if getattr(fn, "id", None) != "CheckConstraint" and getattr(fn, "attr", None) != "CheckConstraint":
            continue
        bieu_thuc = ""
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                bieu_thuc += arg.value
            elif isinstance(arg, ast.JoinedStr):
                bieu_thuc += "".join(
                    v.value for v in arg.values if isinstance(v, ast.Constant) and isinstance(v.value, str)
                )
        ten = None
        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                ten = kw.value.value
        if ten:
            out[ten] = bieu_thuc
    return out


# 🔴 ĐÍNH CHÍNH 26/08 — audit "cổng canh có thật đỏ khi ràng buộc hỏng
# không" (PO giao, hậu phát hiện). Bản CŨ của INV-07/INV-14(BR-11) chỉ kiểm
# 2-3 substring "...isnotnull" ĐỘC LẬP — đổi `AND` thành `OR` (chỉ cần MỘT
# cột khác NULL, không phải CẢ HAI/CẢ BA) vẫn giữ nguyên các chuỗi con, test
# vẫn XANH dù ràng buộc HITL đã bị gỡ một nửa. ĐÃ ĐO bằng git worktree riêng
# (không đụng cây chung, xoá ngay sau đo): sửa AND->OR thật trong models.py,
# chạy lại bản test CŨ này -> PASS (sai) cho cả BR-10 lẫn BR-11, và INV-08
# (forbidden_tools rỗng) -> PASS (sai) tương tự.
#
# CHUẨN PHẢI ĐỌC TỪ `contracts/`, KHÔNG TỪ `models.py` (PO chỉ ra 26/08, sau
# khi bản vá đầu của tôi hardcode đúng chuỗi vừa đọc trong models.py — tự so
# code với chính nó, luôn xanh, chứng minh 0, và trông chặt hơn bản cũ nên
# còn NGUY HIỂM HƠN vì tạo niềm tin giả). BR-10 CÓ `bieu_thuc` khai sẵn ở
# `resolution-state-machine.yaml::resolution.invariant_db` — đọc ĐỘNG từ đó,
# đúng khuôn INV-15/BR-12 ngay dưới. BR-11 KHÔNG có `bieu_thuc` ở bất kỳ đâu
# trong contract (đã tìm toàn file) — lỗ ĐỐI XỨNG thật với BR-10/BR-12, Lead
# đang soạn ADR bổ sung qua §3 (PO duyệt, tech-lead sửa contracts/ — không
# phải việc của tester). Cho tới lúc đó, INV-14 hardcode TẠM bên dưới, niêm
# rõ tại chỗ — không coi đây là điểm dừng cuối.
def test_inv07_check_constraint_br10_ton_tai(fsm):
    """INV-07 · lớp phòng thủ cuối của HITL nằm trong DB, không phải trong if.

    Đây là ràng buộc mạnh nhất của cả hệ thống: kể cả một câu UPDATE viết tay
    lách qua toàn bộ tầng application, database vẫn từ chối tạo ra một
    resolution 'approved' không có người duyệt.
    """
    cons = _check_constraints()
    ten = fsm["resolution"]["invariant_db"]["ten"]
    assert ten in cons, (
        f"MẤT CHECK constraint {ten} trong src/db/models.py.\n"
        "Đây là lớp phòng thủ cuối cùng của HITL — không có nó, một UPDATE "
        "trực tiếp vào DB có thể tạo resolution 'approved' không người duyệt."
    )
    thuc_te = re.sub(r"\s+", "", cons[ten])
    khai_bao = re.sub(r"\s+", "", fsm["resolution"]["invariant_db"]["bieu_thuc"])
    assert thuc_te == khai_bao, (
        f"{ten} LỆCH giữa contract và code (kiểm TOÀN BỘ biểu thức, không chỉ "
        f"từng cột NOT NULL rời rạc — AND đổi thành OR vẫn giữ nguyên các cột "
        f"này nhưng làm yếu hẳn ràng buộc):\n"
        f"  contract khai: {fsm['resolution']['invariant_db']['bieu_thuc']}\n"
        f"  models.py có : {cons[ten]}"
    )


def test_inv14_check_constraint_br11_ton_tai():
    """INV-14 · nhánh TỪ CHỐI cũng phải có lớp phòng thủ cuối ở DB.

    Đối xứng với INV-07 của nhánh duyệt. Vì sao từ chối cũng cần ràng buộc
    cứng dù nó KHÔNG chạm tiền: `reject_reason` là đầu vào của vòng học
    (Phase 2 — chỉ case có `la_tin_hieu_hoc: true` mới được kết xuất thành ứng
    viên eval). Một resolution 'rejected' trống lý do không chỉ mất vết audit,
    nó còn lọt vào bộ đo như một mẫu không phân loại được — hỏng chính cái
    thước dùng để chấm cải tiến agent.

    🔴 TẠM — 26/08. Contract THIẾU `bieu_thuc` cho BR-11 (khác BR-10/BR-12,
    xem ghi chú ĐÍNH CHÍNH phía trên) nên biểu thức mong đợi phải hardcode ở
    đây, không có nguồn nào khác để so. Chuyển sang đọc động theo đúng khuôn
    INV-07/INV-15 NGAY khi Lead/PO đóng ADR bổ sung `bieu_thuc` cho BR-11 vào
    `resolution-state-machine.yaml` qua §3 — đừng để hardcode này sống mãi.
    """
    _BR11_BIEU_THUC_MONG_DOI_TAM = (
        "(status != 'rejected') OR (reject_reason IS NOT NULL "
        "AND rejected_by IS NOT NULL AND rejected_at IS NOT NULL)"
    )
    cons = _check_constraints()
    ten = "ck_resolutions_rejected_requires_reason_br11"
    assert ten in cons, (
        f"MẤT CHECK constraint {ten} trong src/db/models.py.\n"
        "INV-14 (ADR-019, BR-11) — không có nó, một UPDATE trực tiếp có thể "
        "tạo resolution 'rejected' không lý do, không người từ chối."
    )
    thuc_te = re.sub(r"\s+", "", cons[ten])
    khai_bao = re.sub(r"\s+", "", _BR11_BIEU_THUC_MONG_DOI_TAM)
    assert thuc_te == khai_bao, (
        f"{ten} LỆCH khỏi biểu thức TẠM mong đợi (kiểm TOÀN BỘ, không chỉ "
        f"từng cột NOT NULL rời rạc — cùng lỗ AND->OR đã đo ở BR-10):\n"
        f"  mong đợi (TẠM, hardcode — chờ contract bổ sung bieu_thuc BR-11): "
        f"{_BR11_BIEU_THUC_MONG_DOI_TAM}\n"
        f"  thực tế  : {cons[ten]}"
    )


def test_inv15_check_constraint_br12_ton_tai_va_khop_bieu_thuc_contract(fsm):
    """INV-15 · maker-checker phải CÒN ĐÓ, và đúng BIỂU THỨC contract khai.

    Hoàn tất bộ ba cùng INV-07 (nhánh approve) và INV-14 (nhánh reject). Vì sao
    cần vế "hiện diện" riêng dù đã có test hành vi
    (`tests/test_migrations/test_check_constraints_hitl.py`): test hành vi
    chứng minh ràng buộc ĐANG chạy hôm nay; INV này chứng minh nó vẫn CÒN ĐÓ
    ngày mai.

    SO BIỂU THỨC LẤY TỪ CONTRACT, KHÔNG HARDCODE — điểm thiết kế quan trọng
    nhất ở đây. BR-12 đang sắp mở rộng sang nhánh từ chối (F-18, dạng C). Nếu
    test này hardcode biểu thức:
      - khai bản CŨ  -> sau khi coder mở rộng, test vẫn XANH trong khi nó chỉ
        còn canh một nửa ràng buộc (chuỗi cũ là chuỗi con của dạng C!);
      - khai bản MỚI -> đỏ suốt từ giờ tới lúc F-18 áp, một đỏ không nói lên
        điều gì ngoài "chưa tới lượt".
    Đọc từ contract thì test tự đúng ở cả hai thời điểm, và bắt được đúng thứ
    đáng bắt: **models.py và contract lệch nhau**. Sửa một bên quên bên kia là
    ĐỎ, dù bên nào đi trước.
    """
    cons = _check_constraints()
    ten = fsm["resolution"]["invariant_db_maker_checker"]["ten"]
    assert ten in cons, (
        f"MẤT CHECK constraint {ten} trong src/db/models.py.\n"
        "BR-12 (ADR-020): người ĐỀ XUẤT không được là người DUYỆT. Không có nó, "
        "một supervisor đi trọn cả hai đầu và HITL chỉ còn là thao tác hai bước "
        "của cùng một người — mọi test quyền hạn vẫn xanh vì không ai vượt quyền."
    )

    khai_bao = re.sub(r"\s+", "", fsm["resolution"]["invariant_db_maker_checker"]["bieu_thuc"])
    thuc_te = re.sub(r"\s+", "", cons[ten])
    assert thuc_te == khai_bao, (
        f"{ten} LỆCH giữa contract và code:\n"
        f"  contract khai: {fsm['resolution']['invariant_db_maker_checker']['bieu_thuc']}\n"
        f"  models.py có : {cons[ten]}\n"
        "→ Sửa một bên mà quên bên kia. Nếu đây là đợt mở rộng sang nhánh từ chối "
        "(F-18), phải cập nhật ĐỦ CẢ BA nơi: models.py, migration, và `bieu_thuc` "
        "trong contract."
    )


def test_inv14_taxonomy_reject_reason_phan_hoach_du_cho_vong_hoc(fsm):
    """INV-14 (phần contract) · mọi lý do từ chối phải khai `la_tin_hieu_hoc`.

    Đây là cờ quyết định case có được bơm vào bộ eval Phase 2 hay không. Một
    giá trị mới thêm vào mà QUÊN khai cờ sẽ mặc nhiên bị coi là falsy ở chỗ
    dùng — tức im lặng biến mất khỏi vòng học, không ai thấy. Bắt tại đây thay
    vì chờ phát hiện qua việc bộ đo thiếu mẫu.
    """
    values = fsm["resolution"]["reject_reason"]["values"]
    thieu = [k for k, v in values.items() if "la_tin_hieu_hoc" not in (v or {})]
    assert not thieu, f"Lý do từ chối chưa khai `la_tin_hieu_hoc`: {thieu}"

    hoc_duoc = {k for k, v in values.items() if v["la_tin_hieu_hoc"]}
    assert hoc_duoc, "Không lý do nào là tín hiệu học — vòng học Phase 2 sẽ không có đầu vào."
    assert hoc_duoc != set(values), (
        "MỌI lý do đều là tín hiệu học — kể cả 'trùng case'/'khách rút', là những "
        "trường hợp đề xuất KHÔNG hề sai. Trộn chúng vào sẽ bơm nhiễu vào bộ đo "
        "(xem `ghi_chu` của reject_reason)."
    )


def test_inv14_ranh_gioi_thieu_can_cu_khac_han_need_more_info(fsm):
    """Ranh giới 'sai hẳn' vs 'sửa được' — hai đường phải TÁCH BẠCH.

    `thieu_can_cu` (từ chối) và `need_more_info` (trả lại cho CSKH bổ sung) rất
    dễ bị lẫn vì mô tả nghe giống nhau. Lẫn là mất khả năng phân biệt đề xuất
    SAI với đề xuất CHƯA ĐỦ — nhóm sau không phải lỗi agent, tính vào vòng học
    là dạy sai. Contract phải giữ chúng ở hai trục khác nhau.
    """
    trang_thai_resolution = set(fsm["resolution"]["status"]["values"])
    assert "need_more_info" not in trang_thai_resolution, (
        "'need_more_info' xuất hiện trong resolution.status — nó PHẢI chỉ nằm ở "
        "trục ticket.hitl_status. Gộp vào là xoá mất ranh giới sửa-được/sai-hẳn."
    )
    assert "need_more_info" in set(fsm["ticket_hitl_status"]["values"]), (
        "'need_more_info' biến mất khỏi ticket.hitl_status — mất đường trả case "
        "ngược cho CSKH, sếp chỉ còn lựa chọn từ chối hẳn."
    )
    assert "thieu_can_cu" in fsm["resolution"]["reject_reason"]["values"], (
        "Mất lý do 'thieu_can_cu' — không còn phân biệt được thiếu căn cứ với "
        "sai số liệu/sai phân loại."
    )
    ranh_gioi = fsm["resolution"]["reject_reason"]["values"]["thieu_can_cu"].get("ranh_gioi") or ""
    assert "need_more_info" in ranh_gioi, (
        "Mục `ranh_gioi` của 'thieu_can_cu' không còn trỏ sang đường "
        "need_more_info — đây là chỗ DUY NHẤT trong contract dặn người dùng "
        "đừng lẫn hai đường. Mất nó là mất luôn lời cảnh báo."
    )


def test_inv12_gia_tri_status_trong_contract_khop_check_constraint_that(fsm):
    """INV-12 · contract không được mô tả trạng thái mà DB không chấp nhận."""
    cons = _check_constraints()
    loi = []

    kiem_tra = [
        (fsm["resolution"]["status"]["rang_buoc_db"],
         set(fsm["resolution"]["status"]["values"].keys()),
         "resolution.status"),
        (fsm["resolution"]["action_type"]["rang_buoc_db"],
         set(fsm["resolution"]["action_type"]["values"].keys()),
         "resolution.action_type"),
        (fsm["ticket_hitl_status"]["rang_buoc_db"],
         set(fsm["ticket_hitl_status"]["values"]),
         "ticket.hitl_status"),
        (fsm["ticket_partner_wait_status"]["rang_buoc_db"],
         {str(v) for v in fsm["ticket_partner_wait_status"]["values"]},
         "ticket.partner_wait_status"),
        # Thêm 14/08 cùng v2.1.0: taxonomy reject_reason cũng khai
        # `rang_buoc_db` nên phải chịu chung luật chống drift của INV-12 —
        # thiếu dòng này thì thêm/xoá một lý do từ chối trong contract mà quên
        # sửa CHECK (hoặc ngược lại) sẽ KHÔNG ai bắt được.
        (fsm["resolution"]["reject_reason"]["rang_buoc_db"],
         set(fsm["resolution"]["reject_reason"]["values"].keys()),
         "resolution.reject_reason"),
    ]

    for ten_cons, khai_bao, nhan in kiem_tra:
        if ten_cons not in cons:
            loi.append(f"{nhan}: thiếu CheckConstraint '{ten_cons}' trong models.py")
            continue
        thuc_te = set(re.findall(r"'([^']+)'", cons[ten_cons]))
        if thuc_te != khai_bao:
            loi.append(
                f"{nhan}: DB cho phép {sorted(thuc_te)}, contract khai báo {sorted(khai_bao)}"
            )

    assert not loi, "Contract lệch CHECK constraint thật:\n  " + "\n  ".join(loi)


def test_inv05_chi_supervisor_dua_duoc_resolution_sang_approved(fsm):
    """INV-05 · cửa duy nhất tới 'approved' phải do supervisor giữ."""
    toi_approved = [t for t in fsm["resolution"]["transitions"] if t["to"] == "approved"]
    assert toi_approved, "Không còn transition nào tới 'approved' — luồng duyệt bị tắc?"
    for t in toi_approved:
        assert t["boi"] == ["supervisor"], (
            f"Transition {t['from']}→approved cho phép {t['boi']} — chỉ supervisor được duyệt."
        )
        assert t["from"] == "pending_approval", (
            f"Có đường tắt tới 'approved' từ '{t['from']}' — mọi thứ phải qua pending_approval."
        )
        # 🔴 ĐÍNH CHÍNH 26/08 — audit "cổng canh có thật đỏ khi ràng buộc hỏng
        # không". INV-06 (ngay dưới) chỉ lọc transition CÓ `cham_tien=true`
        # rồi kiểm `boi`; nếu ai lỡ xoá `cham_tien: true` khỏi ĐÚNG transition
        # tiền-thật này (pending_approval→approved), vòng lọc của INV-06 còn
        # 0 phần tử và nó xanh trơn — không có test nào khác trong file bắt
        # được việc rớt cờ. ĐÃ ĐO bằng git worktree riêng (xoá ngay sau đo,
        # không đụng contracts/ that): xoá `cham_tien: true` khỏi transition
        # này trong contract, chạy lại CẢ INV-05 (bản trước dòng assert này)
        # LẪN INV-06 -> cả hai PASS (sai). Vá tại đây, không phải INV-06, vì
        # INV-05 đã có sẵn biến `t` trỏ đúng transition tiền-thật cần canh.
        assert t.get("cham_tien") is True, (
            f"Transition {t['from']}→approved KHÔNG khai `cham_tien: true` — đây "
            "chính là hành động chạm tiền thật của cả hệ thống (duyệt hoàn tiền/"
            "điều chỉnh sổ cái). Thiếu cờ này, INV-06 (transition chạm tiền chỉ "
            "do supervisor) không còn thấy transition này để canh, và cổng "
            "'chạm tiền chỉ do supervisor' mất tác dụng ngay trên chính giao "
            "dịch tiền quan trọng nhất."
        )


def test_inv06_transition_cham_tien_chi_boi_supervisor(fsm):
    """INV-06 · không transition chạm tiền nào do role khác thực hiện."""
    xau = [
        f"{t['from']}→{t['to']} bởi {t['boi']}"
        for t in fsm["resolution"]["transitions"]
        if t.get("cham_tien") and t.get("boi") != ["supervisor"]
    ]
    assert not xau, f"Transition chạm tiền không do supervisor: {xau}"


# ===========================================================================
# RÀNG BUỘC CỨNG 2 + 3 — AI không vượt cấp · cấm bịa số liệu
# ===========================================================================

def _live_tool_names() -> list[str]:
    """Gọi thẳng build_customer_tools() để lấy danh sách tool THẬT."""
    from unittest.mock import MagicMock

    from src.agents.tools.customer_tools import build_customer_tools

    tools = build_customer_tools(MagicMock(), user_id="USR-TEST", otp_verified_at=None)
    return sorted(t.name for t in tools)


def test_inv09_danh_sach_tool_khop_code_dang_chay(tools_contract):
    """INV-09 · contract tool phải khớp CHÍNH XÁC build_customer_tools()."""
    thuc_te = set(_live_tool_names())
    khai_bao = set(tools_contract["tools"].keys())

    thieu = sorted(thuc_te - khai_bao)
    thua = sorted(khai_bao - thuc_te)

    loi = []
    if thieu:
        loi.append(f"Tool CÓ trong code nhưng THIẾU trong contract: {thieu}")
    if thua:
        loi.append(f"Tool CÓ trong contract nhưng KHÔNG tồn tại trong code: {thua}")

    assert not loi, (
        "\n  ".join(loi)
        + "\n→ Tester sinh testcase từ contract này. Lệch = test cho sản phẩm tưởng tượng."
    )


def test_inv08_khong_tool_bi_cam_nao_ton_tai(tools_contract):
    """INV-08 · tool trong forbidden_tools không được xuất hiện dưới mọi hình thức."""
    cam = {f["ten"] for f in tools_contract["forbidden_tools"]}
    # 🔴 ĐÍNH CHÍNH 26/08 — thiếu dòng này thì `agent-tools.yaml` lỡ có
    # `forbidden_tools: []` (merge lỗi, sửa nhầm) làm cả hai lượt kiểm bên
    # dưới (giao tập hợp + quét regex `def <tên>(`) chạy trên tập RỖNG — xanh
    # tuyệt đối, không còn chặn `execute_refund`/`approve_resolution`/
    # `lock_wallet`/... gì cả, trong khi chính docstring test này gọi đây là
    # "vi phạm ràng buộc cứng nghiêm trọng nhất của dự án". ĐÃ ĐO bằng git
    # worktree riêng: xoá rỗng forbidden_tools thật trong contract, chạy lại
    # bản test CŨ (không có dòng assert này) -> PASS (sai). Mẫu chống-rỗng
    # này COPY từ `test_inv10_tool_doc_du_lieu_nhay_cam_deu_kiem_otp` ngay
    # dưới (`assert can_otp`) — cùng file đã có sẵn, chỉ chưa áp ở đây.
    assert cam, "forbidden_tools rỗng — contract không còn liệt kê tool nào bị cấm, cổng này mất tác dụng."
    thuc_te = set(_live_tool_names())
    lot = sorted(cam & thuc_te)
    assert not lot, (
        f"TOOL BỊ CẤM ĐÃ ĐƯỢC TẠO: {lot}. "
        "Đây là vi phạm ràng buộc cứng nghiêm trọng nhất của dự án."
    )

    # Chặn cả ở tầng định nghĩa hàm — kể cả khi chưa gắn vào agent.
    #
    # PHẠM VI QUÉT CÓ CHỦ ĐÍCH: chỉ `src/agents/`. Không quét cả `src/` vì
    # `src/api/main.py::approve_resolution` là ROUTE HỢP LỆ của supervisor —
    # chính là thứ HITL yêu cầu phải tồn tại. Điều bị cấm là AI có TOOL trùng
    # tên đó, không phải hệ thống có route đó. Quét cả src/ sẽ biến một thiết
    # kế đúng thành lỗi giả, và test đỏ sai sẽ sớm bị vô hiệu hoá.
    agents_dir = ROOT / "src" / "agents"
    assert agents_dir.is_dir(), "Không tìm thấy src/agents/ — test này phải chạy ở gốc repo."
    vi_pham = []
    for p in agents_dir.rglob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for ten in cam:
            if re.search(rf"^\s*def\s+{re.escape(ten)}\s*\(", text, re.M):
                vi_pham.append(f"{p.relative_to(ROOT)}::{ten}")
    assert not vi_pham, f"Hàm trùng tên tool bị cấm trong src/agents/: {vi_pham}"


def test_inv10_tool_doc_du_lieu_nhay_cam_deu_kiem_otp(tools_contract):
    """INV-10 · tool chạm dữ liệu khách phải chặn khi thiếu/hết hạn OTP."""
    from unittest.mock import MagicMock

    from src.agents.tools.customer_tools import build_customer_tools

    can_otp = sorted(t for t, spec in tools_contract["tools"].items() if spec.get("yeu_cau_otp"))
    assert can_otp, "Contract không khai báo tool nào cần OTP — nghi vấn contract sai."

    # Tham số TỐI THIỂU HỢP LỆ cho từng tool — phải qua được validation của
    # pydantic thì mới chạm tới bước kiểm OTP bên trong. Truyền {} sẽ chết ở
    # ValidationError và test hoá ra kiểm nhầm thứ khác.
    tham_so_toi_thieu: dict[str, dict] = {
        "lookup_transaction": {"trans_id": "TXN-KHONG-CO-THAT"},
        "get_customer_history": {},
        "create_ticket": {
            "complaint_type": "refund",
            "scope": "unknown",
            "description_raw": "kiểm tra bất biến OTP",
        },
    }

    tools = {t.name: t for t in build_customer_tools(MagicMock(), user_id="USR-TEST", otp_verified_at=None)}
    lot = []
    for ten in can_otp:
        assert ten in tools, f"Contract khai báo tool '{ten}' cần OTP nhưng tool không tồn tại."
        assert ten in tham_so_toi_thieu, (
            f"Tool '{ten}' khai báo cần OTP trong contract nhưng test chưa có bộ tham số "
            f"tối thiểu để gọi thử. Bổ sung vào `tham_so_toi_thieu`."
        )
        ket_qua = tools[ten].invoke(tham_so_toi_thieu[ten])
        if not (isinstance(ket_qua, dict) and ket_qua.get("status") == "error"):
            lot.append(f"{ten} → {ket_qua!r}")

    assert not lot, (
        "Tool trả DỮ LIỆU khi chưa xác thực OTP:\n  "
        + "\n  ".join(lot)
        + "\nVi phạm CLAUDE.md §2.4."
    )


def test_inv13_co_che_truy_vet_chong_bia_so_con_nguyen(tools_contract):
    """INV-13 · bảng/cột dùng để đối chiếu số liệu phải còn tồn tại."""
    from src.db import models

    assert hasattr(models, "ToolResult"), (
        "Mất model ToolResult — không còn nơi lưu nguyên văn kết quả tool để đối chiếu."
    )
    for cot in ("tool_name", "raw_json", "content_hash"):
        assert hasattr(models.ToolResult, cot), f"ToolResult mất cột {cot}"

    assert hasattr(models.Resolution, "cited_tool_result_ids"), (
        "Mất cột resolutions.cited_tool_result_ids — đề xuất không còn trích dẫn "
        "được nguồn số liệu, mở đường cho bịa số (CLAUDE.md §2.3)."
    )
    # InvestigationLog nối sang tool_results bằng FK `tool_result_id`
    # (KHÔNG phải `tool_call_ids` — cột đó nằm ở Message của live-chat).
    for cot in ("step_no", "tool_called", "tool_input_json", "tool_result_id"):
        assert hasattr(models.InvestigationLog, cot), (
            f"Mất cột investigation_logs.{cot} — đứt mắt xích truy vết từ kết luận "
            "về đúng kết quả tool đã sinh ra nó."
        )
    assert hasattr(models.Message, "tool_call_ids"), (
        "Mất cột messages.tool_call_ids — tin nhắn live-chat mất dấu vết tool."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 4 — xác thực
# ===========================================================================

def test_khong_bao_gio_hoi_mat_khau_hoac_otp_giao_dich_cua_khach():
    """Agent chỉ được dùng OTP PHIÊN LÀM VIỆC, không bao giờ hỏi OTP giao dịch."""
    prompt_path = ROOT / "src" / "agents" / "prompt.py"
    assert prompt_path.exists(), "Không tìm thấy src/agents/prompt.py"
    text = prompt_path.read_text(encoding="utf-8").lower()

    # Prompt PHẢI dặn rõ điều này — vắng mặt cũng là lỗi, không chỉ sai là lỗi.
    assert re.search(r"otp giao dịch|mật khẩu", text), (
        "System prompt không còn nhắc cấm hỏi mật khẩu / OTP giao dịch. "
        "Đây là ràng buộc cứng 4 — phải nằm tường minh trong prompt."
    )


def test_otp_step_up_cho_hanh_dong_co_hau_qua_van_con(authority):
    """create_ticket phải giữ require_otp_verified — không được nới lỏng âm thầm."""
    ct = _contract_routes(authority)
    key = "POST /tools/create_ticket"
    assert key in ct, f"Mất route {key}"
    assert "require_otp_verified" in ct[key]["extra"], (
        "create_ticket không còn yêu cầu OTP step-up — hành động có hậu quả "
        "bị hạ chuẩn xác thực (CLAUDE.md §2.4)."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 5 — gắn cờ gian lận ≠ khoá ví
# ===========================================================================

def test_inv_gan_co_gian_lan_khong_noi_sang_khoa_vi(fsm):
    """Hai hành động độc lập hoàn toàn, ở cả tầng contract lẫn tầng code."""
    assert fsm["fraud"]["chinh_sach_escalate"]["tin_hieu_kich_hoat"] == ["FS-06"], (
        "Chính sách escalate đã đổi khỏi phạm vi MVP (chỉ FS-06) mà chưa cập nhật "
        "contract — xem src/tools/fraud_policy.py."
    )

    fraud_files = [
        p for p in (ROOT / "src").rglob("*.py")
        if re.search(r"fraud|gian_lan", p.name, re.I)
    ]
    assert fraud_files, "Không tìm thấy module fraud nào trong src/ — nghi vấn bị xoá."

    # 🔴 ĐÍNH CHÍNH 26/08 — audit "cổng canh có thật đỏ không". Bản CŨ chỉ
    # quét DÒNG chứa "import"/"from" CÙNG một trong 3 từ cấm — một lời gọi
    # qua alias module (`import src.wallet_ops as wo` rồi `wo.lock_wallet(...)`
    # Ở CHỖ KHÁC trong file) có dòng gọi chứa "lock_wallet" thật, nhưng dòng
    # đó không có "import"/"from" nên KHÔNG khớp regex cũ — né hoàn toàn.
    # ĐÃ ĐO bằng git worktree riêng (xoá ngay sau đo, không đụng src/ thật):
    # thêm hàm gọi `client.lock_wallet(...)` không kèm dòng import nào chứa
    # từ cấm vào bản sao `fraud_policy.py` -> bản test CŨ vẫn PASS (sai).
    # Vá: bỏ ràng buộc "cùng dòng với import/from" — quét CẢ FILE cho 3 từ
    # cấm ở bất kỳ đâu (import, gọi qua alias, gọi trực tiếp).
    #
    # ⚠️ GIỚI HẠN CÒN LẠI, KHÔNG VÁ ĐƯỢC Ở TẦNG QUÉT TÊN: nếu hàm khoá ví
    # thật bị ĐỔI TÊN khỏi cả 3 từ khoá này (vd `lock_wallet` -> `set_locked`)
    # và không còn lời gọi/import nào nhắc tới 3 từ cấm, KHÔNG quét văn bản/
    # AST nào (kể cả bản vá này) bắt được — đây là giới hạn cố hữu của MỌI
    # cách so khớp theo TÊN, đúng cảnh báo ở đầu file (dòng 3-9). Đóng hẳn
    # lỗ này cần một ca HÀNH VI (gọi evaluate_escalation() thật với wallet đã
    # seed, assert wallet.status không đổi) — ngoài phạm vi file introspect
    # thuần này (không có DB session ở đây), đã báo riêng cho Lead/PO như một
    # đề xuất tách biệt, không tự ý mở rộng file này sang có DB.
    vi_pham = [
        str(p.relative_to(ROOT))
        for p in fraud_files
        if re.search(r"lock_wallet|khoa_vi|wallet_lock", p.read_text(encoding="utf-8", errors="ignore"), re.I)
    ]
    assert not vi_pham, (
        f"Module gian lận nhắc tới định danh khoá ví (import hoặc gọi qua alias): {vi_pham}. "
        "Dương tính giả sẽ làm khách hàng lương thiện mất quyền dùng tiền (CLAUDE.md §2.5)."
    )


def test_fraud_policy_chi_dinh_tuyen_khong_phan_quyet():
    """Tầng fraud chỉ quyết định CÓ ESCALATE HAY KHÔNG, không kết luận gian lận."""
    from src.tools.fraud_policy import evaluate_escalation

    khong_co_tin_hieu = evaluate_escalation([])
    assert khong_co_tin_hieu.should_escalate is False
    assert khong_co_tin_hieu.target is None

    co_fs06 = evaluate_escalation(["FS-06"])
    assert co_fs06.should_escalate is True
    assert co_fs06.target == "supervisor", (
        "FS-06 phải escalate tới supervisor, không tới đâu khác."
    )

    # Tín hiệu khác KHÔNG được tự ý kích hoạt escalate (phạm vi MVP).
    khac = evaluate_escalation(["FS-01", "FS-12"])
    assert khac.should_escalate is False, (
        "Tín hiệu ngoài FS-06 kích hoạt escalate — lệch khỏi phạm vi MVP đã chốt "
        "trong src/tools/fraud_policy.py. Nếu cố ý mở rộng, ghi ADR + sửa contract."
    )


# ===========================================================================
# META — bộ test này có còn khớp contract không
# ===========================================================================

def test_bo_test_nay_khong_loi_thoi():
    """Contract đổi mà test chưa rà lại → đỏ ở đây trước tiên."""
    import hashlib

    lech = []
    for ten, mong_doi in CONTRACT_VERSION.items():
        path = CONTRACTS / ten
        if not path.exists():
            lech.append(f"{ten}: không còn tồn tại")
            continue
        if mong_doi == "PLACEHOLDER":
            lech.append(
                f"{ten}: CONTRACT_VERSION chưa được đóng dấu. "
                f"Chạy: python scripts/check_contracts.py --stamp {ten}"
            )
            continue
        thuc_te = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]
        if thuc_te != mong_doi:
            lech.append(f"{ten}: test dựa trên @{mong_doi}, hiện tại @{thuc_te}")

    assert not lech, (
        "Bộ test này đã lỗi thời so với contract:\n  "
        + "\n  ".join(lech)
        + "\n→ Rà lại test theo contract mới, rồi cập nhật CONTRACT_VERSION ở đầu file."
    )
