# ĐỢT 2 TIẾNG — 4 VIỆC, HẠN CỨNG 24:00 HÔM NAY

> **Từ:** phiên PO · **Cho:** Lead → Coder · QA/QC · Review · Bảo mật
> **Viết lúc:** 01/09 20:40 · **Hạn cứng:** 24:00 (sau đó không cập nhật code nữa)
> **Cửa sổ giao việc:** 20:45 → 22:45 · **đệm 75 phút** trước hạn — đệm này KHÔNG phải
> để làm thêm việc, nó là chỗ cho một lần dựng lại hỏng.
>
> 🔴 **PO thật đã GỠ ĐÓNG BĂNG buổi quay.** Sáu lệnh cấm ở `STATE.md` §0-TER về
> *rebuild ảnh* · *sửa `src/`* · *dựng lại caddy `qa-stripe`* **KHÔNG còn hiệu lực**.
> Các lệnh cấm còn lại (`down -v`, `git add .`, tắt `dot-otp`) **VẪN GIỮ**.

---

## 0. Đọc một phút — thứ đã đổi so với mọi tài liệu trước

Ba việc **nhẹ hơn** hồ sơ mô tả, một việc **là đường găng**. Tất cả đều [ĐO 20:30-20:40]:

| | hồ sơ cũ nói | **đo thật tối nay** |
|---|---|---|
| ② header | *"chờ merge `db8d460`"* | `db8d460` **chỉ là tài liệu đề xuất**, không đụng `Caddyfile`. Nhưng `Caddyfile` là **MOUNT** (`./Caddyfile:/etc/caddy/Caddyfile:ro`, ảnh là `caddy:2-alpine` chính chủ) ⟹ **sửa tệp + reload, KHÔNG dựng lại ảnh** |
| ⑤ LAN | *"vá tốn một lần dựng lại caddy"* | **Nguồn ĐÃ VÁ RỒI** (`docker-compose.yml:292` `${CADDY_BIND_HOST:-127.0.0.1}`). Container thì tạo 6 ngày trước, **trước** bản vá ⟹ chỉ cần **tạo lại container**, không dựng ảnh |
| ① RAG | *"RAG không lọc ngưỡng"* | Đường ống **đã đủ**: `store.py:256` **đã trả `distance`** · `search.py:81` **lấy rồi VỨT** (`_distance`) · `search.py:95` `status="not_found" if not results` **đã đúng sẵn**. ⟹ code sửa ~5 dòng |
| ④ OTP git | — | Không đụng `src/`, không dựng lại gì |

🔴 **Nhưng ① vẫn là đường găng, và không phải vì code.** Code 5 dòng; thứ đắt là **con số
ngưỡng** — không ai được đoán một ngưỡng khoảng cách. Và `src/` **không mount** vào
`po-demo` (`docker inspect` chỉ thấy `chroma_data`, `logs_data`) ⟹ **bắt buộc dựng lại ảnh backend**.

**⟹ Luật xếp lịch của đợt này: khởi động ① NGAY phút đầu, làm ②④⑤ TRONG LÚC nó chạy.**
Dựng lại ảnh **đúng MỘT lần**, ở cuối, đã chứa ①.

---

## 1. 🔴 BỐN THỨ ĐANG CHẶN — và cần gì để gỡ

| # | chặn cái gì | ai gỡ được | mất bao lâu | gỡ bằng cách nào |
|---|---|---|---|---|
| **B1** | **Chưa có giá trị ngưỡng cho ①.** Đây là chặn THẬT duy nhất về kỹ thuật. Đoán một ngưỡng = thay lỗi "luôn trả kết quả" bằng lỗi "im lặng nuốt kết quả đúng" — tệ hơn, vì nó **im**. | Coder + QA/QC | **~25 phút** | Đo phân bố `distance` trên 2 nhóm truy vấn (khớp thật / rác), chọn ngưỡng nằm giữa hai cụm. §2 làn A có lệnh sẵn |
| **B2** | **`QWEN_API_KEY` chỉ PO thật thu hồi được** (console DashScope, không có API) | **PO thật — không uỷ quyền được** | ~5 phút | Làm NGAY phút đầu, song song. Không việc nào phụ thuộc nó ⟹ đừng để nó nằm cuối |
| **B3** | **Cây làm việc dùng chung, phiên khác đang đụng git** — đo được: một phiên `git pull` fast-forward `main` lúc **20:31:04**, giữa lúc tôi đang commit | Lead | 0 phút, chỉ cần ra luật | **MỘT NGƯỜI COMMIT.** Ba vai kia sửa tệp rồi báo Lead. 4 vai commit song song trong 2h trên cây chung **chắc chắn** đụng nhau |
| **B4** | **Dựng lại ảnh cho ngăn nào?** Mỗi lần dựng tốn thời gian thật, không có chỗ cho hai lần | Lead chốt, tôi khuyến nghị | 0 phút | **Chỉ `po-demo`** (ngăn sẽ thành live demo). `qa-stripe` nay đã tự do nhưng **không cần** — để nguyên làm mốc đối chứng |

