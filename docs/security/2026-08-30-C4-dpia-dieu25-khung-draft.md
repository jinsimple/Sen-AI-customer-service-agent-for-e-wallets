# C4 — Khung DPIA / hồ sơ chuyển dữ liệu xuyên biên giới (DRAFT, chưa ký) — Làn C "Nền Vững"

> Vai: `security`. Giao từ Lead (`p-226-61`), theo `docs/giao-viec/2026-08-30-po-ke-hoach-tong-quan-doi-moi.md`
> §3 Làn C, mục C4. **Đây là KHUNG (framework) — sẵn sàng để PO thật ký khi họ quyết mục 6 ở §4 kế
> hoạch Nền Vững (có nộp hồ sơ chính thức hay không). KHÔNG tự quyết thay, KHÔNG hỏi lại câu đó lần
> 3** (đã treo 2 lần, đúng như kế hoạch ghi).
>
> **Căn cứ pháp lý: Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP** (hiệu lực 01/01/2026), **KHÔNG** phải
> NĐ 13/2023 (đã hết hiệu lực — xem `docs/security/2026-08-30-niem-luat-91-2025-thay-nd-13-2023.md`).
> Vật liệu kỹ thuật lấy từ `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`
> (đã có, đầy đủ, [ĐO] 17/08) — tài liệu này chỉ ĐÓNG KHUNG lại theo căn cứ luật mới + cập nhật những
> gì đã đổi từ 17/08 tới nay, không đo lại từ đầu.

## 0. 🔴 Điều kiện tiên quyết trước khi PO ký bản này thành CHÍNH THỨC

Số điều/mục trong Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP **tương đương "Điều 25 NĐ 13/2023"** (đánh
giá tác động chuyển dữ liệu ra nước ngoài) **CHƯA được tôi xác nhận bằng cách đọc toàn văn** — chỉ
xác nhận qua WebSearch rằng NĐ 356/2025/NĐ-CP "quy định chặt chẽ hơn về thủ tục chuyển dữ liệu ra
nước ngoài" là MỘT trong 5 nhóm vấn đề cốt lõi của nghị định (đúng chủ đề, nhưng chưa có số điều cụ
thể). **Người ký bản chính thức phải tự đọc toàn văn** trước khi điền số điều vào khung dưới đây,
không suy từ tên gọi "Điều 25" cũ.

🟢 **CẬP NHẬT — PO đã đọc toàn văn (ảnh từng trang, PDF quét), báo qua Lead 30/08.** Ba điều đã có số
chính xác — [theo báo cáo PO, tôi CHƯA tự đọc bản gốc, chỉ ghi lại có gắn nguồn]:
- **Đ.21.1** — hồ sơ DPIA phải nộp trong **60 NGÀY** kể từ ngày ĐẦU TIÊN xử lý dữ liệu cá nhân THẬT.
  Đây là đồng hồ cần biết đã chạy chưa — xem §0b.
- **Đ.2.3** — "dữ liệu nhạy cảm" được định nghĩa bằng **DANH MỤC DO CHÍNH PHỦ BAN HÀNH** (nghị định
  riêng) — **CHƯA có toàn văn NĐ 356/2025**, nên **KHÔNG khẳng định** "dữ liệu FIN-05 (lịch sử giao
  dịch tài chính) là dữ liệu nhạy cảm theo luật" cho tới khi đọc được danh mục đó. Đã sửa lại toàn bộ
  văn bản dưới đây theo đúng giới hạn này (trước đó §6 có khẳng định vội, đã sửa).
- **Đ.38.2** — miễn trừ Đ.21/Đ.22/khoản 2 Đ.33 cho doanh nghiệp nhỏ, **CÓ mệnh đề loại trừ**: KHÔNG
  áp dụng nếu tổ chức "trực tiếp xử lý dữ liệu nhạy cảm HOẶC xử lý dữ liệu của số lượng lớn chủ thể".
  FIN-05 xử lý khiếu nại tài chính — CÓ THỂ thuộc diện loại trừ (tuỳ Đ.2.3 xác nhận "nhạy cảm" hay
  không, xem trên) — **KHÔNG dùng miễn trừ Đ.38.2 như một lối thoát chắc chắn** trong bất kỳ tài liệu
  nào cho tới khi Đ.2.3 được xác nhận.

## 0b. Đồng hồ Đ.21.1 đã chạy chưa? — đã điều tra 17-18/08, KẾT QUẢ CHƯA ĐÓNG, không phải chưa làm

**Đây không phải câu hỏi mới.** Một phiên security trước đã điều tra kỹ đúng câu này 17-18/08
(`docs/security/2026-08-18-phan-xu-hai-cau-treo-va-ranh-gioi-do-duoc-cua-ho-so-D25.md §3`, dưới thẻ
`<details>` vì PO đã đóng nhánh HỒ SƠ GIẤY 18/08 — nhưng **không đóng vì câu hỏi đã được trả lời**,
đóng vì PO quyết không làm hồ sơ ở thời điểm đó). Tôi (30/08) đọc lại toàn bộ, không đo lại từ đầu:

