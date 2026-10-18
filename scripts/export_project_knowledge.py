#!/usr/bin/env python3
"""export_project_knowledge.py — đóng gói nguồn sự thật để upload lên
Project knowledge của Claude Desktop (dự án "fin05").

BỐI CẢNH
--------
4 vai (PO · bảo mật · tester · UX/UI) là 4 chat riêng trong CÙNG một Project
trên Claude Desktop. Chat trên Desktop KHÔNG đọc được thư mục repo này, nhưng
mọi chat trong cùng Project đều thấy **kho kiến thức chung** của Project.

Hệ quả: upload MỘT LẦN → cả 4 vai cùng thấy. Không phải dán lại cho từng chat.

RỦI RO PHẢI CHẶN
----------------
Kho kiến thức KHÔNG tự đồng bộ với repo. Sửa contract trong repo mà quên
upload lại ⟹ cả 4 vai âm thầm làm việc trên thông tin chết — đúng vấn đề gốc
mà toàn bộ cơ chế này sinh ra để chặn, chỉ là dịch sang một tầng khác.

Cách chặn: mỗi file xuất ra mang DẤU PHIÊN BẢN (hash contract + ngày xuất), và
có file `00-SYNC-VERSION.md` ghi toàn bộ hash. Bất cứ lúc nào cũng hỏi được
một chat bất kỳ: "dấu phiên bản bạn đang thấy là gì?" rồi so với repo bằng
`python scripts/check_contracts.py`. Lệch ⟹ kho kiến thức đã cũ, upload lại.

DÙNG
----
    python scripts/export_project_knowledge.py
    open project-knowledge/          # rồi kéo thả toàn bộ vào Project knowledge
"""

from __future__ import annotations

import datetime as dt
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "project-knowledge"

# Thứ tự có chủ đích: tên file bắt đầu bằng số để kho kiến thức hiển thị đúng
# thứ tự đọc — hiến pháp trước, nguồn sự thật sau, trạng thái cuối.
BUNDLE: list[tuple[str, str]] = [
    ("01-HIEN-PHAP.md", "CLAUDE.md"),
    ("02-contract-authority-matrix.yaml", "contracts/authority-matrix.yaml"),
    ("03-contract-resolution-state-machine.yaml", "contracts/resolution-state-machine.yaml"),
    ("04-contract-agent-tools.yaml", "contracts/agent-tools.yaml"),
    ("05-QUYET-DINH-ADR.md", "docs/DECISIONS.md"),
    ("06-TRANG-THAI-HIEN-TAI.md", "docs/STATE.md"),
]

VAI = ["po", "security", "tester", "ux-ui"]


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:12]


def git_commit() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=ROOT, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "(không rõ)"
    except Exception:  # noqa: BLE001
        return "(không rõ)"


