# Changelog

All notable changes to Dijital Kütüphane will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- **Modern Glassmorphic Tasarım & PWA**: Ultra duyarlı mobil uyumlu arayüz, dinamik `theme-color` meta senkronizasyonu, ARIA rolleri ve klavye erişilebilirliği.

### Security & Architecture
- **SQLite WAL Modu**: Eşzamanlı okuma ve yazma işlemlerinde yüksek veri bütünlüğü ve hız sağlayan Write-Ahead Logging yapılandırması.
- **Erişim Güvenliği & Rate Limiting**: Brute-force saldırılarına karşı IP ve oturum bazlı hız sınırlama, parola kapısı (`ACCESS_PASSWORD`) ve token tabanlı doğrulama.
- **Güvenli Oturum Yönetimi**: Kriptografik session yönetimi, SameSite ve Secure çerez bayrakları desteği.
- **Giriş Doğrulama & İzolasyon**: Path traversal koruması, güvenli dosya yükleme kontrolleri ve Jinja2 otomatik XSS kaçışı.

### Deployment & Tooling
- **Docker Ready**: `Dockerfile` ve `docker-compose.yml` ile tek komutla üretime hazır konteyner dağıtımı.
- **Windows Tek Tıkla Başlatıcı**: Sanal ortamı otomatik oluşturan ve bağımlılıkları yükleyen `BASLAT.bat`.
- **Linux / macOS Kurulum Desteği**: Otomatik ortam hazırlama ve başlatma betikleri (`docs/alternatif_kurulum/install.sh`).
