# Cải thiện luồng hỏi chatbot — Đợt 1A + 1B

> **PO thật duyệt 24/08:** *"ok triển khai luôn"*. Nguồn nghiệp vụ: chuyên gia CSKH ngân hàng/ví
> (văn bản PO chuyển 24/08, đặc tả rút gọn ở cuối file). Đợt 2 (FS-13) và Đợt 3 (slot × loại
> vào contract) **chưa duyệt** — không làm.
>
> **Checklist trạng thái sống ở file này.** PO-agent là người duy nhất tick.

---

## CHECKLIST

> **Đồng bộ 24/08 18:30** — bản trước lỗi thời (1B.2 và 3 việc vá gấp đã xong mà vẫn để trống).
> Lỗi của PO-agent: cập nhật trang artifact mà quên cập nhật chính nguồn sự thật này.

### Đợt 1A — Luật hỏi trong prompt

- [x] ✅ **1A.1** — điều kiện niêm trước (*"lượt chạy chứng minh quan sát được trên hội thoại thật"*)
      **ĐÃ ĐẠT 24/08**, cả hai chiều: R1 bắt được **vi phạm thật** · R3-cầu quan sát được **ca đạt thật**.
      Tick vì **năng lực quan sát** đã chứng minh — KHÔNG phải vì sản phẩm sạch (R1 vẫn đỏ, xem 1A.6).
- [ ] ~~(bản cũ)~~ **1A.1** vá xong `74546a5`, chờ lượt chạy chứng minh — R3/R4 chưa từng quan sát được
      trên hội thoại thật. Tick lại chỉ khi lượt chạy chứng minh, không phải vì bản vá đã land.
- [x] **1A.2** ✅ `f6f70df` + `9418d1a` + `2b197d0` + `9dbbe4b` + `1080762` + `7bd87d5` — R1–R5 và
      ADR-047 vào prompt. Trần +621/600, **vượt 21 CÓ CHỦ Ý** (lý do trung thực). Mốc đợt sau tính từ 621.
- [x] **1A.3** ✅ delta render thật, băm mẫu khớp trong cây
- [x] **1A.4** ✅ **ĐÓNG — A2 không giải được bằng prompt.** 6 vòng, 6 cơ chế loại trừ kể cả trần
      model. Kết luận → **ADR-049** (chờ PO). Không vá thêm.
- [ ] **1A.5** PO-agent kiểm độc lập → tick
- [ ] 🔴 **1A.6 (MỚI 24/08) — R1 VI PHẠM THẬT, chưa sửa.** Agent hỏi **3 trục cùng lượt**
      (`thoi_gian`+`ma_gd`+`so_tien`) trong khi prompt cấm nguyên văn *"gộp dạng A hoặc B"*.
      **Tái hiện 2 lượt độc lập.** Cùng họ với A2: **luật viết rõ, model không tuân**
      ⟹ **bằng chứng thứ hai cho ADR-049**. KHÔNG vá bằng chữ — vá bằng chữ là quay lại
      đúng vòng lặp đã thua 6 lần. *(chờ chuyến chạy)*

### Đợt 1B — Cổng thu thập tất định

- [x] **1B.1** ✅ thiết kế duyệt + sửa lỗi số học cửa sổ MỘT CHIỀU
- [x] **1B.2** ✅ `350fd2f` — cổng land, đo thật: câu thiếu số tiền → `thu_slot`, **0 token**
- [x] **1B.3** ✅ corpus **23 ca** (S1–S24) + **ĐC-1..7** — ba đối chứng sinh trong ngày vì công cụ
      đo hỏng ba kiểu: ĐC-5 lỗi thời · ĐC-6 (ĐC-5 sau sửa bị mù) · ĐC-7 (chưa ai kiểm NỘI DUNG reply)
- [~] 🟡 **1B.4 — 4/5 mục ĐẠT, mục ② CHƯA ĐỦ.** ① eval đường-cho-qua ✅ · ③ R3-cầu ✅ ·
      ④ S7 ✅ · ⑤ S8 ✅ **live-fire thật** (`docker events` xác nhận Redis stop/start thật).
      🔴 **② R1–R5 trọn bộ: R5 CHƯA ĐO ĐƯỢC** (dính `APIConnectionError` thoáng qua — 9,4%/53 lượt).
      **CỐ Ý KHÔNG sửa định nghĩa 5 mục để tick cho trọn** — sửa tiêu chuẩn sau khi thấy kết quả là
      đúng thứ tôi vẫn cấm người khác làm. Tick trọn khi R5 đo được.
