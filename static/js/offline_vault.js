/* ════════════════════════════════════════════════════════════════════════════════
 * offline_vault.js — IndexedDB Offline Book Vault, Catalog Snapshot & Sync Outbox
 * ════════════════════════════════════════════════════════════════════════════════ */

(function () {
  const DB_NAME = 'kutuphane_vault_db';
  const DB_VERSION = 1;
  const vaultedHashesSet = new Set();
  let _dbPromise = null;

  function openVaultDB() {
    if (_dbPromise) return _dbPromise;
    if (typeof indexedDB === 'undefined') return Promise.resolve(null);
    _dbPromise = new Promise((resolve) => {
      try {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = (ev) => {
          const db = ev.target.result;
          if (!db.objectStoreNames.contains('vault_books')) {
            db.createObjectStore('vault_books', { keyPath: 'hash' });
          }
          if (!db.objectStoreNames.contains('catalog_snapshot')) {
            db.createObjectStore('catalog_snapshot', { keyPath: 'id' });
          }
          if (!db.objectStoreNames.contains('mutation_outbox')) {
            db.createObjectStore('mutation_outbox', { keyPath: 'id', autoIncrement: true });
          }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => {
          _dbPromise = null;
          resolve(null);
        };
      } catch (_err) {
        _dbPromise = null;
        resolve(null);
      }
    });
    return _dbPromise;
  }

  async function refreshVaultedHashes() {
    const db = await openVaultDB();
    if (!db) return vaultedHashesSet;
    return new Promise((resolve) => {
      try {
        const tx = db.transaction('vault_books', 'readonly');
        const req = tx.objectStore('vault_books').getAllKeys();
        req.onsuccess = () => {
          vaultedHashesSet.clear();
          (req.result || []).forEach(k => vaultedHashesSet.add(String(k)));
          syncVaultBadgesInDOM();
          resolve(vaultedHashesSet);
        };
        req.onerror = () => resolve(vaultedHashesSet);
      } catch (_e) {
        resolve(vaultedHashesSet);
      }
    });
  }

  function isBookVaulted(hash) {
    return Boolean(hash && vaultedHashesSet.has(String(hash)));
  }

  async function getVaultedBook(hash) {
    if (!hash) return null;
    const db = await openVaultDB();
    if (!db) return null;
    return new Promise((resolve) => {
      try {
        const tx = db.transaction('vault_books', 'readonly');
        const req = tx.objectStore('vault_books').get(String(hash));
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      } catch (_e) {
        resolve(null);
      }
    });
  }

  async function saveBookToVault(book) {
    if (!book?.hash) throw new Error('Geçersiz kitap bilgisi.');
    const db = await openVaultDB();
    if (!db) throw new Error('Tarayıcı IndexedDB depolamasını desteklemiyor.');

    const fname = String(book.file || book.dosya_adi || '').toLowerCase();
    const isStructured = fname.endsWith('.epub') || fname.endsWith('.txt');

    let pdfBuffer = null;
    let readerContent = null;
    let sizeBytes = 0;

    if (isStructured) {
      const res = await apiFetch(`/api/books/${encodeURIComponent(book.hash)}/reader-content`);
      if (!res?.ok) throw new Error('Kitap içeriği sunucudan alınamadı.');
      readerContent = await res.json();
      sizeBytes = JSON.stringify(readerContent).length;
    } else {
      const res = await apiFetch(`/api/download/${encodeURIComponent(book.hash)}`, { timeout: 180000 });
      if (!res?.ok) throw new Error('PDF dosyası indirilemedi.');
      pdfBuffer = await res.arrayBuffer();
      sizeBytes = pdfBuffer.byteLength;
    }

    const record = {
      hash: String(book.hash),
      title: book.title || '',
      author: book.author || '',
      file: book.file || '',
      format: isStructured ? (fname.endsWith('.epub') ? 'epub' : 'txt') : 'pdf',
      pdfBuffer,
      readerContent,
      sizeBytes,
      savedAt: Date.now()
    };

    await new Promise((resolve, reject) => {
      const tx = db.transaction('vault_books', 'readwrite');
      tx.objectStore('vault_books').put(record);
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => reject(tx.error || new Error('IndexedDB yazma hatası'));
    });

    vaultedHashesSet.add(String(book.hash));
    syncVaultBadgesInDOM();
    return record;
  }

  async function removeBookFromVault(hash) {
    if (!hash) return false;
    const db = await openVaultDB();
    if (!db) return false;
    await new Promise((resolve) => {
      const tx = db.transaction('vault_books', 'readwrite');
      tx.objectStore('vault_books').delete(String(hash));
      tx.oncomplete = () => resolve(true);
      tx.onerror = () => resolve(false);
    });
    vaultedHashesSet.delete(String(hash));
    syncVaultBadgesInDOM();
    return true;
  }

  async function saveCatalogSnapshot(booksArray) {
    if (!Array.isArray(booksArray) || booksArray.length === 0) return;
    const db = await openVaultDB();
    if (!db) return;
    try {
      const tx = db.transaction('catalog_snapshot', 'readwrite');
      tx.objectStore('catalog_snapshot').put({
        id: 'primary',
        items: booksArray,
        updatedAt: Date.now()
      });
    } catch (_e) {}
  }

  async function loadCatalogSnapshot() {
    const db = await openVaultDB();
    if (!db) return null;
    return new Promise((resolve) => {
      try {
        const tx = db.transaction('catalog_snapshot', 'readonly');
        const req = tx.objectStore('catalog_snapshot').get('primary');
        req.onsuccess = () => resolve(req.result?.items || null);
        req.onerror = () => resolve(null);
      } catch (_e) {
        resolve(null);
      }
    });
  }

  async function enqueueOfflineMutation(url, method, bodyObj) {
    const db = await openVaultDB();
    if (!db) return;
    try {
      const tx = db.transaction('mutation_outbox', 'readwrite');
      tx.objectStore('mutation_outbox').add({
        url,
        method: method || 'POST',
        body: bodyObj,
        queuedAt: Date.now()
      });
    } catch (_e) {}
  }

  async function flushMutationOutbox() {
    if (typeof navigator !== 'undefined' && !navigator.onLine) return 0;
    const db = await openVaultDB();
    if (!db) return 0;
    const items = await new Promise((resolve) => {
      try {
        const tx = db.transaction('mutation_outbox', 'readonly');
        const req = tx.objectStore('mutation_outbox').getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => resolve([]);
      } catch (_e) {
        resolve([]);
      }
    });

    let flushed = 0;
    for (const item of items) {
      try {
        const res = await apiFetch(item.url, {
          method: item.method,
          headers: { 'Content-Type': 'application/json' },
          body: item.body ? JSON.stringify(item.body) : undefined
        });
        if (res && (res.ok || res.status < 500)) {
          await new Promise((resolve) => {
            const tx = db.transaction('mutation_outbox', 'readwrite');
            tx.objectStore('mutation_outbox').delete(item.id);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => resolve(false);
          });
          flushed++;
        }
      } catch (_netErr) {
        break;
      }
    }
    if (flushed > 0 && typeof showToast === 'function') {
      showToast(`${flushed} çevrimdışı okuma kaydı sunucuyla eşitlendi.`, 'success');
    }
    return flushed;
  }

  function syncVaultBadgesInDOM() {
    document.querySelectorAll('.book-card[data-hash]').forEach(card => {
      const h = card.dataset.hash;
      const cover = card.querySelector('.card-cover');
      if (!cover) return;
      let badge = cover.querySelector('.card-vault-badge');
      if (isBookVaulted(h)) {
        if (!badge) {
          badge = document.createElement('span');
          badge.className = 'card-vault-badge';
          badge.title = 'Çevrimdışı Okuma Kasasında Kayıtlı';
          badge.innerHTML = '<i class="fas fa-shield-check"></i> Çevrimdışı';
          cover.appendChild(badge);
        }
      } else if (badge) {
        badge.remove();
      }
    });

    const wsBtn = document.getElementById('workspace-vault-btn');
    if (wsBtn && typeof activeWorkspaceBook !== 'undefined' && activeWorkspaceBook?.hash) {
      const vaulted = isBookVaulted(activeWorkspaceBook.hash);
      wsBtn.classList.toggle('active', vaulted);
      const sp = wsBtn.querySelector('span');
      if (sp) sp.textContent = vaulted ? 'Kasada Kayıtlı' : 'Çevrimdışı Kaydet';
    }
  }

  async function toggleVaultBookByHash(hash) {
    const book = (window.allBooks || []).find(b => b.hash === hash) ||
      (typeof activeWorkspaceBook !== 'undefined' && activeWorkspaceBook?.hash === hash ? activeWorkspaceBook : null);
    if (!book) return;

    const modalBtn = document.getElementById(`btn-modal-vault-${hash}`);
    if (isBookVaulted(hash)) {
      await removeBookFromVault(hash);
      if (modalBtn) {
        modalBtn.classList.remove('active');
        modalBtn.innerHTML = '<i class="fas fa-cloud-arrow-down"></i> Çevrimdışı Kasaya Kaydet';
      }
      if (typeof showToast === 'function') showToast('Kitap çevrimdışı kasadan kaldırıldı.', 'info');
      return;
    }

    if (modalBtn) {
      modalBtn.disabled = true;
      modalBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kasaya İndiriliyor...';
    }
    try {
      const rec = await saveBookToVault(book);
      const mb = Math.max(0.1, (rec.sizeBytes / (1024 * 1024))).toFixed(1);
      if (modalBtn) {
        modalBtn.disabled = false;
        modalBtn.classList.add('active');
        modalBtn.innerHTML = '<i class="fas fa-circle-check" style="color:var(--ok);"></i> Çevrimdışı Kasada Kayıtlı';
      }
      if (typeof showToast === 'function') {
        showToast(`"${book.title || 'Kitap'}" çevrimdışı kasaya kaydedildi (${mb} MB).`, 'success');
      }
    } catch (err) {
      if (modalBtn) {
        modalBtn.disabled = false;
        modalBtn.innerHTML = '<i class="fas fa-cloud-arrow-down"></i> Çevrimdışı Kasaya Kaydet';
      }
      if (typeof showToast === 'function') {
        showToast(err?.message || 'Çevrimdışı kayıt başarısız oldu.', 'error');
      }
    }
  }

  async function toggleVaultCurrentWorkspaceBook() {
    if (typeof activeWorkspaceBook !== 'undefined' && activeWorkspaceBook?.hash) {
      await toggleVaultBookByHash(activeWorkspaceBook.hash);
    }
  }

  window.OfflineVault = {
    openVaultDB,
    refreshVaultedHashes,
    isBookVaulted,
    getVaultedBook,
    saveBookToVault,
    removeBookFromVault,
    saveCatalogSnapshot,
    loadCatalogSnapshot,
    enqueueOfflineMutation,
    flushMutationOutbox,
    syncVaultBadgesInDOM
  };
  window.toggleVaultBookByHash = toggleVaultBookByHash;
  window.toggleVaultCurrentWorkspaceBook = toggleVaultCurrentWorkspaceBook;

  window.addEventListener('online', () => {
    void flushMutationOutbox();
  });
  document.addEventListener('DOMContentLoaded', () => {
    void refreshVaultedHashes();
    if (navigator.onLine) {
      void flushMutationOutbox();
    }
  });
})();
