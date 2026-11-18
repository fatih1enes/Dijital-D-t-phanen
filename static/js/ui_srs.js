/* ════════════════════════════════════════════════════════════════════════════════
 * ui_srs.js — Focused Reading Session Heartbeat, 365d Heatmap & FSRS-5 Studio
 * ════════════════════════════════════════════════════════════════════════════════ */

(function () {
  let _lastInteractionTs = Date.now();
  let _accumulatedFocusSec = 0;
  let _lastRecordedPage = 1;
  let _pagesDeltaAccum = 0;

  let _srsQueue = [];
  let _srsIndex = 0;
  let _srsRevealed = false;
  let _activeStatsSubtab = 'analytics';

  function _markReaderInteraction() {
    _lastInteractionTs = Date.now();
  }

  ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll'].forEach(evName => {
    window.addEventListener(evName, _markReaderInteraction, { passive: true });
  });

  async function flushReadingHeartbeat() {
    if (_accumulatedFocusSec < 5 || typeof activeWorkspaceBook === 'undefined' || !activeWorkspaceBook?.hash) {
      return;
    }
    const secToSend = _accumulatedFocusSec;
    const pgDelta = _pagesDeltaAccum;
    const curPage = typeof pdfPageNum !== 'undefined' ? (pdfPageNum || 1) : 1;
    _accumulatedFocusSec = 0;
    _pagesDeltaAccum = 0;

    const payload = {
      dosya_hash: activeWorkspaceBook.hash,
      delta_seconds: Math.min(600, secToSend),
      current_page: Math.max(1, curPage),
      pages_read_delta: Math.max(0, pgDelta)
    };

    try {
      if (!navigator.onLine && window.OfflineVault) {
        await window.OfflineVault.enqueueOfflineMutation('/api/analytics/heartbeat', 'POST', payload);
        return;
      }
      const res = await apiFetch('/api/analytics/heartbeat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res && window.OfflineVault) {
        await window.OfflineVault.enqueueOfflineMutation('/api/analytics/heartbeat', 'POST', payload);
      }
    } catch (_err) {
      if (window.OfflineVault) {
        await window.OfflineVault.enqueueOfflineMutation('/api/analytics/heartbeat', 'POST', payload);
      }
    }
  }
  window.flushReadingHeartbeat = flushReadingHeartbeat;

  setInterval(() => {
    const readerOpen = document.getElementById('workspace-reader')?.classList.contains('open');
    if (!readerOpen || document.hidden || typeof activeWorkspaceBook === 'undefined' || !activeWorkspaceBook) {
      return;
    }
    // Pause timer automatically when reader is idle for >90 seconds
    if (Date.now() - _lastInteractionTs > 90000) {
      return;
    }
    _accumulatedFocusSec += 10;
    const curP = typeof pdfPageNum !== 'undefined' ? (pdfPageNum || 1) : 1;
    if (curP !== _lastRecordedPage) {
      if (curP > _lastRecordedPage && (curP - _lastRecordedPage) <= 10) {
        _pagesDeltaAccum += (curP - _lastRecordedPage);
      } else {
        _pagesDeltaAccum += 1;
      }
      _lastRecordedPage = curP;
    }
    if (_accumulatedFocusSec >= 30) {
      void flushReadingHeartbeat();
    }
  }, 10000);

  function switchStatsSubtab(tabName) {
    _activeStatsSubtab = tabName === 'srs' ? 'srs' : 'analytics';
    document.getElementById('stats-subtab-analytics')?.classList.toggle('active', _activeStatsSubtab === 'analytics');
    document.getElementById('stats-subtab-srs')?.classList.toggle('active', _activeStatsSubtab === 'srs');
    const anaPane = document.getElementById('stats-pane-analytics');
    const srsPane = document.getElementById('stats-pane-srs');
    if (anaPane) anaPane.style.display = _activeStatsSubtab === 'analytics' ? 'block' : 'none';
    if (srsPane) srsPane.style.display = _activeStatsSubtab === 'srs' ? 'block' : 'none';

    if (_activeStatsSubtab === 'srs') {
      void loadDueSrsCards();
    } else {
      void loadFocusedReadingAnalytics();
    }
  }
  window.switchStatsSubtab = switchStatsSubtab;

  function _formatEtaDuration(minutes) {
    const m = Math.max(1, Number(minutes) || 1);
    if (m < 60) return `~${m} dk kaldı`;
    const h = Math.floor(m / 60);
    const rem = m % 60;
    return rem > 0 ? `~${h} sa ${rem} dk kaldı` : `~${h} saat kaldı`;
  }

  async function loadFocusedReadingAnalytics() {
    try {
      const [anaRes, srsRes] = await Promise.all([
        apiFetch('/api/analytics/reading'),
        apiFetch('/api/srs/due')
      ]);

      if (srsRes?.ok) {
        const srsData = await srsRes.json();
        const dueBadge = document.getElementById('srs-due-badge');
        if (dueBadge) {
          const cnt = srsData?.summary?.due || 0;
          dueBadge.textContent = String(cnt);
          dueBadge.style.display = cnt > 0 ? 'inline-flex' : 'none';
        }
      }

      if (!anaRes?.ok) return;
      const data = await anaRes.json();

      const kpiWrap = document.getElementById('reading-focus-kpis');
      if (kpiWrap) {
        kpiWrap.innerHTML = `
          <div class="stat-card focus-kpi-card">
            <div class="stat-card-value">${data.streak_days || 0} <small style="font-size:0.45em;">gün</small></div>
            <div class="stat-card-label"><i class="fas fa-fire" style="color:var(--accent);margin-right:4px;"></i> Kesintisiz Okuma Serisi</div>
          </div>
          <div class="stat-card focus-kpi-card">
            <div class="stat-card-value">${data.today_minutes || 0} <small style="font-size:0.45em;">dk</small></div>
            <div class="stat-card-label"><i class="fas fa-clock" style="color:var(--accent);margin-right:4px;"></i> Bugünkü Odak Süresi</div>
          </div>
          <div class="stat-card focus-kpi-card">
            <div class="stat-card-value">${data.pages_per_hour || 28} <small style="font-size:0.45em;">s/sa</small></div>
            <div class="stat-card-label"><i class="fas fa-gauge-high" style="color:var(--accent);margin-right:4px;"></i> Okuma Hızı</div>
          </div>
          <div class="stat-card focus-kpi-card">
            <div class="stat-card-value">${data.total_hours || 0} <small style="font-size:0.45em;">saat</small></div>
            <div class="stat-card-label"><i class="fas fa-hourglass-half" style="color:var(--accent);margin-right:4px;"></i> Yıllık Okuma</div>
          </div>
        `;
      }

      const heatEl = document.getElementById('reading-heatmap-grid');
      if (heatEl && Array.isArray(data.heatmap)) {
        heatEl.innerHTML = data.heatmap.map(cell => {
          const mins = Math.round((cell.seconds || 0) / 60);
          const tip = mins > 0
            ? `${cell.date}: ${mins} dk (${cell.pages || 0} sayfa)`
            : `${cell.date}: Okuma kaydı yok`;
          return `<span class="heatmap-cell lvl-${cell.level || 0}" title="${esc(tip)}"></span>`;
        }).join('');
      }

      const etaEl = document.getElementById('reading-eta-list');
      if (etaEl) {
        const etaBooks = Array.isArray(data.eta_books) ? data.eta_books : [];
        if (etaBooks.length === 0) {
          etaEl.innerHTML = '<div style="color:var(--muted); font-size:0.82rem; padding:0.5rem 0;">Okumaya başladığınız kitapların tahmini bitiş süresi (ETA) burada listelenir.</div>';
        } else {
          etaEl.innerHTML = etaBooks.map(b => `
            <div class="eta-book-row" onclick="openWorkspaceAtPage('${b.dosya_hash}', ${b.okunulan_sayfa})">
              <div class="eta-book-info">
                <strong>${esc(b.kitap_adi)}</strong>
                <span>%${b.progress_pct} · ${b.remaining_pages} sayfa kaldı</span>
              </div>
              <span class="eta-time-pill"><i class="fas fa-hourglass-end"></i> ${_formatEtaDuration(b.eta_minutes)}</span>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.debug('Reading analytics load note:', err);
    }
  }
  window.loadFocusedReadingAnalytics = loadFocusedReadingAnalytics;

  function _renderCurrentSrsCard() {
    const stage = document.getElementById('srs-card-stage');
    if (!stage) return;

    if (!_srsQueue || _srsIndex >= _srsQueue.length) {
      stage.innerHTML = `
        <div class="srs-empty-complete">
          <div class="srs-complete-icon"><i class="fas fa-award"></i></div>
          <h3>Bugünkü Aktif Hatırlama Tamamlandı!</h3>
          <p>FSRS v5 bellek motoru tüm zamanı gelen kartlarınızı gelecekteki en uygun tekrar günlerine planladı. Kitap okurken aldığınız yeni vurgular ve notlar otomatik olarak buraya aktarılır.</p>
          <button type="button" class="btn-modal-secondary" onclick="openCustomSrsModal()" style="margin-top:0.8rem;">
            <i class="fas fa-plus"></i> Özel Bilgi Kartı Ekle
          </button>
        </div>
      `;
      return;
    }

    const card = _srsQueue[_srsIndex];
    const remaining = _srsQueue.length - _srsIndex;
    const intervals = card.intervals || { '1': '5 dk', '2': '15 dk', '3': '3 gün', '4': '14 gün' };

    stage.innerHTML = `
      <div class="srs-flashcard">
        <div class="srs-card-topbar">
          <button type="button" class="srs-context-link" onclick="openWorkspaceAtPage('${esc(card.dosya_hash)}', ${Number(card.sayfa_no) || 1})" title="Kitapta bu sayfaya git">
            <i class="fas fa-book-open"></i> ${esc(card.baglam || card.kitap_adi || 'Kitap Notu')}
          </button>
          <span class="srs-progress-pill">${remaining} kart kaldı</span>
        </div>

        <div class="srs-card-front">${parseMarkdown(card.on_yuz || '')}</div>

        ${_srsRevealed ? `
          <div class="srs-card-divider"><span>Doğru Yanıt &amp; Kitap Pasajı</span></div>
          <div class="srs-card-back">${parseMarkdown(card.arka_yuz || '')}</div>
          <div class="srs-rating-grid">
            <button type="button" class="srs-rate-btn rate-again" onclick="gradeCurrentSrsCard(1)">
              <span class="rate-title">Tekrar <kbd>1</kbd></span>
              <span class="rate-interval">${esc(intervals['1'])}</span>
            </button>
            <button type="button" class="srs-rate-btn rate-hard" onclick="gradeCurrentSrsCard(2)">
              <span class="rate-title">Zor <kbd>2</kbd></span>
              <span class="rate-interval">${esc(intervals['2'])}</span>
            </button>
            <button type="button" class="srs-rate-btn rate-good" onclick="gradeCurrentSrsCard(3)">
              <span class="rate-title">İyi <kbd>3</kbd></span>
              <span class="rate-interval">${esc(intervals['3'])}</span>
            </button>
            <button type="button" class="srs-rate-btn rate-easy" onclick="gradeCurrentSrsCard(4)">
              <span class="rate-title">Kolay <kbd>4</kbd></span>
              <span class="rate-interval">${esc(intervals['4'])}</span>
            </button>
          </div>
        ` : `
          <div class="srs-reveal-wrap">
            <button type="button" class="btn-modal-primary srs-reveal-btn" id="btn-srs-reveal" onclick="revealCurrentSrsCard()">
              <i class="fas fa-eye"></i> Cevabı Göster <kbd style="margin-left:6px;opacity:0.8;">Boşluk</kbd>
            </button>
          </div>
        `}
      </div>
    `;
  }

  function revealCurrentSrsCard() {
    _srsRevealed = true;
    _renderCurrentSrsCard();
  }
  window.revealCurrentSrsCard = revealCurrentSrsCard;

  async function loadDueSrsCards() {
    const stage = document.getElementById('srs-card-stage');
    if (stage && !_srsQueue.length) {
      stage.innerHTML = '<div style="padding:2rem;text-align:center;color:var(--muted);"><i class="fas fa-spinner fa-spin"></i> Bellek kartları hazırlanıyor...</div>';
    }
    try {
      const res = await apiFetch('/api/srs/due');
      if (!res?.ok) return;
      const data = await res.json();
      const s = data.summary || {};

      const sumEl = document.getElementById('srs-deck-summary');
      if (sumEl) {
        sumEl.innerHTML = `
          <span class="srs-stat-chip due">Bugün Tekrar: <strong>${s.due || 0}</strong></span>
          <span class="srs-stat-chip">Yeni: <strong>${s.new || 0}</strong></span>
          <span class="srs-stat-chip">Öğrenilen: <strong>${s.learning || 0}</strong></span>
          <span class="srs-stat-chip">Pekiştirilen: <strong>${s.review || 0}</strong></span>
          <span class="srs-stat-chip">Toplam: <strong>${s.total || 0}</strong></span>
        `;
      }
      const dueBadge = document.getElementById('srs-due-badge');
      if (dueBadge) {
        dueBadge.textContent = String(s.due || 0);
        dueBadge.style.display = (s.due || 0) > 0 ? 'inline-flex' : 'none';
      }

      _srsQueue = Array.isArray(data.cards) ? data.cards : [];
      _srsIndex = 0;
      _srsRevealed = false;
      _renderCurrentSrsCard();
    } catch (e) {
      console.warn('SRS due load error:', e);
    }
  }
  window.loadDueSrsCards = loadDueSrsCards;

  async function gradeCurrentSrsCard(rating) {
    if (!_srsQueue || _srsIndex >= _srsQueue.length) return;
    const card = _srsQueue[_srsIndex];
    try {
      await apiFetch(`/api/srs/cards/${card.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: Number(rating) })
      });
    } catch (_e) {}
    _srsIndex++;
    _srsRevealed = false;
    _renderCurrentSrsCard();
    if (_srsIndex >= _srsQueue.length) {
      void loadDueSrsCards();
    }
  }
  window.gradeCurrentSrsCard = gradeCurrentSrsCard;

  async function openCustomSrsModal() {
    const front = prompt('Kartın Ön Yüzü (Soru veya Kavram):');
    if (!front || !front.trim()) return;
    const back = prompt('Kartın Arka Yüzü (Cevap veya Açıklama):');
    if (!back || !back.trim()) return;
    const defaultHash = (window.allBooks && window.allBooks[0]?.hash) || ('0'.repeat(64));
    const defaultTitle = (window.allBooks && window.allBooks[0]?.title) || 'Kişisel Kart';
    try {
      const res = await apiFetch('/api/srs/cards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dosya_hash: defaultHash,
          sayfa_no: 1,
          on_yuz: front.trim(),
          arka_yuz: back.trim(),
          baglam: defaultTitle
        })
      });
      if (res?.ok) {
        if (typeof showToast === 'function') showToast('FSRS bilgi kartı oluşturuldu.', 'success');
        await loadDueSrsCards();
      }
    } catch (_e) {}
  }
  window.openCustomSrsModal = openCustomSrsModal;

  document.addEventListener('keydown', (e) => {
    const statsView = document.getElementById('stats-view');
    if (!statsView || statsView.style.display === 'none' || _activeStatsSubtab !== 'srs') return;
    const readerOpen = document.getElementById('workspace-reader')?.classList.contains('open');
    if (readerOpen || document.body.classList.contains('modal-open')) return;
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

    if (!_srsRevealed && (e.key === ' ' || e.code === 'Space')) {
      if (_srsQueue && _srsIndex < _srsQueue.length) {
        e.preventDefault();
        revealCurrentSrsCard();
      }
    } else if (_srsRevealed && ['1', '2', '3', '4'].includes(e.key)) {
      e.preventDefault();
      void gradeCurrentSrsCard(Number(e.key));
    }
  });
})();
