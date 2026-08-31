# Kiểm kê dữ liệu RỜI BIÊN GIỚI — vật liệu cho hồ sơ ĐGTĐ (NĐ 13/2023 Đ.25)

> 🔴 **NIÊM 30/08/2026 — NĐ 13/2023 đã bị THAY THẾ từ 01/01/2026** bởi Luật 91/2025/QH15 +
> NĐ 356/2025/NĐ-CP. Vật liệu KỸ THUẬT dưới đây (kiểm kê luồng dữ liệu) vẫn dùng được, nhưng
> **số điều ("Đ.25") KHÔNG còn đúng** — phải đối chiếu số điều tương đương trong văn bản mới trước
> khi dùng làm căn cứ cho hồ sơ DPIA CHÍNH THỨC. Chi tiết:
> `docs/security/2026-08-30-niem-luat-91-2025-thay-nd-13-2023.md`.
>
> Vai: **security** · 2026-08-17 · PO-agent đang trình PO thật câu *"hồ sơ đánh
> giá tác động chuyển dữ liệu ra nước ngoài đã có chưa?"*
>
> Tôi đã hỏi câu đó **hai lần** ở dạng **có/không**. Đó là câu hỏi sai dạng —
> nó trả lời được bằng trí nhớ. Đây là bản đổi nó thành **thứ đo được**: hồ sơ
> Đ.25 đòi liệt kê **loại dữ liệu · bên nhận · nơi nhận · biện pháp bảo vệ**, và
> **phần đó chỉ đo được từ mã**. Người có thẩm quyền pháp lý điền phần còn lại;
> phần dưới đây họ **không tự dựng được**.
>
> ⚠️ **Không phải tư vấn pháp lý.** Đây là **kiểm kê kỹ thuật**, mọi dòng đều
> [ĐO] trên mã/tài liệu nhà cung cấp, ngày 17/08.

## §1. BÊN NHẬN — **HAI**, ở **HAI** tài phán. Không phải một.

| | Đường | Đích | Đo ở |
|---|---|---|---|
| **A** | chat (agent trả lời khách) | **Alibaba Cloud Model Studio** | `graph.py:258-261` ← `LLM_BASE_URL` |
| **B** | embedding (nhúng tài liệu **và truy vấn**) | **OpenAI** | `store.py:44-49` ← `EMBEDDING_BASE_URL` mặc định `None` |
| **C** | trọng tài chấm điểm (eval) | **OpenAI** | `eval/_llm_judge.py:59`, khoá ghim literal |
| **D** | kẻ tấn công giả lập (eval) | **OpenAI** | `eval/_harness.py:108,160` |

🔴 **Đổi sang Qwen là phép THÊM, không phải phép THAY.** Hồ sơ **phải liệt kê
cả hai bên nhận**.

### Nơi nhận — câu trả lời KHÔNG phải "Singapore"

Tài liệu chính thức Alibaba (đường A):
- `dashscope-intl.aliyuncs.com` ↔ **Singapore** (`ap-southeast-1`);
- phạm vi triển khai: *"International (**global nodes excluding the Chinese
  mainland**)"*;
- **lưu**: *"Your static data always remains in the selected region"*;
- **xử lý**: *"The region forwards the request to an **inference node within the
  service deployment scope**"*.

⟹ **Lưu trữ tại Singapore; XỬ LÝ tại các node toàn cầu ngoài Trung Quốc đại
lục.** Hồ sơ phải ghi đúng cả hai vế — vế thứ hai chính là vế Đ.25 hỏi.

## §2. LOẠI DỮ LIỆU thực sự rời hạ tầng — [ĐO] trên mã

| Loại | Có rời không | Cơ chế | Đường |
|---|---|---|---|
| **văn bản khách gõ** (mô tả khiếu nại · tin chat) | 🔴 **RỜI, NGUYÊN VĂN** | **không lớp che nào** | A |
| **truy vấn RAG dẫn xuất từ lời khách** | 🔴 **RỜI** | `store.search(query)` nhúng chuỗi do agent soạn từ lời khách | **B — sang OpenAI** |
| họ tên · SĐT · số TK · `user_id` · `wallet_id` trong kết quả tool | ✅ **đã che** | `_scrub_pii_cho_llm` che **theo TÊN KHOÁ** (`customer_tools.py:477`) | A |
| số tiền · mã GD · thời điểm · trạng thái | rời, **có chủ đích** | agent cần để suy luận + trích dẫn (ràng buộc cứng 3) | A |
| nội dung tài liệu chính sách (chunk) | rời | kho RAG của đối tác | A · B |
| họ tên khách trong system prompt | ✅ **ĐÃ GỠ** | `build_system_prompt` đóng cứng `"quý khách"` (ADR-010) | — |

### 🔴 Phần nặng nhất — và nó KHÔNG che được

**Văn bản khách gõ rời hạ tầng nguyên văn**, và **không thể che**: agent cần
**chính cái nghĩa** mà việc che phá đi. **Đã đo, không phải suy đoán** —
**S-01: `scrub_pii` chặn nhầm 40%** trên văn bản nghiệp vụ tiếng Việt.

