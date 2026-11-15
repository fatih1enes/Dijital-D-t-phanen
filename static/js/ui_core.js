/* ═══════════ ui_core.js — UI Rendering, Grid, Table & Collections ═══════════ */
    window.shouldStagger = true;
    // --- CATEGORY LABELS ---
    function buildCategoryTags() {
      const books = window.allBooks || [];
      const cats = [...new Set(books.map(b => b.category).filter(Boolean))].sort((a, b) => a.localeCompare(b));
      const menu = document.getElementById('category-menu');
      const trigger = document.getElementById('category-trigger');

      let html = `<button type="button" class="dropdown-item ${window.activeCategory === 'all' ? 'active' : ''}" role="option" onclick="selectCat('all', 'Tüm Kategoriler')"><i class="fas fa-layer-group"></i> Tüm Kategoriler</button>`;

      cats.forEach(cat => {
        const encodedCat = encData(cat);
        html += `<button type="button" class="dropdown-item ${window.activeCategory === cat ? 'active' : ''}" role="option" data-value="${encodedCat}" data-label="${encodedCat}" onclick="selectCat(decodeURIComponent(this.dataset.value), decodeURIComponent(this.dataset.label))"><i class="fas fa-tag"></i> ${esc(cat)}</button>`;
      });
      if (menu) menu.innerHTML = html;

      if (trigger) {
        if (window.activeCategory !== 'all') {
          trigger.textContent = window.activeCategory;
        } else {
          trigger.textContent = 'Tüm Kategoriler';
        }
      }
    }

    function selectCat(val, label) {
      window.activeCategory = val;
      const catTrigger = document.getElementById('category-trigger');
      if (catTrigger) catTrigger.textContent = label;
      const dropCat = document.getElementById('dropdown-category');
      if (dropCat) dropCat.classList.remove('open');
      render();
      buildCategoryTags(); // Update active states
    }
    function filterCat(cat) {
      window.activeCategory = cat;
      render();
    }

    function toggleFavFilter() {
      window.showOnlyFav = !window.showOnlyFav;
      const btn = document.getElementById('btn-fav-filter');
      if (btn) btn.classList.toggle('active', window.showOnlyFav);
      render();
    }

    // --- COLLECTIONS ---
    async function loadCollectionsFromAPI() {
      try {
        const res = await apiFetch('/api/collections');
        if (res?.status === 401) {
          window.location.href = '/login';
          return;
        }
        if (res?.ok) {
          window.allCollections = await res.json();
          const menu = document.getElementById('collection-menu');
          const trigger = document.getElementById('collection-trigger');

          let html = `<button type="button" class="dropdown-item ${window.activeCollection === 'all' ? 'active' : ''}" role="option" onclick="selectCol('all', 'Tüm Koleksiyonlar')"><i class="fas fa-folder-open"></i> Tüm Koleksiyonlar</button>`;

          (window.allCollections || []).forEach(c => {
            const encodedName = encData(c.isim);
            html += `<button type="button" class="dropdown-item ${window.activeCollection === String(c.id) ? 'active' : ''}" role="option" data-value="${c.id}" data-label="${encodedName}" onclick="selectCol(this.dataset.value, decodeURIComponent(this.dataset.label))"><i class="fas fa-folder"></i> ${esc(c.isim)}</button>`;
          });
          if (menu) menu.innerHTML = html;

          if (trigger) {
            const activeColObj = (window.allCollections || []).find(c => String(c.id) === window.activeCollection);
            trigger.textContent = activeColObj ? activeColObj.isim : 'Tüm Koleksiyonlar';
          }
        }
      } catch (e) {
        console.error("Koleksiyonlar alınamadı", e);
      }
    }

    function selectCol(val, label) {
      window.activeCollection = String(val);
      const colTrigger = document.getElementById('collection-trigger');
      if (colTrigger) colTrigger.textContent = label;
      const dropCol = document.getElementById('dropdown-collection');
      if (dropCol) closeCustomDropdown(dropCol, { restoreFocus: false });
      render();
      loadCollectionsFromAPI().catch(err => console.warn(err)); // Update active states
    }

    let lastActiveDropdownTrigger = null;

    function openCustomDropdown(el) {
      if (!el) return;
      const menu = el.querySelector('.dropdown-menu');
      const trigger = el.querySelector('.dropdown-trigger') || el.querySelector('button');
      if (trigger) {
        trigger.setAttribute('aria-expanded', 'true');
        lastActiveDropdownTrigger = trigger;
      }
      let firstItem = null;
      if (menu) {
        const items = Array.from(menu.querySelectorAll('.dropdown-item, button, a, [tabindex]')).filter(i => i.offsetParent !== null || window.getComputedStyle(el).display !== 'none');
        items.forEach(item => {
          if (!item.hasAttribute('tabindex')) item.setAttribute('tabindex', '0');
        });
        firstItem = items[0] || null;
      }
      if (menu && window.Motion && typeof window.Motion.enter === 'function') {
        menu.classList.remove('closing');
        el.classList.add('open');
        void window.Motion.enter(menu, {
          className: '',
          origin: 'top center',
          cleanExitClass: 'closing',
          focusEl: firstItem
        });
      } else {
        el.classList.add('open');
        if (firstItem) requestAnimationFrame(() => firstItem.focus({ preventScroll: true }));
      }
    }

    function closeCustomDropdown(el, opts = {}) {
      if (!el) return;
      const restoreFocus = opts.restoreFocus !== false;
      const trigger = el.querySelector('.dropdown-trigger') || el.querySelector('button');
      if (trigger) {
        trigger.setAttribute('aria-expanded', 'false');
      }
      const menu = el.querySelector('.dropdown-menu');
      const finishClose = () => {
        el.classList.remove('open');
        if (restoreFocus && lastActiveDropdownTrigger && el.contains(lastActiveDropdownTrigger)) {
          lastActiveDropdownTrigger.focus({ preventScroll: true });
        }
        if (lastActiveDropdownTrigger && el.contains(lastActiveDropdownTrigger)) {
          lastActiveDropdownTrigger = null;
        }
      };

      if (menu && el.classList.contains('open') && window.Motion && typeof window.Motion.exit === 'function') {
        void window.Motion.exit(menu, {
          className: 'closing',
          afterFn: finishClose
        });
      } else {
        menu?.classList.remove('closing');
        finishClose();
      }
    }

    function toggleDropdown(id) {
      const el = document.getElementById(id);
      if (!el) return;
      const menu = el.querySelector('.dropdown-menu');
      const isOpen = el.classList.contains('open') && !(menu && menu.classList.contains('closing'));

      // Close others without stealing focus back
      document.querySelectorAll('.custom-dropdown.open').forEach(d => {
        if (d !== el) closeCustomDropdown(d, { restoreFocus: false });
      });

      if (!isOpen) {
        openCustomDropdown(el);
      } else {
        closeCustomDropdown(el, { restoreFocus: true });
      }
    }

    // Global click listener to close dropdowns
    window.addEventListener('click', (e) => {
      if (!e.target?.closest?.('.custom-dropdown')) {
        document.querySelectorAll('.custom-dropdown.open').forEach(d => closeCustomDropdown(d, { restoreFocus: false }));
      }
    });

    // Klavye erişilebilirliği: ↑, ↓ gezinme, Enter ile seçim, Esc ile kapatma ve tetikleyiciye odak dönüşü
    document.addEventListener('keydown', (e) => {
      const activeDropdown = document.querySelector('.custom-dropdown.open');
      const toolsMenu = document.getElementById('header-tools-menu');
      const isToolsOpen = toolsMenu && toolsMenu.style.display !== 'none' && !toolsMenu.classList.contains('closing');

      if (!activeDropdown && !isToolsOpen) return;

      const activeMenu = activeDropdown
        ? activeDropdown.querySelector('.dropdown-menu')
        : toolsMenu;

      if (!activeMenu) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        if (activeDropdown) closeCustomDropdown(activeDropdown, { restoreFocus: true });
        if (isToolsOpen && typeof closeToolsMenu === 'function') closeToolsMenu({ restoreFocus: true });
        return;
      }

      const items = Array.from(activeMenu.querySelectorAll('.dropdown-item, .tools-menu-item, button, a, [tabindex="0"]')).filter(i => i.offsetParent !== null);
      if (items.length === 0) return;

      const currentIndex = items.indexOf(document.activeElement);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextIndex = (currentIndex + 1) % items.length;
        items[nextIndex].focus();
        return;
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevIndex = (currentIndex - 1 + items.length) % items.length;
        items[prevIndex].focus();
        return;
      }

      if (e.key === 'Enter') {
        if (document.activeElement && items.includes(document.activeElement)) {
          e.preventDefault();
          document.activeElement.click();
          if (activeDropdown) closeCustomDropdown(activeDropdown);
          if (isToolsOpen && typeof closeToolsMenu === 'function') closeToolsMenu();
        }
      }
    });

    function filterCol(colId) {
      window.activeCollection = String(colId);
      render();
    }

    function openColModal(hash) {
      window.colTargetHash = hash;
      const list = document.getElementById('col-list');
      if (!list) return;
      const book = (window.allBooks || []).find(b => b.hash === hash);
      const bookCols = book?.collections ? book.collections.map(String) : [];
      const collections = window.allCollections || [];

      if (collections.length === 0) {
        list.innerHTML = '<div style="color:var(--muted); font-style:italic; font-size:0.85rem; text-align:center; padding: 2rem 0;"><i class="fas fa-folder-open" style="font-size:2rem; opacity:0.3; margin-bottom:1rem; display:block;"></i>Henüz koleksiyon bulunmuyor.<br>Aşağıdan yeni bir liste oluşturabilirsiniz.</div>';
      } else {
        list.innerHTML = collections.map(c => {
          const inCol = bookCols.includes(String(c.id));
          const encodedName = encData(c.isim);
          return `
      <div class="col-row col-list-item">
         <div class="col-item-meta">
            <i class="fas fa-folder col-item-icon"></i>
            <span class="col-item-name">${esc(c.isim)}</span>
         </div>
         <div class="col-item-actions">
           <button type="button" class="col-toggle-btn ${inCol ? 'is-in-col' : ''}" onclick="event.stopPropagation(); toggleBookCol(${c.id}, ${!inCol})">
               ${inCol ? '<i class="fas fa-minus" style="font-size:0.6rem"></i> Çıkar' : '<i class="fas fa-plus" style="font-size:0.6rem"></i> Ekle'}
           </button>
           
           <div class="custom-dropdown share-dropdown" style="position:relative; display:inline-block; min-width: auto;">
             <button type="button" class="col-icon-btn" onclick="event.stopPropagation(); toggleShareMenu(this)" title="Paylaş" aria-label="Koleksiyonu Paylaş">
                 <i class="fas fa-share-alt"></i>
             </button>
             <div class="dropdown-menu" style="right:0; top:calc(100% + 5px); min-width:180px; z-index:100; left:auto; width:auto; padding:0.4rem;">
                <button type="button" class="dropdown-item" role="menuitem" style="padding:0.6rem 0.8rem;" onclick="window.location.href='/api/share-collection/${c.id}'"><i class="fas fa-file-download"></i> JSON İndir</button>
                <button type="button" class="dropdown-item" role="menuitem" style="padding:0.6rem 0.8rem;" onclick="copyCollectionMarkdown(${c.id}, decodeURIComponent('${encodedName}'))"><i class="fas fa-copy"></i> Markdown Kopyala</button>
             </div>
           </div>

           <button type="button" class="col-icon-btn col-icon-btn--danger" onclick="event.stopPropagation(); deleteCollection(${c.id})" title="Koleksiyonu Sil" aria-label="Koleksiyonu Sil">
               <i class="fas fa-trash-alt"></i>
           </button>
         </div>
      </div>
      `;
        }).join('');
      }

      const importBtn = `
        <div style="margin-top: 1rem; border-top: 1px solid var(--line); padding-top: 1.2rem;">
          <button class="btn-modal-secondary" style="width:100%; padding: 0.9rem; border-radius: 12px; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 0.6rem; font-family:'Geist', sans-serif;" onclick="importCollection()">
            <i class="fas fa-file-import"></i> Dışarıdan Koleksiyon Aktar (JSON)
          </button>
        </div>
      `;
      list.innerHTML += importBtn;
      list.style.overflowX = 'hidden'; // Ensure no horizontal scroll

      const colModal = document.getElementById('col-modal');
      if (colModal) {
        const triggerEl = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        colModal._sourceTriggerEl = triggerEl;
        const modalBox = colModal.querySelector('.modal');
        if (modalBox && triggerEl && triggerEl !== document.body && typeof triggerEl.getBoundingClientRect === 'function') {
          const r = triggerEl.getBoundingClientRect();
          if (r.width > 0 || r.height > 0) {
            modalBox.style.setProperty('--modal-origin-x', `${Math.round(r.left + r.width / 2)}px`);
            modalBox.style.setProperty('--modal-origin-y', `${Math.round(r.top + r.height / 2)}px`);
          }
        }
        colModal.classList.remove('closing');
        document.body.classList.add('modal-open');
        if (window.Motion && typeof window.Motion.enter === 'function') {
          void window.Motion.enter(colModal, { className: '', addClass: 'open', cleanExitClass: 'closing' });
        } else {
          colModal.classList.add('open');
        }
        activateModalFocus(colModal);
      }
    }

    function toggleShareMenu(btn) {
      const container = btn.parentElement;
      const menu = container?.querySelector('.dropdown-menu');
      const isOpen = container?.classList.contains('open') && !(menu && menu.classList.contains('closing'));
      document.querySelectorAll('.custom-dropdown.open').forEach(m => {
        if (m !== container) closeCustomDropdown(m, { restoreFocus: false });
      });
      if (!container) return;
      if (!isOpen) {
        openCustomDropdown(container);
      } else {
        closeCustomDropdown(container, { restoreFocus: true });
      }
    }

    async function deleteCollection(colId) {
      const ok = await (window.showAppConfirm ? window.showAppConfirm("Koleksiyonu silmek istediğinize emin misiniz? (İçindeki kitaplar silinmez, sadece liste silinir)", "Koleksiyonu Sil", "Sil", true) : Promise.resolve(confirm("Koleksiyonu silmek istediğinize emin misiniz?")));
      if (!ok) return;
      try {
        const res = await apiFetch(`/api/collections/${colId}`, { method: 'DELETE' });
        if (res?.ok) {
          // Remove this collection ID from the local books cache
          (window.allBooks || []).forEach(b => {
            if (b.collections) {
              b.collections = b.collections.filter(c => String(c) !== String(colId));
            }
          });

          // If the deleted collection is currently filtered, return to all
          if (window.activeCollection === String(colId)) {
            window.activeCollection = 'all';
            render();
          }

          await loadCollectionsFromAPI();
          if (window.colTargetHash) openColModal(window.colTargetHash);
        } else {
          showToast("Sunucudan silme isteği başarısız oldu.", "error");
        }
      } catch (e) {
        console.error("Koleksiyon silinirken hata:", e);
        showToast("Bağlantı hatası: Sunucu ile iletişim kurulamadı.", "error");
      }
    }

    async function createCollection() {
      const input = document.getElementById('new-col-name');
      const name = input?.value?.trim();
      if (!name) return;
      try {
        const res = await apiFetch('/api/collections', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ isim: name })
        });
        if (res?.ok) {
          input.value = '';
          await loadCollectionsFromAPI();
          if (window.colTargetHash) openColModal(window.colTargetHash);
        }
      } catch (e) {
        console.warn("createCollection failed:", e);
      }
    }

    function updateBookCollectionMemory(hash, colId, checked) {
      const book = (window.allBooks || []).find(b => b.hash === hash);
      if (!book) return;
      if (!Array.isArray(book.collections)) book.collections = [];
      if (checked) {
        if (!book.collections.includes(colId)) book.collections.push(colId);
      } else {
        book.collections = book.collections.filter(c => String(c) !== String(colId));
      }
    }

    async function toggleBookCol(colId, checked) {
      if (!window.colTargetHash) return;
      const method = checked ? 'POST' : 'DELETE';
      const bodyStr = checked ? JSON.stringify({ kitap_hash: window.colTargetHash }) : null;
      let url = `/api/collections/${colId}/books`;
      if (!checked) url += `/${window.colTargetHash}`;

      try {
        const req = { method, headers: { 'Content-Type': 'application/json' } };
        if (checked) req.body = bodyStr;
        const res = await apiFetch(url, req);
        if (res?.ok) {
          updateBookCollectionMemory(window.colTargetHash, colId, checked);
          if (window.activeCollection !== 'all') render(); // Refresh if filtering by it
          openColModal(window.colTargetHash);
        }
      } catch (e) {
        console.warn("toggleBookCol failed:", e);
      }
    }

    const customStyles = document.createElement('style');
    customStyles.innerHTML = `
.switch input:checked + .slider { background-color: var(--accent); }
.switch input:checked + .slider .knob { transform: translateX(14px); }
`;
    document.head.appendChild(customStyles);

    // --- STATISTICS ---
    function updateStats() {
      const total = window.allBooks?.length || 0;
      const statTotal = document.getElementById('stat-total');
      if (statTotal && statTotal.textContent !== String(total)) {
        statTotal.textContent = total;
        statTotal.classList.remove('stat-count-bump');
        void statTotal.offsetWidth;
        statTotal.classList.add('stat-count-bump');
      }
      document.querySelectorAll('.stat-total-val').forEach(el => {
        if (el.textContent !== String(total)) {
          el.textContent = total;
          el.classList.remove('stat-count-bump');
          void el.offsetWidth;
          el.classList.add('stat-count-bump');
        }
      });
    }

    // --- FILTER (Feature 7: Enhanced with AND Logic) ---
    function getFiltered() {
      const q = document.getElementById('search-input')?.value?.toLowerCase() || '';

      return (window.allBooks || []).filter(b => {
        const matchCat = window.activeCategory === 'all' || b.category === window.activeCategory;
        const matchCol = window.activeCollection === 'all' || (b.collections?.map(String).includes(String(window.activeCollection)));
        const matchQ = !q || [b.title, b.author, b.category, b.subcat, b.summary, b.keywords].some(v => v?.toLowerCase().includes(q));
        const matchFav = !window.showOnlyFav || b.is_favorite === true;
        return matchCat && matchCol && matchQ && matchFav;
      });
    }

    function clearFiltersAndSearch() {
      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.value = '';
      window.activeCategory = 'all';
      window.activeCollection = 'all';
      window.showOnlyFav = false;
      const favBtn = document.getElementById('btn-fav-filter');
      if (favBtn) favBtn.classList.remove('active');
      const catTrigger = document.getElementById('category-trigger');
      if (catTrigger) catTrigger.textContent = 'Tüm Kategoriler';
      const colTrigger = document.getElementById('collection-trigger');
      if (colTrigger) colTrigger.textContent = 'Tüm Koleksiyonlar';
      render();
    }
    window.clearFiltersAndSearch = clearFiltersAndSearch;

    function renderGridSkeletons(count = 8) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      const activeUploads = Array.from(grid.querySelectorAll('.uploading')).filter(node => {
        const tempId = node.dataset.tempId;
        return tempId && typeof uploadingCards !== 'undefined' && uploadingCards.has(tempId);
      });
      grid.innerHTML = '';
      activeUploads.forEach(node => grid.appendChild(node));
      for (let i = 0; i < count; i++) {
        const card = document.createElement('div');
        card.className = 'book-card skeleton';
        card.innerHTML = `
          <div class="card-cover skeleton skeleton-shimmer"></div>
          <div class="card-body">
            <div class="skeleton-line skeleton-shimmer" style="width: 75%; height: 18px; margin-bottom: 8px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 45%; height: 13px; margin-bottom: 12px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 90%; height: 11px; margin-bottom: 6px;"></div>
            <div class="skeleton-line skeleton-shimmer" style="width: 65%; height: 11px;"></div>
          </div>
        `;
        grid.appendChild(card);
      }
    }
    window.renderGridSkeletons = renderGridSkeletons;

    function updateEmptyStateUI(emptyState, booksCount) {
      if (!emptyState) return;
      if (booksCount > 0) {
        emptyState.style.display = 'none';
        return;
      }
      emptyState.style.display = 'flex';
      const isSearching = Boolean(document.getElementById('search-input')?.value.trim() || window.activeCategory !== 'all' || window.activeCollection !== 'all' || window.showOnlyFav);
      const titleEl = document.getElementById('empty-state-title');
      const descEl = document.getElementById('empty-state-desc');
      const clearBtn = document.getElementById('btn-empty-clear');

      if (titleEl) {
        titleEl.textContent = isSearching ? 'Eşleşen Kitap Bulunamadı' : 'Kütüphaneniz Henüz Boş';
      }
      if (descEl) {
        descEl.textContent = isSearching
          ? 'Arama kriterlerinize uygun kitap bulunamadı. Filtreleri temizleyerek tüm kütüphaneyi görebilirsiniz.'
          : 'PDF, EPUB veya TXT kitaplarınızı sürükleyip bırakarak veya dosya seçerek hemen okumaya başlayabilirsiniz.';
      }
      if (clearBtn) {
        clearBtn.style.display = isSearching ? 'inline-flex' : 'none';
      }
    }

    // --- MOTION FLOW HELPERS (FLIP GRID & GLIDING PILLS) ---
    function isMotionReduced() {
      return Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }
    window.isMotionReduced = isMotionReduced;

    function animateSegmentedPill(containerOrSelector, prevBtn, nextBtn, prevRectOverride = null) {
      if (isMotionReduced()) return;
      const container = typeof containerOrSelector === 'string'
        ? document.querySelector(containerOrSelector)
        : containerOrSelector;
      if (!container || !prevBtn || !nextBtn || prevBtn === nextBtn) return;
      if (!container.contains(prevBtn) || !container.contains(nextBtn)) return;

      const cRect = container.getBoundingClientRect();
      const pRect = prevRectOverride || prevBtn.getBoundingClientRect();
      const nRect = nextBtn.getBoundingClientRect();
      if (!pRect.width || !nRect.width) return;

      container.querySelectorAll('.seg-glide-indicator').forEach(el => el.remove());

      const pill = document.createElement('span');
      pill.className = 'seg-glide-indicator';
      const targetStyle = window.getComputedStyle(nextBtn);
      if (targetStyle.borderRadius) {
        pill.style.borderRadius = targetStyle.borderRadius;
      }

      const xFrom = pRect.left - cRect.left + container.scrollLeft;
      const yFrom = pRect.top - cRect.top + container.scrollTop;
      const xTo = nRect.left - cRect.left + container.scrollLeft;
      const yTo = nRect.top - cRect.top + container.scrollTop;

      container.appendChild(pill);
      nextBtn.classList.add('is-gliding-target');

      let cleaned = false;
      const cleanup = () => {
        if (cleaned) return;
        cleaned = true;
        pill.remove();
        nextBtn.classList.remove('is-gliding-target');
      };

      if (typeof pill.animate === 'function') {
        const anim = pill.animate([
          {
            transform: `translate3d(${xFrom}px, ${yFrom}px, 0)`,
            width: `${pRect.width}px`,
            height: `${pRect.height}px`
          },
          {
            transform: `translate3d(${xTo}px, ${yTo}px, 0)`,
            width: `${nRect.width}px`,
            height: `${nRect.height}px`
          }
        ], {
          duration: 320,
          easing: 'cubic-bezier(0.22, 1, 0.36, 1)'
        });
        anim.addEventListener('finish', cleanup, { once: true });
        anim.addEventListener('cancel', cleanup, { once: true });
        setTimeout(cleanup, 360);
      } else {
        cleanup();
      }
    }
    window.animateSegmentedPill = animateSegmentedPill;

    function captureGridPositions(grid) {
      if (!grid || grid.style.display === 'none' || isMotionReduced()) return null;
      const rects = new Map();
      const cards = grid.querySelectorAll('.book-card[data-hash]');
      const vh = window.innerHeight || 900;
      for (let i = 0; i < cards.length; i++) {
        const c = cards[i];
        if (c.style.display === 'none') continue;
        const rect = c.getBoundingClientRect();
        if (!rect.width || rect.bottom < -180 || rect.top > vh + 240) continue;
        rects.set(c.dataset.hash, rect);
        if (rects.size >= 48) break;
      }
      return rects;
    }

    function playGridFlip(grid, prevRects, newlyRevealed = [], opts = {}) {
      if (!grid) return;
      if (window.Motion && typeof window.Motion.flip === 'function') {
        window.Motion.flip(grid, prevRects, {
          selector: '.book-card[data-hash]',
          newlyRevealed,
          duration: opts.duration || 300,
          spring: Boolean(opts.spring)
        });
      }
    }

    // --- RENDER ---
    function render() {
      const books = getFiltered();
      const resultInfo = document.getElementById('result-info');
      if (resultInfo) resultInfo.textContent = `${books.length} kitap gösteriliyor`;
      const emptyState = document.getElementById('empty-state');
      updateEmptyStateUI(emptyState, books.length);

      renderRecentShelf();

      if (window.currentView === 'grid') {
        renderGrid(books);
        setTimeout(enableDragSort, 100);
      } else if (window.currentView === 'table') {
        renderTable(books);
      }
      window.shouldStagger = false;
    }

    function renderRecentShelf() {
      const container = document.getElementById('recent-shelf-container');
      if (!container) return;

      const searchVal = document.getElementById('search-input')?.value?.trim() || '';
      const isFilterActive = (searchVal !== '') ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      if (window.currentView !== 'grid' || isFilterActive || !window.allBooks || window.allBooks.length <= 4) {
        container.style.display = 'none';
        container.innerHTML = '';
        return;
      }

      const recentBooks = window.allBooks.slice(0, 4);
      if (!recentBooks.length) {
        container.style.display = 'none';
        return;
      }

      container.style.display = 'block';
      container.innerHTML = `
        <div class="recent-shelf-header">
          <div class="recent-shelf-title">
            <span class="shelf-label">SEÇKİ &amp; SON EKLENENLER</span>
            <h3>Öne Çıkan Eserler</h3>
          </div>
          <span class="shelf-count">${recentBooks.length} Eser</span>
        </div>
        <div class="recent-shelf-grid">
          ${recentBooks.map(b => {
            const cover = b.has_cover
              ? `<img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')">`
              : `<div class="shelf-cover-placeholder"><i class="fas fa-book"></i></div>`;
            const progress = (typeof getBookReadingProgress === 'function') ? getBookReadingProgress(b) : null;
            const scaleVal = progress ? (progress.pct / 100).toFixed(3) : '0';
            const progressBar = progress ? `<div class="card-progress-bar" style="--progress:${scaleVal}; transform:scaleX(${scaleVal});"></div>` : '';
            const progressBadge = progress ? `<span class="card-progress-badge" style="font-size:0.6rem; padding:0 4px; margin-left:6px;">%${progress.pct}</span>` : '';
            return `
              <button type="button" class="shelf-item" onclick="const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(this, target); else openWorkspace(target); }" aria-label="${esc(b.title)} - Kitabı Oku">
                <div class="shelf-item-cover">
                  ${cover}
                  ${progressBar}
                </div>
                <div class="shelf-item-info">
                  <div style="display:flex; align-items:center; justify-content:space-between;">
                    <span class="shelf-item-cat">${esc(b.category) || 'Genel'}</span>
                    ${progressBadge}
                  </div>
                  <h4 class="shelf-item-title">${esc(b.title) || 'İsimsiz'}</h4>
                  <span class="shelf-item-author">${esc(b.author) || 'Bilinmeyen Yazar'}</span>
                </div>
              </button>
            `;
          }).join('')}
        </div>
      `;
    }
    window.renderRecentShelf = renderRecentShelf;

    // --- PERSISTENT ELEMENT MAPS (60FPS ZERO-REBUILD ARCHITECTURE) ---
    function getBookReadingProgress(b) {
      if (!b) return null;
      const readPage = Number.parseInt(b.okunulan_sayfa || b.read_page || 0, 10);
      const totalPages = Number.parseInt(b.sayfa_sayisi || b.pages || b.page_count || 0, 10);
      if (readPage > 0 && totalPages > 0) {
        const pct = Math.min(100, Math.max(1, Math.round((readPage / totalPages) * 100)));
        return { readPage, totalPages, pct };
      }
      return null;
    }
    window.getBookReadingProgress = getBookReadingProgress;

    const cardElementsMap = new Map();
    window.cardElementsMap = cardElementsMap;
    const tableRowsMap = new Map();
    window.tableRowsMap = tableRowsMap;

    function createBookCardElement(b) {
      const card = document.createElement('div');
      card.className = 'book-card';
      card.id = `book-${b.hash}`;
      card.dataset.hash = b.hash;
      card.tabIndex = 0;
      card.setAttribute('role', 'button');
      card.setAttribute('aria-label', b.title || 'Kitap detayları');

      const coverInner = b.has_cover
        ? `<img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')">`
        : `<div class="card-cover-placeholder">${BOOK_ICON_LG}<span>${esc(b.title) || 'Kapak yok'}</span></div>`;

      const favIcon = b.is_favorite
        ? `<i class="fas fa-heart" style="color: var(--danger); font-size: 1.1rem;"></i>`
        : `<i class="far fa-heart" style="color: var(--paper); font-size: 1.1rem;"></i>`;
      const favBtnText = b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle';

      const progress = getBookReadingProgress(b);
      const scaleVal = progress ? (progress.pct / 100).toFixed(3) : '0';
      const progressBarHtml = progress
        ? `<div class="card-progress-bar" style="--progress:${scaleVal}; transform:scaleX(${scaleVal});" title="%${progress.pct} okundu (${progress.readPage}/${progress.totalPages} sayfa)"></div>`
        : '';
      const progressBadgeHtml = progress
        ? `<span class="card-progress-badge">%${progress.pct}</span>`
        : '';

      card.innerHTML = `
        <div class="selection-indicator"></div>
        <div class="card-cover">
          <div class="card-cat-badge">${esc(b.category)}</div>
          <button type="button" class="btn-favorite-card" onclick="event.stopPropagation(); toggleFavorite('${b.hash}')" title="${favBtnText}" aria-label="${favBtnText}">
             ${favIcon}
          </button>
          <button type="button" class="btn-card-quick-read" title="Okumaya Başla" aria-label="Okumaya Başla">
            <i class="fas fa-book-open"></i> <span>Oku</span>
          </button>
          ${coverInner}
          ${progressBarHtml}
        </div>
        <div class="card-body">
          <div class="card-title">${esc(b.title) || '<em>İsimsiz</em>'}</div>
          <div class="card-author" style="display:flex; align-items:center; justify-content:space-between;">
            <span>${esc(b.author) || 'Bilinmeyen Yazar'}</span>
            ${progressBadgeHtml}
          </div>
        </div>
      `;

      const coverImg = card.querySelector('.card-cover img');
      if (coverImg && coverImg.complete) coverImg.classList.add('loaded');

      const btnQuickRead = card.querySelector('.btn-card-quick-read');
      if (btnQuickRead) {
        btnQuickRead.addEventListener('click', (e) => {
          e.stopPropagation();
          const liveBook = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          if (typeof openBookWithMorph === 'function') openBookWithMorph(card, liveBook);
          else if (typeof openWorkspace === 'function') openWorkspace(liveBook);
        });
      }

      const fileKey = (b.file || '').toLowerCase().trim();
      const recentSet = window._recentlyCompletedUploads;
      if (recentSet && (recentSet.has(b.hash) || (fileKey && recentSet.has(fileKey)))) {
        recentSet.delete(b.hash);
        if (fileKey) recentSet.delete(fileKey);
        card.classList.add('just-added');
        setTimeout(() => card.classList.remove('just-added'), 2600);
      }

      let prefetchHoverTimer = null;
      card.addEventListener('pointerenter', () => {
        prefetchHoverTimer = setTimeout(() => {
          if (typeof window.prefetchPdfDocument === 'function') {
            window.prefetchPdfDocument(b.hash);
          }
        }, 150);
      });

      card.addEventListener('pointerleave', () => {
        if (prefetchHoverTimer) {
          clearTimeout(prefetchHoverTimer);
          prefetchHoverTimer = null;
        }
        if (typeof window.cancelPdfPrefetch === 'function') {
          window.cancelPdfPrefetch(b.hash);
        }
      });

      card.addEventListener('keydown', (e) => {
        if (e.target === card && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          card.click();
        }
      });

      card.onclick = () => {
        if (window.isSelectionMode) {
          toggleSelectBook(card, b.hash);
        } else {
          const bookObj = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          openModal(bookObj, card);
        }
      };

      return card;
    }

    // --- GRID ---
    function renderGrid(books) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;

      // Yer tutucu yükleme kartlarından kütüphaneye yeni yerleşen kitapları yakala (konumu morph için sakla)
      const morphMap = window._pendingUploadMorphRects || (window._pendingUploadMorphRects = new Map());
      if (typeof uploadingCards !== 'undefined' && uploadingCards.size > 0 && typeof removeUploadingCard === 'function') {
        const byHash = new Map();
        const byFile = new Map();
        const byTitle = new Map();
        books.forEach((b) => {
          if (b.hash) byHash.set(String(b.hash), b);
          const fn = (b.file || '').toLowerCase().trim();
          if (fn) byFile.set(fn, b);
          const tt = (b.title || '').toLowerCase().trim();
          if (tt) byTitle.set(tt, b);
        });
        for (const [tempId, holder] of Array.from(uploadingCards.entries())) {
          const cardHash = (holder?.card?.dataset?.completedHash || '').trim();
          const cardFn = (holder?.filename || holder?.card?.dataset?.filename || '').toLowerCase().trim();
          const cardTitle = (holder?.title?.textContent || '').toLowerCase().trim();
          const matchedBook = (cardHash && byHash.get(cardHash))
            || (cardFn && byFile.get(cardFn))
            || (cardTitle && byTitle.get(cardTitle));
          if (matchedBook) {
            if (holder?.card?.isConnected) {
              const rect = holder.card.getBoundingClientRect();
              if (matchedBook.hash && !morphMap.has(matchedBook.hash)) {
                morphMap.set(matchedBook.hash, rect);
              }
              const matchedFn = (matchedBook.file || '').toLowerCase().trim();
              if (matchedFn && !morphMap.has(matchedFn)) {
                morphMap.set(matchedFn, rect);
              }
            }
            removeUploadingCard(tempId, false, true);
          }
        }
      }

      const activeUploads = Array.from(grid.querySelectorAll('.uploading')).filter(node => {
        const tempId = node.dataset.tempId;
        return tempId && typeof uploadingCards !== 'undefined' && uploadingCards.has(tempId);
      });

      const isSearchingOrFiltering = Boolean(document.getElementById('search-input')?.value?.trim()) ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      const doStagger = Boolean(window.shouldStagger) && !isSearchingOrFiltering;
      const filteredHashes = new Set(books.map(b => b.hash));
      const prevRects = !doStagger ? captureGridPositions(grid) : null;
      const newlyRevealed = [];
      const morphedCards = [];
      const staggerCards = [];

      // 1. Ensure cards exist in cardElementsMap for all available books
      const allBooksList = window.allBooks || books;
      allBooksList.forEach(b => {
        if (!cardElementsMap.has(b.hash)) {
          cardElementsMap.set(b.hash, createBookCardElement(b));
        }
      });

      // 2. Clean up removed books from cardElementsMap
      if (window.allBooks) {
        const currentHashes = new Set(window.allBooks.map(b => b.hash));
        for (const [hash, card] of cardElementsMap.entries()) {
          if (!currentHashes.has(hash)) {
            card.remove();
            cardElementsMap.delete(hash);
          }
        }
      }

      // 3. Synchronize existing DOM
      const existingCardsInGrid = new Set(Array.from(grid.querySelectorAll('.book-card')).map(c => c.dataset.hash));
      let hasMissingCards = false;

      books.forEach((b, i) => {
        let card = cardElementsMap.get(b.hash);
        if (!card) {
          card = createBookCardElement(b);
          cardElementsMap.set(b.hash, card);
        }

        // Update favorite & selection visual state without re-creating card
        const favBtn = card.querySelector('.btn-favorite-card');
        if (favBtn) {
          favBtn.innerHTML = b.is_favorite
            ? `<i class="fas fa-heart" style="color: var(--danger); font-size: 1.1rem;"></i>`
            : `<i class="far fa-heart" style="color: var(--paper); font-size: 1.1rem;"></i>`;
        }
        card.classList.toggle('selected', selectedBooks.has(b.hash));

        const wasHidden = card.style.display === 'none';

        // Check if this card just settled from an active upload
        const fileKey = (b.file || '').toLowerCase().trim();
        const morphRect = morphMap.get(b.hash) || (fileKey ? morphMap.get(fileKey) : null);
        if (morphRect) {
          morphMap.delete(b.hash);
          if (fileKey) morphMap.delete(fileKey);
          morphedCards.push({ card, rect: morphRect });
        }

        const recentSet = window._recentlyCompletedUploads;
        if (recentSet && (recentSet.has(b.hash) || (fileKey && recentSet.has(fileKey)))) {
          recentSet.delete(b.hash);
          if (fileKey) recentSet.delete(fileKey);
          card.classList.add('just-added');
          setTimeout(() => card.classList.remove('just-added'), 2600);
        }

        // Controlled stagger, filter reveal, or instant display
        if (morphRect) {
          card.classList.remove('stagger-in', 'card-revealing');
          card.style.animation = '';
        } else if (doStagger) {
          card.classList.remove('card-revealing', 'stagger-in');
          card.style.animation = '';
          if (staggerCards.length < 12) staggerCards.push(card);
        } else {
          card.classList.remove('stagger-in');
          card.style.animation = '';
          if (wasHidden) {
            newlyRevealed.push(card);
            card.classList.add('card-revealing');
            setTimeout(() => card.classList.remove('card-revealing'), 320);
          }
        }

        card.style.display = '';

        if (!existingCardsInGrid.has(b.hash)) {
          hasMissingCards = true;
        }
      });

      // Hide cards in DOM that are filtered out (Zero DOM removal, zero image reloads)
      for (const [hash, card] of cardElementsMap.entries()) {
        if (!filteredHashes.has(hash)) {
          card.classList.remove('card-revealing');
          card.style.display = 'none';
        }
      }

      // Populate if cards were missing or grid was empty
      if (hasMissingCards || grid.querySelectorAll('.book-card').length === 0) {
        grid.innerHTML = '';
        activeUploads.forEach(node => grid.appendChild(node));
        books.forEach(b => {
          const card = cardElementsMap.get(b.hash);
          if (card) grid.appendChild(card);
        });
      }

      if (morphedCards.length > 0 && !isMotionReduced()) {
        morphedCards.forEach(({ card, rect }) => {
          const destRect = card.getBoundingClientRect();
          if (destRect.width > 0 && rect.width > 0 && typeof card.animate === 'function') {
            const dx = rect.left - destRect.left;
            const dy = rect.top - destRect.top;
            const sx = rect.width / destRect.width;
            const sy = rect.height / destRect.height;
            card.animate(
              [
                { transform: `translate3d(${dx}px, ${dy}px, 0) scale(${sx}, ${sy})`, opacity: 0.78 },
                { transform: 'translate3d(0, 0, 0) scale(1, 1)', opacity: 1 }
              ],
              { duration: 360, easing: 'cubic-bezier(0.32, 0.72, 0, 1)', fill: 'both' }
            );
          }
        });
      }

      if (doStagger && staggerCards.length > 0 && window.Motion && typeof window.Motion.stagger === 'function') {
        window.Motion.stagger(staggerCards, { limit: 12, step: 24, maxDelay: 264, y: 12, duration: 280 });
      } else if (!doStagger) {
        playGridFlip(grid, prevRects, newlyRevealed);
      }
    }

    async function uploadCover(hash, input) {
      if (!input?.files?.[0]) return;
      const file = input.files[0];
      const formData = new FormData();
      formData.append('file', file);

      try {
        const res = await apiFetch(`/api/books/${hash}/cover`, {
          method: 'POST',
          body: formData
        });
        if (res?.ok) {
          showToast('Kapak başarıyla güncellendi.', 'success');
          loadBooksFromAPI().catch(err => console.error(err));
          closeModalDirect();
        }
      } catch (err) {
        console.error('Kapak yüklenemedi:', err);
      }
    }

    function createTableRowElement(b) {
      const tr = document.createElement('tr');
      tr.id = `book-${b.hash}`;
      tr.dataset.hash = b.hash;

      const thumbCell = b.has_cover
        ? `<td class="td-cover"><img src="/thumbnails/${b.hash}.jpg" alt="" loading="lazy" decoding="async"></td>`
        : `<td class="td-cover"><div class="td-cover-empty">${BOOK_ICON_SM}</div></td>`;
      tr.innerHTML = `
        ${thumbCell}
        <td class="td-title">${esc(b.title) || '—'}</td>
        <td class="td-author">${esc(b.author) || '—'}</td>
        <td class="td-cat">${esc(b.category) || '—'}</td>
        <td class="td-cat">${esc(b.subcat) || '—'}</td>
        <td class="td-summary"><div class="summary-text">${esc(b.summary)}</div></td>
      `;

      tr.onclick = () => {
        if (window.isSelectionMode) {
          toggleSelectBook(tr, b.hash);
        } else {
          const bookObj = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          openModal(bookObj, tr);
        }
      };

      return tr;
    }

    // --- TABLE ---
    function renderTable(books) {
      const tbody = document.getElementById('table-body');
      if (!tbody) return;

      const isSearchingOrFiltering = Boolean(document.getElementById('search-input')?.value?.trim()) ||
        (window.activeCategory && window.activeCategory !== 'all') ||
        (window.activeCollection && window.activeCollection !== 'all') ||
        Boolean(window.showOnlyFav);

      const doStagger = Boolean(window.shouldStagger) && !isSearchingOrFiltering;
      const filteredHashes = new Set(books.map(b => b.hash));

      // 1. Ensure rows exist in tableRowsMap
      const allBooksList = window.allBooks || books;
      allBooksList.forEach(b => {
        if (!tableRowsMap.has(b.hash)) {
          tableRowsMap.set(b.hash, createTableRowElement(b));
        }
      });

      // 2. Clean up removed rows from tableRowsMap
      if (window.allBooks) {
        const currentHashes = new Set(window.allBooks.map(b => b.hash));
        for (const [hash, tr] of tableRowsMap.entries()) {
          if (!currentHashes.has(hash)) {
            tr.remove();
            tableRowsMap.delete(hash);
          }
        }
      }

      // 3. Synchronize existing DOM
      const existingRowsInTbody = new Set(Array.from(tbody.querySelectorAll('tr')).map(r => r.dataset.hash));

      books.forEach((b, i) => {
        let tr = tableRowsMap.get(b.hash);
        if (!tr) {
          tr = createTableRowElement(b);
          tableRowsMap.set(b.hash, tr);
        }

        tr.classList.toggle('selected', selectedBooks.has(b.hash));

        if (doStagger) {
          tr.classList.add('stagger-in');
          const staggerIdx = i < 12 ? i : 0;
          tr.style.setProperty('--card-index', staggerIdx);
          tr.style.animationDelay = i < 12 ? `${i * 30}ms` : '0ms';
        } else {
          tr.classList.remove('stagger-in');
          tr.style.animation = 'none';
        }

        tr.style.display = '';
      });

      // Hide rows that are filtered out
      for (const [hash, tr] of tableRowsMap.entries()) {
        if (!filteredHashes.has(hash)) {
          tr.style.display = 'none';
        }
      }

      // Keep tbody rows synchronized and ordered matching sorted books list
      books.forEach(b => {
        const tr = tableRowsMap.get(b.hash);
        if (tr) tbody.appendChild(tr);
      });
    }

    function compareTableValues(va, vb, sortDir) {
      if (!va && !vb) return 0;
      if (!va) return sortDir;
      if (!vb) return -sortDir;
      return va.localeCompare(vb, 'tr', { sensitivity: 'base' }) * sortDir;
    }

    // --- SIRALA ---
    function sortTable(col) {
      const keys = ['title', 'author', 'category', 'subcat', 'summary'];
      if (window.sortCol === col) window.sortDir *= -1; else { window.sortCol = col; window.sortDir = 1; }
      (window.allBooks || []).sort((a, b) => {
        const va = String(a[keys[col]] || '').trim();
        const vb = String(b[keys[col]] || '').trim();
        return compareTableValues(va, vb, window.sortDir);
      });
      document.querySelectorAll('thead th').forEach((th, i) => {
        const dataCol = i - 1; // first th is cover column (index 0), data columns start from 1
        th.classList.toggle('sorted', dataCol === col);
        const arrow = th.querySelector('.sort-arrow');
        if (arrow) {
          if (dataCol !== col) {
            arrow.textContent = '↕';
          } else {
            arrow.textContent = window.sortDir === 1 ? '↑' : '↓';
          }
        }
      });
      render();
    }

    // --- MODAL ---
    function openModal(b, sourceEl = null) {
      window.currentModalHash = b.hash;
      const isAnalyzed = Boolean(b.category && b.category !== 'Bilinmeyen' && b.category !== 'Bilinmiyor' && (!b.summary || (!b.summary.includes('Analiz başarısız') && !b.summary.includes('API anahtarı yok'))));
      const keywordChips = b.keywords
        ? b.keywords.split(',').map(k => {
          const kv = k.trim();
          if (!kv) return '';
          const encodedKeyword = encData(kv);
          return `<span class="meta-chip" style="cursor:pointer" data-keyword="${encodedKeyword}" onclick="const keyword = decodeURIComponent(this.dataset.keyword); closeModalDirect(); const si = document.getElementById('search-input'); if(si){ si.value = keyword; si.dispatchEvent(new Event('input')); }">${esc(kv)}</span>`;
        }).join('')
        : '';

      const coverHtml = b.has_cover
        ? `<div class="modal-cover-wrap"><img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')"></div>`
        : `<div class="modal-cover-wrap"><div class="modal-cover-empty">${BOOK_ICON_LG}</div></div>`;

      const progress = getBookReadingProgress(b);
      const modalScale = progress ? (progress.pct / 100).toFixed(3) : '0';
      const progressModalHtml = progress ? `
        <div class="modal-progress-wrap">
          <div class="modal-progress-track">
            <div class="modal-progress-fill" style="--progress:${modalScale}; transform:scaleX(${modalScale});"></div>
          </div>
          <span>%${progress.pct} (${progress.readPage} / ${progress.totalPages} sayfa)</span>
        </div>
      ` : '';

      document.getElementById('modal-content').innerHTML = `
    <div class="modal-layout modal-editorial-layout">
      <div class="modal-left">
        ${coverHtml}
        ${progressModalHtml}
        <div class="modal-actions" id="modal-actions-sidebar">
          <button type="button" class="btn-modal-primary" onclick="const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); const modalCover = document.querySelector('#modal .modal-cover-wrap'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(modalCover, target); else { closeModalDirect(); openWorkspace(target); } }">
            <i class="fas fa-book-open"></i> Kitabı Oku
          </button>
          <button type="button" id="btn-modal-fav" class="${b.is_favorite ? 'btn-modal-fav is-fav' : 'btn-modal-fav'}" onclick="toggleFavorite('${b.hash}')">
            <i class="${b.is_favorite ? 'fas' : 'far'} fa-heart"></i> ${b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle'}
          </button>
          <button type="button" class="btn-modal-secondary" onclick="openColModal('${b.hash}')">
            <i class="fas fa-folder-plus"></i> Koleksiyona Ekle
          </button>
          <button type="button" class="btn-modal-secondary btn-cover-upload">
            <i class="fas fa-image"></i> Kapak Değiştir
            <input type="file" accept="image/*" onchange="uploadCover('${b.hash}', this)">
          </button>
          <button type="button" class="btn-modal-secondary" onclick="toggleEditMode('${b.hash}')">
            <i class="fas fa-edit"></i> Düzenle
          </button>
          ${!isAnalyzed ? `
          <button type="button" class="btn-modal-secondary btn-modal-reanalyze" id="btn-reanalyze-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')">
            <i class="fas fa-magic"></i> Yapay Zeka ile Analiz Et
          </button>
          ` : ''}
          <button type="button" class="btn-modal-secondary modal-btn-compact" onclick="window.open('/api/download/${b.hash}', '_blank')">
            <i class="fas fa-download"></i> PDF İndir
          </button>
          <div class="export-dropdown-wrapper">
            <button type="button" class="btn-modal-secondary modal-btn-compact modal-btn-export" onclick="toggleExportMenu('${b.hash}')">
              <i class="fas fa-file-export"></i> Dışa Aktar (PKM) <i class="fas fa-chevron-down modal-chevron-right"></i>
            </button>
            <div id="export-menu-${b.hash}" class="export-menu export-menu-editorial" style="display:none;">
              <a href="/api/books/${b.hash}/export/obsidian" download class="export-menu-item" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-gem"></i> Obsidian Notu (.md)
              </a>
              <a href="/api/books/${b.hash}/export/anki" download class="export-menu-item" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-clone"></i> Anki Kartları (.tsv)
              </a>
              <a href="/api/books/${b.hash}/export/bibtex" download class="export-menu-item" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-graduation-cap"></i> BibTeX Akademik (.bib)
              </a>
            </div>
          </div>
          ${b.file?.toLowerCase().endsWith('.pdf') ? `
          <button type="button" class="btn-modal-secondary modal-btn-compact" id="btn-compress-${b.hash}" onclick="compressBook('${b.hash}')" title="Gereksiz verileri temizleyip PDF boyutunu yerel olarak küçültür">
            <i class="fas fa-compress-arrows-alt" style="color:var(--accent);"></i> Boyutu Küçült (Optimize Et)
          </button>
          ` : ''}
          <button type="button" class="btn-modal-danger" onclick="deleteBook('${b.hash}')">
            <i class="fas fa-trash-alt"></i> Kaydı Sil
          </button>
        </div>
        <div class="modal-meta-left">
          <span class="meta-chip modal-file-chip">${esc(b.file)}</span>
        </div>
      </div>
      <div class="modal-right">
        <div class="modal-cat modal-stagger-1">${esc(b.category)}${b.subcat ? ' / ' + esc(b.subcat) : ''}</div>
        <h2 class="modal-title modal-stagger-2" id="modal-book-title">${esc(b.title) || 'İsimsiz Kitap'}</h2>
        <div class="modal-author modal-stagger-3">${esc(b.author) || 'Bilinmeyen Yazar'}</div>

        ${(!b.category || b.category === 'Bilinmeyen' || b.summary?.includes('Analiz başarısız')) ? `
          <div class="modal-reanalyze-banner modal-stagger-3">
            <div>
              <div class="modal-reanalyze-title">
                <i class="fas fa-exclamation-triangle"></i> Yapay Zeka Analizi Bekliyor
              </div>
              <div class="modal-reanalyze-desc">
                Bu kitabın başlığı, yazarı ve özeti henüz yapay zeka ile incelenmedi.
              </div>
            </div>
            <button type="button" id="btn-reanalyze-banner-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" class="btn btn--primary" style="white-space: nowrap;">
              <i class="fas fa-wand-magic-sparkles"></i> Şimdi Analiz Et
            </button>
          </div>
        ` : ''}
        
        <div class="modal-editorial-section modal-stagger-4">
          <div class="modal-section-label">ÖZET</div>
          <p class="modal-summary">${esc(b.summary) || 'Özet bulunamadı.'}</p>
        </div>
        
        ${keywordChips ? `<div class="modal-editorial-section modal-stagger-5"><div class="modal-section-label">ANAHTAR KAVRAMLAR</div><div class="modal-keywords">${keywordChips}</div></div>` : ''}

        <div id="edit-form-${b.hash}" class="modal-edit-panel" style="display:none;">
          <div class="modal-edit-grid">
            <input type="text" id="edit-title-${b.hash}" class="modal-edit-input" value="${esc(b.title)}" placeholder="Kitap Adı" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <input type="text" id="edit-author-${b.hash}" class="modal-edit-input" value="${esc(b.author)}" placeholder="Yazar" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <textarea id="edit-summary-${b.hash}" class="modal-edit-textarea" rows="5" onkeydown="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); saveBookEdit('${b.hash}'); }">${esc(b.summary)}</textarea>
            <button type="button" class="btn-modal-save" onclick="saveBookEdit('${b.hash}')">DEĞİŞİKLİKLERİ KAYDET</button>
            <button type="button" class="btn-modal-secondary modal-btn-reanalyze-edit" id="btn-reanalyze-edit-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')">
              <i class="fas fa-magic"></i> Yapay Zeka ile Yeniden Analiz Et (Metadata Yenile)
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
      const modalImg = document.querySelector('#modal .modal-cover-wrap img');
      if (modalImg && modalImg.complete) modalImg.classList.add('loaded');

      const modalEl = document.getElementById('modal');
      modalEl.classList.remove('closing');
      modalEl._sourceTriggerEl = (sourceEl instanceof HTMLElement && sourceEl.isConnected)
        ? sourceEl
        : (document.activeElement instanceof HTMLElement ? document.activeElement : null);

      const originCover = (sourceEl instanceof HTMLElement
        ? (sourceEl.querySelector('.card-cover, .shelf-item-cover, .td-cover img') || sourceEl)
        : null) || document.querySelector(`.book-card[data-hash="${b.hash}"] .card-cover`);

      const modalBox = modalEl.querySelector('.modal');
      const originRectSource = (originCover && originCover.offsetParent !== null)
        ? originCover
        : (sourceEl instanceof HTMLElement && sourceEl.offsetParent !== null ? sourceEl : null);
      if (modalBox && originRectSource) {
        const r = originRectSource.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
          modalBox.style.setProperty('--modal-origin-x', `${Math.round(r.left + r.width / 2)}px`);
          modalBox.style.setProperty('--modal-origin-y', `${Math.round(r.top + r.height / 2)}px`);
        } else {
          modalBox.style.removeProperty('--modal-origin-x');
          modalBox.style.removeProperty('--modal-origin-y');
        }
      } else if (modalBox) {
        modalBox.style.removeProperty('--modal-origin-x');
        modalBox.style.removeProperty('--modal-origin-y');
      }

      const canMorph = Boolean(
        document.startViewTransition &&
        !isMotionReduced() &&
        originCover &&
        originCover.offsetParent !== null &&
        !modalEl.classList.contains('open')
      );

      const openDom = () => {
        modalEl.classList.add('open');
        document.body.classList.add('modal-open');
      };

      if (canMorph && window.Motion && typeof window.Motion.transition === 'function') {
        void window.Motion.transition(openDom, {
          name: 'book-cover',
          fromEl: originCover,
          toEl: () => document.querySelector('#modal .modal-cover-wrap')
        });
      } else {
        openDom();
      }
      activateModalFocus(modalEl);
    }

    function showKeywordBooks(keyword) {
      const relatedBooks = (window.allBooks || []).filter(b => b.keywords?.split(',').map(m => m.trim()).includes(keyword));

      let listHtml = relatedBooks.map(b => `
    <div style="display:flex; align-items:center; gap:1rem; padding: 1rem; border-bottom: 1px solid var(--line); cursor:pointer; transition: background 0.2s;" onmouseover="this.style.background='rgba(196,168,130,0.12)'" onmouseout="this.style.background='transparent'" onclick="const target=(window.allBooks || []).find(x=>x.hash==='${b.hash}'); if(target) openModal(target);">
        <div style="width:45px; height:60px; flex-shrink:0; background:var(--sepia-pale); overflow:hidden; border-radius:3px; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 10px var(--shadow);">
            ${b.has_cover ? `<img src="/thumbnails/${b.hash}.jpg" style="width:100%; height:100%; object-fit:cover;">` : BOOK_ICON_SM}
        </div>
        <div>
            <div style="font-family:'Instrument Serif',serif; font-weight:700; font-size:1.1rem; color:var(--ink); margin-bottom:0.2rem;">${esc(b.title)}</div>
            <div style="font-size:0.85rem; color:var(--muted); font-style:italic;">${esc(b.author)}</div>
        </div>
    </div>
  `).join('');

      document.getElementById('modal-content').innerHTML = `
    <div style="padding: 2.5rem;">
        <div class="modal-section-label" style="font-size:0.7rem; margin-top:0;">ANAHTAR KAVRAM</div>
        <div class="modal-title" style="margin-bottom: 1.5rem; color: var(--accent); font-size: 2.2rem;">${esc(keyword)}</div>
        <div style="max-height: 55vh; overflow-y: auto; padding-right: 0.5rem; border-top: 2px solid var(--sepia);">
            ${listHtml || '<div style="color:var(--muted); font-style:italic; padding-top:1rem;">Bu kavrama ait kitap bulunamadı.</div>'}
        </div>
    </div>
  `;
      document.getElementById('modal').classList.add('open');
      document.body.classList.add('modal-open');
    }

    // ── Unified Modal Exit Animation (Apple/Tesla Standard) ──

    // ═══════════════ F2: UNIVERSAL FOCUS TRAP & ACCESSIBILITY ═══════════════
    let modalFocusStack = [];

    function _getModalFocusables(modalEl) {
      if (!modalEl) return [];
      return Array.from(modalEl.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]):not([type="file"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )).filter(el => el.offsetParent !== null || window.getComputedStyle(el).display !== 'none');
    }

    function handleModalTabKey(e) {
      if (e.key !== 'Tab') return;
      const modalEl = this;
      const focusables = _getModalFocusables(modalEl);

      if (focusables.length === 0) {
        e.preventDefault();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first || !modalEl.contains(document.activeElement)) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last || !modalEl.contains(document.activeElement)) {
          e.preventDefault();
          first.focus();
        }
      }
    }

    function activateModalFocus(modalRef) {
      const modalEl = typeof modalRef === 'string' ? document.getElementById(modalRef) : modalRef;
      if (!modalEl) return;

      const prevActive = document.activeElement;
      modalFocusStack.push({ modal: modalEl, returnEl: prevActive });

      const focusables = _getModalFocusables(modalEl);

      if (focusables.length > 0) {
        const nonTextInputTypes = ['file', 'hidden', 'checkbox', 'radio', 'button', 'submit', 'range', 'color'];
        setTimeout(() => {
          const firstInput = focusables.find(el => {
            if (el.readOnly) return false;
            if (el.tagName === 'TEXTAREA') return true;
            if (el.tagName === 'INPUT') {
              return !nonTextInputTypes.includes((el.type || 'text').toLowerCase());
            }
            return false;
          });
          if (firstInput) {
            firstInput.focus();
          } else {
            focusables[0].focus();
          }
        }, 60);
      }

      modalEl.removeEventListener('keydown', handleModalTabKey);
      modalEl.addEventListener('keydown', handleModalTabKey);
    }
    window._modalTabTrapHandler = handleModalTabKey;
    window.activateModalFocus = activateModalFocus;

    function _clearModalFocusEntry(modalRef) {
      const modalEl = typeof modalRef === 'string' ? document.getElementById(modalRef) : modalRef;
      if (!modalEl) return null;
      modalEl.removeEventListener('keydown', handleModalTabKey);
      const idx = modalFocusStack.findLastIndex ? modalFocusStack.findLastIndex(e => e.modal === modalEl) : -1;
      if (idx !== -1) return modalFocusStack.splice(idx, 1)[0];
      return modalFocusStack.pop() || null;
    }
    window._clearModalFocusEntry = _clearModalFocusEntry;

    function releaseModalFocus(modalRef, opts = {}) {
      const modalEl = typeof modalRef === 'string' ? document.getElementById(modalRef) : modalRef;
      if (!modalEl) return;
      const entry = _clearModalFocusEntry(modalEl);
      if (opts.restore === false) return;

      const returnCandidate = (entry && entry.returnEl && entry.returnEl.isConnected && entry.returnEl.offsetParent !== null)
        ? entry.returnEl
        : ((modalEl._sourceTriggerEl && modalEl._sourceTriggerEl.isConnected && modalEl._sourceTriggerEl.offsetParent !== null)
          ? modalEl._sourceTriggerEl
          : null);
      if (returnCandidate && typeof returnCandidate.focus === 'function') {
        requestAnimationFrame(() => {
          if (returnCandidate.isConnected) returnCandidate.focus({ preventScroll: true });
        });
      }
    }
    window.releaseModalFocus = releaseModalFocus;

    function closeModalWithAnimation(modalRef, callback) {
      let modal = modalRef;
      if (typeof modalRef === 'string') {
        modal = document.getElementById(modalRef);
      }
      if (!modal || modal.classList.contains('closing')) return;

      const isOpen = modal.classList.contains('open') || (modal.style.display && modal.style.display !== 'none');
      if (!isOpen) {
        if (typeof callback === 'function') callback();
        return;
      }

      releaseModalFocus(modal);

      const finishClose = () => {
        modal.classList.remove('closing');
        modal.style.display = '';
        const modalBox = modal.querySelector('.modal');
        if (modalBox) {
          modalBox.style.removeProperty('--modal-origin-x');
          modalBox.style.removeProperty('--modal-origin-y');
        }
        const anyModal = document.querySelector('.modal-overlay.open, .modal-overlay.closing');
        if (!anyModal) {
          document.body.classList.remove('modal-open');
        }
        if (typeof callback === 'function') callback();
      };

      if (window.Motion && typeof window.Motion.exit === 'function') {
        void window.Motion.exit(modal, {
          className: 'closing',
          removeClass: 'open',
          afterFn: finishClose
        });
      } else {
        modal.classList.add('closing');
        modal.classList.remove('open');
        setTimeout(finishClose, 180);
      }
    }
    window.closeModalWithAnimation = closeModalWithAnimation;

    function closeModal(e) { if (e.target === document.getElementById('modal')) closeModalDirect(); }
    function closeModalDirect() {
      const modalEl = document.getElementById('modal');
      const bookHash = window.currentModalHash;
      const gridView = document.getElementById('grid-view');
      const modalCover = modalEl ? modalEl.querySelector('.modal-cover-wrap') : null;
      const targetCover = (bookHash && gridView && gridView.style.display !== 'none')
        ? document.querySelector(`.book-card[data-hash="${bookHash}"] .card-cover`)
        : null;

      let targetVisible = false;
      if (targetCover && targetCover.offsetParent !== null) {
        const rect = targetCover.getBoundingClientRect();
        targetVisible = rect.width > 0 && rect.bottom > 0 && rect.top < (window.innerHeight || 900);
      }

      if (modalEl && modalEl.classList.contains('open') && modalCover && targetVisible && window.Motion && typeof window.Motion.transition === 'function' && !isMotionReduced()) {
        const closeDom = () => {
          modalEl.classList.remove('open', 'closing');
          modalEl.style.display = '';
          const modalBox = modalEl.querySelector('.modal');
          if (modalBox) {
            modalBox.style.removeProperty('--modal-origin-x');
            modalBox.style.removeProperty('--modal-origin-y');
          }
          const anyModal = document.querySelector('.modal-overlay.open, .modal-overlay.closing');
          if (!anyModal) document.body.classList.remove('modal-open');
          window.currentModalHash = null;
        };
        void window.Motion.transition(closeDom, {
          name: 'book-cover',
          fromEl: modalCover,
          toEl: targetCover
        }).finally(() => {
          releaseModalFocus(modalEl);
          modalEl._sourceTriggerEl = null;
        });
        return;
      }

      closeModalWithAnimation('modal', () => {
        window.currentModalHash = null;
        if (modalEl) modalEl._sourceTriggerEl = null;
      });
    }

    // --- [D6: UYGULAMA İÇİ ŞIK ONAY DİYALOĞU (NATIVE CONFIRM YERİNE)] ---
    function showAppConfirm(message, title = 'Onay Gerekiyor', confirmText = 'Onayla', isDanger = true) {
      return new Promise((resolve) => {
        let overlay = document.getElementById('app-confirm-modal');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.id = 'app-confirm-modal';
          overlay.className = 'modal-overlay';
          overlay.innerHTML = `
            <div class="modal app-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
              <div class="confirm-dialog-header">
                <h3 id="confirm-dialog-title" class="confirm-dialog-title"></h3>
              </div>
              <div class="confirm-dialog-body">
                <p id="confirm-dialog-msg" class="confirm-dialog-msg"></p>
              </div>
              <div class="confirm-dialog-actions">
                <button type="button" class="btn-modal-secondary" id="confirm-dialog-cancel">Vazgeç</button>
                <button type="button" class="btn-modal-primary" id="confirm-dialog-ok">Onayla</button>
              </div>
            </div>
          `;
          document.body.appendChild(overlay);
        }

        const titleEl = overlay.querySelector('#confirm-dialog-title');
        const msgEl = overlay.querySelector('#confirm-dialog-msg');
        const okBtn = overlay.querySelector('#confirm-dialog-ok');
        const cancelBtn = overlay.querySelector('#confirm-dialog-cancel');

        titleEl.textContent = title;
        msgEl.textContent = message;
        okBtn.textContent = confirmText;

        if (isDanger) {
          okBtn.style.background = 'var(--danger, #b0473c)';
          okBtn.style.color = '#ffffff';
          okBtn.style.borderColor = 'var(--danger, #b0473c)';
        } else {
          okBtn.style.background = '';
          okBtn.style.color = '';
          okBtn.style.borderColor = '';
        }

        let isResolved = false;
        const cleanup = (result) => {
          if (isResolved) return;
          isResolved = true;
          window.removeEventListener('keydown', handleKey);
          closeModalWithAnimation(overlay, () => resolve(result));
        };

        const handleKey = (e) => {
          if (e.key === 'Escape') {
            e.preventDefault();
            cleanup(false);
          }
        };

        window.addEventListener('keydown', handleKey);
        okBtn.onclick = () => cleanup(true);
        cancelBtn.onclick = () => cleanup(false);
        overlay.onclick = (e) => {
          if (e.target === overlay) cleanup(false);
        };

        overlay.classList.add('open');
        document.body.classList.add('modal-open');
        activateModalFocus(overlay);
      });
    }
    window.showAppConfirm = showAppConfirm;

    // --- BULK OPERATIONS ---
    function toggleSelectionMode() {
      window.isSelectionMode = !window.isSelectionMode;
      selectedBooks.clear();

      document.body.classList.toggle('is-selection-mode', window.isSelectionMode);
      document.getElementById('bulk-bar').classList.toggle('active', window.isSelectionMode);
      document.getElementById('btn-manage').classList.toggle('active', window.isSelectionMode);

      updateBulkCount();
      render();
    }

    function toggleSelectBook(el, hash) {
      if (selectedBooks.has(hash)) {
        selectedBooks.delete(hash);
      } else {
        selectedBooks.add(hash);
      }
      el.classList.toggle('selected');
      updateBulkCount();
    }

    function updateBulkCount() {
      document.getElementById('bulk-count').textContent = selectedBooks.size;
      document.getElementById('bulk-delete-btn').disabled = selectedBooks.size === 0;
    }

    async function bulkDelete() {
      if (selectedBooks.size === 0) return;
      const ok = await (window.showAppConfirm ? window.showAppConfirm(`${selectedBooks.size} kitabı kalıcı olarak silmek istediğinize emin misiniz?`, 'Toplu Silme', 'Seçilenleri Sil', true) : Promise.resolve(confirm(`${selectedBooks.size} kitabı silmek istediğinize emin misiniz?`)));
      if (!ok) return;

      const toDelete = Array.from(selectedBooks);
      let successCount = 0;
      const failedBooks = [];

      // Unobtrusive feedback in Activity Pill instead of forcing drawer open
      const opsToggle = document.getElementById('ops-toggle');
      if (opsToggle) {
        opsToggle.classList.remove('ops-toggle-pulse');
        void opsToggle.offsetWidth;
        opsToggle.classList.add('ops-toggle-pulse');
      }

      const results = await Promise.allSettled(toDelete.map(async (hash) => {
        const book = (window.allBooks || []).find(b => b.hash === hash);
        const bookTitle = book ? book.title : hash;
        try {
          const resp = await apiFetch(`/api/books/${hash}`, { method: 'DELETE' });
          if (resp?.ok) return { ok: true, title: bookTitle };
          return { ok: false, title: bookTitle };
        } catch (e) {
          console.error("Bulk delete error for:", hash, e);
          return { ok: false, title: bookTitle };
        }
      }));

      for (const res of results) {
        if (res.status === 'fulfilled' && res.value.ok) {
          successCount++;
        } else if (res.status === 'fulfilled') {
          failedBooks.push(res.value.title);
        }
      }

      addChatMessage('ai', `${successCount} kitap başarıyla silindi.`);
      if (failedBooks.length > 0) {
        addChatMessage('ai', `⚠️ Şu kitaplar silinemedi: ${failedBooks.join(', ')}`);
      }
      toggleSelectionMode(); // Modu kapat ve listeyi yenile
      loadBooksFromAPI().catch(err => console.error("Reload error after bulk delete:", err));
    }

    function debounce(fn, delay = 250) {
      let timer = null;
      return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
      };
    }
    window.debounce = debounce;

    function openShortcutsModal() {
      const m = document.getElementById('shortcuts-modal');
      if (m) {
        m.classList.remove('closing');
        m.classList.add('open');
        document.body.classList.add('modal-open');
        activateModalFocus(m);
      }
    }
    function closeShortcutsModal() {
      closeModalWithAnimation('shortcuts-modal');
    }
    window.openShortcutsModal = openShortcutsModal;
    window.closeShortcutsModal = closeShortcutsModal;

    function isElementVisible(el) {
      return el && (el.classList.contains('open') || (el.style.display && el.style.display !== 'none'));
    }

    function isModalOrDropdownOpen() {
      const modalIds = [
        'handoff-modal',
        'shortcuts-modal',
        'telegram-modal',
        'pdf-note-modal',
        'workspace-reader',
        'col-modal',
        'modal',
        'book-modal',
        'settings-modal',
        'logs-modal',
        'duplicates-modal'
      ];
      return modalIds.some(id => isElementVisible(document.getElementById(id))) || document.body.classList.contains('modal-open');
    }

    function handleEscapeKeyPress() {
      const openDropdown = document.querySelector('.custom-dropdown.open');
      if (openDropdown) {
        closeCustomDropdown(openDropdown, { restoreFocus: true });
        return;
      }

      const modalCloseHandlers = [
        { id: 'handoff-modal', fn: window.closeHandoffModal },
        { id: 'shortcuts-modal', fn: closeShortcutsModal },
        { id: 'telegram-modal', fn: window.closeTelegramModal },
        { id: 'pdf-note-modal', fn: window.closePdfNoteModalDirect },
        { id: 'workspace-reader', fn: window.closeWorkspace },
        { id: 'duplicates-modal', fn: closeDuplicatesModal },
        { id: 'col-modal', fn: window.closeColModalDirect },
        { id: 'book-modal', fn: closeModalDirect },
        { id: 'modal', fn: closeModalDirect },
        { id: 'settings-modal', fn: window.closeSettingsDirect },
        { id: 'logs-modal', fn: window.closeLogsModalDirect },
      ];

      for (const { id, fn } of modalCloseHandlers) {
        if (isElementVisible(document.getElementById(id))) {
          if (typeof fn === 'function') fn();
          return;
        }
      }

      const opsCenter = document.getElementById('ops-center');
      if (opsCenter?.classList.contains('active') && typeof closeOpsCenterSmooth === 'function') {
        closeOpsCenterSmooth({ restoreFocus: true });
        return;
      }

      const chatPanel = document.getElementById('chat-panel');
      if (chatPanel?.classList.contains('active') && typeof closeChatPanelSmooth === 'function') {
        closeChatPanelSmooth({ restoreFocus: true });
        return;
      }

      if (window.isDeepSearchActive && typeof closeDeepSearch === 'function') {
        closeDeepSearch();
      }
    }

    function handleGlobalViewShortcuts(key) {
      switch (key.toLowerCase()) {
        case '/':
        case 'k': {
          const sInput = document.getElementById('search-input');
          if (sInput) {
            sInput.focus();
            sInput.select();
          }
          break;
        }
        case '?':
          openShortcutsModal();
          break;
        case 'g':
          setView('grid');
          break;
        case 't':
          setView('table');
          break;
        case 's':
          setView('stats');
          break;
        case 'f':
          toggleFavFilter();
          break;
        case 'm':
          toggleSelectionMode();
          break;
        case 'd':
          toggleTheme();
          break;
      }
    }

    document.addEventListener('keydown', e => {
      if (e.defaultPrevented) return;

      // If typing in an input, textarea, or contentEditable, protect shortcuts
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable;
      if (isInput) {
        if (e.key === 'Escape') {
          if (e.target.id === 'chat-input' && typeof closeChatPanelSmooth === 'function') {
            e.preventDefault();
            e.target.blur();
            closeChatPanelSmooth({ restoreFocus: true });
            return;
          }
          if (e.target.closest?.('.modal-overlay.open, #ops-center.active, #chat-panel.active') || isModalOrDropdownOpen()) {
            e.preventDefault();
            handleEscapeKeyPress();
            return;
          }
          e.target.blur();
        }
        return;
      }

      // Escape key closes modals in hierarchical order
      if (e.key === 'Escape') {
        handleEscapeKeyPress();
        return;
      }

      // Delete key inside book modal
      if (e.key === 'Delete' && window.currentModalHash) {
        void deleteBook(window.currentModalHash);
        return;
      }

      // Guard against hijacking browser shortcuts (Ctrl+F, Ctrl+S, Ctrl+T, Ctrl+N, Command on macOS)
      if (e.ctrlKey || e.metaKey || e.altKey) {
        return;
      }

      // Block global view shortcuts if any modal is currently open
      if (isModalOrDropdownOpen()) {
        return;
      }

      // Global Navigation Shortcuts
      if (['/', 'k', 'K', '?'].includes(e.key)) {
        e.preventDefault();
      }
      handleGlobalViewShortcuts(e.key);
    });

    const searchInputEl = document.getElementById('search-input');
    if (searchInputEl) {
      searchInputEl.addEventListener('input', debounce(() => {
        if (window.isDeepSearchActive) {
          void executeDeepSearch(searchInputEl.value);
        } else {
          render();
        }
      }, 250));
    }

    // --- VIEW SWITCH ---
    function setView(v) {
      window.currentView = v;
      const viewMap = {
        grid: document.getElementById('grid-view'),
        table: document.getElementById('table-view'),
        stats: document.getElementById('stats-view')
      };

      const btnGrid = document.getElementById('btn-grid');
      const btnTable = document.getElementById('btn-table');
      const btnStats = document.getElementById('btn-stats');
      const viewToggle = document.querySelector('.view-toggle');
      const prevBtn = viewToggle ? viewToggle.querySelector('.view-btn.active') : null;
      const viewBtnMap = { grid: btnGrid, table: btnTable, stats: btnStats };
      const nextBtn = viewBtnMap[v] || null;

      if (btnGrid) btnGrid.classList.toggle('active', v === 'grid');
      if (btnTable) btnTable.classList.toggle('active', v === 'table');
      if (btnStats) btnStats.classList.toggle('active', v === 'stats');

      if (viewToggle && prevBtn && nextBtn && prevBtn !== nextBtn && window.Motion && typeof window.Motion.glidePill === 'function') {
        window.Motion.glidePill(viewToggle, prevBtn, nextBtn);
      }

      const applyViewDom = () => {
        Object.entries(viewMap).forEach(([name, el]) => {
          if (!el) return;
          el.classList.remove('view-fade-in');
          el.style.display = name === v ? (name === 'grid' ? 'grid' : 'block') : 'none';
        });

        window.shouldStagger = true;
        if (v === 'table') {
          renderTable(getFiltered());
        } else if (v === 'grid') {
          renderGrid(getFiltered());
          setTimeout(enableDragSort, 100);
        }
        window.shouldStagger = false;
        if (v === 'stats' && typeof loadStats === 'function') void loadStats();
      };

      if (window.Motion && typeof window.Motion.transition === 'function' && document.startViewTransition && !isMotionReduced()) {
        void window.Motion.transition(applyViewDom);
      } else {
        applyViewDom();
        const activeEl = viewMap[v];
        if (activeEl && !isMotionReduced()) {
          activeEl.classList.add('view-fade-in');
          activeEl.addEventListener('animationend', () => activeEl.classList.remove('view-fade-in'), { once: true });
        }
      }
    }


    // --- DRAG AND DROP SORTING ---
    function enableDragSort() {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
      grid.querySelectorAll('.book-card[data-hash]').forEach(card => {
        card.setAttribute('draggable', 'true');
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('dragenter', handleDragEnter);
        card.addEventListener('dragleave', handleDragLeave);
        card.addEventListener('drop', handleDrop);
        card.addEventListener('dragend', handleDragEnd);
      });
    }

    function handleDragStart(e) {
      window.dragSrcEl = this;
      this.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', this.dataset.hash);
    }
    function handleDragOver(e) { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }
    function handleDragEnter(e) { this.classList.add('drag-over'); }
    function handleDragLeave(e) { this.classList.remove('drag-over'); }
    function handleDrop(e) {
      e.preventDefault();
      this.classList.remove('drag-over');
      const grid = document.getElementById('grid-view');
      if (!window.dragSrcEl || !grid?.contains(window.dragSrcEl)) return;
      if (window.dragSrcEl !== this) {
        const prevRects = captureGridPositions(grid);
        const cards = [...grid.querySelectorAll('.book-card[data-hash]')];
        const fromIdx = cards.indexOf(window.dragSrcEl);
        const toIdx = cards.indexOf(this);
        if (fromIdx < toIdx) this.after(window.dragSrcEl);
        else this.before(window.dragSrcEl);
        playGridFlip(grid, prevRects, [], { spring: true, duration: 340 });
        // Sıralamayı localStorage'a kaydet
        const newOrder = [...grid.querySelectorAll('.book-card[data-hash]')].map(c => c.dataset.hash);
        window.customOrder = newOrder;
        localStorage.setItem('kutuphane-custom-order', JSON.stringify(newOrder));
        // Sıralamayı sunucuya senkronize et
        apiFetch('/api/books/order', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order: newOrder })
        }).catch(err => console.error("Sıralama sunucuya senkronize edilemedi:", err));
      }
    }
    function handleDragEnd(e) {
      document.querySelectorAll('.book-card').forEach(c => { c.classList.remove('dragging', 'drag-over'); });
    }

    async function reanalyzeBookModal(fileHash) {
      const btn = document.getElementById(`btn-reanalyze-${fileHash}`);
      const bannerBtn = document.getElementById(`btn-reanalyze-banner-${fileHash}`);
      const editBtn = document.getElementById(`btn-reanalyze-edit-${fileHash}`);
      const prevHtml = btn ? btn.innerHTML : '';
      const prevBannerHtml = bannerBtn ? bannerBtn.innerHTML : '';
      const prevEditHtml = editBtn ? editBtn.innerHTML : '';

      [btn, bannerBtn, editBtn].forEach(b => {
        if (b) {
          b.disabled = true;
          b.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Yapay Zeka İnceliyor...';
        }
      });

      try {
        const res = await apiReanalyzeBook(fileHash);
        if (res.status === 'success') {
          const d = res.data || {};
          showToast(`Yapay zeka analizi başarıyla tamamlandı!\nKitap: ${d.kitap_adi || ''}\nYazar: ${d.yazar || ''}`, 'success');
          closeModalDirect();
          if (typeof loadBooksFromAPI === 'function') await loadBooksFromAPI();
        } else {
          showToast(`Analiz tamamlanamadı: ${res.message || 'API anahtarınızı kontrol edin.'}`, 'warning');
        }
      } catch (err) {
        showToast(`Hata: ${err.message || 'Analiz sırasında sorun oluştu.'}`, 'error');
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = prevHtml || '<i class="fas fa-magic"></i> Yapay Zeka ile Analiz Et';
        }
        if (bannerBtn) {
          bannerBtn.disabled = false;
          bannerBtn.innerHTML = prevBannerHtml || '<i class="fas fa-magic"></i> Şimdi Analiz Et';
        }
        if (editBtn) {
          editBtn.disabled = false;
          editBtn.innerHTML = prevEditHtml || '<i class="fas fa-magic"></i> Yapay Zeka ile Yeniden Analiz Et (Metadata Yenile)';
        }
      }
    }
    window.reanalyzeBookModal = reanalyzeBookModal;

    function toggleExportMenu(hash) {
      const menu = document.getElementById(`export-menu-${hash}`);
      if (!menu) return;
      const isOpen = menu.style.display === 'block';
      document.querySelectorAll('.export-menu').forEach(el => el.style.display = 'none');
      menu.style.display = isOpen ? 'none' : 'block';
    }
    window.toggleExportMenu = toggleExportMenu;

    const MODAL_BACKDROP_CLOSERS = {
      'modal': () => closeModalDirect(),
      'logs-modal': () => window.closeLogsModalDirect?.(),
      'settings-modal': () => window.closeSettingsDirect?.(),
      'col-modal': () => window.closeColModalDirect?.(),
      'pdf-note-modal': () => window.closePdfNoteModalDirect?.(),
      'telegram-modal': () => window.closeTelegramModal?.(),
      'shortcuts-modal': () => closeShortcutsModal(),
      'handoff-modal': () => window.closeHandoffModal?.(),
      'duplicates-modal': () => closeDuplicatesModal(),
    };

    function _handleBackdropClick(target) {
      if (!target?.classList) return;
      if (!target.classList.contains('modal-overlay') && !target.classList.contains('logs-modal')) return;
      const closer = MODAL_BACKDROP_CLOSERS[target.id];
      if (typeof closer === 'function') {
        closer();
      }
    }

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.export-dropdown-wrapper')) {
        document.querySelectorAll('.export-menu').forEach(el => el.style.display = 'none');
      }
      // Backdrop click to close modals cleanly
      _handleBackdropClick(e.target);
    });

    // --- [10.3] Global Deep Search Helpers ---
    function _setDeepSearchButtonState(active) {
      const toggleBtn = document.getElementById('btn-deep-search-toggle');
      const label = document.getElementById('deep-search-label');
      if (toggleBtn) {
        toggleBtn.classList.toggle('active', active);
        toggleBtn.setAttribute('aria-pressed', active ? 'true' : 'false');
        toggleBtn.closest('.search-wrap')?.classList.toggle('is-deep-search', active);
      }
      if (label) {
        label.textContent = active ? 'Derin Aktif' : 'Derin Arama';
      }
    }

    function _activateDeepSearchUI() {
      const input = document.getElementById('search-input');

      _setDeepSearchButtonState(true);
      if (input) {
        input.placeholder = 'Kitapların tüm satırlarında ara…';
        input.focus();
        if (input.value.trim()) {
          void executeDeepSearch(input.value.trim());
        }
      }
    }

    function _deactivateDeepSearchUI() {
      const input = document.getElementById('search-input');
      const resultsContainer = document.getElementById('deep-search-results');
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');

      _setDeepSearchButtonState(false);
      if (input) {
        input.placeholder = 'Kitap, yazar, konu ara… (Kısayol: /)';
      }
      if (resultsContainer) resultsContainer.style.display = 'none';
      if (window.currentView === 'grid' && gridView) gridView.style.display = 'grid';
      if (window.currentView === 'table' && tableView) tableView.style.display = 'block';
      render();
    }

    function applyDeepSearchActiveUI(isActive) {
      if (isActive) {
        _activateDeepSearchUI();
      } else {
        _deactivateDeepSearchUI();
      }
    }

    function toggleDeepSearchMode() {
      window.isDeepSearchActive = !window.isDeepSearchActive;
      applyDeepSearchActiveUI(window.isDeepSearchActive);
    }
    window.toggleDeepSearchMode = toggleDeepSearchMode;

    function closeDeepSearch() {
      if (window.isDeepSearchActive) {
        toggleDeepSearchMode();
      }
    }
    window.closeDeepSearch = closeDeepSearch;

    function sanitizeDeepSnippet(snippet) {
      if (!snippet) return '';
      const tokenOpen = '___DEEP_MARK_OPEN___';
      const tokenClose = '___DEEP_MARK_CLOSE___';
      const safe = esc(
        String(snippet)
          .replace(/<mark class="deep-hl">/gi, tokenOpen)
          .replace(/<\/mark>/gi, tokenClose)
      )
        .replaceAll(tokenOpen, '<mark class="deep-hl">')
        .replaceAll(tokenClose, '</mark>');
      return safe;
    }

    function renderDeepSearchResults(results) {
      return results.map(r => {
        const coverHtml = r.has_cover
          ? `<img src="/thumbnails/${r.dosya_hash}.jpg" class="deep-search-thumb" alt="${esc(r.kitap_adi)}">`
          : `<div class="deep-search-thumb-empty"><i class="fas fa-book"></i></div>`;
        return `
          <div class="deep-search-card">
            ${coverHtml}
            <div class="deep-search-body">
              <div class="deep-search-meta">
                <span class="deep-search-title">${esc(r.kitap_adi)}</span>
                <span class="deep-search-author">— ${esc(r.yazar)}</span>
                <span class="badge deep-search-page-badge">Sayfa ${r.sayfa_no}</span>
              </div>
              <div class="deep-snippet deep-search-snippet">${sanitizeDeepSnippet(r.snippet)}</div>
            </div>
            <button type="button" class="btn-empty-add deep-search-goto-btn" onclick="openWorkspaceAtPage('${r.dosya_hash}', ${r.sayfa_no})">
              Sayfaya Git <i class="fas fa-arrow-right" style="margin-left:4px;"></i>
            </button>
          </div>
        `;
      }).join('');
    }

    function _restoreViewsForEmptyDeepSearch() {
      const resultsContainer = document.getElementById('deep-search-results');
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');
      const statsView = document.getElementById('stats-view');

      if (resultsContainer) resultsContainer.style.display = 'none';
      if (window.currentView === 'grid' && gridView) gridView.style.display = 'grid';
      if (window.currentView === 'table' && tableView) tableView.style.display = 'block';
      if (window.currentView === 'stats' && statsView) statsView.style.display = 'block';
    }

    function _showDeepSearchLoading() {
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');
      const statsView = document.getElementById('stats-view');
      const emptyState = document.getElementById('empty-state');
      const resultsContainer = document.getElementById('deep-search-results');
      const listEl = document.getElementById('deep-search-list');

      if (gridView) gridView.style.display = 'none';
      if (tableView) tableView.style.display = 'none';
      if (statsView) statsView.style.display = 'none';
      if (emptyState) emptyState.style.display = 'none';
      if (resultsContainer) resultsContainer.style.display = 'block';
      if (listEl) listEl.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--muted);"><i class="fas fa-spinner fa-spin"></i> Tüm kütüphane taranıyor...</div>';
    }

    async function executeDeepSearch(query) {
      const q = (query || '').trim();
      if (!q) {
        _restoreViewsForEmptyDeepSearch();
        return;
      }

      _showDeepSearchLoading();
      const listEl = document.getElementById('deep-search-list');
      const countEl = document.getElementById('deep-search-count');

      try {
        const res = await apiFetch(`/api/search/deep?q=${encodeURIComponent(q)}&limit=30`);
        if (!res?.ok) {
          if (listEl) listEl.innerHTML = '<div style="color:var(--accent); text-align:center; padding:1.5rem;">Arama sırasında hata oluştu.</div>';
          return;
        }
        const data = await res.json();
        const results = data.results || [];
        if (countEl) countEl.textContent = `${results.length} eşleşme`;

        if (results.length === 0) {
          if (listEl) listEl.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--muted);"><i class="fas fa-search" style="font-size:2rem; opacity:0.3; margin-bottom:0.5rem; display:block;"></i>Bu kelimeyi içeren herhangi bir kitap sayfası bulunamadı.</div>';
          return;
        }

        if (listEl) {
          listEl.innerHTML = renderDeepSearchResults(results);
        }
      } catch (err) {
        if (listEl) listEl.innerHTML = `<div style="color:var(--accent); text-align:center; padding:1.5rem;">Hata: ${esc(String(err))}</div>`;
      }
    }
    window.executeDeepSearch = executeDeepSearch;

    // --- [6.4] Mobile Handoff Deep-Link Auto-Opener ---
    document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const openHash = urlParams.get('open_book');
      const openPage = Number.parseInt(urlParams.get('page') || '1', 10);
      if (openHash) {
        setTimeout(() => {
          if (typeof openWorkspaceAtPage === 'function') {
            openWorkspaceAtPage(openHash, openPage);
          }
        }, 500);
      }
    });

    // ── [Option C] In-Place PDF Compression / Size Reducer ──
    async function compressBook(fileHash) {
      if (!fileHash) return;
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Bu PDF dosyasını kayıpsız/hafif JPEG sıkıştırma ile optimize etmek istiyor musunuz? Orijinal dosya güvenlik amacıyla yedeklenerek optimize edilir.', 'PDF Optimize Et', 'Optimize Et', false) : Promise.resolve(confirm('Bu PDF dosyasını optimize etmek istiyor musunuz?')));
      if (!ok) {
        return;
      }

      const btn = document.getElementById(`btn-compress-${fileHash}`) || document.querySelector(`button[onclick*="compressBook('${fileHash}')"]`);
      const prevHtml = btn ? btn.innerHTML : null;
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Optimize Ediliyor...';
      }

      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(fileHash)}/compress`, { method: 'POST' });
        if (!res) return;
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data?.detail || data?.message || `HTTP ${res.status}`);
        }
        if (data?.success) {
          showToast(`PDF Optimize Edildi!\nEski Boyut: ${data.old_mb} MB ➔ Yeni: ${data.new_mb} MB (%${data.reduction_percent} tasarruf)`, 'success');
          // Reload book list to reflect new size
          if (typeof loadBooksFromAPI === 'function') loadBooksFromAPI(1, false);
          // Update details modal if open
          const sizeEl = document.querySelector('#modal-content .book-info-row span:last-child');
          if (sizeEl) sizeEl.textContent = `${data.new_mb} MB`;
        } else {
          showToast(`${data?.message || 'Sıkıştırma tamamlandı.'}`, 'info');
        }
      } catch (err) {
        showToast(`Sıkıştırma hatası: ${err.message || 'İşlem gerçekleştirilemedi.'}`, 'error');
      } finally {
        if (btn && prevHtml) {
          btn.disabled = false;
          btn.innerHTML = prevHtml;
        }
      }
    }
    window.compressBook = compressBook;

    // ── [Option C] Duplicate Book Hunter ──
    async function openDuplicatesModal() {
      const modal = document.getElementById('duplicates-modal');
      const container = document.getElementById('duplicates-container');
      if (!modal || !container) return;

      modal.classList.remove('closing');
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      activateModalFocus(modal);
      container.innerHTML = '<div style="text-align:center; padding:2.5rem; color:var(--muted);"><i class="fas fa-spinner fa-spin fa-2x" style="margin-bottom:0.8rem; display:block; color:var(--accent);"></i>Kütüphane mükerrer kopyalar için taranıyor...</div>';

      try {
        const res = await apiFetch('/api/books/duplicates');
        if (!res) return;
        if (!res.ok) {
          throw new Error(`Sunucu hatası: ${res.status}`);
        }
        const data = await res.json();
        if (!data?.duplicates?.length) {
          container.innerHTML = `
            <div style="text-align:center; padding:3rem 1.5rem; color:var(--muted);">
              <i class="fas fa-check-circle" style="font-size:3rem; color:#22c55e; margin-bottom:1rem; display:block;"></i>
              <h4 style="font-size:1.15rem; color:var(--ink); margin-bottom:0.4rem; font-weight:700;">Mükerrer Kitap Bulunamadı</h4>
              <p style="font-size:0.85rem;">Kütüphaneniz tertemiz! Aynı ada, yazara veya dosya boyutuna sahip yinelenen kitap tespit edilmedi.</p>
            </div>
          `;
          return;
        }

        renderDuplicateGroups(data.duplicates);
      } catch (err) {
        container.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--accent);">Tarama hatası: ${esc(String(err))}</div>`;
      }
    }
    window.openDuplicatesModal = openDuplicatesModal;

    function closeDuplicatesModal() {
      closeModalWithAnimation('duplicates-modal');
    }
    window.closeDuplicatesModal = closeDuplicatesModal;

    function renderDuplicateGroups(groups) {
      const container = document.getElementById('duplicates-container');
      if (!container) return;

      container.innerHTML = groups.map((g, gIdx) => {
        const itemsHtml = g.items.map(b => {
          const mb = b.dosya_boyutu ? (b.dosya_boyutu / (1024 * 1024)).toFixed(2) + ' MB' : 'Bilinmiyor';
          const p = b.sayfa_sayisi ? `${b.sayfa_sayisi} sayfa` : '';
          return `
            <div class="dup-item-card duplicate-item-row" id="dup-item-${b.dosya_hash}">
              <div class="duplicate-item-meta">
                <div class="duplicate-item-title">${esc(b.kitap_adi || 'Başlıksız')}</div>
                <div class="duplicate-item-sub">
                  <span><i class="fas fa-file-alt"></i> ${mb}</span>
                  ${p ? `<span><i class="fas fa-bookmark"></i> ${p}</span>` : ''}
                  <span class="duplicate-item-hash">#${b.dosya_hash.substring(0, 10)}</span>
                </div>
              </div>
              <div class="duplicate-item-actions">
                <button type="button" class="btn-sm duplicate-btn-inspect" onclick="openWorkspaceAtPage('${b.dosya_hash}', 1)" title="Kitabı Aç">
                  <i class="fas fa-eye"></i> İncele
                </button>
                <button type="button" class="btn-sm duplicate-btn-delete" onclick="deleteDuplicateBook('${b.dosya_hash}', this, 'dup-group-${gIdx}')" title="Bu kopyayı sil">
                  <i class="fas fa-trash"></i> Kopyayı Sil
                </button>
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="dup-group-card duplicate-group-card" id="dup-group-${gIdx}">
            <div class="duplicate-group-header">
              <div class="duplicate-group-title">
                <i class="fas fa-clone"></i> ${esc(g.title || 'Mükerrer Grup')}
                <span class="duplicate-group-author">${g.author ? `— ${esc(g.author)}` : ''}</span>
              </div>
              <span class="badge duplicate-count-badge">
                ${g.items.length} Kopya Bulundu (${esc(g.reason || 'Benzerlik')})
              </span>
            </div>
            <div class="duplicate-group-list">
              ${itemsHtml}
            </div>
          </div>
        `;
      }).join('');
    }

    function updateDuplicateDOMAfterDelete(fileHash, groupId) {
      const itemEl = document.getElementById(`dup-item-${fileHash}`);
      if (itemEl) itemEl.remove();

      // Check if group now has <= 1 item left
      const groupEl = document.getElementById(groupId);
      if (groupEl) {
        const remaining = groupEl.querySelectorAll('.dup-item-card');
        if (remaining.length <= 1) {
          groupEl.remove();
        }
      }

      // Check if all groups are gone
      const container = document.getElementById('duplicates-container');
      if (container && !container.querySelector('.dup-group-card')) {
        container.innerHTML = `
          <div style="text-align:center; padding:3rem 1.5rem; color:var(--muted);">
            <i class="fas fa-check-circle" style="font-size:3rem; color:#22c55e; margin-bottom:1rem; display:block;"></i>
            <h4 style="font-size:1.15rem; color:var(--ink); margin-bottom:0.4rem; font-weight:700;">Tüm Mükerrer Kopyalar Temizlendi</h4>
          </div>
        `;
      }
    }

    async function deleteDuplicateBook(fileHash, btnEl, groupId) {
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Bu mükerrer kopyayı kalıcı olarak silmek istediğinize emin misiniz?', 'Kopyayı Sil', 'Sil', true) : Promise.resolve(confirm('Bu mükerrer kopyayı kalıcı olarak silmek istediğinize emin misiniz?')));
      if (!ok) return;

      if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      }

      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(fileHash)}`, { method: 'DELETE' });
        if (!res) return;
        let data = {};
        try {
          data = await res.json();
        } catch (_) {
          // Non-JSON responses are tolerated if status is ok
        }
        if (res.ok && data.success !== false) {
          showToast('Kopya başarıyla silindi.', 'success');
          updateDuplicateDOMAfterDelete(fileHash, groupId);
          if (typeof loadBooksFromAPI === 'function') loadBooksFromAPI(1, false);
        } else {
          showToast(`Silme başarısız: ${data?.detail || data?.message || 'Hata oluştu'}`, 'error');
        }
      } catch (err) {
        showToast(`Silme hatası: ${err.message}`, 'error');
      } finally {
        if (btnEl) btnEl.disabled = false;
      }
    }
    window.deleteDuplicateBook = deleteDuplicateBook;

    // ── [Option C] Portable Full Library Zip Export ──
    function exportFullLibraryZip() {
      showToast('📦 Kütüphane zip arşivi hazırlanıyor...\nDosya boyutuna göre birkaç saniye sürebilir, lütfen bekleyin.', 'info');
      // Direct browser navigation to start streaming download
      window.location.href = '/api/database/export-full-zip';
    }
    window.exportFullLibraryZip = exportFullLibraryZip;

    // ── [Option B] PWA Install Prompt Handlers ──
    let deferredPwaPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPwaPrompt = e;
      const pwaBtn = document.getElementById('btn-pwa-install');
      const compactPwaBtn = document.getElementById('compact-pwa-install');
      if (pwaBtn) pwaBtn.style.display = 'flex';
      if (compactPwaBtn) compactPwaBtn.style.display = 'flex';
    });

    window.addEventListener('appinstalled', () => {
      deferredPwaPrompt = null;
      const pwaBtn = document.getElementById('btn-pwa-install');
      const compactPwaBtn = document.getElementById('compact-pwa-install');
      if (pwaBtn) pwaBtn.style.display = 'none';
      if (compactPwaBtn) compactPwaBtn.style.display = 'none';
      showToast('🎉 Dijital Kütüphane uygulamanız başarıyla yüklendi!', 'success');
    });

    async function triggerPwaInstall() {
      if (!deferredPwaPrompt) {
        showToast('PWA yükleme yönergesi: Tarayıcınızın adres çubuğundaki (veya menüdeki) "Uygulamayı Yükle" simgesine basabilirsiniz.', 'info');
        return;
      }
      deferredPwaPrompt.prompt();
      const { outcome } = await deferredPwaPrompt.userChoice;
      if (outcome === 'accepted') {
        deferredPwaPrompt = null;
        const pwaBtn = document.getElementById('btn-pwa-install');
        const compactPwaBtn = document.getElementById('compact-pwa-install');
        if (pwaBtn) pwaBtn.style.display = 'none';
        if (compactPwaBtn) compactPwaBtn.style.display = 'none';
      }
    }
    window.triggerPwaInstall = triggerPwaInstall;

    // --- HEADER TOOLS MENU ---
    function toggleToolsMenu(event) {
      if (event) {
        event.stopPropagation();
      }
      const menu = document.getElementById('header-tools-menu');
      const trigger = document.getElementById('header-tools-btn');
      if (!menu) return;
      const isHidden = menu.style.display === 'none' || !menu.style.display || menu.classList.contains('closing');
      if (isHidden) {
        const firstItem = menu.querySelector('.tools-menu-item, button, a');
        if (trigger) trigger.setAttribute('aria-expanded', 'true');
        if (window.Motion && typeof window.Motion.enter === 'function') {
          void window.Motion.enter(menu, {
            className: '',
            showDisplay: 'flex',
            origin: 'top right',
            cleanExitClass: 'closing',
            focusEl: firstItem
          });
        } else {
          menu.classList.remove('closing');
          menu.style.display = 'flex';
          if (firstItem) requestAnimationFrame(() => firstItem.focus({ preventScroll: true }));
        }
      } else {
        closeToolsMenu({ restoreFocus: true });
      }
    }
    window.toggleToolsMenu = toggleToolsMenu;

    function closeToolsMenu(opts = {}) {
      const menu = document.getElementById('header-tools-menu');
      const trigger = document.getElementById('header-tools-btn');
      if (!menu || menu.style.display === 'none' || menu.classList.contains('closing')) return;
      const restoreFocus = opts.restoreFocus !== false;
      if (trigger) trigger.setAttribute('aria-expanded', 'false');

      const finalize = () => {
        if (restoreFocus && trigger && trigger.isConnected && typeof trigger.focus === 'function') {
          trigger.focus({ preventScroll: true });
        }
      };

      if (window.Motion && typeof window.Motion.exit === 'function') {
        void window.Motion.exit(menu, {
          className: 'closing',
          hideDisplay: true,
          afterFn: finalize
        });
      } else {
        menu.classList.add('closing');
        setTimeout(() => {
          menu.classList.remove('closing');
          menu.style.display = 'none';
          finalize();
        }, 150);
      }
    }
    window.closeToolsMenu = closeToolsMenu;

    document.addEventListener('click', (e) => {
      const wrapper = document.getElementById('header-tools-wrapper');
      if (wrapper && !wrapper.contains(e.target)) {
        closeToolsMenu({ restoreFocus: false });
      }
    });

