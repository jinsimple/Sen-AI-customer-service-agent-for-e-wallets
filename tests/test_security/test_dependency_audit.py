"""Bảo vệ quyết định risk-accepted cho chromadb (CVE-2026-45829/PYSEC-2026-311
— xem requirements.txt và docs/TESTING.md mục "Rủi ro đã chấp nhận có ghi
chú") — chạy pip-audit ngay ở máy dev/pytest, không đợi tới CI Stage 2
(dependency-and-secret-scan, ci.yml) mới biết đỏ. Audit thẳng requirements.txt
(không phải môi trường đang cài) để kết quả không phụ thuộc gói lẻ có sẵn
trong venv cục bộ mà requirements.txt không khai báo.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from src.config import ROOT_DIR

_KNOWN_ACCEPTED_VULN_IDS = {"PYSEC-2026-311"}  # chromadb — xem docstring module

pytestmark = pytest.mark.skipif(
    shutil.which("pip-audit") is None,
    reason=(
        "pip-audit chưa cài cục bộ — CI (ci.yml, job dependency-and-secret-scan) "
        "luôn cài trước khi audit (`pip install ... pip-audit`), chạy được ở đây "
        "nếu dev đã `pip install pip-audit` thủ công."
    ),
)


def _run_audit(*extra_args: str) -> subprocess.CompletedProcess:
    requirements = ROOT_DIR / "requirements.txt"
    return subprocess.run(
        ["pip-audit", "-r", str(requirements), "--strict", "-f", "json", *extra_args],
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_pip_audit_passes_with_documented_chromadb_ignore():
    """Đúng tinh thần lệnh CI Stage 2 chạy (kèm --ignore-vuln) — fail ở đây
    nghĩa là CI cũng sẽ đỏ, bắt được TRƯỚC khi push thay vì sau."""
    ignore_args = [a for vid in _KNOWN_ACCEPTED_VULN_IDS for a in ("--ignore-vuln", vid)]
    result = _run_audit(*ignore_args)
    assert result.returncode == 0, (
        "pip-audit fail dù đã ignore các CVE đã biết — có phát hiện MỚI cần "
        f"triage (không phải chromadb đã ghi nhận):\n{result.stdout}\n{result.stderr}"
    )


def test_only_documented_vulnerabilities_are_being_ignored():
    """Kiểm CHÍNH XÁC tập hợp CVE đang tồn tại — không chỉ "còn CVE nào đó".
    2 hướng fail đều có ý nghĩa thật:
      - Có CVE NGOÀI danh sách đã ghi nhận -> KHÔNG được để --ignore-vuln ở
        ci.yml vô tình che luôn phát hiện mới, phải triage riêng.
      - Danh sách hiện tại (chromadb) đã BIẾN MẤT -> chromadb khả năng đã có
        bản vá mới, phải GỠ --ignore-vuln PYSEC-2026-311 ở ci.yml +
        requirements.txt + docs/TESTING.md (mục "Rủi ro đã chấp nhận"),
        không giữ mãi 1 ignore không còn cần thiết.
    """
    result = _run_audit()
    found_ids: set[str] = set()
    if result.stdout.strip():
        data = json.loads(result.stdout)
        for dep in data.get("dependencies", []):
            found_ids.update(v["id"] for v in dep.get("vulns", []))

    assert found_ids == _KNOWN_ACCEPTED_VULN_IDS, (
        f"Tập hợp CVE thật ({found_ids or 'rỗng'}) khác danh sách đã risk-accept "
        f"({_KNOWN_ACCEPTED_VULN_IDS}) — xem docstring test này để biết hướng xử lý."
    )
