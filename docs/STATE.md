# Trạng thái hiện tại

Cập nhật: **2026-08-13** · Phiên vừa rồi: Claude Code (chuẩn bị tải 150 người)

> Ghi đè mỗi cuối phiên bằng `/wrapup`. Giữ **dưới 60 dòng**.
> Lịch sử quyết định KHÔNG nằm ở đây — nằm ở `docs/DECISIONS.md`.

## Vừa xong

- **Bảo mật PII** (ADR-010/011): chặn PII rời hệ thống lên LLM ở **cả hai đầu** — kết
  quả tool (`full_name`/`phone`/`account_no`/`user_id`/`wallet_id`) và tin nhắn khách
  tự gõ (`scrub_pii`). Bỏ họ tên khỏi system prompt. 14 test.
- **Chặn đồng thời** (ADR-012): `RedisConcurrencyLimiter`, hết slot → 503 + Retry-After.
- **Gộp 1 database** (ADR-013): bỏ fallback SQLite im lặng, Postgres publish loopback.
- **PostgresSaver** (ADR-014): hội thoại ra khỏi RAM process, sống sót restart.
- **Redis pub/sub live-chat** (ADR-015): fan-out liên worker.
- **Multi-worker 4** — verify thật trong container: 4 worker, 4 subscriber,
  PostgresSaver, 21/100 kết nối Postgres.

## Đang dở — chi tiết đủ để phiên sau tiếp ngay

- **Cắt token (mục 4b) CHƯA LÀM.** Đã đo xong, chưa sửa:
  - schema tool 1.945 token, **docstring chiếm 1.377** (create_ticket 351,
    request_human_handoff 333, get_customer_history 264, search_policy 242,
    lookup_transaction 187)
  - system prompt 4.587 token (Quy trình điều tra 1.644 · Ràng buộc bắt buộc 1.037 ·
    Giọng văn 671 · Ngoài phạm vi 533)
  - **Rủi ro:** docstring mã hoá ràng buộc hành vi thật ("KHÔNG tự chọn candidate",
    "không bịa mã giao dịch"). Cắt ẩu = hỏng chất lượng âm thầm.
  - **Baseline đối chiếu** (`eval/results/baseline_TRUOC_khi_cat_token_raw.json`):
    bịa số liệu **4/40 = 10,0%** · p50 24,3s · $0,1778/40 case. Sau khi cắt phải chạy
    lại `eval/measure_quality.py --n 40` trên CÙNG bộ, so ghép cặp; **bịa số liệu
    không được vượt 10%** mới được ship.

## Chặn / chờ (việc của PO)

- **Nâng tier OpenAI** — đường găng dài nhất. Tier 1 hiện tại: 200K TPM ⇒ ~13 lượt/phút
  cho TOÀN hệ thống ⇒ 150 người mỗi người 1 tin/11 phút. Cần Tier 2 (2M TPM), có lead time.
- **Tạo organization OpenAI + ký DPA** (Settings → Organization → Compliance APIs).
  Tài khoản cá nhân không ký được.
- **Hỏi mentor/luật sư về NĐ 13** — hoãn có điều kiện, mốc kích hoạt ở ADR-011.
- **Upload `project-knowledge/`** lên Project fin05 để các phiên Claude khác hết làm
  việc trên ảnh chụp cũ.

## Cảnh báo còn tồn

- **Load test 150 đồng thời CHƯA CHẠY** (PO hoãn sang 14/08). Mọi con số về đồng thời
  hiện vẫn là suy luận kiến trúc, chưa có số đo thật. Đây là việc đầu tiên nên làm.
- p95=119,5s trong baseline **KHÔNG phải lỗi timeout** — đã điều tra: đó là tổng cả
  case nhiều lượt của eval harness (max 136,5s ≈ 3 × trần 45s). Timeout per-turn hoạt
  động đúng, có test canh.
- Test bất biến 19/19 xanh · full suite **320 passed** · ruff sạch.

## Sau demo

- Ép thứ tự `_enforce_requester_is_party` → `_scrub_pii_cho_llm` ở tầng KIỂU DỮ LIỆU
  (hiện chỉ có test canh) — đề xuất của phiên bảo mật, hoãn có chủ đích.
- `contracts/tone-of-voice.yaml`; `eval/heldout_set.jsonl` CHỈ CHẠY MỘT LẦN gần cuối.
