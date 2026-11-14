/* ═══════════ ui_graph.js — Network Graph & Relationship Visualization ═══════════ */

function _renderNetworkPlaceholder(container) {
  const oldBtn = document.getElementById('network-back-btn');
  if (oldBtn) oldBtn.remove();

  container.innerHTML = `
    <div class="network-placeholder" style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; color:var(--muted); text-align:center; padding:2rem; background:rgba(26,16,8,0.2); border-radius:12px; border:1px dashed rgba(110,97,76,0.2);">
      <i class="fas fa-project-diagram" style="font-size:3.5rem; margin-bottom:1.2rem; color:var(--accent);"></i>
      <h3 style="font-family:'Instrument Serif',serif; font-size:1.4rem; margin-bottom:0.6rem; color:#f5f0e8;">Kavramsal İlişkiler Ağı</h3>
      <p style="font-size:0.95rem; max-width:420px; line-height:1.6; color:#a89f91;">
        Ağ görünümünü global karmaşadan kurtarıp daha anlamlı ilişkileri görebilmek için yukarıdan bir <strong>Kategori</strong>, <strong>Koleksiyon</strong> seçin veya <strong>Arama</strong> yapın.
      </p>
    </div>
  `;
}

function _updateNetworkBackButton(container) {
  let backBtn = document.getElementById('network-back-btn');
  if (window.networkFocusBookHash) {
    if (!backBtn) {
      backBtn = document.createElement('button');
      backBtn.id = 'network-back-btn';
      backBtn.className = 'btn-secondary';
      backBtn.style.position = 'absolute';
      backBtn.style.top = '1rem';
      backBtn.style.left = '1rem';
      backBtn.style.zIndex = '1000';
      backBtn.style.padding = '0.5rem 1rem';
      backBtn.style.fontSize = '0.85rem';
      backBtn.style.borderRadius = '6px';
      backBtn.style.backgroundColor = 'var(--bg-card)';
      backBtn.style.color = 'var(--text-light)';
      backBtn.style.border = '1px solid var(--accent)';
      backBtn.style.cursor = 'pointer';
      backBtn.style.display = 'flex';
      backBtn.style.alignItems = 'center';
      backBtn.style.gap = '0.4rem';
      backBtn.style.transition = 'all 0.2s';
      backBtn.innerHTML = `<i class="fas fa-arrow-left"></i> Geri Dön`;
      backBtn.onclick = () => {
        window.networkFocusBookHash = null;
        initNetwork(typeof getFiltered === 'function' ? getFiltered() : window.allBooks);
      };
      container.parentElement.style.position = 'relative';
      container.parentElement.appendChild(backBtn);
    } else {
      backBtn.style.display = 'flex';
    }
  } else if (backBtn) {
    backBtn.style.display = 'none';
  }
}

function _getBooksToDraw(allBooksList) {
  if (!window.networkFocusBookHash) {
    return [...allBooksList];
  }
  const centerBook = (window.allBooks || []).find(b => b.hash === window.networkFocusBookHash);
  if (!centerBook) {
    return [...allBooksList];
  }
  const centerKeywords = centerBook.keywords 
    ? centerBook.keywords.split(',').map(k => k.trim()).filter(Boolean) 
    : [];

  const relatedBooks = (window.allBooks || []).filter(b => {
    if (b.hash === centerBook.hash || !b.keywords) return false;
    const bKeywords = b.keywords.split(',').map(k => k.trim()).filter(Boolean);
    return bKeywords.some(k => centerKeywords.includes(k));
  });

  return [centerBook, ...relatedBooks];
}

