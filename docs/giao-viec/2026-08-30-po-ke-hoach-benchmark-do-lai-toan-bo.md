# KẾ HOẠCH — ĐO LẠI BENCHMARK TOÀN BỘ, LẤY MỘT CON SỐ CHUẨN

> **Từ:** phiên PO · **Cho:** Lead (p-226-61) · **Ngày:** 30/08/2026
> **Lệnh PO thật:** *"đo benchmark toàn bộ từ đầu với tiêu chuẩn hiện tại, chạy tất cả một
> lần để có một con số chuẩn nhất"* + trục thứ sáu làm ở mức **thiết kế + dựng thật**.

---

## 0. Trước hết — ĐÍNH CHÍNH một con số đang lưu hành sai

Báo cáo benchmark mà PO thật đang cầm (bản v0.4, 16/08) nói: *"50,8% câu khách bị bộ lọc bóp
méo trước khi tới model"*. **Sai.** Tôi chạy thật cổng đo trên HEAD hôm nay:

```
$ python3 eval/do_bop_meo_pii.py
Corpus: 124 câu (eval/golden_set.jsonl, utterances trải phẳng)
Bị chèn ÍT NHẤT 1 nhãn [XXX]: 6/124 (4.8%)
Ngưỡng PRD §17: ≤ 6%
✅ ĐẠT PRD §17 (4.8% ≤ 6%)
```

Repo đã tự niêm con số đó từ 10 ngày trước — `docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md:563`:
*"bóp méo tiếng Việt 50,8% → 5,6% ⛔ **NIÊM 20/08: cả hai số đứng trên chữ ký ĐÃ CHẾT**"*.
Thêm nữa: **cả 6 ca "bóp méo" đều là che số điện thoại ĐÚNG CHỨC NĂNG** (`0766000097` → `[PHONE]`).

⚠️ **Giới hạn phép đo của tôi, đừng làm tròn lên:** máy tôi báo
`pii_presidio_unavailable_fallback_regex_only` — chỉ đo nhánh regex. Theo quyết định 19/08 thì
đường `model_input` **vốn** là regex-only nên đúng phạm vi, nhưng **QA/QC phải chạy lại trong
container thật** trước khi ai trích số 4,8% ra ngoài.

**Hai đính chính kèm theo:**
- `--che-do moc` **KHÔNG chết** — `benchmark.py:388` ghi *"Bug đã vá 19/08"*.
- Gói 30 nhãn **đã dựng xong và đang chờ người thật** — `eval/goi_30_nhan_NGUOI.md`.

🔴 **Điều KHÔNG bị đính chính — giữ nguyên, vì nó vẫn đúng:** bộ chấm **không có trục nào đo
"agent có hiểu đúng câu khách không"**. Cơ chế: agent không hiểu → hỏi lại → **an toàn** (30/30)
**và không bịa** (25/25) → điểm tuyệt đối ở mọi trục đang có. Lập luận này đứng vững **độc lập**
với con số 50,8% đã hỏng. Đừng vứt cả phát hiện vì bằng chứng kèm theo sai.

---

## 1. 🔴 BƯỚC 0 — ĐO HẠN NGẠCH TRƯỚC KHI CHẠY. ĐÂY LÀ CHẶN CỨNG.

**Vì sao đây là bước đầu tiên, không phải bước cuối:** mục tiêu của PO là *một con số chuẩn*.
Con số ấy chỉ chuẩn nếu **cả lượt chạy dùng đúng MỘT model**. Mà:

```
[ĐO, eval/UOC-TINH-TOKEN-v5.md]  một lượt v5 đầy đủ  =  786K – 822K token / model Qwen
[ĐO 19/08]  qwen3.7-plus (model chính)   CÒN  48.537   ← không đủ, thiếu ~16 lần
            deepseek-v4-pro-0813          còn 777.692   ← KHÔNG ĐỦ cho lượt 800K
            deepseek-v3.2                 còn 944.084   ← đủ, nhưng biên mỏng
            deepseek-v4-flash-0731        còn 963.012   ← đủ, biên mỏng
[ĐO 30/08]  logs/usage.jsonl dừng ở 25/08, các bản ghi cuối có token = null
            ⟹ HẠN NGẠCH THẬT HÔM NAY: KHÔNG BIẾT
```

