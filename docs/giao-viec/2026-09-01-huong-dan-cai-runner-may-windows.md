# CÀI RUNNER CI TRÊN MÁY WINDOWS — hướng dẫn cho PO thật

> Viết 01/09 22:07 · Token trong hộp thoại Phoenix **hết hạn 22:54:36** ⟹ còn ~45 phút.
> Nếu quá hạn: quay lại trang "Runner của đội" bấm **Lấy token đăng ký runner** lấy mã mới.

---

## 0. Vì sao cần — đã đo, không phải phỏng đoán

```
$ gh api …/actions/runs/33521788870/jobs
9/14 job QUEUED · KHÔNG job nào nhận được runner
```
Pool chung của BTC **đang không nhận việc**. Đây KHÔNG phải lỗi nhãn hay lỗi cấu hình của đội —
kể cả 8 job vốn chạy tốt trên `self-hosted` cũng đang xếp hàng. Thêm máy riêng là cách duy nhất
đội tự gỡ được, vì tài khoản `jinsimple` **không phải admin repo, không phải owner org**
(`admin:false` · org role `member`).

✅ Điều kiện tiên quyết đã đạt: **repo đang `private`** (Phoenix chỉ cấp token cho repo private).

---

## 1. 🔴 BẪY LỚN NHẤT — đừng chọn "Windows" trong hộp thoại

Hộp thoại đang để **macOS**. Phản xạ tự nhiên là bấm sang **Windows**. **ĐỪNG.**

**Lý do 1 — nhãn không khớp.** Runner Windows tự đăng ký nhãn `self-hosted` · **`Windows`** · `X64`.
Nó **KHÔNG có nhãn `Linux`**. Job `route-guards-docker` mà DevOps vừa đổi sang
`[self-hosted, linux, x64]` sẽ **không bao giờ khớp** ⟹ treo hàng đợi mãi mãi.

**Lý do 2, nặng hơn — toàn bộ CI của dự án viết cho Linux.** Các job dùng `bash`, `docker`,
đường dẫn kiểu Unix, `sudo`. Chạy trên runner Windows thuần thì **hỏng ngay từ bước đầu**, và
hỏng theo kiểu khó đọc (lệnh không tồn tại, đường dẫn sai), không phải hỏng gọn gàng.

### ✅ Chọn **Linux · x64**, và cài **BÊN TRONG WSL2** của máy Windows

WSL2 đăng ký đúng nhãn `self-hosted` · `Linux` · `X64`, chạy được `bash` + `docker`, và **máy
Windows của bạn vốn đã chạy Docker Desktop** cho sản phẩm — nên hạ tầng cần thiết đã có sẵn.

---

## 2. ⚠️ RỦI RO BẢO MẬT — chính BTC cảnh báo, và với máy này nó nặng hơn bình thường

Nguyên văn trang Phoenix:
> *"Khi máy đã nhận việc, **mọi workflow của repo đội sẽ chạy trên chính máy đó, dưới quyền tài
> khoản đang đăng nhập**. Ai trong đội push được code là chạy được lệnh trên máy — tức đọc được
> khoá SSH, thông tin đăng nhập cloud và cookie trình duyệt của bạn. Vì vậy **nên dùng VPS hoặc
> máy ảo riêng**; chỉ dùng laptop cá nhân khi bạn chấp nhận rủi ro đó."*

🔴 **Với máy này, rủi ro cụ thể hơn cảnh báo chung:** đây là máy **đang chạy production thật**,
có `.env` production, CSDL khách hàng mô phỏng, và khoá LLM. CI job đọc được filesystem của máy
⟹ đọc được những thứ đó. Và tối nay đội **vừa có một sự cố lộ 7 secret** — không nên chồng thêm
một đường lộ nữa mà không biết.

**Ba mức, chọn theo thời gian bạn có:**

| mức | cách làm | đánh đổi |
|---|---|---|
| **A — an toàn nhất** | VPS riêng / máy ảo riêng, không dính production | tốn tiền + thời gian dựng, **không kịp đêm nay** |
| **B — cân bằng, KHUYẾN NGHỊ** | **WSL2 distro RIÊNG** chỉ để chạy runner (`Ubuntu-Runner`), khác distro đang chạy sản phẩm | ~15 phút · cách ly phần lớn, **nhưng vẫn đọc được `/mnt/c`** |
| **C — nhanh nhất** | cài thẳng vào WSL2 đang có | ~5 phút · **không cách ly gì** |

⚠️ **Điều KHÔNG mức nào che được:** WSL2 luôn mount ổ Windows tại `/mnt/c`. Muốn chặn hẳn thì phải
tắt automount trong `/etc/wsl.conf` của distro runner — làm được, nhưng đừng làm lúc 23h.

