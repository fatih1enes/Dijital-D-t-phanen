# Dijital Kütüphanem — Hareket Dili & Etkileşim Mimarisi ("Kâğıt ve Mürekkep")

Bu belge, **Dijital Kütüphanem** arayüzündeki hareket dilini, CSS/JS altyapısını, canlı İşlem Merkezi (`#ops-center`) uzlaştırmasını ve erişilebilirlik garantilerini özetler.

---

## 1. Tasarım Dili: "Kâğıt ve Mürekkep" (Paper & Ink)

Tüm geçişler üç temel ilkeye dayanır; süsleme değil, okunabilirlik ve mekânsal süreklilik hedeflenir:

1. **Yerleşme (Settle):** Kartlar, paneller ve modallar sayfaya oturan bir kâğıt yaprağı gibi kısa ve ağırlıklı biçimde yerleşir (`--ease-out` / `--ease-editorial`). Yaylanma (`--ease-spring`) yalnızca doğrudan fiziksel tepki gerektiren öğelerde kullanılır.
2. **Köken (Origin):** Açılır menüler (`--modal-origin-x/y`, `origin`), kapsül çekmeceler (`#ops-toggle` ↔ `#ops-center`, `#chat-panel`) ve okuyucu morfları tetiklendikleri noktadan açılır ve geldikleri yere kapanır.
3. **Sessizlik (Stillness):** Okuma sırasında dikkat dağıtan sürekli hareketler kapatılır; okuma yüzeyi sakin ve kararlıdır.

### Kompozit & Performans Kuralı
- CSS geçişleri ve Web Animations yalnızca GPU kompozit özellikleriyle sınırlandırılmıştır: **`transform`** ve **`opacity`**.
- İlerleme ve grafik çubukları (`.card-progress-bar`, `.modal-progress-fill`, `.ops-progress-bar`, `.book-card.uploading` ve `renderBarChart`) `width` / `height` yerine `scaleX(...)` / `scaleY(...)` kullanır.
- `box-shadow`, `filter`, `width`, `height`, `top`, `left`, `right`, `bottom`, `margin`, `padding` üzerinde CSS `transition` tanımlanmaz.
- Arka planda sürekli çalışan amaçsız `requestAnimationFrame` veya sonsuz nabız/dönüş döngüleri yoktur.

---

## 2. CSS Katmanları ve Hareket Token'ları

CSS yükleme sırası [`static/css/app.css`](../static/css/app.css) içinde açık katmanlarla tanımlanır:

```css
@layer legacy, tokens, design, motion;
```

- `static/css/style.css` (`legacy`) → `static/css/tokens.css` (`tokens`) → `static/css/design.css` (`design`) → `static/css/motion.css` (`motion`).
- Service Worker (`static/sw.js`) ve HTML sürüm parametreleri `?v=2026111504` olarak güncellenmiştir.

### Easing ve Süre Token'ları ([`static/css/tokens.css`](../static/css/tokens.css))

| Token | Değer | Kullanım Alanı |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | Varsayılan yerleşme ve standart mikro etkileşimler |
| `--ease-editorial` | `cubic-bezier(0.22, 1, 0.36, 1)` | Modal, çekmece ve editoryal düzen yerleşimleri |
| `--ease-morph` | `cubic-bezier(0.32, 0.72, 0, 1)` | Kapak View Transitions ve kapsül ↔ çekmece geçişleri |
| `--ease-spring-gentle` | `cubic-bezier(0.25, 1.25, 0.4, 1)` | Hafif dokunsal kart/buton tepkileri |
| `--ease-out-quart` | `cubic-bezier(0.25, 1, 0.5, 1)` | İkincil yumuşak çıkışlar |
| `--ease-in-out` | `cubic-bezier(0.65, 0, 0.35, 1)` | Çift yönlü büyük yüzey geçişleri |
| `--ease-spring` | `linear(0, 0.402 7.4%, 0.711 15.3%, 0.929 23.7%, 1.008 33.3%, 1.067 41.6%, 1.059 49.2%, 1.015 61.5%, 0.999 74%, 1)` | Doğrudan fiziksel tepki gerektiren oturma efektleri |
| `--t-instant` | `90ms` | Anlık dokunuş / basma tepkisi |
| `--t-micro` | `150ms` | Hover, odak halkası, renk ve sınır değişimleri |
| `--t-exit` | `180ms` | Panel, dropdown ve modal kapanışları |
| `--t-ui` | `280ms` | Dropdown, çekmece, kart, modal açılışları |
| `--t-morph` | `400ms` | Kapak morfları ve View Transitions |
| `--t-page` | `520ms` | Okuyucu / büyük tam ekran yüzey geçişleri |
| `--stagger-step` | `28ms` | Sıralı kart/liste öğeleri arası gecikme adımı |

