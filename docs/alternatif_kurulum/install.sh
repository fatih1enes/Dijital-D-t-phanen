#!/bin/bash

# Dijital Kütüphane — Linux/Mac Installation Script
# Exit on error
set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_step() { echo -e "${CYAN}[>] $1${NC}"; }
print_ok() { echo -e "${GREEN}    [OK] $1${NC}"; }
print_skip() { echo -e "${YELLOW}    [--] $1${NC}"; }
print_warn() { echo -e "${YELLOW}    [!] $1${NC}"; }
print_fail() { echo -e "${RED}    [X] $1${NC}"; }

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo " ╔══════════════════════════════════════════════════════════╗"
echo " ║       Dijital Kütüphane — Linux/Mac Installation        ║"
echo " ╚══════════════════════════════════════════════════════════╝"
echo ""

# STEP 1: Python check
print_step "STEP 1/6 — Python Check"

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" > /dev/null 2>&1; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            PYTHON_CMD="$cmd"
            print_ok "Python found: $($cmd --version)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    print_fail "Python 3.10+ not found"
    echo "Please install Python 3.10 or higher from https://www.python.org/downloads/"
    exit 1
fi

# STEP 2: Virtual environment
print_step "STEP 2/6 — Virtual Environment"

VENV_PATH="$ROOT_DIR/.venv"
PYTHON_EXE="$VENV_PATH/bin/python"
PIP_EXE="$VENV_PATH/bin/pip"

if [ -f "$PYTHON_EXE" ]; then
    print_skip "Virtual environment already exists"
else
    print_ok "Creating virtual environment: $VENV_PATH"
    $PYTHON_CMD -m venv "$VENV_PATH"
fi

# Upgrade pip
print_ok "Upgrading pip..."
"$PIP_EXE" install --upgrade pip --quiet

# STEP 3: Python dependencies
print_step "STEP 3/6 — Python Dependencies"

REQ_FILE="$ROOT_DIR/requirements.txt"
if [ -f "$REQ_FILE" ]; then
    print_ok "Installing from $REQ_FILE"
    "$PIP_EXE" install -r "$REQ_FILE"
else
    print_warn "requirements.txt not found, skipping"
fi

# STEP 4: System dependencies (Poppler & Tesseract)
print_step "STEP 4/6 — System Dependencies"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        if brew list poppler &> /dev/null; then
            print_skip "Poppler already installed"
        else
            print_ok "Installing Poppler via Homebrew"
            brew install poppler
        fi
        
        if brew list tesseract &> /dev/null; then
            print_skip "Tesseract already installed"
        else
            print_ok "Installing Tesseract via Homebrew"
            brew install tesseract
            brew install tesseract-lang
        fi
    else
        print_warn "Homebrew not found. Please install manually:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "  brew install poppler tesseract tesseract-lang"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        if dpkg -l | grep -q poppler-utils; then
            print_skip "Poppler already installed"
        else
            print_ok "Installing Poppler via apt"
            sudo apt-get update -qq
            sudo apt-get install -y poppler-utils
        fi
        
        if dpkg -l | grep -q tesseract-ocr; then
            print_skip "Tesseract already installed"
        else
            print_ok "Installing Tesseract via apt"
            sudo apt-get install -y tesseract-ocr tesseract-ocr-tur tesseract-ocr-eng
        fi
    elif command -v yum &> /dev/null; then
        if rpm -q poppler-utils &> /dev/null; then
            print_skip "Poppler already installed"
        else
            print_ok "Installing Poppler via yum"
            sudo yum install -y poppler-utils
        fi
        
        if rpm -q tesseract &> /dev/null; then
            print_skip "Tesseract already installed"
        else
            print_ok "Installing Tesseract via yum"
            sudo yum install -y tesseract
        fi
    else
        print_warn "Package manager not detected. Please install manually:"
        echo "  Poppler: https://poppler.freedesktop.org/"
        echo "  Tesseract: https://github.com/tesseract-ocr/tesseract"
    fi
else
    print_warn "Unsupported OS. Please install Poppler and Tesseract manually."
fi

# STEP 5: Directory structure
print_step "STEP 5/6 — Directory Structure"

DIRS=("veriler/thumbnails" "veriler/Dijital_Kutuphane" "veriler/logs" "veriler/Kaldirilmis_PDFler")
for dir in "${DIRS[@]}"; do
    FULL_DIR="$ROOT_DIR/$dir"
    if [ ! -d "$FULL_DIR" ]; then
        mkdir -p "$FULL_DIR"
        print_ok "Created: $dir"
    else
        print_skip "Exists: $dir"
    fi
done

# STEP 6: Configuration files
print_step "STEP 6/6 — Configuration Files"

# .env template
ENV_FILE="$ROOT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# Gemini API anahtarınızı buraya yazabilirsiniz (isteğe bağlı).
# Bu dosya .gitignore'da olduğu için güvenlidir.
# GEMINI_API_KEY=AIzaSy...
EOF
    print_ok ".env template created"
else
    print_skip ".env already exists"
fi

# config.json template
CONFIG_FILE="$ROOT_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
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
EOF
    print_ok "config.json template created"
else
    print_skip "config.json already exists"
fi

# DONE
echo ""
echo -e "${GREEN} ╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN} ║            INSTALLATION COMPLETED SUCCESSFULLY!          ║${NC}"
echo -e "${GREEN} ╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN} ║  Next steps:                                             ║${NC}"
echo -e "${GREEN} ║  1. Activate virtual environment:                        ║${NC}"
echo -e "${GREEN} ║     source $VENV_PATH/bin/activate                       ║${NC}"
echo -e "${GREEN} ║  2. Run the application:                                 ║${NC}"
echo -e "${GREEN} ║     python main.py                                       ║${NC}"
echo -e "${GREEN} ║  3. Open http://127.0.0.1:8000 in your browser           ║${NC}"
echo -e "${GREEN} ╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
