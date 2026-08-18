"""GĐ2 — cổng ĐỘ PHỦ NHÃN: mỗi giá trị nhãn phải có ≥1 dòng dữ liệu mang nó.

## Vì sao cổng này tồn tại

**[ĐO] 18/08:** `complaints.otp_disclosed = false` trên **cả 761 dòng**. Cờ
*"khách lỡ tiết lộ OTP"* — một tín hiệu gian lận — **chưa từng được ai nhìn thấy
ở trạng thái BẬT**, trong suốt vòng đời dự án.

> **Một nhãn không có dòng nào mang nó KHÔNG phải "ít gặp" — là CHƯA KIỂM.**
> Mọi thứ đọc nhãn ấy (bộ lọc, thống kê, prompt, màn hình CSKH, chính agent)
> chạy trên một nhánh **chưa bao giờ bắn**. Độ phủ mã có thể ghi 100% và vẫn
> không ai biết nhánh ấy làm gì. Đây là **Luật E** ở tầng DỮ LIỆU thay vì tầng
> test.

## 🔴 Vì sao HAI nguồn nhãn, không phải một

Brief GĐ2 nói *"quét mọi CHECK constraint"* và nêu ca đối chứng là
`otp_disclosed`. **[ĐO] hai thứ đó không giao nhau:**

    complaints.otp_disclosed   kiểu = boolean
    CHECK nào nhắc otp_disclosed → KHÔNG CÓ

Một cổng quét **chỉ** CHECK sẽ **XANH** trên đúng cái trục mà ca đối chứng
được nêu ra để canh — và **không ai biết**, vì thứ thiếu là **một cột không
xuất hiện trong danh sách**. Cùng lớp lỗi đã vá ba lần ngày 18/08 (*bộ quét chỉ
tìm thấy thứ nó biết cách gọi tên*), lần này ở tầng **đề bài**.

    ① CHECK dạng liệt kê   col::text = ANY (ARRAY['a','b',…])
    ② cột BOOLEAN          nhãn ẩn {true, false} — KHÔNG constraint nào khai

## Vì sao phải ĐẾM số CHECK bị bỏ qua

Trong 32 CHECK có nhiều cái **không phải enum**: `length(...) <= 12000`,
`csat_score >= 1 AND <= 5`, `VALUE >= 0`. Bỏ qua chúng là đúng — **nhưng im
lặng bỏ qua thì không.** Một bộ quét lặng lẽ bỏ 20/32 **trông y hệt** một bộ
quét phủ hết 32. Cổng in ra cả hai con số (Luật 7 — công cụ đo cũng cần được canh).
"""
from __future__ import annotations

import os
import re
import subprocess

import pytest

from tests._docker_co_mat import LY_DO, co_docker

POSTGRES = os.environ.get("FIN05_POSTGRES_CONTAINER", "fin05-postgres-1")

# Dạng Postgres sinh ra cho một CHECK liệt kê:
#   CHECK (((status)::text = ANY ((ARRAY['a'::character varying, …])::text[])))
_DANG_ENUM = re.compile(r"\(\((\w+)\)::text = ANY \(\(ARRAY\[(.+?)\]\)::text\[\]\)\)")
_GIA_TRI = re.compile(r"'((?:[^']|'')*)'::")


