# 📚 Dijital Kütüphane — Kapsamlı Kullanım ve Kurulum Kılavuzu

Bu kılavuz; **Dijital Kütüphane & Araştırma Çalışma Alanı** uygulamasının sıfırdan kurulumundan, **Google Gemini API** anahtarı teminine, **Telegram kitap aktarım entegrasyonundan**, yapay zeka destekli okuma ve araştırma modüllerinin detaylı kullanımına kadar tüm aşamaları adım adım açıklamaktadır.

---

## 📑 İçindekiler
1. [Genel Bakış ve Temel Felsefe](#1-genel-bakış-ve-temel-felsefe)
2. [Sıfır Bir Bilgisayara Kurulum (Gereksinimler & Başlatma)](#2-sıfır-bir-bilgisayara-kurulum)
3. [Google Gemini API Anahtarı Alma ve Yapılandırma](#3-google-gemini-api-anahtarı-alma)
4. [Telegram Entegrasyonu (API Alma & Kitap Aktarımı)](#4-telegram-entegrasyonu-ve-kitap-aktarımı)
5. [Kütüphane Yönetimi ve Temel Özellikler](#5-kütüphane-yönetimi-ve-temel-özellikler)
6. [Okuma ve Araştırma Çalışma Alanı (Workspace)](#6-okuma-ve-araştırma-çalışma-alanı-workspace)
7. [Görünüm Modları: Kart, Liste ve İstatistik](#7-görünüm-modları)
8. [Ayarlar, Güvenlik ve Şifre Koruması](#8-ayarlar-güvenlik-ve-şifre-koruması)
9. [Sıkça Sorulan Sorular ve Sorun Giderme](#9-sıkça-sorulan-sorular-ve-sorun-giderme)

---

<a name="1-genel-bakış-ve-temel-felsefe"></a>
## 1. Genel Bakış ve Temel Felsefe

Dijital Kütüphane; dijital kitap (PDF/EPUB/TXT) arşivinizi yöneten, yapay zeka aracılığıyla kitapların meta verilerini (yazar, kategori, detaylı özet, anahtar kavramlar) otomatik çıkaran ve kitaplarınızla derinlemesine etkileşime girmenizi sağlayan **tamamen yerel ve bağımsız** bir kütüphane sistemidir.

* **Tam Veri Gizliliği:** Tüm kitaplarınız, notlarınız, veri tabanınız ve ayarlarınız yalnızca kendi bilgisayarınızda (`veriler/` klasöründe) saklanır. Üçüncü parti sunuculara veri aktarılmaz.
* **Hibrit Yapay Zeka:** Bulutta **Google Gemini** (ücretsiz API kotasıyla son derece hızlı ve akıllı) veya yerel bilgisayarınızda **Ollama / LM Studio** ile çevrimdışı çalışabilme esnekliği sunar.
* **Akıllı Okuma Ortamı:** Kitap okurken metin seçerek not alma, renkli vurgular ekleme ve kitap içeriği hakkında yapay zekaya sorular sorma imkanı verir.

---

<a name="2-sıfır-bir-bilgisayara-kurulum"></a>
## 2. Sıfır Bir Bilgisayara Kurulum

Uygulama, sıfır bir bilgisayarda (daha önce hiç çalıştırılmamış sistemlerde) tek bir tıklamayla kurulup çalışabilecek şekilde tasarlanmıştır.

### Sistem Gereksinimleri
* **İşletim Sistemi:** Windows 10/11, macOS veya Linux.
* **Python Sürümü:** Python 3.10 veya üzeri (Python 3.11, 3.12, 3.13 tam desteklenir).
  > **⚠️ ÖNEMLİ (Python Kurulumu):** Python'ı [python.org/downloads](https://www.python.org/downloads/) adresinden kurarken kurulum penceresinin en altında yer alan **`[X] Add python.exe to PATH`** kutucuğunu **mutlaka işaretleyin**.

---

### Windows'ta Tek Tıkla Kurulum ve Başlatma (Önerilen)
1. İndirdiğiniz zip arşivini bilgisayarınızda istediğiniz bir klasöre çıkartın (örn: Masaüstü).
2. Klasör içindeki **`BASLAT.bat`** dosyasına çift tıklayın.
3. Betik otomatik olarak:
   - Python'ın sistemde varlığını denetler.
   - İzole bir sanal ortam (`.venv`) oluşturur.
   - Gerekli tüm kütüphaneleri (`requirements.txt`) otomatik olarak indirip kurar.
   - Varsayılan yapılandırma dosyalarını (`.env` ve veri tabanı şemasını) hazırlar.
   - Kütüphane sunucusunu başlatır ve varsayılan web tarayıcınızda `http://localhost:8000` adresini otomatik açar.

---

### Linux veya macOS'ta Kurulum
Terminali açarak proje dizinine gidin ve şu komutları sırasıyla çalıştırın:
```bash
# 1. Sanal ortam oluşturun ve aktif edin
python3 -m venv .venv
source .venv/bin/activate

# 2. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 3. Kütüphaneyi başlatın
python main.py
```
Sunucu başladığında tarayıcınızdan **`http://localhost:8000`** adresine gidin.

---

### İsteğe Bağlı Ek Bileşenler
* **Tesseract OCR (Taranmış / Resim Halindeki PDF'ler İçin):** Metin tabakası olmayan, sadece taranmış fotoğraf sayfalarından oluşan eski kitapları yapay zekanın okuyabilmesi için sisteminizde Tesseract OCR yüklü olması önerilir.
  - Windows için: [Tesseract-OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki) indirip kurun. Kurulum yolunu kütüphanenin **Ayarlar** menüsündeki "Tesseract Yolu" alanına yazabilirsiniz (örn: `C:\Program Files\Tesseract-OCR\tesseract.exe`).

---

<a name="3-google-gemini-api-anahtarı-alma"></a>
## 3. Google Gemini API Anahtarı Alma ve Yapılandırma

Google Gemini; kitap kapaklarını görsel olarak tanıma, kitap başlığını, yazarını, kategorisini çıkarma ve kapsamlı özetler üretme işlemlerini saniyeler içinde tamamlar. Google, bireysel kullanıcılar için **ücretsiz tier (Free Tier)** sunmaktadır ve kişisel kütüphane için fazlasıyla yeterlidir.

### Adım Adım API Anahtarı Alma:
1. Web tarayıcınızdan **[Google AI Studio (aistudio.google.com)](https://aistudio.google.com/)** adresine gidin.
2. Google (Gmail) hesabınızla oturum açın.
3. Sol taraftaki menüden veya sağ üst köşeden **"Get API key"** (API Anahtarı Al) seçeneğine tıklayın.
4. Açılan pencerede **"Create API key in new project"** (Yeni projede anahtar oluştur) butonuna basın.
5. Birkaç saniye içinde `AIzaSy...` ile başlayan benzersiz API anahtarınız ekranda belirecektir.
6. Yanındaki **Kopyala (Copy)** simgesine tıklayarak anahtarı panonuza alın.

### API Anahtarını Kütüphaneye Tanımlama:
İki kolay yoldan birini seçebilirsiniz:

* **Yol A — Arayüz Üzerinden (En Kolayı):**
  1. Kütüphaneyi açın (`http://localhost:8000`).
  2. Sağ üst köşedeki **⚙️ Ayarlar** çarkına tıklayın.
  3. **Yapay Zeka Servis Sağlayıcısı:** `Google Gemini` seçin.
  4. **Yapay Zeka API Anahtarı:** Kopyaladığınız `AIzaSy...` anahtarını yapıştırın.
* **Gemini Modeli:** `gemini-3.5-flash-lite` (varsayılan) veya kademeli zincir üzerinden `gemini-3.8-flash` / `gemini-3.7-flash` / `gemini-3.6-flash` / `gemini-3.5-flash`.
  6. Alttaki **"Ayarları Kaydet"** butonuna tıklayın.

* **Yol B — `.env` Dosyası Üzerinden:**
  Klasördeki `.env` dosyasını Not Defteri ile açın ve şu satırı düzenleyin:
  ```env
  GEMINI_API_KEY=AIzaSy...kopyaladiginiz_anahtar...
  ```
  Dosyayı kaydedip kütüphaneyi yeniden başlatın.

---

<a name="4-telegram-entegrasyonu-ve-kitap-aktarımı"></a>
## 4. Telegram Entegrasyonu (API Alma & Kitap Aktarımı)

Telegram entegrasyonu sayesinde telefonunuzdan veya bilgisayarınızdan Telegram'daki **Kaydedilen Mesajlar (Saved Messages)** bölümüne veya belirlediğiniz bir kanala/gruba attığınız PDF kitapları, tek tıkla kütüphanenize otomatik aktarabilirsiniz.

### 1. Adım: Telegram API Bilgilerini (API ID & API Hash) Alma
Telegram güvenlik politikası gereği harici istemciler için resmi bir `api_id` ve `api_hash` talep eder. Bu işlem **yalnızca 1 kez** yapılır ve 1 dakika sürer:

1. Tarayıcınızdan **[my.telegram.org](https://my.telegram.org)** adresine gidin.
2. Telegram'a kayıtlı telefon numaranızı uluslararası formatta yazın (Örnek: `+905xxxxxxxxx`) ve **Next**'e tıklayın.
3. Telegram mobil veya masaüstü uygulamanıza Telegram resmi servisinden bir **onay kodu (login code)** gelecektir. Bu kodu tarayıcıya girip oturum açın.
4. Açılan menüden **"API development tools"** bağlantısına tıklayın.
5. Yeni bir uygulama kayıt formu çıkar:
   - **App title:** `Dijital Kutuphanem` yazabilirsiniz.
   - **Short name:** `kutuphane` yazabilirsiniz.
   - Platform ve URL kısımlarını varsayılan bırakabilirsiniz.
6. **"Create application"** butonuna tıklayın.
7. Sayfanın en üstünde iki kritik bilgi görüntülenecektir:
   - **`App api_id`:** (örn: `28471928` gibi rakamlardan oluşur)
   - **`App api_hash`:** (örn: `b4f8a3c9e1...` gibi 32 karakterlik metindir)
8. Bu iki değeri kopyalayın.

---

### 2. Adım: Kütüphanede Telegram Bağlantısını Kurma
1. Kütüphane arayüzünde üst menüdeki mavi **Telegram simgesine** (veya ana sayfadaki *"Telegram'dan Aktar"* butonuna) tıklayın.
2. Açılan pencerede:
   - **Telegram API ID:** my.telegram.org'dan aldığınız rakamları girin.
   - **Telegram API Hash:** my.telegram.org'dan aldığınız hash kodunu yapıştırın.
   - **Hedef Sohbet / Kanal ID:**
     - Kendi kişisel notlarınıza/kaydedilen mesajlarınıza attığınız kitaplar için varsayılan olarak **`me`** bırakın.
     - Özel bir kanal veya gruptan çekecekseniz kanalın kullanıcı adını (örn: `@kitapkanalim`) veya chat ID'sini yazabilirsiniz.
   - **Bağlantı Türü:** `Kullanıcı Hesabı (Önerilen)` seçili olsun.
3. **"Hesaba Bağlan"** butonuna basın.
4. Sistem telefon numaranızı soracaktır; numaranızı girin (`+905xxxxxxxxx`).
5. Telegram uygulamanıza gelen 5 haneli doğrulama kodunu açılan kutuya yazın. *(Hesabınızda İki Adımlı Doğrulama/2FA parolası varsa şifrenizi de girin).*
6. Ekranda **"✅ Telegram Bağlantısı Aktif"** onayını göreceksiniz.

---

### 3. Adım: Kitapları Senkronize Etme ve Akıllı Filtre
* Bağlantı sağlandıktan sonra **"Kitapları Şimdi Senkronize Et"** butonuna basmanız yeterlidir.
* Sistem hedef sohbetteki tüm PDF ve EPUB dosyalarını tarar, bilgisayarınıza indirir (`veriler/Dijital_Kutuphane/`).
* **Akıllı Değişim Takibi (Incremental Sync):** Sistem en son indirilen mesajın kimliğini (`telegram_last_msg_id`) ve tarihini hatırlar. Bir sonraki senkronizasyon butonuna bastığınızda eski dosyalar tekrar indirilmez; yalnızca sohbete **yeni eklenen** kitaplar tespit edilir ve kuyruğa alınır.

---

<a name="5-kütüphane-yönetimi-ve-temel-özellikler"></a>
## 5. Kütüphane Yönetimi ve Temel Özellikler

### Kitap Ekleme Yolları
1. **Sürükle & Bırak:** İstediğiniz PDF veya EPUB dosyasını tarayıcı penceresine sürükleyip bırakın.
2. **"Dosya Seç" Butonu:** Karşılama alanındaki butonla dosya gezgininden kitap seçin.
3. **Fiziksel Klasörden Eşitleme:** Bilgisayarınızdaki `veriler/Dijital_Kutuphane/` klasörüne dilediğiniz zaman haricen klasörler ve PDF'ler kopyalayabilirsiniz. Ardından arayüzdeki **"Kütüphaneyi Eşitle (Tara)"** butonuna bastığınızda klasör taranır, yeni dosyalar anında kütüphaneye dahil edilir.

### Arka Planda Otomatik Yapay Zeka Analizi
Bir kitap yüklendiğinde arka planda asenkron işçi devreye girer:
1. Kitabın ilk sayfalarından yüksek kaliteli kapak görseli (`thumbnails/`) üretilir.
2. Kitabın ilk 10-20 sayfası taranarak metin analizi hazırlanır.
3. Gemini / Yerel AI modeli metni inceleyerek:
   - Kitabın gerçek adını ve alt başlığını,
   - Yazarını,
   - 16 standart kategoriden en uygununu ve alt kategorisini,
   - Akademik nitelikte kapsamlı bir özetini,
   - 5-7 adet anahtar kavramını (Keywords) otomatik olarak çıkarıp kaydeder.

### Canlı İşlem Merkezi ve Terminal Logları (`>_`)
Ekranın sağ üst köşesindeki **`>_` terminal butonuna** tıklayarak arka planda gerçekleşen işlemleri canlı olarak izleyebilirsiniz:
- Hangi kitabın indirildiği,
- OCR durumları,
- Yapay zeka istek ve yanıt süreleri,
- Olası hatalar veya uyarılar anlık olarak terminal ekranına akar.

### Koleksiyonlar ve Favoriler
* Kitap kartlarındaki veya detay penceresindeki **❤️ Favori** butonu ile favorilerinize ekleyebilirsiniz.
* Araç çubuğundaki **"Favoriler"** filtresine basarak yalnızca favorilerinizi listeleyebilirsiniz.
* Kitapları tematik koleksiyonlara (örn: *"2026 Okuma Listem"*, *"Felsefe Araştırmaları"*) ekleyebilir, koleksiyon bazlı filtreleme yapabilirsiniz.

### Toplu Yönetim
Araç çubuğundaki **"Yönet"** butonuna basarak seçim modunu açabilirsiniz. Birden fazla kitabı seçerek tek seferde silebilir veya koleksiyonlara atayabilirsiniz.

---

<a name="6-okuma-ve-araştırma-çalışma-alanı-workspace"></a>
## 6. Okuma ve Araştırma Çalışma Alanı (Workspace)

Bir kitabın altındaki **"Kitabı Oku"** butonuna bastığınızda, tarayıcınız gelişmiş bir dijital okuma ve araştırma laboratuvarına dönüşür:

### Okuma Düzenleri
* **Tek Sayfa:** Sayfaları tek tek incelemek ve odaklanmak için idealdir.
* **Çift Sayfa (Kitap Modu):** Gerçek bir basılı kitap gibi yan yana iki sayfa görüntüler.
* **Dikey Akış:** Web sayfası gibi aşağıya doğru kesintisiz kaydırarak okuma sağlar.

### Metin Vurgulama ve Not Alma
* Okuma sırasında farenizle herhangi bir cümleyi seçtiğinizde üzerinde pratik bir menü belirir:
  - **Sarı, Yeşil, Mavi, Pembe** renklerden biriyle metni vurgulayabilirsiniz.
  - Vurguladığınız yere özel not ekleyebilirsiniz.
* Sol paneldeki **"Notlar"** sekmesinde aldığınız tüm notlar sayfa numaralarıyla listelenir; tıkladığınızda doğrudan ilgili sayfaya ve cümleye gidersiniz.

### PDF İçi Canlı Kelime Arama
* Sol taraftaki arama simgesine tıklayıp bir kelime yazdığınızda, kitabın tamamı taranır ve kelimenin geçtiği sayfalar sonuç listesinde özet parçacıklarıyla gösterilir.
* Tıkladığınızda o sayfaya gidilir ve aranan kelimeler sayfa üzerinde sarı ışıkla vurgulanır.

### Kitap İçi Yapay Zeka Asistanı
* Çalışma alanının sağındaki **"Kütüphane Asistanı"** paneli, o an okuduğunuz kitabın bağlamına tam olarak hakimdir.
* Asistana:
  - *"Bu sayfadaki ana fikri 3 maddede açıkla."*
  - *"Yazarın 4. bölümdeki tezini özetle."*
  - *"Bu kitapta geçen kavramları karşılaştır."*
  gibi komutlar vererek araştırmalarınızı derinleştirebilirsiniz.

### Otomatik Kaldığın Yeri Hatırlama
Kitaptan çıktığınızda veya tarayıcıyı kapattığınızda son okuduğunuz sayfa veri tabanına kaydedilir. Kitabı tekrar açtığınızda otomatik olarak kaldığınız sayfadan başlar.

---

<a name="7-görünüm-modları"></a>
## 7. Görünüm Modları

Araç çubuğundaki düğmelerle kütüphanenizi farklı perspektiflerden görüntüleyebilirsiniz:

1. **🗂️ Kart Görünümü:** Kapak görselleri, yazar, kategori etiketleri ve okuma ilerleme çubuğuyla modern vitrin görünümü.
2. **📋 Liste Görünümü:** Kitap adı, yazar, kategori, ekleme tarihi ve okunan sayfa bilgisini içeren tablo düzeni.
3. **📊 İstatistik Görünümü:**
   - Kütüphanenizdeki toplam kitap, favori, yazar ve kategori sayıları.
   - Kategori dağılım grafikleri ve aylık ekleme trendi.

### Verimlilik & Dışa Aktarım Araçları
* **Derin Metin Arama (FTS5):** Tüm kitapların sayfa içeriklerinde kelime araması yapıp doğrudan eşleşen sayfaya atlayabilirsiniz.
* **PDF Boyut Optimizasyonu & Mükerrer Tarama:** Büyük PDF'leri yerel olarak sıkıştırabilir ve yinelenen kitapları tek pencereden temizleyebilirsiniz.
* **QR Kod ile Telefona Aktarım & OPDS:** Okuduğunuz kitabı ve sayfayı yerel ağdaki (Wi-Fi) telefonunuza QR kod ile aktarabilir veya OPDS e-kitap okuyucularla bağlanabilirsiniz.
* **PKM & Tam Yedek Dışa Aktarma:** Kitap notlarınızı **Obsidian (.md)**, **Anki (.tsv)** veya **BibTeX (.bib)** formatında; tüm kütüphanenizi ise tek tıkla taşınabilir ZIP yedeği olarak dışa aktarabilirsiniz.

---

<a name="8-ayarlar-güvenlik-ve-şifre-koruması"></a>
## 8. Ayarlar, Güvenlik ve Şifre Koruması

### Şifre Koruması (Uzak Erişim & Ağ Güvenliği)
Kütüphanenizi evinizdeki yerel ağa (Wi-Fi), bir sunucuya veya Docker ortamına kurduğunuzda yabancıların kütüphanenize erişmesini engellemek için şifre koruması mevcuttur:

`.env` dosyasını açın:
```env
ACCESS_PASSWORD=belirleyeceginiz_guclu_bir_sifre
```
* Şifre belirlendiğinde kütüphaneye ilk girişte şık bir kilit ekranı açılır.
* Hatalı şifre denemelerine karşı yerleşik **Brute-Force (Kaba Kuvvet) koruması** bulunur (5 hatalı denemede IP adresi 10 dakika kilitlenir).

### Ayarlar Menüsü Parametreleri
Arayüzdeki ⚙️ **Ayarlar** panelinden şunları özelleştirebilirsiniz:
* **Maksimum Analiz Sayfası:** Kitap eklenirken taranacak sayfa adedi (varsayılan: 10 sayfa).
* **OCR Tarama Sayfası:** Resim PDF'lerinde OCR yapılacak sayfa sayısı (varsayılan: 20 sayfa).
* **Görsel Kalitesi & Boyutu:** Kapak çıkarma işlemlerindeki çözünürlük parametreleri.

---

<a name="9-sıkça-sorulan-sorular-ve-sorun-giderme"></a>
## 9. Sıkça Sorulan Sorular ve Sorun Giderme

#### S: `BASLAT.bat` çalıştırdığımda "Python sisteminizde bulunamadı" diyor.
**C:** Bilgisayarınızda Python yüklü değildir veya PATH ortam değişkenine eklenmemiştir. [python.org/downloads](https://www.python.org/downloads/) adresinden Python'ı indirin, kurulum ekranının altındaki **"Add python.exe to PATH"** kutucuğunu işaretleyerek kurun ve `BASLAT.bat` dosyasını yeniden çalıştırın.

#### S: Gemini API ile analiz yaparken hata alıyorum.
**C:** 
1. `config.json` veya Ayarlar menüsünden API anahtarınızın başında/sonunda boşluk olmadan doğru girildiğinden emin olun.
2. Google AI Studio hesabınızda API anahtarınızın aktif olduğunu teyit edin.
3. Model adı olarak varsayılan olan `gemini-3.5-flash-lite` (veya kademeli zincirdeki güncel Gemini modellerinden biri) seçili olduğundan emin olun.

#### S: Telegram doğrulama kodu SMS ile gelmiyor.
**C:** Telegram güvenlik gereği oturum açma kodlarını normal SMS yerine doğrudan telefonunuzda veya bilgisayarınızda açık olan **Telegram uygulaması içindeki resmi Telegram bildirim sohbetine** gönderir. Telegram uygulamanızı kontrol edin.

#### S: Kütüphaneyi başka bir bilgisayara nasıl taşırım?
**C:** Dijital Kütüphane taşınabilir (portable) mimaridedir. Proje klasörünü olduğu gibi yeni bilgisayara kopyalayıp `BASLAT.bat` çalıştırmanız yeterlidir. Tüm veri tabanınız ve kitaplarınız `veriler/` klasöründe eksiksiz korunur.

#### S: Sayfa kaydırınca araç çubuğu veya menü bozulur mu?
**C:** Hayır; kütüphane tüm ekran boyutlarına (4K monitörlerden dizüstü bilgisayarlara ve tabletlere kadar) tam duyarlı (responsive) olarak optimize edilmiştir.
