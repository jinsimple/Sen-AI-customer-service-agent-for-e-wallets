#!/usr/bin/env python3
"""
check_contracts.py — phát hiện artifact đã lỗi thời so với contracts/

Đây là cơ chế thay thế cho việc bắt agent này viết file tóm tắt cho agent kia đọc.

CÁCH HOẠT ĐỘNG
--------------
1. Băm SHA256 (12 ký tự đầu) từng file trong contracts/  → đây là "phiên bản" của contract.
2. Mỗi artifact hạ nguồn (test, báo cáo bảo mật, US) khai báo nó được sinh từ phiên bản nào:

   Trong file Python:
       CONTRACT_VERSION = {
           "authority-matrix.yaml": "a1b2c3d4e5f6",
       }

   Trong file Markdown:
       <!-- CONTRACT_VERSION: authority-matrix.yaml=a1b2c3d4e5f6 -->

3. Hash khai báo ≠ hash hiện tại  →  artifact STALE  →  exit code 1  →  CI đỏ.
4. Ngoài ra so với baseline đã duyệt trong .claude/state/contract-hashes.json:
   contract đổi mà chưa chạy --update  →  cảnh báo "đổi chưa duyệt"  →  exit code 2.

DÙNG
----
    python scripts/check_contracts.py              # kiểm tra, dùng trong /standup và CI
    python scripts/check_contracts.py --verbose    # kèm chi tiết, dùng trong /impact
    python scripts/check_contracts.py --update     # chốt baseline SAU KHI PO duyệt thay đổi
    python scripts/check_contracts.py --stamp <file>  # in dòng khai báo để dán vào artifact mới

KHÔNG chạy --update để "cho hết đỏ". Đỏ nghĩa là có artifact thật sự cần làm lại.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"
STATE_FILE = ROOT / ".claude" / "state" / "contract-hashes.json"

# Nơi tìm artifact hạ nguồn. Thêm thư mục mới ở đây khi dự án lớn lên.
SCAN_DIRS = ["tests", "docs", "src", "eval", "frontend/e2e"]
SCAN_EXTS = {".py", ".md", ".yaml", ".yml", ".ts", ".js"}

HASH_LEN = 12

RE_PY_BLOCK = re.compile(r"CONTRACT_VERSION\s*=\s*\{(.*?)\}", re.S)
RE_PY_PAIR = re.compile(r"[\"']([\w.\-]+\.ya?ml)[\"']\s*:\s*[\"']([0-9a-f]{6,64})[\"']")
RE_MD_LINE = re.compile(r"CONTRACT_VERSION\s*:\s*([^\n\->]+)")
RE_MD_PAIR = re.compile(r"([\w.\-]+\.ya?ml)\s*=\s*([0-9a-f]{6,64})")

C_RED, C_YEL, C_GRN, C_DIM, C_OFF = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def _c(text: str, color: str) -> str:
    return f"{color}{text}{C_OFF}" if sys.stdout.isatty() else text


def hash_file(path: Path) -> str:
    """Băm nội dung đã chuẩn hoá xuống dòng, để đổi CRLF/LF không tính là đổi contract."""
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:HASH_LEN]


def current_contracts() -> dict[str, str]:
    if not CONTRACTS_DIR.is_dir():
        print(_c(f"LỖI: không thấy thư mục {CONTRACTS_DIR}", C_RED))
        sys.exit(3)
    out = {}
    for p in sorted(CONTRACTS_DIR.iterdir()):
        if p.is_file() and p.suffix in {".yaml", ".yml", ".json"}:
            out[p.name] = hash_file(p)
    return out


def load_baseline() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("contracts", {})
    except (json.JSONDecodeError, OSError):
        print(_c(f"CẢNH BÁO: {STATE_FILE} hỏng, coi như chưa có baseline", C_YEL))
        return {}


def save_baseline(contracts: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"contracts": contracts, "note": "Baseline đã được PO duyệt. Cập nhật qua --update."},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def declared_versions(path: Path) -> dict[str, str]:
    """Trích khai báo CONTRACT_VERSION từ một file artifact."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}
    if "CONTRACT_VERSION" not in text:
        return {}
    # Escape hatch cho tài liệu chỉ *nói về* cơ chế này (ví dụ HANDOFF-PROTOCOL.md).
    # Đặt dòng sau vào file để script bỏ qua:  check_contracts: ignore
    if re.search(r"check_contracts\s*:\s*ignore", text):
        return {}

    found: dict[str, str] = {}
    for block in RE_PY_BLOCK.findall(text):
        found.update(dict(RE_PY_PAIR.findall(block)))
    for line in RE_MD_LINE.findall(text):
        found.update(dict(RE_MD_PAIR.findall(line)))
    return found


