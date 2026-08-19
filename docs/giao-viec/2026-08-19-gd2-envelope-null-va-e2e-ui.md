# GĐ2 — 19/08: vá `tool_calls: null` + CHUẨN MỚI của PO thật về nghiệm thu UI

> PO-agent viết, sau khi PO thật test UI thật và gặp lỗi mà TOÀN BỘ cổng + verify GĐ1 không bắt được.
> Đọc kèm: `docs/giao-viec/2026-08-18-team-o3-demo-len-main.md` (GĐ1, đã xong phần kỹ thuật — merge HOÃN).

## 1. SỰ CỐ — PO thật bắt được, không cổng nào của ta kêu

**[ĐO] PO-agent truy vết + tái tạo bằng đường sản phẩm thật (login Demo@123 → POST /agent/chat "chào bạn"):**
```
UI (https://localhost/chat): gõ "chào bạn" → "Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé."
backend: POST /agent/chat → 200 OK · agent_turn_duong_nhe · reply ĐẦY ĐỦ
JSON trả về: tool_calls = null        ← không phải []
client (ChatClient.tsx:346-349): result.tool_calls.length → TypeError trên null
  → rơi vào catch nhánh không-phải-ApiError → câu lỗi chung. Không bubble reply nào được vẽ.
```

**Phạm vi thật — BỐN envelope, không phải một:** `graph.py` `"tool_calls": None` tại
**:639 (đường nhẹ) · :789 · :906 · :999 (ba đường fallback lỗi nhà-cung-cấp)**. Chỉ đường nặng
hạnh phúc (:1230) trả mảng. Frontend `types.ts:280` khai `tool_calls: AgentToolCall[]` (không null).
⟹ mọi câu chào VÀ mọi lượt fallback đều vỡ UI theo cùng một cách.

**Vì sao GĐ1 không bắt được — ghi để không tự trách nhầm chỗ:** lỗi nằm ở HỢP ĐỒNG ENVELOPE
backend↔frontend, chỉ hiện khi đi đúng đường người dùng (trình duyệt→caddy→BFF→backend→client parse).
Verify GĐ1 đi đường API trần; cổng 46 ca đo bộ lọc, không đo hợp đồng envelope; `schemas.py` không
ép kiểu `tool_calls` nên server cứ 200. Tổ hợp "UI + đường nhẹ" chưa từng chạy vì `PHAN_LUONG_BAT=1`
mới bật trên fin05 từ 18/08 — lỗi NẰM SẴN từ commit `1e42146` (T1), không phải hồi quy của GĐ1.

## 2. HAI CHUẨN MỚI — PO THẬT RA LỆNH 19/08, ÁP VĨNH VIỄN

1. **QA/QC test THỰC TẾ trên giao diện localhost** sau mọi bản vá — PO thật không phải là người
   phát hiện lỗi UI nữa.
2. **Trước khi trình PO thật review: MỌI tính năng đã test với ≥3 GOOD CASE** trên UI thật.

## 3. VIỆC — theo vai

### CODER — gỡ băng CÓ KHAI, phạm vi HẸP
- Đổi `"tool_calls": None` → `"tool_calls": []` tại **đúng 4 dòng** :639 · :789 · :906 · :999.
  (`graph.py:219` đã dùng `or []` — không ảnh hưởng. Đường nặng :1230 không chạm.)
- `src/api/schemas.py`: nếu ChatResponse chưa ép kiểu `tool_calls` là **mảng bắt buộc** — thêm,
  để lớp lỗi này từ nay chết ở server-side validation thay vì sống tới client.
- KHÔNG chạm gì khác. Bản vá O3 (GĐ1) giữ nguyên — nó đã được nghiệm thu và vẫn đúng.
- Sau vá: invariants + check_contracts từ host → commit pathspec → dựng ảnh MỘT LẦN (khai qua Lead).

### QA/QC — hai tầng, tầng ② là CHUẨN MỚI
1. **Cổng envelope (0 token):** mọi đường trả về của `run_agent_turn` (nhẹ · 3 fallback · nặng)
   phải cho `tool_calls` là MẢNG. Viết từ đặc tả này, không đọc src.
2. **E2E Playwright trên stack Docker thật** (`frontend/e2e/`, theo khuôn `playwright.livechat.config.ts`
   — 🚫 config mặc định spawn `npm run dev` là bẫy ADR-009): đăng nhập 0974000145/Demo@123, phủ
   **ma trận tính năng × ≥3 good case** trên UI:
   - 0 token: login/logout · rail giao dịch + OTP phiên · danh sách & chi tiết vé · luồng duyệt
     (đăng nhập cskh/supervisor bằng user demo tương ứng) · câu chào đường nhẹ ("chào bạn"/"alo"/"hi")
   - Tốn token (KHAI TRƯỚC với Lead, Lead cộng sổ): câu giao dịch đường nặng · hành trình tạo vé ·
     policy search. Mỗi thứ 3 case tốt.
   - Nghiệm thu màn hình theo NỘI DUNG (bubble reply có chữ, có nguồn khi chạm tool), không chỉ theo HTTP.
3. Ma trận tính năng lấy từ PRD §2 (US-001→018) đối chiếu màn hình thật — tính năng nào chưa có UI
   thì ghi "ngoài phạm vi demo", không bịa case.

### BẢO MẬT — một đoạn
Xác nhận đổi `None→[]` + siết schema không mở bề mặt mới (dự kiến: không — thu hẹp hợp đồng là
chiều an toàn). Kèm định hạng finding nhãn PII lọt UI (GĐ1 mục ③) nếu chưa nộp.

### REVIEW
Soi diff 4 dòng + schema; soi bộ E2E của QA/QC theo trục "3 good case có THẬT SỰ khác nhau không
hay là một case chạy 3 lần" — đó là chỗ dễ gian nhất của chuẩn mới.

### LEAD
1. Điều phối như GĐ1 (trình tự đã chạy tốt, giữ nguyên). Dựng ảnh MỘT LẦN sau khi Coder + QA/QC land.
2. Khai ngân sách phần E2E tốn token TRƯỚC khi chạy (ước: ~9 lượt nặng ≈ 100–150K; còn ~650K).
3. KHÔNG chạy lại 10 lượt verify GĐ1 — diff 4-literal không chạm đường nặng; 3 case E2E đường nặng
   của QA/QC chính là smoke cho ảnh mới. Ghi rõ phán đoán này vào hồ sơ để PO thật thấy nó là
   QUYẾT ĐỊNH có khai, không phải bỏ sót.
4. Hồ sơ trình PO thật (bản GĐ1 + GĐ2 gộp): 6 ô cũ + ma trận tính năng×3-case + trạng thái 2 chuẩn mới.

## 4. ĐỊNH NGHĨA XONG GĐ2
- [ ] 4 envelope trả mảng — cổng envelope xanh từ host
- [ ] Schema ép kiểu — server-side chết sớm nếu tái diễn
- [ ] Ảnh mới: 3 phép kiểm (băm 2 cách · BUILD_COMMIT · grep vá) + cổng 46+ ca xanh
- [ ] **E2E localhost: ma trận tính năng × ≥3 good case — PASS, có ảnh chụp/log Playwright**
- [ ] Câu chào trên UI thật trả lời được (đúng ca PO thật đã vấp)
- [ ] Token E2E đã khai và cộng sổ