**Đã đo được (17-18/08, strict regex, không phải suy đoán):**
```
tool_results.lookup_transaction   4 giá trị dạng SĐT, CẢ 4 thuộc bộ seed users → không phải thật
investigation_logs, NGÀY 15/08    0 dòng có SĐT hợp lệ (con số "5 dòng" ban đầu là báo động giả,
                                   RÚT lại: khớp trúng mảnh trans_id "TXN2026...", không phải SĐT)
investigation_logs, NGÀY 17/08    1 dòng có chuỗi dạng SĐT, đuôi …678, KHÔNG thuộc bộ seed
                                   → chưa xác định thật hay bịa (câu hỏi có/không, 1 dòng, chưa ai trả lời)
```

**Bốn giới hạn khiến kết quả trên KHÔNG đủ để trả lời có/không (nguyên văn từ hồ sơ gốc, vẫn đúng):**
1. Chưa xác nhận ngăn xếp nào thực sự phục vụ `app.adaptivealgo.uk` lúc 14h-15h ngày 15/08 — nếu demo
   chạy trên ngăn khác, toàn bộ phép đo trên rỗng.
2. Chỉ đo được SĐT bằng regex — KHÔNG đo được HỌ TÊN thật (cần lớp NER, chưa từng chạy).
3. 6 tin nhắn ngày 15/08 (3 từ khách) — **MÃ HOÁ** (`messages.content`), chưa ai đọc/giải mã.
4. 3 lời khai plaintext ngày 15/08 (`create_ticket`, LOG-eca112966417 · LOG-452190dde2e3 ·
   LOG-59b87146009a) — đã kiểm KHÔNG có chuỗi dạng SĐT, nhưng CHƯA kiểm có TÊN NGƯỜI thật không.

**🔴 SỬA 30/08 — "bằng chứng có thể đã mất" (bản trước, cùng ngày) là KẾT LUẬN VỘI, dừng tìm quá
sớm.** PO tự điều tra sâu hơn, tôi đã **tự kiểm độc lập lại từng số** (không chép nguyên báo cáo):

```
[ĐO 30/08, tự chạy] docker volume ls | grep postgres → 9 volume postgres CÒN SỐNG:
  fin05-dot-otp · fin05-final · fin05-po-demo · fin05-po-test · fin05-qa-stripe ·
  fin05-sach · fin05-uxui-tmp · fin05do · fin05ttl
  (không có volume tên TRẦN "fin05_postgres_data" — đúng phần này tôi nói trước — nhưng
  SAI ở chỗ suy tiếp "nên bằng chứng có thể mất": còn 9 volume khác chưa ai xem trong đó)

[ĐO 30/08, tự chạy] logs/access.log (repo root, KHÔNG phải trong volume nào) → 39.204 dòng,
  ts từ 2026-08-15T06:59:45 tới 2026-08-27T10:14:12, trường "ip": CHỈ {"testclient", "127.0.0.1"}
  (0 IP ngoài), trường "identity": CHỈ 10 giá trị, toàn mẫu seed
  (USR-A/USR-B/USR-SUP/USR-CSKH/USR-TEST/USR-PA-TEST/USR-0119/USR-0201/anonymous/invalid-token)
```

**Kết luận đúng cho khoảng 15/08→27/08, trên máy dev này:** không có dấu hiệu người dùng thật/IP
ngoài trong log truy cập — nhưng đây là MỘT nguồn, không phải bằng chứng phủ định tuyệt đối. Ba giới
hạn phải đi kèm con số này, không được rơi rụng khi trích lại:
1. Log chỉ phủ **15/08 → 27/08** — có khoảng trống từ 27/08 tới hôm nay 30/08 chưa đo.
2. Chỉ đo được **máy dev này** — KHÔNG phải production (`app.adaptivealgo.uk`, máy Windows PO tại
   nhà) — log production PO thật mới xem được, đã hỏi họ, chưa có kết quả.
3. Một nguồn log (access log tầng HTTP) — chưa đối chiếu chéo với nội dung `investigation_logs`/
   `tool_results` bên trong 9 volume còn sống (danh tính seed ở tầng HTTP không loại trừ khả năng ai
   đó gõ SĐT/tên thật VÀO NỘI DUNG một request dùng danh tính seed để đăng nhập — hai lớp khác nhau).

**🔴 PO BÁC đề xuất "giả định thận trọng đồng hồ chạy từ 15/08" của tôi (bản trước) — lý do đúng, tôi
chấp nhận sửa:** Đ.2.1 định nghĩa dữ liệu cá nhân là dữ liệu xác định MỘT CON NGƯỜI CỤ THỂ. Chạy trên
dữ liệu seed (không phản ánh người thật) không khởi động đồng hồ nào. **Khai một ngày PHỎNG ĐOÁN vào
hồ sơ nộp cơ quan nhà nước không phải sự thận trọng — đó là khai sai**, một loại lỗi khác hẳn "chưa
biết". Bản năng của tôi (thà giả định sớm hơn còn hơn bỏ sót) đúng tinh thần nhưng SAI hướng áp dụng
ở một hồ sơ pháp lý chính thức — khác với một runbook nội bộ (C3) nơi "thận trọng hơn luật đòi hỏi"
không gây hại.

