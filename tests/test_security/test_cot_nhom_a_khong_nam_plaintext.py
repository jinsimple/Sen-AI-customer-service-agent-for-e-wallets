"""ADR-032 việc ③ — cổng khẳng định *"không dòng nào trong cột Nhóm A nằm
plaintext"*.

## Vì sao file này tồn tại

**[ĐO] 18/08 (ADR-032):** `complaints.description_raw` — cột ADR-025 chọn làm
**Nhóm A** (lời khai của khách, dữ liệu nhạy cảm nhất hệ thống) — có **738 dòng
PLAINTEXT** trên đĩa và 23 dòng đã mã hoá. `EncryptedText` được gắn vào kiểu cột
khoảng 15/08; **738 dòng có sẵn chưa bao giờ được nạp lại.**

Ba tháng không ai thấy vì nhánh lỗi giải mã **nuốt im lặng và trả nguyên văn** —
ứng dụng đọc 738 dòng ấy không một lỗi, không một dòng log. Và vì
**không cổng nào khẳng định điều ngược lại.** Đây là cổng đó.

## 🔴 CỔNG NÀY ĐO CÁI GÌ — đọc trước khi trích

    ĐO ĐƯỢC        HÌNH DẠNG TRÊN ĐĨA của giá trị trong CSDL
    KHÔNG ĐO ĐƯỢC  giá trị ấy có giải mã được bằng khoá HIỆN TẠI không
    KHÔNG ĐO ĐƯỢC  hành vi ORM (`process_result_value`) — bản vá ADR-032 việc ①
                   đã vào cây nhưng CONTAINER VẪN CHẠY MÃ CŨ

`gAAAAA` chứng minh **HÌNH DẠNG**, không chứng minh **QUYỀN ĐỌC**: một dòng mã
hoá bằng **khoá khác** cũng mở đầu `gAAAAA` và cổng này đọc là "đã mã hoá". Đó
là **đúng phạm vi** — cổng canh *dữ liệu nằm trần trên đĩa*, không canh *ta còn
đọc được không*. Đừng gộp hai câu.

## Vì sao HAI nửa, cố ý không gộp

    (a) NEO ĐẶC TẢ   4 cột ADR-032 BỔ SUNG ① khai là Nhóm A phải 100% mã hoá
    (b) TỰ DÒ CẢ HỌ  quét MỌI cột văn bản, tìm cột PHA TRỘN

(b) bắt được **cột thứ năm chưa ai khai** — cổng chỉ kiểm danh sách gõ cứng là
cổng không biết gì ngoài danh sách. *(Đúng lớp lỗi đã vá hai lần ngày 18/08:
đầu dò kho RAG gõ cứng tên collection, rồi gõ cứng path.)*
(a) bắt được cột **100% plaintext** mà lẽ ra phải mã hoá — (b) **không thấy**,
vì không pha trộn thì không có gì lạ để dò. **Hai nửa canh hai lỗ khác nhau.**

## 🔴 PHẠM VI MÙ — khai ra, vì một cổng không khai chỗ mù sẽ được đọc là toàn cảnh

Cả hai nửa chỉ quét cột kiểu **văn bản** (`text` · `varchar` · `char` — 113 cột).
**KHÔNG quét** 10 cột kiểu `json`/`jsonb`/`bytea`. [ĐO] 18/08 trên
`fin05-postgres-1`, chỉ đếm, không in nội dung:

    investigation_logs.tool_input_json    0/93     mang hình dạng mã hoá
    checkpoint_blobs.blob                 0/6.213  mang hình dạng mã hoá
    checkpoint_blobs.blob                 2.179/6.213  CHỨA mã giao dịch "TXN2026…"

⟹ Kho checkpoint (trạng thái hội thoại) giữ **2.179 dòng có mã giao dịch nằm
trần**, và nó **nằm ngoài cả sơ đồ mã hoá lẫn cổng này**. Con số 738 của
ADR-032 **không phải toàn cảnh** — nhưng ADR-032 BỔ SUNG ① cũng đã khai đúng
mẫu số của nó (*"cả bốn cột khai `Encrypted*`"*), nên đây là **MỞ RỘNG phạm vi,
KHÔNG phải đính chính**.

Cổng này **cố ý KHÔNG assert** trên 10 cột đó: quyết định cột nào phải mã hoá
là việc của ADR, không phải của tester tự mở rộng. Đã báo PO-agent.
"""
from __future__ import annotations

import os
import subprocess

import pytest

from tests._docker_co_mat import co_docker, container_song

POSTGRES = os.environ.get("FIN05_POSTGRES_CONTAINER", "fin05-postgres-1")

# ADR-032 BỔ SUNG ① — bốn cột khai `Encrypted*`, kèm số đo cùng ngày.
COT_NHOM_A = (
    ("complaints", "description_raw"),
    ("messages", "content"),
    ("policy_chunks", "text"),
    ("bank_accounts", "account_no"),
)

