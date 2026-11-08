import os

output_path = 'TASARIM_KODLARI_VE_SISTEMI.md'

header_text = """# 🏛️ DİJİTAL KÜTÜPHANE — BÜTÜN TASARIM, ARAYÜZ, HAREKET, ERİŞİLEBİLİRLİK VE İMZA ETKİLEŞİM SİSTEMİ KODLARI (FAZ A'DAN FAZ G'YE EKSİKSİZ MASTER SÜRÜM)

Bu dosya, Dijital Kütüphane projesinin **tüm görsel tasarım sistemi, CSS katman mimarisi (@layer), tasarım token'ları, hareket fizikleri (60 FPS motion), paylaşılan eleman geçişleri (View Transitions morph), çift tamponlama, mobil okuyucu alt çekmecesi (bottom sheet), evrensel odak tuzağı (focus trap), WCAG AA/AAA kontrast uyumu ve imza UI/UX etkileşim kodlarını** yapay zekâ modellerine (Claude, GPT-4, Gemini vb.) tek parça halinde aktarmak amacıyla eksiksiz olarak bir araya getirilmiştir.

---

## 📋 İÇİNDEKİLER

1. **TASARIM VE HAREKET FELSEFESİ (Apple Books / Linear / Tesla Sakinliği)**
2. **FAZ A: TEMEL VE KARARLILIK İYİLEŞTİRMELERİ (A1 - A12)**
3. **FAZ B: HAREKET SİSTEMİ STANDARDI (B1 - B5)**
4. **FAZ C: PERFORMANS VE ÇİFT TAMPONLAMA (C1 - C7)**
5. **FAZ D: İMZA ETKİLEŞİMLER (D1 - D6)**
6. **FAZ E: GÖRSEL DİL VE TUTARLILIK (E1 - E8)**
7. **FAZ F: DOKUNMATİK, MOBİL VE ERİŞİLEBİLİRLİK (F1 - F3)**
8. **FAZ G: SON CİLA VE DENETİM (G1 - G2)**
9. **KOD DOSYALARI:**
   - **DOSYA 0:** `static/css/app.css` (CSS Cascade Layers: `@layer legacy, tokens, design;`)
   - **DOSYA 1:** `static/css/tokens.css` (Tek Doğru Kaynak: Renk, Tipografi, Boşluk, Radius, Hareket Token'ları)
   - **DOSYA 2:** `static/css/design.css` (Rafine Tasarım Katmanı, View Transitions, Dokunmatik F1, Odak F2 & Cila G1)
   - **DOSYA 3:** `templates/kutuphane.html` (Ana Kütüphane, Editoryal Hero, Dialog Rolleri & Okuyucu Şablonu)
   - **DOSYA 4:** `templates/login.html` (Giriş Ekranı, Sıcak Kâğıt/Mürekkep, FOUC Önleme & View Transitions)
   - **DOSYA 5:** `static/css/style.css` (Temel Bileşenler, Mojibake Temizliği & Ölü Sınıf Tasfiyesi)
   - **DOSYA 6.1:** `static/js/app.js` (Uygulama Yaşam Döngüsü, Dinamik Theme-Color & Scroll-to-Top)
   - **DOSYA 6.2:** `static/js/state.js` (Toast Sistemi, role='status', aria-live & 4s Hover Pause)
   - **DOSYA 6.3:** `static/js/ui_core.js` (UI Çekirdeği, cardElementsMap, Evrensel Focus Trap & Semantik Butonlar)
   - **DOSYA 6.4:** `static/js/ui_workspace.js` (Retina 2.5 DPR, Mobil Bottom Sheet, Çift Tamponlama Zoom & Dinamik Başlık)
   - **DOSYA 6.5:** `static/js/ui_chat_settings.js` (Daktilo Efekti 2.5s Sınırlaması, Akıllı Scroll & Focus Entegrasyonu)
   - **DOSYA 6.6:** `static/js/ui_logs.js` (İşlem Merkezi, Canlı Log Akışı & Dialog Rolleri)
   - **DOSYA 7:** `static/manifest.json` (PWA Manifest, Sıcak Kâğıt & Kehribar Renk Uyumu)

---

## 1. TASARIM, HAREKET VE PERFORMANS FELSEFESİ

- **Sessiz ve Rafine Estetik:** Yapay zekâ SaaS şablonu klişelerinden (mor/mavi degrade, gereksiz neon parlama, kontrolsüz 20px+ blur, zıplayan butonlar) tamamen arındırılmıştır.
- **Sıcak Kâğıt & Derin Mürekkep Paleti:** Açık temada sıcak kâğıt (`#f4f1eb`) ve derin antrasit mürekkep (`#1f1e1b`, kontrast 14.8:1 AAA); koyu temada obsidian kömür (`#161513`) ve temiz krem metin (`#f0ece3`).
- **Doğal Tipografi:** Başlıklarda Instrument Serif (yalnızca 400 normal/italik, sahte kalın yasak); editoryal metinlerde Newsreader; kullanıcı arayüzünde Geist; sayısal ve künye alanlarında Geist Mono.
- **Paylaşılan Eleman Geçişleri (D1):** Karttan okuyucuya geçerken kapak görseli View Transitions API ile kart konumundan okuyucu başlığına (`#workspace-cover-slot`) akıcı bir yaylanmayla (`--ease-spring`) büyür; okuyucu kapatıldığında karttaki yerine geri uçar.
- **Evrensel Odak Tuzağı (F2):** Tüm modallarda `role="dialog"`, `aria-labelledby` ve tam döngüsel `Tab` / `Escape` odak yönetimi.
- **Mobil Okuyucu Alt Çekmecesi (F1):** Mobilde (375px) PDF'i küçültmeden tam ekran okuma deneyimi sunulur; AI asistanı dokunmatik hız bazlı çekmece (bottom sheet) olarak çalışır.
- **PWA & FOUC Önleme (F3):** Sayfa yüklenirken ilk piksel çizilmeden önce çalışan satır içi tema betiği ile gece modunda beyaz parlama sıfıra indirilmiştir.

---

## 2. FAZ BAZLI MİMARİ DÖNÜŞÜMLER ÖZETİ

- **FAZ A:** `@layer legacy, tokens, design;` mimarisiyle 920+ zorlama `!important` silindi, retina 2.5 DPR keskinliği sağlandı.
- **FAZ B:** Tek hareket sistemi tokenlaştırıldı (`--t-micro`, `--t-ui`, `--t-page`, `--ease-out`, `--ease-spring`).
- **FAZ C:** Kalıcı `will-change` temizlendi, `cardElementsMap` ile DOM sıfır re-render hızına kavuştu, daktilo 2.5s ile sınırlandı.
- **FAZ D:** `openBookWithMorph`, hover prefetch, lazy decoding kapaklar, 2px okuma çizgisi ve `showAppConfirm` eklendi.
- **FAZ E:** Editoryal tam genişlik hero, tek tip SVG ikon sistemi, 35 sabit inline renk temizliği, buton sınıfı konsolidasyonu ve WCAG AAA kontrast düzenlemesi yapıldı.
- **FAZ F:** 44×44px dokunma hedefleri (`::before`), safe-area insets, mobil bottom sheet çekmecesi, focus trap ve semantik `<button>` dönüşümleri tamamlandı.
- **FAZ G:** İnce tema uyumlu scrollbar, `::selection` ve `caret-color: var(--accent)`, sayısal `tabular-nums`, dinamik `document.title` güncellemesi, mojibake tasfiyesi ve 100/100 audit sağlandı.

---
"""

