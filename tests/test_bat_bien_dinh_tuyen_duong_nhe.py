"""Bất biến cho LỚP ĐỊNH TUYẾN — viết TRƯỚC khi cài đặt tồn tại.

    Một lượt đi ĐƯỜNG NHẸ không được tạo bản ghi nghiệp vụ nào:
        Δcomplaints = 0 · Δtickets = 0 · Δresolutions = 0

Nếu một lượt **cần** tạo bản ghi thì tự nó đã không phải lượt đơn — việc nó đi
được đường nhẹ **chính là** bằng chứng phân loại sai. Bất biến biến *"phân loại
sai"* từ một phán đoán của người thành **một hiệu số của máy**.

## 🔴 PHÁT BIỂU NHƯ TRÊN CHƯA ĐO ĐƯỢC — thiếu một vế

PO dặn: *"nếu bạn thấy cần đọc `src/` mới viết được thì phát biểu đang sai,
báo lại"*. Tôi không cần đọc `src/`. Tôi cần một thứ khác, và nó thiếu:

> **Không có cách nào biết một lượt ĐÃ ĐI ĐƯỜNG NÀO.**

Thiếu vế đó thì bất biến rơi thẳng vào Luật 1 — **assertion trùng trạng thái
mặc định**. Vì `Δ = 0` là **trạng thái thường trực**: đại đa số lượt chat không
tạo vé, bất kể chúng đi đường nào. Gửi `"alo"`, đếm ra `Δ = 0`, rồi kết luận
*"đường nhẹ không ghi gì"* — trong khi có thể lượt đó đi **đường đầy đủ** và
chỉ đơn giản là không có gì để ghi.

    Δ = 0 và đi đường nhẹ        → bất biến ĐÚNG
    Δ = 0 và đi đường đầy đủ     → bất biến CHƯA ĐƯỢC THỬ
    hai thứ này KHÔNG phân biệt được nếu không có dấu đường

**Đề nghị sửa phát biểu** (một trong hai, tôi không chọn hộ):

1. **Dấu tường minh** — phản hồi mang một trường kiểu `duong: "nhe" | "day_du"`.
   Rẻ, chắc, và nó còn có ích cho vận hành: khi tỉ lệ đi-đường-nhẹ nhảy vọt
   trên production, đó là tín hiệu sớm của phân loại trôi.
2. **Dấu suy ra được từ `usage`** — đường đầy đủ đã đo được `input_tokens ≈
   12.667`/lượt (17/08, `fin05do`). Đường nhẹ, theo mô tả, không mang prompt
   15.094 ký tự lẫn lược đồ tool ⟹ phải thấp hơn **một bậc độ lớn**. Dùng được,
   nhưng nó là **suy luận từ một đại lượng có mục đích khác** — nó sẽ nói dối
   ngay ngày ai đó đổi prompt hoặc bật nén ngữ cảnh.

Tôi ưu tiên (1). Nhưng đây là **đề xuất**, và cả hai đều nằm ngoài vùng ghi của
tôi — quyết định thuộc PO và coder.

## Vế thứ hai: `Δresolutions` không mang thông tin

`resolutions` sinh ra khi `supervisor` duyệt (ràng buộc cứng 1), **không** sinh
ra từ một lượt chat. Nên `Δresolutions = 0` đúng cho **mọi** lượt, đường nào
cũng vậy — nó là một vế **luôn xanh**. Giữ lại cũng không hại, nhưng đừng tính
nó là một trong ba bằng chứng: bất biến này thực chất có **hai** vế.

## Ca đối chứng — vế PO đã yêu cầu, và tôi giữ nguyên vì nó đúng

Thiếu nó, một cài đặt *"đường nhẹ chặn mọi ghi"* vẫn xanh **kể cả khi nó chặn
nhầm cả đường đầy đủ** — tức chặn nhầm đúng những khiếu nại thật.
"""
from __future__ import annotations

import os
import subprocess

import pytest

from tests._dong_bang import LY_DO, dang_dong_bang

