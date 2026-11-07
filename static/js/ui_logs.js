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

