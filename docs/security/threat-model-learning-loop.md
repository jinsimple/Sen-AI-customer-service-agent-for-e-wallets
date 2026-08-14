# Threat model — Vòng lặp học từ phản hồi (learning loop)

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> Đối tượng: thiết kế 3 phase trong `docs/giao-viec/2026-08-14-ke-hoach-learning-loop.md`.
> Yêu cầu đọc kèm: `docs/security/review-2026-08-13.md` (F-02/F-03/F-04 gộp
> chung migration Phase 1 với các trường reject mới).
>
> **Phải chốt xong tài liệu này trước khi Phase 2 (exporter) chạy** — người
> duyệt ứng viên là phòng tuyến chính, và phòng tuyến phải có checklist trước
> khi có traffic, không phải sau.

---

## 0. Vì sao đây là bề mặt tấn công MỚI

Mọi kiểm soát hiện có của FIN-05 canh **hành động trong một phiên**: authz
theo role, HITL ở DB, OTP, lọc injection — thiệt hại bị chặn tại từng request
và không vượt qua ranh giới phiên. Vòng lặp học mở một **kênh xuyên phiên và
xuyên thời gian**: nội dung do người không tin cậy tạo ra (hội thoại, điểm
CSAT) chảy vào các artifact định hình hành vi tương lai của agent
(`eval/golden_set.jsonl`, few-shot) và vào **chính cây thước đo**
(bộ eval + gate 0% bịa). Ba hệ quả không có ở bề mặt cũ:

1. Một cuộc tấn công thành công ảnh hưởng **mọi phiên tương lai**, không chỉ
   phiên của kẻ tấn công.
2. Đầu độc bộ eval = làm mù thước đo — regression về sau trở nên **vô hình
   một cách hợp lệ** (test vẫn xanh vì thước đã cong).
3. Không CHECK constraint hay `require_role` nào áp lên file trong `eval/` —
   lớp phòng thủ duy nhất là **quy trình duyệt của con người** + scrub tại
   điểm export. Cả hai đều chưa tồn tại hôm nay.

Riêng với PII: `eval/*.jsonl` nằm trong git — dữ liệu vào đó là **vĩnh viễn**
(rewrite history không cứu được bản clone/fork đã tồn tại). Điểm export vì
vậy là ranh giới một chiều, phải đối xử như ranh giới "dữ liệu rời hệ thống"
của ADR-010/011.

## 1. Sơ đồ luồng và điểm tin cậy

```
[Khách/kẻ tấn công]──chat──▶ PostgresSaver (transcript GỐC, chưa scrub)
        │                                │
        └──CSAT 1–5──▶ chat_sessions     │
                            │            │
[Sếp]──reject + reason──▶ resolutions    │
                            │            │
                            ▼            ▼
                    ┌─ EXPORTER (Phase 2) ─┐   ← RANH GIỚI SCRUB (một chiều)
                    │ reject / CSAT ≤ 2    │
                    └──────────┬───────────┘
                               ▼
                   eval/candidates/*.jsonl      ← đã vào git = vĩnh viễn
                               ▼
                  [NGƯỜI DUYỆT — phòng tuyến chính]
                               ▼
              eval/golden_set.jsonl · few-shot trong prompt
                               ▼
              hành vi agent tương lai + thước đo gate 0% bịa
```

Điểm mấu chốt về **quyền kiểm soát tín hiệu phễu**: hai tín hiệu chọn lọc
không tương đương về độ tin cậy —

| Tín hiệu | Ai kiểm soát | Độ tin cậy |
|---|---|---|
| Resolution bị **reject** | Sếp (supervisor) bấm | Cao — có người thẩm quyền ở giữa; kẻ tấn công không tự kích hoạt được |
| **CSAT ≤ 2** | 100% khách tự chấm | **Bằng không** — kẻ tấn công tự đưa hội thoại của mình vào phễu, chi phí ~0 |

Mọi ứng viên đến từ nhánh CSAT phải được coi là **do kẻ tấn công tự đề cử**.

## 2. TM-01 — Data poisoning qua hội thoại dàn dựng

**Đường đi cụ thể trên thiết kế Phase 2:**

