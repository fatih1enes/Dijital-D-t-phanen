/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_state.js — Shared Reader & Workspace State + Core Viewport/Escape Helpers
 * ════════════════════════════════════════════════════════════════════════════════ */

    let activeWorkspaceBook = null;
    let isWorkspaceChatLoading = false;
    let isFullBookLoaded = false;
    let activeTypewriterTimer = null;
    let activeTypewriterFullText = '';
    let activeTypewriterContainer = null;
    let activeChatAbortController = null;
    const workspaceCitationsByPage = new Map();
    const pdfBookmarksMap = new Map();
    let activeNavDrawerTab = 'outline';
    let thumbLazyObserver = null;
    let epubFootnotesMap = {};
    let docTypographyPrefs = { font: 'serif', lineHeight: '1.78', maxWidth: '740px' };
    try {
      const savedTypo = JSON.parse(localStorage.getItem('doc_reader_typography') || 'null');
      if (savedTypo && typeof savedTypo === 'object') {
        docTypographyPrefs = { ...docTypographyPrefs, ...savedTypo };
      }
    } catch (_typoErr) {}
    let isSpeaking = false;
    let workspaceSessionToken = 0;
    let currentPdfLoadingTask = null;
    let pdfRenderGeneration = 0;
    let isDocReaderMode = false;
    let docReaderPages = [];
    let docReaderFormat = 'pdf';

    const READER_SURFACES = ['normal', 'sepia', 'eink', 'chromaguard'];
    let currentReaderSurfaceMode = 'normal';
    try {
      currentReaderSurfaceMode = localStorage.getItem('pdf_reader_surface_mode') || 'normal';
    } catch (e) {}

    let copyChatBtnTimeout = null;
    let lastChatFlex = null;
    let lastPdfFlex = null;
    let workspaceChatPaneTimer = null;

    // PDF & Document Viewer State
    let pdfRenderedPages = {};
    let pdfRenderTasks = {};
    let pdfActiveNoteColorClass = 'yellow';
    let pdfActiveNoteColorHex = '#e8dca0';
    let pdfDoc = null;
    let pdfPageNum = 1;
    let pdfPageCount = 0;
    let pdfScale = 1.2;
    let pdfIsRendering = false;
    let pdfPendingPageNum = null;
    let pdfIsFitWidth = false;
    let pdfIsFitHeight = false;
    let saveProgressDebounceTimer = null;
    let pdfIsSpreadMode = false;
    try {
      pdfIsSpreadMode = localStorage.getItem('pdf_spread_mode') === 'true';
    } catch (_) {}

    // Annotations & Selection State
    let pdfHighlights = {};
    let pdfNotes = {};
    let pdfSelectedText = "";
    let pdfSelectionRanges = [];
    let pdfActiveHighlightIdForNote = null;

    const activeTextLayersMap = new Map();
    const pageGeometryCache = new Map();
    let selectionChangeAbortController = null;
    let prevSelectionRange = null;
    let isUserSelectingText = false;
    let selectionDragState = null;
    let selectionCheckTimer = null;

    // Prefetch, Zoom & Scroll State
    const PDFJS_CDN_BASE = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';
    const pdfPrefetchCache = new Map();
    let zoomWillChangeTimer = null;
    let wheelZoomCommitTimer = null;
    let wheelFocalState = null;
    let wheelBaseScale = null;
    let scrollRaf = 0;
    let resizeSpreadTimer = null;
    let handoffCountdownTimer = null;

    // In-Document Search State
    let pdfSearchQuery = "";
    let pdfSearchResults = [];
    let pdfSearchCurrentMatchIdx = -1;
    let pdfSearchPageMatchesCount = {};
    let pdfSearchTextCache = {};
    let isPdfSearchOpen = false;
    let isPdfSearchDrawerOpen = false;
    let pdfSearchDebounceTimer = null;
    let pdfSearchToken = 0;
    let _pdfSearchTriggerEl = null;

    function isMobileReaderViewport() {
      return window.innerWidth <= 860;
    }
    window.isMobileReaderViewport = isMobileReaderViewport;

    function handleWorkspaceEscape() {
      const fnPop = document.getElementById('epub-footnote-popover');
      if (fnPop && fnPop.classList.contains('visible')) {
        fnPop.classList.remove('visible');
        fnPop.setAttribute('aria-hidden', 'true');
        return true;
      }
      const citePop = document.getElementById('citation-preview-popover');
      if (citePop && citePop.classList.contains('visible')) {
        citePop.classList.remove('visible');
        citePop.setAttribute('aria-hidden', 'true');
        return true;
      }
      const typoPop = document.getElementById('doc-typography-popover');
      if (typoPop && typoPop.style.display !== 'none') {
        typoPop.style.display = 'none';
        document.getElementById('pdf-typography-btn')?.classList.remove('active');
        return true;
      }
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
      if (pageInput) {
        const maxPg = Math.max(1, pdfPageCount || 1);
        pageInput.value = pdfPageNum;
        pageInput.max = String(maxPg);
        pageInput.setAttribute('aria-valuemax', String(maxPg));
      }
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

      const isBookmarked = pdfBookmarksMap.has(pdfPageNum);
      document.getElementById('pdf-bookmark-btn')?.classList.toggle('active', isBookmarked);
      document.getElementById('mobile-bookmark-btn')?.classList.toggle('active', isBookmarked);

      const thumbsRoot = document.getElementById('pdf-thumbs-list');
      if (thumbsRoot && activeNavDrawerTab === 'thumbs') {
        thumbsRoot.querySelectorAll('.pdf-thumb-card.active').forEach(el => el.classList.remove('active'));
        const activeThumb = thumbsRoot.querySelector(`.pdf-thumb-card[data-thumb-page="${pdfPageNum}"]`);
        if (activeThumb) activeThumb.classList.add('active');
      }
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

