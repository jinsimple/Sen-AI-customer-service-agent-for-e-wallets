# Hồ sơ sự cố — 2 file nội bộ vào kho RAG đang phục vụ

> Vai: **security** · lập 2026-08-16 · đánh giá thiệt hại theo yêu cầu PO.
> Mọi mốc thời gian dưới đây là **UTC** (log Docker), giờ máy = **UTC+7**.

## 0. Kết luận đi trước

| | |
|---|---|
| **Thiệt hại tới KHÁCH** | **KHÔNG CÓ — 0 request hướng khách trong cả cửa sổ** |
| **Phơi nhiễm thực tế** | giới hạn ở `/policy-search` = endpoint **nhân viên**, vốn **cố ý** không qua bộ lọc |
| **Cửa sổ** | **19 phút 33 giây** (không phải "nhiều giờ") |
| **Trạng thái** | **ĐÃ ĐÓNG** — kho hiện chỉ còn 2 `.docx` hợp lệ |
| **Quy được ai tra không?** | **KHÔNG** — `/policy-search` không phát log có `user_id` |

## 1. ⚠️ Đính chính hai chi tiết trong mô tả ban đầu

**(a) "08:23 sáng nay" là giờ UTC, không phải giờ máy.** Hai `POST /policy-docs`
nằm ở `08:23:14.667Z` và `08:23:27.806Z` — tức **15:23 giờ máy**, khoảng **20
phút trước** lúc tôi điều tra, **không phải sáng nay**. Điều này quan trọng vì
nó quyết định log nào còn phủ được cửa sổ (log backend chỉ bắt đầu từ
`07:23:59Z`; nếu sự cố thật sự ở 08:23 giờ máy = `01:23Z` thì **đã không còn
log để đo**).

**(b) Cửa sổ là ~19,5 phút, không phải "nhiều giờ".** "15 giây" đúng là khoảng
cách giữa hai lần nạp, nhưng mốc đóng đo được là lúc kho được nạp lại sạch:

```
MoMo_FAQ_Giao_dich.docx  uploaded_at 2026-08-16 08:42:47.590  indexed  297 chunk
MoMo_ToS.docx            uploaded_at 2026-08-16 08:42:51.692  indexed   81 chunk
```

⟹ **cửa sổ = 08:23:14 → 08:42:47 = 19 phút 33 giây.** Kho hiện tại **chỉ có
đúng hai tài liệu trên** — hai file `.md` **không còn**.

## 2. Toàn bộ traffic TRONG cửa sổ (stack `fin05-*`)

```
258   POST /policy-search
 12   POST /auth/login
  2   POST /policy-docs        (chính hai lần nạp)
  2   GET  /policy-docs
 43   GET  /health
———   KHÔNG CÓ GÌ KHÁC
```

**Không một request hướng khách nào**: không `/chat`, không lượt agent, không
`/tickets`. ⟹ **con đường "số chưa kiểm chứng ra miệng agent" KHÔNG được đi
qua.** Đây là dữ kiện quan trọng nhất của hồ sơ.

**Stack thứ hai (`fin05ttl-*`) không bị ảnh hưởng** — kho riêng, chỉ chứa
`MoMo_ToS.pdf` + `MoMo_FAQ_Giao_dich.pdf` (nạp 14–15/08), và trong cửa sổ chỉ
có **39 lượt `GET /health`**, không traffic nào khác.

## 3. Vì sao phơi nhiễm giới hạn ở nhân viên

Toàn bộ 258 lượt là `/policy-search` — **endpoint của CSKH**. Theo thiết kế
(`_sanitize_policy_results`, và **Y5** trong `injection-surface-inventory.md`),
đường này **cố ý KHÔNG qua bộ lọc tier**: nhân viên **phải** thấy nguyên văn để
phát hiện tài liệu độc đã lỡ upload. Đường agent (`search_policy` tool) mới là
đường có lọc — và đường đó **không có lượt nào** trong cửa sổ.

⟹ Thứ đã xảy ra: **nhân viên có thể đã thấy nội dung nội bộ trên một endpoint
vốn thiết kế để hiện nội dung thô.** Thứ **không** xảy ra: khách nhận số chưa
kiểm chứng.

**Dữ kiện định lượng thêm** (không làm nhẹ sự cố, chỉ định lượng):
`business_rules.md` mang cột `verified=false` **ngay trong bảng** — ai trích
được nội dung đó thì trích **kèm cả cột đó**.

