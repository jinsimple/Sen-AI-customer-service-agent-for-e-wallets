#!/usr/bin/env python3
"""Đo ORIGIN-RULE trên bộ corpus đơn vị `corpus_origin_rule.jsonl` — 0 TPM, tất định.

VÌ SAO BỘ NÀY PHẢI RIÊNG, KHÔNG DÙNG LẠI CORPUS 96 CÂU:
Bản ghi eval hiện chỉ lưu **TÊN** tool, không lưu payload. Nên `nguon` luôn rỗng,
và origin-rule đo trên đó sẽ ra "chặn mọi số dài" — một con số vô nghĩa nhưng
trông rất giống một finding. Bộ này mang **nguồn biết trước** cho từng ca, nên
đo được thẳng tấm lưới mà không cần chạy agent.

(Cùng họ Luật 5: bộ chấm origin-rule ĐỌC payload thì bản ghi phải LƯU payload.
Việc sửa harness lưu payload đã được PO xếp HOÃN — không chặn land, vì bộ đơn
vị này đủ để nghiệm thu.)

BA BẪY QA ĐƯA VÀO, VÀ VÌ SAO:
  · lớp B — số HỢP LỆ nhưng KHÁC ĐỊNH DẠNG (`262000` trong tool, `262.000đ`
    trong câu trả lời). Đây là cách origin-rule hay hỏng nhất, và nó chặn đúng
    câu trả lời cốt lõi của sản phẩm — tức bug 27/96 lặp lại ở tầng khác.
  · lớp F — số là CHUỖI CON của nguồn nhưng không phải GIÁ TRỊ nào trong nguồn.
    Đây là cái giá phải trả nếu chữa lớp B bằng cách nới lỏng so khớp. Hai lớp
    B và F kéo ngược nhau **có chủ đích**: qua được cả hai mới là làm đúng, qua
    một lớp là trượt dọc đường đánh đổi.
  · lớp G — `nguon = null` (fallback, KHÔNG khôi phục được) khác hẳn `nguon = []`
    (quan sát thật: agent không gọi tool nào). Lẫn hai thứ này đã tốn của đội
    một vòng ngày 15/08.

BÁO HAI CON SỐ TÁCH NHAU, không gộp — đúng luật nghiệm thu §4.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EVAL_DIR = Path(__file__).resolve().parent
BO = EVAL_DIR / "corpus_origin_rule.jsonl"


def bam_bo_loc() -> str:
    p = EVAL_DIR.parent / "src" / "agents" / "output_filter.py"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.exists() else "(khong co)"


def kiem_shape(cases: list[dict]) -> list[str]:
    """Canh chính BỘ CORPUS — nguồn phải đúng hình dạng tool THẬT sinh ra.

    Nguồn: `docs/security/hinh-dang-payload-tool-that.md` (security lấy bằng
    cách GỌI TOOL THẬT, không đọc code rồi mô tả).

    VÌ SAO PHẢI CANH: một corpus dựng sai shape vẫn chạy trơn tru và vẫn ra
    một con số — nhưng con số đó đo một payload hệ thống KHÔNG BAO GIỜ sinh ra.
    Đó là một bộ corpus xanh vô nghĩa, thứ nguy hiểm hơn không có corpus.
    Bản đầu tiên của tôi mắc đúng lỗi này (`receipt_code` ở gốc, thay vì
    `rec_code` trong `transaction{}`) vì tôi đoán shape — hiến pháp §4 cấm
    tester đọc `src/`, nên phép canh này phải thay chỗ cho việc đọc code.

    Điểm dễ sai nhất là `sender`/`receiver`: TẬP TRƯỜNG ĐỔI THEO `kind`.
    Dựng một giao dịch `from_bank` mà cho sender có `wallet_id`/`phone` là
    dựng ra một thứ không tồn tại.
    """
    truong = {
        "wallet": ({"wallet_id", "phone", "full_name"}, {"account_no", "bank_code"}),
        "bank_account": ({"account_no", "bank_code", "full_name"}, {"wallet_id", "phone"}),
    }
    loi: list[str] = []
    for c in cases:
        for n in c.get("nguon") or []:
            d = json.loads(n)
            if "wallets" in d:
                continue  # get_customer_history — shape khác, không có transaction{}
            for k in ("status", "transaction", "tool_result_id"):
                if k not in d:
                    loi.append(f"{c['id']}: nguồn thiếu khoá tầng ngoài {k!r}")
            for ben in ("sender", "receiver"):
                b = (d.get("transaction") or {}).get(ben)
                if not b:
                    continue
                kind = b.get("kind")
                if kind not in truong:
                    loi.append(f"{c['id']}.{ben}: kind={kind!r} không có thật")
                    continue
                bat_buoc, cam = truong[kind]
                if thieu := bat_buoc - b.keys():
                    loi.append(f"{c['id']}.{ben}({kind}): thiếu {sorted(thieu)}")
                if thua := cam & b.keys():
                    loi.append(
                        f"{c['id']}.{ben}({kind}): CÓ {sorted(thua)} — payload này không "
                        "tồn tại, tool không bao giờ sinh ra nó"
                    )
    return loi


def _tim_ham_loc():
    """Tìm `loc_dau_ra` có nhận tham số `nguon`. Chưa có -> nói CHƯA ĐO ĐƯỢC."""
    import inspect

    from src.agents.output_filter import loc_dau_ra

    if "nguon" not in inspect.signature(loc_dau_ra).parameters:
        return None
    return loc_dau_ra


def main() -> int:
    cases = [json.loads(d) for d in BO.read_text(encoding="utf-8").splitlines() if d.strip()]
    bam_truoc = bam_bo_loc()
    print(f"băm output_filter.py: {bam_truoc}")
    print(f"bộ corpus: {len(cases)} ca\n{'=' * 70}")

    # CANH CORPUS TRƯỚC KHI ĐO — corpus sai shape vẫn ra một con số, và con số
    # đó vô nghĩa. Chặn ở đây thay vì để nó đi vào báo cáo.
    if loi_shape := kiem_shape(cases):
        print("🔴 CORPUS SAI HÌNH DẠNG PAYLOAD THẬT — không đo, sửa corpus trước:")
        for e in loi_shape:
            print(f"    {e}")
        return 4

    loc = _tim_ham_loc()
    if loc is None:
        print("CHƯA ĐO ĐƯỢC: `loc_dau_ra` chưa nhận tham số `nguon` — origin-rule "
              "chưa có trong cây làm việc.\nĐây KHÔNG phải 'đạt', và cũng không "
              "phải 'trượt'.")
        for c in cases:
            print(f"  {c['id']:8} {c['lop']:32} kỳ vọng={c['ky_vong']}")
        return 2

    sai: list[tuple[str, str, str, list[str]]] = []
    for c in cases:
        # LỆCH GIAO DIỆN, ghi rõ chứ không lặng lẽ lấp:
        # corpus lưu `nguon` là DANH SÁCH payload (một lượt agent gọi được N
        # tool), còn `loc_dau_ra` nhận MỘT chuỗi. Ráp ở đây bằng "\n".
        #
        # Dấu phân cách KHÔNG phải chi tiết làm cho chạy: ráp bằng chuỗi rỗng
        # thì hai payload liền nhau đẻ ra những dãy số KHÔNG hề tồn tại ở
        # payload nào — đuôi số của cái này dính đầu số của cái kia — và bộ lọc
        # sẽ cho qua một số bịa vì nó "có trong nguồn". Đúng họ bẫy F, chỉ khác
        # là lát cắt nằm vắt qua ranh giới hai nguồn.
        #
        # ⚠️ Phía sản xuất ráp thế nào là câu hỏi cho coder — nếu ở đó ráp khác,
        # con số đo được ở đây không nói thay cho đường chạy thật.
        nguon_str = "\n".join(c["nguon"] or [])
        moi, nhom = loc(c["reply"], tin_nhan_khach="", thread_id=c["id"], nguon=nguon_str)
        thuc_te = "chan" if moi != c["reply"] else "qua"
        # `khong_cham_duoc` là kỳ vọng RIÊNG: không được chặn, cũng không được
        # âm thầm cho qua như thể đã verify. Bộ lọc phải nói ra là nó không biết.
        if c["ky_vong"] == "khong_cham_duoc":
            if thuc_te == "chan":
                sai.append((c["id"], c["ky_vong"], thuc_te, nhom))
            continue
        if thuc_te != c["ky_vong"]:
            sai.append((c["id"], c["ky_vong"], thuc_te, nhom))

    phai_qua = [c for c in cases if c["ky_vong"] == "qua"]
    phai_chan = [c for c in cases if c["ky_vong"] == "chan"]
    sai_id = {s[0] for s in sai}
    chan_nham = [c["id"] for c in phai_qua if c["id"] in sai_id]
    bat_hut = [c["id"] for c in phai_chan if c["id"] in sai_id]

    print(f"CHẶN NHẦM : {len(chan_nham)}/{len(phai_qua)} câu hợp lệ bị chặn (ngưỡng cứng: 0)")
    print(f"BẮT HỤT   : {len(bat_hut)}/{len(phai_chan)} câu phải-chặn lọt qua")
    for cid, kv, tt, nhom in sai:
        c = next(x for x in cases if x["id"] == cid)
        print(f"\n  ✗ {cid} [{c['lop']}] kỳ vọng={kv} thực tế={tt} nhóm={nhom}")
        print(f"      {c['reply'][:100]!r}")
        print(f"      vì sao ca này tồn tại: {c['vi_sao'][:150]}")

    bam_sau = bam_bo_loc()
    if bam_sau != bam_truoc:
        print(f"\n🔴 BĂM LỆCH ({bam_truoc} -> {bam_sau}) — LƯỢT ĐO VÔ HIỆU.")
        return 3
    print(f"\nbăm khớp hai đầu: {bam_sau}")
    return 0 if not sai else 1


if __name__ == "__main__":
    raise SystemExit(main())
