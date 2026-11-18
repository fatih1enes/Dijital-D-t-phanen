/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_search.js — Turkish-Aware Cross-Span In-Document Search Engine (Ctrl+F)
 * ════════════════════════════════════════════════════════════════════════════════ */

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

    window.togglePdfSearch = togglePdfSearch;
    window.closePdfSearch = closePdfSearch;
    window.clearPdfSearch = clearPdfSearch;
    window.pdfSearchNext = pdfSearchNext;
    window.pdfSearchPrev = pdfSearchPrev;
    window.onPdfSearchInput = onPdfSearchInput;
    window.onPdfSearchKeydown = onPdfSearchKeydown;
    window.togglePdfSearchResultsDrawer = togglePdfSearchResultsDrawer;
    window.jumpToSearchResult = jumpToSearchResult;

