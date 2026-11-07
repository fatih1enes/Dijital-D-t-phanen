import os

output_path = 'TASARIM_KODLARI_VE_SISTEMI.md'

header_text = """# 🏛️ DİJİTAL KÜTÜPHANE — BÜTÜN TASARIM, ARAYÜZ, HAREKET VE İMZA ETKİLEŞİM SİSTEMİ KODLARI (FAZ A + B + C + D GÜNCEL SÜRÜM)

Bu dosya, Dijital Kütüphane projesinin **tüm görsel tasarım sistemi, CSS katman mimarisi, tasarım token'ları, hareket fizikleri (60 FPS motion), paylaşılan eleman geçişleri (View Transitions morph), çift tamponlama ve imza UI/UX etkileşim kodlarını** yapay zekâ modellerine (Claude, GPT-4, Gemini vb.) tek parça halinde aktarmak amacıyla eksiksiz olarak bir araya getirilmiştir.

---

## 📋 İÇİNDEKİLER

1. **TASARIM VE HAREKET FELSEFESİ (Apple Books / Linear / Tesla Sakinliği)**
2. **FAZ A: TEMEL VE KARARLILIK İYİLEŞTİRMELERİ (A1 - A12)**
3. **FAZ B: HAREKET SİSTEMİ STANDARDI (B1 - B5)**
4. **FAZ C: PERFORMANS VE ÇİFT TAMPONLAMA (C1 - C7)**
5. **FAZ D: İMZA ETKİLEŞİMLER (D1 - D6)**
6. **KOD DOSYALARI:**
   - **DOSYA 0:** `static/css/app.css` (CSS Cascade Layers: `@layer legacy, tokens, design;`)
   - **DOSYA 1:** `static/css/tokens.css` (Tek Doğru Kaynak: Renk, Tipografi, Boşluk, Radius, Hareket Token'ları)
   - **DOSYA 2:** `static/css/design.css` (Rafine Tasarım Katmanı, View Transitions & İmza Etkileşimler)
   - **DOSYA 3:** `templates/kutuphane.html` (Ana Kütüphane Arayüzü, Hero, Raf & Çalışma Alanı Şablonu)
   - **DOSYA 4:** `templates/login.html` (Giriş Ekranı, Sıcak Kâğıt/Mürekkep Paleti & View Transitions)
   - **DOSYA 5:** `static/css/style.css` (Temel Bileşenler, Modallar, Panel Yapıları & Temizlikleri)
   - **DOSYA 6.1:** `static/js/app.js` (Uygulama Yaşam Döngüsü, View Transitions Tema Geçişi)
   - **DOSYA 6.2:** `static/js/ui_core.js` (UI Çekirdeği, cardElementsMap, Klavye Erişilebilirliği & showAppConfirm)
   - **DOSYA 6.3:** `static/js/ui_workspace.js` (Retina 2.5 DPR, openBookWithMorph, Prefetch & Çift Tamponlama Zoom)
   - **DOSYA 6.4:** `static/js/ui_chat_settings.js` (Daktilo Efekti 2.5s Sınırlaması, Akıllı Scroll)
   - **DOSYA 6.5:** `static/js/ui_logs.js` (İşlem Merkezi & Canlı Log Akışı)

---

## 1. TASARIM, HAREKET VE PERFORMANS FELSEFESİ

- **Sessiz ve Rafine Estetik:** Yapay zekâ SaaS şablonu klişelerinden (mor/mavi degrade, gereksiz neon parlama, kontrolsüz 20px+ blur, zıplayan hover efektleri) tamamen arındırılmıştır.
- **Sıcak Kâğıt & Derin Mürekkep Paleti:** Açık temada sıcak kâğıt (`#f4f1eb`) ve derin antrasit mürekkep (`#1f1e1b`, kontrast 14:1); koyu temada obsidian kömür (`#161513`) ve temiz krem metin (`#f0ece3`).
- **Doğal Tipografi:** Başlıklarda Instrument Serif (yalnızca 400 normal/italik, sahte kalın yasak); editoryal metinlerde Newsreader; kullanıcı arayüzünde Geist; sayısal ve künye alanlarında Geist Mono.
- **Paylaşılan Eleman Geçişleri (D1):** Karttan okuyucuya geçerken kapak görseli View Transitions API ile kart konumundan okuyucu başlığına (`#workspace-cover-slot`) akıcı bir yaylanmayla (`--ease-spring`) büyür; okuyucu kapatıldığında karttaki yerine geri uçar.
- **Klavye Erişilebilirliği (D5):** Tüm açılır menüler ve araçlar klavye ok tuşları (↑/↓), Enter ve Escape ile yönetilebilir; kapandığında odak tetikleyici butona geri döner.
- **Uygulama İçi Şık Onay Pencereleri (D6):** Tarayıcının kaba yerel `confirm()` pencereleri tamamen kaldırıldı; sıcak kâğıt paletinde çalışan, animasyonlu `showAppConfirm` modalı devreye alındı.

---

## 2. FAZ A, B, C VE D MİMARİ DÖNÜŞÜMLERİ

1. **CSS Katman Mimarisi (`@layer`):** `style.css` (legacy), `tokens.css` (tokens) ve `design.css` (design) katmanlarına ayrıldı. `design.css` içindeki 920'den fazla zorlama `!important` temizlendi.
2. **Merkezi Token Sistemi:** `tokens.css` tek doğru kaynak haline getirildi; mükerrer `:root` blokları silindi.
3. **Modal Sayfa Kayması:** `html { scrollbar-gutter: stable; }` ve `body.modal-open` sınıf standardı ile Windows'ta 15px layout shift çözüldü.
4. **Stagger Kontrolü (B4):** Canlı arama ve filtrelemede `doStagger = false` ile sıfır gecikmeli gösterim sağlandı.
5. **Erişilebilirlik (B5):** `prefers-reduced-motion: reduce` altında 0.01ms hilesi kaldırıldı; sakin 100-150ms opaklık solması sağlandı.
6. **Bulanıklık Temizliği (C1):** Sabit navigasyon ve kontrollerdeki ağır blur'lar kaldırılarak saf yüzey rengine (`var(--surface)`) dönüldü.
7. **GPU Bellek Tasarrufu (C2):** `.book-card` üzerindeki kalıcı `will-change` kaldırıldı; geçici hover/stagger durumlarına bağlandı.
8. **DOM Eleman Ön Bellekleme (C3):** `cardElementsMap` ve `tableRowsMap` ile arama ve filtrelemede `innerHTML = ''` yerine `display: none` / `''` kullanıldı; sıfır DOM re-render!
9. **View Transitions API (C4):** `theme-transitioning` sınıfı silindi; `document.startViewTransition()` ile layout recalculation < 1ms sağlandı.
10. **GPU Yüzey Modları (C5):** Sepya ve E-Ink modları canvas piksel döngüsünden alınıp donanım hızlandırmalı CSS filtrelerine bağlandı (`0.29ms`).
11. **Çift Tamponlama Zoom (C6):** Zoom sırasında beyaz flaş engellendi, `is-zooming` ile `will-change` dinamik yönetildi.
12. **Daktilo Efekti Hızlandırması (C7):** 500 kelimelik yapay zekâ yanıtları 2.5s ile sınırlandı; ara reflow'lar durduruldu.
13. **Paylaşılan Eleman Geçişi (D1):** `openBookWithMorph` ve `#workspace-cover-slot` ile karttan okuyucuya kesintisiz kapak akışı sağlandı.
14. **PDF Pre-fetching & İskelet Yükleyici (D2):** Karta hover yapıldığında (150ms debounce) `pdfjsLib.getDocument` önceden başlatıldı; okuyucuda sakin kapaklı iskelet (skeleton) gösterildi.
15. **Yumuşak Kapak Yükleme (D3):** Kapaklara `loading="lazy"`, `decoding="async"` ve `onload="this.classList.add('loaded')"` ile `--t-ui` opaklık geçişi eklendi; sakin shimmer bağlandı.
16. **Kart Okuma İlerlemesi (D4):** Başlanmış kitapların altına 2px `--accent` okuma çizgisi ve `%xx` rozeti eklendi; okunmamış kitaplarda (%0) gizlendi.
17. **Klavye Erişilebilirliği (D5):** Açılır menülerde ↑/↓/Enter/Esc klavye navigasyonu ve tetikleyiciye odak dönüşü sağlandı.
18. **Uygulama İçi Onay Diyaloğu (D6):** Tüm yerel `confirm()` çağrıları kaldırıldı; `showAppConfirm` modalına geçirildi.

---
"""