**⟹ Sửa hành động cụ thể: ô "ngày xử lý dữ liệu cá nhân thật đầu tiên" trong khung DPIA — ĐỂ TRỐNG**,
không điền ngày phỏng đoán. Ghi chú: "chờ xác nhận log production `app.adaptivealgo.uk`, chỉ PO thật
xem được." Nếu log production (khi có) cũng cho kết quả tương tự (0 IP ngoài/0 danh tính thật) VÀ
loại trừ được khả năng seed-login-nhưng-nội-dung-thật (giới hạn 3 ở trên), đồng hồ Đ.21.1 **chưa
chạy** — đó sẽ là kết luận có căn cứ, không phải giả định.

🔴 **SỬA — giới hạn thứ tư đã được XÁC ĐỊNH, không còn "chưa ai trả lời":** Lead đối chiếu
`docker-compose.yml:194` (`- logs_data:/app/logs`, khai ở `:376` trong khối `volumes:`) — đây là
**NAMED VOLUME**, không `bind-mount` ra `./logs` ở host. Tôi tự kiểm lại: đúng, dòng 194 và 376 khớp
nguyên văn; `.gitignore:52,76` có `logs/` và `logs/*.log` (khớp việc thư mục không được commit);
`lsof logs/access.log` không có tiến trình nào đang giữ mở (khớp mtime tĩnh 27/08 17:14, không có
ai ghi hôm nay).

⟹ **`logs/access.log` ở gốc repo KHÔNG THỂ đến từ bất kỳ container Docker nào** (kể cả ngăn `fin05`
đã mất, kể cả `po-demo`/`qa-stripe` đang sống) — container ghi vào `/app/logs` bên trong volume
riêng của nó, không bao giờ chạm đường dẫn này. File này chỉ có thể sinh ra từ một tiến trình
`uvicorn`/python chạy **TRỰC TIẾP trên máy Mac này, ngoài Docker**, có cwd là gốc repo.

**⟹ Phạm vi thật của bằng chứng ở mục này còn HẸP HƠN cả ba giới hạn đã ghi trước đó**: nó không nói
được gì về BẤT KỲ ngăn Docker nào (kể cả ngăn đã mất `fin05`), và càng không nói được gì về
production Windows. Nó CHỈ trả lời đúng một câu hẹp: *"tiến trình chạy trực tiếp trên máy Mac này,
15-27/08, có phục vụ IP ngoài không — không."* Không phải bằng chứng cho "ngăn nào phục vụ demo" —
câu Ⓐ (ngăn nào phục vụ domain công khai lúc demo 15/08) **vẫn hoàn toàn mở**, chưa được trả lời dù
gián tiếp.

## 0c. 🟢 Mở rộng sang toàn bộ 9 volume `logs_data` còn sống — tự đo, không chỉ chép báo cáo

PO đọc read-only cả 9 volume `logs_data` (không đụng/dựng lại gì) và báo qua Lead. **Tôi tự đo lại
độc lập, không chép nguyên số** — mount read-only từng volume qua container tạm (`docker run --rm -v
<volume>:/logs:ro`), không sửa gì:

```
[TỰ ĐO 30/08, đọc trực tiếp cả 9 volume, không phải chép báo cáo]
fin05ttl        16/08→30/08   IP: 127.0.0.1, 172.20.0.6                        — 0 IP công cộng
fin05do         17/08→30/08   IP: 127.0.0.1                                    — 0 IP công cộng
fin05-dot-otp   25/08→30/08   IP: 127.0.0.1, 172.24.0.6                        — 0 IP công cộng
fin05-final     20/08→25/08   IP: 127.0.0.1, 172.22.0.5                        — 0 IP công cộng
fin05-qa-stripe 26/08→30/08   IP: 127.0.0.1, 172.25.0.6, testclient            — 0 IP công cộng
fin05-sach      25/08→30/08   IP: 127.0.0.1, 172.19.0.6, testclient            — 0 IP công cộng
fin05-po-demo   26/08→30/08   IP: 127.0.0.1, 172.26.0.6                        — 0 IP công cộng
fin05-po-test   24/08→25/08   IP: 127.0.0.1, 172.23.0.5, testclient            — 0 IP công cộng
fin05-uxui-tmp  25/08→27/08   IP: 127.0.0.1, 172.25-27.0.6                     — 0 IP công cộng
```