⟹ Che văn bản khách = **đổi một rủi ro tuân thủ lấy một sản phẩm hỏng**. Hồ sơ
phải ghi đây là **quyết định thiết kế có ý thức**, không phải một thiếu sót.

### 🔴 Và nó chứa dữ liệu của NGƯỜI THỨ BA chưa từng đồng ý

Ca dùng **điển hình nhất** của sản phẩm: *"em chuyển nhầm cho anh X, sđt
09…"* ⟹ dữ liệu cá nhân của một người **chưa từng vào quan hệ với ví**, **chưa
ký đồng ý nào**, đang rời biên giới.

**Đây là câu hỏi nặng nhất trong toàn bộ hồ sơ**, và nó **không đổi theo nhà
cung cấp** — nó đã đúng với OpenAI từ trước.

## §3. BIỆN PHÁP BẢO VỆ đang có — ghi được vào hồ sơ

| Biện pháp | Trạng thái | Nguồn |
|---|---|---|
| che họ tên/SĐT/STK trong **kết quả tool** trước khi vào LLM | ✅ đang chạy | `_scrub_pii_cho_llm`, ADR-010, OWASP LLM02:2025 |
| **không** đưa họ tên khách vào system prompt | ✅ đã gỡ 13/08 | `prompt.py::build_system_prompt` |
| mã hoá at-rest cho lời khai/transcript | ✅ | `EncryptedText` (`messages.content`, `PolicyChunk.text`) |
| khoá của nhà cung cấp này **không** rơi sang nhà cung cấp khác | ✅ đã vá hôm nay | `_khoa_cho_nha_cung_cap` (`config.py:173`) |
| mã hoá đường truyền + chứng nhận bên nhận | AES-256 · **SOC 2** *(Alibaba công bố)* | tài liệu nhà cung cấp |
| cam kết **không dùng dữ liệu để huấn luyện** | ✅ có, **không** khác nhau theo bậc free/trả phí | tài liệu Alibaba — ⚠️ **mức TRANG TÀI LIỆU, chưa mức HỢP ĐỒNG** |

## §4. Ba khoảng trống phải ghi vào hồ sơ, không được bỏ qua

1. 🔴 **Văn bản khách gõ không che được** (§2) — kèm dữ liệu bên thứ ba.
2. 🔴 **Bản ghi phía nhà cung cấp ta không liệt kê được.** Alibaba có tính năng
   **Model monitoring** ghi *"the input, output, and latency for **each** model
   call"*, giữ **30 ngày**; theo tài liệu, phần ghi **nội dung** hiện *"limited
   to some models in the **China (Beijing)** region"* ⟹ **hôm nay Singapore
   chưa có bề mặt đó**, nhưng nó **bật bằng một nút trên console**, bởi bất kỳ
   ai có tài khoản, và **không diff nào của ta nhìn thấy**.
   ⟹ **Việc phải làm:** kiểm công tắc đó trên console **và ghi ngày kiểm**.
3. ⚠️ **Phía OpenAI: chưa kiểm** tài khoản có bật lưu nội dung yêu cầu
   (stored completions / org logging) hay không. Nếu **có**, phạm vi hồ sơ rộng
   hơn hẳn — và nó cũng là ô quyết định hạng của sự cố lộ khoá sáng nay.

## §5. Điều quan trọng nhất về THỜI ĐIỂM — và vì sao nó không phải việc của Qwen

**Nghĩa vụ Đ.25 KHÔNG do Qwen tạo ra.** Hệ thống **đã** gửi văn bản khách ra
nước ngoài từ khi còn dùng `gpt-4o-mini` (Hoa Kỳ). Việc đổi nhà cung cấp
**không** làm nghĩa vụ nặng hay nhẹ hơn — nó chỉ **thêm một bên nhận**.

⟹ **Khoảng trống này đang tồn tại, không phải rủi ro mới**, và **nó không tự
biến mất nếu quyết định là "giữ OpenAI"**. Cả ngày hôm nay đội bận với thứ
**đổi được**; đây là thứ **vốn đã sai từ trước** và vì thế không ai chạm tới.

**Mốc kích hoạt đã chốt là "dữ liệu thật ĐẦU TIÊN"** — và **một buổi demo mentor
gõ số điện thoại thật là đã tính**.

## §6. Điều tôi KHÔNG kết luận

- **Không** biết hồ sơ đã có hay chưa — đó vẫn là câu cho PO thật. Tài liệu này
  **không** thay hồ sơ; nó là **vật liệu §2/§3/§4** mà người làm hồ sơ không tự
  dựng được.
- **Không** phán quyết nhà cung cấp nào an toàn hơn. Đ.25 áp **như nhau** cho
  mọi chuyển ra nước ngoài.
- **Không** đọc *Product Terms of Service* của Alibaba (mức hợp đồng) — mới ở
  mức trang tài liệu.
- **Không** đánh giá chế độ pháp lý của nơi nhận — thuộc người có thẩm quyền
  pháp lý, và nó là **một mục bắt buộc** của hồ sơ.