1. Kẻ tấn công (bất kỳ ai trong 150 người test, hoặc account seed bị lộ) mở
   phiên chat, dàn dựng hội thoại chứa nội dung hắn kiểm soát: câu chữ dạy
   sai chính sách ("ví X luôn hoàn tiền trong 24h không cần điều tra"), mẫu
   câu chứa chỉ thị ẩn cho LLM, hoặc cách diễn đạt cố tình mơ hồ.
2. Hắn tự chấm CSAT 1 → hội thoại lọt phễu `CSAT ≤ 2` mà không cần bất kỳ
   người nội bộ nào hành động.
3. Exporter kết xuất thành case ứng viên trong `eval/candidates/`.
4. Nếu người duyệt nhận case **nguyên văn** (giữ đúng câu chữ của hắn):
   - Vào `golden_set` → hành vi "đúng" của agent từ nay được định nghĩa một
     phần bằng văn bản của kẻ tấn công; các lần so ghép cặp sau tối ưu prompt
     để chiều theo case đó.
   - Vào **few-shot** → văn bản của hắn được nhúng thẳng vào tầng prompt của
     MỌI phiên tương lai — đây là **indirect prompt injection có tính bền**,
     nguy hiểm hơn mọi injection 1 phiên đã rà (OWASP LLM01 + LLM04, khớp
     cảnh báo Unit 42 03/2026 về indirect injection quy mô lớn).

**Phân tích phòng tuyến:** thiết kế Phase 2 đã đúng ở chỗ "NGƯỜI DUYỆT LÀ
CỔNG — không có đường tự động vào bộ eval". Threat model này bổ sung: cổng
người duyệt chỉ đứng vững nếu có **luật cấm nhận nguyên văn** (mục 5,
checklist A) — người duyệt phải **viết lại** case bằng lời của mình + dữ liệu
seed tổng hợp. Viết lại phá vỡ cùng lúc hai vector: payload injection (câu
chữ của kẻ tấn công không sống sót qua paraphrase) và PII (dữ liệu thật không
được chép sang). Đây là khuyến nghị quan trọng nhất của tài liệu này.

**Giảm nhẹ bổ sung:** metadata xuất xứ trên mỗi ứng viên (`session_id`,
`user_id` giả danh hoá, ngày, tín hiệu phễu nào) để người duyệt thấy được
cụm bất thường; trần số ứng viên/người dùng (mục 3).

## 3. TM-02 — CSAT bombing

**Kịch bản:** một người (hoặc nhóm nhỏ trong 150 người test) chấm 1 sao hàng
loạt để (a) đẩy khối lượng lớn hội thoại chọn lọc vào phễu — làm ngập người
duyệt đến mức duyệt ẩu, hoặc (b) bóp méo thống kê CSAT trong
`/reports/summary` (US-018) khiến PO ra quyết định trên số rác.

**Ngưỡng/lọc đề xuất cho exporter (coder làm, tester viết test từ đặc tả này):**

1. **Phiên quá ngắn bị loại**: tối thiểu **3 lượt khách** VÀ **≥ 1 tool call
   thật** trong transcript — hội thoại không có tool call thì không chứa
   phán đoán nghiệp vụ nào đáng học, và đây là loại phiên rẻ nhất để spam.
2. **Trần theo người dùng**: tối đa **1 ứng viên/người dùng/ngày** và tối đa
   **3 ứng viên/người dùng** trong toàn bộ vòng đời phễu — vượt trần thì ghi
   log, không xuất.
3. **Trần toàn cục**: tối đa **20 ứng viên/ngày**; vượt là dấu hiệu bất
   thường, exporter dừng và cảnh báo thay vì xuất tiếp (fail-closed).
4. **Một CSAT cho mỗi phiên** — xác nhận route
   `POST /live-chat/sessions/{id}/csat` từ chối chấm lại/ghi đè (coder kiểm,
   security chưa xác minh trên code).
5. **Báo cáo phân phối**: `/reports/summary` hiển thị phân phối CSAT theo
   ngày + số phiên bị loại bởi từng luật lọc — spike 1 sao đột ngột phải nhìn
   thấy được, không cần đợi ai nghi ngờ.