Toàn bộ IP thuộc `127.0.0.1`/`testclient`/dải `172.16-31.x` (dải bridge nội bộ Docker theo RFC 1918,
không phải người dùng ngoài). **Đối chiếu identity trên cả 9 volume** (tự đo thêm, PO không nêu số
này): toàn bộ chỉ gồm mẫu `USR-####`/`USR-XX`/`anonymous`/`invalid-token` — không có định danh lạ nào
ngoài mẫu seed. Khớp đúng báo cáo của PO ở mọi con số kiểm chéo được (ngày bắt đầu/kết thúc mỗi ngăn).

**⟹ Kết luận mở rộng: toàn bộ máy Mac này — host (§0b) + 9 ngăn Docker (mục này) — khoảng 15/08→30/08
hôm nay, 0 lượt truy cập từ IP công cộng.** Đây là bằng chứng RỘNG hơn nhiều so với bản trước.

⚠️ **Giới hạn PO tự nhấn mạnh, ghi đúng — KHÔNG được viết như thể đã đọc được ngăn `fin05` đã mất:**
ngăn `fin05` trần (mất CSDL 27/08, §0b/C3) **KHÔNG còn volume log riêng** — phần đó thật sự đã mất.
Khoảng trống của nó được lấp GIÁN TIẾP bằng CHỒNG LẤN THỜI GIAN: `fin05ttl` sống từ 16/08 và log host
sống từ 15/08 — nếu không có gì bất thường trên các nguồn CHỒNG LẤN THỜI GIAN với `fin05`, đó là bằng
chứng gián tiếp hợp lý, **không phải bằng chứng trực tiếp về chính ngăn `fin05`**. Hai loại bằng chứng
khác nhau, không được lẫn khi viết vào hồ sơ.

**Giới hạn CÒN LẠI, chỉ còn MỘT:** log production Windows qua Cloudflare Tunnel — ngoài tầm mọi phiên
Claude ở đây (CLAUDE.md: production chỉ đọc, và ngay cả "chỉ đọc" cũng cần con người có quyền truy cập
máy Windows đó, không phải bất kỳ phiên nào trong đội). Câu Ⓐ (ngăn Docker nào, nếu có, từng phục vụ
domain công khai lúc demo 15/08) **vẫn hoàn toàn mở** — mở rộng bằng chứng ở trên không tự động trả
lời câu này, vì domain công khai có thể được phục vụ bởi một cấu hình khác hẳn (production thật là máy
Windows PO tại nhà, không phải máy Mac này — xem `docs/STATE.md` deploy production).

**Kết luận tổng thể của §0 không đổi:** ô "ngày xử lý dữ liệu cá nhân thật đầu tiên" — **VẪN ĐỂ
TRỐNG**, chỉ còn chờ MỘT nguồn duy nhất (log production Windows), thay vì nhiều nguồn rời rạc như bản
trước. Bằng chứng vững hơn hẳn, kết luận hành động không đổi.

## 0d. 🟢 PO chốt — HAI mốc khác nhau, đừng gộp làm một khi đọc phần trên

PO chốt qua Lead, cần tách rõ vì dễ đọc nhầm sau khi lướt §0b/§0c ở trên:

| | Mốc **NỘI BỘ** — lập kế hoạch | Ô **HỒ SƠ CHÍNH THỨC** — nộp cơ quan nhà nước |
|---|---|---|
| Giá trị | **15/08 + 60 ngày = 14/10/2026, còn 45 ngày** (tính từ 30/08) | **ĐỂ TRỐNG** |
| Dùng để | Đội tự thúc mình — trả lời "còn bao lâu phải xong nếu xấu nhất" | Ngày ĐO ĐƯỢC THẬT, không suy đoán |
| Nguồn | Ngày demo mentor sớm nhất được ghi nhận (giả định XẤU NHẤT có căn cứ, không phải phỏng đoán tuỳ ý) | Log production Windows (chưa có) |
| Vì sao chọn 15/08 dù bằng chứng máy Mac cho thấy 0 IP ngoài | **PO tin mốc này gần như chắc chắn SỚM HƠN sự thật** — an toàn theo hướng có lợi cho đội: deadline giả định CĂNG hơn deadline thật, không LỎNG hơn. Lập kế hoạch trên mốc căng hơn không gây hại; lập kế hoạch trên mốc lỏng hơn mới nguy hiểm. | — |

**Không mâu thuẫn với việc PO trước đó bác đề xuất "giả định 15/08" của tôi (§0b):** PO bác việc
**KHAI** 15/08 với cơ quan nhà nước (đó là khai sai nếu chưa đo được thật). PO **KHÔNG** bác việc
**DÙNG** 15/08 để đội tự lên kế hoạch nội bộ — đây là hai hành động khác nhau, một hướng RA NGOÀI
(hồ sơ chính thức, cần sự thật) và một hướng VÀO TRONG (kế hoạch làm việc, giả định xấu nhất là hợp
lý). Bản C4 trước dễ đọc gộp thành một vì cả hai đều nhắc tới "15/08" — mục này tách tường minh.

**Áp dụng cho §6 (trình PO):** khung DPIA nên **hoàn thành xong TRƯỚC 14/10/2026** (mốc nội bộ) dù ô
ngày trong hồ sơ vẫn để trống tới lúc đó — làm khung sẵn không phải chờ biết ngày mới bắt đầu.