**Cơ chế hỏng nếu bỏ qua bước này:** model cạn giữa lượt → **bể xoay tự kích hoạt** (ADR-043,
đúng thiết kế) → nửa đầu mẫu đo model A, nửa sau model B → **con số ra là số của một vật lai,
không phải của sản phẩm nào cả**. Chạy lại từ đầu thì mất thêm ~800K nữa.

**Việc của Lead — giao Coder, làm TRƯỚC mọi thứ khác:**
1. Đo hạn ngạch còn lại **thật** của từng model trong bể (đọc từ nhà cung cấp, không suy từ log).
2. Chọn model có **≥ 900K biên còn lại**. Không model nào đủ → **dừng, báo PO thật**, đừng chạy.
3. **Ghim model đó, TẮT bể xoay trong suốt lượt đo.** Bể xoay là tính năng sản phẩm — nó phải
   tắt khi đo, đúng như ta không đo tốc độ xe trong lúc hộp số tự sang số.
4. Ghi **tên model + mốc ngày** vào đầu file kết quả. Số không có tên model là số vô nghĩa.

---

## 2. 🔴 BƯỚC 0b — HELDOUT: ĐỪNG ĐỐT NÓ TRONG LƯỢT NÀY

`CLAUDE.md:117` và `docs/STATE.md:238`:
> `eval/heldout_set.jsonl` — **NIÊM PHONG, chỉ chạy MỘT LẦN, sau khi hiệu chuẩn trọng tài.**

Chữ *"đo toàn bộ, chạy tất cả một lần"* rất dễ bị đọc thành *"chạy luôn cả heldout"*. **Không.**
Heldout chỉ có giá trị đúng **một lần trong đời dự án**, và nó phải được tiêu **sau khi** trọng
tài đã hiệu chuẩn bằng 30 nhãn người. Chạy trước ⟹ tiêu tài sản đo quý nhất để lấy một con số
do trọng tài **chưa hiệu chuẩn** chấm. Không lấy lại được.

⟹ **Lượt này chạy golden (120) + đối kháng (66) + trục 6. KHÔNG chạm heldout.**
Heldout để dành cho lượt nghiệm thu cuối, sau bước 2.

---

## 3. BƯỚC 1 — 30 nhãn PO: việc duy nhất đội không làm thay được

`eval/goi_30_nhan_NGUOI.md` **đã sẵn sàng**: 30 ca, chấm mù (thứ tự đã xáo, không chứa phán
quyết của máy), mỗi ca ba ô — `ket_luan` (DAT/TRUOT/KHONG_CHAC) · `ly_do` · `co_bia_khong`.

**Nó mở khoá hai thứ cùng lúc:**
- Trục Trải nghiệm **15 điểm** đang bỏ trống ⟹ mẫu số về **100**, thay vì 85.
- Hiệu chuẩn trọng tài ⟹ **điều kiện tiên quyết** để sau này được phép chạy heldout.

**Lead:** đưa gói này cho PO thật **ngay hôm nay**, đừng đợi các bước kỹ thuật xong. Nó chạy
song song, không phụ thuộc gì. Nhắc nguyên tắc chấm mù: **đừng tra kết quả máy trước khi chấm
xong** — thấy trước là mọi nhãn bị neo.

---

## 4. BƯỚC 2 — Trục 6 "Hiểu đúng yêu cầu khách": thiết kế + DỰNG THẬT

PO thật đã chốt mức **dựng thật**, không dừng ở đặc tả.

**Đặc tả tối thiểu — Lead giao QA/QC, KHÔNG giao Coder** *(tester cố ý không đọc `src/`, để trục
này đo từ đặc tả chứ không phản chiếu logic đang có — `CLAUDE.md §4`)*:

- Đo bằng **hành trình nhiều lượt**, không phải một câu hỏi lẻ. Điểm mù chỉ hiện ra qua nhiều lượt.
- 🔴 **Bắt buộc có ca đối chứng DƯƠNG:** ca mà agent **hiểu sai** phải bị chấm **ĐỎ**. Thiếu vế
  này thì trục 6 lại là một trục nữa chỉ biết xanh — đúng căn bệnh nó sinh ra để chữa.
- Ca mẫu bắt buộc có: khách hỏi lại cùng một việc bằng cách khác · khách gõ không dấu, khẩu ngữ,
  không có mã giao dịch · **ca thật PO đã bắt được bằng tay**: agent hỏi đi hỏi lại mã giao dịch
  thứ hai.
- Phân biệt rõ hai thứ mà bộ chấm hiện tại gộp làm một: **"hỏi lại vì thiếu thông tin thật"**
  (đúng, đáng điểm) và **"hỏi lại vì không hiểu"** (sai, phải trừ điểm).

**Trọng số — tôi đề xuất, có thể đảo:** thêm trục 6 thì mẫu số không còn là 100. Đề xuất rút
mỗi trục hiện có một phần để trục 6 lấy **15 điểm**, giữ tổng 100. Lead trình phương án cụ thể
kèm số, **PO thật chốt** — đây là đổi thước đo, không phải đổi code.

---

## 5. BƯỚC 3 — Chạy đủ trục, một lượt

Chỉ chạy sau khi bước 0 (hạn ngạch + ghim model) đã xong. Đầu ra phải mang **đủ nhãn để truy
lại**: tên model + mốc ngày · mã commit · băm kho RAG · số ca từng bộ · ngày chạy.

Nhắc lại con số nền để so: bản 16/08 là **74,57/85 = 87,7%** — An toàn 30/30 · Đúng dữ liệu
25/25 · **Truy hồi RAG 9,57/20** · Trải nghiệm chưa đo · Hiệu năng 10/10.

🔴 **RAG 47,9% cũng đã hết hạn** — `docs/giao-viec/2026-08-24-luong-chatbot-1A-1B.md:78` ghi:
*"47,9% [ĐO 17-20/08] **HẾT HẠN NGAY.** Phải đo lại + niêm số cũ"*. Đừng mang số này vào báo
cáo mới như số hiện hành.

---

## 6. Việc CHỈ PO thật quyết — Lead không quyết, tôi cũng không

| # | Việc | Vì sao |
|---|---|---|
| 1 | Chốt trọng số sau khi thêm trục 6 | Đổi thước đo — mọi số cũ/mới hết so được với nhau |
| 2 | Cho phép tiêu hạn ngạch ~800K cho một lượt đo | Tiền thật, và có thể làm cạn model đang phục vụ |
| 3 | Thời điểm đốt heldout | Tài sản đo dùng được đúng một lần |
| 4 | 30 nhãn | Không ai làm thay được |

---

## 7. Nhịp báo cáo & ba thứ tôi sẽ kiểm

Báo cáo **theo mốc**, không theo giờ: mỗi khi một bước ở §1–§5 đóng, hoặc gặp một mục ở §6.

Ba thứ tôi trả lại báo cáo nếu thiếu:
1. **Phân biệt ĐỌC và CHẠY.** "Sạch" từ đọc diff ≠ "sạch" từ chạy thật.
2. **Cổng phải ăn cả hai đầu vào** — chứng minh được nó ĐỎ khi lỗi còn đó, không chỉ XANH khi
   lỗi đã hết. Áp thẳng cho trục 6.
3. **Phạm vi phép đo phải khớp phạm vi kết luận.** Trình bằng **cơ chế**, đừng trình bằng
   **số đếm**.

**Và một điều tôi muốn Lead chủ động:** nếu một mục trong kế hoạch này sai — sai thứ tự, sai giả
định, hoặc đã lỗi thời so với phép đo thật — **nói ngay và nói bằng phép đo**, đừng thi hành cho
xong. Bản kế hoạch này vừa sửa một con số sai lệch 10 lần mà cả đội đang lưu hành; thứ tự tiếp
theo có thể cũng sai như vậy.
