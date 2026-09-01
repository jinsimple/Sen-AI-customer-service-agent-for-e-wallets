# Đề xuất — sao lưu CSDL tự động trên máy production — 2026-08-27

> Chủ động đề xuất, chưa ai giao. Đúng mục P0-3 trong
> [`2026-08-25-danh-gia-ha-tang-eu-us.md`](2026-08-25-danh-gia-ha-tang-eu-us.md) ("Không có backup
> tự động, không RPO/RTO, chưa từng diễn tập phục hồi") — phần "chưa từng diễn tập" đã đóng
> (`docs/DEPLOY.md`, mục "Khôi phục từ backup"), phần "không tự động" vẫn còn treo.

## Hiện trạng [ĐO 27/08, grep toàn repo]

```
grep -rln "Task Scheduler|schtasks|backup.*tu dong|cron.*backup" docs/ scripts/
→ 0 kết quả
```

Không có cơ chế nào tự chạy backup định kỳ. `backup-truoc-25-08.sql` (tệp PO thật đang dùng để
diễn tập khôi phục) là một lần chụp tay, không lặp lại. Máy production chạy 24/7 không người trực
— một lần quên tay là một khoảng trống không ai biết cho tới khi cần.

## Đề xuất — kịch bản cho `scripts/backup_home.ps1` (tech-lead land, vùng `scripts/` không phải
của DevOps)

```powershell
# backup_home.ps1 — sao lưu Postgres tự động cho FIN-05, chạy qua Windows Task
# Scheduler. Không đụng volume postgres_data — chỉ ĐỌC qua pg_dump, ghi ra thư
# mục NGOÀI phạm vi Docker quản lý (mất volume/`down -v` không kéo theo mất
# backup — hai rủi ro độc lập, đúng nguyên tắc Luật D "cột phòng thủ cần nguồn
# độc lập" đã dùng cho postgres_data external).
#
# Đăng ký chạy hằng ngày (làm MỘT LẦN, PowerShell chạy as Administrator):
#   $action  = New-ScheduledTaskAction -Execute "pwsh.exe" `
#              -Argument '-NoProfile -File "C:\đường\dẫn\repo\scripts\backup_home.ps1"'
#   $trigger = New-ScheduledTaskTrigger -Daily -At 3am
#   Register-ScheduledTask -TaskName "FIN05-Backup-DB" -Action $action `
#              -Trigger $trigger -Description "Sao luu Postgres FIN-05 hang ngay"

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# SỬA hai giá trị này cho khớp máy thật trước khi đăng ký Task Scheduler.
$thuMucBackup = "C:\FIN05-Backups"   # PHẢI ngoài thư mục Docker Desktop quản lý
$giuLaiNgay   = 14                    # cũ hơn N ngày thì tự xoá, tránh đầy đĩa

if (-not (Test-Path $thuMucBackup)) { New-Item -ItemType Directory -Path $thuMucBackup | Out-Null }

$nhanThoiGian = (Get-Date).ToString("yyyy-MM-dd_HHmmss")
$tenFile      = Join-Path $thuMucBackup "fin05-backup-$nhanThoiGian.sql"
$logFile      = Join-Path $thuMucBackup "backup.log"

function Ghi($m) {
    $dong = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m"
    Write-Host $dong
    Add-Content -Path $logFile -Value $dong
}

# pg_dump chạy TRONG container qua docker exec — không cần cài Postgres client
# trên Windows (đúng khuôn deploy_home.ps1 dùng cho kho_rag.py/model check).
docker compose --profile home exec -T postgres pg_dump -U fin05 fin05 > $tenFile
if ($LASTEXITCODE -ne 0) {
    Ghi "[LOI] pg_dump that bai, exit code $LASTEXITCODE"
    exit 1
}

# BƯỚC 0 rẻ — cùng phép kiểm đã landed ở docs/DEPLOY.md mục "Khôi phục từ
# backup": dump có dòng trailer "dump complete" không, TRƯỚC KHI tin file này
# là một bản backup dùng được. Không xoá file nghi ngờ — để lại cho điều tra.
#
# [ĐO 27/08] `-notmatch` trên MỘT MẢNG không làm điều trực giác: nó trả về
# các PHẦN TỬ KHÔNG khớp (mảng con), không phải một bool "có phần tử nào khớp
# không". 5 dòng, 1 dòng khớp ⟹ `-notmatch` trả về 4 dòng còn lại — MẢNG
# KHÔNG RỖNG ⟹ `if (...)` vẫn đúng ⟹ báo lỗi SAI dù trailer có mặt. Tự kiểm
# bằng container `pwsh` thật trước khi viết dòng này — không đoán theo trực
# giác. Cách đúng: `-not (mảng -match mẫu)` — `-match` trả về các phần tử
# KHỚP (mảng rỗng nếu không ai khớp), rồi phủ định cả kết quả đó.
$duoiFile = Get-Content $tenFile -Tail 5
if (-not ($duoiFile -match "PostgreSQL database dump complete")) {
    Ghi "[LOI] File backup NGHI bi cat giua chung: $tenFile — KHONG tin la ban dung duoc"
    exit 1
}

$kichThuoc = [math]::Round((Get-Item $tenFile).Length / 1MB, 1)
Ghi "[OK] Backup xong: $tenFile ($kichThuoc MB)"

# Dọn bản cũ hơn $giuLaiNgay — tránh đầy đĩa vô hạn theo thời gian, KHÔNG đụng
# postgres_data (khác hẳn cơ chế, một cái là volume Docker, một cái là file
# .sql trên đĩa Windows).
$cu = Get-ChildItem $thuMucBackup -Filter "fin05-backup-*.sql" |
      Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$giuLaiNgay) }
foreach ($f in $cu) {
    Remove-Item $f.FullName
    Ghi "[DON] Xoa backup cu: $($f.Name)"
}
```

## Vì sao thiết kế thế này

- **Tách khỏi `postgres_data`, có chủ đích** — hai đường mất dữ liệu độc lập (`down -v`/lỗi volume
  Docker vs ổ đĩa Windows hỏng) không cùng kéo sập cả CSDL lẫn bản sao lưu duy nhất.
- **Tự kiểm dump không bị cắt giữa chừng** — dùng lại đúng phép kiểm đã landed cho quy trình khôi
  phục (`docs/DEPLOY.md`), không phát minh cơ chế thứ hai cho cùng một câu hỏi.
- **Tự dọn theo tuổi** — không tích luỹ vô hạn trên máy cá nhân không ai canh dung lượng đĩa
  thường xuyên.
- **Ghi log riêng, không chỉ in console** — Task Scheduler chạy nền, không ai nhìn thấy output
  console; `backup.log` là nơi PO (hoặc ai điều tra sau) tra lại được lịch sử chạy.
- **KHÔNG tự gửi cảnh báo khi lỗi** (email/Slack) — cố ý để phạm vi nhỏ cho lần land đầu. Nếu PO
  thật muốn báo động chủ động, Windows Task Scheduler hỗ trợ gửi email khi task thất bại — việc
  riêng, đừng gộp vào lần land này.

## Việc còn lại, không thuộc DevOps

- Land `scripts/backup_home.ps1` — vùng ghi tech-lead.
- PO thật: sửa hai giá trị (`$thuMucBackup`, `$giuLaiNgay`) cho khớp máy, chạy lệnh
  `Register-ScheduledTask` MỘT LẦN.
- Diễn tập khôi phục THẬT bằng chính file backup tự động này (không phải dump thủ công như lần
  trước) — sau khi đã chạy được vài ngày, xem `docs/DEPLOY.md` mục "Khôi phục từ backup".