## 4. 🔴 Không quy được AI đã tra — và đây là lỗ hổng quan sát, không phải điểm mù của tôi

```
logger có mặt trong log backend:
  974  httpx2          111  presidio-analyzer     25  fin05.live_chat_ws
   20  fin05.tools.get_customer_history            1  fin05.auth
```

**Không có một logger nào cho `rag` / `policy`.** `/policy-search` chỉ để lại
**access log của uvicorn** — có IP + mã trạng thái, **không có `user_id`,
không có câu truy vấn, không có chunk trả về**.

⟹ **Câu hỏi "có lượt nào của user THẬT không" KHÔNG trả lời được từ log.**
Tôi ghi rõ là **đo-không-được**, không suy đoán.

**Bằng chứng gián tiếp tốt nhất tôi có:**

1. **Toàn bộ đến từ `172.19.0.6` = `fin05-frontend-1`** (proxy của giao diện
   web) + một phần từ `127.0.0.1` (gọi trong chính container).
2. **Nhịp là nhịp MÁY, không phải người gõ**: 66 lượt trong phút `08:24` · 70
   trong `08:26` · **71 trong `08:33`**. Người dùng thật không tra 70 câu/phút.
3. **Ba cụm trùng mạch việc nội bộ đang chạy**: tester tự khai quét ở 08:24 và
   08:26; cụm `08:33` trùng khít với commit `feat(rag): đòn 4` (`08:32Z`) của
   tech-lead. Các lượt lẻ 08:34–08:41 (≤14/phút) cũng nằm trong mạch đó.

⟹ **Không có dấu hiệu nào của lượt tra do người dùng thật**, nhưng đó là suy
luận từ **nhịp + trùng mốc**, **không phải** từ định danh. Nếu cần chắc chắn
hơn thì phải có log `user_id` — xem §6.

## 5. Đường nạp — tôi rút giả thuyết cũ

Giả thuyết trước của tôi (`scripts/kho_rag.py::_chon_nguon` liệt kê `data/raw/`)
**SAI**, và bằng chứng của tester bác nó dứt điểm: `kho_rag.py` nạp bằng
`ingest_document()` **trong tiến trình**, không đi qua HTTP, nên **không thể**
sinh ra 2 dòng `POST /policy-docs`. Đường thật là **API upload của
`partner_admin` — cửa hợp lệ**.

Bản vá siết `_chon_nguon` xuống `.docx/.pdf` **vẫn đúng chỗ**, nhưng cần ghi
đúng bản chất: nó **vá đường suýt-xảy-ra**, không phải đường đã-xảy-ra.

## 6. Đề nghị

1. **Log có cấu trúc cho `/policy-search` và `/policy-docs`** — `user_id` ·
   `doc_id`/`filename` khi nạp · số chunk trả về khi tra. Không có nó thì
   **mọi** đánh giá thiệt hại RAG về sau đều dừng ở "đo không được", đúng như
   lần này. Cùng họ với F-LOG và với AUTH5-03-không-có-log: **ta lại vừa mất
   khả năng trả lời một câu hỏi sự cố vì thiếu một dòng log.**
2. **Xuất xứ trên chunk** (đã được PO duyệt làm đề tài probe kế tiếp của tôi):
   sự cố này là ca dương tính cho nó — nạp qua **cửa hợp lệ** nên mọi biện pháp
   ở tầng nạp đều không chặn; chỉ cờ *nguồn-đã-duyệt* ở tầng serve mới phân
   biệt được "tài liệu đối tác đã duyệt" với "file ai đó lỡ upload".

## 7. Điều tôi KHÔNG kết luận

- **Không** khẳng định 258 lượt tra đều là nội bộ — chỉ khẳng định **không có
  dấu hiệu ngược lại**, và nêu rõ căn cứ là nhịp + trùng mốc.
- Mốc **đóng** cửa sổ suy từ `uploaded_at` của lượt nạp lại + trạng thái kho
  hiện tại, **không** từ một dòng log "đã gỡ" (việc gỡ không qua HTTP).
- Tôi đo **access log HTTP của hai stack**. Nếu có tiến trình nào truy vấn
  thẳng kho (không qua HTTP) thì nó **không xuất hiện** trong phép đo này.