# ADR-032 BỔ SUNG ③ — byte phiên bản Fernet 0x80 ⟹ base64url luôn mở đầu "gA".
TIEN_TO_FERNET = "gAAAAA"


def _psql(sql: str, container: str = POSTGRES) -> list[list[str]]:
    try:
        r = subprocess.run(
            ["docker", "exec", "-e", "PYTHONDONTWRITEBYTECODE=1", container, "sh", "-c",
             f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "|" -c "{sql}"'],
            capture_output=True, text=True, timeout=180,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError) as e:
        # THIẾU CÔNG CỤ cũng là "không đọc được quần thể", không phải một sự cố
        # lạ. Để traceback thô rơi ra ngoài là in KẾT LUẬN sai (`tệp này hỏng`)
        # thay vì TRIỆU CHỨNG (`không chạy được docker ở đây`) — Luật H.
        pytest.fail(f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'sạch'): không gọi được docker — {e}")
    if r.returncode != 0:
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'sạch'): không truy vấn được {container} — "
            f"{(r.stderr or r.stdout)[:300]}"
        )
    return [d.split("|") for d in r.stdout.strip().splitlines() if d.strip()]


def _kho_dang_song() -> bool:
    # Uỷ cho `tests/_docker_co_mat.py` — nó KHÔNG NÉM khi máy thiếu `docker`.
    # Bản cũ gọi thẳng `subprocess.run(["docker", ...])` trong biểu thức
    # `skipif`, tức LÚC IMPORT ⟹ máy không có docker thì pytest ném
    # FileNotFoundError lúc THU THẬP: 11 lỗi, `Interrupted`, 0 ca chạy.
    return container_song(POSTGRES)


def phan_loai(gia_tri: str | None) -> str:
    """LOGIC THUẦN — `'ma_hoa' | 'tran' | 'khong_do_duoc'`.

    Tách khỏi phần đọc hạ tầng để chứng minh được nửa *"KÊU lúc bất thường"*
    (Luật A) bằng dữ liệu bịa, **không ghi một byte nào vào CSDL đang phục vụ**
    (Luật I). Xem `test_doi_chung_phan_loai`.

    `None` và chuỗi rỗng là **KHÔNG ĐO ĐƯỢC**, KHÔNG phải "trần": một ô rỗng
    không chứa dữ liệu khách nào để mà lộ, nhưng nó cũng không chứng minh cột
    đã được mã hoá. Gộp nó vào "trần" thổi phồng con số; gộp vào "mã hoá" giấu
    mất một cột rỗng đáng ngờ. Luôn là BA trạng thái (Luật H).
    """
    if gia_tri is None or not gia_tri.strip():
        return "khong_do_duoc"
    return "ma_hoa" if gia_tri.startswith(TIEN_TO_FERNET) else "tran"


def _dem(bang: str, cot: str, container: str = POSTGRES) -> dict[str, int]:
    """Phân bố `{ma_hoa, tran, khong_do_duoc}` trên TOÀN BẢNG.

    🔴 KHÔNG `LIMIT`. ADR-032 ghi lại chính xác cách sự cố này lọt: security
    trích **3 dòng mẫu** rồi đọc ra *"đã mã hoá"* — ba dòng ấy tình cờ nằm
    trong 23 dòng mới, vì **`LIMIT` mặc định trả về dòng mới nhất**. Bộ lọc vô
    hình nằm trong chính công cụ truy vấn. Hỏi MẪU SỐ thì bức tranh lật ngược.
    """
    sql = (
        f"SELECT CASE WHEN {cot} IS NULL OR btrim({cot}) = '' THEN 'khong_do_duoc' "
        f"WHEN {cot} LIKE '{TIEN_TO_FERNET}%' THEN 'ma_hoa' ELSE 'tran' END AS loai, "
        f"count(*) FROM {bang} GROUP BY 1;"
    )
    return {h[0]: int(h[1]) for h in _psql(sql, container) if len(h) == 2}


def _cot_van_ban() -> list[tuple[str, str]]:
    """Mọi cột kiểu văn bản trong schema `public` — đầu vào cho phép dò (b)."""
    sql = (
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND data_type IN "
        "('text','character varying','character') ORDER BY 1,2;"
    )
    return [(h[0], h[1]) for h in _psql(sql) if len(h) == 2]


