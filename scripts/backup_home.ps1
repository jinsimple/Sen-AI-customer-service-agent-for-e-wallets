# backup_home.ps1 — sao lưu Postgres tự động cho FIN-05, chạy qua Windows Task
# Scheduler. Không đụng volume postgres_data — chỉ ĐỌC qua pg_dump, ghi ra thư
# mục NGOÀI phạm vi Docker quản lý (mất volume/`down -v` không kéo theo mất
# backup — hai rủi ro độc lập, đúng nguyên tắc Luật D "cột phòng thủ cần nguồn
# độc lập" đã dùng cho postgres_data external).
#
# Thiết kế: DevOps (docs/devops/2026-08-27-de-xuat-backup-tu-dong.md).
# Land: tech-lead (vùng `scripts/`).
#
# Đăng ký chạy hằng ngày (làm MỘT LẦN, PowerShell chạy as Administrator):
#   $action  = New-ScheduledTaskAction -Execute "pwsh.exe" `
#              -Argument '-NoProfile -File "C:\đường\dẫn\repo\scripts\backup_home.ps1"'
#   $trigger = New-ScheduledTaskTrigger -Daily -At 3am
#   Register-ScheduledTask -TaskName "FIN05-Backup-DB" -Action $action `
#              -Trigger $trigger -Description "Sao luu Postgres FIN-05 hang ngay"

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# 🔴 THÊM KHI LAND (tech-lead), KHÔNG có trong bản thiết kế — và đây là lý do.
# Dòng `pg_dump ... > $tenFile` bên dưới dùng chuyển hướng của SHELL, nên bản
# ghi ra đĩa mang MÃ HOÁ MẶC ĐỊNH CỦA SHELL:
#     pwsh 6+            -> UTF-8 không BOM      ✅ psql đọc lại được
#     Windows PowerShell -> UTF-16LE             🔴 psql KHÔNG đọc lại được
#       5.1 (powershell.exe)
# Lệnh đăng ký ở trên gọi `pwsh.exe` nên đúng — nhưng ai chạy tay bằng
# `powershell.exe`, hoặc sửa Task Scheduler cho "gọn", sẽ tạo ra một file
# .sql TRÔNG BÌNH THƯỜNG, kích thước hợp lý, log ghi [OK] — và KHÔNG KHÔI
# PHỤC ĐƯỢC. Hỏng đúng lúc cần nhất, im lặng tới tận lúc đó.
# Chết ở đây rẻ hơn phát hiện lúc mất dữ liệu.
if ($PSVersionTable.PSVersion.Major -lt 6) {
    Write-Error ("Script nay PHAI chay bang pwsh 7+ (pwsh.exe), KHONG phai " +
        "Windows PowerShell 5.1. Ly do: chuyen huong `>` cua 5.1 ghi UTF-16LE, " +
        "file .sql sinh ra KHONG psql doc lai duoc — va no trong nhu binh thuong. " +
        "Dang chay: PowerShell $($PSVersionTable.PSVersion)")
    exit 1
}

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
# [ĐO 27/08, DevOps, container pwsh thật] `-notmatch` trên MỘT MẢNG không làm
# điều trực giác: nó trả về các PHẦN TỬ KHÔNG khớp (mảng con), không phải một
# bool. 5 dòng, 1 dòng khớp ⟹ `-notmatch` trả 4 dòng còn lại — MẢNG KHÔNG
# RỖNG ⟹ `if (...)` vẫn đúng ⟹ báo "backup bị cắt" SAI dù trailer CÓ MẶT.
# Cách đúng: `-not (mảng -match mẫu)` — `-match` trả các phần tử KHỚP (rỗng
# nếu không ai khớp), rồi phủ định cả kết quả.
# 🔴 Vì sao đáng viết dài thế này cho một dấu ngoặc: đây là CỔNG DỐI NGƯỢC
# CHIỀU — đỏ giả, không phải xanh giả. Và đỏ giả có cái giá riêng: nó DẠY
# NGƯỜI TA BỎ QUA CẢNH BÁO. Vài lần "backup bi cat" mà mở ra thấy nguyên vẹn
# thì lần thứ tư không ai buồn mở — kể cả lần đó nó cắt thật.
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
