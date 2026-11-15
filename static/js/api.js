/* cspell:disable */
/* ═══════════ api.js — API & Backend Communication ═══════════ */
    let tempIdSeq = 0;
    function generateTempId(prefix = 'temp') {
      if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }
      return `${prefix}-${Date.now()}-${++tempIdSeq}`;
    }

    function esc(str) {
      if (!str) return "";
      return String(str)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;")
        .replaceAll("`", "&#096;")
        .replaceAll("$", "&#036;");
    }

    function encData(str) {
      return encodeURIComponent(String(str || ""));
    }

    function highlightDocReferences(html) {
      const docRefRegex = /(?:^|[\s*+])([\w.-]+\.(?:pdf|epub|txt))(?=[\s*+]|$|[.,!?;:])/gi;
      return html.replace(docRefRegex, (match, filename) => {
        const prefix = (match.startsWith(' ') || match.startsWith('*') || match.startsWith('+')) ? match[0] : '';
        return `${prefix}<span class="source-capsule"><i class="fas fa-file-alt"></i> ${filename}</span>`;
      });
    }

    function convertPageCitations(html) {
      const bracketPattern = /\[(?:Sayfa|s\.|Page)[:\s]+(\d+)(?:[-–,]\s*\d+)?\]/gi;
      const plainPattern = /\b(?:Sayfa|s\.)\s+(\d+)\b/gi;
      const citeReplacer = (_match, pageNum) => {
        return `<span class="chat-page-cite" data-jump-page="${pageNum}" role="button" tabindex="0" title="Sayfa ${pageNum}'e git"><i class="fas fa-bookmark"></i> Sayfa ${pageNum}</span>`;
      };
      return html.replace(bracketPattern, citeReplacer).replace(plainPattern, citeReplacer);
    }

    function parseMarkdown(text) {
      if (!text) return '';
      let html = '';
      if (window.marked && typeof window.marked.parse === 'function') {
        html = window.marked.parse(text);
      } else {
        html = esc(text).replaceAll('\n', '<br>');
      }

      html = highlightDocReferences(html);
      html = convertPageCitations(html);

      if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
        return window.DOMPurify.sanitize(html, { ADD_ATTR: ['data-jump-page'] });
      }
      // Fail-safe: If DOMPurify is unavailable (CDN error / adblock), never output unsanitized marked HTML
      return esc(text).replaceAll('\n', '<br>');
    }
    window.parseMarkdown = parseMarkdown;

    // --- API & AI HELPERS ---
    function getAISettings() {
      const settings = window.appSettings || {};
      const provider = settings.ai_provider || localStorage.getItem('ai_provider') || 'gemini';
      let model = '';
      if (provider === 'gemini') model = settings.gemini_model || localStorage.getItem('gemini_model') || 'gemini-3.5-flash-lite';
      else if (provider === 'ollama') model = settings.ollama_model || localStorage.getItem('ollama_model') || '';
      else if (provider === 'lmstudio') model = settings.lmstudio_model || localStorage.getItem('lmstudio_model') || '';

      const rawKey = settings.ai_api_key || localStorage.getItem('ai_api_key') || '';
      const cleanKey = (rawKey.includes('•') || rawKey.startsWith('••') || rawKey === '••••••••') ? '' : rawKey.trim();

      return {
        provider: provider,
        apiKey: cleanKey,
        baseUrl: settings.ai_base_url || localStorage.getItem('ai_base_url') || '',
        modelName: model
      };
    }

    function safeHeaderVal(val) {
      if (!val) return '';
      const str = String(val).trim();
      // Never send masked bullets (•) or non-ISO-8859-1 chars in HTTP headers
      if (str.includes('•') || str.startsWith('••')) return '';
      return str.replace(/[^\x00-\xFF]/g, '');
    }

    async function apiFetch(url, options = {}) {
      const { provider, apiKey, baseUrl, modelName } = getAISettings();
      const headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        ...options.headers,
      };
      const safeProvider = safeHeaderVal(provider);
      const safeKey = safeHeaderVal(apiKey);
      const safeUrl = safeHeaderVal(baseUrl);
      const safeModel = safeHeaderVal(modelName);

      if (safeProvider) headers['X-AI-Provider'] = safeProvider;
      if (safeKey) headers['X-AI-Key'] = safeKey;
      if (safeUrl) headers['X-AI-Base-Url'] = safeUrl;
      if (safeModel) headers['X-AI-Model-Name'] = safeModel;

      let controller = null;
      let timer = null;
      let signal = options.signal;
      if (!signal && options.timeout !== 0) {
        controller = new AbortController();
        signal = controller.signal;
        const timeoutMs = options.timeout || 35000;
        timer = setTimeout(() => controller.abort(), timeoutMs);
      }

      try {
        const response = await fetch(url, { cache: 'no-store', ...options, signal, headers });
        if (response.status === 401) {
          window.location.href = '/login';
          return null;
        }
        return response;
      } finally {
        if (timer) clearTimeout(timer);
      }
    }

    function updateAICascadeState(isCascadeActive, modelNameEl, modelBadge, modelHint) {
      if (!modelNameEl) return;
      const slotsList = document.getElementById('cascade-slots-list');
      if (slotsList) {
        slotsList.style.opacity = isCascadeActive ? '1' : '0.45';
        slotsList.style.pointerEvents = isCascadeActive ? 'auto' : 'none';
        slotsList.style.transition = 'opacity 0.25s ease';
      }
      if (isCascadeActive) {
        modelNameEl.disabled = true;
        modelNameEl.style.opacity = '0.55';
        modelNameEl.style.cursor = 'not-allowed';
        modelNameEl.style.background = 'var(--bg-hover)';
        if (modelBadge) modelBadge.innerHTML = '<span style="color:var(--accent);"><i class="fas fa-layer-group"></i> Zincir Devrede</span>';
        if (modelHint) modelHint.innerText = 'Kademeli model zinciri devrede olduğu için aşağıdaki kademeli sıra kullanılır.';
      } else {
        modelNameEl.disabled = false;
        modelNameEl.style.opacity = '1';
        modelNameEl.style.cursor = 'text';
        modelNameEl.style.background = 'var(--paper)';
        if (modelBadge) modelBadge.innerHTML = '<span style="color:#5f7a4f;"><i class="fas fa-check-circle"></i> Tekil Mod Aktif</span>';
        if (modelHint) modelHint.innerText = 'Kademeli zincir kapalı; tüm işlemler için bu tekil model kullanılır.';
      }
    }

    function getPreferredModelName(provider) {
      const settings = window.appSettings || {};
      if (provider === 'gemini') {
        let gm = localStorage.getItem('gemini_model') || settings.gemini_model || 'gemini-3.5-flash-lite';
        if (!gm || gm === 'gemini-3.1-flash-lite-preview' || gm === 'gemini-1.5-flash-lite') {
          gm = 'gemini-3.5-flash-lite';
          localStorage.setItem('gemini_model', gm);
        }
        return { value: gm, placeholder: 'gemini-3.5-flash-lite' };
      }
      if (provider === 'ollama') {
        return {
          value: localStorage.getItem('ollama_model') || settings.ollama_model || '',
          placeholder: 'Örn: llama3'
        };
      }
      if (provider === 'lmstudio') {
        return {
          value: localStorage.getItem('lmstudio_model') || settings.lmstudio_model || '',
          placeholder: 'Örn: local-model'
        };
      }
      return { value: '', placeholder: '' };
    }

    function updateAIProviderInputs(provider, cloudInputs, urlContainer, modelContainer, localWarning, modelNameEl) {
      const isGemini = provider === 'gemini';
      if (cloudInputs) cloudInputs.style.display = isGemini ? 'block' : 'none';
      if (urlContainer) urlContainer.style.display = isGemini ? 'none' : 'block';
      if (modelContainer) modelContainer.style.display = 'block';
      if (localWarning) localWarning.style.display = isGemini ? 'none' : 'block';

      if (!modelNameEl) return;
      const { value, placeholder } = getPreferredModelName(provider);
      modelNameEl.value = value;
      modelNameEl.placeholder = placeholder;
    }

    function updateAIUI() {
      const providerEl = document.getElementById('set-ai-provider');
      if (!providerEl) return;
      const provider = providerEl.value;
      const cloudInputs = document.getElementById('ai-cloud-inputs');
      const urlContainer = document.getElementById('ai-url-container');
      const modelContainer = document.getElementById('ai-model-container');
      const localWarning = document.getElementById('ai-local-warning');
      const modelNameEl = document.getElementById('set-ai-model-name');
      const cascadeContainer = document.getElementById('ai-cascade-container');
      const cascadeCheckbox = document.getElementById('set-gemini-cascade-mode');
      const modelBadge = document.getElementById('ai-model-status-badge');
      const modelHint = document.getElementById('ai-model-hint');

      if (cascadeContainer) cascadeContainer.style.display = provider === 'gemini' ? 'block' : 'none';
      
      const isCascadeActive = provider === 'gemini' && (!cascadeCheckbox || cascadeCheckbox.checked);

      updateAICascadeState(isCascadeActive, modelNameEl, modelBadge, modelHint);
      updateAIProviderInputs(provider, cloudInputs, urlContainer, modelContainer, localWarning, modelNameEl);
    }

    let pendingBookReload = false;

    function updateLibraryZoneVisibility(hasItems) {
      const importZone = document.getElementById('import-zone');
      const mainContent = document.getElementById('main-content');
      const controlsPanel = document.querySelector('.controls-panel');
      const headerAddBtn = document.getElementById('header-add-book-btn');
      const compactAddBtn = document.getElementById('compact-add-book-btn');
      const compactNav = document.getElementById('compact-nav');

      if (hasItems) {
        if (importZone) importZone.style.display = 'none';
        if (mainContent) mainContent.style.display = 'block';
        if (controlsPanel) controlsPanel.style.display = 'flex';
        if (headerAddBtn) {
          headerAddBtn.style.display = 'inline-flex';
          headerAddBtn.classList.remove('hidden');
        }
        if (compactAddBtn) {
          compactAddBtn.style.display = 'inline-flex';
          compactAddBtn.classList.remove('hidden');
        }
      } else {
        if (importZone) importZone.style.display = 'block';
        if (mainContent) mainContent.style.display = 'none';
        if (controlsPanel) controlsPanel.style.display = 'none';
        if (headerAddBtn) {
          headerAddBtn.style.display = 'none';
          headerAddBtn.classList.add('hidden');
        }
        if (compactAddBtn) {
          compactAddBtn.style.display = 'none';
          compactAddBtn.classList.add('hidden');
        }
        if (compactNav) compactNav.classList.remove('visible');
      }
    }

    function mapBookRow(row) {
      return {
        title: String(row['kitap_adi'] || '').trim(),
        author: String(row['yazar'] || '').trim(),
        category: String(row['kategori'] || '').trim(),
        subcat: String(row['alt_kategori'] || '').trim(),
        summary: String(row['ozet'] || '').trim(),
        keywords: String(row['anahtar_kelimeler'] || '').trim(),
        file: String(row['dosya_adi'] || '').trim(),
        hash: String(row['dosya_hash'] || '').trim(),
        has_cover: !!row['has_cover'],
        is_favorite: !!row['is_favorite'],
        collections: row['koleksiyonlar'] || [],
        okunulan_sayfa: Number.parseInt(row['okunulan_sayfa'] || 1, 10)
      };
    }

    function _applyLoadedBooksData(data, page, append) {
      const items = data.items || [];
      window.totalBooks = data.total || 0;
      window.currentPage = page;

      const mapped = items.map(mapBookRow);
      window.allBooks = append ? (window.allBooks || []).concat(mapped) : mapped;

      updateLibraryZoneVisibility(window.allBooks.length > 0 || uploadingCards.size > 0);

      buildCategoryTags();
      if (page === 1) {
        void loadCollectionsFromAPI();
      }
      updateStats();
      render();
    }

    async function loadBooksFromAPI(page = 1, append = false) {
      if (window.isLoadingMore) {
        if (!append) pendingBookReload = true;
        return;
      }
      window.isLoadingMore = true;

      // Initial load: show skeleton cards if grid is empty
      if (page === 1 && !append && (!window.allBooks || window.allBooks.length === 0)) {
        if (typeof renderGridSkeletons === 'function') {
          renderGridSkeletons(8);
        }
      }
      try {
        const response = await apiFetch(`/api/books?page=${page}&limit=50&_t=${Date.now()}`);
        if (response?.status === 401) {
          window.location.href = '/login';
          return;
        }
        if (!response?.ok) {
          throw new Error(`API hata kodu: ${response ? response.status : 'Bilinmeyen'}`);
        }
        const data = await response.json();
        _applyLoadedBooksData(data, page, append);
      } catch (error) {
        console.error("Kitaplar yüklenirken hata:", error);
        if (typeof showToast === 'function') {
          showToast("Kitaplar yüklenemedi: Sunucu bağlantısını kontrol edin.", "error");
        }
      } finally {
        window.isLoadingMore = false;
        if (pendingBookReload) {
          pendingBookReload = false;
          void loadBooksFromAPI(1, false);
        }
      }
    }

    function handleExistingUploadedBook(fileHash, tempId) {
      removeUploadingCard(tempId, false);
      window.activeCategory = 'all';
      window.activeCollection = 'all';
      window.showOnlyFav = false;
      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.value = '';
      const catTrigger = document.getElementById('category-trigger');
      if (catTrigger) catTrigger.textContent = 'Tüm Kategoriler';
      const colTrigger = document.getElementById('collection-trigger');
      if (colTrigger) colTrigger.textContent = 'Tüm Koleksiyonlar';
      if (typeof buildCategoryTags === 'function') buildCategoryTags();
      render();
      setTimeout(() => {
        const existingCard = document.getElementById(`book-${fileHash}`);
        if (existingCard) {
          existingCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
          existingCard.style.outline = '3px solid var(--accent)';
          setTimeout(() => {
            existingCard.style.outline = 'none';
          }, 4000);
        }
      }, 150);
    }

    async function uploadFile(file, tempId) {
      const formData = new FormData();
      formData.append('file', file);

      // Etkinlik Merkezi kapsülünü paneli zorla açmadan nazikçe bilgilendir
      const opsToggle = document.getElementById('ops-toggle');
      if (opsToggle) {
        opsToggle.classList.remove('ops-toggle-pulse');
        void opsToggle.offsetWidth;
        opsToggle.classList.add('ops-toggle-pulse');
      }
      if (typeof fetchTasksFromAPI === 'function') {
        void fetchTasksFromAPI();
      }

      const placeholder = uploadingCards.get(tempId);
      if (placeholder) placeholder.label.textContent = 'Sunucuya aktarılıyor...';

      try {
        const response = await apiFetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        const result = await response.json();
        if (result?.status === 'exists') {
          handleExistingUploadedBook(result.file_hash, tempId);
          return;
        }
        if (result?.task_id && tempId) {
          taskToTemp.set(result.task_id, tempId);
          const placeholderCard = uploadingCards.get(tempId);
          if (placeholderCard) placeholderCard.label.textContent = 'Analiz kuyruğuna girdi...';

          // Sync with any early WebSocket messages
          if (lastActiveTasks[result.task_id] || lastArchivedTasks[result.task_id]) {
            updateUploadCards({ ...lastActiveTasks, ...lastArchivedTasks });
          }
        }
      } catch (error) {
        console.error("Yükleme hatası:", error);
        addChatMessage('ai', "Sunucuya bağlanılamadı.");
        const holder = uploadingCards.get(tempId);
        if (holder?.card) {
          holder.card.classList.remove('uploading');
          holder.card.classList.add('is-upload-error');
          if (holder.label) holder.label.textContent = 'Sunucuya bağlanılamadı';
        }
        removeUploadingCard(tempId, true);
      }
    }

    async function prepareUpload(file, dedupeKey) {
      const tempId = generateTempId('upload');
      updateLibraryZoneVisibility(true);
      const placeholder = createUploadingCard(tempId, file.name, dedupeKey);
      uploadingCards.set(tempId, placeholder);

      // İlk sayfa ön izlemesi
      renderPdfPreview(file).then(url => {
        if (url && placeholder?.placeholder) {
          placeholder.placeholder.innerHTML = `<img src="${url}" alt="${esc(file.name)}" loading="lazy" onload="this.classList.add('loaded')">`;
        }
      }).catch(err => {
        console.warn("Önizleme hatası:", err);
      });

      await uploadFile(file, tempId);
    }

    function _setCardInkProgress(holder, pct) {
      if (!holder?.bar) return;
      const clamped = Math.min(100, Math.max(5, Number(pct) || 5));
      const scale = (clamped / 100).toFixed(3);
      holder.bar.style.setProperty('--progress', scale);
      holder.bar.style.transform = `scaleX(${scale})`;
    }

    function createUploadingCard(tempId, filename, dedupeKey) {
      const grid = document.getElementById('grid-view');
      const card = document.createElement('div');
      card.className = 'book-card uploading';
      card.dataset.tempId = tempId;
      card.dataset.filename = filename || '';
      card.innerHTML = `
    <div class="card-cover">
      <div class="card-cat-badge uploading-stage-pill" id="ph-badge-${tempId}">Hazırlanıyor</div>
      <div class="card-cover-placeholder" id="ph-img-${tempId}">${BOOK_ICON_LG}<span>${esc(filename)}</span></div>
    </div>
    <div class="uploading-ink-track" aria-hidden="true">
      <div class="progress-bar"><span style="--progress:0.05; transform:scaleX(0.05);"></span></div>
    </div>
    <div class="card-body">
      <div class="card-title" id="ph-title-${tempId}">${esc(filename)}</div>
      <div class="card-author" id="ph-author-${tempId}">Kuyruğa alındı...</div>
      <div class="uploading-stage-caption">
        <span class="progress-label">Bekliyor...</span>
      </div>
      <div class="card-summary" id="ph-summary-${tempId}">Belge içeriği okunuyor ve kütüphane için analiz ediliyor.</div>
    </div>
  `;
      grid.prepend(card);
      return {
        card,
        filename,
        bar: card.querySelector('.progress-bar span'),
        label: card.querySelector('.progress-label'),
        placeholder: card.querySelector(`#ph-img-${tempId}`),
        badge: card.querySelector(`#ph-badge-${tempId}`),
        title: card.querySelector(`#ph-title-${tempId}`),
        author: card.querySelector(`#ph-author-${tempId}`),
        summary: card.querySelector(`#ph-summary-${tempId}`),
        dedupeKey
      };
    }

    async function renderPdfPreview(file) {
      // Memory guard: skip heavy client-side arrayBuffer decoding for very large files (>40MB) or deep batch queues
      if (!file?.name?.toLowerCase().endsWith('.pdf') || (file.size || 0) > 40 * 1024 * 1024) {
        return null;
      }
      if (typeof uploadingCards !== 'undefined' && uploadingCards.size > 4) {
        return null;
      }
      let pdf = null;
      try {
        const buf = await file.arrayBuffer();
        pdf = await pdfjsLib.getDocument({ data: buf }).promise;
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 0.5 });
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvasContext: ctx, viewport }).promise;
        return canvas.toDataURL('image/jpeg', 0.72);
      } catch (e) {
        console.error("Önizleme hatası:", e);
        return null;
      } finally {
        if (pdf && typeof pdf.destroy === 'function') {
          try { await pdf.destroy(); } catch (_) {}
        }
      }
    }

    function updateExistingTelegramCard(holder, message, percent) {
      if (!holder) return;
      if (holder.label) holder.label.textContent = message || "Telegram'dan indiriliyor...";
      if (holder.bar && percent !== undefined && percent !== null) {
        _setCardInkProgress(holder, Number.parseFloat(percent) || 0);
      }
    }

    function initTelegramCardPlaceholder(placeholder, message, percent) {
      if (!placeholder) return;
      if (placeholder.badge) {
        placeholder.badge.innerHTML = '<i class="fab fa-telegram-plane"></i> Telegram';
        placeholder.badge.style.background = 'var(--accent)';
        placeholder.badge.style.color = 'var(--on-accent)';
      }
      if (placeholder.author) {
        placeholder.author.textContent = 'Telegram Belgesi';
      }
      if (placeholder.summary) {
        placeholder.summary.textContent = 'Belge Telegram sunucularından indiriliyor, ardından analiz edilecek.';
      }
      const initialPct = (percent !== undefined && percent !== null)
        ? (Number.parseFloat(percent) || 0)
        : 10;
      _setCardInkProgress(placeholder, initialPct);
      if (placeholder.label) {
        placeholder.label.textContent = message || "Telegram'dan indiriliyor...";
      }
    }

    function handleTelegramDownloadingCard(filename, message, percent, speed) {
      if (!filename || !document.getElementById('grid-view')) return;

      updateLibraryZoneVisibility(true);

      let tempId = telegramDlCards.get(filename);
      if (tempId && uploadingCards.has(tempId)) {
        updateExistingTelegramCard(uploadingCards.get(tempId), message, percent);
        return;
      }

      tempId = generateTempId('tg-dl');
      telegramDlCards.set(filename, tempId);

      const placeholder = createUploadingCard(tempId, filename);
      if (placeholder) {
        initTelegramCardPlaceholder(placeholder, message, percent);
        uploadingCards.set(tempId, placeholder);
      }
    }

    function handleTelegramCardSkipped(filename, message) {
      if (!filename) return;
      const tempId = telegramDlCards.get(filename);
      if (tempId) {
        const holder = uploadingCards.get(tempId);
        if (holder) {
          if (holder.badge) {
            holder.badge.innerHTML = '<i class="fas fa-check-circle"></i> Zaten Kayıtlı';
            holder.badge.style.background = 'var(--accent)';
            holder.badge.style.color = 'var(--on-accent)';
          }
          if (holder.label) holder.label.textContent = 'Kütüphanede mevcut (Atlandı)';
          _setCardInkProgress(holder, 100);
          holder.card?.classList.add('is-upload-complete');
          setTimeout(() => removeUploadingCard(tempId, false), 1200);
        } else {
          removeUploadingCard(tempId, false);
        }
        telegramDlCards.delete(filename);
      }
    }

    function cleanupTelegramDlCards() {
      for (const tempId of telegramDlCards.values()) {
        const holder = uploadingCards.get(tempId);
        if (holder) {
          let hasActiveTask = false;
          for (const [taskId, mappedTemp] of taskToTemp.entries()) {
            if (mappedTemp === tempId && lastActiveTasks[taskId]) {
              hasActiveTask = true;
              break;
            }
          }
          if (!hasActiveTask) {
            removeUploadingCard(tempId, false);
          }
        }
      }
      telegramDlCards.clear();
    }


    function applyTaskDataToCard(holder, td) {
      if (!td) return;
      if (td.kitap_adi && holder.title) holder.title.textContent = td.kitap_adi;
      if (td.yazar && holder.author) holder.author.textContent = td.yazar;
      if (td.ozet && holder.summary) holder.summary.textContent = td.ozet;
      if (td.kategori && holder.badge) {
        holder.badge.textContent = td.kategori;
        holder.badge.style.background = '';
        holder.badge.style.color = '';
      }
      if (td.dosya_hash && holder.placeholder && !holder.coverLoaded) {
        const img = new Image();
        img.src = `/thumbnails/${td.dosya_hash}.jpg?t=${Date.now()}`;
        img.onload = () => {
          holder.placeholder.innerHTML = `<img src="${img.src}" class="loaded" alt="${esc(td.kitap_adi || '')}" style="width:100%; height:100%; object-fit:cover;">`;
          holder.coverLoaded = true;
        };
      }
    }

    function handleCardStatusOutcome(holder, task, tempId, taskId) {
      if (task.status === 'success') {
        const alreadyHandled = Boolean(holder.outcomeHandled);
        holder.outcomeHandled = true;
        if (holder.card) {
          holder.card.classList.add('is-upload-complete');
        }
        if (holder.label) holder.label.textContent = task.log_message || 'Kütüphaneye eklendi';
        _setCardInkProgress(holder, 100);

        // Yeni eklenen kitabın yer tutucu karttan gerçek karta kesintisiz yerleşmesi için konumunu kaydet
        window._recentlyCompletedUploads = window._recentlyCompletedUploads || new Set();
        window._pendingUploadMorphRects = window._pendingUploadMorphRects || new Map();
        const completedFn = (task.filename || holder.filename || '').trim().toLowerCase();
        const completedHash = (task.task_data?.dosya_hash || '').trim();
        if (completedFn) window._recentlyCompletedUploads.add(completedFn);
        if (completedHash) window._recentlyCompletedUploads.add(completedHash);
        if (holder.card?.isConnected) {
          const rect = holder.card.getBoundingClientRect();
          if (completedHash) {
            holder.card.dataset.completedHash = completedHash;
            window._pendingUploadMorphRects.set(completedHash, rect);
          }
          if (completedFn) window._pendingUploadMorphRects.set(completedFn, rect);
        }

        if (!alreadyHandled) {
          if (holder.cleanupTimer) clearTimeout(holder.cleanupTimer);
          holder.cleanupTimer = setTimeout(() => {
            holder.cleanupTimer = null;
            if (uploadingCards.has(tempId)) {
              removeUploadingCard(tempId, false);
            }
          }, 4200);

          setTimeout(() => {
            if (!completedTasks.has(taskId)) {
              completedTasks.add(taskId);
              if (typeof loadBooksFromAPI === 'function') {
                void loadBooksFromAPI(1, false);
              }
            }
          }, 140);
        }
      } else if (task.status === 'error') {
        holder.card.classList.remove('uploading');
        holder.card.classList.add('is-upload-error');
        if (holder.label) holder.label.textContent = task.log_message || 'İşlem başarısız oldu';
        if (holder.cleanupTimer) clearTimeout(holder.cleanupTimer);
        holder.cleanupTimer = setTimeout(() => removeUploadingCard(tempId, false), 8000);
      }
    }

    function updateSingleCardProgress(holder, task, tempId, taskId) {
      const pct = Math.max(5, task.percentage || 0);
      _setCardInkProgress(holder, pct);
      if (holder.label) holder.label.textContent = task.log_message || 'İşleniyor...';
      if (holder.badge && pct > 10 && !holder.card?.classList.contains('is-upload-complete')) {
        if (pct >= 85) holder.badge.textContent = 'Kataloglanıyor';
        else if (pct >= 50) holder.badge.textContent = 'AI Analizi';
        else holder.badge.textContent = 'Metin Okunuyor';
      }

      if (task.task_data) {
        applyTaskDataToCard(holder, task.task_data);
      }
      handleCardStatusOutcome(holder, task, tempId, taskId);
    }

    function adoptTelegramTaskCard(taskId, filename) {
      const tempId = telegramDlCards.get(filename);
      taskToTemp.set(taskId, tempId);
      const holder = uploadingCards.get(tempId);
      if (holder) {
        if (holder.badge) {
          holder.badge.innerHTML = '<i class="fab fa-telegram-plane"></i> Telegram';
          holder.badge.style.background = 'var(--accent)';
          holder.badge.style.color = 'var(--on-accent)';
        }
        if (holder.author) holder.author.textContent = 'Yapay Zeka Analizinde...';
      }
    }

    function createNewTaskCard(taskId, task) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      updateLibraryZoneVisibility(true);
      const tempId = `bg-task-${taskId}`;
      taskToTemp.set(taskId, tempId);
      const placeholder = createUploadingCard(tempId, task.filename || 'Yeni Kitap', taskId);
      if (placeholder?.badge) {
        const isTg = task.logs?.some(l => l.message?.includes('Telegram')) ||
                     task.log_message?.includes('Telegram');
        if (isTg) {
          placeholder.badge.innerHTML = '<i class="fab fa-telegram-plane"></i> Telegram';
          placeholder.badge.style.background = 'var(--accent)';
          placeholder.badge.style.color = 'var(--on-accent)';
        }
      }
      uploadingCards.set(tempId, placeholder);
    }

    function ensureTaskCardExists(taskId, task) {
      if (!task || task.status === 'success' || task.status === 'error') return;
      if (taskToTemp.has(taskId)) return;

      // If the book is already present and completed in the library, don't spawn a ghost card
      if (Array.isArray(window.allBooks) && task.filename) {
        const taskFn = task.filename.trim().toLowerCase();
        const alreadyInLibrary = window.allBooks.some(b => {
          const bDosya = (b.dosya_adi || '').trim().toLowerCase();
          const bTitle = (b.baslik || '').trim().toLowerCase();
          return (bDosya && (bDosya === taskFn || taskFn.includes(bDosya))) || (bTitle && bTitle === taskFn);
        });
        if (alreadyInLibrary) return;
      }

      if (task.filename && telegramDlCards.has(task.filename)) {
        adoptTelegramTaskCard(taskId, task.filename);
        return;
      }

      // Check if there is an existing uploadingCard created by local file upload
      let matchedTempId = null;
      if (task.filename) {
        const taskFnNorm = task.filename.trim().toLowerCase();
        for (const [tempId, holder] of uploadingCards.entries()) {
          let alreadyBound = false;
          for (const assignedTemp of taskToTemp.values()) {
            if (assignedTemp === tempId) {
              alreadyBound = true;
              break;
            }
          }
          if (alreadyBound) continue;

          const holderFnNorm = (holder.filename || holder.card?.dataset?.filename || '').trim().toLowerCase();
          if (holderFnNorm && (holderFnNorm === taskFnNorm || taskFnNorm.includes(holderFnNorm) || holderFnNorm.includes(taskFnNorm))) {
            matchedTempId = tempId;
            break;
          }
        }
      }

      if (matchedTempId) {
        taskToTemp.set(taskId, matchedTempId);
      } else {
        createNewTaskCard(taskId, task);
      }
    }

    function updateUploadCards(tasks) {
      if (!tasks || typeof tasks !== 'object') return;

      Object.entries(tasks).forEach(([taskId, task]) => {
        ensureTaskCardExists(taskId, task);
      });

      taskToTemp.forEach((tempId, taskId) => {
        const task = tasks[taskId];
        const holder = uploadingCards.get(tempId);
        if (task && holder) {
          updateSingleCardProgress(holder, task, tempId, taskId);
        }
      });
    }

    function removeUploadingCard(tempId, keep = false, immediate = false) {
      const holder = uploadingCards.get(tempId);
      if (holder?.cleanupTimer) {
        clearTimeout(holder.cleanupTimer);
        holder.cleanupTimer = null;
      }
      if (holder?.dedupeKey) pendingUploads.delete(holder.dedupeKey);
      if (holder?.card && !keep) {
        if (immediate) {
          holder.card.remove();
        } else if (window.Motion && typeof window.Motion.exit === 'function') {
          void window.Motion.exit(holder.card, {
            className: 'm-exit',
            afterFn: (el) => { if (el.isConnected) el.remove(); }
          });
        } else {
          holder.card.classList.add('fadeOut');
          setTimeout(() => holder.card.remove(), 300);
        }
      }
      uploadingCards.delete(tempId);
      for (const [tid, tmp] of taskToTemp.entries()) {
        if (tmp === tempId) taskToTemp.delete(tid);
      }
      for (const [fn, tmp] of telegramDlCards.entries()) {
        if (tmp === tempId) telegramDlCards.delete(fn);
      }
    }

    async function deleteBook(hash) {
      if (!hash) {
        showToast('Bu kayıt için silme kimliği bulunamadı.', 'warning');
        return;
      }
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Bu kitabı kalıcı olarak silmek istediğinize emin misiniz?', 'Kitabı Sil', 'Sil', true) : Promise.resolve(confirm('Bu kitabı kalıcı olarak silmek istediğinize emin misiniz?')));
      if (!ok) return;

      try {
        const response = await apiFetch(`/api/books/${encodeURIComponent(hash)}`, { method: 'DELETE' });
        let result = {};
        try {
          result = await response.json();
        } catch (_) {
          // JSON dönmeyen ama başarılı cevaplar için sorun yapma
        }

        if (response?.ok || result.status === 'deleted' || result.success === true) {
          addChatMessage('ai', 'Kitap sistemden silindi.');
          // Listeyi anında güncelle
          window.allBooks = (window.allBooks || []).filter(b => b.hash !== hash);
          updateStats();
          render();
          closeModalDirect();
          updateLibraryZoneVisibility((window.allBooks && window.allBooks.length > 0) || uploadingCards.size > 0);
        } else {
          const msg = result.message || result.status || response?.statusText || 'Bilinmeyen hata.';
          addChatMessage('ai', `Silme işlemi başarısız oldu: ${msg}`);
        }
      } catch (error) {
        console.error("Silme hatası:", error);
        addChatMessage('ai', "Silme işlemi başarısız oldu. Sunucuya ulaşılamadı.");
      }
    }

    function updateFavoriteCardDOM(card, isFav) {
      const heartIconWrap = card.querySelector('.btn-favorite-card');
      if (heartIconWrap) {
        heartIconWrap.innerHTML = isFav
          ? `<i class="fas fa-heart" style="color: var(--danger); font-size: 1.1rem;"></i>`
          : `<i class="far fa-heart" style="color: var(--paper); font-size: 1.1rem;"></i>`;
        heartIconWrap.title = isFav ? 'Favorilerden Çıkar' : 'Favorilere Ekle';
        if (isFav) {
          heartIconWrap.classList.remove('heart-pulse');
          heartIconWrap.getBoundingClientRect();
          heartIconWrap.classList.add('heart-pulse');
        }
      }
      if (showOnlyFav && !isFav) {
        card.classList.add('fadeOut');
        setTimeout(() => card.remove(), 400);
      }
    }

    function updateFavoriteModalBtn(hash, isFav) {
      const modalFavBtn = document.getElementById('btn-modal-fav');
      if (modalFavBtn && window.currentModalHash === hash) {
        modalFavBtn.className = isFav ? 'btn-modal-fav is-fav' : 'btn-modal-fav';
        modalFavBtn.innerHTML = isFav
          ? '<i class="fas fa-heart"></i> Favorilerden Çıkar'
          : '<i class="far fa-heart"></i> Favorilere Ekle';
      }
    }

    async function toggleFavorite(hash) {
      try {
        const res = await apiFetch(`/api/books/${hash}/favorite`, { method: 'PATCH' });
        if (!res?.ok) return;
        const data = await res.json();
        const book = (window.allBooks || []).find(b => b.hash === hash);
        if (!book) return;

        book.is_favorite = data.is_favorite;
        const cards = document.querySelectorAll(`#book-${hash}`);
        cards.forEach(card => updateFavoriteCardDOM(card, data.is_favorite));

        updateFavoriteModalBtn(hash, data.is_favorite);

        if (window.currentView === 'table') {
          render();
        }
      } catch (err) {
        console.error("Favori güncellenemedi:", err);
      }
    }

    // --- COLLECTION SHARING ---
    async function copyCollectionMarkdown(colId, colName) {
      try {
        const res = await apiFetch(`/api/share-collection/${colId}`);
        const data = await res.json();
        const books = data.kitaplar || [];
        
        let md = `### ${colName} Koleksiyonu\n\n`;
        md += `| Kitap Adı | Yazar | Kategori |\n`;
        md += `| :--- | :--- | :--- |\n`;
        books.forEach(b => {
          const title = b.kitap_adi || b.title || '—';
          const author = b.yazar || b.author || '—';
          const cat = b.kategori || b.category || '—';
          md += `| ${title} | ${author} | ${cat} |\n`;
        });
        
        await navigator.clipboard.writeText(md);
        showToast('Koleksiyon listesi Markdown formatında panoya kopyalandı!', 'success');
      } catch (e) {
        console.error('Koleksiyon kopyalama hatası:', e);
        showToast('Kopyalama sırasında hata oluştu.', 'error');
      }
    }

    async function importCollection() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.json';
      input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
          const res = await apiFetch('/api/collections/import', {
            method: 'POST',
            body: formData
          });
          const result = await res.json();
          if (res.ok) {
            showToast(`Koleksiyon başarıyla içe aktarıldı! (${result.added_books} kitap eşleşti)`, 'success');
            if (typeof loadCollectionsFromAPI === 'function') await loadCollectionsFromAPI();
            if (typeof loadBooksFromAPI === 'function') await loadBooksFromAPI(1, false);
            if (colTargetHash && typeof openColModal === 'function') openColModal(colTargetHash);
          } else {
            showToast('Hata: ' + result.detail, 'error');
          }
        } catch (err) {
          console.error('Koleksiyon içe aktarma hatası:', err);
          showToast('Yükleme hatası.', 'error');
        }
      };
      input.click();
    }

    async function syncLibrary() {
      const btn = document.getElementById('btn-sync');
      const icon = document.getElementById('sync-icon');
      if (btn) btn.disabled = true;
      if (icon) icon.className = 'fas fa-sync-alt fa-spin';
      
      try {
        const response = await apiFetch('/api/books/sync', {
          method: 'POST'
        });
        if (!response?.ok) {
          throw new Error('Eşitleme hatası');
        }
        const result = await response.json();
        const count = result.enqueued_count || 0;
        
        await loadBooksFromAPI(1, false);

        if (count > 0) {
          // Etkinlik merkezini düzenli köken animasyonuyla aç
          const opsCenter = document.getElementById('ops-center');
          if (opsCenter && !opsCenter.classList.contains('active') && typeof toggleOps === 'function') {
            toggleOps();
          } else if (opsCenter) {
            opsCenter.classList.add('active');
            if (typeof flushOpsBodyIfDirty === 'function') flushOpsBodyIfDirty();
          }
          
          showToast(`Kütüphane dizininde ${count} yeni kitap bulundu ve analiz kuyruğuna eklendi!`, 'info', 5000);
        } else {
          showToast('Kütüphane dizini kontrol edildi ve eşitlendi. Tüm kitaplar güncel.', 'success');
        }
      } catch (err) {
        console.error("Eşitleme hatası:", err);
        showToast('Kütüphane eşitlenirken bir hata oluştu.', 'error');
      } finally {
        if (btn) btn.disabled = false;
        if (icon) icon.className = 'fas fa-sync-alt';
      }
    }

    window.syncLibrary = syncLibrary;

    // --- TELEGRAM INTEGRATION API HELPERS ---
    async function apiTelegramStatus() {
      const res = await apiFetch('/api/telegram/status');
      if (!res.ok) throw new Error('Telegram durumu alınamadı');
      return await res.json();
    }

    async function apiTelegramSendCode(apiId, apiHash, phoneNumber, chatTarget = null) {
      const payload = {
        api_id: String(apiId).trim(),
        api_hash: String(apiHash).trim(),
        phone_number: String(phoneNumber).trim()
      };
      if (chatTarget) payload.chat_target = String(chatTarget).trim();
      const res = await apiFetch('/api/telegram/auth/send-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || 'Kod gönderilemedi');
      return data;
    }

    async function apiTelegramUpdateChannel(chatTarget) {
      let target = String(chatTarget || 'me').trim();
      if (!target || ['me', 'kayıtlı mesajlar', 'kayitli mesajlar', 'saved messages'].includes(target.toLowerCase())) {
        target = 'me';
      }

      // Try dedicated endpoint first
      try {
        const res = await apiFetch('/api/telegram/channel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_target: target })
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (_) {
        // Fall back to /api/settings
      }

      // Fallback: /api/settings endpoint (supported on all running server instances)
      const resSettings = await apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ telegram_chat_id: target, telegram_last_msg_id: 0 })
      });
      const data = await resSettings.json();
      if (!resSettings.ok) throw new Error(data.detail || data.error || 'Kanal güncellenemedi');
      return { success: true, chat_id: target };
    }

    async function apiTelegramVerify(code, password = null) {
      const payload = { code: String(code).trim() };
      if (password) payload.password = String(password).trim();
      const res = await apiFetch('/api/telegram/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || 'Doğrulama başarısız');
      return data;
    }

    async function apiTelegramSync(chatTarget = null, resetCursor = false) {
      const { provider, apiKey, baseUrl, modelName } = getAISettings();
      const payload = {};
      if (chatTarget) payload.chat_target = String(chatTarget).trim();
      if (apiKey) payload.api_key = apiKey;
      if (provider) payload.provider = provider;
      if (modelName) payload.model_name = modelName;
      if (baseUrl) payload.base_url = baseUrl;
      if (resetCursor) payload.reset_cursor = true;

      const res = await apiFetch('/api/telegram/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || 'Senkronizasyon başlatılamadı');
      return data;
    }

    async function apiTelegramDisconnect() {
      const res = await apiFetch('/api/telegram/disconnect', {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || data.error || 'Bağlantı kesilemedi');
      return data;
    }

    async function apiReanalyzeBook(fileHash) {
      const res = await apiFetch(`/api/books/${fileHash}/reanalyze`, {
        method: 'POST'
      });
      if (!res) throw new Error('Oturum sonlandı veya istek gönderilemedi.');
      let data = null;
      let textErr = '';
      try {
        data = await res.json();
      } catch (_) {
        textErr = await res.text().catch(() => '');
      }
      if (!res.ok) {
        throw new Error(data?.detail || data?.error || textErr || `Sunucu hatası (${res.status})`);
      }
      return data || {};
    }

    async function fetchTasksFromAPI() {
      const icon = document.getElementById('ops-refresh-icon');
      if (icon) icon.classList.add('fa-spin');
      try {
        const res = await apiFetch('/api/tasks');
        if (!res.ok) return;
        const data = await res.json();
        window.lastActiveTasks = data.active || {};
        window.lastArchivedTasks = data.archived || {};
        if (typeof updateOpsUI === 'function') {
          updateOpsUI(lastActiveTasks, lastArchivedTasks);
        }
        if (typeof updateUploadCards === 'function') {
          updateUploadCards({ ...lastActiveTasks, ...lastArchivedTasks });
        }
      } catch (e) {
        console.warn('fetchTasksFromAPI hatası:', e);
      } finally {
        if (icon) {
          setTimeout(() => icon.classList.remove('fa-spin'), 400);
        }
      }
    }

    window.apiTelegramStatus = apiTelegramStatus;
    window.apiTelegramSendCode = apiTelegramSendCode;
    window.apiTelegramUpdateChannel = apiTelegramUpdateChannel;
    window.apiTelegramVerify = apiTelegramVerify;
    window.apiTelegramSync = apiTelegramSync;
    window.apiTelegramDisconnect = apiTelegramDisconnect;
    window.apiReanalyzeBook = apiReanalyzeBook;
    window.handleTelegramDownloadingCard = handleTelegramDownloadingCard;
    window.handleTelegramCardSkipped = handleTelegramCardSkipped;
    window.cleanupTelegramDlCards = cleanupTelegramDlCards;
    window.fetchTasksFromAPI = fetchTasksFromAPI;
    window.removeUploadingCard = removeUploadingCard;
    window.uploadingCards = uploadingCards;
    window.esc = esc;
    window.encData = encData;

