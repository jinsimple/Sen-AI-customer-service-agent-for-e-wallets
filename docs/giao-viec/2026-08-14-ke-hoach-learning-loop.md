# KẾ HOẠCH — Vòng lặp học từ phản hồi (learning loop) — nhánh `dev/learning-loop`

> PO lập 14/08 dựa trên đánh giá của coder ("có trí nhớ, chưa có học").
> Nhánh làm việc: **`dev/learning-loop`** (tách từ `f2d4785`).
> **`main` ĐÓNG BĂNG tới sau demo tối 14/08** — không ai commit lên main.
> Merge về main qua PR, điều kiện: 19/19 bất biến + full suite xanh + PO duyệt.

## 1. Phân tích hiện trạng (PO xác nhận đánh giá của coder + bổ sung)

**Đã có (giữ nguyên, là nền tảng):** PostgresSaver = trí nhớ trong phiên
(US-010, cố ý không xuyên phiên) · RAG = cơ chế cải-tiến-lúc-chạy duy nhất ·
bộ eval ~200 case = "bộ nhớ hồi quy" nhưng vòng lặp hoàn toàn thủ công.

**Chưa có:** không đường nào cho lỗi production tự chảy vào eval; prompt tĩnh;
không few-shot từ case thật; không fine-tuning (và sẽ KHÔNG làm — xem §4).

**Phát hiện đắt nhất — nhãn chuyên gia bị vứt tại nơi sinh ra:**
- Sếp reject chỉ set `status="rejected"` (main.py:844) — không lý do, không
  `rejected_by/rejected_at` (nhánh approve thì ghi đủ). Đây là phán đoán của
  người thẩm quyền cao nhất về "AI/CSKH sai ở đâu" — đang bốc hơi 100%.
- CSAT 1–5 lưu vào `chat_sessions` nhưng không ai đọc để phân tích.
- QA-02: `hitl_status` kẹt `pending` vĩnh viễn → thống kê duyệt/từ chối chưa
  tin được. **Phải vá trong đợt này** — không có số sạch thì không đo được gì.

**Bổ sung của PO — 3 rủi ro coder chưa nêu, quyết định thiết kế phải né:**
1. **Data poisoning:** vòng lặp học là BỀ MẶT TẤN CÔNG mới — hội thoại được
   dàn dựng (hoặc CSAT bombing) có thể chảy vào eval/few-shot và uốn hệ thống
   theo hướng kẻ tấn công muốn. Người duyệt ở giữa (bước 2) chính là phòng
   tuyến — vai security phải threat-model trước khi vòng lặp chạy.
2. **PII vào git:** case ứng viên kết xuất từ hội thoại THẬT rồi nhận vào
   `eval/*.jsonl` là PII đi vào repo vĩnh viễn. Điểm export BẮT BUỘC qua scrub
   (tinh thần ADR-010). Với 150 người thật, đây là mốc chạm ADR-011.
3. **Học ≠ nới rào:** hệ tự tối ưu theo "mượt hơn" sẽ tự bịa nhiều hơn. Mọi
   thay đổi prompt/docstring phải qua so ghép cặp trên bộ chấm, gate **0% bịa
   thật** (thước mới `2d9a709`). Tiền lệ đúng: QA/QC đã từ chối nới
   `multiple_matches` — giữ nguyên tắc đó thành luật của đợt này.

## 2. Ba giai đoạn — thứ tự bắt buộc

### Phase 0 — Quản trị (làm NGAY, không cần đợi demo xong)
Bước 1 đụng `contracts/resolution-state-machine.yaml` (transition `rejected`
thêm trường + taxonomy lý do) → quy trình 7 bước CLAUDE.md §3:
- Coder soạn **dự thảo ADR** ("Thu nhãn phán đoán chuyên gia tại luồng reject")
  + diff contract đề xuất. Taxonomy lý do đề xuất (enum, chốt với PO):
  `sai_so_lieu · sai_phan_loai · thieu_can_cu · sai_chinh_sach · khac`
  (+ ghi chú tự do TÙY CHỌN — phải qua scrub PII, security rà).