def test_doi_chung_phan_loai():
    """Nửa **KÊU LÚC BẤT THƯỜNG** của Luật A — dữ liệu bịa, 0 container.

    Không có ca này thì "xanh" của cổng chỉ nghĩa là chưa ai nhìn kỹ.
    """
    assert phan_loai("gAAAAABm7x9Q_khong_phai_token_that") == "ma_hoa"
    assert phan_loai("Toi bi tru tien nhung nguoi nhan khong nhan duoc") == "tran"
    # Luật 2 — không chặn nhầm: một câu tiếng Việt bắt đầu bằng 'g' vẫn là trần.
    assert phan_loai("giao dich cua toi bi loi") == "tran"
    # TRẠNG THÁI THỨ BA — rỗng KHÔNG phải "trần" và cũng KHÔNG phải "mã hoá".
    for rong in (None, "", "   "):
        assert phan_loai(rong) == "khong_do_duoc", f"{rong!r} bị xếp sai rổ"


@pytest.mark.skipif(not _kho_dang_song(), reason=f"container {POSTGRES} không chạy")
@pytest.mark.parametrize(("bang", "cot"), COT_NHOM_A, ids=lambda x: x)
def test_cot_nhom_a_khong_co_dong_nao_nam_plaintext(bang, cot):
    """(a) NEO ĐẶC TẢ — mỗi cột Nhóm A phải 100% mang hình dạng mã hoá.

    🟢 **18/08 — GỠ NHÃN `security_finding`.** Backfill đã chạy (`5939b6a`) và
    cổng tự chuyển ĐỎ → XANH. Nay nó là **test hồi quy thường**: mở lại lỗ là
    đỏ ngay, không núp được dưới nhãn nữa.

    🔴 **Luật J — cổng này nay khẳng định CÁI GÌ, đọc chứ đừng chỉ ghi nhận màu:**

        TRƯỚC  complaints.description_raw   23 mã hoá /  738 trần
        SAU    complaints.description_raw  761 mã hoá /    0 trần

    Nó khẳng định *"không giá trị nào trong bốn cột Nhóm A mang hình dạng bản
    rõ **trên ngăn xếp đang đo**"*. Nó **KHÔNG** khẳng định giá trị ấy giải mã
    được — việc đó do `test_nghiem_thu_backfill_nhom_a` canh, và **hai ca phải
    đọc cùng nhau**: cổng này một mình vẫn xanh khi bảng bị xoá sạch.

    🔴 **VÀ NÓ CHỈ NÓI VỀ MỘT QUẦN THỂ.** Backfill chạy trên **`fin05`**.
    [ĐO] 18/08, cùng một câu truy vấn, ba ngăn xếp:

        fin05      ma_hoa=761              ← đã nạp lại
        fin05ttl   ma_hoa=4  tran=738      ← 🔴 CÒN NGUYÊN khoản nợ
        fin05do    ma_hoa=607              ← sạch vì hạt giống sinh sau, không do backfill

    `production` **chưa ai đo**. Bốn quần thể, đừng gộp.
    """
    phan_bo = _dem(bang, cot)
    tong = sum(phan_bo.values())
    if tong == 0:
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'sạch'): {bang}.{cot} không có dòng nào "
            f"trên {POSTGRES} — một bảng rỗng không chứng minh được gì"
        )
    tran = phan_bo.get("tran", 0)
    assert tran == 0, (
        f"🔴 CỘT NHÓM A CÓ DÒNG NẰM TRẦN TRÊN ĐĨA: {bang}.{cot}\n"
        f"  trần          {tran}\n"
        f"  mã hoá        {phan_bo.get('ma_hoa', 0)}\n"
        f"  không đo được {phan_bo.get('khong_do_duoc', 0)}\n"
        f"  TỔNG          {tong}   (toàn bảng, KHÔNG LIMIT — container {POSTGRES})\n"
        "ADR-032: cột được ADR-025 chọn làm Nhóm A đang nằm plaintext. Bản vá là "
        "script backfill trong `migrations/`, KHÔNG phải sửa cổng này."
    )


TTL = os.environ.get("FIN05_TTL_POSTGRES_CONTAINER", "fin05ttl-postgres-1")


def _song(container: str) -> bool:
    # 🔴 CHẶN TRƯỚC: hàm này chạy trong biểu thức `skipif`, tức LÚC IMPORT.
    # Máy không có `docker` thì `subprocess` ném FileNotFoundError trong lúc
    # pytest THU THẬP ⟹ `Interrupted`, và kết quả của MỌI ca khác biến mất.
    # Đo được 18/08: 634 ca thu thập được → 0 ca chạy, chỉ vì thiếu một tệp
    # nhị phân. Trạng thái đúng là SKIP KÈM LÝ DO, không phải 'tệp này hỏng'.
    if not co_docker():
        return False
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={container}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


