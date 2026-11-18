/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_renderer.js — Virtualized PDF/EPUB/TXT Renderer, Zoom, Spread & ChromaGuard
 * ════════════════════════════════════════════════════════════════════════════════ */

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

        const ttsLayer = document.createElement('div');
        ttsLayer.className = 'pdf-tts-layer';
        ttsLayer.id = `pdf-tts-layer-${p}`;
        ttsLayer.style.width = `${cssW}px`;
        ttsLayer.style.height = `${cssH}px`;
        pageWrapper.appendChild(ttsLayer);

        const highlightLayer = document.createElement('div');
        highlightLayer.className = 'pdf-highlight-layer';
        highlightLayer.id = `pdf-highlight-layer-${p}`;
        highlightLayer.style.width = `${cssW}px`;
        highlightLayer.style.height = `${cssH}px`;
        pageWrapper.appendChild(highlightLayer);

        frag.appendChild(pageWrapper);
      }
      container.appendChild(frag);
      syncPageBookmarkRibbons();

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

      if (activeNavDrawerTab === 'thumbs') {
        buildThumbnailsGrid();
      }
      renderNotesSidebar();
    }

    // --- [D2: PDF Pre-Fetching & Streaming Config] ---

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
      if (window.OfflineVault && typeof window.OfflineVault.isBookVaulted === 'function' && window.OfflineVault.isBookVaulted(hash)) {
        return;
      }
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
      const tag = String(blk?.type || blk?.tag || 'p').toLowerCase();
      if ((tag === 'image' || tag === 'img') && blk?.src && activeWorkspaceBook?.hash) {
        const assetUrl = `/api/books/${encodeURIComponent(activeWorkspaceBook.hash)}/epub-asset?path=${encodeURIComponent(blk.src)}`;
        const altStr = esc(blk?.alt || '');
        const captionHtml = altStr ? `<figcaption class="doc-figcaption">${altStr}</figcaption>` : '';
        return `<figure class="doc-figure"><img class="doc-embedded-img" src="${assetUrl}" alt="${altStr}" loading="lazy">${captionHtml}</figure>`;
      }

      const text = esc(blk?.text || '');
      if (!text) return '';

      let fnRefsHtml = '';
      if (Array.isArray(blk?.footnotes) && blk.footnotes.length > 0) {
        fnRefsHtml = ' ' + blk.footnotes.map(fn => {
          const lbl = esc(fn.label || '*');
          return `<button type="button" class="epub-footnote-ref" data-fn-id="${esc(fn.id || '')}" data-fn-label="${lbl}" data-fn-body="${encData(fn.content || '')}" title="Dipnot ${lbl}">[${lbl}]</button>`;
        }).join(' ');
      }

      if (tag === 'h1') return `<h1 class="doc-heading-1">${text}${fnRefsHtml}</h1>`;
      if (tag === 'h2') return `<h2 class="doc-heading-1">${text}${fnRefsHtml}</h2>`;
      if (tag === 'h3' || tag === 'h4') return `<h3 class="doc-heading-2">${text}${fnRefsHtml}</h3>`;
      if (tag === 'blockquote') return `<blockquote class="doc-quote">${text}${fnRefsHtml}</blockquote>`;
      if (tag === 'pre') return `<pre class="doc-pre">${text}</pre>`;
      if (tag === 'li') return `<p class="doc-list-item">• ${text}${fnRefsHtml}</p>`;
      return `<p class="doc-para">${text}${fnRefsHtml}</p>`;
    }

    function setupStructuredDocReader(data, book, container, mySession) {
      if (mySession !== undefined && mySession !== workspaceSessionToken) return;
      isDocReaderMode = true;
      docReaderFormat = String(data?.format || 'txt').toLowerCase();
      epubFootnotesMap = (data?.footnotes && typeof data.footnotes === 'object') ? data.footnotes : {};
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
        applyDocTypographyPrefs();
        const frag = document.createDocumentFragment();

        docReaderPages.forEach((pg, idx) => {
          const p = Number(pg.page_num || pg.page) || (idx + 1);
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

          const ttsLayer = document.createElement('div');
          ttsLayer.className = 'pdf-tts-layer';
          ttsLayer.id = `pdf-tts-layer-${p}`;
          pageWrapper.appendChild(ttsLayer);

          const highlightLayer = document.createElement('div');
          highlightLayer.className = 'pdf-highlight-layer';
          highlightLayer.id = `pdf-highlight-layer-${p}`;
          pageWrapper.appendChild(highlightLayer);

          pdfRenderedPages[p] = 'done';
          frag.appendChild(pageWrapper);
        });

        container.appendChild(frag);
        syncPageBookmarkRibbons();

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

      if (activeNavDrawerTab === 'thumbs') {
        buildThumbnailsGrid();
      }
      renderNotesSidebar();
    }

    function syncReaderFormatControls(isStructuredDoc) {
      const typoBtn = document.getElementById('pdf-typography-btn');
      const fitWBtn = document.getElementById('pdf-fit-width-btn');
      const fitHBtn = document.getElementById('pdf-fit-height-btn');
      const spreadBtn = document.getElementById('pdf-spread-btn');
      if (typoBtn) typoBtn.style.display = isStructuredDoc ? '' : 'none';
      if (fitWBtn) fitWBtn.style.display = isStructuredDoc ? 'none' : '';
      if (fitHBtn) fitHBtn.style.display = isStructuredDoc ? 'none' : '';
      if (spreadBtn) spreadBtn.style.display = isStructuredDoc ? 'none' : '';
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
      const initLowerFile = String(book.file || book.dosya_adi || '').toLowerCase();
      const initIsStructured = initLowerFile.endsWith('.epub') || initLowerFile.endsWith('.txt');
      docReaderFormat = initIsStructured ? (initLowerFile.endsWith('.epub') ? 'epub' : 'txt') : 'pdf';
      syncReaderFormatControls(initIsStructured);
      pdfPageNum = (initialPage && initialPage > 0) ? initialPage : Math.max(1, book.okunulan_sayfa || 1);
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
      closeDocTypographyPopover();
      pdfBookmarksMap.clear();
      epubFootnotesMap = {};
      if (typeof switchTocDrawerTab === 'function') {
        switchTocDrawerTab('outline');
      }
      const ocrPill = document.getElementById('pdf-ocr-status-pill');
      if (ocrPill) ocrPill.style.display = 'none';
      const thumbsListEl = document.getElementById('pdf-thumbs-list');
      if (thumbsListEl) thumbsListEl.dataset.builtForHash = '';
      void loadBookBookmarks(book.hash, mySession);
      applyDocTypographyPrefs();
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

      if (window.OfflineVault && typeof window.OfflineVault.syncVaultBadgesInDOM === 'function') {
        window.OfflineVault.syncVaultBadgesInDOM();
      }

      // Check file extension: Native paginated structured reader for .epub and .txt (with Offline Vault priority)
      const bookFilename = String(book.file || book.dosya_adi || "").toLowerCase();
      if (bookFilename.endsWith(".epub") || bookFilename.endsWith(".txt")) {
        const loadStructured = async () => {
          if (window.OfflineVault && typeof window.OfflineVault.getVaultedBook === 'function') {
            const vaulted = await window.OfflineVault.getVaultedBook(book.hash);
            if (vaulted?.readerContent) {
              return vaulted.readerContent;
            }
          }
          const res = await apiFetch(`/api/books/${encodeURIComponent(book.hash)}/reader-content`);
          if (!res || !res.ok) {
            throw new Error(`HTTP ${res?.status || 500}`);
          }
          return res.json();
        };

        loadStructured()
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

      // D2 + Offline Vault: Check IndexedDB ArrayBuffer first (avoids offline 206 Range errors!), then prefetch cache, then HTTP stream
      const openPdfPromise = (async () => {
        if (window.OfflineVault && typeof window.OfflineVault.getVaultedBook === 'function') {
          const vaulted = await window.OfflineVault.getVaultedBook(book.hash);
          if (vaulted?.pdfBuffer) {
            const loadingTask = window.pdfjsLib.getDocument({
              data: vaulted.pdfBuffer.slice(0),
              cMapUrl: `${PDFJS_CDN_BASE}cmaps/`,
              cMapPacked: true,
              standardFontDataUrl: `${PDFJS_CDN_BASE}standard_fonts/`
            });
            currentPdfLoadingTask = loadingTask;
            return loadingTask.promise;
          }
        }
        if (pdfPrefetchCache.has(book.hash)) {
          const cached = pdfPrefetchCache.get(book.hash);
          if (cached?.cleanupTimer) clearTimeout(cached.cleanupTimer);
          currentPdfLoadingTask = cached.task;
          pdfPrefetchCache.delete(book.hash);
          return cached.promise;
        }
        const loadingTask = window.pdfjsLib.getDocument(buildPdfDocumentParams(pdfUrl));
        currentPdfLoadingTask = loadingTask;
        return loadingTask.promise;
      })();

      openPdfPromise
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
      if (typeof flushReadingHeartbeat === 'function') {
        void flushReadingHeartbeat();
      }
      if (typeof stopNeuralTTS === 'function' && isSpeaking) {
        stopNeuralTTS();
      }
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
      closeDocTypographyPopover();
      pdfBookmarksMap.clear();
      epubFootnotesMap = {};
      const ocrPill = document.getElementById('pdf-ocr-status-pill');
      if (ocrPill) ocrPill.style.display = 'none';
      const thumbsListEl = document.getElementById('pdf-thumbs-list');
      if (thumbsListEl) thumbsListEl.dataset.builtForHash = '';
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
      closeDocTypographyPopover();
      if (thumbLazyObserver) {
        try { thumbLazyObserver.disconnect(); } catch (_) {}
        thumbLazyObserver = null;
      }
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
        const progUrl = `/api/books/${targetHash}/progress`;
        if (!navigator.onLine && window.OfflineVault) {
          void window.OfflineVault.enqueueOfflineMutation(progUrl, 'PATCH', payload);
          return;
        }
        apiFetch(progUrl, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }).catch(err => {
          console.warn("Okuma ilerlemesi kaydedilemedi, çevrimdışı kuyruğa alındı:", err);
          if (window.OfflineVault) {
            void window.OfflineVault.enqueueOfflineMutation(progUrl, 'PATCH', payload);
          }
        });
      }, 400);
    }

    function syncBookTotalPagesIfNeeded(book, totalPages) {
      if (!book || !totalPages || totalPages <= 0) return;
      const prevTotal = Number.parseInt(book.sayfa_sayisi || book.pages || 0, 10);
      book.sayfa_sayisi = totalPages;
      if (prevTotal !== totalPages && (book.okunulan_sayfa > 0 || pdfPageNum > 1)) {
        const currentRead = Math.max(1, Number.parseInt(book.okunulan_sayfa || pdfPageNum || 1, 10));
        syncBookProgressMemoryAndCard(book.hash, currentRead, totalPages);
        apiFetch(`/api/books/${book.hash}/progress`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            page: currentRead,
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

        const nativeChars = (textContent?.items || []).reduce(
          (acc, it) => acc + String(it?.str || '').trim().length,
          0
        );

        if (nativeChars >= 15) {
          const textRenderTask = window.pdfjsLib.renderTextLayer({
            textContentSource: textContent,
            container: textLayer,
            viewport: viewport,
            textDivs: []
          });
          await textRenderTask.promise;
          if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;
        } else if (activeWorkspaceBook?.hash) {
          // Scanned (image-only) PDF page detected -> inject invisible normalized OCR bounding-box spans
          const ocrPill = document.getElementById('pdf-ocr-status-pill');
          const ocrPillText = document.getElementById('pdf-ocr-status-text');
          if (ocrPill) {
            ocrPill.style.display = 'inline-flex';
            if (ocrPillText) ocrPillText.textContent = `OCR s.${pageNum}...`;
          }
          try {
            const ocrResp = await apiFetch(
              `/api/books/${encodeURIComponent(activeWorkspaceBook.hash)}/ocr-page/${pageNum}`
            );
            if (myGen !== pdfRenderGeneration || mySession !== workspaceSessionToken) return;
            const ocrData = ocrResp?.ok ? await ocrResp.json() : null;
            if (ocrData?.available && Array.isArray(ocrData.words) && ocrData.words.length > 0) {
              const cssW = Math.max(1, Math.round(viewport.width));
              const cssH = Math.max(1, Math.round(viewport.height));
              const frag = document.createDocumentFragment();
              for (const w of ocrData.words) {
                const sp = document.createElement('span');
                sp.className = 'ocr-word-span';
                sp.textContent = String(w.t || '') + ' ';
                const wx = Math.max(0, Number(w.x || 0) * cssW);
                const wy = Math.max(0, Number(w.y || 0) * cssH);
                const ww = Math.max(4, Number(w.w || 0.02) * cssW);
                const wh = Math.max(6, Number(w.h || 0.02) * cssH);
                sp.style.left = `${wx.toFixed(1)}px`;
                sp.style.top = `${wy.toFixed(1)}px`;
                sp.style.width = `${ww.toFixed(1)}px`;
                sp.style.height = `${wh.toFixed(1)}px`;
                sp.style.fontSize = `${Math.max(7, wh * 0.84).toFixed(1)}px`;
                frag.appendChild(sp);
              }
              textLayer.appendChild(frag);
              if (ocrData.full_text) {
                pdfSearchTextCache[pageNum] = ocrData.full_text;
              }
              if (ocrPillText) ocrPillText.textContent = 'OCR Aktif · Tümünü İndeksle';
            } else if (ocrPillText) {
              ocrPillText.textContent = 'Taranmış Sayfa';
            }
          } catch (ocrErr) {
            console.debug('Sayfa OCR katmanı alınamadı:', pageNum, ocrErr);
          }
        }

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
        const ttsLayer = document.getElementById(`pdf-tts-layer-${pageNum}`);
        if (ttsLayer) {
          ttsLayer.style.width = `${cssW}px`;
          ttsLayer.style.height = `${cssH}px`;
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
            const ttsLayer = document.getElementById(`pdf-tts-layer-${p}`);
            if (ttsLayer) {
              ttsLayer.style.width = `${cssW}px`;
              ttsLayer.style.height = `${cssH}px`;
              ttsLayer.innerHTML = "";
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

    function onPdfContainerScroll() {
      hideFloatingBar();
      const fnPop = document.getElementById('epub-footnote-popover');
      if (fnPop?.classList.contains('visible')) {
        fnPop.classList.remove('visible');
        fnPop.setAttribute('aria-hidden', 'true');
      }
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0;
        checkVisiblePagesAndRender();
      });
    }

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
        if (activeNavDrawerTab === 'thumbs') {
          buildThumbnailsGrid();
        } else if (activeNavDrawerTab === 'bookmarks') {
          renderBookmarksList();
        }
      }
      if (pdfDoc && pdfIsFitWidth && typeof resizeAllPagesForZoom === 'function') {
        setTimeout(() => resizeAllPagesForZoom(), 180);
      }
    }
    window.toggleTocSidebar = toggleTocSidebar;

    function switchTocDrawerTab(tabName) {
      activeNavDrawerTab = ['outline', 'thumbs', 'bookmarks'].includes(tabName) ? tabName : 'outline';
      const tabs = {
        outline: { btn: 'toc-tab-outline', pane: 'pdf-toc-list' },
        thumbs: { btn: 'toc-tab-thumbs', pane: 'pdf-thumbs-list' },
        bookmarks: { btn: 'toc-tab-bookmarks', pane: 'pdf-bookmarks-list' }
      };
      Object.entries(tabs).forEach(([key, cfg]) => {
        const b = document.getElementById(cfg.btn);
        const p = document.getElementById(cfg.pane);
        const isActive = key === activeNavDrawerTab;
        if (b) {
          b.classList.toggle('active', isActive);
          b.setAttribute('aria-selected', String(isActive));
        }
        if (p) {
          p.style.display = isActive ? (key === 'thumbs' ? 'grid' : 'flex') : 'none';
        }
      });
      if (activeNavDrawerTab === 'thumbs') {
        buildThumbnailsGrid();
      } else if (activeNavDrawerTab === 'bookmarks') {
        renderBookmarksList();
      }
    }
    window.switchTocDrawerTab = switchTocDrawerTab;

    function buildThumbnailsGrid() {
      const grid = document.getElementById('pdf-thumbs-list');
      if (!grid) return;
      if (!activeWorkspaceBook || pdfPageCount <= 0) {
        grid.innerHTML = '<div class="pdf-notes-empty" style="grid-column:1/-1;">Sayfa önizlemeleri henüz hazır değil.</div>';
        return;
      }
      const targetKey = `${activeWorkspaceBook.hash}:${pdfPageCount}`;
      if (grid.dataset.builtForHash === targetKey && grid.children.length > 0) {
        grid.querySelectorAll('.pdf-thumb-card.active').forEach(el => el.classList.remove('active'));
        const curEl = grid.querySelector(`.pdf-thumb-card[data-thumb-page="${pdfPageNum}"]`);
        if (curEl) {
          curEl.classList.add('active');
          curEl.scrollIntoView({ block: 'nearest' });
        }
        return;
      }

      if (thumbLazyObserver) {
        try { thumbLazyObserver.disconnect(); } catch (_) {}
        thumbLazyObserver = null;
      }

      grid.innerHTML = '';
      grid.dataset.builtForHash = targetKey;
      const frag = document.createDocumentFragment();

      for (let p = 1; p <= pdfPageCount; p++) {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'pdf-thumb-card' + (p === pdfPageNum ? ' active' : '');
        card.dataset.thumbPage = String(p);
        if (isDocReaderMode && docReaderPages[p - 1]) {
          const pgObj = docReaderPages[p - 1];
          const previewTxt = esc(String(pgObj.text || '').slice(0, 85));
          card.innerHTML = `
            <div class="pdf-thumb-doc-mini">
              <div class="thumb-doc-title">${esc(pgObj.title || `Bölüm`)}</div>
              <div class="thumb-doc-lines">${previewTxt}</div>
            </div>
            <span class="pdf-thumb-num">${p}</span>
          `;
        } else {
          card.innerHTML = `
            <div class="pdf-thumb-frame">
              <span class="pdf-thumb-placeholder">${p}</span>
            </div>
            <span class="pdf-thumb-num">${p}</span>
          `;
        }
        card.addEventListener('click', () => {
          jumpToPdfPage(p);
          if (isMobileReaderViewport()) {
            document.getElementById('pdf-toc-sidebar')?.classList.remove('open');
            document.getElementById('pdf-toc-sidebar-btn')?.classList.remove('active');
          }
        });
        frag.appendChild(card);
      }
      grid.appendChild(frag);

      if (pdfDoc && typeof IntersectionObserver === 'function') {
        const mySession = workspaceSessionToken;
        thumbLazyObserver = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const cardEl = entry.target;
            if (cardEl.dataset.rendered === '1') return;
            cardEl.dataset.rendered = '1';
            const pNo = Number.parseInt(cardEl.dataset.thumbPage || '1', 10);
            if (!pdfDoc || Number.isNaN(pNo)) return;
            pdfDoc.getPage(pNo).then(page => {
              if (mySession !== workspaceSessionToken) return;
              const vp = page.getViewport({ scale: 0.22 });
              const cv = document.createElement('canvas');
              cv.className = 'pdf-thumb-canvas';
              cv.width = Math.max(1, Math.round(vp.width));
              cv.height = Math.max(1, Math.round(vp.height));
              const ctx = cv.getContext('2d', { alpha: false });
              return page.render({ canvasContext: ctx, viewport: vp }).promise.then(() => {
                if (mySession !== workspaceSessionToken) return;
                const frame = cardEl.querySelector('.pdf-thumb-frame');
                if (frame) {
                  frame.innerHTML = '';
                  frame.appendChild(cv);
                }
              });
            }).catch(() => {});
          });
        }, { root: grid, rootMargin: '200px 0px' });

        grid.querySelectorAll('.pdf-thumb-card').forEach(el => thumbLazyObserver.observe(el));
      }
    }
    window.buildThumbnailsGrid = buildThumbnailsGrid;

    function syncPageBookmarkRibbons() {
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return;
      container.querySelectorAll('.page-bookmark-ribbon').forEach(el => el.remove());
      pdfBookmarksMap.forEach((label, pNo) => {
        const wrap = document.getElementById(`pdf-page-wrapper-${pNo}`);
        if (wrap) {
          const rib = document.createElement('div');
          rib.className = 'page-bookmark-ribbon';
          rib.title = label || `Yer İmi · Sayfa ${pNo}`;
          rib.innerHTML = '<i class="fas fa-bookmark"></i>';
          wrap.appendChild(rib);
        }
      });
    }
    window.syncPageBookmarkRibbons = syncPageBookmarkRibbons;

    function renderBookmarksList() {
      const listEl = document.getElementById('pdf-bookmarks-list');
      if (!listEl) return;
      if (pdfBookmarksMap.size === 0) {
        listEl.innerHTML = '<div class="pdf-notes-empty">Henüz yer imi eklemediniz. Üst çubuktaki yer imi simgesine veya B tuşuna basarak ekleyebilirsiniz.</div>';
        return;
      }
      const sorted = [...pdfBookmarksMap.entries()].sort((a, b) => a[0] - b[0]);
      listEl.innerHTML = '';
      sorted.forEach(([pNo, label]) => {
        const row = document.createElement('div');
        row.className = 'pdf-bookmark-row';
        row.innerHTML = `
          <button type="button" class="pdf-toc-item bookmark-jump-btn">
            <i class="fas fa-bookmark" style="color:var(--accent); margin-right:8px;"></i>
            <span style="flex:1;">${esc(label || `Sayfa ${pNo}`)}</span>
            <span class="bookmark-page-pill">s. ${pNo}</span>
          </button>
          <button type="button" class="bookmark-del-btn" title="Yer imini kaldır" aria-label="Yer imini kaldır">
            <i class="fas fa-trash-alt"></i>
          </button>
        `;
        row.querySelector('.bookmark-jump-btn')?.addEventListener('click', () => {
          jumpToPdfPage(pNo);
          if (isMobileReaderViewport()) {
            document.getElementById('pdf-toc-sidebar')?.classList.remove('open');
          }
        });
        row.querySelector('.bookmark-del-btn')?.addEventListener('click', (ev) => {
          ev.stopPropagation();
          void removeBookmarkAtPage(pNo);
        });
        listEl.appendChild(row);
      });
    }
    window.renderBookmarksList = renderBookmarksList;

    async function loadBookBookmarks(bookHash, mySession) {
      if (!bookHash) return;
      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(bookHash)}/bookmarks`);
        if (mySession !== undefined && mySession !== workspaceSessionToken) return;
        const data = res?.ok ? await res.json() : null;
        pdfBookmarksMap.clear();
        if (Array.isArray(data?.bookmarks)) {
          data.bookmarks.forEach(b => {
            const p = Number.parseInt(b.sayfa_no, 10);
            if (!Number.isNaN(p) && p >= 1) {
              pdfBookmarksMap.set(p, b.etiket || `Sayfa ${p}`);
            }
          });
        }
        syncPageIndicatorUI();
        syncPageBookmarkRibbons();
        renderBookmarksList();
      } catch (e) {
        console.debug('Bookmarks load warning:', e);
      }
    }

    async function toggleCurrentPageBookmark() {
      if (!activeWorkspaceBook?.hash || !pdfPageNum) return;
      const targetPage = pdfPageNum;
      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(activeWorkspaceBook.hash)}/bookmarks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sayfa_no: targetPage, toggle: true })
        });
        const data = res?.ok ? await res.json() : null;
        if (!data) return;
        if (data.bookmarked) {
          pdfBookmarksMap.set(targetPage, data.etiket || `Sayfa ${targetPage}`);
          if (typeof showToast === 'function') showToast(`Sayfa ${targetPage} yer imlerine eklendi.`, 'success');
        } else {
          pdfBookmarksMap.delete(targetPage);
          if (typeof showToast === 'function') showToast(`Sayfa ${targetPage} yer imi kaldırıldı.`, 'info');
        }
        syncPageIndicatorUI();
        syncPageBookmarkRibbons();
        renderBookmarksList();
      } catch (_err) {
        if (typeof showToast === 'function') showToast('Yer imi kaydedilemedi.', 'error');
      }
    }
    window.toggleCurrentPageBookmark = toggleCurrentPageBookmark;

    async function removeBookmarkAtPage(pageNum) {
      if (!activeWorkspaceBook?.hash) return;
      try {
        await apiFetch(`/api/books/${encodeURIComponent(activeWorkspaceBook.hash)}/bookmarks/${pageNum}`, {
          method: 'DELETE'
        });
        pdfBookmarksMap.delete(pageNum);
        syncPageIndicatorUI();
        syncPageBookmarkRibbons();
        renderBookmarksList();
      } catch (_err) {}
    }
    window.removeBookmarkAtPage = removeBookmarkAtPage;

    async function triggerCurrentBookOcrIndex() {
      if (!activeWorkspaceBook?.hash) return;
      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(activeWorkspaceBook.hash)}/ocr-index`, {
          method: 'POST'
        });
        if (res?.ok) {
          if (typeof showToast === 'function') {
            showToast('Taranmış kitabın tüm sayfaları arka planda OCR ile indeksleniyor.', 'success');
          }
          const pillTxt = document.getElementById('pdf-ocr-status-text');
          if (pillTxt) pillTxt.textContent = 'OCR Arka Planda Çalışıyor';
          if (typeof fetchTasksFromAPI === 'function') void fetchTasksFromAPI();
        }
      } catch (_e) {
        if (typeof showToast === 'function') showToast('OCR indeksleme başlatılamadı.', 'error');
      }
    }
    window.triggerCurrentBookOcrIndex = triggerCurrentBookOcrIndex;

    // ─── EPUB / TXT Typography Controls & Inline Footnote Popover ────────────
    function applyDocTypographyPrefs() {
      const container = document.getElementById('pdf-canvas-container');
      const fontMap = {
        serif: "var(--font-serif, 'Newsreader', Georgia, serif)",
        sans: "var(--font-ui, 'Geist', system-ui, sans-serif)",
        classic: "Georgia, 'Times New Roman', serif",
        accessible: "'Verdana', 'Segoe UI', sans-serif"
      };
      const familyCss = fontMap[docTypographyPrefs.font] || fontMap.serif;
      if (container) {
        container.style.setProperty('--doc-font-family', familyCss);
        container.style.setProperty('--doc-line-height', String(docTypographyPrefs.lineHeight || '1.78'));
        container.style.setProperty('--doc-max-width', String(docTypographyPrefs.maxWidth || '740px'));
        container.style.setProperty('--doc-letter-spacing', docTypographyPrefs.font === 'accessible' ? '0.025em' : 'normal');
      }
      document.querySelectorAll('[data-typo-font]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.typoFont === docTypographyPrefs.font);
      });
      document.querySelectorAll('[data-typo-lh]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.typoLh === String(docTypographyPrefs.lineHeight));
      });
      document.querySelectorAll('[data-typo-mw]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.typoMw === String(docTypographyPrefs.maxWidth));
      });
    }
    window.applyDocTypographyPrefs = applyDocTypographyPrefs;

    function setDocTypography(key, val) {
      docTypographyPrefs[key] = val;
      try {
        localStorage.setItem('doc_reader_typography', JSON.stringify(docTypographyPrefs));
      } catch (_e) {}
      applyDocTypographyPrefs();
    }
    window.setDocTypography = setDocTypography;

    function toggleDocTypographyPopover(ev) {
      if (ev) ev.stopPropagation();
      const fnPop = document.getElementById('epub-footnote-popover');
      if (fnPop?.classList.contains('visible')) {
        fnPop.classList.remove('visible');
        fnPop.setAttribute('aria-hidden', 'true');
      }
      if (typeof hideCitationPreviewPopover === 'function') {
        hideCitationPreviewPopover(true);
      }
      const pop = document.getElementById('doc-typography-popover');
      const btn = document.getElementById('pdf-typography-btn');
      if (!pop) return;
      const willOpen = pop.style.display === 'none';
      pop.style.display = willOpen ? 'flex' : 'none';
      btn?.classList.toggle('active', willOpen);
      if (willOpen) applyDocTypographyPrefs();
    }
    window.toggleDocTypographyPopover = toggleDocTypographyPopover;

    function closeDocTypographyPopover() {
      const pop = document.getElementById('doc-typography-popover');
      if (pop) pop.style.display = 'none';
      document.getElementById('pdf-typography-btn')?.classList.remove('active');
    }
    window.closeDocTypographyPopover = closeDocTypographyPopover;

    function showEpubFootnotePopover(btnEl) {
      const pop = document.getElementById('epub-footnote-popover');
      if (!pop || !btnEl) return;
      const fnId = btnEl.dataset.fnId || '';
      const fnLabel = btnEl.dataset.fnLabel || '*';
      let bodyTxt = '';
      try { bodyTxt = decodeURIComponent(btnEl.dataset.fnBody || ''); } catch (_e) {}
      if (!bodyTxt && fnId && epubFootnotesMap[fnId]) {
        bodyTxt = epubFootnotesMap[fnId];
      }
      if (!bodyTxt) return;

      pop.innerHTML = `
        <div class="cite-popover-header">
          <span class="cite-popover-badge"><i class="fas fa-asterisk"></i> Dipnot [${esc(fnLabel)}]</span>
          <button type="button" class="cite-popover-jump-btn" onclick="document.getElementById('epub-footnote-popover')?.classList.remove('visible')">Kapat</button>
        </div>
        <blockquote class="cite-popover-quote">${esc(bodyTxt)}</blockquote>
      `;
      pop.classList.add('visible');
      pop.setAttribute('aria-hidden', 'false');

      const r = btnEl.getBoundingClientRect();
      const popRect = pop.getBoundingClientRect();
      const pw = popRect.width || 300;
      const ph = popRect.height || 120;
      const left = Math.max(10, Math.min(r.left - pw / 2 + r.width / 2, window.innerWidth - pw - 10));
      const top = (r.top - ph - 10 >= 10) ? (r.top - ph - 10) : Math.min(window.innerHeight - ph - 10, r.bottom + 10);
      pop.style.left = `${Math.round(left)}px`;
      pop.style.top = `${Math.round(top)}px`;
    }

    document.addEventListener('click', (e) => {
      const fnBtn = e.target?.closest?.('.epub-footnote-ref');
      if (fnBtn) {
        e.preventDefault();
        e.stopPropagation();
        showEpubFootnotePopover(fnBtn);
        return;
      }
      const fnPop = document.getElementById('epub-footnote-popover');
      if (fnPop?.classList.contains('visible') && !fnPop.contains(e.target)) {
        fnPop.classList.remove('visible');
        fnPop.setAttribute('aria-hidden', 'true');
      }
      const typoPop = document.getElementById('doc-typography-popover');
      const typoBtn = document.getElementById('pdf-typography-btn');
      if (typoPop && typoPop.style.display !== 'none' && !typoPop.contains(e.target) && !typoBtn?.contains(e.target)) {
        closeDocTypographyPopover();
      }
    });

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
        let prevOrigLum = 255;
        let prev2OrigLum = 255;
        for (let i = 0; i < count; i++) {
          const px = u32[i];
          const r = px & 0xFF;
          const g = (px >> 8) & 0xFF;
          const b = (px >> 16) & 0xFF;
          const a = px & 0xFF000000;

          // Fast path: pure/near-white paper background (~80% of book pixels) -> 1 bitwise op
          if (r >= 246 && g >= 246 && b >= 246) {
            prev2OrigLum = prevOrigLum;
            prevOrigLum = 255;
            u32[i] = a | paperDarkBase;
            continue;
          }

          const lum = (r * 77 + g * 150 + b * 29) >> 8;
          const maxC = r > g ? (r > b ? r : b) : (g > b ? g : b);
          const minC = r < g ? (r < b ? r : b) : (g < b ? g : b);

          // Distinguish ClearType LCD subpixel glyph anti-aliasing (1-2px transition between white paper & dark ink)
          // from genuine chromatic illustrations, diagrams, covers & photos
          if ((maxC - minC) > 36) {
            let next1Lum = 255;
            let next2Lum = 255;
            if (i + 1 < count) {
              const p1 = u32[i + 1];
              next1Lum = ((p1 & 0xFF) * 77 + ((p1 >> 8) & 0xFF) * 150 + ((p1 >> 16) & 0xFF) * 29) >> 8;
            }
            if (i + 2 < count) {
              const p2 = u32[i + 2];
              next2Lum = ((p2 & 0xFF) * 77 + ((p2 >> 8) & 0xFF) * 150 + ((p2 >> 16) & 0xFF) * 29) >> 8;
            }
            const nearPaper = prevOrigLum >= 235 || prev2OrigLum >= 235 || next1Lum >= 235 || next2Lum >= 235;
            const nearInk = lum <= 135 || prevOrigLum <= 135 || prev2OrigLum <= 135 || next1Lum <= 135 || next2Lum <= 135;
            if (!(nearPaper && nearInk)) {
              prev2OrigLum = prevOrigLum;
              prevOrigLum = lum;
              continue;
            }
          }

          prev2OrigLum = prevOrigLum;
          prevOrigLum = lum;
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

    window.pdfPrevPage = pdfPrevPage;
    window.pdfNextPage = pdfNextPage;
    window.pdfGoToPageFromInput = pdfGoToPageFromInput;
    window.pdfZoomIn = pdfZoomIn;
    window.pdfZoomOut = pdfZoomOut;
    window.pdfFitWidth = pdfFitWidth;
    window.pdfFitHeight = pdfFitHeight;
    window.onPdfContainerScroll = onPdfContainerScroll;
