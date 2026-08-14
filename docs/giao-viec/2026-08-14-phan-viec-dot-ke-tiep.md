# PHÂN VIỆC ĐỢT KẾ TIẾP — PO tổng hợp từ kiểm kê coder + sổ điều phối

> PO lập đêm 14/08 theo lệnh PO thật ("hỏi tồn đọng rồi chia việc cho 3 vai").
> Nguồn: kiểm kê A1–D2 của coder + sổ `2026-08-14-dieu-phoi-sau-huy-demo.md`.
> Nhánh: `dev/learning-loop`. Mỗi vai làm theo THỨ TỰ trong mục của mình.

## Ưu tiên toàn cục (đọc trước)

1. **C4 — BOLA thật đang mở** (REST `POST /tools/lookup_transaction` không áp
   `_enforce_requester_is_party` — khách lạ tra được amount/fee/status/des
   giao dịch không liên quan; 2 xfail-strict đang canh): lỗ bảo mật cao nhất
   kiểm kê. Code đang LỆCH contract (authority-matrix ghi rõ quyền xem ép ở
   tầng dưới) → fix KHÔNG cần ADR. Deadline cứng: trước mọi người dùng thật.
2. **C2/C3 — lỗ CI hệ thống**: vitest không trong CI (4 test ChatClient đỏ
   từ hotfix 1 không ai thấy) + bộ quét guard route tự skip trong CI. Lưới
   an toàn đang thủng ở tầng quy trình — vá một lần, lợi mãi mãi.
3. Gói B2 khép bằng đúng MỘT lượt đo còn lại (phán quyết e41d0b3).

## CODER — thứ tự

1. **Lượt đo cuối gói B2** theo phán quyết e41d0b3: nhánh "chỉ luật 4+1"
   (gỡ luật bước 3), so với nền 161529. Gate đặt sẵn trong phán quyết —
   ĐẠT thì ship 4+1, hỏng (c) thì HOLD + điều tra bằng đọc transcript.
2. **C4 BOLA**: áp `_enforce_requester_is_party` vào REST lookup_transaction
   (đường CSKH/sếp tra hộ giữ nguyên theo contract — chỉ chặn khách tra
   giao dịch không phải của mình). Gỡ 2 xfail-strict thành test thường
   (phối hợp tester — file test vùng họ).
3. **F-12** khoá brute-force OTP duyệt (5 test của QA chờ; khoá thì mã đúng
   cũng không qua).
4. **Nhịp migration gộp** note + F-11 + F-13 + F-14 (lệnh ràng buộc thứ tự
   d161c26 + 5 điều kiện sentinel; 7 test trạng thái đích + 13 test note chờ).
5. **C2/C3 phần sửa**: đưa `npm run test:unit` vào CI + sửa 4 test ChatClient
   đỏ; cho bộ quét guard route chạy được trong CI (stack test hoặc job riêng
   có Docker) — tester ra tiêu chí, bạn nối dây.
6. **ADR-020** (maker–checker `created_by IS NULL OR approved_by !=
   created_by` + V6 backend + câu hỏi sếp-tự-điều-tra) + kèm luôn quyết định
   B2-luật-3 nếu tới lúc đó đã rõ.
7. **Đợt reseed gộp** (brief riêng khi tới lượt): from_bank 28 case + M-04 +
   C8 (USR-PA01 vào TEST_ACCOUNT_USER_IDS) + C10 (script seed kho RAG) +
   seed đủ 3 action_type + C12 đối soát residue.
8. **Vệ sinh nhỏ gộp một commit**: C1 eslint ×4 · C6 `--out` hỏng · C7 log
   OTel TypeError · C9 xoá key chết khỏi .env · C11 chạy thử downgrade
   alembic ADR-019 một lần.
9. **B6 cắt token** — CHỈ SAU khi có kết luận cơ chế hồi quy phân loại (nghi
   phạm chung: độ dài prompt). B3 timezone (31 chỗ utcnow) + B4 (L4-04) +
   B5 (ép thứ tự tầng kiểu) xếp sau đợt này trừ khi PO thật đôn.

## TESTER (QA/QC) — thứ tự

1. **D2 thành máy**: đưa "so sánh TẬP HỢP check hỏng trước/sau" vào thẳng
   output `measure_quality.py` (bảng ca-xấu-đi/ca-tốt-lên tự in) — chính là
   thứ đã cứu gói B2 hôm nay, để máy làm thay người từ giờ. Kèm C13: dọn 3
   lượt đo bỏ đi (~$0,65) vào thư mục archive cho khỏi nhầm.
2. **C4**: khi coder fix xong — gỡ xfail-strict thành test thường + thêm ca
   đối chứng (CSKH/sếp tra hộ vẫn được phép theo contract).
3. **C2/C3 phần tiêu chí**: định nghĩa "CI đạt" (unit test đỏ phải làm CI
   đỏ; guard route phải được canh ở đâu đó có Docker — job nào, tần suất
   nào), giao coder nối dây, bạn nghiệm thu bằng cách CỐ TÌNH làm đỏ.
4. **D1**: xuất transcript đủ lượt trong raw của harness (bài học reply-chỉ-
   là-lượt-cuối — 2 vai đã vấp).
5. Nghiệm thu nhịp migration + note + F-12 của coder bằng bộ test đã dựng.
6. Sau reseed: nghiệm thu bộ case demo mới + 3 nhãn action_type nhìn bằng mắt.

## SECURITY — thứ tự

1. **C4**: sau fix của coder — probe thật xác nhận đóng (khuôn cũ: REST +
   token khách lạ), và rà xem còn REST tool route nào cùng họ lỗi không
   (get_customer_history đã đúng chưa? — đối chiếu từng route trong
   agent-tools/authority-matrix).
2. Rà nhịp migration khi coder nộp (sentinel 5 điều kiện + note 3 điều kiện
   TM-03 + trạng thái đích).
3. **ST2-P0-3 — soạn khuyến nghị cho PO thật quyết** (che gì/giữ gì cho
   staff trong live-chat; deadline: trước đợt 150 người thật — đây là mục
   PO thật đang nợ quyết, cần hồ sơ của bạn để quyết nhanh).
4. Threat model đợt reseed (dữ liệu mới có phá giả định che PII/masking nào).
5. Rà ADR-020 trước khi trình PO thật.

## Việc của PO thật (không đổi + 1 mục mới)

- Nghiệm thu kết quả lượt đo cuối gói B2 (PO-agent sẽ trình cặp số liệu).
- Duyệt ADR-020 khi trình. · Tier OpenAI + DPA. · Quyết ST2-P0-3 (chờ hồ sơ
  security ở mục 3). · **MỚI**: xác nhận thứ tự ưu tiên đợt này — đặc biệt
  nếu muốn đôn B3 (timezone khách thấy) hoặc B4 lên sớm hơn.
