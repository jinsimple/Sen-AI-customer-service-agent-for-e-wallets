"""FIN05-StressTest-Plan-v2 ST2-P0-1 (docs/FIN05-Feature-Inventory-Security-
Review.md §11 finding "security_answer_hash") — chứng minh bug BẰNG TEST, cố
tình để ở trạng thái ĐỎ, KHÔNG tự sửa `src/api/main.py:277` cùng lúc (chỉ PO
mới quyết định vá lúc nào — vá thuật toán hash ảnh hưởng dữ liệu user thật,
cần migration riêng).

Cả 2 test dưới đây khẳng định HÀNH VI AN TOÀN MONG MUỐN (hash phải có salt
ngẫu nhiên riêng mỗi lần/mỗi user, định dạng phải tự mô tả thuật toán như
bcrypt/argon2) — và vì vậy FAIL NGAY hôm nay, đúng chủ đích, vì thực tế
`verify_otp` (src/api/main.py:278) so khớp bằng
`hashlib.sha256(req.security_answer.encode()).hexdigest() == user.security_answer_hash`,
và dữ liệu thật sinh ra qua `scripts/gen_dataset.py:230`:
`hashlib.sha256(f"ans-{seed}-{uid}".encode()).hexdigest()` — cả 2 đều là
SHA-256 THUẦN, không trộn salt/per-user-secret nào. Không dùng test đo thời
gian brute-force (flaky, phụ thuộc máy chạy CI) — chứng minh trực tiếp bằng
chính công thức thật đang dùng.

Khi PO quyết định vá (đổi sang bcrypt/argon2 + salt) — sửa lại 2 hàm
`_verify_otp_hash_formula`/công thức sinh dữ liệu bên dưới cho khớp thuật
toán mới, 2 test này sẽ tự chuyển xanh, không cần viết lại từ đầu.
"""
from __future__ import annotations

import hashlib

import pytest


def _verify_otp_hash_formula(answer: str) -> str:
    """Sao chép NGUYÊN VĂN công thức thật ở src/api/main.py:278 — nếu công
    thức thật đổi (thêm salt) mà hàm này không cập nhật theo, 2 test dưới sẽ
    lệch pha với thực tế thay vì âm thầm pass sai (self-check bằng
    test_gen_dataset_formula_stays_in_sync_with_verify_otp)."""
    return hashlib.sha256(answer.encode()).hexdigest()


@pytest.mark.security_finding
def test_security_answer_hash_differs_across_calls_for_same_input():
    """MONG MUỐN: hash câu trả lời bảo mật phải dùng salt ngẫu nhiên riêng
    mỗi lần hash (bcrypt/argon2 tự sinh salt mới mỗi lần gọi, kể cả cùng 1
    input) — 2 lần hash CÙNG 1 câu trả lời phải ra 2 giá trị KHÁC nhau.
    FAIL hôm nay vì SHA-256 thuần là hàm xác định (deterministic): cùng
    input luôn ra cùng output, không có chỗ nào cho salt chen vào."""
    same_answer = "Nguyễn Thị Bình"

    first = _verify_otp_hash_formula(same_answer)
    second = _verify_otp_hash_formula(same_answer)

    assert first != second, (
        "verify_otp (src/api/main.py:278) đang dùng hashlib.sha256() TRẦN, "
        "không salt — cùng input luôn ra cùng hash, nghĩa là 1 rainbow table "
        "dùng chung được cho toàn bộ user nếu DB rò rỉ. Cần đổi sang "
        "bcrypt/argon2 (tự sinh salt ngẫu nhiên mỗi lần/mỗi user) trước khi "
        "chấp nhận test này pass — xem "
        "docs/FIN05-Feature-Inventory-Security-Review.md §11."
    )


@pytest.mark.security_finding
def test_security_answer_hash_format_is_not_a_raw_fixed_length_digest():
    """MONG MUỐN: `security_answer_hash` lưu ở định dạng tự mô tả thuật toán
    + salt nhúng sẵn (bcrypt bắt đầu '$2a$'/'$2b$', argon2 bắt đầu
    '$argon2'), không phải chuỗi hex 64 ký tự cố định (đặc trưng riêng của
    digest thô như SHA-256/SHA3-256 không salt). FAIL hôm nay — đối chiếu
    TRỰC TIẾP công thức sinh dữ liệu thật `scripts/gen_dataset.py:230`
    (`hashlib.sha256(f"ans-{seed}-{uid}".encode()).hexdigest()`), không suy
    đoán tách biệt khỏi dữ liệu thật."""
    from src.config import DATASET_SEED

    uid = "USR-DEMO-0001"
    stored_hash = hashlib.sha256(f"ans-{DATASET_SEED}-{uid}".encode()).hexdigest()

    is_proper_password_hash_format = stored_hash.startswith(("$2a$", "$2b$", "$2y$", "$argon2", "$scrypt$"))
    assert is_proper_password_hash_format, (
        f"security_answer_hash hiện là digest thô 64 hex char "
        f"({stored_hash[:16]}...), không phải định dạng bcrypt/argon2/scrypt "
        "có salt nhúng sẵn trong chính chuỗi hash — cần vá "
        "scripts/gen_dataset.py:230 + src/api/main.py:278 đồng bộ, kèm "
        "migration cho user thật đã tồn tại (nếu có)."
    )


def test_gen_dataset_formula_stays_in_sync_with_verify_otp():
    """Không phải test bảo mật — test 'khoá' để 2 công thức sao chép tay ở
    trên (_verify_otp_hash_formula) và trong docstring module không lặng lẽ
    lệch pha với 2 file nguồn thật. Đọc trực tiếp source `src/api/main.py`
    và `scripts/gen_dataset.py`, xác nhận công thức SHA-256 trần vẫn còn ở
    đúng vị trí đã ghi — nếu dòng này FAIL nghĩa là code đã đổi (khả năng đã
    vá!), cần cập nhật lại 2 test ở trên theo thuật toán mới thay vì chỉnh
    test này cho pass lại."""
    from src.config import ROOT_DIR

    main_src = (ROOT_DIR / "src" / "api" / "main.py").read_text(encoding="utf-8")
    gen_dataset_src = (ROOT_DIR / "scripts" / "gen_dataset.py").read_text(encoding="utf-8")

    assert "hashlib.sha256(req.security_answer.encode()).hexdigest() == user.security_answer_hash" in main_src, (
        "Công thức so khớp câu trả lời bảo mật ở src/api/main.py đã đổi — "
        "cập nhật lại 2 test P0-1 phía trên theo thuật toán mới."
    )
    assert 'hashlib.sha256(f"ans-{self.seed}-{uid}".encode()).hexdigest()' in gen_dataset_src, (
        "Công thức sinh security_answer_hash ở scripts/gen_dataset.py đã đổi — "
        "cập nhật lại 2 test P0-1 phía trên theo thuật toán mới."
    )
