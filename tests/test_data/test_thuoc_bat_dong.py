"""THƯỚC BẤT ĐỘNG — `gen_dataset.py` không được ghi đè `eval/golden_set.jsonl`.

Nguồn: sự cố đêm 14→15/08 (sổ PO `2ce93b1`). `scripts/gen_dataset.py` có
đường ghi THỨ HAI vào `eval/` bất kể `--out` trỏ đi đâu, nên một lượt sinh
dataset bình thường **âm thầm ghi đè bộ case** — xoá mất nhãn
`must_offer_before_creating_ticket` của 4 case B2 mà PO đã duyệt (`aa5d593`),
ngay giữa lúc một gói đo đang chạy.

VÌ SAO ĐÂY LÀ LỖI NGHIÊM TRỌNG CHỨ KHÔNG PHẢI PHIỀN PHỨC: `golden_set.jsonl`
là **thước đo** của cả dự án. Ghi đè nó không làm hỏng một tính năng — nó làm
mọi phép so sánh trước/sau trở nên vô nghĩa mà **không ai nhận ra**, vì hai
lượt vẫn "40 case", vẫn so được, vẫn ra một cặp số trông hợp lệ. Sự cố này chỉ
lộ ra nhờ dấu thước băm-nội-dung (`eval/measure_quality.py::dau_thuoc`); trước
khi có nó, cùng sự việc sẽ hoàn toàn vô hình.

Coder thêm cờ `--cho-phep-ghi-de-thuoc` để ghi đè trở thành hành vi PHẢI CỐ Ý.
Test này giữ cho lệnh cấm đó không bị gỡ mất — cấm-bằng-cấu-trúc mà không có
test canh thì chỉ là một dòng code chờ ai đó sửa lại cho tiện.

AN TOÀN CỦA CHÍNH TEST NÀY (điểm thiết kế quan trọng nhất ở đây): test phải
CHẠY THẬT `gen_dataset` mới chứng minh được điều nó khẳng định — mà chạy thật
chính là hành vi đang phá thước. Nên nó luôn: **chụp nội dung trước → chạy →
so → KHÔI PHỤC → mới assert**. Khôi phục nằm trong `finally`, xảy ra kể cả khi
assert hỏng hoặc script ném lỗi. Một test canh dữ liệu mà tự làm hỏng dữ liệu
khi sản phẩm còn lỗi thì tệ hơn không có test.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
GOLDEN = REPO / "eval" / "golden_set.jsonl"
GEN = REPO / "scripts" / "gen_dataset.py"
CO_CHO_PHEP = "--cho-phep-ghi-de-thuoc"


def _chay_gen_dataset(*extra_items: str) -> subprocess.CompletedProcess:
    """Chạy gen_dataset với `--out` trỏ vào thư mục tạm.

    KHÔNG truyền `--eval-out`: đường ghi thứ hai vào `eval/` dùng giá trị mặc
    định, và chính đường mặc định đó là thứ gây ra sự cố. Truyền `--eval-out`
    vào thư mục tạm sẽ làm test xanh mà không kiểm được gì — đúng lỗi
    "assertion trùng trạng thái mặc định" đã thành luật của dự án.
    """
    with tempfile.TemporaryDirectory(prefix="fin05_gen_") as tmp:
        return subprocess.run(
            [sys.executable, str(GEN), "--out", tmp, *extra_items],
            capture_output=True, text=True, timeout=300, cwd=REPO,
        )


def _cli_co_co_khong() -> bool:
    r = subprocess.run(
        [sys.executable, str(GEN), "--help"], capture_output=True, text=True, timeout=60, cwd=REPO
    )
    return CO_CHO_PHEP in r.stdout


@pytest.mark.slow
def test_gen_dataset_khong_co_co_thi_khong_duoc_dung_toi_golden_set():
    """Bất biến chính: một lượt sinh dataset bình thường phải để thước YÊN.

    Chạy thật ~20s (sinh trọn dataset) — chậm, nhưng đây là loại bất biến mà
    mock không chứng minh được gì: cái cần canh chính là hành vi ghi file thật
    của script thật.
    """
    if not GOLDEN.exists():
        pytest.skip("Chưa có eval/golden_set.jsonl để canh.")

    before = GOLDEN.read_bytes()
    try:
        outcome = _chay_gen_dataset()
        after = GOLDEN.read_bytes()
    finally:
        # KHÔI PHỤC TRƯỚC KHI ASSERT — kể cả khi script ném lỗi. Test này tồn
        # tại vì sản phẩm ĐANG ghi đè; nếu nó để lại hậu quả thì mỗi lần chạy
        # suite là một lần phá thước.
        if GOLDEN.read_bytes() != before:
            GOLDEN.write_bytes(before)

    # CỐ Ý KHÔNG assert `returncode == 0`. Bất biến cần canh là **thước bất
    # động**, không phải "lệnh chạy trót lọt". Coder chọn fail-fast: không cờ
    # thì gen_dataset TỪ CHỐI CHẠY (exit != 0) kèm hướng dẫn hai lối thoát —
    # thiết kế đó thoả bất biến này một cách mạnh hơn cả "chạy nhưng không
    # ghi". Ràng test vào returncode sẽ biến một lựa chọn thiết kế hợp lệ
    # thành đỏ oan, đúng kiểu test cản trở bản vá đúng.
    assert after == before, (
        "gen_dataset ĐÃ GHI ĐÈ eval/golden_set.jsonl dù không có cờ "
        f"`{CO_CHO_PHEP}`.\n"
        "Đây là đường phá thước của sự cố 14→15/08: bộ case bị sinh lại, mọi "
        "nhãn thêm tay (vd `must_offer_before_creating_ticket` của 4 case B2) "
        "biến mất, và cặp đo trước/sau thành vô nghĩa mà không ai nhận ra.\n"
        "(Test đã tự khôi phục file — không để lại hậu quả.)\n"
        f"[exit={outcome.returncode}] {(outcome.stderr or outcome.stdout)[-300:]}"
    )


@pytest.mark.slow
def test_gen_dataset_co_co_thi_duoc_phep_ghi_de():
    """Mặt NGƯỢC LẠI — lệnh cấm không được chặt tới mức không ai sinh lại được.

    Reseed là việc có thật và sắp làm (sửa khuyết tật `from_bank`). Nếu chỉ có
    test cấm mà không có test này, một bản vá "chặn cứng luôn" vẫn xanh, và
    người cần reseed sẽ phải sửa lại chính lệnh cấm — tức là gỡ nó.
    """
    if not _cli_co_co_khong():
        pytest.skip(
            f"`{CO_CHO_PHEP}` chưa có trong CLI — coder chưa thêm. Test cấm ở trên "
            "đã báo đúng tình trạng này rồi, không cần đỏ thêm lần nữa cho cùng một nguyên nhân."
        )

    before = GOLDEN.read_bytes()
    try:
        outcome = _chay_gen_dataset(CO_CHO_PHEP)
        after = GOLDEN.read_bytes()
    finally:
        if GOLDEN.read_bytes() != before:
            GOLDEN.write_bytes(before)

    assert outcome.returncode == 0, f"gen_dataset lỗi khi có cờ: {outcome.stderr[-400:]}"
    assert after != before or b"golden" in outcome.stdout.encode(), (
        f"Có cờ `{CO_CHO_PHEP}` mà golden_set vẫn không được ghi — lệnh cấm chặt quá "
        "tay, người cần reseed sẽ buộc phải gỡ nó."
    )


@pytest.mark.slow
def test_sinh_lai_du_lieu_thuong_van_chay_duoc_qua_eval_out_tam():
    """Lối thoát NHẸ phải còn dùng được — nếu không, lệnh cấm là vật cản.

    Nhu cầu thật và thường xuyên: chỉ cần sinh lại `data/generated/`, không
    đụng gì tới thước. Nếu đường này cũng bị chặn thì người ta sẽ đi đường
    `--cho-phep-ghi-de-thuoc` cho xong việc — tức lệnh cấm tự đẩy người dùng
    sang đúng hành vi nguy hiểm mà nó sinh ra để chặn.

    Đây là mặt thứ ba của cùng một ràng buộc, cạnh "cấm khi không cố ý" và
    "cho phép khi cố ý": **đường an toàn phải là đường DỄ ĐI NHẤT**.
    """
    before = GOLDEN.read_bytes()
    with tempfile.TemporaryDirectory(prefix="fin05_evalout_") as tmp_eval:
        try:
            outcome = _chay_gen_dataset("--eval-out", tmp_eval)
            after = GOLDEN.read_bytes()
            sinh_ra = sorted(p.name for p in Path(tmp_eval).glob("*.jsonl"))
        finally:
            if GOLDEN.read_bytes() != before:
                GOLDEN.write_bytes(before)

    assert outcome.returncode == 0, (
        "Sinh dataset với `--eval-out` trỏ thư mục tạm PHẢI chạy được — đây là "
        f"đường an toàn cho nhu cầu thường ngày. stderr: {outcome.stderr[-400:]}"
    )
    assert after == before, "Đã trỏ --eval-out ra ngoài mà thước vẫn bị đụng."
    assert "golden_set.jsonl" in sinh_ra, (
        f"--eval-out không sinh ra golden_set trong thư mục được chỉ định: {sinh_ra}"
    )