---

## 3. Ortak JS Hareket Çekirdeği (`static/js/motion.js`)

Framework bağımlılığı olmadan [`static/js/motion.js`](../static/js/motion.js) üzerinden `window.Motion` arayüzü sunulur:

- `Motion.EASE_OUT`, `Motion.EASE_MORPH`, `Motion.EASE_SPRING` — paylaşılan JS eğri sabitleri.
- `Motion.reduced()` *(takma ad: `window.isMotionReduced`)* — `prefers-reduced-motion: reduce` sorgusunu değerlendirir.
- `Motion.enter(el, opts)` — öğeye animasyonlu giriş uygular ve giriş tamamlandığında ya da indirgenmiş harekette odak (`focusEl`) devrini güvenle yapar.
- `Motion.exit(el, opts)` — çıkış sınıfını/geçişini uygulayıp tamamlandığında DOM temizleme geri çağrısını (`afterFn`) çalıştırır.
- `Motion.stagger(elements, opts)` — liste ve ızgara öğelerini sıralı gecikmeyle yerleştirir; büyük kütüphanelerde performansı korumak için **en fazla 12 öğeye** kademeli gecikme uygular, kalanları anında görünür bırakır.
- `Motion.flip(elements, mutateFn, opts)` — FLIP (`First–Last–Invert–Play`) tekniğiyle düzen değişikliklerinde öğelerin `transform` sürekliliğini korur.
- `Motion.glidePill(container, activeEl, opts)` *(takma ad: `window.animateSegmentedPill`)* — `#setView` görünümleri gibi segmentli kontrollerde aktif kapsülü kaydırır.
- `Motion.transition(fn, { name, fromEl, toEl })` — kaynak öğedeki `view-transition-name` niteliğini kaldırıp `document.startViewTransition` içinde `fn()` sonrası hedef öğeye atar ve bitişte temizler. Tarayıcı desteklemiyorsa veya `Motion.reduced()` etkinse `fn()` senkron çalıştırılır ve çözümlenmiş Promise döner.

---

## 4. Yüzey Bazlı Koreografi

### 4.1 Canlı Etkinlik Merkezi (`#ops-toggle` & `#ops-center`)
- **Tek Satır Kapsül (`#ops-toggle`):** Sol alt köşede kompakt biçimde yer alır; mobilde (`@media (max-width: 768px)`) sağ alt köşedeki `#chat-panel:not(.active)` kapsülüyle aynı taban hizasında durur ve `#ops-center` onun hemen üstünde iki kenardan eşit boşlukla (`left: 0.75rem; right: 0.75rem`) açılır.
- **Gerçek Veri Kaynakları:** Yapay durum veya sahte ilerleme üretilmez:
  - `#ops-engine-label` metni mevcut ayar kaynağından (`appSettings` / AI yapılandırması) güncellenir.
  - WebSocket bağlantı göstergesi `setLogsConnectionStatus` ([`static/js/websocket.js`](../static/js/websocket.js)) üzerinden gerçek bağlantı durumunu (`"Canlı"`, `is-ws-reconnecting`) kapsüle yansıtır.
  - Görev kartları backend `update_task_status` / `active_tasks` yayınındaki gerçek alanları (`filename`, `status`, `percentage`, `log_message`, `last_update`, `logs`, `task_data`) işler.
- **Anahtarlı DOM Uzlaştırması ([`static/js/ui_logs.js`](../static/js/ui_logs.js)):** `data-task-id` üzerinden yalnızca değişen kart düğümleri güncellenir; böylece açık durumdaki `<details.ops-log-details>` günlüğü ve liste kaydırma konumu korunur. Çekmece kapalıyken gelen WS olayları `requestAnimationFrame` ile toplulaştırılır.
- **Yükleme Kartı Morfu ([`static/js/api.js`](../static/js/api.js), [`static/js/ui_core.js`](../static/js/ui_core.js)):** Yükleme sırasındaki `.book-card.uploading` yer tutucusu `scaleX` mürekkep ilerleme çubuğu gösterir; `library_update` ile gerçek kitap verisi geldiğinde önceki kart konumu üzerinden yeni kitap kartına morflanır.