- [ ] ~~(định nghĩa gốc, GIỮ NGUYÊN)~~ **1B.4** chuyến chạy cuối, **5 mục, S8 xếp CUỐI**: ① eval đường-cho-qua ② R1–R5 trọn bộ
      ③ R3-cầu (cổng→LLM) ④ S7 ⑤ S8 *(chờ ảnh)*
- [ ] **1B.5** PO-agent đo hiệu ứng cổng theo **phép đo đã niêm trước** *(chờ chuyến chạy)*

### ✅ Năm vòng vá cổng 1B — ĐÃ XONG HẾT

- [x] bắt oan câu chính sách (`1b80bf4`) · [x] S8 đổi hướng về `day_du` (`1b80bf4`)
- [x] đối xử máy móc với người đang hoảng (`5f3a1ef`) · [x] mẫu câu hỏi 3 thứ, vi phạm R1 (`cd5c057`)
- [x] không đọc được số viết chữ — *cổng làm TỆ HƠN không có cổng* (`d9e53ae` + `2dd5c3e`)
- [x] corpus trục tổ hợp + trục cảm xúc + số viết chữ (`c459e24`, `29eda41`, `8e087ab`)

### Xếp hàng SAU khi 1A đóng (đội tự làm, không chặn ai)

- [ ] **`pre-commit` cảnh báo commit chạm file NGOÀI vùng ghi của vai** (DevOps).
      🔴 Lỗi cuốn-WIP-của-người-khác đã xảy ra **HAI lần trong một tuần** trên cây dùng chung:
      PO-agent 15/08 (`git add -A`, 107 dòng của Coder), Tester 24/08 (tự phát hiện + tự sửa sạch).
      Luật pathspec đã phê chuẩn 15/08 mà vẫn tái diễn ⟹ **thiếu CƠ CHẾ, không thiếu luật**.
      §4 hiến pháp đã có bảng phân vùng — máy đọc được. **Cảnh báo, không chặn cứng**: mục tiêu là
      bắt người commit NHÌN THẤY thứ mình sắp cuốn theo.

- [x] ✅ **Nạp tài liệu thời hạn xử lý vào kho RAG** — `DOC-234adbc3f66e`, **3 chunk, CHỈ §1** (khối tác giả tự gắn nhãn *"viết cho khách đọc"*; §2/§3 mang phân tầng độ tin cậy + giọng tác giả, `PolicyChunk` không có trường chở nổi metadata đó ⟹ nạp vào là mời agent đọc lại cho khách nghe). Ngăn `fin05`, không đụng ngăn đo. **Verify thật:** query *"bao lâu thì xử lý xong khiếu nại"* → chunk mới đứng **#1** (khoảng cách 0,64, cách #2 rõ rệt) — được TÌM THẤY, không chỉ được nạp. Băm kho `11b11b494a6a`(378c) → `e11ca51e5346`(381c)
- [ ] ~~(mục cũ)~~ **Nạp tài liệu thời hạn xử lý vào kho RAG** — `b7a7e16` (Bảo mật soạn, TT 15/2024 Điều 6
      Khoản 3-4, đã phân tầng độ tin cậy tại chỗ). 🔴 **Nạp xong ⟹ băm kho ĐỔI ⟹ Recall@4 =
      47,9% [ĐO 17-20/08] HẾT HẠN NGAY.** Phải đo lại + niêm số cũ, không để nó sống tiếp
      dưới danh nghĩa số hiện hành.
- [ ] **ADR-046** (PO duyệt 24/08) — `build_background_complaints()`, `eligible_status` đang là
      set một phần tử.

- [ ] **O5 / mở rộng O4** — từ vựng "tạo hồ sơ/vé/ticket" cho lớp hoàn-tất-giả
      (finding Bảo mật `5f627e3`: "đã tạo hồ sơ cho bạn rồi" lọt sạch O3+O4 vì không số,
      không từ tiền). **Tester viết ca đối chứng TRƯỚC, hai chiều** — bắt bịa-đã-tạo VÀ
      không-chặn-nhầm câu báo-đã-tạo-thật. Khuôn ADV-041 đã có, khác miền từ vựng.
- [ ] Sửa nhãn S9 trong `bo_ca_thu_slot_1b.json`: ghi "①" nhưng lý lẽ thuộc (ii) —
      lỗi nhãn nhẹ (Review), không đổi kỳ vọng ca.