**Không còn chặn nào khác.** Ba thứ tôi tưởng là chặn thì đo ra không phải: Caddyfile mount
(không cần dựng ảnh) · `caddy_data` là volume có tên (tạo lại container **không mất cert**) ·
nhánh `not_found` đã có sẵn (① không cần đụng UI).

---

## 2. BỐN LÀN SONG SONG — mốc giờ, không phải thứ tự

```
20:45 ─────────────────────────────────────────────────── 22:45
 A ①RAG  [đo ngưỡng 25']─[code 15']─[test 20']──────[DỰNG LẠI 20']─[nghiệm 15']
 B ②hdr           [sửa Caddyfile 10']─[reload+curl 10']
 C ④git           [rm --cached + ignore + testIgnore 25']
 D ⑤LAN                    [tạo lại 3 caddy 15']─[đo lại port 5']
 PO  [thu hồi khoá 5']
                                                  ↑
                                    ĐIỂM HẸN 21:45 — B/C/D phải xong
                                    trước khi A dựng lại ảnh
```

🔴 **ĐIỂM HẸN 21:45 là ràng buộc cứng của lịch này.** Dựng lại ảnh là thao tác duy nhất
không hoãn được và không chạy song song với việc sửa tệp. Làn nào chưa xong lúc 21:45 thì
**cắt phạm vi làn đó**, không lùi giờ dựng.

---

### LÀN A — Coder (+ QA/QC đo cùng) · việc ① · ĐƯỜNG GĂNG