def _psql(sql: str) -> list[str]:
    try:
        r = subprocess.run(
            ["docker", "exec", "-i", "-e", "PYTHONDONTWRITEBYTECODE=1", POSTGRES, "sh", "-c",
             'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "\t"'],
            input=sql, capture_output=True, text=True, timeout=180,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as e:
        pytest.fail(f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'đủ nhãn'): không gọi được docker — {e}")
    if r.returncode != 0:
        pytest.fail(f"KHÔNG ĐO ĐƯỢC: psql lỗi trên {POSTGRES} — {(r.stderr or r.stdout)[:300]}")
    return [d for d in r.stdout.strip().splitlines() if d.strip()]


def _nhan_tu_check() -> tuple[dict[tuple[str, str], list[str]], list[str]]:
    """Nguồn ①. Trả `({(bảng, cột): [giá trị]}, [định nghĩa BỊ BỎ QUA])`."""
    dong = _psql(
        "SELECT conrelid::regclass::text, pg_get_constraintdef(oid) FROM pg_constraint "
        "WHERE contype='c' AND conrelid <> 0 ORDER BY 1;"
    )
    nhan: dict[tuple[str, str], list[str]] = {}
    bo_qua = []
    for d in dong:
        bang, dinh_nghia = d.split("\t", 1)
        m = _DANG_ENUM.search(dinh_nghia)
        if not m:
            bo_qua.append(f"{bang}: {dinh_nghia[:90]}")
            continue
        nhan[(bang, m.group(1))] = _GIA_TRI.findall(m.group(2))
    return nhan, bo_qua


def _nhan_tu_boolean() -> dict[tuple[str, str], list[str]]:
    """Nguồn ② — nhãn KHÔNG constraint nào khai, và là nguồn duy nhất phủ được
    `complaints.otp_disclosed`, tức chính ca đối chứng của brief."""
    dong = _psql(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND data_type='boolean' ORDER BY 1,2;"
    )
    return {tuple(d.split("\t", 1)): ["true", "false"] for d in dong}


def _bang_rong() -> set[str]:
    dong = _psql(
        "SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY 1;"
    )
    return {d.split("\t")[0] for d in dong if d.split("\t")[1] == "0"}


@pytest.mark.skipif(not co_docker(), reason=LY_DO)
def test_moi_nhan_co_it_nhat_mot_dong_du_lieu_mang_no():
    """🔴 Cổng này SINH RA ĐỂ ĐỎ hôm nay — dữ liệu demo chưa được sinh.

    Nó chuyển XANH khi tech-lead sinh đủ. Viết nó **sau** khi dữ liệu đã đủ thì
    nó xanh ngay lượt đầu và **không ai chứng minh được nó biết ĐỎ** (Luật A vế
    hai) — đó là lý do PO chốt thứ tự ngược với trực giác.
    """
    tu_check, bo_qua = _nhan_tu_check()
    tu_bool = _nhan_tu_boolean()
    assert tu_bool, "KHÔNG ĐO ĐƯỢC: không đọc được cột boolean nào — nguồn ② chết"
    assert tu_check, "KHÔNG ĐO ĐƯỢC: không bóc được CHECK liệt kê nào — bộ bóc hỏng"

    rong = _bang_rong()
    moi_nhan = {**tu_check, **tu_bool}
    thieu, bo_vi_bang_rong = [], []

    for (bang, cot), gia_tri in sorted(moi_nhan.items()):
        if bang in rong:
            bo_vi_bang_rong.append(f"{bang}.{cot}")
            continue
        for v in gia_tri:
            dk = f"{cot} IS TRUE" if v == "true" else (
                f"{cot} IS FALSE" if v == "false" else f"{cot} = '{v}'")
            n = _psql(f"SELECT count(*) FROM {bang} WHERE {dk};")
            if n and n[0] == "0":
                thieu.append(f"  {bang}.{cot} = {v}")

    bao = (
        f"\n  nguồn ①  {len(tu_check)} cột enum bóc từ CHECK"
        f"  ·  {len(bo_qua)} CHECK BỊ BỎ QUA vì không phải liệt kê"
        f"\n  nguồn ②  {len(tu_bool)} cột boolean"
        f"\n  bảng rỗng (KHÔNG ĐO ĐƯỢC, không tính là thiếu): {sorted(rong) or '—'}"
        f"\n  cột bị bỏ vì bảng rỗng: {bo_vi_bang_rong or '—'}"
    )
    assert not thieu, (
        f"🔴 {len(thieu)} NHÃN KHÔNG CÓ DÒNG NÀO MANG NÓ:\n" + "\n".join(thieu) + "\n" + bao
        + "\n\nMột nhãn không có dòng nào mang nó KHÔNG phải 'ít gặp' — là CHƯA KIỂM. "
        "Mọi thứ đọc nhãn ấy chạy trên một nhánh chưa bao giờ bắn.\n"
        "Bản vá là SINH DỮ LIỆU DEMO cho các nhãn trên, KHÔNG phải nới cổng này."
    )
