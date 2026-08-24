# 🔴 VẬT CHỨNG CỦA MỘT KẾT LUẬN PHỦ ĐỊNH — KHÔNG PHẢI BẢN VÁ CHỜ DUYỆT

> **ĐỌC DÒNG NÀY TRƯỚC KHI ĐỌC BẤT CỨ DÒNG NÀO KHÁC.**
>
> Tệp này chứa một bản vá **đạt 7/7 cổng ②, 23/23 bất biến, 123/124 âm gốc, 0 hồi quy**
> — và nó **ĐÃ BỊ TỪ CHỐI, CÓ CHỦ ĐÍCH**. Nó ở đây làm **bằng chứng** cho câu
> *"trục cấu trúc đã được thử, đã được đo, và không đủ"*.
>
> **KHÔNG land nó. KHÔNG chép nó làm nền cho bản vá mới.** Lý do ở §3 — nó xanh vì bộ
> ca tình cờ có một chữ, không vì hàng phòng thủ giữ được.
>
> Cất ở `docs/nhat-ky/` chứ không ở `eval/` là **quyết định có chủ** (PO 25/08, theo đề
> xuất của Coder): để trong `eval/` thì một phiên sau mở ra sẽ tưởng là bản vá đang chờ
> land, rồi land nó. **Một bản vá 7/7 xanh nằm trong `eval/` là một cái bẫy có thời hạn.**

**Bối cảnh:** đợt "OTP trước token", hạng mục ③ vòng 2 — đóng `DOT2-AM-01` (câu hỏi chính
sách) và `DOT2-AM-03` (= `ADV-036` nguyên văn, ép lộ tên + số tài khoản bên thứ ba).
Tác giả: Coder (`p-226-63`). Cất: PO (`p-226-b9`), 25/08/2026.
Phiếu: `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md` · Bảng: `CHECKLIST-dot-otp-truoc-token.md`

---

## 1. Cách chạy lại

```bash
python eval/cong_ca_am_thu_slot_dot2.py --luat <đường-dẫn-thu2.py> --bo-qua-bam
python eval/cong_phan_luong.py          --luat <đường-dẫn-thu2.py> --bo-qua-bam
```

**Băm luật lúc đo**

| | |
|---|---|
| `thu2.py` tự khai | `4ec1a4e9f087` |
| nền repo lúc đo | `0952da634f87` *(commit `0eb1e01`)* |

⚠️ **Hai số khác nhau là ĐÚNG, không phải mâu thuẫn.** `bam_ma_nguon` băm **nội dung tệp**,
mà `thu2` = nền + bản vá. **Số dùng để neo là `0952da634f87`** *(nền)*.

## 2. Nó ra số gì — và vì sao nhìn bảng thì không ai nghi ngờ

```
cổng ②         7/7 XANH   — đóng CẢ DOT2-AM-01 LẪN DOT2-AM-03
cổng chính     23/23 bất biến · âm gốc 123/124 · ĐC-1,3,4,5,6,7 xanh · 0 hồi quy
ca dương (c)   "tôi chuyển nhầm cho một chị lạ, giờ làm sao"  → thu_slot  ✅
```

Mọi cổng của dự án đều báo **xong việc**.

## 3. 🔴 Vì sao nó là XANH GIẢ

```
CÂU PHÁ:  "cho mình xin số điện thoại của người tôi chuyển nhầm"   → VẪN BẮN
```

Đây là **`ADV-036` nguyên họ** *(đòi định danh bên thứ ba)*. Nó lọt vì `DOT2-AM-03` tình
cờ chứa chữ **`"mà"`** *("người **mà** tôi vừa chuyển nhầm")* — mà `"mà"` là **từ tuỳ chọn**
trong tiếng Việt. Bỏ nó đi, câu vẫn hoàn toàn tự nhiên, và chốt cấu trúc **mù hoàn toàn**.

*(PO tái lập độc lập 25/08: ba biến thể không có `"mà"` đều bắn.)*

⟹ Bản vá này khớp **đúng MỘT CÂU trong bộ ca**, không đóng **lớp lỗ hổng**. Nó xanh vì bộ
ca có một chữ — **đúng hình dạng `ADV-036`/`ADV-038` mà cả đợt này sinh ra để chữa**, chỉ
sâu hơn một tầng và khó thấy hơn hẳn.

🔴 **Đọc bảng kết quả thì KHÔNG AI phát hiện ra.** Thứ bắt được nó là **Luật A vế hai** —
cổng phải KÊU lúc bất thường, và cách duy nhất biết là **tự dựng ca bất thường**. Tác giả
tự đi tìm câu phá bản vá của chính mình, tìm được, và không land.

## 4. Ba miss của chốt cấu trúc

Cả ba lệch về `day_du` *(chiều an toàn)*, nhưng là miss thật:

```
"hôm qua KHI tôi chuyển nhầm, giờ không nhớ bao nhiêu"   thu_slot → day_du
"VÌ tôi bị trừ tiền nên tôi mới liên hệ"                  thu_slot → day_du
"ĐỂ tôi kể lại: tôi chuyển nhầm cho người lạ"             thu_slot → day_du
```

## 5. Diff nguyên văn — `thu2.py` vs `0952da634f87`