file_sections = [
    ("DOSYA 0: static/css/app.css (CSS Cascade Layers: @layer legacy, tokens, design)", "static/css/app.css", "css"),
    ("DOSYA 1: static/css/tokens.css (Tasarım Tokenları & Tek Doğru Kaynak)", "static/css/tokens.css", "css"),
    ("DOSYA 2: static/css/design.css (Rafine Tasarım Sistemi, View Transitions & Mikro-Etkileşimler)", "static/css/design.css", "css"),
    ("DOSYA 3: templates/kutuphane.html (Ana Kütüphane, Hero & Okuyucu Şablonu)", "templates/kutuphane.html", "html"),
    ("DOSYA 4: templates/login.html (Giriş Ekranı Arayüzü & View Transitions)", "templates/login.html", "html"),
    ("DOSYA 5: static/css/style.css (Temel Stil Motoru, Modallar & Temizlikler)", "static/css/style.css", "css"),
    ("DOSYA 6.1: static/js/app.js (Uygulama Yaşam Döngüsü & View Transitions)", "static/js/app.js", "javascript"),
    ("DOSYA 6.2: static/js/ui_core.js (UI Çekirdeği, cardElementsMap ile Sıfır Re-render)", "static/js/ui_core.js", "javascript"),
    ("DOSYA 6.3: static/js/ui_workspace.js (Okuma Alanı, Çift Tamponlama Zoom & GPU Yüzeyler)", "static/js/ui_workspace.js", "javascript"),
    ("DOSYA 6.4: static/js/ui_chat_settings.js (Sohbet Daktilo Hızlandırması & Ayarlar)", "static/js/ui_chat_settings.js", "javascript"),
    ("DOSYA 6.5: static/js/ui_logs.js (İşlem Merkezi & Canlı Log Akışı)", "static/js/ui_logs.js", "javascript"),
]

with open(output_path, 'w', encoding='utf-8') as out:
    out.write(header_text)
    
    for title, filepath, lang in file_sections:
        print(f"Adding {filepath} to bundle...")
        out.write(f"\n\n## {title}\n\n")
        out.write(f"**Dosya Yolu:** `{filepath}`\n\n")
        out.write(f"```{lang}\n")
        with open(filepath, 'r', encoding='utf-8') as src:
            content = src.read()
            out.write(content)
            if not content.endswith('\n'):
                out.write('\n')
        out.write("```\n")

bundle_size = os.path.getsize(output_path)
print(f"Generated {output_path} successfully! Size: {bundle_size:,} bytes ({bundle_size/1024:.1f} KB)")

