# GĐ1 — CHATBOT PHẢI CHẠY. Chặn mọi việc khác.

> PO duyệt 18/08: cả 3 giai đoạn. **GĐ1 là điều kiện của GĐ2 và GĐ3.**
> Viết cho người đọc **NGUỘI**. Luật Q trước tiên: `git rev-parse --abbrev-ref HEAD && git log --oneline -1`

## 0. Trạng thái đã biết — đừng đo lại

```
[ĐO] qwen3.7-max    HTTP 403  "The free quota has been exhausted"   ← ĐÃ CẠN
[ĐO] qwen3.7-plus   HTTP 200  9,9s  549 token  cho một câu chào
[ĐO] qwen-plus      HTTP 200  0,7s   14 token  cho cùng câu
[ĐO] .env:122 đã đổi sang qwen3.7-plus · container fin05-backend-1 đã dựng lại
     ENV THẬT trong container = qwen3.7-plus · /health (cổng 8010) = 200
```

🔴 **NHƯNG:** phép đo trên chỉ chứng minh **API trả lời**. Nó **KHÔNG** chứng minh **chatbot chạy**.
Hai câu khác nhau — đường agent còn tool call, RAG, guardrail, checkpoint. **Chưa ai đi hết đường đó.**
*(PO-agent đã suýt báo cáo nhầm hai câu này làm một; ghi ra để không ai lặp lại.)*

---

## 1.1 · TESTER — nghiệm thu ĐẦU-CUỐI qua UI thật

**Đây là việc duy nhất chứng minh chatbot chạy.** Không suy từ log, không suy từ API 200.

```
đăng nhập bằng tài khoản khách demo
→ gõ một câu hỏi về MỘT giao dịch CÓ THẬT trong CSDL
→ agent phải trả lời KÈM số liệu tra được
→ đối chiếu số trên màn hình với số trong `transactions`  ← phải LÀ MỘT
```

**Ba trạng thái, không phải hai** — báo nguyên trạng, đừng gộp:
```
✅ agent trả lời ĐÚNG, số khớp CSDL
🟡 agent trả lời nhưng nói "không tra được"   ← ĐÚNG HÀNH VI nếu thật sự không tra được,
                                                 SAI nếu dữ liệu có mà nó không thấy
❌ "Có lỗi khi kết nối trợ lý"                ← dán log backend nguyên văn kèm theo
```

⚠️ **Cấm kết luận "chạy được" từ một lượt xanh.** Chạy **≥3 lượt**, ≥1 lượt hỏi thứ **không tồn tại**
để xem agent có bịa không (RÀNG BUỘC CỨNG 3).

## 1.2 · TESTER — đo ĐỘ TRỄ THẬT trên đường agent

`qwen3.7-plus` là model có suy luận: **9,9 giây / 549 token cho một câu chào**. Đường agent có tool
call sẽ lâu hơn — **bao nhiêu thì chưa ai biết**.

```
đo: thời gian từ lúc gửi tới lúc chữ đầu tiên hiện ra, và tới lúc trả lời xong
    ≥5 lượt, có cả lượt CÓ tool call và lượt KHÔNG
báo: trung vị + lượt chậm nhất (đừng báo trung bình — một lượt 40s bị trung bình nuốt mất)
```

🔴 **Phép đo này CÓ THỂ LẬT quyết định model.** Nếu đường agent quá chậm để người thật chịu được,
`qwen-plus` (0,7s) là đường lùi rẻ. **Đừng tự đổi model — báo số, PO quyết.**

⚠️ Mỗi lượt đo **tốn tiền thật**. Ngân sách A3 còn hạn. Đo đủ 5 lượt rồi dừng, đừng lặp cho chắc.

---

## 1.3 · TECH-LEAD — vá NHÃN LỖI SAI

```
[ĐO] logs/usage.jsonl   "ly_do_fallback": "timeout"     ← ứng dụng ghi
[ĐO] API thật            HTTP 403 sau 0,4 giây           ← thực tế
```
**Không có gì timeout cả.** Ứng dụng dán nhãn sai một lỗi nó đọc được rõ ràng.

**Hậu quả trên production:** hết hạn ngạch sẽ hiện ra như *"hệ thống chậm"* — và **không ai đi nạp
tiền**. Đội mất hàng giờ truy một vấn đề hiệu năng không tồn tại.

⟹ Nhánh xử lý lỗi phải ghi **TRIỆU CHỨNG** (`http_403` · `quota_exhausted` · thân lỗi rút gọn), không
ghi **KẾT LUẬN** (`timeout`). Đây là **Luật H** đã có trong `docs/STATE.md` §7.
**Phân biệt tối thiểu:** `timeout` · `http_4xx` (kèm mã) · `http_5xx` · `loi_mang` · `khac`.

## 1.4 · TECH-LEAD — `HOTLINE_CSKH`

```
[ĐO] log khởi động: hotline_cskh_khong_bam_duoc
     gia_tri_tho: "1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)"
```
**PO sẽ gửi số thật sau.** ⟹ **GIỮ NGUYÊN cơ chế fail-loud hiện tại** — nó tự khạc lỗi kèm cách vá,
và chính nó đã cứu ta lần này. **Đừng thay bằng một số bịa cho hết đỏ.**

Việc của bạn bây giờ: **chỉ xác nhận** cơ chế sẽ nhận số mới bằng biến môi trường + `recreate`, và
**không có đường nào để placeholder lọt lên production im lặng**. Nếu có, bịt.

---

## 2 · Điều KHÔNG được làm

- 🚫 **Không đổi model** — báo số, PO quyết (1.2)
- 🚫 **Không sửa test cho xanh.** Cổng đỏ vì mã thì để đỏ
- 🚫 **Không `docker compose down -v`** · mọi lệnh compose **bắt buộc `-p`**
- 🚫 **Mọi lệnh `git` phải có pathspec** — cây dùng chung, đã 3 sự cố
- 🚫 **Không đụng production** `app.adaptivealgo.uk`

## 3 · Xong GĐ1 thì báo — GĐ2 (dữ liệu demo) mở khoá ngay sau đó
Kế hoạch GĐ2: `docs/giao-viec/2026-08-18-ke-hoach-du-lieu-demo.md`
