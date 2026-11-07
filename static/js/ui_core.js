/* ═══════════ ui_core.js — UI Rendering, Grid, Table & Collections ═══════════ */
    window.shouldStagger = true;
    // --- CATEGORY LABELS ---
    function buildCategoryTags() {
      const books = window.allBooks || [];
      const cats = [...new Set(books.map(b => b.category).filter(Boolean))].sort((a, b) => a.localeCompare(b));
      const menu = document.getElementById('category-menu');
      const trigger = document.getElementById('category-trigger');

      let html = `<div class="dropdown-item ${window.activeCategory === 'all' ? 'active' : ''}" onclick="selectCat('all', 'Tüm Kategoriler')"><i class="fas fa-layer-group"></i> Tüm Kategoriler</div>`;

      cats.forEach(cat => {
        const encodedCat = encData(cat);
        html += `<div class="dropdown-item ${window.activeCategory === cat ? 'active' : ''}" data-value="${encodedCat}" data-label="${encodedCat}" onclick="selectCat(decodeURIComponent(this.dataset.value), decodeURIComponent(this.dataset.label))"><i class="fas fa-tag"></i> ${esc(cat)}</div>`;
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

          let html = `<div class="dropdown-item ${window.activeCollection === 'all' ? 'active' : ''}" onclick="selectCol('all', 'Tüm Koleksiyonlar')"><i class="fas fa-folder-open"></i> Tüm Koleksiyonlar</div>`;

          (window.allCollections || []).forEach(c => {
            const encodedName = encData(c.isim);
            html += `<div class="dropdown-item ${window.activeCollection === String(c.id) ? 'active' : ''}" data-value="${c.id}" data-label="${encodedName}" onclick="selectCol(this.dataset.value, decodeURIComponent(this.dataset.label))"><i class="fas fa-folder"></i> ${esc(c.isim)}</div>`;
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
      if (dropCol) dropCol.classList.remove('open');
      render();
      loadCollectionsFromAPI().catch(err => console.warn(err)); // Update active states
    }

    function toggleDropdown(id) {
      const el = document.getElementById(id);
      if (!el) return;
      const isOpen = el.classList.contains('open');

      // Close others
      document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('open'));

      if (!isOpen) el.classList.add('open');
    }

    // Global click listener to close dropdowns
    window.addEventListener('click', (e) => {
      if (!e.target?.closest?.('.custom-dropdown')) {
        document.querySelectorAll('.custom-dropdown').forEach(d => d.classList.remove('open'));
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
      <div class="col-row" style="display:flex; justify-content:space-between; align-items:center; background:var(--paper); padding: 0.6rem 0.8rem; border-radius:12px; border: 1px solid var(--line); transition: all 0.2s; margin-bottom:0.6rem; min-width: 0;" onmouseover="this.style.borderColor='var(--sepia)'" onmouseout="this.style.borderColor='var(--line)'">
         <div style="display:flex; align-items:center; gap: 0.8rem; min-width: 0; flex: 1;">
            <i class="fas fa-folder" style="color: var(--sepia-light); font-size:1.1rem; flex-shrink: 0;"></i>
            <span style="font-family:'Instrument Serif', serif; font-size:1.05rem; color:var(--ink); font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">${esc(c.isim)}</span>
         </div>
         <div style="display:flex; align-items:center; gap: 0.4rem; flex-shrink: 0; margin-left: 0.8rem;">
           <button type="button" onclick="event.stopPropagation(); toggleBookCol(${c.id}, ${!inCol})" style="background:${inCol ? 'var(--line)' : 'var(--accent)'}; color:${inCol ? 'var(--ink)' : '#fff'}; border:none; border-radius:50px; padding:0.4rem 0.9rem; font-family:'Geist', sans-serif; font-weight:600; font-size:0.75rem; cursor:pointer; transition: all 0.2s; display:flex; align-items:center; gap:0.4rem; white-space:nowrap;">
               ${inCol ? '<i class="fas fa-minus" style="font-size:0.6rem"></i> Çıkar' : '<i class="fas fa-plus" style="font-size:0.6rem"></i> Ekle'}
           </button>
           
           <div class="custom-dropdown share-dropdown" style="position:relative; display:inline-block; min-width: auto;">
             <button type="button" onclick="event.stopPropagation(); toggleShareMenu(this)" style="background:none; color:var(--muted); border:none; width:34px; height:34px; border-radius:50%; cursor:pointer; font-size: 1rem; transition: all 0.2s; display:flex; align-items:center; justify-content:center;" onmouseover="this.style.background='var(--line)'; this.style.color='var(--accent)';" onmouseout="this.style.background='none'; this.style.color='var(--muted)';" title="Paylaş">
                 <i class="fas fa-share-alt"></i>
             </button>
             <div class="dropdown-menu" style="right:0; top:calc(100% + 5px); min-width:180px; z-index:100; left:auto; width:auto; padding:0.4rem;">
                <div class="dropdown-item" style="padding:0.6rem 0.8rem;" onclick="window.location.href='/api/share-collection/${c.id}'"><i class="fas fa-file-download"></i> JSON İndir</div>
                <div class="dropdown-item" style="padding:0.6rem 0.8rem;" onclick="copyCollectionMarkdown(${c.id}, decodeURIComponent('${encodedName}'))"><i class="fas fa-copy"></i> Markdown Kopyala</div>
             </div>
           </div>

           <button type="button" onclick="event.stopPropagation(); deleteCollection(${c.id})" style="background:none; color:var(--muted); border:none; width:34px; height:34px; border-radius:50%; cursor:pointer; font-size: 0.9rem; transition: all 0.2s; display:flex; align-items:center; justify-content:center;" onmouseover="this.style.background='rgba(255,62,62,0.1)'; this.style.color='#ff3e3e'" onmouseout="this.style.background='none'; this.style.color='var(--muted)'" title="Koleksiyonu Sil">
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

      document.getElementById('col-modal').classList.add('open');
      document.body.classList.add('modal-open');
      document.body.classList.add('modal-open');
    }

    function toggleShareMenu(btn) {
      const container = btn.parentElement;
      const isOpen = container.classList.contains('open');
      // Close all dropdowns first
      document.querySelectorAll('.custom-dropdown').forEach(m => m.classList.remove('open'));
      if (!isOpen) container.classList.add('open');
    }

    async function deleteCollection(colId) {
      if (!confirm("Koleksiyonu silmek istediğinize emin misiniz? (İçindeki kitaplar silinmez, sadece liste silinir)")) return;
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
      if (statTotal) statTotal.textContent = total;
      document.querySelectorAll('.stat-total-val').forEach(el => el.textContent = total);
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
            return `
              <div class="shelf-item" onclick="const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(this, target); else openWorkspace(target); }">
                <div class="shelf-item-cover">
                  ${cover}
                </div>
                <div class="shelf-item-info">
                  <span class="shelf-item-cat">${esc(b.category) || 'Genel'}</span>
                  <h4 class="shelf-item-title">${esc(b.title) || 'İsimsiz'}</h4>
                  <span class="shelf-item-author">${esc(b.author) || 'Bilinmeyen Yazar'}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }
    window.renderRecentShelf = renderRecentShelf;

    // --- PERSISTENT ELEMENT MAPS (60FPS ZERO-REBUILD ARCHITECTURE) ---
    const cardElementsMap = new Map();
    window.cardElementsMap = cardElementsMap;
    const tableRowsMap = new Map();
    window.tableRowsMap = tableRowsMap;

    function createBookCardElement(b) {
      const card = document.createElement('div');
      card.className = 'book-card';
      card.id = `book-${b.hash}`;
      card.dataset.hash = b.hash;

      const coverInner = b.has_cover
        ? `<img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')">`
        : `<div class="card-cover-placeholder">${BOOK_ICON_LG}<span>${esc(b.title) || 'Kapak yok'}</span></div>`;

      const favIcon = b.is_favorite
        ? `<i class="fas fa-heart" style="color: #ff3e3e; font-size: 1.1rem;"></i>`
        : `<i class="far fa-heart" style="color: #fff; font-size: 1.1rem;"></i>`;
      const favBtnText = b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle';

      card.innerHTML = `
        <div class="selection-indicator"></div>
        <div class="card-cover">
          <div class="card-cat-badge">${esc(b.category)}</div>
          <div class="btn-favorite-card" onclick="event.stopPropagation(); toggleFavorite('${b.hash}')" title="${favBtnText}">
             ${favIcon}
          </div>
          ${coverInner}
        </div>
        <div class="card-body">
          <div class="card-title">${esc(b.title) || '<em>İsimsiz</em>'}</div>
          <div class="card-author">${esc(b.author) || 'Bilinmeyen Yazar'}</div>
        </div>
      `;

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

      card.onclick = () => {
        if (window.isSelectionMode) {
          toggleSelectBook(card, b.hash);
        } else {
          const bookObj = (window.allBooks || []).find(x => x.hash === b.hash) || b;
          openModal(bookObj);
        }
      };

      return card;
    }

    // --- GRID ---
    function renderGrid(books) {
      const grid = document.getElementById('grid-view');
      if (!grid) return;
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
            ? `<i class="fas fa-heart" style="color: #ff3e3e; font-size: 1.1rem;"></i>`
            : `<i class="far fa-heart" style="color: #fff; font-size: 1.1rem;"></i>`;
        }
        card.classList.toggle('selected', selectedBooks.has(b.hash));

        // Controlled stagger or instant display
        if (doStagger) {
          card.classList.add('stagger-in');
          const staggerIdx = i < 12 ? i : 0;
          card.style.setProperty('--card-index', staggerIdx);
          card.style.animationDelay = i < 12 ? `${i * 30}ms` : '0ms';
        } else {
          card.classList.remove('stagger-in');
          card.style.animation = 'none';
        }

        card.style.display = '';

        if (!existingCardsInGrid.has(b.hash)) {
          hasMissingCards = true;
        }
      });

      // Hide cards in DOM that are filtered out (Zero DOM removal, zero image reloads)
      for (const [hash, card] of cardElementsMap.entries()) {
        if (!filteredHashes.has(hash)) {
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
          openModal(bookObj);
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
      let hasMissingRows = false;

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

        if (!existingRowsInTbody.has(b.hash)) {
          hasMissingRows = true;
        }
      });

      // Hide rows that are filtered out
      for (const [hash, tr] of tableRowsMap.entries()) {
        if (!filteredHashes.has(hash)) {
          tr.style.display = 'none';
        }
      }

      // Populate if missing rows or empty tbody
      if (hasMissingRows || tbody.querySelectorAll('tr').length === 0) {
        tbody.innerHTML = '';
        books.forEach(b => {
          const tr = tableRowsMap.get(b.hash);
          if (tr) tbody.appendChild(tr);
        });
      }
    }

    function compareTableValues(va, vb, sortDir) {
      if (va < vb) return -sortDir;
      if (va > vb) return sortDir;
      return 0;
    }

    // --- SIRALA ---
    function sortTable(col) {
      const keys = ['title', 'author', 'category', 'subcat', 'summary'];
      if (window.sortCol === col) window.sortDir *= -1; else { window.sortCol = col; window.sortDir = 1; }
      (window.allBooks || []).sort((a, b) => {
        const va = (a[keys[col]] || '').toLowerCase();
        const vb = (b[keys[col]] || '').toLowerCase();
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
    function openModal(b) {
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
        ? `<div class="modal-cover-wrap"><img src="/thumbnails/${b.hash}.jpg" alt="${esc(b.title)}" loading="lazy" decoding="async" onload="this.classList.add('loaded')" style="width:200px; height:266px; object-fit:cover; border-radius:8px; box-shadow:0 10px 30px var(--shadow);"></div>`
        : `<div class="modal-cover-wrap"><div class="modal-cover-empty" style="width:200px; height:266px; background:var(--sepia-pale); border-radius:8px; display:flex; align-items:center; justify-content:center;">${BOOK_ICON_LG}</div></div>`;

      document.getElementById('modal-content').innerHTML = `
    <div class="modal-layout" style="display: flex; gap: 2.5rem; padding: 2.5rem;">
      <div class="modal-left" style="width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 1rem;">
        ${coverHtml}
        <div class="modal-actions" id="modal-actions-sidebar" style="display: flex; flex-direction: column; gap: 0.75rem;">
          <button class="btn-modal-primary" onclick="closeModalDirect(); const target = (window.allBooks || []).find(x => x.hash === '${b.hash}'); const card = document.querySelector('.book-card[data-hash=\\'${b.hash}\\']'); if (target) { if (typeof openBookWithMorph === 'function') openBookWithMorph(card, target); else openWorkspace(target); }">
            <i class="fas fa-book-open"></i> Kitabı Oku
          </button>
          <button id="btn-modal-fav" class="${b.is_favorite ? 'btn-modal-fav is-fav' : 'btn-modal-fav'}" onclick="toggleFavorite('${b.hash}')">
            <i class="${b.is_favorite ? 'fas' : 'far'} fa-heart"></i> ${b.is_favorite ? 'Favorilerden Çıkar' : 'Favorilere Ekle'}
          </button>
          <button class="btn-modal-secondary" onclick="openColModal('${b.hash}')">
            <i class="fas fa-folder-plus"></i> Koleksiyona Ekle
          </button>
          <button class="btn-modal-secondary btn-cover-upload">
            <i class="fas fa-image"></i> Kapak Değiştir
            <input type="file" accept="image/*" onchange="uploadCover('${b.hash}', this)">
          </button>
          <button class="btn-modal-secondary" onclick="toggleEditMode('${b.hash}')">
            <i class="fas fa-edit"></i> Düzenle
          </button>
          ${!isAnalyzed ? `
          <button class="btn-modal-secondary" id="btn-reanalyze-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" style="background:rgba(234,88,12,0.1); border:1.5px solid #ea580c; color:#ea580c; font-weight:700;">
            <i class="fas fa-magic"></i> Yapay Zeka ile Analiz Et
          </button>
          ` : ''}
          <button class="btn-modal-secondary" style="font-size:0.75rem;" onclick="window.open('/api/download/${b.hash}', '_blank')">
            <i class="fas fa-download"></i> PDF İndir
          </button>
          <div class="export-dropdown-wrapper" style="position:relative; width:100%;">
            <button class="btn-modal-secondary" style="font-size:0.75rem; width:100%; justify-content:center;" onclick="toggleExportMenu('${b.hash}')">
              <i class="fas fa-file-export"></i> Dışa Aktar (PKM) <i class="fas fa-chevron-down" style="font-size:0.65rem; margin-left:auto;"></i>
            </button>
            <div id="export-menu-${b.hash}" class="export-menu" style="display:none; position:absolute; top:100%; left:0; right:0; background:var(--color-surface, #fff); border:1px solid var(--line); border-radius:8px; box-shadow:0 8px 16px rgba(0,0,0,0.12); z-index:100; margin-top:4px; overflow:hidden;">
              <a href="/api/books/${b.hash}/export/obsidian" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer;" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-gem" style="color:#7c3aed;"></i> Obsidian Notu (.md)
              </a>
              <a href="/api/books/${b.hash}/export/anki" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer; border-top:1px solid var(--line);" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-clone" style="color:#2563eb;"></i> Anki Kartları (.tsv)
              </a>
              <a href="/api/books/${b.hash}/export/bibtex" download class="export-menu-item" style="display:flex; align-items:center; gap:0.5rem; padding:0.6rem 0.8rem; font-size:0.75rem; color:var(--ink); text-decoration:none; cursor:pointer; border-top:1px solid var(--line);" onclick="toggleExportMenu('${b.hash}')">
                <i class="fas fa-graduation-cap" style="color:#059669;"></i> BibTeX Akademik (.bib)
              </a>
            </div>
          </div>
          ${b.file?.toLowerCase().endsWith('.pdf') ? `
          <button class="btn-modal-secondary" id="btn-compress-${b.hash}" style="font-size:0.75rem;" onclick="compressBook('${b.hash}')" title="Gereksiz verileri temizleyip PDF boyutunu yerel olarak küçültür">
            <i class="fas fa-compress-arrows-alt" style="color:var(--accent);"></i> Boyutu Küçült (Optimize Et)
          </button>
          ` : ''}
          <button class="btn-modal-danger" onclick="deleteBook('${b.hash}')">
            <i class="fas fa-trash-alt"></i> Kaydı Sil
          </button>
        </div>
        <div class="modal-meta-left" style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem;">
          <span class="meta-chip" style="font-size: 0.6rem; opacity: 0.85; word-break: break-all; white-space: normal; line-height: 1.4; padding: 0.5rem; text-align: center;">📄 ${esc(b.file)}</span>
        </div>
      </div>
      <div class="modal-right" style="flex: 1; border-left: 1px solid var(--line); padding-left: 2rem;">
        <div class="modal-cat" style="color: var(--accent); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.1em;">${esc(b.category)}${b.subcat ? ' / ' + esc(b.subcat) : ''}</div>
        <h2 class="modal-title" style="margin-top: 0.5rem; font-size: 2.2rem; font-family:'Instrument Serif', serif; line-height: 1.1;">${esc(b.title) || 'İsimsiz Kitap'}</h2>
        <div class="modal-author" style="margin-bottom: 1.5rem; font-style: italic; font-size: 1.1rem; color: var(--muted); opacity: 0.9;">${esc(b.author) || 'Bilinmeyen Yazar'}</div>

        ${(!b.category || b.category === 'Bilinmeyen' || b.summary?.includes('Analiz başarısız')) ? `
          <div style="background: rgba(234, 88, 12, 0.08); border: 1.5px dashed #ea580c; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
            <div>
              <div style="font-weight: 700; color: #ea580c; font-size: 0.95rem; display:flex; align-items:center; gap:0.5rem;">
                <i class="fas fa-exclamation-triangle"></i> Yapay Zeka Analizi Bekliyor
              </div>
              <div style="font-size: 0.82rem; color: var(--muted); margin-top: 0.3rem;">
                Bu kitabın başlığı, yazarı ve özeti henüz yapay zeka ile incelenmedi.
              </div>
            </div>
            <button id="btn-reanalyze-banner-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" style="background: #ea580c; color: #fff; border: none; padding: 0.75rem 1.4rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; white-space: nowrap; box-shadow: 0 4px 12px rgba(234,88,12,0.35); transition: all 0.2s;">
              <i class="fas fa-magic"></i> Şimdi Analiz Et
            </button>
          </div>
        ` : ''}
        
        <div class="modal-section-label" style="font-size: 0.65rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 0.5rem;">ÖZET</div>
        <p class="modal-summary" style="text-align: left; line-height: 1.8; font-size: 1.05rem; margin-bottom: 2rem;">${esc(b.summary) || 'Özet bulunamadı.'}</p>
        
        ${keywordChips ? `<div class="modal-section-label" style="font-size: 0.65rem; letter-spacing: 0.2em; opacity: 0.6; margin-bottom: 0.5rem;">ANAHTAR KAVRAMLAR</div><div class="modal-keywords" style="margin-bottom: 1.5rem;">${keywordChips}</div>` : ''}

        <div id="edit-form-${b.hash}" style="display:none; margin-top: 2rem; border-top: 1px solid var(--line); padding-top: 1.5rem;">
          <div style="display:grid; gap: 1rem;">
            <input type="text" id="edit-title-${b.hash}" class="modal-edit-input" value="${esc(b.title)}" placeholder="Kitap Adı" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <input type="text" id="edit-author-${b.hash}" class="modal-edit-input" value="${esc(b.author)}" placeholder="Yazar" onkeydown="if(event.key==='Enter') saveBookEdit('${b.hash}')">
            <textarea id="edit-summary-${b.hash}" class="modal-edit-textarea" rows="5" onkeydown="if(event.key==='Enter' && !event.shiftKey) { event.preventDefault(); saveBookEdit('${b.hash}'); }">${esc(b.summary)}</textarea>
            <button class="btn-modal-save" onclick="saveBookEdit('${b.hash}')">DEĞİŞİKLİKLERİ KAYDET</button>
            <button type="button" class="btn-modal-secondary" id="btn-reanalyze-edit-${b.hash}" onclick="reanalyzeBookModal('${b.hash}')" style="font-size:0.8rem; justify-content:center; opacity:0.85; border:1px dashed var(--line); margin-top:0.25rem;">
              <i class="fas fa-magic"></i> Yapay Zeka ile Yeniden Analiz Et (Metadata Yenile)
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
      document.getElementById('modal').classList.add('open');
      document.body.classList.add('modal-open');
      document.body.classList.add('modal-open');
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
      document.body.classList.add('modal-open');
    }

    // ── Unified Modal Exit Animation (Apple/Tesla Standard) ──
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

      modal.classList.add('closing');
      modal.classList.remove('open');

      setTimeout(() => {
        modal.classList.remove('closing');
        modal.style.display = '';
        const anyModal = document.querySelector('.modal-overlay.open, .modal-overlay.closing');
        if (!anyModal) {
          document.body.classList.remove('modal-open');
        }
        if (typeof callback === 'function') callback();
      }, 150);
    }
    window.closeModalWithAnimation = closeModalWithAnimation;

    function closeModal(e) { if (e.target === document.getElementById('modal')) closeModalDirect(); }
    function closeModalDirect() {
      closeModalWithAnimation('modal', () => {
        window.currentModalHash = null;
      });
    }

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
      if (!confirm(`${selectedBooks.size} kitabı silmek istediğinize emin misiniz?`)) return;

      const toDelete = Array.from(selectedBooks);
      let successCount = 0;
      const failedBooks = [];

      // Open process center
      document.getElementById('ops-center').classList.add('active');

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

      addChatMessage('ai', `✅ ${successCount} kitap başarıyla silindi.`);
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
        m.style.display = 'flex';
        m.classList.add('open');
        document.body.classList.add('modal-open');
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
        openDropdown.classList.remove('open');
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
      // If typing in an input, textarea, or contentEditable, protect shortcuts
      const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable;
      if (isInput) {
        if (e.key === 'Escape') {
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

      Object.entries(viewMap).forEach(([name, el]) => {
        if (!el) return;
        if (name === v) {
          el.style.display = name === 'grid' ? 'grid' : 'block';
          el.classList.remove('view-fade-in');
          el.getBoundingClientRect(); // Force reflow to cleanly restart the entrance animation
          el.classList.add('view-fade-in');
        } else {
          el.style.display = 'none';
          el.classList.remove('view-fade-in');
        }
      });

      const btnGrid = document.getElementById('btn-grid');
      const btnTable = document.getElementById('btn-table');
      const btnStats = document.getElementById('btn-stats');
      if (btnGrid) btnGrid.classList.toggle('active', v === 'grid');
      if (btnTable) btnTable.classList.toggle('active', v === 'table');
      if (btnStats) btnStats.classList.toggle('active', v === 'stats');

      window.shouldStagger = true;
      if (v === 'table') {
        renderTable(getFiltered());
      } else if (v === 'grid') {
        renderGrid(getFiltered());
        setTimeout(enableDragSort, 100);
      }
      window.shouldStagger = false;
      if (v === 'stats' && typeof loadStats === 'function') void loadStats();
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
        const cards = [...grid.querySelectorAll('.book-card[data-hash]')];
        const fromIdx = cards.indexOf(window.dragSrcEl);
        const toIdx = cards.indexOf(this);
        if (fromIdx < toIdx) this.after(window.dragSrcEl);
        else this.before(window.dragSrcEl);
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
          showToast(`✅ Yapay zeka analizi başarıyla tamamlandı!\nKitap: ${d.kitap_adi || ''}\nYazar: ${d.yazar || ''}`, 'success');
          closeModalDirect();
          if (typeof loadBooksFromAPI === 'function') await loadBooksFromAPI();
        } else {
          showToast(`⚠️ Analiz tamamlanamadı: ${res.message || 'API anahtarınızı kontrol edin.'}`, 'warning');
        }
      } catch (err) {
        showToast(`❌ Hata: ${err.message || 'Analiz sırasında sorun oluştu.'}`, 'error');
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
    function _activateDeepSearchUI() {
      const toggleBtn = document.getElementById('btn-deep-search-toggle');
      const label = document.getElementById('deep-search-label');
      const input = document.getElementById('search-input');

      if (toggleBtn) {
        toggleBtn.style.background = 'var(--accent)';
        toggleBtn.style.color = '#fff';
        toggleBtn.style.borderColor = 'var(--accent)';
      }
      if (label) label.textContent = 'Derin Aktif';
      if (input) {
        input.placeholder = '500+ kitabın tüm cümlelerinde ara... (Derin Arama)';
        input.focus();
        if (input.value.trim()) {
          void executeDeepSearch(input.value.trim());
        }
      }
    }

    function _deactivateDeepSearchUI() {
      const toggleBtn = document.getElementById('btn-deep-search-toggle');
      const label = document.getElementById('deep-search-label');
      const input = document.getElementById('search-input');
      const resultsContainer = document.getElementById('deep-search-results');
      const gridView = document.getElementById('grid-view');
      const tableView = document.getElementById('table-view');

      if (toggleBtn) {
        toggleBtn.style.background = 'rgba(255,255,255,0.06)';
        toggleBtn.style.color = 'var(--muted)';
        toggleBtn.style.borderColor = 'var(--line)';
      }
      if (label) label.textContent = 'Derin Arama';
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
          ? `<img src="/thumbnails/${r.dosya_hash}.jpg" style="width:48px; height:64px; object-fit:cover; border-radius:6px; flex-shrink:0;">`
          : `<div style="width:48px; height:64px; background:var(--sepia-pale); border-radius:6px; display:flex; align-items:center; justify-content:center; flex-shrink:0;"><i class="fas fa-book" style="color:var(--muted);"></i></div>`;
        return `
          <div class="deep-search-card" style="display:flex; gap:1rem; padding:0.9rem 1.1rem; background:var(--paper); border:1px solid var(--line); border-radius:10px; align-items:center; transition:border-color 0.2s;" onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='var(--line)'">
            ${coverHtml}
            <div style="flex:1; min-width:0;">
              <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
                <span style="font-weight:700; color:var(--ink); font-size:0.95rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(r.kitap_adi)}</span>
                <span style="font-size:0.75rem; color:var(--muted);">— ${esc(r.yazar)}</span>
                <span class="badge" style="background:var(--accent-glow); color:var(--accent); font-size:0.72rem; padding:1px 6px; border-radius:4px; font-weight:600; margin-left:auto;">Sayfa ${r.sayfa_no}</span>
              </div>
              <div class="deep-snippet" style="font-size:0.83rem; color:var(--text); line-height:1.45; font-family:var(--font-serif, serif);">${sanitizeDeepSnippet(r.snippet)}</div>
            </div>
            <button type="button" class="btn-empty-add" onclick="openWorkspaceAtPage('${r.dosya_hash}', ${r.sayfa_no})" style="padding:0.45rem 0.85rem; font-size:0.78rem; white-space:nowrap; margin-left:0.5rem; flex-shrink:0;">
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
      if (!confirm('Bu PDF dosyasını kayıpsız/hafif JPEG sıkıştırma ile optimize etmek istiyor musunuz? Orijinal dosya güvenlik amacıyla yedeklenerek optimize edilir.')) {
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
        if (res?.success) {
          showToast(`✅ PDF Optimize Edildi!\nEski Boyut: ${res.old_mb} MB ➔ Yeni: ${res.new_mb} MB (%${res.reduction_percent} tasarruf)`, 'success');
          // Reload book list to reflect new size
          if (typeof reloadBooks === 'function') reloadBooks();
          // Update details modal if open
          const sizeEl = document.querySelector('#modal-content .book-info-row span:last-child');
          if (sizeEl) sizeEl.textContent = `${res.new_mb} MB`;
        } else {
          showToast(`ℹ️ ${res?.message || 'Sıkıştırma tamamlandı.'}`, 'info');
        }
      } catch (err) {
        showToast(`❌ Sıkıştırma hatası: ${err.message || 'İşlem gerçekleştirilemedi.'}`, 'error');
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
      modal.style.display = 'flex';
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      container.innerHTML = '<div style="text-align:center; padding:2.5rem; color:var(--muted);"><i class="fas fa-spinner fa-spin fa-2x" style="margin-bottom:0.8rem; display:block; color:var(--accent);"></i>Kütüphane mükerrer kopyalar için taranıyor...</div>';

      try {
        const res = await apiFetch('/api/books/duplicates');
        if (!res?.duplicates?.length) {
          container.innerHTML = `
            <div style="text-align:center; padding:3rem 1.5rem; color:var(--muted);">
              <i class="fas fa-check-circle" style="font-size:3rem; color:#22c55e; margin-bottom:1rem; display:block;"></i>
              <h4 style="font-size:1.15rem; color:var(--ink); margin-bottom:0.4rem; font-weight:700;">Mükerrer Kitap Bulunamadı</h4>
              <p style="font-size:0.85rem;">Kütüphaneniz tertemiz! Aynı ada, yazara veya dosya boyutuna sahip yinelenen kitap tespit edilmedi.</p>
            </div>
          `;
          return;
        }

        renderDuplicateGroups(res.duplicates);
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
            <div class="dup-item-card" id="dup-item-${b.dosya_hash}" style="display:flex; justify-content:space-between; align-items:center; padding:0.75rem 1rem; background:var(--paper-dark); border:1px solid var(--line); border-radius:10px; gap:0.8rem;">
              <div style="min-width:0; flex:1;">
                <div style="font-weight:600; font-size:0.88rem; color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${esc(b.kitap_adi || 'Başlıksız')}</div>
                <div style="font-size:0.76rem; color:var(--muted); display:flex; gap:0.6rem; margin-top:2px; flex-wrap:wrap;">
                  <span><i class="fas fa-file-alt"></i> ${mb}</span>
                  ${p ? `<span><i class="fas fa-bookmark"></i> ${p}</span>` : ''}
                  <span style="font-family:var(--font-mono, monospace); font-size:0.7rem; opacity:0.7;">#${b.dosya_hash.substring(0, 10)}</span>
                </div>
              </div>
              <div style="display:flex; gap:0.4rem; flex-shrink:0;">
                <button type="button" class="btn-sm" onclick="openWorkspaceAtPage('${b.dosya_hash}', 1)" style="padding:0.4rem 0.7rem; font-size:0.76rem; background:var(--paper); border:1px solid var(--line); border-radius:6px; cursor:pointer;" title="Kitabı Aç">
                  <i class="fas fa-eye"></i> İncele
                </button>
                <button type="button" class="btn-sm" onclick="deleteDuplicateBook('${b.dosya_hash}', this, 'dup-group-${gIdx}')" style="padding:0.4rem 0.7rem; font-size:0.76rem; background:rgba(176,71,60,0.12); color:#b0473c; border:1px solid rgba(176,71,60,0.25); border-radius:6px; cursor:pointer; font-weight:600;" title="Bu kopyayı sil">
                  <i class="fas fa-trash"></i> Kopyayı Sil
                </button>
              </div>
            </div>
          `;
        }).join('');

        return `
          <div class="dup-group-card" id="dup-group-${gIdx}" style="border:1px solid var(--line); border-radius:14px; padding:1.1rem; background:var(--paper); box-shadow:0 4px 12px rgba(0,0,0,0.03);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
              <div style="font-weight:700; font-size:0.95rem; color:var(--ink); display:flex; align-items:center; gap:0.5rem;">
                <i class="fas fa-clone" style="color:var(--accent);"></i> ${esc(g.title || 'Mükerrer Grup')}
                <span style="font-size:0.78rem; font-weight:400; color:var(--muted);">${g.author ? `— ${esc(g.author)}` : ''}</span>
              </div>
              <span class="badge" style="background:rgba(184,134,47,0.12); color:#b8862f; font-size:0.72rem; padding:2px 8px; border-radius:6px; font-weight:600;">
                ${g.items.length} Kopya Bulundu (${esc(g.reason || 'Benzerlik')})
              </span>
            </div>
            <div style="display:flex; flex-direction:column; gap:0.5rem;">
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
      if (!confirm('Bu mükerrer kopyayı kalıcı olarak silmek istediğinize emin misiniz?')) return;

      if (btnEl) {
        btnEl.disabled = true;
        btnEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      }

      try {
        const res = await apiFetch(`/api/books/${encodeURIComponent(fileHash)}`, { method: 'DELETE' });
        if (res && res.success !== false) {
          showToast('Kopya başarıyla silindi.', 'success');
          updateDuplicateDOMAfterDelete(fileHash, groupId);
          if (typeof reloadBooks === 'function') reloadBooks();
        } else {
          showToast(`Silme başarısız: ${res?.message || 'Hata oluştu'}`, 'error');
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
      if (pwaBtn) pwaBtn.style.display = 'inline-flex';
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
      if (!menu) return;
      const isHidden = menu.style.display === 'none' || !menu.style.display;
      if (isHidden) {
        menu.classList.remove('closing');
        menu.style.display = 'flex';
      } else {
        closeToolsMenu();
      }
    }
    window.toggleToolsMenu = toggleToolsMenu;

    function closeToolsMenu() {
      const menu = document.getElementById('header-tools-menu');
      if (!menu || menu.style.display === 'none' || menu.classList.contains('closing')) return;
      menu.classList.add('closing');
      setTimeout(() => {
        menu.classList.remove('closing');
        menu.style.display = 'none';
      }, 150);
    }
    window.closeToolsMenu = closeToolsMenu;

    document.addEventListener('click', (e) => {
      const wrapper = document.getElementById('header-tools-wrapper');
      if (wrapper && !wrapper.contains(e.target)) {
        closeToolsMenu();
      }
    });