def scan_artifacts() -> list[tuple[Path, dict[str, str]]]:
    results = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in SCAN_EXTS:
                decl = declared_versions(p)
                if decl:
                    results.append((p, decl))
    return results


def cmd_stamp(name: str, contracts: dict[str, str]) -> int:
    if name not in contracts:
        print(_c(f"Không có contract tên '{name}'. Hiện có: {', '.join(contracts) or '(trống)'}", C_RED))
        return 3
    h = contracts[name]
    print("# Dán vào đầu file test (Python):")
    print(f'CONTRACT_VERSION = {{\n    "{name}": "{h}",\n}}\n')
    print("<!-- Dán vào đầu file tài liệu (Markdown): -->")
    print(f"<!-- CONTRACT_VERSION: {name}={h} -->")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Phát hiện artifact lỗi thời so với contracts/")
    ap.add_argument("--update", action="store_true",
                    help="Chốt baseline mới SAU KHI thay đổi contract đã được duyệt")
    ap.add_argument("--verbose", "-v", action="store_true", help="In chi tiết từng artifact")
    ap.add_argument("--stamp", metavar="FILE", help="In dòng khai báo cho một contract")
    args = ap.parse_args()

    contracts = current_contracts()
    if args.stamp:
        return cmd_stamp(args.stamp, contracts)

    baseline = load_baseline()

    if args.update:
        save_baseline(contracts)
        print(_c(f"Đã chốt baseline cho {len(contracts)} contract:", C_GRN))
        for n, h in contracts.items():
            mark = "  (đổi)" if baseline.get(n) not in (None, h) else ""
            print(f"  {n:<32} {h}{mark}")
        print(_c("\nNhắc: artifact hạ nguồn vẫn phải tự cập nhật khai báo CONTRACT_VERSION.", C_DIM))
        return 0

    print(f"Contract hiện tại ({len(contracts)} file):")
    unapproved = []
    for n, h in contracts.items():
        old = baseline.get(n)
        if old is None:
            state, unapproved = _c("MỚI, chưa có baseline", C_YEL), unapproved + [n]
        elif old != h:
            state, unapproved = _c(f"ĐÃ ĐỔI (baseline {old})", C_YEL), unapproved + [n]
        else:
            state = _c("khớp baseline", C_DIM)
        print(f"  {n:<32} {h}  {state}")

    artifacts = scan_artifacts()
    stale: list[tuple[Path, str, str, str]] = []
    orphan: list[tuple[Path, str]] = []
    for path, decl in artifacts:
        for cname, dhash in decl.items():
            cur = contracts.get(cname)
            if cur is None:
                orphan.append((path, cname))
            elif cur != dhash:
                stale.append((path, cname, dhash, cur))

    def rel(p: Path) -> Path:
        return p.relative_to(ROOT)

    if args.verbose:
        print(f"\nĐã quét {len(artifacts)} artifact có khai báo CONTRACT_VERSION:")
        for path, decl in artifacts:
            flags = ", ".join(f"{k}={v}" for k, v in decl.items())
            print(f"  {rel(path)}  [{flags}]")

    print()
    if stale:
        print(_c(f"ARTIFACT LỖI THỜI ({len(stale)}) — cần làm lại:", C_RED))
        for path, cname, dhash, cur in stale:
            print(f"  {rel(path)}")
            print(f"      dựa trên {cname}@{dhash}, hiện tại là @{cur}")
        print(_c("\n  → Chạy /impact để biết ai phải làm lại gì.", C_DIM))
    else:
        print(_c("Không có artifact lỗi thời.", C_GRN))

    if orphan:
        print(_c(f"\nKHAI BÁO MỒ CÔI ({len(orphan)}) — trỏ tới contract không tồn tại:", C_YEL))
        for path, cname in orphan:
            print(f"  {rel(path)} → {cname}")

    if unapproved:
        print(_c(f"\nCONTRACT ĐỔI CHƯA CHỐT BASELINE: {', '.join(unapproved)}", C_YEL))
        print(_c("  → Nếu đã có ADR và PO đã duyệt: chạy --update.", C_DIM))
        print(_c("  → Nếu chưa: đây là thay đổi lén, phải quay lại quy trình ở CLAUDE.md §3.", C_DIM))

    if not artifacts:
        print(_c("\nCHÚ Ý: chưa artifact nào khai báo CONTRACT_VERSION.", C_YEL))
        print(_c("  Cơ chế phát hiện lệch đang KHÔNG hoạt động. Dùng --stamp để lấy dòng khai báo.", C_DIM))

    if stale:
        return 1
    if unapproved:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