- [ ] **Disclaimer vào output harness eval** (kiểm kê Bảo mật `7e38a62`): ① `_ALWAYS_FRESH`
      — OTP luôn tươi trên đường eval, trục "OTP thiếu/hết hạn" CHƯA TỪNG tồn tại trong
      eval; ② harness gọi thẳng `run_agent_turn()` — JWT/rate-limit/audit KHÔNG nằm trên
      đường đo. Hai dòng in đầu kết quả, không đổi logic.
- [ ] **Ca eval "OTP hết hạn giữa hội thoại"** — trục chưa từng đo, ghép với ca đối chứng
      O5 ở trên (cùng gốc finding `5f627e3`).

### 🟡 CHỜ PO THẬT — năm câu, gom một chỗ

1. **Hạn SLA cho vé `scope=unknown`** — hiện **30 ngày** và `compute_sla_due_at()` chỉ chạy MỘT
   lần lúc tạo, **không bao giờ tính lại**. Ca chạm ngân hàng đáng lẽ **4 ngày làm việc**
   ⟹ vé trôi sai hạn vĩnh viễn, bảng theo dõi vẫn xanh, và agent **đọc mốc sai đó cho khách nghe**.
   *Khuyến nghị: gán hạn CHẶT NHẤT. Đánh đổi: tải CSKH tăng.*
2. **Trần số vé mỗi phiên** — ADR-047 bỏ điều kiện tra-cứu ⟹ một tin nhắn đủ tạo vé.
   ~300 vé/cửa sổ OTP so với 20 vé/CSKH/ca. *Khuyến nghị: trần tất định.*
   🔴 **Bảo mật cảnh báo: nếu duyệt ADR-049 thì đây thành ĐIỀU KIỆN TIÊN QUYẾT**, không phải
   khuyến nghị song song — luật cứng thì **học thuộc được**, không cần thuyết phục model nữa.
3. **FS-13 escalate hay chỉ ghi nhận** (ADR-048) — đổi tải hàng chờ supervisor thật.
4. **ADR-049** — đổi đòn bẩy A2 sang cơ chế tất định. Chuyển một quyết định nghiệp vụ từ **model**
   sang **luật cứng**: được sự đoán trước, mất khả năng model xử ca lạ.
5. **Chạy lại `gen_dataset` thật cho ADR-046** — code xong (`27c2640`), verify ở scratchpad
   (67/23 = 74,4%/25,6%, `processing` vẫn đa số). **Chưa regenerate** vì đổi 600 complaint +
   60K transaction đang backing demo, và ADR-046 tự đặt nghi thức *"công bố DỰ BÁO trước khi
   chạy lại"*. Cần PO quyết thời điểm.

### Chờ PO thật (không thuộc 1A/1B)

- [ ] Đợt 2 — **ADR-048** (đổi số: 047 đã dùng cho tiếp-nhận-trước) tín hiệu FS-13 "có người hướng dẫn chuyển khoản"
- [ ] Nguồn tài liệu SLA tra soát cho kho RAG (chuyên gia CSKH hoặc soạn từ NĐ 52/2024 + TT 40/2024)

---

## 🔴 DỰ BÁO CÔNG BỐ TRƯỚC — niêm tại đây trước khi code

```
token/hội thoại (trung vị, deepseek, n=11):  18.597  [ĐO 20/08]
dự báo sau 1B:                               12.000–14.000  (giảm 25–35%)
```

### 🔴 NIÊM 24/08 — SỐ NỀN 18.597 KHÔNG TÁI TẠO ĐƯỢC. Lỗi của PO-agent.

[ĐO 24/08] `usage.jsonl` trên ngăn đo `fin05do` chỉ có **17/08 (13 dòng)** và **24/08 (29 dòng)** —
**không có dòng nào ngày 20/08**. Con số `18.597` xuất hiện **đúng một chỗ trong toàn repo: chính
dòng trên**, do tôi viết. Không file đo, không định nghĩa "một hội thoại" là gì, không lệnh tái tạo.

**Đây là vi phạm Luật X do chính tôi gây ra** — *kết quả đo phải rơi vào một file trước khi đi vào
một câu* — và tôi đã để nó thành **neo của một dự báo công bố**. So số mới với nó rồi tuyên bố
"giảm 30%" là so với một thứ không kiểm chứng được.

**KHÔNG xoá dòng trên** (Luật P: niêm tại chỗ, đừng để người sau đi truy lại). Nhưng **không dùng
nó làm căn cứ kết luận.**

### Phép đo 1B.5 THAY THẾ — niêm TRƯỚC khi thấy số

Bỏ so-sánh-lịch-sử, đo **hiệu ứng trực tiếp của cổng**, tái tạo được bằng một lệnh:

```
① tỉ lệ chặn   = số lượt duong=thu_slot ÷ tổng lượt   (đọc usage.jsonl)
② token/lượt thu_slot  = 0            (khẳng định, phải verify chứ không giả định)
③ token/lượt day_du    = trung vị thật của các lượt day_du CÙNG ĐỢT ĐO
④ tiết kiệm    = ① × ③                 ← con số công bố được
```

Ưu điểm: **cùng một ngăn, cùng một đợt, cùng một model** — không phụ thuộc bất kỳ số lịch sử nào.
Nếu ① = 0 (cổng không bắn lần nào trên dữ liệu thật) thì kết luận là **"cổng chưa chứng minh được
giá trị trên lưu lượng thật"**, không phải "không đo được".

🔴 **Niêm phương pháp TRƯỚC khi thấy dữ liệu — để không chọn cách tính cho ra số đẹp.**

---

## Đặc tả rút gọn cho 1A (đủ để Tester viết ca, không cần đọc src)

Năm luật phải vào prompt, mỗi luật một hành vi ĐO ĐƯỢC:

| # | luật | hành vi đo được |
|---|---|---|
| R1 | **Một câu hỏi một lượt.** Khi còn thiếu nhiều thông tin, mỗi lượt chỉ hỏi MỘT thứ | reply khi thiếu ≥2 slot chỉ chứa MỘT yêu cầu thông tin |
| R2 | **Hỏi mã giao dịch phải kèm đường đi.** Không nói trống "cho em xin mã" — kèm hướng dẫn dạng "vào Lịch sử, bấm vào giao dịch là thấy" | reply hỏi mã PHẢI chứa hướng dẫn tìm |
| R3 | **Lần hỏi lại thứ hai phải ĐỔI TRỤC.** Tra theo số tiền không ra → hỏi theo trục khác (thời gian, tên người nhận), không lặp nguyên câu | reply hỏi-lại không trùng trục với lần hỏi trước |
| R4 | **Tóm tắt slot trước create_ticket.** Trước khi tạo vé, đọc lại: loại + số tiền + thời gian + đích, để khách tự sửa. (Nâng A2: A2 là "chờ đồng ý", R4 là "đọc lại để khách sửa") | reply ngay trước create_ticket chứa đủ số tiền + thời gian + loại |
| R5 | **Hỏi thời gian bằng mốc neo.** Không hỏi "mấy giờ" — hỏi "hôm nay hay hôm trước, sáng hay chiều" | câu hỏi thời gian không đòi giờ chính xác |

Nguyên tắc gốc (chuyên gia): *mỗi câu hỏi phải mở được một nhánh quyết định · không hỏi thứ
tra được — hỏi để THU HẸP tìm kiếm, không hỏi để lấy dữ liệu*.

## Đặc tả 1B (cho Lead thiết kế)

```
① KHÔNG chặn lời kể — tin nhắn đầu của khách là tự do (= L1 tự nhiên).
   Cổng chỉ xét SAU khi nhận diện ý định tra-giao-dịch.
② BÓC TRƯỚC, HỎI SAU — bóc slot có sẵn trong lời kể (regex: số tiền, mốc ngày,
   mã TXN/TCK — khuôn đã có trong pii.py). CHỈ hỏi phần thiếu, MỘT tin gọn:
   khoảng thời gian + số tiền; mã giao dịch ghi "nếu có" kèm đường đi 3 bước.
③ CỔNG LÀ ĐƯỜNG TĂNG TỐC, KHÔNG PHẢI TƯỜNG — khách không nhớ / kể chuyện khác
   → cho qua LLM như cũ. Nhận diện thà BỎ SÓT còn hơn BẮT OAN: câu chính sách
   ("phí chuyển tiền là bao nhiêu?") tuyệt đối không kích cổng.
```
Điểm nối: `src/agents/phan_luong.py` (đường `nhe`/`day_du` sẵn có, fallback an toàn đã đúng nếp).
Cổng đối chứng: `eval/cong_phan_luong.py` — mở rộng corpus, không thay.

## Những thứ ĐÃ CÓ — cấm làm lại

- Xoa dịu tách khai thác (`prompt.py:21` — "Mình hiểu…" bắt buộc trước kết quả tra)
- Chờ đồng ý tường minh trước create_ticket (test A2)
- `multiple_matches` → PHẢI hỏi lại, cấm tự chọn (contract)
- Danh sách cấm hỏi: OTP/mật khẩu/thẻ (ràng buộc cứng 4) + `otp_disclosed` + che bên thứ ba
- Chống lặp `lap_lai_vo_ich` (R3 NỐI vào đây, không thay)
