#!/usr/bin/env python3
"""pre-commit — CẢNH BÁO khi commit chạm vùng ghi của nhiều vai, đọc trực
tiếp bảng §4 trong CLAUDE.md (KHÔNG hardcode bản sao — sửa CLAUDE.md là đủ,
không cần sửa file này TRỪ hai ngoại lệ viết tay khai rõ bên dưới).

VÌ SAO CẢNH BÁO CHỨ KHÔNG CHẶN: mục tiêu là bắt người commit NHÌN THẤY thứ
mình sắp cuốn theo (`git add -A` cuốn WIP người khác — đã xảy ra ba lần
trong một tuần trên cây dùng chung, kể cả sau khi luật pathspec đã ban
hành), không phải dựng thêm rào. Có ca hợp lệ để ghi ngoài vùng (PO dán hộ
Coder một dòng, hai lần trong ngày 24/08).

CỐ Ý KHÔNG ĐOÁN VAI NGƯỜI COMMIT — không có biến môi trường/tín hiệu nào
khai vai đáng tin (tên phiên KHÔNG suy ra vai, đã ghi nhiều lần trong dự
án), và một cơ chế đoán sai vai sẽ bị phớt lờ trong ba ngày rồi tệ hơn
không có gì. Hai lớp bên dưới đều KHÔNG cần biết ai đang commit:

  Lớp 1 (CẢNH BÁO ĐA VÙNG) — bắt commit trộn ≥2 vùng KHÔNG có vai chung nào
  giải thích được cả commit (công thức: giao của tập-vai-khớp mọi file
  staged rỗng). Bắt được kiểu sự cố `git add -A` cuốn nhầm.

  Lớp 2 (FYI VÙNG) — luôn in vùng khớp của MỌI file staged, kể cả commit
  một vùng. Không đoán đúng/sai — chỉ hiển thị sự thật để mắt người tự đối
  chiếu. Đây là lớp DUY NHẤT có cơ hội bắt ca "chỉ một vùng nhưng SAI vai"
  (vd Coder soạn xong đúng 2 file docs/ định tick hộ PO) — và chỉ bắt được
  NẾU người đọc dòng FYI, không phải cơ chế tự động.

GIỚI HẠN ĐÃ KHAI TRƯỚC (đọc để biết trần năng lực, không phải để vá thêm):
- Không bắt được ca "một vùng nhưng sai vai" nếu người commit không đọc
  FYI — không có cách nào bắt tự động mà không đoán vai.
- Hai ngoại lệ viết tay bên dưới (`_NGOAI_LE_TAY`) vì §4 mô tả bằng lời
  tiếng Việt tự nhiên, không phải glob thuần — sửa §4 thêm ngoại lệ tương
  tự (một pattern cụ thể hơn NẰM BÊN TRONG vùng của vai khác, không viết
  trong backtick) thì PHẢI tự thêm dòng vào đây, hook không tự suy ra được.
"""
from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"

# Hai ngoại lệ VIẾT TAY — §4 diễn đạt bằng lời, không phải glob trong
# backtick, nên trích tự động (xem _trich_bang) bỏ sót. Cả hai đều là một
# pattern CỤ THỂ HƠN nằm bên trong vùng `docs/` chung của `po`.
_NGOAI_LE_TAY: list[tuple[str, str]] = [
    ("docs/nhat-ky/so-giam-ho-anh.md", "devops"),  # §4: "...sổ giám hộ ảnh"
]
# *.md "ở gốc" (po) và *.html "wireframe" không giới hạn thư mục (ux-ui) —
# cụm từ tự nhiên đi kèm backtick, hook không tự suy được "ở gốc" nghĩa là
# maxdepth=0. Khai cứng luôn, cùng lý do.
_MAXDEPTH_0: dict[str, str] = {"*.md": "po"}


