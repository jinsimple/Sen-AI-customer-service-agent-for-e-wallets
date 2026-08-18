"""ADR-036 bước ①② — ca đối chứng cho cổng plaintext, trên QUẦN THỂ VỨT ĐI.

## Vì sao file này thay ca đối chứng cũ

Cổng `test_cot_nhom_a_khong_nam_plaintext` chuyển ĐỎ → XANH nhờ backfill
(ADR-032 ②). Nửa *"im lúc bình thường"* của **Luật A** có rồi; nửa **"KÊU lúc
bất thường"** thì chỉ chứng minh được bằng **ca đối chứng**.

Ca đối chứng đầu tiên chĩa vào `fin05ttl` — **quần thể bẩn có thật, sẵn có,
không do ta tạo ra** (738 dòng plaintext chưa ai nạp lại). Nó đúng ở chỗ
**không phải ghi vào ngăn xếp đang phục vụ** (Luật I).

🔴 **Nhưng nó sai ở một chỗ khác:** nó phụ thuộc vào **việc ai đó QUÊN DỌN**.
ADR-036 nói mạnh hơn — *một dụng cụ đo chỉ hoạt động chừng nào lỗ còn mở là
dụng cụ **cột đội vào việc không bao giờ vá lỗ ấy**.*

⟹ Quần thể phải **do ta dựng ra để vứt**, không phải vật **ta lỡ chưa dọn**.

## 🔴 Vì sao postgres THẬT chứ không SQLite cho nhanh

Cổng đo bằng `docker exec … psql` + `CASE … LIKE 'gAAAAA%'`. Đổi sang SQLite là
**đổi đúng đoạn đường đang cần chứng minh**: ca đối chứng phải đi **CÙNG MỘT
DÂY** với ca thật, nếu không nó chứng minh **một cổng khác**.

Container dùng ảnh `postgres:16-alpine` — **cùng ảnh** ba ngăn xếp đang chạy,
có sẵn cục bộ, không kéo mạng.

## Ranh giới với ngăn xếp đang phục vụ (Luật I)

Quần thể vứt đi là **một container RIÊNG**, tên cố định
`fin05-doi-chung-vut-di`, `--rm`, xoá ở teardown. **Không** tạo CSDL mới trong
postgres của `fin05` — tạo CSDL ở đó vẫn là **ghi vào máy chủ đang phục vụ**.
"""
from __future__ import annotations

import subprocess
import time
import uuid

import pytest

from tests._docker_co_mat import LY_DO, co_docker
from tests.test_security.test_cot_nhom_a_khong_nam_plaintext import _dem

ANH = "postgres:16-alpine"
TEN = "fin05-doi-chung-vut-di"
# Lời khai GIẢ, không lấy từ dữ liệu thật — bộ đo không được tạo ra một bản sao
# PII mới (Luật 10 ở trục rủi ro).
TRAN_GIA = ("Toi bi tru tien nhung nguoi nhan khong nhan duoc",
            "Chuyen khoan sai so tai khoan",
            "Giao dich bao loi nhung van tru tien")
MA_HOA_GIA = ("gAAAAABm" + "x" * 40, "gAAAAABm" + "y" * 40)


def _docker_co() -> bool:
    # Uỷ cho `tests/_docker_co_mat.py` — không ném khi máy thiếu `docker`.
    return co_docker()


def _psql_vut_di(sql: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", "-i", TEN, "psql", "-U", "vutdi", "-d", "vutdi", "-v", "ON_ERROR_STOP=1",
         "-c", sql],
        capture_output=True, text=True, timeout=60,
    )


