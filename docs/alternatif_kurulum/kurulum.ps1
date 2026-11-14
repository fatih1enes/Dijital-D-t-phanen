# cspell:disable
# Dijital Kütüphane — Tam Otomatik Kurulum Betiği
# Hata durumunda durmak için:
$ErrorActionPreference = "Stop"

# --- Yardımcı Fonksiyonlar ---
function Write-Step($msg)  { Write-Host "`n[>] $msg" -ForegroundColor Cyan }
function Write-OK($msg)    { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Skip($msg)  { Write-Host "    [--] $msg" -ForegroundColor Gray }
function Write-Warn($msg)  { Write-Host "    [!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg)  { Write-Host "    [X]  $msg" -ForegroundColor Red }

# Proje kök dizinini belirle (kurulum klasörünün 2 üstü veya requirements.txt içeren dizin)
$ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path (Join-Path $ROOT "requirements.txt"))) {
    $ROOT = Split-Path -Parent $PSScriptRoot
}
Set-Location $ROOT

Write-Host ""
Write-Host " ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host " ║       Dijital Kütüphane — Tam Otomatik Kurulum           ║" -ForegroundColor Magenta
Write-Host " ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
Write-Host ""

# ──────────────────────────────────────────────────────────────
# ADIM 1: Python Kontrolü
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 1/7 — Python Kontrolü"

$pythonCmd = $null
foreach ($cmd in @("python", "py")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(1[0-9]|[1-9]\d)") {
            $pythonCmd = $cmd
            Write-OK "Python bulundu: $ver"
            break
        } elseif ($ver -match "Python 3\.") {
            Write-Warn "Python 3.x bulundu ama sürüm eski olabilir: $ver (3.10+ önerilir)"
            $pythonCmd = $cmd
            break
        }
    } catch { }
}

if (-not $pythonCmd) {
    Write-Warn "Python bulunamadı. winget ile Python 3.12 kuruluyor..."
    try {
        winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
        # PATH'i yenile
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        $pythonCmd = "python"
        Write-OK "Python kurulumu tamamlandı."
    } catch {
        Write-Fail "Python otomatik kurulamadı!"
        Write-Fail "Lütfen https://www.python.org/downloads/ adresinden Python 3.10+ kurun ve tekrar çalıştırın."
        Write-Host ""
        Read-Host "Devam etmek için Enter'a basın"
        exit 1
    }
}

# ──────────────────────────────────────────────────────────────
# ADIM 2: Sanal Ortam Oluşturma
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 2/7 — Sanal Ortam (virtualenv)"

$venvPath = Join-Path $ROOT ".venv"
$pipExe   = Join-Path $venvPath "Scripts\pip.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

if (Test-Path $pipExe) {
    Write-Skip "Sanal ortam zaten mevcut, atlanıyor."
} else {
    Write-Host "    Sanal ortam oluşturuluyor: $venvPath" -ForegroundColor Gray
    & $pythonCmd -m venv $venvPath
    Write-OK "Sanal ortam oluşturuldu."
}

# pip'i güncelle
Write-Host "    pip güncelleniyor..." -ForegroundColor Gray
& $pythonExe -m pip install --upgrade pip --quiet

# ──────────────────────────────────────────────────────────────
# ADIM 3: Python Kütüphaneleri
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 3/7 — Python Kütüphaneleri Yükleniyor"

$reqFile = Join-Path $ROOT "requirements.txt"
Write-Host "    $reqFile dosyası yükleniyor..." -ForegroundColor Gray
& $pipExe install -r $reqFile
Write-OK "Tüm Python kütüphaneleri yüklendi."

# ──────────────────────────────────────────────────────────────
# ADIM 4: Poppler Kurulumu
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 4/7 — Poppler (PDF Görselleştirme)"

