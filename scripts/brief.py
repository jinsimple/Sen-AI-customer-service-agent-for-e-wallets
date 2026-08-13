#!/usr/bin/env python3
"""brief.py — sinh gói tóm tắt NGẮN, DÁN ĐƯỢC cho một phiên Claude bất kỳ.

VÌ SAO CẦN FILE NÀY
-------------------
`CLAUDE.md` + `.claude/agents/` chỉ tự nạp cho phiên **Claude Code chạy trong
chính thư mục repo này**. Nếu một vai (QA/QC, UX/UI, Tester...) đang chạy ở
nơi KHÔNG đọc được repo — cửa sổ chat riêng trên claude.ai, máy khác, hoặc
Claude Desktop chưa mở thư mục này — thì nó không thấy gì cả, và ta quay lại
đúng vấn đề cũ: phải chép tay tóm tắt cho nhau.

File này là cầu nối: sinh ra một khối văn bản gọn, tự chứa, dán thẳng vào đầu
phiên chat của vai đó. Nội dung được TRÍCH TỰ ĐỘNG từ nguồn sự thật
(`contracts/`, `docs/STATE.md`, `docs/DECISIONS.md`, kết quả test bất biến),
nên không bao giờ là bản chép tay lỗi thời.

DÙNG
----
    python scripts/brief.py tester        # gói cho vai tester
    python scripts/brief.py ux-ui         # gói cho vai UX/UI
    python scripts/brief.py security
    python scripts/brief.py po
    python scripts/brief.py --list        # xem các vai có sẵn
    python scripts/brief.py tester | pbcopy    # chép thẳng vào clipboard (macOS)

NGUYÊN TẮC THIẾT KẾ
-------------------
Gói này CỐ Ý ngắn. Dán cả `contracts/` vào chat sẽ đốt sạch ngân sách ngữ cảnh
của vai đó vào thứ nó chỉ cần một phần. Mỗi vai nhận đúng lát cắt của mình +
đường dẫn để hỏi thêm khi cần.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
DOCS = ROOT / "docs"
AGENTS = ROOT / ".claude" / "agents"


def _doc(name: str, max_lines: int | None = None) -> str:
    path = DOCS / name
    if not path.exists():
        return f"(thiếu docs/{name})"
    text = path.read_text(encoding="utf-8")
    if max_lines:
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines]) + f"\n… (còn {len(lines) - max_lines} dòng, đọc docs/{name})"
    return text.strip()


def _adr_gan_nhat(n: int = 5) -> str:
    """Lấy n ADR cuối — phần quan trọng nhất chống 'tối ưu ngược' quyết định cũ."""
    path = DOCS / "DECISIONS.md"
    if not path.exists():
        return "(thiếu docs/DECISIONS.md)"
    khoi = [k for k in path.read_text(encoding="utf-8").split("\n## ") if k.startswith("ADR-")]
    if not khoi:
        return "(chưa có ADR nào)"
    return "\n\n".join("## " + k.strip() for k in khoi[-n:])


def _hien_phap() -> str:
    """5 ràng buộc cứng — mục 2 của CLAUDE.md, ai cũng phải biết."""
    path = ROOT / "CLAUDE.md"
    if not path.exists():
        return "(thiếu CLAUDE.md)"
    text = path.read_text(encoding="utf-8")
    try:
        start = text.index("## 2. NĂM RÀNG BUỘC CỨNG")
        end = text.index("## 3. ")
        return text[start:end].strip()
    except ValueError:
        return "(không tìm thấy mục ràng buộc cứng trong CLAUDE.md)"


def _trang_thai_test() -> str:
    """Chạy THẬT test bất biến — không khai báo suông là 'đang xanh'."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_invariants.py", "-q", "--no-header"],
            cwd=ROOT, capture_output=True, text=True, timeout=180,
            env={**__import__("os").environ,
                 "LANGCHAIN_TRACING_V2": "false", "LANGSMITH_TRACING": "false"},
        )
        dong = [d for d in r.stdout.splitlines() if "passed" in d or "failed" in d or "error" in d]
        ket_qua = dong[-1].strip() if dong else "(không đọc được kết quả)"
        return f"{'XANH' if r.returncode == 0 else 'ĐỎ'} — {ket_qua}"
    except Exception as e:  # noqa: BLE001 — briefing không được chết vì test lỗi
        return f"(không chạy được: {type(e).__name__}: {e})"