def main() -> int:
    if not (ROOT / "contracts").is_dir():
        sys.exit("Không thấy contracts/ — chạy script này ở gốc repo.")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    ngay = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = git_commit()
    hashes: dict[str, str] = {}

    for ten_ra, source in BUNDLE:
        src = ROOT / source
        if not src.exists():
            print(f"  BỎ QUA (thiếu): {source}")
            continue
        content_text = src.read_text(encoding="utf-8")
        h = hash_file(src)
        hashes[source] = h

        dau = (
            f"<!-- DẤU PHIÊN BẢN — sinh bởi scripts/export_project_knowledge.py\n"
            f"     nguồn: {source}\n"
            f"     hash: {h}\n"
            f"     xuất lúc: {ngay}  ·  commit: {commit}\n"
            f"     Đây là BẢN SAO. Nguồn sự thật là file trong repo.\n"
            f"     Nghi ngờ đã cũ? Hỏi PO chạy: python scripts/check_contracts.py -->\n\n"
        )
        if ten_ra.endswith(".yaml"):
            dau = dau.replace("<!--", "#").replace("-->", "").replace("\n     ", "\n#   ")
        (OUT / ten_ra).write_text(dau + content_text, encoding="utf-8")
        print(f"  {ten_ra:<45} ← {source}  @{h}")

    # ---- File giới thiệu dự án cho mục đích KHÁC (dựng slide, không phải làm
    # việc phát triển) — tự chứa, KHÔNG đi qua vòng lặp BUNDLE ở trên vì CỐ Ý
    # không mang dấu phiên bản/không vào bảng hash 00-SYNC-VERSION.md: bảng đó
    # canh NGUỒN SỰ THẬT (contract/ADR/STATE), lệch ở đó là nguy hiểm; file này
    # là tài liệu trình bày, lệch thì viết lại, không ai làm việc trên nó.
    #
    # `gate/` là thư mục PO thật có thể xoá bất cứ lúc nào (dùng-rồi-bỏ) — bắt
    # buộc `if exists()`, không được để thiếu file này làm cả script chết.
    gioi_thieu = ROOT / "gate" / "07-project-knowledge.md"
    co_gioi_thieu = gioi_thieu.exists()
    if co_gioi_thieu:
        shutil.copy(gioi_thieu, OUT / "07-GIOI-THIEU-DU-AN.md")
        print(f"  {'07-GIOI-THIEU-DU-AN.md':<45} ← gate/07-project-knowledge.md")
    else:
        print("  BỎ QUA 07 — không có gate/ (thư mục dùng-rồi-bỏ, không bắt buộc)")

    # ---- File đồng bộ: thứ dùng để phát hiện kho kiến thức đã cũ ----
    table_rows = "\n".join(f"| `{k}` | `{v}` |" for k, v in sorted(hashes.items()))
    (OUT / "00-SYNC-VERSION.md").write_text(
        f"""# DẤU ĐỒNG BỘ — kho kiến thức Project "fin05"

**Xuất lúc:** {ngay}
**Commit repo:** `{commit}`

Mọi chat trong Project này đang đọc bản sao được chụp tại thời điểm trên.

## Hash nguồn

| File nguồn trong repo | Hash |
|---|---|
{table_rows}

## Cách kiểm kho kiến thức có còn mới không

Bất cứ lúc nào nghi ngờ, hỏi **bất kỳ chat nào** trong Project:

> Dấu đồng bộ trong tài liệu `00-SYNC-VERSION.md` bạn đang thấy là commit nào,
> xuất lúc nào?

Rồi ở máy có repo, chạy:

```bash
python scripts/check_contracts.py     # in hash contract hiện tại
git rev-parse --short HEAD            # commit hiện tại
```

**Lệch nhau ⟹ kho kiến thức đã cũ.** Chạy lại:

```bash
python scripts/export_project_knowledge.py
```

rồi xoá toàn bộ file cũ trong Project knowledge và upload lại thư mục
`project-knowledge/`.

## Quy tắc bắt buộc cho mọi vai

Nếu bạn (một chat trong Project này) phát hiện tài liệu mâu thuẫn với thứ
người dùng mô tả, hoặc mâu thuẫn giữa hai tài liệu với nhau:

**DỪNG LẠI VÀ NÓI RA.** Không tự chọn bên nào có vẻ đúng hơn. Mâu thuẫn gần
như luôn có nghĩa kho kiến thức đã cũ so với code thật — và suy đoán để lấp
chỗ trống chính là thứ sinh ra vấn đề phân mảnh ngay từ đầu.

## Thứ KHÔNG có trong kho này

Kho kiến thức chỉ chứa **đặc tả**, không chứa code. Cố ý:

- Không có `src/` — tester phải viết test từ contract, không phản chiếu code.
- Không có kết quả test — luôn hỏi PO chạy thật, đừng tin con số trong tài liệu.
- Không có file test — tránh vai này sửa test của vai kia mà không ai biết.
""",
        encoding="utf-8",
    )
    print(f"  {'00-SYNC-VERSION.md':<45} ← (sinh mới)")

    # ---- Lời mở đầu cho từng vai, dán vào tin nhắn đầu của chat tương ứng ----
    thu_muc_vai = OUT / "loi-mo-dau-cho-tung-chat"
    thu_muc_vai.mkdir()
    for v in VAI:
        agent_md = ROOT / ".claude" / "agents" / f"{v}.md"
        if not agent_md.exists():
            continue
        content_text = agent_md.read_text(encoding="utf-8")
        if content_text.startswith("---"):
            content_text = content_text.split("---", 2)[-1].strip()
        (thu_muc_vai / f"{v}.md").write_text(
            f"""Bạn là vai **{v}** trong dự án FIN-05.

Kho kiến thức của Project này đã có: hiến pháp (5 ràng buộc cứng), 3 contract
nguồn sự thật, nhật ký quyết định (ADR), và trạng thái hiện tại. **Đọc chúng
trước khi làm bất cứ việc gì.** Bắt đầu bằng `00-SYNC-VERSION.md`.

---

{content_text}

---

## Việc đầu tiên của phiên này

Trả lời NGẮN 3 ý để xác nhận đã đọc:

a. Vai của bạn được ghi vào thư mục nào, và KHÔNG được ghi vào đâu?
b. Ràng buộc cứng nào công việc sắp tới của bạn dễ chạm phải nhất?
c. Một điểm bạn thấy **mâu thuẫn hoặc thiếu** thông tin để làm việc.

Ý (c) bắt buộc phải có nội dung. Trả lời "đã hiểu, không thắc mắc" là dấu hiệu
chưa đọc kỹ — hãy đọc lại rồi nêu ít nhất một điểm.

Kèm theo: nêu **commit và thời điểm xuất** ghi trong `00-SYNC-VERSION.md` bạn
đang thấy, để PO đối chiếu xem kho kiến thức còn mới không.
""",
            encoding="utf-8",
        )
    print(f"  loi-mo-dau-cho-tung-chat/    ← {len(VAI)} file ({', '.join(VAI)})")

    # ---- Lời nhắc thu hoạch chat cũ — chỉ cần khi chuyển đổi lần đầu ----
    harvest = ROOT / "scripts" / "harvest_prompt.md"
    if harvest.exists():
        shutil.copy(harvest, thu_muc_vai / "00-THU-HOACH-CHAT-CU.md")
        print(f"  {'loi-mo-dau-cho-tung-chat/00-THU-HOACH-CHAT-CU.md':<45} ← scripts/harvest_prompt.md")

    so_file_goc = len(BUNDLE) + 1 + (1 if co_gioi_thieu else 0)  # BUNDLE + 00-SYNC-VERSION + [07 nếu có]
    print(f"""
{'=' * 74}
XONG. Thư mục: {OUT}
{'=' * 74}

CÁCH DÙNG TRÊN CLAUDE DESKTOP

1. Mở Project "fin05" → mục Project knowledge.
2. XOÁ HẾT file cũ (quan trọng — để lẫn bản cũ còn tệ hơn không có, vì các
   vai sẽ đọc phải contract đã chết mà không biết).
3. Kéo thả {so_file_goc} file ở gốc thư mục `project-knowledge/` vào
   ({'có' if co_gioi_thieu else 'không có'} `07-GIOI-THIEU-DU-AN.md` lần xuất này).
   KHÔNG upload thư mục `loi-mo-dau-cho-tung-chat/` — nội dung đó dành để dán
   vào từng chat, không phải kiến thức chung.
4. Với MỖI chat vai: dán nội dung file tương ứng trong
   `loi-mo-dau-cho-tung-chat/` làm tin nhắn đầu tiên.

SAU NÀY, MỖI KHI SỬA CONTRACT / ADR / STATE:
   python scripts/export_project_knowledge.py   →  upload lại (bước 2-3)
Không cần dán lại lời mở đầu cho từng chat.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