## 1. Cấu trúc hồ sơ — 4 trường bắt buộc, đã điền từ vật liệu D25

*(Theo đúng cấu trúc D25 tự đặt ra: loại dữ liệu · bên nhận · nơi nhận · biện pháp bảo vệ — cấu trúc
này không phụ thuộc số điều luật, chỉ phụ thuộc BẢN CHẤT việc chuyển dữ liệu, nên giữ nguyên được.)*

### 1.1 Bên nhận — bốn đường, hai tài phán (từ D25 §1)

| Đường | Đích | Mục đích | Vẫn đúng 30/08? |
|---|---|---|---|
| A — chat | Alibaba Cloud Model Studio (`dashscope-intl`, Singapore lưu / xử lý toàn cầu ngoài TQ đại lục) | Agent trả lời khách | ✅ [ĐO 30/08] `LLM_BASE_URL` bể model DashScope vẫn đúng, không đổi từ 17/08 |
| B — embedding | OpenAI (`text-embedding-3-small`) | Nhúng tài liệu + truy vấn RAG | ✅ không đổi (tách cố ý khỏi chat, xem `project-knowledge/07`) |
| C — trọng tài eval | OpenAI | Chấm điểm | ✅ không đổi, khoá ghim literal |
| D — kẻ tấn công giả lập (eval) | OpenAI | Test đối kháng | ✅ không đổi |

### 1.2 Loại dữ liệu thực sự rời hạ tầng (từ D25 §2, không đổi)

- 🔴 **Văn bản khách gõ (mô tả khiếu nại, tin chat) — RỜI NGUYÊN VĂN, không che được.** Lý do kỹ
  thuật: che sẽ phá nghĩa câu (đo được: S-01 chặn nhầm 40% văn bản nghiệp vụ tiếng Việt). Đây là
  **quyết định thiết kế có ý thức**, phải ghi vào hồ sơ như vậy — không phải thiếu sót.
- 🔴 **Chứa dữ liệu NGƯỜI THỨ BA chưa từng đồng ý** — ca điển hình "chuyển nhầm cho anh X, sđt 09…".
  Đây là **câu hỏi nặng nhất trong toàn hồ sơ**, không đổi theo nhà cung cấp.
- ✅ Họ tên/SĐT/số TK trong KẾT QUẢ TOOL — đã che trước khi vào LLM (`_scrub_pii_cho_llm`).
- Số tiền/mã GD/thời điểm/trạng thái — rời có chủ đích (ràng buộc cứng #3: cấm bịa số liệu, agent
  cần dữ liệu thật để trích dẫn).

### 1.3 Nơi nhận — không phải "Singapore" đơn giản (từ D25 §1, không đổi)

Lưu trữ tại Singapore (`ap-southeast-1`); **xử lý** tại node toàn cầu ngoài Trung Quốc đại lục. Hồ sơ
chính thức phải ghi cả hai vế — vế xử lý mới là vế luật hỏi.

### 1.4 Biện pháp bảo vệ đang có (từ D25 §3, không đổi)

Che PII trong kết quả tool trước LLM · không đưa tên khách vào system prompt · mã hoá at-rest
(`EncryptedText`) · cách ly khoá theo nhà cung cấp (`_khoa_cho_nha_cung_cap`) · mã hoá đường truyền +
SOC 2 (Alibaba công bố) · cam kết không dùng dữ liệu huấn luyện (mức TRANG TÀI LIỆU, chưa mức HỢP
ĐỒNG — D25 §3 đã tự khai giới hạn này).

## 2. Ba khoảng trống chặn việc KÝ chính thức (từ D25 §4, xác nhận lại 30/08 — chưa đổi)

1. Văn bản khách gõ không che được, kèm dữ liệu bên thứ ba (mục 1.2).
2. Bản ghi phía Alibaba (Model monitoring — ghi input/output 30 ngày) — tính năng bật bằng một nút
   console, không diff nào của đội nhìn thấy được. **Việc chưa làm:** kiểm công tắc đó trên console
   thật + ghi ngày kiểm. Không có gì trong 13 ngày qua (17/08→30/08) cho thấy việc này đã làm.
3. Phía OpenAI — chưa kiểm tài khoản có bật lưu nội dung yêu cầu (stored completions/org logging).

## 2a. 🟢 SỬA 31/08 — retention KHÔNG phải "chưa có quyết định nào", đã có HAI ADR ký, chưa code

**Đính chính việc tôi tự viết trước đó** (bản 27/08 kế thừa + 30/08 của tôi): câu "không có ADR nào
quyết định về xoá dữ liệu" là **KHÔNG CHÍNH XÁC**. Đọc nốt toàn bộ `docs/DECISIONS.md` (31/08, quét
từ khoá đầy đủ + đọc từng chỗ khớp, không chỉ lướt ADR-040→055 như bản 27/08 tự khai giới hạn) tìm
ra:

- **ADR-025 Quyết định 3** (15/08, **ĐÃ KÝ TOÀN BỘ**): hồ sơ khiếu nại (transcript + description +
  note + agent_note) giữ **5 NĂM kể từ ticket đóng**, hết hạn thì xoá hoặc ẩn danh hoá không đảo
  ngược. Căn cứ lấy MAX nhiều chế độ (VN PCTT rửa tiền · NĐ 13/2023 giới hạn lưu trữ · EU AMLD/MiFID
  II · US Reg E) — **[TỰ SỬA 31/08]** vế "NĐ 13/2023" là TRÍCH NGUYÊN VĂN từ chính ADR-025 (15/08),
  đã hết hiệu lực NGAY TỪ LÚC ADR được viết (Luật 91/2025 hiệu lực 01/01/2026, trước đó). Không đổi
  con số 5 năm (vẫn lấy MAX nhiều chế độ khác), nhưng nếu tư vấn pháp lý thật xác nhận số này, cần
  đối chiếu lại nguyên tắc giới hạn lưu trữ theo Luật 91/2025 (nếu có điều khoản tương đương), không
  dựa vào NĐ 13/2023 nữa. Cờ giữ nguyên: **con số cần tư vấn pháp lý thật xác nhận trước production**.
  Đã tự cảnh báo KHÔNG dùng crypto-shredding (khoá mã hoá dùng chung, huỷ khoá phá luôn dữ liệu khác)
  — xoá theo retention phải là xoá dòng thật.
- **ADR-045b** (24/08, **PO thật quyết trực tiếp**): lịch sử hội thoại (LangGraph checkpoint) giữ
  **90 NGÀY** rồi xoá.
- **[ĐO 31/08]** `grep -rl "retention" src/ scripts/` → **không tìm thấy job xoá theo lịch nào đã
  code** cho cả hai con số trên. Hai quyết định đã KÝ nhưng CHƯA THỰC THI.

**Phân biệt quan trọng, đừng gộp khi viết hồ sơ:**
```
RETENTION (đã quyết, chưa code)     ≠     ROUTE TỰ PHỤC VỤ (chưa quyết, chưa code)
"hệ thống TỰ xoá sau N ngày/năm"          "KHÁCH tự bấm xuất/xoá dữ liệu của mình bất cứ lúc nào"
= nghĩa vụ Đ.5(1)(e)/storage limitation   = nghĩa vụ Đ.4.1.d/Đ.15-17 GDPR (quyền chủ thể dữ liệu)
```
Kết luận GAP ở mục 2b dưới đây (route tự phục vụ) **vẫn đứng vững, không đổi** — nhưng mô tả trước
đây ("không có quyết định nào về xoá dữ liệu") là quá rộng, nay đã chính xác hơn: có quyết định
RETENTION TỰ ĐỘNG, không có QUYỀN TỰ PHỤC VỤ theo yêu cầu khách. Hồ sơ DPIA nên trích cả ADR-025 Q3
và ADR-045b vào phần "biện pháp bảo vệ" (mục 1.4) — đây là bằng chứng có sẵn, không cần dựng mới.

## 2b. Route xoá/xuất dữ liệu khách hàng (GDPR Đ.15/17 · PDPL 2025) — 🟡 CẬP NHẬT 30/08, PO đã quyết

**Không còn là câu hỏi mở.** Trạng thái trước: bản 27/08 xác nhận GAP (không có route
`GET /users/me/data-export` / `DELETE /users/me` trong `contracts/authority-matrix.yaml`, không có
ADR nào quyết định hoãn) nhưng chưa rõ ưu tiên. **PO đã quyết 30/08 (qua Lead):**

- **KHÔNG vào backlog code của đợt đo benchmark hiện tại** — thêm route mới giữa lượt đo sẽ làm hỏng
  phép đo (đúng nguyên tắc "đóng băng tính năng" của kế hoạch Nền Vững §1).
- **NHƯNG lên backlog có ưu tiên** (không còn "chưa biết có cần không") — vì Luật 91/2025/QH15 đã
  hiệu lực **8 tháng** (từ 01/01/2026) và quyền truy cập/xoá dữ liệu là **quyền luật định**, không
  phải tính năng tuỳ chọn.

⚠️ **Khai rõ giới hạn của chính mục này:** Lead có nhắc tôi "giữ nguyên phân biệt
retention-vs-self-service-export" như một việc tôi đã tách trước đó — **tôi kiểm lại và KHÔNG tìm
thấy tôi từng viết phân biệt đó** (không có trong C4 này, không có trong bản 27/08 hay bản 30/08 của
tôi). Có thể đây là việc của `p-226-1c` mà Lead gộp nhắc, hoặc một hiểu nhầm quy kết. Tôi không nhận
lại phân tích tôi chưa làm — nếu cần phân biệt retention (chính sách LƯU dữ liệu nội bộ, vd
`EncryptedText`/mã hoá at-rest, đã ghi ở mục 1.4) khỏi self-service export/erasure (route KHÁCH tự
kích hoạt), người giữ bản phân tích gốc (`p-226-1c`?) nên xác nhận trực tiếp, tôi không tự suy diễn
thay.

