/* ════════════════════════════════════════════════════════════════════════════════
 * ui_workspace.js — Workspace Lifecycle, Split-Pane, Annotations & LAN Handoff
 * ════════════════════════════════════════════════════════════════════════════════ */

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
      
      // Keep keyboard focus on the reader canvas container so Space / PageDown / Arrows / Escape work immediately
      setTimeout(() => {
        if (mySession !== workspaceSessionToken) return;
        const canvasContainer = document.getElementById('pdf-canvas-container');
        if (canvasContainer && !document.activeElement?.closest?.('#pdf-search-bar')) {
          if (!canvasContainer.hasAttribute('tabindex')) {
            canvasContainer.setAttribute('tabindex', '-1');
          }
          canvasContainer.focus({ preventScroll: true });
        }
      }, 120);
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
    window.selectModalNoteColor = selectModalNoteColor;

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
      if (pdfDoc && pdfIsFitWidth && typeof resizeAllPagesForZoom === 'function') {
        setTimeout(() => resizeAllPagesForZoom(), 180);
      }
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

      if (!e.ctrlKey && !e.metaKey && !e.altKey && (e.key === 'b' || e.key === 'B')) {
        if (typeof toggleCurrentPageBookmark === 'function') {
          e.preventDefault();
          void toggleCurrentPageBookmark();
          return;
        }
      }

      // Spacebar smooth reading / page advance (Kindle style) — skip if a button is focused
      if ((e.key === ' ' || e.code === 'Space') && (!activeEl || activeEl.tagName !== 'BUTTON')) {
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

    window.openWorkspace = openWorkspace;
    window.closeWorkspace = closeWorkspace;
    window.toggleNotesSidebar = toggleNotesSidebar;
    window.applyHighlight = applyHighlight;
    window.openNoteModalForSelection = openNoteModalForSelection;
    window.closePdfNoteModal = closePdfNoteModal;
    window.closePdfNoteModalDirect = closePdfNoteModalDirect;
    window.savePdfNote = savePdfNote;
    window.deleteHighlight = deleteHighlight;
    window.jumpToHighlight = jumpToHighlight;
    window.editExistingNote = editExistingNote;
