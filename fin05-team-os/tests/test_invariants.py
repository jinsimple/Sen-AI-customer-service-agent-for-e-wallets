"""
tests/test_invariants.py — 5 ràng buộc cứng của FIN-05, dạng test chạy được.

Một dòng prompt "AI không bao giờ được tự duyệt hoàn tiền" là lời đề nghị: mô hình tuân ~95-99%.
Với sản phẩm tài chính, đó là hỏng. File này biến ràng buộc thành 100%.

Đây cũng là bằng chứng mạnh nhất khi pitch tuần 6: mở terminal, chạy pytest, các dòng xanh.

CHẠY:  pytest tests/test_invariants.py -v
CẦN:   pip install pytest pyyaml

Test ở đây chia hai lớp:
  Lớp 1 — kiểm chính contracts/ (chạy được ngay từ ngày 1, kể cả khi chưa có code)
  Lớp 2 — kiểm src/ có khớp contract không (tự skip khi src/ chưa tồn tại)

Quan trọng: KHÔNG sửa file này cho khớp code. Nếu test đỏ, code sai hoặc contract sai.
Xem CLAUDE.md §2.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="cần: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
SRC = ROOT / "src"

# Phiên bản contract mà bộ test này được viết dựa trên.
# Cập nhật bằng: python scripts/check_contracts.py --stamp <file>
CONTRACT_VERSION = {
    "authority-matrix.yaml": "cdc333ce54b3",
    "ticket-state-machine.yaml": "aeaadb7efab4",
    "agent-tools.yaml": "7ac1f7158fb1",
}


def load(name: str) -> dict:
    path = CONTRACTS / name
    if not path.exists():
        pytest.skip(f"chưa có {name}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def authority() -> dict:
    return load("authority-matrix.yaml")


@pytest.fixture(scope="module")
def fsm() -> dict:
    return load("ticket-state-machine.yaml")


@pytest.fixture(scope="module")
def tools() -> dict:
    return load("agent-tools.yaml")


def src_files() -> list[Path]:
    if not SRC.is_dir():
        return []
    exts = {".py", ".ts", ".tsx", ".js", ".jsx"}
    return [p for p in SRC.rglob("*") if p.is_file() and p.suffix in exts]


# ===========================================================================
# RÀNG BUỘC CỨNG 1 — HITL tuyệt đối
# ===========================================================================

def test_inv01_moi_hanh_dong_cham_tien_chi_supervisor(authority):
    """INV-01 · CLAUDE.md §2.1 — chỉ supervisor được allow ở action chạm tiền."""
    vi_pham = []
    for ten, act in authority["actions"].items():
        if not act.get("cham_tien"):
            continue
        for role in ("ai_agent", "cskh", "customer"):
            if act.get(role) == "allow":
                vi_pham.append(f"{ten}: {role}=allow")
    assert not vi_pham, (
        "Hành động chạm tiền bị mở cho role không phải supervisor:\n  "
        + "\n  ".join(vi_pham)
        + "\nĐây là vi phạm HITL tuyệt đối. Xem ADR-002."
    )


def test_inv01b_moi_action_cham_tien_deu_allow_cho_supervisor(authority):
    """Mặt còn lại: nếu không role nào duyệt được thì luồng nghiệp vụ tắc."""
    thieu = [t for t, a in authority["actions"].items()
             if a.get("cham_tien") and a.get("supervisor") != "allow"]
    assert not thieu, f"Action chạm tiền không có ai duyệt được: {thieu}"


def test_inv02_ai_agent_khong_allow_o_bat_ky_action_cham_tien(authority):
    """INV-02 · AI không bao giờ thực thi tài chính, kể cả propose_only cũng phải cân nhắc."""
    xau = [t for t, a in authority["actions"].items()
           if a.get("cham_tien") and a.get("ai_agent") == "allow"]
    assert not xau, f"AI agent được allow ở action chạm tiền: {xau}"


def test_inv04_tham_quyen_khong_phu_thuoc_so_tien(authority):
    """INV-04 · PRD §4.6 — 'ngoài thẩm quyền' định nghĩa theo role, không theo hạn mức."""
    cam = re.compile(r"(han_muc|limit|threshold|nguong_tien|max_amount)", re.I)
    xau = [t for t, a in authority["actions"].items()
           if any(cam.search(str(k)) for k in a.keys())]
    assert not xau, (
        f"Action có điều kiện theo hạn mức tiền: {xau}. "
        "Thẩm quyền phải định nghĩa theo role. Nếu thật sự cần đổi, ghi ADR trước."
    )


def test_inv01_src_khong_co_duong_thuc_thi_thieu_phe_duyet():
    """Lớp 2 — code thực thi tài chính phải yêu cầu bằng chứng phê duyệt của supervisor."""
    files = src_files()
    if not files:
        pytest.skip("chưa có src/ — test này bật khi tech-lead bắt đầu code")

    cham_tien = re.compile(r"def\s+(\w*(refund|hoan_tien|adjust_balance|dieu_chinh_so_du|execute_payout)\w*)\s*\(([^)]*)\)", re.I)
    thieu = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in cham_tien.finditer(text):
            ten_ham, _, tham_so = m.groups()
            if not re.search(r"(SupervisorApproval|approval|approved_by)", tham_so, re.I):
                thieu.append(f"{p.relative_to(ROOT)}::{ten_ham}")
    assert not thieu, (
        "Hàm thực thi tài chính không nhận bằng chứng phê duyệt của supervisor:\n  "
        + "\n  ".join(thieu)
        + "\nRàng buộc phải nằm trong KIỂU DỮ LIỆU, không chỉ trong if. Xem CLAUDE.md §2.1."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 2 — AI không vượt cấp CSKH
# ===========================================================================

def test_inv03_ai_khong_duoc_tiep_nhan_ticket(authority):
    """INV-03 · mọi thứ phải qua CSKH tiếp nhận trước."""
    act = authority["actions"]["tiep_nhan_ticket"]
    assert act["ai_agent"] == "deny", (
        "AI được phép tiếp nhận ticket → có thể tự đẩy case lên mà không qua CSKH. "
        "Vi phạm CLAUDE.md §2.2."
    )


def test_inv05_khong_co_duong_tat_tu_draft_toi_executed(fsm):
    """INV-05 · duyệt toàn bộ đồ thị transition, chặn mọi đường tắt."""
    states = set(fsm["states"])
    edges: dict[str, set[str]] = {s: set() for s in states}
    for t in fsm["transitions"]:
        froms = t["from"] if isinstance(t["from"], list) else [t["from"]]
        tos = t["to"] if isinstance(t["to"], list) else [t["to"]]
        for f in froms:
            edges.setdefault(f, set()).update(tos)

    bat_buoc = ["cskh_received", "pending_supervisor", "approved"]

    def co_duong_tranh(chan: str) -> bool:
        """Có đường từ draft tới executed mà không đi qua state `chan` không?"""
        stack, seen = ["draft"], {"draft"}
        while stack:
            cur = stack.pop()
            if cur == "executed":
                return True
            for nxt in edges.get(cur, ()):
                if nxt != chan and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return False

    tranh_duoc = [s for s in bat_buoc if co_duong_tranh(s)]
    assert not tranh_duoc, (
        f"Tồn tại đường đi draft → executed né được state bắt buộc: {tranh_duoc}. "
        "Vi phạm CLAUDE.md §2.1 và §2.2."
    )


def test_inv06_ai_khong_thuc_hien_transition_cham_tien(fsm):
    """INV-06 · AI không xuất hiện trong transition chạm tiền."""
    xau = [f"{t['from']}→{t['to']}" for t in fsm["transitions"]
           if t.get("cham_tien") and "ai_agent" in t.get("boi", [])]
    assert not xau, f"AI thực hiện được transition chạm tiền: {xau}"


def test_transition_dan_toi_approved_chi_boi_supervisor(fsm):
    """Cửa duy nhất mở đường tới executed phải do supervisor giữ."""
    for t in fsm["transitions"]:
        tos = t["to"] if isinstance(t["to"], list) else [t["to"]]
        if "approved" in tos:
            assert t["boi"] == ["supervisor"], (
                f"Transition tới 'approved' cho phép role khác supervisor: {t['boi']}"
            )


def test_khong_ton_tai_tool_escalate_thang_len_supervisor(tools):
    """AI không được có tool đẩy thẳng lên sếp."""
    cam = {f["ten"] for f in tools["forbidden_tools"]}
    assert "escalate_len_supervisor" in cam
    assert "escalate_len_supervisor" not in tools["tools"]


# ===========================================================================
# RÀNG BUỘC CỨNG 3 — Cấm bịa số liệu
# ===========================================================================

def test_inv09_moi_tool_deu_tra_ve_tool_call_id(tools):
    """INV-09 · không có tool_call_id thì không truy vết được số liệu."""
    thieu = [t for t, spec in tools["tools"].items()
             if "tool_call_id" not in (spec.get("output") or {})]
    assert not thieu, (
        f"Tool không trả tool_call_id: {thieu}. "
        "Không truy vết được nguồn số liệu → không chặn được bịa số. Xem CLAUDE.md §2.3."
    )


def test_inv10_tool_co_trang_thai_not_found(tools):
    """INV-10 · tool phải nói 'không tìm thấy', không được trả giá trị mặc định."""
    thieu = []
    for ten, spec in tools["tools"].items():
        status = (spec.get("output") or {}).get("status") or {}
        if "not_found" not in (status.get("values") or []):
            thieu.append(ten)
    assert not thieu, (
        f"Tool không có trạng thái not_found: {thieu}. "
        "Tool im lặng trả 0 là nguồn gốc của bịa số liệu."
    )


def test_khong_ton_tai_tool_bi_cam_trong_src(tools):
    """Các tool trong forbidden_tools không được xuất hiện trong code."""
    files = src_files()
    if not files:
        pytest.skip("chưa có src/")
    cam = [f["ten"] for f in tools["forbidden_tools"]]
    vi_pham = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for ten in cam:
            if re.search(rf"\bdef\s+{re.escape(ten)}\b|\bfunction\s+{re.escape(ten)}\b", text):
                vi_pham.append(f"{p.relative_to(ROOT)}::{ten}")
    assert not vi_pham, f"Tool bị cấm xuất hiện trong src/: {vi_pham}"


# ===========================================================================
# RÀNG BUỘC CỨNG 4 — Xác thực
# ===========================================================================

def test_khong_bao_gio_hoi_mat_khau_hoac_otp_giao_dich():
    """Quét toàn bộ src/ tìm chỗ hỏi mật khẩu hoặc OTP giao dịch của khách hàng."""
    files = src_files()
    if not files:
        pytest.skip("chưa có src/")
    nghi_van = re.compile(r"(nhap_mat_khau|password_prompt|otp_giao_dich|transaction_otp)", re.I)
    hit = []
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if nghi_van.search(line) and "# ALLOWED:" not in line:
                hit.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:80]}")
    assert not hit, (
        "Có chỗ hỏi mật khẩu / OTP giao dịch:\n  " + "\n  ".join(hit)
        + "\nChỉ được dùng OTP PHIÊN LÀM VIỆC. Xem CLAUDE.md §2.4."
    )


# ===========================================================================
# RÀNG BUỘC CỨNG 5 — Gắn cờ gian lận ≠ khoá ví
# ===========================================================================

def test_inv07_gan_co_va_khoa_vi_tach_biet(authority, tools):
    """Hai hành động độc lập ở tầng contract."""
    assert authority["actions"]["gan_co_nghi_gian_lan"]["ai_agent"] == "allow"
    assert authority["actions"]["khoa_vi"]["ai_agent"] == "deny"
    assert authority["actions"]["khoa_vi"]["cskh"] == "deny"
    fs = tools["tools"]["danh_gia_tin_hieu_gian_lan"]
    assert "khoa" not in str(fs.get("output", {})).lower(), (
        "Tool chấm tín hiệu gian lận trả về thứ liên quan tới khoá ví — phải tách bạch."
    )


def test_module_gan_co_khong_import_module_khoa_vi():
    """Lớp 2 — tách bạch ở tầng code, không chỉ ở tầng ý định."""
    files = [p for p in src_files() if re.search(r"(fraud|gian_lan|signal)", p.name, re.I)]
    if not files:
        pytest.skip("chưa có module gian lận trong src/")
    vi_pham = []
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(import|from|require).*(lock_wallet|khoa_vi|wallet_lock)", text, re.I):
            vi_pham.append(str(p.relative_to(ROOT)))
    assert not vi_pham, (
        f"Module gian lận import module khoá ví: {vi_pham}. "
        "Dương tính giả sẽ làm khách hàng lương thiện mất quyền dùng tiền. Xem CLAUDE.md §2.5."
    )


# ===========================================================================
# Meta — bộ test này có còn khớp contract không
# ===========================================================================

def test_bo_test_nay_khong_loi_thoi():
    """Nếu contract đã đổi mà test chưa cập nhật, test này đỏ trước tiên."""
    import hashlib
    lech = []
    for ten, mong_doi in CONTRACT_VERSION.items():
        path = CONTRACTS / ten
        if not path.exists():
            lech.append(f"{ten}: không còn tồn tại")
            continue
        thuc_te = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]
        if thuc_te != mong_doi:
            lech.append(f"{ten}: test dựa trên @{mong_doi}, hiện tại @{thuc_te}")
    assert not lech, (
        "Bộ test này đã lỗi thời so với contract:\n  " + "\n  ".join(lech)
        + "\n→ Chạy /impact, rà lại test, rồi cập nhật CONTRACT_VERSION ở đầu file."
    )