**Việc thuộc scope tôi (security) đã làm ở mục này:** xác nhận lại GAP còn tồn tại + gắn mốc pháp lý
(Luật 91/2025/QH15) làm áp lực thời gian. **Việc KHÔNG thuộc scope tôi:** thiết kế route/API cụ thể
(việc `tech-lead`), quyết định đưa vào sprint nào (đã có, PO quyết ở trên).

🔴 **NÂNG MỨC NGHIÊM TRỌNG 30/08** — theo báo cáo PO đọc toàn văn, chuyển qua Lead (tôi chưa tự đọc
bản gốc): **Đ.4.1.d** xác nhận quyền xoá/xuất dữ liệu là **quyền luật định** của chủ thể dữ liệu
(không phải tính năng "nice-to-have" của sản phẩm). Nặng hơn: **Đ.23.3.c** — theo báo cáo, việc
KHÔNG đảm bảo được quyền đó **tự nó là một sự kiện phải thông báo** (breach-notifiable event), không
chỉ là "thiếu tính năng". Nếu đúng, GAP ở mục này không còn nằm gọn trong khung "backlog ưu tiên
trung bình" — nó có khả năng kéo theo nghĩa vụ Bước 4 của C3 (thông báo cơ quan chuyên trách trong
72 giờ) NẾU có yêu cầu xoá/xuất dữ liệu thật từ một chủ thể dữ liệu mà hệ thống không đáp ứng được.
**Chưa tự tôi xác nhận Đ.23.3.c** — cần đọc toàn văn trước khi dùng khẳng định này trong hồ sơ ký
chính thức, nhưng đủ nghiêm trọng để KHÔNG chờ tới lúc đó mới cảnh báo Lead/PO.

## 3. Điều mới — tình huống pháp lý đã đổi so với D25 (viết 17/08 theo NĐ 13/2023)

- **Yêu cầu về DPO** (Nhân sự bảo vệ dữ liệu) — theo tóm tắt WebSearch 30/08, NĐ 356/2025/NĐ-CP có
  "quy định mới về chức năng, nhiệm vụ của DPO". D25 (viết trước khi luật mới có hiệu lực) **không
  nhắc tới yêu cầu này**. **Cần xác nhận: dự án ở quy mô hiện tại (1 người + nhiều phiên AI, chưa có
  dữ liệu khách thật) có thuộc diện bắt buộc chỉ định DPO không** — câu hỏi này KHÔNG tự trả lời được
  từ đọc code, thuộc thẩm quyền pháp lý, đưa vào hồ sơ như một mục cần xác nhận trước khi ký.
- **Cơ chế phối hợp kiểm tra/thanh tra của Cục An ninh mạng (A05)** — theo tóm tắt, đây là điểm mới
  của NĐ 356/2025 so với NĐ 13/2023. Không ảnh hưởng nội dung kỹ thuật của hồ sơ, nhưng đáng ghi vào
  phần "cơ quan có thẩm quyền" của hồ sơ chính thức (khác gì so với cơ quan thẩm quyền cũ, nếu có).
- **[CẬP NHẬT 30/08, theo báo cáo PO đọc toàn văn]** **Đ.38.2** — miễn trừ 5 năm cho doanh nghiệp nhỏ
  (Đ.21/Đ.22/khoản 2 Đ.33) **CÓ THẬT** nhưng **KHÔNG áp dụng chắc chắn cho FIN-05** — mệnh đề loại
  trừ: không áp dụng nếu "trực tiếp xử lý dữ liệu nhạy cảm HOẶC xử lý dữ liệu của số lượng lớn chủ
  thể". Xem §0 — phụ thuộc Đ.2.3 (danh mục dữ liệu nhạy cảm, chưa có toàn văn NĐ 356/2025). **Không
  đưa miễn trừ này vào hồ sơ như một kết luận đã chốt** — chỉ ghi là một khả năng cần Đ.2.3 xác nhận.

## 4. Không đổi so với D25 §5 — vẫn đúng, nhắc lại vì dễ hiểu nhầm theo thời gian

**Nghĩa vụ đánh giá tác động KHÔNG do việc đổi luật tạo ra**, cũng **không do việc đổi nhà cung cấp
LLM tạo ra**. Hệ thống đã gửi văn bản khách ra nước ngoài từ khi còn dùng `gpt-4o-mini`. Đổi luật chỉ
đổi **CĂN CỨ TRÍCH DẪN**, không đổi bản chất nghĩa vụ đã tồn tại từ trước.

