/* ═══════════ app.js — Application Bootstrap & Initialization ═══════════ */

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

      // Infinite Scroll listener
      window.addEventListener('scroll', () => {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
          if (!window.isLoadingMore && (window.allBooks?.length || 0) < (window.totalBooks || 0)) {
            loadBooksFromAPI((window.currentPage || 1) + 1, true).catch(err => console.error(err));
          }
        }
      });

      // Chat Counter Listener
      const chatInput = document.getElementById('chat-input');
      if (chatInput) {
        chatInput.addEventListener('input', updateChatCounter);
      }

      // Sürükle-Bırak Entegrasyonu
      const dropBox = document.getElementById('drop-box');
      if (dropBox) {
        dropBox.addEventListener('dragover', (e) => {
          e.preventDefault();
          dropBox.style.borderColor = 'var(--accent)';
        });
        dropBox.addEventListener('dragleave', () => {
          dropBox.style.borderColor = 'var(--sepia-light)';
        });
        dropBox.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          dropBox.style.borderColor = 'var(--sepia-light)';
          handleFiles(e.dataTransfer.files);
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
        if (!overlay) return;
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
        window.addEventListener(evt, (e) => { e.preventDefault(); show(e); });
      });
      window.addEventListener('dragleave', (e) => {
        if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) hide();
      });
      window.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.target?.closest?.('#drop-overlay')) return;
        hide();
        handleFiles(e.dataTransfer.files);
      });
      if (overlay) {
        overlay.addEventListener('drop', (e) => {
          e.preventDefault();
          e.stopPropagation();
          hide();
          handleFiles(e.dataTransfer.files);
        });
      }
      document.addEventListener('dragover', (e) => e.preventDefault());
      document.addEventListener('drop', (e) => e.preventDefault());
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
    function toggleTheme() {
      const html = document.documentElement;
      const next = html.dataset.theme === 'dark' ? 'light' : 'dark';

      // İpeksi pürüzsüz geçiş sınıfını etkinleştir
      html.classList.add('theme-transitioning');
      html.dataset.theme = next;
      localStorage.setItem('kutuphane-theme', next);

      const iconHTML = next === 'dark'
        ? '<i class="fas fa-sun theme-icon-spin"></i>'
        : '<i class="fas fa-moon theme-icon-spin"></i>';

      // Butonları senkronize et
      const mainThemeBtn = document.getElementById('theme-toggle');
      if (mainThemeBtn) mainThemeBtn.innerHTML = iconHTML;
      document.querySelectorAll('.compact-theme-toggle').forEach(btn => btn.innerHTML = iconHTML);

      // Geçiş süresi bittiğinde sınıfı temizle
      setTimeout(() => {
        html.classList.remove('theme-transitioning');
      }, 350);
    }

    // Sayfa yüklenirken kaydedilmiş tema tercihini uygula
    (function () {
      const saved = localStorage.getItem('kutuphane-theme') || 'light';
      document.documentElement.dataset.theme = saved;
      const iconHTML = saved === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
      const btn = document.getElementById('theme-toggle');
      if (btn) btn.innerHTML = iconHTML;
      document.querySelectorAll('.compact-theme-toggle').forEach(b => b.innerHTML = iconHTML);
    })();

    // ─── İŞLEM MERKEZİ MANTIĞI ──────────────────────────────────────────

    // ─── MODERN SCROLL LOGIC (Smooth & Zero Jitter) ─────────────────────
    let lastScrollY = window.scrollY;
    const compactNav = document.getElementById('compact-nav');
    const scrollBtn = document.getElementById('scroll-top-btn');

    window.addEventListener('scroll', () => {
      const currentScrollY = window.scrollY;

      if (currentScrollY <= 150) {
        compactNav?.classList.remove('visible');
      } else if (currentScrollY > lastScrollY && currentScrollY > 300) {
        compactNav?.classList.remove('visible');
      } else if (currentScrollY < lastScrollY) {
        compactNav?.classList.add('visible');
      }

      if (currentScrollY > 600) {
        scrollBtn?.classList.add('visible');
      } else {
        scrollBtn?.classList.remove('visible');
      }
      lastScrollY = currentScrollY;
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
