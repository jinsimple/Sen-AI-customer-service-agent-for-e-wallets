# deploy_home.ps1 — dựng/cập nhật FIN-05 trên máy bàn Windows chạy 24/7.
#
# Chạy lại bao nhiêu lần cũng vô hại (idempotent): pull → build → up → smoke.
# KHÔNG đụng dữ liệu — volume `fin05_postgres_data` giữ nguyên qua mọi lượt.
#
#   Cách chạy (PowerShell, trong thư mục repo):
#       .\scripts\deploy_home.ps1
#
# Vì sao là script tay chứ không phải GitHub Actions: billing CI của tổ chức
# đang tắc, và một máy ở nhà sau CGNAT thì runner cũng không SSH vào được.
# Deploy tay có kiểm tra tự động vẫn tốt hơn deploy tay không có gì.

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Say($m) { Write-Host $m }
function Ok($m)  { Write-Host "  [OK]    $m" -ForegroundColor Green }
function Bad($m) { Write-Host "  [LOI]   $m" -ForegroundColor Red }
function Warn($m){ Write-Host "  [LUU Y] $m" -ForegroundColor Yellow }

Say ""
Say "=== FIN-05 — deploy tai nha (profile: home) ==="
Say ""

# --- CỔNG 1: .env phải có, và phải đủ 3 biến sống-chết -------------------
# Đây là chỗ FAIL-FAST thật của đường home. KHÔNG đặt trong docker-compose.yml
# bằng `${VAR:?}` được: compose nội suy biến cho MỌI service kể cả service bị
# profile loại ra, nên `${VAR:?}` sẽ làm chết luôn `docker compose up` thường
# trên máy dev — đo thật, xem ghi chú trong docker-compose.yml.
if (-not (Test-Path ".env")) {
    Bad ".env khong ton tai. Chep tu may cu sang (xem docs huong dan chuyen may)."
    exit 1
}
$envText = Get-Content ".env" -Raw

$batBuoc = @{
    "CLOUDFLARE_TUNNEL_TOKEN" = "Lay tren dashboard Cloudflare: Zero Trust > Networks > Tunnels > tunnel cua ban > Install connector. Day la buoc TAY, khong tu dong hoa duoc."
    "FIELD_ENCRYPTION_KEY"    = "PHAI la khoa CU tu may Mac. Doi khoa = moi cot ma hoa (chat, so tai khoan, mo ta khieu nai) thanh rac VINH VIEN."
    "JWT_SECRET_KEY"          = "PHAI la khoa CU. Doi = moi phien dang nhap hien co bi vo."
}
$thieu = $false
foreach ($k in $batBuoc.Keys) {
    if ($envText -notmatch "(?m)^\s*$k\s*=\s*\S") {
        Bad "$k chua co gia tri trong .env"
        Warn "        $($batBuoc[$k])"
        $thieu = $true
    } else { Ok "$k co gia tri" }
}
if ($thieu) { Say ""; Bad "Dung lai. Bo sung .env roi chay lai."; exit 1 }

# --- CỔNG 2: biến PHỤ THUỘC MÁY còn sót từ máy Mac -----------------------
# Bẫy đã cắn thật một lần: SSL_CERT_FILE trỏ /Library/Frameworks/... (macOS)
# đi theo .env sang container -> MOI luot chat agent tra HTTP 500 trong 0,06s,
# ma /health van xanh nen `docker ps` khong lo ra. Nghich ly: .env cang duoc
# mang sang trung thanh thi loi cang chac chan tai hien.
if ($envText -match "(?m)^\s*SSL_CERT_FILE\s*=\s*(.+)$") {
    $v = $Matches[1].Trim()
    if ($v -match "^/(Library|Users|opt|usr)/") {
        Warn "SSL_CERT_FILE dang tro duong dan cua may Mac: $v"
        Warn "        Khong chan deploy (docker-compose.yml da ghi de cho container),"
        Warn "        nhung nen XOA dong nay khoi .env tren may Windows cho sach."
    }
}

# --- Docker còn sống không -----------------------------------------------
try { docker info *> $null; Ok "Docker dang chay" }
catch { Bad "Docker Desktop chua chay. Mo Docker Desktop roi chay lai."; exit 1 }

# --- Kéo code mới --------------------------------------------------------
Say ""; Say "--- Cap nhat ma nguon ---"
git pull --ff-only origin main
if ($LASTEXITCODE -ne 0) {
    Bad "git pull --ff-only that bai — cay lam viec co thay doi cuc bo?"
    Warn "        KHONG tu dong ghi de. Xem 'git status' roi xu ly tay."
    exit 1
}
Ok "Da o ban main moi nhat: $(git rev-parse --short HEAD)"

# --- Build + up ----------------------------------------------------------
Say ""; Say "--- Build + khoi dong (profile home) ---"
docker compose --profile home build
if ($LASTEXITCODE -ne 0) { Bad "Build that bai"; exit 1 }
docker compose --profile home up -d
if ($LASTEXITCODE -ne 0) { Bad "Khoi dong that bai"; exit 1 }

# --- SMOKE: khong tin "up -d khong bao loi" ------------------------------
# Bai hoc cua du an: container `healthy` KHONG dong nghia dich vu phuc vu
# duoc — /health khong cham OpenAI nen no van xanh khi duong dat nhat da chet.
Say ""; Say "--- Kiem tra thuc te ---"
$loi = 0

Say "  cho backend san sang..."
$san = $false
foreach ($i in 1..30) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $san = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if ($san) { Ok "/health tra 200" } else { Bad "/health khong tra 200 sau 60s"; $loi++ }

try {
    $r = Invoke-WebRequest -Uri "http://localhost/login" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($r.StatusCode -eq 200) { Ok "Trang dang nhap tra 200" } else { Bad "Trang dang nhap tra $($r.StatusCode)"; $loi++ }
} catch { Bad "Khong mo duoc trang dang nhap: $_"; $loi++ }

$chay = (docker compose --profile home ps --services --filter "status=running")
foreach ($s in @("postgres","redis","backend","frontend","caddy","cloudflared")) {
    if ($chay -contains $s) { Ok "service $s dang chay" } else { Bad "service $s KHONG chay"; $loi++ }
}

# Tunnel da noi duoc Cloudflare chua — doc log that, khong doan.
$logTunnel = docker compose --profile home logs --tail 40 cloudflared 2>&1 | Out-String
if ($logTunnel -match "Registered tunnel connection|Connection .* registered") {
    Ok "Cloudflare Tunnel da ket noi"
} else {
    Bad "Chua thay tunnel ket noi trong log"
    Warn "        Xem chi tiet: docker compose --profile home logs cloudflared"
    $loi++
}

Say ""
if ($loi -eq 0) {
    Say "=== TAT CA XANH ==="
    Say ""
    Warn "CHUA XONG: buoc nghiem thu cuoi cung KHONG chay tu may nay duoc."
    Say "  Mo https://app.adaptivealgo.uk tu MOT MAY KHAC (hoac 4G dien thoai,"
    Say "  TAT WiFi) va thay man dang nhap. Chi khi do moi goi la xong."
    exit 0
} else {
    Say "=== CO $loi MUC DO ==="
    exit 1
}