$popplerDir = Join-Path $ROOT "poppler"
if (Test-Path (Join-Path $PSScriptRoot "poppler")) {
    $popplerDir = Join-Path $PSScriptRoot "poppler"
}
$popplerBin = Join-Path $popplerDir "Library\bin"
# Eski yapı için de kontrol et
$popplerBinAlt = Join-Path $popplerDir "bin"

$popplerOK = (Test-Path (Join-Path $popplerBin "pdftoppm.exe")) -or (Test-Path (Join-Path $popplerBinAlt "pdftoppm.exe"))

if ($popplerOK) {
    Write-Skip "Poppler zaten kurulu, atlanıyor."
} else {
    Write-Host "    Poppler indiriliyor (GitHub)..." -ForegroundColor Gray
    
    # conda-forge'dan kurulum (en güvenilir kaynak)
    $popplerUrl = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    $zipPath    = Join-Path $env:TEMP "poppler.zip"
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $popplerUrl -OutFile $zipPath -UseBasicParsing
        
        Write-Host "    Poppler çıkartılıyor..." -ForegroundColor Gray
        if (Test-Path $popplerDir) { Remove-Item $popplerDir -Recurse -Force }
        New-Item -ItemType Directory -Path $popplerDir | Out-Null
        
        Expand-Archive -Path $zipPath -DestinationPath $popplerDir -Force
        Remove-Item $zipPath -ErrorAction SilentlyContinue
        
        # ZIP içindeki yapıyı düzelt (alt klasör varsa taşı)
        $inner = Get-ChildItem $popplerDir -Directory | Select-Object -First 1
        if ($inner -and (Test-Path (Join-Path $inner.FullName "Library\bin\pdftoppm.exe"))) {
            # İçerideki dosyaları dışarıya taşı
            $innerItems = Get-ChildItem $inner.FullName
            foreach ($item in $innerItems) {
                Move-Item $item.FullName $popplerDir -Force
            }
            Remove-Item $inner.FullName -Recurse -Force -ErrorAction SilentlyContinue
        }
        
        Write-OK "Poppler indirildi ve kuruldu: $popplerDir"
    } catch {
        Write-Warn "Poppler otomatik indirilemedi: $_"
        Write-Warn "Elle kurulum için: https://github.com/oschwartz10612/poppler-windows/releases"
        Write-Warn "İndirdiğiniz ZIP'i '$popplerDir' klasörüne çıkartın."
    }
}

# Poppler bin yolunu bul ve USER PATH'e ekle
$popplerBinFinal = $null
if     (Test-Path (Join-Path $popplerBin "pdftoppm.exe"))    { $popplerBinFinal = $popplerBin }
elseif (Test-Path (Join-Path $popplerBinAlt "pdftoppm.exe")) { $popplerBinFinal = $popplerBinAlt }

if ($popplerBinFinal) {
    $currentUserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentUserPath -notlike "*$popplerBinFinal*") {
        [System.Environment]::SetEnvironmentVariable("Path", "$currentUserPath;$popplerBinFinal", "User")
        $env:Path += ";$popplerBinFinal"
        Write-OK "Poppler bin klasörü PATH'e eklendi: $popplerBinFinal"
    } else {
        Write-Skip "Poppler zaten PATH'te."
    }
}

# ──────────────────────────────────────────────────────────────
# ADIM 5: Tesseract-OCR Kurulumu
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 5/7 — Tesseract-OCR (Metin Tanıma)"

$tesseractExe = "C:\Program Files\Tesseract-OCR\tesseract.exe"
$tesseractExeAlt = "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"

