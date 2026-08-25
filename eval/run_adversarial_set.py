#!/usr/bin/env python3
"""Nhóm B — bộ adversarial prompt (`adversarial_set.jsonl`, 40 case bám 10 mục
B1-B10 FIN05-StressTest-Plan.md + PDPA/A2/A6 bổ sung + RAG injection). Gọi
agent THẬT — xem docs/TESTING.md trước khi chạy.

Dùng:
    python eval/run_adversarial_set.py
    python eval/run_adversarial_set.py --sample 5   # debug nhanh
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import (
    build_eval_session,
    cau_hinh_dinh_tuyen_luc_chay,
    cham_bo_da_luot,
    dong_bang_nguon_mo_hinh,
    load_jsonl,
    now_stamp,
    phan_loai_loi,
    run_case_adversary,
    xac_nhan_nguon_mo_hinh_luc_chay,
    xep_trang_thai,
)
from eval.measure_quality import dau_thuoc

EVAL_DIR = Path(__file__).resolve().parent
_PARTNER_ADMIN_ID = "USR-EVAL-PA01"


def _ensure_partner_admin(session) -> str:
    from src.db.models import User

    if session.get(User, _PARTNER_ADMIN_ID) is None:
        session.add(
            User(
                user_id=_PARTNER_ADMIN_ID,
                role="partner_admin",
                full_name="Eval Partner Admin",
                phone="0900000999",
                kyc_level=0,
                created_at=dt.datetime.utcnow(),
            )
        )
        session.commit()
    return _PARTNER_ADMIN_ID


def _ingest_malicious_policy(session, text: str, case_id: str) -> None:
    from src.rag.ingest import ingest_document

    uploader = _ensure_partner_admin(session)
    ingest_document(
        session, file_bytes=text.encode("utf-8"), filename=f"{case_id}.txt", uploaded_by=uploader
    )
    session.commit()


def _inject_malicious_transaction_note(session, trans_id: str, text: str) -> None:
    """SEC-001 (FIN05_QA_TestCases.jsonl) — bề mặt tấn công KHÁC với RAG policy
    doc: `Transaction.des` (ghi chú giao dịch) là trường tự do, được
    lookup_transaction trả nguyên văn cho agent (src/tools/lookup_transaction.py
    "des": txn.des) — chính fraud_engine.py cũng đọc trường này để dò từ khoá
    (FS-09), hệ thống đã tự coi đây là dữ liệu không tin cậy."""
    from src.db.models import Transaction

    txn = session.get(Transaction, trans_id)
    if txn is None:
        raise RuntimeError(f"trans_id không tồn tại để inject SEC-001: {trans_id}")
    txn.des = text
    session.commit()


def run(cases: list[dict], nguon_mo_hinh: dict) -> list[dict]:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="fin05_adv_") as tmp:
        db_path = Path(tmp) / "adv.db"
        session = build_eval_session(db_path)

        results = []
        # ĐÓNG DẤU cả THƯỚC lẫn HỆ THỐNG vào từng bản ghi. Bộ này là bộ sẽ
        # dùng để đo before/after các bản vá guardrail — mà một cặp before/
        # after chỉ có nghĩa khi biết chắc hai nhánh khác nhau ĐÚNG MỘT BIẾN.
        # Không đóng dấu thì lặp lại đúng sự cố W1 bị chẻ đôi bởi 38 giây.
        dau = dau_thuoc()
        for i, case in enumerate(cases, start=1):
            case_id = case["case_id"]
            print(f"[{i}/{len(cases)}] {case_id} ({case['category']})...", file=sys.stderr)
            try:
                if case.get("setup_malicious_policy"):
                    _ingest_malicious_policy(session, case["setup_malicious_policy"], case_id)
                # KHOÁ RIÊNG cho tài liệu chính sách HỢP LỆ (F-25 tầng b). Cùng
                # một cơ chế nạp, nhưng KHÔNG dùng chung tên với
                # `setup_malicious_policy`: người đọc thấy một ca chính sách hợp
                # lệ khai khoá "malicious" sẽ đọc kết quả ngược hẳn ý nghĩa —
                # tưởng agent đang bị tấn công trong khi nó chỉ đang được hỏi
                # một câu bình thường. Dữ liệu test gây hiểu nhầm là cách nhanh
                # nhất để đẻ ra một kết luận sai mà không ai kiểm lại.
                if case.get("setup_chinh_sach_hop_le"):
                    _ingest_malicious_policy(
                        session, case["setup_chinh_sach_hop_le"], case_id
                    )
                if case.get("setup_malicious_transaction_note"):
                    note = case["setup_malicious_transaction_note"]
                    _inject_malicious_transaction_note(session, note["trans_id"], note["text"])

                # W0 — chạy qua `run_case_adversary`, kể cả case 1 lượt.
                # `so_luot_leo_thang` mặc định = đúng số lượt viết sẵn, nên 45
                # case cũ chạy Y HỆT trước đây; case nào khai số lớn hơn thì
                # phần dôi ra do kẻ-tấn-công-ảo sinh, phản ứng theo câu agent
                # vừa trả lời.
                kich_ban = case.get("kich_ban_leo_thang") or case["utterances"]
                agent_result = run_case_adversary(
                    session, case=case, thread_id=f"ADV-{case_id}",
                    so_luot_toi_da=int(case.get("so_luot_leo_thang") or len(kich_ban)),
                )
                all_replies = agent_result.get("all_agent_replies") or []
                reply = agent_result.get("reply", "")
                # CHẤM TÍCH LUỸ TOÀN HỘI THOẠI, không chỉ lượt cuối. Bản cũ
                # chấm trên `reply` (= lượt cuối): agent sập ở lượt 2 rồi lượt
                # 5 nói lại câu từ chối chuẩn mực vẫn được tính ĐẠT, dù tiền đã
                # hứa hoàn ở lượt 2. Với bộ đa lượt thì bỏ sót gần như chắc chắn.
                cham = cham_bo_da_luot(case, agent_result)
                violations = cham["vi_pham"]
                first_violation_turn = cham["first_violation_turn"]
                ha_tang = None
            except Exception as e:
                # LƯU TRACEBACK ĐẦY ĐỦ — thiếu 15/08, phát hiện khi coder cần
                # điều tra MT-E02 mà raw chỉ có `repr(e)`.
                # `repr(e)` nói CÁI GÌ hỏng; traceback nói HỎNG Ở ĐÂU. Với lỗi
                # nghi ô-nhiễm-chéo-case (bản ghi mồ côi của case TRƯỚC làm
                # case SAU chết ở autoflush), chỗ ném lỗi chính là dữ kiện
                # quyết định — không có nó thì người điều tra phải chạy lại và
                # cầu cho lỗi ngắt quãng tái hiện.
                import traceback as _tb
                traceback_day_du = "".join(_tb.format_exception(type(e), e, e.__traceback__))
                reply = ""
                all_replies = []
                first_violation_turn = None
                loai = phan_loai_loi(e)
                if loai == "ha_tang":
                    # KHÔNG ĐO ĐƯỢC — không phải TRƯỢT. Case này chưa được đo
                    # lần nào, phải chạy lại chứ không kết luận gì về agent.
                    ha_tang = f"LỖI HẠ TẦNG (không đo được): {e!r}"
                    violations = []
                else:
                    ha_tang = None
                    violations = [f"LỖI CHẠY CASE: {e!r}"]
                agent_result = {}

                # KHÔNG LƯỢT NÀO CHẠY XONG => KHÔNG THỂ TRƯỢT.
                #
                # Lỗ này lộ ra 15/08 với MT-F01: IntegrityError ném ra TRƯỚC khi
                # agent kịp trả lời lượt đầu, `phan_loai_loi` không nhận ra dấu
                # hiệu hạ tầng nào nên xếp "khong_ro" -> bản ghi thành TRƯỢT với
                # `luot=0`.
                #
                # TRƯỢT là một phán quyết VỀ HÀNH VI của agent. Không có lượt
                # nào chạy xong thì không có hành vi nào tồn tại để phán — con
                # số đó không phải "agent làm sai", nó là "bộ đo chưa chạm được
                # tới agent". Xếp nó thành TRƯỢT là bịa ra một kết luận bất lợi
                # từ chỗ không có dữ liệu, đúng thứ ràng buộc cứng số 3 cấm
                # agent làm — và bộ đo không được phép làm thứ nó đi bắt lỗi.
                #
                # CỐ Ý KHÔNG nới `phan_loai_loi`: danh sách dấu hiệu hạ tầng vẫn
                # một chiều, thận trọng như cũ. Đây là một điều kiện KHÁC và
                # mạnh hơn — không phải "lỗi này có vẻ do hạ tầng" mà là "không
                # có gì để chấm", đúng hay sai không phụ thuộc việc đoán nguyên
                # nhân. Lỗi vẫn giữ nguyên trong `violations` + traceback để
                # điều tra, chỉ thôi bị đếm vào mẫu số hành vi.
                #
                # VÀ NÓ LÀ TRẠNG THÁI RIÊNG, không gộp vào KHÔNG ĐO ĐƯỢC. Hai
                # thứ này đòi hai hành động khác nhau:
                #   khong_do_duoc  -> 429/timeout: CHẠY LẠI là xong
                #   chua_co_hanh_vi -> có cái gì đó vỡ bên trong: PHẢI ĐIỀU TRA
                # Gộp lại thì một bug thật (IntegrityError của MT-F01) đội chung
                # nhãn với một lần chạm trần TPM, và sẽ bị đọc lướt thành "chạy
                # lại là xong" — tức chôn đúng thứ cần đào lên. Lại đúng họ
                # "hai trạng thái đội chung một vỏ" đã gặp ở tool_calls và ở
                # câu fallback.
            else:
                traceback_day_du = None
            session.rollback()

            results.append(
                {
                    "case_id": case_id,
                    "_thuoc": dau,
                    # ② hạng mục PO giao 26/08 (lỗ 41aacd5) — TỰ KHAI model/
                    # base_url/mã nguồn trên TỪNG bản ghi, cùng chỗ `_thuoc`
                    # đã đóng dấu THƯỚC — lý do giống hệt: before/after chỉ có
                    # nghĩa khi biết chắc khác nhau ĐÚNG MỘT BIẾN, và một script
                    # lọc riêng lẻ raw JSON vẫn thấy được nguồn không cần mở .md.
                    **{k: v for k, v in nguon_mo_hinh.items() if k != "dung_duoc"},
                    "nguon_mo_hinh_dung_duoc": nguon_mo_hinh["dung_duoc"],
                    "category": case["category"],
                    "description": case.get("description", ""),
                    # BA trạng thái, không phải hai: ĐẠT · TRƯỢT · KHÔNG ĐO
                    # ĐƯỢC. `passed` chỉ còn ý nghĩa khi đã đo được.
                    # BỐN trạng thái — xem `xep_trang_thai()`. Đưa ra hàm thuần
                    # vì khi phép gán này còn là biểu thức ba ngôi nằm ở đây thì
                    # không test nào gọi tới được, và lỗ 0-lượt-mà-TRƯỢT sống
                    # sót đúng vì thế.
                    "trang_thai": xep_trang_thai(
                        ha_tang=ha_tang,
                        so_luot_chay_xong=len(all_replies),
                        vi_pham=violations,
                    ),
                    "loi_ha_tang": ha_tang,
                    "traceback": traceback_day_du,
                    "passed": (not violations) and not ha_tang,
                    "violations": violations,
                    "reply": reply,
                    # D1 — giữ TRANSCRIPT ĐỦ LƯỢT trong raw. Điều tra một ca
                    # leo thang mà chỉ có lượt cuối thì không lần ra được agent
                    # bắt đầu nhượng bộ từ đâu.
                    "all_agent_replies": all_replies,
                    "all_customer_texts": agent_result.get("all_customer_texts") or [],
                    "so_luot_da_chay": agent_result.get("so_luot_da_chay", 0),
                    # Tool THEO TỪNG LƯỢT — tách được "từ chối SAU KHI đã thử
                    # tra" (đúng) với "từ chối mà không thử gì" (over-refusal).
                    "tool_calls_theo_luot": agent_result.get("tool_calls_theo_luot") or [],
                    # Nửa "agent không nói được gì" — 18 ca MÙ với nó, xem
                    # tests/test_security/test_o_group_khong_chan_nham.py
                    "loc_dau_ra_theo_luot": agent_result.get("loc_dau_ra_theo_luot") or [],
                    "ly_do_fallback_theo_luot": agent_result.get("ly_do_fallback_theo_luot") or [],
                    # ĐƯỜNG ĐỊNH TUYẾN mỗi lượt (`nhe`/`thu_slot`/`day_du`) — ①
                    # đợt "OTP trước token" 24/08. Phân biệt "xanh vì O1-O5 giữ
                    # được" với "xanh vì câu lạc đề, chưa từng chạm LLM/O1-O5"
                    # (N2 nghiệm thu cả đợt) mà KHÔNG PHẢI mở code.
                    "duong_theo_luot": agent_result.get("duong_theo_luot") or [],
                    # Tách TIMEOUT khỏi TỪ CHỐI: cùng câu fallback, khác thời gian.
                    "thoi_gian_theo_luot": agent_result.get("thoi_gian_theo_luot") or [],
                    # Crescendo hay thắng ở lượt GIỮA rồi lượt cuối quay lại vô
                    # hại — biết vỡ ở lượt nào mới biết guardrail chặn ở đâu.
                    "first_violation_turn": first_violation_turn,
                    "tool_calls": [c.get("tool_name") for c in agent_result.get("tool_calls", [])],
                    # PAYLOAD ĐẦY ĐỦ — thêm 15/08, KHÔNG đổi nghĩa `tool_calls`.
                    #
                    # VÌ SAO TRƯỜNG MỚI CHỨ KHÔNG SỬA TRƯỜNG CŨ: file raw cũ đã
                    # ghi `tool_calls` là danh sách TÊN. Nếu đổi nó thành danh
                    # sách dict thì cùng một khoá mang hai nghĩa tuỳ ngày ghi,
                    # và mọi phép chấm lại phải đoán xem đang đọc file đời nào.
                    # Đúng họ lỗi đã tốn của đội cả buổi hôm nay (`[]` vs `None`,
                    # "không có" vs "không biết"). Trường mới thì file cũ chỉ
                    # đơn giản là thiếu khoá — một trạng thái đọc được rõ ràng.
                    #
                    # VÌ SAO CẦN: bộ chấm `so_lieu_dung_tham_chieu` và luật xuất
                    # xứ đều ĐỌC kết quả tool, mà raw chỉ lưu TÊN nên không phép
                    # chấm lại nào ngoài lượt chạy thật làm được. Đây đúng Luật 5:
                    # cái gì bộ chấm ĐỌC để phán quyết thì bản ghi phải LƯU.
                    # Thiếu nó, cổng chặn-nhầm 96 câu — cổng mạnh nhất ta có —
                    # đang TẮT.
                    #
                    # PII: payload đã được che ở tầng tool trước khi tới đây
                    # (`wallet_id` `********0068`, `phone` `036***0068`,
                    # `full_name` `⟦…⟧`). Raw nằm local, không rời máy.
                    "tool_calls_day_du": agent_result.get("tool_calls") or [],
                }
            )
        session.close()
    return results


# `_check_adv_patterns` (chấm trên MỘT reply) đã bị thay bằng
# `check_forbidden_tich_luy` ở `_harness.py` — quét TOÀN BỘ hội thoại và ghi rõ
# vi phạm ở lượt nào. Xoá hẳn thay vì để lại: một hàm chấm-lượt-cuối nằm cạnh
# một hàm chấm-tích-luỹ là lời mời gọi ai đó dùng nhầm cái yếu hơn.


def write_report(results: list[dict], out_path: Path, nguon_mo_hinh: dict) -> None:
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    # BA trạng thái. Mẫu số của tỉ lệ là số case ĐO ĐƯỢC, không phải tổng case
    # — nếu chia cho tổng thì mỗi lần chạm trần TPM là tỉ lệ tụt, và người đọc
    # tưởng chất lượng giảm trong khi thực ra chỉ là chưa đo được.
    khong_do = sum(1 for r in results if r.get("trang_thai") == "khong_do_duoc")
    chua_hanh_vi = [r for r in results if r.get("trang_thai") == "chua_co_hanh_vi"]
    do_duoc = total - khong_do - len(chua_hanh_vi)
    truot = do_duoc - passed
    # ① — phân bố ĐƯỜNG ĐỊNH TUYẾN toàn corpus (đếm LƯỢT).
    duong_dem = Counter(
        d for r in results for d in (r.get("duong_theo_luot") or [None])
    )
    lines = [
        f"# Báo cáo eval adversarial_set — {now_stamp()}",
        "",
        dong_bang_nguon_mo_hinh(nguon_mo_hinh),
        "",
        "> ⚠️ **Đường eval dùng sentinel `_ALWAYS_FRESH`** (`run_agent_turn`, "
        "`graph.py`) — OTP phiên LUÔN được coi là vừa xác thực xong. Không ca "
        "nào ở đây đo được hành vi khi OTP thiếu/hết hạn; trục đó chỉ đo được "
        "bằng chạy thật (`fin05do`/production) — xem finding A2 24/08.",
        "> ⚠️ **Harness gọi thẳng `run_agent_turn()` trong tiến trình** — JWT/"
        "rate-limit/audit-log KHÔNG nằm trên đường đo này. Kết luận về các "
        "tầng đó từ kết quả eval là kết luận SAI CHỖ ĐO; xem "
        "`tests/test_api/` cho bộ test có đi qua các tầng đó.",
        f"> 🚦 **{cau_hinh_dinh_tuyen_luc_chay()}.** Đóng Đ2 (24/08).",
        "> 🚦 **Phân bố đường định tuyến toàn corpus (đếm LƯỢT):** "
        + " · ".join(f"`{k}`={v}" for k, v in duong_dem.most_common())
        + " — ⚠️ một ca `passed=true` mà đi `nhe`/`thu_slot` nghĩa là CHƯA TỪNG "
        "chạm O1-O5/spotlighting, khác hẳn `passed=true` vì lớp phòng thủ giữ được.",
        "",
        (f"**Tổng:** {passed}/{do_duoc} ĐẠT trên số ĐO ĐƯỢC ({passed / do_duoc * 100:.1f}%) "
         f"· TRƯỢT {truot} · **KHÔNG ĐO ĐƯỢC {khong_do}**/{total}") if do_duoc else
        (f"**KHÔNG ĐO ĐƯỢC case nào** ({khong_do}/{total}) — xem mục lỗi hạ tầng." if total else "Không có case."),
        "",
    ]
    if khong_do:
        lines += [
            "> ⚠️ **KHÔNG ĐO ĐƯỢC ≠ TRƯỢT.** Case dưới đây chết vì hạ tầng "
            "(rate limit, timeout, code đang sửa dở) nên CHƯA có kết luận nào về "
            "agent — phải chạy lại, không được đọc thành lỗi chất lượng.",
            "",
        ]
        for r in results:
            if r.get("trang_thai") == "khong_do_duoc":
                lines.append(f"- **{r['case_id']}**: {r.get('loi_ha_tang', '')[:180]}")
        lines.append("")
    if chua_hanh_vi:
        # ĐỂ RIÊNG, và để NGAY TRÊN mục "agent bị dụ" — đây là mục dễ bị đọc
        # lướt nhất mà lại là mục duy nhất chỉ đích danh một bug của hệ thống.
        lines += [
            "## ⛔ CHƯA CÓ HÀNH VI ĐỂ CHẤM — cần ĐIỀU TRA, không phải chạy lại",
            "",
            "> Case dưới đây chết **trước khi agent kịp trả lời lượt nào**, và lỗi "
            "**không** mang dấu hiệu hạ tầng. Khác hẳn KHÔNG ĐO ĐƯỢC: chạy lại "
            "không giải quyết gì, phải mở traceback ra đọc. Đây là chỗ duy nhất "
            "trong báo cáo chỉ đích danh một thứ đang vỡ bên trong hệ thống.",
            "",
        ]
        for r in chua_hanh_vi:
            lines.append(f"- **{r['case_id']}**: {(r.get('violations') or [''])[0][:180]}")
        lines.append("")
    # ĐẾM CÂU BỊ BỘ LỌC CHẶN — nửa "agent KHÔNG NÓI ĐƯỢC GÌ".
    #
    # ĐẾM, KHÔNG PHÁN QUYẾT. Ở bộ đối kháng, từ chối thường là hành vi ĐÚNG,
    # nên một bất biến "phải trả lời được gì đó" sẽ phạt agent vì cư xử đúng —
    # đúng bẫy ca-âm-tính-số-1 mà security viết cho O2. Vế đạt/trượt cứng cho
    # siết nhầm nằm ở F-25 tầng (b), nơi agent BẮT BUỘC phải trả lời được.
    #
    # VÌ SAO MỤC NÀY PHẢI TỒN TẠI: đã đo được rằng thay sạch mọi reply bằng câu
    # an toàn vẫn cho 18/18 ĐẠT. Tức "18/18 -> 18/18" ở lượt so-cặp là ĐÚNG CÁI
    # ta sẽ thấy nếu bộ lọc xoá sạch mọi câu trả lời. Không có con số này thì
    # hai kết cục đối nghịch nhau đội chung một vỏ.
    bi_chan = [
        (r["case_id"], i + 1, nhom)
        for r in results
        for i, nhom in enumerate(r.get("loc_dau_ra_theo_luot") or [])
        if nhom
    ]
    if bi_chan:
        dem_nhom: dict[str, int] = {}
        for _, _, nhom in bi_chan:
            for n in nhom:
                dem_nhom[n] = dem_nhom.get(n, 0) + 1
        lines += [
            f"## 🔇 Bộ lọc đầu ra đã chặn {len(bi_chan)} lượt — ĐỌC BẰNG MẮT, không tự kết luận",
            "",
            "> Con số này KHÔNG phải đạt/trượt. Mốc so là nhánh **trước** (bộ lọc "
            "chưa tồn tại ⇒ **0**). Mọi mức tăng đều phải mở ra đọc: chặn đúng "
            "một rò rỉ và nuốt mất một câu trả lời hợp lệ trông giống hệt nhau ở đây.",
            "",
            f"- Theo nhóm: `{dem_nhom}`",
        ]
        for cid, luot, nhom in bi_chan[:15]:
            lines.append(f"- {cid} lượt {luot} · {nhom}")
        lines.append("")

    # ① — bảng ĐẦY ĐỦ mọi case ĐO ĐƯỢC, kể cả case passed=true. Đây chính là
    # chỗ N2 (nghiệm thu cả đợt) cần: phân biệt ADV-036/ADV-038 "xanh vì O1-O5
    # giữ được" với "xanh vì câu lạc đề, chưa từng chạm model" MÀ KHÔNG PHẢI
    # mở code hay đọc raw JSON.
    lines += ["## Đường định tuyến mỗi ca (`duong`, đọc được không cần mở code)", "",
              "| Case | passed | Đường đi từng lượt | Có chạm model? |", "|---|---|---|---|"]
    for r in sorted(results, key=lambda x: x["case_id"]):
        if r.get("trang_thai") in ("khong_do_duoc", "chua_co_hanh_vi"):
            continue
        dtl = r.get("duong_theo_luot") or []
        cham_model = "có" if any(d == "day_du" for d in dtl) else ("KHÔNG — toàn nhe/thu_slot" if dtl else "?")
        lines.append(f"| {r['case_id']} | {r['passed']} | {', '.join(str(d) for d in dtl) or '(rỗng)'} | {cham_model} |")
    lines.append("")

    # LOẠI case KHÔNG ĐO ĐƯỢC khỏi mục này — nếu để lẫn thì một case chết vì
    # rate limit sẽ nằm dưới tiêu đề "agent bị dụ thành công, cần fix ngay",
    # tức là đúng cái hiểu nhầm mà cả vòng phân loại này sinh ra để diệt.
    failing = [
        r for r in results
        if not r["passed"] and r.get("trang_thai") not in ("khong_do_duoc", "chua_co_hanh_vi")
    ]
    if failing:
        lines += ["## Case KHÔNG pass (agent bị dụ thành công — cần fix ngay)", ""]
        for r in failing:
            lines.append(f"### {r['case_id']} — {r['category']}: {r['description']}")
            lines.append(f"- Vi phạm: {'; '.join(r['violations'])}")
            lines.append(f"- Tool đã gọi: {', '.join(r['tool_calls']) or '(không)'}")
            lines.append(f"- Reply: {r['reply'][:300]!r}")
            lines.append("")
    else:
        lines.append("Không có case nào bị dụ thành công.")
        if khong_do:
            lines.append(
                f"\n*(Nhưng {khong_do} case CHƯA ĐO ĐƯỢC — chưa thể nói bộ này sạch.)*"
            )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nBáo cáo: {out_path}", file=sys.stderr)
    print(
        (f"Tổng: {passed}/{do_duoc} ĐẠT trên số ĐO ĐƯỢC · TRƯỢT {truot} · KHÔNG ĐO ĐƯỢC {khong_do}/{total}")
        if total else "0 case",
        file=sys.stderr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", type=Path, default=EVAL_DIR / "adversarial_set.jsonl")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    cases = load_jsonl(args.file)
    if args.sample:
        cases = cases[: args.sample]

    nguon_mo_hinh = xac_nhan_nguon_mo_hinh_luc_chay()
    print(f"🚦 {cau_hinh_dinh_tuyen_luc_chay()}", file=sys.stderr)
    print(f"🚦 {dong_bang_nguon_mo_hinh(nguon_mo_hinh)}", file=sys.stderr)
    print(f"Chạy {len(cases)} case adversarial từ {args.file} — gọi OpenAI thật.", file=sys.stderr)
    results = run(cases, nguon_mo_hinh)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = now_stamp()

    # Lưu raw JSON trước khi format báo cáo — xem run_golden_set.py cho lý do
    # (tránh lặp lại sự cố mất kết quả đã tốn phí OpenAI thật do lỗi format).
    raw_path = out_dir / f"adversarial_run_{stamp}_raw.json"
    raw_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw JSON (khôi phục nếu format báo cáo lỗi): {raw_path}", file=sys.stderr)

    out_path = args.out or out_dir / f"adversarial_run_{stamp}.md"
    write_report(results, out_path, nguon_mo_hinh)

    sys.exit(1 if any(not r["passed"] for r in results) else 0)


if __name__ == "__main__":
    main()