**Lưu ý thiết kế (câu hỏi cho coder trước khi viết exporter):** CSAT hiện
gắn vào `chat_sessions` = phiên **live-chat với CSKH người thật**, trong khi
đối tượng học là hành vi **AI agent** (transcript nằm trong LangGraph
checkpoint). Điểm 1 sao có thể phản ánh người xử lý, không phải AI. Exporter
phải định nghĩa rõ transcript nào được xuất và tín hiệu CSAT quy cho ai —
nếu không, phễu sẽ "học" nhầm từ lỗi của con người. (Chi tiết ở mục 7.c.)

## 4. TM-03 — Nhãn từ chối làm kênh rò (khuyến nghị cho PO chốt — kế hoạch §5.3)

**Vấn đề:** `reject_reason` enum thì an toàn nhưng nghèo; ghi chú tự do của
sếp là nhãn chuyên gia giá trị nhất nhưng là kênh rò kép: PII khách ("KH Trần
Văn B khai sai số tài khoản 9704...") và thông tin nội bộ (ngưỡng gian lận,
tên quy trình) — nếu ứng viên mang nó vào git thì rò vĩnh viễn, và nếu nó
lọt vào few-shot thì thông tin nội bộ đi thẳng lên LLM mọi phiên.

**Khuyến nghị của security: phương án lai, tách theo ranh giới lưu trữ.**

1. **Enum bắt buộc** (5 giá trị đề xuất của kế hoạch: `sai_so_lieu ·
   sai_phan_loai · thieu_can_cu · sai_chinh_sach · khac`) — đây là trường
   duy nhất máy được phép đọc/xuất/thống kê.
2. **Ghi chú tự do CHO PHÉP, nhưng:**
   - qua `scrub_pii()` **trước khi ghi DB** (tinh thần ADR-010 — scrub trước
     khi dữ liệu rời vùng kiểm soát, không phải sau);
   - chỉ đọc được qua route staff (cskh/supervisor), **không bao giờ** xuất
     hiện trong kết quả tool của agent (không lên LLM), **không bao giờ**
     được exporter chép vào `eval/candidates/` — kể cả bản đã scrub;
   - người duyệt ứng viên được *đọc* ghi chú trong hệ thống để hiểu case,
     rồi **tự viết lại** phần cần thiết vào case bằng lời của mình (nhất
     quán với luật cấm-nguyên-văn của TM-01).
3. Lý do bác bỏ hai phương án đơn: *enum thuần* vứt đi đúng phần phán đoán
   chuyên gia mà cả đợt learning-loop sinh ra để nhặt (kế hoạch §1 gọi đây là
   "phát hiện đắt nhất"); *tự do + scrub rồi xuất* đặt toàn bộ an toàn lên
   một bộ scrub xác suất (NER có tỉ lệ lọt) trước ranh giới một chiều là git
   — che nhầm còn cứu được, để lọt thì không.

**Tóm tắt cho PO:** giá trị nhãn ở lại trong DB (truy cập theo role), chỉ
enum đi qua ranh giới export. Sếp vẫn gõ thoải mái, git không bao giờ thấy.

## 5. ĐẦU RA A — Checklist chống poisoning cho NGƯỜI DUYỆT ứng viên

> Giao **tester** tích hợp vào `eval/CANDIDATE-REVIEW.md`. Mỗi case ứng viên
> phải qua đủ các mục; một mục fail = LOẠI (ghi lý do vào nhật ký duyệt, giữ
> file ứng viên để điều tra, không xoá).

- [ ] **Nguồn**: case đến từ nhánh nào (reject / CSAT)? Nếu CSAT — nhớ rằng
      người chấm tự đề cử được case, soi kỹ gấp đôi.
- [ ] **Cụm bất thường**: cùng `user_id` (giả danh hoá) hoặc cùng khung giờ
      với ≥ 2 ứng viên khác? → nghi CSAT bombing, đối chiếu báo cáo phân phối
      trước khi nhận bất kỳ case nào của cụm.