def _contract_stale() -> str:
    try:
        r = subprocess.run(
            [sys.executable, "scripts/check_contracts.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            return "sạch — không có artifact lỗi thời"
        return f"CÓ VẤN ĐỀ (exit {r.returncode}):\n" + "\n".join(
            d for d in r.stdout.splitlines() if "LỖI THỜI" in d or "CHƯA CHỐT" in d or "  " in d
        )[:600]
    except Exception as e:  # noqa: BLE001
        return f"(không chạy được: {type(e).__name__})"


def _vai(ten: str) -> str:
    path = AGENTS / f"{ten}.md"
    if not path.exists():
        co_san = sorted(p.stem for p in AGENTS.glob("*.md"))
        sys.exit(f"Không có vai '{ten}'. Hiện có: {', '.join(co_san)}")
    text = path.read_text(encoding="utf-8")
    # Bỏ frontmatter YAML — phần đó dành cho Claude Code, không cần trong chat.
    if text.startswith("---"):
        text = text.split("---", 2)[-1]
    return text.strip()


def _contract_can_thiet(ten_vai: str) -> list[str]:
    """Mỗi vai chỉ cần một lát cắt — dán cả contracts/ là phí ngân sách ngữ cảnh."""
    return {
        "tester": ["authority-matrix.yaml", "resolution-state-machine.yaml", "agent-tools.yaml"],
        "security": ["authority-matrix.yaml", "agent-tools.yaml"],
        "ux-ui": ["authority-matrix.yaml", "resolution-state-machine.yaml"],
        "tech-lead": ["authority-matrix.yaml", "resolution-state-machine.yaml", "agent-tools.yaml"],
        "po": [],
        "ba": ["authority-matrix.yaml"],
        "critic": ["authority-matrix.yaml", "resolution-state-machine.yaml", "agent-tools.yaml"],
    }.get(ten_vai, [])


def main() -> int:
    ap = argparse.ArgumentParser(description="Sinh gói tóm tắt dán được cho một phiên Claude")
    ap.add_argument("vai", nargs="?", help="tên vai (tester, ux-ui, security, po, tech-lead, ba, critic)")
    ap.add_argument("--list", action="store_true", help="liệt kê các vai có sẵn")
    ap.add_argument("--full-contracts", action="store_true",
                    help="nhúng nguyên văn contract thay vì chỉ liệt kê đường dẫn "
                         "(dùng khi phiên kia KHÔNG đọc được repo)")
    args = ap.parse_args()

    if args.list:
        for p in sorted(AGENTS.glob("*.md")):
            mo_ta = ""
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("description:"):
                    mo_ta = line[len("description:"):].strip()[:90]
                    break
            print(f"  {p.stem:<12} {mo_ta}")
        return 0

    if not args.vai:
        ap.error("thiếu tên vai (hoặc dùng --list)")

    vai = args.vai
    can = _contract_can_thiet(vai)

    print("=" * 78)
    print(f"GÓI BÀN GIAO PHIÊN — VAI: {vai.upper()}   ·   dự án FIN-05")
    print("=" * 78)
    print()
    print("Đọc hết khối này TRƯỚC KHI làm bất cứ việc gì. Đây là bản trích tự động từ")
    print("nguồn sự thật của repo, không phải bản tóm tắt chép tay — nếu thấy mâu thuẫn")
    print("với thứ bạn nhớ từ phiên trước, TIN KHỐI NÀY và nói ra điểm mâu thuẫn.")
    print()

    print("─" * 78)
    print("1. RÀNG BUỘC CỨNG — vi phạm là từ chối, không thương lượng")
    print("─" * 78)
    print(_hien_phap())
    print()

    print("─" * 78)
    print("2. VAI CỦA BẠN TRONG PHIÊN NÀY")
    print("─" * 78)
    print(_vai(vai))
    print()

    print("─" * 78)
    print("3. TRẠNG THÁI HIỆN TẠI (docs/STATE.md)")
    print("─" * 78)
    print(_doc("STATE.md", max_lines=60))
    print()

    print("─" * 78)
    print("4. NĂM QUYẾT ĐỊNH GẦN NHẤT — đọc kỹ mục 'lý do BÁC BỎ'")
    print("─" * 78)
    print(_adr_gan_nhat(5))
    print()

    print("─" * 78)
    print("5. SỨC KHOẺ HỆ THỐNG (chạy thật lúc sinh gói này)")
    print("─" * 78)
    print(f"Test bất biến : {_trang_thai_test()}")
    print(f"Contract      : {_contract_stale()}")
    print()

    print("─" * 78)
    print("6. NGUỒN SỰ THẬT BẠN ĐƯỢC DÙNG")
    print("─" * 78)
    if not can:
        print("Vai này làm việc từ docs/ và PRD, không cần đọc contract chi tiết.")
    elif args.full_contracts:
        for ten in can:
            path = CONTRACTS / ten
            print(f"\n<<<<<< contracts/{ten} >>>>>>")
            print(path.read_text(encoding="utf-8").strip() if path.exists() else "(THIẾU FILE)")
    else:
        for ten in can:
            print(f"  contracts/{ten}")
        print()
        print("Phiên này đọc được repo → mở thẳng các file trên.")
        print("Nếu KHÔNG đọc được repo, chạy lại lệnh với --full-contracts để nhúng nguyên văn.")
    print()

    print("─" * 78)
    print("7. VIỆC ĐẦU TIÊN")
    print("─" * 78)
    print("Xác nhận đã đọc bằng cách trả lời NGẮN 3 ý:")
    print("  a. Vai của bạn được GHI vào những thư mục nào (và KHÔNG được ghi vào đâu)")
    print("  b. Một ràng buộc cứng mà công việc sắp tới của bạn dễ chạm phải nhất")
    print("  c. Một điểm trong gói này bạn thấy MÂU THUẪN hoặc THIẾU thông tin để làm việc")
    print()
    print("Ý (c) là bắt buộc — trả lời 'đã hiểu, không có gì thắc mắc' là dấu hiệu chưa đọc kỹ.")
    print("Thiếu thông tin thì DỪNG và hỏi, tuyệt đối không suy đoán để lấp chỗ trống.")
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
