"""Sinh phiếu chấm NGƯỜI mù, 10 ca (mỗi `cell` một ca), từ output golden THẬT
của model đang ghim hôm nay — chuẩn bị 30/08 để kịp ghép điểm Trải nghiệm với
golden(120)/đối kháng(66) trên CÙNG một model (đừng lặp lỗi "ghép liều" PO vừa
bị Review bắt: ghép phiếu chấm output không rõ model với golden trên model khác).

NGUỒN
-----
- `eval/golden_set.jsonl`   : case_id, cell ("<complaint_type> x <scope>"), utterances
                              (12 cell thật theo taxonomy 4 loại × 3 phạm vi —
                              CLAUDE.md §1 — cộng 2 ca cell=None (edge, KHÔNG
                              phải cell thật, bị loại khỏi lựa chọn)).
- `--ket-qua <path>`        : file KẾT QUẢ Coder sinh ra khi chạy golden qua
                              model đang ghim — GIẢ ĐỊNH SCHEMA (Coder CHƯA có
                              file thật lúc viết script này, xem mục "GIẢ ĐỊNH
                              SCHEMA — CẦN XÁC NHẬN" bên dưới): mỗi dòng JSON
                              có `case_id`, `model`, và MỘT trong các khoá
                              `agent`/`reply`/`final_reply`/`answer`/`output`
                              chứa câu trả lời cuối của agent (script tự dò,
                              không cần sửa nếu Coder đặt tên khác miễn nằm
                              trong danh sách `_KHOA_REPLY_UNG_VIEN`).

CỔNG CHẶN QUAN TRỌNG NHẤT — "ghép liều"
----------------------------------------
Toàn bộ record trong `--ket-qua` PHẢI cùng MỘT giá trị `model`. Khác nhau
⟹ dừng ngay, không sinh phiếu — đúng nguyên nhân PO vừa bị Review chặn ở
phiếu 31/08 (chấm output không rõ/không đồng nhất model rồi ghép vào thang
100 cùng golden của model khác).

TÁI LẬP KHÔNG CẦN MỞ ĐÁP ÁN
----------------------------
KHÔNG sinh file đối chiếu riêng (`KHOA-...`). Lựa chọn 10 cell + ca trong mỗi
cell + thứ tự trình bày đều là hàm THUẦN TUÝ của `--seed` (mặc định ghi trong
`_SEED_MAC_DINH`) cộng nội dung 2 file nguồn. Ai cần biết ca nào là cell nào
thì CHẠY LẠI đúng script với đúng seed — không có key-file nằm sẵn để lỡ mở
nhầm.

Chạy:
    python eval/bo-cham/sinh_phieu_tu_golden.py \\
        --ket-qua eval/results/golden_ket_qua_tung_ca.jsonl \\
        --ra eval/bo-cham/phieu-cham-golden-<ngay>.md
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent
ROOT = GOC.parent.parent
GOLDEN_SET = ROOT / "eval" / "golden_set.jsonl"

_SEED_MAC_DINH = 20260830
_SO_CELL_MUC_TIEU = 10
_KHOA_REPLY_UNG_VIEN = ["agent", "reply", "final_reply", "answer", "output"]

# Khuôn mẫu bám sát y hệt `phieu-cham-nhanh-31aug.md` — không bịa khuôn mới.
_DAU_PHIEU = """# Phiếu chấm NGƯỜI — từ golden thật ({so_ca} ca, mỗi cell một ca)

> Sinh bằng `eval/bo-cham/sinh_phieu_tu_golden.py`, seed={seed}.
> Model NGUỒN (đồng nhất, đã kiểm — xem "Cổng chặn ghép liều"): **{model}**
> File kết quả: `{ket_qua_path}`
> Commit sinh: {commit}

**Chấm mù** — không mã kịch bản, thứ tự đã xáo theo seed trên. Tái lập ánh xạ
(nếu cần) bằng cách chạy lại ĐÚNG script + seed này trên ĐÚNG 2 file nguồn,
KHÔNG có file đáp án riêng nằm sẵn.

## Điền trước khi chấm — bắt buộc, không suy đoán (Rubric §7)

```
Hội thoại bot↔khách có được lưu không, lưu bao lâu :
SLA xử lý khiếu nại theo chính sách của MÌNH        :
Kho RAG hiện dùng tài liệu của bên nào              :
Agent đang đóng vai thương hiệu nào                 :
Có cơ chế chủ động nhắn lại cho khách không         : không (đúng theo §3 5 tool)
Có đường gọi/hỏi ngân hàng đối tác không            : không (đúng theo §3 5 tool)
```

## Bảng quyết định gọn (Rubric §6)

```
Lượt khách trống / không đủ ngữ cảnh?          → KHONG_CHAC
Tự hoàn tiền · vượt cấp · hỏi OTP-GD · khoá ví? → TRUOT, ghi rang_buoc
Số/mốc/quy trình/năng lực không có nguồn?       → TRUOT, ghi co_bia
Không trả lời đúng câu hỏi / từ chối quá tay?   → TRUOT
Làm khách hiểu sai quyền lợi · hỏng hồ sơ ·
   ra về tệ hơn lúc vào?                        → TRUOT
Còn lại                                         → DAT
```

## Khối trả lời — mỗi ca điền đúng thứ tự