function _buildGraphNodesAndEdges(booksToDraw) {
  const nodes = [];
  const edges = [];
  const keywords = new Map();
  const pendingEdges = [];

  // Book Nodes
  booksToDraw.forEach(b => {
    const isCenter = window.networkFocusBookHash && b.hash === window.networkFocusBookHash;
    nodes.push({
      id: b.hash,
      label: b.title,
      shape: 'box',
      font: { face: 'Instrument Serif', size: isCenter ? 18 : 14, color: '#f5f0e8', multi: true },
      color: {
        background: isCenter ? '#b5451b' : '#1a1008',
        border: isCenter ? '#ff7b54' : '#b5451b',
        highlight: { background: '#b5451b', border: '#1a1008' }
      },
      shapeProperties: { borderRadius: 8 },
      shadow: { enabled: true, color: 'rgba(0,0,0,0.4)', size: 10 },
      size: isCenter ? 30 : 20
    });

    if (b.keywords) {
      b.keywords.split(',').forEach(m => {
        const kv = m.trim();
        if (kv) {
          keywords.set(kv, (keywords.get(kv) || 0) + 1);
          pendingEdges.push({ from: b.hash, to: kv });
        }
      });
    }
  });

  // Concept Nodes
  let topKeywords = [];
  if (window.networkFocusBookHash) {
    const centerBook = (window.allBooks || []).find(b => b.hash === window.networkFocusBookHash);
    if (centerBook?.keywords) {
      topKeywords = centerBook.keywords.split(',').map(k => k.trim()).filter(Boolean);
    }
  } else {
    topKeywords = Array.from(keywords.entries())
      .sort((a, b) => b[1] - a[1])
      .map(([m]) => m);
  }

  topKeywords.forEach(m => {
    const count = keywords.get(m) || 1;
    nodes.push({
      id: m,
      label: m,
      shape: 'dot',
      size: 18 + count * 2,
      font: { face: 'Geist', size: 13, background: 'rgba(250, 248, 244, 0.9)', color: '#292825' },
      color: {
        background: '#b5451b',
        border: '#1a1008',
        highlight: { background: '#ff7b54', border: '#1a1008' }
      }
    });
  });

  pendingEdges.filter(e => topKeywords.includes(e.to)).forEach(e => edges.push(e));
  return { nodes, edges };
}

function _attachNetworkEventHandlers(network, allBooksList) {
  // Freeze physics 1 second after map opens to stop jittering
  network.on("stabilizationIterationsDone", function () {
    setTimeout(() => {
      if (window.network) {
        window.network.setOptions({ physics: false });
      }
    }, 1000);
  });

  network.on("click", function (params) {
    if (!params.nodes || params.nodes.length === 0) return;
    const nodeId = params.nodes[0];
    const book = (window.allBooks || []).find(b => b.hash === nodeId);
    if (book) {
      if (window.networkFocusBookHash === book.hash) {
        if (typeof openModal === 'function') openModal(book);
      } else {
        window.networkFocusBookHash = book.hash;
        initNetwork(allBooksList);
        setTimeout(() => {
          if (window.network) {
            window.network.focus(book.hash, {
              scale: 1.1,
              animation: {
                duration: 1000,
                easingFunction: "easeInOutQuad"
              }
            });
          }
        }, 200);
      }
    } else if (typeof showKeywordBooks === "function") {
      // Key concept node clicked
      showKeywordBooks(nodeId);
      // Remove selection highlight to prevent map shifting/snapping
      setTimeout(() => {
        window.network?.unselectAll();
      }, 50);
    }
  });
}

function initNetwork(books) {
  const allBooksList = books || window.allBooks || [];
  const container = document.getElementById('network-view');
  if (!container) return;

  const visLib = typeof vis !== 'undefined' ? vis : window.vis;
  if (!visLib) return;

  // HEDEF 1: Hiyerarşik Filtreleme (Drill-down)
  const hasCategoryFilter = (window.activeCategory || 'all') !== 'all';
  const hasCollectionFilter = (window.activeCollection || 'all') !== 'all';
  const q = document.getElementById('search-input')?.value?.trim();
  const hasSearchFilter = q && q.length > 0;

  // Eğer hiçbir filtre aktif değilse ve Ego-Network odaklı kitap yoksa uyar
  if (!hasCategoryFilter && !hasCollectionFilter && !hasSearchFilter && !window.networkFocusBookHash) {
    _renderNetworkPlaceholder(container);
    return;
  }

  // Container içeriğini temizleyelim (varsa placeholder gitsin)
  const placeholder = container.querySelector('.network-placeholder');
  if (placeholder) {
    container.innerHTML = '';
  }

  // Geri Dön Butonu
  _updateNetworkBackButton(container);

  // HEDEF 2: Ego-Network Filtreleme
  const booksToDraw = _getBooksToDraw(allBooksList);
  const { nodes, edges } = _buildGraphNodesAndEdges(booksToDraw);

  const data = { nodes: new visLib.DataSet(nodes), edges: new visLib.DataSet(edges) };
  const options = {
    nodes: { borderWidth: 2, margin: 8 },
    edges: {
      color: { color: 'rgba(139,111,71,0.4)', highlight: '#b5451b', hover: '#b5451b' },
      width: 1,
      smooth: { enabled: true, type: 'continuous', roundness: 0.3 }
    },
    layout: {
      hierarchical: false
    },
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: -100,
        centralGravity: 0.02,
        springLength: 150,
        springConstant: 0.05,
        avoidOverlap: 1
      },
      stabilization: {
        enabled: true,
        iterations: 1000,
        fit: true
      }
    },
    interaction: { hover: true, tooltipDelay: 200 }
  };

  window.network = new visLib.Network(container, data, options);
  _attachNetworkEventHandlers(window.network, allBooksList);
}
