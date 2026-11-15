# Changelog

All notable changes to Dijital Kütüphane will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Editoryal "Kâğıt ve Mürekkep" Hareket Sistemi**: Harici animasyon kütüphanesi olmadan `static/css/motion.css` (`@layer motion`) ve `static/js/motion.js` (`window.Motion`: `enter`, `exit`, `stagger`, `flip`, `glidePill`, `transition`) altyapısı ile `--ease-*` / `--t-*` token birleştirme.
- **Hareket & Etkileşim Dokümantasyonu**: Token referansı, `Motion` API sözleşmesi, İşlem Merkezi uzlaştırma akışı ve erişilebilirlik kararlarını belgeleyen `docs/MOTION_NOTES.md`.

### Changed
- **Canlı Etkinlik Merkezi (`#ops-toggle` / `#ops-center`)**: Tek satır kapsül tasarımı, gerçek AI motor adı ve WebSocket bağlantı durumu senkronizasyonu, `data-task-id` anahtarlı DOM uzlaştırması (`<details.ops-log-details>` açık durumu ve kaydırma korunumu), kapalı çekmecede `requestAnimationFrame` toplulaştırma, `scaleX` mürekkep ilerleme çubuğu ve `.book-card.uploading` → gerçek kitap kartı morfu.
- **Mekânsal Süreklilik & İkincil Yüzeyler**: Kitap kartı ↔ detay modalı ↔ `#workspace-reader` arasında `view-transition-name: book-cover` morfları; tema geçişinde (`toggleTheme`) View Transitions çapraz geçişi; karanlık mod yüzey/kenarlık ve terminal log kontrast iyileştirmeleri; tüm ilerleme/grafik çubuklarının `scaleX`/`scaleY` kompozit animasyonuna taşınması; sürekli nabız/dönüş (`opsPulse`/`opsSpin`) ve kart 3B eğimlerinin kaldırılması; `static/sw.js` önbellek sürümü güncellemesi (`v2026111504`).
- **Tasarım Kimliği Güncellemesi**: `README.md` ve `docs/CHANGELOG.md` içindeki hatalı `"Glassmorphic"` ifadeleri uygulamanın gerçek `"Kâğıt ve Mürekkep" (Paper & Ink)` editoryal tasarım kimliğiyle güncellendi.

### Fixed
- **Okuyucu ve Mobil Yerleşim İzolasyonu**: Kapalı `.workspace-reader:not(.open)` yüzeyinin sayfa altında görünmesi ve odak alması engellendi; `390px` mobil görünümde `#ops-toggle` ile `#ops-center` çakışması giderildi.
- **Okuyucu Sohbet Çekmecesi & PDF Arama Odakları**: `toggleWorkspaceChatPane` sonrası fit modunu koruyan `_refitReaderAfterChatToggle` yeniden sığdırma eklendi; `#pdf-search-bar` `Escape` ile odağı `#pdf-search-btn`'e döndürecek şekilde düzenlendi.
- **Modal Odak Tuzağı & `Escape` Hiyerarşisi**: `_getModalFocusables` ile gizli/file input'ların otomatik odaklanması önlendi ve açık modal/çekmece içindeki bir input odaklıyken `Escape` ile üst modalın kapanması sağlandı.

## [1.0.0] - 2026-11-08

