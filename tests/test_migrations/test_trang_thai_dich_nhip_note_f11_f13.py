"""Trạng thái đích của nhịp migration F-11 + F-13 — nghiệm thu bằng máy.

Nguồn đặc tả: `docs/security/pre-review-nhip-migration-note-f11-f13.md` §3
("Trạng thái đích — assert được"). Viết từ đặc tả, KHÔNG đọc `src/`.

ĐÂY LÀ TEST TRÊN DỮ LIỆU THẬT, không phải fixture. Nó mở đúng DB mà ứng dụng
đang dùng (`DATABASE_URL`) và đếm hàng. Lý do phải làm vậy: F-11 và F-13 là
lỗi của **dữ liệu đã nằm trong sổ**, không phải lỗi của logic — một fixture
sạch dựng lại từ đầu sẽ luôn xanh và chứng minh đúng con số không.

Không tới được DB thì `skip`, không đỏ giả — cùng cách `test_frontend_route_
guards.py` xử lý khi thiếu stack Docker.

CÁCH CHẠY (mặc định `pytest tests/` sẽ SKIP hết vì DATABASE_URL là SQLite —
đừng nhìn "7 skipped" rồi tưởng đã xanh):

    PW=$(docker compose exec -T backend printenv DATABASE_URL | sed -E 's|.*://[^:]+:([^@]+)@.*|\1|')
    DATABASE_URL="postgresql+psycopg2://fin05:${PW}@127.0.0.1:5432/fin05" \
        pytest tests/test_migrations/test_trang_thai_dich_nhip_note_f11_f13.py -q

TRẠNG THÁI NỀN đo lúc viết test (14/08, TRƯỚC migration) — để coder đối chiếu:
  - resolutions: 6 approved · 3 pending_approval · **3** rejected (đích: 1)
  - cả 3 dòng rejected đều có `rejected_by = USR-0205` (đích: sentinel)
  - **7** ticket lệch hitl_status (đích: 0)
Con số 7 hoà giải đúng với "6 ticket đổi trạng thái" của đặc tả: 6 ticket được
backfill, còn ticket thứ 7 (`TCK-518527ab869f`) tự hết lệch khi 2 resolution
của nó bị xoá — nó rời khỏi phép đếm thay vì được sửa. Đặc tả nhất quán.
Chạy lần đầu: **5 đỏ · 2 xanh** — đúng trạng thái chưa migrate.

VÌ SAO CANH BẰNG DỮ LIỆU CHỨ KHÔNG BẰNG CONSTRAINT: PO đã chốt giữ CHECK br11
một chiều (F-15), nên bất biến "hàng chưa từ chối không được mang nhãn từ
chối" không có ai ép ở tầng DB. Nó phải được canh ở đây, nếu không thì không
ai canh.

CẢNH BÁO KHI ĐỌC KẾT QUẢ: `rejected` giảm 3 → 1 là **có chủ đích** (xoá 2 dòng
dữ liệu QA), không phải dữ liệu trôi. Đừng "sửa" test cho khớp số cũ.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

# 5 ticket phải sang `approved` + 1 sang `rejected` (đặc tả §3).
TICKET_SANG_APPROVED = {
    "TCK-173cee0218a0",
    "TCK-5ce978c5fd8b",
    "TCK-5ff347d86281",
    "TCK-77f6333334e2",
    "TCK-cfd642f7461c",
}
TICKET_SANG_REJECTED = {"TCK-0e7f530fbd4f"}

# Ticket có 2 resolution bị xoá -> còn 0 resolution, PHẢI giữ `pending`:
# ticket không còn bản ghi nào chống đỡ thì không được khẳng định phán quyết
# HITL nào (contract v2.1.0 `dan_xuat.quy_tac`).
TICKET_MAT_HET_RESOLUTION = "TCK-518527ab869f"

# 3 ticket mà resolution mới nhất còn `pending_approval` -> giữ `pending`.
TICKET_GIU_PENDING = {"TCK-8a4779f8861a", "TCK-ddd78e22867f", "TCK-4fea9a74557b"}

# 2 supervisor NGƯỜI THẬT trong DB (báo cáo security §Nhiệm vụ 1 mục 4).
SUPERVISOR_NGUOI_THAT = {"USR-0205", "USR-0206"}

RES_REJECTED_CON_LAI = "RES-3b3026227331"

# Cùng thứ tự `_dong_bo_hitl_status()` dùng ở runtime — hai đường PHẢI cho cùng
# kết quả, nếu không dữ liệu lịch sử và dữ liệu mới sẽ theo hai luật khác nhau.
SQL_RESOLUTION_MOI_NHAT = """
    SELECT t.ticket_id, t.hitl_status, r.status AS res_status
    FROM tickets t
    JOIN LATERAL (
        SELECT status FROM resolutions
        WHERE ticket_id = t.ticket_id
        ORDER BY created_at DESC, resolution_id DESC
        LIMIT 1
    ) r ON TRUE