- **DỪNG chờ PO thật duyệt** → rồi mới `check_contracts.py --update`, bump
  `CONTRACT_VERSION`, code.
- Gộp luôn ADR-018 (nguyên tắc giao tin live-chat — nợ từ 13/08) vào đợt ADR này.

### Phase 1 — Bắt tín hiệu (tuần này)
| Vai | Việc |
|---|---|
| Coder | Migration `reject_reason/rejected_by/rejected_at` + enum · API + UI sếp chọn lý do khi reject · **vá QA-02** (hitl_status chuyển đúng sau approve/reject) · trả `approved_by/approved_at/rejected_*` trong API ticket (đóng luôn M-02) |
| Tester | Viết test TỪ CONTRACT MỚI (không đọc src): reject ghi đủ 3 trường · reject thiếu lý do bị chặn · hitl_status chuyển đúng cả 2 nhánh · API ticket trả đủ trường audit |
| Security | Rà thiết kế: ghi chú tự do có qua scrub chưa · xác nhận reject vẫn không cần OTP (đúng contract — không phải hành động tài chính) · trường mới không lộ qua route của customer |

### Phase 2 — Vòng lặp bán tự động (sau Phase 1)
| Vai | Việc |
|---|---|
| Coder | Exporter: resolution bị reject + phiên CSAT ≤2 → file ỨNG VIÊN (`eval/candidates/*.jsonl`, qua scrub PII tại điểm export) · nối CSAT vào `/reports/summary` (US-018) |
| Tester | Quy trình duyệt ứng viên → golden_set: format case, tiêu chí nhận/loại, nhật ký duyệt. NGƯỜI DUYỆT LÀ CỔNG — không có đường tự động vào bộ eval |
| Security | Threat model poisoning (hội thoại dàn dựng, CSAT bombing) → checklist duyệt ứng viên cho tester · kiểm scrub tại điểm export bằng test đối kháng |

### Phase 3 — Tối ưu prompt CÓ ĐO (chỉ mở khi 2 điều kiện xanh)
Điều kiện: (a) tester phân loại xong **29/40 vi phạm checks** (đang treo —
không có thước tin được thì không đo được cải tiến), (b) Phase 1 merge xong.
- Coder: cắt token mục 4b (schema 1.945 + prompt 4.587 token) — so ghép cặp
  cùng bộ 40 case, gate **0% bịa thật**, latency không tăng.
- Tester: chạy so ghép cặp, báo số; thử nghiệm few-shot từ case ĐÃ DUYỆT ở
  Phase 2 (nếu tới kịp) — cũng qua cùng cổng đo.

## 3. Kỷ luật nhánh
- Mọi commit của đợt này vào `dev/learning-loop`. `main` chỉ nhận hotfix demo.
- Sau demo tối 14/08: rebase `dev/learning-loop` lên main mới nhất rồi làm tiếp.
- Ba vai commit chung 1 nhánh: kéo (`git pull --rebase`) trước mỗi phiên; ai
  đổi vùng nào chỉ commit vùng đó (coder src/, tester tests+eval, security docs).

## 4. Hai lằn ranh KHÔNG vượt (ghi để không phiên nào "tối ưu" ngược)
1. **KHÔNG fine-tuning trên dữ liệu khách** — chạm mốc kích hoạt ADR-011
   (Mẫu 06 + ZDR + sổ ICT). Học = curate case + sửa prompt có đo, không hơn.
2. **Ràng buộc cứng 3 không đổi lấy sự trôi chảy** — cấm nới
   `multiple_matches`/hành vi hỏi-lại; mọi thay đổi prompt qua gate 0% bịa.

## 5. Chờ PO thật quyết (trước khi Phase 1 code)
1. Duyệt ADR + diff contract của Phase 0 (coder sẽ trình).
2. Chốt taxonomy lý do reject (5 giá trị đề xuất ở trên).
3. Ghi chú tự do khi reject: cho phép (kèm scrub) hay chỉ enum? — security sẽ
   có khuyến nghị, PO chốt.
