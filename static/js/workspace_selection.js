/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_selection.js — PDF.js Geometric Selection Engine & Floating Action Bar
 * ════════════════════════════════════════════════════════════════════════════════ */

    function invalidatePageGeometry(pageNum) {
      if (pageNum) {
        pageGeometryCache.delete(Number(pageNum));
      } else {
        pageGeometryCache.clear();
      }
    }

    function extractSpanInfos(spans, pageRect) {
      const spanInfos = [];
      for (const s of spans) {
        if (!s.textContent?.trim()) continue;
        const r = s.getBoundingClientRect();
        if (r.width === 0 && r.height === 0) continue;

        const textNode = s.firstChild || s;
        spanInfos.push({
          element: s,
          textNode: textNode,
          text: s.textContent,
          top: r.top - pageRect.top,
          bottom: r.bottom - pageRect.top,
          left: r.left - pageRect.left,
          right: r.right - pageRect.left,
          width: r.width,
          height: r.height,
          centerY: (r.top + r.bottom) / 2 - pageRect.top
        });
      }
      return spanInfos;
    }

    function groupSpansIntoLines(spanInfos) {
      const lines = [];
      let currentLine = null;

      for (const s of spanInfos) {
        if (!currentLine) {
          currentLine = {
            top: s.top,
            bottom: s.bottom,
            left: s.left,
            right: s.right,
            centerY: s.centerY,
            spans: [s]
          };
          lines.push(currentLine);
        } else {
          const verticalMatch =
            Math.abs(s.centerY - currentLine.centerY) <= 8 ||
            (s.top < currentLine.bottom - 2 && s.bottom > currentLine.top + 2);

          if (verticalMatch) {
            currentLine.spans.push(s);
            currentLine.top = Math.min(currentLine.top, s.top);
            currentLine.bottom = Math.max(currentLine.bottom, s.bottom);
            currentLine.left = Math.min(currentLine.left, s.left);
            currentLine.right = Math.max(currentLine.right, s.right);
            currentLine.centerY = (currentLine.top + currentLine.bottom) / 2;
          } else {
            currentLine = {
              top: s.top,
              bottom: s.bottom,
              left: s.left,
              right: s.right,
              centerY: s.centerY,
              spans: [s]
            };
            lines.push(currentLine);
          }
        }
      }

      for (const line of lines) {
        line.spans.sort((a, b) => a.left - b.left);
        line.firstSpan = line.spans[0];
        line.lastSpan = line.spans.at(-1);
        line.height = line.bottom - line.top;
      }
      return lines;
    }

    function getOrComputePageGeometry(textLayer) {
      if (!textLayer) return null;
      const pageWrapper = textLayer.closest('.pdf-page-wrapper');
      const pageNum = pageWrapper ? Number(pageWrapper.id.replace('pdf-page-wrapper-', '')) : null;

      if (pageNum && pageGeometryCache.has(pageNum)) {
        return pageGeometryCache.get(pageNum);
      }

      const spans = Array.from(textLayer.querySelectorAll('span'));
      if (spans.length === 0) return null;

      const pageRect = textLayer.getBoundingClientRect();
      if (!pageRect.width || !pageRect.height) return null;

      const spanInfos = extractSpanInfos(spans, pageRect);
      if (spanInfos.length === 0) return null;

      spanInfos.sort((a, b) => {
        if (Math.abs(a.centerY - b.centerY) > 6) {
          return a.centerY - b.centerY;
        }
        return a.left - b.left;
      });

      const lines = groupSpansIntoLines(spanInfos);
      const geometry = {
        pageNum: pageNum,
        pageWidth: pageRect.width,
        pageHeight: pageRect.height,
        lines: lines
      };

      if (pageNum) {
        pageGeometryCache.set(pageNum, geometry);
      }

      return geometry;
    }

    function getSafeTextNode(spanInfo) {
      let node = spanInfo.textNode;
      if (node.nodeType !== Node.TEXT_NODE) {
        node = node.firstChild || node;
      }
      return node;
    }

    function getNodeLength(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        return node.nodeValue ? node.nodeValue.length : 0;
      }
      return node.textContent ? node.textContent.length : 0;
    }

    function findBestLineForY(lines, pageY) {
      if (pageY < lines[0].top) return { bestLine: lines[0], bestLineIdx: 0 };
      if (pageY > lines.at(-1).bottom) return { bestLine: lines.at(-1), bestLineIdx: lines.length - 1 };

      for (let i = 0; i < lines.length; i++) {
        const cur = lines[i];
        const prev = i > 0 ? lines[i - 1] : null;
        const next = i < lines.length - 1 ? lines[i + 1] : null;

        const topBoundary = prev ? (prev.bottom + cur.top) / 2 : cur.top - 30;
        const bottomBoundary = next ? (cur.bottom + next.top) / 2 : cur.bottom + 30;

        if (pageY >= topBoundary && pageY <= bottomBoundary) {
          return { bestLine: cur, bestLineIdx: i };
        }
      }

      return { bestLine: lines.at(-1), bestLineIdx: lines.length - 1 };
    }

    function findCaretByPoint(clientX, clampedClientY, textLayer, bestLineIdx) {
      if (document.caretPositionFromPoint) {
        const pos = document.caretPositionFromPoint(clientX, clampedClientY);
        if (pos?.offsetNode && textLayer.contains(pos.offsetNode)) {
          return {
            node: pos.offsetNode,
            offset: pos.offset,
            lineIdx: bestLineIdx
          };
        }
      } else {
        const legacyFnName = 'caretRange' + 'FromPoint';
        const getLegacyRange = document[legacyFnName];
        if (typeof getLegacyRange === 'function') {
          const range = getLegacyRange.call(document, clientX, clampedClientY);
          if (range?.startContainer && textLayer.contains(range.startContainer)) {
            return {
              node: range.startContainer,
              offset: range.startOffset,
              lineIdx: bestLineIdx
            };
          }
        }
      }
      return null;
    }

    function findCaretBySpanInterpolation(bestLine, pageX, bestLineIdx) {
      let closestSpan = bestLine.spans[0];
      let minDistance = Infinity;
      for (const s of bestLine.spans) {
        if (pageX >= s.left && pageX <= s.right) {
          closestSpan = s;
          break;
        }
        const dist = Math.min(Math.abs(pageX - s.left), Math.abs(pageX - s.right));
        if (dist < minDistance) {
          minDistance = dist;
          closestSpan = s;
        }
      }

      const node = getSafeTextNode(closestSpan);
      const textLen = getNodeLength(node);
      const ratio = Math.max(0, Math.min(1, (pageX - closestSpan.left) / (closestSpan.width || 1)));
      const charOffset = Math.round(ratio * textLen);

      return {
        node: node,
        offset: Math.max(0, Math.min(textLen, charOffset)),
        lineIdx: bestLineIdx
      };
    }

    function findCaretPositionInPage(textLayer, geometry, clientX, clientY) {
      if (!geometry?.lines?.length) return null;
      const pageRect = textLayer.getBoundingClientRect();
      const pageX = clientX - pageRect.left;
      const pageY = clientY - pageRect.top;

      const { bestLine, bestLineIdx } = findBestLineForY(geometry.lines, pageY);

      if (pageX <= bestLine.left + 6) {
        const node = getSafeTextNode(bestLine.firstSpan);
        return {
          node: node,
          offset: 0,
          lineIdx: bestLineIdx,
          isStartOfLine: true
        };
      }

      if (pageX >= bestLine.right - 6) {
        const node = getSafeTextNode(bestLine.lastSpan);
        return {
          node: node,
          offset: getNodeLength(node),
          lineIdx: bestLineIdx,
          isEndOfLine: true
        };
      }

      const clampedClientY = pageRect.top + bestLine.centerY;
      const browserCaret = findCaretByPoint(clientX, clampedClientY, textLayer, bestLineIdx);
      if (browserCaret) return browserCaret;

      return findCaretBySpanInterpolation(bestLine, pageX, bestLineIdx);
    }

    function findPageWrapperAtPoint(clientX, clientY) {
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return null;

      const elements = document.elementsFromPoint(clientX, clientY);
      for (const el of elements) {
        const wrapper = el.closest('.pdf-page-wrapper');
        if (wrapper) return wrapper;
      }

      // If clicked in margin outside the page wrapper horizontally, match by vertical range
      const wrappers = Array.from(container.querySelectorAll('.pdf-page-wrapper'));
      for (const w of wrappers) {
        const r = w.getBoundingClientRect();
        if (clientY >= r.top && clientY <= r.bottom) {
          return w;
        }
      }

      return null;
    }

    function registerTextLayerForSelection(textLayerDiv, endDiv) {
      if (!textLayerDiv || !endDiv) return;
      activeTextLayersMap.set(textLayerDiv, endDiv);
      enableGlobalSelectionListener();
    }

    function unregisterTextLayerForSelection(textLayerDiv) {
      if (!textLayerDiv) return;
      const endDiv = activeTextLayersMap.get(textLayerDiv);
      if (endDiv && endDiv.parentElement === textLayerDiv) {
        endDiv.remove();
      }
      activeTextLayersMap.delete(textLayerDiv);
      if (activeTextLayersMap.size === 0) {
        if (selectionChangeAbortController) {
          try { selectionChangeAbortController.abort(); } catch (_) {}
          selectionChangeAbortController = null;
        }
        prevSelectionRange = null;
      }
    }

    function resetAllEndOfContent() {
      activeTextLayersMap.forEach((end, textLayer) => {
        if (textLayer?.contains(end)) {
          textLayer.append(end);
          end.style.width = "";
          end.style.height = "";
          end.style.top = "";
        }
        if (end) end.classList.remove("active");
      });
      prevSelectionRange = null;
    }

    function getActiveTextLayersFromSelection(selection, activeLayers) {
      const activeTextLayers = new Set();
      for (let i = 0; i < selection.rangeCount; i++) {
        const range = selection.getRangeAt(i);
        for (const textLayerDiv of activeLayers.keys()) {
          if (!activeTextLayers.has(textLayerDiv) && range.intersectsNode(textLayerDiv)) {
            activeTextLayers.add(textLayerDiv);
          }
        }
      }
      return activeTextLayers;
    }

    function updateEndOfContentLayer(textLayerDiv, endDiv, isActive) {
      if (isActive) {
        endDiv.classList.add("active");
      } else {
        if (textLayerDiv.contains(endDiv)) {
          textLayerDiv.append(endDiv);
          endDiv.style.width = "";
          endDiv.style.height = "";
          endDiv.style.top = "";
        }
        endDiv.classList.remove("active");
      }
    }

    function enableGlobalSelectionListener() {
      if (selectionChangeAbortController) return;
      selectionChangeAbortController = new AbortController();
      const signal = selectionChangeAbortController.signal;

      // Pointer down: initiate smart geometric selection ONLY for mouse/pen margin drags
      // (Touch events pass through untouched for 60fps native touch scrolling, pinch & tap-to-toggle;
      // direct span clicks pass through for native double-click word & triple-click paragraph selection!)
      document.addEventListener("pointerdown", (evt) => {
        if (evt.pointerType === 'touch') return;
        if (evt.button !== 0 && evt.button !== undefined) return;
        if (isDocReaderMode) return;

        // Ignore clicks on floating UI widgets
        if (evt.target.closest('#pdf-floating-bar') ||
            evt.target.closest('#pdf-search-bar') ||
            evt.target.closest('.pdf-note-modal') ||
            evt.target.closest('.sticky-note-marker')) {
          return;
        }

        const container = document.getElementById('pdf-canvas-container');
        if (!container?.contains(evt.target)) {
          return;
        }

        // Allow native double/triple-click word/paragraph selection and direct span selection
        if (evt.detail > 1 || evt.target.closest('.textLayer span') || evt.target.closest('.doc-reader-sheet')) {
          return;
        }

        let pageWrapper = evt.target.closest('.pdf-page-wrapper');
        if (!pageWrapper) {
          pageWrapper = findPageWrapperAtPoint(evt.clientX, evt.clientY);
        }
        if (!pageWrapper) {
          clearSelection();
          return;
        }

        const textLayer = pageWrapper.querySelector('.textLayer');
        if (!textLayer) return;

        const geometry = getOrComputePageGeometry(textLayer);
        if (!geometry) return;

        const hit = findCaretPositionInPage(textLayer, geometry, evt.clientX, evt.clientY);
        if (!hit?.node) return;

        // Margin/whitespace click: anchor cleanly at nearest line edge without full-page selection bleed
        evt.preventDefault();

        selectionDragState = {
          startX: evt.clientX,
          startY: evt.clientY,
          anchorNode: hit.node,
          anchorOffset: hit.offset,
          anchorTextLayer: textLayer,
          anchorPageWrapper: pageWrapper,
          anchorLineIdx: hit.lineIdx,
          isDragging: false,
          isMarginStart: true
        };

        const sel = window.getSelection();
        try {
          sel.collapse(hit.node, hit.offset);
        } catch (_) {}
      }, { signal });

      // Pointer move: update selection with geometric clamping for margin-initiated drags
      document.addEventListener("pointermove", (evt) => {
        if (!selectionDragState) return;

        const dx = evt.clientX - selectionDragState.startX;
        const dy = evt.clientY - selectionDragState.startY;
        const dist = Math.hypot(dx, dy);

        if (!selectionDragState.isDragging && dist < 4) {
          return;
        }

        selectionDragState.isDragging = true;
        isUserSelectingText = true;

        const pageWrapper = findPageWrapperAtPoint(evt.clientX, evt.clientY) || selectionDragState.anchorPageWrapper;
        if (!pageWrapper) return;

        const textLayer = pageWrapper.querySelector('.textLayer');
        if (!textLayer) return;

        const geometry = getOrComputePageGeometry(textLayer);
        if (!geometry) return;

        const hit = findCaretPositionInPage(textLayer, geometry, evt.clientX, evt.clientY);
        if (!hit?.node) return;

        const sel = window.getSelection();
        try {
          sel.setBaseAndExtent(
            selectionDragState.anchorNode,
            selectionDragState.anchorOffset,
            hit.node,
            hit.offset
          );
        } catch (_) {}
      }, { signal });

      // Pointer up: complete selection and position floating action bar
      document.addEventListener("pointerup", () => {
        if (selectionDragState) {
          if (selectionDragState.isDragging) {
            handleTextSelection();
          } else {
            clearSelection();
          }
          selectionDragState = null;
        }
        isUserSelectingText = false;
        resetAllEndOfContent();
      }, { signal });

      document.addEventListener("mouseup", () => {
        isUserSelectingText = false;
        resetAllEndOfContent();
      }, { signal });

      // selectionchange: Mozilla PDF.js endOfContent stabilizer for native span/word/touch selection
      document.addEventListener("selectionchange", () => {
        if (selectionDragState?.isDragging) {
          return;
        }

        const selection = document.getSelection();
        if (!selection || selection.rangeCount === 0) {
          resetAllEndOfContent();
          return;
        }

        const activeTextLayers = getActiveTextLayersFromSelection(selection, activeTextLayersMap);

        for (const [textLayerDiv, endDiv] of activeTextLayersMap) {
          updateEndOfContentLayer(textLayerDiv, endDiv, activeTextLayers.has(textLayerDiv));
        }
      }, { signal });
    }

    function getPageWrapperFromRange(range) {
      const startNode = range.commonAncestorContainer;
      let pageWrapper = startNode.nodeType === Node.TEXT_NODE ? 
                          startNode.parentNode.closest('.pdf-page-wrapper') : 
                          startNode.closest('.pdf-page-wrapper');
      if (!pageWrapper) {
        const sc = range.startContainer;
        pageWrapper = sc.nodeType === Node.TEXT_NODE ? sc.parentNode.closest('.pdf-page-wrapper') : sc.closest('.pdf-page-wrapper');
      }
      return pageWrapper;
    }

    function updateFloatingBarPosition(range, text, pageWrapper) {
      const pageNum = Number.parseInt(pageWrapper.dataset.pageNum || pageWrapper.dataset.pageNumber || pageWrapper.id.replace('pdf-page-wrapper-', ''), 10);
      if (!Number.isNaN(pageNum) && pageNum >= 1) {
        pdfPageNum = pageNum;
      }

      const viewerEl = document.getElementById('custom-pdf-viewer');
      const floatingBar = document.getElementById('pdf-floating-bar');
      if (!viewerEl || !floatingBar) return;

      const rect = range.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return;
      const viewerRect = viewerEl.getBoundingClientRect();

      floatingBar.classList.add('active');
      const barWidth = floatingBar.offsetWidth || 280;
      const barHeight = floatingBar.offsetHeight || 42;

      const desiredLeft = rect.left - viewerRect.left + (rect.width / 2) - (barWidth / 2);
      let desiredTop = rect.top - viewerRect.top - barHeight - 10;
      // Flip below selection if near top edge of viewer
      if (desiredTop < 12) {
        desiredTop = Math.min(viewerRect.height - barHeight - 12, rect.bottom - viewerRect.top + 10);
      }

      floatingBar.style.left = Math.max(10, Math.min(desiredLeft, Math.max(10, viewerRect.width - barWidth - 10))) + 'px';
      floatingBar.style.top = Math.max(10, desiredTop) + 'px';

      pdfSelectedText = text;
      pdfSelectionRanges = getSelectionCoordsRelativeToPage(range, pageWrapper);
    }

    // Handle Text Selection for highlights & floating bar positioning (deduplicated)
    function handleTextSelection() {
      if (selectionCheckTimer) clearTimeout(selectionCheckTimer);
      selectionCheckTimer = setTimeout(() => {
        selectionCheckTimer = null;
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) {
          hideFloatingBar();
          return;
        }
        const text = selection.toString().trim();
        if (text.length === 0) {
          hideFloatingBar();
          return;
        }

        const range = selection.getRangeAt(0);
        const container = document.getElementById('pdf-canvas-container');
        if (!container?.contains(range.commonAncestorContainer)) {
          hideFloatingBar();
          return;
        }

        const pageWrapper = getPageWrapperFromRange(range);
        if (!pageWrapper) {
          hideFloatingBar();
          return;
        }

        updateFloatingBarPosition(range, text, pageWrapper);
      }, 45);
    }

    // Hide float tooltip
    function hideFloatingBar() {
      const bar = document.getElementById('pdf-floating-bar');
      if (bar) bar.classList.remove('active');
    }

    function clearSelection() {
      window.getSelection()?.removeAllRanges();
      hideFloatingBar();
    }

    function copySelectedReaderText() {
      const text = pdfSelectedText || window.getSelection()?.toString()?.trim() || '';
      if (!text) return;
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(text)
          .then(() => {
            if (typeof showToast === 'function') showToast('Seçili metin kopyalandı.', 'success', 1800);
          })
          .catch(() => {
            if (typeof showToast === 'function') showToast('Metin kopyalanamadı.', 'error');
          });
      }
      clearSelection();
    }
    window.copySelectedReaderText = copySelectedReaderText;

    function askAIAboutSelection() {
      const text = (pdfSelectedText || window.getSelection()?.toString()?.trim() || '').slice(0, 1200);
      if (!text) return;
      const pageRef = pdfPageNum || 1;
      clearSelection();

      const chatPane = document.getElementById('workspace-chat-pane');
      if (chatPane && chatPane.classList.contains('collapsed')) {
        toggleWorkspaceChatPane();
      }
      const input = document.getElementById('workspace-chat-input');
      if (input) {
        input.value = `[Sayfa ${pageRef}] şu pasajı açıklar mısın:\n"${text}"`;
        input.style.height = 'auto';
        input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
        input.focus({ preventScroll: true });
      }
    }
    window.askAIAboutSelection = askAIAboutSelection;

    function collectTextNodesFromRange(range, root) {
      const textNodes = [];
      try {
        const treeWalker = document.createTreeWalker(
          root,
          NodeFilter.SHOW_TEXT,
          {
            acceptNode: function(node) {
              if (range.intersectsNode(node)) return NodeFilter.FILTER_ACCEPT;
              return NodeFilter.FILTER_REJECT;
            }
          }
        );
        let currentNode = treeWalker.currentNode;
        while (currentNode) {
          if (currentNode.nodeType === Node.TEXT_NODE && range.intersectsNode(currentNode) && currentNode.textContent.trim().length > 0) {
            textNodes.push(currentNode);
          }
          currentNode = treeWalker.nextNode();
        }
      } catch (err) {
        console.warn("TreeWalker coordinate traversal failed:", err);
      }
      return textNodes;
    }

    function extractNodeLineRects(node, range) {
      const textContent = node.textContent || '';
      let start = (node === range.startContainer) ? range.startOffset : 0;
      let end = (node === range.endContainer) ? range.endOffset : textContent.length;

      while (start < end && /\s/.test(textContent.charAt(start))) start++;
      while (end > start && /\s/.test(textContent.charAt(end - 1))) end--;
      if (start >= end) return [];

      const rects = [];
      try {
        const subRange = document.createRange();
        subRange.setStart(node, start);
        subRange.setEnd(node, end);
        const clientRects = subRange.getClientRects();
        for (let i = 0; i < clientRects.length; i++) {
          const r = clientRects[i];
          if (r.width > 0.5 && r.height > 0.5) {
            rects.push({
              left: r.left,
              right: r.right,
              top: r.top,
              bottom: r.bottom,
              width: r.width,
              height: r.height
            });
          }
        }
      } catch (_) {}
      return rects;
    }

    function groupCharRectsIntoLines(charRects) {
      const lines = [];
      charRects.forEach(rect => {
        const centerY = rect.top + rect.height / 2;
        let added = false;
        for (const line of lines) {
          const lineCenterY = line.top + line.height / 2;
          if (Math.abs(centerY - lineCenterY) < Math.max(8, rect.height * 0.6)) {
            line.left = Math.min(line.left, rect.left);
            line.right = Math.max(line.right, rect.right);
            line.top = Math.min(line.top, rect.top);
            line.bottom = Math.max(line.bottom, rect.bottom);
            line.height = line.bottom - line.top;
            added = true;
            break;
          }
        }
        if (!added) {
          lines.push({
            left: rect.left,
            right: rect.right,
            top: rect.top,
            bottom: rect.bottom,
            height: rect.height
          });
        }
      });
      return lines;
    }

    // Fast O(spans) coordinates relative to page wrapper bounding box (zero per-character layout thrash)
    function getSelectionCoordsRelativeToPage(range, pageWrapperOverride = null) {
      const pageWrapper = pageWrapperOverride || getPageWrapperFromRange(range);
      if (!pageWrapper) return [];
      const wrapperRect = pageWrapper.getBoundingClientRect();
      if (wrapperRect.width <= 0 || wrapperRect.height <= 0) return [];

      const textNodes = collectTextNodesFromRange(range, pageWrapper);
      const rawRects = [];
      for (let i = 0; i < textNodes.length; i++) {
        const nodeRects = extractNodeLineRects(textNodes[i], range);
        for (let j = 0; j < nodeRects.length; j++) {
          rawRects.push(nodeRects[j]);
        }
      }

      const mergedLines = groupCharRectsIntoLines(rawRects);
      const coords = [];
      mergedLines.forEach(line => {
        const w = line.right - line.left;
        if (w < 1.5 || line.height < 1.5) return;
        coords.push({
          left: Math.max(0, (line.left - wrapperRect.left) / wrapperRect.width),
          top: Math.max(0, (line.top - wrapperRect.top) / wrapperRect.height),
          width: Math.min(1, w / wrapperRect.width),
          height: Math.min(1, line.height / wrapperRect.height)
        });
      });

      if (coords.length === 0) {
        const rects = range.getClientRects();
        for (const r of rects) {
          if (r.width < 1.5 || r.height < 1.5) continue;
          if (r.bottom < wrapperRect.top || r.top > wrapperRect.bottom) continue;
          coords.push({
            left: Math.max(0, (r.left - wrapperRect.left) / wrapperRect.width),
            top: Math.max(0, (r.top - wrapperRect.top) / wrapperRect.height),
            width: Math.min(1, r.width / wrapperRect.width),
            height: Math.min(1, r.height / wrapperRect.height)
          });
        }
      }
      return coords;
    }


    window.clearSelection = clearSelection;
    window.hideFloatingBar = hideFloatingBar;
