#!/usr/bin/env python3
"""F-MIG — so schema HAI ĐƯỜNG dựng. Chạy trong CI, job `migration-chain`.

`alembic upgrade head`  vs  `Base.metadata.create_all()`

Đây là thứ DUY NHẤT trả lời được hệ quả số 3 của hồ sơ F-MIG: vì chuỗi
migration chưa bao giờ chạy trọn, không tồn tại phép kiểm nào xác nhận hai
đường dựng schema còn khớp. Lệch = finding riêng, KHÔNG tự xử.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HERE = Path(tempfile.mkdtemp(prefix="kiem-schema-"))
sys.path.insert(0, str(REPO))

from sqlalchemy import create_engine, inspect
from src.db.models import Base


def mo_ta(eng) -> dict:
    """Mô tả schema ở dạng so sánh được, bỏ qua thứ tự."""
    insp = inspect(eng)
    ra = {}
    for t in sorted(insp.get_table_names()):
        if t == "alembic_version":
            continue
        cols = {
            c["name"]: f"{c['type']!s}|null={bool(c['nullable'])}"
            for c in insp.get_columns(t)
        }
        pk = sorted(insp.get_pk_constraint(t).get("constrained_columns") or [])
        fks = sorted(
            f"{sorted(f['constrained_columns'])}->{f['referred_table']}.{sorted(f['referred_columns'])}"
            for f in insp.get_foreign_keys(t)
        )
        cks = sorted(
            (c.get("name") or "?") for c in insp.get_check_constraints(t)
        )
        uqs = sorted(str(sorted(u["column_names"])) for u in insp.get_unique_constraints(t))
        ra[t] = {"cols": cols, "pk": pk, "fk": fks, "check": cks, "unique": uqs}
    return ra


print(f"HEAD = {subprocess.run(['git','rev-parse','--short','HEAD'],cwd=REPO,capture_output=True,text=True).stdout.strip()}")

# --- đường A: alembic upgrade head ---
db_a = HERE / "phep3_alembic.db"
db_a.unlink(missing_ok=True)
env = dict(os.environ, DATABASE_URL=f"sqlite:///{db_a}")
r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=REPO, env=env, capture_output=True, text=True)
if r.returncode != 0:
    print("alembic upgrade head TRƯỢT:", r.stderr[-500:]); sys.exit(2)
A = mo_ta(create_engine(f"sqlite:///{db_a}"))

# --- đường B: Base.metadata.create_all() ---
db_b = HERE / "phep3_createall.db"
db_b.unlink(missing_ok=True)
eb = create_engine(f"sqlite:///{db_b}")
Base.metadata.create_all(eb)
B = mo_ta(eb)

# --- so ---
print(f"\nđường A (alembic)    : {len(A)} bảng")
print(f"đường B (create_all) : {len(B)} bảng")

lech = []
for t in sorted(set(A) | set(B)):
    if t not in A:
        lech.append(f"BẢNG chỉ có ở create_all: {t}"); continue
    if t not in B:
        lech.append(f"BẢNG chỉ có ở alembic: {t}"); continue
    for khoa in ("cols", "pk", "fk", "check", "unique"):
        if A[t][khoa] != B[t][khoa]:
            if khoa == "cols":
                ca, cb = A[t]["cols"], B[t]["cols"]
                for c in sorted(set(ca) | set(cb)):
                    if ca.get(c) != cb.get(c):
                        lech.append(f"{t}.{c}: alembic={ca.get(c)} · create_all={cb.get(c)}")
            else:
                lech.append(f"{t}.{khoa}: alembic={A[t][khoa]} · create_all={B[t][khoa]}")

print()
if not lech:
    print("PHÉP 3 ĐẠT — hai đường dựng schema TRÙNG KHỚP.")
else:
    print(f"PHÉP 3 TRƯỢT — {len(lech)} điểm lệch (mỗi điểm là một finding cần báo, KHÔNG tự xử):")
    for d in lech:
        print("  •", d)
    sys.exit(1)