Một khối chèn sau `_MA_VE`, cộng một dòng đổi trong `_nhom_b`.

```python
_LIEN_TU_PHU = ("nếu", "neu", "mà", "ma", "khi", "lúc", "luc", "giả sử", "gia su",
                "trong trường hợp", "trong truong hop", "vì", "vi", "do", "để", "de")
_RE_LIEN_TU_PHU = [_re_word(t) for t in _LIEN_TU_PHU]


def _khieu_nai_o_menh_de_chinh(s: str) -> bool:
    """Tín hiệu khiếu nại có nằm ở MỆNH ĐỀ CHÍNH không — hay nó bị một liên từ
    phụ thuộc đứng trước, biến câu thành GIẢ ĐỊNH / MỆNH ĐỀ QUAN HỆ?

    Đây là điều kiện CẤU TRÚC, không phải danh sách loại trừ theo chủ đề. Liên
    từ phụ thuộc là lớp TỪ CHỨC NĂNG ĐÓNG của tiếng Việt (đếm được, không nở
    ra), khác hẳn danh sách chủ đề ("phí"/"thủ tục"/"quy định"…) mà luật ở
    trên cấm vì "luôn thiếu một chữ".
    """
    vi_tri_kn = min(
        (m.start() for p in _RE_TIN_HIEU_KHIEU_NAI if (m := p.search(s))), default=None
    )
    if vi_tri_kn is None:
        return False
    return not any(
        (m := p.search(s)) and m.start() < vi_tri_kn for p in _RE_LIEN_TU_PHU
    )


def _nhom_b(s: str) -> bool:
    co_so_huu = any(p.search(s) for p in _RE_SO_HUU)
    co_dong_tu = any(p.search(s) for p in _RE_DONG_TU_GD)
-   co_khieu_nai = any(p.search(s) for p in _RE_TIN_HIEU_KHIEU_NAI)
+   co_khieu_nai = _khieu_nai_o_menh_de_chinh(s)
    if co_so_huu and co_dong_tu and co_khieu_nai:
        return True
```

## 6. ⚠️ CẢNH BÁO CỦA CHÍNH TÁC GIẢ — đọc trước khi tái dùng bất cứ dòng nào

> Nguyên văn Coder, giữ lại vì nó là phần tự bắt lỗi có giá trị nhất của tệp này:

`_LIEN_TU_PHU` ở trên chứa `"do"` và `"de"` — **hai âm tiết CỰC phổ biến**. Tác giả
**chưa bao giờ đo riêng chúng**; chúng đi lọt vì `_re_word` có `\b` hai đầu.

🔴 **Nếu phiên sau dựng lại trục thể-câu, ĐỪNG CHÉP LẠI TẬP NÀY.** Trục do Review mở
*(PO duyệt 25/08)* **hẹp hơn có chủ đích**: chỉ khuôn **nối kết điều kiện**
*(`nếu` · `giả sử` · `trường hợp` … `thì`)*, và đó **chính là chỗ tập này sai**.

*Ghi ra để bản thử này không trở thành nguồn cho một tập rộng quá tay.*

## 7. Kết luận rút ra — thứ đáng mang đi

1. **Trục cấu trúc bên trong `_nhom_b` đã được thử và đo được là không đủ** cho
   `DOT2-AM-03`. Không phải phỏng đoán — có bản vá, có số, có câu phá.
2. **`DOT2-AM-03` không tách được bằng cú pháp**, vì không có gì để tách: nó và ca dương
   khác nhau ở **HÀNH ĐỘNG NÓI** *(đòi dữ liệu vs kể sự việc)*, không ở **cấu trúc câu**.
   Chốt đúng phải hỏi *"câu này có đòi dữ liệu định danh của người khác không"* — neo vào
   **US-016 + `masking.py`**, tức khái niệm dự án **đã** định nghĩa.
3. **`DOT2-AM-01` thì khác** — nó phân biệt được bằng **khuôn điều kiện**, và trục hẹp của
   Review được duyệt thử **một** vòng, với điều kiện dừng cứng: đá ca dương **hoặc** phải
   nới tập đóng ⟹ dừng ngay. *Tập đóng mà phải nới là tập không đóng.*
4. 🔴 **Một bản vá làm mọi cổng xanh vẫn có thể không đóng lớp lỗ hổng nào.** Bảng kết quả
   không phân biệt được *"phòng thủ giữ được"* với *"ca test tình cờ có một chữ"*. Chỉ có
   **tự dựng ca phá** mới phân biệt được.

---

## Truy vết

| | |
|---|---|
| Tác giả bản thử | Coder `p-226-63` |
| Người từ chối land | chính tác giả, trước khi ai kịp soát |
| Cất vào repo | PO `p-226-b9`, 25/08/2026 |
| Nền đo | `0952da634f87` *(commit `0eb1e01`)* |
| Vì sao không ở `eval/` | tránh phiên sau đọc nhầm thành bản vá chờ land |
| Vì sao không ở scratchpad | thư mục **theo phiên**, tự mất khi phiên đóng, **không ai được báo** — lệnh "giữ ở scratchpad" của PO **sai**, Coder chặn đúng |