🔑 **Yếu tố làm giảm rủi ro thật trong hoàn cảnh này:** danh sách người push được vào repo hiện
gần như chỉ có bạn. Rủi ro "đồng đội xấu" gần bằng 0; rủi ro còn lại là **BTC có quyền admin** và
**bất kỳ ai chiếm được tài khoản GitHub của bạn**.

---

## 3. Các bước — gõ TRÊN MÁY WINDOWS, trong terminal WSL2

**Bước 0 — mở WSL2.** Trong PowerShell:
```powershell
wsl --list --verbose          # xem distro nào đang có, cột VERSION phải là 2
wsl -d <tên-distro>           # vào distro. Mức B: tạo riêng trước (xem cuối file)
```

**Bước 1 — trong hộp thoại Phoenix, bấm `Linux` + `x64`** rồi chép lệnh bước 1 nó sinh ra.
Nó phải là `actions-runner-**linux**-x64-…`, **không phải** `osx`:
```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.336.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.336.0/actions-runner-linux-x64-2.336.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.336.0.tar.gz
```

**Bước 2 — đăng ký.** Chép nguyên dòng `./config.sh` từ hộp thoại (đã điền sẵn tên máy
`team-226-jinsimple` và nhãn `team-226`).
🔴 **Token chỉ dùng MỘT LẦN và hết hạn 22:54:36** — quá hạn thì lấy mã mới, đừng gõ lại mã cũ.
⚠️ **Đừng dán dòng lệnh đó vào chat chung, issue, hay bất kỳ tab AI nào khác** — nó chứa token.

**Bước 3 — chạy nền 24/7** (đừng dùng `./run.sh`, nó chết khi đóng terminal):
```bash
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status        # phải thấy "active (running)"
```
⚠️ WSL2 **không tự khởi động khi Windows bật**. Muốn thật sự 24/7 phải thêm một tác vụ
Task Scheduler chạy `wsl -d <distro> -u root /etc/init.d/… ` lúc đăng nhập — hoặc chấp nhận
bật tay sau mỗi lần khởi động lại máy. **Ghi nhận, đừng làm đêm nay.**

**Bước 4 — nghiệm thu, phải thấy CẢ HAI vế:**
1. Trang "Runner của đội": dòng `team-226-jinsimple` đổi từ **Chưa cài** → **đang chạy**, cột
   Label hiện `team-226`.
2. Job đang treo **bắt đầu chạy** — đây mới là vế thật:
   ```
   gh run list --limit 3          # trạng thái đổi từ queued sang in_progress
   ```
   Chỉ vế 1 mà job vẫn treo ⟹ nhãn không khớp, xem §4.

---

## 4. 🔴 VIỆC PHẢI LÀM TRONG REPO — nếu không, runner cài xong vẫn vô dụng

BTC ghi rõ:
> *"Không phải sửa gì thêm: cứ để `runs-on: self-hosted` như cũ… Chỉ khi bắt buộc phải chạy đúng
> máy này mới ghi rõ `[self-hosted, team-226]`."*

⟹ **Bảo DevOps đổi `route-guards-docker` từ `[self-hosted, linux, x64]` về `runs-on: self-hosted` trần**,
giống hệt 8 job kia. Ba lý do:
1. **Đồng nhất** — 8 job đang chạy đều dùng dạng trần, có bằng chứng chạy được.
2. **Thông lượng** — dạng trần cho job chạy trên **pool BTC HOẶC máy bạn**, cái nào rảnh trước.
   Ghim `team-226` thì **mọi job dồn vào một máy**, mà **một runner chỉ chạy MỘT job tại một
   thời điểm** ⟹ 14 job xếp hàng nối đuôi, có job 27 phút ⟹ **không kịp trước 24:00**.
3. Đó đúng là điều BTC hướng dẫn.

⟹ Chỉ dùng `[self-hosted, team-226]` khi cần **ép** một job chạy đúng máy này (ví dụ job cần
Docker Desktop local). Không phải mặc định.

---

## 5. Phụ lục — tạo WSL2 distro riêng (mức B, khuyến nghị)

Trong PowerShell trên Windows:
```powershell
wsl --install -d Ubuntu-24.04 --name Ubuntu-Runner    # tên riêng, tách khỏi distro sản phẩm
wsl -d Ubuntu-Runner
```
Trong distro mới, cài thứ CI cần rồi mới làm §3:
```bash
sudo apt update && sudo apt install -y curl tar git
docker --version     # nếu THIẾU: bật Docker Desktop → Settings → Resources → WSL Integration
                     # → tick Ubuntu-Runner. KHÔNG cài docker engine riêng trong WSL.
```
🔴 `route-guards-docker` **cần Docker**. Thiếu bước tick WSL Integration thì runner nhận việc
rồi hỏng ở bước docker — tệ hơn không cài, vì lúc đó job **không còn queued để ai nhìn thấy**.