@pytest.fixture(scope="module")
def quan_the_vut_di():
    """Dựng một postgres RIÊNG, nạp dữ liệu giả, xoá sạch lúc xong.

    `POSTGRES_USER`/`POSTGRES_DB` đặt là `vutdi` **có chủ đích**: nếu ai đó lỡ
    trỏ ca này vào một container thật, `psql -U vutdi` sẽ trượt ngay thay vì
    lặng lẽ đọc CSDL sản phẩm.
    """
    if not _docker_co():
        pytest.skip(LY_DO)
    subprocess.run(["docker", "rm", "-f", TEN], capture_output=True)
    r = subprocess.run(
        ["docker", "run", "-d", "--rm", "--name", TEN,
         "-e", "POSTGRES_USER=vutdi", "-e", "POSTGRES_DB=vutdi",
         "-e", "POSTGRES_PASSWORD=" + uuid.uuid4().hex, ANH],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        pytest.fail(f"KHÔNG ĐO ĐƯỢC: không dựng được quần thể vứt đi — {r.stderr[:300]}")
    try:
        # 🔴 KHÔNG dùng `pg_isready` làm mốc sẵn sàng — đo được 18/08: nó trả 0
        # TRONG KHI psql vẫn báo `FATAL: the database system is starting up`.
        # Ảnh postgres chạy một server TẠM trong lúc initdb, và `pg_isready`
        # bắt tay được với server tạm ấy.
        #
        # Hậu quả: ca ① XANH lượt đầu, ĐỎ lượt sau, cùng một mã — một ca CHẬP
        # CHỜN, tức là ca không đọc được theo cả hai chiều. Cách chữa KHÔNG phải
        # chạy lại tới khi xanh, mà là đổi mốc sẵn sàng sang **thứ ta thật sự
        # cần**: một câu lệnh SQL chạy trót lọt.
        han = time.monotonic() + 60
        while time.monotonic() < han:
            if _psql_vut_di("SELECT 1;").returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail(f"KHÔNG ĐO ĐƯỢC: {TEN} không nhận được câu SQL nào sau 60s")
        yield
    finally:
        subprocess.run(["docker", "rm", "-f", TEN], capture_output=True)


def _nap(bang: str, gia_tri: tuple[str, ...]) -> None:
    _psql_vut_di(f"DROP TABLE IF EXISTS {bang};")
    r = _psql_vut_di(f"CREATE TABLE {bang} (id serial primary key, description_raw text);")
    if r.returncode != 0:
        pytest.fail(f"KHÔNG ĐO ĐƯỢC: không tạo được bảng {bang} — {r.stderr[:300]}")
    for v in gia_tri:
        _psql_vut_di(f"INSERT INTO {bang} (description_raw) VALUES ('{v}');")


def test_cong_KEU_khi_quan_the_CO_dong_plaintext(quan_the_vut_di):
    """🔴 Nửa **KÊU LÚC BẤT THƯỜNG** của Luật A — thứ ca thật không tự chứng minh được.

    Đây là bước ② của ADR-036, và nó là **bước nghiệm thu, không phải thủ tục**:
    nếu ca này không đỏ được thì cổng plaintext **không có ai canh nó**, và điều
    đó **không có triệu chứng** — cổng vẫn xanh y hệt.
    """
    _nap("ban", TRAN_GIA + MA_HOA_GIA)
    phan_bo = _dem("ban", "description_raw", TEN)
    assert phan_bo.get("tran", 0) == len(TRAN_GIA), (
        f"cổng KHÔNG đếm đúng số dòng trần trên quần thể bẩn: {phan_bo} "
        f"(chờ tran={len(TRAN_GIA)})"
    )
    assert phan_bo.get("ma_hoa", 0) == len(MA_HOA_GIA), (
        f"cổng đếm sai số dòng đã mã hoá: {phan_bo}"
    )


def test_cong_IM_khi_quan_the_SACH(quan_the_vut_di):
    """Luật 2 — ca chứng minh cổng **KHÔNG chặn nhầm**.

    Thiếu vế này thì một bộ phân loại đánh dấu **mọi thứ** là trần cũng "đạt" ca
    trên, và cổng trở thành thứ luôn kêu — tức là thứ cả đội học cách bỏ qua.
    """
    _nap("sach", MA_HOA_GIA)
    phan_bo = _dem("sach", "description_raw", TEN)
    assert phan_bo.get("tran", 0) == 0, f"cổng kêu OAN trên quần thể sạch: {phan_bo}"
    assert phan_bo.get("ma_hoa", 0) == len(MA_HOA_GIA), phan_bo


def test_khong_doc_duoc_quan_the_bao_RIENG_khong_lang_le_xanh():
    """🔴 TRẠNG THÁI THỨ BA — chỗ dễ mất nhất, và mất thì không ai thấy.

    Nếu quần thể vứt đi bị dọn/hỏng/đổi tên, phép đo **không đọc được gì**. Một
    cổng gộp *"không đọc được"* vào *"không thấy dòng trần nào"* sẽ **XANH vì
    không thấy gì** — đúng hình dạng *assertion trùng trạng thái mặc định*
    (`tests/CHUAN-VIET-TEST.md` Luật 1).

    Ca này ép đúng tình huống ấy bằng một tên container **chắc chắn không tồn
    tại**, và đòi phép đo phải **KÊU**, không được trả về một phân bố rỗng
    trông như "sạch".
    """
    ten_khong_co = f"fin05-khong-ton-tai-{uuid.uuid4().hex[:8]}"
    # `pytest.fail()` ném `Failed`, kế thừa **BaseException** chứ không phải
    # `Exception` ⟹ `pytest.raises(Exception)` KHÔNG bắt được nó. Bản đầu của ca
    # này viết `Exception` và đỏ — nhưng đỏ vì **test-của-test sai**, không phải
    # vì cổng sai: thông điệp cổng in ra đã đúng ngay từ lượt đầu.
    #
    # Ghi lại vì nó đúng lớp lỗi cả ngày: **"phép thử của tôi hỏng" ≠ "thứ tôi
    # đo hỏng"**, và phân biệt được chỉ nhờ ĐỌC thông điệp thay vì đọc màu.
    with pytest.raises(pytest.fail.Exception) as e:
        _dem("ban", "description_raw", ten_khong_co)
    assert "KHÔNG ĐO ĐƯỢC" in str(e.value), (
        f"phép đo thất bại nhưng KHÔNG báo trạng thái thứ ba: {str(e.value)[:200]}"
    )