if ((Test-Path $tesseractExe) -or (Test-Path $tesseractExeAlt)) {
    Write-Skip "Tesseract zaten kurulu, atlanıyor."
} else {
    Write-Host "    Tesseract indiriliyor (UB-Mannheim)..." -ForegroundColor Gray
    
    $tesseractUrl   = "https://github.com/UB-Mannheim/tesseract/releases/download/v5.5.0.20241111/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
    $installerPath  = Join-Path $env:TEMP "tesseract_setup.exe"
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $tesseractUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "    Tesseract kuruluyor (sessiz mod — yönetici izni gerekebilir)..." -ForegroundColor Gray
        # /S = sessiz kurulum, /LANG=tur = Türkçe dil paketi
        Start-Process -FilePath $installerPath -ArgumentList "/S", "/LANG=tur" -Wait -Verb RunAs
        
        Remove-Item $installerPath -ErrorAction SilentlyContinue
        
        if (Test-Path $tesseractExe) {
            Write-OK "Tesseract başarıyla kuruldu: $tesseractExe"
            # PATH'e ekle
            $currentUserPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
            $tessDir = "C:\Program Files\Tesseract-OCR"
            if ($currentUserPath -notlike "*$tessDir*") {
                [System.Environment]::SetEnvironmentVariable("Path", "$currentUserPath;$tessDir", "User")
                $env:Path += ";$tessDir"
            }
        } else {
            Write-Warn "Tesseract kurulum tamamlandı ancak doğrulanamadı."
        }
    } catch {
        Write-Warn "Tesseract otomatik indirilemedi: $_"
        Write-Warn "Elle kurulum için: https://github.com/UB-Mannheim/tesseract/wiki"
        Write-Warn "OCR özelliği olmadan uygulama çalışmaya devam eder."
    }
}

# ──────────────────────────────────────────────────────────────
# ADIM 6: Klasör Yapısı
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 6/7 — Klasör Yapısı Kontrolü"

$dirs = @("veriler\thumbnails", "veriler\Dijital_Kutuphane", "veriler\logs", "veriler\Kaldirilmis_PDFler")
foreach ($dir in $dirs) {
    $dirPath = Join-Path $ROOT $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Write-OK "Oluşturuldu: $dir"
    } else {
        Write-Skip "Mevcut: $dir"
    }
}

# ──────────────────────────────────────────────────────────────
# ADIM 7: Yapılandırma Dosyaları
# ──────────────────────────────────────────────────────────────
Write-Step "ADIM 7/7 — Yapılandırma Dosyaları"

# .env şablonu
$envFile = Join-Path $ROOT ".env"
if (-not (Test-Path $envFile)) {
    @"
# Gemini API anahtarınızı buraya yazabilirsiniz (isteğe bağlı).
# Bu dosya .gitignore'da olduğu için güvenlidir.
# GEMINI_API_KEY=AIzaSy...
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-OK ".env şablon dosyası oluşturuldu."
} else {
    Write-Skip ".env zaten mevcut."
}

# config.json şablonu
$configFile = Join-Path $ROOT "config.json"
if (-not (Test-Path $configFile)) {
    @"
{
    "ai_api_key": "",
    "gemini_model": "gemini-3.5-flash-lite",
    "max_pages": 10,
    "ocr_pages": 20,
    "vision_pages": 20,
    "vision_max_image_dim": 1200,
    "vision_jpeg_quality": 82,
    "tesseract_cmd": ""
}
"@ | Out-File -FilePath $configFile -Encoding utf8
    Write-OK "config.json şablon dosyası oluşturuldu."
} else {
    Write-Skip "config.json zaten mevcut."
}

# ──────────────────────────────────────────────────────────────
# TAMAMLANDI
# ──────────────────────────────────────────────────────────────
Write-Host ""
Write-Host " ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host " ║            KURULUM BAŞARIYLA TAMAMLANDI!                 ║" -ForegroundColor Green
Write-Host " ╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host " ║  Sonraki adımlar:                                        ║" -ForegroundColor Green
Write-Host " ║  1. Ana dizindeki 'BASLAT.bat' dosyasina cift tiklayin     ║" -ForegroundColor Green
Write-Host " ║  2. Açılan arayüzde Ayarlar >> Gemini API Key girin      ║" -ForegroundColor Green
Write-Host " ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Read-Host "Çıkmak için Enter'a basın"
