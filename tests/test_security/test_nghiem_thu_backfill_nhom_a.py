"""ADR-032 việc ② — cổng NGHIỆM THU backfill cột Nhóm A.

## 🔴 Vì sao cổng "0 dòng plaintext" MỘT MÌNH là cổng hỏng

`test_cot_nhom_a_khong_nam_plaintext` đã khẳng định *"không dòng nào nằm trần"*.
**Một backfill chạy `DELETE FROM complaints` sẽ làm nó XANH.** Đây là Luật 1 ở
dạng nguy hiểm nhất: **bản cài đặt tầm thường nhất thoả mãn assertion.**

Bốn kiểu hỏng mà "0 plaintext" không bắt được — file này bắt cả bốn:

    1  mất dòng            ít dòng hơn ⟹ vẫn 0 trần
    2  mất nội dung        đúng hình dạng gAAAAA, ruột rỗng
    3  MÃ HOÁ HAI LẦN      🔴 hình dạng KHÔNG phân biệt được — token trong token
    4  mã hoá khoá KHÁC    hình dạng đúng, không ai đọc được nữa

## Vì sao có tệp nền `eval/NEN-TRUOC-BACKFILL-2026-08-18.json`

Mẫu số **"sau"** đo lúc nào cũng được; mẫu số **"trước"** chỉ đo được **trước
khi backfill chạy**. Nền được chụp lúc `02:40:29 UTC 18/08`, **trước khi
`migrations/` có script nào**, trên `bam_ma_nguon = d5b73a04d6ef`.
🔴 **KHÔNG dùng `BUILD_COMMIT`** làm mốc — [ĐO] 18/08: nhãn `bf1bd5a` **khác**
mã đang chạy (ảnh dựng từ **cây làm việc**, không từ HEAD).

## Vì sao vân tay GỘP, không phải băm theo dòng

`md5` mỗi bản rõ → sắp xếp → `md5` của chuỗi nối. **Một** con số cho cả cột.
Băm của một câu ngắn là thứ **dò ngược được**; một tệp trong git chứa 761 băm
lời khai khách là **một tài sản PII mới do chính bộ đo tạo ra** — Luật 10 ở
trục rủi ro thay vì trục kết quả. Vân tay gộp trả lời đúng câu cần hỏi
(*"tập nội dung có đổi không"*) và **không trả lời được** câu không nên hỏi.

## Vì sao neo theo MỐC THỜI GIAN

Ngăn xếp đang **sống**: khiếu nại mới vào thì `tong` và vân tay đổi **hợp lệ**.
Neo `WHERE created_at <= <mốc>` làm tập đo **bất động**, nên `tong` so được
**chính xác** (không phải `>=`) — mất một dòng là ĐỎ, và dòng mới không gây
báo động giả.

## 🔴 `PYTHONDONTWRITEBYTECODE=1` — bắt buộc, và đây là lý do

[ĐO] 18/08, phép đối chứng trên container **chưa ai chạm**: cùng một lệnh
`docker exec … python -c` "chỉ đọc" làm `docker diff` tăng **+101 dòng**
(bytecode cache). Thêm biến này ⟹ **Δ=0**, xác minh trên container thứ ba.

Nó không hỏng dữ liệu — nhưng **nó làm hỏng CÁI BẪY**: `docker diff` là dây
báo động của cả đội cho câu *"phép đo có chạm vật không"*, và một phép đo tự
thêm 101 dòng nhiễu khiến lần dò tampering sau phải bới qua nhiễu của chính
mình. **Bộ đo làm mù chính dụng cụ dùng để canh bộ đo.**
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess

import pytest

GOC = pathlib.Path(__file__).resolve().parent.parent.parent
NEN = GOC / "eval" / "NEN-TRUOC-BACKFILL-2026-08-18.json"
BACKEND = os.environ.get("FIN05_BACKEND_CONTAINER", "fin05-backend-1")

COT = (
    ("complaints", "description_raw", "created_at"),
    ("messages", "content", "created_at"),
    ("policy_chunks", "text", "created_at"),
    ("bank_accounts", "account_no", "linked_at"),
)

_MA_DO = '''
import hashlib, json, os, sys
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import create_engine, text
moc = sys.argv[1] if len(sys.argv) > 1 else None
COT = %r
f = Fernet(os.environ["FIELD_ENCRYPTION_KEY"].encode())
e = create_engine(os.environ["DATABASE_URL"])
ra = {}
with e.connect() as c:
    for bang, cot, tcot in COT:
        hang = [r[0] for r in c.execute(
            text("SELECT " + cot + " FROM " + bang + " WHERE " + tcot + " <= :m"), {"m": moc})]
        d = {"giai_ma_duoc": 0, "chua_ma_hoa": 0, "khoa_khac": 0, "boc_hai_lan": 0, "rong": 0}
        van = []
        for v in hang:
            if v is None or not str(v).strip():
                d["rong"] += 1
                continue
            v = str(v)
            try:
                ban_ro = f.decrypt(v.encode()).decode()
                d["giai_ma_duoc"] += 1
                if ban_ro.startswith("gAAAAA"):
                    d["boc_hai_lan"] += 1
            except InvalidToken:
                ban_ro = v
                d["khoa_khac" if v.startswith("gAAAAA") else "chua_ma_hoa"] += 1
            van.append(hashlib.md5(ban_ro.encode()).hexdigest())
        d["tong"] = len(hang)
        d["van_tay_gop"] = hashlib.md5("".join(sorted(van)).encode()).hexdigest()[:16]
        ra[bang + "." + cot] = d
print(json.dumps(ra, sort_keys=True))
''' % (COT,)


def _song() -> bool:
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={BACKEND}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


def _nen() -> dict:
    if not NEN.exists():
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC: thiếu tệp nền {NEN.relative_to(GOC)} — không có mẫu "
            "số ĐẦU thì 'sau' không nói lên điều gì. Nền này KHÔNG dựng lại được "
            "sau khi backfill chạy."
        )
    d = json.loads(NEN.read_text())
    # 🔴 CƠ CHẾ, không phải lời nhắc — Luật 18 (băm phải khai TÊN THUẬT TOÁN).
    #
    # Tệp nền bản đầu mang bốn con số `van_tay_gop` mà KHÔNG mang cách băm, và
    # chính tệp của tôi vi phạm chính luật của tôi. Hậu quả đo được ngay hôm đó:
    # PO-agent tự gõ lại phép băm để đối chiếu, ra `8440c6c1…` rồi `51b7b712…`
    # — cả hai SAI, cả hai vì băm THẲNG giá trị thay vì băm-từng-dòng-rồi-gộp.
    # Nếu họ báo sau lần một, sếp đã nhận tin "dữ liệu bị thay" cho một sự cố
    # KHÔNG TỒN TẠI — đúng loại tin đẩy người nhận vào chế độ xử lý sự cố.
    #
    # ⟹ Cổng TỪ CHỐI một tệp nền không tự khai cách băm. Người sau không phải
    # đọc mã test mới dùng được tệp, và ai chép tệp này đi nơi khác cũng mang
    # theo định nghĩa.
    thieu = [k for k in ("__cach_bam__", "__moc_thoi_gian__", "__do__") if k not in d]
    if thieu:
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC: tệp nền thiếu khoá tự-khai {thieu} — một con số băm "
            "không kèm CÁCH BĂM thì không phải bằng chứng (Luật 18). Đã có ca "
            "thật: hai lần tính lại độc lập ra hai giá trị khác nhau và cả hai "
            "đều sai, chỉ vì phép băm được gõ lại từ trí nhớ."
        )
    return d


def _do_lai(moc: str) -> dict:
    r = subprocess.run(
        ["docker", "exec", "-e", "PYTHONDONTWRITEBYTECODE=1", BACKEND,
         "python", "-c", _MA_DO, moc],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'đạt'): không đo được trong {BACKEND} — "
            f"{(r.stderr or r.stdout)[:400]}"
        )
    return json.loads(r.stdout.strip().splitlines()[-1])


@pytest.mark.skipif(not _song(), reason=f"container {BACKEND} không chạy")
def test_backfill_khong_lam_mat_dong_hay_doi_noi_dung():
    """🟢 Ở CỔNG CHÍNH — ba mốc mà "0 plaintext" mù hoàn toàn.

    Tách khỏi ca dưới **có chủ đích** (Luật J): ca này canh được **ngay hôm
    nay** và phải ở cổng chính màu xanh. Gộp chung rồi gắn `security_finding`
    thì cả nửa đang canh được cũng bị ẩn khỏi `lint-and-test` — và đúng nửa ấy
    mới là nửa bắt được một backfill làm mất dữ liệu.
    """
    nen = _nen()
    moc = nen["__moc_thoi_gian__"]
    nay = _do_lai(moc)

    hong = []
    for bang, cot, _t in COT:
        k = f"{bang}.{cot}"
        a, b = nen[k], nay[k]
        if b["tong"] != a["tong"]:
            hong.append(f"  {k}: MẤT/THÊM DÒNG trong tập đã đóng băng — "
                        f"nền {a['tong']} → nay {b['tong']}")
        if b["van_tay_gop"] != a["van_tay_gop"]:
            hong.append(f"  {k}: NỘI DUNG ĐỔI — vân tay {a['van_tay_gop']} → "
                        f"{b['van_tay_gop']}")
        if b["khoa_khac"]:
            hong.append(f"  {k}: {b['khoa_khac']} dòng mã hoá bằng KHOÁ KHÁC — "
                        "không ai đọc được nữa")
        if b["boc_hai_lan"]:
            hong.append(f"  {k}: {b['boc_hai_lan']} dòng BỌC HAI LẦN — hình dạng "
                        "không phân biệt được, chỉ giải mã mới thấy")

    assert not hong, (
        "🔴 BACKFILL LÀM HỎNG DỮ LIỆU (hoặc có thứ khác đã đụng vào):\n"
        + "\n".join(hong)
        + f"\n  tập đo đóng băng tại mốc {moc} — dòng mới KHÔNG nằm trong đây, "
        "nên đây không thể là báo động giả do lưu lượng thường."
    )


@pytest.mark.skipif(not _song(), reason=f"container {BACKEND} không chạy")
def test_cot_nhom_a_da_duoc_nap_lai_het():
    """🔴 ĐIỀU KIỆN NGHIỆM THU của ADR-032 việc ② — cố ý ĐỎ tới khi backfill chạy.

    🟢 **18/08 — GỠ NHÃN `security_finding`.** Backfill đã chạy (`5939b6a`);
    ca chuyển ĐỎ → XANH và nay là **test hồi quy thường**.

    🔴 **Luật J — nó khẳng định CÁI GÌ:** *"trong tập đóng băng tại mốc
    `2026-08-18 02:40:29 UTC`, không dòng nào còn mang dạng bản rõ"* —
    `complaints.description_raw` **738 trần → 0**, `tong` vẫn **761**, vân tay
    gộp **không đổi** (`2805e52d1a4d0bed`) ⟹ nội dung được **bảo toàn**, không
    phải bị thay bằng thứ khác cho đúng hình dạng.

    Ca này **một mình không đủ**: nó xanh cả khi backfill xoá sạch bảng. Nó chỉ
    có nghĩa khi đọc **cùng** `test_backfill_khong_lam_mat_dong_hay_doi_noi_dung`
    — ca ấy mới là ca bám `tong` và vân tay.

    🔴 Và nó nói về **MỘT quần thể**: `fin05`. `fin05ttl` còn nguyên 738 dòng
    trần, `fin05do` sạch vì hạt giống sinh sau (không do backfill),
    **`production` chưa ai đo**.
    """
    nen = _nen()
    moc = nen["__moc_thoi_gian__"]
    nay = _do_lai(moc)

    con_tran = {k: nay[f"{b}.{c}"]["chua_ma_hoa"]
                for b, c, _ in COT if (k := f"{b}.{c}") and nay[k]["chua_ma_hoa"]}
    assert not con_tran, (
        "🔴 CÒN DÒNG CHƯA ĐƯỢC NẠP LẠI (ADR-032 việc ② chưa xong):\n"
        + "\n".join(f"  {k}: {v} dòng trần" for k, v in sorted(con_tran.items()))
        + "\n  nền 18/08 02:40 UTC: complaints.description_raw 738 trần / 23 giải "
        "mã được. Bản vá là script backfill trong `migrations/`, KHÔNG phải sửa "
        "cổng này."
    )