file_sections = [
    ("DOSYA 0: static/css/app.css (CSS Cascade Layers: @layer legacy, tokens, design)", "static/css/app.css", "css"),
    ("DOSYA 1: static/css/tokens.css (Tasarım Tokenları & Tek Doğru Kaynak)", "static/css/tokens.css", "css"),
    ("DOSYA 2: static/css/design.css (Rafine Tasarım Sistemi, View Transitions, Dokunmatik F1, Odak F2 & Cila G1)", "static/css/design.css", "css"),
    ("DOSYA 3: templates/kutuphane.html (Ana Kütüphane, Editoryal Hero, Dialog Rolleri & Okuyucu Şablonu)", "templates/kutuphane.html", "html"),
    ("DOSYA 4: templates/login.html (Giriş Ekranı Arayüzü, FOUC Önleme & View Transitions)", "templates/login.html", "html"),
    ("DOSYA 5: static/css/style.css (Temel Stil Motoru, Mojibake Temizliği & Ölü Sınıf Tasfiyesi)", "static/css/style.css", "css"),
    ("DOSYA 6.1: static/js/app.js (Uygulama Yaşam Döngüsü, Dinamik Theme-Color & Scroll-to-Top)", "static/js/app.js", "javascript"),
    ("DOSYA 6.2: static/js/state.js (Toast Bildirim Sistemi, role='status', aria-live & 4s Hover Pause)", "static/js/state.js", "javascript"),
    ("DOSYA 6.3: static/js/ui_core.js (UI Çekirdeği, cardElementsMap, Evrensel Focus Trap & Semantik Butonlar)", "static/js/ui_core.js", "javascript"),
    ("DOSYA 6.4: static/js/ui_workspace.js (Okuma Alanı, Mobil Bottom Sheet, Çift Tamponlama Zoom & Dinamik Başlık)", "static/js/ui_workspace.js", "javascript"),
    ("DOSYA 6.5: static/js/ui_chat_settings.js (Sohbet Daktilo Hızlandırması & Ayarlar Focus Entegrasyonu)", "static/js/ui_chat_settings.js", "javascript"),
    ("DOSYA 6.6: static/js/ui_logs.js (İşlem Merkezi & Canlı Log Akışı Dialog Rolleri)", "static/js/ui_logs.js", "javascript"),
    ("DOSYA 7: static/manifest.json (PWA Manifest, Sıcak Kâğıt & Kehribar Renk Uyumu)", "static/manifest.json", "json"),
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
