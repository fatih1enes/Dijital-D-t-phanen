#!/usr/bin/env bash
# ================================================================
#                    DİJİTAL KÜTÜPHANE (macOS & Linux)
# ================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================"
echo "                    DIJITAL KUTUPHANE"
echo "================================================================"
echo ""

# 1. Python 3 Kontrolü
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[HATA] Python 3 sisteminizde bulunamadı!"
    echo "macOS için: brew install python"
    echo "veya https://www.python.org/downloads/ adresinden yükleyebilirsiniz."
    exit 1
fi

# 2. .env Dosyası Kontrolü (Yoksa güvenli varsayılanlarla üret)
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "[BİLGİ] İlk çalıştırma tespit edildi. .env yapılandırması oluşturuluyor..."
    RND_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || date +%s | shasum -a 256 | head -c 64)
    cat <<EOF > "$SCRIPT_DIR/.env"
# Dijital Kütüphane Ortam Değişkenleri
AUTO_OPEN_BROWSER=True
ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
MAX_UPLOAD_MB=250
ACCESS_PASSWORD=
COOKIE_SECURE=0
SESSION_SECRET=$RND_SECRET
EOF
fi

# 3. Sanal Ortam (venv) Kurulumu ve Kontrolü
VENV_DIR="$HOME/.dijital_kutuphane_venv"
if [ -d "$SCRIPT_DIR/.venv" ]; then
    VENV_DIR="$SCRIPT_DIR/.venv"
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[1/3] İlk kurulum tespit edildi. Sanal ortam oluşturuluyor: $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    echo "[2/3] Bağımlılıklar yükleniyor (requirements.txt)..."
    "$VENV_DIR/bin/pip" install --upgrade pip >/dev/null 2>&1
    "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    echo "[OK] Kurulum başarıyla tamamlandı!"
else
    # Eksik paket kontrolü
    if ! "$VENV_DIR/bin/python" -c "import fastapi, uvicorn, telethon, aiosqlite, google.genai, pdfplumber, pydantic, PIL, pypdfium2, defusedxml, numpy, fastapi_cache" >/dev/null 2>&1; then
        echo "[GÜNCELLEME] Eksik veya yeni eklenen kütüphaneler tespit edildi. Yükleniyor..."
        "$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    fi
fi

# 4. Uygulamayı Başlat
echo ""
echo "[2/2] Dijital Kütüphane başlatılıyor..."
echo "----------------------------------------------------------------"
echo "Tarayıcınız otomatik açılacaktır: http://localhost:8000"
echo "Durdurmak için: Ctrl+C"
echo "----------------------------------------------------------------"
echo ""

export AUTO_OPEN_BROWSER=True
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py"