BASE = os.environ.get("FIN05_TEST_BASE_URL", "")
BANG_NGHIEP_VU = ("complaints", "tickets", "resolutions")


def _stack_do_song() -> bool:
    r = subprocess.run(["docker", "ps", "-q", "-f", "name=fin05do-backend-1"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not _stack_do_song(),
                       reason="cần ngăn xếp ĐO DÙNG RIÊNG fin05do — phép đo này GHI, "
                              "không được chạy trên ngăn xếp dùng chung (Luật 15)"),
    pytest.mark.skipif(dang_dong_bang(), reason=LY_DO),
]


def _dem() -> dict[str, int]:
    """Đếm TỪNG bảng nghiệp vụ. Đếm cả ba, không đếm bảng mình đoán sẽ đổi."""
    sql = " UNION ALL ".join(f"SELECT '{b}',count(*) FROM {b}" for b in BANG_NGHIEP_VU)
    r = subprocess.run(
        ["docker", "exec", "fin05do-postgres-1", "psql", "-U", "fin05", "-d", "fin05", "-tAc", sql],
        capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"không đếm được: {(r.stderr or r.stdout)[:200]}"
    return {l.split("|")[0]: int(l.split("|")[1]) for l in r.stdout.splitlines() if "|" in l}


@pytest.fixture
def duong_cua_luot():
    """Trả một hàm `(phản_hồi) -> "nhe" | "day_du"`. CHƯA CÀI ĐẶT ĐƯỢC.

    Đây là chỗ bất biến đứt, và nó `skip` với lý do là **thiếu NĂNG LỰC thật**,
    không phải skip cho qua chuyện (Luật 6): phản hồi hiện không mang trường nào
    nói lượt đó đi đường nào, nên **không quy được** một `Δ` cho một đường.
    """
    pytest.skip(
        "THIẾU DẤU ĐƯỜNG. Phản hồi /agent/chat chưa có trường phân biệt lượt đi "
        "đường nhẹ hay đường đầy đủ. Không có nó, Δ=0 KHÔNG phân biệt được "
        "'đường nhẹ không ghi' với 'đường đầy đủ không có gì để ghi' — assertion "
        "trùng trạng thái mặc định (Luật 1). Xem docstring: hai cách chữa đã đề "
        "xuất, quyết định thuộc PO/coder."
    )


def test_luot_don_di_duong_nhe_KHONG_tao_ban_ghi_nghiep_vu(duong_cua_luot):
    """`"alo"` ⟹ đi đường nhẹ ⟹ Δcomplaints = Δtickets = 0.

    Chỉ có nghĩa khi `duong_cua_luot` khẳng định được lượt đó ĐÃ đi đường nhẹ.
    """
    raise AssertionError("không tới đây — fixture skip trước")


def test_DOI_CHUNG_luot_nghiep_vu_di_duong_day_du_CO_tao_ban_ghi(duong_cua_luot):
    """🔴 VẾ BẮT BUỘC — thiếu nó thì bất biến trên vô nghĩa.

    Một cài đặt *"đường nhẹ chặn mọi ghi"* sẽ làm test trên xanh **kể cả khi nó
    chặn nhầm cả đường đầy đủ**. Ca này chứng minh `Δ ≠ 0` **vẫn đạt tới được** —
    tức guardrail có hiệu lực mà không quá rộng (Luật 2).
    """
    raise AssertionError("không tới đây — fixture skip trước")


def test_dau_duong_phai_PHAN_BIET_duoc_hai_duong(duong_cua_luot):
    """Bản thân DẤU ĐƯỜNG cũng phải được canh.

    Một dấu luôn trả `"day_du"` sẽ làm test 1 `skip`/xanh vĩnh viễn mà không ai
    biết; một dấu luôn trả `"nhe"` sẽ làm ca đối chứng đỏ vì lý do sai. Dấu là
    **thước**, và thước cũng cần được canh (Luật 7).
    """
    raise AssertionError("không tới đây — fixture skip trước")
