"""Backfill `policy_chunks.scope` từ bản BA chốt (ADR-061, Finding ① Lớp 1).

Nguồn: `eval/results/rag-baseline-03-09/scope_ban_giao.csv`, cột `scope_dung`
(KHÔNG dùng `scope_nhap` — đó là bản nháp máy, `scope_dung` mới là phán quyết
cuối của BA). Join theo `chunk_id`.

🔴 KHÔNG PHẢI MỘT ALEMBIC REVISION — CÓ CHỦ ĐÍCH, cùng lý do với
`backfill_ma_hoa_description_raw.py` cạnh file này: `alembic upgrade head`
chạy TỰ ĐỘNG mỗi lần container khởi động, trên MỌI ngăn xếp kể cả production.
Backfill dữ liệu không được tự động chạy lại mỗi lần deploy.

An toàn hơn backfill mã hoá cạnh nó: thao tác này ĐẢO NGƯỢC ĐƯỢC (CSV vẫn còn,
chạy lại script là quay về đúng trạng thái đó — không phải mất bản gốc vĩnh
viễn như giải mã-mã hoá lại). Vẫn giữ khuôn "mặc định KHÔNG ghi, phải `--ghi`"
cho nhất quán và để người chạy luôn thấy trước SẼ đổi gì.

Cách dùng (trong container backend):
    python migrations/backfill_policy_chunk_scope.py                # dry-run, chỉ in
    python migrations/backfill_policy_chunk_scope.py --ghi          # ghi thật

🔴 DỪNG NGAY, KHÔNG GHI GÌ nếu chunk_id lệch giữa CSV và store (CSV có mà
store không có, hoặc ngược lại) — đúng chỉ đạo PO. Không tự bỏ qua id lệch.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from src.db.models import PolicyChunk  # noqa: E402
from src.db.session import session_scope  # noqa: E402

CSV_PATH = Path(__file__).resolve().parent.parent / "eval" / "results" / "rag-baseline-03-09" / "scope_ban_giao.csv"
GIA_TRI_HOP_LE = {"internal_wallet", "from_bank", "to_bank", "unknown"}


def main() -> None:
    ghi_that = "--ghi" in sys.argv

    rows = list(csv.DictReader(CSV_PATH.open()))
    csv_scope = {r["chunk_id"]: r["scope_dung"].strip() for r in rows}

    la = {cid: s for cid, s in csv_scope.items() if s not in GIA_TRI_HOP_LE}
    if la:
        print(f"🔴 DỪNG — {len(la)} dòng CSV có scope_dung KHÔNG hợp lệ: {la}", file=sys.stderr)
        raise SystemExit(1)

    with session_scope() as db:
        store_ids = set(db.scalars(select(PolicyChunk.chunk_id)).all())
        csv_ids = set(csv_scope)

        chi_co_csv = csv_ids - store_ids
        chi_co_store = store_ids - csv_ids
        if chi_co_csv or chi_co_store:
            print("🔴 DỪNG — chunk_id lệch giữa CSV và store, KHÔNG ghi gì:", file=sys.stderr)
            print(f"  CSV có, store KHÔNG có ({len(chi_co_csv)}): {sorted(chi_co_csv)[:10]}", file=sys.stderr)
            print(f"  store có, CSV KHÔNG có ({len(chi_co_store)}): {sorted(chi_co_store)[:10]}", file=sys.stderr)
            raise SystemExit(1)

        print(f"Khớp {len(csv_ids)}/{len(csv_ids)} chunk_id — không lệch.")

        rows_db = db.scalars(select(PolicyChunk)).all()
        so_doi = 0
        for chunk in rows_db:
            moi = csv_scope[chunk.chunk_id]
            if chunk.scope != moi:
                so_doi += 1
                if ghi_that:
                    chunk.scope = moi

        tu_kiem_dem = {}
        for s in csv_scope.values():
            tu_kiem_dem[s] = tu_kiem_dem.get(s, 0) + 1
        print(f"Phân bố scope_dung trong CSV: {tu_kiem_dem}")
        print(f"Số chunk cần đổi giá trị: {so_doi}/{len(rows_db)}")

        if not ghi_that:
            print("DRY-RUN — chưa ghi gì. Chạy lại kèm --ghi để ghi thật.")
        else:
            print(f"ĐÃ GHI {so_doi} chunk.")


if __name__ == "__main__":
    main()
