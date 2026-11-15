# Dijital Kütüphanem — Hareket Dili & Etkileşim Mimari Notları

> **İlk İnceleme ve Mimari Doğrulama (Adım 1)**  
> Hareket dili: **"Kâğıt ve Mürekkep"** (`Yerleşme`, `Köken`, `Sessizlik`)

---

## 1. Koddan Doğrulanan Mevcut Durum ve Bulgular

### 1.1 CSS Katmanları ve Token Kullanımı
- **Cascade Layers (`static/css/app.css`)**: `legacy (style.css)` → `tokens (tokens.css)` → `design (design.css)`. Ortak hareket katmanı için 4. katman olan `motion (motion.css)` ekleniyor.
- **`static/css/tokens.css`**: `--ease-out`, `--ease-in-out`, `--ease-morph`, `--ease-spring` (`linear(...)`) ve süre tokenları (`--t-instant`, `--t-micro`, `--t-ui`, `--t-morph`, `--t-page`, `--stagger-step`) mevcut; ancak eski katmanlarda doğrudan `cubic-bezier(0.16, 1, 0.3, 1)` ve tutarsız sabit ms değerleri hâlâ yer alıyor (`style.css:7197-7567`).
- **Çift ve dağınık `@keyframes`**: `style.css` ve `design.css` genelinde dağınık `@keyframes` blokları var (`modalPopIn/Out`, `modalOverlayIn/Out`, `themeIconSpin`, `opsCenterIn`, `dropdownIn` iki dosyada birden tanımlı).
- **Kısıtlı animasyon özellikleri**: Bazı seçicilerde performans/kompozit kuralına aykırı `width`, `flex-basis`, `height`, `box-shadow` veya `filter` transition'ları bulunuyor (`.uploading .progress-bar`, `.card-progress-bar`, `.workspace-chat-pane`, `.modal-overlay`). İlerleme çubukları `scaleX(...)` modeline taşınmalıdır.
- **`prefers-reduced-motion` dağınıklığı**: `tokens.css` ve `design.css` içinde birden çok yerde parça parça ele alınıyor; tüm hareket indirgemesi `static/css/motion.css` altında tek merkezde toplanacaktır.

### 1.2 View Transitions ve Kitap Açma Akışı
- Mevcut View Transitions kullanımı: `static/js/ui_workspace.js` (`openBookWithMorph`, `closeWorkspace`, `view-transition-name: book-cover`), `static/js/app.js` (`toggleTheme`), `static/js/ui_core.js` (`openModal`, `closeModalDirect`).
- **Süreklilik kopukluğu**: Karttaki hızlı "Oku" butonu (`btn-card-quick-read`) ve raf öğeleri (`shelf-item`) doğrudan `openBookWithMorph` çağırırken, kart gövdesine tıklamak önce detay modalını açar. Detay modalından "Kitabı Oku" denildiğinde modalın kapanışını beklemeden tek bir View Transition içinde `.modal-cover-wrap` → `#workspace-cover-slot` morfu ve modal çıkışı senkronize edilir. Modal kapanışı ve okuyucu kapanışı ise kapağı görünürdeki kitap kartına iade eder (`transform-origin` + `view-transition-name`).

### 1.3 Canlı UI / İşlem Merkezi ve Gerçek Backend Görev Şeması
- **WebSocket & Görev Kaynakları (`app/tasks.py`, `app/routers/books.py`, `app/task_queue.py`, `app/durable_queue.py`)**:
  - `active_tasks[task_id]` ve `update_task_status(...)` üzerinden `notify_ws("task", {"task_id": task_id, "task": task_snapshot})` yayını yapılır.
  - Görev nesnesinin gerçek alanları: `filename`, `status` (`"processing"` | `"pending"` | `"success"` | `"error"`), `percentage` (`0–100`), `log_message`, `last_update` (epoch sn), `logs` (en fazla 40 girdi: `{ts, message, status, state, pct}`), `task_data` (tamamlandığında `book_entry` — `kitap_adi`, `yazar`, `kategori`, `dosya_hash` vb.). (UI tarafında `step` alanı backend tarafından gönderilmez; `percentage` ve `log_message` üzerinden türetilir.)
- **Frontend Darboğazları (`static/js/ui_logs.js`, `templates/kutuphane.html`)**:
  - `updateOpsUI` her WebSocket `task` mesajında `#ops-body` içeriğini `body.innerHTML = ...` ile baştan kuruyor → ilerleme çubuğu animasyonu kesiliyor, açık `<details>` panelleri kapanıyor ve kaydırma konumu sıfırlanıyor.
  - Sabit/varsayılan metinler: `#ops-engine-label` içinde `"Gemini 3.5 Flash-Lite"` sabit yazılmış durumda; gerçek `appSettings` / `getAISettings()` kaynağına bağlanmalıdır.
  - `setLogsConnectionStatus` (`websocket.js`) yalnızca log modalı göstergesini güncelliyor; İşlem Merkezi pill/şeridine bağlı değil.

### 1.4 Okuyucu, AI Sohbet Paneli, Responsive & PWA
- Okuyucu AI paneli (`toggleWorkspaceChatPane` in `ui_workspace.js`), arama barı/çekmecesi ve not modalı (`openNoteModalForSelection` / `closePdfNoteModalDirect`) aynı `Motion` yaşam döngüsüne bağlanacak; `cleanupCustomPdfViewer` ve `closeWorkspace` zamanlayıcıları temizleyecektir.
- `static/sw.js`: `CACHE_NAME` ve `STATIC_ASSETS` yeni `motion.css` / `motion.js` dosyalarını içerecek şekilde sürümlenir (`v2026111504`).

---

*(Detaylı token tablosu, `Motion` API referansı ve yüzey karar matrisi Adım 6 sonunda tamamlanacaktır.)*
