# Dijital Kütüphane (Digital Library)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite WAL + FTS5](https://img.shields.io/badge/SQLite-WAL%20%2B%20FTS5-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](docker-compose.yml)

**Yerel öncelikli, yapay zeka destekli kişisel dijital kütüphane ve araştırma çalışma alanı.**  
PDF, EPUB ve TXT arşivlerinizi kendi bilgisayarınızda veya sunucunuzda saklar; metaveri çıkarımı, tam metin arama (FTS5 + vektör RAG), kitap içi sohbet, OCR, OPDS 1.2 ve mobil aktarım özelliklerini tek bir editoryal arayüzde sunar.

> *A local-first, AI-powered personal digital library and research workspace built with FastAPI and SQLite (WAL + FTS5). Designed around an editorial "Paper & Ink" interface with hybrid Cloud/Local AI, ChromaGuard™ reading modes, OPDS 1.2 cataloging, and QR mobile handoff.*

[**Türkçe**](#türkçe) · [**English**](#english) · [**Sistem Mimarisi**](#architecture) · [**Proje Yapısı**](#project-structure) · [**Geliştirme & Test**](#development) · [**📖 Kullanım Kılavuzu**](KULLANIM_KILAVUZU.md)

---

<a id="türkçe"></a>
## Türkçe

### Neden Dijital Kütüphane?

- **Tam Veri Sahipliği:** Kitaplarınız, kapak görselleriniz, notlarınız ve SQLite veritabanınız yalnızca yerel `veriler/` dizininde tutulur; üçüncü parti bir bulut kütüphanesine bağımlı değildir.
- **Hibrit Yapay Zeka:** İster **Google Gemini** (ücretsiz katman dahil, kademeli model zinciriyle) ister **Ollama / LM Studio** (OpenAI uyumlu yerel modeller) ile tamamen çevrimdışı çalışır.
- **"Kâğıt ve Mürekkep" (Paper & Ink) Editoryal Arayüzü:** Koyu SaaS panelleri yerine sıcak kâğıt tonları, toprak vurgular, `Instrument Serif` / `Newsreader` / `Geist` tipografisi ve harici JS framework'ü olmadan geliştirilen mekânsal View Transitions geçişleri kullanır.

### Öne Çıkan Özellikler

#### Okuma, Tipografi ve Araştırma Çalışma Alanı
- **ChromaGuard™ Akıllı Okuma Yüzeyi:** Gündüz, Sepya, E-Ink ve Gece (OLED anti-ghosting) modlarıyla göz yorgunluğunu azaltan kontrast dengesi ve duyarlı tipografi.
- **Doğal Sinirsel Seslendirme (Neural TTS + 60 FPS Karaoke):** Microsoft `edge-tts` (Türkçe doğal Ahmet/Emel sesleri) ile kitapları dinleme; sesle eşzamanlı kelime ve cümle bazlı akıcı karaoke takibi.
- **Taranmış PDF'ler İçin Görünmez OCR Katmanı:** Taranmış (salt resim) PDF'leri Tesseract ile işleyerek piksel hizalı, seçilebilir ve kopyalanabilir görünmez metin katmanı üretimi.
- **Küçük Sayfa Önizleme Şeridi (Filmstrip) & Yer İmleri:** Sayfalar arasında hızlı gezinme sağlayan görsel şerit çekmecesi, yer imleri ve otomatik PDF İçindekiler (TOC) haritası.
- **Zengin EPUB Tipografisi & Etkileşimli Dipnotlar:** EPUB içi resim büyütme, editoryal `Aa` tipografi ayarları ve sayfadan koparmayan interaktif dipnot önizleme balonları.
- **Akıllı Çalışma Alanı (Workspace):** Metin seçerek anında not/renkli vurgu alma ve PDF sayfa sapması (offset) çözümleme.
- **Mobil Handoff:** Masaüstünde açık olan kitabın tam sayfa konumunu dinamik QR kod ile telefonunuza aktarıp kesintisiz devam etme.
- **OPDS 1.2 Kablosuz Katalog (`/opds`):** KOReader, Moon+ Reader, Apple Books ve uyumlu e-okuyucular için standart kablosuz katalog akışı.

#### Hibrit Yapay Zeka, Vektör RAG & Bilişsel Hafıza
- **Gerçek Anlamsal Vektör Gömme (Hybrid RAG):** SQLite **FTS5** tam metin araması ile 3 katmanlı semantik vektör gömme (`ONNX` yerel model, `Gemini Text-Embedding-004` ve deterministik hash) ve hibrit yeniden sıralama (Rerank).
- **Gerçek SSE Token Akışı & Doğrulanabilir Kanıt Balonları:** AI kitap sohbetinde kelime kelime akıcı token akışı (True Streaming) ve cevabın hangi sayfadan alındığını gösteren tıklanabilir sayfa kanıt balonları.
- **FSRS v5 Aktif Hatırlama & Aralıklı Tekrar:** Kitap notları ve vurgularından FSRS (Free Spaced Repetition Scheduler v5) algoritmasıyla kişiselleştirilmiş hafıza kartları ve günlük çalışma stüdyosu.
- **Gemini Cascade Motoru:** Modeller (`gemini-3.8-flash` → `gemini-3.5-flash-lite`) arasında otomatik yedekleme zinciri ve HTTP 429 kota aşımlarına karşı üstel geri çekilmeli yeniden deneme.
- **Bilgi Grafiği, Çoklu Ajan Münazarası & Keşif:** Kavram ilişkileri (`knowledge_graph`), çoklu ajan tartışma akışı (`multi_agent_debate`) ve tesadüfi keşif motoru (`serendipity_engine`).
- **Otomatik Analiz:** Yüklenen eserlerden başlık, yazar, kategori, etiket ve editoryal özet üretimi.

#### İçe Aktarma, Otomasyon ve Bakım
- **Çoklu Format & OCR:** `pypdfium2`, `pdfplumber` ve Poppler ile PDF, EPUB ve TXT işleme; taranmış PDF'ler için **Tesseract OCR**.
- **Canlı İşlem Merkezi:** WebSocket (`/ws`) üzerinden anlık görev kuyruğu, canlı ilerleme yüzdesi ve terminal log akışı; çökme sonrası kurtarma destekli dayanıklı kuyruk (`durable_queue`).
- **Gölge Kütüphaneci (Watchfolder):** Belirlenen klasöre düşen yeni PDF/EPUB dosyalarını otomatik algılayıp analiz kuyruğuna alma.
- **Telegram Senkronizasyonu:** Telethon aracılığıyla Telegram mesaj/kanallarından doğrudan kitap aktarımı.
- **Mükerrer Eser Avcısı & PDF Optimize Edici:** SHA-256 hash ve başlık/yazar benzerliği ile çift kopya tespiti; yerel PDF boyut sıkıştırma.
- **Taşınabilir Yedekleme & PKM Dışa Aktarma:** Veritabanı, ayarlar ve kitaplar için tek tıkla ZIP yedeği; notları **Obsidian** (`.md`), **Anki** (`.tsv`) ve **BibTeX** (`.bib`) olarak dışa aktarma.

#### Güvenlik, Çevrimdışı Kasa ve Platform Desteği
- **Çevrimdışı Okuma Kasası (IndexedDB Offline Vault):** Kitapları tarayıcının yerel hafızasına güvenle mühürleyerek internet bağlantısı yokken bile kesintisiz okuma ve yerel ilerleme kaydı.
- **Çapraz Platform:** Windows, macOS (Apple Silicon M1/M2/M3/M4 ve Intel) ile Linux üzerinde %100 yerel ve optimize çalışma.
- **Yerel ve Uzak Erişim Güvenliği:** SQLite WAL modu, parola kapısı (`ACCESS_PASSWORD`), imzalı oturum çerezleri (`SESSION_SECRET`), brute-force hız sınırlama ve CORS/Origin doğrulaması.
- **Çevrimdışı Hazır PWA & Masaüstü Kabuğu:** Service Worker (`static/sw.js`) ile PWA desteği ve isteğe bağlı **PyWebView + Pystray** masaüstü uygulaması (`desktop_shell.py`).

### Hızlı Başlangıç

#### Seçenek 1: Windows Tek Tıkla Kurulum (`BASLAT.bat`)
1. Python 3.10+ kurulumunda **`Add python.exe to PATH`** seçeneğini işaretleyin.
2. Proje ana dizinindeki **`BASLAT.bat`** dosyasına çift tıklayın.
   - Sanal ortamı (`.venv` veya `%USERPROFILE%\.dijital_kutuphane_venv`) kurar,
   - `requirements.txt` bağımlılıklarını yükler,
   - `.env` dosyasını otomatik hazırlar ve `http://localhost:8000` adresini tarayıcıda açar.

#### Seçenek 2: macOS ve Linux Tek Komutla Kurulum (`baslat.sh`)
Mac (Apple Silicon & Intel) ve Linux kullanıcıları için tek tıkla / tek komutla başlatma:

```bash
chmod +x baslat.sh
./baslat.sh
```
*Bu betik Python 3 ortamını denetler, `.venv` sanal ortamını kurar, kütüphaneleri yükler, güvenli `.env` oluşturur ve kütüphaneyi tarayıcınızda otomatik başlatır.*

> [!TIP]
> **macOS Kullanıcıları İçin OCR Desteği (Tesseract & Poppler):**  
> Taranmış görsel PDF'lerde görünmez metin katmanı çıkarmak için Mac terminalinde Homebrew ile tek satırda kurulum yapabilirsiniz:
> ```bash
> brew install tesseract tesseract-lang poppler
> ```
> *Dijital Kütüphane, Homebrew'in kurduğu Tesseract yolunu (`/opt/homebrew/bin/tesseract` veya `/usr/local/bin/tesseract`) otomatik olarak tanır.*

#### Seçenek 3: Docker / Docker Compose
Poppler, Tesseract OCR (`tur` + `eng`) ve tüm Python bağımlılıkları hazır gelir.

```bash
cp .env.example .env
# ÖNEMLİ: Docker dış ağa açık çalıştığı için .env içinde güçlü bir ACCESS_PASSWORD tanımlayın.
docker compose up -d --build
```
Sunucu hazır olduğunda `http://localhost:8000` adresinden erişebilirsiniz (`/health` uç noktası konteyner sağlık kontrolünü sağlar; kalıcı veriler `./veriler` klasöründe tutulur).

#### Seçenek 4: Standart Manuel Python Kurulumu
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

#### Seçenek 5: Masaüstü Uygulaması Modu (PyWebView + Sistem Tepsisi)
```bash
pip install -e ".[desktop]"
python desktop_shell.py
```

#### İlk Kurulum Sonrası 3 Adım
1. Tarayıcıda **`http://localhost:8000`** adresini açın.
2. Sağ üst köşedeki **⚙️ Ayarlar** penceresinden **Google Gemini** API anahtarınızı girin veya **Ollama / LM Studio** yerel sunucu adresinizi seçin.
3. İlk PDF, EPUB veya TXT dosyanızı sürükleyip bırakın; sağ üstteki **İşlem Merkezi** kapsülünden canlı analiz sürecini izleyin.

> [!TIP]
> Taranmış (görsel tabanlı) PDF'ler için sisteminizde **Tesseract OCR** ve **Poppler** kurulu olması önerilir. Ayrıntılı anlatım, Gemini API anahtarı alma ve Telegram kurulumu için [**KULLANIM_KILAVUZU.md**](KULLANIM_KILAVUZU.md) rehberine bakın.

### Yapılandırma (`.env`)

Tüm şablon değişkenleri [`.env.example`](.env.example) dosyasında belgelenmiştir:

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `PORT` / `HOST` | Sunucu portu ve dinleme adresi | `8000` / `127.0.0.1` (`.env.example`: `0.0.0.0`) |
| `ACCESS_PASSWORD` | Kütüphane giriş parolası (**Docker ve uzak erişim için zorunlu**) | Boş (yalnızca `localhost` erişebilir) |
| `ALLOW_UNPROTECTED_REMOTE_ACCESS` | Uzaktan şifresiz erişime açıkça izin ver (**önerilmez**) | `False` |
| `SESSION_SECRET` | Oturum çerezi imzalama anahtarı (boşsa `veriler/.session_secret` üretilir) | Otomatik üretilir |
| `GEMINI_API_KEY` | Google Gemini bulut AI anahtarı (Ayarlar menüsünden de girilebilir) | Yok |
| `ALLOWED_ORIGINS` | CORS / WebSocket için izinli origin listesi | `http://127.0.0.1:8000,http://localhost:8000` |
| `MAX_UPLOAD_MB` | Maksimum dosya yükleme boyutu (MB) | `250` |
| `MAX_CONCURRENT_TASKS` | Eşzamanlı arka plan görev sayısı | `1` |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | Telethon ile Telegram kitap aktarımı kimlik bilgileri | Yok |
| `TRUST_PROXY` | Nginx / Traefik / Cloudflare arkasında `X-Forwarded-*` güveni | `False` |
| `LOG_LEVEL` | Günlükleme seviyesi (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

> [!IMPORTANT]
> Güvenlik gereği `ACCESS_PASSWORD` boş bırakıldığında uygulama yalnızca yerel (`localhost` / `127.0.0.1`) isteklere izin verir; dış ağdan gelen istekler `403` ile reddedilir.

---

<a id="architecture"></a>
## Sistem Mimarisi / Architecture

```mermaid
flowchart TD
    subgraph Clients["Erişim Arayüzleri ve Cihazlar (Clients)"]
        WEB["Editoryal Web Arayüzü ve PWA (Kâğıt ve Mürekkep)"]
        DESKTOP["Masaüstü Kabuğu (PyWebView + Pystray)"]
        OPDS_CLIENTS["E-Okuyucular (KOReader, Moon+, Apple Books)"]
        MOBILE_HANDOFF["Mobil Cihazlar (QR Kod Handoff)"]
    end

    subgraph Gateway["FastAPI Ağ Geçidi ve Güvenlik"]
        ROUTER["FastAPI Router ve Jinja2 / Statik Sunucu"]
        SECURITY["Güvenlik Katmanı (Session, Rate Limiting, CORS/Origin)"]
        OPDS_FEED["OPDS 1.2 Katalog Beslemesi (/opds)"]
        WS_SYNC["WebSocket Canlı Durum ve İşlem Merkezi (/ws)"]
    end

    subgraph CoreServices["Çekirdek Servisler ve Kuyruk"]
        QUEUE["Dayanıklı Görev Kuyruğu & Event Bus"]
        CHROMA["ChromaGuard™ Okuma Yüzeyi & Çalışma Alanı"]
        DOC_PROC["Belge & OCR Motoru (pypdfium2, pdfplumber, Poppler, Tesseract)"]
        EXTRAS["Mükerrer Avcısı, PDF Sıkıştırma, Watchfolder, Telegram, PKM"]
    end

    subgraph AIEngine["Hibrit Zeka & Arama Katmanı (AI & RAG)"]
        CASCADE["Gemini Cascade (Çok Kademeli Model Zinciri + 429 Toleransı)"]
        LOCAL_LLM["Yerel LLM (Ollama / LM Studio / OpenAI Uyumlu)"]
        RAG["Hibrit RAG (FTS5 + Vektör Arama, Bilgi Grafiği, Çoklu Ajan Münazarası)"]
    end

    subgraph Storage["Kalıcı Depolama (veriler/)"]
        DB[("SQLite Veritabanı (WAL Modu + FTS5)")]
        STORAGE[("Yerel Dosyalar (Kitaplar, Kapaklar, İndeksler)")]
    end

    WEB --> ROUTER
    DESKTOP --> ROUTER
    MOBILE_HANDOFF --> ROUTER
    OPDS_CLIENTS --> OPDS_FEED

    ROUTER --> SECURITY
    OPDS_FEED --> SECURITY

    SECURITY --> QUEUE
    SECURITY --> CHROMA
    SECURITY --> EXTRAS
    SECURITY --> WS_SYNC

    QUEUE --> DOC_PROC
    DOC_PROC --> CASCADE
    DOC_PROC --> LOCAL_LLM
    CHROMA --> RAG
    RAG --> CASCADE
    RAG --> LOCAL_LLM

    CHROMA --> DB
    RAG --> DB
    EXTRAS --> DB
    EXTRAS --> STORAGE
    DOC_PROC --> STORAGE
    ROUTER --> DB
    OPDS_FEED --> DB
```

---

<a id="project-structure"></a>
## Proje Yapısı / Project Structure

```text
.
├── main.py                      # FastAPI sunucu giriş noktası
├── desktop_shell.py             # İsteğe bağlı PyWebView + Pystray masaüstü kabuğu
├── BASLAT.bat                   # Windows tek tıkla kurulum ve başlatma betiği
├── Dockerfile & docker-compose.yml
├── pyproject.toml               # Proje meta verisi, ruff / black / mypy / pytest ayarları
├── requirements.txt             # Çalışma zamanı bağımlılıkları
├── requirements-dev.txt         # Geliştirme ve test bağımlılıkları
├── KULLANIM_KILAVUZU.md         # Adım adım son kullanıcı kurulum & kullanım rehberi
│
├── app/
│   ├── main.py                  # Lifespan, middleware, auth/origin korumaları, /ws
│   ├── config.py & constants.py # Ortam değişkenleri, sınırlar, yol çözümleme
│   ├── database.py & models.py  # SQLite WAL şeması, FTS5 tabloları ve modeller
│   ├── auth.py                  # Oturum doğrulama ve brute-force koruması
│   ├── task_queue.py, durable_queue.py, event_bus.py, tasks.py, websocket.py
│   ├── pdf.py & epub.py         # PDF/EPUB metin, kapak ve sayfa işleme
│   ├── routers/                 # HTTP uç noktaları: auth, books, chat, collections,
│   │                            # debate, opds, settings, tasks, telegram
│   ├── repositories/            # document_repository.py (veri erişim katmanı)
│   └── services/                # ai_service, cascade_manager, chunking_service,
│                                # embedding_service, hybrid_search, knowledge_graph,
│                                # multi_agent_debate, serendipity_engine, toc_service,
│                                # handoff_service, pdf_compressor, pkm_exporter,
│                                # smart_collections, telegram_service, watchfolder_service
│
├── templates/                   # Jinja2 HTML şablonları (kutuphane.html, login.html vb.)
├── static/
│   ├── sw.js                    # PWA Service Worker (önbellek sürümleme)
│   ├── css/
│   │   ├── app.css              # Cascade katmanları: @layer legacy, tokens, design, motion
│   │   ├── style.css            # Temel yapısal stiller (legacy)
│   │   ├── tokens.css           # Renk, tipografi ve hareket token'ları
│   │   ├── design.css           # "Kâğıt ve Mürekkep" bileşenleri ve duyarlı yerleşim
│   │   └── motion.css           # Merkezi hareket kuralları ve reduced-motion desteği
│   └── js/                      # Framework'süz modüler JS (state, motion, api, websocket, ui_*)
│
├── docs/                        # CHANGELOG, MOTION_NOTES, CONTRIBUTING, SECURITY, install.sh
└── tests/                       # Pytest birim, güvenlik, API, RAG, OPDS ve arayüz testleri
```

---

<a id="development"></a>
## Geliştirme ve Test / Development & Testing

### Geliştirici Kurulumu
```bash
pip install -r requirements-dev.txt
pip install -e .
```

### Lint ve Test Komutları
Proje CI akışı ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) Python 3.10–3.13 üzerinde Linux ve Windows için `ruff` ve `pytest` çalıştırır:
```bash
# Kod kalitesi ve stil kontrolü
ruff check .

# Tüm test paketi
pytest -v tests/
```

### Frontend Mimarisi Notları
- Harici bundler veya JS framework'ü yoktur; [static/css/app.css](static/css/app.css) içindeki `@layer legacy, tokens, design, motion;` sırası korunur.
- Etkileşim ve hareket dili yalnızca `transform` ve `opacity` üzerinden çalışır; ayrıntılar için [docs/MOTION_NOTES.md](docs/MOTION_NOTES.md) dosyasına bakın.
- Statik CSS/JS değişikliği yaptığınızda PWA önbelleğinin yenilenmesi için `templates/kutuphane.html`, `static/css/app.css` ve `static/sw.js` içindeki `?v=` sürümünü güncelleyin.

---

<a id="english"></a>
## English

### Overview

**Dijital Kütüphane** is a local-first, privacy-focused digital library and AI research workspace built with **FastAPI**, **SQLite (WAL + FTS5)**, and a dependency-free editorial **"Paper & Ink"** frontend. All books, covers, annotations, and indexes remain in your local `veriler/` directory.

### Core Capabilities

- **ChromaGuard™ Reading Surface & Workspace**: Day, Sepia, E-Ink, and Night reading themes; in-book annotations & highlights; automatic PDF TOC extraction and page-offset resolution.
- **Natural Neural TTS + 60 FPS Karaoke**: Built-in Microsoft `edge-tts` narration with word- and sentence-synchronized live karaoke highlighting.
- **Invisible OCR Text Layer**: Automatic Tesseract OCR text layer generation for scanned/image-only PDFs, making them fully searchable and selectable.
- **Interactive EPUB Typography & Filmstrip**: Rich EPUB footnotes with non-intrusive preview popovers, embedded image zoom, visual thumbnail filmstrip, and bookmarks drawer.
- **Hybrid Vector RAG & Verifiable Citations**: Combines SQLite **FTS5** with 3-tier semantic embeddings (`ONNX` local, `Gemini Text-Embedding-004`, and deterministic hash), true SSE token streaming, and clickable citation badges linking directly to referenced book pages.
- **FSRS v5 Active Recall Studio**: Intelligent spaced repetition flashcards generated from in-book highlights and notes using the Free Spaced Repetition Scheduler (FSRS v5) algorithm.
- **Offline Vault (IndexedDB)**: Cryptographically seals books into browser local storage for offline reading and local progress tracking without internet.
- **Cross-Platform**: 100% native compatibility across Windows, macOS (Apple Silicon M1/M2/M3/M4 & Intel), and Linux.
- **OPDS 1.2 & Mobile Handoff**: Wireless `/opds` catalog feed for KOReader, Moon+ Reader, and Apple Books, plus instant QR-code handoff to continue reading on mobile at the exact page.
- **Automation & Maintenance**: Live WebSocket task & log center (`durable_queue`), automated Watchfolder monitoring, Telethon Telegram sync, SHA-256 duplicate book hunter, local PDF compression, one-click ZIP backups, and **Obsidian / Anki / BibTeX** PKM exports.

### Quick Start

1. **Windows (One-Click)**
   - Double-click **`BASLAT.bat`** (creates `.venv`, installs requirements, sets up `.env`, and launches `http://localhost:8000`).
2. **macOS & Linux (One-Command)**
   ```bash
   chmod +x baslat.sh
   ./baslat.sh
   ```
   *For scanned PDF OCR on macOS: `brew install tesseract tesseract-lang poppler`*
3. **Docker (Recommended for Servers)**
   ```bash
   cp .env.example .env
   # Set a strong ACCESS_PASSWORD in .env for non-localhost deployments
   docker compose up -d --build
   ```
4. **Desktop Shell (Optional)**
   ```bash
   pip install -e ".[desktop]"
   python desktop_shell.py
   ```

### Key Configuration (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | API key for Google Gemini cloud AI features | None |
| `ACCESS_PASSWORD` | Access password (**Required for Docker / remote access**) | Protected (`localhost` only if empty) |
| `ALLOW_UNPROTECTED_REMOTE_ACCESS` | Explicitly allow remote access without password (not recommended) | `False` |
| `ALLOWED_ORIGINS` | Allowed CORS and WebSocket origins | `http://127.0.0.1:8000,http://localhost:8000` |
| `MAX_UPLOAD_MB` | Maximum upload file size in MB | `250` |

---

## Belgeler ve Katkı / Documentation & Contributing

- [📖 Kapsamlı Kullanım ve Kurulum Kılavuzu (`KULLANIM_KILAVUZU.md`)](KULLANIM_KILAVUZU.md)
- [🎞️ Hareket Dili ve Frontend Notları (`docs/MOTION_NOTES.md`)](docs/MOTION_NOTES.md)
- [🤝 Katkı Rehberi (`docs/CONTRIBUTING.md`)](docs/CONTRIBUTING.md)
- [🛡️ Güvenlik Politikası (`docs/SECURITY.md`)](docs/SECURITY.md)
- [📜 Değişiklik Günlüğü (`docs/CHANGELOG.md`)](docs/CHANGELOG.md)
- [⚖️ Davranış Kuralları (`docs/CODE_OF_CONDUCT.md`)](docs/CODE_OF_CONDUCT.md)

## Lisans / License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
