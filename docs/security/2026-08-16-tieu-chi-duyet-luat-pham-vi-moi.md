# Tiêu chí duyệt — văn bản luật phạm vi mới (F-31 + F-32)

> Vai: **security/tuân thủ** · 2026-08-16 · viết **TRƯỚC** khi coder soạn, để
> lúc duyệt không phải tuỳ hứng. PO giao tôi rà văn bản luật trước khi land.
> Nền: ý kiến tuân thủ ToS (`a65e9fc`) · chẩn đoán tầng-chặn (MISINFO-002,
> `prompt.py:52-60`) · ràng buộc thiết kế PO đã chốt.

## Bảy tiêu chí. Thiếu bất kỳ cái nào ⟹ tôi không duyệt.

### 1. Trục phân loại phải viết bằng chữ **"về ví NÀY"**, không phải **"pháp lý"**

Luật hiện tại phân theo *pháp lý / không pháp lý*, rào bằng cụm phụ *"không
liên quan giao dịch ví"*. Đó là lý do câu về **Điều 19** rơi vào vùng nhập
nhằng: nó **vừa** mang màu pháp lý **vừa** đúng là về ví này.

Văn bản mới phải đặt **"có phải việc của ví/giao dịch của chính khách này
không"** làm câu hỏi **thứ nhất**, và tính chất pháp lý **không** được là tiêu
chí loại trừ.

### 2. **Đường thứ ba phải được viết ra thành nhánh riêng**, không để suy ra

Ba nhánh phải **hiện diện tách bạch** trong văn bản:

| Tình huống | Hành vi |
|---|---|
| ngoài ví (thừa kế · ly hôn · đầu tư · chứng khoán) | MISINFO-002 |
| **về ví, TRA ĐƯỢC** | **trích/dẫn đúng nội dung tra được** |
| **về ví, KHÔNG tra được** | **"chưa tra được" + chuyển người thật** |

Thiếu nhánh giữa/cuối thì luật lại ép mọi thứ về nhị phân *từ chối / tự trả
lời* — đúng cái đang gây F-31 và F-32.

### 3. 🔴 **"Ngoài phạm vi" và "không tra được" phải là HAI trạng thái khác nhau**

Hiện tại hai thứ này **sinh ra cùng một hành vi từ chối**, và đó là lý do
RAG-38/RAG-40 *trông giống* từ chối phạm vi.

Chúng khác nhau ở **việc kế tiếp**:

- *ngoài phạm vi* → **không** escalate (không ai trong đội trả lời được câu về
  thừa kế) → hướng khách sang kênh khác
- *không tra được* → **PHẢI** escalate (người thật **có** trả lời được câu về
  Điều 19) → chuyển người thật

⟹ Gộp chúng làm một là **đánh mất một escalate lẽ ra phải xảy ra**. Với câu về
điều khoản, đó là mất đúng cái phao mà toàn bộ lập luận "an toàn tuân thủ" của
tôi dựa vào.

### 4. Ca ranh giới phải liệt kê **ĐỦ HAI CHIỀU**

Văn bản phải có **cả** danh sách *phải từ chối* **và** danh sách *cấm từ chối*,
đặt cạnh nhau.

Một luật chỉ phát biểu từ một phía **luôn bắn quá tay về phía đó** — bài học
lặp bốn lần trong dự án này (F-22 → F-24 → F-25 → S-01). Tối thiểu phía
*cấm-từ-chối*: **Điều 19** (tra soát/khiếu nại) · **Điều 8** (nghi gian lận,
khoá ví — chạm **ràng buộc cứng 5**) · **Điều 13/15** (bồi hoàn, giới hạn trách
nhiệm) · phí · hạn mức.

### 5. **CẤM định nghĩa luật bằng ví dụ**

Luật hiện tại dạy bằng ca cụ thể (*"tôi già rồi không rành công nghệ…"*). Ca đó
được thêm để vá một triệu chứng — và **8 ca ToS chứng minh nó không tổng
quát hoá**: sửa được ca người-lớn-tuổi, không sửa được ca điều-khoản.

Văn bản mới phải phát biểu **tiêu chí**; ví dụ chỉ để **minh hoạ tiêu chí đã
phát biểu**, không được **thay** nó.

### 6. **CẤM danh sách từ khoá pháp lý**

Bất kỳ dạng *"nếu câu chứa `thừa kế|ly hôn|kiện tụng|…` thì từ chối"* → **bác
ngay**. Đây đúng lớp lỗi **danh-sách-viết-tay-luôn-thiếu-chữ-người-ta-sắp-gõ**,
đã tốn của đội **năm vòng** ở F-28 (`ignore` → `disregard` → `disregarding` →
mỏ-neo-ma → `\b`). Không lặp lại nó ở tầng prompt.

### 7. Phải nói rõ **cái gì KHÔNG đổi**

- **MISINFO-002 giữ NGUYÊN VĂN** cho ca thật sự ngoài ví. Prompt hiện tại yêu
  cầu *"trả lời ĐÚNG NGUYÊN VĂN mẫu câu sau, không thêm bớt"* — đó là **câu chữ
  tuân thủ**, không phải văn phong. Nếu bản vá **sửa chính câu đó** thì là một
  **quyết định riêng**, phải nêu tách ra, không lẫn vào việc sửa trục phân loại.
- **Không nới ràng buộc 9 / CTRL-002.** Lằn ranh *"sửa RAG không nới prompt"*
  vẫn đứng: đường ra cho câu tra-không-được là **escalate**, **không** phải cho
  agent tự suy rộng hơn.

## Cách tôi sẽ duyệt

Đọc văn bản **như một người sẽ tuân theo nó**, không như người viết nó. Ba câu
tôi hỏi mỗi đoạn:

1. Một câu hỏi về **Điều 19** đọc luật này ra hành vi nào? (phải là: tra → trích, hoặc không tra được → escalate)
2. Một câu hỏi về **thừa kế** ra hành vi nào? (phải là: MISINFO-002)
3. Có đoạn nào mà **cả hai** câu trên đọc ra **cùng** một hành vi không? (nếu có ⟹ trục vẫn sai)

## Sau khi land

Probe theo nếp, **cấm chạy lẻ** (Luật 2): 8 ca ToS (hiệu quả) **cùng** bộ ca
ngoài-ví (đối chứng chống-nới-quá). Và mang theo điều kiện §D: **ca mồi-neo
phải neo cả chiều agent-viết-lại-truy-vấn**, nếu không một ca âm-bản-gần sẽ
**pass giả** vì agent viết lại truy vấn thành thứ khác hẳn câu thước hỏi.
