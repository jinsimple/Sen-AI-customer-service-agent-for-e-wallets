#!/usr/bin/env python3
"""
Submit .ai-log/session.jsonl to grading server.
Called by git pre-push hook or manually.

After a successful submit, the live log is rotated:
  - Moved into .ai-log/archive/YYYY-MM-DD.jsonl (appended, never overwritten)
  - The live session.jsonl is recreated empty by the next hook write

If the POST fails, the pending file is restored so nothing is lost.
"""
import json
import os
import shutil
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SERVER_URL = os.environ.get("AI_LOG_SERVER", "")
API_KEY = os.environ.get("AI_LOG_API_KEY", "")
LOG_DIR = Path(os.environ.get("AI_LOG_DIR", ".ai-log"))
LOG_FILE = LOG_DIR / "session.jsonl"
ARCHIVE_DIR = LOG_DIR / "archive"

# Match server-side MAX_BATCH_ENTRIES so we never get a 422.
# If the local file has more than this, we submit the oldest BATCH_LIMIT
# and leave the rest for the next push.
BATCH_LIMIT = 500


def _archive(pending: Path) -> None:
    """Append pending file to today's archive. Never overwrites existing data."""
    if not pending.exists() or pending.stat().st_size == 0:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_file = ARCHIVE_DIR / f"{today}.jsonl"
    with open(pending, "rb") as src, open(archive_file, "ab") as dst:
        shutil.copyfileobj(src, dst)


def _archive_entries(entries: list) -> None:
    """Append ONLY the submitted entries to today's archive.

    Must not archive the whole pending file: pending also holds leftover_lines
    (entries beyond BATCH_LIMIT) which get written back to LOG_FILE and picked
    up next push — archiving the whole file re-archives that leftover every run,
    inflating the archive by the leftover size each push.
    """
    if not entries:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_file = ARCHIVE_DIR / f"{today}.jsonl"
    with open(archive_file, "a", encoding="utf-8") as dst:
        for e in entries:
            dst.write(json.dumps(e, ensure_ascii=False) + "\n")


def _archive_hong(lines: list) -> None:
    """F-LOG — dòng không parse được, giữ NGUYÊN VĂN sang file archive RIÊNG.

    File riêng (`YYYY-MM-DD.hong.jsonl`) chứ không trộn vào archive chính:
    archive chính phải giữ tính chất "mỗi dòng là một bản ghi JSON hợp lệ" —
    ai đếm/parse nó cũng không phải xử lý ngoại lệ. Trộn dòng hỏng vào đó là
    đổi một lỗ mất-dữ-liệu lấy một lỗ hỏng-định-dạng.

    Ghi nguyên văn, KHÔNG cố sửa/cắt: dòng hỏng thường là ghi dở do tiến trình
    chết giữa chừng, và phần đọc được của nó là manh mối để biết mất cái gì.
    """
    if not lines:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(ARCHIVE_DIR / f"{today}.hong.jsonl", "a", encoding="utf-8") as dst:
        for line in lines:
            dst.write(line if line.endswith("\n") else line + "\n")


def _restore_pending(pending: Path) -> None:
    """Failure path: put pending back at LOG_FILE so the next push retries.
    If hook wrote new entries to LOG_FILE in the meantime, prepend pending."""
    if not pending.exists():
        return
    if LOG_FILE.exists():
        # Concat: pending (older) + LOG_FILE (newer) → LOG_FILE
        tmp = LOG_FILE.with_suffix(".merge.jsonl")
        with open(tmp, "wb") as out:
            with open(pending, "rb") as a:
                shutil.copyfileobj(a, out)
            with open(LOG_FILE, "rb") as b:
                shutil.copyfileobj(b, out)
        os.replace(tmp, LOG_FILE)
        pending.unlink()
    else:
        pending.rename(LOG_FILE)


def main():
    if not SERVER_URL:
        print("[ai-log] AI_LOG_SERVER not set — skipping submission.", file=sys.stderr)
        sys.exit(0)

    if not LOG_FILE.exists() or LOG_FILE.stat().st_size == 0:
        print("[ai-log] No logs to submit.", file=sys.stderr)
        sys.exit(0)

    # Atomic rename closes the race window: hook writes that arrive after this
    # land in a fresh LOG_FILE, not in the batch we're about to POST.
    pending = LOG_FILE.with_name(f"session.pending.{int(time.time())}.jsonl")
    try:
        LOG_FILE.rename(pending)
    except FileNotFoundError:
        print("[ai-log] No logs to submit.", file=sys.stderr)
        sys.exit(0)

    entries = []
    leftover_lines = []
    hong_lines = []  # F-LOG: dòng không parse được — giữ NGUYÊN VĂN, xem dưới
    with open(pending, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if len(entries) >= BATCH_LIMIT:
                leftover_lines.append(line)
                continue
            try:
                entries.append(json.loads(stripped))
            except json.JSONDecodeError:
                # F-LOG — KHÔNG vứt im lặng. Dòng hỏng không gửi được (server
                # từ chối cả lô), nhưng nó vẫn là bản ghi DUY NHẤT của một
                # lượt làm việc đã xảy ra thật. Trước bản này nó biến mất khỏi
                # cả ba đường cùng lúc — không POST, không archive, rồi
                # pending.unlink() — không một dòng cảnh báo.
                # Đo A/B thật: bản trước eadcca7 archive 10/10 dòng (dòng hỏng
                # CÒN, vì _archive chép nguyên file); bản sau archive 9/10
                # (MẤT HẲN). Backlog P-121 9133 dòng chạy 19 lượt trên đường
                # này, và archive/ là bằng chứng khách quan DUY NHẤT của việc
                # nộp bài.
                hong_lines.append(line)

    if not entries:
        # Nothing to send; archive whatever was there (probably junk) and bail.
        _archive(pending)
        pending.unlink()
        print("[ai-log] No valid entries to submit.", file=sys.stderr)
        sys.exit(0)

    payload = json.dumps({"entries": entries}, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(
        SERVER_URL,
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"[ai-log] Submitted {len(entries)} entries → {resp.status}", file=sys.stderr)
    except urllib.error.URLError as e:
        # Failure: restore the whole pending (including leftover) for next push.
        _restore_pending(pending)
        print(f"[ai-log] Submit failed: {e} — logs kept locally.", file=sys.stderr)
        sys.exit(0)  # Don't block push on server error

    # Success: archive ONLY the submitted batch, then handle any leftover.
    _archive_entries(entries)
    # F-LOG — PHẢI đứng TRƯỚC unlink: sau unlink thì pending không còn, dòng
    # hỏng mất vĩnh viễn. Và phải BÁO RA, không im lặng — hỏng-im-lặng là
    # đúng thứ cả đợt này mất thời gian vì nó.
    if hong_lines:
        _archive_hong(hong_lines)
        print(
            f"[ai-log] {len(hong_lines)} dòng KHÔNG parse được — không gửi, "
            f"đã giữ nguyên văn ở archive/*.hong.jsonl",
            file=sys.stderr,
        )
    pending.unlink()

    if leftover_lines:
        # More than BATCH_LIMIT entries existed; put the rest back so the
        # next push picks them up.
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.writelines(leftover_lines)
        print(
            f"[ai-log] {len(leftover_lines)} entries deferred to next push.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