@pytest.mark.skipif(not _song(TTL), reason=f"container {TTL} không chạy")
def test_doi_chung_cong_keu_tren_quan_the_chua_nap_lai():
    """🔴 Nửa **KÊU LÚC BẤT THƯỜNG** của Luật A — trên VẬT THẬT, 0 byte ghi ra.

    Nửa *"im lúc bình thường"* đã có (`fin05` xanh). Nửa còn lại chỉ chứng minh
    được bằng **ca đối chứng**, và cho tới 18/08 nó chưa có: cổng chuyển ĐỎ →
    XANH nhờ backfill, nhưng **không ai chứng minh nó còn biết đỏ**.

    Cách rẻ nhất trông có vẻ là nhét một dòng plaintext giả vào CSDL — **không
    làm**: đó là ghi vào ngăn xếp đang phục vụ (Luật I).

    Không cần. **`fin05ttl` CHƯA được nạp lại** ([ĐO] 18/08: `ma_hoa=4 ·
    tran=738`) ⟹ nó là một quần thể bẩn **có thật, sẵn có, không do ta tạo ra**.
    Chĩa đúng phép đo ấy sang đó thì cổng **phải kêu**.

    Nếu ngày nào đó `fin05ttl` cũng được nạp lại, ca này báo **KHÔNG ĐO ĐƯỢC**
    chứ không im lặng xanh — mất quần thể bẩn nghĩa là mất khả năng chứng minh
    cổng biết đỏ, và điều đó phải **hiện ra**, không được lặng lẽ thành "đạt".
    """
    phan_bo = _dem("complaints", "description_raw", TTL)
    tran = phan_bo.get("tran", 0)
    if tran == 0:
        pytest.fail(
            f"KHÔNG ĐO ĐƯỢC (KHÔNG phải 'đạt'): {TTL} nay cũng sạch "
            f"({phan_bo}) — mất quần thể bẩn để chứng minh cổng biết KÊU. "
            "Tìm quần thể khác hoặc đổi cách đối chứng; đừng bỏ ca này."
        )
    assert tran > 0 and phan_bo.get("ma_hoa", 0) >= 0, phan_bo


@pytest.mark.skipif(not _kho_dang_song(), reason=f"container {POSTGRES} không chạy")
def test_khong_cot_van_ban_nao_pha_tron_ma_hoa_voi_tran():
    """(b) TỰ DÒ CẢ HỌ — không cột nào được vừa có dòng `gAAAAA…` vừa có dòng trần.

    Một cột PHA TRỘN **theo định nghĩa** là cột đáng lẽ được mã hoá mà có dòng
    nằm trần. Phép dò này không cần biết trước tên cột nào, nên nó bắt được
    **cột thứ năm chưa ai khai** — thứ mà danh sách gõ cứng ở (a) mù hoàn toàn.

    🔴 Tiêu chí ④ (`eval/QUET-TEN-HUA-KHAC-ASSERTION.md`): *"0 kết quả" chỉ có
    nghĩa NẾU bộ dò bắt được ca ĐÃ BIẾT.* Nên ca này **assert rằng nó bắt được**
    `complaints.description_raw` chừng nào (a) còn đỏ — bộ dò im trong lúc ca đã
    biết vẫn hỏng là **bộ dò hỏng**, không phải CSDL sạch.
    """
    pha_tron = {}
    for bang, cot in _cot_van_ban():
        phan_bo = _dem(bang, cot)
        if phan_bo.get("ma_hoa", 0) > 0 and phan_bo.get("tran", 0) > 0:
            pha_tron[f"{bang}.{cot}"] = phan_bo

    da_biet = "complaints.description_raw"
    if da_biet not in pha_tron:
        # Có thể backfill đã chạy — nhưng ta KHÔNG được tự kết luận thế.
        phan_bo_da_biet = _dem("complaints", "description_raw")
        if phan_bo_da_biet.get("tran", 0) > 0:
            pytest.fail(
                f"BỘ DÒ HỎNG: {da_biet} có {phan_bo_da_biet['tran']} dòng trần "
                f"nhưng phép dò không bắt được nó — {phan_bo_da_biet}"
            )

    da_khai = {f"{b}.{c}" for b, c in COT_NHOM_A}
    ngoai_pham_vi = sorted(set(pha_tron) - da_khai)
    assert not pha_tron, (
        "🔴 CỘT PHA TRỘN (vừa có dòng mã hoá vừa có dòng nằm trần):\n"
        + "\n".join(f"  {c}: {p}" for c, p in sorted(pha_tron.items()))
        + f"\n  (toàn bảng, KHÔNG LIMIT — container {POSTGRES})\n"
        + (
            f"🔴 NGOÀI 4 cột Nhóm A đã khai ⟹ FINDING MỚI, ngoài phạm vi "
            f"ADR-032: {ngoai_pham_vi}"
            if ngoai_pham_vi
            else "Tất cả đều nằm TRONG 4 cột Nhóm A đã khai ⟹ đúng phạm vi "
                 "ADR-032, KHÔNG phải finding mới. Bản vá là script backfill."
        )
    )