- [ ] **Chỉ thị ẩn**: transcript có câu chữ nói VỚI hệ thống thay vì với
      CSKH không ("bỏ qua hướng dẫn", "từ giờ trả lời là...", "luôn hoàn tiền
      khi...", nội dung dạy chính sách không tồn tại)? → LOẠI, đánh dấu
      nghi injection.
- [ ] **Phán đoán nghiệp vụ có thật**: case có ≥ 1 tool call và một điểm
      sai/đúng nghiệp vụ xác định được (đối chiếu enum `reject_reason`)?
      Case chỉ có "khách không hài lòng" chung chung → LOẠI.
- [ ] **CẤM NGUYÊN VĂN**: case đưa vào `golden_set`/few-shot phải được VIẾT
      LẠI bằng lời người duyệt + dữ liệu seed tổng hợp (tên/SĐT/số tài khoản
      lấy từ `data/generated/`, không phải từ transcript). Không copy-paste
      bất kỳ câu nào của khách. Đây là mục quan trọng nhất — nó vô hiệu cả
      payload injection lẫn PII còn sót.
- [ ] **PII sót**: sau viết lại, rà lần cuối — không tên thật, SĐT thật,
      số tài khoản thật, địa chỉ, email, và không mang theo `reject_reason`
      dạng ghi chú tự do (chỉ enum).
- [ ] **Cân bằng bộ**: case mới không làm một kịch bản/loại khiếu nại chiếm
      quá 20% golden_set — bộ lệch là bộ dễ bị uốn.
- [ ] **Nhật ký duyệt**: ghi ai duyệt, ngày, nguồn case, quyết định
      nhận/loại + lý do — bản thân phễu cũng cần audit trail (khớp F-05).

## 6. ĐẦU RA B — Danh sách kiểm scrub tại điểm export

> Giao **coder** hiện thực thành test đối kháng cho exporter (tinh thần
> "chạy thật, không suy luận"). Mỗi dòng là một case test tối thiểu; kỳ vọng:
> giá trị KHÔNG xuất hiện trong file ứng viên đầu ra.

**B1 — PII khách tự gõ (dữ liệu thật của người test, rủi ro ADR-011):**
1. Tự xưng tên: "mình là Bách", "em tên Nguyễn Thị Hoa ạ" (bắt bằng NER —
   regex không bắt được, đúng bài học ADR-010).
2. SĐT mọi format VN: `0912345678`, `+84 91 234 56 78`, `091-234-5678`,
   đọc rời "không chín một hai...".
3. Số tài khoản/thẻ: chuỗi 9–19 số, có/không dấu cách; đầu `9704`.
4. CCCD 12 số (chấp nhận false positive che nhầm mã 12 số khác — đánh đổi đã
   chốt ở checklist observability, không nới regex).
5. Email, địa chỉ nhà (NER), ngày sinh dạng "sinh ngày ...".
6. PII của **bên thứ ba** trong case chuyển nhầm (tên/số người nhận) — kiểm
   cả khi nó nằm trong kết quả tool được nhúng lại vào transcript.

**B2 — Trường cấm xuất (kiểm cấu trúc, không phải nội dung):**
7. `reject_reason` ghi chú tự do: KHÔNG có trong file xuất, kể cả đã scrub —
   chỉ enum (TM-03).
8. `user_id`/`session_id` thật: chỉ xuất dạng giả danh hoá (hash có salt),
   đủ để gom cụm khi duyệt, không đủ để truy ngược.
9. OTP code, JWT, ws-ticket nếu lỡ nằm trong transcript (khách paste nhầm) —
   phải bị che như PII.
10. Tên ngưỡng/tín hiệu nội bộ (`FS-06`, `OTP_STEPUP_FRESH_MINUTES`, tên
    file nội bộ) nếu xuất hiện trong nội dung — không được rời hệ thống
    (khớp hướng "lọc đầu ra" PO-TONG-KET §5b).

**B3 — Đối kháng scrub (kẻ tấn công chủ động né scrub):**
11. PII chèn ký tự: "0 9 1 2 3 4 5 6 7 8", "chín-một-hai", zero-width space.
12. PII trong context đánh lừa NER: "bạn tôi tên là X nhưng đó không phải
    tên thật đâu".
13. Prompt-injection payload sống sót qua scrub (scrub chỉ che PII, không che
    chỉ thị): xác nhận file ứng viên mang **cờ cảnh báo** khi
    `_contains_injection_signal` bắn — để người duyệt thấy ngay ở checklist A.

**B4 — Fail-closed:** scrub lỗi (Presidio timeout, model NER thiếu) →
exporter **không xuất gì** và báo lỗi, tuyệt đối không xuất bản chưa scrub.

## 7. NHIỆM VỤ 3 — Rà thiết kế Phase 1 (trạng thái: coder CHƯA trình gói ADR)

Chưa có dự thảo ADR/diff contract nào trong repo tại thời điểm viết (đã kiểm
`docs/giao-viec/`, `docs/DECISIONS.md`, git log `dev/learning-loop`). Ý kiến
rà **sơ bộ** dưới đây để coder soạn gói cho đúng ngay từ đầu; security sẽ rà
chính thức khi gói được trình:

a. **Trường mới không lộ qua route customer** (least-privilege, tinh thần
   INV-11): `reject_reason` (enum + note) và `rejected_by/rejected_at` chỉ
   trả qua route staff. Kiểm đặc biệt: kết quả `get_customer_history` — nếu
   ticket của khách mang theo lý do reject thì nó lên LLM và tới khách; ghi
   chú tự do của sếp KHÔNG bao giờ được vào context agent (TM-03).
b. **Reject vẫn KHÔNG cần OTP — xác nhận đúng contract hiện hành.** Duyệt
   (chạm tiền) có OTP, từ chối (không chạm tiền) không — hành động an toàn
   phải rẻ hơn hành động nguy hiểm. Ai "tiện tay" thêm OTP cho reject là tạo
   sai lệch khuyến khích: sếp sẽ ngại từ chối. Giữ nguyên.
c. **Gộp vào cùng migration đợt này (đã xác minh trên code, xem F-02/03/04
   của `review-2026-08-13.md`):**
   - `resolutions.created_by` **chưa tồn tại** — thêm cột + backfill + CHECK
     `approved_by != created_by` (maker–checker). Lưu ý: PO-TONG-KET §4 dẫn
     "models.py:331 có sẵn" là nhầm sang cột của `Escalation`.
   - Guard trạng thái cho reject (`status == "pending_approval"`) — hiện
     resolution đã `approved` vẫn reject được, không vết (F-03). Trường
     `rejected_by/rejected_at` của chính Phase 1 là một nửa lời giải; guard
     là nửa còn lại. Đồng thời chốt với PO: guard approve đang nhận cả
     `draft` (`main.py:803`) — lệch transitions trong contract, sửa cùng lúc.
   - Consume OTP duyệt sau khi dùng (F-04) — xoá/đánh dấu `AuthSession` ngay
     sau approve thành công, kèm test.
d. **Câu hỏi thiết kế phải trả lời trong ADR trước khi PO duyệt:** CSAT gắn
   `chat_sessions` (phiên live-chat với người) trong khi phễu học nhắm hành
   vi AI (transcript ở LangGraph checkpoint) — exporter Phase 2 xuất
   transcript nào, và điểm CSAT quy cho AI hay cho CSKH người? Nhập nhằng ở
   đây là phễu học nhầm từ lỗi của con người (TM-02).

## 8. Rủi ro tồn dư sau khi áp toàn bộ giảm nhẹ

- Scrub là xác suất — NER có tỉ lệ lọt; luật cấm-nguyên-văn (checklist A) là
  lớp bù, nhưng phụ thuộc kỷ luật người duyệt. Kiểm tra chéo định kỳ: security
  rà ngẫu nhiên N case đã nhận mỗi đợt.
- Người duyệt là single point — hiện là 1 người (tester/PO). Chấp nhận được
  ở quy mô demo; khi phễu chạy thường xuyên, cần 2 người (đề xuất, chưa cần
  quyết bây giờ).
- Poisoning "chậm" dưới mọi ngưỡng (mỗi tuần 1 case sạch sẽ, uốn dần) — không
  ngưỡng nào bắt được; phòng tuyến thật là cân bằng bộ (checklist A, mục cân
  bằng) + so ghép cặp có gate 0% bịa trước mọi thay đổi prompt.
