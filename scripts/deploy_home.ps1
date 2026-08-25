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

param(
    # GHIM, CO TRONG GIT ⟹ doi phai qua commit + Review. DOC LAP voi .env
    # (khong git, khong lich su, khong ai soat — dung thu gay 403 hang loat
    # 25/08: .env tro sai model, khong ai phat hien vi khong nam trong commit
    # nao). Day la nguon THU HAI de SO, KHONG phai noi dat cau hinh that.
    # KHONG Mandatory: PO go script khong tham so, ep nhap la treo vo han
    # trong cua so khong co nguoi, va go sai chuoi ghim = bao dong gia ngay
    # lan dau.
    [string]$ModelDuKien = "qwen3.7-plus-2026-05-26"
)

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

# --- CỔNG 2b: APP_ENV còn là development ---------------------------------
# Cung ho voi SSL_CERT_FILE o tren: `.env` chep tu may Mac mang theo ca dong
# chi dung o may dev. CANH BAO chu khong CHAN — sai nhan moi truong khong lam
# hong dich vu.
if ($envText -match "(?m)^\s*APP_ENV\s*=\s*development") {
    Warn "APP_ENV=development tren may chay 24/7 — /api/env-info se bao 'development'"
    Warn "        Sua .env thanh APP_ENV=production roi chay lai."
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
# DAU VAT: doc git ngay TRUOC khi build, tren may co `.git`.
$env:BUILD_COMMIT = (git rev-parse --short HEAD)
$env:BUILD_AT     = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss+00:00")
Ok "Dau build: $($env:BUILD_COMMIT) · $($env:BUILD_AT)"
docker compose --profile home build
if ($LASTEXITCODE -ne 0) { Bad "Build that bai"; exit 1 }
docker compose --profile home up -d
if ($LASTEXITCODE -ne 0) { Bad "Khoi dong that bai"; exit 1 }

# --- SMOKE: khong tin "up -d khong bao loi" ------------------------------
# Bai hoc cua du an: container `healthy` KHONG dong nghia dich vu phuc vu
# duoc — /health khong cham OpenAI nen no van xanh khi duong dat nhat da chet.
Say ""; Say "--- Kiem tra thuc te ---"
$loi = 0

# --- KHO RAG: kiem lech phien ban, tu nap lai neu can -------------------
# KHONG de nguoi dung phai NHO buoc nay — xem ghi chu trong ban .sh.
Say ""; Say "--- Kho RAG ---"
docker compose --profile home exec -T backend python scripts/kho_rag.py kiem
if ($LASTEXITCODE -ne 0) {
    Say "  -> nap lai kho (mat vai phut, co goi API embedding)"
    docker compose --profile home exec -T backend python scripts/kho_rag.py nap-lai
    if ($LASTEXITCODE -ne 0) {
        Bad "Nap lai kho RAG that bai"; $loi++
    } else {
        # BAT BUOC restart sau khi nap lai. `chromadb.PersistentClient` khong ho
        # tro nhieu tien trinh dung chung mot persist dir: nap-lai chay trong
        # tien trinh RIENG, con uvicorn giu `_client` cache o cap module tro toi
        # segment vua bi xoa -> /policy-search tra 0 ket qua, HTTP 200, khong
        # loi, khong log. Va no KHONG TAT DINH: `_get_client()` khoi tao LUOI,
        # nen server nao chua truy van lan nao truoc khi nap lai thi van chay
        # tot. Do that: 1 luot co ket qua roi 12 luot lien tiep rong, trong khi
        # Chroma dung yen 378 vector.
        # nap-lai khong the tu restart: no chay BEN TRONG chinh container do.
        docker compose --profile home restart backend | Out-Null
        if ($LASTEXITCODE -ne 0) { Bad "Restart backend sau nap lai that bai"; $loi++ }
        else { Ok "Da restart backend de no doc kho moi" }
    }
}

# Cong nay chay CA KHI khong nap lai — bat ca "ai do vua nap tay roi quen restart".
docker compose --profile home exec -T backend python scripts/kho_rag.py kiem
if ($LASTEXITCODE -ne 0) { Bad "Kho RAG van chua san sang sau buoc tren"; $loi++ }


Say "  cho backend san sang..."
# CONG NAY TUNG GIA: Invoke-WebRequest qua "http://localhost/health" di qua
# Caddy. Backend chet han -> Caddy chuyen /health sang /login -> Next phuc vu
# trang login KHONG CAN backend -> 200 -> cong van xanh trong khi backend da
# chet. Hoi THANG backend qua docker compose exec, dung python3 + urllib
# (anh slim khong dam bao co curl — cung ly do HEALTHCHECK trong Dockerfile
# da chon urllib thay vi curl).
$san = $false
foreach ($i in 1..30) {
    docker compose --profile home exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8010/health', timeout=5)" *> $null
    if ($LASTEXITCODE -eq 0) { $san = $true; break }
    Start-Sleep -Seconds 2
}
if ($san) { Ok "backend song (health noi bo qua docker exec)" } else { Bad "backend khong song sau 60s (health noi bo that bai)"; $loi++ }

# --- CONG SO MODEL: .env doc lap voi git, khong ai soat -- dung nguyen nhan
# gay 403 hang loat 25/08 (.env tro sai model, khong ai phat hien vi khong
# nam trong lich su commit nao). $ModelDuKien la nguon THU HAI de SO, KHONG
# phai noi dat cau hinh that -- .env/docker-compose.yml van la noi that. Doc
# gia tri DA GIAI QUYET boi app (src.config.LLM_MODEL), khong doc text .env:
# .env co the khong co dong nay va roi ve mac dinh cua docker-compose.yml,
# doc text se bao "thieu" trong khi app van chay dung.
if ($san) {
    $modelThat = (docker compose --profile home exec -T backend python -c "from src.config import LLM_MODEL; print(LLM_MODEL)" 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $modelThat) {
        Bad "Khong doc duoc LLM_MODEL dang chay tu backend"; $loi++
    } else {
        $modelThat = $modelThat.Trim()
        if ($modelThat -eq $ModelDuKien) {
            Ok "LLM_MODEL dang chay khop ghim: $modelThat"
        } else {
            Bad "LLM_MODEL dang chay ($modelThat) LECH voi ghim ($ModelDuKien)"
            Warn "        Doi model CO CHU DICH? Chay lai voi -ModelDuKien '$modelThat'."
            Warn "        Khong chu dich? Sua LLM_MODEL trong .env roi chay lai script nay."
            $loi++
        }
    }
}

# Truoc ban va /health o tren, cong nay va /health kiem TRUNG NHAU: ca hai
# deu do FRONTEND phuc vu, khong cai nao cham backend. Sau ban va: /health (o
# tren) = backend song, cong nay = frontend song -- hai cong THAT, khong phai
# mot cong lap lai. DUNG xoa vi thay "thua".
try {
    $r = Invoke-WebRequest -Uri "http://localhost/login" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    if ($r.StatusCode -eq 200) { Ok "Trang dang nhap tra 200" } else { Bad "Trang dang nhap tra $($r.StatusCode)"; $loi++ }
} catch { Bad "Khong mo duoc trang dang nhap: $_"; $loi++ }

# postgres/redis/backend co Docker HEALTHCHECK that (docker-compose.yml) -->
# doc thang trang thai do, chinh xac hon "status=running" (co the trung
# khoanh khac container vua restart trong crash-loop).
foreach ($s in @("postgres","redis","backend")) {
    $cid = (docker compose --profile home ps -q $s)
    $health = $null
    if ($cid) { $health = (docker inspect --format "{{.State.Health.Status}}" $cid 2>$null) }
    if ($health -eq "healthy") { Ok "service $s healthy (Docker healthcheck that)" }
    else { Bad "service $s KHONG healthy (trang thai: $health)"; $loi++ }
}
# frontend/caddy/cloudflared KHONG co Docker healthcheck rieng -> "running"
# la tin hieu re nhat co, chua do tat dinh. NGHI VAN, chua nang thanh phat
# hien: co the trung khoanh khac container vua restart trong crash-loop.
$chay = (docker compose --profile home ps --services --filter "status=running")
foreach ($s in @("frontend","caddy","cloudflared")) {
    if ($chay -contains $s) { Ok "service $s dang chay (NGHI VAN: status=running, chua do tat dinh)" } else { Bad "service $s KHONG chay"; $loi++ }
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
