#!/usr/bin/env python3
"""CỔNG cho cờ `PHAN_LUONG_BAT` — chạy lại được, 0 lượt LLM.

    python eval/cong_phan_luong.py --luat <đường dẫn quy_tac_phan_luong.py>

## Vì sao là một LỆNH chứ không phải một lần chạy tay

Cờ này sẽ bật/tắt nhiều lần trong đợt đo. **Mỗi lần bật phải qua cổng**, không
phải chỉ lần đầu — vì thứ đổi giữa hai lần bật (danh sách từ, một ngưỡng, một
mệnh đề bị xoá) chính là thứ không ai nghĩ cần chạy lại.

## Ba nguyên tắc đã đắt tiền, mã hoá thẳng vào đây

**① Kiểm BĂM BỘ CA trước khi chấm.** Chấm một bộ ca đã trôi rồi báo số là báo
về một vật không còn tồn tại. Cổng **từ chối chạy**, không cảnh báo rồi chạy
tiếp.

**② In PHÂN BỐ LÝ DO, không chỉ tỉ lệ** (Luật E). `124/124` từng đạt với
**0 ca** nào chạm mệnh đề chính của thiết kế — một nhánh chưa khai hoả lần nào
là một nhánh **chưa được kiểm**, dù tỉ lệ có là 100%.

**③ Băm khai kèm TÊN THUẬT TOÁN** (Luật 18). `1edd51dff555` và `742df94b195a`
là **cùng một file**, khác thuật toán, và không ai kiểm vì cả hai đều là 12 ký
tự hex.

## 🔴 ĐC-1..5 — CHƯA ĐỦ ĐỊNH NGHĨA, và cổng NỔ thay vì bỏ qua

PO giao *"ĐC-1..5 thành bộ cổng chính thức"*. Tôi tìm trong `docs/` và
**không thấy định nghĩa nào**. Tôi biết chắc hai cái qua tin nhắn:

    ĐC-2  phân loại theo TỪNG LƯỢT, không theo phiên
    ĐC-5  không câu âm nào lọt qua đường NHẸ (không còn "phải đi day_du" —
          xem sửa 24/08, `thu_slot` là đường hợp lệ thứ ba)

Ba cái còn lại tôi **không biết**, và **không đoán** — một cổng có ba mục tôi tự
nghĩ ra là một cổng đo ý kiến của tôi, không đo điều kiện dự án đã chốt.

Cổng dưới đây chạy phần định nghĩa được và **thoát mã 3** ở phần chưa có định
nghĩa. Nó sẽ **không bao giờ báo ĐẠT** cho tới khi ĐC-1/3/4 được viết ra.

## 🔴 Kết quả chỉ đủ tư cách báo cáo/tick khi `--luat` là bản ĐÃ COMMIT

Chạy trên file đang sửa dở (`git status` dirty) là hợp lệ để tự dò lúc dev,
nhưng con số đó KHÔNG có vật ổn định đứng sau — bản WIP có thể đổi trước khi
commit. Cổng tự phát hiện và cảnh báo (không chặn) khi file dirty — xem
`_dang_dirty()`. Báo cáo/tick chỉ dùng kết quả chạy trên bản sạch, và PHẢI kèm
mã commit của `--luat` tại thời điểm chạy (`git rev-parse HEAD -- <file>` hoặc
tương đương) để người đọc sau tra lại được đúng vật đã đo.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

GOC = pathlib.Path(__file__).resolve().parent.parent
BAM = "sha256[:12] của nội dung tệp (bytes), hoặc của json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) sau khi bỏ 'bam_nhan' và 'thuat_toan_bam'"


def _bam_tep(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def _dang_dirty(p: pathlib.Path) -> bool:
    """`git status --porcelain -- <p>` khác rỗng ⟹ file có sửa CHƯA COMMIT.

    24/08 — vấp thật: chạy cổng trên `phan_luong.py` đang là WIP (chưa commit)
    của Coder, ra 10/10 đẹp bất ngờ — con số đó không có vật nào đứng sau, vì
    bản WIP có thể đổi trước khi commit. Cảnh báo, KHÔNG chặn: chạy thử trên
    WIP là hợp lệ (chính người viết code cần thế lúc dev), chỉ là kết quả phải
    tự khai thân phận để không ai tick/báo cáo nhầm một trạng thái trung gian.
    """
    try:
        # cwd = GỐC repo, đường dẫn TUYỆT ĐỐI — cwd=thư mục của file + đường
        # dẫn TƯƠNG ĐỐI sẽ bị git nối lệch (vd `src/agents/` + `src/agents/x.py`
        # → tìm nhầm `src/agents/src/agents/x.py`, không khớp gì, LUÔN "sạch").
        # Tự bắt được bug này bằng cách chạy thử trên chính file đang biết là
        # dirty (`git status --short` báo `M`) trước khi tin hàm này.
        r = subprocess.run(
            ["git", "status", "--porcelain", "--", str(p.resolve())],
            capture_output=True, text=True, cwd=GOC, timeout=10,
        )
    except Exception:  # noqa: BLE001 — cảnh báo là phụ, không được làm cổng chết vì git lỗi
        return False
    return bool(r.stdout.strip())


def _bam_nhan(d: dict) -> str:
    t = {k: v for k, v in d.items() if k not in ("bam_nhan", "thuat_toan_bam")}
    return hashlib.sha256(
        json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True).encode()
    ).hexdigest()[:12]


def _nap_luat(p: pathlib.Path):
    spec = importlib.util.spec_from_file_location("luat", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _nhanh(ly_do: str) -> str:
    dg = ly_do.lower()
    if "chữ số" in dg:
        return "CHỮ SỐ"
    if "dài" in dg:
        return "ĐỘ DÀI"
    if "ngoài tập" in dg:
        return "TOKEN NGOÀI TẬP"
    if "xã giao" in dg:
        return "mọi token xã giao"
    return f"khác({ly_do[:24]})"


def _nhanh_luat_co(nguon: str) -> set[str]:
    """Nhánh nào luật THỰC SỰ có — đọc từ nguồn, không từ danh sách tôi nhớ.

    🔴 Bản đầu dùng một danh sách CỨNG ba nhánh, nên sau khi `DAI_TOI_DA` bị
    XOÁ nó vẫn cảnh báo *"ĐỘ DÀI chưa khai hoả"* ở cả ba bộ ca. Cảnh báo về một
    nhánh KHÔNG CÒN TỒN TẠI là nhiễu — và nhiễu dạy người đọc bỏ qua cảnh báo,
    tức nó phá đúng thứ Luật E dựng ra.
    """
    co = set()
    if "CO_CHU_SO" in nguon:
        co.add("CHỮ SỐ")
    if "DAI_TOI_DA" in nguon:
        co.add("ĐỘ DÀI")
    if "XA_GIAO" in nguon:
        co.add("TOKEN NGOÀI TẬP")
    return co


def cham(ten, cau_nhan, phan_luong, nhanh_co=None) -> tuple[bool, str]:
    """Trả (đạt, báo cáo). `cau_nhan` = list[(câu, nhãn kỳ vọng)]."""
    dem = collections.Counter()
    sai = []
    for cau, mong in cau_nhan:
        # `*_` chấp nhận cả tuple 2 phần tử (nhe/day_du hiện có) lẫn 4 phần tử
        # (nhánh thu_slot theo thiết kế 1B — thêm slot_hien_co/slot_thieu) —
        # cổng chỉ đọc hai phần tử đầu, không phá vỡ khi arity đổi.
        duong, ly_do, *_ = phan_luong(cau)
        dem[_nhanh(ly_do)] += 1
        if duong != mong:
            sai.append((cau, mong, duong, ly_do))
    n = len(cau_nhan)
    d = n - len(sai)
    ra = [f"\n  {ten}: {d}/{n}"]
    ra.append("    phân bố lý do: " + " · ".join(f"{k}={v}" for k, v in dem.most_common()))
    chua_chay = sorted(k for k in (nhanh_co or set()) if dem[k] == 0)
    if chua_chay:
        ra.append(f"    ⚠️  nhánh CHƯA KHAI HOẢ lần nào: {chua_chay} — chưa được kiểm (Luật E)")
    for cau, mong, thuc, ly in sai[:8]:
        ra.append(f"    ✗ {cau!r}  mong {mong} · được {thuc} · vì {ly}")
    return not sai, "\n".join(ra)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--luat", required=True, help="đường dẫn quy_tac_phan_luong.py")
    ap.add_argument("--bo-qua-bam", action="store_true",
                    help="CHỈ để dò lỗi. Cổng thật KHÔNG được dùng cờ này.")
    a = ap.parse_args()

    p_luat = pathlib.Path(a.luat)
    if not p_luat.exists():
        print(f"🔴 không thấy luật: {p_luat}")
        return 2
    if _dang_dirty(p_luat):
        print(f"  ⚠️  ĐANG ĐO BẢN CHƯA CHỐT — {p_luat} có sửa đổi CHƯA COMMIT.")
        print("      Kết quả KHÔNG dùng để tick/báo cáo — chỉ hợp lệ để tự dò lúc dev.")
    print(f"  LUẬT   {p_luat.name} · {p_luat.stat().st_size} byte")
    print(f"         sha256[:12] = {_bam_tep(p_luat)}   md5[:12] = "
          f"{hashlib.md5(p_luat.read_bytes()).hexdigest()[:12]}")
    print(f"  cách băm: {BAM}")
    luat = _nap_luat(p_luat)

    bo = []
    # bộ ca DƯƠNG + ÂM-NGẮN: nhãn nằm trong file JSON đã băm
    for f, ky in (("eval/bo_ca_luot_don.json", "dương 20 ca"),
                  ("eval/bo_ca_am_ngan_khong_so.json", "âm-ngắn 14 ca")):
        p = GOC / f
        if not p.exists():
            print(f"🔴 thiếu bộ ca: {f}")
            return 2
        d = json.loads(p.read_text(encoding="utf-8"))
        thuc, ghi = _bam_nhan(d), d.get("bam_nhan")
        if thuc != ghi and not a.bo_qua_bam:
            print(f"🔴 BỘ CA ĐÃ TRÔI: {f}\n   băm ghi {ghi} ≠ tính lại {thuc}\n"
                  "   TỪ CHỐI CHẤM — số chấm trên bộ ca trôi là số về một vật không còn tồn tại.")
            return 2
        bo.append((f"{ky} [{ghi}]", [(c["cau"], c["ky_vong"]) for c in d["ca"]]))

    # bộ ca ÂM gốc: nhãn ngầm — MỌI câu đều phải đi day_du
    p = GOC / "eval" / "golden_set.jsonl"
    if p.exists():
        cau = []
        for dg in p.read_text(encoding="utf-8").splitlines():
            if not dg.strip():
                continue
            x = json.loads(dg)
            u = x.get("utterances") or ([x["utterance"]] if "utterance" in x else [])
            cau += [(c, "day_du") for c in u if isinstance(c, str) and c.strip()]
        bo.append((f"âm gốc {len(cau)} CÂU [{_bam_tep(p)}]", cau))
        print(f"\n  ⚠️  ĐƠN VỊ ĐẾM: golden_set.jsonl có 120 CA nhưng {len(cau)} CÂU. "
              "Cổng chấm theo CÂU.")

    nhanh_co = _nhanh_luat_co(p_luat.read_text(encoding="utf-8"))
    print(f"  nhánh luật CÓ: {sorted(nhanh_co)}")
    tat_ca_dat = True
    for ten, cn in bo:
        dat, bc = cham(ten, cn, luat.phan_luong, nhanh_co)
        print(bc)
        tat_ca_dat &= dat

    # ── 1B.3 — S1-S9 (nhánh MỚI `thu_slot`, đặc tả Lead 24/08) ──
    # Viết TRƯỚC khi 1B.2 land (cùng nếp A2/1A.1). Trước khi vá, mọi ca kỳ
    # vọng thu_slot ĐÚNG ĐẮN sẽ đỏ (nhánh chưa tồn tại) — đỏ ĐÚNG LÝ DO, không
    # phải bug ở đây. Không gộp vào `tat_ca_dat` cho tới khi Coder xác nhận
    # 1B.2 đã land, để không biến một cổng "chờ vá" thành "cổng đỏ chưa rõ vì
    # sao" trong con mắt người đọc log.
    p_slot = GOC / "eval" / "bo_ca_thu_slot_1b.json"
    d_slot = None  # dùng lại ở ĐC-6 bên dưới nếu nạp được
    if p_slot.exists():
        d_slot = json.loads(p_slot.read_text(encoding="utf-8"))
        thuc, ghi = _bam_nhan(d_slot), d_slot.get("bam_nhan")
        if thuc != ghi and not a.bo_qua_bam:
            print(f"\n🔴 BỘ CA 1B.3 ĐÃ TRÔI: băm ghi {ghi} ≠ tính lại {thuc} — TỪ CHỐI CHẤM.")
            return 2
        # Nhãn ĐỘNG — "S1-S9" cứng đã lỗi thời khi bộ ca lớn thêm (tới S20 và
        # còn tăng), tự nói sai số ca đang thật sự có. Đếm sống, không đoán.
        print(f"\n  ── 1B.3 — {len(d_slot['ca'])} ca (thu_slot) [{ghi}] ──")
        cn = [(c["cau"], c["ky_vong"]) for c in d_slot["ca"]]
        _, bc = cham(f"{len(cn)} ca", cn, luat.phan_luong, None)
        print(bc)
        print("  ⚠️  KHÔNG gộp vào cổng chính — trước 1B.2, ca kỳ vọng `thu_slot` "
              "ĐỎ ĐÚNG LÝ DO (nhánh chưa tồn tại). Đối xử như A2: land trước, xanh sau khi vá.")
        print("  🔴 S7 (tối đa 1 lần/hội thoại) và S8 (Redis lỗi fail-open) — KHÔNG có ca ở "
              "đây, có chủ đích: đòi trạng thái theo thread_id/Redis, ngoài khả năng của "
              "phan_luong(cau) dạng hàm thuần. Cần cổng riêng ở tầng gọi (graph.py) khi "
              "Coder xác nhận nơi state thực sự sống.")

    print("\n  ── ĐC-1..5 ── nguồn: docs/giao-viec/2026-08-17-dinh-nghia-cong-DC-phan-luong.md")
    print("     ĐC-6 (24/08, đề xuất Review) không thuộc phiếu gốc — ràng buộc THUẬN, "
          "cổng tự áp cho chính nó, xem chú thích tại chỗ định nghĩa.")
    print(f"     sha256[:12] = {_bam_tep(GOC / 'docs/giao-viec/2026-08-17-dinh-nghia-cong-DC-phan-luong.md')}")
    dc = {}

    # ĐC-1 — xã giao thuần PHẢI đi nhẹ. Vế "kêu thật lúc bất thường".
    # 🔴 DÂN SỐ: ĐC-1 nói "câu xã giao THUẦN (kiểu 'alo')" — KHÔNG phải mọi ca
    # nhãn `nhe`. Bản đầu của tôi lấy cả 10 ca nhãn nhe (gồm 'cho mình hỏi cái
    # này với') rồi báo 5/10 — đo sai DÂN SỐ, đúng lớp lỗi golden_set-không-có-
    # lượt-đơn. Dân số đúng là nhóm ① chào hỏi, phân nhóm tôi đặt TỪ ĐẶC TẢ
    # trước khi thấy luật.
    _d = json.loads((GOC / "eval/bo_ca_luot_don.json").read_text(encoding="utf-8"))
    xa_giao = [c["cau"] for c in _d["ca"] if c["nhom"].startswith("①")]
    sai1 = [c for c in xa_giao if luat.phan_luong(c)[0] != "nhe"]
    dc["ĐC-1"] = (not sai1, f"{len(xa_giao)-len(sai1)}/{len(xa_giao)} câu xã giao đi nhẹ"
                  + (f" · TRƯỢT: {sai1[:3]}" if sai1 else ""))

    # ĐC-3 — ném lỗi / đầu vào bất thường ⟹ ĐẦY ĐỦ, KHÔNG được nổ ra ngoài.
    # fail-open VỀ PHÍA ĐẮT TIỀN: lỗi của lớp tiết kiệm không bao giờ thành lỗi của khách.
    quai = [("", "chuỗi rỗng"), ("   ", "toàn khoảng trắng"), ("\n\t", "toàn ký tự trắng"),
            ("\x00\x01", "byte điều khiển"), ("😀🔥", "chỉ emoji"),
            ("a" * 5000, "5000 ký tự"), ("﷽" * 50, "ký tự hợp âm"),
            (None, "None"), (12345, "số nguyên"), ([], "list rỗng")]
    hong3 = []
    for v, ten in quai:
        try:
            d, _ = luat.phan_luong(v)
            if d != "day_du":
                hong3.append(f"{ten} → {d} (phải day_du)")
        except Exception as e:
            hong3.append(f"{ten} → NÉM {type(e).__name__} (phải nuốt và trả day_du)")
    dc["ĐC-3"] = (not hong3, f"{len(quai)-len(hong3)}/{len(quai)} đầu vào bất thường → day_du"
                  + ("\n         🔴 " + "\n         🔴 ".join(hong3) if hong3 else ""))

    # ĐC-4 — câu lạ / không phân định được ⟹ ĐẦY ĐỦ.
    la = ["asdkjhasd", "xin chào ạaaaa bqzxk", "test test 123 abc xyz",
          "ủa gì vậy trời", "hmm thế à ừ nhỉ sao lại thế được nhỉ"]
    sai4 = [c for c in la if luat.phan_luong(c)[0] != "day_du"]
    dc["ĐC-4"] = (not sai4, f"{len(la)-len(sai4)}/{len(la)} câu lạ → day_du"
                  + (f" · LỌT: {sai4}" if sai4 else ""))

    # 🔴 DÂN SỐ: ĐC-5 nói "mọi câu của BỘ ÂM" — bản đầu tôi dùng `tat_ca_dat`
    # gộp CẢ bộ dương, nên 5 ca dương trượt (đúng theo thiết kế, chúng lệch phía
    # an toàn) kéo ĐC-5 xuống đỏ. Đo sai dân số lần thứ HAI trong cùng một hàm.
    #
    # 🔴 24/08 — MỆNH ĐỀ GỐC "mọi câu ÂM đi day_du" LỖI THỜI, sửa lần BA. Router
    # giờ có BA đường (`nhe`/`thu_slot`/`day_du`), không phải hai — `thu_slot`
    # là đường HỢP LỆ cho một câu ÂM mô tả một khiếu nại thật còn thiếu số tiền
    # (vd "Bạn tôi nói chưa nhận được khoản tôi gửi..."). Cấm `thu_slot` tuyệt
    # đối sẽ biến ĐC-5 thành cổng canh một thế giới hai-đường không còn tồn
    # tại. NHƯNG ĐC-1/ĐC-5 phải giữ đúng tính chất gốc: không cái nào một mình
    # đủ, bắt được router suy biến "cho-tất-qua" (mọi câu, kể cả câu KHÔNG
    # nghiệp vụ gì, đều bị đẩy sang MỘT đường tốn kém indiscriminate). Mệnh đề
    # mới: KHÔNG câu ÂM nào được đi `nhe` (đối xứng đúng ĐC-1: câu xã giao đi
    # nhẹ, câu ÂM không phải xã giao thì không được đi nhẹ) — giữ nguyên khả
    # năng bắt "router không làm gì" (mọi câu ÂM lọt qua nhẹ), bỏ giả định sai
    # "chỉ có MỘT đường không-nhẹ".
    ket_am = [(c, luat.phan_luong(c)[0]) for ten, cn in bo if "âm" in ten for c, _ in cn]
    n_am = len(ket_am)
    di_nhe = [c for c, d in ket_am if d == "nhe"]
    dem_duong = collections.Counter(d for _, d in ket_am)
    dat_am = not di_nhe
    mo_ta = (
        f"KHÔNG câu ÂM nào (trong {n_am} CÂU, KHÔNG gồm bộ dương) đi `nhe` — "
        f"phân bố: {dict(dem_duong)}"
    )
    if di_nhe:
        mo_ta += f"\n         🔴 {len(di_nhe)} câu ÂM lọt qua đường NHẸ: {di_nhe[:5]}"
    dc["ĐC-5"] = (dat_am, mo_ta)

    # ĐC-6 — 24/08, đề xuất Review sau khi ĐC-5 đổi mệnh đề. "Không câu ÂM nào
    # đi nhe" bắt được router-suy-biến nhưng MÙ đúng lớp lỗi ĐC-5 CŨ tình cờ
    # bắt được: câu lẽ ra phải day_du (có cảm xúc mạnh/có số tiền/có mã) mà bị
    # đẩy NHẦM vào thu_slot — thu_slot vẫn ≠ nhe nên ĐC-5 mới không thấy. Đây
    # ĐÚNG hình dạng S17-S20 (ca người mẹ hoảng loạn) sáng nay. Vá bằng một
    # RÀNG BUỘC THUẬN: cổng tự áp cho CHÍNH NÓ — mọi câu ĐI thu_slot (bất kể
    # nhãn kỳ vọng gì) phải KHÔNG cảm xúc mạnh VÀ KHÔNG số tiền VÀ KHÔNG mã —
    # kiểm code có nhất quán với ĐẶC TẢ của chính nó, không chỉ "không rơi nhe".
    #
    # Từ khoá cảm xúc/mã KHÔNG đọc từ src/ — lấy nguyên từ chính đặc tả Lead
    # (mục 3.3, khuôn TXN/TCK) + từ PO-agon liệt kê khi giao việc trục cảm xúc
    # (lo/hoảng/sợ/gấp/"giúp...với"/"làm sao bây giờ"). Regex số tiền dùng lại
    # ĐÚNG khuôn đã ghi trong `vi_sao` của S4 khi soạn 1B.3.
    _tu_cam_xuc = ("lo quá", "hoảng", "sợ ", "sợ,", "gấp", "giúp tôi với",
                   "giúp mình với", "làm sao bây giờ", "cứu tôi", "cứu mình", "trời ơi")
    _re_so_tien = re.compile(r"\d[\d.,]*\s*(k|nghìn|nghin|ngàn|ngan|tr|triệu|trieu|đ|d|vnd|vnđ)\b", re.IGNORECASE)
    _re_ma = re.compile(r"\bTXN\d{14}\b|\bTCK-\d{5}\b", re.IGNORECASE)

    tat_ca_cau = [c for _, cn2 in bo for c, _ in cn2]
    if d_slot:
        tat_ca_cau += [c["cau"] for c in d_slot["ca"]]
    vi_pham_dc6 = []
    n_thu_slot = 0
    for c in tat_ca_cau:
        if luat.phan_luong(c)[0] != "thu_slot":
            continue
        n_thu_slot += 1
        co_cam_xuc = any(tk in c.lower() for tk in _tu_cam_xuc)
        co_tien = bool(_re_so_tien.search(c))
        co_ma = bool(_re_ma.search(c))
        if co_cam_xuc or co_tien or co_ma:
            vi_pham_dc6.append((c, {"cảm_xúc": co_cam_xuc, "số_tiền": co_tien, "mã_GD": co_ma}))
    dc["ĐC-6"] = (
        not vi_pham_dc6,
        f"mọi câu ĐI thu_slot ({n_thu_slot} câu, toàn corpus) đều KHÔNG cảm xúc mạnh · "
        f"KHÔNG số tiền · KHÔNG mã GD"
        + ("".join(f"\n         🔴 {c!r} đi thu_slot NHƯNG {flag}" for c, flag in vi_pham_dc6[:5]) if vi_pham_dc6 else "")
    )

    # ĐC-7 — 24/08, PO-agon giao sau khi phát hiện ĐỢT 1A và ĐỢT 1B đặt hai
    # luật NGƯỢC NHAU về cùng một hành vi: R1 (1A, đặc tả chuyên gia) đòi
    # "reply khi thiếu slot chỉ chứa MỘT yêu cầu thông tin"; `phan_luong.py`
    # (1B) LÚC PHÁT HIỆN có hằng số `HOI_THIEU_CA_HAI` hỏi BA thứ (thời gian +
    # số tiền + mã) trong MỘT tin. Không ai thấy cả ngày vì R1 đo trên đường
    # LLM (test 1A), còn cổng này đo trên đường tất định (1B) — hai bộ đo
    # tách biệt. [ĐO 24/08, SAU] Coder xoá hẳn `HOI_THIEU_CA_HAI` (`cd5c057`)
    # NGAY trong lúc ĐC-7 đang viết — chạy lại thấy đã sạch (chỉ còn
    # `HOI_THIEU_SO_TIEN`, 1 trục). Giữ ĐC-7 làm HỒI QUY, không phải ca chờ
    # vá — nếu ai thêm hằng số `HOI_*` mới hỏi nhiều hơn 1 trục, ĐC-7 bắt lại.
    #
    # 🔴 ĐỔI MỆNH ĐỀ 25/08 (đợt "OTP trước token", phiếu §2b — quyết QA/QC,
    # "vùng của bạn" theo Coder khi báo ⑤ sắp land). "R1 = một YÊU CẦU mỗi
    # tin" ở đoạn trên là cách đọc SAI mà chính Đ1 (đợt này) đo được hậu quả:
    # cổng hỏi-số-tiền đứng CÔ LẬP với hỏi-thời-gian, bắn oan 6/11 lần. R1
    # thật là "một Ý mỗi tin", và Q2 (24/08) CHỦ Ý cho ⑤ hỏi thời gian+số tiền
    # TRONG MỘT TIN — đây KHÔNG còn là vi phạm, là hành vi ĐÚNG ĐẶC TẢ. Mù
    # trục này thì ĐC-7 sẽ đỏ SAI LÝ DO ngay khi ⑤ land đúng.
    # Đồng bộ CÙNG NGUYÊN TẮC với `tests/test_1a_luat_hoi_prompt.py::
    # test_r1_thieu_hai_slot_hoi_gop_thoi_gian_va_so_tien` (đổi tên+mệnh đề
    # cùng ngày, cùng lý do — hai bộ đo KHÔNG được lệch nhau lần thứ hai).
    # Vẫn PHẢI giữ khả năng bắt trục thứ BA (`ma_gd`, hoặc bất kỳ trục nào
    # ngoài cặp) — đó mới là vi phạm R1 thật, không được nới rộng quá cặp đã
    # được PO/chuyên gia CHO PHÉP.
    #
    # Đây là ĐC ÁP LÊN ĐẦU RA (nội dung reply), khác ĐC-1..6 (áp lên ĐẦU VÀO/
    # đường đi) — cùng tinh thần ĐC-6 (code tự nhất quán với đặc tả của chính
    # nó), lần này cho phần THU SLOT SINH RA CÂU GÌ, không phải ĐI ĐƯỜNG NÀO.
    #
    # Đọc hằng số CÔNG KHAI dạng chuỗi bắt đầu `HOI_` — đọc GIÁ TRỊ, không đọc
    # LOGIC chọn hằng số nào cho câu nào (đó vẫn là `src/`, không đụng). Dùng
    # lại NGUYÊN bộ dò `_TRUC`/`_MAU_YEU_CAU` đã tự kiểm ở `tests/
    # test_1a_luat_hoi_prompt.py::_truc_hoi()` — chép tối giản qua đây vì
    # eval/ không import ngược được từ tests/ (cùng lý do `tests/_dong_bang.py`
    # đã ghi).
    # 🔴 GIỚI HẠN ĐÃ KHAI: chỉ quét tên bắt đầu đúng `HOI_` — hằng số đặt tên
    # với tiền tố `_` (private-style) SẼ MÙ HOÀN TOÀN với ĐC-7, không đỏ,
    # không cảnh báo, im lặng. Đã báo Coder giữ tiền tố `HOI_` công khai cho
    # hằng số mới của ⑤/⑨ để ĐC-7 còn nhìn thấy — nếu đổi quy ước đặt tên,
    # ĐC-7 phải cập nhật theo, đây KHÔNG phải cổng tự phát hiện quy ước đổi.
    _truc_ra = {
        "so_tien": ("số tiền", "bao nhiêu tiền", "số dư"),
        "thoi_gian": ("thời gian giao dịch", "khoảng thời gian", "hôm nay, hôm qua"),
        "ma_gd": ("mã giao dịch", "mã gd"),
    }
    _cap_duoc_phep_hoi_chung = frozenset({"so_tien", "thoi_gian"})
    hang_so_hoi = {
        n: v for n in dir(luat)
        if n.startswith("HOI_") and isinstance((v := getattr(luat, n)), str) and len(v) > 10
    }
    vi_pham_dc7 = []
    for ten, mau in hang_so_hoi.items():
        ml = mau.lower()
        truc_hoi = {truc for truc, tk in _truc_ra.items() if any(t in ml for t in tk)}
        if len(truc_hoi) > 1 and truc_hoi != _cap_duoc_phep_hoi_chung:
            vi_pham_dc7.append((ten, truc_hoi, mau))
    dc["ĐC-7"] = (
        not vi_pham_dc7,
        f"mọi hằng số `HOI_*` ({len(hang_so_hoi)} cái: {sorted(hang_so_hoi)}) chỉ hỏi MỘT Ý/tin — "
        f"cặp {sorted(_cap_duoc_phep_hoi_chung)} được PHÉP đi cùng nhau (Q2, phiếu §2b 25/08), "
        "trục khác thì không — khớp R1 thật (1A)"
        + ("".join(f"\n         🔴 {ten} hỏi {len(truc)} trục CÙNG LƯỢT {sorted(truc)}: {mau!r}"
                    for ten, truc, mau in vi_pham_dc7) if vi_pham_dc7 else "")
    )

    for k in ("ĐC-1", "ĐC-3", "ĐC-4", "ĐC-5", "ĐC-6", "ĐC-7"):
        ok, mo = dc[k]
        print(f"  {'✅' if ok else '🔴'} {k}  {mo}")

    # RÀNG BUỘC ĐỌC ①: ĐC-1 và ĐC-5 chỉ có nghĩa khi ĐỨNG CÙNG NHAU
    if dc["ĐC-1"][0] != dc["ĐC-5"][0]:
        print("  ⚠️  ĐC-1 và ĐC-5 KHÔNG cùng trạng thái — mỗi cái một mình bị một")
        print("      router suy biến qua mặt (không-làm-gì ↔ cho-tất-qua).")

    print("\n  ── CHƯA CHẠY ĐƯỢC (cần hệ thống, không phải luật thuần) ──")
    print("  ĐC-2  phân loại theo TỪNG LƯỢT — luật này KHÔNG có trạng thái nên ở")
    print("        tầng luật nó đạt HIỂN NHIÊN. Phép thử THẬT phải qua hệ thống,")
    print("        nơi có thể có cache/phiên. Đạt ở đây KHÔNG có nghĩa gì.")
    print("  Δ     đường nhẹ: không LLM · không trả lời nghiệp vụ · không bản ghi")
    print("        → tests/test_bat_bien_dinh_tuyen_duong_nhe.py, chờ dấu `duong`")

    het = all(v[0] for v in dc.values())
    if not het:
        print("\n  ⟹ 🔴 CỔNG ĐỎ.")
        return 1
    print("\n  ⟹ ✅ phần LUẬT THUẦN đạt. CHƯA ĐẠT TOÀN PHẦN: ĐC-2 và Δ cần hệ thống.")
    return 3


if __name__ == "__main__":
    sys.exit(main())