🔴 **SỬA 30/08 (hai lượt) — câu gốc bên dưới bị khẳng định vội, rồi lượt sửa đầu lại giả định vội
theo hướng ngược lại. Bản ĐÚNG là lượt sửa thứ hai (§0b, cập nhật sau cùng):** ~~"Mốc kích hoạt vẫn
là 'dữ liệu khách hàng THẬT đầu tiên' — chưa xảy ra tính tới 30/08"~~ (SAI — đây là câu hỏi cần đo,
không phải suy từ "chưa deploy công khai"). ~~"Nên giả định thận trọng đồng hồ đã chạy từ 15/08"~~
(CŨNG SAI — Đ.2.1 chỉ tính dữ liệu xác định người thật; khai một ngày phỏng đoán vào hồ sơ nhà nước
là khai sai, không phải thận trọng — xem §0b).

**Kết luận đúng hiện tại (30/08, sau khi đối chiếu log thật):** trên máy dev, 15/08→27/08, log HTTP
39.204 dòng không cho thấy IP ngoài hay danh tính thật nào — bằng chứng NGHIÊNG về "chưa có dữ liệu
cá nhân thật ở giai đoạn này", nhưng CHƯA ĐỦ để kết luận dứt điểm (ba giới hạn ở §0b: khoảng trống
27/08→30/08, không phủ production, chưa loại trừ nội dung-thật-dưới-danh-tính-seed). **Ô "ngày xử lý
đầu tiên" của hồ sơ: ĐỂ TRỐNG, không suy đoán theo bất kỳ hướng nào**, chờ log production.

## 5. Điều tôi (security) KHÔNG kết luận — giữ nguyên từ D25 §6

- Không quyết định có nộp hồ sơ chính thức hay không — đó là mục 6, §4 kế hoạch Nền Vững, thuộc PO
  thật, KHÔNG hỏi lại lần 3.
- Không phán quyết nhà cung cấp nào an toàn hơn.
- Không đọc *Product Terms of Service* cấp hợp đồng của Alibaba/OpenAI.
- Không đánh giá chế độ pháp lý nơi nhận (Singapore) — thuộc người có thẩm quyền pháp lý.
- **Mới, bổ sung 30/08:** không đọc toàn văn Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP — số điều/mục
  trong khung này ở dạng "tương đương", chưa phải trích dẫn chính xác. Không đọc yêu cầu DPO đủ sâu
  để trả lời có bắt buộc hay không cho quy mô dự án hiện tại.

## 6. Trình cho PO — dữ kiện kèm hệ quả, không hỏi lại câu hỏi (đúng luật CLAUDE.md §5)

🔴 **SỬA 30/08 (hai lượt, giữ cả hai làm lịch sử — Luật P):** bản gốc khẳng định "dữ liệu FIN-05
thuộc nhóm nhạy cảm" như đã chốt — SAI (Đ.2.3 chưa xác nhận). Lượt sửa đầu khẳng định "đồng hồ có
thể đã chạy từ 15/08" như một kết luận nên dùng — CŨNG SAI, PO bác đúng lý do (§0b): đó là phỏng đoán
đưa vào hồ sơ nhà nước, không phải thận trọng. Bản dưới đây là lượt sửa THỨ HAI, khớp §0b bản cuối.

**Trạng thái đúng hiện tại:** mốc kích hoạt Đ.21.1 **CHƯA XÁC ĐỊNH** (không phải "có thể đã chạy",
cũng không phải "chắc chắn chưa chạy") — bằng chứng trên máy dev nghiêng về "chưa có dữ liệu thật"
nhưng chưa đủ dứt điểm, chờ log production (§0b). Vì vậy: **nếu hồ sơ chính thức KHÔNG được chuẩn bị
sẵn trong lúc chờ xác nhận**, và log production sau đó cho thấy đồng hồ ĐÃ chạy từ 15/08, tổ chức sẽ
phát hiện mình đã trễ hạn 60 ngày ngay tại thời điểm phát hiện — không còn thời gian chuẩn bị. Đây là
lý do làm khung TRƯỚC (mục 1, đã có) vẫn hợp lý dù chưa biết ngày kích hoạt, **miễn là không điền
ngày phỏng đoán vào khung đó**. Mức nghiêm trọng cụ thể nếu đồng hồ đã chạy (có thuộc nhóm chế tài
nặng hơn cho "dữ liệu nhạy cảm" hay không) vẫn phụ thuộc Đ.2.3, chưa xác nhận được — nhưng rủi ro
Đ.23.3.c (§2b, chưa tự tôi xác nhận) tồn tại độc lập với câu hỏi ngày kích hoạt.

**Việc cụ thể, không phải câu hỏi lại:** (a) log production `app.adaptivealgo.uk` — chỉ PO thật xem
được, đã hỏi, chờ kết quả; (b) đọc toàn văn xác nhận Đ.2.3 (mục 0); (c) quyết định DPO (mục 3); (d)
xác nhận `logs/access.log` (đo ở §0b) thuộc ngăn xếp nào, có phải ngăn phục vụ domain công khai lúc
demo hay chỉ log cục bộ trên máy dev — giới hạn thứ tư mới phát hiện ở §0b, chưa ai trả lời.
