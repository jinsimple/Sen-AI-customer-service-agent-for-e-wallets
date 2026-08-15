# Cơ chế cho BỐN CỬA — đầu vào cho ADR-025

> Vai: **security** · 2026-08-15 · vùng ghi `docs/security/`
> Viết TRƯỚC khi PO-agent soạn dự thảo ADR-025, vì phần **cơ chế** phải đứng
> trên số đo, không trên suy luận. Mọi số dẫn ở đây đo trong phiên 15/08,
> 0 TPM, tất định — dấu `he_thong=fd16681d8088`.
>
> Nguồn số: `2026-08-15-ra-soat-cuoi-sprint-note-scrub-va-pipeline.md` (S-01,
> S-02) · `ho-so-quyet-ST2-P0-3-pii-live-chat.md` (bảng bốn cửa, §2 đo CSKH đã
> có SĐT từ kênh khác).

---

## 1. Kết luận đi trước: MỘT nguyên tắc, KHÔNG phải một cơ chế

Nguy cơ lớn nhất của việc gộp bốn cửa vào một ADR là kết luận sai thành **"áp
scrub-lúc-ghi cho cả bốn"**. Số đo nói điều đó sẽ hỏng — và hỏng nặng nhất ở
đúng hai cửa quan trọng nhất.

**Nguyên tắc đề nghị chốt (một câu):**

> **Giảm thiểu PII phải xảy ra ở nơi KHÔNG phá được bản ghi gốc. Chỗ nào bản
> ghi là BẰNG CHỨNG thì không che-lúc-ghi.**

Từ nguyên tắc đó, bốn cửa tách thành **hai nhóm có cơ chế khác nhau**, và
đường phân chia **không phải** "nhân viên gõ / khách gõ" như bảng cũ gợi ý —
mà là **bản ghi đó có phải bằng chứng không, và người gõ có sửa lại được không.**

| | Nhóm A — **lời khai, là bằng chứng** | Nhóm B — **ghi chú thao tác** |
|---|---|---|
| Cửa | `complaints.description_raw` · `messages.content` | `resolutions.note` · `investigation_logs.agent_note` |
| Ai gõ | khách (và CSKH trong live-chat) | nhân viên |
| Vai trò bản ghi | **nội dung khiếu nại** — căn cứ giải quyết tranh chấp | diễn giải/thao tác của nhân viên |
| Sửa lại được không | **KHÔNG** — không thể bắt khách gõ lại lời khiếu nại | **CÓ** — nhân viên đang ngồi trước màn hình |
| Cơ chế đúng | **KHÔNG che-lúc-ghi.** Mã hoá at-rest + siết đọc + retention + che lúc XUẤT/HIỂN THỊ | **Che-lúc-ghi ĐƯỢC**, nhưng phải **fail-visible** (xác nhận vòng tròn) |

---

## 2. Nhóm A — `description_raw` + `messages.content`: **BÁC che-lúc-ghi**

### Lý do bác, có số

`scrub_pii` đo được **chặn nhầm 8/20 = 40%** trên văn bản nghiệp vụ tiếng Việt,
kiểu hỏng là **đổi nghĩa câu trong im lặng** (`"không cần xử lý tiếp"` →
`"không [PERSON]"`). Áp lên lời khai của khách thì:

1. **Không có bản gốc để đối chiếu** — che-lúc-ghi nghĩa là DB chỉ còn bản đã
   che. CSKH đọc một khiếu nại đã bị sửa nghĩa mà **không biết chữ nào đã mất**.
2. **Bản ghi là bằng chứng.** Đây là căn cứ giải quyết tranh chấp tiền bạc; một
   lời khai bị hệ thống sửa chữ là thứ **không đứng được** nếu tranh chấp đi xa
   hơn (khiếu nại lên NHNN, hoặc ra toà). Ba cửa kia hỏng thì mất khả năng đọc;
   cửa này hỏng thì **mất giá trị chứng cứ**.
3. **Không sửa lại được.** Nhân viên bị che nhầm thì gõ lại; khách thì không —
   họ đã rời đi, và ta không được phép "hỏi lại cho rõ" mỗi lần NER bắt nhầm.

⟹ **Che-lúc-ghi ở nhóm A là đánh đổi SAI HƯỚNG**: đổi giá trị chứng cứ lấy một
mức giảm thiểu mà các cơ chế khác đạt được rẻ hơn và không phá gì.

### Cơ chế đề nghị cho nhóm A (xếp theo rẻ→đắt, làm được từng bước)

| # | Việc | Ghi chú |
|---|---|---|
| A1 | **`description_raw` → `EncryptedText`** | `messages.content` ĐÃ có (`models.py:475`). Đây là cửa khách-tự-gõ **duy nhất** còn thiếu. Rẻ, không phá gì, **không cần PO quyết cơ chế** — chỉ là bù một thứ đã là chuẩn của dự án. Có migration. |
| A2 | **Trần độ dài** | đo được: nhận **20.000** ký tự (`description_raw`), **5.000** (`agent_note`). Một trường text không giới hạn trong bảng kiểm toán là vấn đề vận hành lẫn bảo mật. |
| A3 | **Siết đọc theo NGƯỜI PHỤ TRÁCH, không theo vai** | hiện `cskh`+`supervisor` **bất kỳ ai** đọc được mọi hội thoại (ST2-P0-3 §3). Đây mới là lớp chặn "người đọc hợp lệ nhưng không có việc gì để đọc" — thứ mã hoá at-rest không chạm tới. |
| A4 | **Retention** | F-06: nội dung chat lưu **vĩnh viễn**, không chính sách xoá. NĐ 13/2023 + GDPR Đ.5(1)(e). |
| A5 | **Che lúc XUẤT** (phễu học Phase 2, DSAR, báo cáo) | Đây là chỗ scrub-phá-nghĩa **chấp nhận được**, vì bản gốc vẫn còn trong DB — mất chữ ở bản xuất không phá bản ghi. **Đúng chỗ để dùng `scrub_pii`.** |