### Added
- **ChromaGuard™ Akıllı Okuma Yüzeyi**: Göz yorgunluğunu önleyen Gündüz, Sepya, E-Ink ve Gece renk modları; ortam ışığına duyarlı dinamik kontrast, parlaklık optimizasyonu ve özelleştirilebilir tipografi.
- **OPDS 1.2 Kataloğu**: KOReader, Moon+ Reader, Apple Books ve uyumlu e-okuyucu cihazlar için standart kablosuz katalog beslemesi (`/opds`).
- **Gemini Cascade Mimarisi**: Google Gemini modelleri (`gemini-3.8-flash` → `gemini-3.5-flash-lite`) arasında akıllı yedekleme zinciri (fallback chain) ve HTTP 429 kota aşımlarına karşı üstel geri çekilmeli otomatik yeniden deneme toleransı.
- **Mobil Handoff**: Masaüstünde okunan kitabın sayfasını QR kod ile anında mobil cihaza aktarma ve okumaya mobilde kalınan yerden kesintisiz devam edebilme.
- **Çift Kitap / Mükerrer Eser Avcısı**: SHA-256 dosya hash kontrolü ve akıllı başlık/yazar benzerlik analizi ile kütüphanedeki mükerrer kitapları tespit edip raporlama ve temizleme.
- **Taşınabilir Tam Yedekleme & PKM Dışa Aktarma**: Tüm veritabanı (`SQLite`), kitaplar ve yapılandırmayı tek tıkla taşınabilir ZIP arşivi olarak dışa aktarma; kitap notlarını Obsidian (`.md`), Anki (`.tsv`) ve BibTeX (`.bib`) formatlarında alma.
- **Hibrit Zeka Mimarisi**: Doküman analizi, özetleme ve metaveri çıkarmada Google Gemini (Bulut) veya Ollama / LM Studio (Yerel LLM) modelleriyle tam entegrasyon.
- **Derin Kitap Sohbeti, FTS5 Arama & Çalışma Alanı (RAG)**: Gemini File API entegrasyonu, FTS5 sayfa içi tam metin arama, otomatik PDF içindekiler (TOC) çıkarma ve sayfa sapması çözümü.
- **Otomatik PDF, EPUB, TXT & OCR İşleme**: `pypdfium2`, `pdfplumber` ve Poppler ile kapak görseli/metin çıkarma, yerel PDF boyut sıkıştırma, EPUB/TXT desteği ve Tesseract OCR ile taranmış belgeleri metne dönüştürme.
- **Gölge Kütüphaneci (Watchfolder) & Masaüstü Kabuğu**: Seçili klasörü otomatik izleyip yeni kitapları kuyruğa alma ve isteğe bağlı PyWebView sistem tepsisi masaüstü deneyimi.
- **Koleksiyon ve Raf Yönetimi**: Özelleştirilebilir kitap koleksiyonları, JSON dışa aktarım ve Markdown formatında paylaşılabilir okuma listeleri.
- **Editoryal Kâğıt ve Mürekkep Tasarım & PWA**: Ultra duyarlı mobil uyumlu arayüz, dinamik `theme-color` meta senkronizasyonu, ARIA rolleri ve klavye erişilebilirliği.

### Security & Architecture
- **SQLite WAL Modu**: Eşzamanlı okuma ve yazma işlemlerinde yüksek veri bütünlüğü ve hız sağlayan Write-Ahead Logging yapılandırması.
- **Erişim Güvenliği & Rate Limiting**: Brute-force saldırılarına karşı IP ve oturum bazlı hız sınırlama, parola kapısı (`ACCESS_PASSWORD`) ve token tabanlı doğrulama.
- **Güvenli Oturum Yönetimi**: Kriptografik session yönetimi, SameSite ve Secure çerez bayrakları desteği.
- **Giriş Doğrulama & İzolasyon**: Path traversal koruması, güvenli dosya yükleme kontrolleri ve Jinja2 otomatik XSS kaçışı.

### Deployment & Tooling
- **Docker Ready**: `Dockerfile` ve `docker-compose.yml` ile tek komutla üretime hazır konteyner dağıtımı.
- **Windows Tek Tıkla Başlatıcı**: Sanal ortamı otomatik oluşturan ve bağımlılıkları yükleyen `BASLAT.bat`.
- **Linux / macOS Kurulum Desteği**: Otomatik ortam hazırlama ve başlatma betikleri (`docs/alternatif_kurulum/install.sh`).
