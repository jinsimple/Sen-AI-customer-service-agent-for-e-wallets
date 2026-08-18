# Giao việc — TESTER · 18/08/2026 · dời ca đối chứng khỏi `fin05ttl` trước khi xoá nó

> Viết cho người đọc **NGUỘI**. Bạn **KHÔNG đọc `src/`** — đó là cố ý (`CLAUDE.md` §4). Mọi thứ cần
> biết nằm ở đây và ở `docs/` + `contracts/`. Thiếu gì thì **hỏi, đừng suy đoán**.

## 0. Đọc trước

| đọc | vì sao |
|---|---|
| `docs/DECISIONS.md` → **ADR-036** | quyết định của PO, đây là việc |
| `docs/STATE.md` §5.O | mẫu số ba ngăn xếp, và vì sao "738 → 0" chỉ đúng cho một |
| `docs/STATE.md` §7 **Luật A** · **Luật I** · **Luật Q** | ba luật ràng buộc trực tiếp việc này |

🔴 **Luật Q, làm trước tiên:** `git rev-parse --abbrev-ref HEAD && git log --oneline -1`.
Nhánh đúng: **`dev/learning-loop`**. 18/08 cây từng bị chuyển sang nhánh khung mẫu **giữa lượt** mà
`git status` vẫn báo SẠCH (§5.P). Hỏi cây đang đứng đâu **trước** khi tin file nào.

## 1. Việc

PO chốt **xoá `fin05ttl`**. Nhưng `fin05ttl` đang giữ **ca đối chứng duy nhất** chứng minh cổng
plaintext **còn biết ĐỎ** — nửa *"KÊU lúc bất thường"* của **Luật A**. Xoá trước = tắt nó.

⟹ **Ba bước, đúng thứ tự, không rút gọn:**

```
① dựng lại ca đối chứng trên một QUẦN THỂ VỨT ĐI
   (tạo riêng cho việc đó — KHÔNG phải ngăn xếp đang phục vụ)
② chứng minh ca mới ĐỎ đúng lúc cần đỏ      ← bước nghiệm thu, không phải thủ tục
③ báo lại → khi đó fin05ttl mới được xoá
```

**Bạn làm ① và ②. Bước ③ là báo cáo, không phải xoá** — việc xoá ngăn xếp không thuộc vùng ghi của
bạn.

## 2. Ràng buộc cứng của việc này

- 🚫 **KHÔNG nhét dòng plaintext giả vào CSDL của ngăn xếp đang phục vụ** — **Luật I**. Bạn đã từ
  chối cách này một lần và đúng; ADR-036 ghi lại lựa chọn ấy làm chuẩn.
- 🚫 **KHÔNG `docker compose down -v`.** Mọi lệnh compose **bắt buộc `-p`**.
- 🚫 **Mọi lệnh `git` phải có pathspec** — cây dùng chung, đã có 3 sự cố.
- ✅ Quần thể vứt đi phải **do ta dựng ra để vứt**, không phải vật **ta lỡ chưa dọn**. Lý do nằm ở
  ADR-036: một dụng cụ đo chỉ hoạt động chừng nào lỗ còn mở là dụng cụ **cột đội vào việc không bao
  giờ vá lỗ ấy**.

## 3. Ca ② phải phân biệt được BA trạng thái, không phải hai

```
plaintext CÒN          → cổng ĐỎ          (đây là thứ phải chứng minh)
plaintext HẾT          → cổng XANH
KHÔNG ĐỌC ĐƯỢC quần thể → cổng phải BÁO RIÊNG, không được lặng lẽ XANH
```

Trạng thái thứ ba là chỗ dễ mất nhất: nếu quần thể vứt đi bị dọn/hỏng, ca sẽ **xanh vì không thấy gì**
— đúng hình dạng *"assertion trùng trạng thái mặc định"*. Xem `tests/CHUAN-VIET-TEST.md`.

## 4. Nghiệm thu — dán số thật

Báo lại đủ ba dòng:
```
① quần thể vứt đi:  bao nhiêu dòng plaintext, dựng bằng cách nào (lệnh nguyên văn)
② ca đối chứng:     ĐỎ — dán output thật, không tóm tắt
③ ca chiều xuôi:    XANH trên quần thể sạch — dán output thật
```

⚠️ **CI đang KHÔNG chạy** (billing GitHub — §5.A0 vòng 2). Chạy tay, dán thật.
**Test không chạy được thì nói là chưa chạy được** — đừng báo xong bằng suy luận.

## 5. Sau khi bạn xong

`fin05ttl` bị xoá ⟹ **bảng ba ngăn xếp ở `docs/STATE.md` §2 còn HAI**. `fin05do` **giữ** (kho RAG
rỗng, phục vụ trục đo token — ADR-036 QĐ3). Và cho tới lúc bước ③ xong, **mọi phát biểu về mã hoá
at-rest phải kèm phạm vi**: *"đã mã hoá trên ngăn xếp phục vụ `fin05`"*, không phải *"đã mã hoá"*.
