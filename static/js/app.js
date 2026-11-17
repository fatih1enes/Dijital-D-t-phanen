/* ═══════════ app.js — Application Bootstrap & Initialization ═══════════ */

    function isExternalFileDrag(e) {
      const types = e?.dataTransfer?.types;
      if (!types) return false;
      return Array.from(types).includes('Files');
    }

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

      // Infinite Scroll listener (passive + rAF throttled for 60fps scroll)
      let scrollCheckTicking = false;
      window.addEventListener('scroll', () => {
        if (scrollCheckTicking) return;
        scrollCheckTicking = true;
        requestAnimationFrame(() => {
          scrollCheckTicking = false;
          if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
            if (!window.isLoadingMore && (window.allBooks?.length || 0) < (window.totalBooks || 0)) {
              loadBooksFromAPI((window.currentPage || 1) + 1, true).catch(err => console.error(err));
            }
          }
        });
      }, { passive: true });

      // Chat Counter Listener
      const chatInput = document.getElementById('chat-input');
      if (chatInput) {
        chatInput.addEventListener('input', updateChatCounter);
      }

      // Hero drop-box visual highlight (only for external OS file drags; drop is handled centrally by setupGlobalDragDrop)
      const dropBox = document.getElementById('drop-box');
      if (dropBox) {
        dropBox.addEventListener('dragover', (e) => {
          if (!isExternalFileDrag(e)) return;
          e.preventDefault();
          dropBox.classList.add('dragover');
        });
        dropBox.addEventListener('dragleave', () => {
          dropBox.classList.remove('dragover');
        });
        dropBox.addEventListener('drop', (e) => {
          if (!isExternalFileDrag(e)) return;
          e.preventDefault();
          e.stopPropagation();
          dropBox.classList.remove('dragover');
          if (e.dataTransfer?.files?.length > 0) {
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
        if (!overlay || !isExternalFileDrag(e)) return;
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
        window.addEventListener(evt, (e) => {
          if (!isExternalFileDrag(e)) return;
          e.preventDefault();
          show(e);
        });
      });
      window.addEventListener('dragleave', (e) => {
        if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) hide();
      });
      window.addEventListener('drop', (e) => {
        if (!isExternalFileDrag(e)) return;
        e.preventDefault();
        if (e.target?.closest?.('#drop-overlay')) return;
        hide();
        if (e.dataTransfer?.files?.length > 0) {
          handleFiles(e.dataTransfer.files);
        }
      });
      if (overlay) {
        overlay.addEventListener('drop', (e) => {
          if (!isExternalFileDrag(e)) {
            hide();
            return;
          }
          e.preventDefault();
          e.stopPropagation();
          hide();
          if (e.dataTransfer?.files?.length > 0) {
            handleFiles(e.dataTransfer.files);
          }
        });
      }
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
      document.querySelectorAll('#compact-theme-btn, .compact-theme-btn, .compact-theme-toggle').forEach(btn => {
        btn.innerHTML = iconHTML;
      });
    }

    function toggleTheme() {
      const html = document.documentElement;
      const next = html.dataset.theme === 'dark' ? 'light' : 'dark';

      const apply = () => {
        html.dataset.theme = next;
        try {
          localStorage.setItem('kutuphane-theme', next);
          localStorage.setItem('theme', next);
        } catch (_e) {
          /* Storage unavailable */
        }
        updateThemeIcons(next, true);
        updateThemeMeta(next);
      };

      if (window.Motion && typeof window.Motion.transition === 'function') {
        html.classList.add('theme-transitioning');
        void window.Motion.transition(apply).finally(() => {
          html.classList.remove('theme-transitioning');
        });
        return;
      }

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        apply();
        return;
      }

      document.startViewTransition(apply);
    }

    // Sayfa yüklenirken kaydedilmiş veya sistem tema tercihini uygula
    (function () {
      let saved = document.documentElement.dataset.theme;
      try {
        saved = localStorage.getItem('kutuphane-theme') || localStorage.getItem('theme') || saved;
      } catch (_e) {
        /* Storage unavailable */
      }
      if (!saved) {
        saved = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      }
      document.documentElement.dataset.theme = saved;
      updateThemeIcons(saved, false);
      updateThemeMeta(saved);
    })();

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
          const workspace = document.getElementById('workspace-reader');
          const isWorkspaceActive = workspace && workspace.classList.contains('open');
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