### 4.2 Kitap Kartı → Detay Modalı → Okuyucu Sürekliliği
- **Kart → Modal:** `openModal` tetikleyici kartın konumundan `--modal-origin-x` / `--modal-origin-y` kökenini hesaplar ve `closeModalDirect` kapanırken görünürdeki `.book-card .card-cover` öğesine `Motion.transition(..., { name: 'book-cover' })` ile geri döner.
- **Modal / Kart / Raf → Okuyucu:** `openBookWithMorph` ve `closeWorkspace` ([`static/js/ui_workspace.js`](../static/js/ui_workspace.js)) `view-transition-name: book-cover` üzerinden kapağı `#workspace-cover-slot` hedefine taşır ve okuyucu kapatıldığında görünür kart kapağına iade eder.
- **Kapalı Okuyucu İzolasyonu:** `#workspace-reader:not(.open)` CSS tarafında `visibility: hidden; pointer-events: none;` ile kapalıyken sayfa altında görünmez ve odak/tıklama almaz.

### 4.3 Okuyucu İçi ve İkincil Yüzeyler
- **Okuyucu Sohbet Çekmecesi (`toggleWorkspaceChatPane`):** `_refitReaderAfterChatToggle` yardımcısı mevcut yakınlaştırma/sığdırma modunu bozmadan yeniden sığdırma yapar ve kaydırma oranını korur; `Escape` tuşu çekmeceyi kapatır.
- **PDF İçi Arama ve Not Modalı:** `togglePdfSearch` / `closePdfSearch` `Escape` ile arama çubuğunu kapatıp odağı `#pdf-search-btn` butonuna döndürür (`stopPropagation()` ile üst okuyucuyu kapatmaz); not ekleme/düzenleme `_presentPdfNoteModal` üzerinden yürür ve `btn-edit-note` dinleyicisi korunur.
- **Kütüphane Asistanı, Ayarlar, Menüler ve Bildirimler:** `#chat-panel` (`toggleAssistant`, `closeChatPanelSmooth`), ayar sekmeleri (`switchSettingsTab`), özel açılır menüler (`openCustomDropdown`/`closeCustomDropdown`), araçlar menüsü (`toggleToolsMenu`/`closeToolsMenu`), Telegram modalı (`ui_telegram.js`), bilgi bildirimleri (`showToast` in `state.js`) ve tema değişimi (`toggleTheme()` in `app.js` — `Motion.transition` + `theme-transitioning` 180ms çapraz geçiş) tek hareket diliyle çalışır.

---

## 5. Bilinçli Olarak Sessiz Bırakılan Yüzeyler

- **`#workspace-reader` Okuma Alanı:** PDF/EPUB sayfa tuvali açıkken dikkat dağıtıcı sürekli animasyonlar çalıştırılmaz.
- **Kitap Kartları (`.book-card`):** Fare işaretçisiyle tetiklenen 3B eğim (pointer tilt) kaldırılarak kâğıt ağırlığı korunmuştur.
- **`#ops-toggle` İşlem Kapsülü:** `.ops-toggle.is-processing` üzerindeki sürekli nabız (`opsPulse`) ve sonsuz dönme (`opsSpin`) animasyonları `animation: none` ile devre dışı bırakılmıştır.

---

## 6. Erişilebilirlik, Odak Yönetimi ve Geri Dönüşler

- **İndirgenmiş Hareket (`prefers-reduced-motion: reduce`):** [`static/css/motion.css`](../static/css/motion.css) içinde tek merkezden yönetilir; tüm giriş/çıkış/yaylanma geçişleri anlık veya kısa opaklık çözünmesine indirgenir ve View Transitions devreden çıkarılır.
- **Modal Odak Tuzağı ve `Escape` Hiyerarşisi ([`static/js/ui_core.js`](../static/js/ui_core.js)):**
  - `_getModalFocusables` yardımcı fonksiyonu `input[type="hidden"]` ve kapak yükleme butonundaki gizli `input[type="file"]` öğelerini odak zincirinden çıkarır; böylece modal açıldığında gizli dosya girişi odaklanmaz.
  - Global `keydown` dinleyicisi açık bir modal/çekmece içindeki bir input odaktayken bile `Escape` ile `handleEscapeKeyPress()` sırasını çalıştırır (`e.defaultPrevented` kontrolüyle iç içe bileşenlerin `Escape` davranışına saygı duyar) ve kapatma sonrası `releaseModalFocus` ile odağı tetikleyici öğeye döndürür.
- **Tarayıcı Geri Dönüşü:** `document.startViewTransition` desteklemeyen ortamlarda `Motion.transition` DOM mutasyonunu doğrudan uygular; tüm timer, gözlemci ve sınıf izleri okuyucu kapanışında (`cleanupCustomPdfViewer`) temizlenir.