**A1 · 20:45-21:10 · GỠ B1 — đo ngưỡng, đừng đoán.**
Chạy trong container `po-demo` (kho Chroma thật đã nạp):
```bash
docker exec fin05-po-demo-backend-1 python -c "
from src.rag import store
KHOP = ['hoàn tiền chuyển nhầm người nhận','giao dịch trừ tiền hai lần','tiền chưa vào ví từ ngân hàng']
RAC  = ['công thức nấu phở bò','tỷ số trận đấu tối qua','xin chào bạn khỏe không','zzzqwx plquv']
for nhan, bo in (('KHỚP',KHOP),('RÁC',RAC)):
    for q in bo:
        h = store.search(q, k=3)
        print(f'{nhan:5} {min(d for _,d in h) if h else float(\"nan\"):.4f}  {q[:38]}')
"
```
**Kết quả cần:** hai cụm tách rời. Ngưỡng = **giữa max(KHỚP) và min(RÁC)**, làm tròn về
phía **an toàn cho khách** (thà trả *"không tìm thấy"* còn hơn trả chính sách sai — Ràng
buộc cứng #3 đứng trên trải nghiệm).
🔴 **Hai cụm CHỒNG NHAU ⟹ DỪNG, báo Lead ngay.** Chồng nhau nghĩa là ngưỡng khoảng cách
**không đủ** để phân biệt, và việc này **đổi bản chất** — lúc đó phải hoãn ① sang đợt sau
chứ không được chọn đại một số. **Đây là nhánh phải báo, không phải nhánh tự xoay.**

**A2 · 21:10-21:25 · Code.** `src/config.py` thêm `RAG_MAX_DISTANCE` (đọc env, có mặc định
= số đo ở A1). `src/rag/search.py:81` lọc trước khi dựng `results`.
- ✅ **KHÔNG đụng** `store.py` (nó đã trả `distance` đúng) · **KHÔNG đụng** `search.py:95`
  (nhánh `not_found` đã đúng sẵn) · **KHÔNG đụng** frontend (`PolicyLookupClient.tsx:59`
  đã hiện *"Chưa tìm thấy…"* đúng khi `results.length === 0`).
- 🔴 **KHÔNG đụng `contracts/`.** Lược đồ `search_policy` không đổi, chỉ đổi *nội dung* trả
  về. Nếu Coder thấy mình đang mở `contracts/agent-tools.yaml` ⟹ **DỪNG**, báo Lead —
  đổi contract phải qua ADR + PO duyệt (`CLAUDE.md` §3), **không có đường tắt kể cả tối nay**.
- ⚠️ Nhớ **hai đường** dùng chung hàm này: `duong_tra="agent"` (qua tool) và `"cskh"`
  (`POST /policy-search`). Ngưỡng áp cho **cả hai** — đó là chủ đích, vì cả hai đều lộ ra người.

**A3 · 21:25-21:45 · Test đỏ-trước/xanh-sau (QA/QC viết, không đọc `src/`).**
Ca đỏ **bắt buộc**: truy vấn rác ⟹ `status == "not_found"` **và** `results == []`.
Chạy trên commit TRƯỚC bản vá ⟹ **phải ĐỎ**. Thiếu vế đỏ = chưa nghiệm thu, không có ngoại lệ.
E2E: `policy-lookup.spec.ts` đang đỏ — nó phải **chuyển xanh**, và đó là bằng chứng mặt UI.

**Cổng A:** dán **cả hai** kết quả (đỏ trước / xanh sau) + bảng số đo A1.

---

### LÀN B — Bảo mật (hoặc Coder nếu Bảo mật bận) · việc ② · KHÔNG dựng lại gì

**B1 · Lấy nguyên khối 5 header từ `docs/devops/2026-08-27-de-xuat-header-bao-mat-caddy.md`
(`db8d460`) chép vào `Caddyfile`.** Năm cái: HSTS · X-Frame-Options · X-Content-Type-Options ·
Referrer-Policy · Permissions-Policy.
🔴 **CSP đã được tách ra CÓ CHỦ ĐÍCH trong chính bản đề xuất** — rủi ro phá trang cao nhất,
cần đo `Report-Only` trên traffic thật trước. **Đừng thêm CSP tối nay.** Ai thấy thiếu CSP mà
tự thêm vào là đang phá một quyết định đã cân nhắc.

**B2 · Áp:** cả ba ngăn mount **CÙNG một tệp** `./Caddyfile` ⟹ một lần sửa, ba lần nạp:
```bash
for p in fin05-po-demo fin05-qa-stripe fin05-dot-otp; do
  docker exec ${p}-caddy-1 caddy reload --config /etc/caddy/Caddyfile 2>&1 | tail -1
done
```
**Cổng B:** `curl -skI https://localhost:60443 | grep -iE 'strict-transport|x-frame|x-content|referrer|permissions'`
⟹ **5/5 dòng**. Và vế đỏ: chạy đúng lệnh đó **trước** khi sửa ⟹ **0 dòng** (tôi đã đo 0, dán lại làm mốc).

---

### LÀN C — QA/QC hoặc tester · việc ④ · thuần git, không đụng container

PO thật đã chốt: **chỉ chặn từ nay, KHÔNG viết lại lịch sử, KHÔNG force-push.**

**C1 · Hai bước, ĐÚNG THỨ TỰ** (chỉ `.gitignore` là vá không chặn gì mà trông như đã chặn,
vì cả 6 tệp `render_that_*` **đã tracked** từ `db7a488`/`1a6eff1`):
```bash
git rm --cached eval/results/render_that_*        # bước 1, BẮT BUỘC trước
printf 'eval/results/render_that_*\n' >> .gitignore   # bước 2
```

**C2 · 🔴 Chặn nguồn, nếu không nó MỌC LẠI.** Nguyên nhân gốc đã tìm ra (§0b.19e):
`playwright.config.ts:25/30` `testIgnore` **chỉ** loại `live-chat.spec.ts`, nên
`kich-ban-chuyen-gia-render-that.spec.ts` **chạy mặc định**, và CI nightly
(`.github/workflows/ci.yml:724/756`) chạy nó **hằng đêm, tự động**.
⟹ Thêm nó vào `testIgnore`. **Bỏ bước này thì C1 vô nghĩa từ đêm mai.**

**C3 · Bốn tệp `M` đang treo:** sau C1 chúng rời khỏi chỉ mục. **Không `git checkout`, không
`git clean`** — để nguyên trên đĩa. Xoá hiện vật không rõ nguồn gốc là bắt phiên sau đo lại từ đầu.

**C4 · Niêm hồ sơ:** ghi vào `docs/security/2026-09-01-ma-otp-da-render-trong-git-quet-eval-e2e.md`
rằng lịch sử **cố ý giữ nguyên**, kèm lý do PO chốt (dữ liệu tổng hợp · chế độ demo · mã đã hết
hạn ⟹ rủi ro thấp) và mức rủi ro chấp nhận. **Quyết định có khai ≠ khoảng trống im lặng** — đây
đúng là thứ đội due-diligence hỏi, và có khai thì trả lời được.

**Cổng C:** `git ls-files eval/results/ | grep render_that` ⟹ **rỗng** · và
`npx playwright test --list 2>/dev/null | grep -c render-that` ⟹ **0**.

---

### LÀN D — Coder/DevOps · việc ⑤ · tạo lại container, KHÔNG dựng ảnh

**Đo mốc nền (dán vào báo cáo, đây là vế ĐỎ):**
```
fin05-qa-stripe-caddy-1   0.0.0.0:59080 / 0.0.0.0:59443   ← HỞ RA LAN
fin05-po-demo-caddy-1     0.0.0.0:60080 / 0.0.0.0:60443   ← HỞ RA LAN
fin05-dot-otp-caddy-1     127.0.0.1:48080 / 127.0.0.1:48443  ← ĐÚNG (tạo 33h trước, SAU bản vá)
```
`dot-otp` đúng sẵn chính là **bằng chứng bản vá nguồn hoạt động** — không cần sửa gì thêm,
chỉ cần container sinh lại từ nguồn hiện tại.

🔴 **BẪY ĐÃ TRẢ GIÁ, đọc trước khi gõ** (Coder đo được 01/09): khi `image:` chỉ có trong
override còn base chỉ có `build:`, thì `up --force-recreate` **thiếu `-f …override.yml`**
làm compose **âm thầm quay về `build:` và tự dựng một ảnh MỚI** dưới tag khác.
⟹ **Mọi lệnh phải đủ `-p <project>` VÀ đủ mọi `-f`.** Kiểm ngăn nào có override trước khi gõ.

Tạo lại **chỉ dịch vụ `caddy`**, không đụng dịch vụ khác:
`docker compose -p <ngăn> -f docker-compose.yml [-f <override nếu có>] up -d --force-recreate caddy`

**Cổng D:** chạy lại đúng lệnh `docker port` ở trên ⟹ **cả ba đều `127.0.0.1`**.
Và cert còn sống: `curl -skI https://localhost:60443` ⟹ có phản hồi (`caddy_data` là volume có
tên nên cert sống qua lần tạo lại — nếu **mất** cert thì báo ngay, đó là dữ kiện mới).

---

### PO THẬT · 5 phút · làm ngay phút đầu, không ai chờ được thay

Thu hồi **`QWEN_API_KEY`** trong console DashScope, phát khoá mới, cập nhật `.env`.
Không việc nào ở trên phụ thuộc việc này ⟹ **đừng để nó nằm cuối danh sách rồi quên**.
⚠️ `.env` **không** tracked (đã kiểm) — đổi khoá không sinh commit nào.

---

## 3. Nghiệm thu cuối · 22:45 · Lead dán MỘT bảng

| việc | vế ĐỎ (trước) | vế XANH (sau) | ai xác nhận |
|---|---|---|---|
| ① RAG | test rác `status != not_found` · `policy-lookup.spec.ts` đỏ | `not_found` + `results: []` · spec xanh | QA/QC |
| ② header | `curl -I` → **0** dòng header | **5/5** dòng, cả 3 ngăn | Bảo mật |
| ④ OTP git | `git ls-files` → 6 tệp `render_that_*` | **rỗng** + `testIgnore` chặn nguồn | QA/QC |
| ⑤ LAN | 2 ngăn `0.0.0.0` | **3/3** `127.0.0.1` | Coder |

🔴 **Cổng nào chỉ có vế xanh thì tôi trả lại**, kể cả 23:50. Cổng chỉ biết xanh là cổng không
mang thông tin — đây đúng bài học đội tự rút chiều nay (*phép kiểm "phiên OTP tươi" chạy mỗi
15 phút suốt chiều, luôn xanh, và không đo gì cả*).

**Sau nghiệm thu, TRƯỚC khi lên `main`, còn một việc [ĐO 20:35]:** `main` = `origin/main` =
`e92214c`, HEAD trước nó **148 commit**. Merge 148 commit là thao tác của **PO thật**
(`CLAUDE.md` §3 · kích CI trên hạ tầng BTC · chạm production).

---

## 4. Thứ tôi CỐ Ý không đưa vào 2 tiếng này

Nói ra để không ai tưởng bị bỏ quên — cả bốn đều **đáng làm**, chỉ là **không đêm nay**:

- **② xoay model dừng ở lỗi non-quota** — chạm `src/`, đáng ra hợp lúc vì đang dựng lại ảnh.
  Loại vì **gộp hai thay đổi `src/` vào một lần dựng làm hỏng khả năng quy trách**: hỏng thì
  không biết tại cái nào. Một lần dựng, một thay đổi.
- **③ rò rỉ RAM** — chưa tái lập được, còn ở mức *hướng điều tra*. Không đưa việc chưa tái
  lập được vào một cửa sổ 2 tiếng có hạn cứng.
- **⑥ golden không phủ tool** — là **mở rộng phạm vi**, cần PO thật gật, và không sửa được
  bằng cách thêm tiêu chí chấm (§0b.19d).
- **Mật khẩu khách hardcode** trong 2 tệp `quay-video*` — cùng dạng tiền lệ đã tracked
  (`auth.spec.ts`, `auth-multirole.spec.ts`), **không mở lớp rủi ro mới**. Dọn chung một lượt.
