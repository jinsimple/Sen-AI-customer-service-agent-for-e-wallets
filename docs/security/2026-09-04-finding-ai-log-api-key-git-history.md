# Finding: AI_LOG_API_KEY còn đọc được trong git history

> **Ngày:** 04/09/2026 · **Phát hiện bởi:** DevOps, khi soát 17 finding gitleaks sau khi chuyển
> `dependency-and-secret-scan` sang binary trực tiếp.

## Sự việc

`.env.example` từng chứa (đã gỡ khỏi HEAD hiện tại, nhưng gitleaks quét full git history — `fetch-depth: 0` — vẫn đọc lại được vĩnh viễn qua `git log -p`):

```
# ---- AI Hook Logging (provided by instructor) ----
AI_LOG_SERVER=https://ai-logs.note.transformerlabs.ai/api/ingest
AI_LOG_API_KEY=REDACTED_AI_LOG_KEY
```

Entropy cao, không có dấu hiệu placeholder — khác hẳn 15 finding còn lại trong cùng đợt quét
(đều xác nhận là sentinel test/hash file/placeholder tài liệu).

## Đánh giá của PO thật (04/09)

Khoá này là **telemetry do BTC AI20K tự cấp cho cả cohort** để đếm log hoạt động Claude Code —
hạ tầng của BTC, họ tự phát cho mọi repo (nằm trong repo là điều BTC lường trước, không phải
sự cố rò rỉ từ phía dự án). Rủi ro thấp: xấu nhất là gửi rác vào log-ingest của BTC, KHÔNG lộ
dữ liệu khách hàng/dự án.

## Quyết định

> 🔴 **ĐÍNH CHÍNH cùng ngày (append, không sửa):** bản đầu của hồ sơ này (viết trước khi PO thật
> có đủ ngữ cảnh) ghi "KHÔNG allowlist, giữ đỏ". Sau khi PO thật đánh giá rủi ro (xem trên), quyết
> định CUỐI là **CÓ allowlist, kèm chú thích rõ** — xem lý do bên dưới. Giữ dòng cũ lại đây làm
> bằng chứng lịch sử quyết định (Luật P — niêm, không xoá), KHÔNG áp dụng nữa.

- **CÓ allowlist trong `.gitleaks.toml`** (mảng `regexes`/`paths` của rule `generic-api-key`),
  KÈM CHÚ THÍCH RÕ ngay tại chỗ (không allowlist trống/im lặng) — đây là RISK-ACCEPT CÓ GHI CHÉP,
  khác với che giấu: người sau đọc `.gitleaks.toml` VÀ hồ sơ này hiểu ngay lý do, không cần điều
  tra lại từ đầu. `dependency-and-secret-scan` sẽ XANH sau khi land.
- **KHÔNG rewrite git history** (filter-repo/BFG/force-push) — quá nhạy cho một khoá rủi ro
  thấp: nhánh dùng chung, nhiều phiên đang làm việc song song, giữa cửa sổ chuẩn bị quay demo.
- **KHÔNG cần báo BTC** — họ là bên phát hành khoá, không phải nạn nhân của một lần rò rỉ.
- **KHÔNG thử gọi/xác thực khoá** — không dùng credential khả nghi, kể cả khi đang điều tra.

## Việc còn treo (không khẩn)

Nếu sau này BTC xác nhận khoá đã hết hạn/thu hồi hẳn, cập nhật lại chú thích trong
`.gitleaks.toml` ("đã thu hồi, xem xác nhận từ BTC ngày...") — không bắt buộc, chỉ để hồ sơ luôn
khớp trạng thái mới nhất.
