# DỰ BÁO — trạng thái bốn cổng SAU lần dựng ảnh thứ hai

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC khi tech-lead dựng**,
> trong lúc cửa sổ dựng đang mở và tôi **không chạm container**.
> Người đổi vật lần này **không phải tôi** — nên dự báo này là cách duy nhất để
> phân biệt *"cổng đổi màu vì bản dựng"* với *"cổng đổi màu vì thứ khác"*.

## ① Vì sao viết bây giờ chứ không viết sau

Nếp của đội là công bố dự báo trước khi **ta** chạm vật. Ca này khác: **người
khác** chạm. Nếu tôi đọc cổng **sau** khi ảnh lên rồi mới giải thích, mọi giải
thích đều là **hồi cứu** — và hồi cứu luôn khớp. Viết trước là thứ duy nhất
làm nó bác được.

## ② Điều lần dựng này đổi (theo khai báo của tech-lead qua PO-agent)

```
1  cờ FIN05_CHO_PHEP_GOI_RA_NGOAI  mặc định đảo → TỪ CHỐI; compose khai =1 cho cả ba
2  tests/ trong ảnh  ← nay là bản mới nhất của tôi
3  sổ cong_ra_ngoai.jsonl  bắt đầu đếm từ 0
```

## ③ DỰ BÁO — bốn cổng của tôi, chạy TỪ HOST

| # | dự báo | độ chắc | lý lẽ |
|---|---|---|---|
| 1 | `-m "not security_finding"` vẫn **577 passed · 42 skipped · 11 xfailed** | **cao** | bản dựng đổi `src/` + compose, **không** đổi `tests/` trên host — mà tôi chạy từ host |
| 2 | `-m security_finding` vẫn **1 failed** (P0 live-chat) | **cao** | file đó sửa lần cuối 12/08, không nằm trong thay đổi lần này |
| 3 | `fin05` vẫn **761 mã hoá / 0 trần** | **cao** | CSDL nằm trên **volume**, `rebuild` không đụng volume — và PO-agent đã cấm `down -v` |
| 4 | `fin05ttl` vẫn **4 / 738** ⟹ ca đối chứng vẫn **PASSED** | **trung bình** | phụ thuộc `fin05ttl` còn sống — sếp **đang quyết** có bỏ hay không |
| 5 | `docker diff` ba container về **gần 0** | **cao** | container mới tinh; 678/181/287 dòng cũ là tích luỹ của phiên trước |
| 6 | cổng chi phí của tôi **vẫn skip** (`FIN05_CHO_PHEP_TON_TIEN` tắt) | **cao** | cờ transport là lớp **thứ hai**, không thay lớp thứ nhất |

## ④ 🔴 NẾU KHÁC THÌ NGHI GÌ — dòng đầu là dòng quan trọng nhất

| quan sát | nghi ĐẦU TIÊN | vì sao nó nghiêm trọng |
|---|---|---|
| 🔴 `fin05` quay lại **738 trần** | **VOLUME BỊ TẠO LẠI ⟹ BACKFILL MẤT** — và cùng với nó là 761 dòng dữ liệu thật | Đây là kịch bản đắt nhất của cả cửa sổ dựng, và nó **im lặng**: hệ thống chạy bình thường, chỉ dữ liệu lùi về ba tháng trước |
| `fin05` trần **> 0 nhưng ≠ 738** | backfill chạy dở, hoặc lưu lượng mới ghi trần | so `tong` với **761** ở tệp nền — `tong` mới là thứ phân định |
| vân tay gộp **đổi** mà `tong` giữ | 🔴 nội dung bị thay, không phải bị mất | mốc này **không cổng nào khác có** |
| số ca chạy **≠ 577** | `tests/` trên host bị đụng, hoặc bộ ca thu thập khác | đọc **SỐ CA**, không đọc màu — `skip` và `pass` cùng màu |
| ca đối chứng báo **KHÔNG ĐO ĐƯỢC** | `fin05ttl` đã bị bỏ/nạp lại | **đúng thiết kế** — nó phải kêu, không được im |
| `-m security_finding` **> 1 failed** | có finding mới, hoặc nhãn bị gắn lại | đọc tên ca trước khi kết luận |

🔴 **Khai trước:** dự báo 3 TRÚNG là mệnh đề hẹp — *"volume sống sót lần dựng
này"*. Nó **không** nói gì về lần dựng sau, và **không** nói gì về
`production`, nơi **chưa ai đo**.

## ⑤ Ghi nhận một điểm yếu trong THIẾT KẾ CỦA TÔI, do PO-agent chỉ ra

Ca đối chứng dương của cổng plaintext dựa vào `fin05ttl` — **một quần thể bẩn
tồn tại vì chưa ai dọn nó**.

> **Một cổng không nên phụ thuộc vào việc ai đó QUÊN DỌN.** Hôm nay nó chạy;
> ngày có người tử tế đi vá 738 dòng ấy, đối chứng biến mất.

PO-agent đúng, và tôi nhận. **Một nửa tôi đã lường:** ca báo **KHÔNG ĐO ĐƯỢC**
chứ không im lặng xanh khi quần thể bẩn hết bẩn — nên nó **tắt ồn ào**, không
tắt lặng lẽ. Nhưng "tắt ồn ào" vẫn là **tắt**.

**Thiết kế đúng hơn** (chưa làm, chờ sếp quyết `fin05ttl`): quần thể **VỨT ĐI
tạo lúc chạy test** — bảng tạm trong CSDL tạm, nhét dòng trần giả, đo, xoá.
Nó **không ghi vào ngăn xếp đang phục vụ** (Luật I vẫn được giữ) và **không
phụ thuộc trạng thái bẩn của ai**. Ghi ra đây để nó là **việc đã lên lịch**,
không phải một ý tưởng trong hội thoại — đúng Luật P.