**A5 là chỗ đặt `scrub_pii` cho đúng hạng mục nó được viết ra.** Docstring của
nó tự khai: dùng cho **log/span attribute**. Xuất/log là nơi mất một chữ không
sao. Bản ghi gốc thì không.

---

## 3. Nhóm B — `note` + `agent_note`: che-lúc-ghi ĐƯỢC, nhưng phải **fail-visible**

Ở đây che-lúc-ghi hợp lý vì: (1) nhân viên **không có cơ sở pháp lý** để chép
PII khách vào ghi chú tự do ngay từ đầu — dữ liệu đó đã có ở trường có cấu
trúc; (2) nhân viên **sửa lại được** ngay lúc gõ.

Nhưng cơ chế hiện tại **hỏng trong im lặng**, và đó mới là thứ phải sửa:

| # | Việc | Ghi chú |
|---|---|---|
| B1 | **Xác nhận vòng tròn lúc ghi** ⭐ | API trả **bản đã che** → nhân viên xác nhận hoặc viết lại. Sửa đúng cái gốc (**im lặng**) mà **không đụng chất lượng NER** — bài toán đắt, không có bộ gán nhãn tiếng Việt (cùng lý do ADR-022 hoãn PhoBERT). Là thay đổi UX + 1 route, **không phải** thay đổi lớp bảo mật. |
| B2 | (nếu bác B1) **Ghi số vùng bị che + hiển thị** | rẻ hơn, chỉ làm phép che *nhìn thấy được*, không cho người gõ cơ hội diễn đạt lại. Chấp nhận được, yếu hơn. |
| B3 | **`agent_note` nhận đủ ba lớp của `note`** | scrub fail-closed · trần 500 · cờ tier qua `_phan_loai_tier()`. Dùng lại **một nguồn sự thật**, đúng Quyết định 2 của ADR-024 — không dựng bộ mẫu song song. |
| B4 | **Cân nhắc `EncryptedText`** cho cả hai | hiện `Text` thuần. |

⚠️ **B3 phải đi SAU B1/B2**, không đi trước: bê nguyên `scrub_pii` sang
`agent_note` khi chưa sửa chế độ im lặng = **nhân bản lỗi 40% sang cửa thứ hai**.
Đây là Luật 8 áp lên chính đề xuất này.

### Cạm bẫy đã đo — đừng "sửa NER" theo cách hiển nhiên

Cách sửa trực giác là bỏ nhãn generic của spaCy, giữ `PERSON_VN` của
underthesea. **Đo cho thấy làm vậy mở một lỗ rò thật:** `Nguyễn Thị Hoa` bị bắt
bởi ĐÚNG lớp spaCy (`[PERSON]`), underthesea **bỏ sót** (nhãn gộp chỉ có
`PERSON`, không có `/PERSON_VN`; đối chứng `Lê Thu Hà` ra `[LOCATION/PERSON_VN]`
chứng minh cơ chế gộp có chạy). **Tắt spaCy = đổi lỗ toàn-vẹn lấy lỗ bảo-mật.
Không nhận đánh đổi đó.**

---

## 4. Thứ tự đề nghị (nếu PO muốn cắt lô)

**Làm được ngay, không cần quyết cơ chế** — A1 (mã hoá `description_raw`), A2
(trần độ dài cả bốn cửa). Bù thứ đã là chuẩn dự án, không phá gì, không chặn ai.

**Cần PO quyết** — B1 vs B2 (chế độ fail-visible cho nhóm B); A3/A4 (siết đọc +
retention: đụng vận hành CSKH, không thuần kỹ thuật).

**Sau cùng** — B3 (áp ba lớp cho `agent_note`), vì phụ thuộc B1/B2.

⚠️ **Không cửa nào trong bốn nên bị coi là "cửa nhẹ nhất làm trước".**
`description_raw` nghe như cửa phụ nhưng nó chứa **PII bên thứ ba** ngay ở ca
dùng điển hình nhất (*"em chuyển nhầm cho anh X, sđt…"*) — người **chưa từng
vào quan hệ với ví**, không có cơ sở pháp lý để lưu ngay từ đầu, và là cửa
khách-tự-gõ duy nhất **không mã hoá at-rest**.

---

## 5. Điều tôi KHÔNG kết luận

- **Không** kết luận nhóm A cần scrub-lúc-ghi ở bất kỳ dạng nào. Nếu PO vẫn
  muốn, xin đo trước trên corpus lời khai thật (không phải 20 câu ghi chú của
  tôi) — và ngưỡng phải là **0 câu bị đổi nghĩa**, không phải "thấp hơn".
- **Không** đề xuất con số retention cụ thể — đó là câu hỏi pháp lý/nghiệp vụ
  (NĐ 13/2023 + thời hiệu khiếu nại theo TT 40/2024), cần PO và có thể cần tư
  vấn pháp lý thật, không phải suy luận của tôi.
- **Không** đo `messages.content` bằng probe hành vi trong phiên này (số của nó
  dẫn từ ST2-P0-3 14/08 + đọc `models.py`). Nếu ADR-025 định quyết dựa trên nó,
  nói một tiếng, tôi đo như đã đo ba cửa kia.
