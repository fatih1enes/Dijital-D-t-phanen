# 🏛️ DİJİTAL KÜTÜPHANE — BÜTÜN TASARIM, ARAYÜZ, HAREKET, ERİŞİLEBİLİRLİK VE İMZA ETKİLEŞİM SİSTEMİ KODLARI (FAZ A'DAN FAZ G'YE EKSİKSİZ MASTER SÜRÜM)

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


## DOSYA 0: static/css/app.css (CSS Cascade Layers: @layer legacy, tokens, design)

**Dosya Yolu:** `static/css/app.css`

```css
/**
 * 📚 Dijital Kütüphane - Unified Application Stylesheet
 * CSS Cascade Layers:
 * 1. legacy: Base and structural styles from style.css
 * 2. tokens: CSS Custom Properties design tokens from tokens.css
 * 3. design: High-level design system, typography, components, and responsive layouts from design.css
 */
@layer legacy, tokens, design;

@import url("style.css?v=2026110805") layer(legacy);
@import url("tokens.css?v=2026110805") layer(tokens);
@import url("design.css?v=2026110805") layer(design);

```


## DOSYA 1: static/css/tokens.css (Tasarım Tokenları & Tek Doğru Kaynak)

**Dosya Yolu:** `static/css/tokens.css`

```css
/**
 * 🎨 Dijital Kütüphane - Unified Design Tokens (Single Source of Truth)
 * Conforms to Apple Books / Linear / Tesla Editorial Minimalist Standard.
 */

:root {
  /* ═══════════════ 1. PRIMITIVES & SCALES ═══════════════ */
  --primitive-hue-warm: 35;
  --primitive-hue-accent: 15;
  --primitive-hue-info: 215;
  --primitive-hue-success: 142;
  --primitive-hue-warning: 38;
  --primitive-hue-danger: 0;

  /* Typography Stacks */
  --font-display: 'Instrument Serif', Georgia, serif;
  --font-serif: 'Newsreader', Georgia, serif;
  --font-ui: 'Geist', system-ui, -apple-system, sans-serif;
  --font-mono: 'Geist Mono', ui-monospace, Consolas, monospace;

  /* Typography Font Sizes (E6 Standard Scale) */
  --fs-label: 0.6875rem;                       /* Küçük etiket: Geist Mono */
  --fs-xs: 0.75rem;
  --fs-sm: 0.8125rem;
  --fs-base: 0.9375rem;                        /* Gövde: Geist 0.9375rem */
  --fs-book-title: 1.0625rem;                  /* Kitap adı & Okuma metni: Newsreader */
  --fs-h3: 1.35rem;                            /* H3 Bölüm başlığı: Newsreader 500 */
  --fs-h2: 2rem;                               /* H2 Modal başlığı: Instrument Serif 400 */
  --fs-h1: clamp(2.4rem, 5vw, 3.6rem);         /* H1 Header: Instrument Serif 400 */
  --fs-display: clamp(3.25rem, 9vw, 7rem);     /* Display: Hero Instrument Serif 400 */

  --lh-tight: 0.95;
  --lh-heading: 1.15;
  --lh-body: 1.55;
  --lh-reading: 1.7;

  /* Spacing Scale (4px Grid) */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 24px;
  --sp-6: 32px;
  --sp-7: 48px;
  --sp-8: 64px;
  --sp-9: 80px;
  --sp-12: 96px;

  --space-2xs: var(--sp-1);
  --space-xs: var(--sp-2);
  --space-sm: var(--sp-3);
  --space-md: var(--sp-4);
  --space-lg: var(--sp-5);
  --space-xl: var(--sp-6);
  --space-2xl: var(--sp-7);

  /* Radius Scale */
  --r-xs: 3px;
  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 16px;
  --r-full: 9999px;

  --radius-xs: var(--r-xs);
  --radius-sm: var(--r-sm);
  --radius: var(--r-md);
  --radius-md: var(--r-md);
  --radius-lg: var(--r-lg);
  --radius-xl: 20px;
  --radius-full: var(--r-full);

  /* ═══════════════ UNIFIED MOTION SYSTEM (Apple Books / Linear Standard) ═══════════════ */
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);   /* Varsayılan akıcı çıkış */
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1); /* Büyük geçişler */
  --ease-spring: linear(0, 0.402 7.4%, 0.711 15.3%, 0.929 23.7%, 1.008 33.3%,
                        1.067 41.6%, 1.059 49.2%, 1.015 61.5%, 0.999 74%, 1);
  --t-micro: 150ms;  /* Hover, renk, basma */
  --t-ui:    280ms;  /* Dropdown, panel, kart, modal */
  --t-page:  600ms;  /* Okuyucu, hero, büyük geçişler */

  /* Aliases for System Backwards Compatibility */
  --t-fast: var(--t-micro);
  --t-base: var(--t-ui);
  --duration-instant: 100ms;
  --duration-fast: var(--t-micro);
  --duration-normal: var(--t-ui);
  --duration-slow: var(--t-page);
  --ease-out-smooth: var(--ease-out);

  --transition-fast: var(--t-micro) var(--ease-out);
  --transition-smooth: var(--t-ui) var(--ease-out);
  --transition-spring: var(--t-ui) var(--ease-spring);
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --t-page: 0ms;
    --t-ui: 150ms;
    --t-micro: 100ms;
    --transition-fast: 100ms ease;
    --transition-smooth: 150ms ease;
    --transition-spring: 150ms ease;
  }
}

:root {

  /* ═══════════════ 2. LIGHT MODE SEMANTIC COLORS ═══════════════ */
  /* Surfaces */
  --paper: #f4f1eb;          /* Ana arka plan (Sıcak krem / kâğıt) */
  --surface: #ffffff;        /* Yükseltilmiş kart, modal, panel yüzeyi */
  --surface-hover: #faf8f5;  /* Yüzey hover */
  --paper-dark: #ebe7de;     /* Gömülü zemin, tab bar arkası, tag'ler */
  --sepia-pale: #e5dfd2;     /* Kapak placeholder zemini */
  --card-bg: var(--surface);
  --modal-bg: var(--surface);

  --color-canvas: var(--paper);
  --color-surface: var(--surface);
  --color-surface-hover: var(--surface-hover);
  --color-surface-sunken: var(--paper-dark);

  /* Typography & Contrast (WCAG Compliance) */
  --ink: #1f1e1b;            /* Derin antrasit ana metin (Kontrast: 14.8:1, WCAG AAA) */
  --muted: #6b675d;          /* İkincil yardımcı metin (Kontrast: 5.0:1, WCAG AA) */
  --muted-light: #8a8579;    /* Yalnızca dekoratif çizgiler ve devre dışı öğeler (Kontrast: 3.3:1) */
  --sepia: #6b675d;
  --sepia-light: #b9b3a6;

  --color-text-main: var(--ink);
  --color-text-secondary: var(--muted);
  --color-text-muted: var(--muted);
  --color-text-inverse: #ffffff;

  /* Lines & Borders */
  --line: #ddd8cf;           /* Birincil ince ayraç */
  --line-strong: #c4bdb0;    /* İnput, çerçeve ve aktif kenarlıklar */
  --line-subtle: #eae5dc;    /* Çok yumuşak ayırıcılar */

  --color-border-subtle: var(--line);
  --color-border-medium: var(--line-strong);
  --color-border-strong: #8a8579;

  /* Accent (Library Lamp & Warm Earth) */
  --accent: #5e523f;         /* Metin ve ikon vurgusu */
  --accent-soft: #786952;    /* Dolgulu butonlar, hover'lar */
  --accent-glow: rgba(94, 82, 63, 0.12);
  --accent-rgb: 94, 82, 63;
  --on-accent: #ffffff;

  --color-primary: var(--accent);
  --color-primary-hover: #4a4031;
  --color-primary-soft: var(--accent-soft);
  --color-primary-subtle: var(--accent-glow);

  /* Status Colors */
  --ok: #2e5f38;
  --ok-bg: #eaf3ec;
  --warn: #8c6314;
  --warn-bg: #fdf5e2;
  --danger: #9c2e25;
  --danger-bg: #fbeceb;
  --info: #2d587b;
  --info-bg: #eaf1f8;

  --color-accent-blue: var(--info);
  --color-accent-green: var(--ok);
  --color-accent-amber: var(--warn);
  --color-accent-red: var(--danger);

  /* Terminal & Diagnostics Console Tokens (Consistent Monospace Dark Surface) */
  --terminal-bg: #161513;
  --terminal-surface: #201e1b;
  --terminal-ink: #f0ece3;
  --terminal-muted: #a39e93;
  --terminal-line: rgba(240, 236, 227, 0.12);

  /* Shadows (Natural Diffusion) */
  --shadow-color: rgba(31, 30, 27, 0.08);
  --shadow-sm: 0 1px 3px rgba(31, 30, 27, 0.05), 0 1px 2px rgba(31, 30, 27, 0.03);
  --shadow-md: 0 4px 14px -2px rgba(31, 30, 27, 0.08), 0 2px 6px -1px rgba(31, 30, 27, 0.04);
  --shadow-lg: 0 18px 40px -10px rgba(31, 30, 27, 0.16), 0 4px 12px -2px rgba(31, 30, 27, 0.05);
  --shadow-xl: 0 24px 50px -12px rgba(31, 30, 27, 0.22), 0 8px 16px -4px rgba(31, 30, 27, 0.08);

  --shadow: var(--shadow-sm);
  --shadow-subtle: var(--shadow-sm);
  --shadow-medium: var(--shadow-md);
  --shadow-elevated: var(--shadow-lg);
  --shadow-modal: var(--shadow-xl);
  --elev-1: var(--shadow-sm);
  --elev-2: var(--shadow-lg);
}

/* ═══════════════ 3. DARK MODE (OBSIDIAN & WARM CHARCOAL) ═══════════════ */
[data-theme="dark"],
body.dark-mode {
  /* Surfaces */
  --paper: #161513;          /* Derin obsidian kömür */
  --surface: #201e1b;        /* Yükseltilmiş kart ve modal yüzeyi */
  --surface-hover: #292723;
  --paper-dark: #272522;
  --sepia-pale: #292723;
  --card-bg: var(--surface);
  --modal-bg: var(--surface);

  --color-canvas: var(--paper);
  --color-surface: var(--surface);
  --color-surface-hover: var(--surface-hover);
  --color-surface-sunken: var(--paper-dark);

  /* Typography & Contrast (WCAG Compliance) */
  --ink: #f0ece3;            /* Yüksek kontrastlı temiz krem metin (Kontrast: 15.5:1, WCAG AAA) */
  --muted: #a39e93;          /* Yardımcı metin (Kontrast: 6.8:1, WCAG AA) */
  --muted-light: #736e64;    /* Yalnızca dekoratif çizgiler ve devre dışı öğeler (Kontrast: 3.6:1) */
  --sepia: #a39e93;
  --sepia-light: #59554e;

  --color-text-main: var(--ink);
  --color-text-secondary: var(--muted);
  --color-text-muted: var(--muted);
  --color-text-inverse: #161513;

  /* Lines & Borders */
  --line: rgba(240, 236, 227, 0.11);
  --line-strong: rgba(240, 236, 227, 0.22);
  --line-subtle: rgba(240, 236, 227, 0.06);

  --color-border-subtle: var(--line);
  --color-border-medium: var(--line-strong);
  --color-border-strong: rgba(240, 236, 227, 0.35);

  /* Accent */
  --accent: #c4b59b;
  --accent-soft: #b0a187;
  --accent-glow: rgba(196, 181, 155, 0.16);
  --accent-rgb: 196, 181, 155;
  --on-accent: #161513;

  --color-primary: var(--accent);
  --color-primary-hover: #d5c8b0;
  --color-primary-soft: var(--accent-soft);
  --color-primary-subtle: var(--accent-glow);

  /* Status Colors */
  --ok: #88c495;
  --ok-bg: #1c2b20;
  --warn: #e4b85c;
  --warn-bg: #302613;
  --danger: #ea7f76;
  --danger-bg: #351b19;
  --info: #78aed9;
  --info-bg: #192633;

  /* Shadows */
  --shadow-color: rgba(0, 0, 0, 0.5);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 6px 18px -3px rgba(0, 0, 0, 0.65);
  --shadow-lg: 0 20px 48px -10px rgba(0, 0, 0, 0.85);
  --shadow-xl: 0 28px 60px -12px rgba(0, 0, 0, 0.92);

  --shadow: var(--shadow-sm);
  --shadow-subtle: var(--shadow-sm);
  --shadow-medium: var(--shadow-md);
  --shadow-elevated: var(--shadow-lg);
  --shadow-modal: var(--shadow-xl);
  --elev-1: var(--shadow-sm);
  --elev-2: var(--shadow-lg);
}
```


## DOSYA 2: static/css/design.css (Rafine Tasarım Sistemi, View Transitions, Dokunmatik F1, Odak F2 & Cila G1)

**Dosya Yolu:** `static/css/design.css`

```css
/**
 * 🏛️ Dijital Kütüphane — Tasarım Sistemi v5 (Refined Editorial & Tactile UI)
 * -------------------------------------------------------------------------
 * style.css'ten SONRA yüklenir.
 * Tüm görsel kararlar, mikrotıklamalar, tema geçişleri ve okunabilirlik
 * bu stil katmanından beslenir.
 */

/* ═══════════════ DESIGN SYSTEM: COMPONENTS & INTERFACE ═══════════════
 * All design tokens are centrally managed in static/css/tokens.css
 */


/* ═══════════════ 2. GENEL SIFIRLAMA, TİPOGRAFİ & TABAN (E6) ═══════════════ */
html {
  scrollbar-gutter: stable;
}

body {
  font-family: var(--font-ui);
  font-size: var(--fs-base);
  line-height: var(--lh-body);
  background-color: var(--paper);
  background-image: none;
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  padding-bottom: max(var(--sp-12), calc(var(--sp-8) + env(safe-area-inset-bottom)));
}

h1, h2, h3, h4, h5, h6,
.hero-title,
.modal-title,
.brand-title-row h1 {
  text-wrap: balance;
}

p,
.hero-subtitle,
.modal-author,
.book-summary-text {
  text-wrap: pretty;
}

.brand-title-row h1 {
  font-family: var(--font-serif);
  font-size: var(--fs-h1);
  font-weight: 400;
  line-height: var(--lh-heading);
  letter-spacing: -0.02em;
}

.modal-title {
  font-family: var(--font-serif);
  font-size: var(--fs-h2);
  font-weight: 400;
  line-height: var(--lh-heading);
}

.card-title {
  font-family: var(--font-reading);
  font-size: var(--fs-book-title);
  font-weight: 500;
  line-height: 1.35;
}

.card-badge,
.meta-chip,
.tag-badge,
.category-pill {
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  letter-spacing: 0.04em;
  text-transform: none;
}

::selection {
  background: var(--accent-glow);
  color: var(--ink);
}

::-moz-selection {
  background: var(--accent-glow);
  color: var(--ink);
}

input,
textarea {
  caret-color: var(--accent);
}

/* Modern, slim, theme-aware scrollbar */
* {
  scrollbar-width: thin;
  scrollbar-color: var(--muted-light) transparent;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--muted-light);
  border-radius: var(--r-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--muted);
}

/* Tabular numerals for all quantitative & status counters */
.stat-pill,
.stat-card-value,
.stat-total,
.badge,
.ops-badge,
.pdf-page-indicator,
.pdf-search-counter,
.card-progress-badge,
.modal-progress-wrap span,
.ops-tab-badge,
.shortcut-kbd,
.meta-chip,
.logs-timestamp,
.shelf-item-cat,
.shelf-item-info span,
.pdf-zoom-label {
  font-variant-numeric: tabular-nums;
}

:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* ═══════════════ 3. TEMA GEÇİŞİ (VIEW TRANSITIONS API) ═══════════════ */
html {
  color-scheme: light dark;
}

::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: var(--t-ui);
  animation-timing-function: var(--ease-out);
}

.theme-icon-spin {
  display: inline-block;
  animation: themeIconSpin var(--t-ui) var(--ease-out) both;
}

@keyframes themeIconSpin {
  0% { transform: rotate(-70deg) scale(0.7); opacity: 0; }
  100% { transform: rotate(0) scale(1); opacity: 1; }
}

/* ═══════════════ 4. DOKUNSAL BUTONLAR & ETKİLEŞİM GERİ BİLDİRİMİ ═══════════════ */
button,
.view-btn,
.dropdown-trigger,
.theme-toggle,
.btn-card-read,
.ops-btn-icon,
.logs-action-btn,
.btn-import,
.btn-sync,
.prompt-chip,
.meta-chip {
  position: relative;
  cursor: pointer;
  user-select: none;
  transition: transform var(--t-micro) var(--ease-out),
              background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              box-shadow var(--t-ui) var(--ease-out),
              color var(--t-micro) var(--ease-out);
}

.modal-close {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  width: 36px;
  height: 36px;
  border-radius: var(--r-sm);
  background: var(--paper-dark);
  border: 1px solid var(--line);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  font-size: 0.95rem;
  transition: transform var(--t-micro) var(--ease-out),
              background-color var(--t-micro) var(--ease-out),
              color var(--t-micro) var(--ease-out);
}

.modal-close:hover {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line-strong);
}

.modal-close:active {
  transform: translateY(1.5px) scale(0.95);
}

.modal-close i {
  transition: transform var(--t-ui) var(--ease-out);
}

.modal-close:hover i {
  transform: rotate(90deg) scale(1.1);
}

/* Basılma Efekti (Tactile Click) */
button:active:not(:disabled),
.view-btn:active,
.dropdown-trigger:active,
.theme-toggle:active,
.btn-card-read:active,
.modal-close:active,
.ops-btn-icon:active,
.logs-action-btn:active,
.btn-import:active,
.btn-sync:active {
  transform: scale(0.985);
}

/* ═══════════════ UNIFIED BUTTON COMPONENT SYSTEM (E5) ═══════════════ */
.btn,
.btn-import,
.btn-modal-primary,
.btn-modal-save,
.btn-settings-save,
.btn-empty-add,
.btn-banner-load,
.btn-modal-secondary,
.btn-modal-fav,
.btn-settings-cancel,
.btn-empty-clear,
.btn-cascade-reset,
.btn-modal-danger,
.btn-primary-action,
.btn-hero-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  height: 36px;
  padding: 0 var(--sp-4);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
  user-select: none;
  cursor: pointer;
  border: 1px solid transparent;
  box-sizing: border-box;
  box-shadow: none;
  transition: background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              color var(--t-micro) var(--ease-out),
              transform var(--t-micro) var(--ease-out);
}

.btn:active:not(:disabled),
.btn-import:active:not(:disabled),
.btn-modal-primary:active:not(:disabled),
.btn-modal-save:active:not(:disabled),
.btn-settings-save:active:not(:disabled),
.btn-empty-add:active:not(:disabled),
.btn-modal-secondary:active:not(:disabled),
.btn-settings-cancel:active:not(:disabled),
.btn-empty-clear:active:not(:disabled),
.btn-cascade-reset:active:not(:disabled),
.btn-modal-danger:active:not(:disabled),
.btn-primary-action:active:not(:disabled),
.btn-hero-primary:active:not(:disabled) {
  transform: scale(0.97);
}

.btn:disabled,
button:disabled,
[class*="btn-"]:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  pointer-events: none;
  transform: none;
}

/* Button Sizes */
.btn--sm,
.btn-primary-action.compact {
  height: 32px;
  padding: 0 var(--sp-3);
  font-size: 0.8125rem;
}

.btn--lg,
.btn-hero-primary {
  height: 44px;
  padding: 0 var(--sp-6);
  font-size: 1rem;
  border-radius: var(--r-md);
}

/* 1. Primary Variant */
.btn--primary,
.btn-import,
.btn-modal-primary,
.btn-modal-save,
.btn-settings-save,
.btn-empty-add,
.btn-banner-load,
.btn-primary-action,
.btn-hero-primary {
  background: var(--ink);
  color: var(--paper);
  border-color: var(--ink);
}

.btn--primary:hover,
.btn-import:hover,
.btn-modal-primary:hover,
.btn-modal-save:hover,
.btn-settings-save:hover,
.btn-empty-add:hover,
.btn-banner-load:hover,
.btn-primary-action:hover,
.btn-hero-primary:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--paper);
}

/* 2. Secondary Variant */
.btn--secondary,
.btn-modal-secondary,
.btn-modal-fav,
.btn-settings-cancel,
.btn-empty-clear,
.btn-cascade-reset,
.btn-sync {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line);
}

.btn--secondary:hover,
.btn-modal-secondary:hover,
.btn-modal-fav:hover,
.btn-settings-cancel:hover,
.btn-empty-clear:hover,
.btn-cascade-reset:hover,
.btn-sync:hover {
  background: var(--paper-dark);
  border-color: var(--line-strong);
  color: var(--ink);
}

.btn-modal-fav.is-fav {
  background: var(--accent-glow);
  border-color: var(--accent);
  color: var(--accent);
}

/* 3. Ghost Variant */
.btn--ghost {
  background: transparent;
  color: var(--muted);
  border-color: transparent;
}

.btn--ghost:hover {
  background: var(--paper-dark);
  color: var(--ink);
}

/* 4. Danger Variant */
.btn--danger,
.btn-modal-danger {
  background: var(--surface);
  color: var(--danger);
  border-color: var(--line);
}

.btn--danger:hover,
.btn-modal-danger:hover {
  background: var(--danger-bg);
  border-color: var(--danger);
  color: var(--danger);
}

/* ═══════════════ 5. HEADER & KOMPAKT NAV ═══════════════ */
header {
  position: relative;
  z-index: 1500;
  padding: var(--sp-6) 4rem var(--sp-5);
  background: transparent;
  border-bottom: 1px solid var(--line);
}

header::before { display: none !important; }

.brand-label {
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
  color: var(--muted);
  margin-bottom: var(--sp-1);
}

h1 {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: clamp(2.6rem, 5.5vw, 3.8rem);
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--ink);
}

h1 em {
  font-style: italic;
  color: var(--ink);
}

.brand-title-row {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.btn-primary-action.hidden,
#header-add-book-btn[style*="display: none"],
#compact-add-book-btn[style*="display: none"] {
  display: none !important;
}

.header-action-divider {
  width: 1px;
  height: 20px;
  background: var(--line);
  margin: 0 0.2rem;
}

.header-icon-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--r-sm);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--muted);
  box-shadow: var(--shadow-sm);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--transition-fast) ease;
}

.header-icon-btn:hover {
  background: var(--paper-dark);
  color: var(--ink);
  border-color: var(--line-strong);
}

.header-icon-btn:active {
  transform: scale(0.96);
}

.header-icon-btn.compact-icon {
  width: 32px;
  height: 32px;
}

.header-tools-wrapper {
  position: relative;
}

.header-tools-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 250px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-lg);
  padding: 0.4rem;
  z-index: 2500;
  display: flex;
  flex-direction: column;
  gap: 2px;
  animation: toolsMenuFadeIn var(--t-micro) var(--ease-out);
}

@keyframes toolsMenuFadeIn {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes toolsMenuFadeOut {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-4px); }
}

.header-tools-menu.closing {
  pointer-events: none;
  animation: toolsMenuFadeOut var(--t-micro) var(--ease-out) forwards;
}

.tools-menu-label {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--sepia);
  padding: 0.35rem 0.6rem 0.25rem;
  font-weight: 600;
}

.tools-menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.75rem;
  border-radius: var(--r-xs);
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  color: var(--ink);
  font-family: var(--font-ui);
  transition: background var(--t-micro) var(--ease-out);
}

.tools-menu-item:hover {
  background: var(--paper-dark);
}

.tools-menu-item i {
  width: 18px;
  text-align: center;
  color: var(--accent);
  font-size: 0.85rem;
  flex-shrink: 0;
}

.tools-item-content {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.tools-item-title {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--ink);
  line-height: 1.2;
}

.tools-item-desc {
  font-size: var(--fs-xs);
  color: var(--muted);
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.compact-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: color-mix(in srgb, var(--surface) 85%, transparent);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
  padding: var(--sp-2) 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transform: translateY(-101%);
  transition: transform var(--t-ui) var(--ease-out);
  z-index: 2000;
}

.compact-nav.visible {
  transform: translateY(0);
}

.compact-brand {
  display: flex;
  flex-direction: column;
}

.compact-brand-sub {
  font-family: var(--font-mono);
  font-size: 0.55rem;
  letter-spacing: 0.2em;
  color: var(--sepia);
  text-transform: uppercase;
}

.compact-brand-title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  color: var(--ink);
  line-height: 1.1;
}

.compact-actions {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.stat-pill {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  border-radius: var(--r-full);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  padding: 4px 10px;
  font-variant-numeric: tabular-nums;
  display: inline-flex;
  align-items: center;
}

.stat-pill i { color: var(--muted); }
.stat-pill span { color: var(--ink); font-weight: 600; }

#stat-total,
.stat-total-val {
  font-variant-numeric: tabular-nums;
  display: inline-block;
  transition: transform var(--t-micro) var(--ease-spring);
}

@keyframes statCountBump {
  0% { transform: scale(1); }
  50% { transform: scale(1.18); color: var(--accent); }
  100% { transform: scale(1); }
}

.stat-count-bump {
  animation: statCountBump 320ms var(--ease-spring);
}

/* ═══════════════ UNIFORM ICON SYSTEM (E3) ═══════════════ */
i[class*="fa-"],
svg {
  color: currentColor;
  vertical-align: -0.125em;
  display: inline-block;
  flex-shrink: 0;
}

i[class*="fa-heart"] {
  transition: transform var(--t-micro) var(--ease-spring), color var(--t-micro) var(--ease-out);
}

.theme-toggle {
  width: 36px;
  height: 36px;
  border-radius: var(--r-sm);
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.theme-toggle:hover {
  background: var(--paper-dark);
  color: var(--ink);
  border-color: var(--line);
}

/* ═══════════════ REFINED UTILITY & CALLOUT SYSTEM (E4) ═══════════════ */
.callout {
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--r-md);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  line-height: 1.5;
  display: flex;
  align-items: flex-start;
  gap: var(--sp-2);
}

.callout--warn {
  background: var(--warn-bg);
  border: 1px solid var(--warn);
  color: var(--warn);
}

.callout--danger {
  background: var(--danger-bg);
  border: 1px solid var(--danger);
  color: var(--danger);
}

.callout--ok {
  background: var(--ok-bg);
  border: 1px solid var(--ok);
  color: var(--ok);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  margin-bottom: var(--sp-3);
}

.field-label {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--ink);
  margin-bottom: var(--sp-1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.field-input,
.field-textarea {
  width: 100%;
  padding: 0.65rem var(--sp-3);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface);
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color var(--t-micro) var(--ease-out), box-shadow var(--t-micro) var(--ease-out);
}

.field-input:focus,
.field-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--line-strong);
}

.shortcut-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--sp-2) 0;
  border-bottom: 1px solid var(--line);
}

.shortcut-key {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  background: var(--paper-dark);
  border: 1px solid var(--line);
  border-radius: var(--r-xs);
  padding: 2px 6px;
  color: var(--ink);
}

.modal-top {
  height: 3px;
  background: var(--accent);
  width: 100%;
}

/* ═══════════════ 6. KONTROL PANELİ & ARAMA & FİLTRELER ═══════════════ */
.controls-panel {
  position: relative;
  z-index: 50;
  background: transparent;
  border: none;
  box-shadow: none;
}

.search-wrap {
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-wrap:focus-within {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.search-wrap input {
  background: transparent;
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: var(--fs-base);
}

.search-wrap input::placeholder {
  color: var(--muted);
}

#btn-deep-search-toggle {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  border-radius: var(--r-xs);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 500;
}

#btn-deep-search-toggle:hover,
#btn-deep-search-toggle.active {
  color: var(--ink);
  border-color: var(--ink);
}

.dropdown-trigger {
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  box-shadow: var(--shadow-sm);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--ink);
}

.dropdown-trigger:hover,
.custom-dropdown.open .dropdown-trigger {
  border-color: var(--ink);
}

/* Akıcı Dropdown Animasyonu (Standard Micro-Motion) */
@keyframes dropdownIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-menu {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-lg);
  padding: var(--sp-1);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out), visibility var(--t-micro);
  pointer-events: none;
}

.custom-dropdown.open .dropdown-menu,
.dropdown.open .dropdown-menu,
.open > .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
  animation: dropdownIn var(--t-micro) var(--ease-out);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  width: 100%;
  border: none;
  background: transparent;
  text-align: left;
  border-radius: var(--r-xs);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  color: var(--ink);
  padding: 8px 12px;
  cursor: pointer;
}

.dropdown-item:hover {
  background: var(--paper-dark);
}

.dropdown-item.active {
  background: var(--accent-soft);
  color: var(--on-accent);
}

/* Segmentli Görünüm Değiştirici */
.view-toggle {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  padding: 3px;
  gap: 3px;
}

.view-btn {
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--r-xs);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--muted);
  padding: 5px 12px;
}

.view-btn:hover:not(.active) {
  color: var(--ink);
}

.view-btn.active {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line);
  box-shadow: var(--shadow-sm);
}

.view-btn.active i {
  color: var(--accent);
}

.actions-group .view-btn.active {
  background: var(--accent-glow);
  color: var(--accent);
}

/* ═══════════════ 10. KİTAP KARTLARI (EDITORIAL MINIMALISM) ═══════════════ */
#grid-view {
  grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
  gap: var(--sp-6) var(--sp-5);
}

.book-card {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  display: flex;
  flex-direction: column;
  transition: transform var(--t-ui) var(--ease-out);
}

.book-card::before,
.book-card::after { display: none !important; }

@media (hover: hover) and (pointer: fine) {
  .book-card:hover {
    transform: translateY(-4px);
  }
  .book-card:hover .card-cover {
    box-shadow: inset 0 0 0 1px var(--line), var(--shadow-lg);
  }
  .book-card:hover .card-cover img,
  .book-card:hover .card-cover-placeholder {
    transform: scale(1.02);
  }
}

.book-card:active {
  transform: translateY(-2px) scale(0.99);
  transition-duration: var(--t-micro);
}

.card-cover {
  aspect-ratio: 2/3;
  border-radius: var(--r-xs);
  background: var(--sepia-pale);
  box-shadow: inset 0 0 0 1px var(--line), var(--shadow-sm);
  transition: box-shadow var(--t-ui) var(--ease-out);
  position: relative;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  top: 0; bottom: 0; left: 0; width: 8px;
  background: linear-gradient(90deg, rgba(0, 0, 0, 0.22) 0%, rgba(0, 0, 0, 0.06) 60%, transparent 100%);
  pointer-events: none;
  z-index: 2;
}

.card-cover::after {
  content: '';
  position: absolute;
  top: 0; bottom: 0; left: 0; width: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-right: 1px solid rgba(255, 255, 255, 0.15);
  pointer-events: none;
}

.book-card:hover .card-cover {
  box-shadow: inset 0 0 0 1px var(--line), var(--shadow-md);
}

.card-cover img {
  transition: transform var(--t-ui) var(--ease-out);
}

.book-card:hover .card-cover img {
  transform: none;
}

.card-cat-badge {
  background: var(--surface);
  color: var(--ink);
  top: auto;
  right: auto;
  bottom: var(--sp-2);
  left: var(--sp-2);
  padding: 3px 8px;
  border-radius: var(--r-xs);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 500;
  box-shadow: var(--shadow-sm);
  opacity: 0;
  transform: translateY(4px);
  transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out);
}

.book-card:hover .card-cat-badge {
  opacity: 1;
  transform: translateY(0);
}

.btn-favorite-card {
  top: var(--sp-2);
  right: var(--sp-2);
  width: 30px;
  height: 30px;
  border-radius: var(--r-sm);
  background: var(--surface);
  border: 1px solid var(--line);
  backdrop-filter: none;
  box-shadow: var(--shadow-sm);
  opacity: 0;
  transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out), background var(--t-micro);
}

.book-card:hover .btn-favorite-card,
.btn-favorite-card:focus-visible,
.is-selection-mode .btn-favorite-card {
  opacity: 1;
}

.btn-favorite-card:hover {
  background: var(--paper-dark);
  transform: none;
}

.card-body {
  padding: var(--sp-3) 0 var(--sp-2);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-family: var(--font-serif);
  font-weight: 500;
  font-size: var(--fs-lg);
  line-height: 1.25;
  letter-spacing: -0.01em;
  color: var(--ink);
  margin-bottom: var(--sp-1);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-author {
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  color: var(--muted);
  border: none;
  padding: 0;
  margin-bottom: var(--sp-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-summary,
.btn-card-read {
  display: none !important;
}

.btn-card-read:hover {
  color: var(--accent);
  background: transparent;
  transform: none;
}

.btn-card-read:hover::after {
  transform: translateX(4px);
}

/* ═══════════════ 11. VIEW GEÇİŞ ANİMASYONU (PÜRÜZSÜZ & AKICI) ═══════════════ */
.view-fade-in {
  animation: smoothViewReveal var(--t-ui) var(--ease-out) both;
}

@keyframes smoothViewReveal {
  0% {
    opacity: 0;
    transform: translateY(10px) scale(0.995);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ═══════════════ 12. SISTEM & İŞLEM LOGLARI (KRİSTAL NETLİKTE OKUNABİLİRLİK) ═══════════════ */
.logs-modal {
  background: rgba(22, 21, 19, 0.5);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  transition: opacity var(--t-ui) var(--ease-out);
}

.logs-panel {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-lg);
  color: var(--ink);
  font-family: var(--font-ui);
}

.logs-header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  padding: var(--sp-3) var(--sp-5);
}

.logs-header h4,
.logs-title-wrap h4 {
  font-family: var(--font-ui);
  font-size: var(--fs-base);
  font-weight: 600;
  color: var(--ink);
}

.logs-title-icon {
  color: var(--muted);
}

.logs-status-pill {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  color: var(--muted);
  border-radius: var(--r-full);
}

.logs-status-pill .status-dot {
  background: var(--ok);
  box-shadow: none;
}

.logs-action-btn {
  background: var(--surface);
  border: 1px solid var(--line-strong);
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 500;
  border-radius: var(--r-sm);
  box-shadow: var(--shadow-sm);
  padding: 6px 12px;
}

.logs-action-btn:hover {
  background: var(--paper-dark);
  border-color: var(--ink);
}

.logs-action-btn.logs-btn-danger:hover {
  background: var(--danger-bg);
  color: var(--danger);
  border-color: var(--danger);
}

/* Sidebar & Kategoriler */
.logs-sidebar {
  background: var(--paper);
  border-right: 1px solid var(--line);
}

.logs-section-title {
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 600;
}

.logs-filter-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  border-radius: var(--r-sm);
  padding: 8px 12px;
}

.logs-filter-btn:hover:not(.active) {
  background: var(--paper-dark);
  color: var(--ink);
}

.logs-filter-btn.active {
  background: var(--surface);
  color: var(--ink);
  border-color: var(--line);
  box-shadow: var(--shadow-sm);
  font-weight: 600;
}

.logs-filter-btn small {
  background: var(--paper-dark);
  color: var(--muted);
  border-radius: var(--r-full);
  padding: 2px 7px;
  font-variant-numeric: tabular-nums;
}

.logs-filter-btn.active small {
  background: var(--accent-glow);
  color: var(--accent);
}

/* Toolbar & Arama */
.logs-content-area {
  background: var(--surface);
}

.logs-toolbar {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.logs-search-wrap input {
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
}

.logs-search-wrap input::placeholder {
  color: var(--muted);
}

.logs-search-wrap input:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.logs-level-btn {
  background: var(--paper);
  border: 1px solid var(--line);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 500;
  border-radius: var(--r-sm);
}

.logs-level-btn.active {
  background: var(--paper-dark);
  border-color: var(--line-strong);
  color: var(--ink);
  font-weight: 600;
}

/* Log Satırları & Yüksek Kontrastlı Metinler */
.logs-main {
  background: var(--surface);
  padding: var(--sp-2) var(--sp-4);
}

.log-card {
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--line);
  border-left: 3px solid var(--line-strong);
  border-radius: 0;
  padding: var(--sp-3) var(--sp-4);
  transition: background var(--t-micro) var(--ease-out);
}

.log-card:hover {
  background: var(--surface-hover);
}

.log-card.lvl-info { border-left-color: var(--ok); }
.log-card.lvl-warning { border-left-color: var(--warn); }
.log-card.lvl-error { border-left-color: var(--danger); }
.log-card.lvl-debug { border-left-color: var(--muted-light); }

/* Log Mesajı: Asla soluk olmayacak! */
.log-message {
  color: var(--ink);
  font-family: var(--font-mono);
  font-size: 0.84rem;
  line-height: 1.55;
  margin-top: 4px;
}

.log-time {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  font-variant-numeric: tabular-nums;
}

/* Canlı ve Net Seviye Rozetleri */
.log-level-tag {
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: var(--r-xs);
  padding: 2px 7px;
}

.log-level-tag.INFO {
  background: var(--ok-bg);
  color: var(--ok);
  border: 1px solid color-mix(in srgb, var(--ok) 30%, transparent);
}

.log-level-tag.WARNING {
  background: var(--warn-bg);
  color: var(--warn);
  border: 1px solid color-mix(in srgb, var(--warn) 30%, transparent);
}

.log-level-tag.ERROR {
  background: var(--danger-bg);
  color: var(--danger);
  border: 1px solid color-mix(in srgb, var(--danger) 30%, transparent);
}

.log-level-tag.DEBUG {
  background: var(--paper-dark);
  color: var(--muted);
  border: 1px solid var(--line);
}

.log-cat-tag {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  border-radius: var(--r-xs);
  padding: 2px 6px;
}

.log-tool-btn {
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  border-radius: var(--r-xs);
  padding: 3px 8px;
}

.log-tool-btn:hover {
  background: var(--paper-dark);
  color: var(--ink);
}

.log-context-box {
  background: var(--paper-dark);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  color: var(--ink);
}

.log-ctx-key { color: var(--muted); font-weight: 600; }
.log-ctx-val { color: var(--ink); }

.logs-footer {
  background: var(--surface);
  border-top: 1px solid var(--line);
  color: var(--muted);
}

/* ═══════════════ 13. MODAL VE AYARLAR PENCERELERİ ═══════════════ */
@keyframes modalOverlayIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modalOverlayOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@keyframes modalPopIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes modalPopOut {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.98) translateY(4px);
  }
}

.modal-overlay {
  background: rgba(22, 21, 19, 0.5);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

.modal-overlay.open {
  display: flex;
  animation: modalOverlayIn var(--t-ui) var(--ease-out) forwards;
}

.modal-overlay.open .modal {
  animation: modalPopIn var(--t-ui) var(--ease-out) forwards;
  opacity: 1;
  pointer-events: auto;
}

.modal-overlay.closing {
  display: flex;
  pointer-events: none;
  animation: modalOverlayOut var(--t-micro) var(--ease-out) forwards;
}

.modal-overlay.closing .modal {
  pointer-events: none;
  animation: modalPopOut var(--t-micro) var(--ease-out) forwards;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-lg);
}

.modal-top { display: none !important; }

.modal-title {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: var(--fs-2xl);
  color: var(--ink);
}

.modal-cat,
.modal-section-label,
.settings-section-label {
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0;
}

.modal-author {
  font-family: var(--font-serif);
  font-style: italic;
  color: var(--muted);
}

.modal-summary {
  font-family: var(--font-serif);
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--ink);
}

.modal-cover-wrap img,
.modal-cover-empty {
  border-radius: var(--r-xs);
  box-shadow: var(--shadow-md);
}

.settings-header,
.settings-footer {
  background: var(--surface);
}

.settings-tabs {
  background: var(--paper);
  border-bottom: 1px solid var(--line);
}

.settings-tab-btn {
  font-family: var(--font-ui);
  border-radius: var(--r-sm);
  color: var(--muted);
}

.settings-tab-btn.active {
  background: var(--surface);
  color: var(--ink);
  box-shadow: var(--shadow-sm);
  font-weight: 600;
}

.settings-section-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  box-shadow: var(--shadow-sm);
}

/* ═══════════════ 14. İŞLEM MERKEZİ & SOHBET WIDGET (FLOATING PILL DOCK) ═══════════════ */
#ops-center {
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-lg);
  font-family: var(--font-ui);
  color: var(--ink);
  left: 1.75rem;
  bottom: 4.8rem;
  transform: translateY(8px);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out), visibility var(--t-micro);
}

#ops-center.active {
  transform: translateY(0);
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  animation: opsCenterIn var(--t-ui) var(--ease-out);
}

.ops-header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  color: var(--ink);
}

/* Sol Alt İşlem Merkezi Kapsülü (Floating Status Pill) */
.ops-toggle {
  position: fixed;
  left: 1.75rem;
  bottom: 1.5rem;
  width: auto;
  height: 42px;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-full);
  box-shadow: var(--shadow-md);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  z-index: 2100;
  transform: none;
  transition: transform var(--t-ui) var(--ease-out),
              box-shadow var(--t-ui) var(--ease-out),
              background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out);
}


.ops-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 3px var(--ok-bg);
  flex-shrink: 0;
  transition: all var(--t-ui) var(--ease-out);
}

.ops-toggle.is-processing .ops-status-dot {
  background: var(--warn);
  box-shadow: 0 0 0 3px var(--warn-bg);
  animation: pulseBeacon 1.2s infinite ease-in-out;
}

.ops-toggle .ops-label {
  display: inline;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.ops-badge {
  position: static;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  font-size: 0.7rem;
  font-family: var(--font-mono);
  font-weight: 600;
  background: var(--paper-dark);
  color: var(--muted);
  border-radius: var(--r-full);
  border: 1px solid var(--line);
}

/* Sağ Alt Kütüphane Asistanı (Kapalıyken Yüzen Kapsül, Açıkken Sohbet Penceresi) */
#chat-panel {
  position: fixed;
  right: 1.75rem;
  bottom: 1.5rem;
  z-index: 2500;
}

/* Kapalı Durum: Kusursuz Yüzen Hap (Input ve Body Tamamen Gizli) */
#chat-panel:not(.active) {
  width: auto;
  height: 42px;
  overflow: hidden;
  transform: none;
  border-radius: var(--r-full);
  background: var(--surface);
  border: 1px solid var(--line-strong);
  box-shadow: var(--shadow-md);
  transition: transform var(--t-ui) var(--ease-out),
              box-shadow var(--t-ui) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              background-color var(--t-micro) var(--ease-out);
}


#chat-panel:not(.active) .chat-body,
#chat-panel:not(.active) .chat-input-area {
  display: none !important;
}

#chat-panel:not(.active) .chat-header {
  height: 40px;
  width: auto;
  padding: 0 16px 0 10px;
  background: transparent;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transform: none;
  box-shadow: none;
}

.chat-header-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.chat-ai-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-glow);
  color: var(--accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  flex-shrink: 0;
}

#chat-panel .chat-header h3 {
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  font-weight: 500;
  letter-spacing: -0.01em;
  margin: 0;
  color: var(--ink);
  white-space: nowrap;
}

#chat-panel .chat-chevron {
  font-size: 0.72rem;
  color: var(--muted);
  display: inline-flex;
  align-items: center;
  transition: transform var(--t-ui) var(--ease-out);
}

/* Açık Durum: Yaylanarak Açılan Modern Sohbet Paneli */
@keyframes chatPanelExpand {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

#chat-panel.active {
  width: min(380px, calc(100vw - 2rem));
  height: auto;
  transform: none;
  transform-origin: bottom right;
  border-radius: var(--r-lg);
  background: var(--surface);
  border: 1px solid var(--line-strong);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: chatPanelExpand var(--t-ui) var(--ease-out) both;
}

#chat-panel.active .chat-header {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  background: var(--paper-dark);
  border: none;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transform: none;
}

#chat-panel.active .chat-header h3 {
  font-size: 0.85rem;
  font-weight: 600;
}

#chat-panel.active .chat-chevron {
  transform: rotate(180deg);
}

#chat-panel.active .chat-body {
  display: flex;
  height: 340px;
  background: var(--surface);
}

#chat-panel.active .chat-input-area {
  display: flex;
  background: var(--paper);
  border-top: 1px solid var(--line);
  padding: 0.75rem 1rem;
}

.chat-input-area input {
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  color: var(--ink);
}

.chat-input-area input:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

#scroll-top-btn {
  right: 1.75rem;
  bottom: 4.8rem;
  margin-bottom: 0;
  width: 40px;
  height: 40px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-full);
  box-shadow: var(--shadow-md);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transform: translateY(12px);
  transition: opacity var(--t-ui) var(--ease-out), transform var(--t-ui) var(--ease-out), background-color var(--t-micro);
}

#scroll-top-btn.visible {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
  transform: translateY(0);
}

/* ═══════════════ 8. SIFIR DURUMU (ZERO STATE) & EDİTORYAL HERO ═══════════════ */
.import-zone {
  display: block;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: clamp(3rem, 10vh, 7rem) var(--sp-6);
  box-sizing: border-box;
}

.zero-state-hero {
  max-width: 880px;
  margin: 0;
  padding: var(--sp-6) 0;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--r-lg);
  box-shadow: none;
  text-align: left;
  position: relative;
  transition: background-color var(--t-ui) var(--ease-out),
              border-color var(--t-ui) var(--ease-out);
}

.zero-state-hero.dragover {
  background: var(--surface-hover);
  border-color: var(--line-strong);
}

@keyframes heroMaskReveal {
  from {
    opacity: 0;
    transform: translateY(20px);
    clip-path: inset(0 0 100% 0);
  }
  to {
    opacity: 1;
    transform: translateY(0);
    clip-path: inset(0 0 0 0);
  }
}

@keyframes heroFadeUp {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-kicker {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.14em;
  color: var(--muted);
  text-transform: uppercase;
  margin-bottom: var(--sp-4);
  animation: heroFadeUp var(--t-page) var(--ease-out) both;
  animation-delay: 0ms;
}

.hero-title {
  font-family: var(--font-serif);
  font-size: clamp(3.25rem, 9vw, 7rem);
  font-weight: 400;
  font-style: normal;
  color: var(--ink);
  letter-spacing: -0.03em;
  line-height: 0.95;
  margin: 0 0 var(--sp-5) 0;
  text-wrap: balance;
  animation: heroMaskReveal var(--t-page) var(--ease-out) both;
  animation-delay: 80ms;
}

.hero-title em {
  font-style: italic;
  font-weight: 400;
  color: var(--accent);
}

.hero-subtitle {
  font-family: var(--font-ui);
  font-size: clamp(1rem, 1.8vw, 1.25rem);
  color: var(--muted);
  max-width: 46ch;
  line-height: 1.55;
  font-weight: 400;
  margin: 0 0 var(--sp-6) 0;
  text-wrap: pretty;
  animation: heroFadeUp var(--t-page) var(--ease-out) both;
  animation-delay: 160ms;
}

.hero-primary-actions {
  margin-bottom: var(--sp-4);
  display: flex;
  justify-content: flex-start;
  animation: heroFadeUp var(--t-page) var(--ease-out) both;
  animation-delay: 240ms;
}

.btn-hero-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-2);
  height: 48px;
  padding: 0 var(--sp-6);
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 500;
  background: var(--ink);
  color: var(--paper);
  border: 1px solid var(--ink);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              transform var(--t-micro) var(--ease-out);
}

.btn-hero-primary:hover {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--paper);
}

.btn-hero-primary:active {
  transform: scale(0.97);
}

.hero-secondary-links {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  font-family: var(--font-ui);
  font-size: 0.875rem;
  color: var(--muted);
  animation: heroFadeUp var(--t-page) var(--ease-out) both;
  animation-delay: 320ms;
}

.hero-text-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--muted);
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
  text-decoration-color: var(--line-strong);
  cursor: pointer;
  font-family: inherit;
  font-size: inherit;
  display: inline-flex;
  align-items: center;
  transition: color var(--t-micro) var(--ease-out),
              text-decoration-color var(--t-micro) var(--ease-out);
}

.hero-text-link:hover {
  color: var(--ink);
  text-decoration-color: var(--ink);
}

.hero-text-link:active {
  transform: scale(0.97);
}

.hero-link-sep {
  color: var(--muted-light);
  user-select: none;
}

@media (prefers-reduced-motion: reduce) {
  .hero-kicker,
  .hero-title,
  .hero-subtitle,
  .hero-primary-actions,
  .hero-secondary-links {
    animation: none;
    opacity: 1;
    transform: none;
    clip-path: none;
  }
}

/* ═══════════════ DERİN ARAMA BUTONU ═══════════════ */
.btn-deep-search-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  height: 28px;
  padding: 0 0.65rem;
  border-radius: var(--r-sm);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--muted);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  margin-right: 6px;
  transition: all 140ms var(--ease-out);
  transform: none;
}

.btn-deep-search-toggle:hover {
  border-color: var(--line-strong);
  color: var(--ink);
  background: var(--paper-dark);
  transform: none;
}

.btn-deep-search-toggle.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #ffffff;
}

/* ═══════════════ 9. ÖNE ÇIKAN ESERLER (RECENT SHELF) ═══════════════ */
.recent-shelf-container {
  margin-bottom: var(--sp-6);
  padding-bottom: var(--sp-5);
  border-bottom: 1px solid var(--line);
}

.recent-shelf-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: var(--sp-4);
}

.recent-shelf-title .shelf-label {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  color: var(--muted);
  text-transform: uppercase;
  display: block;
  margin-bottom: 2px;
}

.recent-shelf-title h3 {
  font-family: var(--font-serif);
  font-size: 1.35rem;
  font-weight: 400;
  color: var(--ink);
  margin: 0;
  letter-spacing: -0.01em;
}

.shelf-count {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--muted);
}

.recent-shelf-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--sp-4);
}

.shelf-item {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  width: 100%;
  text-align: left;
  font-family: inherit;
  padding: var(--sp-2) var(--sp-3);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out);
}

@media (hover: hover) and (pointer: fine) {
  .shelf-item:hover {
    background: var(--paper-dark);
    border-color: var(--line-strong);
  }
}

.shelf-item:active {
  transform: scale(0.985);
}

.shelf-item-cover {
  width: 44px;
  height: 62px;
  flex-shrink: 0;
  border-radius: var(--r-xs);
  overflow: hidden;
  background: var(--sepia-pale);
  box-shadow: var(--shadow-sm);
  position: relative;
}

.shelf-item-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.shelf-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--muted);
  font-size: 0.85rem;
}

.shelf-item-info {
  flex: 1;
  min-width: 0;
}

.shelf-item-cat {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: block;
}

.shelf-item-title {
  font-family: var(--font-serif);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--ink);
  margin: 1px 0 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.shelf-item-author {
  font-family: var(--font-ui);
  font-size: 0.78rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

/* ═══════════════ WORKSPACE READER POLISH ═══════════════ */
.workspace-book-banner {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  height: 34px;
  padding: 0 0.75rem;
  border-radius: var(--r-sm);
  background: var(--surface);
  border: 1px solid var(--line);
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: var(--fs-xs);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 140ms var(--ease-out);
  box-shadow: none;
  transform: none;
}

.workspace-book-banner:hover {
  background: var(--paper-dark);
  border-color: var(--line-strong);
  transform: none;
}

.workspace-book-banner:active {
  transform: scale(0.985);
}

.workspace-book-banner .banner-icon {
  font-size: 0.8rem;
  color: var(--accent);
  display: flex;
  align-items: center;
}

.workspace-book-banner .banner-content {
  display: flex;
  align-items: center;
}

.workspace-book-banner .banner-title {
  font-size: var(--fs-xs);
  font-weight: 500;
  color: var(--ink);
}

.workspace-book-banner .banner-subtitle,
.workspace-book-banner .btn-banner-load {
  display: none !important;
}

.workspace-book-banner.loaded {
  border-color: var(--ok);
  background: var(--ok-bg);
  color: var(--ok);
}

.workspace-book-banner.loaded .banner-icon,
.workspace-book-banner.loaded .banner-title {
  color: var(--ok);
}

/* ═══════════════ FLUID INTERACTION PHYSICS ═══════════════ */
/* İkon Butonları */
.header-icon-btn,
.view-btn,
.theme-toggle-btn,
.ops-btn-icon,
.ops-btn-close {
  cursor: pointer;
  transition: background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              color var(--t-micro) var(--ease-out),
              transform var(--t-micro) var(--ease-out);
}

/* Yüzen Haplar (#ops-toggle ve #chat-panel kapalı hapı) */
.ops-toggle,
#chat-panel:not(.active) {
  cursor: pointer;
  transition: background-color var(--t-micro) var(--ease-out),
              border-color var(--t-micro) var(--ease-out),
              box-shadow var(--t-micro) var(--ease-out),
              transform var(--t-micro) var(--ease-out);
}

/* ── MOUSE HOVER: Sadece fare/pointer cihazlarda çalışır, dokunmatik ekranda asla yapışmaz ── */
@media (hover: hover) and (pointer: fine) {
  .btn--primary:hover:not(:disabled),
  .btn-import:hover:not(:disabled),
  .btn-modal-primary:hover:not(:disabled),
  .btn-modal-save:hover:not(:disabled),
  .btn-settings-save:hover:not(:disabled),
  .btn-empty-add:hover:not(:disabled),
  .btn-banner-load:hover:not(:disabled),
  .btn-primary-action:hover:not(:disabled),
  .btn-hero-primary:hover:not(:disabled) {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--paper);
    transform: none;
  }

  .btn--secondary:hover:not(:disabled),
  .btn-modal-secondary:hover:not(:disabled),
  .btn-modal-fav:hover:not(:disabled),
  .btn-settings-cancel:hover:not(:disabled),
  .btn-empty-clear:hover:not(:disabled),
  .btn-cascade-reset:hover:not(:disabled),
  .btn-sync:hover:not(:disabled) {
    background: var(--paper-dark);
    border-color: var(--line-strong);
    color: var(--ink);
    transform: none;
  }

  .header-icon-btn:hover:not(:disabled),
  .view-btn:hover:not(:disabled),
  .theme-toggle-btn:hover:not(:disabled),
  .ops-btn-icon:hover:not(:disabled),
  .ops-btn-close:hover:not(:disabled) {
    background: var(--paper-dark);
    color: var(--ink);
    transform: none;
  }

  .ops-toggle:hover {
    background: var(--surface-hover);
    border-color: var(--ink);
    transform: none;
  }

  #chat-panel:not(.active):hover {
    background: var(--surface-hover);
    border-color: var(--ink);
    transform: none;
  }

  #scroll-top-btn:hover {
    background: var(--paper-dark);
    border-color: var(--ink);
    transform: none;
  }
}

/* ── BASMA GERİ BİLDİRİMİ: Hem fare hem dokunmatik ekranda çalışır ── */
button:active:not(:disabled),
.btn:active:not(:disabled),
[class*="btn-"]:active:not(:disabled) {
  transform: scale(0.97);
}

.header-icon-btn:active:not(:disabled),
.view-btn:active:not(:disabled),
.theme-toggle-btn:active:not(:disabled),
.ops-btn-icon:active:not(:disabled),
.ops-btn-close:active:not(:disabled) {
  transform: scale(0.94);
}

.ops-toggle:active,
#chat-panel:not(.active):active {
  transform: scale(0.96);
}

/* Zero-State Hero Giriş Animasyonu ve Derinliği */
@keyframes heroCardReveal {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.99);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}



/* Kitap Kartları İpeksi Hover */
.book-card {
  transition: transform var(--t-ui) var(--ease-out);
}

.book-card:hover {
  transform: translateY(-4px);
}

.card-cover img {
  transition: transform var(--t-page) var(--ease-out);
}

.book-card:hover .card-cover img {
  transform: scale(1.025);
}

/* ═══════════════ 15. ÇALIŞMA ALANI & ODAKLI OKUYUCU (WORKSPACE) ═══════════════ */
.workspace-reader {
  background: var(--paper);
}

.workspace-header {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
}

.btn-workspace-back {
  background: var(--paper);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  color: var(--ink);
  font-family: var(--font-ui);
  font-size: var(--fs-sm);
  font-weight: 600;
  transition: all var(--transition-fast) ease;
}

.btn-workspace-back:hover {
  background: var(--paper-dark);
  border-color: var(--ink);
  transform: translateX(-2px);
}

.workspace-book-title {
  font-family: var(--font-display), 'Newsreader', Georgia, serif;
  font-size: 1.25rem;
  color: var(--ink);
}

.btn-toggle-workspace-chat,
.btn-workspace-action {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.85rem;
  font-size: var(--fs-xs);
  font-weight: 600;
  font-family: var(--font-ui);
  background: var(--paper);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: all var(--transition-fast) ease;
  box-shadow: var(--shadow-sm);
  white-space: nowrap;
}

.btn-toggle-workspace-chat:hover,
.btn-workspace-action:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--paper-dark);
}

.btn-toggle-workspace-chat.active,
.btn-workspace-action.active {
  background: var(--paper-dark);
  border-color: var(--accent);
  color: var(--accent);
}

.workspace-chat-pane {
  flex: 0 0 380px;
  width: 380px;
  background: var(--surface);
  border-left: 1px solid var(--line);
  transition: width var(--t-ui) var(--ease-out), min-width var(--t-ui) var(--ease-out), opacity var(--t-ui) var(--ease-out);
}

.workspace-chat-pane.collapsed {
  width: 0;
  min-width: 0;
  max-width: 0;
  opacity: 0;
  pointer-events: none;
  overflow: hidden;
  border-left: none;
}

.pdf-toolbar {
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}

.pdf-toc-item {
  width: 100%;
  background: transparent;
  border: 1px solid transparent;
  text-align: left;
  font-family: inherit;
}

.pdf-btn {
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--r-xs);
  color: var(--muted);
  transition: all var(--transition-fast) ease;
}

.pdf-btn:hover {
  background: var(--paper-dark);
  color: var(--ink);
  border-color: var(--line);
}

.pdf-btn.active,
.pdf-btn.toggle-btn.active {
  background: var(--paper-dark);
  color: var(--accent);
  border-color: var(--line-strong);
}

/* ═══════════════ 16. RESPONSIVE DÜZENLEMELER & MOBİL ERGONOMİ (F1) ═══════════════ */
/* Safe area insets for mobile edge-to-edge screens */
.container,
#library-view {
  padding-bottom: max(var(--sp-12), calc(var(--sp-8) + env(safe-area-inset-bottom)));
}

@media (pointer: coarse), (hover: none) {
  /* Expand tap hit area to at least 44x44px for compact controls */
  .theme-toggle-btn,
  .header-icon-btn,
  .btn-favorite-card,
  .view-btn,
  .modal-close,
  .btn-modal-close,
  .ops-btn-icon,
  .shelf-nav-btn,
  .pdf-btn,
  .hl-color-btn,
  .hl-action-btn,
  .btn-compact-action,
  .compact-theme-btn,
  .prompt-chip {
    position: relative;
    min-width: 36px;
    min-height: 36px;
  }

  .theme-toggle-btn::before,
  .header-icon-btn::before,
  .btn-favorite-card::before,
  .view-btn::before,
  .modal-close::before,
  .btn-modal-close::before,
  .ops-btn-icon::before,
  .shelf-nav-btn::before,
  .pdf-btn::before,
  .hl-color-btn::before,
  .hl-action-btn::before,
  .btn-compact-action::before,
  .compact-theme-btn::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    min-width: 44px;
    min-height: 44px;
    width: 100%;
    height: 100%;
    pointer-events: auto;
  }

  /* Book cards: category badge and favorite heart always visible on touch */
  .book-card .card-cat-badge,
  .book-card .btn-favorite-card {
    opacity: 1;
    transform: none;
    visibility: visible;
    pointer-events: auto;
  }
}

@media (max-width: 768px) {
  .hero-features-strip {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  .zero-state-hero {
    padding: var(--sp-4) 0;
    margin: 0;
  }
  .hero-title {
    font-size: clamp(2.5rem, 12vw, 3.8rem);
  }
  .header-actions .btn-primary-action span {
    display: none !important;
  }
  .header-actions .btn-primary-action {
    padding: 0.45rem 0.65rem;
  }
  .compact-actions .btn-primary-action span {
    display: none !important;
  }

  /* Mobile Floating Action Pills: Sitting in their respective corners with safe area */
  #chat-panel:not(.active) {
    left: auto;
    right: 1rem;
    bottom: max(1rem, env(safe-area-inset-bottom));
    width: auto;
    max-width: fit-content;
  }

  #ops-toggle {
    left: 1rem;
    right: auto;
    bottom: max(1rem, env(safe-area-inset-bottom));
    width: auto;
  }

  #scroll-top-btn {
    bottom: max(4.5rem, calc(4rem + env(safe-area-inset-bottom)));
  }

  .modal-box,
  .modal-content {
    padding-bottom: max(var(--sp-4), env(safe-area-inset-bottom));
  }

  /* Reader Workspace Mobile Bottom Sheet */
  .workspace-content {
    position: relative;
    overflow: hidden;
  }

  .workspace-pdf-pane {
    flex: 1 1 100%;
    width: 100%;
    min-width: 100%;
    height: 100%;
  }

  .workspace-resize-handle {
    display: none;
  }

  .workspace-chat-pane {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    height: 72vh;
    max-height: 80vh;
    border-radius: var(--r-lg) var(--r-lg) 0 0;
    border-left: none;
    border-top: 1px solid var(--line);
    box-shadow: 0 -8px 30px var(--shadow-color);
    z-index: 5020;
    transform: translateY(0);
    transition: transform var(--t-ui) var(--ease-spring), opacity var(--t-ui) var(--ease-out);
  }

  .workspace-chat-pane.collapsed {
    transform: translateY(100%);
    opacity: 0;
    pointer-events: none;
    width: 100%;
    min-width: 100%;
    max-width: 100%;
  }

  .workspace-chat-header {
    flex-direction: column;
    align-items: center;
    padding: var(--sp-2) var(--sp-4);
    touch-action: pan-y;
    cursor: grab;
  }

  .workspace-chat-header::before {
    content: '';
    display: block;
    width: 38px;
    height: 4px;
    border-radius: var(--r-full);
    background: var(--muted-light);
    margin-bottom: var(--sp-2);
  }

  .workspace-chat-input-area {
    padding-bottom: max(var(--sp-3), env(safe-area-inset-bottom));
  }
}



/* ═══════════════ 17. ERİŞİLEBİLİRLİK (REDUCED MOTION) ═══════════════ */
@media (prefers-reduced-motion: reduce) {
  /* Hareketi sıfırla, yumuşak geçişi (opacity, color) koru */
  *, *::before, *::after {
    scroll-behavior: auto !important;
  }

  /* Sonsuz dönen, yanıp sönen ve nabız gibi atan döngüleri durdur */
  .fa-spin,
  .ops-status-dot,
  .is-processing .ops-status-dot,
  [class*="pulse"],
  [class*="spin"],
  [class*="shimmer"],
  [class*="radar"] {
    animation: none !important;
  }

  /* Butonlar, kartlar ve interaktif elemanlarda zıplamayı ve büyümeyi durdur */
  button,
  [class*="btn-"],
  .book-card,
  .card-cover img,
  .card-cover-placeholder,
  .header-icon-btn,
  .ops-toggle,
  #chat-panel,
  #ops-center,
  .dropdown-menu,
  .modal-close,
  .shelf-item {
    transform: none !important;
    transition-property: opacity, background-color, border-color, color !important;
  }

  /* Modallar: Transform kalkar, sadece sakin ve zarif opacity geçişi (150ms) */
  @keyframes modalPopIn {
    from { opacity: 0; transform: none; }
    to { opacity: 1; transform: none; }
  }

  @keyframes modalPopOut {
    from { opacity: 1; transform: none; }
    to { opacity: 0; transform: none; }
  }

  @keyframes modalOverlayIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes modalOverlayOut {
    from { opacity: 1; }
    to { opacity: 0; }
  }

  /* Dropdown & Ops Panel: Transformsuz, sadece opacity */
  @keyframes dropdownIn {
    from { opacity: 0; transform: none; }
    to { opacity: 1; transform: none; }
  }

  @keyframes toolsMenuFadeIn {
    from { opacity: 0; transform: none; }
    to { opacity: 1; transform: none; }
  }

  @keyframes toolsMenuFadeOut {
    from { opacity: 1; transform: none; }
    to { opacity: 0; transform: none; }
  }

  @keyframes opsCenterIn {
    from { opacity: 0; transform: none; }
    to { opacity: 1; transform: none; }
  }

  @keyframes chatPanelExpand {
    from { opacity: 0; transform: none; }
    to { opacity: 1; transform: none; }
  }

  @keyframes chatPanelCollapse {
    from { opacity: 1; transform: none; }
    to { opacity: 0; transform: none; }
  }

  /* Kartlarda stagger zıplamasını durdur, sadece hızlı sakin beliriş */
  .book-card.stagger-in,
  #table-body tr.stagger-in {
    animation: none !important;
  }
}

/* ═══════════════ READER SURFACE MODES (GPU HARDWARE ACCELERATED) ═══════════════ */
#custom-pdf-viewer[data-surface-mode="sepia"] canvas,
#custom-pdf-viewer[data-surface-mode="sepia"] .pdf-page-canvas,
[data-surface="sepia"] .pdf-page-canvas,
[data-surface="sepia"] .epub-content {
  filter: sepia(0.35) contrast(0.95) brightness(0.98);
  transition: filter var(--t-ui) var(--ease-out);
}

#custom-pdf-viewer[data-surface-mode="eink"] canvas,
#custom-pdf-viewer[data-surface-mode="eink"] .pdf-page-canvas,
[data-surface="eink"] .pdf-page-canvas,
[data-surface="eink"] .epub-content {
  filter: grayscale(1) contrast(1.1);
  transition: filter var(--t-ui) var(--ease-out);
}

#custom-pdf-viewer[data-surface-mode="normal"] canvas,
#custom-pdf-viewer[data-surface-mode="normal"] .pdf-page-canvas {
  filter: none;
  transition: filter var(--t-ui) var(--ease-out);
}

/* ═══════════════ READER DOUBLE-BUFFERED ZOOM (GPU TRANSITION) ═══════════════ */
#pdf-canvas-container.is-zooming .pdf-page-canvas,
#pdf-canvas-container.is-zooming .pdf-page-wrapper {
  will-change: transform;
}

/* ═══════════════ D1: SHARED ELEMENT MORPH (CARD <-> WORKSPACE) ═══════════════ */
::view-transition-group(book-cover) {
  animation-duration: var(--t-page);
  animation-timing-function: var(--ease-spring);
}

.workspace-cover-slot {
  width: 28px;
  height: 38px;
  border-radius: var(--r-sm);
  overflow: hidden;
  background: var(--paper-dark);
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  margin-left: var(--sp-2);
}

.workspace-cover-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ═══════════════ D2: SKELETON READER LOADER ═══════════════ */
.reader-skeleton-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--sp-6);
  padding: var(--sp-8) var(--sp-4);
  max-width: 680px;
  margin: 0 auto;
  min-height: 70vh;
}

.reader-skeleton-cover-preview {
  width: 140px;
  height: 196px;
  border-radius: var(--r-md);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--line);
  background: var(--paper-dark);
}

.reader-skeleton-cover-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.reader-skeleton-page {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  padding: var(--sp-8);
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  box-shadow: var(--shadow-sm);
}

.reader-skeleton-line {
  height: 14px;
  background: var(--paper-dark);
  border-radius: var(--r-sm);
  position: relative;
  overflow: hidden;
}

.reader-skeleton-line.title {
  height: 24px;
  width: 60%;
  margin-bottom: var(--sp-2);
}

.reader-skeleton-line.short {
  width: 40%;
  margin-bottom: var(--sp-3);
}

.reader-skeleton-line.medium {
  width: 75%;
}

.reader-skeleton-line::after {
  content: "";
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
  animation: skeletonPulse 1.8s var(--ease-out) infinite;
}

[data-theme="light"] .reader-skeleton-line::after {
  background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.04), transparent);
}

@keyframes skeletonPulse {
  100% {
    transform: translateX(100%);
  }
}

/* ═══════════════ D3: SMOOTH COVER LOADING & CALM SHIMMER ═══════════════ */
.card-cover {
  position: relative;
  background: var(--paper-dark);
  aspect-ratio: 3 / 4;
  overflow: hidden;
}

.card-cover img,
.shelf-item-cover img,
.modal-cover-wrap img {
  opacity: 0;
  transition: opacity var(--t-ui) var(--ease-out);
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-cover img.loaded,
.card-cover img[complete],
.shelf-item-cover img.loaded,
.modal-cover-wrap img.loaded {
  opacity: 1;
}

.skeleton-shimmer {
  background: linear-gradient(90deg, var(--paper-dark) 20%, rgba(255, 255, 255, 0.05) 50%, var(--paper-dark) 80%);
  background-size: 200% 100%;
  animation: calmShimmer 2.2s var(--ease-out) infinite;
}

[data-theme="light"] .skeleton-shimmer {
  background: linear-gradient(90deg, var(--paper-dark) 20%, rgba(0, 0, 0, 0.03) 50%, var(--paper-dark) 80%);
  background-size: 200% 100%;
  animation: calmShimmer 2.2s var(--ease-out) infinite;
}

@keyframes calmShimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ═══════════════ D4: CARD READING PROGRESS BAR ═══════════════ */
.card-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: var(--accent);
  z-index: 10;
  transition: width var(--t-ui) var(--ease-out);
}

.card-progress-badge {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--accent);
  background: var(--accent-glow);
  padding: 1px 5px;
  border-radius: var(--r-full);
  margin-left: auto;
}

.modal-progress-wrap {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
  margin-bottom: var(--sp-3);
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--muted);
}

.modal-progress-track {
  flex: 1;
  height: 4px;
  background: var(--paper-dark);
  border-radius: var(--r-full);
  overflow: hidden;
  border: 1px solid var(--line);
}

.modal-progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: var(--r-full);
}

/* ═══════════════ D6: IN-APP CONFIRMATION DIALOG & EMPTY STATES ═══════════════ */
.app-confirm-dialog {
  max-width: 420px !important;
  width: 90% !important;
  padding: var(--sp-6) var(--sp-6) !important;
  background: var(--surface) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: var(--shadow-xl) !important;
}

.confirm-dialog-title {
  font-family: var(--font-title);
  font-size: 1.6rem;
  font-weight: 400;
  color: var(--ink);
  margin-bottom: var(--sp-2);
}

.confirm-dialog-msg {
  font-family: var(--font-sans);
  font-size: 0.9rem;
  line-height: 1.55;
  color: var(--muted);
  white-space: pre-line;
  margin-bottom: var(--sp-6);
}

.confirm-dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-3);
}

.confirm-dialog-actions button {
  min-width: 90px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--sp-12) var(--sp-6);
  max-width: 540px;
  margin: var(--sp-8) auto;
}

#empty-state-title {
  font-family: var(--font-title);
  font-size: 2.2rem;
  font-weight: 400;
  line-height: 1.15;
  color: var(--ink);
  margin-bottom: var(--sp-2);
}

#empty-state-desc {
  font-family: var(--font-sans);
  font-size: 0.95rem;
  color: var(--muted);
  line-height: 1.55;
  max-width: 44ch;
  margin-bottom: var(--sp-6);
}

.empty-state-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--sp-3);
}
```


## DOSYA 3: templates/kutuphane.html (Ana Kütüphane, Editoryal Hero, Dialog Rolleri & Okuyucu Şablonu)

**Dosya Yolu:** `templates/kutuphane.html`

```html
<!DOCTYPE html>
<html lang="tr">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#f4f1eb" id="theme-color-meta">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="default">
  <title>Kütüphanem</title>
  <script>
    (function () {
      try {
        var t = localStorage.getItem('kutuphane-theme') || localStorage.getItem('theme');
        if (!t) {
          t = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        document.documentElement.setAttribute('data-theme', t);
        var meta = document.getElementById('theme-color-meta');
        if (meta) meta.setAttribute('content', t === 'dark' ? '#161513' : '#f4f1eb');
      } catch (e) {}
    })();
  </script>
  <link rel="icon" type="image/svg+xml" href="{{ url_for('static', path='/favicon.svg') }}">
  <link rel="manifest" href="{{ url_for('static', path='/manifest.json') }}">
  <link rel="apple-touch-icon" href="{{ url_for('static', path='/favicon.svg') }}">
  <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js').catch(function(err) {
          console.debug('PWA ServiceWorker note:', err);
        });
      });
    }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap"
    rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js" integrity="sha512-r22gChDnGvBylk90+2e/ycr3RVrDi8DIOkIGNhJlKfuyQM4tIRAI062MaV8sfjQKYVGjOBaZBOA87z+IhZE9DA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" integrity="sha512-Avb2QiuDEEvB4bZJYdft2mNjVShBftLdPG8FJ0V7irTLQ8Uo0qcPxh4Plq7G5tGm0rU+1SPhVotteLpBERwTkw==" crossorigin="anonymous" referrerpolicy="no-referrer">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js" integrity="sha512-q+4liFwdPC/bNdhUpZx6aXDx/h77yEQtn4I1slHydcbZK34nLaR3cAeYSJshoxIOq3mjEf7xJE8YWIUHMn+oCQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.0/marked.min.js" integrity="sha512-tjg8I2d6Fi0OBGz1csmr7RfI4uupYaCfL/RqhVRTS42RMGwfBsjwBGmhzhI+e2dPmyew8cFkoxnVkGvADDLvbg==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.9/purify.min.js" integrity="sha512-9+ilAOeXY8qy2bw/h51MmliNNHvdyhTpLIlqDmVpD26z8VjVJsUJtk5rhbDIUvYiD+EpGoAu0xTa7MhZohFQjA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
  <script>
    if (window.pdfjsLib) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    }
  </script>
  <link rel="stylesheet" href="{{ url_for('static', path='/css/app.css') }}?v=2026110805">
</head>

<body>
  <div id="drop-overlay" class="drop-overlay">
    <div class="drop-box">
      <h3>Belgeleri sürükleyip bırak</h3>
      <p>İlk sayfayı önizle, yapay zekâ özetini hazırlarken yükleme çubuğunu izle.</p>
      <div class="pill"><i class="fas fa-file-alt"></i> PDF, EPUB, TXT desteklenir</div>
    </div>
  </div>

  <header>
    <div class="header-inner">
      <div class="brand">
        <div class="brand-label">Dijital Koleksiyon</div>
        <div class="brand-title-row">
          <h1><em>Kütüphanem</em></h1>
          <div class="stat-pill" id="header-stat-pill" title="Kütüphanedeki Toplam Eser">
            <i class="fas fa-book" style="margin-right: 5px; color: var(--accent);"></i>
            <span id="stat-total" style="font-weight: 600;">—</span> <span style="margin-left: 3px;">Eser</span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <!-- Primary Action: + Kitap Ekle (Visible when library has items) -->
        <button type="button" class="btn btn--primary btn--sm btn-primary-action" id="header-add-book-btn" style="display:none;" onclick="document.getElementById('file-input').click()" title="Yeni Kitap Ekle (PDF, EPUB, TXT)">
          <i class="fas fa-plus"></i>
          <span>Kitap Ekle</span>
        </button>

        <div class="header-action-divider"></div>

        <!-- Quick Theme Toggle -->
        <button type="button" class="header-icon-btn" id="theme-toggle" onclick="toggleTheme()" title="Aydınlık / Karanlık Mod (d)" aria-label="Aydınlık veya Karanlık Mod">
          <i class="fas fa-moon"></i>
        </button>

        <!-- Tools Dropdown (Organized Utilities: Logs, Telegram, Sync, Duplicates, Shortcuts, PWA) -->
        <div class="header-tools-wrapper" id="header-tools-wrapper">
          <button type="button" class="header-icon-btn" id="header-tools-btn" aria-haspopup="menu" aria-expanded="false" onclick="toggleToolsMenu(event)" title="Araçlar &amp; Sistem Menüsü" aria-label="Araçlar ve Sistem Menüsü">
            <i class="fas fa-sliders-h"></i>
            <span class="header-logs-badge" id="header-logs-badge" style="display:none;"></span>
          </button>
          <div class="header-tools-menu" id="header-tools-menu" role="menu" aria-label="Araçlar ve Sistem Menüsü" style="display:none;">
            <div class="tools-menu-label">Araçlar &amp; Sistem</div>
            <button type="button" class="tools-menu-item" id="header-logs-btn" onclick="openLogsModal(); closeToolsMenu();">
              <i class="fas fa-terminal"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Canlı İşlem Logları</span>
                <span class="tools-item-desc">Arka plan görevleri ve sistem akışı</span>
              </div>
            </button>
            <button type="button" class="tools-menu-item" id="header-telegram-btn" onclick="openTelegramModal(); closeToolsMenu();">
              <i class="fab fa-telegram-plane"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Telegram'dan Aktar</span>
                <span class="tools-item-desc">Kanal veya bot üzerinden kitap çek</span>
              </div>
            </button>
            <button type="button" class="tools-menu-item" onclick="syncLibrary(); closeToolsMenu();">
              <i class="fas fa-sync-alt"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Kütüphaneyi Eşitle</span>
                <span class="tools-item-desc">Klasördeki yeni belgeleri tara</span>
              </div>
            </button>
            <button type="button" class="tools-menu-item" onclick="openDuplicatesModal(); closeToolsMenu();">
              <i class="fas fa-copy"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Çift Kitap Avcısı</span>
                <span class="tools-item-desc">Mükerrer dosyaları tespit et</span>
              </div>
            </button>
            <button type="button" class="tools-menu-item" id="header-shortcuts-btn" onclick="openShortcutsModal(); closeToolsMenu();">
              <i class="fas fa-keyboard"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Klavye Kısayolları</span>
                <span class="tools-item-desc">Hızlı erişim kombinasyonları (?)</span>
              </div>
            </button>
            <button type="button" class="tools-menu-item" id="btn-pwa-install" onclick="triggerPwaInstall(); closeToolsMenu();" style="display:none;">
              <i class="fas fa-download"></i>
              <div class="tools-item-content">
                <span class="tools-item-title">Uygulamayı Yükle</span>
                <span class="tools-item-desc">Masaüstü/Mobil PWA</span>
              </div>
            </button>
          </div>
        </div>

        <!-- Settings Cog -->
        <button type="button" class="header-icon-btn" id="settings-btn" onclick="openSettings()" title="Ayarlar" aria-label="Ayarlar">
          <i class="fas fa-cog"></i>
        </button>
      </div>
    </div>
  </header>

  <div class="compact-nav" id="compact-nav">
    <div class="compact-brand">
      <span class="compact-brand-sub">Dijital Koleksiyon</span>
      <span class="compact-brand-title"><em>Kütüphanem</em></span>
    </div>
    <div class="compact-actions">
      <div class="stat-pill" style="font-size:0.75rem;">
        <i class="fas fa-book" style="margin-right:5px; color:var(--accent);"></i>
        <span class="stat-total-val">—</span>
      </div>
      <button type="button" class="btn btn--primary btn--sm btn-primary-action compact" id="compact-add-book-btn" style="display:none;" onclick="document.getElementById('file-input').click()" title="Yeni Kitap Ekle">
        <i class="fas fa-plus"></i>
        <span>Kitap Ekle</span>
      </button>
      <button type="button" class="header-icon-btn compact-icon" id="compact-theme-btn" onclick="toggleTheme()" title="Aydınlık / Karanlık Mod" aria-label="Aydınlık veya Karanlık Mod">
        <i class="fas fa-moon"></i>
      </button>
      <button type="button" class="header-icon-btn compact-icon" id="compact-logs-btn" onclick="openLogsModal()" title="İşlem Logları" aria-label="İşlem Logları" style="position:relative;">
        <i class="fas fa-terminal"></i>
        <span class="header-logs-badge compact-logs-badge" id="compact-logs-badge" style="display:none;"></span>
      </button>
      <button type="button" class="header-icon-btn compact-icon" id="compact-pwa-install" onclick="triggerPwaInstall()" title="Masaüstü/Mobil Uygulama Olarak Yükle" aria-label="Uygulamayı Yükle" style="display:none;">
        <i class="fas fa-download"></i>
      </button>
      <button type="button" class="header-icon-btn compact-icon" onclick="openSettings()" title="Ayarlar" aria-label="Kütüphane Ayarları">
        <i class="fas fa-cog"></i>
      </button>
    </div>
  </div>

  <div class="controls-panel" style="display:none;">
    <div class="search-wrap" style="position:relative; display:flex; align-items:center;">
      <i class="fas fa-search"></i>
      <input type="search" id="search-input" placeholder="Kitap, yazar, konu ara… (Kısayol: /)" aria-label="Kitap, yazar veya konu ara">
      <button type="button" id="btn-deep-search-toggle" class="btn-deep-search-toggle" onclick="toggleDeepSearchMode()" title="Global Derin Arama: Tüm kitapların sayfalarında ara">
        <i class="fas fa-layer-group"></i> <span id="deep-search-label">Derin Arama</span>
      </button>
    </div>

    <div class="control-group dropdowns-group">
      <div class="custom-dropdown" id="dropdown-category">
        <button type="button" class="dropdown-trigger" id="category-trigger" aria-haspopup="listbox" aria-expanded="false" onclick="toggleDropdown('dropdown-category')">Tüm Kategoriler</button>
        <div class="dropdown-menu" id="category-menu" role="listbox" aria-label="Kategori seçin"></div>
      </div>

      <div class="custom-dropdown" id="dropdown-collection">
        <button type="button" class="dropdown-trigger" id="collection-trigger" aria-haspopup="listbox" aria-expanded="false" onclick="toggleDropdown('dropdown-collection')">Tüm Koleksiyonlar</button>
        <div class="dropdown-menu" id="collection-menu" role="listbox" aria-label="Koleksiyon seçin"></div>
      </div>
    </div>

    <div class="view-toggle">
      <button type="button" class="view-btn active" id="btn-grid" onclick="setView('grid')" title="Kart Görünümü (g)">
        <i class="fas fa-th-large"></i> <span class="btn-label">Kart</span>
      </button>
      <button type="button" class="view-btn" id="btn-table" onclick="setView('table')" title="Liste Görünümü (t)">
        <i class="fas fa-list"></i> <span class="btn-label">Liste</span>
      </button>
      <button type="button" class="view-btn" id="btn-stats" onclick="setView('stats')" title="İstatistikler (s)">
        <i class="fas fa-chart-pie"></i> <span class="btn-label">İstatistik</span>
      </button>
    </div>

    <div class="control-group actions-group">
      <button type="button" class="view-btn" id="btn-fav-filter" onclick="toggleFavFilter()" title="Favorilerim (f)">
        <i class="fas fa-heart"></i> <span class="btn-label">Favoriler</span>
      </button>
      <div class="manage-sep"></div>
      <button type="button" class="view-btn" id="btn-manage" onclick="toggleSelectionMode()" title="Toplu Yönetim (m)">
        <i class="fas fa-tasks"></i> <span class="btn-label">Yönet</span>
      </button>
    </div>
  </div>

  <div class="import-zone" id="import-zone">
    <div class="zero-state-hero" id="drop-box">
      <div class="hero-kicker">KİŞİSEL ARŞİV &amp; OKUMA ALANI</div>
      <h2 class="hero-title">Kişisel dijital <em>arşiviniz</em>.</h2>
      <p class="hero-subtitle">PDF, EPUB ve TXT belgelerinizi bu alana sürükleyip bırakın ya da cihazınızdan seçin.</p>
      
      <div class="hero-primary-actions">
        <button type="button" class="btn btn--primary btn--lg btn-hero-primary" onclick="document.getElementById('file-input').click()">
          <i class="fas fa-plus"></i>
          <span>Kitap Dosyası Seç</span>
        </button>
      </div>

      <div class="hero-secondary-links">
        <button type="button" class="hero-text-link" id="btn-telegram" onclick="openTelegramModal()">Telegram'dan aktar</button>
        <span class="hero-link-sep" aria-hidden="true">·</span>
        <button type="button" class="hero-text-link" id="btn-sync" onclick="syncLibrary()">
          <i class="fas fa-sync-alt" id="sync-icon" style="font-size:0.75em; margin-right:4px;"></i>Klasörü eşitle
        </button>
      </div>

      <input type="file" id="file-input" accept=".pdf,.epub,.txt" multiple onchange="handleFiles(this.files)" aria-label="Kütüphaneye eklenecek PDF veya EPUB dosyaları">
    </div>
  </div>

  <main id="main-content" style="display:none">
    <div class="result-info" id="result-info">— kitap gösteriliyor</div>
    <div id="empty-state" class="empty-state" style="display: none;">
      <div class="empty-state-card">
        <div class="empty-state-icon">
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            <path d="M12 6v6"></path>
            <path d="M12 16h.01"></path>
          </svg>
        </div>
        <h3 id="empty-state-title">Kitap Bulunamadı</h3>
        <p id="empty-state-desc">Arama veya filtre kriterlerinize uygun kitap bulunamadı.</p>
        <div class="empty-state-actions">
          <button class="btn-empty-clear" id="btn-empty-clear" onclick="clearFiltersAndSearch()">
            <i class="fas fa-times-circle"></i> Filtreleri Temizle
          </button>
          <button class="btn-empty-add" onclick="document.getElementById('file-input').click()">
            <i class="fas fa-plus"></i> Yeni Kitap Yükle
          </button>
        </div>
      </div>
    </div>
    <div id="deep-search-results" style="display:none; padding:1.2rem; background:transparent; border:1px solid var(--line); border-radius:14px; margin-bottom:1.5rem;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; border-bottom:1px solid var(--line); padding-bottom:0.75rem;">
        <h3 style="font-size:1.05rem; color:var(--ink); margin:0; display:flex; align-items:center; gap:0.5rem;">
          <i class="fas fa-search-location" style="color:var(--accent);"></i>
          <span>Sayfa Düzeyinde Eşleşmeler</span>
          <span class="badge" id="deep-search-count" style="font-size:0.75rem; background:var(--accent-glow); color:var(--accent); padding:2px 8px; border-radius:12px;">0 sonuç</span>
        </h3>
        <button class="btn-empty-clear" onclick="closeDeepSearch()" style="padding:0.35rem 0.75rem; font-size:0.8rem; cursor:pointer;"><i class="fas fa-times"></i> Kapat</button>
      </div>
      <div id="deep-search-list" style="display:flex; flex-direction:column; gap:0.75rem;"></div>
    </div>
    <div id="recent-shelf-container" style="display:none;" class="recent-shelf-container"></div>
    <div id="grid-view"></div>
    <div id="table-view" style="display: none;">
      <table>
        <thead>
          <tr>
            <th style="width:58px;cursor:default"></th>
            <th><button type="button" class="th-sort-btn" onclick="sortTable(0)">Kitap Adı <span class="sort-arrow">↕</span></button></th>
            <th><button type="button" class="th-sort-btn" onclick="sortTable(1)">Yazar <span class="sort-arrow">↕</span></button></th>
            <th><button type="button" class="th-sort-btn" onclick="sortTable(2)">Kategori <span class="sort-arrow">↕</span></button></th>
            <th><button type="button" class="th-sort-btn" onclick="sortTable(3)">Alt Kategori <span class="sort-arrow">↕</span></button></th>
            <th><button type="button" class="th-sort-btn" onclick="sortTable(4)">Açıklama <span class="sort-arrow">↕</span></button></th>
          </tr>
        </thead>
        <tbody id="table-body"></tbody>
      </table>
    </div>

    <div id="stats-view" style="display: none;">
      <div class="stats-grid" id="stats-cards"></div>
      <div class="stats-charts">
        <div class="stats-chart-box">
          <div class="stats-chart-title">Kategori Dağılımı</div>
          <div class="donut-wrap" id="donut-chart"></div>
        </div>
        <div class="stats-chart-box">
          <div class="stats-chart-title">Aylık Eklenen Kitaplar</div>
          <div class="bar-chart" id="bar-chart"></div>
        </div>
      </div>
    </div>
  </main>

  <div class="modal-overlay" id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-book-title" tabindex="-1">
    <div class="modal" id="modal-box">
      <div class="modal-top"></div>
      <button type="button" class="modal-close" onclick="closeModalDirect()" aria-label="Kapat" title="Kapat"><i class="fas fa-times"></i></button>
      <div id="modal-content"><h2 id="modal-book-title" style="display:none;">Kitap Detayı</h2></div>
    </div>
  </div>

  <div id="ops-center">
    <div class="ops-header">
      <div class="ops-title-wrap">
        <span class="ops-live-pulse pulse-idle" id="ops-live-pulse" title="Sistem Canlı Bağlantı Durumu"></span>
        <h3><i class="fas fa-terminal"></i> İşlem merkezi</h3>
        <span class="ops-count-pill" id="ops-active-pill">Hazır</span>
      </div>
      <div class="ops-header-actions">
        <button type="button" class="ops-btn-icon" onclick="fetchTasksFromAPI()" title="Yenile / Güncelle" aria-label="İşlemleri Yenile">
          <i class="fas fa-sync-alt" id="ops-refresh-icon"></i>
        </button>
        <button id="archive-toggle" class="ops-archive-btn" onclick="openLogsModal()" title="Tüm Sistem ve Arka Plan Logları">
          <i class="fas fa-scroll"></i> Loglar
        </button>
        <button type="button" class="ops-btn-close" onclick="toggleOps()" title="Kapat" aria-label="İşlem Merkezini Kapat">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- Filter Tabs (Tümü / Aktif / Tamamlanan) -->
    <div class="ops-tabs">
      <button class="ops-tab-btn active" id="ops-tab-all" onclick="setOpsTab('all')">
        Tümü <span class="ops-tab-badge" id="ops-tab-badge-all">0</span>
      </button>
      <button class="ops-tab-btn" id="ops-tab-active" onclick="setOpsTab('active')">
        Aktif <span class="ops-tab-badge active-tag" id="ops-tab-badge-active">0</span>
      </button>
      <button class="ops-tab-btn" id="ops-tab-completed" onclick="setOpsTab('completed')">
        Tamamlanan <span class="ops-tab-badge" id="ops-tab-badge-completed">0</span>
      </button>
    </div>

    <!-- Live System Banner (Quick heartbeat strip) -->
    <div class="ops-system-strip" id="ops-system-strip">
      <div class="ops-strip-item"><i class="fas fa-brain"></i> <span id="ops-engine-label">Gemini 3.5 Flash-Lite</span></div>
      <div class="ops-strip-item"><i class="fas fa-wifi"></i> <span id="ops-ws-status">Canlı</span></div>
      <div class="ops-strip-item"><i class="fas fa-tasks"></i> <span id="ops-queue-label">0 Sırada</span></div>
    </div>

    <div class="ops-body" id="ops-body">
      <div style="opacity:0.5; text-align:center; padding:2rem;">Yükleniyor...</div>
    </div>
  </div>

  <div class="logs-modal" id="logs-modal" role="dialog" aria-modal="true" aria-labelledby="logs-modal-title" tabindex="-1">
    <div class="logs-panel">
      <!-- Top Bar: Header & Actions -->
      <div class="logs-header">
        <div class="logs-header-left">
          <div class="logs-title-wrap">
            <i class="fas fa-terminal logs-title-icon"></i>
            <h4 id="logs-modal-title">Sistem ve işlem logları</h4>
          </div>
          <div class="logs-status-pill status-online" id="logs-status-indicator" title="WebSocket Canlı Bağlantı Durumu">
            <span class="status-dot"></span>
            <span id="logs-status-text">Canlı</span>
          </div>
        </div>

        <div class="logs-header-actions">
          <button type="button" class="logs-action-btn" id="logs-toggle-pause" onclick="toggleLogPause()" title="Canlı akışı duraklat veya devam ettir">
            <i class="fas fa-pause"></i> <span id="logs-pause-text">Duraklat</span>
          </button>
          <button type="button" class="logs-action-btn" onclick="exportLogs('json')" title="Logları JSON olarak indir">
            <i class="fas fa-file-code"></i> <span>JSON</span>
          </button>
          <button type="button" class="logs-action-btn" onclick="exportLogs('log')" title="Logları TXT/LOG olarak indir">
            <i class="fas fa-file-lines"></i> <span>TXT</span>
          </button>
          <button type="button" class="logs-action-btn logs-btn-danger" onclick="clearLogsUI()" title="Ekrandaki ve bellekteki logları temizle">
            <i class="fas fa-trash-alt"></i> <span>Temizle</span>
          </button>
          <button type="button" class="logs-close" onclick="closeLogsModalDirect()" title="Kapat" aria-label="Loglar Panelini Kapat">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Main Layout: Sidebar & Log Viewport -->
      <div class="logs-body">
        <aside class="logs-sidebar">
          <div class="logs-section-title">Kategoriler</div>
          <button type="button" class="logs-filter-btn active" data-cat="all" onclick="setLogCategory('all', this)">
            <span>Tümü</span><small id="logs-count-all">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="upload" onclick="setLogCategory('upload', this)">
            <span>Yükleme &amp; Görev</span><small id="logs-count-upload">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="ai_analyze" onclick="setLogCategory('ai_analyze', this)">
            <span>AI Analiz</span><small id="logs-count-ai_analyze">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="ai_raw" onclick="setLogCategory('ai_raw', this)">
            <span>AI Ham Yanıt</span><small id="logs-count-ai_raw">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="ai_chat" onclick="setLogCategory('ai_chat', this)">
            <span>AI Sohbet</span><small id="logs-count-ai_chat">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="pdf" onclick="setLogCategory('pdf', this)">
            <span>PDF &amp; OCR</span><small id="logs-count-pdf">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="filesystem" onclick="setLogCategory('filesystem', this)">
            <span>Dosya &amp; Arşiv</span><small id="logs-count-filesystem">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="security" onclick="setLogCategory('security', this)">
            <span>Güvenlik &amp; Erişim</span><small id="logs-count-security">0</small>
          </button>
          <button type="button" class="logs-filter-btn" data-cat="system" onclick="setLogCategory('system', this)">
            <span>Sistem</span><small id="logs-count-system">0</small>
          </button>
        </aside>

        <section class="logs-content-area">
          <!-- Toolbar: Search Bar + Level Pills -->
          <div class="logs-toolbar">
            <div class="logs-search-wrap">
              <i class="fas fa-search logs-search-icon"></i>
              <input type="text" id="logs-search-input" placeholder="Loglarda ara (mesaj, dosya, hata kodu, ip...)" aria-label="Loglarda ara" oninput="handleLogSearchInput(this.value)">
              <button type="button" id="logs-search-clear" onclick="clearLogSearch()" style="display:none;" title="Aramayı temizle" aria-label="Aramayı Temizle"><i class="fas fa-times"></i></button>
            </div>
            <div class="logs-level-filters">
              <button class="logs-level-btn active" data-lvl="all" onclick="setLogLevel('all', this)">Tümü</button>
              <button class="logs-level-btn lvl-error" data-lvl="ERROR" onclick="setLogLevel('ERROR', this)">
                <span class="lvl-indicator"></span> Hata <small id="logs-lvl-count-error">0</small>
              </button>
              <button class="logs-level-btn lvl-warning" data-lvl="WARNING" onclick="setLogLevel('WARNING', this)">
                <span class="lvl-indicator"></span> Uyarı <small id="logs-lvl-count-warning">0</small>
              </button>
              <button class="logs-level-btn lvl-info" data-lvl="INFO" onclick="setLogLevel('INFO', this)">
                <span class="lvl-indicator"></span> Bilgi <small id="logs-lvl-count-info">0</small>
              </button>
              <button class="logs-level-btn lvl-debug" data-lvl="DEBUG" onclick="setLogLevel('DEBUG', this)">
                <span class="lvl-indicator"></span> Debug
              </button>
            </div>
          </div>

          <!-- Logs Feed Body -->
          <div class="logs-main" id="logs-body">
            <div class="logs-loading-state"><i class="fas fa-spinner fa-spin"></i> Loglar yükleniyor...</div>
          </div>

          <!-- Bottom Footer Bar -->
          <div class="logs-footer">
            <div class="logs-footer-left">
              <label class="logs-autoscroll-toggle" title="Yeni log geldiğinde otomatik olarak en son satıra kaydır">
                <input type="checkbox" id="logs-autoscroll-check" checked onchange="toggleAutoScroll(this.checked)" aria-label="Otomatik Kaydırma">
                <span class="custom-toggle-slider"></span>
                <span>Otomatik Kaydırma</span>
              </label>
              <span id="logs-paused-banner" class="logs-paused-banner" style="display:none;">
                <i class="fas fa-pause-circle"></i> Canlı Akış Duraklatıldı
              </span>
            </div>
            <div class="logs-footer-right">
              <span id="logs-counter-info" class="logs-counter-info">0 log</span>
              <button type="button" class="logs-nav-btn" onclick="scrollLogsToTop()" title="En Başa Git" aria-label="En Başa Git"><i class="fas fa-arrow-up"></i></button>
              <button type="button" class="logs-nav-btn" onclick="scrollLogsToBottom()" title="En Sona Git" aria-label="En Sona Git"><i class="fas fa-arrow-down"></i></button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>

  <div id="chat-panel">
    <button type="button" class="chat-header" onclick="toggleAssistant()">
      <div class="chat-header-title">
        <span class="chat-ai-dot"><i class="fas fa-wand-magic-sparkles"></i></span>
        <h3>Kütüphane Asistanı</h3>
      </div>
      <span class="chat-chevron"><i class="fas fa-chevron-up"></i></span>
    </button>
    <div class="chat-body" id="chat-body">
      <div class="chat-msg chat-ai">Merhaba! Kütüphanendeki kitaplar hakkında sana nasıl yardımcı olabilirim?</div>
    </div>
    <div class="chat-input-area">
      <input type="text" id="chat-input" placeholder="Bir şey sor..." aria-label="Asistana soru sor" maxlength="1000"
        onkeydown="if(event.key==='Enter') sendMessage()">
      <div class="chat-counter-wrap">
        <svg class="chat-progress-svg">
          <circle class="chat-progress-bg" cx="12" cy="12" r="10"></circle>
          <circle id="chat-progress-fill" class="chat-progress-fill" cx="12" cy="12" r="10"></circle>
        </svg>
        <span id="chat-char-count">1000</span>
      </div>
      <button type="button" class="btn-send" onclick="sendMessage()" aria-label="Mesaj Gönder"><i class="fas fa-paper-plane"></i></button>
    </div>
  </div>

  <button type="button" class="ops-toggle" id="ops-toggle" onclick="toggleOps()" title="Canlı İşlem Merkezi ve Görev Kuyruğu">
    <span class="ops-status-dot"></span>
    <span class="ops-label">İşlem Merkezi</span>
    <span class="ops-badge" id="ops-badge">0</span>
  </button>

  <button type="button" id="scroll-top-btn" onclick="window.scrollTo({top: 0, behavior: 'smooth'})" title="Yukarı Çık" aria-label="Yukarı Çık">
    <i class="fas fa-chevron-up"></i>
  </button>

  <!-- Modern Workspace Reader Overlay (Split-Pane PDF Reader + Chat) -->
  <div id="workspace-reader" class="workspace-reader">
    <header class="workspace-header">
      <div class="workspace-header-left">
        <button type="button" class="btn-workspace-back" onclick="closeWorkspace()">
          <i class="fas fa-arrow-left"></i> Kütüphaneye Dön
        </button>
        <div id="workspace-cover-slot" class="workspace-cover-slot" aria-hidden="true"></div>
        <span class="workspace-book-divider">|</span>
        <div class="workspace-book-meta">
          <span id="workspace-book-cat" class="workspace-book-cat">—</span>
          <h2 id="workspace-book-title" class="workspace-book-title">—</h2>
        </div>
      </div>
      <div class="workspace-header-right" style="display: flex; align-items: center; gap: 1rem;">
        <!-- Compact Workspace Book Loading Banner -->
        <button type="button" class="workspace-book-banner" id="workspace-book-banner" onclick="loadFullBookToAI()" title="Kitabı AI hafızasına yükle">
          <span class="banner-icon" id="banner-icon"><i class="fas fa-book-open"></i></span>
          <span class="banner-content">
            <span class="banner-title" id="banner-title">AI Hafızasına Yükle</span>
            <span class="banner-subtitle" id="banner-subtitle" style="display:none;"></span>
          </span>
          <span class="btn-banner-load" id="btn-banner-load" style="display:none;"></span>
        </button>

        <!-- Workspace PKM Export Dropdown -->
        <div class="workspace-export-wrapper" style="position:relative;">
          <button type="button" class="btn-workspace-action" id="workspace-export-btn" onclick="toggleWorkspaceExportMenu()" title="Kitap ve Notları Dışa Aktar (Obsidian, Anki, BibTeX)">
            <i class="fas fa-file-export"></i> <span>Dışa Aktar</span>
          </button>
          <div id="workspace-export-menu" class="export-menu" style="display:none; position:absolute; top:120%; right:0; width:180px; background:var(--surface); border:1px solid var(--line); border-radius:var(--r-sm); box-shadow:var(--shadow-md); z-index:1000; overflow:hidden;">
            <button type="button" class="export-menu-item" style="display:flex; width:100%; border:none; background:none; cursor:pointer; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none;" onclick="exportCurrentWorkspaceBook('obsidian')">
              <i class="fas fa-gem" style="color:var(--accent);"></i> Obsidian (.md)
            </button>
            <button type="button" class="export-menu-item" style="display:flex; width:100%; border:none; background:none; cursor:pointer; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; border-top:1px solid var(--line);" onclick="exportCurrentWorkspaceBook('anki')">
              <i class="fas fa-clone" style="color:var(--accent);"></i> Anki Kartları (.tsv)
            </button>
            <button type="button" class="export-menu-item" style="display:flex; width:100%; border:none; background:none; cursor:pointer; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; border-top:1px solid var(--line);" onclick="exportCurrentWorkspaceBook('bibtex')">
              <i class="fas fa-graduation-cap" style="color:var(--accent);"></i> BibTeX (.bib)
            </button>
          </div>
        </div>

        <!-- Toggle AI Chat Pane (Distraction-Free Reading Mode) -->
        <button type="button" class="btn-toggle-workspace-chat" id="btn-toggle-workspace-chat" onclick="toggleWorkspaceChatPane()" title="AI Asistan Panelini Gizle / Göster (Odaklı Okuma)">
          <i class="fas fa-wand-magic-sparkles"></i> <span id="workspace-chat-toggle-label">AI Paneli</span>
        </button>

        <div class="workspace-status-badge" id="workspace-status-badge">
          <i class="fas fa-robot"></i> <span id="workspace-status-text">AI Asistan Bağlı</span>
        </div>
      </div>
    </header>

    <div class="workspace-content">
      <!-- Left Panel: PDF Viewer (Custom PDF.js Interactive Reader) -->
      <div class="workspace-pdf-pane" id="workspace-pdf-pane" style="flex: 1;">
        <div class="custom-pdf-viewer" id="custom-pdf-viewer">
          <!-- Toolbar -->
          <div class="pdf-toolbar">
            <div class="pdf-toolbar-group">
              <button type="button" id="pdf-prev-btn" class="pdf-btn" onclick="pdfPrevPage()" aria-label="Önceki Sayfa"><i class="fas fa-chevron-left"></i></button>
              <span class="pdf-page-indicator">
                Sayfa <input type="number" id="pdf-page-num" value="1" min="1" aria-label="Sayfa numarası" onchange="pdfGoToPageFromInput()"> / <span id="pdf-page-count">-</span>
              </span>
              <button type="button" id="pdf-next-btn" class="pdf-btn" onclick="pdfNextPage()" aria-label="Sonraki Sayfa"><i class="fas fa-chevron-right"></i></button>
            </div>
            <div class="pdf-toolbar-divider"></div>
            <div class="pdf-toolbar-group">
              <button type="button" class="pdf-btn" onclick="pdfZoomOut()" aria-label="Uzaklaştır"><i class="fas fa-search-minus"></i></button>
              <span id="pdf-zoom-percent" class="pdf-zoom-label">100%</span>
              <button type="button" class="pdf-btn" onclick="pdfZoomIn()" aria-label="Yakınlaştır"><i class="fas fa-search-plus"></i></button>
              <button type="button" class="pdf-btn text-btn" id="pdf-fit-width-btn" onclick="pdfFitWidth()"><i class="fas fa-arrows-left-right"></i> Genişliğe Sığdır</button>
              <button type="button" class="pdf-btn text-btn" id="pdf-fit-height-btn" onclick="pdfFitHeight()"><i class="fas fa-arrows-up-down"></i> Yükseklik Sığdır</button>
              <button type="button" class="pdf-btn toggle-btn" id="pdf-spread-btn" onclick="togglePdfSpreadMode()" title="Çift Sayfa Kitap Modu (İki sayfa yan yana)"><i class="fas fa-book-open"></i> Çift Sayfa</button>
            </div>
            <div class="pdf-toolbar-divider"></div>
            <div class="pdf-toolbar-group">
              <button type="button" class="pdf-btn toggle-btn" id="pdf-toc-sidebar-btn" onclick="toggleTocSidebar()" title="İçindekiler Tablosu"><i class="fas fa-list-ol"></i> İçindekiler</button>
              <button type="button" class="pdf-btn toggle-btn" id="pdf-search-btn" onclick="togglePdfSearch()" title="Belgede Ara (Ctrl + F)"><i class="fas fa-search"></i> Ara</button>
              <button type="button" class="pdf-btn toggle-btn" id="pdf-notes-sidebar-btn" onclick="toggleNotesSidebar()" title="Notlarım"><i class="fas fa-pen-nib"></i> Notlarım</button>
              <button type="button" class="pdf-btn toggle-btn" id="pdf-tts-btn" onclick="togglePdfTTS()" title="Kitabı Seslendir / Durdur"><i class="fas fa-volume-high"></i> Dinle</button>
            </div>
            <div class="pdf-toolbar-divider"></div>
            <div class="pdf-toolbar-group" id="reader-surface-group" title="ChromaGuard™ Okuma Yüzeyi">
              <button type="button" class="pdf-btn surface-btn active" id="btn-surface-normal" onclick="setReaderSurfaceMode('normal')" title="Normal Gündüz" aria-label="Normal Gündüz Modu"><i class="fas fa-sun"></i></button>
              <button type="button" class="pdf-btn surface-btn" id="btn-surface-sepia" onclick="setReaderSurfaceMode('sepia')" title="Sepya Kağıt Dokusu" aria-label="Sepya Kağıt Dokusu"><i class="fas fa-scroll"></i></button>
              <button type="button" class="pdf-btn surface-btn" id="btn-surface-eink" onclick="setReaderSurfaceMode('eink')" title="E-Ink Monokrom" aria-label="E-Ink Monokrom"><i class="fas fa-newspaper"></i></button>
              <button type="button" class="pdf-btn surface-btn" id="btn-surface-chromaguard" onclick="setReaderSurfaceMode('chromaguard')" title="ChromaGuard™ Akıllı Gece (Görseller Bozulmaz)" aria-label="ChromaGuard Akıllı Gece"><i class="fas fa-moon"></i></button>
            </div>
            <div class="pdf-toolbar-divider"></div>
            <div class="pdf-toolbar-group">
              <button type="button" class="pdf-btn text-btn" id="btn-lan-handoff" onclick="openHandoffModal()" title="Telefonda Okumaya Devam Et (QR Kod)"><i class="fas fa-mobile-alt"></i> Telefonda Devam Et</button>
            </div>
          </div>

          <!-- Floating In-Document Search Bar -->
          <div class="pdf-search-bar" id="pdf-search-bar" style="display: none;">
            <div class="pdf-search-main-row">
              <div class="pdf-search-input-wrap">
                <i class="fas fa-search pdf-search-input-icon"></i>
                <input type="text" id="pdf-search-input" placeholder="Belgede ara... (Enter ile sonraki)" aria-label="Belgede ara" autocomplete="off" spellcheck="false" oninput="onPdfSearchInput(this.value)" onkeydown="onPdfSearchKeydown(event)">
                <button type="button" class="pdf-search-icon-btn clear" id="pdf-search-clear-btn" onclick="clearPdfSearch()" style="display: none;" title="Aramayı Temizle" aria-label="Aramayı Temizle"><i class="fas fa-times"></i></button>
              </div>
              <div class="pdf-search-counter" id="pdf-search-counter">0 / 0</div>
              <div class="pdf-search-actions">
                <button type="button" class="pdf-search-nav-btn" id="pdf-search-prev-btn" onclick="pdfSearchPrev()" title="Önceki Eşleşme (Shift + Enter)" aria-label="Önceki Eşleşme" disabled><i class="fas fa-chevron-up"></i></button>
                <button type="button" class="pdf-search-nav-btn" id="pdf-search-next-btn" onclick="pdfSearchNext()" title="Sonraki Eşleşme (Enter)" aria-label="Sonraki Eşleşme" disabled><i class="fas fa-chevron-down"></i></button>
                <button type="button" class="pdf-search-nav-btn" id="pdf-search-list-btn" onclick="togglePdfSearchResultsDrawer()" title="Sonuç Listesi" aria-label="Sonuç Listesi"><i class="fas fa-list-ul"></i></button>
                <button type="button" class="pdf-search-nav-btn close" onclick="closePdfSearch()" title="Kapat (Esc)" aria-label="Aramayı Kapat"><i class="fas fa-times"></i></button>
              </div>
            </div>
            <!-- Collapsible Results Drawer -->
            <div class="pdf-search-results-drawer" id="pdf-search-results-drawer" style="display: none;">
              <div class="pdf-search-drawer-header">
                <span id="pdf-search-drawer-title">Arama Sonuçları</span>
              </div>
              <div class="pdf-search-drawer-list" id="pdf-search-drawer-list">
                <!-- Dynamically populated: page groups and snippets -->
              </div>
            </div>
          </div>

          <!-- Viewer Body -->
          <div class="pdf-viewer-body">
            <!-- Notes Sidebar -->
            <div class="pdf-notes-sidebar" id="pdf-notes-sidebar">
              <div class="pdf-notes-sidebar-header">
                <h3>Notlar & İşaretlemeler</h3>
              </div>
              <div id="pdf-notes-list" class="pdf-notes-list">
                <div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>
              </div>
            </div>

            <!-- Table of Contents (TOC) Sidebar -->
            <div class="pdf-toc-sidebar" id="pdf-toc-sidebar">
              <div class="pdf-notes-sidebar-header">
                <h3><i class="fas fa-list-ol" style="color:var(--accent); margin-right:6px;"></i> İçindekiler</h3>
              </div>
              <div id="pdf-toc-list" class="pdf-toc-list">
                <div class="pdf-notes-empty">Bu belgede içindekiler tablosu bulunamadı.</div>
              </div>
            </div>

            <!-- Canvas Container -->
            <div class="pdf-canvas-container" id="pdf-canvas-container" onscroll="onPdfContainerScroll()">
              <div class="pdf-page-wrapper" id="pdf-page-wrapper">
                <canvas id="pdf-render-canvas"></canvas>
                <div class="textLayer" id="pdf-text-layer"></div>
                <div class="pdf-highlight-layer" id="pdf-highlight-layer"></div>
              </div>
            </div>
          </div>

          <!-- Floating Action Bar -->
          <div class="pdf-floating-bar" id="pdf-floating-bar">
            <button type="button" class="hl-color-btn yellow" onclick="applyHighlight('#e8dca0', 'yellow')" title="Sarı" aria-label="Sarı Vurgu"></button>
            <button type="button" class="hl-color-btn green" onclick="applyHighlight('#d3dfc3', 'green')" title="Yeşil" aria-label="Yeşil Vurgu"></button>
            <button type="button" class="hl-color-btn blue" onclick="applyHighlight('#d8d1c3', 'blue')" title="Mavi" aria-label="Mavi Vurgu"></button>
            <button type="button" class="hl-color-btn pink" onclick="applyHighlight('#e4d6cd', 'pink')" title="Pembe" aria-label="Pembe Vurgu"></button>
            <button class="hl-action-btn" onclick="openNoteModalForSelection()"><i class="fas fa-sticky-note"></i> Not Ekle</button>
            <button type="button" class="hl-action-btn close" onclick="clearSelection()" aria-label="Vurgu Seçimini Temizle" title="Kapat"><i class="fas fa-times"></i></button>
          </div>
        </div>
        <!-- Keep iframe hidden for background fallback download/printing in needed cases -->
        <iframe id="workspace-pdf-frame" src="" title="PDF Belge Önizleme Çerçevesi" class="workspace-pdf-iframe" style="display: none;"></iframe>
      </div>

      <!-- Interactive Drag Resize Handle -->
      <div class="workspace-resize-handle" id="workspace-resize-handle">
        <div class="resize-dot"></div>
      </div>

      <!-- Right Panel: AI Chat Panel -->
      <div class="workspace-chat-pane" id="workspace-chat-pane">
        <!-- Chat Header with Copy Button -->
        <div class="workspace-chat-header" id="workspace-chat-header">
          <div class="workspace-chat-title">
            <i class="fas fa-wand-magic-sparkles" style="color: var(--accent);"></i>
            <span>AI Asistanı</span>
          </div>
          <button type="button" class="btn-copy-chat" id="btn-copy-chat" onclick="copyWorkspaceChat()" title="Tüm konuşmayı panoya kopyala">
            <i class="fas fa-copy"></i>
            <span class="btn-copy-text">Konuşmayı Kopyala</span>
          </button>
        </div>

        <!-- Chat messages occupy the full vertical pane height now -->
        <div class="workspace-chat-messages" id="workspace-chat-messages">
          <!-- Initial Welcome message -->
        </div>

        <div class="workspace-chat-input-area">
          <div id="workspace-stop-wrap" style="display:none; margin-bottom:8px;">
            <button type="button" id="btn-stop-chat" class="btn-stop-chat" onclick="stopChatGeneration()">
              <i class="fas fa-stop-circle"></i> Yanıtı Durdur
            </button>
          </div>
          <div class="workspace-prompt-chips" id="workspace-prompt-chips" style="display:flex; gap:6px; overflow-x:auto; padding-bottom:6px; margin-bottom:6px;">
            <button type="button" class="prompt-chip" onclick="insertPromptChip('Bu kitabı ana hatlarıyla özetler misin?')">Özetle</button>
            <button type="button" class="prompt-chip" onclick="insertPromptChip('Kitabın ana fikirleri ve kilit temaları nelerdir?')">Ana Temalar</button>
            <button type="button" class="prompt-chip" onclick="insertPromptChip('Bu kitabın ana mesajını 5 yaşındaki birine anlatır gibi basitçe açıkla.')">Basitçe Açıkla</button>
            <button type="button" class="prompt-chip" onclick="insertPromptChip('Bu kitaptan akılda kalıcı en çarpıcı 3 alıntıyı sayfa referansıyla listele.')">Çarpıcı Alıntılar</button>
          </div>
          <div class="workspace-input-wrapper">
            <textarea id="workspace-chat-input" placeholder="Bu kitap hakkında soru sor..." aria-label="Kitap hakkında soru sor" rows="1" onkeydown="handleWorkspaceChatKey(event)"></textarea>
            <button type="button" class="btn-workspace-send" id="btn-workspace-send" onclick="sendWorkspaceMessage()" aria-label="Mesajı Gönder">
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Ayarlar Modalı -->
  <div class="modal-overlay" id="settings-modal" role="dialog" aria-modal="true" aria-labelledby="settings-modal-title" tabindex="-1">
    <div class="modal">
      <div class="modal-top"></div>
      
      <!-- Modal Header -->
      <div class="settings-header">
        <div class="settings-header-left">
          <div class="settings-header-icon">
            <i class="fas fa-sliders-h"></i>
          </div>
          <div>
            <h2 id="settings-modal-title">Kütüphane Ayarları</h2>
            <p>AI modelleri, analiz limitleri ve sistem tercihleri</p>
          </div>
        </div>
        <button type="button" class="modal-close" style="position: static;" onclick="closeSettingsDirect()" title="Kapat" aria-label="Kapat"><i class="fas fa-times"></i></button>
      </div>

      <!-- Settings Tabs Bar -->
      <div class="settings-tabs">
        <button type="button" class="settings-tab-btn active" id="tab-btn-ai" onclick="switchSettingsTab('ai')">
          <i class="fas fa-brain"></i> Yapay Zeka
        </button>
        <button type="button" class="settings-tab-btn" id="tab-btn-analysis" onclick="switchSettingsTab('analysis')">
          <i class="fas fa-microscope"></i> Analiz &amp; Görsel
        </button>
        <button type="button" class="settings-tab-btn" id="tab-btn-security" onclick="switchSettingsTab('security')">
          <i class="fas fa-shield-alt"></i> Güvenlik &amp; Telefon
        </button>
        <button type="button" class="settings-tab-btn" id="tab-btn-system" onclick="switchSettingsTab('system')">
          <i class="fas fa-cog"></i> Sistem &amp; Veri
        </button>
      </div>

      <!-- Modal Body (The ONLY scrollable container) -->
      <div class="settings-body">
        <!-- TAB 1: Yapay Zeka & Modeller -->
        <div class="settings-tab-pane active" id="tab-pane-ai">
          <div class="settings-section-card">
            <span class="settings-section-label">AI sağlayıcı ve erişim</span>
            
            <div class="settings-field-group">
              <label for="set-ai-provider">Sağlayıcı</label>
              <select id="set-ai-provider" class="settings-select" onchange="updateAIUI()">
                <option value="gemini">Google Gemini</option>
                <option value="ollama">Ollama (Local)</option>
                <option value="lmstudio">LM Studio (Local)</option>
              </select>
              <div id="ai-local-warning" class="callout callout--danger" style="display:none; margin-top: 0.4rem;">
                <i class="fas fa-exclamation-triangle"></i> <strong>Uyarı:</strong> Yerel modda sohbet asistanı kullanılamaz.
              </div>
            </div>

            <div id="ai-url-container" class="settings-field-group" style="display:none;">
              <label for="set-ai-base-url">Base URL</label>
              <input type="text" id="set-ai-base-url" class="settings-input" placeholder="http://localhost:11434/v1"
                onkeydown="if(event.key==='Enter') saveSettings()">
            </div>

            <div id="ai-cloud-inputs" class="settings-field-group">
              <label for="set-api-key">API Anahtarı</label>
              <input type="password" id="set-api-key" class="settings-input" placeholder="API anahtarı..."
                onkeydown="if(event.key==='Enter') saveSettings()">
            </div>

            <div id="ai-model-container" class="settings-field-group">
              <label id="ai-model-name-label" for="set-ai-model-name">
                <span>Model Adı (Varsayılan veya Tekil Mod)</span>
                <span id="ai-model-status-badge" style="font-size: 0.68rem; color: var(--muted); font-weight: 500;"></span>
              </label>
              <input type="text" id="set-ai-model-name" class="settings-input" value="gemini-3.8-flash" placeholder="gemini-3.8-flash"
                onkeydown="if(event.key==='Enter') saveSettings()">
              <small id="ai-model-hint" style="font-size: 0.68rem; color: var(--muted); display: block; margin-top: 0.2rem;">
                Kademeli model zinciri kapalıyken tüm işlemler için bu tekil model kullanılır.
              </small>
            </div>
          </div>

          <!-- Kademeli Model Zinciri (Cascade Engine) -->
          <div id="ai-cascade-container" class="settings-section-card">
            <div style="display: flex; align-items: center; justify-content: space-between;">
              <label for="set-gemini-cascade-mode" style="font-size: 0.82rem; font-weight: 700; cursor: pointer; user-select: none; display: flex; align-items: center; gap: 0.5rem; color: var(--ink); margin: 0;">
                <i class="fas fa-layer-group" style="color: var(--accent);"></i>
                Kademeli Model Zinciri (Cascade Engine)
                <span class="tooltip-wrap tooltip-right"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">İstekler ilk modelden başlar. Model yoğunsa (503) veya kotası dolarsa bekleme yapmadan sıradaki modele aktarılır.</span></span>
              </label>
              <label class="ui-toggle-switch" title="Kademeli zinciri aç/kapat">
                <input type="checkbox" id="set-gemini-cascade-mode" checked onchange="updateAIUI()">
                <span class="ui-toggle-slider"></span>
              </label>
            </div>

            <div class="cascade-info-box">
              <i class="fas fa-info-circle" style="color: var(--accent); margin-top: 1px; flex-shrink: 0;"></i>
              <div>
                <strong>Nasıl Çalışır?</strong> İstekler sırasıyla aşağıdaki modellere gider. Meşgul veya kotası biten model otomatik olarak sonrakine devredilir.
              </div>
            </div>

            <div id="cascade-slots-list" style="display: flex; flex-direction: column; gap: 0.35rem; width: 100%; box-sizing: border-box;">
              <!-- 1. Kademe -->
              <div class="cascade-slot-row">
                <span class="cascade-level-pill lvl-1">1. Kademe</span>
                <input type="text" id="cascade-model-0" value="gemini-3.8-flash" placeholder="Örn: gemini-3.8-flash" aria-label="1. Kademe Model" class="cascade-model-input" onkeydown="if(event.key==='Enter') saveSettings()">
                <span class="cascade-role-badge role-primary">İlk Tercih</span>
              </div>

              <div class="cascade-flow-connector">
                <div class="cascade-flow-line"></div>
                <div class="cascade-flow-pill">
                  <i class="fas fa-arrow-down"></i>
                  <span>meşgulse devret</span>
                </div>
                <div class="cascade-flow-line"></div>
              </div>

              <!-- 2. Kademe -->
              <div class="cascade-slot-row">
                <span class="cascade-level-pill lvl-2">2. Kademe</span>
                <input type="text" id="cascade-model-1" value="gemini-3.7-flash" placeholder="Örn: gemini-3.7-flash" aria-label="2. Kademe Model" class="cascade-model-input" onkeydown="if(event.key==='Enter') saveSettings()">
                <span class="cascade-role-badge role-thinking">Düşünce</span>
              </div>

              <div class="cascade-flow-connector">
                <div class="cascade-flow-line"></div>
                <div class="cascade-flow-pill">
                  <i class="fas fa-arrow-down"></i>
                  <span>meşgulse devret</span>
                </div>
                <div class="cascade-flow-line"></div>
              </div>

              <!-- 3. Kademe -->
              <div class="cascade-slot-row">
                <span class="cascade-level-pill lvl-3">3. Kademe</span>
                <input type="text" id="cascade-model-2" value="gemini-3.6-flash" placeholder="Örn: gemini-3.6-flash" aria-label="3. Kademe Model" class="cascade-model-input" onkeydown="if(event.key==='Enter') saveSettings()">
                <span class="cascade-role-badge role-flagship">Amiral</span>
              </div>

              <div class="cascade-flow-connector">
                <div class="cascade-flow-line"></div>
                <div class="cascade-flow-pill">
                  <i class="fas fa-arrow-down"></i>
                  <span>meşgulse devret</span>
                </div>
                <div class="cascade-flow-line"></div>
              </div>

              <!-- 4. Kademe -->
              <div class="cascade-slot-row">
                <span class="cascade-level-pill lvl-4">4. Kademe</span>
                <input type="text" id="cascade-model-3" value="gemini-3.5-flash" placeholder="Örn: gemini-3.5-flash (isteğe bağlı)" aria-label="4. Kademe Model" class="cascade-model-input" onkeydown="if(event.key==='Enter') saveSettings()">
                <span class="cascade-role-badge role-standard">Standart</span>
              </div>

              <div class="cascade-flow-connector">
                <div class="cascade-flow-line"></div>
                <div class="cascade-flow-pill">
                  <i class="fas fa-arrow-down"></i>
                  <span>meşgulse devret</span>
                </div>
                <div class="cascade-flow-line"></div>
              </div>

              <!-- 5. Kademe -->
              <div class="cascade-slot-row">
                <span class="cascade-level-pill lvl-5">5. Kademe</span>
                <input type="text" id="cascade-model-4" value="gemini-3.5-flash-lite" placeholder="Örn: gemini-3.5-flash-lite (isteğe bağlı)" aria-label="5. Kademe Model" class="cascade-model-input" onkeydown="if(event.key==='Enter') saveSettings()">
                <span class="cascade-role-badge role-fallback">Son Yedek</span>
              </div>
            </div>

            <div class="cascade-footer-bar">
              <span class="cascade-footer-note">
                <i class="fas fa-info-circle" style="opacity: 0.7;"></i> İsteğe bağlı kademeler boş bırakılabilir.
              </span>
              <button type="button" class="btn-cascade-reset" onclick="resetCascadeModelsToDefault()">
                <i class="fas fa-undo"></i> Varsayılana Sıfırla
              </button>
            </div>
          </div>

          <div class="settings-section-card">
            <div class="settings-field-group">
              <label for="set-ai-max-chars">
                <span>Analiz Karakter Sınırı <small style="color:var(--muted); font-weight:400;">(1000-250000)</small></span>
                <span id="ai-max-chars-val" style="font-family:'Geist Mono',monospace; color:var(--accent); font-weight:700;">50000</span>
              </label>
              <input type="range" id="set-ai-max-chars" min="1000" max="250000" step="1000" value="50000" 
                style="width:100%; accent-color: var(--accent); cursor: pointer;"
                oninput="document.getElementById('ai-max-chars-val').innerText = this.value">
              <small style="font-size: 0.68rem; color: var(--muted); display: block; margin-top: 0.2rem;">Gemini için 50k-100k, Local modeller için 3k-10k önerilir.</small>
            </div>
          </div>
        </div>

        <!-- TAB 2: Analiz Limitleri ve Vision Ayarları -->
        <div class="settings-tab-pane" id="tab-pane-analysis">
          <div class="settings-section-card">
            <span class="settings-section-label">Analiz limitleri</span>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
              <div class="settings-field-group">
                <label for="set-pages">
                  <span>Max Sayfa <small style="color:var(--muted); font-weight:400;">(1-100)</small></span>
                  <span class="tooltip-wrap tooltip-right"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">Yapay zekanın kitabın toplamda kaç sayfasını incelemesini istiyorsunuz? 1 ile 100 sayfa arasında bir değer seçebilirsiniz.</span></span>
                </label>
                <input type="number" id="set-pages" class="settings-input" min="1" max="100">
              </div>
              <div class="settings-field-group">
                <label for="set-ocr-pages">
                  <span>OCR Sayfa <small style="color:var(--muted); font-weight:400;">(0-60)</small></span>
                  <span class="tooltip-wrap tooltip-left"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">Eğer kitap taranmış resim formatındaysa, kaç sayfanın yazılarının okunacağını belirler. 0 ile 60 sayfa arası sınır koyabilirsiniz.</span></span>
                </label>
                <input type="number" id="set-ocr-pages" class="settings-input" min="0" max="60">
              </div>
            </div>
          </div>

          <div class="settings-section-card">
            <span class="settings-section-label" style="color:var(--accent);">Görüntü / Vision ayarları</span>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
              <div class="settings-field-group">
                <label for="set-vision-pages">
                  <span>Vision Sayfa <small style="color:var(--muted); font-weight:400;">(0-60)</small></span>
                  <span class="tooltip-wrap tooltip-right"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">Yapay zekanın kitap kapaklarını ve içindeki görselleri görerek analiz edeceği sayfa sayısıdır.</span></span>
                </label>
                <input type="number" id="set-vision-pages" class="settings-input" min="0" max="60">
              </div>
              <div class="settings-field-group">
                <label for="set-vision-quality">
                  <span>JPEG Kalite <small style="color:var(--muted); font-weight:400;">(40-95)</small></span>
                  <span class="tooltip-wrap tooltip-left"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">İncelenen resimlerin netlik kalitesidir. 82 değeri ideal hız ve netlik dengesidir.</span></span>
                </label>
                <input type="number" id="set-vision-quality" class="settings-input" min="40" max="95">
              </div>
            </div>
            <div class="settings-field-group" style="margin-top: 0.3rem;">
              <label for="set-vision-dim">
                <span>Çözünürlük Sınırı <small style="color:var(--muted); font-weight:400;">(256-2400)</small></span>
                <span class="tooltip-wrap tooltip-right"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">Gönderilen resimlerin büyüklüğünü belirler. 1200 piksel çoğu kitap için en iyi sonuçtur.</span></span>
              </label>
              <input type="number" id="set-vision-dim" class="settings-input" min="256" max="2400">
            </div>
          </div>
        </div>

        <!-- TAB 3: Güvenlik & Telefon Bağlantısı -->
        <div class="settings-tab-pane" id="tab-pane-security">
          <!-- Kart 1: Giriş ve Erişim Şifresi -->
          <div class="settings-section-card">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 0.2rem;">
              <span class="settings-section-label" style="margin-bottom:0;">Uzaktan ve yerel erişim şifresi</span>
              <span id="sec-pwd-status-badge" style="font-size: 0.72rem; padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 600; display: inline-flex; align-items: center; gap: 0.35rem; background: var(--paper-dark); border: 1px solid var(--line); color: var(--muted);">
                <i class="fas fa-circle" style="font-size:0.5rem;"></i> Kontrol ediliyor...
              </span>
            </div>

            <p style="font-size: 0.78rem; color: var(--muted); margin: 0; line-height: 1.45;">
              Aynı Wi-Fi ağındaki telefon veya tabletinizden kütüphanenize güvenle erişebilmek için bir erişim şifresi belirleyin.
            </p>

            <div class="settings-field-group">
              <label for="set-access-password">
                <span>Erişim Şifresi</span>
                <span class="tooltip-wrap tooltip-left"><i class="fas fa-info-circle info-icon"></i><span class="tooltip">Şifre belirlendiğinde harici cihazlar kütüphaneye girmeden önce bu şifreyi girmek zorundadır.</span></span>
              </label>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="position: relative; flex: 1; display: flex; align-items: center;">
                  <input type="password" id="set-access-password" class="settings-input" placeholder="Şifre belirlenmemiş" style="padding-right: 2.5rem;" autocomplete="new-password" onkeydown="if(event.key==='Enter'){event.preventDefault();saveAccessPasswordDirect();}">
                  <button type="button" onclick="toggleAccessPasswordVisibility()" title="Şifreyi Göster/Gizle" aria-label="Şifreyi Göster veya Gizle" style="position: absolute; right: 0.6rem; background: transparent; border: none; color: var(--muted); cursor: pointer; padding: 0.4rem; font-size: 0.9rem; display: flex; align-items: center; justify-content: center;">
                    <i id="btn-toggle-pwd-icon" class="fas fa-eye"></i>
                  </button>
                </div>
                <button type="button" id="btn-save-access-pwd" onclick="saveAccessPasswordDirect()" class="btn-settings-save" style="padding: 0.65rem 1.1rem; font-size: 0.8rem; white-space: nowrap; border-radius: var(--radius-xs);">
                  <i class="fas fa-save"></i> <span>Şifreyi Kaydet</span>
                </button>
              </div>
            </div>

            <div style="display: flex; gap: 0.6rem; align-items: center; justify-content: space-between; margin-top: 0.2rem;">
              <small id="sec-pwd-hint" style="font-size: 0.72rem; color: var(--muted);">Şifreyi yazdıktan sonra "Şifreyi Kaydet" butonuna veya Enter'a basabilirsiniz.</small>
              <button type="button" id="btn-remove-access-pwd" onclick="removeAccessPassword()" class="btn btn--danger btn--sm" style="display: none; padding: 0.4rem 0.8rem;">
                <i class="fas fa-trash-alt" style="margin-right: 0.3rem;"></i> Şifreyi Kaldır
              </button>
            </div>
          </div>

          <!-- Kart 2: Telefonda Nasıl Açılır? (Bağlantı Rehberi) -->
          <div class="settings-section-card">
            <span class="settings-section-label">Telefondan veya tabletten bağlanma</span>
            
            <div style="background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xs); padding: 0.85rem 1rem;">
              <div style="font-size: 0.76rem; font-weight: 600; color: var(--ink); margin-bottom: 0.4rem; display: flex; align-items: center; justify-content: space-between;">
                <span>Telefon Tarayıcısına Yazılacak Adres:</span>
                <span style="font-size: 0.7rem; color: var(--ok); font-weight: 500;"><i class="fas fa-wifi"></i> Aynı Wi-Fi</span>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <code id="phone-connection-url-display" style="flex: 1; padding: 0.55rem 0.8rem; background: var(--paper-dark); border-radius: 6px; font-size: 0.88rem; font-weight: 600; color: var(--accent); border: 1px dashed var(--line); word-break: break-all;">
                  http://...
                </code>
                <button type="button" onclick="copyPhoneConnectionUrl()" class="btn-modal-secondary" style="padding: 0.55rem 0.85rem; font-size: 0.78rem; display: flex; align-items: center; gap: 0.35rem; white-space: nowrap;">
                  <i class="fas fa-copy"></i> Kopyala
                </button>
              </div>
            </div>

            <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.78rem; color: var(--muted); line-height: 1.45;">
              <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="background: var(--accent); color: var(--paper); width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;">1</span>
                <span>Bilgisayarınız ve telefonunuzun <strong>aynı Wi-Fi ağına</strong> bağlı olduğundan emin olun.</span>
              </div>
              <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="background: var(--accent); color: var(--paper); width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;">2</span>
                <span>Yukarıdaki adresi telefonunuzun Chrome, Safari veya tarayıcısına girin.</span>
              </div>
              <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                <span style="background: var(--accent); color: var(--paper); width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; flex-shrink: 0; margin-top: 2px;">3</span>
                <span>Ekrana gelen şifre kutusuna yukarıda belirlediğiniz erişim şifresini yazıp kütüphanenizi kullanın.</span>
              </div>
            </div>
          </div>

          <!-- Kart 3: E-Kitap Okuyucular İçin OPDS 1.2 Kataloğu -->
          <div class="settings-section-card">
            <span class="settings-section-label"><i class="fas fa-rss" style="margin-right: 4px;"></i> E-KİTAP OKUYUCU (OPDS 1.2 KATALOĞU)</span>
            <p style="font-size: 0.78rem; color: var(--muted); margin: 0; line-height: 1.45;">
              Moon+ Reader, Apple Books, Kobo, KOReader veya Aldiko gibi e-okuyucu uygulamalarına aşağıdaki OPDS kataloğu adresini ekleyerek kütüphanenizdeki kitapları doğrudan e-okuyucunuzdan indirebilirsiniz:
            </p>
            <div style="background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius-xs); padding: 0.85rem 1rem; margin-top: 0.6rem;">
              <div style="font-size: 0.76rem; font-weight: 600; color: var(--ink); margin-bottom: 0.4rem; display: flex; align-items: center; justify-content: space-between;">
                <span>OPDS Katalog Bağlantı Adresi:</span>
                <span style="font-size: 0.7rem; color: var(--muted); font-weight: 500;"><i class="fas fa-book-reader"></i> OPDS 1.2</span>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <code id="opds-connection-url-display" style="flex: 1; padding: 0.55rem 0.8rem; background: var(--paper-dark); border-radius: 6px; font-size: 0.88rem; font-weight: 600; color: var(--accent); border: 1px dashed var(--line); word-break: break-all;">
                  http://.../opds
                </code>
                <button type="button" onclick="copyOpdsConnectionUrl()" class="btn-modal-secondary" style="padding: 0.55rem 0.85rem; font-size: 0.78rem; display: flex; align-items: center; gap: 0.35rem; white-space: nowrap;">
                  <i class="fas fa-copy"></i> Kopyala
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 4: Sistem & Veri Yönetimi -->
        <div class="settings-tab-pane" id="tab-pane-system">
          <div class="settings-section-card">
            <span class="settings-section-label">Tesseract OCR sistemi</span>
            <div class="settings-field-group">
              <label for="set-tesseract-cmd">Tesseract Yürütülebilir Dosya Yolu</label>
              <input type="text" id="set-tesseract-cmd" class="settings-input" placeholder="C:\Program Files\Tesseract-OCR\tesseract.exe">
              <div id="tesseract-status" style="font-size: 0.7rem; margin-top: 0.3rem; color: var(--muted);"></div>
            </div>
          </div>

          <div class="settings-section-card">
            <span class="settings-section-label">Gölge kütüphaneci (otomatik izleme klasörü)</span>
            <div class="settings-field-group">
              <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer;">
                <input type="checkbox" id="set-watchfolder-enabled" aria-label="Klasör İzlemeyi Etkinleştir">
                <span>İndirilenleri Otomatik Ekle (Auto-Watchfolder)</span>
              </label>
              <div style="font-size:0.75rem; color:var(--muted); margin-top:0.3rem;">
                Belirlediğiniz klasöre inen PDF ve EPUB dosyaları tespit edilip indirme tamamlandığında otomatik kütüphaneye eklenir.
              </div>
            </div>
            <div class="settings-field-group" style="margin-top:0.6rem;">
              <label for="set-watchfolder-path">İzlenecek Klasör Yolu</label>
              <input type="text" id="set-watchfolder-path" class="settings-input" placeholder="Örn: C:\Users\fatih\Downloads">
            </div>
          </div>

          <div class="settings-section-card">
            <span class="settings-section-label">Veri ve sistem araçları</span>
            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
              <button type="button" class="btn-modal-secondary" style="width:100%; padding: 0.8rem 1rem; border-radius: var(--radius-xs); display: flex; align-items: center; justify-content: center; gap: 0.6rem;" onclick="exportToExcel()">
                <i class="fas fa-file-excel" style="color: var(--accent); font-size: 1.05rem;"></i> Kütüphaneyi Excel'e Aktar (.xlsx)
              </button>
              <button type="button" class="btn-modal-secondary" style="width:100%; padding: 0.8rem 1rem; border-radius: var(--radius-xs); display: flex; align-items: center; justify-content: center; gap: 0.6rem;" onclick="openDuplicatesModal()">
                <i class="fas fa-copy" style="color: var(--accent); font-size: 1.05rem;"></i> Mükerrer / Çift Kitapları Tara ve Temizle
              </button>
              <button type="button" class="btn-modal-secondary" style="width:100%; padding: 0.8rem 1rem; border-radius: var(--radius-xs); display: flex; align-items: center; justify-content: center; gap: 0.6rem;" onclick="exportFullLibraryZip()">
                <i class="fas fa-file-archive" style="color: var(--accent); font-size: 1.05rem;"></i> Taşınabilir Tam Kütüphane Yedeği (.zip)
              </button>
              <button type="button" class="btn-modal-secondary" style="width:100%; padding: 0.8rem 1rem; border-radius: var(--radius-xs); display:flex; align-items:center; justify-content:center; gap:0.6rem;" onclick="closeSettingsDirect(); openLogsModal();">
                <i class="fas fa-terminal" style="color: var(--accent); font-size: 1.05rem;"></i> Sistem &amp; İşlem Günlüklerini (Log) Görüntüle
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Footer (Sticky, Clean & Prominent) -->
      <div class="settings-footer">
        <button type="button" class="btn-settings-cancel" onclick="closeSettingsDirect()">Vazgeç</button>
        <button type="button" class="btn-settings-save" id="btn-save-settings" onclick="saveSettings()">
          <i class="fas fa-check"></i> <span>Ayarları Kaydet</span>
        </button>
      </div>
    </div>
  </div>

  <!-- ÖZELLİK: Toplu İşlem Barı -->
  <div class="bulk-bar" id="bulk-bar">
    <div style="font-size: 0.9rem; color: var(--muted);"><span id="bulk-count">0</span> kitap seçildi</div>
    <div style="display:flex; gap: 1rem;">
      <button class="btn-modal-danger" id="bulk-delete-btn" onclick="bulkDelete()"
        style="padding: 0.6rem 1.2rem; border-radius: var(--r-sm);">
        <i class="fas fa-trash-alt" style="margin-right: 0.4rem;"></i> Seçilenleri Sil
      </button>
      <button class="btn-modal-secondary" onclick="toggleSelectionMode()"
        style="padding: 0.6rem 1.2rem; border-radius: var(--r-sm);">Vazgeç</button>
    </div>
  </div>

  <!-- Koleksiyon Yönetim Modalı -->
  <div class="modal-overlay" id="col-modal" role="dialog" aria-modal="true" aria-labelledby="col-modal-title" tabindex="-1" style="z-index: 3500;">
    <div class="modal"
      style="max-width: 480px; padding: 2.5rem; background: var(--paper); border: 1px solid var(--line); border-radius: var(--r-md); box-shadow: var(--shadow-lg);">
      <div class="modal-top"
        style="background: var(--sepia); height: 6px; top: 0; left: 0; right: 0; position: absolute; border-radius: 6px 6px 0 0;">
      </div>
      <button type="button" class="modal-close" onclick="closeColModalDirect()" title="Kapat" aria-label="Kapat"><i class="fas fa-times"></i></button>

      <div style="text-align: center; margin-bottom: 2rem;">
        <div
          style="width: 64px; height: 64px; margin: 0 auto 1rem; background: var(--paper-dark); border-radius: 50%; display:flex; align-items:center; justify-content:center; color: var(--accent); font-size: 1.8rem;">
          <i class="fas fa-layer-group"></i>
        </div>
        <h3 id="col-modal-title" style="font-family:'Instrument Serif',serif; color:var(--ink); font-size:1.8rem; font-weight: 400;">Koleksiyon Yönetimi</h3>
        <p style="color:var(--muted); font-size:0.9rem; margin-top: 0.5rem; font-family:'Geist', sans-serif;">Bu kitabı
          okuma listelerinize dahil edin</p>
      </div>

      <div style="margin-bottom: 2rem;">
        <div id="col-list"
          style="max-height: 250px; overflow-y:auto; border: 1px solid var(--line); border-radius: var(--r-sm); background: var(--paper-dark); padding: 0.8rem; display:flex; flex-direction:column; gap:0.5rem;">
          <!-- Koleksiyonlar buraya yüklenecek -->
        </div>
      </div>

      <div
        style="background: var(--paper-dark); padding: 1.5rem; border-radius: 8px; border: 1px dashed var(--sepia-light);">
        <h4
          style="font-family:'Geist Mono', monospace; color:var(--sepia); font-size:0.75rem; letter-spacing:0.1em; margin-bottom: 1rem; text-transform:uppercase; font-weight:600;">
          Yeni Liste Oluştur</h4>
        <div style="display:flex; gap: 0.8rem; align-items: center;">
          <input type="text" id="new-col-name" placeholder="Koleksiyon Adı..." aria-label="Yeni Koleksiyon Adı"
            style="flex:1; padding:0.8rem 1rem; border:1px solid var(--line); border-radius:var(--r-sm); font-family:'Geist', sans-serif; font-size:0.95rem; background: var(--paper); color: var(--ink); outline: none;"
            onkeydown="if(event.key === 'Enter') createCollection()">
          <button type="button" class="btn-modal-primary" onclick="createCollection()" style="padding: 0.8rem 1.4rem;">
            <i class="fas fa-plus"></i> Ekle
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- PDF Not Ekleme / Düzenleme Modalı -->
  <div class="modal-overlay" id="pdf-note-modal" role="dialog" aria-modal="true" aria-labelledby="pdf-note-modal-title" tabindex="-1" style="z-index: 7000;">
    <div class="modal" style="max-width: 480px; padding: 2.5rem; background: var(--paper); border: 1px solid var(--line); border-radius: var(--r-md); box-shadow: var(--shadow-lg); position: relative;">
      <div class="modal-top" style="background: var(--accent); height: 6px; top: 0; left: 0; right: 0; position: absolute; border-radius: 6px 6px 0 0;"></div>
      <button type="button" class="modal-close" onclick="closePdfNoteModalDirect()" title="Kapat" aria-label="Kapat"><i class="fas fa-times"></i></button>

      <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="width: 54px; height: 54px; margin: 0 auto 1rem; background: var(--paper-dark); border-radius: 50%; display:flex; align-items:center; justify-content:center; color: var(--accent); font-size: 1.5rem;">
          <i class="fas fa-pen-fancy"></i>
        </div>
        <h3 id="pdf-note-modal-title" style="font-family:'Instrument Serif',serif; color:var(--ink); font-size:1.6rem; font-weight: 400;">Okuma Notu Ekle</h3>
        <p style="color:var(--muted); font-size:0.85rem; margin-top: 0.3rem; font-family:'Geist', sans-serif;">Seçtiğiniz metne kişisel yorumlarınızı veya özetlerinizi ekleyin.</p>
      </div>

      <div style="margin-bottom: 1.5rem;">
        <div class="pdf-selected-text-preview" id="pdf-selected-text-preview" style="max-height: 80px; overflow-y: auto; background: var(--paper-dark); border-left: 3px solid var(--accent); padding: 0.6rem 0.8rem; font-style: italic; font-size: 0.85rem; border-radius: 4px; margin-bottom: 1rem; color: var(--muted);"></div>
        <textarea id="pdf-note-textarea" placeholder="Notunuzu buraya yazın..." aria-label="Not Metni" class="field-textarea" style="min-height: 120px; font-family:'Geist', sans-serif; font-size: 0.95rem; resize: vertical;"></textarea>
      </div>

      <!-- Vurgu Rengi Seçici -->
      <div style="margin-bottom: 1.5rem; text-align: left;">
        <span style="display: block; font-family:'Geist', sans-serif; font-size: 0.8rem; font-weight: 600; color: var(--muted); margin-bottom: 0.5rem;">Vurgu Rengi:</span>
        <div style="display: flex; gap: 0.6rem; align-items: center;">
          <button type="button" class="hl-color-btn yellow" id="modal-color-yellow" onclick="selectModalNoteColor('#e8dca0', 'yellow')" style="width: 28px; height: 28px; border: 2px solid transparent;" title="Sarı" aria-label="Sarı"></button>
          <button type="button" class="hl-color-btn green" id="modal-color-green" onclick="selectModalNoteColor('#d3dfc3', 'green')" style="width: 28px; height: 28px; border: 2px solid transparent;" title="Yeşil" aria-label="Yeşil"></button>
          <button type="button" class="hl-color-btn blue" id="modal-color-blue" onclick="selectModalNoteColor('#d8d1c3', 'blue')" style="width: 28px; height: 28px; border: 2px solid transparent;" title="Mavi" aria-label="Mavi"></button>
          <button type="button" class="hl-color-btn pink" id="modal-color-pink" onclick="selectModalNoteColor('#e4d6cd', 'pink')" style="width: 28px; height: 28px; border: 2px solid transparent;" title="Pembe" aria-label="Pembe"></button>
        </div>
      </div>

      <div style="display: flex; gap: 0.8rem; justify-content: flex-end;">
        <button type="button" class="btn-modal-secondary" onclick="closePdfNoteModalDirect()" style="padding: 0.6rem 1.2rem; border-radius: var(--r-sm);">Vazgeç</button>
        <button type="button" onclick="savePdfNote()" class="btn btn--primary">Kaydet</button>
      </div>
    </div>
  </div>

  <!-- Telegram Senkronizasyon Modalı -->
  <div class="modal-overlay" id="telegram-modal" role="dialog" aria-modal="true" aria-labelledby="telegram-modal-title" tabindex="-1" style="z-index: 7500;">
    <div class="modal" style="max-width: 520px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; padding: 0; border-radius: var(--r-md);">
      <div class="modal-top"></div>
      <button type="button" class="modal-close" style="top: 1.2rem; right: 1.2rem;" onclick="closeTelegramModal()" title="Kapat" aria-label="Kapat"><i class="fas fa-times"></i></button>

      <!-- Modal Header -->
      <div style="padding: 1.5rem 2rem 1.2rem; border-bottom: 1px solid var(--line); display:flex; align-items:center; gap: 0.9rem;">
        <div style="width: 44px; height: 44px; border-radius: var(--r-sm); background: var(--paper-dark); color: var(--ink); display: flex; align-items: center; justify-content: center; font-size: 1.4rem;">
          <i class="fab fa-telegram-plane"></i>
        </div>
        <div>
          <h2 id="telegram-modal-title" style="font-family:'Instrument Serif',serif; font-size: 1.6rem; color: var(--ink); margin: 0;">Telegram Senkronizasyonu</h2>
          <p style="font-family:'Geist',sans-serif; font-size: 0.8rem; color: var(--muted); margin-top: 0.2rem;">Kitaplarınızı Telegram'dan kütüphaneye otomatik aktarın</p>
        </div>
      </div>

      <!-- Error banner -->
      <div id="tg-modal-error" class="callout callout--danger" style="display:none; margin: 1rem 2rem 0;"></div>

      <!-- Modal Body (Scrollable) -->
      <div style="flex: 1; overflow-y: auto; padding: 1.5rem 2rem;">

        <!-- STEP 1: API Bilgileri & Telefon No -->
        <div id="tg-step-1" style="display: block;">
          <div style="display:flex; flex-direction:column; gap: 1.2rem;">
            <div style="background: var(--paper-dark); padding: 0.85rem 1rem; border-radius: var(--r-sm); border: 1px solid var(--line); font-size: 0.8rem; color: var(--muted); line-height: 1.5;">
              <i class="fas fa-info-circle" style="color: var(--muted); margin-right: 4px;"></i>
              Telegram API ID ve Hash bilgilerinizi almak için <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" style="color:var(--accent); font-weight:600; text-decoration:underline;">my.telegram.org</a> adresine giriş yapıp <em>API development tools</em> bölümünü ziyaret edebilirsiniz.
            </div>

            <div>
              <label for="tg-input-api-id" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.4rem; color: var(--ink);">API ID</label>
              <input type="text" id="tg-input-api-id" aria-label="Telegram API ID" placeholder="Örn: 12345678" style="width:100%; padding:0.75rem; border:1.5px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.9rem;">
            </div>

            <div>
              <label for="tg-input-api-hash" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.4rem; color: var(--ink);">API Hash</label>
              <input type="password" id="tg-input-api-hash" aria-label="Telegram API Hash" placeholder="Örn: 9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d" style="width:100%; padding:0.75rem; border:1.5px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.9rem;">
            </div>

            <div>
              <label for="tg-input-phone" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.4rem; color: var(--ink);">Telefon Numarası (Ülke Koduyla)</label>
              <input type="tel" id="tg-input-phone" aria-label="Telefon Numarası" placeholder="+905xxxxxxxxx" style="width:100%; padding:0.75rem; border:1.5px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.9rem;">
            </div>

            <div>
              <label for="tg-input-chat-id" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.4rem; color: var(--ink);">Kaynak Sohbet / Kanal</label>
              <input type="text" id="tg-input-chat-id" aria-label="Kaynak Sohbet veya Kanal" value="me" placeholder="me (Kayıtlı Mesajlar) veya @kanaladi" style="width:100%; padding:0.75rem; border:1.5px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.9rem;">
              <small style="font-size: 0.72rem; color: var(--muted); margin-top: 0.3rem; display:block;">Kayıtlı Mesajlarınız için <strong>me</strong> bırakın veya kitap paylaştığınız kanalın kullanıcı adını/ID'sini girin.</small>
            </div>

            <button type="button" id="tg-btn-send-code" onclick="telegramSubmitCredentials()" class="btn btn--primary" style="width: 100%;">
              Doğrulama Kodu Gönder <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        <!-- STEP 2: SMS Doğrulama Kodu & 2FA -->
        <div id="tg-step-2" style="display: none;">
          <div style="display:flex; flex-direction:column; gap: 1.2rem;">
            <div style="text-align:center; padding: 0.5rem 0;">
              <div style="width: 50px; height: 50px; margin: 0 auto 0.8rem; background: var(--paper-dark); border-radius: 50%; display:flex; align-items:center; justify-content:center; color: var(--ink); font-size: 1.3rem;">
                <i class="fas fa-sms"></i>
              </div>
              <h3 style="font-family:'Instrument Serif',serif; color:var(--ink); font-size:1.3rem; margin:0;">Doğrulama Kodu</h3>
              <p style="color:var(--muted); font-size:0.82rem; margin-top: 0.4rem; font-family:'Geist', sans-serif;">
                Telegram uygulamasına veya <span id="tg-step-2-phone" style="font-weight:600; color:var(--ink);"></span> numarasına gelen onay kodunu girin.
              </p>
            </div>

            <div>
              <label for="tg-input-code" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.4rem; color: var(--ink); text-align:center;">Onay Kodu</label>
              <input type="text" id="tg-input-code" aria-label="Onay Kodu" placeholder="12345" maxlength="8" style="width:100%; text-align:center; letter-spacing: 0.4em; font-size: 1.4rem; font-weight: 700; padding:0.75rem; border:2px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist Mono', monospace;" onfocus="this.style.borderColor='var(--accent)'" onblur="this.style.borderColor='var(--line)'">
            </div>

            <!-- 2FA Password Field (shown if needed) -->
            <div id="tg-2fa-container" class="callout callout--warn" style="display: none; padding: 1rem; border-radius: var(--r-sm); flex-direction: column;">
              <label for="tg-input-password" style="font-size: 0.78rem; font-weight: 600; display: flex; align-items:center; gap: 0.4rem; color: var(--warn); margin-bottom: 0.4rem;">
                <i class="fas fa-lock"></i> İki Adımlı Doğrulama (2FA) Şifresi
              </label>
              <input type="password" id="tg-input-password" aria-label="İki Adımlı Doğrulama Şifresi" placeholder="Telegram Bulut Şifreniz" style="width:100%; padding:0.75rem; border:1px solid var(--line); border-radius:8px; background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.9rem;">
            </div>

            <div style="display: flex; gap: 0.8rem; margin-top: 0.5rem;">
              <button type="button" class="btn-modal-secondary" onclick="setTelegramStep(1)" style="padding: 0.75rem 1.2rem; border-radius: var(--r-sm); border: 1px solid var(--line); background: var(--paper); color: var(--muted); cursor: pointer; font-weight: 500;">
                <i class="fas fa-arrow-left"></i> Geri
              </button>
              <button type="button" id="tg-btn-verify-code" onclick="telegramSubmitCode()" class="btn btn--primary" style="flex: 1;">
                <i class="fas fa-check"></i> Bağlantıyı Tamamla
              </button>
            </div>
          </div>
        </div>

        <!-- STEP 3: Bağlı Hesap & Senkronizasyon -->
        <div id="tg-step-3" style="display: none;">
          <div style="display:flex; flex-direction:column; gap: 1.2rem;">
            <div class="callout callout--ok" style="border-radius: var(--r-md); padding: 1.2rem; display: flex; align-items: center; gap: 1rem;">
              <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--ok); color: var(--paper); display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                <i class="fas fa-check"></i>
              </div>
              <div style="flex: 1;">
                <div style="font-family:'Geist',sans-serif; font-weight:700; color:var(--ink); font-size:1.05rem;" id="tg-connected-name">Telegram Kullanıcısı</div>
                <div style="font-family:'Geist Mono',monospace; font-size:0.8rem; color:var(--muted); margin-top: 0.2rem;" id="tg-connected-phone">+90...</div>
                <div style="display: flex; gap: 0.6rem; align-items: center; margin-top: 0.4rem;">
                  <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--ok);"></span>
                  <span style="font-size:0.75rem; color:var(--ok); font-weight:600;">Oturum Aktif</span>
                </div>
              </div>
            </div>

            <!-- Kanal / Sohbet Ayarı (Düzenlenebilir) -->
            <div style="background: var(--paper-dark); border: 1px solid var(--line); border-radius: 12px; padding: 1rem; display:flex; flex-direction:column; gap: 0.8rem;">
              <div>
                <label for="tg-active-chat-input" style="font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.35rem; color: var(--ink);">
                  <i class="fab fa-telegram-plane" style="color:var(--accent); margin-right:4px;"></i> Kaynak Sohbet / Kanal:
                </label>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                  <input type="text" id="tg-active-chat-input" aria-label="Aktif Sohbet veya Kanal" value="me" placeholder="me, @kanaladi veya link" style="flex:1; padding:0.65rem 0.8rem; border:1.5px solid var(--line); border-radius:var(--r-sm); background:var(--paper); color:var(--ink); font-family:'Geist', sans-serif; font-size:0.88rem;" onkeydown="if(event.key==='Enter') saveTelegramActiveChat()">
                  <button type="button" id="tg-btn-save-chat" onclick="saveTelegramActiveChat()" class="btn btn--primary" style="white-space: nowrap;">
                    <i class="fas fa-save"></i> Kaydet
                  </button>
                </div>
                <small style="font-size: 0.72rem; color: var(--muted); margin-top: 0.35rem; display:block;">
                  Kendi Kayıtlı Mesajlarınız için <strong>me</strong>, kitap kanalınız için <strong>@kanaladi</strong> veya link girin.
                </small>
              </div>

              <div style="display: flex; justify-content: space-between; align-items:center; border-top: 1px solid var(--line); padding-top: 0.6rem; font-size: 0.8rem; color: var(--muted);">
                <span>Son Senkronizasyon:</span>
                <span style="font-weight: 600; color: var(--ink);" id="tg-connected-last-sync">—</span>
              </div>
            </div>

              <div style="display:flex; align-items:center; gap:0.55rem; font-size:0.8rem; color:var(--muted); padding: 0.2rem 0.2rem;">
                <input type="checkbox" id="tg-reset-cursor" style="cursor:pointer; width:16px; height:16px; accent-color:var(--accent);">
                <label for="tg-reset-cursor" style="cursor:pointer; user-select:none; color:var(--ink); font-weight:500;">
                  Tüm geçmişi tara <span style="color:var(--muted); font-weight:normal;">(Son mesaj ID'sini sıfırla)</span>
                </label>
              </div>

              <button type="button" id="tg-btn-sync-action" class="btn-modal-primary" onclick="telegramTriggerSync()" style="width: 100%; padding: 0.85rem; justify-content:center; gap: 0.6rem;">
                <i class="fas fa-sync-alt"></i> Kitapları Şimdi Senkronize Et
              </button>

              <button type="button" id="tg-btn-disconnect" class="btn-modal-danger" onclick="telegramDisconnectAccount()" style="width: 100%; padding: 0.75rem; justify-content:center; gap: 0.5rem; background: transparent; color: var(--danger); border: 1px solid color-mix(in srgb, var(--danger) 40%, transparent); border-radius: var(--r-sm);">
                <i class="fas fa-unlink"></i> Hesabı Ayır (Çıkış Yap)
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

  <!-- Shortcuts Help Modal -->
  <div class="modal-overlay" id="shortcuts-modal" role="dialog" aria-modal="true" aria-labelledby="shortcuts-modal-title" tabindex="-1" style="z-index:8000;">
    <div class="modal" style="max-width: 480px; padding: 2rem; border-radius: var(--r-md); background: var(--paper); border: 1px solid var(--line); box-shadow: var(--shadow-lg);">
      <div class="modal-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem;">
        <h2 id="shortcuts-modal-title" style="font-family:'Instrument Serif',serif; font-size:1.35rem; color:var(--ink); margin:0; display:flex; align-items:center; gap:0.6rem;">
          <i class="fas fa-keyboard" style="color:var(--accent);"></i> Klavye Kısayolları
        </h2>
        <button type="button" class="btn-close" onclick="closeShortcutsModal()" aria-label="Kapat" style="background:transparent; border:none; font-size:1.4rem; cursor:pointer; color:var(--muted);">&times;</button>
      </div>
      <div class="shortcuts-list" style="display:flex; flex-direction:column; gap:0.65rem; font-size:0.86rem;">
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Kitap veya yazar ara</span>
          <div style="display:flex; gap:0.3rem;"><kbd class="shortcut-kbd">/</kbd> <span style="opacity:0.5;">veya</span> <kbd class="shortcut-kbd">k</kbd></div>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Kart Görünümü</span>
          <kbd class="shortcut-kbd">g</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Liste / Tablo Görünümü</span>
          <kbd class="shortcut-kbd">t</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>İstatistikler</span>
          <kbd class="shortcut-kbd">s</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Favorileri Aç / Kapa</span>
          <kbd class="shortcut-kbd">f</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Toplu Yönetim Modu</span>
          <kbd class="shortcut-kbd">m</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Aydınlık / Karanlık Tema</span>
          <kbd class="shortcut-kbd">d</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>PDF İçinde Ara (Okuyucu)</span>
          <kbd class="shortcut-kbd">Ctrl + F</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--line);">
          <span>Açık pencere / paneli kapat</span>
          <kbd class="shortcut-kbd">Esc</kbd>
        </div>
        <div class="shortcut-row" style="display:flex; justify-content:space-between; align-items:center; padding:0.4rem 0;">
          <span>Kısayol Kılavuzu</span>
          <kbd class="shortcut-kbd">?</kbd>
        </div>
      </div>
    </div>
  </div>

  <!-- Instant LAN Handoff (QR Code) Modal -->
  <div class="modal-overlay" id="handoff-modal" role="dialog" aria-modal="true" aria-labelledby="handoff-modal-title" tabindex="-1" style="z-index:99999;">
    <div class="modal" style="max-width:440px; text-align:center; padding:2rem; border-radius:var(--r-md); background:var(--paper); border:1px solid var(--line); box-shadow:var(--shadow-xl);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
        <h3 id="handoff-modal-title" style="font-size:1.15rem; color:var(--ink); margin:0; display:flex; align-items:center; gap:0.5rem;">
          <i class="fas fa-mobile-alt" style="color:var(--accent);"></i> Telefonda Okumaya Devam Et
        </h3>
        <button type="button" class="modal-close" style="position:static; font-size:1.3rem; border:none; background:none; cursor:pointer;" onclick="closeHandoffModal()" title="Kapat" aria-label="Kapat">&times;</button>
      </div>
      <p style="font-size:0.83rem; color:var(--muted); margin-bottom:1.2rem; line-height:1.5;">
        Telefonunuzun kamerasıyla QR kodu taratın. Aynı Wi-Fi ağındayken kitap şifre sormadan doğrudan bu sayfadan açılır.
      </p>
      <div id="handoff-qr-container" style="background:#fff; padding:1.2rem; border-radius:var(--r-sm); display:inline-block; box-shadow:var(--shadow-md); margin-bottom:1rem; min-width:210px; min-height:210px;">
        <div style="padding:3rem 1rem; color:var(--muted);"><i class="fas fa-spinner fa-spin"></i> QR Kod Üretiliyor...</div>
      </div>
      <div id="handoff-url-text" style="font-size:0.75rem; color:var(--muted); word-break:break-all; margin-bottom:0.8rem;"></div>
      <div style="font-size:0.75rem; color:var(--accent); font-weight:600;" id="handoff-timer">Kod süresi: 120 sn</div>
    </div>
  </div>

  <!-- Duplicate Books Modal -->
  <div class="modal-overlay" id="duplicates-modal" role="dialog" aria-modal="true" aria-labelledby="duplicates-modal-title" tabindex="-1" style="z-index:3600;">
    <div class="modal" style="max-width:680px; padding:2rem; border-radius:var(--r-md); background:var(--paper); border:1px solid var(--line); box-shadow:var(--shadow-xl);">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; border-bottom:1px solid var(--line); padding-bottom:0.8rem;">
        <h3 id="duplicates-modal-title" style="font-family:'Instrument Serif',serif; font-size:1.35rem; color:var(--ink); margin:0; display:flex; align-items:center; gap:0.6rem;">
          <i class="fas fa-copy" style="color:var(--accent);"></i> Mükerrer / Çift Kitap Avcısı
        </h3>
        <button type="button" class="btn-close" onclick="closeDuplicatesModal()" aria-label="Kapat" style="background:transparent; border:none; font-size:1.4rem; cursor:pointer; color:var(--muted);">&times;</button>
      </div>
      <p style="font-size:0.82rem; color:var(--muted); margin-bottom:1rem; line-height:1.4;">
        Aynı ada, yazara veya dosya boyutuna sahip mükerrer kopyalar tespit edilir. İstediğiniz kopyayı tek tıkla kütüphaneden silebilirsiniz.
      </p>
      <div id="duplicates-container" style="max-height:55vh; overflow-y:auto; display:flex; flex-direction:column; gap:1rem; padding-right:0.3rem;">
        <div style="text-align:center; padding:2rem; color:var(--muted);"><i class="fas fa-spinner fa-spin"></i> Taranıyor...</div>
      </div>
    </div>
  </div>

  <script src="{{ url_for('static', path='/js/state.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/api.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/ui_core.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/ui_logs.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/ui_chat_settings.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/ui_telegram.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/ui_workspace.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/websocket.js') }}?v=2026110804"></script>
  <script src="{{ url_for('static', path='/js/app.js') }}?v=2026110804"></script>
</body>

</html>
```


## DOSYA 4: templates/login.html (Giriş Ekranı Arayüzü, FOUC Önleme & View Transitions)

**Dosya Yolu:** `templates/login.html`

```html
<!DOCTYPE html>
<html lang="tr">

<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#f4f1eb" id="theme-color-meta">
  <title>Giriş Yap — Dijital Kütüphane</title>
  <script>
    (function () {
      try {
        var t = localStorage.getItem('kutuphane-theme') || localStorage.getItem('theme');
        if (!t) {
          t = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        document.documentElement.setAttribute('data-theme', t);
        var meta = document.getElementById('theme-color-meta');
        if (meta) meta.setAttribute('content', t === 'dark' ? '#161513' : '#f4f1eb');
      } catch (e) {}
    })();
  </script>
  <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Geist:wght@300;400;500;600&family=Geist+Mono:wght@400;500&display=swap"
    rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" integrity="sha512-Avb2QiuDEEvB4bZJYdft2mNjVShBftLdPG8FJ0V7irTLQ8Uo0qcPxh4Plq7G5tGm0rU+1SPhVotteLpBERwTkw==" crossorigin="anonymous" referrerpolicy="no-referrer">
  <link rel="stylesheet" href="{{ url_for('static', path='/css/app.css') }}?v=2026110805">
  <style>
    body {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: var(--sp-6) var(--sp-4);
      background-color: var(--paper);
      color: var(--ink);
      font-family: var(--font-ui);
      position: relative;
      box-sizing: border-box;
      transition: opacity var(--t-ui) var(--ease-out);
    }

    .login-topbar {
      position: absolute;
      top: var(--sp-6);
      left: var(--sp-6);
      right: var(--sp-6);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .login-brand-top {
      display: flex;
      flex-direction: column;
    }

    .login-brand-sub {
      font-family: var(--font-mono);
      font-size: 0.6875rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
    }

    .login-brand-title {
      font-family: var(--font-serif);
      font-size: 1.15rem;
      color: var(--ink);
    }

    .theme-toggle-btn {
      width: 36px;
      height: 36px;
      border-radius: var(--r-sm);
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
      transition: color var(--t-micro) var(--ease-out),
                  border-color var(--t-micro) var(--ease-out),
                  background-color var(--t-micro) var(--ease-out);
    }

    .theme-toggle-btn:hover {
      border-color: var(--line-strong);
      color: var(--ink);
      background: var(--paper-dark);
    }

    .login-container {
      width: 100%;
      max-width: 380px;
      margin: 0 auto;
      text-align: left;
    }

    .login-title {
      font-family: var(--font-serif);
      font-size: clamp(2.4rem, 6vw, 3.4rem);
      font-weight: 400;
      color: var(--ink);
      letter-spacing: -0.02em;
      line-height: 1.05;
      margin: 0 0 var(--sp-3) 0;
      text-wrap: balance;
    }

    .login-desc {
      font-family: var(--font-ui);
      font-size: 0.9375rem;
      color: var(--muted);
      line-height: 1.55;
      margin: 0 0 var(--sp-6) 0;
      text-wrap: pretty;
    }

    .login-form {
      display: flex;
      flex-direction: column;
      gap: var(--sp-4);
    }

    .input-wrapper {
      position: relative;
      display: flex;
      align-items: center;
    }

    .login-input {
      width: 100%;
      height: 44px;
      padding: 0 2.8rem 0 var(--sp-4);
      font-family: var(--font-ui);
      font-size: 0.9375rem;
      color: var(--ink);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--r-sm);
      box-sizing: border-box;
      outline: none;
      transition: border-color var(--t-micro) var(--ease-out),
                  box-shadow var(--t-micro) var(--ease-out);
    }

    .login-input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--line-strong);
    }

    @keyframes inputMicroShake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-3px); }
      75% { transform: translateX(3px); }
    }

    .login-input.input-error {
      border-color: var(--danger);
      animation: inputMicroShake 200ms var(--ease-out) 2;
    }

    .toggle-pwd-btn {
      position: absolute;
      right: var(--sp-3);
      background: none;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.9rem;
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color var(--t-micro) var(--ease-out);
    }

    .toggle-pwd-btn:hover {
      color: var(--ink);
    }

    .login-footer-note {
      margin-top: var(--sp-6);
      font-family: var(--font-mono);
      font-size: 0.6875rem;
      color: var(--muted);
      letter-spacing: 0.04em;
    }

    @media (prefers-reduced-motion: reduce) {
      .login-input.input-error {
        animation: none;
      }
    }
  </style>
</head>

<body>
  <div class="login-topbar">
    <div class="login-brand-top">
      <span class="login-brand-sub">DİJİTAL KOLEKSİYON</span>
      <span class="login-brand-title">Kütüphanem</span>
    </div>
    <button class="theme-toggle-btn" id="theme-toggle" onclick="toggleTheme()" title="Aydınlık / Karanlık Mod" aria-label="Aydınlık veya Karanlık Mod">
      <i class="fas fa-moon"></i>
    </button>
  </div>

  <div class="login-container">
    <h1 class="login-title">Kütüphanem</h1>
    <p class="login-desc">Kişisel dijital arşivinize erişmek için lütfen şifrenizi girin.</p>

    <form class="login-form" id="login-form" onsubmit="handleLogin(event)">
      <div class="field-group">
        <label class="field-label" for="password">Giriş Şifresi</label>
        <div class="input-wrapper">
          <input type="password" id="password" name="password" class="login-input" placeholder="Şifrenizi yazın..." autocomplete="current-password" autofocus required>
          <button type="button" class="toggle-pwd-btn" onclick="togglePasswordVisibility()" title="Şifreyi Göster/Gizle" aria-label="Şifreyi Göster veya Gizle">
            <i class="fas fa-eye" id="pwd-icon"></i>
          </button>
        </div>
      </div>

      <button type="submit" class="btn btn--primary btn--lg" id="submit-btn" style="width: 100%;">
        <span>Giriş Yap</span>
        <i class="fas fa-arrow-right"></i>
      </button>

      <div class="callout callout--danger" id="msg-box" style="display: none; margin-top: var(--sp-2);">
        <i class="fas fa-exclamation-circle" id="msg-icon"></i>
        <span id="msg-text"></span>
      </div>
    </form>

    <p class="login-footer-note">Dijital Kütüphane &bull; Güvenli Oturum</p>
  </div>

  <script>
    // Tema Yönetimi
    function updateThemeMeta(theme) {
      const color = theme === 'dark' ? '#161513' : '#f4f1eb';
      let meta = document.querySelector('meta[name="theme-color"]:not([media])');
      if (!meta) meta = document.querySelector('meta[name="theme-color"]');
      if (meta) {
        meta.setAttribute('content', color);
        if (meta.hasAttribute('media')) meta.removeAttribute('media');
      }
    }

    function applyTheme(theme) {
      document.documentElement.dataset.theme = theme;
      const icon = document.querySelector('#theme-toggle i');
      if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
      }
      updateThemeMeta(theme);
    }

    function toggleTheme() {
      const current = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      const apply = () => {
        localStorage.setItem('kutuphane-theme', next);
        applyTheme(next);
      };
      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        apply();
        return;
      }
      document.startViewTransition(apply);
    }

    // Başlangıç teması
    (function () {
      const savedTheme = localStorage.getItem('kutuphane-theme') ||
        (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      applyTheme(savedTheme);
    })();

    // Şifre Göster / Gizle
    function togglePasswordVisibility() {
      const pwdInput = document.getElementById('password');
      const pwdIcon = document.getElementById('pwd-icon');
      if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        pwdIcon.className = 'fas fa-eye-slash';
      } else {
        pwdInput.type = 'password';
        pwdIcon.className = 'fas fa-eye';
      }
    }

    // Mesaj Kutusu
    function showMessage(text, type = 'error') {
      const box = document.getElementById('msg-box');
      const msgText = document.getElementById('msg-text');
      const msgIcon = document.getElementById('msg-icon');
      box.className = type === 'warning' ? 'callout callout--warn' : 'callout callout--danger';
      msgText.textContent = text;
      msgIcon.className = type === 'warning' ? 'fas fa-shield-alt' : 'fas fa-exclamation-circle';
      box.style.display = 'flex';
    }

    function hideMessage() {
      const box = document.getElementById('msg-box');
      box.style.display = 'none';
    }

    let lockCountdownTimer = null;
    function startCountdown(seconds) {
      let remaining = seconds;
      const submitBtn = document.getElementById('submit-btn');
      submitBtn.disabled = true;

      clearInterval(lockCountdownTimer);
      showMessage(`Çok fazla hatalı deneme yapıldı. Lütfen ${remaining} saniye bekleyin.`, 'warning');

      lockCountdownTimer = setInterval(() => {
        remaining--;
        if (remaining <= 0) {
          clearInterval(lockCountdownTimer);
          lockCountdownTimer = null;
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Giriş Yap</span><i class="fas fa-arrow-right"></i>';
          hideMessage();
        } else {
          showMessage(`Çok fazla hatalı deneme yapıldı. Lütfen ${remaining} saniye bekleyin.`, 'warning');
        }
      }, 1000);
    }

    // Oturum Durumu Kontrolü (Halihazırda giriş yapılmışsa ana sayfaya yönlendir)
    async function checkAuthStatus() {
      try {
        const res = await fetch('/api/auth/status');
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated) {
            window.location.href = '/';
          } else if (data.locked) {
            showMessage('Bu cihazdan çok fazla hatalı giriş yapıldı. Lütfen bir süre bekleyin.', 'warning');
            document.getElementById('submit-btn').disabled = true;
          }
        }
      } catch (e) {
        // Ağ hatası durumunda formu açık bırak
      }
    }

    document.addEventListener('DOMContentLoaded', () => {
      void checkAuthStatus();
    });

    // Giriş Gönderme
    async function handleLogin(e) {
      e.preventDefault();
      hideMessage();

      const pwdInput = document.getElementById('password');
      const submitBtn = document.getElementById('submit-btn');
      const password = pwdInput.value;

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Giriş yapılıyor...';

      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password: password })
        });

        if (res.ok) {
          // Başarılı giriş: Sayfayı yumuşakça soluklaştırarak yönlendir
          document.body.style.transition = 'opacity var(--t-ui) var(--ease-out)';
          document.body.style.opacity = '0';
          setTimeout(() => {
            const params = new URLSearchParams(window.location.search);
            const rawNext = params.get('next');
            const nextUrl = (rawNext && rawNext.startsWith('/') && !rawNext.startsWith('//')) ? rawNext : '/';
            window.location.href = nextUrl;
          }, 280);
          return;
        }

        const data = await res.json().catch(() => ({}));
        pwdInput.classList.add('input-error');
        setTimeout(() => pwdInput.classList.remove('input-error'), 450);

        if (res.status === 429) {
          const detail = String(data.detail || '');
          let seconds = 60;
          if (detail.includes('saniye')) {
            const words = detail.split('saniye')[0].trim().split(' ');
            const parsed = Number.parseInt(words[words.length - 1], 10);
            if (!Number.isNaN(parsed)) seconds = parsed;
          }
          startCountdown(seconds);
        } else if (res.status === 401) {
          showMessage('Hatalı şifre. Lütfen tekrar deneyin.', 'error');
          pwdInput.select();
        } else {
          showMessage(data.detail || 'Giriş yapılamadı.', 'error');
        }
      } catch (err) {
        console.error('Giriş isteği sırasında hata oluştu:', err);
        showMessage('Sunucuya bağlanırken bir sorun oluştu.', 'error');
      } finally {
        if (!lockCountdownTimer) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Giriş Yap</span><i class="fas fa-arrow-right"></i>';
        }
      }
    }
  </script>
</body>

</html>
```


## DOSYA 5: static/css/style.css (Temel Stil Motoru, Mojibake Temizliği & Ölü Sınıf Tasfiyesi)

**Dosya Yolu:** `static/css/style.css`

```css

    /* Tooltip Styling */
    .tooltip-wrap {
      position: relative;
      display: inline-flex;
      align-items: center;
      margin-left: 6px;
      cursor: help;
    }

    .info-icon {
      font-size: 0.7rem;
      color: var(--sepia);
      opacity: 0.6;
      transition: opacity var(--t-micro);
    }

    .tooltip-wrap:hover .info-icon {
      opacity: 1;
      color: var(--accent);
    }

    .tooltip {
      position: absolute;
      bottom: 140%;
      background: #292825;
      color: #fff;
      padding: 0.85rem 1.1rem;
      border-radius: 6px;
      font-size: 0.72rem;
      width: 260px;
      text-align: left;
      line-height: 1.5;
      pointer-events: none;
      opacity: 0;
      visibility: hidden;
      transition: all var(--t-ui) var(--ease-out);
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
      z-index: 9999;
      font-family: 'Geist', sans-serif;
      font-weight: 400;
      border: 1px solid rgba(255,255,255,0.1);
    }

    /* Direction: Opens to the RIGHT (for left-column items) */
    .tooltip-right .tooltip {
      left: 0;
      right: auto;
      transform: translateY(10px);
    }
    .tooltip-right:hover .tooltip {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }
    .tooltip-right .tooltip::after {
      content: "";
      position: absolute;
      top: 100%;
      left: 10px;
      border-width: 5px;
      border-style: solid;
      border-color: #292825 transparent transparent transparent;
    }

    /* Direction: Opens to the LEFT (for right-column items) */
    .tooltip-left .tooltip {
      right: 0;
      left: auto;
      transform: translateY(10px);
    }
    .tooltip-left:hover .tooltip {
      opacity: 1;
      visibility: visible;
      transform: translateY(0);
    }
    .tooltip-left .tooltip::after {
      content: "";
      position: absolute;
      top: 100%;
      right: 10px;
      border-width: 5px;
      border-style: solid;
      border-color: #292825 transparent transparent transparent;
    }

    /* Drag & Drop Overlay */
    .drop-overlay {
      position: fixed;
      inset: 0;
      background: rgba(20, 14, 8, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      pointer-events: none;
      transition: opacity var(--transition-fast);
      z-index: 4000;
      backdrop-filter: blur(8px);
    }

    .drop-overlay.visible {
      opacity: 1;
      pointer-events: auto;
    }

    .drop-box {
      border: 2px dashed var(--accent-soft);
      border-radius: 8px;
      padding: 3.5rem 4rem;
      max-width: 520px;
      width: 92%;
      background: rgba(0, 0, 0, 0.2);
      color: #fff;
      text-align: center;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
      backdrop-filter: blur(24px);
    }

    .drop-box h3 {
      font-family: 'Instrument Serif', serif;
      font-size: 1.6rem;
      margin-bottom: 0.6rem;
      letter-spacing: 0.02em;
      font-weight: 400;
    }

    .drop-box p {
      font-family: 'Geist', sans-serif;
      font-size: 0.82rem;
      opacity: 0.7;
      font-weight: 300;
      letter-spacing: 0.02em;
    }

    .drop-box .pill {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(255, 255, 255, 0.08);
      padding: 0.6rem 1.2rem;
      border-radius: 999px;
      font-size: 0.8rem;
      margin-top: 1.2rem;
      border: 1px solid rgba(255, 255, 255, 0.12);
    }


    [data-theme="dark"] body {
      background-image:
        radial-gradient(ellipse at 20% 0%, rgba(160,145,120, 0.05) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 100%, rgba(130,116,94, 0.04) 0%, transparent 60%);
    }

    [data-theme="dark"] .controls {
      background: rgba(12, 10, 8, 0.8);
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }



    /* controls-panel unified styling */
    .controls-panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 60px;
      padding: 0.5rem 0.8rem;
      margin: 1.2rem auto;
      width: calc(100% - 2rem);
      max-width: 1240px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      box-shadow: 0 4px 24px var(--shadow-color), 0 1px 3px var(--shadow-color);
      transition: all var(--transition-smooth);
      position: relative;
      z-index: 1100;
    }

    [data-theme="dark"] .controls-panel {
      background: rgba(21, 18, 16, 0.6);
      border-color: rgba(255, 255, 255, 0.05);
    }

    .search-wrap {
      flex: 1.5;
      min-width: 180px;
      max-width: 360px;
      position: relative;
      background: var(--paper);
      border-radius: 6px;
      padding: 0.15rem 0.6rem;
      border: 1.5px solid var(--line);
      transition: max-width var(--t-ui) var(--ease-out), border-color var(--t-ui) var(--ease-out), box-shadow var(--t-ui) var(--ease-out), background-color var(--t-ui) var(--ease-out);
      display: flex;
      align-items: center;
      box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .search-wrap:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px var(--accent-glow), inset 0 1px 3px rgba(0, 0, 0, 0.02);
      max-width: 440px;
    }

    .search-wrap i {
      margin: 0 0.6rem;
      color: var(--muted);
      font-size: 0.85rem;
      transition: color var(--transition-fast), transform var(--t-ui) var(--ease-out);
    }

    .search-wrap:focus-within i {
      color: var(--accent);
      transform: scale(1.08);
    }

    #search-input {
      border: none;
      background: transparent;
      padding: 0.65rem 0;
      font-size: 0.88rem;
      font-family: 'Geist', sans-serif;
      font-weight: 400;
      width: 100%;
      outline: none;
      color: var(--ink);
      letter-spacing: 0.01em;
    }

    #search-input::placeholder {
      color: var(--sepia-light);
      font-weight: 300;
    }

    .control-group {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    /* Custom Dropdown Styling */
    .custom-dropdown {
      position: relative;
      min-width: 155px;
      font-family: 'Geist', sans-serif;
      user-select: none;
    }

    .dropdown-trigger {
      padding: 0.6rem 1.05rem;
      padding-right: 2.2rem;
      border: 1.5px solid var(--line);
      border-radius: 6px;
      background: var(--paper);
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--ink);
      cursor: pointer;
      transition: all var(--transition-fast);
      box-shadow: 0 1px 4px var(--shadow-color);
      display: flex;
      align-items: center;
      position: relative;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .dropdown-trigger:active {
      transform: scale(0.97);
      transition-duration: var(--t-micro);
    }

    .dropdown-trigger::after {
      content: '';
      position: absolute;
      right: 1.1rem;
      top: 50%;
      transform: translateY(-50%);
      width: 10px;
      height: 10px;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' fill='none' stroke='%238a7355' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m3 5 4 4 4-4'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: center;
      transition: transform var(--t-ui) var(--ease-out);
    }

    .custom-dropdown.open .dropdown-trigger::after {
      transform: translateY(-50%) rotate(180deg);
    }

    .custom-dropdown.open .dropdown-trigger {
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .custom-dropdown.open {
      z-index: 10;
    }

    .dropdown-menu {
      position: absolute;
      top: calc(100% + 8px);
      left: 0;
      width: 100%;
      min-width: 220px;
      background: var(--modal-bg);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      box-shadow: 0 16px 40px var(--shadow-color);
      z-index: 2000;
      opacity: 0;
      visibility: hidden;
      transform: translateY(-6px) scale(0.97);
      transform-origin: top center;
      transition: opacity var(--t-ui) var(--ease-out), transform var(--t-ui) var(--ease-out), visibility var(--t-ui);
      padding: 0.5rem;
      max-height: 350px;
      overflow-y: auto;
    }

    .custom-dropdown.open .dropdown-menu {
      opacity: 1;
      visibility: visible;
      transform: translateY(0) scale(1);
    }

    .dropdown-item {
      padding: 0.7rem 1rem;
      border-radius: var(--radius-xs);
      font-size: 0.82rem;
      color: var(--ink);
      cursor: pointer;
      transition: background var(--t-micro) var(--ease-out), color var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out);
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }

    .dropdown-item:hover {
      background: var(--accent-glow);
      color: var(--accent);
      transform: translateX(4px);
    }

    .dropdown-item:active {
      transform: translateX(4px) scale(0.98);
      transition-duration: var(--t-micro);
    }

    .dropdown-item.active {
      background: var(--accent);
      color: #fff;
    }

    [data-theme="dark"] .dropdown-trigger {
      background-color: var(--paper-dark);
      border-color: rgba(255, 255, 255, 0.08);
    }

    [data-theme="dark"] .dropdown-menu {
      background: rgba(21, 18, 16, 0.95);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .view-toggle {
      display: flex;
      background: var(--paper);
      padding: 3px;
      border-radius: 6px;
      border: 1px solid var(--line);
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    .view-btn {
      border: none;
      background: transparent;
      padding: 0.5rem 0.85rem;
      border-radius: 6px;
      font-size: 0.78rem;
      font-weight: 500;
      font-family: 'Geist', sans-serif;
      transition: all var(--transition-fast);
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 0.35rem;
      cursor: pointer;
      white-space: nowrap;
      letter-spacing: 0.01em;
      position: relative;
    }

    .view-btn:active {
      transform: scale(0.94);
      transition-duration: var(--t-micro);
    }

    .view-btn i {
      font-size: 0.8rem;
      transition: transform var(--t-ui) var(--ease-out);
    }

    .view-btn:hover i {
      transform: scale(1.12);
    }

    .view-btn:hover:not(.active) {
      color: var(--accent);
      background: rgba(110,97,76, 0.06);
    }

    .view-btn.active {
      background: var(--accent);
      color: #fff;
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    [data-theme="dark"] .view-btn.active {
      background: var(--accent);
      color: #fff;
    }

    .tag {
      padding: 0.4rem 0.9rem;
      border: 1.5px solid var(--line);
      border-radius: 6px;
      font-family: 'Geist', sans-serif;
      font-size: 0.72rem;
      letter-spacing: 0.02em;
      font-weight: 500;
      cursor: pointer;
      color: var(--muted);
      background: rgba(255, 255, 255, 0.4);
      white-space: nowrap;
      transition: all var(--transition-fast);
    }

    .tag:hover {
      border-color: var(--ink);
      color: var(--ink);
      background: var(--paper-dark);
    }

    .tag.active {
      background: var(--ink);
      border-color: var(--ink);
      color: var(--paper);
      transform: scale(1.05);
    }

    [data-theme="dark"] .tag.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }

    .manage-sep {
      width: 1px;
      height: 20px;
      background: var(--line);
      margin: 0 0.4rem;
    }

    *, *::before, *::after {
      box-sizing: border-box;
    }

    * {
      margin: 0;
      padding: 0;
      scrollbar-width: thin;
      scrollbar-color: rgba(130,116,94, 0.35) transparent;
    }

    html {
      scroll-behavior: smooth;
      overflow-x: hidden;
    }

    body {
      overflow-x: hidden;
      max-width: 100vw;
      background: var(--paper);
      color: var(--ink);
      font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 16px;
      min-height: 100vh;
      background-image:
        radial-gradient(ellipse at 15% 0%, rgba(110,97,76, 0.04) 0%, transparent 55%),
        radial-gradient(ellipse at 85% 100%, rgba(130,116,94, 0.05) 0%, transparent 55%);
      transition: background-color var(--t-ui) var(--ease-out), color var(--t-ui) var(--ease-out);
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* ── Evrensel Modal Scroll-Lock (Arka Plan Kilitlenmesi) ── */
    body.modal-open,
    body:has(.modal-overlay.open),
    body:has(.logs-modal.open) {
      overflow: hidden;
    }

    /* ── GLOBAL MODERN SLEEK SCROLLBARS ── */

    *::-webkit-scrollbar {
      width: 7px;
      height: 7px;
    }

    *::-webkit-scrollbar-track {
      background: transparent;
    }

    *::-webkit-scrollbar-thumb {
      background: rgba(130,116,94, 0.3);
      border-radius: 999px;
      border: 2px solid transparent;
      background-clip: content-box;
      transition: background var(--t-micro) var(--ease-out);
    }

    *::-webkit-scrollbar-thumb:hover {
      background: rgba(130,116,94, 0.65);
      background-clip: content-box;
    }

    *::-webkit-scrollbar-corner {
      background: transparent;
    }

    [data-theme="dark"] * {
      scrollbar-color: rgba(255, 255, 255, 0.22) transparent;
    }

    [data-theme="dark"] *::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.22);
      background-clip: content-box;
    }

    [data-theme="dark"] *::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.45);
      background-clip: content-box;
    }


    /* --- MODERN HEADER SYSTEM --- */
    header {
      position: relative;
      padding: 3.5rem 4rem 2.5rem;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      z-index: 100;
    }

    header::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent 5%, var(--accent), var(--sepia-light) 70%, transparent 95%);
      opacity: 0.7;
    }

    /* Kaydırınca yukarıdan inen Kompakt Navbar */
    .compact-nav {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      padding: 0.65rem 4rem;
      background: rgba(250, 248, 244, 0.88);
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border-bottom: 1px solid rgba(130,116,94, 0.06);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
      z-index: 2000;
      transform: translateY(-101%);
      transition: transform var(--t-ui) var(--ease-out);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    [data-theme="dark"] .compact-nav {
      background: rgba(12, 10, 8, 0.88);
      border-bottom-color: rgba(255, 255, 255, 0.04);
    }

    .compact-nav.visible {
      transform: translateY(0);
    }

    .compact-nav em {
      font-style: italic;
      color: var(--accent);
    }

    .header-inner {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 2rem;
    }

    .brand-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.3em;
      text-transform: uppercase;
      color: var(--sepia);
      margin-bottom: 0.3rem;
      font-weight: 400;
      opacity: 0.7;
    }

    h1 {
      font-family: 'Instrument Serif', serif;
      font-size: 2.8rem;
      font-weight: 400;
      line-height: 1;
      letter-spacing: -0.02em;
    }

    h1 em {
      font-style: italic;
      color: var(--accent);
    }

    .stat-pill {
      padding: 0.45rem 0.9rem;
      background: var(--accent-glow);
      border-radius: 6px;
      font-family: 'Geist Mono', monospace;
      font-size: 0.75rem;
      color: var(--accent);
      display: flex;
      align-items: center;
      border: 1px solid rgba(110,97,76, 0.08);
    }

    .btn-favorite-card {
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 10;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: rgba(0, 0, 0, 0.4);
      backdrop-filter: blur(4px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      transition: all var(--t-ui) var(--ease-spring);
    }

    .btn-favorite-card:hover {
      transform: scale(1.15);
      background: rgba(0, 0, 0, 0.6);
    }

    .btn-favorite-card i {
      transition: transform var(--t-micro) var(--ease-spring);
    }

    .btn-favorite-card:active i {
      transform: scale(0.85);
    }

    .bulk-bar {
      position: fixed;
      bottom: -100px;
      left: 50%;
      transform: translateX(-50%);
      background: var(--modal-bg);
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 0.8rem 1.5rem;
      display: flex;
      align-items: center;
      gap: 1.5rem;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      z-index: 2500;
      transition: all var(--t-ui) var(--ease-spring);
      backdrop-filter: blur(16px);
    }

    .bulk-bar.active {
      bottom: 2rem;
      transform: translateX(-50%) translateY(0);
    }

    #bulk-count {
      font-weight: 700;
      color: var(--accent);
      font-family: 'Geist Mono', monospace;
    }

    /* ── IMPORT ── */
    .import-zone {
      max-width: 1400px;
      margin: 3rem auto;
      padding: 0 4rem;
      text-align: center;
    }

    /* .import-box superseded by .zero-state-hero */

    .btn-import {
      display: inline-block;
      padding: 0.75rem 2.2rem;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 6px;
      font-family: 'Geist', sans-serif;
      font-size: 0.78rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      cursor: pointer;
      font-weight: 600;
      transition: all var(--transition-fast);
      box-shadow: 0 2px 8px var(--accent-glow);
    }

    .btn-import:hover {
      background: var(--accent-soft);
      transform: translateY(-1px);
      box-shadow: 0 4px 16px var(--accent-glow);
    }

    #file-input {
      display: none;
    }

    /* ── MAIN ── */
    main {
      max-width: 1400px;
      margin: 0 auto;
      padding: 2rem 4rem 4rem;
    }

    .result-info {
      font-family: 'Geist Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--sepia);
      margin-bottom: 1.5rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--line);
      font-weight: 400;
    }

    /* ── VIEW TRANSITIONS ── */
    @keyframes viewFadeSlide {
      from {
        opacity: 0;
        transform: translateY(14px) scale(0.995);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .view-fade-in {
      animation: viewFadeSlide var(--t-ui) var(--ease-out) both;
    }

    /* ── GRID ── */
    #grid-view {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 1.25rem;
    }

    .book-card {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      overflow: hidden;
      cursor: pointer;
      transition: transform var(--t-ui) var(--ease-out), box-shadow var(--t-ui) var(--ease-out), border-color var(--t-ui) var(--ease-out);
      display: flex;
      flex-direction: column;
      position: relative;
      box-shadow: 0 1px 3px var(--shadow-color), 0 4px 12px rgba(0, 0, 0, 0.02);
    }

    .book-card.stagger-in,
    #table-body tr.stagger-in {
      animation: fadeSlideUp var(--t-page) var(--ease-out);
      animation-delay: calc(var(--card-index, 0) * 30ms);
      will-change: transform, opacity;
    }

    .book-card:hover {
      will-change: transform;
    }

    .book-card::before {
      content: '';
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.2);
      z-index: 1;
      pointer-events: none;
      opacity: 0;
      transition: opacity var(--transition-smooth);
    }

    @keyframes fadeSlideUp {
      from {
        opacity: 0;
        transform: translateY(12px) scale(0.98);
      }

      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .book-card:hover {
      transform: translateY(-6px) scale(1.008);
      box-shadow: 0 16px 36px -6px var(--shadow-color), 0 0 0 1px var(--accent-glow);
      border-color: rgba(110,97,76, 0.35);
    }

    .book-card:active {
      transform: translateY(-2px) scale(0.99);
      transition-duration: var(--t-micro);
    }

    .book-card.selected {
      border-color: var(--accent);
      box-shadow: inset 0 0 0 2px var(--accent), 0 8px 20px var(--shadow-color);
      transform: translateY(0);
    }

    .book-card.selected::before {
      opacity: 1;
    }

    .selection-indicator {
      position: absolute;
      top: 0.8rem;
      right: 0.8rem;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      border: 2px solid #fff;
      background: rgba(0, 0, 0, 0.2);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 10;
      backdrop-filter: blur(4px);
      transition: all var(--t-micro);
    }

    .is-selection-mode .selection-indicator {
      display: flex;
    }

    .book-card.selected .selection-indicator {
      background: var(--accent);
      border-color: var(--accent);
    }

    .book-card.selected .selection-indicator::after {
      content: '\f00c';
      font-family: 'Font Awesome 5 Free', sans-serif;
      font-weight: 900;
      color: #fff;
      font-size: 0.7rem;
    }

    .book-card.uploading {
      position: relative;
      overflow: hidden;
      cursor: default;
    }

    .book-card.uploading::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(120deg, rgba(110,97,76, 0.12) 0%, rgba(237, 230, 212, 0.0) 40%, rgba(110,97,76, 0.12) 80%);
      animation: shimmer 1.8s infinite;
      pointer-events: none;
    }

    @keyframes shimmer {
      0% {
        transform: translateX(-100%);
      }

      100% {
        transform: translateX(100%);
      }
    }

    .uploading .card-cover-placeholder {
      color: #fff;
    }

    .uploading .progress-wrap {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(26, 16, 8, 0.78);
      padding: 0.35rem 0.7rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      z-index: 2;
    }

    .uploading .progress-bar {
      flex: 1;
      height: 6px;
      background: rgba(255, 255, 255, 0.18);
      border-radius: 999px;
      overflow: hidden;
    }

    .uploading .progress-bar span {
      display: block;
      height: 100%;
      width: 18%;
      background: var(--accent);
      border-radius: 999px;
      transition: width var(--t-ui) var(--ease-out);
    }

    .uploading .progress-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.62rem;
      color: rgba(255, 255, 255, 0.8);
    }

    @keyframes fadeUp {
      from {
        opacity: 0;
        transform: translateY(16px)
      }

      to {
        opacity: 1;
        transform: translateY(0)
      }
    }

    .card-cover {
      width: 100%;
      aspect-ratio: 3/4;
      overflow: hidden;
      flex-shrink: 0;
      background: linear-gradient(135deg, var(--sepia-pale), var(--paper-dark));
      position: relative;
    }

    .card-cover img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform var(--t-page) var(--ease-out);
    }

    .book-card:hover .card-cover img {
      transform: scale(1.04);
    }

    .card-cover-placeholder {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      color: var(--sepia-light);
      padding: 1rem;
      text-align: center;
    }

    .card-cover-placeholder svg {
      opacity: 0.35;
    }

    .card-cover-placeholder span {
      font-family: 'Instrument Serif', serif;
      font-size: 0.82rem;
      font-style: italic;
      color: var(--sepia);
      line-height: 1.3;
    }

    .card-cat-badge {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      background: linear-gradient(180deg, rgba(28, 23, 16, 0.6) 0%, transparent 100%);
      padding: 0.55rem 0.7rem 1.2rem;
      font-family: 'Geist Mono', monospace;
      font-size: 0.5rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: rgba(250, 248, 244, 0.85);
      font-weight: 400;
      z-index: 10;
      pointer-events: none;
      transition: opacity var(--transition-smooth);
    }

    .book-card:hover .card-cat-badge {
      opacity: 1;
    }

    .card-body {
      padding: 1rem 1.1rem 0.7rem;
      flex: 1;
    }

    .card-title {
      font-family: 'Instrument Serif', serif;
      font-size: 1.05rem;
      font-weight: 400;
      line-height: 1.3;
      margin-bottom: 0.25rem;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      min-height: 2.5em;
      color: var(--ink);
    }

    .card-author {
      font-size: 0.8rem;
      color: var(--muted);
      font-weight: 400;
      margin-bottom: 0.5rem;
      border-bottom: 1px solid var(--line);
      padding-bottom: 0.5rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .card-summary {
      font-size: 0.76rem;
      color: var(--muted);
      line-height: 1.5;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      font-weight: 300;
    }

    .card-actions {
      padding: 0.65rem 1rem;
      display: flex;
      gap: 0.5rem;
      border-top: 1px solid var(--line);
      background: rgba(250, 248, 244, 0.3);
    }

    .btn-card-read {
      flex: 1;
      padding: 0.65rem;
      border-radius: var(--radius-sm);
      background: var(--accent);
      color: #fff;
      text-decoration: none;
      font-size: 0.78rem;
      font-weight: 600;
      text-align: center;
      font-family: 'Geist', sans-serif;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.4rem;
      box-shadow: 0 2px 8px var(--accent-glow);
      border: none;
      outline: none;
      cursor: pointer;
    }

    .btn-card-read:hover {
      background: var(--accent-soft);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    .fadeOut {
      animation: fadeOutScale var(--t-ui) forwards;
    }

    @keyframes fadeOutScale {
      from {
        opacity: 1;
        transform: scale(1);
      }

      to {
        opacity: 0;
        transform: scale(0.9);
      }
    }

    .is-selection-mode .btn-card-read {
      pointer-events: none;
      opacity: 0.5;
      filter: grayscale(1);
    }

    .btn-delete-card {
      background: none;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.8rem;
      padding: 0.2rem;
      transition: background-color var(--t-ui) var(--ease-out), color var(--t-ui) var(--ease-out), border-color var(--t-ui) var(--ease-out), box-shadow var(--t-ui) var(--ease-out), color var(--t-micro);
    }

    .btn-delete-card:hover {
      color: var(--accent);
    }

    /* ── DEEP SEARCH & CHROMAGUARD ── */
    mark.deep-hl {
      background: rgba(184,134,47, 0.35);
      color: var(--ink);
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 4px;
    }

    .surface-btn {
      padding: 0.4rem 0.6rem;
      border-radius: 6px;
      transition: all var(--t-micro) var(--ease-out);
    }
    .surface-btn.active {
      background: var(--accent);
      color: #fff;
    }
    .surface-btn:hover:not(.active) {
      background: rgba(255, 255, 255, 0.1);
    }

    .network-legend {
      position: absolute;
      bottom: 1.5rem;
      left: 2rem;
      z-index: 10;
      pointer-events: none;
      font-family: 'Geist Mono', monospace;
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.8);
      backdrop-filter: blur(8px);
      padding: 0.6rem 1.2rem;
      border-radius: 6px;
      color: var(--muted);
      border: 1px solid var(--line);
      box-shadow: 0 4px 15px var(--shadow-color);
    }

    [data-theme="dark"] .network-legend {
      background: rgba(0, 0, 0, 0.6);
      color: #ccc;
      border-color: rgba(255, 255, 255, 0.1);
    }

    /* ── TABLE ── */
    #table-view {
      display: none;
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      font-family: 'Geist', sans-serif;
    }

    thead tr {
      border-bottom: 1.5px solid var(--sepia-light);
    }

    th {
      font-family: 'Geist Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--sepia);
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      transition: color var(--transition-fast);
    }

    th .th-sort-btn {
      all: unset;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      font: inherit;
      color: inherit;
      width: 100%;
    }

    th:hover {
      color: var(--accent);
    }

    th .sort-arrow {
      margin-left: 0.3rem;
      opacity: 0.4;
      transition: opacity var(--t-micro);
    }

    th.sorted .sort-arrow {
      opacity: 1;
      color: var(--accent);
    }

    tbody tr {
      border-bottom: 1px solid var(--line);
      cursor: pointer;
      transition: background var(--transition-fast), transform var(--t-micro) var(--ease-out);
      animation: fadeUp var(--t-ui) var(--ease-out) both;
      animation-delay: calc(var(--card-index, 0) * 20ms);
    }

    tbody tr:hover {
      background: var(--accent-glow);
    }

    tbody tr:active {
      transform: scale(0.995);
      transition-duration: var(--t-micro);
    }

    td {
      padding: 0.9rem 1rem;
      vertical-align: top;
    }

    .td-cover {
      width: 56px;
      padding: 0.5rem 0.5rem 0.5rem 1rem;
    }

    .td-cover img {
      width: 40px;
      height: 54px;
      object-fit: cover;
      border-radius: 3px;
      display: block;
      box-shadow: 0 3px 8px var(--shadow-color);
      transition: transform var(--t-ui);
    }

    tbody tr:hover .td-cover img {
      transform: scale(1.05);
    }

    .td-cover-empty {
      width: 40px;
      height: 54px;
      background: var(--sepia-pale);
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    td.td-title {
      font-family: 'Instrument Serif', serif;
      font-weight: 400;
      font-size: 1.05rem;
      max-width: 200px;
      color: var(--ink);
    }

    td.td-author {
      font-style: italic;
      color: var(--muted);
      font-size: 0.85rem;
    }

    td.td-cat {
      font-family: 'Geist Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.05em;
      color: var(--sepia);
    }

    td.td-summary {
      max-width: 800px;
      font-size: 0.83rem;
      color: var(--muted);
      line-height: 1.6;
    }

    .summary-text {
      display: -webkit-box;
      -webkit-line-clamp: 3;
      line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    /* ── MODAL ANIMATIONS & OVERLAY (STANDARD MOTION SYSTEM) ── */
    @keyframes modalOverlayIn {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }

    @keyframes modalOverlayOut {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }

    @keyframes modalPopIn {
      from {
        opacity: 0;
        transform: scale(0.96) translateY(8px);
      }
      to {
        opacity: 1;
        transform: scale(1) translateY(0);
      }
    }

    @keyframes modalPopOut {
      from {
        opacity: 1;
        transform: scale(1) translateY(0);
      }
      to {
        opacity: 0;
        transform: scale(0.98) translateY(4px);
      }
    }

    .modal-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(20, 14, 8, 0.72);
      z-index: 3000;
      align-items: center;
      justify-content: center;
      padding: 2rem;
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
    }

    .modal-overlay.open {
      display: flex;
      animation: modalOverlayIn var(--t-ui) var(--ease-out) forwards;
    }

    .modal-overlay.open .modal {
      animation: modalPopIn var(--t-ui) var(--ease-out) forwards;
      opacity: 1;
      pointer-events: auto;
    }

    .modal-overlay.closing {
      display: flex;
      pointer-events: none;
      animation: modalOverlayOut var(--t-micro) var(--ease-out) forwards;
    }

    .modal-overlay.closing .modal {
      pointer-events: none;
      animation: modalPopOut var(--t-micro) var(--ease-out) forwards;
    }

    .modal {
      background: var(--modal-bg);
      max-width: 960px;
      width: 100%;
      max-height: 92vh;
      overflow-y: auto;
      border-radius: 8px;
      box-shadow: 0 40px 100px rgba(0, 0, 0, 0.3);
      position: relative;
      backdrop-filter: blur(24px) saturate(180%);
      -webkit-backdrop-filter: blur(24px) saturate(180%);
      border: 1px solid rgba(255, 255, 255, 0.2);
      transform: scale(0.96) translateY(20px);
      opacity: 0;
      pointer-events: none;
      -ms-overflow-style: none;
      scrollbar-width: none;
    }

    /* ── SETTINGS MODAL SPECIALIZED DESIGN ── */
    #settings-modal {
      align-items: flex-start;
      padding-top: max(1.5rem, 4.5vh);
      padding-bottom: max(1.5rem, 4.5vh);
    }

    #settings-modal .modal {
      max-width: 680px;
      width: 100%;
      height: 740px;
      max-height: calc(100vh - 2 * max(1.5rem, 4.5vh));
      min-height: min(600px, 85vh);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      padding: 0;
      border-radius: 22px;
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.28);
      background: var(--modal-bg);
      border: 1px solid var(--line);
    }

    [data-theme="dark"] #settings-modal .modal {
      background: rgba(20, 17, 14, 0.98);
      border-color: rgba(255, 255, 255, 0.08);
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6);
    }

    .settings-header {
      padding: 1.25rem 1.6rem 1rem;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
      position: relative;
      overflow: visible;
    }

    .settings-header-left {
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }

    .settings-header-icon {
      width: 42px;
      height: 42px;
      border-radius: 6px;
      background: var(--accent-glow);
      color: var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.3rem;
      flex-shrink: 0;
      border: 1px solid rgba(110,97,76, 0.2);
    }

    .settings-header h2 {
      font-family: 'Instrument Serif', serif;
      font-size: 1.55rem;
      color: var(--ink);
      line-height: 1.2;
      margin: 0;
    }

    .settings-header p {
      font-family: 'Geist', sans-serif;
      font-size: 0.76rem;
      color: var(--muted);
      margin-top: 0.2rem;
    }

    /* Tabs Bar */
    .settings-tabs {
      display: flex;
      padding: 0.5rem 1.4rem;
      background: var(--paper-dark);
      border-bottom: 1px solid var(--line);
      gap: 0.45rem;
      flex-shrink: 0;
      overflow-x: auto;
      overflow-y: hidden;
      scrollbar-width: none;
      -ms-overflow-style: none;
    }

    .settings-tabs::-webkit-scrollbar {
      display: none;
      height: 0;
      width: 0;
    }

    [data-theme="dark"] .settings-tabs {
      background: rgba(14, 12, 10, 0.7);
    }

    .settings-tab-btn {
      background: transparent;
      border: 1px solid transparent;
      padding: 0.52rem 0.95rem;
      border-radius: 8px;
      font-family: 'Geist', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.45rem;
      transition: all var(--t-micro) var(--ease-out);
      white-space: nowrap;
      flex-shrink: 0;
    }

    .settings-tab-btn i {
      font-size: 0.85rem;
    }

    .settings-tab-btn:hover {
      color: var(--ink);
      background: rgba(130,116,94, 0.08);
    }

    .settings-tab-btn.active {
      background: var(--paper);
      color: var(--accent);
      border-color: var(--line);
      box-shadow: 0 2px 6px var(--shadow-color);
    }

    [data-theme="dark"] .settings-tab-btn.active {
      background: rgba(255, 255, 255, 0.08);
      color: var(--accent-soft);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .settings-tab-btn:active {
      transform: scale(0.96);
      transition-duration: var(--t-micro);
    }

    /* Modal Body: THE ONLY SCROLLABLE CONTAINER */
    .settings-body {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 1.4rem 1.6rem;
      box-sizing: border-box;
      -webkit-overflow-scrolling: touch;
      display: flex;
      flex-direction: column;
    }

    @keyframes tabSlideIn {
      from {
        opacity: 0;
        transform: translateX(12px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }

    .settings-tab-pane {
      display: none;
      flex-direction: column;
      gap: 1.2rem;
      width: 100%;
      box-sizing: border-box;
    }

    .settings-tab-pane.active {
      display: flex;
      animation: tabSlideIn var(--t-ui) var(--ease-out) both;
    }

    .settings-section-card {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      padding: 1rem 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.9rem;
      box-sizing: border-box;
    }

    [data-theme="dark"] .settings-section-card {
      background: rgba(255, 255, 255, 0.03);
    }

    .settings-section-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      display: block;
      font-weight: 700;
      color: var(--sepia);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-bottom: 0.2rem;
    }

    .settings-field-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .settings-field-group label {
      font-size: 0.76rem;
      font-weight: 600;
      color: var(--ink);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .settings-input, .settings-select {
      width: 100%;
      padding: 0.65rem 0.8rem;
      border: 1.5px solid var(--line);
      border-radius: var(--radius-xs);
      background: var(--paper);
      color: var(--ink);
      font-family: 'Geist', sans-serif;
      font-size: 0.84rem;
      box-sizing: border-box;
      transition: border-color var(--t-micro), box-shadow var(--t-micro);
    }

    .settings-input:focus, .settings-select:focus {
      outline: none;
      border-color: var(--accent);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    /* ═══════════ Cascade Engine & Toggle Switch ═══════════ */
    .ui-toggle-switch {
      position: relative;
      display: inline-block;
      width: 40px;
      height: 22px;
      flex-shrink: 0;
      cursor: pointer;
      user-select: none;
      margin: 0;
    }

    .ui-toggle-switch input {
      opacity: 0;
      width: 0;
      height: 0;
      position: absolute;
    }

    .ui-toggle-slider {
      position: absolute;
      inset: 0;
      background-color: var(--line);
      border-radius: 22px;
      transition: background-color var(--t-ui) var(--ease-out), box-shadow var(--t-ui) var(--ease-out);
    }

    .ui-toggle-slider::before {
      position: absolute;
      content: "";
      height: 16px;
      width: 16px;
      left: 3px;
      bottom: 3px;
      background-color: #ffffff;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
      transition: transform var(--t-ui) var(--ease-out);
    }

    .ui-toggle-switch input:checked + .ui-toggle-slider {
      background-color: var(--accent);
    }

    .ui-toggle-switch input:focus-visible + .ui-toggle-slider {
      outline: 2px solid var(--accent);
      outline-offset: 2px;
    }

    .ui-toggle-switch input:checked + .ui-toggle-slider::before {
      transform: translateX(18px);
    }

    .cascade-info-box {
      font-size: 0.73rem;
      color: var(--ink);
      line-height: 1.45;
      background: var(--paper);
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      border: 1px solid var(--line);
      border-left: 3.5px solid var(--accent);
      width: 100%;
      box-sizing: border-box;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .cascade-slot-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      background: var(--paper);
      border: 1px solid var(--line);
      padding: 0.45rem 0.65rem;
      border-radius: 8px;
      width: 100%;
      box-sizing: border-box;
      transition: border-color var(--t-micro), box-shadow var(--t-micro), background-color var(--t-micro);
    }

    .cascade-slot-row:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent-glow, rgba(234, 88, 12, 0.15));
    }

    .cascade-level-pill {
      font-size: 0.72rem;
      font-weight: 700;
      width: 82px;
      flex-shrink: 0;
      font-family: 'Geist Mono', monospace;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.3rem;
      letter-spacing: 0.02em;
      border: 1px solid transparent;
      box-sizing: border-box;
    }

    .cascade-level-pill.lvl-1 { background: #f6eee4; color: #8a4b2a; border-color: #efe3d3; }
    .cascade-level-pill.lvl-2 { background: #eef2e6; color: #3a4d2f; border-color: #e1e8d6; }
    .cascade-level-pill.lvl-3 { background: #f0ece4; color: #5a4f3f; border-color: #e8e3d8; }
    .cascade-level-pill.lvl-4 { background: #faf3e0; color: #7a5a1e; border-color: #f3e7c4; }
    .cascade-level-pill.lvl-5 { background: #f6e9e6; color: #7a2b23; border-color: #f3e1de; }

    [data-theme="dark"] .cascade-level-pill.lvl-1 { background: #2e1b10; color: #c9a47a; border-color: #6b3a20; }
    [data-theme="dark"] .cascade-level-pill.lvl-2 { background: #2f4026; color: #a3b88f; border-color: #4a6340; }
    [data-theme="dark"] .cascade-level-pill.lvl-3 { background: #2c2924; color: #b9ad96; border-color: #4a4136; }
    [data-theme="dark"] .cascade-level-pill.lvl-4 { background: #33261a; color: #e6d3a0; border-color: #5e4318; }
    [data-theme="dark"] .cascade-level-pill.lvl-5 { background: #3a1b18; color: #d9a39c; border-color: #7a2b23; }

    .cascade-model-input {
      flex: 1;
      min-width: 0;
      width: 100%;
      padding: 0.45rem 0.65rem;
      font-size: 0.8rem;
      font-family: 'Geist Mono', monospace;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--paper-dark);
      color: var(--ink);
      box-sizing: border-box;
      transition: border-color var(--t-micro), background-color var(--t-micro);
    }

    .cascade-model-input:focus {
      outline: none;
      border-color: var(--accent);
      background: var(--paper);
    }

    .cascade-role-badge {
      font-size: 0.67rem;
      font-weight: 600;
      width: 78px;
      flex-shrink: 0;
      text-align: center;
      padding: 0.25rem 0.45rem;
      border-radius: 9999px;
      letter-spacing: 0.02em;
      border: 1px solid var(--line);
      background: var(--paper-dark);
      color: var(--muted);
      white-space: nowrap;
      box-sizing: border-box;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }

    .cascade-role-badge.role-primary {
      background: #f6eee4;
      color: #8a4b2a;
      border-color: #e3cdb2;
      font-weight: 700;
    }
    .cascade-role-badge.role-thinking {
      background: #f0ece4;
      color: #5a4f3f;
      border-color: #d8d1c3;
    }
    .cascade-role-badge.role-flagship {
      background: #eeeae2;
      color: #4a4740;
      border-color: #ddd5c4;
    }
    .cascade-role-badge.role-standard {
      background: #faf3e0;
      color: #7a5a1e;
      border-color: #e6d3a0;
    }
    .cascade-role-badge.role-fallback {
      background: #f4f1eb;
      color: #4a4740;
      border-color: #cfc9bd;
    }

    [data-theme="dark"] .cascade-role-badge.role-primary {
      background: #2e1b10;
      color: #c9a47a;
      border-color: #6b3a20;
    }
    [data-theme="dark"] .cascade-role-badge.role-thinking {
      background: #2c2924;
      color: #b9ad96;
      border-color: #4a4136;
    }
    [data-theme="dark"] .cascade-role-badge.role-flagship {
      background: #2c2a25;
      color: #c2b8a4;
      border-color: #292825;
    }
    [data-theme="dark"] .cascade-role-badge.role-standard {
      background: #33261a;
      color: #e6d3a0;
      border-color: #5e4318;
    }
    [data-theme="dark"] .cascade-role-badge.role-fallback {
      background: #292825;
      color: #cfc9bd;
      border-color: #4a4740;
    }

    .cascade-flow-connector {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0.15rem 0;
      position: relative;
      margin: 0.05rem 0;
    }

    .cascade-flow-line {
      flex: 1;
      height: 1px;
      border-top: 1px dashed var(--line);
      opacity: 0.7;
    }

    .cascade-flow-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.18rem 0.65rem;
      font-size: 0.64rem;
      font-family: 'Geist Mono', monospace;
      color: var(--muted);
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: 9999px;
      margin: 0 0.5rem;
      letter-spacing: 0.02em;
      user-select: none;
    }

    .cascade-flow-pill i {
      font-size: 0.58rem;
      color: var(--accent);
    }

    .cascade-footer-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 0.4rem;
      padding-top: 0.6rem;
      border-top: 1px dashed var(--line);
      width: 100%;
      box-sizing: border-box;
    }

    .cascade-footer-note {
      font-size: 0.7rem;
      color: var(--muted);
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }

    .btn-cascade-reset {
      background: var(--paper);
      border: 1px solid var(--line);
      color: var(--ink);
      font-size: 0.72rem;
      font-weight: 600;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all var(--t-micro) var(--ease-out);
    }

    .btn-cascade-reset:hover {
      background: var(--paper-dark);
      border-color: var(--accent);
      color: var(--accent);
      transform: translateY(-1px);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }

    .btn-cascade-reset:active {
      transform: translateY(0);
    }

    /* Modal Footer */
    .settings-footer {
      padding: 1rem 1.6rem;
      background: var(--paper);
      border-top: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.75rem;
      flex-shrink: 0;
      box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.03);
      overflow: visible;
    }

    [data-theme="dark"] .settings-footer {
      background: rgba(18, 15, 13, 0.96);
    }

    .btn-settings-cancel {
      padding: 0.7rem 1.2rem;
      border-radius: var(--radius-xs);
      border: 1px solid var(--line);
      background: transparent;
      color: var(--muted);
      font-family: 'Geist', sans-serif;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--t-micro);
    }

    .btn-settings-cancel:hover {
      background: var(--paper-dark);
      color: var(--ink);
    }

    .btn-settings-save {
      padding: 0.7rem 1.5rem;
      border-radius: var(--radius-xs);
      border: none;
      background: var(--accent);
      color: #fff;
      font-family: 'Geist', sans-serif;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      transition: all var(--t-micro);
      box-shadow: 0 4px 14px rgba(110,97,76, 0.25);
    }

    .btn-settings-save:hover {
      background: var(--accent-soft);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(110,97,76, 0.35);
    }

    .btn-settings-save:active {
      transform: translateY(0);
    }

    [data-theme="dark"] .modal {
      border-color: rgba(255, 255, 255, 0.05);
    }

    .modal::-webkit-scrollbar {
      display: none;
    }

    .modal-top {
      height: 6px;
      min-height: 6px;
      max-height: 6px;
      padding: 0;
      margin: 0;
      flex-shrink: 0;
      background: linear-gradient(90deg, var(--accent), var(--sepia-light));
    }

    .modal-close {
      position: absolute;
      top: 1.5rem;
      right: 1.5rem;
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--muted);
      font-size: 1.1rem;
      transition: all var(--transition-fast);
      z-index: 10;
    }

    .modal-close:hover {
      color: var(--accent);
      background: var(--paper);
      transform: scale(1.1);
      box-shadow: 0 4px 12px var(--shadow-color);
    }

    .modal-layout {
      display: flex;
      gap: 2.5rem;
      padding: 3rem;
      align-items: flex-start;
    }

    .modal-cover-wrap {
      flex-shrink: 0;
    }

    .modal-cover-wrap img {
      width: 180px;
      height: 240px;
      object-fit: cover;
      border-radius: 8px;
      box-shadow: -8px 12px 24px rgba(0, 0, 0, 0.25);
      display: block;
    }

    .modal-cover-empty {
      width: 180px;
      height: 240px;
      background: linear-gradient(135deg, var(--sepia-pale), var(--paper-dark));
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 8px 24px var(--shadow-color);
    }

    .modal-info {
      flex: 1;
      min-width: 0;
    }

    .modal-cat {
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--accent);
      margin-bottom: 0.8rem;
      font-weight: 600;
    }

    .modal-title {
      font-family: 'Instrument Serif', serif;
      font-size: 2.2rem;
      font-weight: 400;
      line-height: 1.1;
      margin-bottom: 0.5rem;
      color: var(--ink);
    }

    .modal-author {
      font-size: 1.05rem;
      font-family: 'Geist', sans-serif;
      color: var(--sepia);
      margin-bottom: 1.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--line);
      font-weight: 500;
    }

    .modal-section-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.6rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 0.6rem;
      margin-top: 1.2rem;
      font-weight: 600;
    }

    .modal-summary {
      font-size: 0.95rem;
      line-height: 1.7;
      color: var(--ink);
      font-family: 'Geist', sans-serif;
      font-weight: 300;
    }

    .modal-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
      margin-top: 1.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--line);
    }

    .meta-chip {
      display: inline-flex;
      align-items: center;
      padding: 0.4rem 1rem;
      background: rgba(130,116,94, 0.06);
      border-radius: 999px;
      font-family: 'Geist Mono', monospace;
      font-size: 0.65rem;
      color: var(--sepia);
      letter-spacing: 0.04em;
      border: 1px solid var(--line);
      transition: all var(--transition-fast);
    }

    .meta-chip:hover {
      border-color: var(--accent);
      color: var(--accent);
      background: var(--accent-glow);
      transform: translateY(-1px);
    }

    .modal-keywords {
      display: flex;
      flex-wrap: wrap;
      gap: 0.6rem;
      margin-top: 0.8rem;
      font-size: 0.85rem;
      color: var(--muted);
      font-style: italic;
    }

    /* Modal Action Buttons */
    .btn-modal-primary {
      background: var(--accent);
      color: #fff;
      border-radius: var(--radius-sm);
      padding: 0.9rem;
      border: none;
      outline: none;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: 'Geist Mono', monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      text-decoration: none;
      font-weight: 600;
      transition: all var(--transition-fast);
      box-shadow: 0 4px 15px rgba(110,97,76, 0.2);
    }

    .btn-modal-primary i {
      transition: transform var(--t-ui) var(--ease-out);
    }

    .btn-modal-primary:hover {
      background: var(--accent-soft);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(110,97,76, 0.3);
    }

    .btn-modal-primary:hover i {
      transform: translateX(3px);
    }

    .btn-modal-primary:active {
      transform: translateY(0) scale(0.96);
      transition-duration: var(--t-micro);
    }

    .btn-modal-fav {
      background: transparent;
      color: var(--accent);
      border: 1.5px solid var(--accent);
      border-radius: var(--radius-sm);
      padding: 0.9rem;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: 'Geist Mono', monospace;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      font-weight: 600;
      transition: all var(--transition-fast);
    }

    .btn-modal-fav:hover {
      background: var(--accent-glow);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px var(--shadow-color);
    }

    .btn-modal-fav:active {
      transform: translateY(0) scale(0.96);
      transition-duration: var(--t-micro);
    }

    .btn-modal-fav.is-fav {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }

    .btn-modal-secondary {
      background: rgba(130,116,94, 0.06);
      color: var(--sepia);
      border: 1.5px solid transparent;
      border-radius: var(--radius-sm);
      padding: 0.9rem;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all var(--transition-fast);
    }

    .btn-modal-secondary:hover {
      background: var(--paper-dark);
      color: var(--ink);
      border-color: var(--line);
      transform: translateY(-1px);
    }

    .btn-modal-secondary:active {
      transform: translateY(0) scale(0.96);
      transition-duration: var(--t-micro);
    }

    .btn-modal-danger {
      background: transparent;
      color: #b0473c;
      border: 1.5px solid transparent;
      border-radius: var(--radius-sm);
      padding: 0.9rem;
      cursor: pointer;
      font-size: 0.85rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: all var(--transition-fast);
    }

    .btn-modal-danger:hover {
      background: rgba(176,71,60, 0.08);
      border-color: rgba(176,71,60, 0.2);
    }

    .btn-modal-danger:active {
      transform: scale(0.96);
      transition-duration: var(--t-micro);
    }

    /* Edit Form Elements */
    .modal-edit-input,
    .modal-edit-textarea {
      width: 100%;
      padding: 1rem;
      border: 1.5px solid var(--line);
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.5);
      color: var(--ink);
      font-family: 'Geist', sans-serif;
      font-size: 0.95rem;
      transition: all var(--transition-fast);
      outline: none;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
    }

    [data-theme="dark"] .modal-edit-input,
    [data-theme="dark"] .modal-edit-textarea {
      background: rgba(0, 0, 0, 0.2);
      border-color: rgba(255, 255, 255, 0.08);
    }

    .modal-edit-input:focus,
    .modal-edit-textarea:focus {
      border-color: var(--accent);
      background: var(--paper);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .btn-modal-save {
      background: var(--accent);
      color: #fff;
      border-radius: var(--radius-sm);
      padding: 1rem;
      border: none;
      cursor: pointer;
      font-size: 0.9rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 600;
      letter-spacing: 0.05em;
      transition: all var(--transition-fast);
      box-shadow: 0 4px 15px rgba(110,97,76, 0.2);
    }

    .btn-modal-save:hover {
      background: var(--accent-soft);
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(110,97,76, 0.3);
    }

    .btn-modal-save:active {
      transform: translateY(0) scale(0.96);
      transition-duration: var(--t-micro);
    }

    .header-stats {
      display: flex;
      align-items: center;
      gap: 1.2rem;
    }

    .theme-toggle,
    #settings-btn {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 50%;
      width: 44px;
      height: 44px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--muted);
      transition: all var(--t-ui) var(--ease-spring);
      box-shadow: 0 4px 15px var(--shadow-color);
      font-size: 1.15rem;
      position: relative;
      overflow: hidden;
      padding: 0;
    }

    .theme-toggle:hover,
    #settings-btn:hover {
      border-color: var(--line-strong);
      color: var(--ink);
      background: var(--paper-dark);
    }

    #settings-btn i,
    .theme-toggle[onclick*="openSettings"] i {
      display: inline-block;
      transform-origin: center center;
      transition: transform var(--t-page) var(--ease-out);
    }

    #settings-btn:hover i,
    .theme-toggle[onclick*="openSettings"]:hover i {
      transform: rotate(90deg);
    }

    #settings-btn:active,
    .theme-toggle:active {
      transform: scale(0.92);
      transition-duration: var(--t-micro);
    }

    /* ── EMPTY ── */
    .empty {
      text-align: center;
      padding: 5rem 2rem;
    }

    .empty svg {
      opacity: 0.25;
      margin-bottom: 1rem;
      color: var(--sepia-light);
    }

    .empty h3 {
      font-family: 'Instrument Serif', serif;
      font-weight: 400;
      font-size: 1.4rem;
      margin-bottom: 0.5rem;
      color: var(--sepia);
    }

    /* –– SCROLL TOP BTN –– */
    #scroll-top-btn {
      position: fixed;
      right: 2rem;
      bottom: 0;
      margin-bottom: 200px;
      width: 50px;
      height: 50px;
      border-radius: 50%;
      background: #fff;
      color: var(--accent);
      border: 2px solid var(--accent);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2040;
      opacity: 0;
      transform: translateY(20px) scale(0.8);
      transition: all var(--t-page) var(--ease-spring);
      box-shadow: 0 8px 25px var(--shadow-color);
      pointer-events: none;
      --shift-y: 0px;
    }

    #scroll-top-btn.visible {
      opacity: 1;
      transform: translateY(var(--shift-y)) scale(1);
      pointer-events: auto;
    }

    #scroll-top-btn:hover {
      background: var(--accent);
      color: #fff;
      transform: scale(1.1);
    }

    #scroll-top-btn:active {
      transform: scale(0.9);
    }

    /* ══════════════════════════════════════════════════════════════
     DESKTOP / LAPTOP / TABLET RESPONSIVE BREAKPOINTS
     ══════════════════════════════════════════════════════════════ */
    @media(max-width:1200px) {
      header {
        padding: 3rem 2.5rem 2rem;
      }
      .controls-panel {
        border-radius: 36px;
        padding: 0.65rem 0.9rem;
        gap: 0.55rem;
      }
      .search-wrap {
        flex: 1 1 200px;
        min-width: 160px;
      }
      .custom-dropdown {
        min-width: 140px;
      }
      .dropdown-trigger {
        padding: 0.55rem 0.9rem;
        padding-right: 2rem;
        font-size: 0.78rem;
      }
      .view-btn {
        padding: 0.45rem 0.75rem;
        font-size: 0.76rem;
      }
    }

    @media(max-width:1040px) {
      header {
        padding: 2.5rem 1.8rem 1.8rem;
      }
      .controls-panel {
        border-radius: 28px;
        padding: 0.75rem 1rem;
        row-gap: 0.75rem;
        column-gap: 0.6rem;
        justify-content: center;
      }
      .search-wrap {
        flex: 1 1 240px;
        max-width: none;
      }
      .dropdowns-group {
        flex: 1 1 auto;
        justify-content: flex-end;
      }
      .view-toggle {
        flex: 0 0 auto;
      }
      .actions-group {
        flex: 0 0 auto;
      }
    }

    /* ═══════════════════════════════════════════════════════════
     MOBILE RESPONSIVE — TABLET (≤768px)
     ═══════════════════════════════════════════════════════════ */
    @media(max-width:768px) {

      /* — Header — */
      header {
        padding: 2rem 1.2rem 1.5rem;
      }

      header .header-inner {
        flex-direction: column;
        align-items: flex-start;
        gap: 1rem;
      }

      h1 {
        font-size: 2rem;
      }

      .brand-label {
        font-size: 0.55rem;
      }

      /* — Compact Nav — */
      .compact-nav {
        padding: 0.5rem 1.2rem;
      }

      /* — Controls Panel — */
      .controls-panel {
        flex-wrap: wrap;
        justify-content: center;
        padding: 0.6rem;
        margin: 0.8rem auto;
        width: calc(100% - 1.6rem);
        border-radius: 8px;
        gap: 0.4rem;
      }

      .search-wrap {
        width: 100%;
        max-width: none;
        flex: none;
        order: -1;
      }

      .control-group {
        width: 100%;
        justify-content: center;
        flex-wrap: wrap;
      }

      .custom-dropdown {
        flex: 1;
        min-width: 130px;
      }

      .dropdown-trigger {
        padding: 0.5rem 1.8rem 0.5rem 0.8rem;
        font-size: 0.75rem;
        border-radius: 6px;
      }

      .dropdown-menu {
        min-width: 100%;
        border-radius: 6px;
      }

      .view-toggle {
        width: auto;
        flex: none;
      }

      .view-btn {
        padding: 0.45rem 0.7rem;
        font-size: 0.72rem;
      }

      .view-btn span.btn-label {
        display: none;
      }

      .manage-sep {
        height: 14px;
      }

      /* — Import Zone — */
      .import-zone {
        padding: 0 1.2rem;
        margin: 2rem auto;
      }

      /* .import-box superseded */

      /* — Main Content — */
      main {
        padding: 1.5rem 1.2rem 2rem;
      }

      /* — Grid — */
      #grid-view {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 0.8rem;
      }

      .card-body {
        padding: 0.75rem 0.8rem 0.5rem;
      }

      .card-title {
        font-size: 0.92rem;
        min-height: 2.2em;
      }

      .card-author {
        font-size: 0.72rem;
      }

      .card-summary {
        font-size: 0.7rem;
        -webkit-line-clamp: 2;
        line-clamp: 2;
      }

      .card-actions {
        padding: 0.5rem 0.7rem;
      }

      /* — Table — */
      #table-view {
        font-size: 0.8rem;
      }

      td.td-summary {
        display: none;
      }

      .td-cover {
        width: 44px;
      }

      .td-cover img {
        width: 32px;
        height: 44px;
      }

      /* — Modal — */
      .modal-overlay {
        padding: 0.5rem;
      }

      .modal {
        max-width: 98vw;
        margin: 0;
        max-height: 96vh;
        border-radius: 8px;
      }

      .modal-layout {
        flex-direction: column;
        padding: 1.8rem 1.5rem;
        gap: 1.5rem;
      }

      .modal-cover-wrap {
        width: 100%;
        display: flex;
        justify-content: center;
      }

      .modal-cover-wrap img {
        width: 140px;
        height: 187px;
      }

      .modal-cover-empty {
        width: 140px;
        height: 187px;
      }

      .modal-title {
        font-size: 1.5rem;
      }

      .modal-author {
        font-size: 0.95rem;
      }

      .modal-summary {
        font-size: 0.88rem;
      }

      .modal-actions {
        flex-direction: row;
        flex-wrap: wrap;
      }

      .modal-actions>* {
        flex: 1;
        min-width: 100px;
        font-size: 0.78rem;
        padding: 0.75rem;
      }

      .modal-meta {
        gap: 0.4rem;
      }

      .meta-chip {
        font-size: 0.6rem;
        padding: 0.3rem 0.7rem;
      }

      .modal-close {
        top: 1rem;
        right: 1rem;
        width: 32px;
        height: 32px;
      }

      /* — Chat Panel — */
      #chat-panel {
        width: calc(100vw - 1.5rem);
        right: 0.75rem;
        left: 0.75rem;
        bottom: 0.75rem;
        border-radius: 8px;
      }

      .chat-body {
        height: 280px;
        padding: 1rem;
        font-size: 0.84rem;
      }

      .chat-msg {
        max-width: 90%;
        padding: 0.65rem 0.85rem;
        font-size: 0.84rem;
      }

    @keyframes opsCenterIn {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* — Ops Center — */
    #ops-center {
      position: fixed;
      left: 2rem;
      bottom: 5.75rem;
      width: min(380px, calc(100vw - 32px));
      height: min(560px, calc(100vh - 120px));
      max-height: min(560px, calc(100vh - 120px));
      background: var(--surface);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid var(--line);
      border-radius: var(--r-md);
      box-shadow: var(--shadow-lg);
      z-index: 2100;
      display: flex;
      flex-direction: column;
      font-family: var(--font-mono);
      transform: translateY(8px);
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
      overflow: hidden;
      transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out), visibility var(--t-micro);
    }

    #ops-center.active {
      transform: translateY(0);
      opacity: 1;
      visibility: visible;
      pointer-events: auto;
      animation: opsCenterIn var(--t-ui) var(--ease-out);
    }

    .ops-header {
      background: var(--surface-hover);
      padding: 0.85rem 1.1rem;
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
    }

    .ops-title-wrap {
      display: flex;
      align-items: center;
      gap: 0.55rem;
    }

    .ops-header h3 {
      font-size: 0.75rem;
      color: var(--ink);
      letter-spacing: 0.12em;
      margin: 0;
      font-weight: 700;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .ops-header h3 i {
      color: var(--ok);
    }

    .ops-live-pulse {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
      transition: all var(--t-ui);
    }

    .ops-live-pulse.pulse-idle {
      background: var(--ok);
      box-shadow: 0 0 8px var(--ok);
    }

    .ops-live-pulse.pulse-active {
      background: var(--warn);
      box-shadow: 0 0 12px var(--warn);
      animation: pulseBeacon 1.2s infinite ease-in-out;
    }

    @keyframes pulseBeacon {
      0% { transform: scale(0.9); opacity: 0.8; }
      50% { transform: scale(1.3); opacity: 1; filter: drop-shadow(0 0 6px var(--warn)); }
      100% { transform: scale(0.9); opacity: 0.8; }
    }

    .ops-count-pill {
      font-size: 0.62rem;
      padding: 2px 7px;
      border-radius: var(--r-sm);
      font-weight: 600;
      background: var(--ok-bg);
      color: var(--ok);
      border: 1px solid var(--ok);
    }

    .ops-count-pill.is-active {
      background: var(--warn-bg);
      color: var(--warn);
      border-color: var(--warn);
      animation: pulseBeacon 1.5s infinite;
    }

    .ops-header-actions {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .ops-btn-icon, .ops-btn-close {
      background: none;
      border: none;
      color: var(--muted);
      cursor: pointer;
      padding: 0.35rem 0.45rem;
      border-radius: var(--r-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      transition: all var(--t-micro);
    }

    .ops-btn-icon:hover, .ops-btn-close:hover {
      color: var(--ink);
      background: var(--paper-dark);
    }

    .ops-archive-btn {
      background: var(--surface);
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: var(--r-sm);
      padding: 0.3rem 0.65rem;
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      transition: all var(--t-micro);
    }

    .ops-archive-btn:hover {
      background: var(--surface-hover);
      color: var(--ink);
      border-color: var(--line-strong);
    }

    /* Tabs Bar */
    .ops-tabs {
      display: flex;
      background: var(--paper-dark);
      border-bottom: 1px solid var(--line);
      padding: 0.3rem 0.6rem;
      gap: 0.4rem;
    }

    .ops-tab-btn {
      background: none;
      border: none;
      color: var(--muted);
      font-family: var(--font-mono);
      font-size: 0.68rem;
      font-weight: 600;
      padding: 0.35rem 0.6rem;
      border-radius: var(--r-sm);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      transition: all var(--t-micro);
    }

    .ops-tab-btn:hover {
      color: var(--ink);
      background: var(--surface);
    }

    .ops-tab-btn.active {
      color: var(--ok);
      background: var(--ok-bg);
      border: 1px solid var(--ok);
    }

    .ops-tab-badge {
      font-size: 0.6rem;
      padding: 1px 5px;
      border-radius: var(--r-xs);
      background: var(--line-subtle);
      color: inherit;
    }

    .ops-tab-badge.active-tag {
      background: var(--warn-bg);
      color: var(--warn);
    }

    /* System Diagnostics Strip */
    .ops-system-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.45rem 1rem;
      background: var(--paper-dark);
      border-bottom: 1px solid var(--line);
      font-size: 0.64rem;
      color: var(--muted);
    }

    .ops-strip-item {
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    .ops-strip-item i {
      color: var(--accent);
    }

    .ops-strip-item span {
      color: var(--muted);
      font-weight: 500;
    }

    /* Body */
    .ops-body {
      flex: 1;
      padding: 0.85rem;
      overflow-y: auto;
      color: var(--ink);
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      scrollbar-width: thin;
      scrollbar-color: var(--line-strong) transparent;
    }

    .ops-body::-webkit-scrollbar {
      width: 4px;
    }
    .ops-body::-webkit-scrollbar-thumb {
      background: var(--line);
      border-radius: 4px;
    }

    .ops-section-divider {
      font-size: 0.62rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin: 0.4rem 0 0.1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .ops-section-divider::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--line);
    }

    /* Task Card */
    .ops-task-card {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: var(--r-sm);
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.55rem;
      transition: all var(--t-ui) var(--ease-out);
    }

    .ops-task-card:hover {
      border-color: var(--line-strong);
      background: var(--surface-hover);
    }

    .ops-task-card.is-active {
      border-color: var(--ok);
      background: var(--surface-hover);
      box-shadow: 0 0 16px var(--ok-bg);
    }

    .ops-task-card.is-success {
      border-color: var(--line);
    }

    .ops-task-card.is-error {
      border-color: var(--danger);
      background: var(--danger-bg);
    }

    /* Card Header */
    .ops-card-header {
      display: flex;
      align-items: flex-start;
      gap: 0.6rem;
    }

    .ops-file-badge {
      width: 28px;
      height: 28px;
      border-radius: var(--r-sm);
      background: var(--paper-dark);
      color: var(--muted);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.8rem;
      flex-shrink: 0;
    }

    .ops-file-badge.success {
      background: var(--ok-bg);
      color: var(--ok);
    }

    .ops-file-badge.error {
      background: var(--danger-bg);
      color: var(--danger);
    }

    .ops-file-info {
      flex: 1;
      min-width: 0;
    }

    .ops-file-title {
      font-size: 0.74rem;
      font-weight: 600;
      color: var(--ink);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.3;
    }

    .ops-file-title.success {
      color: var(--ok);
    }

    .ops-file-title.error {
      color: var(--danger);
    }

    .ops-file-meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.4rem;
      margin-top: 0.2rem;
      font-size: 0.64rem;
      color: var(--muted);
    }

    .ops-phase-tag {
      color: var(--accent);
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
    }

    .ops-author-tag, .ops-cat-tag {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      color: var(--muted);
      padding: 1px 6px;
      border-radius: var(--r-xs);
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      white-space: nowrap;
    }

    .ops-card-pct {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--ok);
      font-variant-numeric: tabular-nums;
    }

    .ops-status-pill {
      font-size: 0.62rem;
      padding: 2px 7px;
      border-radius: var(--r-xs);
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
    }

    .ops-status-pill.success {
      background: var(--ok-bg);
      color: var(--ok);
      border: 1px solid var(--ok);
    }

    .ops-status-pill.error {
      background: var(--danger-bg);
      color: var(--danger);
      border: 1px solid var(--danger);
    }

    /* Stepper */
    .ops-stepper {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.25rem 0.2rem;
      margin: 0.1rem 0;
    }

    .ops-step {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      font-size: 0.58rem;
      color: var(--muted);
    }

    .ops-step .step-num {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--paper-dark);
      border: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.58rem;
      font-weight: 700;
      transition: all var(--t-ui);
    }

    .ops-step.active .step-num {
      background: var(--ok);
      color: var(--surface);
      border-color: var(--ok);
      box-shadow: 0 0 10px var(--ok-bg);
      animation: pulseBeacon 1.2s infinite;
    }

    .ops-step.active {
      color: var(--ok);
      font-weight: 600;
    }

    .ops-step.done .step-num {
      background: var(--ok-bg);
      color: var(--ok);
      border-color: var(--ok);
    }

    .ops-step.done {
      color: var(--muted);
    }

    .ops-step-line {
      flex: 1;
      height: 2px;
      background: var(--line);
      margin: 0 4px -10px 4px;
      transition: background var(--t-ui);
    }

    .ops-step-line.done {
      background: var(--ok);
    }

    /* Progress Bar */
    .ops-progress-track {
      height: 6px;
      background: var(--paper-dark);
      border-radius: var(--r-xs);
      overflow: hidden;
      border: 1px solid var(--line);
    }

    .ops-progress-bar {
      height: 100%;
      border-radius: var(--r-xs);
      background: var(--ok);
      transition: width var(--t-ui) var(--ease-out);
    }

    .ops-progress-bar.animated {
      background: linear-gradient(90deg, var(--ok) 0%, var(--accent) 50%, var(--ok) 100%);
      background-size: 200% 100%;
      animation: shimmerMove 2s linear infinite;
      box-shadow: 0 0 12px var(--ok-bg);
    }

    /* Status line */
    .ops-status-line {
      font-size: 0.68rem;
      color: var(--ink);
      display: flex;
      align-items: center;
      gap: 0.4rem;
      background: var(--paper-dark);
      padding: 0.4rem 0.6rem;
      border-radius: var(--r-xs);
      border-left: 2px solid var(--ok);
    }

    .ops-pulse-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--ok);
      box-shadow: 0 0 6px var(--ok);
      animation: pulseBeacon 1s infinite;
      flex-shrink: 0;
    }

    .ops-status-text {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .ops-terminal-cursor {
      color: var(--ok);
      font-weight: 700;
      animation: blinkCursor var(--t-page) infinite;
    }

    /* Log Details Dropdown */
    .ops-log-details {
      font-size: 0.64rem;
      color: var(--muted);
      border-top: 1px solid var(--line);
      padding-top: 0.35rem;
    }

    .ops-log-details summary {
      cursor: pointer;
      user-select: none;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      color: var(--muted);
      font-weight: 600;
      margin-bottom: 0.3rem;
      outline: none;
    }

    .ops-log-details summary:hover {
      color: var(--ink);
    }

    .ops-log-stream {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: var(--r-xs);
      padding: 0.4rem 0.55rem;
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      max-height: 120px;
      overflow-y: auto;
    }

    .ops-stream-line {
      display: flex;
      align-items: flex-start;
      gap: 0.35rem;
      font-size: 0.62rem;
      line-height: 1.4;
      color: var(--ink);
    }

    .ops-stream-line .line-time {
      color: var(--muted);
      flex-shrink: 0;
    }

    .ops-stream-line .line-dot {
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: var(--ok);
      margin-top: 5px;
      flex-shrink: 0;
    }

    .ops-stream-line.error .line-dot {
      background: var(--danger);
    }

    /* Action row in completed card */
    .ops-result-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding-top: 0.3rem;
      border-top: 1px solid var(--line);
      font-size: 0.65rem;
    }

    .ops-result-filename {
      color: var(--muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 1;
    }

    .ops-btn-action {
      background: var(--ok-bg);
      border: 1px solid var(--ok);
      color: var(--ok);
      border-radius: var(--r-xs);
      padding: 0.25rem 0.6rem;
      font-family: inherit;
      font-size: 0.65rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      transition: all var(--t-micro);
    }

    .ops-btn-action:hover {
      background: var(--ok);
      color: var(--surface);
    }

    .ops-error-box {
      font-size: 0.66rem;
      color: var(--danger);
      background: var(--danger-bg);
      border: 1px solid var(--danger);
      border-radius: var(--r-xs);
      padding: 0.4rem 0.6rem;
      line-height: 1.4;
    }

    /* Empty State */
    .ops-empty-state {
      padding: 1.5rem 0.8rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.7rem;
    }

    .ops-empty-radar {
      position: relative;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      border: 1.5px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--paper-dark);
      margin-bottom: 0.1rem;
    }

    .ops-radar-sweep {
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border-top: 2px solid var(--accent);
      animation: radarSweep 2.5s linear infinite;
    }

    .ops-empty-icon {
      font-size: 1.3rem;
      color: var(--accent);
    }

    .ops-empty-title {
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--ink);
      letter-spacing: 0.03em;
    }

    .ops-empty-desc {
      font-size: 0.68rem;
      color: var(--muted);
      line-height: 1.4;
      max-width: 280px;
    }

    .ops-empty-specs {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: var(--r-xs);
      padding: 0.55rem 0.75rem;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      font-size: 0.64rem;
      color: var(--muted);
      text-align: left;
    }

    .ops-empty-specs .spec-item {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .ops-empty-specs strong {
      color: var(--ink);
      font-weight: 600;
    }

    .ops-empty-actions {
      display: flex;
      gap: 0.45rem;
      width: 100%;
      margin-top: 0.2rem;
    }

    .ops-quick-action {
      flex: 1;
      background: var(--surface);
      border: 1px solid var(--line);
      color: var(--ink);
      border-radius: var(--r-sm);
      padding: 0.45rem 0.35rem;
      font-family: inherit;
      font-size: 0.65rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      transition: all var(--t-micro);
    }

    .ops-quick-action:hover {
      background: var(--ok-bg);
      color: var(--ok);
      border-color: var(--ok);
    }

    /* Floating button active state */
    @keyframes opsPulse {
      0% { box-shadow: 0 0 0 0 var(--ok); }
      70% { box-shadow: 0 0 0 16px rgba(0, 0, 0, 0); }
      100% { box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
    }

    .ops-toggle.is-processing {
      border-color: var(--ok);
      animation: opsPulse 2s infinite ease-in-out;
    }

    .ops-toggle.is-processing i {
      animation: opsSpin 4s linear infinite;
      color: var(--ok);
    }

    /* ═══════════ SİSTEM & İŞLEM LOGLARI (MODERN LOG CENTER) ═══════════ */
    .logs-modal {
      position: fixed;
      inset: 0;
      background: rgba(8, 10, 15, 0.82);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 3000;
      backdrop-filter: blur(14px) saturate(180%);
      transition: opacity var(--t-micro) var(--ease-out);
      padding: 1.2rem;
    }

    .logs-modal.open {
      display: flex;
    }

    .logs-panel {
      width: min(1200px, 96vw);
      height: 88vh;
      max-height: 88vh;
      overflow: hidden;
      background: var(--terminal-bg);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      box-shadow: 0 32px 80px -10px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255, 255, 255, 0.06);
      color: var(--terminal-ink);
      font-family: 'Geist Mono', monospace;
      display: flex;
      flex-direction: column;
    }

    /* Header Bar */
    .logs-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.9rem 1.4rem;
      border-bottom: 1px solid var(--terminal-line);
      background: var(--terminal-surface);
      backdrop-filter: blur(10px);
      gap: 1rem;
      flex-wrap: wrap;
    }

    .logs-header-left {
      display: flex;
      align-items: center;
      gap: 0.9rem;
    }

    .logs-title-wrap {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .logs-title-icon {
      color: #9db58a;
      font-size: 1rem;
      filter: drop-shadow(0 0 6px rgba(157,181,138, 0.5));
    }

    .logs-header h4 {
      font-size: 0.85rem;
      letter-spacing: 0.12em;
      margin: 0;
      color: var(--terminal-ink);
      text-transform: uppercase;
      font-weight: 700;
    }

    /* Live Status Pill */
    .logs-status-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.65rem;
      font-weight: 600;
      padding: 3px 9px;
      border-radius: 999px;
      background: #1f1e1b;
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #8f8a80;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .logs-status-pill .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #9db58a;
      box-shadow: 0 0 8px #9db58a;
      animation: logPulse 2s infinite;
    }

    .logs-status-pill.status-reconnecting {
      border-color: rgba(184,134,47, 0.4);
      color: #b8862f;
    }
    .logs-status-pill.status-reconnecting .status-dot {
      background: #b8862f;
      box-shadow: 0 0 8px #b8862f;
    }

    .logs-status-pill.status-offline {
      border-color: rgba(176,71,60, 0.4);
      color: #b0473c;
    }
    .logs-status-pill.status-offline .status-dot {
      background: #b0473c;
      box-shadow: 0 0 8px #b0473c;
      animation: none;
    }

    @keyframes logPulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.25); opacity: 0.6; }
    }

    /* Header Actions */
    .logs-header-actions {
      display: flex;
      align-items: center;
      gap: 0.45rem;
    }

    .logs-action-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      background: #1f1e1b;
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: #cfc9bd;
      padding: 0.4rem 0.75rem;
      border-radius: 8px;
      font-size: 0.72rem;
      font-family: 'Geist Mono', monospace;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
    }

    .logs-action-btn:hover {
      background: #272521;
      color: #fff;
      border-color: rgba(255, 255, 255, 0.22);
    }

    .logs-action-btn.logs-btn-danger:hover {
      background: #3a1b18;
      border-color: #b0473c;
      color: #d9a39c;
    }

    .logs-action-btn.paused {
      background: #33261a;
      border-color: #b8862f;
      color: #e6d3a0;
    }

    .logs-close {
      background: #1f1e1b;
      border: 1px solid rgba(255, 255, 255, 0.1);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      color: #8f8a80;
      cursor: pointer;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--t-micro) var(--ease-out);
      margin-left: 0.3rem;
    }

    .logs-close:hover {
      background: #3a1b18;
      border-color: #b0473c;
      color: #fff;
    }

    /* Body Layout */
    .logs-body {
      display: grid;
      grid-template-columns: 240px 1fr;
      min-height: 0;
      flex: 1;
      background: var(--terminal-bg);
    }

    /* Sidebar */
    .logs-sidebar {
      border-right: 1px solid rgba(255, 255, 255, 0.07);
      padding: 1rem 0.8rem;
      background: rgba(22,21,18, 0.85);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }

    .logs-section-title {
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: #6f6a60;
      margin: 0.4rem 0 0.6rem 0.4rem;
      font-weight: 700;
    }

    .logs-filter-btn {
      width: 100%;
      text-align: left;
      padding: 0.55rem 0.75rem;
      border-radius: 8px;
      border: 1px solid transparent;
      background: transparent;
      color: #8f8a80;
      font-size: 0.74rem;
      font-family: 'Geist Mono', monospace;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
    }

    .logs-filter-btn span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .logs-filter-btn small {
      font-size: 0.65rem;
      padding: 2px 7px;
      border-radius: 6px;
      background: #1f1e1b;
      color: #8f8a80;
      font-weight: 600;
      min-width: 22px;
      text-align: center;
      transition: all var(--t-micro) var(--ease-out);
    }

    .logs-filter-btn:hover:not(.active) {
      background: #272521;
      color: var(--terminal-ink);
    }

    .logs-filter-btn.active {
      border-color: rgba(157,181,138, 0.4);
      background: #2f4026;
      color: #e4ecd9;
      font-weight: 600;
    }

    .logs-filter-btn.active small {
      background: #1f2a19;
      color: #a3b88f;
    }

    /* Content Area */
    .logs-content-area {
      display: flex;
      flex-direction: column;
      min-height: 0;
      overflow: hidden;
      background: var(--terminal-bg);
    }

    /* Toolbar: Search + Level Filters */
    .logs-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.75rem 1.2rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      background: rgba(14, 18, 26, 0.6);
      gap: 0.8rem;
      flex-wrap: wrap;
    }

    .logs-search-wrap {
      flex: 1;
      min-width: 240px;
      position: relative;
      display: flex;
      align-items: center;
    }

    .logs-search-icon {
      position: absolute;
      left: 10px;
      font-size: 0.75rem;
      color: #6f6a60;
      pointer-events: none;
    }

    .logs-search-wrap input {
      width: 100%;
      padding: 0.45rem 2rem 0.45rem 2rem;
      background: #1f1e1b;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: var(--terminal-ink);
      font-family: 'Geist Mono', monospace;
      font-size: 0.75rem;
      outline: none;
      transition: all var(--t-micro) var(--ease-out);
    }

    .logs-search-wrap input:focus {
      border-color: #9db58a;
      background: rgba(157,181,138, 0.03);
      box-shadow: 0 0 0 2px rgba(157,181,138, 0.15);
    }

    #logs-search-clear {
      position: absolute;
      right: 8px;
      background: none;
      border: none;
      color: #6f6a60;
      cursor: pointer;
      font-size: 0.75rem;
      padding: 4px;
    }
    #logs-search-clear:hover { color: var(--terminal-ink); }

    /* Level Filters */
    .logs-level-filters {
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }

    .logs-level-btn {
      padding: 0.25rem 0.55rem;
      border-radius: 6px;
      font-size: 0.65rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 600;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: #1f1e1b;
      color: #8f8a80;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
    }

    .logs-level-btn .lvl-indicator {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .logs-level-btn.lvl-error .lvl-indicator { background: #b0473c; }
    .logs-level-btn.lvl-warning .lvl-indicator { background: #c9a04a; }
    .logs-level-btn.lvl-info .lvl-indicator { background: #5f7a4f; }
    .logs-level-btn.lvl-debug .lvl-indicator { background: #9a8d77; }

    .logs-level-btn small {
      font-size: 0.6rem;
      opacity: 0.75;
    }

    .logs-level-btn:hover:not(.active) {
      background: #272521;
      color: #fff;
    }

    .logs-level-btn.active {
      border-color: rgba(255, 255, 255, 0.3);
      background: #272521;
      color: #fff;
    }

    .logs-level-btn.active.lvl-error {
      background: #3a1b18;
      border-color: #b0473c;
      color: #ecd0cb;
    }

    .logs-level-btn.active.lvl-warning {
      background: #33261a;
      border-color: #c9a04a;
      color: #f3e7c4;
    }

    .logs-level-btn.active.lvl-info {
      background: #2f4026;
      border-color: #5f7a4f;
      color: #e1e8d6;
    }

    /* Main Logs Feed */
    .logs-main {
      flex: 1;
      padding: 0.9rem 1.2rem;
      overflow-y: auto;
      scroll-behavior: smooth;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .logs-main::-webkit-scrollbar {
      width: 6px;
    }
    .logs-main::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.12);
      border-radius: 4px;
    }
    .logs-main::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.22);
    }

    /* Log Entry Card */
    .log-card {
      background: rgba(31,30,27, 0.65);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-left: 3px solid #5f7a4f;
      border-radius: 8px;
      padding: 0.65rem 0.9rem;
      transition: background var(--t-micro) var(--ease-out), border-color var(--t-micro) var(--ease-out);
    }

    .log-card:hover {
      background: rgba(24, 30, 42, 0.85);
      border-color: rgba(255, 255, 255, 0.12);
    }

    .log-card.lvl-error {
      border-left-color: #b0473c;
      background: rgba(176,71,60, 0.05);
    }
    .log-card.lvl-warning {
      border-left-color: #c9a04a;
      background: rgba(251, 191, 36, 0.04);
    }
    .log-card.lvl-info {
      border-left-color: #5f7a4f;
    }
    .log-card.lvl-debug {
      border-left-color: #9a8d77;
    }

    .log-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.35rem;
      font-size: 0.68rem;
    }

    .log-card-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .log-time {
      color: #6f6a60;
      font-size: 0.68rem;
    }

    .log-level-tag {
      font-size: 0.6rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .log-level-tag.ERROR { background: #3a1b18; color: #d9a39c; }
    .log-level-tag.WARNING { background: #33261a; color: #e8dca0; }
    .log-level-tag.INFO { background: #2f4026; color: #a3b88f; }
    .log-level-tag.DEBUG { background: #2c2a25; color: #c2b8a4; }

    .log-cat-tag {
      font-size: 0.62rem;
      color: #8f8a80;
      background: #1f1e1b;
      padding: 1px 6px;
      border-radius: 4px;
    }

    .log-card-tools {
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    .log-tool-btn {
      background: none;
      border: 1px solid transparent;
      color: #6f6a60;
      font-size: 0.68rem;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
      transition: all var(--t-micro) var(--ease-out);
      display: flex;
      align-items: center;
      gap: 3px;
    }

    .log-tool-btn:hover {
      background: #272521;
      color: var(--terminal-ink);
    }

    .log-message {
      font-family: 'Geist', sans-serif;
      font-size: 0.82rem;
      line-height: 1.45;
      color: var(--terminal-ink);
      overflow-wrap: break-word;
    }

    .log-match {
      background: #5e4318;
      color: #e8dca0;
      padding: 0 2px;
      border-radius: 2px;
    }

    /* Context Drawer */
    .log-context-box {
      margin-top: 0.5rem;
      padding: 0.5rem 0.75rem;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 6px;
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      display: none;
    }

    .log-context-box.open {
      display: block;
    }

    .log-ctx-item {
      margin-bottom: 0.25rem;
      display: flex;
      gap: 0.4rem;
      overflow-wrap: break-word;
    }
    .log-ctx-item:last-child { margin-bottom: 0; }
    .log-ctx-key { color: #9a8d77; font-weight: 600; flex-shrink: 0; }
    .log-ctx-val { color: #cfc9bd; }

    /* Footer Bar */
    .logs-footer {
      padding: 0.65rem 1.2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
      background: #1b1a17;
      font-size: 0.72rem;
      color: #8f8a80;
    }

    .logs-footer-left, .logs-footer-right {
      display: flex;
      align-items: center;
      gap: 0.8rem;
    }

    .logs-autoscroll-toggle {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      cursor: pointer;
      user-select: none;
      color: #8f8a80;
    }

    .logs-autoscroll-toggle input {
      accent-color: #9db58a;
      cursor: pointer;
    }

    .logs-paused-banner {
      color: #b8862f;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.3rem;
      animation: logPulse 1.5s infinite;
    }

    .logs-nav-btn {
      background: #1f1e1b;
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #8f8a80;
      border-radius: 6px;
      padding: 3px 8px;
      cursor: pointer;
      font-size: 0.7rem;
      transition: all var(--t-micro) var(--ease-out);
    }
    .logs-nav-btn:hover { background: #272521; color: #fff; }

    /* Header Nav Badge for Errors */
    .header-logs-badge {
      position: absolute;
      top: 4px;
      right: 4px;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #b0473c;
      box-shadow: 0 0 6px #b0473c;
      animation: logPulse 1.5s infinite;
    }


    /* — Floating Controls — */


    .ops-badge {
      position: absolute;
      top: -5px;
      right: -5px;
      background: #b0473c;
      color: #fff;
      font-size: 0.65rem;
      padding: 2px 6px;
      border-radius: 6px;
      display: none;
    }

    #chat-panel.active~#scroll-top-btn.visible {
      --shift-y: -435px;
    }

    /* ══════════ PDF READER ══════════ */


    /* ══════════ STATS DASHBOARD ══════════ */
    #stats-view {
      display: none;
      padding: 2rem 0;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 1.5rem;
      text-align: center;
      transition: all var(--transition-smooth);
      box-shadow: 0 2px 8px var(--shadow-color);
    }

    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px var(--shadow-color);
    }

    .stat-card-value {
      font-family: 'Instrument Serif', serif;
      font-size: 2.4rem;
      font-weight: 400;
      color: var(--accent);
      line-height: 1;
    }

    .stat-card-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--muted);
      margin-top: 0.6rem;
    }

    .stats-charts {
      display: grid;
      grid-template-columns: 1fr 1.5fr;
      gap: 2rem;
      align-items: start;
    }

    .stats-chart-box {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 2rem;
      box-shadow: 0 2px 8px var(--shadow-color);
    }

    .stats-chart-title {
      font-family: 'Geist Mono', monospace;
      font-size: 0.7rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 1.5rem;
      font-weight: 600;
    }

    .donut-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 2rem;
      flex-wrap: wrap;
    }

    .donut-legend {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-family: 'Geist', sans-serif;
      font-size: 0.78rem;
    }

    .donut-legend-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--ink);
    }

    .donut-legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .donut-legend-count {
      font-family: 'Geist Mono', monospace;
      font-size: 0.7rem;
      color: var(--muted);
      margin-left: auto;
      padding-left: 1rem;
    }

    .bar-chart {
      display: flex;
      align-items: flex-end;
      gap: 0.8rem;
      height: 180px;
      padding-top: 1rem;
    }

    .bar-col {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.4rem;
      height: 100%;
      justify-content: flex-end;
    }

    .bar-fill {
      width: 100%;
      min-width: 28px;
      background: linear-gradient(180deg, var(--accent), var(--accent-soft));
      border-radius: 6px 6px 0 0;
      transition: height var(--t-page) var(--ease-out);
      box-shadow: 0 -2px 10px var(--accent-glow);
    }

    .bar-label {
      font-family: 'Geist Mono', monospace;
      font-size: 0.6rem;
      color: var(--muted);
      text-align: center;
    }

    .bar-value {
      font-family: 'Geist Mono', monospace;
      font-size: 0.7rem;
      color: var(--accent);
      font-weight: 600;
    }

    @media(max-width:768px) {
      .stats-charts {
        grid-template-columns: 1fr;
      }

      .stats-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    /* ══════════ COVER UPLOAD ══════════ */
    .btn-cover-upload {
      position: relative;
      overflow: hidden;
    }

    .btn-cover-upload input[type="file"] {
      position: absolute;
      inset: 0;
      opacity: 0;
      cursor: pointer;
    }

    /* ══════════ DRAG SORT ══════════ */
    .book-card.dragging {
      opacity: 0.4;
      transform: scale(0.95);
    }

    .book-card.drag-over {
      border: 2px dashed var(--accent);
      background: var(--accent-glow);
    }

    /* ═════════════════════════════════════════════════════════════
       Premium Workspace Reader Overlay (PDF + AI Chat)
       ═════════════════════════════════════════════════════════════ */
    /* ═════════════════════════════════════════════════════════════
       Premium Workspace Reader Overlay (PDF + AI Chat)
       ═════════════════════════════════════════════════════════════ */
    .workspace-reader {
      position: fixed;
      inset: 0;
      z-index: 5000;
      display: flex;
      flex-direction: column;
      background: var(--paper);
      transform: translateY(100%);
      transition: transform var(--t-page) var(--ease-out);
      overflow: hidden;
      color: var(--ink);
    }

    .workspace-reader.open {
      transform: translateY(0);
    }

    .workspace-header {
      height: 64px;
      padding: 0 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(250, 248, 244, 0.85);
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      border-bottom: 1px solid rgba(110,97,76, 0.1);
      flex-shrink: 0;
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.03);
      z-index: 5010;
    }

    [data-theme="dark"] .workspace-header {
      background: rgba(22, 19, 16, 0.85);
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .workspace-header-left {
      display: flex;
      align-items: center;
      gap: 1.2rem;
      min-width: 0;
      flex: 1;
    }

    .btn-workspace-back {
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      background: var(--paper);
      color: var(--muted);
      border: 1px solid var(--line);
      padding: 0.55rem 1.2rem;
      border-radius: 6px;
      font-family: 'Geist', sans-serif;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--t-ui) var(--ease-out);
      white-space: nowrap;
    }

    .btn-workspace-back:hover {
      color: var(--accent);
      border-color: var(--accent);
      transform: translateX(-3px);
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    .workspace-book-divider {
      color: var(--line);
      font-size: 1.2rem;
      font-weight: 300;
    }

    .workspace-book-meta {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .workspace-book-cat {
      font-family: 'Geist Mono', monospace;
      font-size: 0.58rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--sepia);
      font-weight: 600;
    }

    .workspace-book-title {
      font-family: 'Instrument Serif', serif;
      font-size: 1.15rem;
      font-weight: 400;
      color: var(--ink);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 1.2;
    }

    .workspace-header-right {
      display: flex;
      align-items: center;
      gap: 1.5rem;
    }

    .workspace-status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: #eef2e6;
      border: 1px solid rgba(95,122,79, 0.2);
      color: #3a4d2f;
      padding: 0.4rem 0.9rem;
      border-radius: 6px;
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      font-weight: 600;
      box-shadow: 0 2px 10px rgba(95,122,79, 0.05);
    }

    .workspace-status-badge::before {
      content: '';
      display: inline-block;
      width: 6px;
      height: 6px;
      background: #5f7a4f;
      border-radius: 50%;
      box-shadow: 0 0 8px #5f7a4f;
      animation: wsStatusPulse 2s infinite;
    }

    @keyframes wsStatusPulse {
      0% { box-shadow: 0 0 0 0 rgba(95,122,79, 0.7); }
      70% { box-shadow: 0 0 0 5px rgba(95,122,79, 0); }
      100% { box-shadow: 0 0 0 0 rgba(95,122,79, 0); }
    }

    .workspace-content {
      display: flex;
      flex-direction: row;
      flex: 1;
      overflow: hidden;
      position: relative;
    }

    .workspace-pdf-pane {
      flex: 1;
      min-width: 320px;
      height: 100%;
      background: var(--paper-dark);
      position: relative;
    }

    .workspace-pdf-iframe {
      width: 100%;
      height: 100%;
      border: none;
      background: var(--paper-dark);
    }

    /* Resize handle */
    .workspace-resize-handle {
      width: 8px;
      background: transparent;
      cursor: col-resize;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
      position: relative;
      user-select: none;
      border-left: 1px solid var(--line);
      border-right: 1px solid var(--line);
      transition: all var(--t-ui) var(--ease-out);
    }

    .workspace-resize-handle:hover,
    .workspace-resize-handle.active {
      background: rgba(110,97,76, 0.04);
      border-left-color: var(--accent);
      border-right-color: var(--accent);
    }

    .resize-dot {
      width: 2px;
      height: 28px;
      background: var(--accent);
      border-radius: 4px;
      opacity: 0.3;
      transition: all var(--t-micro) var(--ease-out);
    }

    .workspace-resize-handle:hover .resize-dot,
    .workspace-resize-handle.active .resize-dot {
      opacity: 1;
      height: 40px;
      box-shadow: 0 0 8px var(--accent);
    }

    /* Chat Panel Styles */
    .workspace-chat-pane {
      width: auto;
      min-width: 300px;
      max-width: 800px;
      height: 100%;
      background: var(--paper-dark);
      border-left: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      flex-shrink: 1;
      z-index: 50;
    }

    /* Book Loading Banner */
    .workspace-book-banner {
      display: flex;
      align-items: center;
      gap: 0.8rem;
      padding: 0.75rem 1.2rem;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      flex-shrink: 0;
      transition: all var(--t-ui) var(--ease-out);
      position: relative;
      overflow: hidden;
    }

    .workspace-book-banner::before {
      content: '';
      position: absolute;
      inset: 0;
      opacity: 0;
      transition: opacity var(--t-ui);
    }

    .workspace-book-banner.loading {
      background: linear-gradient(90deg, var(--paper), var(--accent-glow), var(--paper));
      background-size: 200% 100%;
      animation: bannerShimmer 1.5s ease infinite;
    }

    @keyframes bannerShimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    .workspace-book-banner.loaded {
      background: rgba(95,122,79, 0.06);
      border-bottom-color: rgba(95,122,79, 0.2);
      cursor: default;
    }

    .workspace-book-banner.error {
      background: rgba(176,71,60, 0.06);
      border-bottom-color: rgba(176,71,60, 0.2);
    }

    .banner-icon {
      width: 34px;
      height: 34px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 0.9rem;
      background: var(--accent-glow);
      color: var(--accent);
      transition: all var(--t-ui) var(--ease-out);
    }

    .workspace-book-banner.loaded .banner-icon {
      background: #eef2e6;
      color: #3a4d2f;
    }

    .workspace-book-banner.error .banner-icon {
      background: #f6e9e6;
      color: #7a2b23;
    }

    .banner-content {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
    }

    .banner-title {
      font-family: 'Geist', sans-serif;
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--ink);
      line-height: 1.3;
    }

    .workspace-book-banner.loaded .banner-title {
      color: #5f7a4f;
    }

    .workspace-book-banner.error .banner-title {
      color: #b0473c;
    }

    .banner-subtitle {
      font-family: 'Geist', sans-serif;
      font-size: 0.65rem;
      color: var(--muted);
      line-height: 1.3;
    }

    .btn-banner-load {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.45rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--accent);
      background: var(--accent);
      color: #fff;
      font-family: 'Geist', sans-serif;
      font-size: 0.72rem;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
      white-space: nowrap;
      flex-shrink: 0;
    }

    .btn-banner-load:hover:not(:disabled) {
      background: var(--accent-soft);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px var(--accent-glow);
    }

    .btn-banner-load:active:not(:disabled) {
      transform: scale(0.97);
    }

    .btn-banner-load:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .workspace-book-banner.loaded .btn-banner-load {
      background: #eef2e6;
      border-color: rgba(95,122,79, 0.3);
      color: #3a4d2f;
      cursor: default;
    }

    /* Compact Workspace Book Banner */
    .workspace-book-banner.compact {
      border: 1.5px solid var(--line);
      border-bottom: 1.5px solid var(--line);
      border-radius: 6px;
      padding: 0.35rem 0.8rem 0.35rem 0.5rem;
      background: var(--paper);
      margin: 0;
      cursor: pointer;
      height: 44px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      min-width: 280px;
    }
    .workspace-book-banner.compact.loading {
      background: linear-gradient(90deg, var(--paper), var(--accent-glow), var(--paper));
      background-size: 200% 100%;
      animation: bannerShimmer 1.5s ease infinite;
    }
    .workspace-book-banner.compact.loaded {
      background: rgba(95,122,79, 0.05);
      border-color: rgba(95,122,79, 0.2);
    }
    .workspace-book-banner.compact.error {
      background: rgba(176,71,60, 0.05);
      border-color: rgba(176,71,60, 0.2);
    }
    .workspace-book-banner.compact .banner-icon {
      width: 28px;
      height: 28px;
      font-size: 0.75rem;
      border-radius: 50%;
    }
    .workspace-book-banner.compact .banner-content {
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .workspace-book-banner.compact .banner-title {
      font-size: 0.74rem;
    }
    .workspace-book-banner.compact .banner-subtitle {
      font-size: 0.58rem;
      max-width: 170px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .workspace-book-banner.compact .btn-banner-load {
      padding: 0.3rem 0.8rem;
      font-size: 0.65rem;
      border-radius: 30px;
      height: 26px;
    }

    /* Offline Status Badge */
    .workspace-status-badge.offline {
      background: #f6e9e6;
      border: 1px solid rgba(176,71,60, 0.2);
      color: #7a2b23;
      box-shadow: 0 2px 10px rgba(176,71,60, 0.05);
    }
    .workspace-status-badge.offline::before {
      background: #b0473c;
      box-shadow: 0 0 8px #b0473c;
      animation: wsStatusPulseOffline 2s infinite;
    }
    @keyframes wsStatusPulseOffline {
      0% { box-shadow: 0 0 0 0 rgba(176,71,60, 0.7); }
      70% { box-shadow: 0 0 0 5px rgba(176,71,60, 0); }
      100% { box-shadow: 0 0 0 0 rgba(176,71,60, 0); }
    }

    .workspace-chat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.85rem 1.4rem;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      flex-shrink: 0;
    }

    .workspace-chat-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--ink);
      font-family: 'Geist', sans-serif;
    }

    .btn-copy-chat {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: var(--paper-dark);
      color: var(--sepia);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.35rem 0.85rem;
      font-size: 0.76rem;
      font-weight: 600;
      font-family: 'Geist', sans-serif;
      cursor: pointer;
      transition: all var(--t-ui) var(--ease-out);
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      position: relative;
      overflow: hidden;
    }

    .btn-copy-chat:hover {
      background: var(--accent-glow);
      border-color: var(--accent);
      color: var(--accent);
      transform: translateY(-1px);
    }

    .btn-copy-chat:active {
      transform: translateY(0);
    }

    .btn-copy-chat.copied {
      background: #eef2e6;
      border-color: rgba(95,122,79, 0.4);
      color: #3a4d2f;
      animation: copySuccessPulse var(--t-ui) var(--ease-out);
    }

    .btn-copy-chat .btn-copy-text {
      transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out);
    }

    @keyframes copySuccessPulse {
      0% { transform: scale(0.95); }
      50% { transform: scale(1.06); }
      100% { transform: scale(1); }
    }

    .workspace-chat-messages {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: 1.8rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      scroll-behavior: smooth;
      background-image: radial-gradient(var(--line) 1px, transparent 1px);
      background-size: 18px 18px;
      background-color: var(--paper-dark);
    }

    /* Custom Scrollbar for Chat Messages */
    .workspace-chat-messages::-webkit-scrollbar {
      width: 6px;
    }

    .workspace-chat-messages::-webkit-scrollbar-track {
      background: transparent;
    }

    .workspace-chat-messages::-webkit-scrollbar-thumb {
      background: var(--line);
      border-radius: 6px;
    }

    .workspace-chat-messages::-webkit-scrollbar-thumb:hover {
      background: var(--sepia-light);
    }

    /* Workspace Chat Bubble */
    .workspace-chat-messages .chat-msg {
      display: flex;
      gap: 0.95rem;
      max-width: 85%;
      margin: 0;
      animation: wsFadeIn var(--t-ui) var(--ease-out) forwards;
      opacity: 0;
      transform: translateY(10px);
    }

    @keyframes wsFadeIn {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .workspace-chat-messages .chat-msg.chat-ai {
      align-self: flex-start;
      flex-direction: row;
    }

    .workspace-chat-messages .chat-msg.chat-user {
      align-self: flex-end;
      flex-direction: row-reverse;
      max-width: 80%;
    }

    .chat-msg-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 0.8rem;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
      transition: transform var(--t-micro) var(--ease-out);
    }

    .chat-msg-avatar:hover {
      transform: scale(1.08);
    }

    .chat-ai .chat-msg-avatar {
      background: var(--accent-glow);
      border: 1px solid rgba(110,97,76, 0.12);
      color: var(--accent);
    }

    .chat-ai .chat-msg-avatar i {
      animation: sparkleRotate 6s linear infinite;
    }

    @keyframes sparkleRotate {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .chat-user .chat-msg-avatar {
      background: var(--ink);
      color: var(--paper);
    }

    .chat-msg-text {
      padding: 0.95rem 1.25rem;
      font-family: 'Geist', sans-serif;
      font-size: 0.88rem;
      line-height: 1.6;
      overflow-wrap: break-word;
    }

    .chat-ai .chat-msg-text {
      background: var(--paper);
      color: var(--ink);
      border: 1px solid var(--line);
      border-radius: 18px 18px 18px 4px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }

    .chat-user .chat-msg-text {
      background: var(--accent);
      color: #fff;
      border-radius: 18px 18px 4px 18px;
      box-shadow: 0 4px 14px var(--accent-glow);
    }

    /* Markdown styling inside chat messages */
    .chat-msg-text strong {
      font-weight: 700;
      color: var(--accent);
    }

    .chat-user .chat-msg-text strong {
      color: #fff;
      text-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }

    .source-capsule {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(110,97,76, 0.08);
      border: 1px solid rgba(110,97,76, 0.2);
      color: var(--accent);
      padding: 0.2rem 0.65rem;
      border-radius: 6px;
      font-size: 0.72rem;
      margin-top: 0.5rem;
      font-family: 'Geist Mono', monospace;
      transition: all var(--t-micro) var(--ease-out);
    }

    .source-capsule:hover {
      background: rgba(110,97,76, 0.15);
      border-color: var(--accent);
    }

    .chat-user .source-capsule {
      background: #8a4b2a;
      border-color: rgba(255, 255, 255, 0.3);
      color: #fff;
    }

    .chat-list-item {
      margin-left: 1.2rem;
      margin-top: 0.35rem;
      list-style-type: square;
    }

    .chat-list-number {
      margin-top: 0.4rem;
      padding-left: 0.5rem;
      display: flex;
      align-items: flex-start;
      gap: 0.4rem;
    }

    .list-num {
      font-family: 'Geist Mono', monospace;
      color: var(--accent);
      font-weight: 700;
      font-size: 0.78rem;
    }

    .chat-user .list-num {
      color: #fff;
    }

    /* Typing indicators */
    .chat-typing-indicator {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 0.4rem 0.2rem;
    }

    .chat-typing-indicator span {
      width: 5px;
      height: 5px;
      background: var(--muted);
      border-radius: 50%;
      opacity: 0.4;
      animation: wsBounce 1.4s infinite ease-in-out both;
    }

    .chat-typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .chat-typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes wsBounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1.0); }
    }

    /* Input area style */
    .workspace-chat-input-area {
      padding: 1.25rem 1.5rem;
      background: rgba(250, 248, 244, 0.95);
      backdrop-filter: blur(10px);
      border-top: 1px solid var(--line);
      flex-shrink: 0;
    }

    [data-theme="dark"] .workspace-chat-input-area {
      background: rgba(22, 19, 16, 0.95);
    }

    .workspace-input-wrapper {
      position: relative;
      display: flex;
      align-items: flex-end;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.4rem 0.5rem;
      transition: all var(--t-ui) var(--ease-out);
      box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }

    .workspace-input-wrapper:focus-within {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px var(--accent-glow);
    }

    #workspace-chat-input {
      flex: 1;
      border: none;
      background: transparent;
      padding: 0.5rem 0.8rem;
      font-family: 'Geist', sans-serif;
      font-size: 0.86rem;
      line-height: 1.5;
      color: var(--ink);
      outline: none;
      resize: none;
      max-height: 140px;
      min-height: 36px;
    }

    #workspace-chat-input::placeholder {
      color: var(--sepia-light);
      font-weight: 300;
    }

    .btn-workspace-send {
      width: 36px;
      height: 36px;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
      flex-shrink: 0;
      box-shadow: 0 2px 6px var(--accent-glow);
    }

    .btn-workspace-send:hover:not(:disabled) {
      background: var(--accent-soft);
      transform: scale(1.05);
    }

    .btn-workspace-send:active:not(:disabled) {
      transform: scale(0.95);
    }

    .btn-workspace-send:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .workspace-input-tip {
      font-size: 0.65rem;
      color: var(--muted);
      opacity: 0.5;
      text-align: center;
      margin-top: 0.5rem;
    }

    /* --- Custom PDF.js Viewer UI Styles --- */
    .custom-pdf-viewer {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      background: var(--paper-dark);
      position: relative;
      overflow: hidden;
      font-family: 'Geist', sans-serif;
    }

    .pdf-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 1rem;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
      z-index: 10;
      flex-shrink: 0;
    }

    [data-theme="dark"] .pdf-toolbar {
      background: rgba(18, 16, 14, 0.95);
      border-bottom-color: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(10px);
    }

    .pdf-toolbar-group {
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }

    .pdf-toolbar-divider {
      width: 1px;
      height: 20px;
      background: var(--line);
      margin: 0 0.5rem;
    }

    .pdf-btn {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--ink);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
      font-size: 0.85rem;
    }

    .pdf-btn:hover {
      background: var(--line);
      color: var(--accent);
    }

    .pdf-btn.text-btn {
      width: auto;
      padding: 0 0.6rem;
      font-size: 0.75rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 500;
      gap: 0.3rem;
    }

    .pdf-btn.toggle-btn {
      width: auto;
      padding: 0 0.7rem;
      font-size: 0.75rem;
      font-weight: 600;
      gap: 0.3rem;
      background: rgba(110,97,76, 0.08);
      border-color: rgba(110,97,76, 0.15);
      color: var(--accent);
    }

    .pdf-btn.toggle-btn:hover, .pdf-btn.toggle-btn.active {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
      box-shadow: 0 2px 8px var(--accent-glow);
    }

    .pdf-page-indicator {
      font-size: 0.78rem;
      font-family: 'Geist Mono', monospace;
      color: var(--muted);
      display: flex;
      align-items: center;
      gap: 0.3rem;
    }

    .pdf-page-indicator input {
      width: 42px;
      padding: 0.15rem 0.3rem;
      border-radius: 4px;
      border: 1px solid var(--line);
      background: var(--paper);
      color: var(--ink);
      font-family: inherit;
      font-size: inherit;
      text-align: center;
      outline: none;
    }

    .pdf-page-indicator input::-webkit-outer-spin-button,
    .pdf-page-indicator input::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }

    .pdf-zoom-label {
      font-size: 0.78rem;
      font-family: 'Geist Mono', monospace;
      min-width: 46px;
      text-align: center;
      color: var(--muted);
    }

    .pdf-viewer-body {
      display: flex;
      flex: 1;
      overflow: hidden;
      width: 100%;
      position: relative;
    }

    /* --- PDF Sidebar Notlarım --- */
    .pdf-notes-sidebar {
      width: 0;
      background: var(--paper);
      border-right: 0 solid var(--line);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: all var(--t-ui) var(--ease-out);
      flex-shrink: 0;
      z-index: 5;
    }

    .pdf-notes-sidebar.open {
      width: 280px;
      border-right: 1px solid var(--line);
    }

    /* --- PDF Sidebar İçindekiler (TOC) --- */
    .pdf-toc-sidebar {
      width: 0;
      background: var(--paper);
      border-right: 0 solid var(--line);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: all var(--t-ui) var(--ease-out);
      flex-shrink: 0;
      z-index: 5;
    }

    .pdf-toc-sidebar.open {
      width: 300px;
      border-right: 1px solid var(--line);
    }

    .pdf-toc-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }

    .pdf-toc-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0.55rem 0.75rem;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.82rem;
      color: var(--ink);
      transition: all var(--t-micro) var(--ease-out);
      text-decoration: none;
      user-select: none;
      border: 1px solid transparent;
    }

    .pdf-toc-item:hover {
      background: var(--accent-glow);
      color: var(--accent);
      border-color: rgba(110,97,76, 0.15);
      transform: translateX(3px);
    }

    .pdf-toc-item.level-1 { padding-left: 1.4rem; font-size: 0.78rem; opacity: 0.9; }
    .pdf-toc-item.level-2 { padding-left: 2.1rem; font-size: 0.74rem; opacity: 0.8; }

    .prompt-chip {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.74rem;
      padding: 3px 10px;
      border-radius: 8px;
      cursor: pointer;
      white-space: nowrap;
      transition: all var(--t-micro) var(--ease-out);
      font-family: 'Geist', sans-serif;
    }

    .prompt-chip:hover {
      background: var(--accent-glow);
      color: var(--accent);
      border-color: var(--accent);
    }

    .pdf-notes-sidebar-header {
      padding: 1rem;
      border-bottom: 1px solid var(--line);
      background: var(--paper-dark);
      flex-shrink: 0;
    }

    .pdf-notes-sidebar-header h3 {
      font-family: 'Instrument Serif', serif;
      font-size: 1.05rem;
      color: var(--ink);
      margin: 0;
    }

    .pdf-notes-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.8rem;
      display: flex;
      flex-direction: column;
      gap: 0.8rem;
    }

    .pdf-notes-empty {
      font-size: 0.78rem;
      color: var(--muted);
      text-align: center;
      padding: 2rem 1rem;
      line-height: 1.5;
      font-family: 'Geist', sans-serif;
    }

    .pdf-note-item {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0.8rem;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
      position: relative;
      overflow: hidden;
    }

    .pdf-note-item:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
      border-color: var(--sepia-light);
    }

    .pdf-note-item-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.4rem;
      font-size: 0.7rem;
      font-family: 'Geist Mono', monospace;
      color: var(--muted);
    }

    .pdf-note-item-page {
      background: rgba(110,97,76, 0.08);
      color: var(--accent);
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
    }

    .pdf-note-item-quote {
      font-size: 0.78rem;
      font-style: italic;
      color: var(--ink);
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin-bottom: 0.4rem;
      padding-left: 0.4rem;
    }

    .pdf-note-item-quote.yellow { border-left: 3px solid #e8dca0; }
    .pdf-note-item-quote.green { border-left: 3px solid #d3dfc3; }
    .pdf-note-item-quote.blue { border-left: 3px solid #d8d1c3; }
    .pdf-note-item-quote.pink { border-left: 3px solid #e4d6cd; }

    .pdf-note-item-text {
      font-size: 0.78rem;
      color: var(--ink);
      background: var(--paper);
      padding: 0.4rem 0.6rem;
      border-radius: 6px;
      border: 1px solid var(--line);
      line-height: 1.4;
      margin-top: 0.4rem;
    }

    .pdf-note-item-actions {
      display: flex;
      justify-content: flex-end;
      gap: 0.4rem;
      margin-top: 0.4rem;
      opacity: 0;
      transition: opacity var(--t-micro) var(--ease-out);
    }

    .pdf-note-item:hover .pdf-note-item-actions {
      opacity: 1;
    }

    .pdf-note-item-btn {
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.72rem;
      padding: 0.1rem 0.3rem;
      border-radius: 4px;
    }

    .pdf-note-item-btn:hover {
      color: var(--accent);
      background: var(--line);
    }

    .pdf-note-item-btn.delete:hover {
      color: #8f3228;
      background: #f3e1de;
    }

    /* --- Canvas Container & Scroll --- */
    .pdf-canvas-container {
      flex: 1;
      overflow-y: auto;
      overflow-x: auto;
      padding: 2rem 1.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      position: relative;
      scroll-behavior: smooth;
      gap: 24px;
    }

    .pdf-page-wrapper {
      position: relative;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
      background: #fff;
      border-radius: 4px;
      overflow: visible;
      transition: box-shadow var(--t-ui) var(--ease-out);
    }

    [data-theme="dark"] .pdf-page-wrapper {
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
    }

    .pdf-page-wrapper canvas {
      display: block;
      border-radius: 4px;
    }

    /* --- Floating Select Menu --- */
    .pdf-floating-bar {
      position: absolute;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0.4rem;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.04);
      display: flex;
      align-items: center;
      gap: 0.4rem;
      z-index: 100;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.9) translateY(10px);
      transition: opacity var(--t-micro) var(--ease-out), transform var(--t-micro) var(--ease-out);
    }

    [data-theme="dark"] .pdf-floating-bar {
      background: rgba(22, 20, 18, 0.95);
      border-color: rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(12px);
    }

    .pdf-floating-bar.active {
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
    }

    .hl-color-btn {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      border: 2px solid transparent;
      cursor: pointer;
      transition: transform var(--t-micro) var(--ease-out), border-color var(--t-micro) var(--ease-out);
    }

    .hl-color-btn.active {
      border-color: var(--ink);
      transform: scale(1.15);
      box-shadow: 0 0 0 2px var(--accent-glow);
    }

    .hl-color-btn:hover {
      transform: scale(1.15);
    }

    .hl-color-btn.yellow { background-color: #e8dca0; border-color: #e6c872; }
    .hl-color-btn.green { background-color: #d3dfc3; border-color: #a9c297; }
    .hl-color-btn.blue { background-color: #d8d1c3; border-color: #b8b0a0; }
    .hl-color-btn.pink { background-color: #e4d6cd; border-color: #d9b8b0; }

    .hl-action-btn {
      height: 28px;
      padding: 0 0.6rem;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: var(--paper-dark);
      color: var(--ink);
      font-size: 0.72rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.3rem;
      cursor: pointer;
      transition: all var(--t-micro) var(--ease-out);
    }

    .hl-action-btn:hover {
      background: var(--accent);
      color: #fff;
      border-color: var(--accent);
    }

    .hl-action-btn.close {
      width: 28px;
      padding: 0;
      justify-content: center;
      border-radius: 50%;
    }

    .hl-action-btn.close:hover {
      background: rgba(0, 0, 0, 0.05);
      color: var(--ink);
      border-color: transparent;
    }

    /* --- Text Selection Overlay Layer (Mozilla PDF.js Selection Stabilization Standard) --- */
    .textLayer {
      position: absolute;
      text-align: initial;
      inset: 0;
      overflow: hidden;
      opacity: 1;
      line-height: 1;
      -webkit-text-size-adjust: none;
         -moz-text-size-adjust: none;
              text-size-adjust: none;
      forced-color-adjust: none;
      transform-origin: 0 0;
      caret-color: var(--ink);
      z-index: 2;
    }

    .textLayer :is(span, br) {
      color: transparent;
      position: absolute;
      white-space: pre;
      cursor: text;
      transform-origin: 0% 0%;
    }

    /* Text spans stay above the endOfContent selection balancer */
    .textLayer > :not(.markedContent),
    .textLayer .markedContent span:not(.markedContent) {
      z-index: 1;
    }

    /* Chrome fix for issue 14205 — prevents misaligned markedContent spans */
    .textLayer span.markedContent {
      top: 0;
      height: 0;
    }

    /* Smooth, uniform and premium selection highlight without flickering */
    .textLayer ::-moz-selection {
      background: rgba(110,97,76, 0.35);
    }

    .textLayer ::selection {
      background: rgba(110,97,76, 0.35);
    }

    /* Prevents br elements from showing selection highlight — fixes Chrome bug */
    .textLayer br::-moz-selection {
      background: transparent;
    }
    .textLayer br::selection {
      background: transparent;
    }

    /* endOfContent — dynamic selection anchor preventing cursor jumps across paragraphs */
    .textLayer .endOfContent {
      display: block;
      position: absolute;
      inset: 100% 0 0;
      z-index: 0;
      cursor: default;
      pointer-events: none;
      -webkit-user-select: none;
         -moz-user-select: none;
              user-select: none;
    }

    .textLayer .endOfContent.active {
      top: 0;
    }

    /* --- Rendered Custom Highlights --- */
    .pdf-highlight-layer {
      position: absolute;
      left: 0;
      top: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
      border-radius: 4px;
    }

    .rendered-highlight {
      position: absolute;
      mix-blend-mode: multiply;
      opacity: 0.45;
      border-radius: 2px;
      transition: opacity var(--t-micro) var(--ease-out);
    }

    #custom-pdf-viewer[data-surface-mode="chromaguard"] .rendered-highlight {
      mix-blend-mode: screen;
      opacity: 0.35;
    }

    .rendered-highlight.yellow { background-color: #e8dca0; }
    .rendered-highlight.green { background-color: #d3dfc3; }
    .rendered-highlight.blue { background-color: #d8d1c3; }
    .rendered-highlight.pink { background-color: #e4d6cd; }

    /* --- Sticky Note Pins --- */
    .sticky-note-marker {
      position: absolute;
      width: 26px;
      height: 26px;
      border-radius: 50%;
      background: var(--accent);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.72rem;
      cursor: pointer;
      box-shadow: 0 4px 10px var(--accent-glow);
      z-index: 10;
      transition: all var(--t-micro) var(--ease-out);
      animation: notePulse 2s infinite;
    }

    .sticky-note-marker:hover {
      transform: scale(1.15);
      background: var(--accent-soft);
    }

    @keyframes notePulse {
      0% { box-shadow: 0 0 0 0 rgba(110,97,76, 0.4); }
      70% { box-shadow: 0 0 0 8px rgba(110,97,76, 0); }
      100% { box-shadow: 0 0 0 0 rgba(110,97,76, 0); }
    }

    /* ═════════════════════════════════════════════════════════════
       PDF In-Document Search (Ctrl + F) UI Styles
       ═════════════════════════════════════════════════════════════ */
    .pdf-search-bar {
      position: absolute;
      top: 52px;
      right: 20px;
      z-index: 50;
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 6px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.04);
      width: 400px;
      max-width: calc(100% - 40px);
      overflow: hidden;
      font-family: 'Geist', sans-serif;
      animation: pdfSearchSlideDown var(--t-ui) var(--ease-out);
      backdrop-filter: blur(12px);
    }

    [data-theme="dark"] .pdf-search-bar {
      background: rgba(24, 21, 18, 0.96);
      border-color: rgba(255, 255, 255, 0.12);
      box-shadow: 0 14px 40px rgba(0, 0, 0, 0.5);
    }

    @keyframes pdfSearchSlideDown {
      from {
        opacity: 0;
        transform: translateY(-8px) scale(0.98);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }

    .pdf-search-main-row {
      display: flex;
      align-items: center;
      padding: 0.55rem 0.75rem;
      gap: 0.5rem;
    }

    .pdf-search-input-wrap {
      position: relative;
      flex: 1;
      display: flex;
      align-items: center;
    }

    .pdf-search-input-icon {
      position: absolute;
      left: 10px;
      font-size: 0.8rem;
      color: var(--sepia-light);
      pointer-events: none;
    }

    #pdf-search-input {
      width: 100%;
      padding: 0.45rem 1.8rem 0.45rem 2rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--paper-dark);
      color: var(--ink);
      font-size: 0.82rem;
      font-family: 'Geist', sans-serif;
      outline: none;
      transition: all var(--t-micro) var(--ease-out);
    }

    #pdf-search-input:focus {
      border-color: var(--accent);
      background: var(--paper);
      box-shadow: 0 0 0 3px var(--accent-glow);
    }

    .pdf-search-icon-btn.clear {
      position: absolute;
      right: 6px;
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 0.75rem;
      padding: 4px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: color var(--t-micro) var(--ease-out);
    }

    .pdf-search-icon-btn.clear:hover {
      color: var(--ink);
    }

    .pdf-search-counter {
      font-size: 0.74rem;
      font-family: 'Geist Mono', monospace;
      color: var(--muted);
      white-space: nowrap;
      min-width: 55px;
      text-align: center;
      padding: 0.25rem 0.5rem;
      border-radius: 6px;
      background: var(--paper-dark);
      font-weight: 500;
    }

    .pdf-search-counter.has-matches {
      color: var(--accent);
      background: rgba(110,97,76, 0.08);
      font-weight: 700;
    }

    .pdf-search-actions {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .pdf-search-nav-btn {
      width: 28px;
      height: 28px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: transparent;
      color: var(--ink);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.78rem;
      transition: all var(--t-micro) var(--ease-out);
    }

    .pdf-search-nav-btn:hover:not(:disabled) {
      background: var(--line);
      color: var(--accent);
    }

    .pdf-search-nav-btn.active {
      background: var(--accent);
      color: #fff;
    }

    .pdf-search-nav-btn:disabled {
      opacity: 0.3;
      cursor: not-allowed;
    }

    .pdf-search-nav-btn.close:hover {
      background: #f3e1de;
      color: #8f3228;
    }

    /* Results Drawer */
    .pdf-search-results-drawer {
      max-height: 260px;
      overflow-y: auto;
      border-top: 1px solid var(--line);
      background: var(--paper-dark);
    }

    .pdf-search-drawer-header {
      padding: 0.5rem 0.85rem;
      font-size: 0.72rem;
      font-family: 'Geist Mono', monospace;
      font-weight: 600;
      color: var(--sepia);
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .pdf-search-drawer-list {
      display: flex;
      flex-direction: column;
    }

    .pdf-search-result-item {
      padding: 0.55rem 0.85rem;
      border-bottom: 1px solid var(--line);
      cursor: pointer;
      transition: background var(--t-micro) var(--ease-out);
      font-size: 0.78rem;
      line-height: 1.45;
      color: var(--ink);
    }

    .pdf-search-result-item:hover, .pdf-search-result-item.active {
      background: rgba(110,97,76, 0.08);
    }

    .pdf-search-result-meta {
      display: flex;
      justify-content: space-between;
      margin-bottom: 0.25rem;
      font-size: 0.7rem;
      font-family: 'Geist Mono', monospace;
      color: var(--muted);
    }

    .pdf-search-result-page {
      font-weight: 700;
      color: var(--accent);
    }

    .pdf-search-result-snippet {
      color: var(--ink);
      overflow-wrap: break-word;
    }

    .pdf-search-result-snippet strong {
      background: #e8dca0;
      color: #6b5016;
      padding: 1px 3px;
      border-radius: 3px;
      font-weight: 700;
    }

    [data-theme="dark"] .pdf-search-result-snippet strong {
      background: #5e4318;
      color: #e8dca0;
    }

    /* In-Page Visual Highlights */
    .pdf-search-highlight {
      position: absolute;
      background-color: rgba(254, 240, 138, 0.55);
      border-bottom: 2px solid #c49a3a;
      border-radius: 2px;
      mix-blend-mode: multiply;
      pointer-events: none;
      transition: all var(--t-micro) var(--ease-out);
      z-index: 4;
    }

    #custom-pdf-viewer[data-surface-mode="chromaguard"] .pdf-search-highlight {
      background-color: rgba(234, 179, 8, 0.35);
      border-bottom-color: #d0a653;
      mix-blend-mode: screen;
    }

    .pdf-search-highlight.active {
      background-color: rgba(184,134,47, 0.85);
      border: 1.5px solid #b8862f;
      box-shadow: 0 0 10px rgba(184,134,47, 0.6);
      animation: searchHighlightPulse 1.2s infinite;
      z-index: 6;
    }

    @keyframes searchHighlightPulse {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.05); }
    }

    /* Telegram Toast Animation */
    #telegram-toast {
      box-shadow: 0 12px 32px rgba(110,97,76, 0.3);
      backdrop-filter: blur(12px);
    }



    @keyframes themeIconSpin {
      0% {
        transform: rotate(-90deg) scale(0.6);
        opacity: 0;
      }
      100% {
        transform: rotate(0deg) scale(1);
        opacity: 1;
      }
    }

    .theme-icon-spin {
      animation: themeIconSpin var(--t-ui) var(--ease-spring) both;
      display: inline-block;
    }

    /* ═══════════ Toast Notification Stack ═══════════ */
    .toast-container {
      position: fixed;
      top: 24px;
      right: 24px;
      z-index: 999999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
      max-width: 420px;
      width: calc(100vw - 32px);
    }

    .toast-item {
      pointer-events: auto;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 13px 18px;
      border-radius: 6px;
      background: var(--paper);
      border: 1px solid var(--line);
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.14), 0 3px 10px rgba(0, 0, 0, 0.06);
      backdrop-filter: blur(20px) saturate(180%);
      -webkit-backdrop-filter: blur(20px) saturate(180%);
      color: var(--ink);
      font-family: 'Geist', sans-serif;
      font-size: 0.88rem;
      line-height: 1.45;
      opacity: 0;
      transform: translateX(45px) scale(0.95);
      transition: all var(--t-ui) var(--ease-out);
    }

    .toast-item.show {
      opacity: 1;
      transform: translateX(0) scale(1);
    }

    .toast-item.hide {
      opacity: 0;
      transform: translateX(35px) scale(0.92);
    }

    .toast-item .toast-icon {
      font-size: 1.25rem;
      flex-shrink: 0;
    }

    .toast-item.toast-success .toast-icon { color: #5f7a4f; }
    .toast-item.toast-error .toast-icon { color: #b0473c; }
    .toast-item.toast-warning .toast-icon { color: #b8862f; }
    .toast-item.toast-info .toast-icon { color: #6e614c; }

    .toast-item.toast-success { border-left: 4px solid #5f7a4f; }
    .toast-item.toast-error { border-left: 4px solid #b0473c; }
    .toast-item.toast-warning { border-left: 4px solid #b8862f; }
    .toast-item.toast-info { border-left: 4px solid #6e614c; }

    [data-theme="dark"] .toast-item {
      background: rgba(26, 22, 19, 0.94);
      border-color: rgba(255, 255, 255, 0.1);
      box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
    }

    .toast-content {
      flex: 1;
      overflow-wrap: break-word;
      word-break: normal;
    }

    .toast-close {
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 1.25rem;
      padding: 0 4px;
      line-height: 1;
      transition: color var(--t-micro);
    }

    .toast-close:hover {
      color: var(--ink);
    }

    /* ═══════════ Skeleton Shimmer Loaders ═══════════ */
    .book-card.skeleton {
      pointer-events: none;
      user-select: none;
      border-color: var(--line);
      animation: none;
    }

    .skeleton-shimmer {
      background: linear-gradient(90deg, var(--paper-dark) 25%, var(--sepia-pale) 50%, var(--paper-dark) 75%);
      background-size: 200% 100%;
      animation: skeletonShimmerAnim 1.6s infinite ease-in-out;
      border-radius: 6px;
    }

    [data-theme="dark"] .skeleton-shimmer {
      background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.04) 75%);
      background-size: 200% 100%;
      animation: skeletonShimmerAnim 1.6s infinite ease-in-out;
    }

    @keyframes skeletonShimmerAnim {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    .card-cover.skeleton {
      background: var(--paper-dark);
      position: relative;
      overflow: hidden;
      min-height: 220px;
    }

    .skeleton-line {
      border-radius: 4px;
      margin-bottom: 8px;
    }

    /* ═══════════ Empty State Illustration ═══════════ */
    .empty-state {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3.5rem 1.5rem;
      width: 100%;
      text-align: center;
    }

    .empty-state-card {
      max-width: 480px;
      background: var(--paper);
      border: 1.5px dashed var(--line);
      border-radius: 8px;
      padding: 2.8rem 2.2rem;
      box-shadow: 0 10px 32px var(--shadow-color);
    }

    [data-theme="dark"] .empty-state-card {
      background: rgba(22, 19, 16, 0.7);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .empty-state-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 76px;
      height: 76px;
      border-radius: 50%;
      background: var(--accent-glow);
      color: var(--accent);
      margin-bottom: 1.25rem;
    }

    .empty-state-card h3 {
      font-family: 'Instrument Serif', serif;
      font-size: 1.45rem;
      color: var(--ink);
      margin-bottom: 0.6rem;
    }

    .empty-state-card p {
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.55;
      margin-bottom: 1.6rem;
    }

    .empty-state-actions {
      display: flex;
      gap: 0.85rem;
      justify-content: center;
      flex-wrap: wrap;
    }

    .btn-empty-clear {
      background: var(--paper-dark);
      border: 1px solid var(--line);
      color: var(--ink);
      padding: 0.65rem 1.25rem;
      border-radius: 6px;
      font-weight: 500;
      font-size: 0.88rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all var(--t-micro) var(--ease-out);
    }

    .btn-empty-clear:hover {
      border-color: var(--ink);
      color: var(--ink);
      background: var(--paper-dark);
    }

    .btn-empty-add {
      background: var(--accent);
      border: none;
      color: #fff;
      padding: 0.65rem 1.35rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all var(--t-micro) var(--ease-out);
      box-shadow: 0 4px 14px var(--accent-glow);
    }

    .btn-empty-add:hover {
      filter: brightness(1.1);
      transform: translateY(-1px);
      box-shadow: 0 6px 18px var(--accent-glow);
    }

    /* ═══════════ Keyboard Shortcuts Styling ═══════════ */
    .shortcut-kbd {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 26px;
      height: 24px;
      padding: 0 6px;
      background: var(--paper-dark);
      border: 1px solid var(--line);
      border-bottom: 2px solid var(--sepia-light);
      border-radius: 6px;
      font-family: 'Geist Mono', monospace;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--ink);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
    }

    [data-theme="dark"] .shortcut-kbd {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.15);
      border-bottom-color: rgba(255, 255, 255, 0.25);
    }

    /* ═══════════ AI Chat Page Citations & Pulse ═══════════ */
    .chat-page-cite {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 8px;
      margin: 0 2px;
      border-radius: 6px;
      background: rgba(110,97,76, 0.1);
      border: 1px solid rgba(110,97,76, 0.25);
      color: var(--accent);
      font-family: 'Geist Mono', monospace;
      font-size: 0.78rem;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      vertical-align: baseline;
      transition: all var(--t-micro) var(--ease-out);
    }

    .chat-page-cite:hover {
      background: var(--accent);
      color: #fff;
    }

    .pdf-page-wrapper.page-pulse {
      box-shadow: 0 0 0 6px var(--accent), 0 12px 36px rgba(110,97,76, 0.4);
      transition: box-shadow var(--t-ui) var(--ease-out);
    }

    /* ═══════════ AI Chat Stop Generation Button ═══════════ */
    .btn-stop-chat {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 8px;
      background: #f3e1de;
      border: 1px solid rgba(176,71,60, 0.3);
      color: #8f3228;
      font-family: 'Geist', sans-serif;
      font-size: 0.76rem;
      font-weight: 600;
      cursor: pointer;
      margin-bottom: 8px;
      transition: all var(--t-micro) var(--ease-out);
    }

    .btn-stop-chat:hover {
      background: #8f3228;
      color: #fff;
    }

    /* ═══════════ Mobile Responsive Workspace ═══════════ */
    @media (max-width: 768px) {
      .workspace-content {
        flex-direction: column;
      }
      .workspace-pdf-pane {
        flex: 1 1 55%;
        min-height: 280px;
        min-width: 100%;
      }
      .workspace-resize-handle {
        display: none;
      }
      .workspace-chat-pane {
        flex: 1 1 45%;
        width: 100%;
        min-width: 100%;
        border-left: none;
        border-top: 1px solid var(--line);
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.08);
      }
      .workspace-header {
        padding: 0 1rem;
      }
      .workspace-book-info {
        max-width: 160px;
      }
    }

    /* ── TWO-PAGE SPREAD BOOK MODE ── */
    .pdf-spread-row {
      display: flex;
      justify-content: center;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 24px;
      width: 100%;
    }

    .pdf-spread-row .pdf-page-wrapper {
      margin-bottom: 0;
      transition: transform var(--t-micro) var(--ease-out), box-shadow var(--t-micro) var(--ease-out);
    }

    .pdf-spread-row .pdf-page-wrapper.spread-left {
      box-shadow: -8px 12px 28px rgba(0, 0, 0, 0.12), inset -4px 0 10px rgba(0, 0, 0, 0.05);
      border-top-right-radius: 2px;
      border-bottom-right-radius: 2px;
    }

    .pdf-spread-row .pdf-page-wrapper.spread-right {
      box-shadow: 8px 12px 28px rgba(0, 0, 0, 0.12), inset 4px 0 10px rgba(0, 0, 0, 0.05);
      border-top-left-radius: 2px;
      border-bottom-left-radius: 2px;
    }

    [data-theme="dark"] .pdf-spread-row .pdf-page-wrapper.spread-left {
      box-shadow: -8px 12px 28px rgba(0, 0, 0, 0.4), inset -4px 0 10px rgba(0, 0, 0, 0.2);
    }

    [data-theme="dark"] .pdf-spread-row .pdf-page-wrapper.spread-right {
      box-shadow: 8px 12px 28px rgba(0, 0, 0, 0.4), inset 4px 0 10px rgba(0, 0, 0, 0.2);
    }




```


## DOSYA 6.1: static/js/app.js (Uygulama Yaşam Döngüsü, Dinamik Theme-Color & Scroll-to-Top)

**Dosya Yolu:** `static/js/app.js`

```javascript
/* ═══════════ app.js — Application Bootstrap & Initialization ═══════════ */

    // ── API ENTEGRASYONU ──────────────────────────────────────
    async function bootstrap() {
      try {
        await loadSettings();
        await loadBooksFromAPI(1, false);
      } catch (err) {
        console.error("Bootstrap data load failed:", err);
      }
      setupGlobalDragDrop();
      initWebSocket();
      if (typeof fetchTasksFromAPI === 'function') {
        fetchTasksFromAPI().catch(err => console.warn("Task fetch error:", err));
      }

      // Infinite Scroll listener
      window.addEventListener('scroll', () => {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
          if (!window.isLoadingMore && (window.allBooks?.length || 0) < (window.totalBooks || 0)) {
            loadBooksFromAPI((window.currentPage || 1) + 1, true).catch(err => console.error(err));
          }
        }
      });

      // Chat Counter Listener
      const chatInput = document.getElementById('chat-input');
      if (chatInput) {
        chatInput.addEventListener('input', updateChatCounter);
      }

      // Sürükle-Bırak Entegrasyonu (Tüm pencere ve hero alanı)
      const dropBox = document.getElementById('drop-box');
      if (dropBox) {
        window.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropBox.classList.add('dragover');
        });
        window.addEventListener('dragleave', (e) => {
          if (!e.relatedTarget) {
            dropBox.classList.remove('dragover');
          }
        });
        window.addEventListener('drop', (e) => {
          e.preventDefault();
          dropBox.classList.remove('dragover');
          if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
          }
        });
        dropBox.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropBox.classList.add('dragover');
        });
        dropBox.addEventListener('dragleave', () => {
          dropBox.classList.remove('dragover');
        });
        dropBox.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropBox.classList.remove('dragover');
          if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
          }
        });
      }
    }

    (async function initApp() {
      try {
        if (document.readyState === 'loading') {
          await new Promise((resolve) => window.addEventListener('DOMContentLoaded', resolve, { once: true }));
        }
        await bootstrap();
      } catch (err) {
        console.error("Bootstrap error:", err);
      }
    })();

    function setupGlobalDragDrop() {
      const overlay = document.getElementById('drop-overlay');
      const pill = overlay ? overlay.querySelector('.pill') : null;

      const show = (e) => {
        if (!overlay) return;
        overlay.classList.add('visible');
        const items = e?.dataTransfer?.items;
        if (pill && items) {
          const count = items.length;
          if (count > 0) {
            pill.innerHTML = `<i class="fas fa-cloud-arrow-up"></i> ${count} dosya bırakılmaya hazır`;
          }
        }
      };
      const hide = () => {
        if (!overlay) return;
        overlay.classList.remove('visible');
        if (pill) {
          pill.innerHTML = `<i class="fas fa-file-alt"></i> PDF, EPUB, TXT desteklenir`;
        }
      };

      ['dragenter', 'dragover'].forEach(evt => {
        window.addEventListener(evt, (e) => { e.preventDefault(); show(e); });
      });
      window.addEventListener('dragleave', (e) => {
        if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) hide();
      });
      window.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.target?.closest?.('#drop-overlay')) return;
        hide();
        handleFiles(e.dataTransfer.files);
      });
      if (overlay) {
        overlay.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          hide();
          handleFiles(e.dataTransfer.files);
        });
      }
      document.addEventListener('dragover', (e) => e.preventDefault());
      document.addEventListener('drop', (e) => e.preventDefault());
    }

    function makeUploadKey(file) {
      return `${file.name}__${file.size}`;
    }

    function handleFiles(files) {
      const validExtensions = new Set(['pdf', 'epub', 'txt']);
      let skippedCount = 0;
      let validCount = 0;

      Array.from(files).forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!validExtensions.has(ext) && file.type !== 'application/pdf') {
          skippedCount++;
          return;
        }
        validCount++;
        const key = makeUploadKey(file);
        if (window.pendingUploads?.has(key)) return;
        window.pendingUploads?.add(key);
        void prepareUpload(file, key);
      });

      if (skippedCount > 0 && typeof showToast === 'function') {
        showToast(`${skippedCount} desteklenmeyen dosya atlandı. (Yalnızca PDF, EPUB ve TXT desteklenir)`, 'warning');
      }
    }

    // ─── ÖZELLİK 6: GECE MODU TOGGLE FONKSİYONU ─────────────────────────
    function updateThemeMeta(theme) {
      const color = theme === 'dark' ? '#161513' : '#f4f1eb';
      let meta = document.querySelector('meta[name="theme-color"]:not([media])');
      if (!meta) {
        meta = document.querySelector('meta[name="theme-color"]');
      }
      if (meta) {
        meta.setAttribute('content', color);
        if (meta.hasAttribute('media')) {
          meta.removeAttribute('media');
        }
      }
    }

    function updateThemeIcons(theme, spin = true) {
      const spinClass = spin ? ' theme-icon-spin' : '';
      const iconHTML = theme === 'dark'
        ? `<i class="fas fa-sun${spinClass}"></i>`
        : `<i class="fas fa-moon${spinClass}"></i>`;
      const mainThemeBtn = document.getElementById('theme-toggle');
      if (mainThemeBtn) mainThemeBtn.innerHTML = iconHTML;
      document.querySelectorAll('.compact-theme-toggle').forEach(btn => btn.innerHTML = iconHTML);
    }

    function toggleTheme() {
      const html = document.documentElement;
      const next = html.dataset.theme === 'dark' ? 'light' : 'dark';

      const apply = () => {
        html.dataset.theme = next;
        localStorage.setItem('kutuphane-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcons(next, true);
        updateThemeMeta(next);
      };

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        apply();
        return;
      }

      document.startViewTransition(apply);
    }

    // Sayfa yüklenirken kaydedilmiş tema tercihini uygula
    (function () {
      const saved = localStorage.getItem('kutuphane-theme') || localStorage.getItem('theme') || 'light';
      document.documentElement.dataset.theme = saved;
      updateThemeIcons(saved, false);
      updateThemeMeta(saved);
    })();

    // ─── İŞLEM MERKEZİ MANTIĞI ──────────────────────────────────────────

    // ─── HEADER & COMPACT-NAV INTERSECTION OBSERVER (Zero Jitter) ──────
    const mainHeader = document.querySelector('header:not(.workspace-header)');
    const compactNav = document.getElementById('compact-nav');
    const scrollBtn = document.getElementById('scroll-top-btn');

    if (mainHeader && compactNav && 'IntersectionObserver' in window) {
      const headerObserver = new IntersectionObserver((entries) => {
        const entry = entries[0];
        if (entry.isIntersecting) {
          compactNav.classList.remove('visible');
        } else {
          const workspace = document.getElementById('workspace-view');
          const isWorkspaceActive = workspace && workspace.classList.contains('active');
          if (!isWorkspaceActive) {
            compactNav.classList.add('visible');
          }
        }
      }, {
        threshold: 0
      });
      headerObserver.observe(mainHeader);
    }

    // Scroll to Top Button Visibility
    window.addEventListener('scroll', () => {
      if (window.scrollY > 600) {
        scrollBtn?.classList.add('visible');
      } else {
        scrollBtn?.classList.remove('visible');
      }
    }, { passive: true });

// EXPOSE FUNCTIONS TO GLOBAL SCOPE
window.loadBooksFromAPI = loadBooksFromAPI;
window.uploadFile = uploadFile;
window.prepareUpload = prepareUpload;
window.deleteBook = deleteBook;
window.toggleFavorite = toggleFavorite;
window.selectCat = selectCat;
window.filterCat = filterCat;
window.toggleFavFilter = toggleFavFilter;
window.selectCol = selectCol;
window.toggleDropdown = toggleDropdown;
window.filterCol = filterCol;
window.openColModal = openColModal;
window.closeColModal = closeColModal;
window.deleteCollection = deleteCollection;
window.createCollection = createCollection;
window.toggleBookCol = toggleBookCol;
window.copyCollectionMarkdown = copyCollectionMarkdown;
window.importCollection = importCollection;
window.setView = setView;
window.openSettings = openSettings;
window.updateAIUI = updateAIUI;
window.closeSettings = closeSettings;
window.closeSettingsDirect = closeSettingsDirect;
window.saveSettings = saveSettings;
window.resetCascadeModelsToDefault = typeof resetCascadeModelsToDefault !== 'undefined' ? resetCascadeModelsToDefault : window.resetCascadeModelsToDefault;
window.toggleEditMode = toggleEditMode;
window.saveBookEdit = saveBookEdit;
window.toggleSelectionMode = toggleSelectionMode;
window.toggleSelectBook = toggleSelectBook;
window.bulkDelete = bulkDelete;
window.sendMessage = sendMessage;
window.exportToExcel = exportToExcel;
window.handleFiles = handleFiles;
window.toggleAssistant = toggleAssistant;
window.toggleOps = toggleOps;
window.setOpsTab = typeof setOpsTab !== 'undefined' ? setOpsTab : window.setOpsTab;
window.openBookFromOps = typeof openBookFromOps !== 'undefined' ? openBookFromOps : window.openBookFromOps;
window.fetchTasksFromAPI = typeof fetchTasksFromAPI !== 'undefined' ? fetchTasksFromAPI : window.fetchTasksFromAPI;
window.toggleArchive = toggleArchive;
window.openLogsModal = openLogsModal;
window.closeLogsModal = closeLogsModal;
window.closeLogsModalDirect = closeLogsModalDirect;
window.setLogCategory = setLogCategory;
window.closeModal = closeModal;
window.closeModalDirect = closeModalDirect;
window.uploadCover = uploadCover;
window.sortTable = sortTable;
window.render = render;
window.toggleTheme = toggleTheme;
window.login = () => { window.location.href = "/login"; };
```


## DOSYA 6.2: static/js/state.js (Toast Bildirim Sistemi, role='status', aria-live & 4s Hover Pause)

**Dosya Yolu:** `static/js/state.js`

```javascript
/* ═══════════ state.js — Global State & Constants ═══════════ */
var allBooks = [];
var currentPage = 1;
var totalBooks = 0;
var isLoadingMore = false;
var allCollections = [];
var activeCategory = 'all';
var activeCollection = 'all';
var currentView = 'grid';
var sortCol = -1, sortDir = 1;
var opsActiveTab = 'all';
var lastActiveTasks = {};
var lastArchivedTasks = {};
var pendingUploads = new Set();
var uploadingCards = new Map();   // tempId -> {card, bar, label}
var taskToTemp = new Map();       // taskId -> tempId
var telegramDlCards = new Map();   // filename -> tempId
var currentModalHash = null;      // Track open book in modal
var isSelectionMode = false;      // Is bulk selection mode active?
var selectedBooks = new Set();    // Hash list of selected books
var showOnlyFav = false;          // Is "Show favorites only" active?
var appSettings = {};             // Sunucudan gelen ayarlar
var completedTasks = new Set();
var currentLogCategory = 'all';
var currentLogLevel = 'all';
var currentLogSearch = '';
var isLogLivePaused = false;
var isLogAutoScroll = true;
var unreadLogErrors = 0;
var cachedLogs = [];
var ws = null;
var wsReconnectTimer = null;
var wsReconnectDelay = 1500;
var colTargetHash = null;
var dragSrcEl = null;
var customOrder = JSON.parse(localStorage.getItem('kutuphane-custom-order') || 'null');
var network = null;
var networkFocusBookHash = null;
var isDeepSearchActive = false;


const BOOK_ICON_LG = `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" style="color:var(--sepia-light)"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;
const BOOK_ICON_SM = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:var(--sepia-light)"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;
const DONUT_COLORS = ['#6e614c', '#82745e', '#e8a87c', '#82745e', '#b9b3a6', '#e6e1d6', '#5a8a6e', '#7eb8a0', '#4a7a9b', '#7fb3d4', '#9b6ea0', '#c49bc7'];

/* ═══════════ Toast Notification System ═══════════ */
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;
  toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
  toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
  toast.setAttribute('aria-atomic', 'true');

  const iconMap = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };
  const icon = iconMap[type] || 'fa-circle-info';

  const escapeHtml = (str) => {
    return (str || '').toString()
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  };
  const formattedMsg = escapeHtml(message).replaceAll('\n', '<br>');

  toast.innerHTML = `
    <div class="toast-icon"><i class="fas ${icon}"></i></div>
    <div class="toast-content">${formattedMsg}</div>
    <button class="toast-close" onclick="this.closest('.toast-item').remove()" aria-label="Kapat">&times;</button>
  `;

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  let dismissTimer = setTimeout(() => {
    toast.classList.remove('show');
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 280);
  }, duration);

  toast.addEventListener('mouseenter', () => clearTimeout(dismissTimer));
  toast.addEventListener('mouseleave', () => {
    dismissTimer = setTimeout(() => {
      toast.classList.remove('show');
      toast.classList.add('hide');
      setTimeout(() => toast.remove(), 280);
    }, 1200);
  });
}

window.showToast = showToast;
window.showNotification = showToast;
window.toast = {
  success: (msg, dur) => showToast(msg, 'success', dur),
  error: (msg, dur) => showToast(msg, 'error', dur || 5000),
  warning: (msg, dur) => showToast(msg, 'warning', dur),
  info: (msg, dur) => showToast(msg, 'info', dur)
};

```


## DOSYA 6.3: static/js/ui_core.js (UI Çekirdeği, cardElementsMap, Evrensel Focus Trap & Semantik Butonlar)

**Dosya Yolu:** `static/js/ui_core.js`

```javascript
/* ═══════════ ui_core.js — UI Rendering, Grid, Table & Collections ═══════════ */
    window.shouldStagger = true;
    // --- CATEGORY LABELS ---
    function buildCategoryTags() {
      const books = window.allBooks || [];
      const cats = [...new Set(books.map(b => b.category).filter(Boolean))].sort((a, b) => a.localeCompare(b));
      const menu = document.getElementById('category-menu');
      const trigger = document.getElementById('category-trigger');

      let html = `<button type="button" class="dropdown-item ${window.activeCategory === 'all' ? 'active' : ''}" role="option" onclick="selectCat('all', 'Tüm Kategoriler')"><i class="fas fa-layer-group"></i> Tüm Kategoriler</button>`;

      cats.forEach(cat => {
        const encodedCat = encData(cat);
        html += `<button type="button" class="dropdown-item ${window.activeCategory === cat ? 'active' : ''}" role="option" data-value="${encodedCat}" data-label="${encodedCat}" onclick="selectCat(decodeURIComponent(this.dataset.value), decodeURIComponent(this.dataset.label))"><i class="fas fa-tag"></i> ${esc(cat)}</button>`;
      });
      if (menu) menu.innerHTML = html;

      if (trigger) {
        if (window.activeCategory !== 'all') {
          trigger.textContent = window.activeCategory;
        } else {
          trigger.textContent = 'Tüm Kategoriler';
        }
      }
    }

    function selectCat(val, label) {
      window.activeCategory = val;
      const catTrigger = document.getElementById('category-trigger');
      if (catTrigger) catTrigger.textContent = label;
      const dropCat = document.getElementById('dropdown-category');
      if (dropCat) dropCat.classList.remove('open');
      render();
      buildCategoryTags(); // Update active states
    }
    function filterCat(cat) {
      window.activeCategory = cat;
      render();
    }

    function toggleFavFilter() {
      window.showOnlyFav = !window.showOnlyFav;
      const btn = document.getElementById('btn-fav-filter');
      if (btn) btn.classList.toggle('active', window.showOnlyFav);
      render();
    }

    // --- COLLECTIONS ---
    async function loadCollectionsFromAPI() {
      try {
        const res = await apiFetch('/api/collections');
        if (res?.status === 401) {
          window.location.href = '/login';
          return;
        }
        if (res?.ok) {
          window.allCollections = await res.json();
          const menu = document.getElementById('collection-menu');
          const trigger = document.getElementById('collection-trigger');

          let html = `<button type="button" class="dropdown-item ${window.activeCollection === 'all' ? 'active' : ''}" role="option" onclick="selectCol('all', 'Tüm Koleksiyonlar')"><i class="fas fa-folder-open"></i> Tüm Koleksiyonlar</button>`;

          (window.allCollections || []).forEach(c => {
            const encodedName = encData(c.isim);
            html += `<button type="button" class="dropdown-item ${window.activeCollection === String(c.id) ? 'active' : ''}" role="option" data-value="${c.id}" data-label="${encodedName}" onclick="selectCol(this.dataset.value, decodeURIComponent(this.dataset.label))"><i class="fas fa-folder"></i> ${esc(c.isim)}</button>`;
          });
          if (menu) menu.innerHTML = html;

          if (trigger) {
            const activeColObj = (window.allCollections || []).find(c => String(c.id) === window.activeCollection);
            trigger.textContent = activeColObj ? activeColObj.isim : 'Tüm Koleksiyonlar';
          }
        }
      } catch (e) {
        console.error("Koleksiyonlar alınamadı", e);
      }
    }

    function selectCol(val, label) {
      window.activeCollection = String(val);
      const colTrigger = document.getElementById('collection-trigger');
      if (colTrigger) colTrigger.textContent = label;
      const dropCol = document.getElementById('dropdown-collection');
      if (dropCol) dropCol.classList.remove('open');
      render();
      loadCollectionsFromAPI().catch(err => console.warn(err)); // Update active states
    }

    let lastActiveDropdownTrigger = null;

    function openCustomDropdown(el) {
      if (!el) return;
      el.classList.add('open');
      const trigger = el.querySelector('.dropdown-trigger') || el.querySelector('button');
      if (trigger) {
        trigger.setAttribute('aria-expanded', 'true');
        lastActiveDropdownTrigger = trigger;
      }
      const menu = el.querySelector('.dropdown-menu');
      if (menu) {
        const items = Array.from(menu.querySelectorAll('.dropdown-item, button, a, [tabindex]')).filter(i => i.offsetParent !== null);
        items.forEach(item => {
          if (!item.hasAttribute('tabindex')) item.setAttribute('tabindex', '0');
        });
        if (items.length > 0) {
          setTimeout(() => items[0].focus(), 40);
        }
      }
    }

    function closeCustomDropdown(el) {
      if (!el) return;
      el.classList.remove('open');
      const trigger = el.querySelector('.dropdown-trigger') || el.querySelector('button');
      if (trigger) {
        trigger.setAttribute('aria-expanded', 'false');
      }
      if (lastActiveDropdownTrigger && el.contains(lastActiveDropdownTrigger)) {
        lastActiveDropdownTrigger.focus();
        lastActiveDropdownTrigger = null;
      }
    }

    function toggleDropdown(id) {
      const el = document.getElementById(id);
      if (!el) return;
      const isOpen = el.classList.contains('open');

      // Close others
      document.querySelectorAll('.custom-dropdown.open').forEach(d => {
        if (d !== el) closeCustomDropdown(d);
      });

      if (!isOpen) {
        openCustomDropdown(el);
      } else {
        closeCustomDropdown(el);
      }
    }

    // Global click listener to close dropdowns
    window.addEventListener('click', (e) => {
      if (!e.target?.closest?.('.custom-dropdown')) {
        document.querySelectorAll('.custom-dropdown.open').forEach(d => closeCustomDropdown(d));
      }
    });

    // Klavye erişilebilirliği: ↑, ↓ gezinme, Enter ile seçim, Esc ile kapatma ve tetikleyiciye odak dönüşü
    document.addEventListener('keydown', (e) => {
      const activeDropdown = document.querySelector('.custom-dropdown.open');
      const toolsMenu = document.getElementById('header-tools-menu');
      const isToolsOpen = toolsMenu && toolsMenu.style.display !== 'none' && !toolsMenu.classList.contains('closing');

      if (!activeDropdown && !isToolsOpen) return;

      const activeMenu = activeDropdown
        ? activeDropdown.querySelector('.dropdown-menu')
        : toolsMenu;

      if (!activeMenu) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        if (activeDropdown) closeCustomDropdown(activeDropdown);
        if (isToolsOpen && typeof closeToolsMenu === 'function') closeToolsMenu();
        return;
      }

      const items = Array.from(activeMenu.querySelectorAll('.dropdown-item, .tools-menu-item, button, a, [tabindex="0"]')).filter(i => i.offsetParent !== null);
      if (items.length === 0) return;

      const currentIndex = items.indexOf(document.activeElement);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % items.length;
        items[nextIndex].focus();
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevIndex = (currentIndex - 1 + items.length) % items.length;
        items[prevIndex].focus();
        return;
      }

      if (e.key === 'Enter') {
        if (document.activeElement && items.includes(document.activeElement)) {
          e.preventDefault();
          document.activeElement.click();
          if (activeDropdown) closeCustomDropdown(activeDropdown);
          if (isToolsOpen && typeof closeToolsMenu === 'function') closeToolsMenu();
        }
      }
    });

    function filterCol(colId) {
      window.activeCollection = String(colId);
      render();
    }

    function openColModal(hash) {
      window.colTargetHash = hash;
      const list = document.getElementById('col-list');
      if (!list) return;
      const book = (window.allBooks || []).find(b => b.hash === hash);
      const bookCols = book?.collections ? book.collections.map(String) : [];
      const collections = window.allCollections || [];

      if (collections.length === 0) {
        list.innerHTML = '<div style="color:var(--muted); font-style:italic; font-size:0.85rem; text-align:center; padding: 2rem 0;"><i class="fas fa-folder-open" style="font-size:2rem; opacity:0.3; margin-bottom:1rem; display:block;"></i>Henüz koleksiyon bulunmuyor.<br>Aşağıdan yeni bir liste oluşturabilirsiniz.</div>';
      } else {
        list.innerHTML = collections.map(c => {
          const inCol = bookCols.includes(String(c.id));
          const encodedName = encData(c.isim);
          return `
      <div class="col-row" style="display:flex; justify-content:space-between; align-items:center; background:var(--paper); padding: 0.6rem 0.8rem; border-radius:12px; border: 1px solid var(--line); transition: all 0.2s; margin-bottom:0.6rem; min-width: 0;" onmouseover="this.style.borderColor='var(--sepia)'" onmouseout="this.style.borderColor='var(--line)'">
         <div style="display:flex; align-items:center; gap: 0.8rem; min-width: 0; flex: 1;">
            <i class="fas fa-folder" style="color: var(--sepia-light); font-size:1.1rem; flex-shrink: 0;"></i>
            <span style="font-family:'Instrument Serif', serif; font-size:1.05rem; color:var(--ink); font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">${esc(c.isim)}</span>
         </div>
         <div style="display:flex; align-items:center; gap: 0.4rem; flex-shrink: 0; margin-left: 0.8rem;">
           <button type="button" onclick="event.stopPropagation(); toggleBookCol(${c.id}, ${!inCol})" style="background:${inCol ? 'var(--line)' : 'var(--accent)'}; color:${inCol ? 'var(--ink)' : '#fff'}; border:none; border-radius:50px; padding:0.4rem 0.9rem; font-family:'Geist', sans-serif; font-weight:600; font-size:0.75rem; cursor:pointer; transition: all 0.2s; display:flex; align-items:center; gap:0.4rem; white-space:nowrap;">
               ${inCol ? '<i class="fas fa-minus" style="font-size:0.6rem"></i> Çıkar' : '<i class="fas fa-plus" style="font-size:0.6rem"></i> Ekle'}
           </button>
           
           <div class="custom-dropdown share-dropdown" style="position:relative; display:inline-block; min-width: auto;">
             <button type="button" onclick="event.stopPropagation(); toggleShareMenu(this)" style="background:none; color:var(--muted); border:none; width:34px; height:34px; border-radius:50%; cursor:pointer; font-size: 1rem; transition: all 0.2s; display:flex; align-items:center; justify-content:center;" onmouseover="this.style.background='var(--line)'; this.style.color='var(--accent)';" onmouseout="this.style.background='none'; this.style.color='var(--muted)';" title="Paylaş">
                 <i class="fas fa-share-alt"></i>
             </button>
             <div class="dropdown-menu" style="right:0; top:calc(100% + 5px); min-width:180px; z-index:100; left:auto; width:auto; padding:0.4rem;">
                <button type="button" class="dropdown-item" role="menuitem" style="padding:0.6rem 0.8rem;" onclick="window.location.href='/api/share-collection/${c.id}'"><i class="fas fa-file-download"></i> JSON İndir</button>
                <button type="button" class="dropdown-item" role="menuitem" style="padding:0.6rem 0.8rem;" onclick="copyCollectionMarkdown(${c.id}, decodeURIComponent('${encodedName}'))"><i class="fas fa-copy"></i> Markdown Kopyala</button>
             </div>
           </div>

           <button type="button" onclick="event.stopPropagation(); deleteCollection(${c.id})" style="background:none; color:var(--muted); border:none; width:34px; height:34px; border-radius:50%; cursor:pointer; font-size: 0.9rem; transition: all 0.2s; display:flex; align-items:center; justify-content:center;" onmouseover="this.style.background='var(--danger-bg)'; this.style.color='var(--danger)'" onmouseout="this.style.background='none'; this.style.color='var(--muted)'" title="Koleksiyonu Sil">
               <i class="fas fa-trash-alt"></i>
           </button>
         </div>
      </div>
      `;
        }).join('');
      }

      const importBtn = `
        <div style="margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 1.2rem;">
          <button class="btn-modal-secondary" style="width:100%; padding: 0.9rem; border-radius: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 0.6rem; font-family:'Geist', sans-serif;" onclick="importCollection()">
            <i class="fas fa-file-import"></i> Dışarıdan Koleksiyon Aktar (JSON)
          </button>
        </div>
      `;
      list.innerHTML += importBtn;
      list.style.overflowX = 'hidden'; // Ensure no horizontal scroll

      const colModal = document.getElementById('col-modal');
      colModal.classList.add('open');
      document.body.classList.add('modal-open');
      activateModalFocus(colModal);
    }

    function toggleShareMenu(btn) {
      const container = btn.parentElement;
      const isOpen = container.classList.contains('open');
      // Close all dropdowns first
      document.querySelectorAll('.custom-dropdown').forEach(m => m.classList.remove('open'));
      if (!isOpen) container.classList.add('open');
    }

    async function deleteCollection(colId) {
      const ok = await (window.showAppConfirm ? window.showAppConfirm("Koleksiyonu silmek istediğinize emin misiniz? (İçindeki kitaplar silinmez, sadece liste silinir)", "Koleksiyonu Sil", "Sil", true) : Promise.resolve(confirm("Koleksiyonu silmek istediğinize emin misiniz?")));
      if (!ok) return;
      try {
        const res = await apiFetch(`/api/collections/${colId}`, { method: 'DELETE' });
        if (res?.ok) {
          // Remove this collection ID from the local books cache
          (window.allBooks || []).forEach(b => {
            if (b.collections) {
              b.collections = b.collections.filter(c => String(c) !== String(colId));
            }
          });

          // If the deleted collection is currently filtered, return to all
          if (window.activeCollection === String(colId)) {
            window.activeCollection = 'all';
            render();
          }

          await loadCollectionsFromAPI();
          if (window.colTargetHash) openColModal(window.colTargetHash);
        } else {
          showToast("Sunucudan silme isteği başarısız oldu.", "error");
        }
      } catch (e) {
        console.error("Koleksiyon silinirken hata:", e);
        showToast("Bağlantı hatası: Sunucu ile iletişim kurulamadı.", "error");
      }
    }

    async function createCollection() {
      const input = document.getElementById('new-col-name');
      const name = input?.value?.trim();
      if (!name) return;
      try {
        const res = await apiFetch('/api/collections', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ isim: name })
        });
        if (res?.ok) {
          input.value = '';
          await loadCollectionsFromAPI();
          if (window.colTargetHash) openColModal(window.colTargetHash);
        }
      } catch (e) {
        console.warn("createCollection failed:", e);
      }
    }

    function updateBookCollectionMemory(hash, colId, checked) {
      const book = (window.allBooks || []).find(b => b.hash === hash);
      if (!book) return;
      if (!Array.isArray(book.collections)) book.collections = [];
      if (checked) {
        if (!book.collections.includes(colId)) book.collections.push(colId);
      } else {
        book.collections = book.collections.filter(c => String(c) !== String(colId));
      }
    }

    async function toggleBookCol(colId, checked) {
      if (!window.colTargetHash) return;
      const method = checked ? 'POST' : 'DELETE';
      const bodyStr = checked ? JSON.stringify({ kitap_hash: window.colTargetHash }) : null;
      let url = `/api/collections/${colId}/books`;
      if (!checked) url += `/${window.colTargetHash}`;

      try {
        const req = { method, headers: { 'Content-Type': 'application/json' } };
        if (checked) req.body = bodyStr;
        const res = await apiFetch(url, req);
        if (res?.ok) {
          updateBookCollectionMemory(window.colTargetHash, colId, checked);
          if (window.activeCollection !== 'all') render(); // Refresh if filtering by it
          openColModal(window.colTargetHash);
        }
      } catch (e) {
        console.warn("toggleBookCol failed:", e);
      }
    }

    const customStyles = document.createElement('style');
    customStyles.innerHTML = `
.switch input:checked + .slider { background-color: var(--accent); }
.switch input:checked + .slider .knob { transform: translateX(14px); }
`;
    document.head.appendChild(customStyles);

    // --- STATISTICS ---
    function updateStats() {
      const total = window.allBooks?.length || 0;
      const statTotal = document.getElementById('stat-total');
      if (statTotal && statTotal.textContent !== String(total)) {
        statTotal.textContent = total;
        statTotal.classList.remove('stat-count-bump');
        void statTotal.offsetWidth;
        statTotal.classList.add('stat-count-bump');
      }
      document.querySelectorAll('.stat-total-val').forEach(el => {
        if (el.textContent !== String(total)) {
          el.textContent = total;
          el.classList.remove('stat-count-bump');
          void el.offsetWidth;
          el.classList.add('stat-count-bump');
        }
      });
    }

    // --- FILTER (Feature 7: Enhanced with AND Logic) ---
    function getFiltered() {
      const q = document.getElementById('search-input')?.value?.toLowerCase() || '';

      return (window.allBooks || []).filter(b => {
        const matchCat = window.activeCategory === 'all' || b.category === window.activeCategory;
        const matchCol = window.activeCollection === 'all' || (b.collections?.map(String).includes(String(window.activeCollection)));
        const matchQ = !q || [b.title, b.author, b.category, b.subcat, b.summary, b.keywords].some(v => v?.toLowerCase().includes(q));
        const matchFav = !window.showOnlyFav || b.is_favorite === true;
        return matchCat && matchCol && matchQ && matchFav;
      });
    }

    function clearFiltersAndSearch() {
      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.value = '';
      window.activeCategory = 'all';
      window.activeCollection = 'all';
      window.showOnlyFav = false;
      const favBtn = document.getElementById('btn-fav-filter');
      if (favBtn) favBtn.classList.remove('active');
      const catTrigger = document.getElementById('category-trigger');
      if (catTrigger) catTrigger.textContent = 'Tüm Kategoriler';
      const colTrigger = document.getElementById('collection-trigger');
      if (colTrigger) colTrigger.textContent = 'Tüm Koleksiyonlar';
      render();
    }
    window.clearFiltersAndSearch = clearFiltersAndSearch;

    function renderGridSkeletons(count = 8) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      const activeUploads = Array.from(grid.querySelectorAll('.uploading')).filter(node => {
        const tempId = node.dataset.tempId;
        return tempId && typeof uploadingCards !== 'undefined' && uploadingCards.has(tempId);
      });
      grid.innerHTML = '';
      activeUploads.forEach(node => grid.appendChild(node));
      for (let i = 0; i < count; i++) {
        const card = document.createElement('div');
        card.className = 'book-card skeleton';
        card.innerHTML = `
          <div class="card-cover skeleton skeleton-shimmer"></div>
          <div class="card-body">
            <div class="skeleton-line skeleton-shimmer" style="width: 75%; height: 18px; margin-bottom: 8px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 45%; height: 13px; margin-bottom: 12px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 90%; height: 11px; margin-bottom: 6px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 65%; height: 11px;"></div>
          </div>
        `;
        grid.appendChild(card);
      }
    }
    window.renderGridSkeletons = renderGridSkeletons;

    function updateEmptyStateUI(emptyState, booksCount) {
      if (!emptyState) return;
      if (booksCount > 0) {
        emptyState.style.display = 'none';
        return;
      }
      emptyState.style.display = 'flex';
      const isSearching = Boolean(document.getElementById('search-input')?.value.trim() || window.activeCategory !== 'all' || window.activeCollection !== 'all' || window.showOnlyFav);
      const titleEl = document.getElementById('empty-state-title');
      const descEl = document.getElementById('empty-state-desc');
      const clearBtn = document.getElementById('btn-empty-clear');

      if (titleEl) {
        titleEl.textContent = isSearching ? 'Eşleşen Kitap Bulunamadı' : 'Kütüphaneniz Henüz Boş';
      }
      if (descEl) {
        descEl.textContent = isSearching
          ? 'Arama kriterlerinize uygun kitap bulunamadı. Filtreleri temizleyerek tüm kütüphaneyi görebilirsiniz.'
          : 'PDF, EPUB veya TXT kitaplarınızı sürükleyip bırakarak veya dosya seçerek hemen okumaya başlayabilirsiniz.';
      }
      if (clearBtn) {
        clearBtn.style.display = isSearching ? 'inline-flex' : 'none';
      }
    }

    // --- RENDER ---
    function render() {
      const books = getFiltered();
      const resultInfo = document.getElementById('result-info');
      if (resultInfo) resultInfo.textContent = `${books.length} kitap gösteriliyor`;
      const emptyState = document.getElementById('empty-state');
      updateEmptyStateUI(emptyState, books.length);

      renderRecentShelf();

      if (window.currentView === 'grid') {
        renderGrid(books);
        setTimeout(enableDragSort, 100);
      } else if (window.currentView === 'table') {
        renderTable(books);
      }
      window.shouldStagger = false;
    }

    function renderRecentShelf() {
      const container = document.getElementById('recent-shelf-container');
      if (!container) return;

      const searchVal = document.getElementById('search-input')?.value?.trim() || '';
      const isFilterActive = (searchVal !== '') ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      if (window.currentView !== 'grid' || isFilterActive || !window.allBooks || window.allBooks.length <= 4) {
        container.style.display = 'none';
        container.innerHTML = '';
        return;
      }

      const recentBooks = window.allBooks.slice(0, 4);
      if (!recentBooks.length) {
        container.style.display = 'none';
        return;
      }

      container.style.display = 'block';
      container.innerHTML = `
        <div class="recent-shelf-header">
          <div class="recent-shelf-title">
            <span class="shelf-label">SEÇKİ &amp; SON EKLENENLER</span>
            <h3>Öne Çıkan Eserler</h3>
          </div>
          <span class="shelf-count">${recentBooks.length} Eser</span>
        </div>
        <div class="recent-shelf-grid">
          ${recentBooks.map(b => {
            const cover = b.has_cover
              ? `<img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')">`
              : `<div class="shelf-cover-placeholder"><i class="fas fa-book"></i></div>`;
            const progress = (typeof getBookReadingProgress === 'function') ? getBookReadingProgress(b) : null;
            const progressBar = progress ? `<div class="card-progress-bar" style="width: ${progress.pct}%;"></div>` : '';
            const progressBadge = progress ? `<span class="card-progress-badge" style="font-size:0.6rem; padding:0 4px; margin-left:6px;">%${progress.pct}</span>` : '';
            return `
              <button type="button" class="shelf-item" onclick="const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(this, target); else openWorkspace(target); }" aria-label="${esc(b.title)} - Kitabı Oku">
                <div class="shelf-item-cover">
                  ${cover}
                  ${progressBar}
                </div>
                <div class="shelf-item-info">
                  <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span class="shelf-item-cat">${esc(b.category) || 'Genel'}</span>
                    ${progressBadge}
                  </div>
                  <h4 class="shelf-item-title">${esc(b.title) || 'İsimsiz'}</h4>
                  <span class="shelf-item-author">${esc(b.author) || 'Bilinmeyen Yazar'}</span>
                </div>
              </button>
            `;
          }).join('')}
        </div>
      `;
    }
    window.renderRecentShelf = renderRecentShelf;

    // --- PERSISTENT ELEMENT MAPS (60FPS ZERO-REBUILD ARCHITECTURE) ---
    function getBookReadingProgress(b) {
      if (!b) return null;
      const readPage = Number.parseInt(b.okunulan_sayfa || b.read_page || 0, 10);
      const totalPages = Number.parseInt(b.sayfa_sayisi || b.pages || b.page_count || 0, 10);
      if (readPage > 0 && totalPages > 0) {
        const pct = Math.min(100, Math.max(1, Math.round((readPage / totalPages) * 100)));
        return { readPage, totalPages, pct };
      }
      return null;
    }
    window.getBookReadingProgress = getBookReadingProgress;

    const cardElementsMap = new Map();
    window.cardElementsMap = cardElementsMap;
    const tableRowsMap = new Map();
    window.tableRowsMap = tableRowsMap;

    function createBookCardElement(b) {
      const card = document.createElement('div');
      card.className = 'book-card';
      card.id = `book-${b.hash}`;
      card.dataset.hash = b.hash;

      const coverInner = b.has_cover
        ? `<img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')">`
        : `<div class="card-cover-placeholder">${BOOK_ICON_LG}<span>${esc(b.title) || 'Kapak yok'}</span></div>`;

      const favIcon = b.is_favorite
        ? `<i class="fas fa-heart" style="color: var(--danger); font-size: 1.1rem;"></i>`
        : `<i class="far fa-heart" style="color: var(--paper); font-size: 1.1rem;"></i>`;
      const favBtnText = b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle';

      const progress = getBookReadingProgress(b);
      const progressBarHtml = progress
        ? `<div class="card-progress-bar" style="width: ${progress.pct}%;" title="%${progress.pct} okundu (${progress.readPage}/${progress.totalPages} sayfa)"></div>`
        : '';
      const progressBadgeHtml = progress
        ? `<span class="card-progress-badge">%${progress.pct}</span>`
        : '';

      card.innerHTML = `
        <div class="selection-indicator"></div>
        <div class="card-cover">
          <div class="card-cat-badge">${esc(b.category)}</div>
          <button type="button" class="btn-favorite-card" onclick="event.stopPropagation(); toggleFavorite('${b.hash}')" title="${favBtnText}" aria-label="${favBtnText}">
             ${favIcon}
          </button>
          ${coverInner}
          ${progressBarHtml}
        </div>
        <div class="card-body">
          <div class="card-title">${esc(b.title) || '<em>İsimsiz</em>'}</div>
          <div class="card-author" style="display:flex; align-items:center; justify-content:space-between;">
            <span>${esc(b.author) || 'Bilinmeyen Yazar'}</span>
            ${progressBadgeHtml}
          </div>
        </div>
      `;

      let prefetchHoverTimer = null;
      card.addEventListener('pointerenter', () => {
        prefetchHoverTimer = setTimeout(() => {
          if (typeof window.prefetchPdfDocument === 'function') {
            window.prefetchPdfDocument(b.hash);
          }
        }, 150);
      });

      card.addEventListener('pointerleave', () => {
        if (prefetchHoverTimer) {
          clearTimeout(prefetchHoverTimer);
          prefetchHoverTimer = null;
        }
        if (typeof window.cancelPdfPrefetch === 'function') {
          window.cancelPdfPrefetch(b.hash);
        }
      });

      card.onclick = () => {
        if (window.isSelectionMode) {
          toggleSelectBook(card, b.hash);
        } else {
          const bookObj = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          openModal(bookObj);
        }
      };

      return card;
    }

    // --- GRID ---
    function renderGrid(books) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      const activeUploads = Array.from(grid.querySelectorAll('.uploading')).filter(node => {
        const tempId = node.dataset.tempId;
        return tempId && typeof uploadingCards !== 'undefined' && uploadingCards.has(tempId);
      });

      const isSearchingOrFiltering = Boolean(document.getElementById('search-input')?.value?.trim()) ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      const doStagger = Boolean(window.shouldStagger) && !isSearchingOrFiltering;
      const filteredHashes = new Set(books.map(b => b.hash));

      // 1. Ensure cards exist in cardElementsMap for all available books
      const allBooksList = window.allBooks || books;
      allBooksList.forEach(b => {
        if (!cardElementsMap.has(b.hash)) {
          cardElementsMap.set(b.hash, createBookCardElement(b));
        }
      });

      // 2. Clean up removed books from cardElementsMap
      if (window.allBooks) {
        const currentHashes = new Set(window.allBooks.map(b => b.hash));
        for (const [hash, card] of cardElementsMap.entries()) {
          if (!currentHashes.has(hash)) {
            card.remove();
            cardElementsMap.delete(hash);
          }
        }
      }

      // 3. Synchronize existing DOM
      const existingCardsInGrid = new Set(Array.from(grid.querySelectorAll('.book-card')).map(c => c.dataset.hash));
      let hasMissingCards = false;

      books.forEach((b, i) => {
        let card = cardElementsMap.get(b.hash);
        if (!card) {
          card = createBookCardElement(b);
          cardElementsMap.set(b.hash, card);
        }

        // Update favorite & selection visual state without re-creating card
        const favBtn = card.querySelector('.btn-favorite-card');
        if (favBtn) {
          favBtn.innerHTML = b.is_favorite
            ? `<i class="fas fa-heart" style="color: var(--danger); font-size: 1.1rem;"></i>`
            : `<i class="far fa-heart" style="color: var(--paper); font-size: 1.1rem;"></i>`;
        }
        card.classList.toggle('selected', selectedBooks.has(b.hash));

        // Controlled stagger or instant display
        if (doStagger) {
          card.classList.add('stagger-in');
          const staggerIdx = i < 12 ? i : 0;
          card.style.setProperty('--card-index', staggerIdx);
          card.style.animationDelay = i < 12 ? `${i * 30}ms` : '0ms';
        } else {
          card.classList.remove('stagger-in');
          card.style.animation = 'none';
        }

        card.style.display = '';

        if (!existingCardsInGrid.has(b.hash)) {
          hasMissingCards = true;
        }
      });

      // Hide cards in DOM that are filtered out (Zero DOM removal, zero image reloads)
      for (const [hash, card] of cardElementsMap.entries()) {
        if (!filteredHashes.has(hash)) {
          card.style.display = 'none';
        }
      }

      // Populate if cards were missing or grid was empty
      if (hasMissingCards || grid.querySelectorAll('.book-card').length === 0) {
        grid.innerHTML = '';
        activeUploads.forEach(node => grid.appendChild(node));
        books.forEach(b => {
          const card = cardElementsMap.get(b.hash);
          if (card) grid.appendChild(card);
        });
      }
    }

    async function uploadCover(hash, input) {
      if (!input?.files?.[0]) return;
      const file = input.files[0];
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await apiFetch(`/api/books/${hash}/cover`, {
          method: 'POST',
          body: formData
        });
        if (res?.ok) {
          showToast('Kapak başarıyla güncellendi.', 'success');
          loadBooksFromAPI().catch(err => console.error(err));
          closeModalDirect();
        }
      } catch (err) {
        console.error('Kapak yüklenemedi:', err);
      }
    }

    function createTableRowElement(b) {
      const tr = document.createElement('tr');
      tr.id = `book-${b.hash}`;
      tr.dataset.hash = b.hash;

      const thumbCell = b.has_cover
        ? `<td class="td-cover"><img src="/thumbnails/${b.hash}.jpg" alt="" loading="lazy" decoding="async"></td>`
        : `<td class="td-cover"><div class="td-cover-empty">${BOOK_ICON_SM}</div></td>`;
      tr.innerHTML = `
        ${thumbCell}
        <td class="td-title">${esc(b.title) || '—'}</td>
        <td class="td-author">${esc(b.author) || '—'}</td>
        <td class="td-cat">${esc(b.category) || '—'}</td>
        <td class="td-cat">${esc(b.subcat) || '—'}</td>
        <td class="td-summary"><div class="summary-text">${esc(b.summary)}</div></td>
      `;

      tr.onclick = () => {
        if (window.isSelectionMode) {
          toggleSelectBook(tr, b.hash);
        } else {
          const bookObj = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          openModal(bookObj);
        }
      };

      return tr;
    }

    // --- TABLE ---
    function renderTable(books) {
      const tbody = document.getElementById('table-body');
      if (!tbody) return;

      const isSearchingOrFiltering = Boolean(document.getElementById('search-input')?.value?.trim()) ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      const doStagger = Boolean(window.shouldStagger) && !isSearchingOrFiltering;
      const filteredHashes = new Set(books.map(b => b.hash));

      // 1. Ensure rows exist in tableRowsMap
      const allBooksList = window.allBooks || books;
      allBooksList.forEach(b => {
        if (!tableRowsMap.has(b.hash)) {
          tableRowsMap.set(b.hash, createTableRowElement(b));
        }
      });

      // 2. Clean up removed rows from tableRowsMap
      if (window.allBooks) {
        const currentHashes = new Set(window.allBooks.map(b => b.hash));
        for (const [hash, tr] of tableRowsMap.entries()) {
          if (!currentHashes.has(hash)) {
            tr.remove();
            tableRowsMap.delete(hash);
          }
        }
      }

      // 3. Synchronize existing DOM
      const existingRowsInTbody = new Set(Array.from(tbody.querySelectorAll('tr')).map(r => r.dataset.hash));
      let hasMissingRows = false;

      books.forEach((b, i) => {
        let tr = tableRowsMap.get(b.hash);
        if (!tr) {
          tr = createTableRowElement(b);
          tableRowsMap.set(b.hash, tr);
        }

        tr.classList.toggle('selected', selectedBooks.has(b.hash));

        if (doStagger) {
          tr.classList.add('stagger-in');
          const staggerIdx = i < 12 ? i : 0;
          tr.style.setProperty('--card-index', staggerIdx);
          tr.style.animationDelay = i < 12 ? `${i * 30}ms` : '0ms';
        } else {
          tr.classList.remove('stagger-in');
          tr.style.animation = 'none';
        }

        tr.style.display = '';

        if (!existingRowsInTbody.has(b.hash)) {
          hasMissingRows = true;
        }
      });

      // Hide rows that are filtered out
      for (const [hash, tr] of tableRowsMap.entries()) {
        if (!filteredHashes.has(hash)) {
          tr.style.display = 'none';
        }
      }

      // Populate if missing rows or empty tbody
      if (hasMissingRows || tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '';
        books.forEach(b => {
          const tr = tableRowsMap.get(b.hash);
          if (tr) tbody.appendChild(tr);
        });
      }
    }

    function compareTableValues(va, vb, sortDir) {
      if (va < vb) return -sortDir;
      if (va > vb) return sortDir;
      return 0;
    }

    // --- SIRALA ---
    function sortTable(col) {
      const keys = ['title', 'author', 'category', 'subcat', 'summary'];
      if (window.sortCol === col) window.sortDir *= -1; else { window.sortCol = col; window.sortDir = 1; }
      (window.allBooks || []).sort((a, b) => {
        const va = (a[keys[col]] || '').toLowerCase();
        const vb = (b[keys[col]] || '').toLowerCase();
        return compareTableValues(va, vb, window.sortDir);
      });
      document.querySelectorAll('thead th').forEach((th, i) => {
        const dataCol = i - 1; // first th is cover column (index 0), data columns start from 1
        th.classList.toggle('sorted', dataCol === col);
        const arrow = th.querySelector('.sort-arrow');
        if (arrow) {
          if (dataCol !== col) {
            arrow.textContent = '↕';
          } else {
            arrow.textContent = window.sortDir === 1 ? '↑' : '↓';
          }
        }
      });
      render();
    }

    // --- MODAL ---
    function openModal(b) {
      window.currentModalHash = b.hash;
      const isAnalyzed = Boolean(b.category && b.category !== 'Bilinmeyen' && b.category !== 'Bilinmiyor' && (!b.summary || (!b.summary.includes('Analiz başarısız') && !b.summary.includes('API anahtarı yok'))));
      const keywordChips = b.keywords
        ? b.keywords.split(',').map(k => {
          const kv = k.trim();
          if (!kv) return '';
          const encodedKeyword = encData(kv);
          return `<span class="meta-chip" style="cursor:pointer" data-keyword="${encodedKeyword}" onclick="const keyword = decodeURIComponent(this.dataset.keyword); closeModalDirect(); const si = document.getElementById('search-input'); if(si){ si.value = keyword; si.dispatchEvent(new Event('input')); }">${esc(kv)}</span>`;
        }).join('')
        : '';

      const coverHtml = b.has_cover
        ? `<div class="modal-cover-wrap"><img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')" style="width:200px; height:266px; object-fit:cover; border-radius:8px; box-shadow:0 10px 30px var(--shadow);"></div>`
        : `<div class="modal-cover-wrap"><div class="modal-cover-empty" style="width:200px; height:266px; background:var(--sepia-pale); border-radius:8px; display:flex; align-items:center; justify-content:center;">${BOOK_ICON_LG}</div></div>`;

      const progress = getBookReadingProgress(b);
      const progressModalHtml = progress ? `
        <div class="modal-progress-wrap">
          <div class="modal-progress-track">
            <div class="modal-progress-fill" style="width: ${progress.pct}%;"></div>
          </div>
          <span>%${progress.pct} (${progress.readPage} / ${progress.totalPages} sayfa)</span>
        </div>
      ` : '';

      document.getElementById('modal-content').innerHTML = `
    <div class="modal-layout" style="display: flex; gap: 2.5rem; padding: 2.5rem;">
      <div class="modal-left" style="width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem;">
        ${coverHtml}
        ${progressModalHtml}
        <div class="modal-actions" id="modal-actions-sidebar" style="display: flex; flex-direction: column; gap: 0.75rem;">
          <button class="btn-modal-primary" onclick="closeModalDirect(); const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); const card = document.querySelector('.book-card[data-hash=\\'${b.hash}\\']'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(card, target); else openWorkspace(target); }">
            <i class="fas fa-book-open"></i> Kitabı Oku
          </button>
          <button id="btn-modal-fav" class="${b.is_favorite ? 'btn-modal-fav is-fav' : 'btn-modal-fav'}" onclick="toggleFavorite('${b.hash}')">
            <i class="${b.is_favorite ? 'fas' : 'far'} fa-heart"></i> ${b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle'}
          </button>
          <button class="btn-modal-secondary" onclick="openColModal('${b.hash}')">
            <i class="fas fa-folder-plus"></i> Koleksiyona Ekle
          </button>
          <button class="btn-modal-secondary btn-cover-upload">
            <i class="fas fa-image"></i> Kapak Değiştir
            <input type="file" accept="image/*" onchange="uploadCover('${b.hash}', this)">
          </button>
          <button class="btn-modal-secondary" onclick="toggleEditMode('${b.hash}')">
            <i class="fas fa-edit"></i> Düzenle
          </button>
          ${!isAnalyzed ? `
          <button class="btn-modal-secondary" id="btn-reanalyze-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" style="background:var(--warn-bg); border:1px solid var(--warn); color:var(--warn); font-weight:600;">
            <i class="fas fa-magic"></i> Yapay Zeka ile Analiz Et
          </button>
          ` : ''}
          <button class="btn-modal-secondary" style="font-size:0.75rem;" onclick="window.open('/api/download/${b.hash}', '_blank')">
            <i class="fas fa-download"></i> PDF İndir
          </button>
          <div class="export-dropdown-wrapper" style="position:relative; width:100%;">
            <button class="btn-modal-secondary" style="font-size:0.75rem; width:100%; justify-content:center;" onclick="toggleExportMenu('${b.hash}')">
              <i class="fas fa-file-export"></i> Dışa Aktar (PKM) <i class="fas fa-chevron-down" style="font-size:0.65rem; margin-left:auto;"></i>
            </button>
            <div id="export-menu-${b.hash}" class="export-menu" style="display:none; position:absolute; top:100%; left:0; right:0; background:var(--color-surface, #fff); border:1px solid var(--line); border-radius:8px; box-shadow:0 8px 16px rgba(0,0,0,0.12); z-index:100; margin-top:4px; overflow:hidden;">
              <a href="/api/books/${b.hash}/export/obsidian" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer;" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-gem" style="color:var(--accent);"></i> Obsidian Notu (.md)
              </a>
              <a href="/api/books/${b.hash}/export/anki" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer; border-top:1px solid var(--line);" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-clone" style="color:var(--accent);"></i> Anki Kartları (.tsv)
              </a>
              <a href="/api/books/${b.hash}/export/bibtex" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer; border-top:1px solid var(--line);" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-graduation-cap" style="color:var(--accent);"></i> BibTeX Akademik (.bib)
              </a>
            </div>
          </div>
          ${b.file?.toLowerCase().endsWith('.pdf') ? `
          <button class="btn-modal-secondary" id="btn-compress-${b.hash}" style="font-size:0.75rem;" onclick="compressBook('${b.hash}')" title="Gereksiz verileri temizleyip PDF boyutunu yerel olarak küçültür">
            <i class="fas fa-compress-arrows-alt" style="color:var(--accent);"></i> Boyutu Küçült (Optimize Et)
          </button>
          ` : ''}
          <button class="btn-modal-danger" onclick="deleteBook('${b.hash}')">
            <i class="fas fa-trash-alt"></i> Kaydı Sil
          </button>
        </div>
        <div class="modal-meta-left" style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem;">
          <span class="meta-chip" style="font-size: 0.6rem; opacity: 0.85; word-break: break-all; white-space: normal; line-height: 1.4; padding: 0.5rem; text-align: center;">${esc(b.file)}</span>
        </div>
      </div>
      <div class="modal-right" style="flex: 1; border-left: 1px solid var(--line); padding-left: 2rem;">
        <div class="modal-cat" style="color: var(--accent); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.1em;">${esc(b.category)}${b.subcat ? ' / ' + esc(b.subcat) : ''}</div>
        <h2 class="modal-title" id="modal-book-title" style="margin-top: 0.5rem; font-size: 2.2rem; font-family:'Instrument Serif', serif; line-height: 1.1;">${esc(b.title) || 'İsimsiz Kitap'}</h2>
        <div class="modal-author" style="margin-bottom: 1.5rem; font-style: italic; font-size: 1.1rem; color: var(--muted); opacity: 0.9;">${esc(b.author) || 'Bilinmeyen Yazar'}</div>

        ${(!b.category || b.category === 'Bilinmeyen' || b.summary?.includes('Analiz başarısız')) ? `
          <div style="background: var(--warn-bg); border: 1px solid var(--warn); border-radius: var(--r-md); padding: 1.2rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
            <div>
              <div style="font-weight: 600; color: var(--warn); font-size: 0.95rem; display:flex; align-items:center; gap:0.5rem;">
                <i class="fas fa-exclamation-triangle"></i> Yapay Zeka Analizi Bekliyor
              </div>
              <div style="font-size: 0.82rem; color: var(--muted); margin-top: 0.3rem;">
                Bu kitabın başlığı, yazarı ve özeti henüz yapay zeka ile incelenmedi.
              </div>
            </div>
            <button id="btn-reanalyze-banner-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" class="btn btn--primary" style="white-space: nowrap;">
              <i class="fas fa-wand-magic-sparkles"></i> Şimdi Analiz Et
            </button>
          </div>
        ` : ''}
        
        <div class="modal-section-label" style="font-size: 0.65rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 0.5rem;">ÖZET</div>
        <p class="modal-summary" style="text-align: left; line-height: 1.8; font-size: 1.05rem; margin-bottom: 2rem;">${esc(b.summary) || 'Özet bulunamadı.'}</p>
        
        ${keywordChips ? `<div class="modal-section-label" style="font-size: 0.65rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 0.5rem;">ANAHTAR KAVRAMLAR</div><div class="modal-keywords" style="margin-bottom: 1.5rem;">${keywordChips}</div>` : ''}

        <div id="edit-form-${b.hash}" style="display:none; margin-top: 2rem; border-top: 1px solid var(--line); padding-top: 1.5rem;">
          <div style="display:grid; gap: 1rem;">
            <input type="text" id="edit-title-${b.hash}" class="modal-edit-input" value="${esc(b.title)}" placeholder="Kitap Adı" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <input type="text" id="edit-author-${b.hash}" class="modal-edit-input" value="${esc(b.author)}" placeholder="Yazar" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <textarea id="edit-summary-${b.hash}" class="modal-edit-textarea" rows="5" onkeydown="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); saveBookEdit('${b.hash}'); }">${esc(b.summary)}</textarea>
            <button class="btn-modal-save" onclick="saveBookEdit('${b.hash}')">DEĞİŞİKLİKLERİ KAYDET</button>
            <button type="button" class="btn-modal-secondary" id="btn-reanalyze-edit-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" style="font-size:0.8rem; justify-content:center; opacity:0.85; border:1px dashed var(--line); margin-top:0.25rem;">
              <i class="fas fa-magic"></i> Yapay Zeka ile Yeniden Analiz Et (Metadata Yenile)
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
      const modalEl = document.getElementById('modal');
      modalEl.classList.add('open');
      document.body.classList.add('modal-open');
      activateModalFocus(modalEl);
    }

    function showKeywordBooks(keyword) {
      const relatedBooks = (window.allBooks || []).filter(b => b.keywords?.split(',').map(m => m.trim()).includes(keyword));

      let listHtml = relatedBooks.map(b => `
    <div style="display:flex; align-items:center; gap:1rem; padding: 1rem; border-bottom: 1px solid var(--line); cursor:pointer; transition: background 0.2s;" onmouseover="this.style.background='rgba(196,168,130,0.12)'" onmouseout="this.style.background='transparent'" onclick="const target=(window.allBooks || []).find(x=>x.hash==='${b.hash}'); if(target) openModal(target);">
        <div style="width:45px; height:60px; flex-shrink:0; background:var(--sepia-pale); overflow:hidden; border-radius:3px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 10px var(--shadow);">
            ${b.has_cover ? `<img src="/thumbnails/${b.hash}.jpg" style="width:100%; height:100%; object-fit:cover;">` : BOOK_ICON_SM}
        </div>
        <div>
            <div style="font-family:'Instrument Serif',serif; font-weight:700; font-size:1.1rem; color:var(--ink); margin-bottom:0.2rem;">${esc(b.title)}</div>
            <div style="font-size:0.85rem; color:var(--muted); font-style:italic;">${esc(b.author)}</div>
        </div>
    </div>
  `).join('');

      document.getElementById('modal-content').innerHTML = `
    <div style="padding: 2.5rem;">
        <div class="modal-section-label" style="font-size:0.7rem; margin-top:0;">ANAHTAR KAVRAM</div>
        <div class="modal-title" style="margin-bottom: 1.5rem; color: var(--accent); font-size: 2.2rem;">${esc(keyword)}</div>
        <div style="max-height: 55vh; overflow-y: auto; padding-right: 0.5rem; border-top: 2px solid var(--sepia);">
            ${listHtml || '<div style="color:var(--muted); font-style:italic; padding-top:1rem;">Bu kavrama ait kitap bulunamadı.</div>'}
        </div>
    </div>
  `;
      document.getElementById('modal').classList.add('open');
      document.body.classList.add('modal-open');
      document.body.classList.add('modal-open');
    }

    // ── Unified Modal Exit Animation (Apple/Tesla Standard) ──

    // ═══════════════ F2: UNIVERSAL FOCUS TRAP & ACCESSIBILITY ═══════════════
    let modalFocusStack = [];

    function handleModalTabKey(e) {
      if (e.key !== 'Tab') return;
      const modalEl = this;
      const focusables = Array.from(modalEl.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter(el => el.offsetParent !== null || window.getComputedStyle(el).display !== 'none');

      if (focusables.length === 0) {
        e.preventDefault();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last || !modalEl.contains(document.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    function activateModalFocus(modalRef) {
      const modalEl = typeof modalRef === 'string' ? document.getElementById(modalRef) : modalRef;
      if (!modalEl) return;

      const prevActive = document.activeElement;
      modalFocusStack.push({ modal: modalEl, returnEl: prevActive });

      const focusables = Array.from(modalEl.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter(el => el.offsetParent !== null || window.getComputedStyle(el).display !== 'none');

      if (focusables.length > 0) {
        setTimeout(() => {
          const firstInput = focusables.find(el => (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && !el.readOnly);
          if (firstInput) {
            firstInput.focus();
          } else {
            focusables[0].focus();
          }
        }, 60);
      }

      modalEl.removeEventListener('keydown', handleModalTabKey);
      modalEl.addEventListener('keydown', handleModalTabKey);
    }
    window.activateModalFocus = activateModalFocus;

    function releaseModalFocus(modalRef) {
      const modalEl = typeof modalRef === 'string' ? document.getElementById(modalRef) : modalRef;
      if (!modalEl) return;
      modalEl.removeEventListener('keydown', handleModalTabKey);

      const idx = modalFocusStack.findLastIndex ? modalFocusStack.findLastIndex(e => e.modal === modalEl) : -1;
      let entry = null;
      if (idx !== -1) {
        entry = modalFocusStack.splice(idx, 1)[0];
      } else {
        entry = modalFocusStack.pop();
      }

      if (entry && entry.returnEl && typeof entry.returnEl.focus === 'function' && document.body.contains(entry.returnEl)) {
        setTimeout(() => entry.returnEl.focus(), 40);
      }
    }
    window.releaseModalFocus = releaseModalFocus;

    function closeModalWithAnimation(modalRef, callback) {
      let modal = modalRef;
      if (typeof modalRef === 'string') {
        modal = document.getElementById(modalRef);
      }
      if (!modal || modal.classList.contains('closing')) return;

      const isOpen = modal.classList.contains('open') || (modal.style.display && modal.style.display !== 'none');
      if (!isOpen) {
        if (typeof callback === 'function') callback();
        return;
      }

      releaseModalFocus(modal);
      modal.classList.add('closing');
      modal.classList.remove('open');

      setTimeout(() => {
        modal.classList.remove('closing');
        modal.style.display = '';
        const anyModal = document.querySelector('.modal-overlay.open, .modal-overlay.closing');
        if (!anyModal) {
          document.body.classList.remove('modal-open');
        }
        if (typeof callback === 'function') callback();
      }, 150);
    }
    window.closeModalWithAnimation = closeModalWithAnimation;

    function closeModal(e) { if (e.target === document.getElementById('modal')) closeModalDirect(); }
    function closeModalDirect() {
      closeModalWithAnimation('modal', () => {
        window.currentModalHash = null;
      });
    }

    // --- [D6: UYGULAMA İÇİ ŞIK ONAY DİYALOĞU (NATIVE CONFIRM YERİNE)] ---
    function showAppConfirm(message, title = 'Onay Gerekiyor', confirmText = 'Onayla', isDanger = true) {
      return new Promise((resolve) => {
        let overlay = document.getElementById('app-confirm-modal');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.id = 'app-confirm-modal';
          overlay.className = 'modal-overlay';
          overlay.innerHTML = `
            <div class="modal app-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
              <div class="confirm-dialog-header">
                <h3 id="confirm-dialog-title" class="confirm-dialog-title"></h3>
              </div>
              <div class="confirm-dialog-body">
                <p id="confirm-dialog-msg" class="confirm-dialog-msg"></p>
              </div>
              <div class="confirm-dialog-actions">
                <button type="button" class="btn-modal-secondary" id="confirm-dialog-cancel">Vazgeç</button>
                <button type="button" class="btn-modal-primary" id="confirm-dialog-ok">Onayla</button>
              </div>
            </div>
          `;
          document.body.appendChild(overlay);
        }

        const titleEl = overlay.querySelector('#confirm-dialog-title');
        const msgEl = overlay.querySelector('#confirm-dialog-msg');
        const okBtn = overlay.querySelector('#confirm-dialog-ok');
        const cancelBtn = overlay.querySelector('#confirm-dialog-cancel');

        titleEl.textContent = title;
        msgEl.textContent = message;
        okBtn.textContent = confirmText;

        if (isDanger) {
          okBtn.style.background = 'var(--danger, #b0473c)';
          okBtn.style.color = '#ffffff';
          okBtn.style.borderColor = 'var(--danger, #b0473c)';
        } else {
          okBtn.style.background = '';
          okBtn.style.color = '';
          okBtn.style.borderColor = '';
        }

        let isResolved = false;
        const cleanup = (result) => {
          if (isResolved) return;
          isResolved = true;
          window.removeEventListener('keydown', handleKey);
          closeModalWithAnimation(overlay, () => resolve(result));
        };

        const handleKey = (e) => {
          if (e.key === 'Escape') {
            e.preventDefault();
            cleanup(false);
          }
        };

        window.addEventListener('keydown', handleKey);
        okBtn.onclick = () => cleanup(true);
        cancelBtn.onclick = () => cleanup(false);
        overlay.onclick = (e) => {
          if (e.target === overlay) cleanup(false);
        };

        overlay.classList.add('open');
        document.body.classList.add('modal-open');
        activateModalFocus(overlay);
      });
    }
    window.showAppConfirm = showAppConfirm;

    // --- BULK OPERATIONS ---
    function toggleSelectionMode() {
      window.isSelectionMode = !window.isSelectionMode;
      selectedBooks.clear();

      document.body.classList.toggle('is-selection-mode', window.isSelectionMode);
      document.getElementById('bulk-bar').classList.toggle('active', window.isSelectionMode);
      document.getElementById('btn-manage').classList.toggle('active', window.isSelectionMode);

      updateBulkCount();
      render();
    }

    function toggleSelectBook(el, hash) {
      if (selectedBooks.has(hash)) {
        selectedBooks.delete(hash);
      } else {
        selectedBooks.add(hash);
      }
      el.classList.toggle('selected');
      updateBulkCount();
    }

    function updateBulkCount() {
      document.getElementById('bulk-count').textContent = selectedBooks.size;
      document.getElementById('bulk-delete-btn').disabled = selectedBooks.size === 0;
    }

    async function bulkDelete() {
      if (selectedBooks.size === 0) return;
      const ok = await (window.showAppConfirm ? window.showAppConfirm(`${selectedBooks.size} kitabı kalıcı olarak silmek istediğinize emin misiniz?`, 'Toplu Silme', 'Seçilenleri Sil', true) : Promise.resolve(confirm(`${selectedBooks.size} kitabı silmek istediğinize emin misiniz?`)));
      if (!ok) return;

      const toDelete = Array.from(selectedBooks);
      let successCount = 0;
      const failedBooks = [];

      // Open process center
      document.getElementById('ops-center').classList.add('active');

      const results = await Promise.allSettled(toDelete.map(async (hash) => {
        const book = (window.allBooks || []).find(b => b.hash === hash);
        const bookTitle = book ? book.title : hash;
        try {
          const resp = await apiFetch(`/api/books/${hash}`, { method: 'DELETE' });
          if (resp?.ok) return { ok: true, title: bookTitle };
          return { ok: false, title: bookTitle };
        } catch (e) {
          console.error("Bulk delete error for:", hash, e);
          return { ok: false, title: bookTitle };
        }
      }));

      for (const res of results) {
        if (res.status === 'fulfilled' && res.value.ok) {
          successCount++;
        } else if (res.status === 'fulfilled') {
          failedBooks.push(res.value.title);
        }
      }

      addChatMessage('ai', `${successCount} kitap başarıyla silindi.`);
      if (failedBooks.length > 0) {
        addChatMessage('ai', `⚠️ Şu kitaplar silinemedi: ${failedBooks.join(', ')}`);
      }
      toggleSelectionMode(); // Modu kapat ve listeyi yenile
      loadBooksFromAPI().catch(err => console.error("Reload error after bulk delete:", err));
    }

    function debounce(fn, delay = 250) {
      let timer = null;
      return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
      };
    }
    window.debounce = debounce;

    function openShortcutsModal() {
      const m = document.getElementById('shortcuts-modal');
      if (m) {
        m.classList.remove('closing');
        m.classList.add('open');
        document.body.classList.add('modal-open');
        activateModalFocus(m);
      }
    }
    function closeShortcutsModal() {
      closeModalWithAnimation('shortcuts-modal');
    }
    window.openShortcutsModal = openShortcutsModal;
    window.closeShortcutsModal = closeShortcutsModal;

    function isElementVisible(el) {
      return el && (el.classList.contains('open') || (el.style.display && el.style.display !== 'none'));
    }

    function isModalOrDropdownOpen() {
      const modalIds = [
        'handoff-modal',
        'shortcuts-modal',
        'telegram-modal',
        'pdf-note-modal',
        'workspace-reader',
        'col-modal',
        'modal',
        'book-modal',
        'settings-modal',
        'logs-modal',
        'duplicates-modal'
      ];
      return modalIds.some(id => isElementVisible(document.getElementById(id))) || document.body.classList.contains('modal-open');
    }

    function handleEscapeKeyPress() {
      const openDropdown = document.querySelector('.custom-dropdown.open');
      if (openDropdown) {
        openDropdown.classList.remove('open');
        return;
      }

      const modalCloseHandlers = [
        { id: 'handoff-modal', fn: window.closeHandoffModal },
        { id: 'shortcuts-modal', fn: closeShortcutsModal },
        { id: 'telegram-modal', fn: window.closeTelegramModal },
        { id: 'pdf-note-modal', fn: window.closePdfNoteModalDirect },
        { id: 'workspace-reader', fn: window.closeWorkspace },
        { id: 'duplicates-modal', fn: closeDuplicatesModal },
        { id: 'col-modal', fn: window.closeColModalDirect },
        { id: 'book-modal', fn: closeModalDirect },
        { id: 'modal', fn: closeModalDirect },
        { id: 'settings-modal', fn: window.closeSettingsDirect },
        { id: 'logs-modal', fn: window.closeLogsModalDirect },
      ];

      for (const { id, fn } of modalCloseHandlers) {
        if (isElementVisible(document.getElementById(id))) {
          if (typeof fn === 'function') fn();
          return;
        }
      }

      if (window.isDeepSearchActive && typeof closeDeepSearch === 'function') {
        closeDeepSearch();
      }
    }

    function handleGlobalViewShortcuts(key) {
      switch (key.toLowerCase()) {
        case '/':
        case 'k': {
          const sInput = document.getElementById('search-input');
          if (sInput) {
            sInput.focus();
            sInput.select();
          }
          break;
        }
        case '?':
          openShortcutsModal();
          break;
        case 'g':
          setView('grid');
          break;
        case 't':
          setView('table');
          break;
        case 's':
          setView('stats');
          break;
        case 'f':
          toggleFavFilter();
          break;
        case 'm':
          toggleSelectionMode();
          break;
        case 'd':
          toggleTheme();
          break;
      }
    }

    document.addEventListener('keydown', e => {
      // If typing in an input, textarea, or contentEditable, protect shortcuts
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable;
      if (isInput) {
        if (e.key === 'Escape') {
          e.target.blur();
        }
        return;
      }

      // Escape key closes modals in hierarchical order
      if (e.key === 'Escape') {
        handleEscapeKeyPress();
        return;
      }

      // Delete key inside book modal
      if (e.key === 'Delete' && window.currentModalHash) {
        void deleteBook(window.currentModalHash);
        return;
      }

      // Guard against hijacking browser shortcuts (Ctrl+F, Ctrl+S, Ctrl+T, Ctrl+N, Command on macOS)
      if (e.ctrlKey || e.metaKey || e.altKey) {
        return;
      }

      // Block global view shortcuts if any modal is currently open
      if (isModalOrDropdownOpen()) {
        return;
      }

      // Global Navigation Shortcuts
      if (['/', 'k', 'K', '?'].includes(e.key)) {
        e.preventDefault();
      }
      handleGlobalViewShortcuts(e.key);
    });

    const searchInputEl = document.getElementById('search-input');
    if (searchInputEl) {
      searchInputEl.addEventListener('input', debounce(() => {
        if (window.isDeepSearchActive) {
          void executeDeepSearch(searchInputEl.value);
        } else {
          render();
        }
      }, 250));
    }

    // --- VIEW SWITCH ---
    function setView(v) {
      window.currentView = v;
      const viewMap = {
        grid: document.getElementById('grid-view'),
        table: document.getElementById('table-view'),
        stats: document.getElementById('stats-view')
      };

      Object.entries(viewMap).forEach(([name, el]) => {
        if (!el) return;
        if (name === v) {
          el.style.display = name === 'grid' ? 'grid' : 'block';
          el.classList.remove('view-fade-in');
          el.getBoundingClientRect(); // Force reflow to cleanly restart the entrance animation
          el.classList.add('view-fade-in');
        } else {
          el.style.display = 'none';
          el.classList.remove('view-fade-in');
        }
      });

      const btnGrid = document.getElementById('btn-grid');
      const btnTable = document.getElementById('btn-table');
      const btnStats = document.getElementById('btn-stats');
      if (btnGrid) btnGrid.classList.toggle('active', v === 'grid');
      if (btnTable) btnTable.classList.toggle('active', v === 'table');
      if (btnStats) btnStats.classList.toggle('active', v === 'stats');

      window.shouldStagger = true;
      if (v === 'table') {
        renderTable(getFiltered());
      } else if (v === 'grid') {
        renderGrid(getFiltered());
        setTimeout(enableDragSort, 100);
      }
      window.shouldStagger = false;
      if (v === 'stats' && typeof loadStats === 'function') void loadStats();
    }


    // --- DRAG AND DROP SORTING ---
    function enableDragSort() {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      grid.querySelectorAll('.book-card[data-hash]').forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('dragenter', handleDragEnter);
        card.addEventListener('dragleave', handleDragLeave);
        card.addEventListener('drop', handleDrop);
        card.addEventListener('dragend', handleDragEnd);
      });
    }

    function handleDragStart(e) {
      window.dragSrcEl = this;
      this.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', this.dataset.hash);
    }
    function handleDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }
    function handleDragEnter(e) { this.classList.add('drag-over'); }
    function handleDragLeave(e) { this.classList.remove('drag-over'); }
    function handleDrop(e) {
      e.preventDefault();
      this.classList.remove('drag-over');
      const grid = document.getElementById('grid-view');
      if (!window.dragSrcEl || !grid?.contains(window.dragSrcEl)) return;
      if (window.dragSrcEl !== this) {
        const cards = [...grid.querySelectorAll('.book-card[data-hash]')];
        const fromIdx = cards.indexOf(window.dragSrcEl);
        const toIdx = cards.indexOf(this);
        if (fromIdx < toIdx) this.after(window.dragSrcEl);
        else this.before(window.dragSrcEl);
        // Sıralamayı localStorage'a kaydet
        const newOrder = [...grid.querySelectorAll('.book-card[data-hash]')].map(c => c.dataset.hash);
        window.customOrder = newOrder;
        localStorage.setItem('kutuphane-custom-order', JSON.stringify(newOrder));
        // Sıralamayı sunucuya senkronize et
        apiFetch('/api/books/order', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order: newOrder })
        }).catch(err => console.error("Sıralama sunucuya senkronize edilemedi:", err));
      }
    }
    function handleDragEnd(e) {
      document.querySelectorAll('.book-card').forEach(c => { c.classList.remove('dragging', 'drag-over'); });
    }

    async function reanalyzeBookModal(fileHash) {
      const btn = document.getElementById(`btn-reanalyze-${fileHash}`);
      const bannerBtn = document.getElementById(`btn-reanalyze-banner-${fileHash}`);
      const editBtn = document.getElementById(`btn-reanalyze-edit-${fileHash}`);
      const prevHtml = btn ? btn.innerHTML : '';
      const prevBannerHtml = bannerBtn ? bannerBtn.innerHTML : '';
      const prevEditHtml = editBtn ? editBtn.innerHTML : '';

      [btn, bannerBtn, editBtn].forEach(b => {
        if (b) {
          b.disabled = true;
          b.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yapay Zeka İnceliyor...';
        }
      });

      try {
        const res = await apiReanalyzeBook(fileHash);
        if (res.status === 'success') {
          const d = res.data || {};
          showToast(`Yapay zeka analizi başarıyla tamamlandı!\nKitap: ${d.kitap_adi || ''}\nYazar: ${d.yazar || ''}`, 'success');
          closeModalDirect();
          if (typeof loadBooksFromAPI === 'function') await loadBooksFromAPI();
        } else {
          showToast(`Analiz tamamlanamadı: ${res.message || 'API anahtarınızı kontrol edin.'}`, 'warning');
        }
      } catch (err) {
        showToast(`Hata: ${err.message || 'Analiz sırasında sorun oluştu.'}`, 'error');
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = prevHtml || '<i class="fas fa-magic"></i> Yapay Zeka ile Analiz Et';
        }
        if (bannerBtn) {
          bannerBtn.disabled = false;
          bannerBtn.innerHTML = prevBannerHtml || '<i class="fas fa-magic"></i> Şimdi Analiz Et';
        }
        if (editBtn) {
          editBtn.disabled = false;
          editBtn.innerHTML = prevEditHtml || '<i class="fas fa-magic"></i> Yapay Zeka ile Yeniden Analiz Et (Metadata Yenile)';
        }
      }
    }
    window.reanalyzeBookModal = reanalyzeBookModal;

    function toggleExportMenu(hash) {
      const menu = document.getElementById(`export-menu-${hash}`);
      if (!menu) return;
      const isOpen = menu.style.display === 'block';
      document.querySelectorAll('.export-menu').forEach(el => el.style.display = 'none');
      menu.style.display = isOpen ? 'none' : 'block';
    }
    window.toggleExportMenu = toggleExportMenu;

    const MODAL_BACKDROP_CLOSERS = {
      'modal': () => closeModalDirect(),
      'logs-modal': () => window.closeLogsModalDirect?.(),
      'settings-modal': () => window.closeSettingsDirect?.(),
      'col-modal': () => window.closeColModalDirect?.(),
      'pdf-note-modal': () => window.closePdfNoteModalDirect?.(),
      'telegram-modal': () => window.closeTelegramModal?.(),
      'shortcuts-modal': () => closeShortcutsModal(),
      'handoff-modal': () => window.closeHandoffModal?.(),
      'duplicates-modal': () => closeDuplicatesModal(),
    };

    function _handleBackdropClick(target) {
      if (!target?.classList) return;
      if (!target.classList.contains('modal-overlay') && !target.classList.contains('logs-modal')) return;
      const closer = MODAL_BACKDROP_CLOSERS[target.id];
      if (typeof closer === 'function') {
        closer();
      }
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.export-dropdown-wrapper')) {
        document.querySelectorAll('.export-menu').forEach(el => el.style.display = 'none');
      }
      // Backdrop click to close modals cleanly
      _handleBackdropClick(e.target);
    });

    // --- [10.3] Global Deep Search Helpers ---
    function _activateDeepSearchUI() {
      const toggleBtn = document.getElementById('btn-deep-search-toggle');
      const label = document.getElementById('deep-search-label');
      const input = document.getElementById('search-input');

      if (toggleBtn) {
        toggleBtn.style.background = 'var(--accent)';
        toggleBtn.style.color = '#fff';
        toggleBtn.style.borderColor = 'var(--accent)';
      }
      if (label) label.textContent = 'Derin Aktif';
      if (input) {
        input.placeholder = '500+ kitabın tüm cümlelerinde ara... (Derin Arama)';
        input.focus();
        if (input.value.trim()) {
          void executeDeepSearch(input.value.trim());
        }
      }
    }

    function _deactivateDeepSearchUI() {
      const toggleBtn = document.getElementById('btn-deep-search-toggle');
      const label = document.getElementById('deep-search-label');
      const input = document.getElementById('search-input');
      const resultsContainer = document.getElementById('deep-search-results');
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');

      if (toggleBtn) {
        toggleBtn.style.background = 'rgba(255,255,255,0.06)';
        toggleBtn.style.color = 'var(--muted)';
        toggleBtn.style.borderColor = 'var(--line)';
      }
      if (label) label.textContent = 'Derin Arama';
      if (input) {
        input.placeholder = 'Kitap, yazar, konu ara… (Kısayol: /)';
      }
      if (resultsContainer) resultsContainer.style.display = 'none';
      if (window.currentView === 'grid' && gridView) gridView.style.display = 'grid';
      if (window.currentView === 'table' && tableView) tableView.style.display = 'block';
      render();
    }

    function applyDeepSearchActiveUI(isActive) {
      if (isActive) {
        _activateDeepSearchUI();
      } else {
        _deactivateDeepSearchUI();
      }
    }

    function toggleDeepSearchMode() {
      window.isDeepSearchActive = !window.isDeepSearchActive;
      applyDeepSearchActiveUI(window.isDeepSearchActive);
    }
    window.toggleDeepSearchMode = toggleDeepSearchMode;

    function closeDeepSearch() {
      if (window.isDeepSearchActive) {
        toggleDeepSearchMode();
      }
    }
    window.closeDeepSearch = closeDeepSearch;

    function sanitizeDeepSnippet(snippet) {
      if (!snippet) return '';
      const tokenOpen = '___DEEP_MARK_OPEN___';
      const tokenClose = '___DEEP_MARK_CLOSE___';
      const safe = esc(
        String(snippet)
          .replace(/<mark class="deep-hl">/gi, tokenOpen)
          .replace(/<\/mark>/gi, tokenClose)
      )
        .replaceAll(tokenOpen, '<mark class="deep-hl">')
        .replaceAll(tokenClose, '</mark>');
      return safe;
    }

    function renderDeepSearchResults(results) {
      return results.map(r => {
        const coverHtml = r.has_cover
          ? `<img src="/thumbnails/${r.dosya_hash}.jpg" style="width:48px; height:64px; object-fit:cover; border-radius:6px; flex-shrink:0;">`
          : `<div style="width:48px; height:64px; background:var(--sepia-pale); border-radius:6px; display:flex; align-items:center; justify-content:center; flex-shrink:0;"><i class="fas fa-book" style="color:var(--muted);"></i></div>`;
        return `
          <div class="deep-search-card" style="display:flex; gap:1rem; padding:0.9rem 1.1rem; background:var(--paper); border:1px solid var(--line); border-radius:10px; align-items:center; transition:border-color 0.2s;" onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='var(--line)'">
            ${coverHtml}
            <div style="flex:1; min-width:0;">
              <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
                <span style="font-weight:700; color:var(--ink); font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(r.kitap_adi)}</span>
                <span style="font-size:0.75rem; color:var(--muted);">— ${esc(r.yazar)}</span>
                <span class="badge" style="background:var(--accent-glow); color:var(--accent); font-size:0.72rem; padding:1px 6px; border-radius:4px; font-weight:600; margin-left:auto;">Sayfa ${r.sayfa_no}</span>
              </div>
              <div class="deep-snippet" style="font-size:0.83rem; color:var(--text); line-height:1.45; font-family:var(--font-serif, serif);">${sanitizeDeepSnippet(r.snippet)}</div>
            </div>
            <button type="button" class="btn-empty-add" onclick="openWorkspaceAtPage('${r.dosya_hash}', ${r.sayfa_no})" style="padding:0.45rem 0.85rem; font-size:0.78rem; white-space:nowrap; margin-left:0.5rem; flex-shrink:0;">
              Sayfaya Git <i class="fas fa-arrow-right" style="margin-left:4px;"></i>
            </button>
          </div>
        `;
      }).join('');
    }

    function _restoreViewsForEmptyDeepSearch() {
      const resultsContainer = document.getElementById('deep-search-results');
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');
      const statsView = document.getElementById('stats-view');

      if (resultsContainer) resultsContainer.style.display = 'none';
      if (window.currentView === 'grid' && gridView) gridView.style.display = 'grid';
      if (window.currentView === 'table' && tableView) tableView.style.display = 'block';
      if (window.currentView === 'stats' && statsView) statsView.style.display = 'block';
    }

    function _showDeepSearchLoading() {
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');
      const statsView = document.getElementById('stats-view');
      const emptyState = document.getElementById('empty-state');
      const resultsContainer = document.getElementById('deep-search-results');
      const listEl = document.getElementById('deep-search-list');

      if (gridView) gridView.style.display = 'none';
      if (tableView) tableView.style.display = 'none';
      if (statsView) statsView.style.display = 'none';
      if (emptyState) emptyState.style.display = 'none';
      if (resultsContainer) resultsContainer.style.display = 'block';
      if (listEl) listEl.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--muted);"><i class="fas fa-spinner fa-spin"></i> Tüm kütüphane taranıyor...</div>';
    }

    async function executeDeepSearch(query) {
      const q = (query || '').trim();
      if (!q) {
        _restoreViewsForEmptyDeepSearch();
        return;
      }

      _showDeepSearchLoading();
      const listEl = document.getElementById('deep-search-list');
      const countEl = document.getElementById('deep-search-count');

      try {
        const res = await apiFetch(`/api/search/deep?q=${encodeURIComponent(q)}&limit=30`);
        if (!res?.ok) {
          if (listEl) listEl.innerHTML = '<div style="color:var(--accent); text-align:center; padding:1.5rem;">Arama sırasında hata oluştu.</div>';
          return;
        }
        const data = await res.json();
        const results = data.results || [];
        if (countEl) countEl.textContent = `${results.length} eşleşme`;

        if (results.length === 0) {
          if (listEl) listEl.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--muted);"><i class="fas fa-search" style="font-size:2rem; opacity:0.3; margin-bottom:0.5rem; display:block;"></i>Bu kelimeyi içeren herhangi bir kitap sayfası bulunamadı.</div>';
          return;
        }

        if (listEl) {
          listEl.innerHTML = renderDeepSearchResults(results);
        }
      } catch (err) {
        if (listEl) listEl.innerHTML = `<div style="color:var(--accent); text-align:center; padding:1.5rem;">Hata: ${esc(String(err))}</div>`;
      }
    }
    window.executeDeepSearch = executeDeepSearch;

    // --- [6.4] Mobile Handoff Deep-Link Auto-Opener ---
    document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const openHash = urlParams.get('open_book');
      const openPage = Number.parseInt(urlParams.get('page') || '1', 10);
      if (openHash) {
        setTimeout(() => {
          if (typeof openWorkspaceAtPage === 'function') {
            openWorkspaceAtPage(openHash, openPage);
          }
        }, 500);
      }
    });

    // ── [Option C] In-Place PDF Compression / Size Reducer ──
    async function compressBook(fileHash) {
      if (!fileHash) return;
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Bu PDF dosyasını kayıpsız/hafif JPEG sıkıştırma ile optimize etmek istiyor musunuz? Orijinal dosya güvenlik amacıyla yedeklenerek optimize edilir.', 'PDF Optimize Et', 'Optimize Et', false) : Promise.resolve(confirm('Bu PDF dosyasını optimize etmek istiyor musunuz?')));
      if (!ok) {
        return;
      }

      const btn = document.getElementById(`btn-compress-${fileHash}`) || document.querySelector(`button[onclick*="compressBook('${fileHash}')"]`);
      const prevHtml = btn ? btn.innerHTML : null;
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimize Ediliyor...';
      }

      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(fileHash)}/compress`, { method: 'POST' });
        if (res?.success) {
          showToast(`PDF Optimize Edildi!\nEski Boyut: ${res.old_mb} MB ➔ Yeni: ${res.new_mb} MB (%${res.reduction_percent} tasarruf)`, 'success');
          // Reload book list to reflect new size
          if (typeof reloadBooks === 'function') reloadBooks();
          // Update details modal if open
          const sizeEl = document.querySelector('#modal-content .book-info-row span:last-child');
          if (sizeEl) sizeEl.textContent = `${res.new_mb} MB`;
        } else {
          showToast(`${res?.message || 'Sıkıştırma tamamlandı.'}`, 'info');
        }
      } catch (err) {
        showToast(`Sıkıştırma hatası: ${err.message || 'İşlem gerçekleştirilemedi.'}`, 'error');
      } finally {
        if (btn && prevHtml) {
          btn.disabled = false;
          btn.innerHTML = prevHtml;
        }
      }
    }
    window.compressBook = compressBook;

    // ── [Option C] Duplicate Book Hunter ──
    async function openDuplicatesModal() {
      const modal = document.getElementById('duplicates-modal');
      const container = document.getElementById('duplicates-container');
      if (!modal || !container) return;

      modal.classList.remove('closing');
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      activateModalFocus(modal);
      container.innerHTML = '<div style="text-align:center; padding:2.5rem; color:var(--muted);"><i class="fas fa-spinner fa-spin fa-2x" style="margin-bottom:0.8rem; display:block; color:var(--accent);"></i>Kütüphane mükerrer kopyalar için taranıyor...</div>';

      try {
        const res = await apiFetch('/api/books/duplicates');
        if (!res?.duplicates?.length) {
          container.innerHTML = `
            <div style="text-align:center; padding:3rem 1.5rem; color:var(--muted);">
              <i class="fas fa-check-circle" style="font-size:3rem; color:#22c55e; margin-bottom:1rem; display:block;"></i>
              <h4 style="font-size:1.15rem; color:var(--ink); margin-bottom:0.4rem; font-weight:700;">Mükerrer Kitap Bulunamadı</h4>
              <p style="font-size:0.85rem;">Kütüphaneniz tertemiz! Aynı ada, yazara veya dosya boyutuna sahip yinelenen kitap tespit edilmedi.</p>
            </div>
          `;
          return;
        }

        renderDuplicateGroups(res.duplicates);
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--accent);">Tarama hatası: ${esc(String(err))}</div>`;
      }
    }
    window.openDuplicatesModal = openDuplicatesModal;

    function closeDuplicatesModal() {
      closeModalWithAnimation('duplicates-modal');
    }
    window.closeDuplicatesModal = closeDuplicatesModal;

    function renderDuplicateGroups(groups) {
      const container = document.getElementById('duplicates-container');
      if (!container) return;

      container.innerHTML = groups.map((g, gIdx) => {
        const itemsHtml = g.items.map(b => {
          const mb = b.dosya_boyutu ? (b.dosya_boyutu / (1024 * 1024)).toFixed(2) + ' MB' : 'Bilinmiyor';
          const p = b.sayfa_sayisi ? `${b.sayfa_sayisi} sayfa` : '';
          return `
            <div class="dup-item-card" id="dup-item-${b.dosya_hash}" style="display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1rem; background:var(--paper-dark); border:1px solid var(--line); border-radius:10px; gap:0.8rem;">
              <div style="min-width:0; flex:1;">
                <div style="font-weight:600; font-size:0.88rem; color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(b.kitap_adi || 'Başlıksız')}</div>
                <div style="font-size:0.76rem; color:var(--muted); display:flex; gap:0.6rem; margin-top:2px; flex-wrap:wrap;">
                  <span><i class="fas fa-file-alt"></i> ${mb}</span>
                  ${p ? `<span><i class="fas fa-bookmark"></i> ${p}</span>` : ''}
                  <span style="font-family:var(--font-mono, monospace); font-size:0.7rem; opacity:0.7;">#${b.dosya_hash.substring(0, 10)}</span>
                </div>
              </div>
              <div style="display:flex; gap:0.4rem; flex-shrink:0;">
                <button type="button" class="btn-sm" onclick="openWorkspaceAtPage('${b.dosya_hash}', 1)" style="padding:0.4rem 0.7rem; font-size:0.76rem; background:var(--paper); border:1px solid var(--line); border-radius:6px; cursor:pointer;" title="Kitabı Aç">
                  <i class="fas fa-eye"></i> İncele
                </button>
                <button type="button" class="btn-sm" onclick="deleteDuplicateBook('${b.dosya_hash}', this, 'dup-group-${gIdx}')" style="padding:0.4rem 0.7rem; font-size:0.76rem; background:rgba(176,71,60,0.12); color:#b0473c; border:1px solid rgba(176,71,60,0.25); border-radius:6px; cursor:pointer; font-weight:600;" title="Bu kopyayı sil">
                  <i class="fas fa-trash"></i> Kopyayı Sil
                </button>
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="dup-group-card" id="dup-group-${gIdx}" style="border:1px solid var(--line); border-radius:14px; padding:1.1rem; background:var(--paper); box-shadow:0 4px 12px rgba(0,0,0,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
              <div style="font-weight:700; font-size:0.95rem; color:var(--ink); display:flex; align-items:center; gap:0.5rem;">
                <i class="fas fa-clone" style="color:var(--accent);"></i> ${esc(g.title || 'Mükerrer Grup')}
                <span style="font-size:0.78rem; font-weight:400; color:var(--muted);">${g.author ? `— ${esc(g.author)}` : ''}</span>
              </div>
              <span class="badge" style="background:rgba(184,134,47,0.12); color:#b8862f; font-size:0.72rem; padding:2px 8px; border-radius:6px; font-weight:600;">
                ${g.items.length} Kopya Bulundu (${esc(g.reason || 'Benzerlik')})
              </span>
            </div>
            <div style="display:flex; flex-direction:column; gap:0.5rem;">
              ${itemsHtml}
            </div>
          </div>
        `;
      }).join('');
    }

    function updateDuplicateDOMAfterDelete(fileHash, groupId) {
      const itemEl = document.getElementById(`dup-item-${fileHash}`);
      if (itemEl) itemEl.remove();

      // Check if group now has <= 1 item left
      const groupEl = document.getElementById(groupId);
      if (groupEl) {
        const remaining = groupEl.querySelectorAll('.dup-item-card');
        if (remaining.length <= 1) {
          groupEl.remove();
        }
      }

      // Check if all groups are gone
      const container = document.getElementById('duplicates-container');
      if (container && !container.querySelector('.dup-group-card')) {
        container.innerHTML = `
          <div style="text-align:center; padding:3rem 1.5rem; color:var(--muted);">
            <i class="fas fa-check-circle" style="font-size:3rem; color:#22c55e; margin-bottom:1rem; display:block;"></i>
            <h4 style="font-size:1.15rem; color:var(--ink); margin-bottom:0.4rem; font-weight:700;">Tüm Mükerrer Kopyalar Temizlendi</h4>
          </div>
        `;
      }
    }

    async function deleteDuplicateBook(fileHash, btnEl, groupId) {
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Bu mükerrer kopyayı kalıcı olarak silmek istediğinize emin misiniz?', 'Kopyayı Sil', 'Sil', true) : Promise.resolve(confirm('Bu mükerrer kopyayı kalıcı olarak silmek istediğinize emin misiniz?')));
      if (!ok) return;

      if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      }

      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(fileHash)}`, { method: 'DELETE' });
        if (res && res.success !== false) {
          showToast('Kopya başarıyla silindi.', 'success');
          updateDuplicateDOMAfterDelete(fileHash, groupId);
          if (typeof reloadBooks === 'function') reloadBooks();
        } else {
          showToast(`Silme başarısız: ${res?.message || 'Hata oluştu'}`, 'error');
        }
      } catch (err) {
        showToast(`Silme hatası: ${err.message}`, 'error');
      } finally {
        if (btnEl) btnEl.disabled = false;
      }
    }
    window.deleteDuplicateBook = deleteDuplicateBook;

    // ── [Option C] Portable Full Library Zip Export ──
    function exportFullLibraryZip() {
      showToast('📦 Kütüphane zip arşivi hazırlanıyor...\nDosya boyutuna göre birkaç saniye sürebilir, lütfen bekleyin.', 'info');
      // Direct browser navigation to start streaming download
      window.location.href = '/api/database/export-full-zip';
    }
    window.exportFullLibraryZip = exportFullLibraryZip;

    // ── [Option B] PWA Install Prompt Handlers ──
    let deferredPwaPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPwaPrompt = e;
      const pwaBtn = document.getElementById('btn-pwa-install');
      const compactPwaBtn = document.getElementById('compact-pwa-install');
      if (pwaBtn) pwaBtn.style.display = 'inline-flex';
      if (compactPwaBtn) compactPwaBtn.style.display = 'flex';
    });

    window.addEventListener('appinstalled', () => {
      deferredPwaPrompt = null;
      const pwaBtn = document.getElementById('btn-pwa-install');
      const compactPwaBtn = document.getElementById('compact-pwa-install');
      if (pwaBtn) pwaBtn.style.display = 'none';
      if (compactPwaBtn) compactPwaBtn.style.display = 'none';
      showToast('🎉 Dijital Kütüphane uygulamanız başarıyla yüklendi!', 'success');
    });

    async function triggerPwaInstall() {
      if (!deferredPwaPrompt) {
        showToast('PWA yükleme yönergesi: Tarayıcınızın adres çubuğundaki (veya menüdeki) "Uygulamayı Yükle" simgesine basabilirsiniz.', 'info');
        return;
      }
      deferredPwaPrompt.prompt();
      const { outcome } = await deferredPwaPrompt.userChoice;
      if (outcome === 'accepted') {
        deferredPwaPrompt = null;
        const pwaBtn = document.getElementById('btn-pwa-install');
        const compactPwaBtn = document.getElementById('compact-pwa-install');
        if (pwaBtn) pwaBtn.style.display = 'none';
        if (compactPwaBtn) compactPwaBtn.style.display = 'none';
      }
    }
    window.triggerPwaInstall = triggerPwaInstall;

    // --- HEADER TOOLS MENU ---
    function toggleToolsMenu(event) {
      if (event) {
        event.stopPropagation();
      }
      const menu = document.getElementById('header-tools-menu');
      if (!menu) return;
      const isHidden = menu.style.display === 'none' || !menu.style.display;
      if (isHidden) {
        menu.classList.remove('closing');
        menu.style.display = 'flex';
        const firstItem = menu.querySelector('.tools-menu-item, button, a');
        if (firstItem) setTimeout(() => firstItem.focus(), 40);
      } else {
        closeToolsMenu();
      }
    }
    window.toggleToolsMenu = toggleToolsMenu;

    function closeToolsMenu() {
      const menu = document.getElementById('header-tools-menu');
      if (!menu || menu.style.display === 'none' || menu.classList.contains('closing')) return;
      menu.classList.add('closing');
      setTimeout(() => {
        menu.classList.remove('closing');
        menu.style.display = 'none';
        const trigger = document.getElementById('header-tools-btn');
        if (trigger) trigger.focus();
      }, 150);
    }
    window.closeToolsMenu = closeToolsMenu;

    document.addEventListener('click', (e) => {
      const wrapper = document.getElementById('header-tools-wrapper');
      if (wrapper && !wrapper.contains(e.target)) {
        closeToolsMenu();
      }
    });

```


## DOSYA 6.4: static/js/ui_workspace.js (Okuma Alanı, Mobil Bottom Sheet, Çift Tamponlama Zoom & Dinamik Başlık)

**Dosya Yolu:** `static/js/ui_workspace.js`

```javascript
/* ═══════════ ui_workspace.js — Workspace Reader, PDF.js Engine & Annotations ═══════════ */
    /* ═════════════════════════════════════════════════════════════
       Workspace Reader Functions (Split-Pane PDF + Contextual AI Chat)
       ═════════════════════════════════════════════════════════════ */
    let activeWorkspaceBook = null;
    let isWorkspaceChatLoading = false;
    let isFullBookLoaded = false;
    let activeTypewriterTimer = null;
    let activeTypewriterFullText = '';
    let activeTypewriterContainer = null;
    let isSpeaking = false;

    function jumpToPdfPage(pageNum) {
      const p = Number.parseInt(pageNum, 10);
      if (!p || Number.isNaN(p) || !pdfDoc || p < 1 || p > pdfPageCount) {
        if (typeof showToast === 'function') showToast(`Geçersiz sayfa numarası: ${pageNum}`, 'warning');
        return;
      }
      pdfPageNum = p;
      const pageInput = document.getElementById('pdf-page-num');
      if (pageInput) pageInput.value = p;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
      void renderPdfPageVirtual(p);
      scrollToPage(p);
      if (wrapper) {
        wrapper.classList.add('page-pulse');
        setTimeout(() => wrapper.classList.remove('page-pulse'), 1600);
      }
    }
    window.jumpToPdfPage = jumpToPdfPage;

    function stopChatGeneration() {
      if (activeTypewriterTimer) {
        clearInterval(activeTypewriterTimer);
        activeTypewriterTimer = null;
      }
      if (activeTypewriterContainer && activeTypewriterFullText) {
        activeTypewriterContainer.innerHTML = parseMarkdown(activeTypewriterFullText);
      }
      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'none';
      isWorkspaceChatLoading = false;
      const input = document.getElementById('workspace-chat-input');
      if (input) input.focus();
    }
    window.stopChatGeneration = stopChatGeneration;

    function insertPromptChip(promptText) {
      const input = document.getElementById('workspace-chat-input');
      if (!input) return;
      input.value = promptText;
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      input.focus();
    }
    window.insertPromptChip = insertPromptChip;

    function resetBannerState() {
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (!banner) return;
      banner.className = 'workspace-book-banner';
      icon.innerHTML = '<i class="fas fa-book-open"></i>';
      title.textContent = 'Kitabı AI hafızasına yükle';
      subtitle.textContent = 'Tüm kitap metnini yapay zekaya ver — derin analiz için';
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-cloud-arrow-up"></i> Yükle';
      isFullBookLoaded = false;
    }

    async function loadFullBookToAI() {
      if (!activeWorkspaceBook || isFullBookLoaded) return;
      
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      
      // Set loading state
      banner.classList.add('loading');
      icon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      title.textContent = 'Kitap PDF\'i Gemini\'a yükleniyor...';
      subtitle.textContent = 'Oturum oluşturuluyor (yalnızca ilk defaya mahsustur)';
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Hazırlanıyor';
      
      try {
        const response = await apiFetch(`/api/workspace/load-book/${activeWorkspaceBook.hash}`, {
          method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
          isFullBookLoaded = true;
          banner.classList.remove('loading');
          banner.classList.add('loaded');
          icon.innerHTML = '<i class="fas fa-circle-check"></i>';
          const charK = Math.round(data.char_count / 1000);
          title.textContent = 'Kitap AI oturumu aktif';
          subtitle.textContent = `${charK}K karakter · Oturum hazır — sorular anında yanıtlanacak`;
          btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
          
          // Inject system message into chat
          const chatMessages = document.getElementById('workspace-chat-messages');
          chatMessages.insertAdjacentHTML('beforeend', `
            <div class="chat-msg chat-ai" style="max-width: 100%;">
              <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
              <div class="chat-msg-text"><strong>${esc(activeWorkspaceBook.title)}</strong> kitabı yapay zeka oturumuna başarıyla yüklendi. Artık tüm sorularınız beklemeden ve doğrudan kitap üzerinden yanıtlanacak.</div>
            </div>
          `);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
          banner.classList.remove('loading');
          banner.classList.add('error');
          icon.innerHTML = '<i class="fas fa-triangle-exclamation"></i>';
          title.textContent = 'Yükleme başarısız';
          subtitle.textContent = data.error || 'Bilinmeyen hata';
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';
          
          setTimeout(() => {
            banner.classList.remove('error');
            resetBannerState();
          }, 5000);
        }
      } catch (err) {
        // İsteğe bağlı / sessiz hata toleransı: bağlantı hatası kullanıcıya banner üzerinde bildirilir
        console.warn('loadFullBookToAI hatası:', err);
        banner.classList.remove('loading');
        icon.innerHTML = '<i class="fas fa-triangle-exclamation"></i>';
        title.textContent = 'Bağlantı hatası';
        subtitle.textContent = 'Sunucuya ulaşılamadı';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';
        
        setTimeout(() => resetBannerState(), 5000);
      }
    }
    window.loadFullBookToAI = loadFullBookToAI;

    function renderChatHistoryItem(item) {
      if (item.role === 'user') {
        return `
          <div class="chat-msg chat-user">
            <div class="chat-msg-text">${esc(item.text)}</div>
            <div class="chat-msg-avatar"><i class="fas fa-user"></i></div>
          </div>
        `;
      }
      return `
        <div class="chat-msg chat-ai">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">${parseMarkdown(item.text)}</div>
        </div>
      `;
    }

    function updateBannerForActiveSession() {
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (banner) {
        banner.className = 'workspace-book-banner loaded';
        if (icon) icon.innerHTML = '<i class="fas fa-circle-check"></i>';
        if (title) title.textContent = 'Kitap AI oturumu aktif';
        if (subtitle) subtitle.textContent = 'Önbellek devrede — sorular anında yanıtlanıyor';
        if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
        isFullBookLoaded = true;
      }
    }

    function applyWorkspaceChatHistory(data, chatMessages) {
      if (!data?.success || !Array.isArray(data.history) || data.history.length === 0) return;
      chatMessages.innerHTML = data.history.map(renderChatHistoryItem).join('');
      chatMessages.scrollTop = chatMessages.scrollHeight;

      if (data.has_active_session) {
        updateBannerForActiveSession();
      }
    }

    function openWorkspace(book, initialPage = null) {
      activeWorkspaceBook = book;
      
      // Reset copy chat button if active
      resetCopyButtonUI();
      
      // Sync meta text and cover slot
      document.getElementById('workspace-book-cat').textContent = book.category || 'Belge';
      document.getElementById('workspace-book-title').textContent = book.title || 'İsimsiz';
      document.title = `${book.title || 'İsimsiz Eser'} — Kütüphanem`;
      const coverSlot = document.getElementById('workspace-cover-slot');
      if (coverSlot) {
        coverSlot.innerHTML = book.has_cover
          ? `<img src="/thumbnails/${book.hash}.jpg" alt="${esc(book.title || '')}">`
          : `<i class="fas fa-book-open" style="font-size:0.75rem; color:var(--muted);"></i>`;
      }
      
      // Reset banner
      resetBannerState();

      // Load PDF via custom HTML5 PDF.js Reader
      initCustomPdfViewer(book, initialPage);
      
      // Let the user load the book manually via the banner button
      // setTimeout(() => {
      //   loadFullBookToAI();
      // }, 500);
      
      // Open overlay
      document.getElementById('workspace-reader').classList.add('open');
      document.body.classList.add('modal-open');

      // On mobile viewports, start in immersive reading mode with bottom sheet chat collapsed
      if (window.innerWidth <= 768) {
        const cp = document.getElementById('workspace-chat-pane');
        const tb = document.getElementById('btn-toggle-workspace-chat');
        const lbl = document.getElementById('workspace-chat-toggle-label');
        if (cp) cp.classList.add('collapsed');
        if (tb) tb.classList.remove('active');
        if (lbl) lbl.textContent = 'AI Aç';
      }

      // Load previous persistent chat history from server if exists
      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.innerHTML = `
        <div class="chat-msg chat-ai">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">Merhaba! Şu anda <strong>${esc(book.title)}</strong> eseri üzerinde konuşmaya hazırız. Kitabın ana fikirleri, terimleri veya sormak istediğiniz kısımları hakkında sorular sorabilirsiniz.</div>
        </div>
      `;

      apiFetch(`/api/workspace/chat-history/${book.hash}`)
        .then(res => res.json())
        .then(data => applyWorkspaceChatHistory(data, chatMessages))
        .catch(err => {
          // İsteğe bağlı / sessiz hata toleransı: Geçmiş yüklenemezse varsayılan selamlama kalır
          console.debug('Chat history load error:', err);
        });
      
      // Focus textarea
      setTimeout(() => {
        const textarea = document.getElementById('workspace-chat-input');
        if (textarea) textarea.focus();
      }, 300);
    }

    function openBookWithMorph(cardOrCover, book) {
      const targetBook = book || (typeof allBooks !== 'undefined' ? allBooks.find(b => b.hash === cardOrCover?.dataset?.hash) : null);
      if (!targetBook) return;

      const card = (cardOrCover instanceof HTMLElement) ? (cardOrCover.closest('.book-card') || cardOrCover) : document.querySelector(`.book-card[data-hash="${targetBook.hash}"]`);
      const cover = card ? (card.querySelector('.card-cover') || card) : null;

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        if (typeof closeModalDirect === 'function') closeModalDirect();
        openWorkspace(targetBook);
        return;
      }

      if (cover) cover.style.viewTransitionName = 'book-cover';
      if (typeof closeModalDirect === 'function') closeModalDirect();

      const transition = document.startViewTransition(() => {
        openWorkspace(targetBook);
        const slot = document.getElementById('workspace-cover-slot');
        if (slot) slot.style.viewTransitionName = 'book-cover';
        if (cover) cover.style.viewTransitionName = '';
      });

      transition.finished.finally(() => {
        const slot = document.getElementById('workspace-cover-slot');
        if (slot) slot.style.removeProperty('view-transition-name');
        if (cover) cover.style.removeProperty('view-transition-name');
      });
    }
    window.openBookWithMorph = openBookWithMorph;

    function closeWorkspace() {
      const currentBook = activeWorkspaceBook;
      const card = currentBook ? document.querySelector(`.book-card[data-hash="${currentBook.hash}"]`) : null;
      const cover = card ? (card.querySelector('.card-cover') || card) : null;
      const slot = document.getElementById('workspace-cover-slot');

      const doClose = () => {
        document.getElementById('workspace-reader').classList.remove('open');
        document.body.classList.remove('modal-open');
        document.title = 'Kütüphanem';
        
        // Stop ongoing typewriter or TTS
        if (activeTypewriterTimer) {
          clearInterval(activeTypewriterTimer);
          activeTypewriterTimer = null;
        }
        const stopWrap = document.getElementById('workspace-stop-wrap');
        if (stopWrap) stopWrap.style.display = 'none';

        if (window.speechSynthesis?.speaking) {
          window.speechSynthesis.cancel();
        }
        isSpeaking = false;
        const ttsBtn = document.getElementById('pdf-tts-btn');
        if (ttsBtn) {
          ttsBtn.classList.remove('active');
          ttsBtn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }

        // Cleanup custom HTML5 PDF.js Reader resources
        cleanupCustomPdfViewer();
        
        activeWorkspaceBook = null;
        isFullBookLoaded = false;
      };

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches || !cover) {
        doClose();
        return;
      }

      if (slot) slot.style.viewTransitionName = 'book-cover';
      const transition = document.startViewTransition(() => {
        doClose();
        if (cover) cover.style.viewTransitionName = 'book-cover';
        if (slot) slot.style.viewTransitionName = '';
      });

      transition.finished.finally(() => {
        if (cover) cover.style.removeProperty('view-transition-name');
        if (slot) slot.style.removeProperty('view-transition-name');
      });
    }

    function handleWorkspaceChatKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void sendWorkspaceMessage();
      }
    }

    function markSessionLoadedInBanner() {
      if (isFullBookLoaded) return;
      isFullBookLoaded = true;
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (banner) {
        banner.className = 'workspace-book-banner loaded';
        if (icon) icon.innerHTML = '<i class="fas fa-circle-check"></i>';
        if (title) title.textContent = 'Kitap AI oturumu aktif';
        if (subtitle) subtitle.textContent = 'Önbellek devrede — sonraki sorular anında yanıtlanacak';
        if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
      }
    }

    function startWorkspaceTypewriter(rawReply, replyId, chatMessages) {
      const targetContainer = document.querySelector(`#${replyId} .chat-msg-text`);
      if (!targetContainer) return;
      const words = (rawReply || '').split(' ');
      const totalWords = words.length || 1;
      // Daktilo efekti en fazla 2.5 saniyede (2500ms) tamamlansın, min 5ms, max 25ms
      const wordDelay = Math.min(25, Math.max(5, Math.floor(2500 / totalWords)));
      let currentText = '';
      let wordIndex = 0;

      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'block';
      activeTypewriterFullText = rawReply;
      activeTypewriterContainer = targetContainer;

      // Smart auto-scroll check: Yalnızca kullanıcı en alttaysa otomatik kaydır, yukarı kaydırdıysa scrollu kilitleme
      const isUserNearBottom = () => {
        if (!chatMessages) return true;
        return (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight) < 60;
      };

      let lastParagraphCheck = '';
      activeTypewriterTimer = setInterval(() => {
        if (wordIndex < words.length) {
          currentText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
          wordIndex++;

          // Sadece paragraf bitişlerinde (\n\n) veya son kelimede tam markdown parse et; ara kelimelerde ham metin güncelle
          const hasNewParagraph = currentText.includes('\n\n') && currentText.lastIndexOf('\n\n') > lastParagraphCheck.length;
          if (hasNewParagraph) {
            targetContainer.innerHTML = parseMarkdown(currentText);
            lastParagraphCheck = currentText.slice(0, currentText.lastIndexOf('\n\n'));
          } else if (lastParagraphCheck.length === 0) {
            targetContainer.textContent = currentText;
          } else {
            const unrenderedPart = currentText.slice(lastParagraphCheck.length);
            const safeUnrendered = typeof esc === 'function' ? esc(unrenderedPart) : unrenderedPart;
            targetContainer.innerHTML = parseMarkdown(lastParagraphCheck) + '<p>' + safeUnrendered + '</p>';
          }

          if (isUserNearBottom() && chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        } else {
          clearInterval(activeTypewriterTimer);
          activeTypewriterTimer = null;
          targetContainer.innerHTML = parseMarkdown(rawReply);
          if (isUserNearBottom() && chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
          if (stopWrap) stopWrap.style.display = 'none';
          isWorkspaceChatLoading = false;
        }
      }, wordDelay);
    }

    async function sendWorkspaceMessage() {
      if (isWorkspaceChatLoading || !activeWorkspaceBook) return;
      
      const input = document.getElementById('workspace-chat-input');
      const text = input.value.trim();
      if (!text) return;
      
      // Reset copy button if in copied state
      resetCopyButtonUI();

      input.value = '';
      input.style.height = 'auto'; // Reset size
      
      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-user">
          <div class="chat-msg-avatar"><i class="fas fa-user"></i></div>
          <div class="chat-msg-text">${esc(text)}</div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      const tempId = `typing-${Date.now()}`;
      const loadingNoticeText = !isFullBookLoaded 
        ? '<div style="font-size: 0.78rem; opacity: 0.85; margin-bottom: 6px;"><i class="fas fa-cloud-arrow-up fa-fade"></i> Kitap PDF\'i Gemini oturumuna yükleniyor, ilk soru biraz sürebilir...</div>' 
        : '';
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-ai" id="${tempId}">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">
            ${loadingNoticeText}
            <div class="chat-typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      isWorkspaceChatLoading = true;
      
      try {
        const response = await apiFetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: text,
            target_book_hash: activeWorkspaceBook.hash,
            load_full_book: isFullBookLoaded
          })
        });
        
        if (!response?.ok) {
          const errDetail = response ? `Sunucu hatası (${response.status})` : 'Sunucuya ulaşılamadı.';
          throw new Error(errDetail);
        }

        const data = await response.json();
        const rawReply = data.response || 'Yanıt alınamadı.';
        
        document.getElementById(tempId)?.remove();
        markSessionLoadedInBanner();
        
        const replyId = `reply-${Date.now()}`;
        chatMessages.insertAdjacentHTML('beforeend', `
          <div class="chat-msg chat-ai" id="${replyId}">
            <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
            <div class="chat-msg-text"></div>
          </div>
        `);
        startWorkspaceTypewriter(rawReply, replyId, chatMessages);
      } catch (err) {
        document.getElementById(tempId)?.remove();
        isWorkspaceChatLoading = false;
        const errText = err?.message || 'Bağlantı hatası: Sunucuya ulaşılamadı.';
        chatMessages.insertAdjacentHTML('beforeend', `
          <div class="chat-msg chat-ai">
            <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
            <div class="chat-msg-text" style="color: #b0473c;">${esc(errText)}</div>
          </div>
        `);
      } finally {
        if (!activeTypewriterTimer) {
          isWorkspaceChatLoading = false;
          const stopWrap = document.getElementById('workspace-stop-wrap');
          if (stopWrap) stopWrap.style.display = 'none';
        }
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }
    }

    // Copy entire workspace chat conversation to clipboard
    function copyWorkspaceChat() {
      const chatMessages = document.getElementById('workspace-chat-messages');
      const btn = document.getElementById('btn-copy-chat');
      if (!chatMessages) return;

      const msgs = chatMessages.querySelectorAll('.chat-msg');
      if (!msgs || msgs.length === 0) {
        showToast('Kopyalanacak mesaj bulunamadı.', 'info');
        return;
      }

      const bookTitle = activeWorkspaceBook ? (activeWorkspaceBook.title || 'Kitap') : 'Kitap';
      const lines = [`# ${bookTitle} - AI Sohbet Notları\n`];

      msgs.forEach(msg => {
        const isUser = msg.classList.contains('chat-user');
        const textEl = msg.querySelector('.chat-msg-text');
        if (!textEl) return;

        // Clean and extract text
        const text = textEl.innerText.trim();
        if (!text) return;

        if (isUser) {
          lines.push(`\n**Kullanıcı:**\n${text}\n`);
        } else {
          lines.push(`\n**AI Asistanı:**\n${text}\n`);
        }
      });

      const fullContent = lines.join('\n');

      const notify = (msg) => {
        if (typeof showNotification === 'function') {
          showNotification(msg, 'success');
        } else {
          // Self-contained elegant toast
          let toast = document.getElementById('chat-copy-toast');
          if (!toast) {
            toast = document.createElement('div');
            toast.id = 'chat-copy-toast';
            toast.style.cssText = 'position: fixed; bottom: 30px; right: 30px; background: #5f7a4f; color: #fff; padding: 0.75rem 1.4rem; border-radius: 50px; font-family: Inter, sans-serif; font-size: 0.88rem; font-weight: 600; box-shadow: 0 10px 25px rgba(95,122,79,0.3); z-index: 10000; display: flex; align-items: center; gap: 0.5rem; transition: all 0.3s ease; opacity: 0; transform: translateY(10px);';
            document.body.appendChild(toast);
          }
          toast.innerHTML = `<i class="fas fa-check-circle"></i> ${msg}`;
          toast.style.opacity = '1';
          toast.style.transform = 'translateY(0)';
          setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
          }, 2500);
        }
      };

      const setCopiedUI = () => {
        if (btn) {
          if (copyChatBtnTimeout) {
            clearTimeout(copyChatBtnTimeout);
          }
          btn.classList.add('copied');
          const icon = btn.querySelector('i');
          if (icon) icon.className = 'fas fa-check';
          const btnText = btn.querySelector('.btn-copy-text');
          if (btnText) btnText.textContent = 'Kopyalandı!';
          
          copyChatBtnTimeout = setTimeout(() => {
            resetCopyButtonUI();
          }, 2000);
        }
        notify('Sohbet başarıyla panoya kopyalandı!');
      };

      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(fullContent)
          .then(setCopiedUI)
          .catch(err => {
            console.warn('Panoya yazma başarısız, fallback deneniyor:', err);
            fallbackCopy(fullContent);
          });
      } else {
        fallbackCopy(fullContent);
      }

      function fallbackCopy(text) {
        if (navigator?.clipboard?.writeText) {
          navigator.clipboard.writeText(text)
            .then(setCopiedUI)
            .catch(() => showToast('Panoya kopyalama başarısız oldu.', 'error'));
          return;
        }
        showToast('Tarayıcınız panoya kopyalamayı desteklemiyor.', 'error');
      }
    }
    window.copyWorkspaceChat = copyWorkspaceChat;

    let copyChatBtnTimeout = null;
    function resetCopyButtonUI() {
      const btn = document.getElementById('btn-copy-chat');
      if (!btn) return;
      if (copyChatBtnTimeout) {
        clearTimeout(copyChatBtnTimeout);
        copyChatBtnTimeout = null;
      }
      btn.classList.remove('copied');
      const icon = btn.querySelector('i');
      if (icon) icon.className = 'fas fa-copy';
      const btnText = btn.querySelector('.btn-copy-text');
      if (btnText) btnText.textContent = 'Konuşmayı Kopyala';
    }
    window.resetCopyButtonUI = resetCopyButtonUI;

    // Dynamic Textarea Auto-sizing for workspace chat
    document.addEventListener('input', (e) => {
      if (e.target?.id === 'workspace-chat-input') {
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
      }
    });

    // ─── Workspace Split-Pane Resizer Logic ──────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
      const handle = document.getElementById('workspace-resize-handle');
      const pdfPane = document.getElementById('workspace-pdf-pane');
      const chatPane = document.getElementById('workspace-chat-pane');
      
      if (!handle || !pdfPane || !chatPane) return;
      
      let isDragging = false;
      
      const onMouseDown = (e) => {
        isDragging = true;
        handle.classList.add('active');
        document.body.style.cursor = 'col-resize';
        // Add a temporary overlay over iframe so mouse events don't get swallowed by pdf
        const iframeMask = document.createElement('div');
        iframeMask.id = 'iframe-drag-mask';
        iframeMask.style.position = 'absolute';
        iframeMask.style.inset = '0';
        iframeMask.style.zIndex = '9999';
        pdfPane.appendChild(iframeMask);
      };
      
      const onMouseMove = (e) => {
        if (!isDragging) return;
        
        const clientX = e.clientX || e.touches?.[0]?.clientX;
        if (!clientX) return;
        
        const totalWidth = window.innerWidth;
        const leftWidthPercent = (clientX / totalWidth) * 100;
        
        // Limits constraints (between 30% and 80%)
        if (leftWidthPercent > 30 && leftWidthPercent < 80) {
          pdfPane.style.flex = leftWidthPercent / 100;
          chatPane.style.flex = (100 - leftWidthPercent) / 100;
        }
      };
      
      const onMouseUp = () => {
        if (!isDragging) return;
        isDragging = false;
        handle.classList.remove('active');
        document.body.style.cursor = '';
        document.getElementById('iframe-drag-mask')?.remove();
      };
      
      handle.addEventListener('mousedown', onMouseDown);
      handle.addEventListener('touchstart', onMouseDown);
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('touchmove', onMouseMove);
      
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchend', onMouseUp);
    });

    function toggleWorkspaceChatPane() {
      const chatPane = document.getElementById('workspace-chat-pane');
      const resizeHandle = document.getElementById('workspace-resize-handle');
      const toggleBtn = document.getElementById('btn-toggle-workspace-chat');
      const label = document.getElementById('workspace-chat-toggle-label');
      if (!chatPane) return;

      const isCollapsed = chatPane.classList.toggle('collapsed');
      if (resizeHandle) {
        resizeHandle.style.display = isCollapsed ? 'none' : 'flex';
      }
      if (toggleBtn) {
        toggleBtn.classList.toggle('active', !isCollapsed);
        toggleBtn.title = isCollapsed ? 'AI Asistan Panelini Aç' : 'AI Asistan Panelini Gizle (Odaklı Okuma)';
      }
      if (label) {
        label.textContent = isCollapsed ? 'AI Aç' : 'AI Paneli';
      }

      // Smoothly trigger a resize / refit on the PDF canvas so reader is responsive
      setTimeout(() => {
        if (typeof pdfFitWidth === 'function') {
          pdfFitWidth();
        }
        window.dispatchEvent(new Event('resize'));
      }, 280);
    }
    window.toggleWorkspaceChatPane = toggleWorkspaceChatPane;

    // Mobile bottom sheet velocity drag gesture for reader chat pane
    (function setupMobileChatSheetDrag() {
      const chatPane = document.getElementById('workspace-chat-pane');
      const chatHeader = document.getElementById('workspace-chat-header');
      if (!chatPane || !chatHeader) return;

      let startY = 0;
      let currentY = 0;
      let isDragging = false;
      let startTime = 0;

      chatHeader.addEventListener('touchstart', (e) => {
        if (window.innerWidth > 768) return;
        if (chatPane.classList.contains('collapsed')) return;
        startY = e.touches[0].clientY;
        currentY = startY;
        startTime = Date.now();
        isDragging = true;
        chatPane.style.transition = 'none';
      }, { passive: true });

      window.addEventListener('touchmove', (e) => {
        if (!isDragging || window.innerWidth > 768) return;
        currentY = e.touches[0].clientY;
        const deltaY = currentY - startY;
        if (deltaY > 0) {
          chatPane.style.transform = `translateY(${deltaY}px)`;
        }
      }, { passive: true });

      window.addEventListener('touchend', () => {
        if (!isDragging || window.innerWidth > 768) return;
        isDragging = false;
        chatPane.style.transition = '';
        const deltaY = currentY - startY;
        const elapsed = Date.now() - startTime;
        const velocity = deltaY / Math.max(elapsed, 1);

        if (deltaY > 80 || (velocity > 0.4 && deltaY > 20)) {
          chatPane.style.transform = '';
          if (!chatPane.classList.contains('collapsed')) {
            toggleWorkspaceChatPane();
          }
        } else {
          chatPane.style.transform = '';
        }
      });
    })();


    /* ==========================================================================
       CUSTOM INTERACTIVE HTML5 PDF.JS READER ENGINE WITH ANNOTATIONS & NOTES
       ========================================================================== */
    
    // Keep track of which pages are currently rendered or rendering to avoid duplicate render tasks
    let pdfRenderedPages = {}; // pageNum -> 'done' or 'rendering'
    let pdfRenderTasks = {};   // pageNum -> active PDF.js RenderTask
    let pdfActiveNoteColorClass = 'yellow';
    let pdfActiveNoteColorHex = '#e8dca0';

    function selectModalNoteColor(colorHex, colorClass) {
      pdfActiveNoteColorClass = colorClass;
      pdfActiveNoteColorHex = colorHex;
      
      const colors = ['yellow', 'green', 'blue', 'pink'];
      colors.forEach(c => {
        const btn = document.getElementById(`modal-color-${c}`);
        if (btn) {
          if (c === colorClass) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        }
      });
    }
    
    // PDF Viewer State variables
    let pdfDoc = null;
    let pdfPageNum = 1;
    let pdfPageCount = 0;
    let pdfScale = 1.2;
    let pdfIsRendering = false;
    let pdfPendingPageNum = null;
    let pdfIsFitWidth = false;
    let pdfIsFitHeight = false;
    let saveProgressDebounceTimer = null;
    let pdfIsSpreadMode = localStorage.getItem('pdf_spread_mode') === 'true';

    function updateSpreadUI() {
      const btn = document.getElementById('pdf-spread-btn');
      if (btn) {
        btn.classList.toggle('active', !!pdfIsSpreadMode);
        btn.title = pdfIsSpreadMode ? 'Tek Sayfa Görünümüne Geç' : 'Çift Sayfa Kitap Görünümüne Geç';
      }
    }

    function togglePdfSpreadMode() {
      pdfIsSpreadMode = !pdfIsSpreadMode;
      try {
        localStorage.setItem('pdf_spread_mode', String(pdfIsSpreadMode));
      } catch (_) {}
      updateSpreadUI();
      applySpreadLayout();
      checkVisiblePagesAndRender();
    }
    window.togglePdfSpreadMode = togglePdfSpreadMode;
    window.updateSpreadUI = updateSpreadUI;

    function renderSpreadRows(container, wrappers) {
      let i = 0;
      while (i < wrappers.length) {
        const row = document.createElement('div');
        row.className = 'pdf-spread-row';

        if (i === 0) {
          wrappers[0].classList.remove('spread-left', 'spread-right');
          row.appendChild(wrappers[0]);
          i++;
        } else {
          const leftPage = wrappers[i];
          leftPage.classList.add('spread-left');
          leftPage.classList.remove('spread-right');
          row.appendChild(leftPage);
          i++;

          if (i < wrappers.length) {
            const rightPage = wrappers[i];
            rightPage.classList.add('spread-right');
            rightPage.classList.remove('spread-left');
            row.appendChild(rightPage);
            i++;
          }
        }
        container.appendChild(row);
      }
    }

    function renderSinglePageRows(container, wrappers) {
      wrappers.forEach(w => {
        w.classList.remove('spread-left', 'spread-right');
        container.appendChild(w);
      });
    }

    function applySpreadLayout() {
      const container = document.getElementById('pdf-canvas-container');
      if (!container || !pdfDoc || pdfPageCount === 0) return;

      const isWide = window.innerWidth >= 800;
      const useSpread = pdfIsSpreadMode && isWide;

      const wrappers = [];
      for (let p = 1; p <= pdfPageCount; p++) {
        const w = document.getElementById(`pdf-page-wrapper-${p}`);
        if (w) wrappers.push(w);
      }
      if (wrappers.length === 0) return;

      container.innerHTML = '';

      if (!useSpread) {
        renderSinglePageRows(container, wrappers);
      } else {
        renderSpreadRows(container, wrappers);
      }

      if (pdfPageNum > 0) {
        scrollToPage(pdfPageNum);
      }
    }
    window.applySpreadLayout = applySpreadLayout;
    
    // Annotation variables (Keys are book hashes for sandboxed persistency)
    let pdfHighlights = {}; // pageNum -> Array of {id, text, colorClass, colorHex, coords: [{left, top, width, height}]}
    let pdfNotes = {};      // highlightId -> noteText string
    
    // Temporary selection tracking
    let pdfSelectedText = "";
    let pdfSelectionRanges = [];
    let pdfActiveHighlightIdForNote = null;

    // ═════════════════════════════════════════════════════════════
    // PDF.js Smart Geometric Line & Margin Clamping Selection Engine
    // (Google Chrome PDFium & Adobe Acrobat Reader Standard)
    // Eliminates margin click misses, paragraph bleed-through & whitespace jumping
    // ═════════════════════════════════════════════════════════════
    const activeTextLayersMap = new Map(); // textLayerDiv -> endOfContentDiv
    const pageGeometryCache = new Map();   // pageNum -> geometry
    let selectionChangeAbortController = null;
    let prevSelectionRange = null;
    let isUserSelectingText = false;
    let selectionDragState = null;

    function invalidatePageGeometry(pageNum) {
      if (pageNum) {
        pageGeometryCache.delete(Number(pageNum));
      } else {
        pageGeometryCache.clear();
      }
    }

    function extractSpanInfos(spans, pageRect) {
      const spanInfos = [];
      for (const s of spans) {
        if (!s.textContent?.trim()) continue;
        const r = s.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;

        const textNode = s.firstChild || s;
        spanInfos.push({
          element: s,
          textNode: textNode,
          text: s.textContent,
          top: r.top - pageRect.top,
          bottom: r.bottom - pageRect.top,
          left: r.left - pageRect.left,
          right: r.right - pageRect.left,
          width: r.width,
          height: r.height,
          centerY: (r.top + r.bottom) / 2 - pageRect.top
        });
      }
      return spanInfos;
    }

    function groupSpansIntoLines(spanInfos) {
      const lines = [];
      let currentLine = null;

      for (const s of spanInfos) {
        if (!currentLine) {
          currentLine = {
            top: s.top,
            bottom: s.bottom,
            left: s.left,
            right: s.right,
            centerY: s.centerY,
            spans: [s]
          };
          lines.push(currentLine);
        } else {
          const verticalMatch =
            Math.abs(s.centerY - currentLine.centerY) <= 8 ||
            (s.top < currentLine.bottom - 2 && s.bottom > currentLine.top + 2);

          if (verticalMatch) {
            currentLine.spans.push(s);
            currentLine.top = Math.min(currentLine.top, s.top);
            currentLine.bottom = Math.max(currentLine.bottom, s.bottom);
            currentLine.left = Math.min(currentLine.left, s.left);
            currentLine.right = Math.max(currentLine.right, s.right);
            currentLine.centerY = (currentLine.top + currentLine.bottom) / 2;
          } else {
            currentLine = {
              top: s.top,
              bottom: s.bottom,
              left: s.left,
              right: s.right,
              centerY: s.centerY,
              spans: [s]
            };
            lines.push(currentLine);
          }
        }
      }

      for (const line of lines) {
        line.spans.sort((a, b) => a.left - b.left);
        line.firstSpan = line.spans[0];
        line.lastSpan = line.spans.at(-1);
        line.height = line.bottom - line.top;
      }
      return lines;
    }

    function getOrComputePageGeometry(textLayer) {
      if (!textLayer) return null;
      const pageWrapper = textLayer.closest('.pdf-page-wrapper');
      const pageNum = pageWrapper ? Number(pageWrapper.id.replace('pdf-page-wrapper-', '')) : null;

      if (pageNum && pageGeometryCache.has(pageNum)) {
        return pageGeometryCache.get(pageNum);
      }

      const spans = Array.from(textLayer.querySelectorAll('span'));
      if (spans.length === 0) return null;

      const pageRect = textLayer.getBoundingClientRect();
      if (!pageRect.width || !pageRect.height) return null;

      const spanInfos = extractSpanInfos(spans, pageRect);
      if (spanInfos.length === 0) return null;

      spanInfos.sort((a, b) => {
        if (Math.abs(a.centerY - b.centerY) > 6) {
          return a.centerY - b.centerY;
        }
        return a.left - b.left;
      });

      const lines = groupSpansIntoLines(spanInfos);
      const geometry = {
        pageNum: pageNum,
        pageWidth: pageRect.width,
        pageHeight: pageRect.height,
        lines: lines
      };

      if (pageNum) {
        pageGeometryCache.set(pageNum, geometry);
      }

      return geometry;
    }

    function getSafeTextNode(spanInfo) {
      let node = spanInfo.textNode;
      if (node.nodeType !== Node.TEXT_NODE) {
        node = node.firstChild || node;
      }
      return node;
    }

    function getNodeLength(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.nodeValue ? node.nodeValue.length : 0;
      }
      return node.textContent ? node.textContent.length : 0;
    }

    function findBestLineForY(lines, pageY) {
      if (pageY < lines[0].top) return { bestLine: lines[0], bestLineIdx: 0 };
      if (pageY > lines.at(-1).bottom) return { bestLine: lines.at(-1), bestLineIdx: lines.length - 1 };

      for (let i = 0; i < lines.length; i++) {
        const cur = lines[i];
        const prev = i > 0 ? lines[i - 1] : null;
        const next = i < lines.length - 1 ? lines[i + 1] : null;

        const topBoundary = prev ? (prev.bottom + cur.top) / 2 : cur.top - 30;
        const bottomBoundary = next ? (cur.bottom + next.top) / 2 : cur.bottom + 30;

        if (pageY >= topBoundary && pageY <= bottomBoundary) {
          return { bestLine: cur, bestLineIdx: i };
        }
      }

      return { bestLine: lines.at(-1), bestLineIdx: lines.length - 1 };
    }

    function findCaretByPoint(clientX, clampedClientY, textLayer, bestLineIdx) {
      if (document.caretPositionFromPoint) {
        const pos = document.caretPositionFromPoint(clientX, clampedClientY);
        if (pos?.offsetNode && textLayer.contains(pos.offsetNode)) {
          return {
            node: pos.offsetNode,
            offset: pos.offset,
            lineIdx: bestLineIdx
          };
        }
      } else {
        const legacyFnName = 'caretRange' + 'FromPoint';
        const getLegacyRange = document[legacyFnName];
        if (typeof getLegacyRange === 'function') {
          const range = getLegacyRange.call(document, clientX, clampedClientY);
          if (range?.startContainer && textLayer.contains(range.startContainer)) {
            return {
              node: range.startContainer,
              offset: range.startOffset,
              lineIdx: bestLineIdx
            };
          }
        }
      }
      return null;
    }

    function findCaretBySpanInterpolation(bestLine, pageX, bestLineIdx) {
      let closestSpan = bestLine.spans[0];
      let minDistance = Infinity;
      for (const s of bestLine.spans) {
        if (pageX >= s.left && pageX <= s.right) {
          closestSpan = s;
          break;
        }
        const dist = Math.min(Math.abs(pageX - s.left), Math.abs(pageX - s.right));
        if (dist < minDistance) {
          minDistance = dist;
          closestSpan = s;
        }
      }

      const node = getSafeTextNode(closestSpan);
      const textLen = getNodeLength(node);
      const ratio = Math.max(0, Math.min(1, (pageX - closestSpan.left) / (closestSpan.width || 1)));
      const charOffset = Math.round(ratio * textLen);

      return {
        node: node,
        offset: Math.max(0, Math.min(textLen, charOffset)),
        lineIdx: bestLineIdx
      };
    }

    function findCaretPositionInPage(textLayer, geometry, clientX, clientY) {
      if (!geometry?.lines?.length) return null;
      const pageRect = textLayer.getBoundingClientRect();
      const pageX = clientX - pageRect.left;
      const pageY = clientY - pageRect.top;

      const { bestLine, bestLineIdx } = findBestLineForY(geometry.lines, pageY);

      if (pageX <= bestLine.left + 6) {
        const node = getSafeTextNode(bestLine.firstSpan);
        return {
          node: node,
          offset: 0,
          lineIdx: bestLineIdx,
          isStartOfLine: true
        };
      }

      if (pageX >= bestLine.right - 6) {
        const node = getSafeTextNode(bestLine.lastSpan);
        return {
          node: node,
          offset: getNodeLength(node),
          lineIdx: bestLineIdx,
          isEndOfLine: true
        };
      }

      const clampedClientY = pageRect.top + bestLine.centerY;
      const browserCaret = findCaretByPoint(clientX, clampedClientY, textLayer, bestLineIdx);
      if (browserCaret) return browserCaret;

      return findCaretBySpanInterpolation(bestLine, pageX, bestLineIdx);
    }

    function findPageWrapperAtPoint(clientX, clientY) {
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return null;

      const elements = document.elementsFromPoint(clientX, clientY);
      for (const el of elements) {
        const wrapper = el.closest('.pdf-page-wrapper');
        if (wrapper) return wrapper;
      }

      // If clicked in margin outside the page wrapper horizontally, match by vertical range
      const wrappers = Array.from(container.querySelectorAll('.pdf-page-wrapper'));
      for (const w of wrappers) {
        const r = w.getBoundingClientRect();
        if (clientY >= r.top && clientY <= r.bottom) {
          return w;
        }
      }

      return null;
    }

    function registerTextLayerForSelection(textLayerDiv, endDiv) {
      if (!textLayerDiv || !endDiv) return;
      activeTextLayersMap.set(textLayerDiv, endDiv);
      enableGlobalSelectionListener();
    }

    function unregisterTextLayerForSelection(textLayerDiv) {
      if (!textLayerDiv) return;
      const endDiv = activeTextLayersMap.get(textLayerDiv);
      if (endDiv && endDiv.parentElement === textLayerDiv) {
        endDiv.remove();
      }
      activeTextLayersMap.delete(textLayerDiv);
      if (activeTextLayersMap.size === 0) {
        if (selectionChangeAbortController) {
          try { selectionChangeAbortController.abort(); } catch (_) {}
          selectionChangeAbortController = null;
        }
        prevSelectionRange = null;
      }
    }

    function resetAllEndOfContent() {
      activeTextLayersMap.forEach((end, textLayer) => {
        if (textLayer?.contains(end)) {
          textLayer.append(end);
          end.style.width = "";
          end.style.height = "";
          end.style.top = "";
        }
        if (end) end.classList.remove("active");
      });
      prevSelectionRange = null;
    }

    function getActiveTextLayersFromSelection(selection, activeLayers) {
      const activeTextLayers = new Set();
      for (let i = 0; i < selection.rangeCount; i++) {
        const range = selection.getRangeAt(i);
        for (const textLayerDiv of activeLayers.keys()) {
          if (!activeTextLayers.has(textLayerDiv) && range.intersectsNode(textLayerDiv)) {
            activeTextLayers.add(textLayerDiv);
          }
        }
      }
      return activeTextLayers;
    }

    function updateEndOfContentLayer(textLayerDiv, endDiv, isActive) {
      if (isActive) {
        endDiv.classList.add("active");
      } else {
        if (textLayerDiv.contains(endDiv)) {
          textLayerDiv.append(endDiv);
          endDiv.style.width = "";
          endDiv.style.height = "";
          endDiv.style.top = "";
        }
        endDiv.classList.remove("active");
      }
    }

    function enableGlobalSelectionListener() {
      if (selectionChangeAbortController) return;
      selectionChangeAbortController = new AbortController();
      const signal = selectionChangeAbortController.signal;

      // Pointer down: initiate smart geometric selection
      document.addEventListener("pointerdown", (evt) => {
        if (evt.button !== 0 && evt.button !== undefined) return;

        // Ignore clicks on floating UI widgets
        if (evt.target.closest('#pdf-floating-bar') ||
            evt.target.closest('#pdf-search-bar') ||
            evt.target.closest('.pdf-note-modal') ||
            evt.target.closest('.sticky-note-marker')) {
          return;
        }

        const container = document.getElementById('pdf-canvas-container');
        if (!container?.contains(evt.target)) {
          return;
        }

        // Allow native double/triple-click word/paragraph selection
        if (evt.detail > 1) {
          return;
        }

        let pageWrapper = evt.target.closest('.pdf-page-wrapper');
        if (!pageWrapper) {
          pageWrapper = findPageWrapperAtPoint(evt.clientX, evt.clientY);
        }
        if (!pageWrapper) {
          clearSelection();
          return;
        }

        const textLayer = pageWrapper.querySelector('.textLayer');
        if (!textLayer) return;

        const geometry = getOrComputePageGeometry(textLayer);
        if (!geometry) return;

        const hit = findCaretPositionInPage(textLayer, geometry, evt.clientX, evt.clientY);
        if (!hit?.node) return;

        // Prevent erratic native browser selection heuristics from taking over
        evt.preventDefault();

        const isDirectSpanClick = evt.target.tagName === 'SPAN' && evt.target.closest('.textLayer');

        selectionDragState = {
          startX: evt.clientX,
          startY: evt.clientY,
          anchorNode: hit.node,
          anchorOffset: hit.offset,
          anchorTextLayer: textLayer,
          anchorPageWrapper: pageWrapper,
          anchorLineIdx: hit.lineIdx,
          isDragging: false,
          isMarginStart: !isDirectSpanClick
        };

        const sel = window.getSelection();
        try {
          sel.collapse(hit.node, hit.offset);
        } catch (_) {
          // İsteğe bağlı / sessiz hata toleransı: Geçersiz seçim aralığı
        }
      }, { signal });

      // Pointer move: update selection with geometric clamping
      document.addEventListener("pointermove", (evt) => {
        if (!selectionDragState) return;

        const dx = evt.clientX - selectionDragState.startX;
        const dy = evt.clientY - selectionDragState.startY;
        const dist = Math.hypot(dx, dy);

        if (!selectionDragState.isDragging && dist < 3) {
          return;
        }

        selectionDragState.isDragging = true;
        isUserSelectingText = true;

        const pageWrapper = findPageWrapperAtPoint(evt.clientX, evt.clientY) || selectionDragState.anchorPageWrapper;
        if (!pageWrapper) return;

        const textLayer = pageWrapper.querySelector('.textLayer');
        if (!textLayer) return;

        const geometry = getOrComputePageGeometry(textLayer);
        if (!geometry) return;

        const hit = findCaretPositionInPage(textLayer, geometry, evt.clientX, evt.clientY);
        if (!hit?.node) return;

        const sel = window.getSelection();
        try {
          sel.setBaseAndExtent(
            selectionDragState.anchorNode,
            selectionDragState.anchorOffset,
            hit.node,
            hit.offset
          );
        } catch (e) {
          // Cross-boundary selection fallback
        }
      }, { signal });

      // Pointer up: complete selection and position floating action bar
      document.addEventListener("pointerup", (evt) => {
        if (selectionDragState) {
          if (selectionDragState.isDragging) {
            handleTextSelection();
          } else {
            // Simple click without drag: clear selection
            clearSelection();
          }
          selectionDragState = null;
        }
        isUserSelectingText = false;
        resetAllEndOfContent();
      }, { signal });

      document.addEventListener("mouseup", () => {
        isUserSelectingText = false;
        resetAllEndOfContent();
      }, { signal });

      // selectionchange: Auxiliary stabilizer for keyboard / touch selection
      document.addEventListener("selectionchange", () => {
        // Skip if custom geometric drag is actively driving setBaseAndExtent
        if (selectionDragState?.isDragging) {
          return;
        }

        const selection = document.getSelection();
        if (!selection || selection.rangeCount === 0) {
          resetAllEndOfContent();
          return;
        }

        const activeTextLayers = getActiveTextLayersFromSelection(selection, activeTextLayersMap);

        for (const [textLayerDiv, endDiv] of activeTextLayersMap) {
          updateEndOfContentLayer(textLayerDiv, endDiv, activeTextLayers.has(textLayerDiv));
        }
      }, { signal });
    }

    // Initialize custom PDF.js reader for the loaded book
    function setupPdfPages(firstPage, container) {
      let viewport = firstPage.getViewport({ scale: 1.0 });

      if (pdfIsFitWidth) {
        const containerWidth = Math.max(300, container.clientWidth - 48);
        pdfScale = Math.max(0.3, Math.min(4.0, containerWidth / viewport.width));
        updateZoomLabel();
      } else if (pdfIsFitHeight) {
        const containerHeight = Math.max(300, container.clientHeight - 80);
        pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
        updateZoomLabel();
      }

      viewport = firstPage.getViewport({ scale: pdfScale });

      for (let p = 1; p <= pdfPageCount; p++) {
        const pageWrapper = document.createElement('div');
        pageWrapper.className = 'pdf-page-wrapper';
        pageWrapper.id = `pdf-page-wrapper-${p}`;
        pageWrapper.dataset.pageNumber = p;
        pageWrapper.dataset.pageNum = p;
        pageWrapper.style.width = viewport.width + 'px';
        pageWrapper.style.height = viewport.height + 'px';
        pageWrapper.style.marginBottom = '24px';
        pageWrapper.style.position = 'relative';

        const textLayer = document.createElement('div');
        textLayer.className = 'textLayer';
        textLayer.id = `textLayer-${p}`;
        textLayer.style.width = viewport.width + 'px';
        textLayer.style.height = viewport.height + 'px';
        textLayer.style.setProperty('--scale-factor', String(pdfScale));
        pageWrapper.appendChild(textLayer);

        const highlightLayer = document.createElement('div');
        highlightLayer.className = 'pdf-highlight-layer';
        highlightLayer.id = `pdf-highlight-layer-${p}`;
        highlightLayer.style.width = viewport.width + 'px';
        highlightLayer.style.height = viewport.height + 'px';
        pageWrapper.appendChild(highlightLayer);

        container.appendChild(pageWrapper);
      }

      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        applySpreadLayout();
      }

      void renderPdfPageVirtual(pdfPageNum);

      requestAnimationFrame(() => {
        if (pdfPageNum > 1) {
          scrollToPage(pdfPageNum);
        }
        setTimeout(() => {
          if (pdfPageNum > 1) {
            scrollToPage(pdfPageNum);
          }
          checkVisiblePagesAndRender();
        }, 120);
      });
    }

    async function setupLoadedPdf(pdf, book, container, pdfUrl) {
      pdfDoc = pdf;
      pdfPageCount = pdf.numPages;

      document.getElementById('pdf-page-count').textContent = pdfPageCount;
      const pageInput = document.getElementById('pdf-page-num');
      pageInput.max = pdfPageCount;
      pageInput.value = pdfPageNum;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      loadPdfOutline(pdf).catch(err => console.debug("loadPdfOutline error:", err));

      if (container) {
        container.innerHTML = "";
        try {
          const firstPage = await pdf.getPage(1);
          setupPdfPages(firstPage, container);
        } catch (err) {
          console.error("PDF getPage(1) hatası:", err);
        }
      }

      renderNotesSidebar();
    }

    // --- [D2: PDF Pre-Fetching & Skeleton Loader] ---
    const pdfPrefetchCache = new Map();

    function prefetchPdfDocument(hash) {
      if (!hash || !window.pdfjsLib || pdfPrefetchCache.has(hash)) return;
      const pdfUrl = `/api/download/${hash}`;
      try {
        const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
        pdfPrefetchCache.set(hash, {
          task: loadingTask,
          promise: loadingTask.promise
        });
      } catch (e) {
        console.debug('Prefetch silent skip:', e);
      }
    }
    window.prefetchPdfDocument = prefetchPdfDocument;

    function cancelPdfPrefetch(hash) {
      if (!hash || !pdfPrefetchCache.has(hash)) return;
      const item = pdfPrefetchCache.get(hash);
      if (item && item.cleanupTimer) clearTimeout(item.cleanupTimer);
      if (item) {
        item.cleanupTimer = setTimeout(() => {
          try { item.task.destroy(); } catch (_) {}
          pdfPrefetchCache.delete(hash);
        }, 8000);
      }
    }
    window.cancelPdfPrefetch = cancelPdfPrefetch;

    function initCustomPdfViewer(book, initialPage = null) {
      // Reset state
      pdfDoc = null;
      pdfPageNum = (initialPage && initialPage > 0) ? initialPage : (book.okunulan_sayfa || 1);
      pdfPageCount = 0;
      pdfScale = 1.2;
      pdfIsRendering = false;
      pdfPendingPageNum = null;
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      closePdfSearch();
      pdfSearchTextCache = {};
      pdfHighlights = {};
      pdfNotes = {};
      pdfSelectedText = "";
      pdfSelectionRanges = [];
      pdfActiveHighlightIdForNote = null;
      pdfRenderedPages = {};
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};

      // Sync surface mode and toolbar buttons
      const viewer = document.getElementById('custom-pdf-viewer');
      if (viewer) {
        viewer.dataset.surfaceMode = currentReaderSurfaceMode;
      }
      document.querySelectorAll('#reader-surface-group .surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `btn-surface-${currentReaderSurfaceMode}`);
      });

      // Update zoom label to initial
      updateZoomLabel();
      updateSpreadUI();
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');

      // Load annotations: First from localStorage for zero-latency, then sync from server API
      try {
        const savedHighlights = localStorage.getItem(`lib-highlights-${book.hash}`);
        const savedNotes = localStorage.getItem(`lib-notes-${book.hash}`);
        if (savedHighlights) pdfHighlights = JSON.parse(savedHighlights);
        if (savedNotes) pdfNotes = JSON.parse(savedNotes);
      } catch (e) {
        console.error("Local storage okuma hatası:", e);
      }

      apiFetch(`/api/books/${book.hash}/annotations`)
        .then(res => res.json())
        .then(data => {
          if (data?.status === 'success' && Array.isArray(data.annotations) && data.annotations.length > 0) {
            const apiHighlights = {};
            const apiNotes = {};
            data.annotations.forEach(a => {
              const p = a.sayfa_no;
              if (!apiHighlights[p]) apiHighlights[p] = [];
              let coords = [];
              try { coords = JSON.parse(a.koordinatlar || '[]'); } catch (_) {}
              apiHighlights[p].push({
                id: a.id,
                text: a.secilen_metin || '',
                colorClass: a.renk_sinif || 'yellow',
                colorHex: a.renk_hex || '#e8dca0',
                coords: coords
              });
              if (a.not_metni) {
                apiNotes[a.id] = a.not_metni;
              }
            });
            pdfHighlights = apiHighlights;
            pdfNotes = apiNotes;
            // Update local storage cache
            try {
              localStorage.setItem(`lib-highlights-${book.hash}`, JSON.stringify(pdfHighlights));
              localStorage.setItem(`lib-notes-${book.hash}`, JSON.stringify(pdfNotes));
            } catch (_) {
              // İsteğe bağlı / sessiz hata toleransı: localStorage kayıt hatası göz ardı edilir
            }
            renderNotesSidebar();
            if (pdfPageNum) drawPageHighlightsAndNotes(pdfPageNum);
          }
        })
        .catch(err => console.warn("API notları yüklenirken hata:", err));

      // Initialize UI controls
      document.getElementById('pdf-page-num').value = pdfPageNum;
      document.getElementById('pdf-page-count').textContent = "-";
      
      const emptyDiv = `<div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>`;
      document.getElementById('pdf-notes-list').innerHTML = emptyDiv;

      // Hide floating bar
      hideFloatingBar();

      // Begin loading PDF document
      const pdfUrl = `/api/download/${book.hash}`;
      
      if (!window.pdfjsLib) {
        console.error("PDF.js kütüphanesi yüklenemedi.");
        return;
      }

      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.innerHTML = `
          <div class="reader-skeleton-wrap">
            <div class="reader-skeleton-cover-preview">
              ${book.has_cover ? `<img src="/thumbnails/${book.hash}.jpg" alt="">` : '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);"><i class="fas fa-book" style="font-size:2.5rem;"></i></div>'}
            </div>
            <div class="reader-skeleton-page">
              <div class="reader-skeleton-line title"></div>
              <div class="reader-skeleton-line short"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line medium"></div>
            </div>
          </div>
        `;
      }

      // Check file extension: If .txt, render clean typography reader
      const bookFilename = (book.file || book.dosya_adi || book.title || "").toLowerCase();
      if (bookFilename.endsWith(".txt")) {
        fetch(pdfUrl)
          .then(r => r.text())
          .then(txt => {
            if (container) {
              container.innerHTML = `
                <div style="max-width: 800px; margin: 2rem auto; padding: 3rem 2.5rem; background: var(--paper); border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); font-family: 'Geist', sans-serif; line-height: 1.8; color: var(--ink); white-space: pre-wrap; word-break: break-word; font-size: 1.05rem;">${esc(txt)}</div>
              `;
            }
            document.getElementById('pdf-page-count').textContent = "1";
            document.getElementById('pdf-page-num').value = 1;
            renderNotesSidebar();
          })
          .catch(err => {
            if (container) container.innerHTML = `<div style="padding: 2rem; color: var(--accent); text-align: center;">Metin dosyası yüklenirken hata oluştu: ${esc(String(err))}</div>`;
          });
        return;
      }

      // D2: Use pre-fetched promise if available for zero-latency instant open
      let docPromise = null;
      if (pdfPrefetchCache.has(book.hash)) {
        const cached = pdfPrefetchCache.get(book.hash);
        docPromise = cached.promise;
        pdfPrefetchCache.delete(book.hash);
      } else {
        const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
        docPromise = loadingTask.promise;
      }

      docPromise
        .then(pdf => setupLoadedPdf(pdf, book, container, pdfUrl))
        .catch(function(error) {
          console.error("PDF.js yükleme hatası:", error);
          if (container) {
            container.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--muted); font-family: 'Geist', sans-serif;"><i class="fas fa-book-open" style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--accent); opacity: 0.8; display: block;"></i><strong>${esc(book.title || 'Belge')}</strong><p style="margin-top: 0.5rem; font-size: 0.9rem;">Bu dosya türü standart PDF olmadığı için gömülü önizleyici yerine AI Asistanı ile doğrudan taranabilir ve soru-cevap yapılabilir.</p><a href="${pdfUrl}" class="btn-import" style="display: inline-block; margin-top: 1rem; text-decoration: none; padding: 0.6rem 1.4rem;" download><i class="fas fa-download"></i> Dosyayı İndir</a></div>`;
          }
        });

      // Bind selection mouse/touch listeners to container
      if (container) {
        container.addEventListener('mouseup', handleTextSelection);
        container.addEventListener('touchend', handleTextSelection);
      }
    }

    // Free resources and bindings on close
    function cleanupCustomPdfViewer() {
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      pdfRenderedPages = {};
      if (pdfDoc && typeof pdfDoc.destroy === 'function') {
        try { pdfDoc.destroy(); } catch (_) {}
      }
      pdfDoc = null;
      hideFloatingBar();
      closePdfSearch();
      pdfSearchTextCache = {};
      if (selectionChangeAbortController) {
        try { selectionChangeAbortController.abort(); } catch (_) {}
        selectionChangeAbortController = null;
      }
      activeTextLayersMap.clear();
      invalidatePageGeometry();
      selectionDragState = null;
      prevSelectionRange = null;
      isUserSelectingText = false;
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.removeEventListener('mouseup', handleTextSelection);
        container.removeEventListener('touchend', handleTextSelection);
      }
    }

    function cleanupOffscreenPage(pNum) {
      if (pdfRenderTasks[pNum]) {
        try { pdfRenderTasks[pNum].cancel(); } catch (_) { /* sessiz iptal */ }
        delete pdfRenderTasks[pNum];
      }
      const canvas = document.getElementById(`pdf-render-canvas-${pNum}`);
      if (canvas) {
        canvas.width = 0;
        canvas.height = 0;
        canvas.remove();
      }
      const textLayer = document.getElementById(`textLayer-${pNum}`);
      if (textLayer) {
        unregisterTextLayerForSelection(textLayer);
        textLayer.innerHTML = "";
      }
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pNum}`);
      if (highlightLayer) highlightLayer.innerHTML = "";
      delete pdfRenderedPages[pNum];
    }

    function updateVisiblePageProgress(mostVisiblePage) {
      if (!mostVisiblePage || Number.isNaN(mostVisiblePage) || pdfPageNum === mostVisiblePage) return;

      pdfPageNum = mostVisiblePage;
      const pageInput = document.getElementById('pdf-page-num');
      if (pageInput) pageInput.value = pdfPageNum;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      if (activeWorkspaceBook) {
        activeWorkspaceBook.okunulan_sayfa = pdfPageNum;
        if (typeof allBooks !== 'undefined' && Array.isArray(allBooks)) {
          const cachedBook = allBooks.find(b => (b.hash || b.dosya_hash) === activeWorkspaceBook.hash);
          if (cachedBook) {
            cachedBook.okunulan_sayfa = pdfPageNum;
          }
        }
        if (saveProgressDebounceTimer) {
          clearTimeout(saveProgressDebounceTimer);
        }
        const targetHash = activeWorkspaceBook.hash;
        const targetPage = pdfPageNum;
        saveProgressDebounceTimer = setTimeout(() => {
          apiFetch(`/api/books/${targetHash}/progress`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page: targetPage })
          }).catch(err => console.warn("Okuma ilerlemesi kaydedilemedi:", err));
        }, 400);
      }
    }

    // Dynamic virtual scroll renderer
    function checkVisiblePagesAndRender() {
      if (!pdfDoc) return;
      
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return;
      
      if (pdfPageNum && !Number.isNaN(pdfPageNum) && pdfPageNum >= 1 && !pdfRenderedPages[pdfPageNum]) {
        void renderPdfPageVirtual(pdfPageNum);
      }
      
      const containerRect = container.getBoundingClientRect();
      const wrappers = container.querySelectorAll('.pdf-page-wrapper');
      
      let mostVisiblePage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      let maxVisibleHeight = 0;
      
      wrappers.forEach(wrapper => {
        const pNum = Number.parseInt(wrapper.dataset.pageNum || wrapper.dataset.pageNumber || wrapper.id.replace('pdf-page-wrapper-', ''), 10);
        if (Number.isNaN(pNum) || pNum < 1) return;
        const rect = wrapper.getBoundingClientRect();
        
        const visibleTop = Math.max(rect.top, containerRect.top);
        const visibleBottom = Math.min(rect.bottom, containerRect.bottom);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        
        if (visibleHeight > maxVisibleHeight) {
          maxVisibleHeight = visibleHeight;
          mostVisiblePage = pNum;
        }
        
        const isNearViewport = (rect.bottom >= containerRect.top - rect.height * 1.5 && rect.top <= containerRect.bottom + rect.height * 1.5);
        if (isNearViewport) {
          if (!pdfRenderedPages[pNum]) {
            void renderPdfPageVirtual(pNum);
          }
        } else if (pdfRenderedPages[pNum] === 'done' && !isUserSelectingText) {
          cleanupOffscreenPage(pNum);
        }
      });
      
      updateVisiblePageProgress(mostVisiblePage);
    }

    async function renderTextLayerForPage(page, textLayer, viewport, pageNum) {
      unregisterTextLayerForSelection(textLayer);
      invalidatePageGeometry(pageNum);
      textLayer.innerHTML = "";
      textLayer.style.setProperty('--scale-factor', String(viewport.scale));
      try {
        const textContent = await page.getTextContent();
        const textRenderTask = window.pdfjsLib.renderTextLayer({
          textContentSource: textContent,
          container: textLayer,
          viewport: viewport,
          textDivs: []
        });
        await textRenderTask.promise;

        const endOfContent = document.createElement("div");
        endOfContent.className = "endOfContent";
        textLayer.appendChild(endOfContent);

        registerTextLayerForSelection(textLayer, endOfContent);

        drawPageHighlightsAndNotes(pageNum);
        if (pdfSearchQuery) {
          drawPageSearchHighlights(pageNum);
        }
      } catch (tErr) {
        if (tErr?.name === 'RenderingCancelledException') return;
        console.warn("Text layer render failed:", pageNum, tErr);
      }
    }

    async function renderPdfPageVirtual(pageNum) {
      if (!pdfDoc || !pageNum || Number.isNaN(pageNum) || pageNum < 1 || pageNum > pdfPageCount) return;
      if (pdfRenderedPages[pageNum] === 'done' || pdfRenderedPages[pageNum] === 'rendering') return;
      
      pdfRenderedPages[pageNum] = 'rendering';
      
      if (pdfRenderTasks[pageNum]) {
        try { pdfRenderTasks[pageNum].cancel(); } catch (_) { /* sessiz iptal */ }
        delete pdfRenderTasks[pageNum];
      }
      
      try {
        const page = await pdfDoc.getPage(pageNum);
        const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
        const existingCanvas = document.getElementById(`pdf-render-canvas-${pageNum}`);
        const textLayer = document.getElementById(`textLayer-${pageNum}`);
        const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
        const viewport = page.getViewport({ scale: pdfScale });
        
        if (wrapper) {
          wrapper.style.width = viewport.width + 'px';
          wrapper.style.height = viewport.height + 'px';
          wrapper.style.setProperty('--scale-factor', String(viewport.scale));
        }

        // Çift tamponlama (double-buffering): Eski canvas render bitene kadar yerinde kalır, beyaz flaş engellenir
        if (existingCanvas) {
          existingCanvas.style.width = viewport.width + 'px';
          existingCanvas.style.height = viewport.height + 'px';
        }
        
        const dpr = Math.min(window.devicePixelRatio || 1, 2.5); // Retina netliği & bellek tavanı
        const newCanvas = document.createElement('canvas');
        newCanvas.className = 'pdf-page-canvas';
        newCanvas.width = Math.floor(viewport.width * dpr);
        newCanvas.height = Math.floor(viewport.height * dpr);
        newCanvas.style.width = viewport.width + 'px';
        newCanvas.style.height = viewport.height + 'px';
        
        const ctx = newCanvas.getContext('2d');
        
        if (textLayer) {
          textLayer.style.width = viewport.width + 'px';
          textLayer.style.height = viewport.height + 'px';
          textLayer.style.setProperty('--scale-factor', String(viewport.scale));
        }
        if (highlightLayer) {
          highlightLayer.style.width = viewport.width + 'px';
          highlightLayer.style.height = viewport.height + 'px';
        }
        
        const renderContext = {
          canvasContext: ctx,
          viewport: viewport,
          transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null
        };
        
        const renderTask = page.render(renderContext);
        pdfRenderTasks[pageNum] = renderTask;
        
        await renderTask.promise;
        delete pdfRenderTasks[pageNum];
        pdfRenderedPages[pageNum] = 'done';
        applyChromaGuard(newCanvas, currentReaderSurfaceMode);
        
        // requestAnimationFrame ile atomik ve flaşsız canvas değişimi
        requestAnimationFrame(() => {
          newCanvas.id = `pdf-render-canvas-${pageNum}`;
          if (existingCanvas && existingCanvas.parentNode) {
            existingCanvas.parentNode.replaceChild(newCanvas, existingCanvas);
          } else if (wrapper) {
            wrapper.insertBefore(newCanvas, wrapper.firstChild);
          }
        });
        
        if (textLayer) {
          await renderTextLayerForPage(page, textLayer, viewport, pageNum);
        }
      } catch (err) {
        delete pdfRenderTasks[pageNum];
        if (err?.name === 'RenderingCancelledException') {
          return;
        }
        console.warn("Virtual page render failed:", pageNum, err);
        delete pdfRenderedPages[pageNum];
      }
    }

    // Scroll container layout resizing on zoom/width change
    function resizeAllPagesForZoom() {
      if (!pdfDoc) return;
      
      // Cancel active renders so canvases can resize cleanly
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      
      const targetPage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      
      pdfDoc.getPage(targetPage).then(function(samplePage) {
        let viewport = samplePage.getViewport({ scale: 1.0 });
        const container = document.getElementById('pdf-canvas-container');
        if (!container) return;
        
        if (pdfIsFitWidth) {
          const containerWidth = Math.max(300, container.clientWidth - 48);
          pdfScale = Math.max(0.3, Math.min(4.0, containerWidth / viewport.width));
          updateZoomLabel();
        } else if (pdfIsFitHeight) {
          const containerHeight = Math.max(300, container.clientHeight - 80);
          pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
          updateZoomLabel();
        }
        
        viewport = samplePage.getViewport({ scale: pdfScale });
        pdfRenderedPages = {}; // reset render states to force redraw on scroll check
        invalidatePageGeometry();
        
        for (let p = 1; p <= pdfPageCount; p++) {
          const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
          if (wrapper) {
            wrapper.style.width = viewport.width + 'px';
            wrapper.style.height = viewport.height + 'px';
            
            // Mevcut canvas'ı hemen silme, yeni boyuta göre CSS ile ölçeklendir (beyaz boşluğu önle)
            const existingCanvas = document.getElementById(`pdf-render-canvas-${p}`);
            if (existingCanvas) {
              existingCanvas.style.width = viewport.width + 'px';
              existingCanvas.style.height = viewport.height + 'px';
            }
            
            const textLayer = document.getElementById(`textLayer-${p}`);
            if (textLayer) {
              textLayer.style.width = viewport.width + 'px';
              textLayer.style.height = viewport.height + 'px';
              textLayer.style.setProperty('--scale-factor', String(pdfScale));
              unregisterTextLayerForSelection(textLayer);
              textLayer.innerHTML = "";
            }
            
            const highlightLayer = document.getElementById(`pdf-highlight-layer-${p}`);
            if (highlightLayer) {
              highlightLayer.style.width = viewport.width + 'px';
              highlightLayer.style.height = viewport.height + 'px';
              highlightLayer.innerHTML = "";
            }
          }
        }
        
        // Render target initial page immediately and keep scroll aligned
        void renderPdfPageVirtual(targetPage);
        scrollToPage(targetPage);
        
        setTimeout(() => {
          checkVisiblePagesAndRender();
        }, 120);
      }).catch(function(err) {
        console.warn("resizeAllPagesForZoom getPage failed:", err);
      });
    }

    function scrollToPage(pageNum) {
      if (pageNum < 1 || pageNum > pdfPageCount) return;
      const container = document.getElementById('pdf-canvas-container');
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper && container) {
        const row = wrapper.closest('.pdf-spread-row');
        const targetTop = row ? (row.offsetTop - 16) : (wrapper.offsetTop - 16);
        container.scrollTo({ top: Math.max(0, targetTop), behavior: 'smooth' });
      } else if (wrapper) {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    function pdfPrevPage() {
      if (pdfPageNum <= 1) return;
      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        if (pdfPageNum <= 3) {
          scrollToPage(1);
        } else {
          const target = (pdfPageNum % 2 === 0) ? (pdfPageNum - 2) : (pdfPageNum - 3);
          scrollToPage(Math.max(1, target));
        }
      } else {
        scrollToPage(pdfPageNum - 1);
      }
      hideFloatingBar();
    }

    function pdfNextPage() {
      if (pdfPageNum >= pdfPageCount) return;
      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        if (pdfPageNum === 1) {
          scrollToPage(Math.min(pdfPageCount, 2));
        } else {
          const target = (pdfPageNum % 2 === 0) ? (pdfPageNum + 2) : (pdfPageNum + 1);
          scrollToPage(Math.min(pdfPageCount, target));
        }
      } else {
        scrollToPage(pdfPageNum + 1);
      }
      hideFloatingBar();
    }

    function pdfGoToPageFromInput() {
      const input = document.getElementById('pdf-page-num');
      let val = Number.parseInt(input.value, 10);
      if (Number.isNaN(val) || val < 1) val = 1;
      if (val > pdfPageCount) val = pdfPageCount;
      scrollToPage(val);
      hideFloatingBar();
    }

    // Zoom Controls & Hardware Acceleration State
    let zoomWillChangeTimer = null;
    function markZoomActive() {
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.classList.add('is-zooming');
      }
      if (zoomWillChangeTimer) clearTimeout(zoomWillChangeTimer);
      zoomWillChangeTimer = setTimeout(() => {
        const c = document.getElementById('pdf-canvas-container');
        if (c) c.classList.remove('is-zooming');
      }, 300);
    }

    function updateZoomLabel() {
      const pct = Math.round(pdfScale * 100);
      document.getElementById('pdf-zoom-percent').textContent = pct + "%";
    }

    function pdfZoomIn() {
      markZoomActive();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');
      pdfScale += 0.15;
      if (pdfScale > 4.0) pdfScale = 4.0;
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfZoomOut() {
      markZoomActive();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');
      pdfScale -= 0.15;
      if (pdfScale < 0.5) pdfScale = 0.5;
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfFitWidth() {
      markZoomActive();
      const btn = document.getElementById('pdf-fit-width-btn');
      const otherBtn = document.getElementById('pdf-fit-height-btn');
      if (pdfIsFitWidth) {
        pdfIsFitWidth = false;
        btn?.classList.remove('active');
        pdfScale = 1.2;
      } else {
        pdfIsFitWidth = true;
        pdfIsFitHeight = false;
        btn?.classList.add('active');
        otherBtn?.classList.remove('active');
      }
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfFitHeight() {
      markZoomActive();
      const btn = document.getElementById('pdf-fit-height-btn');
      const otherBtn = document.getElementById('pdf-fit-width-btn');
      if (pdfIsFitHeight) {
        pdfIsFitHeight = false;
        btn?.classList.remove('active');
        pdfScale = 1.2;
      } else {
        pdfIsFitHeight = true;
        pdfIsFitWidth = false;
        btn?.classList.add('active');
        otherBtn?.classList.remove('active');
      }
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    // Ctrl + Mouse Wheel ile pürüzsüz zoom desteği
    document.addEventListener('wheel', function(e) {
      if (!e.ctrlKey) return;
      const container = document.getElementById('pdf-canvas-container');
      if (!container || !container.contains(e.target)) return;
      e.preventDefault();
      if (e.deltaY < 0) {
        pdfZoomIn();
      } else {
        pdfZoomOut();
      }
    }, { passive: false });

    // Toggle Notes Sidebar on left
    function toggleNotesSidebar() {
      const sidebar = document.getElementById('pdf-notes-sidebar');
      const btn = document.getElementById('pdf-notes-sidebar-btn');
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        btn.classList.remove('active');
      } else {
        sidebar.classList.add('open');
        btn.classList.add('active');
        renderNotesSidebar();
      }
    }

    function getPageWrapperFromRange(range) {
      const startNode = range.commonAncestorContainer;
      let pageWrapper = startNode.nodeType === Node.TEXT_NODE ? 
                          startNode.parentNode.closest('.pdf-page-wrapper') : 
                          startNode.closest('.pdf-page-wrapper');
      if (!pageWrapper) {
        const sc = range.startContainer;
        pageWrapper = sc.nodeType === Node.TEXT_NODE ? sc.parentNode.closest('.pdf-page-wrapper') : sc.closest('.pdf-page-wrapper');
      }
      return pageWrapper;
    }

    function updateFloatingBarPosition(range, text, pageWrapper) {
      const pageNum = Number.parseInt(pageWrapper.dataset.pageNum || pageWrapper.dataset.pageNumber || pageWrapper.id.replace('pdf-page-wrapper-', ''), 10);
      if (!Number.isNaN(pageNum) && pageNum >= 1) {
        pdfPageNum = pageNum;
      }

      const rect = range.getBoundingClientRect();
      const viewerRect = document.getElementById('custom-pdf-viewer').getBoundingClientRect();
      const floatingBar = document.getElementById('pdf-floating-bar');
      
      const barLeft = rect.left - viewerRect.left + (rect.width / 2) - 100;
      const barTop = rect.top - viewerRect.top - 48;
      
      floatingBar.style.left = Math.max(10, Math.min(barLeft, viewerRect.width - 210)) + 'px';
      floatingBar.style.top = Math.max(10, barTop) + 'px';
      floatingBar.classList.add('active');

      pdfSelectedText = text;
      pdfSelectionRanges = getSelectionCoordsRelativeToPage(range);
    }

    // Handle Text Selection for highlights & floating bar positioning
    function handleTextSelection() {
      setTimeout(() => {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        if (text.length === 0) {
          hideFloatingBar();
          return;
        }

        const range = selection.getRangeAt(0);
        const container = document.getElementById('pdf-canvas-container');
        if (!container.contains(range.commonAncestorContainer)) {
          hideFloatingBar();
          return;
        }

        const pageWrapper = getPageWrapperFromRange(range);
        if (!pageWrapper) {
          hideFloatingBar();
          return;
        }

        updateFloatingBarPosition(range, text, pageWrapper);
      }, 50);
    }

    // Hide float tooltip
    function hideFloatingBar() {
      const bar = document.getElementById('pdf-floating-bar');
      if (bar) bar.classList.remove('active');
    }

    function clearSelection() {
      window.getSelection()?.removeAllRanges();
      hideFloatingBar();
    }

    function collectTextNodesFromRange(range, root) {
      const textNodes = [];
      try {
        const treeWalker = document.createTreeWalker(
          root,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function(node) {
              if (range.intersectsNode(node)) return NodeFilter.FILTER_ACCEPT;
              return NodeFilter.FILTER_REJECT;
            }
          }
        );
        let currentNode = treeWalker.currentNode;
        while (currentNode) {
          if (currentNode.nodeType === Node.TEXT_NODE && range.intersectsNode(currentNode) && currentNode.textContent.trim().length > 0) {
            textNodes.push(currentNode);
          }
          currentNode = treeWalker.nextNode();
        }
      } catch (err) {
        console.warn("TreeWalker coordinate traversal failed:", err);
      }
      return textNodes;
    }

    function extractCharRectsFromNode(node, range) {
      const textContent = node.textContent;
      let start = (node === range.startContainer) ? range.startOffset : 0;
      let end = (node === range.endContainer) ? range.endOffset : textContent.length;
      
      while (start < end && /\s/.test(textContent.charAt(start))) {
        start++;
      }
      while (end > start && /\s/.test(textContent.charAt(end - 1))) {
        end--;
      }
      if (start >= end) return [];

      const charRects = [];
      const tempRange = document.createRange();
      for (let idx = start; idx < end; idx++) {
        if (/\s/.test(textContent.charAt(idx))) continue;
        try {
          tempRange.setStart(node, idx);
          tempRange.setEnd(node, idx + 1);
          const rect = tempRange.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            charRects.push({
              left: rect.left,
              right: rect.right,
              top: rect.top,
              bottom: rect.bottom,
              width: rect.width,
              height: rect.height
            });
          }
        } catch (_) {
          // Range sınır toleransı
        }
      }
      return charRects;
    }

    function groupCharRectsIntoLines(charRects) {
      const lines = [];
      charRects.forEach(rect => {
        const centerY = rect.top + rect.height / 2;
        let added = false;
        for (const line of lines) {
          const lineCenterY = line.top + line.height / 2;
          if (Math.abs(centerY - lineCenterY) < Math.max(8, rect.height * 0.6)) {
            line.left = Math.min(line.left, rect.left);
            line.right = Math.max(line.right, rect.right);
            line.top = Math.min(line.top, rect.top);
            line.bottom = Math.max(line.bottom, rect.bottom);
            line.height = line.bottom - line.top;
            added = true;
            break;
          }
        }
        if (!added) {
          lines.push({
            left: rect.left,
            right: rect.right,
            top: rect.top,
            bottom: rect.bottom,
            height: rect.height
          });
        }
      });
      return lines;
    }

    // Normalize coordinates relative to page wrapper bounding box with character precision
    function getSelectionCoordsRelativeToPage(range) {
      const startNode = range.commonAncestorContainer;
      const pageWrapper = startNode.nodeType === Node.TEXT_NODE ? 
                          startNode.parentNode.closest('.pdf-page-wrapper') : 
                          startNode.closest('.pdf-page-wrapper');
      
      if (!pageWrapper) return [];
      const wrapperRect = pageWrapper.getBoundingClientRect();
      const root = startNode.nodeType === Node.TEXT_NODE ? startNode.parentNode : startNode;
      const textNodes = collectTextNodesFromRange(range, root);

      if (textNodes.length === 0 && startNode.nodeType === Node.TEXT_NODE && startNode.textContent.trim().length > 0) {
        textNodes.push(startNode);
      }

      const coords = [];
      textNodes.forEach(node => {
        const charRects = extractCharRectsFromNode(node, range);
        if (charRects.length === 0) return;

        const lines = groupCharRectsIntoLines(charRects);
        lines.forEach(line => {
          const w = line.right - line.left;
          if (w < 1.5 || line.height < 1.5) return;
          coords.push({
            left: (line.left - wrapperRect.left) / wrapperRect.width,
            top: (line.top - wrapperRect.top) / wrapperRect.height,
            width: w / wrapperRect.width,
            height: line.height / wrapperRect.height
          });
        });
      });

      // Fallback
      if (coords.length === 0) {
        const rects = range.getClientRects();
        for (const r of rects) {
          if (r.width < 1.5 || r.height < 1.5) continue;
          coords.push({
            left: (r.left - wrapperRect.left) / wrapperRect.width,
            top: (r.top - wrapperRect.top) / wrapperRect.height,
            width: r.width / wrapperRect.width,
            height: r.height / wrapperRect.height
          });
        }
      }
      return coords;
    }

    function generateHighlightId() {
      if (typeof crypto !== 'undefined') {
        if (typeof crypto.randomUUID === 'function') {
          return `hl_${crypto.randomUUID()}`;
        }
        if (crypto.getRandomValues) {
          const arr = new Uint32Array(1);
          crypto.getRandomValues(arr);
          return `hl_${Date.now()}_${arr[0].toString(36)}`;
        }
      }
      return `hl_${Date.now()}_${Date.now().toString(36)}`;
    }

    // Apply Highlighter action
    function applyHighlight(colorHex, colorClass) {
      if (!activeWorkspaceBook || !pdfSelectedText || pdfSelectionRanges.length === 0) return;

      const hlId = generateHighlightId();
      
      if (!pdfHighlights[pdfPageNum]) {
        pdfHighlights[pdfPageNum] = [];
      }

      pdfHighlights[pdfPageNum].push({
        id: hlId,
        text: pdfSelectedText,
        colorClass: colorClass,
        colorHex: colorHex,
        coords: pdfSelectionRanges
      });

      // Save and Draw immediately
      saveAnnotations();
      drawPageHighlightsAndNotes(pdfPageNum);
      renderNotesSidebar();
      clearSelection();
    }

    // Sticky Note Modals Functions
    function openNoteModalForSelection() {
      if (!pdfSelectedText) return;
      
      pdfActiveHighlightIdForNote = generateHighlightId();
      
      // Default to yellow for new selections
      selectModalNoteColor('#e8dca0', 'yellow');
      
      // Populate previews
      document.getElementById('pdf-selected-text-preview').textContent = `"${pdfSelectedText}"`;
      document.getElementById('pdf-note-textarea').value = "";
      
      // Show Modal
      const noteModal = document.getElementById('pdf-note-modal');
      if (noteModal) {
        noteModal.classList.remove('closing');
        noteModal.classList.add('open');
        document.body.classList.add('modal-open');
        if (typeof activateModalFocus === 'function') activateModalFocus(noteModal);
      }
    }

    function closePdfNoteModalDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('pdf-note-modal', () => {
          pdfActiveHighlightIdForNote = null;
          clearSelection();
        });
      } else {
        document.getElementById('pdf-note-modal')?.classList.remove('open');
        document.body.classList.remove('modal-open');
        pdfActiveHighlightIdForNote = null;
        clearSelection();
      }
    }

    function closePdfNoteModal(e) {
      if (e.target.id === 'pdf-note-modal') {
        closePdfNoteModalDirect();
      }
    }

    function savePdfNote() {
      const textarea = document.getElementById('pdf-note-textarea');
      const noteText = textarea ? textarea.value.trim() : "";

      if (!pdfHighlights[pdfPageNum]) pdfHighlights[pdfPageNum] = [];

      let existingHighlight = pdfHighlights[pdfPageNum].find(h => h.id === pdfActiveHighlightIdForNote);

      if (!noteText && !existingHighlight) {
        closePdfNoteModalDirect();
        return;
      }

      if (existingHighlight) {
        // Update color and text if edited
        existingHighlight.colorClass = pdfActiveNoteColorClass;
        existingHighlight.colorHex = pdfActiveNoteColorHex;
      } else {
        // Create new highlight automatically if applying note from selection
        pdfHighlights[pdfPageNum].push({
          id: pdfActiveHighlightIdForNote,
          text: pdfSelectedText,
          colorClass: pdfActiveNoteColorClass,
          colorHex: pdfActiveNoteColorHex,
          coords: pdfSelectionRanges
        });
      }

      // Store note text mapped to highlight (or remove if emptied)
      if (noteText) {
        pdfNotes[pdfActiveHighlightIdForNote] = noteText;
      } else if (existingHighlight) {
        delete pdfNotes[pdfActiveHighlightIdForNote];
      }

      // Persist and Sync
      saveAnnotations();
      drawPageHighlightsAndNotes(pdfPageNum);
      renderNotesSidebar();
      closePdfNoteModalDirect();
    }

    // Persist to local storage and sync to backend DB
    function saveAnnotations() {
      if (!activeWorkspaceBook) return;
      try {
        localStorage.setItem(`lib-highlights-${activeWorkspaceBook.hash}`, JSON.stringify(pdfHighlights));
        localStorage.setItem(`lib-notes-${activeWorkspaceBook.hash}`, JSON.stringify(pdfNotes));
      } catch (e) {
        console.error("Local storage kaydetme hatası:", e);
      }

      // Sync to SQLite backend API
      const batchList = [];
      Object.keys(pdfHighlights).forEach(pStr => {
        const pNum = Number(pStr);
        (pdfHighlights[pNum] || []).forEach(hl => {
          batchList.push({
            id: hl.id,
            sayfa_no: pNum,
            secilen_metin: hl.text || '',
            not_metni: pdfNotes[hl.id] || '',
            renk_hex: hl.colorHex || '#e8dca0',
            renk_sinif: hl.colorClass || 'yellow',
            koordinatlar: JSON.stringify(hl.coords || [])
          });
        });
      });

      apiFetch(`/api/books/${activeWorkspaceBook.hash}/annotations/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ annotations: batchList })
      }).catch(err => console.warn("Not senkronizasyonu hatası:", err));
    }

    // Render Highlights & Notes overlays absolute coords relative to wrapper width/height
    function drawPageHighlightsAndNotes(pageNum) {
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
      if (!highlightLayer) return;
      highlightLayer.innerHTML = "";

      const pageHls = pdfHighlights[pageNum] || [];
      pageHls.forEach(function(hl) {
        // Draw highlight overlay divs
        hl.coords.forEach(function(coord) {
          const div = document.createElement('div');
          div.className = `rendered-highlight ${hl.colorClass}`;
          div.style.left = (coord.left * 100) + "%";
          div.style.top = (coord.top * 100) + "%";
          div.style.width = (coord.width * 100) + "%";
          div.style.height = (coord.height * 100) + "%";
          div.dataset.hlId = hl.id;
          highlightLayer.appendChild(div);
        });

        // Draw Margin Sticky Note marker if note exists
        if (pdfNotes[hl.id]) {
          const firstCoord = hl.coords[0];
          const pin = document.createElement('div');
          pin.className = 'sticky-note-marker';
          pin.innerHTML = '<i class="fas fa-sticky-note"></i>';
          pin.style.left = "8px"; // place neatly in left margin
          pin.style.top = (firstCoord.top * 100) + "%";
          pin.title = pdfNotes[hl.id];
          pin.onclick = function() {
            // Edit existing note
            editExistingNote(hl.id, hl.text, pdfNotes[hl.id], pageNum);
          };
          highlightLayer.appendChild(pin);
        }
      });
    }

    // Edit note modal trigger
    function editExistingNote(hlId, quote, currentNote, pageNum) {
      pdfActiveHighlightIdForNote = hlId;
      pdfPageNum = pageNum; // sync page context
      
      let hl = null;
      if (pdfHighlights[pageNum]) {
        hl = pdfHighlights[pageNum].find(h => h.id === hlId);
      }
      const activeColorHex = hl ? hl.colorHex : '#e8dca0';
      const activeColorClass = hl ? hl.colorClass : 'yellow';
      selectModalNoteColor(activeColorHex, activeColorClass);
      
      document.getElementById('pdf-selected-text-preview').textContent = `"${quote}"`;
      document.getElementById('pdf-note-textarea').value = currentNote;
      document.getElementById('pdf-note-modal').classList.add('open');
      document.body.classList.add('modal-open');
      document.body.classList.add('modal-open');
      setTimeout(() => document.getElementById('pdf-note-textarea').focus(), 150);
    }

    // Annotation Sidebar populating & interactive jump-to-page trigger
    function renderNotesSidebar() {
      const list = document.getElementById('pdf-notes-list');
      list.innerHTML = "";

      let totalCount = 0;
      
      // Sort pages numerically
      const pages = Object.keys(pdfHighlights).map(Number).sort((a,b) => a-b);
      
      pages.forEach(function(pNum) {
        const pageHls = pdfHighlights[pNum] || [];
        pageHls.forEach(function(hl) {
          totalCount++;
          const hasNote = !!pdfNotes[hl.id];
          
          const div = document.createElement('div');
          div.className = 'pdf-note-item';
          div.onclick = function() {
            jumpToHighlight(pNum, hl.id);
          };

          let noteHtml = "";
          if (hasNote) {
            noteHtml = `<div class="pdf-note-item-text"><i class="fas fa-comment-dots" style="color: var(--accent); margin-right: 0.3rem;"></i> ${esc(pdfNotes[hl.id])}</div>`;
          }

          div.innerHTML = `
            <div class="pdf-note-item-meta">
              <span class="pdf-note-item-page">Sayfa ${pNum}</span>
              <span style="font-size: 0.65rem; opacity: 0.7;">${hasNote ? 'Notlu' : 'İşaretleme'}</span>
            </div>
            <div class="pdf-note-item-quote ${hl.colorClass}">${esc(hl.text)}</div>
            ${noteHtml}
            <div class="pdf-note-item-actions">
              <button class="pdf-note-item-btn btn-edit-note" title="Notu / Alıntıyı Düzenle"><i class="fas fa-edit"></i></button>
              <button class="pdf-note-item-btn delete btn-delete-note" title="Sil"><i class="fas fa-trash-alt"></i></button>
            </div>
          `;
          const editBtn = div.querySelector('.btn-edit-note');
          if (editBtn) {
            editBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              editExistingNote(hl.id, hl.text, pdfNotes[hl.id] || '', pNum);
            });
          }
          const delBtn = div.querySelector('.btn-delete-note');
          if (delBtn) {
            delBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              deleteHighlight(pNum, hl.id);
            });
          }
          list.appendChild(div);
        });
      });

      if (totalCount === 0) {
        list.innerHTML = `<div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>`;
      }
    }

    // Jump immediately to specific page and scroll to highlight element
    function jumpToHighlight(pageNum, hlId) {
      pdfPageNum = pageNum;
      document.getElementById('pdf-page-num').value = pageNum;
      
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper) {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Pulse highlighting effect
        setTimeout(() => {
          const highlightEl = document.querySelector(`[data-hl-id="${hlId}"]`);
          if (highlightEl) {
            highlightEl.style.opacity = "0.9";
            setTimeout(() => highlightEl.style.opacity = "", 1500);
          }
        }, 350);
      }
    }

    // Delete Highlight and associated Note
    function deleteHighlight(pageNum, hlId) {
      if (!pdfHighlights[pageNum]) return;
      
      // Filter out
      pdfHighlights[pageNum] = pdfHighlights[pageNum].filter(h => h.id !== hlId);
      if (pdfHighlights[pageNum].length === 0) {
        delete pdfHighlights[pageNum];
      }
      
      // Delete associated note
      if (pdfNotes[hlId]) {
        delete pdfNotes[hlId];
      }

      if (activeWorkspaceBook) {
        apiFetch(`/api/books/${activeWorkspaceBook.hash}/annotations/${hlId}`, {
          method: 'DELETE'
        }).catch(err => console.warn("Not silinirken API hatası:", err));
      }

      try {
        localStorage.setItem(`lib-highlights-${activeWorkspaceBook.hash}`, JSON.stringify(pdfHighlights));
        localStorage.setItem(`lib-notes-${activeWorkspaceBook.hash}`, JSON.stringify(pdfNotes));
      } catch (e) {
        console.error("Local storage silme güncellemesi hatası:", e);
      }

      drawPageHighlightsAndNotes(pageNum);
      renderNotesSidebar();
    }

    // 60FPS fluid virtual page rendering & progress tracking on scroll
    let scrollRaf = 0;
    function onPdfContainerScroll() {
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0;
        checkVisiblePagesAndRender();
      });
    }

    // ═════════════════════════════════════════════════════════════
    // In-Document Fast PDF Search Engine (Ctrl + F & Live Highlights)
    // ═════════════════════════════════════════════════════════════
    let pdfSearchQuery = "";
    let pdfSearchResults = []; // Array of { pageNum, matchIndex, snippet }
    let pdfSearchCurrentMatchIdx = -1;
    let pdfSearchPageMatchesCount = {}; // pageNum -> count
    let pdfSearchTextCache = {}; // pageNum -> { text: string, textLower: string }
    let isPdfSearchOpen = false;
    let isPdfSearchDrawerOpen = false;
    let pdfSearchDebounceTimer = null;
    let pdfSearchToken = 0; // Incremental cancellation token preventing search race conditions

    // Toggle search bar
    function togglePdfSearch(forceOpen) {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const input = document.getElementById('pdf-search-input');
      if (!searchBar) return;

      const shouldOpen = (forceOpen !== undefined) ? forceOpen : (searchBar.style.display === 'none' || !searchBar.style.display);
      if (shouldOpen) {
        searchBar.style.display = 'block';
        toggleBtn?.classList.add('active');
        isPdfSearchOpen = true;
        setTimeout(() => {
          input?.focus();
          input?.select();
        }, 50);
      } else {
        closePdfSearch();
      }
    }

    function closePdfSearch() {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const drawer = document.getElementById('pdf-search-results-drawer');
      const listBtn = document.getElementById('pdf-search-list-btn');
      if (searchBar) searchBar.style.display = 'none';
      if (drawer) drawer.style.display = 'none';
      toggleBtn?.classList.remove('active');
      listBtn?.classList.remove('active');
      isPdfSearchOpen = false;
      isPdfSearchDrawerOpen = false;
      clearPdfSearch(true); // clear visual highlights
    }

    function clearPdfSearch(onlyClearHighlights) {
      const input = document.getElementById('pdf-search-input');
      const clearBtn = document.getElementById('pdf-search-clear-btn');
      const counter = document.getElementById('pdf-search-counter');
      const prevBtn = document.getElementById('pdf-search-prev-btn');
      const nextBtn = document.getElementById('pdf-search-next-btn');
      const drawer = document.getElementById('pdf-search-results-drawer');
      const listBtn = document.getElementById('pdf-search-list-btn');

      if (!onlyClearHighlights && input) {
        input.value = "";
      }
      if (clearBtn) clearBtn.style.display = 'none';
      if (counter) {
        counter.textContent = '0 / 0';
        counter.classList.remove('has-matches');
      }
      if (prevBtn) prevBtn.disabled = true;
      if (nextBtn) nextBtn.disabled = true;
      if (drawer) drawer.style.display = 'none';
      listBtn?.classList.remove('active');
      isPdfSearchDrawerOpen = false;

      pdfSearchQuery = "";
      pdfSearchResults = [];
      pdfSearchCurrentMatchIdx = -1;
      pdfSearchPageMatchesCount = {};
      ++pdfSearchToken; // Invalidate any running background page scans

      // Remove all search highlight elements across all rendered highlight layers
      document.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());
    }

    function togglePdfSearchResultsDrawer() {
      const drawer = document.getElementById('pdf-search-results-drawer');
      const listBtn = document.getElementById('pdf-search-list-btn');
      if (!drawer) return;
      isPdfSearchDrawerOpen = !isPdfSearchDrawerOpen;
      drawer.style.display = isPdfSearchDrawerOpen ? 'block' : 'none';
      if (isPdfSearchDrawerOpen) {
        listBtn?.classList.add('active');
      } else {
        listBtn?.classList.remove('active');
      }
    }

    function onPdfSearchInput(val) {
      const clearBtn = document.getElementById('pdf-search-clear-btn');
      if (clearBtn) clearBtn.style.display = val.length > 0 ? 'flex' : 'none';

      if (pdfSearchDebounceTimer) {
        clearTimeout(pdfSearchDebounceTimer);
      }
      pdfSearchDebounceTimer = setTimeout(() => {
        void executePdfSearch(val.trim());
      }, 250);
    }

    function onPdfSearchKeydown(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (e.shiftKey) {
          pdfSearchPrev();
        } else {
          pdfSearchNext();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        closePdfSearch();
      }
    }

    function collectMatchesForPage(p, pageData, query, normalizedQuery) {
      const textLower = pageData.textLower;
      let pos = 0;
      let pageMatchCount = 0;
      while ((pos = textLower.indexOf(normalizedQuery, pos)) !== -1) {
        const startSnippet = Math.max(0, pos - 35);
        const endSnippet = Math.min(pageData.text.length, pos + query.length + 35);
        let rawSnippet = pageData.text.substring(startSnippet, endSnippet);
        if (startSnippet > 0) rawSnippet = "..." + rawSnippet;
        if (endSnippet < pageData.text.length) rawSnippet = rawSnippet + "...";

        pdfSearchResults.push({
          pageNum: p,
          matchIndex: pdfSearchResults.length,
          matchInPageIndex: pageMatchCount,
          charOffset: pos,
          snippet: rawSnippet
        });

        pageMatchCount++;
        pos += Math.max(1, normalizedQuery.length);
      }

      if (pageMatchCount > 0) {
        pdfSearchPageMatchesCount[p] = pageMatchCount;
      }
    }

    // Iterative fast page scanner with token-based cancellation
    async function scanPagesIteratively(myToken, pageCount, query, normalizedQuery) {
      for (let p = 1; p <= pageCount; p++) {
        if (myToken !== pdfSearchToken) return false;

        let pageData = pdfSearchTextCache[p];
        if (!pageData) {
          try {
            const page = await pdfDoc.getPage(p);
            if (myToken !== pdfSearchToken) return false;
            const textContent = await page.getTextContent();
            if (myToken !== pdfSearchToken) return false;
            const textParts = textContent.items.map(item => item.str || "");
            const fullText = textParts.join(" ");
            pageData = {
              text: fullText,
              textLower: fullText.toLocaleLowerCase('tr-TR'),
              items: textContent.items
            };
            pdfSearchTextCache[p] = pageData;
          } catch (err) {
            console.warn("Sayfa metni taranamadı:", p, err);
          }
        }

        if (myToken !== pdfSearchToken) return false;

        if (pageData) {
          collectMatchesForPage(p, pageData, query, normalizedQuery);
        }
      }
      return true;
    }

    function _applyPdfSearchResults(totalMatches, query) {
      const counter = document.getElementById('pdf-search-counter');
      const prevBtn = document.getElementById('pdf-search-prev-btn');
      const nextBtn = document.getElementById('pdf-search-next-btn');

      let targetIdx = 0;
      for (let i = 0; i < pdfSearchResults.length; i++) {
        if (pdfSearchResults[i].pageNum >= pdfPageNum) {
          targetIdx = i;
          break;
        }
      }
      pdfSearchCurrentMatchIdx = targetIdx;
      if (counter) {
        counter.textContent = `${targetIdx + 1} / ${totalMatches}`;
        counter.classList.add('has-matches');
      }
      if (prevBtn) prevBtn.disabled = false;
      if (nextBtn) nextBtn.disabled = false;

      populateSearchDrawer(query);
      drawAllVisibleSearchHighlights();
      jumpToSearchResult(targetIdx, false);
    }

    function _applyPdfSearchZeroResults(query) {
      const counter = document.getElementById('pdf-search-counter');
      const prevBtn = document.getElementById('pdf-search-prev-btn');
      const nextBtn = document.getElementById('pdf-search-next-btn');

      pdfSearchCurrentMatchIdx = -1;
      if (counter) {
        counter.textContent = '0 / 0';
        counter.classList.remove('has-matches');
      }
      if (prevBtn) prevBtn.disabled = true;
      if (nextBtn) nextBtn.disabled = true;
      populateSearchDrawer(query, true);
      document.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());
    }

    // Main search executor with race-condition immune token architecture
    async function executePdfSearch(query) {
      if (!pdfDoc || !query || query.length < 1) {
        clearPdfSearch(true);
        return;
      }

      const myToken = ++pdfSearchToken;
      pdfSearchQuery = query;
      const normalizedQuery = query.toLocaleLowerCase('tr-TR');
      const counter = document.getElementById('pdf-search-counter');
      if (counter) counter.textContent = '...';

      // Clear previous search visual artifacts & results
      pdfSearchResults = [];
      pdfSearchPageMatchesCount = {};
      document.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());

      const completed = await scanPagesIteratively(myToken, pdfPageCount, query, normalizedQuery);
      if (!completed || myToken !== pdfSearchToken) return;

      const totalMatches = pdfSearchResults.length;
      if (totalMatches > 0) {
        _applyPdfSearchResults(totalMatches, query);
      } else {
        _applyPdfSearchZeroResults(query);
      }
    }

    function populateSearchDrawer(query, isZero) {
      const drawerList = document.getElementById('pdf-search-drawer-list');
      const drawerTitle = document.getElementById('pdf-search-drawer-title');
      if (!drawerList) return;

      if (isZero) {
        if (drawerTitle) drawerTitle.textContent = 'Sonuç Bulunamadı';
        drawerList.innerHTML = `<div style="padding: 1.2rem; text-align: center; color: var(--muted); font-size: 0.78rem;">"${esc(query)}" için eşleşme bulunamadı.</div>`;
        return;
      }

      const uniquePages = Object.keys(pdfSearchPageMatchesCount).length;
      if (drawerTitle) {
        drawerTitle.textContent = `${pdfSearchResults.length} sonuç (${uniquePages} sayfada)`;
      }

      let html = "";
      pdfSearchResults.forEach((match, idx) => {
        const isActive = (idx === pdfSearchCurrentMatchIdx);
        // Highlight query inside snippet
        const escSnippet = esc(match.snippet);
        let highlightedSnippet = escSnippet;
        try {
          const safeEscQuery = esc(query).replace(/[.*+?^${}()|[\]\\]/g, String.raw`\$&`);
          highlightedSnippet = escSnippet.replace(new RegExp(safeEscQuery, 'gi'), (m) => `<strong>${m}</strong>`);
        } catch (err) {
          // Regex derleme hatasında snippet'i olduğu gibi göster
          console.debug('PDF snippet highlight regex failed, using plain snippet:', err);
          highlightedSnippet = escSnippet;
        }

        html += `
          <div class="pdf-search-result-item ${isActive ? 'active' : ''}" data-match-idx="${idx}" onclick="jumpToSearchResult(${idx}, true)">
            <div class="pdf-search-result-meta">
              <span class="pdf-search-result-page">Sayfa ${match.pageNum}</span>
              <span>#${idx + 1}</span>
            </div>
            <div class="pdf-search-result-snippet">${highlightedSnippet}</div>
          </div>
        `;
      });
      drawerList.innerHTML = html;
    }

    // Go to next match
    function pdfSearchNext() {
      if (pdfSearchResults.length === 0) return;
      pdfSearchCurrentMatchIdx = (pdfSearchCurrentMatchIdx + 1) % pdfSearchResults.length;
      updateSearchNavState();
      jumpToSearchResult(pdfSearchCurrentMatchIdx, true);
    }

    // Go to prev match
    function pdfSearchPrev() {
      if (pdfSearchResults.length === 0) return;
      pdfSearchCurrentMatchIdx = (pdfSearchCurrentMatchIdx - 1 + pdfSearchResults.length) % pdfSearchResults.length;
      updateSearchNavState();
      jumpToSearchResult(pdfSearchCurrentMatchIdx, true);
    }

    function updateSearchNavState() {
      const counter = document.getElementById('pdf-search-counter');
      if (counter && pdfSearchResults.length > 0) {
        counter.textContent = `${pdfSearchCurrentMatchIdx + 1} / ${pdfSearchResults.length}`;
      }
      // Update active class in drawer
      document.querySelectorAll('.pdf-search-result-item').forEach((item, idx) => {
        if (idx === pdfSearchCurrentMatchIdx) {
          item.classList.add('active');
          item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
          item.classList.remove('active');
        }
      });
    }

    // Jump to specific search match
    function jumpToSearchResult(idx, shouldScrollSmooth) {
      if (idx < 0 || idx >= pdfSearchResults.length) return;
      pdfSearchCurrentMatchIdx = idx;
      updateSearchNavState();

      const match = pdfSearchResults[idx];
      const targetPage = match.pageNum;

      // Scroll to target page
      scrollToPage(targetPage);

      // Draw highlights and activate specific match on target page
      setTimeout(() => {
        drawPageSearchHighlights(targetPage);
        
        // Highlight active marker
        const activeMarker = document.querySelector(`.pdf-search-highlight[data-match-idx="${idx}"]`);
        if (activeMarker) {
          document.querySelectorAll('.pdf-search-highlight.active').forEach(el => el.classList.remove('active'));
          activeMarker.classList.add('active');
          activeMarker.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 120);
    }

    function _appendSearchHighlightDiv(rect, wrapperRect, globalIdx, highlightLayer) {
      if (rect.width <= 0 || rect.height <= 0) return;
      const hlDiv = document.createElement('div');
      hlDiv.className = 'pdf-search-highlight';
      hlDiv.style.left = ((rect.left - wrapperRect.left) / wrapperRect.width * 100) + '%';
      hlDiv.style.top = ((rect.top - wrapperRect.top) / wrapperRect.height * 100) + '%';
      hlDiv.style.width = (rect.width / wrapperRect.width * 100) + '%';
      hlDiv.style.height = (rect.height / wrapperRect.height * 100) + '%';

      if (globalIdx !== undefined) {
        hlDiv.dataset.matchIdx = globalIdx;
        if (globalIdx === pdfSearchCurrentMatchIdx) {
          hlDiv.classList.add('active');
        }
      }
      highlightLayer.appendChild(hlDiv);
    }

    function highlightSearchMatchesInSpan(span, normalizedQuery, wrapperRect, pageMatches, state) {
      const text = span.textContent;
      const textLower = text.toLocaleLowerCase('tr-TR');
      let pos = 0;

      while ((pos = textLower.indexOf(normalizedQuery, pos)) !== -1) {
        try {
          const range = document.createRange();
          const textNode = span.firstChild || span;
          if (textNode?.nodeType === Node.TEXT_NODE && pos + pdfSearchQuery.length <= textNode.length) {
            range.setStart(textNode, pos);
            range.setEnd(textNode, pos + pdfSearchQuery.length);
            const rects = range.getClientRects();
            const globalIdx = (state.pointer < pageMatches.length) ? pageMatches[state.pointer].matchIndex : undefined;

            for (const rect of rects) {
              _appendSearchHighlightDiv(rect, wrapperRect, globalIdx, state.highlightLayer);
            }
          }
        } catch (_err) {
          // Range sınır toleransı
        }

        state.pointer++;
        pos += Math.max(1, normalizedQuery.length);
      }
    }

    // Draw visual yellow highlight rects for a given page
    function drawPageSearchHighlights(pageNum) {
      if (!pdfSearchQuery || !pdfSearchPageMatchesCount[pageNum]) return;

      const textLayer = document.getElementById(`textLayer-${pageNum}`);
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
      const pageWrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (!textLayer || !highlightLayer || !pageWrapper) return;

      highlightLayer.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());

      const wrapperRect = pageWrapper.getBoundingClientRect();
      if (wrapperRect.width <= 0 || wrapperRect.height <= 0) return;

      const normalizedQuery = pdfSearchQuery.toLocaleLowerCase('tr-TR');
      const spans = textLayer.querySelectorAll('span:not(.markedContent)');
      const pageMatches = pdfSearchResults.filter(m => m.pageNum === pageNum);
      const state = { pointer: 0, highlightLayer };

      spans.forEach(span => {
        highlightSearchMatchesInSpan(span, normalizedQuery, wrapperRect, pageMatches, state);
      });
    }

    function drawAllVisibleSearchHighlights() {
      if (!pdfDoc || !pdfSearchQuery) return;
      for (let p = 1; p <= pdfPageCount; p++) {
        if (pdfRenderedPages[p] === 'done') {
          drawPageSearchHighlights(p);
        }
      }
    }

    // Global Keyboard Shortcut Listener for Workspace Reader (Ctrl+F, Space, Arrows)
    document.addEventListener('keydown', (e) => {
      const workspaceReader = document.getElementById('workspace-reader');
      const isReaderActive = workspaceReader && (workspaceReader.classList.contains('active') || workspaceReader.classList.contains('open'));

      if (!isReaderActive) return;

      if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
        e.preventDefault();
        togglePdfSearch(true);
        return;
      }

      // Guard against typing inside input, textarea or contenteditable
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
        return;
      }

      // Spacebar smooth reading / page advance (Kindle style)
      if (e.key === ' ' || e.code === 'Space') {
        const container = document.getElementById('pdf-canvas-container');
        if (container) {
          e.preventDefault();
          const scrollDistance = container.clientHeight * 0.78;
          if (e.shiftKey) {
            container.scrollBy({ top: -scrollDistance, behavior: 'smooth' });
          } else {
            container.scrollBy({ top: scrollDistance, behavior: 'smooth' });
          }
        }
        return;
      }

      // Page Navigation with Arrow keys
      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        pdfNextPage();
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        pdfPrevPage();
      }
    });

    // Handle window resize dynamically for spread layout
    let resizeSpreadTimer = null;
    window.addEventListener('resize', () => {
      if (resizeSpreadTimer) clearTimeout(resizeSpreadTimer);
      resizeSpreadTimer = setTimeout(() => {
        if (pdfDoc && pdfPageCount > 0 && pdfIsSpreadMode) {
          applySpreadLayout();
        }
      }, 200);
    });

    // Expose all PDF variables globally to window context for templates
    window.pdfPrevPage = pdfPrevPage;
    window.pdfNextPage = pdfNextPage;
    window.togglePdfSpreadMode = togglePdfSpreadMode;
    window.applySpreadLayout = applySpreadLayout;
    window.updateSpreadUI = updateSpreadUI;
    window.pdfGoToPageFromInput = pdfGoToPageFromInput;
    window.pdfZoomIn = pdfZoomIn;
    window.pdfZoomOut = pdfZoomOut;
    window.pdfFitWidth = pdfFitWidth;
    window.pdfFitHeight = pdfFitHeight;
    window.toggleNotesSidebar = toggleNotesSidebar;
    window.applyHighlight = applyHighlight;
    window.clearSelection = clearSelection;
    window.openNoteModalForSelection = openNoteModalForSelection;
    window.closePdfNoteModal = closePdfNoteModal;
    window.closePdfNoteModalDirect = closePdfNoteModalDirect;
    window.savePdfNote = savePdfNote;
    window.deleteHighlight = deleteHighlight;
    window.jumpToHighlight = jumpToHighlight;
    window.onPdfContainerScroll = onPdfContainerScroll;
    window.editExistingNote = editExistingNote;

    // Search Functions globally exposed
    window.togglePdfSearch = togglePdfSearch;
    window.closePdfSearch = closePdfSearch;
    window.clearPdfSearch = clearPdfSearch;
    window.pdfSearchNext = pdfSearchNext;
    window.pdfSearchPrev = pdfSearchPrev;
    window.onPdfSearchInput = onPdfSearchInput;
    window.onPdfSearchKeydown = onPdfSearchKeydown;
    window.togglePdfSearchResultsDrawer = togglePdfSearchResultsDrawer;
    window.jumpToSearchResult = jumpToSearchResult;

    // TOC & TTS Functions
    function toggleTocSidebar() {
      const sidebar = document.getElementById('pdf-toc-sidebar');
      const btn = document.getElementById('pdf-toc-sidebar-btn');
      const notesSidebar = document.getElementById('pdf-notes-sidebar');
      const notesBtn = document.getElementById('pdf-notes-sidebar-btn');
      if (!sidebar) return;

      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (btn) btn.classList.remove('active');
      } else {
        if (notesSidebar) {
          notesSidebar.classList.remove('open');
          if (notesBtn) notesBtn.classList.remove('active');
        }
        sidebar.classList.add('open');
        if (btn) btn.classList.add('active');
      }
    }
    window.toggleTocSidebar = toggleTocSidebar;

    async function fetchSynthesizedTocFallback(tocList) {
      try {
        if (activeWorkspaceBook?.hash) {
          const res = await apiFetch(`/api/books/${activeWorkspaceBook.hash}/toc`);
          if (res.ok) {
            const data = await res.json();
            if (data.items && data.items.length > 0) {
              renderSynthesizedToc(data.items);
              return true;
            }
          }
        }
      } catch (e) {
        console.debug('TOC fallback fetch warning:', e);
      }
      tocList.innerHTML = '<div class="pdf-notes-empty">Bu belgede yer imi veya içindekiler tablosu bulunamadı.</div>';
      return false;
    }

    async function loadPdfOutline(pdf) {
      const tocList = document.getElementById('pdf-toc-list');
      if (!tocList) return;
      try {
        const outline = await pdf.getOutline();
        if (!outline || outline.length === 0) {
          tocList.innerHTML = '<div style="padding:1rem; text-align:center; color:var(--muted); font-size:0.8rem;"><i class="fas fa-spinner fa-spin"></i> İçindekiler tablosu taranıyor...</div>';
          await fetchSynthesizedTocFallback(tocList);
          return;
        }
        tocList.innerHTML = '';
        
        function appendItems(items, level = 0) {
          for (const item of items) {
            const div = document.createElement('button');
            div.type = 'button';
            div.className = `pdf-toc-item level-${Math.min(level, 2)}`;
            div.innerHTML = `<span>${esc(item.title)}</span><i class="fas fa-chevron-right" style="font-size:0.65rem; opacity:0.4;"></i>`;
            
            div.addEventListener('click', async () => {
              try {
                let dest = item.dest;
                if (typeof dest === 'string') {
                  dest = await pdf.getDestination(dest);
                }
                if (dest && Array.isArray(dest)) {
                  const pageRef = dest[0];
                  const pageIdx = await pdf.getPageIndex(pageRef);
                  jumpToPdfPage(pageIdx + 1);
                }
              } catch (e) {
                console.error('TOC atlama hatası:', e);
              }
            });
            tocList.appendChild(div);
            if (item.items && item.items.length > 0) {
              appendItems(item.items, level + 1);
            }
          }
        }
        appendItems(outline, 0);
      } catch (err) {
        // İsteğe bağlı / sessiz hata toleransı: İçindekiler tablosu okunamadığında boş durum mesajı gösterilir
        console.debug('loadPdfOutline hatası:', err);
        tocList.innerHTML = '<div class="pdf-notes-empty">İçindekiler tablosu okunamadı.</div>';
      }
    }

    function togglePdfTTS() {
      if (!('speechSynthesis' in window)) {
        showToast('Tarayıcınız sesli okuma özelliğini (Web Speech API) desteklemiyor.', 'warning');
        return;
      }

      const btn = document.getElementById('pdf-tts-btn');

      if (window.speechSynthesis.speaking || isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
        showToast('Seslendirme durduruldu.', 'info', 1800);
        return;
      }

      const selection = window.getSelection().toString().trim();
      let textToSpeak = selection;

      if (!textToSpeak && pdfDoc) {
        const activeWrapper = document.getElementById(`pdf-page-wrapper-${pdfPageNum}`);
        if (activeWrapper) {
          textToSpeak = activeWrapper.querySelector('.textLayer')?.innerText?.trim() || '';
        }
      }

      if (!textToSpeak) {
        showToast('Seslendirilecek metin bulunamadı. Lütfen bir metin seçin veya sayfanın tam yüklenmesini bekleyin.', 'warning');
        return;
      }

      const utterance = new SpeechSynthesisUtterance(textToSpeak.slice(0, 3500));
      utterance.lang = 'tr-TR';
      utterance.rate = 1.0;

      utterance.onstart = () => {
        isSpeaking = true;
        if (btn) {
          btn.classList.add('active');
          btn.innerHTML = '<i class="fas fa-stop"></i> Durdur';
        }
        showToast(`Sayfa ${pdfPageNum} seslendiriliyor...`, 'info', 2500);
      };

      utterance.onend = () => {
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
      };

      utterance.onerror = () => {
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
      };

      window.speechSynthesis.speak(utterance);
    }
    window.togglePdfTTS = togglePdfTTS;

    // Event Delegation for clicking on citation chips inside chat messages
    document.addEventListener('click', (e) => {
      const citeEl = e.target.closest('.chat-page-cite');
      if (citeEl) {
        e.preventDefault();
        const page = citeEl.dataset.jumpPage;
        if (page) {
          jumpToPdfPage(page);
        }
      }
    });

    // Expose functions globally to window context
    window.openWorkspace = openWorkspace;
    window.closeWorkspace = closeWorkspace;
    window.sendWorkspaceMessage = sendWorkspaceMessage;
    window.handleWorkspaceChatKey = handleWorkspaceChatKey;

    function toggleWorkspaceExportMenu() {
      const menu = document.getElementById('workspace-export-menu');
      if (!menu) return;
      menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    }
    window.toggleWorkspaceExportMenu = toggleWorkspaceExportMenu;

    function exportCurrentWorkspaceBook(format) {
      if (!activeWorkspaceBook?.hash) {
        if (typeof showToast === 'function') showToast('Dışa aktarılacak aktif kitap bulunamadı.', 'error');
        return;
      }
      const menu = document.getElementById('workspace-export-menu');
      if (menu) menu.style.display = 'none';
      window.open(`/api/books/${activeWorkspaceBook.hash}/export/${format}`, '_blank');
    }
    window.exportCurrentWorkspaceBook = exportCurrentWorkspaceBook;

    document.addEventListener('click', (e) => {
      const wrap = document.querySelector('.workspace-export-wrapper');
      const menu = document.getElementById('workspace-export-menu');
      if (menu && wrap && !wrap.contains(e.target)) {
        menu.style.display = 'none';
      }
    });

    // Dynamic Connection Status Monitor
    function updateConnectionStatus() {
      const badge = document.getElementById('workspace-status-badge');
      if (!badge) return;

      if (navigator.onLine) {
        badge.classList.remove('offline');
        badge.innerHTML = '<i class="fas fa-robot"></i> <span id="workspace-status-text">AI Asistan Bağlı</span>';
      } else {
        badge.classList.add('offline');
        badge.innerHTML = '<i class="fas fa-triangle-exclamation"></i> <span id="workspace-status-text">Bağlantı Yok</span>';
      }
    }

    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    document.addEventListener('DOMContentLoaded', updateConnectionStatus);

    // --- [7.3] Auto-Synthesized TOC Renderer ---
    function renderSynthesizedToc(items) {
      const tocList = document.getElementById('pdf-toc-list');
      if (!tocList) return;
      tocList.innerHTML = '';
      items.forEach(it => {
        const div = document.createElement('button');
        div.type = 'button';
        div.className = `pdf-toc-item level-${Math.min(it.level || 1, 2)}`;
        const srcBadge = it.source === 'auto_detected' ? '<span style="font-size:0.65rem; color:#b8862f; margin-left:4px;">(Otomatik)</span>' : '';
        div.innerHTML = `<span style="flex:1;">${esc(it.title)} ${srcBadge}</span><span style="font-size:0.75rem; color:var(--muted); font-family:var(--font-mono, monospace);">s. ${it.page_number}</span>`;
        div.addEventListener('click', () => {
          jumpToPdfPage(it.target_page || it.page_number);
        });
        tocList.appendChild(div);
      });
    }
    window.renderSynthesizedToc = renderSynthesizedToc;

    // --- [8.1] ChromaGuard™ Smart Surface & Image Preservation ---
    let currentReaderSurfaceMode = 'normal';
    try {
      currentReaderSurfaceMode = localStorage.getItem('pdf_reader_surface_mode') || 'normal';
    } catch (e) {}

    function applySepiaFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        data[i] = Math.min(255, (r * 0.393) + (g * 0.769) + (b * 0.189) + 20);
        data[i + 1] = Math.min(255, (r * 0.349) + (g * 0.686) + (b * 0.168) + 15);
        data[i + 2] = Math.min(255, (r * 0.272) + (g * 0.534) + (b * 0.131) + 10);
      }
    }

    function applyEinkFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const gray = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
        let val = gray;
        if (gray > 185) {
          val = 245;
        } else if (gray < 75) {
          val = 20;
        }
        data[i] = val;
        data[i + 1] = val;
        data[i + 2] = val;
      }
    }

    function applyChromaGuardFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const maxC = Math.max(r, g, b);
        const minC = Math.min(r, g, b);
        const chroma = maxC - minC;

        // Chroma guard check: If pixel has significant color (chroma > 28), PRESERVE original colors!
        if (chroma > 28) {
          continue;
        }

        // Low-chroma text/paper: Invert luminance onto dark OLED background (#181a20)
        const lum = (r * 0.299 + g * 0.587 + b * 0.114);
        const invLum = 225 - (lum * 0.78);
        data[i] = Math.max(22, Math.min(235, Math.round(invLum * 0.96)));
        data[i + 1] = Math.max(24, Math.min(235, Math.round(invLum * 0.98)));
        data[i + 2] = Math.max(28, Math.min(240, Math.round(invLum * 1.02)));
      }
    }

    function applyChromaGuard(canvas, mode) {
      // Sepia, e-ink and normal modes are handled via zero-cost GPU CSS filters on [data-surface-mode]
      if (!canvas || mode !== 'chromaguard') return;

      const runTransform = () => {
        try {
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          const w = canvas.width;
          const h = canvas.height;
          if (!w || !h) return;
          const imgData = ctx.getImageData(0, 0, w, h);
          applyChromaGuardFilter(imgData.data, imgData.data.length);
          ctx.putImageData(imgData, 0, 0);
        } catch (e) {
          console.debug('ChromaGuard pixel transform warning:', e);
        }
      };

      if (typeof window.requestIdleCallback === 'function') {
        window.requestIdleCallback(() => runTransform(), { timeout: 200 });
      } else {
        setTimeout(runTransform, 16);
      }
    }
    window.applyChromaGuard = applyChromaGuard;

    function setReaderSurfaceMode(mode) {
      const prevMode = currentReaderSurfaceMode;
      currentReaderSurfaceMode = mode;
      try {
        localStorage.setItem('pdf_reader_surface_mode', mode);
      } catch (e) {}

      const viewer = document.getElementById('custom-pdf-viewer');
      if (viewer) {
        viewer.dataset.surfaceMode = mode;
      }

      document.querySelectorAll('#reader-surface-group .surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `btn-surface-${mode}`);
      });

      // Switching between normal, sepia and eink requires ZERO re-renders: GPU CSS filter handles it in 0ms!
      const requiresReRender = (prevMode === 'chromaguard' && mode !== 'chromaguard') || (mode === 'chromaguard');
      if (!requiresReRender) {
        return;
      }

      // Cancel ongoing render tasks and re-render only when entering/leaving ChromaGuard OLED mode
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};

      // Clear render tracker and re-render visible canvases
      pdfRenderedPages = {};
      checkVisiblePagesAndRender();
    }
    window.setReaderSurfaceMode = setReaderSurfaceMode;

    // --- [6.4] Mobile Instant LAN Handoff (QR Code) ---
    let handoffCountdownTimer = null;

    async function openHandoffModal() {
      if (!activeWorkspaceBook) return;
      const modal = document.getElementById('handoff-modal');
      const qrContainer = document.getElementById('handoff-qr-container');
      const urlText = document.getElementById('handoff-url-text');
      const timerEl = document.getElementById('handoff-timer');
      if (!modal || !qrContainer) return;

      modal.classList.remove('closing');
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      if (typeof activateModalFocus === 'function') activateModalFocus(modal);
      qrContainer.innerHTML = '<div style="padding:3rem 1rem; color:#888;"><i class="fas fa-spinner fa-spin"></i> QR Kod Üretiliyor...</div>';
      if (urlText) urlText.textContent = '';

      try {
        const res = await apiFetch('/api/auth/handoff-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_hash: activeWorkspaceBook.hash,
            page_number: pdfPageNum || 1,
          }),
        });

        if (!res.ok) {
          qrContainer.innerHTML = '<div style="color:var(--accent); padding:2rem 1rem;">QR kod üretilemedi.</div>';
          return;
        }

        const data = await res.json();
        qrContainer.innerHTML = data.qr_svg;
        if (urlText) urlText.innerHTML = `Bağlantı: <a href="${data.url}" target="_blank" style="color:var(--accent); text-decoration:none;">${data.url}</a>`;

        let remaining = data.expires_in_seconds || 120;
        if (handoffCountdownTimer) clearInterval(handoffCountdownTimer);
        handoffCountdownTimer = setInterval(() => {
          remaining -= 1;
          if (timerEl) timerEl.textContent = `Kod süresi: ${remaining} sn`;
          if (remaining <= 0) {
            clearInterval(handoffCountdownTimer);
            qrContainer.innerHTML = '<div style="color:var(--muted); padding:3rem 1rem;">QR kodun süresi doldu.<br><button class="btn-empty-add" onclick="openHandoffModal()" style="margin-top:0.8rem; font-size:0.8rem;">Yenile</button></div>';
          }
        }, 1000);
      } catch (err) {
        qrContainer.innerHTML = `<div style="color:var(--accent); padding:2rem 1rem;">Hata: ${esc(String(err))}</div>`;
      }
    }
    window.openHandoffModal = openHandoffModal;

    function closeHandoffModal() {
      if (handoffCountdownTimer) {
        clearInterval(handoffCountdownTimer);
        handoffCountdownTimer = null;
      }
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('handoff-modal');
      } else {
        const modal = document.getElementById('handoff-modal');
        if (modal) {
          modal.style.display = 'none';
          modal.classList.remove('open');
        }
        document.body.classList.remove('modal-open');
      }
    }
    window.closeHandoffModal = closeHandoffModal;

    // Direct page teleportation helper
    function openWorkspaceAtPage(bookOrHash, pageNum) {
      let book = bookOrHash;
      if (typeof bookOrHash === 'string') {
        if (typeof allBooks !== 'undefined' && Array.isArray(allBooks)) {
          book = allBooks.find(b => (b.hash || b.dosya_hash) === bookOrHash);
        }
        if (!book) {
          book = { hash: bookOrHash, title: 'Belge', category: 'PDF' };
        }
      }
      openWorkspace(book, pageNum);
      if (pageNum && pageNum > 0) {
        setTimeout(() => {
          jumpToPdfPage(pageNum);
        }, 600);
      }
    }
    window.openWorkspaceAtPage = openWorkspaceAtPage;

    // Listen for DPI changes (e.g. dragging between Retina & standard screens)
    if (typeof window !== 'undefined' && window.matchMedia) {
      const setupDprWatcher = () => {
        const dpr = window.devicePixelRatio || 1;
        const mq = window.matchMedia(`(resolution: ${dpr}dppx)`);
        mq.addEventListener('change', () => {
          if (pdfDoc && typeof isPdfOpen !== 'undefined' && isPdfOpen) {
            Object.keys(pdfRenderedPages).forEach(p => cleanupOffscreenPage(Number(p)));
            if (typeof checkVisiblePagesAndRender === 'function') checkVisiblePagesAndRender();
          }
          setupDprWatcher();
        }, { once: true });
      };
      setupDprWatcher();
    }

```


## DOSYA 6.5: static/js/ui_chat_settings.js (Sohbet Daktilo Hızlandırması & Ayarlar Focus Entegrasyonu)

**Dosya Yolu:** `static/js/ui_chat_settings.js`

```javascript
/* ═══════════ ui_chat_settings.js — Assistant Drawer, Settings & Analytics ═══════════ */
    function startChatTypewriter(rawReply, msgEl, chatBody) {
      if (!msgEl) return;
      const body = chatBody || document.getElementById('chat-body');
      const words = (rawReply || '').split(' ');
      const totalWords = words.length || 1;
      const wordDelay = Math.min(25, Math.max(5, Math.floor(2500 / totalWords)));
      let currentText = '';
      let wordIndex = 0;

      const isUserNearBottom = () => {
        if (!body) return true;
        return (body.scrollHeight - body.scrollTop - body.clientHeight) < 60;
      };

      let lastParagraphCheck = '';
      const timer = setInterval(() => {
        if (wordIndex < words.length) {
          currentText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
          wordIndex++;

          const hasNewParagraph = currentText.includes('\n\n') && currentText.lastIndexOf('\n\n') > lastParagraphCheck.length;
          if (hasNewParagraph) {
            msgEl.innerHTML = parseMarkdown(currentText);
            lastParagraphCheck = currentText.slice(0, currentText.lastIndexOf('\n\n'));
          } else if (lastParagraphCheck.length === 0) {
            msgEl.textContent = currentText;
          } else {
            const unrenderedPart = currentText.slice(lastParagraphCheck.length);
            const safeUnrendered = typeof esc === 'function' ? esc(unrenderedPart) : unrenderedPart;
            msgEl.innerHTML = parseMarkdown(lastParagraphCheck) + '<p>' + safeUnrendered + '</p>';
          }

          if (isUserNearBottom() && body) {
            body.scrollTop = body.scrollHeight;
          }
        } else {
          clearInterval(timer);
          msgEl.innerHTML = parseMarkdown(rawReply);
          if (isUserNearBottom() && body) {
            body.scrollTop = body.scrollHeight;
          }
        }
      }, wordDelay);
    }
    window.startChatTypewriter = startChatTypewriter;

    function sendMessage() {
      const input = document.getElementById('chat-input');
      const sendBtn = document.querySelector('.btn-send');
      const text = input.value.trim();
      if (!text || text.length > 1000) return;

      // Lock UI
      input.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      addChatMessage('sender', text);
      input.value = '';
      updateChatCounter(); // Reset counter

      const aiMsgId = 'ai-typing-' + Date.now();
      addChatMessage('ai', 'Düşünüyorum...', aiMsgId);

      apiFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
        .then(r => r ? r.json() : null)
        .then(data => {
          const msgEl = document.getElementById(aiMsgId);
          if (msgEl) {
            startChatTypewriter(data?.response || '', msgEl);
          }
        })
        .catch(err => {
          const msgEl = document.getElementById(aiMsgId);
          if (msgEl) msgEl.textContent = "Hata oluştu. Lütfen tekrar dene.";
        })
        .finally(() => {
          // Unlock UI
          input.disabled = false;
          if (sendBtn) sendBtn.disabled = false;
          input.focus();
        });
    }

    function addChatMessage(type, text, id = null) {
      const body = document.getElementById('chat-body');
      if (!body) return;
      const msg = document.createElement('div');
      msg.className = `chat-msg chat-${type}`;
      
      if (type === 'ai') {
        msg.innerHTML = parseMarkdown(text);
      } else {
        msg.textContent = text;
      }
      
      if (id) msg.id = id;
      body.appendChild(msg);
      body.scrollTop = body.scrollHeight;
    }

    const DEFAULT_CASCADE_MODELS = [
      "gemini-3.8-flash",
      "gemini-3.7-flash",
      "gemini-3.6-flash",
      "gemini-3.5-flash",
      "gemini-3.5-flash-lite"
    ];

    function populateCascadeSlots(models) {
      const list = Array.isArray(models) && models.length ? models : DEFAULT_CASCADE_MODELS;
      for (let i = 0; i < 5; i++) {
        const el = document.getElementById(`cascade-model-${i}`);
        if (el) {
          el.value = (list[i] || '').trim();
        }
      }
    }

    function getCascadeSlots() {
      const models = [];
      for (let i = 0; i < 5; i++) {
        const el = document.getElementById(`cascade-model-${i}`);
        if (el) {
          const val = (el.value || '').trim();
          if (val) models.push(val);
        }
      }
      return models.length ? models : [...DEFAULT_CASCADE_MODELS];
    }

    function resetCascadeModelsToDefault() {
      populateCascadeSlots(DEFAULT_CASCADE_MODELS);
    }
    window.resetCascadeModelsToDefault = resetCascadeModelsToDefault;

    function populateServerOcrVisionSettings(data) {
      document.getElementById('set-pages').value = data.max_pages || 20;
      document.getElementById('set-ocr-pages').value = data.ocr_pages || 20;
      document.getElementById('set-vision-pages').value = data.vision_pages || 20;
      document.getElementById('set-vision-dim').value = data.vision_max_image_dim || 1200;
      document.getElementById('set-vision-quality').value = data.vision_jpeg_quality || 82;
      document.getElementById('set-tesseract-cmd').value = data.tesseract_cmd || '';
      if (document.getElementById('set-watchfolder-enabled')) {
        document.getElementById('set-watchfolder-enabled').checked = Boolean(data.watchfolder_enabled);
      }
      if (document.getElementById('set-watchfolder-path')) {
        document.getElementById('set-watchfolder-path').value = data.watchfolder_path || '';
      }
      const maxChars = data.ai_max_chars || 50000;
      document.getElementById('set-ai-max-chars').value = maxChars;
      document.getElementById('ai-max-chars-val').innerText = maxChars;
    }

    function _populateApiKeyAndModel(data) {
      if (data.has_gemini_key || data.has_ai_api_key) {
        const keyEl = document.getElementById('set-api-key');
        if (keyEl && !keyEl.value) keyEl.placeholder = "•••••••• (Sunucuda Yapılandırılmış)";
      } else if (data.ai_api_key && !data.ai_api_key.startsWith('••')) {
        document.getElementById('set-api-key').value = data.ai_api_key;
      }
      if (data.gemini_model) {
        localStorage.setItem('gemini_model', data.gemini_model);
        if ((data.ai_provider || document.getElementById('set-ai-provider')?.value || 'gemini') === 'gemini') {
          const mn = document.getElementById('set-ai-model-name');
          if (mn) mn.value = data.gemini_model;
        }
      }
    }

    function populateServerAISettingsFields(data) {
      if (data.ai_provider) document.getElementById('set-ai-provider').value = data.ai_provider;
      _populateApiKeyAndModel(data);
      if (data.ai_base_url) document.getElementById('set-ai-base-url').value = data.ai_base_url;
      if (data.gemini_cascade_mode !== undefined && document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = Boolean(data.gemini_cascade_mode);
        localStorage.setItem('gemini_cascade_mode', Boolean(data.gemini_cascade_mode));
      }
      if (Array.isArray(data.gemini_cascade_models)) {
        populateCascadeSlots(data.gemini_cascade_models);
        localStorage.setItem('gemini_cascade_models', JSON.stringify(data.gemini_cascade_models));
      }
      updateAIUI();
    }

    function _applyPasswordStateBadge(hasPassword, pwdBadge, pwdInput, removePwdBtn) {
      if (hasPassword) {
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
          pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
          pwdBadge.style.color = '#5f7a4f';
        }
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = '•••••••• (Şifre Belirlenmiş)';
        }
        if (removePwdBtn) removePwdBtn.style.display = 'inline-flex';
      } else {
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#b8862f;"></i> Şifre Belirlenmemiş';
          pwdBadge.style.background = 'rgba(184,134,47, 0.12)';
          pwdBadge.style.color = '#b8862f';
        }
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = 'Erişim şifresi belirleyin...';
        }
        if (removePwdBtn) removePwdBtn.style.display = 'none';
      }
    }

    function populateServerSecuritySettings(data) {
      const pwdInput = document.getElementById('set-access-password');
      const pwdBadge = document.getElementById('sec-pwd-status-badge');
      const removePwdBtn = document.getElementById('btn-remove-access-pwd');
      const phoneUrlDisplay = document.getElementById('phone-connection-url-display');
      const opdsUrlDisplay = document.getElementById('opds-connection-url-display');
      const phoneUrl = data.phone_url || (window.location.protocol + '//' + window.location.hostname + ':8000');
      if (phoneUrlDisplay) phoneUrlDisplay.textContent = phoneUrl;
      if (opdsUrlDisplay) opdsUrlDisplay.textContent = phoneUrl.replace(/\/$/, '') + '/opds';

      _applyPasswordStateBadge(data.has_access_password, pwdBadge, pwdInput, removePwdBtn);
    }

    function syncOpenSettingsFromServer(data) {
      if (!data) return;
      window.appSettings = data;
      populateServerOcrVisionSettings(data);
      populateServerAISettingsFields(data);

      const tsStatus = document.getElementById('tesseract-status');
      if (tsStatus) {
        const cmd = (data.tesseract_cmd || '').trim();
        if (cmd) {
          tsStatus.innerHTML = '<i class="fas fa-check-circle" style="color:#4caf50; margin-right:0.3rem;"></i> Tesseract yolu ayarlanmış: <code style="font-size:0.7rem;">' + esc(cmd) + '</code>';
        } else {
          tsStatus.innerHTML = '<i class="fas fa-info-circle" style="color:var(--accent); margin-right:0.3rem;"></i> Tesseract yolu belirtilmemiş. Sistem PATH\'ten otomatik bulunmaya çalışılacak.';
        }
      }

      populateServerSecuritySettings(data);
    }

    function getModelPlaceholder(provider) {
      if (provider === 'gemini') return 'gemini-3.5-flash-lite';
      if (provider === 'ollama') return 'Örn: llama3';
      return 'Örn: local-model';
    }

    function _getSavedGeminiModel() {
      let savedGemini = localStorage.getItem('gemini_model');
      if (!savedGemini || savedGemini.includes('3.1') || savedGemini.includes('1.5')) {
        savedGemini = 'gemini-3.5-flash-lite';
        localStorage.setItem('gemini_model', 'gemini-3.5-flash-lite');
      }
      return savedGemini;
    }

    function _getSavedCascadeModels() {
      let savedCascadeModels = null;
      try {
        const raw = localStorage.getItem('gemini_cascade_models');
        if (raw) savedCascadeModels = JSON.parse(raw);
      } catch {
        // Ignore parse errors on corrupted local cache
      }
      if (!savedCascadeModels && window.appSettings?.gemini_cascade_models) {
        savedCascadeModels = window.appSettings.gemini_cascade_models;
      }
      return savedCascadeModels || DEFAULT_CASCADE_MODELS;
    }

    // --- Yeni Fonksiyonlar (Settings & Edit) ---
    function openSettings() {
      try {
        const { provider, apiKey, baseUrl, modelName } = getAISettings();
        const providerEl = document.getElementById('set-ai-provider');
        const apiKeyEl = document.getElementById('set-api-key');
        const baseUrlEl = document.getElementById('set-ai-base-url');
        const modelNameEl = document.getElementById('set-ai-model-name');
        const modal = document.getElementById('settings-modal');

        const savedGemini = _getSavedGeminiModel();

        if (providerEl) providerEl.value = provider;
        if (apiKeyEl) apiKeyEl.value = apiKey;
        if (baseUrlEl) baseUrlEl.value = baseUrl;
        if (modelNameEl) {
          modelNameEl.value = provider === 'gemini' ? savedGemini : modelName;
          modelNameEl.placeholder = getModelPlaceholder(provider);
        }
        if (document.getElementById('set-gemini-cascade-mode')) {
          const savedCascade = localStorage.getItem('gemini_cascade_mode');
          document.getElementById('set-gemini-cascade-mode').checked = savedCascade !== null ? savedCascade === 'true' : true;
        }

        populateCascadeSlots(_getSavedCascadeModels());

        updateAIUI();
        
        if (modal) {
          modal.classList.remove('closing');
          modal.classList.add('open');
          document.body.classList.add('modal-open');
          switchSettingsTab('ai');
          if (typeof activateModalFocus === 'function') activateModalFocus(modal);
        }
      } catch (err) {
        console.error("openSettings error:", err);
      }

      apiFetch('/api/settings')
        .then(r => r ? r.json() : null)
        .then(syncOpenSettingsFromServer)
        .catch(err => console.error("openSettings settings fetch error:", err));
    }

    function _loadSettingsFromLocalStorage() {
      const provider = localStorage.getItem('ai_provider') || 'gemini';
      const apiKey = localStorage.getItem('ai_api_key') || '';
      const baseUrl = localStorage.getItem('ai_base_url') || '';
      let geminiModel = localStorage.getItem('gemini_model') || 'gemini-3.5-flash-lite';
      if (!geminiModel || geminiModel.includes('3.1') || geminiModel.includes('1.5')) {
        geminiModel = 'gemini-3.5-flash-lite';
        localStorage.setItem('gemini_model', 'gemini-3.5-flash-lite');
      }
      const ollamaModel = localStorage.getItem('ollama_model') || '';
      const lmstudioModel = localStorage.getItem('lmstudio_model') || '';

      let savedCascadeModels = null;
      try {
        const raw = localStorage.getItem('gemini_cascade_models');
        if (raw) savedCascadeModels = JSON.parse(raw);
      } catch {
        // Ignore cache read errors
      }

      return {
        ai_provider: provider,
        ai_api_key: apiKey,
        ai_base_url: baseUrl,
        gemini_model: geminiModel,
        ollama_model: ollamaModel,
        lmstudio_model: lmstudioModel,
        vision_pages: Number.parseInt(localStorage.getItem('vision_pages') || '20', 10),
        vision_max_image_dim: Number.parseInt(localStorage.getItem('vision_max_image_dim') || '1200', 10),
        vision_jpeg_quality: Number.parseInt(localStorage.getItem('vision_jpeg_quality') || '82', 10),
        ai_max_chars: Number.parseInt(localStorage.getItem('ai_max_chars') || '50000', 10),
        gemini_cascade_mode: localStorage.getItem('gemini_cascade_mode') !== null ? localStorage.getItem('gemini_cascade_mode') === 'true' : true,
        gemini_cascade_models: savedCascadeModels || DEFAULT_CASCADE_MODELS
      };
    }

    function _populateSettingsInputs(settings) {
      if (document.getElementById('set-ai-provider')) document.getElementById('set-ai-provider').value = settings.ai_provider;
      if (document.getElementById('set-api-key')) document.getElementById('set-api-key').value = settings.ai_api_key;
      if (document.getElementById('set-ai-base-url')) document.getElementById('set-ai-base-url').value = settings.ai_base_url;
      if (document.getElementById('set-ai-model-name')) {
        let model = settings.lmstudio_model;
        if (settings.ai_provider === 'gemini') model = settings.gemini_model;
        else if (settings.ai_provider === 'ollama') model = settings.ollama_model;
        document.getElementById('set-ai-model-name').value = model;
      }
      if (document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = settings.gemini_cascade_mode;
      }
      populateCascadeSlots(settings.gemini_cascade_models);
      
      const maxChars = settings.ai_max_chars || 50000;
      if (document.getElementById('set-ai-max-chars')) {
        document.getElementById('set-ai-max-chars').value = maxChars;
        document.getElementById('ai-max-chars-val').innerText = maxChars;
      }
      updateAIUI();
    }

    function _applyServerAiCredentials(data) {
      if (data.ai_provider) {
        document.getElementById('set-ai-provider').value = data.ai_provider;
      }
      const keyEl = document.getElementById('set-api-key');
      if (data.has_gemini_key || data.has_ai_api_key) {
        if (keyEl && !keyEl.value) keyEl.placeholder = "•••••••• (Sunucuda Yapılandırılmış)";
      } else if (data.ai_api_key && !data.ai_api_key.startsWith('••') && keyEl) {
        keyEl.value = data.ai_api_key;
      }
      if (data.ai_base_url) {
        document.getElementById('set-ai-base-url').value = data.ai_base_url;
      }
      if (data.gemini_model) {
        localStorage.setItem('gemini_model', data.gemini_model);
        const currProv = data.ai_provider || document.getElementById('set-ai-provider')?.value || 'gemini';
        if (currProv === 'gemini') {
          const mn = document.getElementById('set-ai-model-name');
          if (mn) mn.value = data.gemini_model;
        }
      }
    }

    function _applyServerCascadeAndWatchfolder(data) {
      if (data.gemini_cascade_mode !== undefined && document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = Boolean(data.gemini_cascade_mode);
        localStorage.setItem('gemini_cascade_mode', Boolean(data.gemini_cascade_mode));
      }
      if (data.gemini_cascade_models && Array.isArray(data.gemini_cascade_models)) {
        populateCascadeSlots(data.gemini_cascade_models);
        localStorage.setItem('gemini_cascade_models', JSON.stringify(data.gemini_cascade_models));
      }
      if (data.watchfolder_enabled !== undefined && document.getElementById('set-watchfolder-enabled')) {
        document.getElementById('set-watchfolder-enabled').checked = !!data.watchfolder_enabled;
      }
      if (data.watchfolder_path !== undefined && document.getElementById('set-watchfolder-path')) {
        document.getElementById('set-watchfolder-path').value = data.watchfolder_path || '';
      }
    }

    function _applyServerSettingsToUI(data) {
      _applyServerAiCredentials(data);
      _applyServerCascadeAndWatchfolder(data);
      updateAIUI();
    }

    async function loadSettings() {
      try {
        window.appSettings = _loadSettingsFromLocalStorage();
        _populateSettingsInputs(window.appSettings);

        // Then, try to sync with server
        const res = await apiFetch('/api/settings');
        if (res?.ok) {
          const data = await res.json();
          window.appSettings = { ...window.appSettings, ...data };
          _applyServerSettingsToUI(data);
        }
      } catch (e) {
        console.error("Settings load failed:", e);
      }
    }

    function _collectNumericSettings() {
      const rawVPages = Number.parseInt(document.getElementById('set-vision-pages')?.value, 10);
      const rawVDim = Number.parseInt(document.getElementById('set-vision-dim')?.value, 10);
      const rawVQual = Number.parseInt(document.getElementById('set-vision-quality')?.value, 10);
      const rawMaxPages = Number.parseInt(document.getElementById('set-pages')?.value, 10);
      const rawOcrPages = Number.parseInt(document.getElementById('set-ocr-pages')?.value, 10);
      const rawMaxChars = Number.parseInt(document.getElementById('set-ai-max-chars')?.value, 10);

      return {
        vPages: Number.isNaN(rawVPages) ? 20 : rawVPages,
        vDim: Number.isNaN(rawVDim) ? 1200 : rawVDim,
        vQual: Number.isNaN(rawVQual) ? 82 : rawVQual,
        maxPages: Number.isNaN(rawMaxPages) ? 20 : rawMaxPages,
        ocrPages: Number.isNaN(rawOcrPages) ? 20 : rawOcrPages,
        maxChars: Number.isNaN(rawMaxChars) ? 50000 : rawMaxChars
      };
    }

    function _handleSettingsSaveSuccess(settings, saveBtn, originalHtml) {
      window.appSettings = { ...window.appSettings, ...settings };
      if (settings.access_password) {
        const pwdBadge = document.getElementById('sec-pwd-status-badge');
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
          pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
          pwdBadge.style.color = '#5f7a4f';
        }
        const pwdInput = document.getElementById('set-access-password');
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = '•••••••• (Şifre Belirlenmiş)';
        }
        const removePwdBtn = document.getElementById('btn-remove-access-pwd');
        if (removePwdBtn) removePwdBtn.style.display = 'inline-flex';
      }
      if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-check"></i> <span>Kaydedildi</span>';
        saveBtn.style.background = '#5f7a4f';
      }
      showToast('Ayarlar başarıyla kaydedildi.', 'success');
      setTimeout(() => {
        closeSettingsDirect();
        if (saveBtn) {
          saveBtn.innerHTML = originalHtml;
          saveBtn.disabled = false;
          saveBtn.style.background = '';
        }
      }, 450);
    }

    function _persistSettingsLocally(aiConfig, num, cascadeMode, cascadeModels) {
      const { provider, apiKey, isPlaceholderMasked, baseUrl, modelName } = aiConfig;
      localStorage.setItem('ai_provider', provider);
      if (apiKey && !apiKey.startsWith('••') && !apiKey.includes('•')) {
        localStorage.setItem('ai_api_key', apiKey);
      } else if (!apiKey && !isPlaceholderMasked) {
        localStorage.removeItem('ai_api_key');
      }
      localStorage.setItem('ai_base_url', baseUrl);

      const modelKeyMap = { gemini: 'gemini_model', ollama: 'ollama_model', lmstudio: 'lmstudio_model' };
      const targetKey = modelKeyMap[provider];
      if (targetKey) {
        localStorage.setItem(targetKey, modelName);
      }

      localStorage.setItem('vision_pages', num.vPages);
      localStorage.setItem('vision_max_image_dim', num.vDim);
      localStorage.setItem('vision_jpeg_quality', num.vQual);
      localStorage.setItem('gemini_cascade_mode', cascadeMode);
      localStorage.setItem('gemini_cascade_models', JSON.stringify(cascadeModels));
    }

    function _buildSettingsPayload(aiConfig, num, cascadeMode, cascadeModels) {
      const { provider, apiKey, baseUrl, modelName } = aiConfig;
      const settings = {
        max_pages: num.maxPages,
        ocr_pages: num.ocrPages,
        vision_pages: num.vPages,
        vision_max_image_dim: num.vDim,
        vision_jpeg_quality: num.vQual,
        tesseract_cmd: document.getElementById('set-tesseract-cmd')?.value || '',
        ai_provider: provider || 'gemini',
        ai_base_url: baseUrl || '',
        ai_max_chars: num.maxChars,
        gemini_cascade_mode: cascadeMode,
        gemini_cascade_models: cascadeModels,
        watchfolder_enabled: document.getElementById('set-watchfolder-enabled')?.checked || false,
        watchfolder_path: document.getElementById('set-watchfolder-path')?.value.trim() || '',
      };

      const accessPwdInput = document.getElementById('set-access-password');
      const accessPwd = accessPwdInput ? accessPwdInput.value.trim() : '';
      if (accessPwd && !accessPwd.startsWith('••')) {
        settings.access_password = accessPwd;
      }

      if (apiKey && !apiKey.startsWith('••') && !apiKey.includes('•')) {
        settings.ai_api_key = apiKey;
      }

      const modelPropMap = { gemini: 'gemini_model', ollama: 'ollama_model', lmstudio: 'lmstudio_model' };
      const targetProp = modelPropMap[provider];
      if (targetProp) {
        settings[targetProp] = modelName;
      }

      return settings;
    }

    function saveSettings() {
      const provider = document.getElementById('set-ai-provider').value;
      const keyEl = document.getElementById('set-api-key');
      const apiKey = keyEl ? keyEl.value.trim() : '';
      const keyPlaceholder = keyEl ? (keyEl.placeholder || '') : '';
      const isPlaceholderMasked = keyPlaceholder.includes('•');
      const baseUrl = document.getElementById('set-ai-base-url').value;
      const modelName = document.getElementById('set-ai-model-name').value;
      const num = _collectNumericSettings();
      const geminiCascadeMode = document.getElementById('set-gemini-cascade-mode') ? document.getElementById('set-gemini-cascade-mode').checked : true;
      const cascadeModels = getCascadeSlots();

      const aiConfig = { provider, apiKey, isPlaceholderMasked, baseUrl, modelName };
      _persistSettingsLocally(aiConfig, num, geminiCascadeMode, cascadeModels);
      const settings = _buildSettingsPayload(aiConfig, num, geminiCascadeMode, cascadeModels);

      const saveBtn = document.getElementById('btn-save-settings');
      const originalHtml = saveBtn ? saveBtn.innerHTML : '';
      if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Kaydediliyor...</span>';
        saveBtn.disabled = true;
      }

      apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
        .then(res => {
          if (res?.ok) {
            _handleSettingsSaveSuccess(settings, saveBtn, originalHtml);
          } else {
            if (saveBtn) {
              saveBtn.innerHTML = originalHtml;
              saveBtn.disabled = false;
            }
            showToast('Ayarlar kaydedilirken hata oluştu.', 'error');
          }
        })
        .catch(_err => {
          if (saveBtn) {
            saveBtn.innerHTML = originalHtml;
            saveBtn.disabled = false;
          }
          showToast('Bağlantı hatası.', 'error');
        });
    }

    function switchSettingsTab(tabName) {
      const tabBtns = document.querySelectorAll('.settings-tab-btn');
      const tabPanes = document.querySelectorAll('.settings-tab-pane');
      tabBtns.forEach(btn => btn.classList.remove('active'));
      tabPanes.forEach(pane => pane.classList.remove('active'));

      const activeBtn = document.getElementById(`tab-btn-${tabName}`);
      const activePane = document.getElementById(`tab-pane-${tabName}`);
      if (activeBtn) activeBtn.classList.add('active');
      if (activePane) {
        activePane.getBoundingClientRect(); // Clean reflow for restartable spring slide
        activePane.classList.add('active');
      }

      const settingsBody = document.querySelector('#settings-modal .settings-body');
      if (settingsBody) {
        settingsBody.scrollTop = 0;
      }
    }
    window.switchSettingsTab = switchSettingsTab;

    function toggleAccessPasswordVisibility() {
      const input = document.getElementById('set-access-password');
      const icon = document.getElementById('btn-toggle-pwd-icon');
      if (!input) return;
      if (input.type === 'password') {
        input.type = 'text';
        if (icon) {
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        }
      } else {
        input.type = 'password';
        if (icon) {
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }
    }
    window.toggleAccessPasswordVisibility = toggleAccessPasswordVisibility;

    async function saveAccessPasswordDirect() {
      const input = document.getElementById('set-access-password');
      if (!input) return;
      const pwd = input.value.trim();
      if (!pwd) {
        showToast('Lütfen önce bir şifre girin.', 'warning');
        input.focus();
        return;
      }
      if (pwd.startsWith('••')) {
        showToast('Mevcut şifreniz zaten aktif.', 'info');
        return;
      }
      const saveBtn = document.getElementById('btn-save-access-pwd');
      const origHtml = saveBtn ? saveBtn.innerHTML : '';
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Kaydediliyor...</span>';
      }
      try {
        const res = await apiFetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_password: pwd })
        });
        if (res?.ok) {
          const pwdBadge = document.getElementById('sec-pwd-status-badge');
          if (pwdBadge) {
            pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
            pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
            pwdBadge.style.color = '#5f7a4f';
          }
          input.value = '';
          input.placeholder = '•••••••• (Şifre Belirlenmiş)';
          const removeBtn = document.getElementById('btn-remove-access-pwd');
          if (removeBtn) removeBtn.style.display = 'inline-flex';
          showToast('Erişim şifresi başarıyla kaydedildi ve aktif edildi!', 'success');
        } else {
          showToast('Şifre kaydedilirken hata oluştu.', 'error');
        }
      } catch (e) {
        console.error('saveAccessPasswordDirect error:', e);
        showToast('Bağlantı hatası oluştu.', 'error');
      } finally {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerHTML = origHtml;
        }
      }
    }
    window.saveAccessPasswordDirect = saveAccessPasswordDirect;

    async function removeAccessPassword() {
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Erişim şifresini kaldırmak istediğinizden emin misiniz?\n(Uzaktan telefon bağlantısı için şifre gereklidir)', 'Şifreyi Kaldır', 'Kaldır', true) : Promise.resolve(confirm('Erişim şifresini kaldırmak istediğinizden emin misiniz?')));
      if (!ok) {
        return;
      }
      try {
        const res = await apiFetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_password: '__REMOVE__' })
        });
        if (res?.ok) {
          const pwdBadge = document.getElementById('sec-pwd-status-badge');
          if (pwdBadge) {
            pwdBadge.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#b8862f;"></i> Şifre Belirlenmemiş';
            pwdBadge.style.background = 'rgba(184,134,47, 0.12)';
            pwdBadge.style.color = '#b8862f';
          }
          const pwdInput = document.getElementById('set-access-password');
          if (pwdInput) {
            pwdInput.value = '';
            pwdInput.placeholder = 'Erişim şifresi belirleyin...';
          }
          const removePwdBtn = document.getElementById('btn-remove-access-pwd');
          if (removePwdBtn) removePwdBtn.style.display = 'none';
          showToast('Erişim şifresi kaldırıldı.', 'success');
        } else {
          showToast('Şifre kaldırılırken hata oluştu.', 'error');
        }
      } catch (err) {
        console.error('removeAccessPassword error:', err);
        showToast('Bağlantı hatası.', 'error');
      }
    }
    window.removeAccessPassword = removeAccessPassword;

    function copyPhoneConnectionUrl() {
      const codeEl = document.getElementById('phone-connection-url-display');
      if (!codeEl) return;
      const url = codeEl.textContent.trim();
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('Bağlantı adresi kopyalandı: ' + url, 'success');
        }).catch(() => {
          fallbackCopyUrl(url);
        });
      } else {
        fallbackCopyUrl(url);
      }
    }

    function copyOpdsConnectionUrl() {
      const codeEl = document.getElementById('opds-connection-url-display');
      if (!codeEl) return;
      const url = codeEl.textContent.trim();
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('OPDS katalog adresi kopyalandı: ' + url, 'success');
        }).catch(() => {
          fallbackCopyUrl(url);
        });
      } else {
        fallbackCopyUrl(url);
      }
    }
    window.copyOpdsConnectionUrl = copyOpdsConnectionUrl;
    function fallbackCopyUrl(url) {
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url)
          .then(() => showToast('Bağlantı adresi kopyalandı: ' + url, 'success'))
          .catch(() => showToast('Adres: ' + url, 'info'));
        return;
      }
      showToast('Bağlantı adresi: ' + url, 'info');
    }
    window.copyPhoneConnectionUrl = copyPhoneConnectionUrl;



    function closeSettings(e) { if (e.target === document.getElementById('settings-modal')) closeSettingsDirect(); }
    function closeSettingsDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('settings-modal');
      } else {
        const modal = document.getElementById('settings-modal');
        if (modal) modal.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    }

    function closeColModal(e) { if (e.target === document.getElementById('col-modal')) closeColModalDirect(); }
    function closeColModalDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('col-modal');
      } else {
        const modal = document.getElementById('col-modal');
        if (modal) modal.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    }

    function toggleEditMode(hash) {
      const form = document.getElementById(`edit-form-${hash}`);
      form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }

    function saveBookEdit(hash) {
      const data = {
        kitap_adi: document.getElementById(`edit-title-${hash}`).value,
        yazar: document.getElementById(`edit-author-${hash}`).value,
        ozet: document.getElementById(`edit-summary-${hash}`).value
      };
      apiFetch(`/api/books/${hash}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
        .then(r => r ? r.json() : null)
        .then(() => {
          showToast('Kitap bilgileri güncellendi.', 'success');
          closeModalDirect();
          if (typeof loadBooksFromAPI === 'function') {
            return loadBooksFromAPI();
          }
          return null;
        })
        .catch(err => {
          console.error("saveBookEdit error:", err);
          showToast('Kitap güncellenirken hata oluştu.', 'error');
        });
    }

    function toggleAssistant() {
      const panel = document.getElementById('chat-panel');
      if (!panel) return;
      if (panel.classList.contains('active')) {
        panel.classList.add('closing');
        panel.classList.remove('active');
        setTimeout(() => {
          panel.classList.remove('closing');
        }, 150);
      } else {
        panel.classList.remove('closing');
        panel.classList.add('active');
        // Mutual Exclusion: Close Process Center
        const ops = document.getElementById('ops-center');
        if (ops) ops.classList.remove('active');

        // Auto Focus: Focus on input when panel opens
        const input = document.getElementById('chat-input');
        if (input) setTimeout(() => input.focus(), 280);
      }
    }

    function toggleOps() {
      const ops = document.getElementById('ops-center');
      const isActive = ops.classList.toggle('active');
      if (isActive) {
        // Mutual Exclusion: Close Assistant Panel
        const chat = document.getElementById('chat-panel');
        if (chat) chat.classList.remove('active');
        if (typeof fetchTasksFromAPI === 'function') {
          void fetchTasksFromAPI();
        }
      }
    }

    function toggleArchive() {
      openLogsModal();
    }


    // --- STATS DASHBOARD & CHARTS ---
    // â•â•â•â•â•â•â•â•â•â• STATS DASHBOARD â•â•â•â•â•â•â•â•â•â•


    async function loadStats() {
      try {
        const res = await apiFetch('/api/stats');
        const data = await res.json();
        renderStatCards(data.general);
        renderDonutChart(data.categories);
        renderBarChart(data.monthly);
      } catch {
        // UI fallback when statistics endpoint is unreachable
      }
    }

    function renderStatCards(g) {
      const cards = [
        { value: g.total_books, label: 'Toplam Kitap', icon: 'fa-book' },
        { value: g.unique_authors, label: 'Farklı Yazar', icon: 'fa-pen-nib' },
        { value: g.unique_categories, label: 'Kategori', icon: 'fa-layer-group' },
        { value: g.total_favorites, label: 'Favori', icon: 'fa-heart' },
      ];
      document.getElementById('stats-cards').innerHTML = cards.map(c => `
    <div class="stat-card">
      <div class="stat-card-value">${c.value}</div>
      <div class="stat-card-label"><i class="fas ${c.icon}" style="margin-right:4px;color:var(--accent)"></i> ${c.label}</div>
    </div>
  `).join('');
    }

    function renderDonutChart(categories) {
      if (!categories || categories.length === 0) {
        document.getElementById('donut-chart').innerHTML = '<div style="color:var(--muted);font-size:0.8rem;">Veri yok</div>';
        return;
      }
      const total = categories.reduce((s, c) => s + c.count, 0);
      const top = categories.slice(0, 8);
      const otherCount = categories.slice(8).reduce((s, c) => s + c.count, 0);
      if (otherCount > 0) top.push({ name: 'Diğer', count: otherCount });

      const size = 160, cx = 80, cy = 80, r = 60, circumference = 2 * Math.PI * r;
      let offset = 0;
      let paths = '';
      top.forEach((c, i) => {
        const pct = c.count / total;
        const dashLen = pct * circumference;
        const color = DONUT_COLORS[i % DONUT_COLORS.length];
        paths += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="24"
      stroke-dasharray="${dashLen} ${circumference - dashLen}" stroke-dashoffset="${-offset}"
      style="transition: stroke-dashoffset 0.6s"/>`;
        offset += dashLen;
      });

      const legend = top.map((c, i) => `
    <div class="donut-legend-item">
      <span class="donut-legend-dot" style="background:${DONUT_COLORS[i % DONUT_COLORS.length]}"></span>
      <span>${esc(c.name)}</span>
      <span class="donut-legend-count">${c.count}</span>
    </div>
  `).join('');

      document.getElementById('donut-chart').innerHTML = `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform:rotate(-90deg)">
      ${paths}
    </svg>
    <div class="donut-legend">${legend}</div>
  `;
    }

    function renderBarChart(monthly) {
      if (!monthly || monthly.length === 0) {
        document.getElementById('bar-chart').innerHTML = '<div style="color:var(--muted);font-size:0.8rem;">Henüz veri yok</div>';
        return;
      }
      const maxVal = Math.max(...monthly.map(m => m.count), 1);
      const months = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
      document.getElementById('bar-chart').innerHTML = monthly.map(m => {
        const pct = (m.count / maxVal) * 100;
        const [, mo] = m.month.split('-');
        const label = months[Number.parseInt(mo, 10) - 1] || m.month;
        return `
      <div class="bar-col">
        <span class="bar-value">${m.count}</span>
        <div class="bar-fill" style="height:${Math.max(pct, 4)}%"></div>
        <span class="bar-label">${label}</span>
      </div>
    `;
      }).join('');
    }

    // â•â•â•â•â•â•â•â•â•â• DRAG & DROP SORT â•â•â•â•â•â•â•â•â•â•




```


## DOSYA 6.6: static/js/ui_logs.js (İşlem Merkezi & Canlı Log Akışı Dialog Rolleri)

**Dosya Yolu:** `static/js/ui_logs.js`

```javascript
/* ═══════════ ui_logs.js — Live Log Monitoring & Diagnostic Console ═══════════ */
    function openLogsModal() {
      const modal = document.getElementById('logs-modal');
      if (!modal) return;
      window.unreadLogErrors = 0;
      updateHeaderLogsBadge();

      if ((window.cachedLogs || []).length === 0) {
        fetchAndRenderLogs().catch(() => {});
      } else {
        updateCategoryCounters();
        renderLogsModalBody();
      }

      modal.classList.remove('closing');
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      if (typeof activateModalFocus === 'function') activateModalFocus(modal);

      // Setup smart scroll detection on logs container
      const body = document.getElementById('logs-body');
      if (body && !body._scrollHandlerBound) {
        body._scrollHandlerBound = true;
        body.addEventListener('scroll', () => {
          const atBottom = (body.scrollHeight - body.scrollTop - body.clientHeight) < 40;
          if (!atBottom && window.isLogAutoScroll) {
            window.isLogAutoScroll = false;
            const chk = document.getElementById('logs-autoscroll-check');
            if (chk) chk.checked = false;
            const banner = document.getElementById('logs-paused-banner');
            if (banner) {
              banner.innerHTML = '<i class="fas fa-arrow-up"></i> Otomatik Kaydırma Duraklatıldı';
              banner.style.display = 'inline-flex';
            }
          } else if (atBottom && !window.isLogAutoScroll && !window.isLogLivePaused) {
            window.isLogAutoScroll = true;
            const chk = document.getElementById('logs-autoscroll-check');
            if (chk) chk.checked = true;
            const banner = document.getElementById('logs-paused-banner');
            if (banner) banner.style.display = 'none';
          }
        });
      }
    }

    function closeLogsModal(e) {
      if (e.target === document.getElementById('logs-modal')) closeLogsModalDirect();
    }

    function closeLogsModalDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('logs-modal', () => {
          updateHeaderLogsBadge();
        });
      } else {
        const modal = document.getElementById('logs-modal');
        if (modal) modal.classList.remove('open');
        document.body.classList.remove('modal-open');
        updateHeaderLogsBadge();
      }
    }

    function setLogCategory(cat, btn) {
      window.currentLogCategory = cat;
      document.querySelectorAll('.logs-filter-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderLogsModalBody();
    }

    function setLogLevel(lvl, btn) {
      window.currentLogLevel = lvl;
      document.querySelectorAll('.logs-level-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderLogsModalBody();
    }

    let _searchDebounce = null;
    function handleLogSearchInput(val) {
      window.currentLogSearch = String(val || '').trim().toLowerCase();
      const clearBtn = document.getElementById('logs-search-clear');
      if (clearBtn) clearBtn.style.display = window.currentLogSearch ? 'block' : 'none';

      clearTimeout(_searchDebounce);
      _searchDebounce = setTimeout(() => {
        renderLogsModalBody();
      }, 120);
    }

    function clearLogSearch() {
      const input = document.getElementById('logs-search-input');
      if (input) input.value = '';
      handleLogSearchInput('');
    }

    function toggleLogPause() {
      window.isLogLivePaused = !window.isLogLivePaused;
      const btn = document.getElementById('logs-toggle-pause');
      const banner = document.getElementById('logs-paused-banner');

      if (window.isLogLivePaused) {
        if (btn) {
          btn.classList.add('paused');
          btn.innerHTML = '<i class="fas fa-play"></i> <span id="logs-pause-text">Devam Et</span>';
        }
        if (banner) {
          banner.innerHTML = '<i class="fas fa-pause-circle"></i> Canlı Akış Duraklatıldı';
          banner.style.display = 'inline-flex';
        }
      } else {
        if (btn) {
          btn.classList.remove('paused');
          btn.innerHTML = '<i class="fas fa-pause"></i> <span id="logs-pause-text">Duraklat</span>';
        }
        if (banner && window.isLogAutoScroll) banner.style.display = 'none';
        renderLogsModalBody();
      }
    }

    function toggleAutoScroll(checked) {
      window.isLogAutoScroll = !!checked;
      const banner = document.getElementById('logs-paused-banner');
      if (window.isLogAutoScroll) {
        if (banner && !window.isLogLivePaused) banner.style.display = 'none';
        scrollLogsToBottom();
      } else if (banner) {
        banner.innerHTML = '<i class="fas fa-hand"></i> Otomatik Kaydırma Kapalı';
        banner.style.display = 'inline-flex';
      }
    }

    function scrollLogsToTop() {
      const body = document.getElementById('logs-body');
      if (body) body.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function scrollLogsToBottom() {
      const body = document.getElementById('logs-body');
      if (body) body.scrollTo({ top: body.scrollHeight, behavior: 'smooth' });
    }

    async function clearLogsUI() {
      const ok = await (window.showAppConfirm ? window.showAppConfirm("Tüm sistem ve işlem loglarını temizlemek istediğinize emin misiniz?", "Logları Temizle", "Temizle", true) : Promise.resolve(confirm("Tüm logları temizlemek istediğinize emin misiniz?")));
      if (!ok) {
        return;
      }
      try {
        await fetch('/api/logs/clear', { method: 'POST' });
        window.cachedLogs = [];
        window.unreadLogErrors = 0;
        updateHeaderLogsBadge();
        updateCategoryCounters();
        renderLogsModalBody();
        showToast("Loglar başarıyla temizlendi.", "success");
      } catch (err) {
        // Log temizleme işlemi başarısız olduğunda konsola yaz ve kullanıcıyı bilgilendir
        console.error("Log temizleme hatası:", err);
        showToast("Loglar temizlenirken hata oluştu.", "error");
      }
    }

    function exportLogs(format) {
      window.location.href = `/api/logs/export?format=${encodeURIComponent(format)}`;
    }

    function copyLogEntry(logId, btn) {
      const log = cachedLogs.find(l => String(l.id) === String(logId));
      if (!log) return;
      const text = `[${log.iso || new Date(log.ts * 1000).toLocaleString('tr-TR')}] [${log.level || 'INFO'}] [${log.category || 'system'}] ${log.message}` +
        (log.context && Object.keys(log.context).length > 0 ? `\nContext: ${JSON.stringify(log.context, null, 2)}` : '');

      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check" style="color:#9db58a"></i> Kopyalandı!';
        btn.style.color = '#9db58a';
        setTimeout(() => {
          btn.innerHTML = orig;
          btn.style.color = '';
        }, 1500);
      }).catch(() => {});
    }

    function toggleLogContext(logId) {
      const el = document.getElementById(`log-ctx-${logId}`);
      const btn = document.getElementById(`log-btn-ctx-${logId}`);
      if (!el) return;
      const isOpen = el.classList.toggle('open');
      if (btn) {
        btn.innerHTML = isOpen
          ? '<i class="fas fa-chevron-up"></i> Gizle'
          : '<i class="fas fa-code"></i> Detay';
      }
    }

    function updateCategoryCounters() {
      const logs = window.cachedLogs || [];
      const counts = {
        all: logs.length,
        upload: 0,
        ai_analyze: 0,
        ai_raw: 0,
        ai_chat: 0,
        pdf: 0,
        filesystem: 0,
        security: 0,
        system: 0,
      };
      const lvlCounts = { ERROR: 0, WARNING: 0, INFO: 0 };

      for (const l of logs) {
        const c = l?.category;
        if (c && Object.hasOwn(counts, c)) counts[c]++;
        const lvl = (l?.level || '').toUpperCase();
        if (Object.hasOwn(lvlCounts, lvl)) lvlCounts[lvl]++;
      }

      for (const cat in counts) {
        const el = document.getElementById(`logs-count-${cat}`);
        if (el) el.textContent = counts[cat];
      }

      const errEl = document.getElementById('logs-lvl-count-error');
      if (errEl) errEl.textContent = lvlCounts.ERROR;
      const warnEl = document.getElementById('logs-lvl-count-warning');
      if (warnEl) warnEl.textContent = lvlCounts.WARNING;
      const infoEl = document.getElementById('logs-lvl-count-info');
      if (infoEl) infoEl.textContent = lvlCounts.INFO;
    }

    function updateHeaderLogsBadge() {
      const badge1 = document.getElementById('header-logs-badge');
      const badge2 = document.getElementById('compact-logs-badge');
      const modal = document.getElementById('logs-modal');
      const isOpen = modal?.classList?.contains('open');
      const show = !isOpen && (window.unreadLogErrors || 0) > 0;

      if (badge1) badge1.style.display = show ? 'block' : 'none';
      if (badge2) badge2.style.display = show ? 'block' : 'none';
    }

    function highlightLogText(text, query) {
      if (!query) return esc(text);
      const safeText = esc(text);
      const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, String.raw`\$&`);
      const regex = new RegExp(`(${escaped})`, 'gi');
      return safeText.replace(regex, '<mark class="log-match">$1</mark>');
    }

    function renderLogsModalBody() {
      const body = document.getElementById('logs-body');
      if (!body) return;

      const logs = window.cachedLogs || [];
      if (logs.length === 0) {
        body.innerHTML = '<div style="opacity:0.6; font-size:0.8rem; color:#8f8a80; text-align:center; padding:3rem 1rem;"><i class="fas fa-terminal" style="font-size:2rem; margin-bottom:0.75rem; display:block; opacity:0.3;"></i>Henüz kaydedilmiş log bulunmuyor.</div>';
        const counter = document.getElementById('logs-counter-info');
        if (counter) counter.textContent = '0 log';
        return;
      }

      const q = window.currentLogSearch || '';
      const cat = window.currentLogCategory || 'all';
      const lvl = window.currentLogLevel || 'all';

      const filtered = logs.filter(l => {
        if (cat !== 'all' && l.category !== cat) return false;
        if (lvl !== 'all' && (l.level || '').toUpperCase() !== lvl) return false;
        if (q) {
          const msg = (l.message || '').toLowerCase();
          const catName = (l.category || '').toLowerCase();
          const lvlName = (l.level || '').toLowerCase();
          const ctx = JSON.stringify(l.context || {}).toLowerCase();
          if (!msg.includes(q) && !ctx.includes(q) && !catName.includes(q) && !lvlName.includes(q)) return false;
        }
        return true;
      });

      const counter = document.getElementById('logs-counter-info');
      if (counter) {
        counter.textContent = `${filtered.length} / ${logs.length} log`;
      }

      if (filtered.length === 0) {
        body.innerHTML = '<div style="opacity:0.6; font-size:0.8rem; color:#8f8a80; text-align:center; padding:3rem 1rem;"><i class="fas fa-search" style="font-size:2rem; margin-bottom:0.75rem; display:block; opacity:0.3;"></i>Seçilen filtre ve arama kriterlerine uyan log bulunamadı.</div>';
        return;
      }

      body.innerHTML = renderLogCardsHtml(filtered, q);

      if (window.isLogAutoScroll && !window.isLogLivePaused) {
        body.scrollTop = body.scrollHeight;
      }
    }

    function getLogLevelClass(level) {
      if (level === 'ERROR') return 'lvl-error';
      if (level === 'WARNING') return 'lvl-warning';
      if (level === 'DEBUG') return 'lvl-debug';
      return 'lvl-info';
    }

    function _renderSingleLogCard(l, i, q) {
      const logId = l.id || `idx_${i}_${l.ts || ''}`;
      const date = new Date((l.ts || 0) * 1000);
      const timeStr = l.iso ? l.iso.split(' ')[1] : date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const level = (l.level || 'INFO').toUpperCase();
      const lvlClass = getLogLevelClass(level);

      const ctx = l.context || {};
      const ctxKeys = Object.keys(ctx);
      const hasContext = ctxKeys.length > 0;

      let ctxHtml = '';
      if (hasContext) {
        ctxHtml = `<div class="log-context-box" id="log-ctx-${logId}">`;
        for (const k of ctxKeys) {
          const v = ctx[k];
          const valStr = typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v);
          ctxHtml += `<div class="log-ctx-item"><span class="log-ctx-key">${esc(k)}:</span><span class="log-ctx-val">${highlightLogText(valStr, q)}</span></div>`;
        }
        ctxHtml += `</div>`;
      }

      return `
        <div class="log-card ${lvlClass}" id="log-row-${logId}">
          <div class="log-card-header">
            <div class="log-card-meta">
              <span class="log-time" title="${esc(l.iso || '')}">${timeStr}</span>
              <span class="log-level-tag ${level}">${level}</span>
              <span class="log-cat-tag">${esc(l.category || 'system')}</span>
            </div>
            <div class="log-card-tools">
              ${hasContext ? `<button class="log-tool-btn" id="log-btn-ctx-${logId}" onclick="toggleLogContext('${logId}')"><i class="fas fa-code"></i> Detay (${ctxKeys.length})</button>` : ''}
              <button class="log-tool-btn" onclick="copyLogEntry('${logId}', this)" title="Log satırını kopyala"><i class="fas fa-copy"></i> Kopyala</button>
            </div>
          </div>
          <div class="log-message">${highlightLogText(l.message || '', q)}</div>
          ${ctxHtml}
        </div>
      `;
    }

    function renderLogCardsHtml(filtered, q) {
      let html = '';
      for (let i = 0; i < filtered.length; i++) {
        html += _renderSingleLogCard(filtered[i], i, q);
      }
      return html;
    }

    async function fetchAndRenderLogs() {
      try {
        const res = await fetch('/api/logs?limit=800');
        const data = await res.json();
        window.cachedLogs = Array.isArray(data.logs) ? data.logs : [];
        updateCategoryCounters();
        renderLogsModalBody();
      } catch {
        // UI fallback when logs endpoint is unreachable
        const body = document.getElementById('logs-body');
        if (body) body.innerHTML = '<div style="opacity:0.7; color:#b0473c; font-size:0.8rem; text-align:center; padding:2rem;"><i class="fas fa-exclamation-triangle"></i> Loglar yüklenirken bir ağ hatası oluştu.</div>';
      }
    }

    function setOpsTab(tab) {
      window.opsActiveTab = tab;
      document.querySelectorAll('.ops-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `ops-tab-${tab}`);
      });
      updateOpsUI(window.lastActiveTasks, window.lastArchivedTasks);
    }
    window.setOpsTab = setOpsTab;

    function openBookFromOps(fileHash) {
      if (!fileHash) return;
      const allB = window.allBooks || [];
      const book = allB.find(b => b.dosya_hash === fileHash || b.hash === fileHash);
      if (book && typeof openModal === 'function') {
        openModal(book);
        const ops = document.getElementById('ops-center');
        if (ops) ops.classList.remove('active');
      } else if (typeof loadBooksFromAPI === 'function') {
        loadBooksFromAPI(1, false).then(() => {
          const b = (window.allBooks || []).find(x => x.dosya_hash === fileHash || x.hash === fileHash);
          if (b && typeof openModal === 'function') {
            openModal(b);
            const ops = document.getElementById('ops-center');
            if (ops) ops.classList.remove('active');
          }
        }).catch(err => console.error("Book open from ops error:", err));
      }
    }
    window.openBookFromOps = openBookFromOps;

    function getTaskStep(pct, msg = '', status = '') {
      if (status === 'success') return 4;
      const m = String(msg || '');
      if (pct >= 90 || m.includes('Veritabanı') || m.includes('kaydedildi')) return 4;
      if (pct >= 70 || m.includes('Kapak') || m.includes('arşivleniyor')) return 3;
      if (pct >= 25 || m.includes('Yapay zeka') || m.includes('GEMINI')) return 2;
      return 1;
    }

    function getTaskPhaseLabel(pct, msg = '', status = '') {
      if (status === 'success') return 'Kütüphaneye Kaydedildi';
      if (status === 'error') return 'İşlem Başarısız';
      const m = String(msg || '');
      if (pct >= 90 || m.includes('Veritabanı')) return '4/4 Veritabanı Kaydı';
      if (pct >= 70 || m.includes('Kapak') || m.includes('arşivleniyor')) return '3/4 Kapak & Görsel';
      if (pct >= 25 || m.includes('Yapay zeka') || m.includes('GEMINI')) return '2/4 Gemini 3.5 AI Analizi';
      return '1/4 Belge Okuma';
    }

    function formatTimeAgo(ts) {
      if (!ts) return '';
      const diff = Math.max(0, Math.floor(Date.now() / 1000 - ts));
      if (diff < 5) return 'az önce';
      if (diff < 60) return `${diff} sn önce`;
      if (diff < 3600) return `${Math.floor(diff / 60)} dk önce`;
      return `${Math.floor(diff / 3600)} sa önce`;
    }

    function formatLogTime(ts) {
      if (!ts) return '';
      const d = new Date(ts * 1000);
      return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    function getOpsStepClass(step, target) {
      if (step > target) return 'done';
      if (step === target) return 'active';
      return '';
    }

    function getOpsStepNum(step, target) {
      return step > target ? '<i class="fas fa-check" style="font-size:0.65em;"></i>' : String(target);
    }

    function renderOpsActiveCard(t, pct, logs) {
      const step = getTaskStep(pct, t.log_message, t.status);
      const phaseLabel = getTaskPhaseLabel(pct, t.log_message, t.status);

      let logDetailsHtml = '';
      if (logs.length > 0) {
        const streamLines = logs.slice(-6).map(l => `
          <div class="ops-stream-line ${l.state || l.status || ''}">
            <span class="line-time">${formatLogTime(l.ts)}</span>
            <span class="line-dot"></span>
            <span class="line-msg">${esc(l.message || '')}</span>
          </div>
        `).join('');
        logDetailsHtml = `
          <details class="ops-log-details" ${logs.length <= 4 ? 'open' : ''}>
            <summary><i class="fas fa-terminal"></i> Ayrıntılı Loglar (${logs.length})</summary>
            <div class="ops-log-stream">${streamLines}</div>
          </details>
        `;
      }

      return `
        <div class="ops-task-card is-active" id="task-${t.id}">
          <div class="ops-card-header">
            <div class="ops-file-badge"><i class="fas fa-file-pdf"></i></div>
            <div class="ops-file-info">
              <div class="ops-file-title" title="${esc(t.filename)}">${esc(t.filename)}</div>
              <div class="ops-file-meta">
                <span class="ops-phase-tag"><i class="fas fa-spinner fa-spin"></i> ${phaseLabel}</span>
                <span class="ops-time-ago">${formatTimeAgo(t.last_update)}</span>
              </div>
            </div>
            <div class="ops-card-pct">%${pct}</div>
          </div>
          <div class="ops-stepper">
            <div class="ops-step ${getOpsStepClass(step, 1)}">
              <span class="step-num">${getOpsStepNum(step, 1)}</span>
              <span class="step-lbl">Okuma</span>
            </div>
            <div class="ops-step-line ${step > 1 ? 'done' : ''}"></div>
            <div class="ops-step ${getOpsStepClass(step, 2)}">
              <span class="step-num">${getOpsStepNum(step, 2)}</span>
              <span class="step-lbl">Gemini AI</span>
            </div>
            <div class="ops-step-line ${step > 2 ? 'done' : ''}"></div>
            <div class="ops-step ${getOpsStepClass(step, 3)}">
              <span class="step-num">${getOpsStepNum(step, 3)}</span>
              <span class="step-lbl">Kapak</span>
            </div>
            <div class="ops-step-line ${step > 3 ? 'done' : ''}"></div>
            <div class="ops-step ${getOpsStepClass(step, 4)}">
              <span class="step-num">${getOpsStepNum(step, 4)}</span>
              <span class="step-lbl">Kayıt</span>
            </div>
          </div>
          <div class="ops-progress-track">
            <div class="ops-progress-bar animated" style="width: ${pct}%"></div>
          </div>
          <div class="ops-status-line">
            <span class="ops-pulse-dot"></span>
            <span class="ops-status-text" title="${esc(t.log_message)}">${esc(t.log_message || 'İşlem yürütülüyor...')}</span>
            <span class="ops-terminal-cursor">_</span>
          </div>
          ${logDetailsHtml}
        </div>
      `;
    }

    function renderOpsSuccessCard(t, title, author, category, bookHash) {
      return `
        <div class="ops-task-card is-success" id="task-${t.id}">
          <div class="ops-card-header">
            <div class="ops-file-badge success"><i class="fas fa-book"></i></div>
            <div class="ops-file-info">
              <div class="ops-file-title success" title="${esc(title)}">${esc(title)}</div>
              <div class="ops-file-meta">
                ${author ? `<span class="ops-author-tag"><i class="fas fa-pen-nib"></i> ${esc(author)}</span>` : ''}
                ${category ? `<span class="ops-cat-tag"><i class="fas fa-folder"></i> ${esc(category)}</span>` : ''}
              </div>
            </div>
            <div class="ops-status-pill success"><i class="fas fa-check-circle"></i> Eklendi</div>
          </div>
          <div class="ops-result-row">
            <span class="ops-result-filename" title="${esc(t.filename)}"><i class="fas fa-file-alt"></i> ${esc(t.filename)}</span>
            ${bookHash ? `
              <button class="ops-btn-action" onclick="openBookFromOps('${bookHash}')">
                <i class="fas fa-eye"></i> Kitabı Aç
              </button>
            ` : ''}
          </div>
        </div>
      `;
    }

    function renderOpsErrorCard(t) {
      return `
        <div class="ops-task-card is-error" id="task-${t.id}">
          <div class="ops-card-header">
            <div class="ops-file-badge error"><i class="fas fa-exclamation-triangle"></i></div>
            <div class="ops-file-info">
              <div class="ops-file-title error">${esc(t.filename)}</div>
              <div class="ops-file-meta">
                <span class="ops-status-pill error"><i class="fas fa-times-circle"></i> Hata Oluştu</span>
                <span class="ops-time-ago">${formatTimeAgo(t.last_update)}</span>
              </div>
            </div>
          </div>
          <div class="ops-error-box">${esc(t.log_message || 'İşlem sırasında bir hata oluştu.')}</div>
        </div>
      `;
    }

    function renderOpsEmptyState(tab) {
      if (tab === 'active') {
        return `
          <div style="opacity:0.65; font-size:0.75rem; text-align:center; padding:3rem 1rem;">
            <i class="fas fa-check-circle" style="font-size:1.8rem; color:#5f7a4f; margin-bottom:0.6rem; display:block; opacity:0.8;"></i>
            Devam eden aktif bir işlem yok.<br>
            <span style="font-size:0.68rem; color:#6f6a60;">Tamamlanan işlemleri görmek için "Tamamlanan" sekmesine tıklayabilirsiniz.</span>
          </div>
        `;
      }
      if (tab === 'completed') {
        return `
          <div style="opacity:0.65; font-size:0.75rem; text-align:center; padding:3rem 1rem;">
            <i class="fas fa-history" style="font-size:1.8rem; color:#6f6a60; margin-bottom:0.6rem; display:block; opacity:0.6;"></i>
            Henüz tamamlanmış işlem kaydı yok.
          </div>
        `;
      }
      return `
        <div class="ops-empty-state">
          <div class="ops-empty-radar">
            <div class="ops-radar-sweep"></div>
            <i class="fas fa-microchip ops-empty-icon"></i>
          </div>
          <div class="ops-empty-title">Sistem Hazır ve Dinlemede</div>
          <div class="ops-empty-desc">
            Yapay zeka kuyruğunda bekleyen işlem yok. Arka plan servisleri canlı ve yanıt vermeye hazır.
          </div>
          <div class="ops-empty-specs">
            <div class="spec-item"><i class="fas fa-brain" style="color:#9a8d77;"></i> AI Motoru: <strong>Gemini 3.5 Flash-Lite</strong></div>
            <div class="spec-item"><i class="fas fa-wifi" style="color:#5f7a4f;"></i> WebSocket: <strong>Canlı Bağlantı Aktif</strong></div>
            <div class="spec-item"><i class="fas fa-database" style="color:#b8862f;"></i> Kütüphane: <strong>${(window.allBooks?.length || 0)} Kayıtlı Eser</strong></div>
          </div>
          <div class="ops-empty-actions">
            <button class="ops-quick-action" onclick="document.getElementById('file-input')?.click();">
              <i class="fas fa-plus"></i> Kitap Yükle
            </button>
            <button class="ops-quick-action" onclick="if(typeof syncLibrary==='function') syncLibrary();">
              <i class="fas fa-sync-alt"></i> Klasörleri Tara
            </button>
          </div>
        </div>
      `;
    }

    function handleCompletedTaskRefreshes(completedEntries) {
      completedEntries.forEach(t => {
        if (t.status === 'success' && !window.completedTasks.has(t.id)) {
          window.completedTasks.add(t.id);
          if (typeof loadBooksFromAPI === 'function') {
            loadBooksFromAPI(1, false).catch(err => console.error("Book reload failed:", err));
          }
          if (typeof addChatMessage === 'function') {
            addChatMessage('ai', `${t.filename} başarıyla analiz edildi ve kütüphanenize eklendi.`);
          }
        }
      });
    }

    function _renderActiveOpsBadges(activeCount) {
      const activePill = document.getElementById('ops-active-pill');
      const livePulse = document.getElementById('ops-live-pulse');
      const toggleBtn = document.getElementById('ops-toggle');
      const floatingBadge = document.getElementById('ops-badge');

      if (activePill) {
        activePill.textContent = `${activeCount} Aktif`;
        activePill.className = 'ops-count-pill is-active';
      }
      if (livePulse) livePulse.className = 'ops-live-pulse pulse-active';
      if (floatingBadge) {
        floatingBadge.textContent = activeCount;
        floatingBadge.style.display = 'block';
      }
      if (toggleBtn) {
        toggleBtn.classList.add('is-processing');
        toggleBtn.title = `${activeCount} kitap arka planda işleniyor... (Görüntülemek için tıklayın)`;
      }
    }

    function _renderIdleOpsBadges() {
      const activePill = document.getElementById('ops-active-pill');
      const livePulse = document.getElementById('ops-live-pulse');
      const toggleBtn = document.getElementById('ops-toggle');
      const floatingBadge = document.getElementById('ops-badge');

      if (activePill) {
        activePill.textContent = 'Hazır';
        activePill.className = 'ops-count-pill';
      }
      if (livePulse) livePulse.className = 'ops-live-pulse pulse-idle';
      if (floatingBadge) floatingBadge.style.display = 'none';
      if (toggleBtn) {
        toggleBtn.classList.remove('is-processing');
        toggleBtn.title = 'İşlem Merkezi';
      }
    }

    function updateOpsBadges(activeCount, completedCount, totalCount) {
      const queueLabel = document.getElementById('ops-queue-label');
      const badgeAll = document.getElementById('ops-tab-badge-all');
      const badgeActive = document.getElementById('ops-tab-badge-active');
      const badgeCompleted = document.getElementById('ops-tab-badge-completed');

      if (badgeAll) badgeAll.textContent = totalCount;
      if (badgeActive) badgeActive.textContent = activeCount;
      if (badgeCompleted) badgeCompleted.textContent = completedCount;

      if (queueLabel) {
        queueLabel.textContent = activeCount > 0 ? `${activeCount} Sırada` : 'Boşta';
      }

      if (activeCount > 0) {
        _renderActiveOpsBadges(activeCount);
      } else {
        _renderIdleOpsBadges();
      }
    }

    function renderOpsCardsHtml(listToRender, currentTab, activeCount, completedCount) {
      let html = '';
      let hasActiveSection = false;
      let hasCompletedSection = false;

      listToRender.forEach(t => {
        const isSuccess = t.status === 'success';
        const isError = t.status === 'error';
        const isActive = !isSuccess && !isError;
        const pct = Math.min(100, Math.max(isActive ? 5 : 0, t.percentage || 0));
        const logs = Array.isArray(t.logs) ? t.logs : [];
        const taskData = t.task_data || {};
        const title = taskData.kitap_adi || t.filename || 'Yeni Kitap';
        const author = taskData.yazar || '';
        const category = taskData.kategori || '';
        const bookHash = taskData.dosya_hash || '';

        // Add section headers in 'all' view
        if (currentTab === 'all') {
          if (isActive && !hasActiveSection) {
            html += `<div class="ops-section-divider"><i class="fas fa-bolt" style="color:#b8862f;"></i> Devam Eden İşlemler (${activeCount})</div>`;
            hasActiveSection = true;
          } else if (!isActive && !hasCompletedSection) {
            html += `<div class="ops-section-divider" style="margin-top:0.8rem;"><i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Son İşlemler (${completedCount})</div>`;
            hasCompletedSection = true;
          }
        }

        if (isActive) {
          html += renderOpsActiveCard(t, pct, logs);
        } else if (isSuccess) {
          html += renderOpsSuccessCard(t, title, author, category, bookHash);
        } else if (isError) {
          html += renderOpsErrorCard(t);
        }
      });
      return html;
    }

    function updateOpsUI(activeTasks, archivedTasks = {}) {
      const body = document.getElementById('ops-body');
      if (!body) return;

      const activeEntries = Object.entries(activeTasks || {})
        .filter(([_, t]) => t && t.status !== 'success' && t.status !== 'error')
        .map(([id, t]) => ({ id, ...t, isActive: true }))
        .sort((a, b) => (b.last_update || 0) - (a.last_update || 0));

      const archivedRaw = [
        ...Object.entries(activeTasks || {}).filter(([_, t]) => t && (t.status === 'success' || t.status === 'error')),
        ...Object.entries(archivedTasks || {})
      ].map(([id, t]) => ({ id, ...t, isActive: false }))
       .sort((a, b) => (b.last_update || b.archived_at || 0) - (a.last_update || a.archived_at || 0));

      const completedSeen = new Set();
      const completedEntries = [];
      for (const t of archivedRaw) {
        if (!completedSeen.has(t.id)) {
          completedSeen.add(t.id);
          completedEntries.push(t);
        }
      }

      handleCompletedTaskRefreshes(completedEntries);

      // Update Header Badges & Indicators
      const activeCount = activeEntries.length;
      const completedCount = completedEntries.length;
      const totalCount = activeCount + completedCount;

      updateOpsBadges(activeCount, completedCount, totalCount);

      // Filter based on active tab
      const currentTab = window.opsActiveTab || 'all';
      let listToRender = [];
      if (currentTab === 'active') {
        listToRender = activeEntries;
      } else if (currentTab === 'completed') {
        listToRender = completedEntries;
      } else {
        listToRender = [...activeEntries, ...completedEntries];
      }

      // Empty State Handling
      if (listToRender.length === 0) {
        body.innerHTML = renderOpsEmptyState(currentTab);
        return;
      }

      body.innerHTML = renderOpsCardsHtml(listToRender, currentTab, activeCount, completedCount);
    }

    function excelSafe(str) {
      const value = String(str || '');
      return /^[=+\-@]/.test(value) ? `'${value}` : value;
    }

    function updateChatCounter() {
      const input = document.getElementById('chat-input');
      const countSpan = document.getElementById('chat-char-count');
      const circle = document.getElementById('chat-progress-fill');
      if (!input || !countSpan || !circle) return;

      const len = input.value.length;
      const remaining = 1000 - len;
      countSpan.textContent = remaining;

      // SVG Circle Animation: circumference = 2 * pi * r = 2 * 3.14 * 10 = ~62.8
      const circumference = 62.8;
      const offset = circumference - (len / 1000) * circumference;
      circle.style.strokeDashoffset = offset;

      // Change color if getting close
      if (remaining < 100) {
        circle.style.stroke = 'var(--accent)';
        countSpan.style.color = 'var(--accent)';
      } else {
        circle.style.stroke = 'var(--accent)'; // Keep custom primary or change to theme
        countSpan.style.color = 'var(--muted)';
      }
    }

    function exportToExcel() {
      if (!allBooks || allBooks.length === 0) {
        showToast("Dışa aktarılacak kitap bulunamadı.", "warning");
        return;
      }

      // Format data for Excel
      const data = allBooks.map(b => ({
        "Kitap Adı": excelSafe(b.title || ""),
        "Yazar": excelSafe(b.author || ""),
        "Kategori": excelSafe(b.category || ""),
        "Alt Kategori": excelSafe(b.subcat || ""),
        "Özet": excelSafe(b.summary || ""),
        "Anahtar Kelimeler": excelSafe(b.keywords || ""),
        "Dosya Adı": excelSafe(b.file || ""),
        "Favori": b.is_favorite ? "Evet" : "Hayır",
        "Kapak Var": b.has_cover ? "Evet" : "Hayır"
      }));

      // Create Excel workbook
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();

      // Set column widths for a cleaner look
      const wscols = [
        { wch: 35 }, { wch: 25 }, { wch: 20 }, { wch: 20 }, { wch: 80 }, { wch: 30 }, { wch: 30 }, { wch: 10 }, { wch: 10 }
      ];
      ws['!cols'] = wscols;

      XLSX.utils.book_append_sheet(wb, ws, "Kütüphane Kayıtları");

      // Dosyayı indir
      XLSX.writeFile(wb, "Dijital_Kutuphane_Yedegi.xlsx");
    }

```


## DOSYA 7: static/manifest.json (PWA Manifest, Sıcak Kâğıt & Kehribar Renk Uyumu)

**Dosya Yolu:** `static/manifest.json`

```json
{
  "id": "/?source=pwa",
  "name": "Dijital Kütüphane",
  "short_name": "Kütüphane",
  "description": "Kişisel Dijital PDF ve EPUB Kütüphanesi",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#f4f1eb",
  "theme_color": "#b8862f",
  "categories": ["books", "productivity", "utilities"],
  "icons": [
    {
      "src": "/static/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}
```
