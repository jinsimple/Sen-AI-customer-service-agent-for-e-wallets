# KẾ HOẠCH 3 CHỦ ĐỀ NÂNG CẤP (Đợt 2) — chia việc song song, không-ai-chờ-ai

> PO khởi động 15/08 (từ research 13/08, PO-TONG-KET §5). Nhánh: `dev/learning-loop`
> (nhánh tích hợp đợt-sau-demo). Ba chủ đề: 5a cảm xúc · 5b injection · 5c đa-lượt.
> KHÔNG phụ thuộc 3 việc PO thật (key/secret/note) — chạy song song với chúng.

## Nguyên tắc song song hoá (vì sao chia thế này)

Ràng buộc phụ thuộc thật:
- **5c** rẻ nhất, chia 2 pha: (i) BỘ TEST phát hiện lỗ (eval, không đụng code SP)
  → (ii) GUARDRAIL phòng thủ (code, sau).
- **5b** spotlighting + lọc đầu ra: code lệch-nội-bộ, KHÔNG đổi contract → không ADR.
- **5a** ES-xx: thêm tín hiệu định tuyến (giống FS-06) → ĐỔI CONTRACT, CẦN ADR-022 +
  PO thật ký. Đây là nhánh DÀI NHẤT → khởi động ADR sớm nhất để không thành đường găng.
- **Hạ tầng đếm-tín-hiệu-theo-thread** (Redis, theo `thread_id`): 5a (leo thang cảm xúc)
  và 5c-guardrail DÙNG CHUNG → thiết kế MỘT LẦN.

## LÀN SÓNG 0 — ngay lập tức, 3 vai 3 việc độc lập (KHÔNG ai chờ ai)

| Vai | Việc W0 (không chờ đầu vào từ ai) |
|---|---|
| **Security** | Đặc tả **5c**: kịch bản tấn công đa-lượt cho FIN-05 (Crescendo/Echo Chamber) — moi thông tin bên thứ 3 qua 5-10 lượt · ép agent HỨA hoàn tiền · leo thang cảm xúc giả · moi system prompt/ngưỡng qua nhiều lượt. Đầu ra: `docs/security/threat-model-multiturn.md` + bảng case đặc tả giao tester. (Ưu tiên vì tester chờ nó nhất.) |
| **Coder** | Dự thảo **ADR-022** (tín hiệu cảm xúc ES-xx: ES-01 bức xúc leo thang ≥N lượt · ES-02 ngôn ngữ khủng hoảng — tính ở TẦNG SERVICE giống FS-06, giữ ràng buộc cứng 2 · bật → agent ĐỀ NGHỊ request_human_handoff + ưu tiên ticket · KHÔNG thêm lượt gọi LLM) + diff contract đề xuất (fraud/signals trong resolution-state-machine.yaml). DỪNG chờ PO duyệt trước khi code. Đây là thinking-work không chờ ai. |
| **Tester** | Mở rộng **harness đa-lượt** cho adversarial: harness hiện có khách-ảo đa lượt (d72017a) — thêm chế độ "adversary mô phỏng" chạy kịch bản leo thang N lượt + chấm theo forbidden tích luỹ toàn hội thoại (không chỉ lượt cuối — bài học `reply`-là-lượt-cuối). Hạ tầng test, chưa cần nội dung case. |

## LÀN SÓNG 1 — mở khoá khi W0 của security xong

| Vai | Việc W1 |
|---|---|
| **Tester** | Security giao bảng case 5c → viết `eval/adversarial_multiturn_set.jsonl` (chạy trên harness đã mở rộng W0). Đây là "45 case toàn 1 lượt" được bù bằng bộ đa-lượt — lỗ hổng test lớn nhất. |
| **Security** | Đặc tả **5b**: kiểm kê 3 cửa untrusted (RAG partner_admin · ghi chú giao dịch · tin khách gõ) thành `docs/security/injection-surface-inventory.md` + đặc tả spotlighting (delimiter đánh dấu DỮ-LIỆU-không-phải-LỆNH) + đặc tả lọc ĐẦU RA (chặn reply lộ system prompt / tên ngưỡng nội bộ FS-06/OTP_*). |
| **Coder** | (nếu ADR-022 chưa duyệt) bắt **5b spotlighting** phần KHUNG khi security giao đặc tả — không đổi contract nên không chờ ADR. |

## LÀN SÓNG 2 — code (chạy song song 2 nhánh)

| Vai | Việc W2 |
|---|---|
| **Coder** | **5b**: spotlighting kết quả tool + RAG (graph.py/customer_tools.py) · lọc đầu ra. **5a** (SAU khi PO ký ADR-022): classifier cảm xúc tiếng Việt tầng service + **hạ tầng đếm-tín-hiệu-theo-thread** (Redis) — thiết kế để 5c-guardrail dùng lại. |
| **Tester** | Chạy bộ đa-lượt trên bản có/chưa guardrail → đo lỗ trước-sau. Test 5b (injection gồm indirect qua RAG). Test 5a (ES-xx bật đúng → đề nghị handoff, không bịa cảm xúc). |
| **Security** | Re-probe 5b (spotlighting có chặn thật injection? lọc đầu ra có rò?) + rà classifier 5a không đưa cảm xúc vào quyết định tự động (giữ ràng buộc cứng 2). |

## LÀN SÓNG 3 — guardrail đa-lượt (5c pha ii)
Coder: guardrail nhìn CẢ hội thoại + đếm tín hiệu tích luỹ theo thread (dùng hạ tầng
W2) → case ranh giới định tuyến sang người. Tester: bộ đa-lượt phải giảm ASR sau guardrail.

## Cổng & thẩm quyền
- 5b, 5c: KHÔNG đổi 3 contract nguồn → không ADR, code theo quy trình thường.
- 5a: ĐỔI contract → ADR-022, **PO thật ký trước khi code phần contract**. Coder soạn
  dự thảo ngay (W0) để PO duyệt sớm, không thành đường găng.
- Mọi thay đổi prompt (lọc đầu ra, spotlighting đổi cách trình bày cho LLM) → qua CỔNG ĐO
  khi hạ tầng đo k≥3 sẵn; trước đó đo thủ công + gate 0% bịa. KHÔNG nới ràng buộc cứng.

## Chờ PO thật
- Ký ADR-022 (khi coder trình) · quyết N cho ES-01 (số lượt leo thang) — đề xuất N=3,
  chốt sau khi có bộ đa-lượt để canh.