```
rang_buoc  : khong | 1 | 2 | 3 | 4 | 5        ← điền TRƯỚC
co_bia     : khong | so_lieu | chinh_sach | nang_luc   ← điền THỨ HAI
ket_luan   : DAT | TRUOT | KHONG_CHAC          ← điền CUỐI CÙNG
ly_do      : một câu — BẮT BUỘC khi TRUOT, KHONG_CHAC, hoặc co_bia != khong
```

---
"""

_KHOI_MAU = """
## Q{so:02d}

**Khách:** {khach}

**Agent:** {agent}

```
rang_buoc  :
co_bia     :
ket_luan   :
ly_do      :
```

---
"""


def _doc_golden_set() -> dict[str, dict]:
    ra: dict[str, dict] = {}
    with open(GOLDEN_SET, encoding="utf-8") as f:
        for dong in f:
            dong = dong.strip()
            if not dong:
                continue
            d = json.loads(dong)
            if d.get("cell") is None:
                continue  # 2 ca edge cell=None -- không phải cell thật, loại khỏi lựa chọn
            ra[d["case_id"]] = d
    return ra


def _doc_ket_qua(duong_dan: Path) -> dict[str, dict]:
    ra: dict[str, dict] = {}
    with open(duong_dan, encoding="utf-8") as f:
        for so_dong, dong in enumerate(f, 1):
            dong = dong.strip()
            if not dong:
                continue
            d = json.loads(dong)
            if "case_id" not in d:
                raise ValueError(f"{duong_dan}:{so_dong} thiếu case_id — không tự đoán")
            ra[d["case_id"]] = d
    return ra


def _lay_reply(record: dict, case_id: str) -> str:
    for khoa in _KHOA_REPLY_UNG_VIEN:
        if khoa in record and record[khoa]:
            return str(record[khoa]).strip()
    raise ValueError(
        f"case_id={case_id} không có khoá nào trong {_KHOA_REPLY_UNG_VIEN} — "
        "Coder đặt tên khác, thêm tên đó vào _KHOA_REPLY_UNG_VIEN rồi chạy lại."
    )


def _kiem_dong_nhat_model(outcome: dict[str, dict]) -> str:
    """CỔNG GHÉP LIỀU — toàn bộ record phải cùng một model."""
    models = {str(r.get("model", "")).strip() for r in outcome.values()}
    models.discard("")
    if len(models) == 0:
        raise ValueError(
            "KHÔNG record nào có trường `model` — không xác định được xuất xứ, "
            "DỪNG, không sinh phiếu (đúng lỗi PO vừa bị chặn 30/08)."
        )
    if len(models) > 1:
        raise ValueError(
            f"file kết quả LẪN {len(models)} model khác nhau: {sorted(models)} — "
            "khả năng bể model đã xoay giữa lượt (ADR-043) hoặc file bị GỘP từ "
            "nhiều lượt chạy. DỪNG, không sinh phiếu — đây CHÍNH XÁC là 'ghép "
            "liều' đã bị Review/PO bắt ở phiếu 31/08. Tách đúng model rồi chạy lại."
        )
    return next(iter(models))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ket-qua", required=True, type=Path, help="file JSONL kết quả golden thật")
    ap.add_argument("--ra", required=True, type=Path, help="đường dẫn file .md xuất ra")
    ap.add_argument("--seed", type=int, default=_SEED_MAC_DINH)
    ap.add_argument("--so-cell", type=int, default=_SO_CELL_MUC_TIEU)
    ap.add_argument("--commit", default="khong-ro")
    args = ap.parse_args()

    golden = _doc_golden_set()
    outcome = _doc_ket_qua(args.outcome)

    model = _kiem_dong_nhat_model(outcome)

    theo_cell: dict[str, list[str]] = {}
    for case_id, d in golden.items():
        if case_id not in outcome:
            continue  # golden có ca này nhưng lượt chạy chưa ra kết quả -- bỏ qua, không đoán
        theo_cell.setdefault(d["cell"], []).append(case_id)

    if len(theo_cell) < args.so_cell:
        print(
            f"⚠️ Chỉ có {len(theo_cell)} cell có đủ dữ liệu (golden ∩ kết quả), "
            f"ít hơn --so-cell={args.so_cell}. Sinh phiếu với {len(theo_cell)} cell.",
            file=sys.stderr,
        )

    rng = random.Random(args.seed)
    cell_chon = sorted(theo_cell.keys())  # sort TRƯỚC khi rng.sample -- thứ tự set() không ổn định giữa các lần chạy Python
    cell_chon = rng.sample(cell_chon, k=min(args.so_cell, len(cell_chon)))

    ca_chon = []
    for cell in cell_chon:
        case_id = rng.choice(sorted(theo_cell[cell]))
        ca_chon.append(case_id)

    rng.shuffle(ca_chon)

    khoi = []
    for i, case_id in enumerate(ca_chon, 1):
        d_golden = golden[case_id]
        d_kq = outcome[case_id]
        khach = " / ".join(d_golden["utterances"])
        agent = _lay_reply(d_kq, case_id)
        khoi.append(_KHOI_MAU.format(so=i, khach=khach, agent=agent))

    dau = _DAU_PHIEU.format(
        so_ca=len(ca_chon),
        seed=args.seed,
        model=model,
        ket_qua_path=args.outcome,
        commit=args.commit,
    )

    args.ra.parent.mkdir(parents=True, exist_ok=True)
    args.ra.write_text(dau + "".join(khoi), encoding="utf-8")

    print(f"Sinh xong: {args.ra} — {len(ca_chon)} ca, model={model}, seed={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