def _trich_bang() -> dict[str, list[str]]:
    """Vai -> danh sách pattern (trong backtick) ở cột "Được ghi", §4."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    m = re.search(r"^## 4\..*?\n(.*?)\n## 5\.", text, re.S | re.M)
    if not m:
        return {}
    vung: dict[str, list[str]] = {}
    for dong in m.group(1).splitlines():
        if not dong.startswith("|"):
            continue
        column = [c.strip() for c in dong.strip("|").split("|")]
        if len(column) < 2 or not column[0].startswith("`"):
            continue
        vai = column[0].strip("`")
        pattern = re.findall(r"`([^`]+)`", column[1])
        vung.setdefault(vai, []).extend(pattern)
    return vung


def _khop(duong_dan: str, pattern: str) -> bool:
    if pattern in _MAXDEPTH_0:
        return "/" not in duong_dan and fnmatch.fnmatch(duong_dan, pattern)
    if pattern.endswith("/"):
        return duong_dan.startswith(pattern)
    return fnmatch.fnmatch(duong_dan, pattern) or fnmatch.fnmatch(
        duong_dan, f"*/{pattern}"
    )


def _vai_khop(duong_dan: str, vung: dict[str, list[str]]) -> set[str]:
    outcome = {vai for route, vai in _NGOAI_LE_TAY if route == duong_dan}
    if outcome:
        return outcome
    for vai, patterns in vung.items():
        for p in patterns:
            if _khop(duong_dan, p):
                outcome.add(vai)
                break
    return outcome


def main() -> int:
    try:
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except Exception:  # noqa: BLE001 — hook KHÔNG BAO GIỜ được chặn commit
        return 0
    staged = [f for f in staged if f]
    if not staged:
        return 0

    vung = _trich_bang()
    if not vung:
        return 0  # không đọc được §4 -> im lặng, đừng cảnh báo mù

    khop_theo_file = {f: _vai_khop(f, vung) for f in staged}

    print("\n[vung-ghi] Vùng §4 của các file trong commit này (chỉ để bạn đối chiếu, không chặn):")
    for f, vais in khop_theo_file.items():
        nhan = ", ".join(sorted(vais)) if vais else "(không khớp vùng nào đã khai)"
        print(f"  {f}  ->  {nhan}")

    tat_ca_vai = [v for v in khop_theo_file.values() if v]
    if tat_ca_vai:
        giao = set.intersection(*tat_ca_vai) if len(tat_ca_vai) > 1 else tat_ca_vai[0]
        if not giao:
            print(
                "\n[vung-ghi] 🔴 KHÔNG có vai chung nào giải thích được cả "
                "commit này — các file trải trên nhiều vùng §4 KHÔNG chồng "
                "lấn. Kiểm lại có đang cuốn nhầm việc dở của người khác "
                "không.\n"
                "[vung-ghi] LÝ DO THẬT hay gặp nhất KHÔNG PHẢI `git add -A` —\n"
                "[vung-ghi] staging là một GIỎ CHUNG: người khác `git add` "
                "trước bạn, bạn `git add` đúng pathspec của MÌNH, nhưng "
                "`git commit` (không pathspec) vẫn đổ CẢ GIỎ, kể cả phần "
                "không phải của bạn. [ĐO 24/08, PO-agent tự bắt: `491c91d`]\n"
                "[vung-ghi] Nếu KHÔNG cố ý, đừng Ctrl-C rồi đoán — commit lại "
                "CHỈ đúng phần của bạn:"
            )
            for vai in sorted(giao_ung_vien := set().union(*tat_ca_vai)):
                file_cua_vai = [f for f, v in khop_theo_file.items() if vai in v]
                if len(file_cua_vai) == len(staged):
                    continue  # vai này đã giải thích hết -> không phải thủ phạm lệch
                mau = " ".join(f'"{f}"' for f in file_cua_vai)
                print(f'[vung-ghi]   git commit -- {mau}   # phần thuộc vai {vai}')
            print(
                "[vung-ghi] Rồi `git status` xem staging còn gì sót lại của "
                "người khác — ĐỪNG commit tiếp, để họ tự commit phần của họ."
            )
    print()
    return 0  # LUÔN — cảnh báo, không chặn


if __name__ == "__main__":
    sys.exit(main())
