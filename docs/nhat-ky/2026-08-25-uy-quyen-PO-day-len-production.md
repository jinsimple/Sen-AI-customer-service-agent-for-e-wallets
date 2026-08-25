# UỶ QUYỀN CỦA PO THẬT — đẩy lên `main` → production

> Land vào repo vì **tin nhắn không tra được về sau**. Coder từ chối hành động theo
> lời chuyển tiếp và đòi *"dữ kiện, không cần lời chuyển tiếp"* — **đúng**, và đây là dữ kiện đó.

## Nguyên văn lệnh

**PO thật, 25/08/2026:**

> *"Sau khi lên kế hoạch thì song song đấy **báo devops build cho tôi để đẩy bản hiện tại lên
> main** — sau đó **cho lên product live** nhé."*

Nhận trực tiếp bởi phiên PO-agent `p-226-f0` *(trước là `p-226-b9`)*.

## 🔴 Nó ĐẢO một quyết định đã chốt

Trước đó PO thật đã quyết **KHÔNG push** `dev/learning-loop` *(quyết định ③)*. Lệnh trên **đảo
quyết định ấy**, và chỉ chính PO thật mới đảo được — không phải một phiên mới, không phải PO-agent.

## ⚠️ UỶ QUYỀN NÀY KHÔNG XOÁ ĐƯỢC CÁI GÌ

🔴 **Nó KHÔNG xoá được một finding P0 chưa vá.**

```
tests/test_api/test_live_chat_pii_gap.py   @pytest.mark.security_finding
live_chat.py::record_message lưu NGUYÊN VĂN số điện thoại / số tài khoản
khách gõ tay vào live-chat — KHÔNG qua scrub/mask nào.
(luồng AI đã có scrub_pii + masking.py; luồng live-chat thì CHƯA)
```

Cổng CI `security-findings-gate` **đỏ ĐÚNG CHỨC NĂNG** — nó không hỏng, nó **đang làm việc**.

**Hai đường hợp lệ, chỉ hai:**
| | |
|---|---|
| **A · VÁ** | PO thật chốt **mức che**. ⚠️ Tài liệu đã ghi: *"không được che tới mức CSKH mất khả năng gọi lại khách"* ⟹ **đây là quyết định của PO, không phải việc kỹ thuật** |
| **B · KÝ CHẤP NHẬN RỦI RO** | thành **ADR có văn bản**, ghi rõ biết lỗ gì và vá ở đợt nào |

🔴 **Đi vòng qua cổng** *(nới `-m`, `continue-on-error`, gỡ marker)* **KHÔNG phải đường thứ ba.**
Đó là **cơ chế thứ sáu cùng một tội** đã liệt ở `CHECKLIST #28`: *che mất tín hiệu của chính cái
đang hỏng*. Coder đã từ chối làm; PO-agent cũng sẽ không giao.

## 🔴 Và việc này KHÔNG phải "cập nhật production"

```
[ĐO Lead 25/08, xác nhận lại từ docs/DEPLOY.md:3]
app.adaptivealgo.uk   →  ✅ ĐANG CHẠY main CỦA P-226  (PO thật đính chính 25/08)
P-226                 →  CHƯA TỪNG lên site thật
job Deploy            →  20/20 lần gần nhất đều SKIPPED, chưa từng chạy thật
```

⟹ Đây là **LẦN GO-LIVE ĐẦU TIÊN của P-226**, lên một domain **đang chạy dự án khác**.
~~**PO thật phải quyết P-121-new đi đâu**~~ ✅ **ĐÃ GỠ 25/08** — domain **đang chạy main của P-226**. 🔴 Nhưng vế *«Deploy 20/20 lần SKIPPED»* **vẫn đúng và vẫn là câu hỏi mở**: nếu CI chưa từng deploy, thì **bản đang chạy trên domain lên đó bằng cách nào** — deploy tay? **Chưa ai đo.** Đừng cho là đã hiểu.

## Bốn thứ CHẶN, chưa cái nào xong

| # | chặn | ai gỡ được |
|---|---|---|
| ~~1~~ | ~~**P-121-new đang chiếm domain**~~ ✅ **GỠ 25/08** — PO thật đính chính: domain **ĐANG CHẠY main của P-226**. ⟹ đây là **cập nhật sản phẩm đang chạy**, KHÔNG phải thay dự án khác | — |
| ~~2~~ | ~~**finding P0 lộ số tài khoản khách**~~ ✅ **PO THẬT CHỌN M3 (25/08)** — lưu đủ, che ở tầng ĐỌC. Kèm **điều kiện bắt buộc**: sửa test sang chấm đường đọc **VÀ** thêm test khẳng định **bản lưu vẫn đủ** | — |
| 3 | **3 secret deploy KHÔNG TỒN TẠI** — chỉ có `OPENAI_API_KEY`; thiếu `DEPLOY_HOST` · `DEPLOY_USER` · `DEPLOY_SSH_KEY` | 🔴 **tay PO thật**, qua GitHub Settings |
| 4 | **hạn mức chi tiêu GitHub Actions** — 6 job đỏ vì *"spending limit needs to be increased"* | 🔴 **chỉ PO thật** |

⚠️ Và `docs/DEPLOY.md` **tự khai chưa xác minh**: nghi đường thật là **Cloudflare Tunnel**, không
phải expose thẳng port Oracle VPS như mục 1–2 mô tả. **Đừng làm theo tài liệu ấy như sự thật.**

## Được phép làm ngay, không cần chờ

- ✅ **push `dev/learning-loop`** lên remote — để CI chấm **đúng thứ ta định ship** *(đã làm,
  `3f00e07`, run `32846571488`)*. Không chạm `main`, không chạm production.
- ✅ vá lint trong phạm vi CI thật
- ✅ **đọc + chuẩn bị** bản vá P0 — nhưng **KHÔNG tự chọn mức che**

## KHÔNG được làm khi chưa có lệnh mới của PO thật

```
✗ push lên main            ✗ chạm production          ✗ tạo/đổi secret
✗ đi vòng qua cổng bảo mật ✗ thăm dò app.adaptivealgo.uk mà chưa báo
```