"""


@pytest.fixture(scope="module")
def db():
    from src.config import DATABASE_URL
    from src.db.session import get_engine

    if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        pytest.skip(f"Cần DB thật (Postgres), DATABASE_URL hiện là {DATABASE_URL!r}", allow_module_level=True)
    try:
        engine = get_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Không tới được DB thật ({e!r}) — cần `docker compose up -d`", allow_module_level=True)

    # CHẶN ĐỎ SAI CHỖ (phát hiện khi rà C3, lỗi của chính file này): CI có job
    # `db-migration-test` chạy `pytest tests/test_migrations/` trên một Postgres
    # RỖNG dựng mới mỗi lần. File này canh trạng thái dữ liệu của DB demo —
    # trên DB rỗng nó sẽ đỏ toàn bộ vì lý do KHÔNG liên quan gì tới migration,
    # và một job đỏ vì lý do sai sẽ dạy người ta bỏ qua job đó.
    #
    # Phân biệt bằng: DB đích LUÔN có resolution. DB rỗng của CI thì không.
    # Chỉ skip ở đúng ca đó, không nới rộng hơn.
    try:
        with engine.connect() as conn:
            so_resolution = conn.execute(text("SELECT COUNT(*) FROM resolutions")).scalar_one()
    except Exception as e:  # noqa: BLE001 — bảng chưa tồn tại: DB rỗng chưa migrate
        pytest.skip(
            f"Chưa có bảng `resolutions` ({type(e).__name__}) — DB rỗng chưa migrate, "
            "không phải DB demo mà file này canh.",
            allow_module_level=True,
        )
    if so_resolution == 0:
        pytest.skip(
            "DB không có resolution nào — đây là DB rỗng (CI dựng mới), không phải DB demo "
            "mà file này canh. Chạy trên DB demo: xem lệnh ở docstring đầu file.",
            allow_module_level=True,
        )
    with engine.connect() as conn:
        yield conn


def test_so_luong_resolution_theo_status_dung_chinh_xac(db):
    """6 approved · 3 pending_approval · 1 rejected.

    `rejected` 3 → 1 là CHỦ ĐÍCH (xoá 2 dòng QA). Nếu test này đỏ ở con số
    rejected, hỏi "đã xoá đúng 2 dòng nào" trước khi nghĩ tới việc sửa test.
    """
    thuc_te = dict(db.execute(text("SELECT status, COUNT(*) FROM resolutions GROUP BY status")).all())
    assert thuc_te == {"approved": 6, "pending_approval": 3, "rejected": 1}, (
        f"Phân bố resolution lệch đặc tả. Thực tế: {thuc_te}"
    )


def test_dong_rejected_duy_nhat_tro_vao_sentinel_khong_phai_nguoi_that(db):
    """F-11 — cốt lõi của cả nhịp này.

    Sổ kiểm toán không được ghi tên một người thật vào một hành động mà không
    có gì chứng minh là họ làm. Migration cũ gán Phan Hữu Châu (USR-0205) bằng
    `ORDER BY user_id LIMIT 1` — tức là chọn theo thứ tự bảng chữ cái, không
    theo bằng chứng nào.
    """
    hang = db.execute(text("SELECT resolution_id, rejected_by FROM resolutions WHERE status = 'rejected'")).all()
    assert len(hang) == 1, f"Phải còn đúng 1 dòng rejected, thực tế {len(hang)}: {hang}"

    resolution_id, rejected_by = hang[0]
    assert resolution_id == RES_REJECTED_CON_LAI, (
        f"Dòng rejected còn lại là {resolution_id}, đặc tả nói phải là {RES_REJECTED_CON_LAI} "
        "— có thể đã xoá nhầm dòng."
    )
    assert rejected_by not in SUPERVISOR_NGUOI_THAT, (
        f"`rejected_by` = {rejected_by} là supervisor NGƯỜI THẬT. Phải trỏ vào user "
        "sentinel hệ thống — đây chính là F-11: gán bừa tên người vào bản ghi kiểm toán."
    )
    assert rejected_by is not None, "CHECK br11 cấm NULL — sentinel phải là user có thật trong bảng users."


def test_khong_con_ticket_lech_hitl_status_so_voi_resolution_moi_nhat(db):
    """F-13 — bất biến chính, và là thứ phải đúng MÃI, không chỉ sau migration.

    Contract v2.1.0 `dan_xuat.quy_tac`: hitl_status theo resolution MỚI NHẤT.
    Vá QA-02 chỉ chạy khi có approve/reject mới, nên dữ liệu lịch sử không tự
    khớp — đó là lý do cần backfill, và lý do cần test này canh về sau.
    """
    lech = db.execute(text(SQL_RESOLUTION_MOI_NHAT + """
        WHERE r.status IN ('approved', 'rejected') AND t.hitl_status = 'pending'
    """)).all()
    assert not lech, (
        f"{len(lech)} ticket có resolution mới nhất đã approved/rejected nhưng hitl_status "
        f"vẫn 'pending': {[r[0] for r in lech]}"
    )


def test_sau_ticket_dung_dich_trang_thai(db):
    """5 sang approved + 1 sang rejected, kiểm ĐÍCH DANH từng mã.

    Kiểm đích danh chứ không chỉ đếm: một backfill viết sai điều kiện WHERE có
    thể vẫn cho ra "6 ticket" nhưng là 6 ticket khác.
    """
    can_kiem = TICKET_SANG_APPROVED | TICKET_SANG_REJECTED
    rows = db.execute(
        text("SELECT ticket_id, hitl_status FROM tickets WHERE ticket_id = ANY(:ids)"),
        {"ids": list(can_kiem)},
    ).all()
    thuc_te = dict(rows)

    thieu = can_kiem - set(thuc_te)
    assert not thieu, f"Không tìm thấy ticket trong DB: {sorted(thieu)}"

    sai = {
        tid: thuc_te[tid]
        for tid in can_kiem
        if thuc_te[tid] != ("approved" if tid in TICKET_SANG_APPROVED else "rejected")
    }
    assert not sai, f"Ticket sai hitl_status sau migration: {sai}"


def test_ticket_mat_het_resolution_van_giu_pending(db):
    """Thứ tự F-11-trước-F-13 tồn tại chính vì ca này.

    Làm ngược (F-13 trước, F-11 sau) sẽ set ticket sang 'rejected' rồi mới xoá
    hai resolution — để lại một ticket **khẳng định một phán quyết HITL mà
    không còn bản ghi nào chống đỡ**. Đó là dữ liệu kiểm toán bịa đúng nghĩa,
    và nó sẽ im lặng, không có test nào khác bắt được.
    """
    con_lai = db.execute(
        text("SELECT COUNT(*) FROM resolutions WHERE ticket_id = :tid"),
        {"tid": TICKET_MAT_HET_RESOLUTION},
    ).scalar_one()
    assert con_lai == 0, f"{TICKET_MAT_HET_RESOLUTION} còn {con_lai} resolution, đặc tả nói phải còn 0."

    hitl = db.execute(
        text("SELECT hitl_status FROM tickets WHERE ticket_id = :tid"),
        {"tid": TICKET_MAT_HET_RESOLUTION},
    ).scalar_one()
    assert hitl == "pending", (
        f"{TICKET_MAT_HET_RESOLUTION} có hitl_status='{hitl}' trong khi KHÔNG còn resolution nào. "
        "Ticket chưa có resolution phải là 'pending' (contract v2.1.0). Nhiều khả năng migration "
        "đã chạy sai thứ tự: F-13 trước F-11."
    )


def test_ba_ticket_con_cho_duyet_van_giu_pending(db):
    """Mặt còn lại của F-13: backfill KHÔNG được quét quá tay.

    Ticket mà resolution mới nhất vẫn `pending_approval` thì chưa có phán quyết
    nào — set sang approved/rejected là bịa theo chiều ngược lại.
    """
    rows = db.execute(
        text("SELECT ticket_id, hitl_status FROM tickets WHERE ticket_id = ANY(:ids)"),
        {"ids": list(TICKET_GIU_PENDING)},
    ).all()
    sai = {tid: st for tid, st in rows if st != "pending"}
    assert not sai, f"Ticket còn chờ duyệt bị đổi trạng thái oan: {sai}"


def test_khong_hang_nao_chua_tu_choi_ma_mang_nhan_tu_choi(db):
    """F-15 canh bằng DỮ LIỆU, vì PO đã chốt giữ CHECK br11 một chiều.

    Rủi ro cụ thể cho Phase 2: exporter lọc nhầm theo `reject_reason IS NOT
    NULL` thay vì `status='rejected'` sẽ kéo những hàng này vào phễu học. Đặc
    tả lọc đúng đã ghi ở `eval/CANDIDATE-REVIEW.md`.
    """
    ban = db.execute(text("""
        SELECT resolution_id, status, reject_reason, rejected_by, rejected_at
        FROM resolutions
        WHERE status <> 'rejected'
          AND (reject_reason IS NOT NULL OR rejected_by IS NOT NULL OR rejected_at IS NOT NULL)
    """)).all()
    assert not ban, f"Hàng chưa từ chối nhưng mang nhãn từ chối: {ban}"
