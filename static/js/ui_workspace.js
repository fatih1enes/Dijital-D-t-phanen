/* ════════════════════════════════════════════════════════════════════════════════
 * ui_workspace.js — Focused Workspace Reader, Virtualized Engine & Annotations
 * ════════════════════════════════════════════════════════════════════════════════
 * Modüler Mimari Dizini:
 *   [1] MOBIL KONTROLLER & SCRUBBER (Mobile App Bar, Page Scrubber, Theme Cycle)
 *   [2] WORKSPACE YAŞAM DÖNGÜSÜ (Open/Close, Morph Opening, Header & Backdrops)
 *   [3] BAĞLAMSAL AI SOHBET MOTORU (Streaming, Typewriter, Auto-load Full Book)
 *   [4] MOBIL DOKUNMATIK JESTLER (Velocity Drag Bottom Sheet, Touch Gestures)
 *   [5] ÇİFT SAYFALI GÖRÜNÜM (Two-Page Spread Mode & Spread Geometry)
 *   [6] MOZILLA PDF.JS SELECTION STABILIZATION (Caret Balancer, EndOfContent)
 *   [7] SANALLAŞTIRILMIŞ PDF RENDERER (Virtual DOM, Pre-fetching, Zoom/Fit)
 *   [8] ANOTASYON & VURGU SİSTEMİ (Inline Highlights, Sticky Notes, Floating Bar)
 *   [9] DOKÜMAN İÇİ ARAMA (Ctrl+F In-Document Search Scanner & Highlights)
 *   [10] İÇİNDEKİLER (TOC), METİN OKUMA (TTS) & PKM DIŞA AKTARIM
 *   [11] CHROMAGUARD™ AKILLI GECE YÜZEYİ (Smart OLED Inversion with Figure Preservation)
 *   [12] INSTANT LAN HANDOFF (30-Günlük Kesintisiz QR Passkey Geçiş Sistemi)
 * ════════════════════════════════════════════════════════════════════════════════ */

    let activeWorkspaceBook = null;
    let isWorkspaceChatLoading = false;
    let isFullBookLoaded = false;
    let activeTypewriterTimer = null;
    let activeTypewriterFullText = '';
    let activeTypewriterContainer = null;
    let isSpeaking = false;
    let workspaceSessionToken = 0;
    let currentPdfLoadingTask = null;
    let pdfRenderGeneration = 0;
    let isDocReaderMode = false;
    let docReaderPages = [];
    let docReaderFormat = 'pdf';

    function isMobileReaderViewport() {
      return window.innerWidth <= 860;
    }
    window.isMobileReaderViewport = isMobileReaderViewport;

    function handleWorkspaceEscape() {
      const exportMenu = document.getElementById('workspace-export-menu');
      if (exportMenu && exportMenu.style.display === 'block') {
        exportMenu.style.display = 'none';
        return true;
      }
      const appearanceSheet = document.getElementById('mobile-appearance-sheet');
      if (appearanceSheet && appearanceSheet.classList.contains('open')) {
        toggleMobileAppearanceSheet();
        return true;
      }
      if (typeof isPdfSearchOpen !== 'undefined' && isPdfSearchOpen) {
        closePdfSearch({ restoreFocus: true });
        return true;
      }
      const tocSidebar = document.getElementById('pdf-toc-sidebar');
      if (tocSidebar && tocSidebar.classList.contains('open')) {
        toggleTocSidebar();
        return true;
      }
      const notesSidebar = document.getElementById('pdf-notes-sidebar');
      if (notesSidebar && notesSidebar.classList.contains('open')) {
        toggleNotesSidebar();
        return true;
      }
      const chatPane = document.getElementById('workspace-chat-pane');
      if (isMobileReaderViewport() && chatPane && !chatPane.classList.contains('collapsed')) {
        toggleWorkspaceChatPane();
        return true;
      }
      const floatingBar = document.getElementById('pdf-floating-bar');
      if (floatingBar && floatingBar.classList.contains('active')) {
        clearSelection();
        return true;
      }
      return false;
    }
    window.handleWorkspaceEscape = handleWorkspaceEscape;

    function syncPageIndicatorUI() {
      const pageInput = document.getElementById('pdf-page-num');
      if (pageInput) pageInput.value = pdfPageNum;
      const countEl = document.getElementById('pdf-page-count');
      if (countEl) countEl.textContent = pdfPageCount || '-';
      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageCount > 0 ? pdfPageNum >= pdfPageCount : true);

      const scrubPage = document.getElementById('mobile-scrub-page');
      const scrubTotal = document.getElementById('mobile-scrub-total');
      if (scrubPage) scrubPage.textContent = pdfPageNum;
      if (scrubTotal) scrubTotal.textContent = pdfPageCount || '-';
    }
    window.syncPageIndicatorUI = syncPageIndicatorUI;

    function promptMobilePageJump() {
      const input = prompt(`Gitmek istediğiniz sayfa numarasını girin (1 - ${pdfPageCount || 1}):`, String(pdfPageNum || 1));
      if (!input) return;
      const p = Number.parseInt(input, 10);
      if (!Number.isNaN(p) && p >= 1 && p <= pdfPageCount) {
        jumpToPdfPage(p);
      }
    }
    window.promptMobilePageJump = promptMobilePageJump;

    const READER_SURFACES = ['normal', 'sepia', 'eink', 'chromaguard'];
    function cycleMobileTheme() {
      const idx = READER_SURFACES.indexOf(currentReaderSurfaceMode);
      const nextMode = READER_SURFACES[(idx + 1) % READER_SURFACES.length];
      setReaderSurfaceMode(nextMode);
      if (typeof showToast === 'function') {
        const names = { normal: 'Gündüz', sepia: 'Sepya Kağıt', eink: 'E-Ink', chromaguard: 'Akıllı Gece' };
        showToast(`Tema: ${names[nextMode]}`, 'info');
      }
    }
    window.cycleMobileTheme = cycleMobileTheme;

    function toggleMobileAppearanceSheet() {
      const sheet = document.getElementById('mobile-appearance-sheet');
      const backdrop = document.getElementById('mobile-appearance-backdrop');
      if (!sheet) return;
      const isOpen = sheet.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('active', isOpen);
    }
    window.toggleMobileAppearanceSheet = toggleMobileAppearanceSheet;

    function setupImmersiveMobileReaderToggle() {
      const container = document.getElementById('pdf-canvas-container');
      if (!container || container.dataset.tapToggleBound) return;
      container.dataset.tapToggleBound = 'true';

      let hasScrolled = false;

      container.addEventListener('touchstart', () => {
        hasScrolled = false;
      }, { passive: true });

      container.addEventListener('touchmove', () => {
        hasScrolled = true;
      }, { passive: true });

      container.addEventListener('click', (e) => {
        if (!isMobileReaderViewport()) return;
        if (hasScrolled) return;
        if (e.target.closest('button') || e.target.closest('a') || e.target.closest('input') ||
            e.target.closest('#pdf-floating-bar') || e.target.closest('.sticky-note-marker') ||
            e.target.closest('#pdf-search-bar') || e.target.closest('.pdf-notes-sidebar') ||
            e.target.closest('.pdf-toc-sidebar') || e.target.closest('.workspace-chat-pane') ||
            e.target.closest('.mobile-appearance-sheet')) {
          return;
        }
        const sel = window.getSelection();
        if (sel && sel.toString().trim().length > 0) return;

        const reader = document.getElementById('workspace-reader');
        if (reader) {
          reader.classList.toggle('controls-hidden');
        }
      });
    }

    function jumpToPdfPage(pageNum) {
      const p = Number.parseInt(pageNum, 10);
      if (!p || Number.isNaN(p)) return;
      if (!pdfDoc && !isDocReaderMode) {
        pdfPageNum = p;
        return;
      }
      if (p < 1 || p > pdfPageCount) {
        if (typeof showToast === 'function') showToast(`Geçersiz sayfa numarası: ${pageNum}`, 'warning');
        return;
      }
      const prevPage = pdfPageNum;
      pdfPageNum = p;
      syncPageIndicatorUI();

      const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
      if (pdfDoc) {
        void renderPdfPageVirtual(p);
      }
      scrollToPage(p, { instant: Math.abs(p - prevPage) > 2 });
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
      banner.classList.remove('error', 'loaded');
      banner.classList.add('loading');
      icon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      title.textContent = 'Kitap metni AI oturumuna yükleniyor...';
      subtitle.textContent = 'Oturum oluşturuluyor (yalnızca ilk defaya mahsustur)';
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Hazırlanıyor';
      
      try {
        const response = await apiFetch(`/api/workspace/load-book/${activeWorkspaceBook.hash}`, {
          method: 'POST'
        });
        const data = response ? await response.json() : {};
        
        if (response?.ok && data.success) {
          isFullBookLoaded = true;
          banner.classList.remove('loading', 'error');
          banner.classList.add('loaded');
          icon.innerHTML = '<i class="fas fa-circle-check"></i>';
          const charK = Math.max(1, Math.round((data.char_count || 0) / 1000));
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
          subtitle.textContent = data.error || data.detail || 'Bilinmeyen hata';
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';
          
          setTimeout(() => {
            banner.classList.remove('error');
            resetBannerState();
          }, 5000);
        }
      } catch (err) {
        console.warn('loadFullBookToAI hatası:', err);
        banner.classList.remove('loading');
        banner.classList.add('error');
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

    function openWorkspace(book, initialPage = null, opts = {}) {
      if (!book) return;
      const mySession = ++workspaceSessionToken;
      activeWorkspaceBook = book;
      
      // Reset copy chat button if active
      resetCopyButtonUI();
      
      // Sync meta text and cover slot
      document.getElementById('workspace-book-cat').textContent = book.category || 'Belge';
      document.getElementById('workspace-book-title').textContent = book.title || 'İsimsiz';
      const mobTitle = document.getElementById('mobile-reader-book-title');
      if (mobTitle) mobTitle.textContent = book.title || 'İsimsiz Eser';

      document.title = `${book.title || 'İsimsiz Eser'} — Kütüphanem`;
      const coverSlot = document.getElementById('workspace-cover-slot');
      if (coverSlot) {
        const coverSrc = typeof window.getBookCoverUrl === 'function'
          ? window.getBookCoverUrl(book.hash)
          : `/thumbnails/${book.hash}.jpg`;
        coverSlot.innerHTML = book.has_cover
          ? `<img src="${coverSrc}" alt="${esc(book.title || '')}">`
          : `<i class="fas fa-book-open" style="font-size:0.75rem; color:var(--muted);"></i>`;
      }
      
      // Reset banner
      resetBannerState();

      // Open overlay & establish exact layout geometry BEFORE initializing viewer (ensures accurate Fit-Width measurement)
      const readerEl = document.getElementById('workspace-reader');
      const isMobileDevice = isMobileReaderViewport();
      readerEl.classList.add('open');
      readerEl.classList.remove('controls-hidden');
      readerEl.classList.toggle('is-mobile-reader', isMobileDevice);
      document.body.classList.add('modal-open');

      if (!opts.viaViewTransition) {
        readerEl.classList.add('workspace-entering');
        setTimeout(() => readerEl.classList.remove('workspace-entering'), 460);
      } else {
        readerEl.classList.remove('workspace-entering');
      }

      // On mobile viewports, start in immersive reading mode with bottom sheet chat collapsed
      const cp = document.getElementById('workspace-chat-pane');
      const tb = document.getElementById('btn-toggle-workspace-chat');
      const lbl = document.getElementById('workspace-chat-toggle-label');
      const backdrop = document.getElementById('mobile-chat-backdrop');
      const resizeHandle = document.getElementById('workspace-resize-handle');
      if (isMobileDevice) {
        if (cp) {
          cp.classList.add('collapsed');
          cp.style.flex = '';
          cp.style.width = '';
          cp.style.minWidth = '';
          cp.style.maxWidth = '';
        }
        const pdfPane = document.getElementById('workspace-pdf-pane');
        if (pdfPane) pdfPane.style.flex = '';
        if (tb) tb.classList.remove('active');
        if (lbl) lbl.textContent = 'AI';
        if (backdrop) backdrop.classList.remove('active');
        if (resizeHandle) resizeHandle.style.display = 'none';
      } else if (resizeHandle) {
        resizeHandle.style.display = cp?.classList.contains('collapsed') ? 'none' : 'flex';
      }

      setupImmersiveMobileReaderToggle();

      // Load PDF / EPUB / TXT via custom interactive reader AFTER layout is live
      initCustomPdfViewer(book, initialPage, mySession);

      // Load previous persistent chat history from server if exists
      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.innerHTML = `
        <div class="chat-msg chat-ai">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">Merhaba! Şu anda <strong>${esc(book.title)}</strong> eseri üzerinde konuşmaya hazırız. Kitabın ana fikirleri, terimleri veya sormak istediğiniz kısımları hakkında sorular sorabilirsiniz.</div>
        </div>
      `;

      apiFetch(`/api/workspace/chat-history/${book.hash}`)
        .then(res => (res && res.ok) ? res.json() : null)
        .then(data => {
          if (mySession !== workspaceSessionToken) return;
          applyWorkspaceChatHistory(data, chatMessages);
        })
        .catch(err => {
          console.debug('Chat history load error:', err);
        });
      
      // Focus textarea on desktop only when chat pane is expanded
      setTimeout(() => {
        if (mySession !== workspaceSessionToken) return;
        if (!isMobileReaderViewport() && cp && !cp.classList.contains('collapsed')) {
          const textarea = document.getElementById('workspace-chat-input');
          if (textarea) textarea.focus({ preventScroll: true });
        }
      }, 280);
    }

    function openBookWithMorph(cardOrCover, book, initialPage = null) {
      let originArg = cardOrCover;
      let bookArg = book;
      if (typeof cardOrCover === 'string' && (!book || book instanceof HTMLElement)) {
        const hashStr = cardOrCover;
        originArg = book instanceof HTMLElement ? book : document.querySelector(`.book-card[data-hash="${hashStr}"]`);
        bookArg = (typeof allBooks !== 'undefined' ? allBooks.find(b => b.hash === hashStr) : null);
      }

      const targetBook = bookArg || (typeof allBooks !== 'undefined' ? allBooks.find(b => b.hash === originArg?.dataset?.hash) : null);
      if (!targetBook) return;

      const readerEl = document.getElementById('workspace-reader');
      const modalEl = document.getElementById('modal');
      const fromOpenModal = Boolean(modalEl && modalEl.classList.contains('open'));
      let originTarget = originArg;
      if (fromOpenModal && !(originTarget instanceof HTMLElement)) {
        originTarget = modalEl.querySelector('.modal-cover-wrap');
      }

      // Okuyucu kapatıldığında odağı tetikleyiciye veya eşleşen kitap kartına geri döndür
      if (readerEl) {
        const returnCandidate = fromOpenModal
          ? (modalEl._sourceTriggerEl || document.querySelector(`.book-card[data-hash="${targetBook.hash}"]`))
          : ((originArg instanceof HTMLElement && originArg.isConnected)
            ? (originArg.closest('button, .shelf-item, .book-card') || originArg)
            : (document.activeElement instanceof HTMLElement ? document.activeElement : null));
        readerEl._returnFocusEl = returnCandidate;
      }

      const card = (originTarget instanceof HTMLElement)
        ? (originTarget.closest('.book-card, .shelf-item, .modal-editorial-layout, .modal-layout') || originTarget)
        : document.querySelector(`.book-card[data-hash="${targetBook.hash}"]`);
      const cover = card ? (card.querySelector('.card-cover, .shelf-item-cover, .modal-cover-wrap') || card) : null;

      const dismissOpenModalImmediate = () => {
        if (!fromOpenModal || !modalEl) return;
        modalEl.removeEventListener('keydown', window._modalTabTrapHandler);
        if (typeof window._clearModalFocusEntry === 'function') {
          window._clearModalFocusEntry(modalEl);
        } else if (typeof window.releaseModalFocus === 'function') {
          window.releaseModalFocus(modalEl, { restore: false });
        }
        modalEl.classList.remove('open', 'closing');
        modalEl.style.display = '';
        modalEl._sourceTriggerEl = null;
        window.currentModalHash = null;
      };

      const canUseViewTransition = Boolean(
        cover &&
        cover.offsetParent !== null &&
        document.startViewTransition &&
        window.Motion &&
        typeof window.Motion.transition === 'function' &&
        !(typeof window.isMotionReduced === 'function' && window.isMotionReduced())
      );

      const enterReader = () => {
        if (fromOpenModal) {
          dismissOpenModalImmediate();
        }
        openWorkspace(targetBook, initialPage, { viaViewTransition: canUseViewTransition });
      };

      if (canUseViewTransition) {
        void window.Motion.transition(enterReader, {
          name: 'book-cover',
          fromEl: cover,
          toEl: () => document.getElementById('workspace-cover-slot')
        });
      } else {
        enterReader();
      }
    }
    window.openBookWithMorph = openBookWithMorph;

    function closeWorkspace() {
      ++workspaceSessionToken;
      const readerEl = document.getElementById('workspace-reader');
      const currentBook = activeWorkspaceBook;
      const returnEl = readerEl?._returnFocusEl || null;

      const doClose = () => {
        if (readerEl) readerEl.classList.remove('open', 'workspace-entering', 'controls-hidden');
        const anyModal = document.querySelector('.modal-overlay.open, .modal-overlay.closing, .logs-modal.open');
        if (!anyModal) {
          document.body.classList.remove('modal-open');
        }
        document.title = 'Kütüphanem';

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
          ttsBtn.innerHTML = '<i class="fas fa-volume-high"></i> <span class="pdf-btn-label">Dinle</span>';
        }

        cleanupCustomPdfViewer();

        activeWorkspaceBook = null;
        isFullBookLoaded = false;
      };

      const restoreFocus = () => {
        if (readerEl) readerEl._returnFocusEl = null;
        const fallbackCard = currentBook ? document.querySelector(`.book-card[data-hash="${currentBook.hash}"]`) : null;
        const focusTarget = (returnEl && returnEl.isConnected && returnEl.offsetParent !== null)
          ? returnEl
          : ((fallbackCard && fallbackCard.offsetParent !== null) ? fallbackCard : null);
        if (focusTarget && typeof focusTarget.focus === 'function') {
          focusTarget.focus({ preventScroll: true });
        }
      };

      doClose();
      restoreFocus();
    }

    function handleWorkspaceChatKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void sendWorkspaceMessage();
      } else if (e.key === 'Escape') {
        const chatPane = document.getElementById('workspace-chat-pane');
        if (chatPane && !chatPane.classList.contains('collapsed')) {
          e.preventDefault();
          e.stopPropagation();
          e.target.blur();
          toggleWorkspaceChatPane();
        }
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
    let lastChatFlex = null;
    let lastPdfFlex = null;

    document.addEventListener('DOMContentLoaded', () => {
      const handle = document.getElementById('workspace-resize-handle');
      const pdfPane = document.getElementById('workspace-pdf-pane');
      const chatPane = document.getElementById('workspace-chat-pane');
      const reader = document.getElementById('workspace-reader');
      
      if (!handle || !pdfPane || !chatPane) return;
      
      let isDragging = false;
      
      const onMouseDown = (e) => {
        isDragging = true;
        handle.classList.add('active');
        if (reader) reader.classList.add('is-resizing');
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
        // Limit: PDF pane minimum 380px or 28%, Chat pane min 280px or 20%
        const minPdfPercent = Math.max(25, (380 / totalWidth) * 100);
        const maxPdfPercent = Math.min(80, ((totalWidth - 300) / totalWidth) * 100);
        const leftWidthPercent = Math.max(minPdfPercent, Math.min(maxPdfPercent, (clientX / totalWidth) * 100));
        
        const pdfF = leftWidthPercent / 100;
        const chatF = (100 - leftWidthPercent) / 100;
        pdfPane.style.flex = `${pdfF} 1 0px`;
        chatPane.style.flex = `${chatF} 1 0px`;
        chatPane.style.width = 'auto';
        chatPane.style.minWidth = '280px';
        lastPdfFlex = pdfPane.style.flex;
        lastChatFlex = chatPane.style.flex;
      };
      
      const onMouseUp = () => {
        if (!isDragging) return;
        isDragging = false;
        handle.classList.remove('active');
        if (reader) reader.classList.remove('is-resizing');
        document.body.style.cursor = '';
        document.getElementById('iframe-drag-mask')?.remove();
        if (pdfDoc && (pdfIsFitWidth || pdfIsFitHeight) && typeof resizeAllPagesForZoom === 'function') {
          resizeAllPagesForZoom();
        }
        window.dispatchEvent(new Event('resize'));
      };
      
      handle.addEventListener('mousedown', onMouseDown);
      handle.addEventListener('touchstart', onMouseDown, { passive: true });
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('touchmove', onMouseMove, { passive: true });
      
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchend', onMouseUp);

      // Double-click to reset split-pane to default clean ratio
      handle.addEventListener('dblclick', () => {
        pdfPane.style.flex = '1 1 0px';
        chatPane.style.flex = '0 0 380px';
        chatPane.style.width = '380px';
        lastPdfFlex = null;
        lastChatFlex = null;
        if (pdfDoc && (pdfIsFitWidth || pdfIsFitHeight) && typeof resizeAllPagesForZoom === 'function') {
          resizeAllPagesForZoom();
        }
        window.dispatchEvent(new Event('resize'));
      });

      // Enable horizontal mouse wheel scroll on the pdf toolbar
      const toolbar = document.querySelector('.pdf-toolbar');
      if (toolbar) {
        toolbar.addEventListener('wheel', (e) => {
          if (e.deltaY !== 0 && toolbar.scrollWidth > toolbar.clientWidth) {
            e.preventDefault();
            toolbar.scrollLeft += (e.deltaY * 0.85);
          }
        }, { passive: false });
      }
    });

    let workspaceChatPaneTimer = null;

    function _refitReaderAfterChatToggle(prevScrollRatio) {
      const container = document.getElementById('pdf-canvas-container');
      const applyScrollRatio = () => {
        if (container && prevScrollRatio > 0 && container.scrollHeight > container.clientHeight) {
          container.scrollTop = Math.round(prevScrollRatio * (container.scrollHeight - container.clientHeight));
        }
      };
      if (pdfDoc && (pdfIsFitWidth || pdfIsFitHeight) && typeof resizeAllPagesForZoom === 'function') {
        resizeAllPagesForZoom();
        setTimeout(() => requestAnimationFrame(applyScrollRatio), 90);
      } else {
        requestAnimationFrame(applyScrollRatio);
      }
      window.dispatchEvent(new Event('resize'));
    }

    function toggleWorkspaceChatPane() {
      const chatPane = document.getElementById('workspace-chat-pane');
      const pdfPane = document.getElementById('workspace-pdf-pane');
      const resizeHandle = document.getElementById('workspace-resize-handle');
      const toggleBtn = document.getElementById('btn-toggle-workspace-chat');
      const label = document.getElementById('workspace-chat-toggle-label');
      const backdrop = document.getElementById('mobile-chat-backdrop');
      const scrollContainer = document.getElementById('pdf-canvas-container');
      if (!chatPane) return;

      if (workspaceChatPaneTimer) {
        clearTimeout(workspaceChatPaneTimer);
        workspaceChatPaneTimer = null;
      }

      const prevScrollRatio = (scrollContainer && scrollContainer.scrollHeight > scrollContainer.clientHeight)
        ? scrollContainer.scrollTop / (scrollContainer.scrollHeight - scrollContainer.clientHeight)
        : 0;
      const isCurrentlyCollapsed = chatPane.classList.contains('collapsed') || chatPane.classList.contains('m-exit');
      const isCollapsed = !isCurrentlyCollapsed;
      const isMobile = window.innerWidth <= 860 || document.getElementById('workspace-reader')?.classList.contains('is-mobile-reader');
      const reduced = window.Motion && typeof window.Motion.reduced === 'function' && window.Motion.reduced();

      if (backdrop) {
        backdrop.classList.toggle('active', !isCollapsed && isMobile);
      }

      if (resizeHandle) {
        resizeHandle.style.display = (isCollapsed || isMobile) ? 'none' : 'flex';
      }
      if (toggleBtn) {
        toggleBtn.classList.toggle('active', !isCollapsed);
        toggleBtn.setAttribute('aria-expanded', String(!isCollapsed));
        toggleBtn.title = isCollapsed ? 'AI Asistan Panelini Aç' : 'AI Asistan Panelini Gizle (Odaklı Okuma)';
      }
      if (label) {
        if (isCollapsed) {
          label.textContent = isMobile ? 'AI' : 'AI Aç';
        } else {
          label.textContent = 'AI Paneli';
        }
      }

      const applyDesktopExpandedLayout = () => {
        if (isMobile) {
          chatPane.style.flex = '';
          chatPane.style.width = '';
          chatPane.style.minWidth = '';
          chatPane.style.maxWidth = '';
          if (pdfPane) pdfPane.style.flex = '';
        } else if (pdfPane) {
          chatPane.style.maxWidth = '800px';
          chatPane.style.minWidth = '280px';
          if (lastPdfFlex && lastChatFlex) {
            pdfPane.style.flex = lastPdfFlex;
            chatPane.style.flex = lastChatFlex;
            chatPane.style.width = 'auto';
          } else {
            pdfPane.style.flex = '1 1 0px';
            chatPane.style.flex = '0 0 380px';
            chatPane.style.width = '380px';
          }
        }
      };

      const applyCollapsedLayout = () => {
        chatPane.classList.add('collapsed');
        chatPane.classList.remove('m-exit', 'm-enter');
        if (isMobile) {
          chatPane.style.flex = '';
          chatPane.style.width = '';
          chatPane.style.minWidth = '';
          chatPane.style.maxWidth = '';
          if (pdfPane) pdfPane.style.flex = '';
        } else if (pdfPane) {
          if (chatPane.style.flex && chatPane.style.flex !== '0 0 0px') {
            lastChatFlex = chatPane.style.flex;
            lastPdfFlex = pdfPane.style.flex;
          }
          chatPane.style.flex = '0 0 0px';
          chatPane.style.width = '0px';
          chatPane.style.minWidth = '0px';
          chatPane.style.maxWidth = '0px';
          pdfPane.style.flex = '1 1 100%';
        }
        _refitReaderAfterChatToggle(prevScrollRatio);
        if (toggleBtn && toggleBtn.isConnected && typeof toggleBtn.focus === 'function') {
          toggleBtn.focus({ preventScroll: true });
        }
      };

      if (!isCollapsed) {
        chatPane.classList.remove('collapsed', 'm-exit');
        applyDesktopExpandedLayout();
        const chatInput = document.getElementById('workspace-chat-input');
        if (!isMobile && window.Motion && typeof window.Motion.enter === 'function') {
          void window.Motion.enter(chatPane, {
            className: 'm-enter',
            origin: 'right center',
            cleanExitClass: 'm-exit',
            focusEl: chatInput
          });
        } else {
          chatPane.style.transformOrigin = isMobile ? 'bottom center' : 'right center';
          if (chatInput) {
            setTimeout(() => chatInput.focus({ preventScroll: true }), reduced ? 20 : 220);
          }
        }
        workspaceChatPaneTimer = setTimeout(() => {
          workspaceChatPaneTimer = null;
          _refitReaderAfterChatToggle(prevScrollRatio);
        }, reduced ? 16 : 240);
      } else if (!isMobile && window.Motion && typeof window.Motion.exit === 'function') {
        chatPane.style.transformOrigin = 'right center';
        void window.Motion.exit(chatPane, {
          className: 'm-exit',
          afterFn: applyCollapsedLayout
        });
      } else {
        applyCollapsedLayout();
      }
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
        if (!isMobileReaderViewport()) return;
        if (e.target.closest('button') || e.target.closest('a')) return;
        if (chatPane.classList.contains('collapsed')) return;
        startY = e.touches[0].clientY;
        currentY = startY;
        startTime = Date.now();
        isDragging = true;
        chatPane.style.transition = 'none';
      }, { passive: true });

      window.addEventListener('touchmove', (e) => {
        if (!isDragging || !isMobileReaderViewport()) return;
        currentY = e.touches[0].clientY;
        const deltaY = currentY - startY;
        if (deltaY > 0) {
          chatPane.style.transform = `translateY(${deltaY}px)`;
        }
      }, { passive: true });

      window.addEventListener('touchend', () => {
        if (!isDragging || !isMobileReaderViewport()) return;
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
      if (pdfDoc && pdfIsFitWidth) {
        resizeAllPagesForZoom();
      } else {
        checkVisiblePagesAndRender();
      }
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
      if (!container || (!pdfDoc && !isDocReaderMode) || pdfPageCount === 0) return;

      const isWide = !isMobileReaderViewport();
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
        scrollToPage(pdfPageNum, { instant: true });
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

      // Pointer down: initiate smart geometric selection ONLY for mouse/pen margin drags
      // (Touch events pass through untouched for 60fps native touch scrolling, pinch & tap-to-toggle;
      // direct span clicks pass through for native double-click word & triple-click paragraph selection!)
      document.addEventListener("pointerdown", (evt) => {
        if (evt.pointerType === 'touch') return;
        if (evt.button !== 0 && evt.button !== undefined) return;
        if (isDocReaderMode) return;

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

        // Allow native double/triple-click word/paragraph selection and direct span selection
        if (evt.detail > 1 || evt.target.closest('.textLayer span') || evt.target.closest('.doc-reader-sheet')) {
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

        // Margin/whitespace click: anchor cleanly at nearest line edge without full-page selection bleed
        evt.preventDefault();

        selectionDragState = {
          startX: evt.clientX,
          startY: evt.clientY,
          anchorNode: hit.node,
          anchorOffset: hit.offset,
          anchorTextLayer: textLayer,
          anchorPageWrapper: pageWrapper,
          anchorLineIdx: hit.lineIdx,
          isDragging: false,
          isMarginStart: true
        };

        const sel = window.getSelection();
        try {
          sel.collapse(hit.node, hit.offset);
        } catch (_) {}
      }, { signal });

      // Pointer move: update selection with geometric clamping for margin-initiated drags
      document.addEventListener("pointermove", (evt) => {
        if (!selectionDragState) return;

        const dx = evt.clientX - selectionDragState.startX;
        const dy = evt.clientY - selectionDragState.startY;
        const dist = Math.hypot(dx, dy);

        if (!selectionDragState.isDragging && dist < 4) {
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
        } catch (_) {}
      }, { signal });

      // Pointer up: complete selection and position floating action bar
      document.addEventListener("pointerup", () => {
        if (selectionDragState) {
          if (selectionDragState.isDragging) {
            handleTextSelection();
          } else {
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

      // selectionchange: Mozilla PDF.js endOfContent stabilizer for native span/word/touch selection
      document.addEventListener("selectionchange", () => {
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

    function computeFitWidthScale(baseWidth, container) {
      const isMobile = isMobileReaderViewport();
      const padding = isMobile ? 12 : 48;
      const useSpread = pdfIsSpreadMode && !isMobile && pdfPageCount > 1;
      const totalAvail = Math.max(240, container.clientWidth - padding);
      const perPageAvail = useSpread ? Math.max(200, (totalAvail - 20) / 2) : totalAvail;
      return Math.max(0.3, Math.min(4.0, perPageAvail / baseWidth));
    }

    // Initialize custom PDF.js reader for the loaded book
    function setupPdfPages(firstPage, container) {
      let viewport = firstPage.getViewport({ scale: 1.0 });
      const isMobile = isMobileReaderViewport();

      if (isMobile) {
        pdfIsFitWidth = true;
      }

      if (pdfIsFitWidth) {
        pdfScale = computeFitWidthScale(viewport.width, container);
        updateZoomLabel();
      } else if (pdfIsFitHeight) {
        const containerHeight = Math.max(300, container.clientHeight - 64);
        pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
        updateZoomLabel();
      }

      viewport = firstPage.getViewport({ scale: pdfScale });
      const cssW = Math.max(1, Math.round(viewport.width));
      const cssH = Math.max(1, Math.round(viewport.height));

      const frag = document.createDocumentFragment();
      for (let p = 1; p <= pdfPageCount; p++) {
        const pageWrapper = document.createElement('div');
        pageWrapper.className = 'pdf-page-wrapper';
        pageWrapper.id = `pdf-page-wrapper-${p}`;
        pageWrapper.dataset.pageNumber = p;
        pageWrapper.dataset.pageNum = p;
        pageWrapper.style.width = `${cssW}px`;
        pageWrapper.style.height = `${cssH}px`;
        pageWrapper.style.minHeight = `${cssH}px`;
        pageWrapper.style.flexShrink = '0';
        pageWrapper.style.position = 'relative';

        const textLayer = document.createElement('div');
        textLayer.className = 'textLayer';
        textLayer.id = `textLayer-${p}`;
        textLayer.style.width = `${cssW}px`;
        textLayer.style.height = `${cssH}px`;
        textLayer.style.setProperty('--scale-factor', String(viewport.scale));
        pageWrapper.appendChild(textLayer);

        const highlightLayer = document.createElement('div');
        highlightLayer.className = 'pdf-highlight-layer';
        highlightLayer.id = `pdf-highlight-layer-${p}`;
        highlightLayer.style.width = `${cssW}px`;
        highlightLayer.style.height = `${cssH}px`;
        pageWrapper.appendChild(highlightLayer);

        frag.appendChild(pageWrapper);
      }
      container.appendChild(frag);

      if (pdfIsSpreadMode && !isMobileReaderViewport()) {
        applySpreadLayout();
      }

      if (pdfPageNum > pdfPageCount) {
        pdfPageNum = pdfPageCount;
        syncPageIndicatorUI();
      }

      void renderPdfPageVirtual(pdfPageNum);

      requestAnimationFrame(() => {
        if (pdfPageNum > 1) {
          scrollToPage(pdfPageNum, { instant: true });
        }
        checkVisiblePagesAndRender();
      });
    }

    async function setupLoadedPdf(pdf, book, container, mySession) {
      if (mySession !== undefined && mySession !== workspaceSessionToken) {
        try { pdf.destroy(); } catch (_) {}
        return;
      }
      pdfDoc = pdf;
      pdfPageCount = pdf.numPages;
      if (pdfPageNum > pdfPageCount) {
        pdfPageNum = Math.max(1, pdfPageCount);
      }

      syncPageIndicatorUI();
      syncBookTotalPagesIfNeeded(book, pdfPageCount);

      loadPdfOutline(pdf).catch(err => console.debug("loadPdfOutline error:", err));

      if (container) {
        container.innerHTML = "";
        try {
          const firstPage = await pdf.getPage(1);
          if (mySession !== undefined && mySession !== workspaceSessionToken) return;
          setupPdfPages(firstPage, container);
        } catch (err) {
          console.error("PDF getPage(1) hatası:", err);
        }
      }

      renderNotesSidebar();
    }

    // --- [D2: PDF Pre-Fetching & Streaming Config] ---
    const PDFJS_CDN_BASE = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';
    const pdfPrefetchCache = new Map();

    function buildPdfDocumentParams(pdfUrl) {
      return {
        url: pdfUrl,
        cMapUrl: `${PDFJS_CDN_BASE}cmaps/`,
        cMapPacked: true,
        standardFontDataUrl: `${PDFJS_CDN_BASE}standard_fonts/`,
        disableAutoFetch: true,
        disableStream: false,
        rangeChunkSize: 65536
      };
    }

    function prefetchPdfDocument(hash) {
      if (!hash || !window.pdfjsLib || pdfPrefetchCache.has(hash)) return;
      const bookObj = (window.allBooks || []).find(b => b.hash === hash);
      const fname = String(bookObj?.file || bookObj?.dosya_adi || '').toLowerCase();
      if (fname && !fname.endsWith('.pdf')) return;

      // Bound prefetch cache to max 3 idle documents to keep memory lean
      if (pdfPrefetchCache.size >= 3) {
        const oldestKey = pdfPrefetchCache.keys().next().value;
        const oldest = pdfPrefetchCache.get(oldestKey);
        if (oldest?.cleanupTimer) clearTimeout(oldest.cleanupTimer);
        try { oldest?.task?.destroy(); } catch (_) {}
        pdfPrefetchCache.delete(oldestKey);
      }

      const pdfUrl = `/api/download/${hash}`;
      try {
        const loadingTask = window.pdfjsLib.getDocument(buildPdfDocumentParams(pdfUrl));
        loadingTask.promise.catch(() => {
          pdfPrefetchCache.delete(hash);
        });
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
      if (item?.cleanupTimer) clearTimeout(item.cleanupTimer);
      if (item) {
        item.cleanupTimer = setTimeout(() => {
          try { item.task.destroy(); } catch (_) {}
          pdfPrefetchCache.delete(hash);
        }, 1500);
      }
    }
    window.cancelPdfPrefetch = cancelPdfPrefetch;

    function renderDocBlockHtml(blk) {
      const text = esc(blk?.text || '');
      if (!text) return '';
      const tag = String(blk?.tag || 'p').toLowerCase();
      if (tag === 'h1' || tag === 'h2') return `<h2 class="doc-heading-1">${text}</h2>`;
      if (tag === 'h3' || tag === 'h4') return `<h3 class="doc-heading-2">${text}</h3>`;
      if (tag === 'blockquote') return `<blockquote class="doc-quote">${text}</blockquote>`;
      if (tag === 'pre') return `<pre class="doc-pre">${text}</pre>`;
      if (tag === 'li') return `<p class="doc-list-item">• ${text}</p>`;
      return `<p class="doc-para">${text}</p>`;
    }

    function setupStructuredDocReader(data, book, container, mySession) {
      if (mySession !== undefined && mySession !== workspaceSessionToken) return;
      isDocReaderMode = true;
      docReaderFormat = String(data?.format || 'txt').toLowerCase();
      docReaderPages = Array.isArray(data?.pages) && data.pages.length > 0
        ? data.pages
        : [{ page_num: 1, title: book.title || 'Belge', blocks: [{ tag: 'p', text: 'Belge içeriği boş.' }] }];
      pdfDoc = null;
      pdfPageCount = docReaderPages.length;
      pdfScale = 1.0;
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      if (pdfPageNum > pdfPageCount) {
        pdfPageNum = Math.max(1, pdfPageCount);
      }

      updateZoomLabel();
      syncPageIndicatorUI();
      syncBookTotalPagesIfNeeded(book, pdfPageCount);

      const tocList = document.getElementById('pdf-toc-list');
      if (Array.isArray(data?.toc) && data.toc.length > 0) {
        renderSynthesizedToc(data.toc);
      } else if (tocList) {
        tocList.innerHTML = '<div class="pdf-notes-empty">Bu belgede içindekiler tablosu bulunamadı.</div>';
      }

      if (container) {
        container.innerHTML = '';
        container.style.setProperty('--doc-font-scale', String(pdfScale));
        const frag = document.createDocumentFragment();

        docReaderPages.forEach((pg, idx) => {
          const p = Number(pg.page_num) || (idx + 1);
          const pageWrapper = document.createElement('div');
          pageWrapper.className = 'pdf-page-wrapper doc-page-wrapper';
          pageWrapper.id = `pdf-page-wrapper-${p}`;
          pageWrapper.dataset.pageNumber = p;
          pageWrapper.dataset.pageNum = p;
          pageWrapper.style.position = 'relative';

          const textLayer = document.createElement('div');
          textLayer.className = 'textLayer doc-text-layer';
          textLayer.id = `textLayer-${p}`;

          const blocks = Array.isArray(pg.blocks) ? pg.blocks : [];
          const firstBlkText = (blocks[0]?.text || '').trim();
          const showPageTitle = pg.title && pg.title.trim() && pg.title.trim() !== firstBlkText;
          const headerHtml = showPageTitle
            ? `<div class="doc-sheet-kicker">${esc(pg.title)}</div>`
            : '';
          const bodyHtml = blocks.map(renderDocBlockHtml).join('');

          textLayer.innerHTML = `
            <article class="doc-reader-sheet" data-format="${esc(docReaderFormat)}">
              ${headerHtml}
              <div class="doc-sheet-body">${bodyHtml || '<p class="doc-para"><em>Bu sayfada metin bulunmuyor.</em></p>'}</div>
              <footer class="doc-sheet-footer">Sayfa ${p} / ${pdfPageCount}</footer>
            </article>
          `;
          pageWrapper.appendChild(textLayer);

          const highlightLayer = document.createElement('div');
          highlightLayer.className = 'pdf-highlight-layer';
          highlightLayer.id = `pdf-highlight-layer-${p}`;
          pageWrapper.appendChild(highlightLayer);

          pdfRenderedPages[p] = 'done';
          frag.appendChild(pageWrapper);
        });

        container.appendChild(frag);

        if (pdfIsSpreadMode && !isMobileReaderViewport()) {
          applySpreadLayout();
        }

        Object.keys(pdfHighlights).forEach(pStr => {
          drawPageHighlightsAndNotes(Number(pStr));
        });

        requestAnimationFrame(() => {
          if (pdfPageNum > 1) {
            scrollToPage(pdfPageNum, { instant: true });
          }
        });
      }

      renderNotesSidebar();
    }

    function initCustomPdfViewer(book, initialPage = null, sessionOverride = null) {
      const mySession = sessionOverride !== null ? sessionOverride : workspaceSessionToken;
      ++pdfRenderGeneration;

      // Cancel any previous in-flight PDF loading task immediately
      if (currentPdfLoadingTask) {
        try { currentPdfLoadingTask.destroy(); } catch (_) {}
        currentPdfLoadingTask = null;
      }

      const isMobile = isMobileReaderViewport();
      pdfDoc = null;
      isDocReaderMode = false;
      docReaderPages = [];
      docReaderFormat = 'pdf';
      pdfPageNum = (initialPage && initialPage > 0) ? initialPage : (book.okunulan_sayfa || 1);
      pdfPageCount = 0;
      pdfScale = isMobile ? 1.0 : 1.2;
      pdfIsRendering = false;
      pdfPendingPageNum = null;
      pdfIsFitWidth = isMobile;
      pdfIsFitHeight = false;
      if (isMobile) {
        pdfIsSpreadMode = false;
      }
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
      document.querySelectorAll('.mobile-surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `mob-surface-${currentReaderSurfaceMode}`);
      });

      // Update zoom label to initial
      updateZoomLabel();
      updateSpreadUI();
      document.getElementById('pdf-fit-width-btn')?.classList.toggle('active', pdfIsFitWidth);
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
        .then(res => (res && res.ok) ? res.json() : null)
        .then(data => {
          if (mySession !== workspaceSessionToken) return;
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
            try {
              localStorage.setItem(`lib-highlights-${book.hash}`, JSON.stringify(pdfHighlights));
              localStorage.setItem(`lib-notes-${book.hash}`, JSON.stringify(pdfNotes));
            } catch (_) {}
            renderNotesSidebar();
            Object.keys(pdfHighlights).forEach(pStr => {
              const pNum = Number(pStr);
              if (pdfRenderedPages[pNum] === 'done') {
                drawPageHighlightsAndNotes(pNum);
              }
            });
          }
        })
        .catch(err => console.warn("API notları yüklenirken hata:", err));

      // Initialize UI controls
      syncPageIndicatorUI();
      
      const emptyDiv = `<div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>`;
      const notesListEl = document.getElementById('pdf-notes-list');
      if (notesListEl) notesListEl.innerHTML = emptyDiv;

      // Hide floating bar
      hideFloatingBar();

      const pdfUrl = `/api/download/${book.hash}`;
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.removeEventListener('mouseup', handleTextSelection);
        container.removeEventListener('touchend', handleTextSelection);
        container.addEventListener('mouseup', handleTextSelection);
        container.addEventListener('touchend', handleTextSelection);

        const coverSrc = typeof window.getBookCoverUrl === 'function'
          ? window.getBookCoverUrl(book.hash)
          : `/thumbnails/${book.hash}.jpg`;
        container.innerHTML = `
          <div class="reader-skeleton-wrap">
            <div class="reader-skeleton-cover-preview">
              ${book.has_cover ? `<img src="${coverSrc}" alt="">` : '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);"><i class="fas fa-book" style="font-size:2.5rem;"></i></div>'}
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

      // Check file extension: Native paginated structured reader for .epub and .txt
      const bookFilename = String(book.file || book.dosya_adi || "").toLowerCase();
      if (bookFilename.endsWith(".epub") || bookFilename.endsWith(".txt")) {
        apiFetch(`/api/books/${encodeURIComponent(book.hash)}/reader-content`)
          .then(async res => {
            if (!res || !res.ok) {
              throw new Error(`HTTP ${res?.status || 500}`);
            }
            return res.json();
          })
          .then(data => {
            if (mySession !== workspaceSessionToken) return;
            setupStructuredDocReader(data, book, container, mySession);
          })
          .catch(err => {
            if (mySession !== workspaceSessionToken) return;
            console.warn("Structured reader load error:", err);
            if (container) {
              container.innerHTML = `<div style="padding: 2.5rem; text-align: center; color: var(--muted); font-family: 'Geist', sans-serif;"><i class="fas fa-book-open" style="font-size: 2.2rem; margin-bottom: 0.8rem; color: var(--accent); display: block;"></i><strong>${esc(book.title || 'Belge')}</strong><p style="margin-top: 0.5rem; font-size: 0.9rem;">Belge içeriği okunamadı (${esc(err?.message || 'Hata')}). Dosyayı doğrudan indirebilirsiniz.</p><a href="${pdfUrl}" class="btn-import" style="display: inline-block; margin-top: 1rem; text-decoration: none; padding: 0.6rem 1.4rem;" download><i class="fas fa-download"></i> Dosyayı İndir</a></div>`;
            }
          });
        return;
      }

      if (!window.pdfjsLib) {
        console.error("PDF.js kütüphanesi yüklenemedi.");
        return;
      }

      // D2: Use pre-fetched promise if available for zero-latency instant open
      let docPromise = null;
      if (pdfPrefetchCache.has(book.hash)) {
        const cached = pdfPrefetchCache.get(book.hash);
        if (cached?.cleanupTimer) clearTimeout(cached.cleanupTimer);
        currentPdfLoadingTask = cached.task;
        docPromise = cached.promise;
        pdfPrefetchCache.delete(book.hash);
      } else {
        const loadingTask = window.pdfjsLib.getDocument(buildPdfDocumentParams(pdfUrl));
        currentPdfLoadingTask = loadingTask;
        docPromise = loadingTask.promise;
      }

      docPromise
        .then(pdf => {
          currentPdfLoadingTask = null;
          return setupLoadedPdf(pdf, book, container, mySession);
        })
        .catch(function(error) {
          currentPdfLoadingTask = null;
          if (mySession !== workspaceSessionToken) return;
          if (error?.name === 'RenderingCancelledException' || String(error?.message || '').includes('Worker was destroyed')) {
            return;
          }
          console.error("PDF.js yükleme hatası:", error);
          if (container) {
            container.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--muted); font-family: 'Geist', sans-serif;"><i class="fas fa-book-open" style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--accent); opacity: 0.8; display: block;"></i><strong>${esc(book.title || 'Belge')}</strong><p style="margin-top: 0.5rem; font-size: 0.9rem;">Bu belge görüntülenirken hata oluştu. AI Asistanı ile doğrudan soru-cevap yapabilir veya dosyayı indirebilirsiniz.</p><a href="${pdfUrl}" class="btn-import" style="display: inline-block; margin-top: 1rem; text-decoration: none; padding: 0.6rem 1.4rem;" download><i class="fas fa-download"></i> Dosyayı İndir</a></div>`;
          }
        });
    }

    // Free resources and bindings on close
    function cleanupCustomPdfViewer() {
      ++pdfRenderGeneration;
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      pdfRenderedPages = {};
      if (currentPdfLoadingTask) {
        try { currentPdfLoadingTask.destroy(); } catch (_) {}
        currentPdfLoadingTask = null;
      }
      if (pdfDoc && typeof pdfDoc.destroy === 'function') {
        try { pdfDoc.destroy(); } catch (_) {}
      }
      pdfDoc = null;
      isDocReaderMode = false;
      docReaderPages = [];
      hideFloatingBar();
      closePdfSearch();
      pdfSearchTextCache = {};
      if (pdfSearchDebounceTimer) {
        clearTimeout(pdfSearchDebounceTimer);
        pdfSearchDebounceTimer = null;
      }
      if (saveProgressDebounceTimer) {
        clearTimeout(saveProgressDebounceTimer);
        saveProgressDebounceTimer = null;
      }
      if (zoomWillChangeTimer) {
        clearTimeout(zoomWillChangeTimer);
        zoomWillChangeTimer = null;
      }
      if (wheelZoomCommitTimer) {
        clearTimeout(wheelZoomCommitTimer);
        wheelZoomCommitTimer = null;
      }
      wheelFocalState = null;
      wheelBaseScale = null;
      if (resizeSpreadTimer) {
        clearTimeout(resizeSpreadTimer);
        resizeSpreadTimer = null;
      }
      if (workspaceChatPaneTimer) {
        clearTimeout(workspaceChatPaneTimer);
        workspaceChatPaneTimer = null;
      }
      if (copyChatBtnTimeout) {
        clearTimeout(copyChatBtnTimeout);
        copyChatBtnTimeout = null;
      }
      if (selectionCheckTimer) {
        clearTimeout(selectionCheckTimer);
        selectionCheckTimer = null;
      }
      if (selectionChangeAbortController) {
        try { selectionChangeAbortController.abort(); } catch (_) {}
        selectionChangeAbortController = null;
      }
      activeTextLayersMap.clear();
      invalidatePageGeometry();
      selectionDragState = null;
      prevSelectionRange = null;
      isUserSelectingText = false;

      document.getElementById('pdf-notes-sidebar')?.classList.remove('open');
      document.getElementById('pdf-notes-sidebar-btn')?.classList.remove('active');
      document.getElementById('pdf-toc-sidebar')?.classList.remove('open');
      document.getElementById('pdf-toc-sidebar-btn')?.classList.remove('active');
      document.getElementById('mobile-appearance-sheet')?.classList.remove('open');
      document.getElementById('mobile-appearance-backdrop')?.classList.remove('active');
      document.getElementById('mobile-chat-backdrop')?.classList.remove('active');

      const readerEl = document.getElementById('workspace-reader');
      if (readerEl) readerEl.style.viewTransitionName = '';
      const chatPane = document.getElementById('workspace-chat-pane');
      if (chatPane) {
        chatPane.classList.remove('m-enter', 'm-exit', 'closing');
        chatPane.style.transformOrigin = '';
        chatPane.style.viewTransitionName = '';
      }
      const searchBar = document.getElementById('pdf-search-bar');
      if (searchBar) {
        searchBar.classList.remove('m-enter', 'm-exit', 'closing');
      }
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.classList.remove('is-zooming');
        container.style.willChange = '';
        container.removeEventListener('mouseup', handleTextSelection);
        container.removeEventListener('touchend', handleTextSelection);
        // Zero all active canvas backing stores immediately so browser frees GPU VRAM
        container.querySelectorAll('canvas').forEach(cv => {
          cv.width = 0;
          cv.height = 0;
        });
        container.innerHTML = '';
      }
    }

    function cleanupOffscreenPage(pNum) {
      if (isDocReaderMode) return;
      if (pdfRenderTasks[pNum]) {
        try { pdfRenderTasks[pNum].cancel(); } catch (_) {}
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

    function syncBookProgressMemoryAndCard(bookHash, page, totalPages) {
      if (!bookHash) return;
      if (activeWorkspaceBook && activeWorkspaceBook.hash === bookHash) {
        if (page > 0) activeWorkspaceBook.okunulan_sayfa = page;
        if (totalPages > 0) activeWorkspaceBook.sayfa_sayisi = totalPages;
      }
      if (typeof allBooks !== 'undefined' && Array.isArray(allBooks)) {
        const cachedBook = allBooks.find(b => (b.hash || b.dosya_hash) === bookHash);
        if (cachedBook) {
          if (page > 0) cachedBook.okunulan_sayfa = page;
          if (totalPages > 0) cachedBook.sayfa_sayisi = totalPages;
        }
      }
      if (typeof window.syncBookCardByHash === 'function') {
        window.syncBookCardByHash(bookHash);
      }
    }

    function scheduleSaveReadingProgress(targetPage) {
      if (!activeWorkspaceBook || !targetPage || Number.isNaN(targetPage)) return;
      const targetHash = activeWorkspaceBook.hash;
      const targetTotal = pdfPageCount > 0 ? pdfPageCount : (activeWorkspaceBook.sayfa_sayisi || 0);
      syncBookProgressMemoryAndCard(targetHash, targetPage, targetTotal);

      if (saveProgressDebounceTimer) {
        clearTimeout(saveProgressDebounceTimer);
      }
      saveProgressDebounceTimer = setTimeout(() => {
        const payload = { page: targetPage };
        if (targetTotal > 0) payload.total_pages = targetTotal;
        apiFetch(`/api/books/${targetHash}/progress`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).catch(err => console.warn("Okuma ilerlemesi kaydedilemedi:", err));
      }, 400);
    }

    function syncBookTotalPagesIfNeeded(book, totalPages) {
      if (!book || !totalPages || totalPages <= 0) return;
      const prevTotal = Number.parseInt(book.sayfa_sayisi || book.pages || 0, 10);
      if (prevTotal !== totalPages) {
        syncBookProgressMemoryAndCard(book.hash, book.okunulan_sayfa || pdfPageNum || 1, totalPages);
        apiFetch(`/api/books/${book.hash}/progress`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            page: Math.max(1, Number.parseInt(book.okunulan_sayfa || pdfPageNum || 1, 10)),
            total_pages: totalPages
          })
        }).catch(() => {});
      }
    }

    function updateVisiblePageProgress(mostVisiblePage) {
      if (!mostVisiblePage || Number.isNaN(mostVisiblePage) || pdfPageNum === mostVisiblePage) return;
      pdfPageNum = mostVisiblePage;
      syncPageIndicatorUI();
      scheduleSaveReadingProgress(pdfPageNum);
    }

    // Dynamic virtual scroll renderer
    function checkVisiblePagesAndRender() {
      if (!pdfDoc && !isDocReaderMode) return;
      
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return;
      
      if (pdfDoc && pdfPageNum && !Number.isNaN(pdfPageNum) && pdfPageNum >= 1 && !pdfRenderedPages[pdfPageNum]) {
        void renderPdfPageVirtual(pdfPageNum);
      }
      
      const containerRect = container.getBoundingClientRect();
      const wrappers = container.querySelectorAll('.pdf-page-wrapper');
      
      let mostVisiblePage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      let maxVisibleHeight = 0;
      
      for (let i = 0; i < wrappers.length; i++) {
        const wrapper = wrappers[i];
        const pNum = Number.parseInt(wrapper.dataset.pageNum || wrapper.dataset.pageNumber || wrapper.id.replace('pdf-page-wrapper-', ''), 10);
        if (Number.isNaN(pNum) || pNum < 1) continue;
        const rect = wrapper.getBoundingClientRect();
        
        const visibleTop = Math.max(rect.top, containerRect.top);
        const visibleBottom = Math.min(rect.bottom, containerRect.bottom);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        
        if (visibleHeight > maxVisibleHeight) {
          maxVisibleHeight = visibleHeight;
          mostVisiblePage = pNum;
        }
        
        if (pdfDoc) {
          const preloadBuffer = Math.max(rect.height * 1.5, containerRect.height * 0.9);
          const isNearViewport = (rect.bottom >= containerRect.top - preloadBuffer && rect.top <= containerRect.bottom + preloadBuffer);
          if (isNearViewport) {
            if (!pdfRenderedPages[pNum]) {
              void renderPdfPageVirtual(pNum);
            }
          } else if (pdfRenderedPages[pNum] === 'done' && !isUserSelectingText) {
            cleanupOffscreenPage(pNum);
          }
        }
      }
      
      updateVisiblePageProgress(mostVisiblePage);
    }

    async function renderTextLayerForPage(page, textLayer, viewport, pageNum, myGen, mySession) {
      unregisterTextLayerForSelection(textLayer);
      invalidatePageGeometry(pageNum);
      textLayer.innerHTML = "";
      textLayer.style.setProperty('--scale-factor', String(viewport.scale));
      try {
        const textContent = await page.getTextContent();
        if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;
        const textRenderTask = window.pdfjsLib.renderTextLayer({
          textContentSource: textContent,
          container: textLayer,
          viewport: viewport,
          textDivs: []
        });
        await textRenderTask.promise;
        if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;

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
      if (isDocReaderMode) return;
      if (!pdfDoc || !pageNum || Number.isNaN(pageNum) || pageNum < 1 || pageNum > pdfPageCount) return;
      if (pdfRenderedPages[pageNum] === 'done') return;
      if (pdfRenderedPages[pageNum] === 'rendering' && pdfRenderTasks[pageNum]?.promise) {
        try { await pdfRenderTasks[pageNum].promise; } catch (_) {}
        return;
      }
      
      const myGen = pdfRenderGeneration;
      const mySession = workspaceSessionToken;
      pdfRenderedPages[pageNum] = 'rendering';
      
      if (pdfRenderTasks[pageNum]) {
        try { pdfRenderTasks[pageNum].cancel(); } catch (_) {}
        delete pdfRenderTasks[pageNum];
      }
      
      try {
        const page = await pdfDoc.getPage(pageNum);
        if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;

        const container = document.getElementById('pdf-canvas-container');
        const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
        if (!wrapper) {
          delete pdfRenderedPages[pageNum];
          return;
        }
        const existingCanvas = document.getElementById(`pdf-render-canvas-${pageNum}`);
        const textLayer = document.getElementById(`textLayer-${pageNum}`);
        const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
        const viewport = page.getViewport({ scale: pdfScale });
        const cssW = Math.max(1, Math.round(viewport.width));
        const cssH = Math.max(1, Math.round(viewport.height));

        // Anchor scrollTop if this page's true intrinsic height differs from initial placeholder above viewport
        const prevH = wrapper.offsetHeight;
        if (container && prevH > 0 && Math.abs(cssH - prevH) > 2) {
          const rowOrWrap = wrapper.closest('.pdf-spread-row') || wrapper;
          if (rowOrWrap.offsetTop + prevH < container.scrollTop) {
            container.scrollTop += (cssH - prevH);
          }
        }

        wrapper.style.width = `${cssW}px`;
        wrapper.style.height = `${cssH}px`;
        wrapper.style.minHeight = `${cssH}px`;
        wrapper.style.flexShrink = '0';
        wrapper.style.transform = '';
        wrapper.style.setProperty('--scale-factor', String(viewport.scale));

        if (existingCanvas) {
          existingCanvas.style.width = `${cssW}px`;
          existingCanvas.style.height = `${cssH}px`;
        }
        
        // Exact 1:1 physical pixel alignment on 100%/125%/150%/200% HiDPI screens (eliminates subpixel blur)
        const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
        const pxW = Math.max(1, Math.round(cssW * dpr));
        const pxH = Math.max(1, Math.round(cssH * dpr));
        const scaleX = pxW / viewport.width;
        const scaleY = pxH / viewport.height;

        const newCanvas = document.createElement('canvas');
        newCanvas.className = 'pdf-page-canvas';
        newCanvas.width = pxW;
        newCanvas.height = pxH;
        newCanvas.style.width = `${cssW}px`;
        newCanvas.style.height = `${cssH}px`;
        
        const ctx = newCanvas.getContext('2d', { alpha: false });
        
        if (textLayer) {
          textLayer.style.width = `${cssW}px`;
          textLayer.style.height = `${cssH}px`;
          textLayer.style.setProperty('--scale-factor', String(viewport.scale));
        }
        if (highlightLayer) {
          highlightLayer.style.width = `${cssW}px`;
          highlightLayer.style.height = `${cssH}px`;
        }
        
        const renderContext = {
          canvasContext: ctx,
          viewport: viewport,
          transform: (scaleX !== 1 || scaleY !== 1) ? [scaleX, 0, 0, scaleY, 0, 0] : null
        };
        
        const renderTask = page.render(renderContext);
        pdfRenderTasks[pageNum] = renderTask;
        
        await renderTask.promise;
        delete pdfRenderTasks[pageNum];

        if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) {
          newCanvas.width = 0;
          newCanvas.height = 0;
          return;
        }

        // Apply ChromaGuard synchronously on offscreen buffer (~2ms Uint32Array) BEFORE DOM swap — zero white flash!
        if (currentReaderSurfaceMode === 'chromaguard') {
          applyChromaGuardSync(ctx, pxW, pxH);
        }

        pdfRenderedPages[pageNum] = 'done';
        newCanvas.id = `pdf-render-canvas-${pageNum}`;
        const currentExisting = document.getElementById(`pdf-render-canvas-${pageNum}`);
        if (currentExisting && currentExisting.parentNode) {
          const oldW = currentExisting;
          currentExisting.parentNode.replaceChild(newCanvas, currentExisting);
          oldW.width = 0;
          oldW.height = 0;
        } else if (wrapper.isConnected) {
          wrapper.insertBefore(newCanvas, wrapper.firstChild);
        }
        
        if (textLayer) {
          await renderTextLayerForPage(page, textLayer, viewport, pageNum, myGen, mySession);
        }
      } catch (err) {
        delete pdfRenderTasks[pageNum];
        if (err?.name === 'RenderingCancelledException') {
          if (myGen === pdfRenderGeneration) {
            delete pdfRenderedPages[pageNum];
          }
          return;
        }
        console.warn("Virtual page render failed:", pageNum, err);
        delete pdfRenderedPages[pageNum];
      }
    }

    function captureScrollFocalPoint(container, clientY = null) {
      if (!container) return null;
      const cRect = container.getBoundingClientRect();
      const probeY = (typeof clientY === 'number' && clientY >= cRect.top && clientY <= cRect.bottom)
        ? clientY
        : (cRect.top + cRect.height * 0.35);
      const pointerViewportOffset = probeY - cRect.top;

      let targetWrapper = null;
      const wrappers = container.querySelectorAll('.pdf-page-wrapper');
      for (let i = 0; i < wrappers.length; i++) {
        const r = wrappers[i].getBoundingClientRect();
        if (probeY >= r.top && probeY <= r.bottom) {
          targetWrapper = wrappers[i];
          break;
        }
      }
      if (!targetWrapper) {
        targetWrapper = document.getElementById(`pdf-page-wrapper-${pdfPageNum}`) || wrappers[0] || null;
      }
      if (!targetWrapper) return null;

      const wRect = targetWrapper.getBoundingClientRect();
      const pNum = Number.parseInt(targetWrapper.dataset.pageNum || targetWrapper.dataset.pageNumber || '1', 10) || 1;
      const ratio = wRect.height > 0
        ? Math.max(0, Math.min(1, (probeY - wRect.top) / wRect.height))
        : 0;
      return { pageNum: pNum, ratio, pointerViewportOffset };
    }

    function restoreScrollFocalPoint(container, focal) {
      if (!container || !focal) return;
      const wrapper = document.getElementById(`pdf-page-wrapper-${focal.pageNum}`);
      if (!wrapper) return;
      const rowOrWrap = wrapper.closest('.pdf-spread-row') || wrapper;
      const pageTop = rowOrWrap.offsetTop;
      const pageHeight = wrapper.offsetHeight;
      const desiredScrollTop = pageTop + (focal.ratio * pageHeight) - focal.pointerViewportOffset;
      container.scrollTop = Math.max(0, Math.round(desiredScrollTop));
    }

    // Scroll container layout resizing on zoom/width change
    function resizeAllPagesForZoom(focalOverride = null) {
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return;

      if (isDocReaderMode) {
        if (pdfIsFitWidth || pdfIsFitHeight) {
          pdfScale = 1.0;
          updateZoomLabel();
        }
        const focal = focalOverride || captureScrollFocalPoint(container);
        container.style.setProperty('--doc-font-scale', String(pdfScale));
        restoreScrollFocalPoint(container, focal);
        return;
      }

      if (!pdfDoc) return;
      const myGen = ++pdfRenderGeneration;
      const mySession = workspaceSessionToken;
      const focal = focalOverride || captureScrollFocalPoint(container);
      
      // Cancel active renders so canvases can resize cleanly
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      
      const targetPage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      
      pdfDoc.getPage(targetPage).then(function(samplePage) {
        if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;
        let viewport = samplePage.getViewport({ scale: 1.0 });
        
        if (pdfIsFitWidth) {
          pdfScale = computeFitWidthScale(viewport.width, container);
          updateZoomLabel();
        } else if (pdfIsFitHeight) {
          const containerHeight = Math.max(300, container.clientHeight - 64);
          pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
          updateZoomLabel();
        }
        
        viewport = samplePage.getViewport({ scale: pdfScale });
        const cssW = Math.max(1, Math.round(viewport.width));
        const cssH = Math.max(1, Math.round(viewport.height));
        pdfRenderedPages = {};
        invalidatePageGeometry();
        
        for (let p = 1; p <= pdfPageCount; p++) {
          const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
          if (wrapper) {
            wrapper.style.transform = '';
            wrapper.style.transformOrigin = '';
            wrapper.style.width = `${cssW}px`;
            wrapper.style.height = `${cssH}px`;
            wrapper.style.minHeight = `${cssH}px`;
            
            // Keep existing canvas scaled via CSS until new sharp bitmap swaps in (zero white gap)
            const existingCanvas = document.getElementById(`pdf-render-canvas-${p}`);
            if (existingCanvas) {
              existingCanvas.style.width = `${cssW}px`;
              existingCanvas.style.height = `${cssH}px`;
            }
            
            const textLayer = document.getElementById(`textLayer-${p}`);
            if (textLayer) {
              textLayer.style.width = `${cssW}px`;
              textLayer.style.height = `${cssH}px`;
              textLayer.style.setProperty('--scale-factor', String(viewport.scale));
              unregisterTextLayerForSelection(textLayer);
              textLayer.innerHTML = "";
            }
            
            const highlightLayer = document.getElementById(`pdf-highlight-layer-${p}`);
            if (highlightLayer) {
              highlightLayer.style.width = `${cssW}px`;
              highlightLayer.style.height = `${cssH}px`;
              highlightLayer.innerHTML = "";
            }
          }
        }
        
        restoreScrollFocalPoint(container, focal);
        void renderPdfPageVirtual(focal?.pageNum || targetPage);
        requestAnimationFrame(() => {
          checkVisiblePagesAndRender();
        });
      }).catch(function(err) {
        console.warn("resizeAllPagesForZoom getPage failed:", err);
      });
    }

    function scrollToPage(pageNum, opts = {}) {
      if (pageNum < 1 || pageNum > pdfPageCount) return;
      const prevPage = pdfPageNum;
      pdfPageNum = pageNum;
      syncPageIndicatorUI();
      scheduleSaveReadingProgress(pageNum);

      const container = document.getElementById('pdf-canvas-container');
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper && container) {
        if (pdfDoc && !pdfRenderedPages[pageNum]) {
          void renderPdfPageVirtual(pageNum);
        }
        const row = wrapper.closest('.pdf-spread-row');
        const targetTop = Math.max(0, row ? (row.offsetTop - 12) : (wrapper.offsetTop - 12));
        const isLargeJump = Math.abs(pageNum - prevPage) > 2;
        const reduced = typeof window.isMotionReduced === 'function' && window.isMotionReduced();
        if (opts.instant || isLargeJump || reduced) {
          container.scrollTop = targetTop;
          checkVisiblePagesAndRender();
        } else {
          container.scrollTo({ top: targetTop, behavior: 'smooth' });
        }
      }
    }

    function pdfPrevPage() {
      if (pdfPageNum <= 1) return;
      if (pdfIsSpreadMode && !isMobileReaderViewport()) {
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
      if (pdfIsSpreadMode && !isMobileReaderViewport()) {
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

    // Zoom Controls & 60fps Focal-Point Pinch / Ctrl+Wheel Engine
    let zoomWillChangeTimer = null;
    let wheelZoomCommitTimer = null;
    let wheelFocalState = null;
    let wheelBaseScale = null;

    function markZoomActive() {
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.classList.add('is-zooming');
      }
      if (zoomWillChangeTimer) clearTimeout(zoomWillChangeTimer);
      zoomWillChangeTimer = setTimeout(() => {
        const c = document.getElementById('pdf-canvas-container');
        if (c) c.classList.remove('is-zooming');
      }, 280);
    }

    function updateZoomLabel() {
      const pct = Math.round(pdfScale * 100);
      const el = document.getElementById('pdf-zoom-percent');
      if (el) el.textContent = pct + "%";
    }

    function pdfZoomIn() {
      markZoomActive();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');
      pdfScale = Math.min(4.0, Math.round((pdfScale + 0.15) * 100) / 100);
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
      pdfScale = Math.max(0.4, Math.round((pdfScale - 0.15) * 100) / 100);
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
        pdfScale = isDocReaderMode ? 1.0 : 1.2;
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
        pdfScale = isDocReaderMode ? 1.0 : 1.2;
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

    // Smooth 60fps Ctrl+Wheel & Trackpad Pinch Zoom (GPU preview during gesture + sharp PDF commit on settle)
    document.addEventListener('wheel', function(e) {
      if (!e.ctrlKey && !e.metaKey) return;
      const container = document.getElementById('pdf-canvas-container');
      if (!container?.contains(e.target)) return;
      e.preventDefault();
      if (!pdfDoc && !isDocReaderMode) return;

      markZoomActive();
      hideFloatingBar();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');

      if (!wheelFocalState) {
        wheelFocalState = captureScrollFocalPoint(container, e.clientY);
        wheelBaseScale = pdfScale;
      }

      const sensitivity = e.deltaMode === 1 ? 0.045 : 0.0028;
      const nextScale = Math.max(0.4, Math.min(4.0, pdfScale * Math.exp(-e.deltaY * sensitivity)));
      pdfScale = Math.round(nextScale * 1000) / 1000;
      updateZoomLabel();

      if (isDocReaderMode) {
        container.style.setProperty('--doc-font-scale', String(pdfScale));
        restoreScrollFocalPoint(container, wheelFocalState);
      } else if (wheelBaseScale && wheelBaseScale > 0) {
        const previewRatio = pdfScale / wheelBaseScale;
        const activeWrap = document.getElementById(`pdf-page-wrapper-${wheelFocalState?.pageNum || pdfPageNum}`);
        if (activeWrap) {
          activeWrap.style.transformOrigin = `50% ${Math.round((wheelFocalState?.ratio || 0.35) * 100)}%`;
          activeWrap.style.transform = `scale(${previewRatio.toFixed(4)})`;
        }
      }

      if (wheelZoomCommitTimer) clearTimeout(wheelZoomCommitTimer);
      wheelZoomCommitTimer = setTimeout(() => {
        const committedFocal = wheelFocalState;
        wheelFocalState = null;
        wheelBaseScale = null;
        wheelZoomCommitTimer = null;
        if (!isDocReaderMode) {
          resizeAllPagesForZoom(committedFocal);
        }
      }, 110);
    }, { passive: false });

    // Toggle Notes Sidebar on left
    function toggleNotesSidebar() {
      const sidebar = document.getElementById('pdf-notes-sidebar');
      const btn = document.getElementById('pdf-notes-sidebar-btn');
      const tocSidebar = document.getElementById('pdf-toc-sidebar');
      const tocBtn = document.getElementById('pdf-toc-sidebar-btn');
      if (!sidebar) return;
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (btn) btn.classList.remove('active');
      } else {
        if (tocSidebar) {
          tocSidebar.classList.remove('open');
          if (tocBtn) tocBtn.classList.remove('active');
        }
        sidebar.classList.add('open');
        if (btn) btn.classList.add('active');
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

    let selectionCheckTimer = null;

    function updateFloatingBarPosition(range, text, pageWrapper) {
      const pageNum = Number.parseInt(pageWrapper.dataset.pageNum || pageWrapper.dataset.pageNumber || pageWrapper.id.replace('pdf-page-wrapper-', ''), 10);
      if (!Number.isNaN(pageNum) && pageNum >= 1) {
        pdfPageNum = pageNum;
      }

      const viewerEl = document.getElementById('custom-pdf-viewer');
      const floatingBar = document.getElementById('pdf-floating-bar');
      if (!viewerEl || !floatingBar) return;

      const rect = range.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return;
      const viewerRect = viewerEl.getBoundingClientRect();

      floatingBar.classList.add('active');
      const barWidth = floatingBar.offsetWidth || 280;
      const barHeight = floatingBar.offsetHeight || 42;

      const desiredLeft = rect.left - viewerRect.left + (rect.width / 2) - (barWidth / 2);
      let desiredTop = rect.top - viewerRect.top - barHeight - 10;
      // Flip below selection if near top edge of viewer
      if (desiredTop < 12) {
        desiredTop = Math.min(viewerRect.height - barHeight - 12, rect.bottom - viewerRect.top + 10);
      }

      floatingBar.style.left = Math.max(10, Math.min(desiredLeft, Math.max(10, viewerRect.width - barWidth - 10))) + 'px';
      floatingBar.style.top = Math.max(10, desiredTop) + 'px';

      pdfSelectedText = text;
      pdfSelectionRanges = getSelectionCoordsRelativeToPage(range, pageWrapper);
    }

    // Handle Text Selection for highlights & floating bar positioning (deduplicated)
    function handleTextSelection() {
      if (selectionCheckTimer) clearTimeout(selectionCheckTimer);
      selectionCheckTimer = setTimeout(() => {
        selectionCheckTimer = null;
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
          hideFloatingBar();
          return;
        }
        const text = selection.toString().trim();
        if (text.length === 0) {
          hideFloatingBar();
          return;
        }

        const range = selection.getRangeAt(0);
        const container = document.getElementById('pdf-canvas-container');
        if (!container?.contains(range.commonAncestorContainer)) {
          hideFloatingBar();
          return;
        }

        const pageWrapper = getPageWrapperFromRange(range);
        if (!pageWrapper) {
          hideFloatingBar();
          return;
        }

        updateFloatingBarPosition(range, text, pageWrapper);
      }, 45);
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

    function copySelectedReaderText() {
      const text = pdfSelectedText || window.getSelection()?.toString()?.trim() || '';
      if (!text) return;
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(text)
          .then(() => {
            if (typeof showToast === 'function') showToast('Seçili metin kopyalandı.', 'success', 1800);
          })
          .catch(() => {
            if (typeof showToast === 'function') showToast('Metin kopyalanamadı.', 'error');
          });
      }
      clearSelection();
    }
    window.copySelectedReaderText = copySelectedReaderText;

    function askAIAboutSelection() {
      const text = (pdfSelectedText || window.getSelection()?.toString()?.trim() || '').slice(0, 1200);
      if (!text) return;
      const pageRef = pdfPageNum || 1;
      clearSelection();

      const chatPane = document.getElementById('workspace-chat-pane');
      if (chatPane && chatPane.classList.contains('collapsed')) {
        toggleWorkspaceChatPane();
      }
      const input = document.getElementById('workspace-chat-input');
      if (input) {
        input.value = `[Sayfa ${pageRef}] şu pasajı açıklar mısın:\n"${text}"`;
        input.style.height = 'auto';
        input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
        input.focus({ preventScroll: true });
      }
    }
    window.askAIAboutSelection = askAIAboutSelection;

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

    function extractNodeLineRects(node, range) {
      const textContent = node.textContent || '';
      let start = (node === range.startContainer) ? range.startOffset : 0;
      let end = (node === range.endContainer) ? range.endOffset : textContent.length;

      while (start < end && /\s/.test(textContent.charAt(start))) start++;
      while (end > start && /\s/.test(textContent.charAt(end - 1))) end--;
      if (start >= end) return [];

      const rects = [];
      try {
        const subRange = document.createRange();
        subRange.setStart(node, start);
        subRange.setEnd(node, end);
        const clientRects = subRange.getClientRects();
        for (let i = 0; i < clientRects.length; i++) {
          const r = clientRects[i];
          if (r.width > 0.5 && r.height > 0.5) {
            rects.push({
              left: r.left,
              right: r.right,
              top: r.top,
              bottom: r.bottom,
              width: r.width,
              height: r.height
            });
          }
        }
      } catch (_) {}
      return rects;
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

    // Fast O(spans) coordinates relative to page wrapper bounding box (zero per-character layout thrash)
    function getSelectionCoordsRelativeToPage(range, pageWrapperOverride = null) {
      const pageWrapper = pageWrapperOverride || getPageWrapperFromRange(range);
      if (!pageWrapper) return [];
      const wrapperRect = pageWrapper.getBoundingClientRect();
      if (wrapperRect.width <= 0 || wrapperRect.height <= 0) return [];

      const textNodes = collectTextNodesFromRange(range, pageWrapper);
      const rawRects = [];
      for (let i = 0; i < textNodes.length; i++) {
        const nodeRects = extractNodeLineRects(textNodes[i], range);
        for (let j = 0; j < nodeRects.length; j++) {
          rawRects.push(nodeRects[j]);
        }
      }

      const mergedLines = groupCharRectsIntoLines(rawRects);
      const coords = [];
      mergedLines.forEach(line => {
        const w = line.right - line.left;
        if (w < 1.5 || line.height < 1.5) return;
        coords.push({
          left: Math.max(0, (line.left - wrapperRect.left) / wrapperRect.width),
          top: Math.max(0, (line.top - wrapperRect.top) / wrapperRect.height),
          width: Math.min(1, w / wrapperRect.width),
          height: Math.min(1, line.height / wrapperRect.height)
        });
      });

      if (coords.length === 0) {
        const rects = range.getClientRects();
        for (const r of rects) {
          if (r.width < 1.5 || r.height < 1.5) continue;
          if (r.bottom < wrapperRect.top || r.top > wrapperRect.bottom) continue;
          coords.push({
            left: Math.max(0, (r.left - wrapperRect.left) / wrapperRect.width),
            top: Math.max(0, (r.top - wrapperRect.top) / wrapperRect.height),
            width: Math.min(1, r.width / wrapperRect.width),
            height: Math.min(1, r.height / wrapperRect.height)
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
    function _presentPdfNoteModal(triggerEl) {
      const noteModal = document.getElementById('pdf-note-modal');
      if (!noteModal) return;
      noteModal._sourceTriggerEl = triggerEl || document.activeElement || null;
      const modalBox = noteModal.querySelector('.modal');
      if (modalBox) {
        modalBox.style.setProperty('--modal-origin-x', 'center');
        modalBox.style.setProperty('--modal-origin-y', 'center');
      }
      noteModal.classList.remove('closing', 'm-exit');
      document.body.classList.add('modal-open');
      if (window.Motion && typeof window.Motion.enter === 'function') {
        void window.Motion.enter(noteModal, { className: '', addClass: 'open', cleanExitClass: 'closing' });
      } else {
        noteModal.classList.add('open');
      }
      if (typeof activateModalFocus === 'function') activateModalFocus(noteModal);
    }

    function openNoteModalForSelection() {
      if (!pdfSelectedText) return;
      const triggerEl = document.activeElement instanceof HTMLElement ? document.activeElement : null;

      pdfActiveHighlightIdForNote = generateHighlightId();

      // Default to yellow for new selections
      selectModalNoteColor('#e8dca0', 'yellow');

      // Populate previews
      document.getElementById('pdf-selected-text-preview').textContent = `"${pdfSelectedText}"`;
      document.getElementById('pdf-note-textarea').value = "";

      _presentPdfNoteModal(triggerEl);
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
      const triggerEl = document.activeElement instanceof HTMLElement ? document.activeElement : null;
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
      _presentPdfNoteModal(triggerEl);
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
    async function jumpToHighlight(pageNum, hlId) {
      const prevPage = pdfPageNum;
      scrollToPage(pageNum, { instant: Math.abs(pageNum - prevPage) > 2 });
      if (pdfDoc) {
        await renderPdfPageVirtual(pageNum);
      }
      drawPageHighlightsAndNotes(pageNum);

      if (isMobileReaderViewport()) {
        document.getElementById('pdf-notes-sidebar')?.classList.remove('open');
        document.getElementById('pdf-notes-sidebar-btn')?.classList.remove('active');
      }

      requestAnimationFrame(() => {
        const highlightEl = document.querySelector(`[data-hl-id="${hlId}"]`);
        if (highlightEl) {
          highlightEl.style.opacity = "0.95";
          setTimeout(() => { highlightEl.style.opacity = ""; }, 1500);
        }
      });
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
      hideFloatingBar();
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
    let _pdfSearchTriggerEl = null;

    // Toggle search bar
    function togglePdfSearch(forceOpen) {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const input = document.getElementById('pdf-search-input');
      if (!searchBar) return;

      const isHidden = searchBar.style.display === 'none' || !searchBar.style.display || searchBar.classList.contains('closing');
      const shouldOpen = (forceOpen !== undefined) ? forceOpen : isHidden;
      if (shouldOpen) {
        if (document.activeElement instanceof HTMLElement && !searchBar.contains(document.activeElement)) {
          _pdfSearchTriggerEl = document.activeElement;
        } else {
          _pdfSearchTriggerEl = toggleBtn;
        }
        toggleBtn?.classList.add('active');
        toggleBtn?.setAttribute('aria-expanded', 'true');
        isPdfSearchOpen = true;
        if (window.Motion && typeof window.Motion.enter === 'function') {
          void window.Motion.enter(searchBar, {
            className: '',
            showDisplay: 'block',
            origin: 'top right',
            cleanExitClass: 'closing',
            focusEl: input
          });
          requestAnimationFrame(() => input?.select());
        } else {
          searchBar.classList.remove('closing');
          searchBar.style.display = 'block';
          requestAnimationFrame(() => {
            input?.focus({ preventScroll: true });
            input?.select();
          });
        }
      } else {
        closePdfSearch({ restoreFocus: true });
      }
    }

    function closePdfSearch(opts = {}) {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const drawer = document.getElementById('pdf-search-results-drawer');
      const listBtn = document.getElementById('pdf-search-list-btn');

      toggleBtn?.classList.remove('active');
      toggleBtn?.setAttribute('aria-expanded', 'false');
      listBtn?.classList.remove('active');
      listBtn?.setAttribute('aria-expanded', 'false');
      isPdfSearchOpen = false;
      isPdfSearchDrawerOpen = false;
      clearPdfSearch(true); // clear visual highlights

      const restoreFocus = () => {
        if (opts.restoreFocus) {
          const target = (_pdfSearchTriggerEl && _pdfSearchTriggerEl.isConnected) ? _pdfSearchTriggerEl : toggleBtn;
          if (target && typeof target.focus === 'function') {
            target.focus({ preventScroll: true });
          }
        }
      };

      if (drawer) {
        drawer.classList.remove('m-enter', 'm-exit');
        drawer.style.display = 'none';
      }

      if (searchBar && searchBar.style.display !== 'none' && !searchBar.classList.contains('closing')) {
        if (window.Motion && typeof window.Motion.exit === 'function') {
          void window.Motion.exit(searchBar, {
            className: 'closing',
            hideDisplay: true,
            afterFn: restoreFocus
          });
        } else {
          searchBar.style.display = 'none';
          restoreFocus();
        }
      } else {
        if (searchBar) searchBar.style.display = 'none';
        restoreFocus();
      }
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
      listBtn?.setAttribute('aria-expanded', String(isPdfSearchDrawerOpen));
      if (isPdfSearchDrawerOpen) {
        listBtn?.classList.add('active');
        if (window.Motion && typeof window.Motion.enter === 'function') {
          void window.Motion.enter(drawer, {
            className: 'm-enter',
            showDisplay: 'block',
            origin: 'top center',
            cleanExitClass: 'm-exit'
          });
        } else {
          drawer.style.display = 'block';
        }
      } else {
        listBtn?.classList.remove('active');
        if (window.Motion && typeof window.Motion.exit === 'function') {
          void window.Motion.exit(drawer, {
            className: 'm-exit',
            hideDisplay: true
          });
        } else {
          drawer.style.display = 'none';
        }
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
        e.stopPropagation();
        closePdfSearch({ restoreFocus: true });
      }
    }

    function foldTrChar(ch) {
      if (ch === 'İ' || ch === 'i') return 'i';
      if (ch === 'I' || ch === 'ı') return 'ı';
      const lower = ch.toLowerCase();
      return lower.length === 1 ? lower : ch;
    }

    function normalizeSearchString(raw) {
      if (!raw) return { rawNorm: '', folded: '' };
      const nfc = String(raw).normalize('NFC');
      const rawOut = [];
      const foldOut = [];
      for (let i = 0; i < nfc.length; i++) {
        const ch = nfc[i];
        if (/\s/.test(ch)) {
          if (foldOut.length > 0 && foldOut[foldOut.length - 1] !== ' ') {
            rawOut.push(' ');
            foldOut.push(' ');
          }
        } else {
          rawOut.push(ch);
          foldOut.push(foldTrChar(ch));
        }
      }
      if (foldOut.length > 0 && foldOut[foldOut.length - 1] === ' ') {
        rawOut.pop();
        foldOut.pop();
      }
      return { rawNorm: rawOut.join(''), folded: foldOut.join('') };
    }

    function collectMatchesForPage(p, pageData, query, normalizedQuery) {
      const textLower = pageData.textLower;
      if (!normalizedQuery) return;
      let pos = 0;
      let pageMatchCount = 0;
      while ((pos = textLower.indexOf(normalizedQuery, pos)) !== -1) {
        const startSnippet = Math.max(0, pos - 35);
        const endSnippet = Math.min(pageData.text.length, pos + normalizedQuery.length + 35);
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

    // Iterative fast page scanner with token-based cancellation (supports PDF, EPUB & TXT)
    async function scanPagesIteratively(myToken, pageCount, query, normalizedQuery) {
      for (let p = 1; p <= pageCount; p++) {
        if (myToken !== pdfSearchToken) return false;

        let pageData = pdfSearchTextCache[p];
        if (!pageData) {
          if (isDocReaderMode) {
            const pgObj = docReaderPages[p - 1];
            const blocks = Array.isArray(pgObj?.blocks) ? pgObj.blocks : [];
            const rawParts = [];
            if (pgObj?.title) rawParts.push(pgObj.title);
            blocks.forEach(b => { if (b?.text) rawParts.push(b.text); });
            const { rawNorm, folded } = normalizeSearchString(rawParts.join(' '));
            pageData = { text: rawNorm, textLower: folded };
            pdfSearchTextCache[p] = pageData;
          } else if (pdfDoc) {
            try {
              const page = await pdfDoc.getPage(p);
              if (myToken !== pdfSearchToken) return false;
              const textContent = await page.getTextContent();
              if (myToken !== pdfSearchToken) return false;
              const textParts = textContent.items.map(item => item.str || "");
              const { rawNorm, folded } = normalizeSearchString(textParts.join(" "));
              pageData = {
                text: rawNorm,
                textLower: folded,
                items: textContent.items
              };
              pdfSearchTextCache[p] = pageData;
            } catch (err) {
              console.warn("Sayfa metni taranamadı:", p, err);
            }
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
      void jumpToSearchResult(targetIdx, false);
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
      if ((!pdfDoc && !isDocReaderMode) || !query || query.length < 1) {
        clearPdfSearch(true);
        return;
      }

      const { folded: normalizedQuery } = normalizeSearchString(query);
      if (!normalizedQuery) {
        clearPdfSearch(true);
        return;
      }

      const myToken = ++pdfSearchToken;
      pdfSearchQuery = query;
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

    // Jump to specific search match (awaits virtual page render before scrolling to highlight)
    async function jumpToSearchResult(idx, shouldScrollSmooth) {
      if (idx < 0 || idx >= pdfSearchResults.length) return;
      pdfSearchCurrentMatchIdx = idx;
      updateSearchNavState();

      const match = pdfSearchResults[idx];
      const targetPage = match.pageNum;
      const prevPage = pdfPageNum;

      scrollToPage(targetPage, { instant: !shouldScrollSmooth || Math.abs(targetPage - prevPage) > 2 });
      if (pdfDoc) {
        await renderPdfPageVirtual(targetPage);
      }

      drawPageSearchHighlights(targetPage);
      document.querySelectorAll('.pdf-search-highlight.active').forEach(el => el.classList.remove('active'));
      const activeMarkers = document.querySelectorAll(`.pdf-search-highlight[data-match-idx="${idx}"]`);
      if (activeMarkers.length > 0) {
        activeMarkers.forEach(el => el.classList.add('active'));
        const container = document.getElementById('pdf-canvas-container');
        if (container) {
          const mRect = activeMarkers[0].getBoundingClientRect();
          const cRect = container.getBoundingClientRect();
          if (mRect.top < cRect.top + 36 || mRect.bottom > cRect.bottom - 36) {
            const delta = (mRect.top - cRect.top) - (cRect.height / 2) + (mRect.height / 2);
            container.scrollTop = Math.max(0, Math.round(container.scrollTop + delta));
          }
        }
      }
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

    function buildTextLayerSearchMap(textLayer) {
      const foldedChars = [];
      const locMap = [];
      const walker = document.createTreeWalker(
        textLayer,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode(node) {
            if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
            const parent = node.parentElement;
            if (parent && (parent.classList.contains('endOfContent') || parent.classList.contains('doc-sheet-footer'))) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );

      let cur = walker.nextNode();
      while (cur) {
        const val = cur.nodeValue;
        if (val.length > 0) {
          if (foldedChars.length > 0 && foldedChars[foldedChars.length - 1] !== ' ' && !/\s/.test(val[0])) {
            foldedChars.push(' ');
            locMap.push(null);
          }
          for (let i = 0; i < val.length; i++) {
            const ch = val[i];
            if (/\s/.test(ch)) {
              if (foldedChars.length > 0 && foldedChars[foldedChars.length - 1] !== ' ') {
                foldedChars.push(' ');
                locMap.push({ node: cur, offset: i });
              }
            } else {
              foldedChars.push(foldTrChar(ch));
              locMap.push({ node: cur, offset: i });
            }
          }
        }
        cur = walker.nextNode();
      }
      if (foldedChars.length > 0 && foldedChars[foldedChars.length - 1] === ' ') {
        foldedChars.pop();
        locMap.pop();
      }
      return { foldedText: foldedChars.join(''), locMap };
    }

    // Draw visual yellow highlight rects for a given page (matches across split <span> boundaries!)
    function drawPageSearchHighlights(pageNum) {
      if (!pdfSearchQuery || !pdfSearchPageMatchesCount[pageNum]) return;

      const textLayer = document.getElementById(`textLayer-${pageNum}`);
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
      const pageWrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (!textLayer || !highlightLayer || !pageWrapper) return;

      highlightLayer.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());

      const wrapperRect = pageWrapper.getBoundingClientRect();
      if (wrapperRect.width <= 0 || wrapperRect.height <= 0) return;

      const { folded: normalizedQuery } = normalizeSearchString(pdfSearchQuery);
      if (!normalizedQuery) return;

      const { foldedText, locMap } = buildTextLayerSearchMap(textLayer);
      if (!foldedText) return;

      const pageMatches = pdfSearchResults.filter(m => m.pageNum === pageNum);
      let pos = 0;
      let matchIdxInPage = 0;

      while ((pos = foldedText.indexOf(normalizedQuery, pos)) !== -1) {
        const endPos = pos + normalizedQuery.length;
        const globalIdx = matchIdxInPage < pageMatches.length ? pageMatches[matchIdxInPage].matchIndex : undefined;

        // Group contiguous character offsets belonging to the same text node
        let segNode = null;
        let segStart = 0;
        let segEnd = 0;
        const flushSegment = () => {
          if (!segNode) return;
          try {
            const range = document.createRange();
            const maxLen = segNode.nodeValue ? segNode.nodeValue.length : 0;
            const s = Math.max(0, Math.min(maxLen, segStart));
            const e = Math.max(s, Math.min(maxLen, segEnd));
            if (e > s) {
              range.setStart(segNode, s);
              range.setEnd(segNode, e);
              const rects = range.getClientRects();
              for (const rect of rects) {
                _appendSearchHighlightDiv(rect, wrapperRect, globalIdx, highlightLayer);
              }
            }
          } catch (_) {}
          segNode = null;
        };

        for (let k = pos; k < endPos; k++) {
          const entry = locMap[k];
          if (!entry) continue;
          if (entry.node === segNode) {
            segEnd = entry.offset + 1;
          } else {
            flushSegment();
            segNode = entry.node;
            segStart = entry.offset;
            segEnd = entry.offset + 1;
          }
        }
        flushSegment();

        matchIdxInPage++;
        pos += Math.max(1, normalizedQuery.length);
      }
    }

    function drawAllVisibleSearchHighlights() {
      if ((!pdfDoc && !isDocReaderMode) || !pdfSearchQuery) return;
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

    // Handle window resize dynamically for spread layout, mobile reader mode, and Fit-Width
    let resizeSpreadTimer = null;
    window.addEventListener('resize', () => {
      const readerEl = document.getElementById('workspace-reader');
      if (readerEl?.classList.contains('open')) {
        readerEl.classList.toggle('is-mobile-reader', isMobileReaderViewport());
      }
      if (resizeSpreadTimer) clearTimeout(resizeSpreadTimer);
      resizeSpreadTimer = setTimeout(() => {
        if (!activeWorkspaceBook) return;
        if ((pdfDoc || isDocReaderMode) && pdfPageCount > 0 && pdfIsSpreadMode) {
          applySpreadLayout();
        }
        if (pdfDoc && (pdfIsFitWidth || pdfIsFitHeight)) {
          resizeAllPagesForZoom();
        }
      }, 180);
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
                  const pageIdx = typeof pageRef === 'number'
                    ? pageRef
                    : await pdf.getPageIndex(pageRef);
                  jumpToPdfPage(pageIdx + 1);
                  if (isMobileReaderViewport()) {
                    const sb = document.getElementById('pdf-toc-sidebar');
                    if (sb) sb.classList.remove('open');
                    document.getElementById('pdf-toc-sidebar-btn')?.classList.remove('active');
                  }
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
        const mobLabel = document.getElementById('mob-tts-label');
        if (mobLabel) mobLabel.textContent = 'Kitabı Sesli Dinle';
        showToast('Seslendirme durduruldu.', 'info', 1800);
        return;
      }

      const selection = window.getSelection().toString().trim();
      let textToSpeak = selection;

      if (!textToSpeak && (pdfDoc || isDocReaderMode)) {
        const activeWrapper = document.getElementById(`pdf-page-wrapper-${pdfPageNum}`);
        if (activeWrapper) {
          const docBody = activeWrapper.querySelector('.doc-sheet-body');
          textToSpeak = (docBody ? docBody.innerText : activeWrapper.querySelector('.textLayer')?.innerText)?.trim() || '';
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
        const mobLabel = document.getElementById('mob-tts-label');
        if (mobLabel) mobLabel.textContent = 'Kitabı Sesli Dinle';
      };

      utterance.onerror = () => {
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
        const mobLabel = document.getElementById('mob-tts-label');
        if (mobLabel) mobLabel.textContent = 'Kitabı Sesli Dinle';
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
          if (window.innerWidth <= 860) {
            const sb = document.getElementById('pdf-toc-sidebar');
            if (sb) sb.classList.remove('open');
          }
        });
        tocList.appendChild(div);
      });
    }
    window.renderSynthesizedToc = renderSynthesizedToc;

    // --- [8.1] ChromaGuard™ Smart Surface & Image Preservation (32-bit Uint32Array Fast Path) ---
    let currentReaderSurfaceMode = 'normal';
    try {
      currentReaderSurfaceMode = localStorage.getItem('pdf_reader_surface_mode') || 'normal';
    } catch (e) {}

    const _CHROMA_LITTLE_ENDIAN = (() => {
      try {
        const buf = new ArrayBuffer(4);
        new Uint32Array(buf)[0] = 0x0a0b0c0d;
        return new Uint8Array(buf)[0] === 0x0d;
      } catch (_) {
        return true;
      }
    })();

    // Sepia and e-ink modes use zero-overhead GPU CSS filters via [data-surface-mode].
    // ChromaGuard uses a ~2ms 32-bit integer pass on the offscreen canvas BEFORE DOM insertion (zero white flash, colored figures preserved).
    function applyChromaGuardBuffer(imgData) {
      const data = imgData.data;
      if (_CHROMA_LITTLE_ENDIAN && imgData.data.buffer && (imgData.data.byteOffset % 4 === 0)) {
        const u32 = new Uint32Array(imgData.data.buffer, imgData.data.byteOffset, imgData.data.byteLength >> 2);
        const count = u32.length;
        const paperDarkBase = (0x14 << 16) | (0x16 << 8) | 0x17; // #171614 warm obsidian
        for (let i = 0; i < count; i++) {
          const px = u32[i];
          const r = px & 0xFF;
          const g = (px >> 8) & 0xFF;
          const b = (px >> 16) & 0xFF;
          const a = px & 0xFF000000;

          // Fast path: pure/near-white paper background (~80% of book pixels) -> 1 bitwise op
          if (r >= 246 && g >= 246 && b >= 246) {
            u32[i] = a | paperDarkBase;
            continue;
          }

          const maxC = r > g ? (r > b ? r : b) : (g > b ? g : b);
          const minC = r < g ? (r < b ? r : b) : (g < b ? g : b);
          // Preserve chromatic diagrams, covers, photos & charts untouched
          if ((maxC - minC) > 28) {
            continue;
          }

          const lum = (r * 77 + g * 150 + b * 29) >> 8;
          const inv = 255 - lum;
          const nr = 23 + ((inv * 213) >> 8);
          const ng = 22 + ((inv * 209) >> 8);
          const nb = 20 + ((inv * 201) >> 8);
          u32[i] = a | (nb << 16) | (ng << 8) | nr;
        }
        return;
      }

      // Big-endian fallback
      const len = data.length;
      for (let i = 0; i < len; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const maxC = Math.max(r, g, b);
        const minC = Math.min(r, g, b);
        if ((maxC - minC) > 28) continue;
        const inv = 255 - ((r * 77 + g * 150 + b * 29) >> 8);
        data[i] = 23 + ((inv * 213) >> 8);
        data[i + 1] = 22 + ((inv * 209) >> 8);
        data[i + 2] = 20 + ((inv * 201) >> 8);
      }
    }

    function applyChromaGuardSync(ctx, w, h) {
      if (!ctx || !w || !h) return;
      try {
        const imgData = ctx.getImageData(0, 0, w, h);
        applyChromaGuardBuffer(imgData);
        ctx.putImageData(imgData, 0, 0);
      } catch (e) {
        console.debug('ChromaGuard pixel transform warning:', e);
      }
    }

    function applyChromaGuard(canvas, mode) {
      if (!canvas || mode !== 'chromaguard') return;
      const ctx = canvas.getContext('2d');
      if (ctx) applyChromaGuardSync(ctx, canvas.width, canvas.height);
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
      document.querySelectorAll('.mobile-surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `mob-surface-${mode}`);
      });

      // EPUB/TXT structured sheets and normal/sepia/eink switches are styled purely via CSS in 0ms!
      if (isDocReaderMode) {
        return;
      }
      const requiresReRender = (prevMode === 'chromaguard' && mode !== 'chromaguard') || (mode === 'chromaguard' && prevMode !== 'chromaguard');
      if (!requiresReRender) {
        return;
      }

      ++pdfRenderGeneration;
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};

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
        if (timerEl) timerEl.textContent = 'Aynı yerel ağdaki (Wi-Fi) telefonunuzla okutarak anında okumaya devam edin.';
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
    }
    window.openWorkspaceAtPage = openWorkspaceAtPage;

    // Listen for DPI changes (e.g. dragging between Retina & standard screens)
    if (typeof window !== 'undefined' && window.matchMedia) {
      const setupDprWatcher = () => {
        const dpr = window.devicePixelRatio || 1;
        const mq = window.matchMedia(`(resolution: ${dpr}dppx)`);
        mq.addEventListener('change', () => {
          if (activeWorkspaceBook && pdfDoc) {
            ++pdfRenderGeneration;
            Object.keys(pdfRenderedPages).forEach(p => cleanupOffscreenPage(Number(p)));
            checkVisiblePagesAndRender();
          }
          setupDprWatcher();
        }, { once: true });
      };
      setupDprWatcher();
    }

