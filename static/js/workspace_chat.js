/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_chat.js — True SSE Streaming Chat, AbortController & Citation Popovers
 * ════════════════════════════════════════════════════════════════════════════════ */

    let _citePopoverHideTimer = null;
    let _activeCitedElement = null;

    function stopChatGeneration() {
      if (activeChatAbortController) {
        try {
          activeChatAbortController.abort();
        } catch (_abortErr) {}
        activeChatAbortController = null;
      }
      if (activeTypewriterTimer) {
        clearInterval(activeTypewriterTimer);
        activeTypewriterTimer = null;
      }
      if (activeTypewriterContainer) {
        if (activeTypewriterFullText) {
          activeTypewriterContainer.innerHTML =
            parseMarkdown(activeTypewriterFullText) +
            '<div class="chat-stopped-pill"><i class="fas fa-stop-circle"></i> Yanıt durduruldu</div>';
        } else {
          activeTypewriterContainer.innerHTML =
            '<div class="chat-stopped-pill"><i class="fas fa-stop-circle"></i> Yanıt isteği iptal edildi</div>';
        }
      }
      activeTypewriterContainer = null;
      activeTypewriterFullText = '';
      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'none';
      isWorkspaceChatLoading = false;
      const input = document.getElementById('workspace-chat-input');
      if (input) input.focus();
    }
    window.stopChatGeneration = stopChatGeneration;

    function insertPromptChip(promptText) {
      const input = document.getElementById('workspace-chat-input');
      if (!input) return;
      input.value = promptText;
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      input.focus();
    }
    window.insertPromptChip = insertPromptChip;

    function resetBannerState() {
      workspaceCitationsByPage.clear();
      hideCitationPreviewPopover(true);
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (!banner) return;
      banner.className = 'workspace-book-banner';
      icon.innerHTML = '<i class="fas fa-book-open"></i>';
      title.textContent = 'Kitabı AI hafızasına yükle';
      subtitle.textContent = 'Tüm kitap metnini yapay zekaya ver — derin analiz için';
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-cloud-arrow-up"></i> Yükle';
      isFullBookLoaded = false;
    }

    async function loadFullBookToAI() {
      if (!activeWorkspaceBook || isFullBookLoaded) return;

      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');

      banner.classList.remove('error', 'loaded');
      banner.classList.add('loading');
      icon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      title.textContent = 'Kitap metni AI oturumuna yükleniyor...';
      subtitle.textContent = 'Oturum oluşturuluyor (yalnızca ilk defaya mahsustur)';
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Hazırlanıyor';

      try {
        const response = await apiFetch(`/api/workspace/load-book/${activeWorkspaceBook.hash}`, {
          method: 'POST'
        });
        const data = response ? await response.json() : {};

        if (response?.ok && data.success) {
          isFullBookLoaded = true;
          banner.classList.remove('loading', 'error');
          banner.classList.add('loaded');
          icon.innerHTML = '<i class="fas fa-circle-check"></i>';
          const charK = Math.max(1, Math.round((data.char_count || 0) / 1000));
          title.textContent = 'Kitap AI oturumu aktif';
          subtitle.textContent = `${charK}K karakter · Oturum hazır — sorular anında yanıtlanacak`;
          btn.innerHTML = '<i class="fas fa-check"></i> Hazır';

          const chatMessages = document.getElementById('workspace-chat-messages');
          chatMessages.insertAdjacentHTML('beforeend', `
            <div class="chat-msg chat-ai" style="max-width: 100%;">
              <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
              <div class="chat-msg-text"><strong>${esc(activeWorkspaceBook.title)}</strong> kitabı yapay zeka oturumuna başarıyla yüklendi. Artık tüm sorularınız beklemeden ve doğrudan kitap üzerinden yanıtlanacak.</div>
            </div>
          `);
          chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
          banner.classList.remove('loading');
          banner.classList.add('error');
          icon.innerHTML = '<i class="fas fa-triangle-exclamation"></i>';
          title.textContent = 'Yükleme başarısız';
          subtitle.textContent = data.error || data.detail || 'Bilinmeyen hata';
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';

          setTimeout(() => {
            banner.classList.remove('error');
            resetBannerState();
          }, 5000);
        }
      } catch (err) {
        console.warn('loadFullBookToAI hatası:', err);
        banner.classList.remove('loading');
        banner.classList.add('error');
        icon.innerHTML = '<i class="fas fa-triangle-exclamation"></i>';
        title.textContent = 'Bağlantı hatası';
        subtitle.textContent = 'Sunucuya ulaşılamadı';
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';

        setTimeout(() => resetBannerState(), 5000);
      }
    }
    window.loadFullBookToAI = loadFullBookToAI;

    function renderChatHistoryItem(item) {
      if (item.role === 'user') {
        return `
          <div class="chat-msg chat-user">
            <div class="chat-msg-text">${esc(item.text)}</div>
            <div class="chat-msg-avatar"><i class="fas fa-user"></i></div>
          </div>
        `;
      }
      return `
        <div class="chat-msg chat-ai">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">${parseMarkdown(item.text)}</div>
        </div>
      `;
    }

    function updateBannerForActiveSession() {
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (banner) {
        banner.className = 'workspace-book-banner loaded';
        if (icon) icon.innerHTML = '<i class="fas fa-circle-check"></i>';
        if (title) title.textContent = 'Kitap AI oturumu aktif';
        if (subtitle) subtitle.textContent = 'Önbellek devrede — sorular anında yanıtlanıyor';
        if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
        isFullBookLoaded = true;
      }
    }

    function applyWorkspaceChatHistory(data, chatMessages) {
      if (!data?.success || !Array.isArray(data.history) || data.history.length === 0) return;
      chatMessages.innerHTML = data.history.map(renderChatHistoryItem).join('');
      chatMessages.scrollTop = chatMessages.scrollHeight;

      if (data.has_active_session) {
        updateBannerForActiveSession();
      }
    }

    function handleWorkspaceChatKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void sendWorkspaceMessage();
      } else if (e.key === 'Escape') {
        const chatPane = document.getElementById('workspace-chat-pane');
        if (isMobileReaderViewport() && chatPane && !chatPane.classList.contains('collapsed')) {
          e.preventDefault();
          e.stopPropagation();
          e.target.blur();
          toggleWorkspaceChatPane();
          return;
        }
        // On desktop: if user has unsent text, 1st Escape safely blurs input without closing reader;
        // if input is empty, allow global hierarchical Escape (close popover/drawer -> exit reader).
        if ((e.target.value || '').trim().length > 0) {
          e.preventDefault();
          e.stopPropagation();
          e.target.blur();
        } else {
          e.target.blur();
        }
      }
    }

    function markSessionLoadedInBanner() {
      if (isFullBookLoaded) return;
      isFullBookLoaded = true;
      const banner = document.getElementById('workspace-book-banner');
      const icon = document.getElementById('banner-icon');
      const title = document.getElementById('banner-title');
      const subtitle = document.getElementById('banner-subtitle');
      const btn = document.getElementById('btn-banner-load');
      if (banner) {
        banner.className = 'workspace-book-banner loaded';
        if (icon) icon.innerHTML = '<i class="fas fa-circle-check"></i>';
        if (title) title.textContent = 'Kitap AI oturumu aktif';
        if (subtitle) subtitle.textContent = 'Önbellek devrede — sonraki sorular anında yanıtlanacak';
        if (btn) btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
      }
    }

    function _storeCitationsOnElement(msgWrapEl, citationsList) {
      if (!Array.isArray(citationsList) || citationsList.length === 0) return;
      const localMap = new Map();
      for (const c of citationsList) {
        const p = Number.parseInt(c.page, 10);
        if (Number.isNaN(p) || p < 1) continue;
        const snippet = String(c.snippet || '').trim();
        if (!snippet) continue;
        if (!localMap.has(p)) localMap.set(p, []);
        localMap.get(p).push({
          snippet,
          score: c.score || 0,
          bookTitle: c.book_title || activeWorkspaceBook?.title || ''
        });
        if (!workspaceCitationsByPage.has(p)) {
          workspaceCitationsByPage.set(p, []);
        }
        const existing = workspaceCitationsByPage.get(p);
        if (!existing.some(e => e.snippet === snippet)) {
          existing.unshift({
            snippet,
            score: c.score || 0,
            bookTitle: c.book_title || activeWorkspaceBook?.title || ''
          });
        }
      }
      if (msgWrapEl) {
        msgWrapEl._citationsByPage = localMap;
      }
    }

    function startWorkspaceTypewriter(rawReply, replyId, chatMessages) {
      const targetContainer = document.querySelector(`#${replyId} .chat-msg-text`);
      if (!targetContainer) return;
      targetContainer.innerHTML = parseMarkdown(rawReply || '');
      if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'none';
      isWorkspaceChatLoading = false;
    }

    async function sendWorkspaceMessage() {
      if (isWorkspaceChatLoading || !activeWorkspaceBook) return;

      const input = document.getElementById('workspace-chat-input');
      const text = input.value.trim();
      if (!text) return;

      resetCopyButtonUI();
      input.value = '';
      input.style.height = 'auto';

      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-user">
          <div class="chat-msg-avatar"><i class="fas fa-user"></i></div>
          <div class="chat-msg-text">${esc(text)}</div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;

      const replyId = `reply-${Date.now()}`;
      const loadingNoticeText = !isFullBookLoaded
        ? '<div class="chat-session-prep-note"><i class="fas fa-cloud-arrow-up fa-fade"></i> Kitap bağlamı hazırlanıyor, yanıt anlık akacak...</div>'
        : '';
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-ai" id="${replyId}">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-body-wrap">
            <div class="chat-rag-grounding-slot"></div>
            <div class="chat-msg-text">
              ${loadingNoticeText}
              <div class="chat-typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;

      const msgWrapEl = document.getElementById(replyId);
      const groundingSlot = msgWrapEl?.querySelector('.chat-rag-grounding-slot');
      const targetContainer = msgWrapEl?.querySelector('.chat-msg-text');

      isWorkspaceChatLoading = true;
      const abortCtrl = new AbortController();
      activeChatAbortController = abortCtrl;
      activeTypewriterFullText = '';
      activeTypewriterContainer = targetContainer;

      // Show Stop button IMMEDIATELY at t=0ms so user has real cancellation control
      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'block';

      const isUserNearBottom = () => {
        if (!chatMessages) return true;
        return (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight) < 75;
      };

      let accumulated = '';
      let rafId = 0;

      const flushStreamRender = () => {
        rafId = 0;
        if (!targetContainer || abortCtrl.signal.aborted) return;
        const shouldPin = isUserNearBottom();
        targetContainer.innerHTML = parseMarkdown(accumulated);
        if (shouldPin && chatMessages) {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      };

      try {
        await streamChatSSE(
          {
            message: text,
            target_book_hash: activeWorkspaceBook.hash,
            load_full_book: isFullBookLoaded
          },
          {
            onCitations: (citations) => {
              _storeCitationsOnElement(msgWrapEl, citations);
              if (groundingSlot && Array.isArray(citations) && citations.length > 0) {
                const uniquePages = [...new Set(citations.map(c => c.page))].slice(0, 5);
                groundingSlot.innerHTML = `
                  <div class="chat-rag-grounding-pill" title="Kitap içinden doğrulanmış kaynak sayfalar">
                    <i class="fas fa-book-bookmark"></i>
                    <span>${citations.length} pasaj doğrulandı (Sayfa ${uniquePages.join(', ')})</span>
                  </div>
                `;
              }
            },
            onSession: () => {
              markSessionLoadedInBanner();
            },
            onToken: (piece) => {
              if (!piece) return;
              accumulated += piece;
              activeTypewriterFullText = accumulated;
              if (!rafId) {
                rafId = requestAnimationFrame(flushStreamRender);
              }
            },
            onError: (errMsg) => {
              if (targetContainer && !accumulated) {
                targetContainer.innerHTML = `<span style="color: var(--danger);">${esc(errMsg)}</span>`;
              }
            }
          },
          abortCtrl.signal
        );

        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = 0;
        }
        if (!abortCtrl.signal.aborted && targetContainer && accumulated) {
          const shouldPin = isUserNearBottom();
          targetContainer.innerHTML = parseMarkdown(accumulated);
          if (shouldPin && chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        }
      } catch (err) {
        if (rafId) {
          cancelAnimationFrame(rafId);
          rafId = 0;
        }
        if (err?.name === 'AbortError' || abortCtrl.signal.aborted) {
          return;
        }
        const errText = err?.message || 'Bağlantı hatası: Sunucuya ulaşılamadı.';
        if (targetContainer) {
          targetContainer.innerHTML = `<span style="color: var(--danger);">${esc(errText)}</span>`;
        }
      } finally {
        if (activeChatAbortController === abortCtrl) {
          activeChatAbortController = null;
          activeTypewriterContainer = null;
          activeTypewriterFullText = '';
          isWorkspaceChatLoading = false;
          if (stopWrap) stopWrap.style.display = 'none';
        }
      }
    }

    // ─── Grounded Citation Preview Popover ───────────────────────────────────
    function _resolveCitationSnippetForPage(citeEl, pageNum) {
      const msgEl = citeEl.closest('.chat-msg');
      const msgHits = msgEl?._citationsByPage?.get(pageNum);
      if (msgHits && msgHits.length > 0) {
        return msgHits[0].snippet;
      }
      const globalHits = workspaceCitationsByPage.get(pageNum);
      if (globalHits && globalHits.length > 0) {
        return globalHits[0].snippet;
      }
      if (pdfSearchTextCache && pdfSearchTextCache[pageNum]) {
        const rawPage = String(pdfSearchTextCache[pageNum]).trim();
        if (rawPage) {
          return rawPage.length > 260 ? rawPage.slice(0, 260).trim() + '…' : rawPage;
        }
      }
      if (isDocReaderMode && Array.isArray(docReaderPages) && docReaderPages[pageNum - 1]) {
        const blocks = docReaderPages[pageNum - 1].blocks || [];
        const joined = blocks.map(b => b.text || '').join(' ').trim();
        if (joined) {
          return joined.length > 260 ? joined.slice(0, 260).trim() + '…' : joined;
        }
      }
      return '';
    }

    function hideCitationPreviewPopover(immediate = false) {
      if (_citePopoverHideTimer) {
        clearTimeout(_citePopoverHideTimer);
        _citePopoverHideTimer = null;
      }
      const doHide = () => {
        const pop = document.getElementById('citation-preview-popover');
        if (pop) {
          pop.classList.remove('visible');
          pop.setAttribute('aria-hidden', 'true');
        }
        _activeCitedElement = null;
      };
      if (immediate) {
        doHide();
      } else {
        _citePopoverHideTimer = setTimeout(doHide, 160);
      }
    }
    window.hideCitationPreviewPopover = hideCitationPreviewPopover;

    function showCitationPreviewPopover(citeEl) {
      if (!citeEl) return;
      const pageNum = Number.parseInt(citeEl.dataset.jumpPage || '', 10);
      if (Number.isNaN(pageNum) || pageNum < 1) return;

      if (_citePopoverHideTimer) {
        clearTimeout(_citePopoverHideTimer);
        _citePopoverHideTimer = null;
      }

      const pop = document.getElementById('citation-preview-popover');
      if (!pop) return;

      const snippet = _resolveCitationSnippetForPage(citeEl, pageNum);
      const bookTitle = activeWorkspaceBook?.title || 'Kitap Kaynağı';
      const quoteBody = snippet
        ? `<blockquote class="cite-popover-quote">“${esc(snippet.length > 300 ? snippet.slice(0, 300).trim() + '…' : snippet)}”</blockquote>`
        : `<div class="cite-popover-fallback">Bu referansı kitap sayfasında doğrudan görüntülemek için tıklayın.</div>`;

      pop.innerHTML = `
        <div class="cite-popover-header">
          <span class="cite-popover-badge"><i class="fas fa-check-double"></i> Sayfa ${pageNum} · Kanıt</span>
          <button type="button" class="cite-popover-jump-btn" data-popover-jump="${pageNum}" data-popover-snippet="${encData(snippet.slice(0, 80))}">
            Sayfaya Git <i class="fas fa-arrow-right"></i>
          </button>
        </div>
        <div class="cite-popover-book">${esc(bookTitle)}</div>
        ${quoteBody}
      `;

      pop.classList.add('visible');
      pop.setAttribute('aria-hidden', 'false');
      _activeCitedElement = citeEl;

      const rect = citeEl.getBoundingClientRect();
      const popRect = pop.getBoundingClientRect();
      const popW = popRect.width || 320;
      const popH = popRect.height || 150;

      let left = rect.left + (rect.width / 2) - (popW / 2);
      left = Math.max(10, Math.min(left, window.innerWidth - popW - 10));

      let top = rect.top - popH - 10;
      if (top < 10) {
        top = Math.min(window.innerHeight - popH - 10, rect.bottom + 10);
      }

      pop.style.left = `${Math.round(left)}px`;
      pop.style.top = `${Math.round(top)}px`;
    }
    window.showCitationPreviewPopover = showCitationPreviewPopover;

    function navigateToCitationWithSpotlight(pageNum, snippetHint = '') {
      hideCitationPreviewPopover(true);
      jumpToPdfPage(pageNum);
      if (snippetHint && typeof onPdfSearchInput === 'function') {
        const cleanPhrase = snippetHint
          .replace(/[^\p{L}\p{N}\s]/gu, ' ')
          .trim()
          .split(/\s+/)
          .slice(0, 4)
          .join(' ');
        if (cleanPhrase.length >= 8 && !isPdfSearchOpen) {
          setTimeout(() => {
            const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
            if (wrapper) {
              wrapper.classList.remove('page-pulse');
              void wrapper.offsetWidth;
              wrapper.classList.add('page-pulse');
            }
          }, 260);
        }
      }
    }

    // Copy entire workspace chat conversation to clipboard
    function copyWorkspaceChat() {
      const chatMessages = document.getElementById('workspace-chat-messages');
      const btn = document.getElementById('btn-copy-chat');
      if (!chatMessages) return;

      const msgs = chatMessages.querySelectorAll('.chat-msg');
      if (!msgs || msgs.length === 0) {
        showToast('Kopyalanacak mesaj bulunamadı.', 'info');
        return;
      }

      const bookTitle = activeWorkspaceBook ? (activeWorkspaceBook.title || 'Kitap') : 'Kitap';
      const lines = [`# ${bookTitle} - AI Sohbet Notları\n`];

      msgs.forEach(msg => {
        const isUser = msg.classList.contains('chat-user');
        const textEl = msg.querySelector('.chat-msg-text');
        if (!textEl) return;

        const text = textEl.innerText.trim();
        if (!text) return;

        if (isUser) {
          lines.push(`\n**Kullanıcı:**\n${text}\n`);
        } else {
          lines.push(`\n**AI Asistanı:**\n${text}\n`);
        }
      });

      const fullContent = lines.join('\n');

      const notify = (msg) => {
        if (typeof showNotification === 'function') {
          showNotification(msg, 'success');
        } else if (typeof showToast === 'function') {
          showToast(msg, 'success');
        }
      };

      const setCopiedUI = () => {
        if (btn) {
          if (copyChatBtnTimeout) {
            clearTimeout(copyChatBtnTimeout);
          }
          btn.classList.add('copied');
          const icon = btn.querySelector('i');
          if (icon) icon.className = 'fas fa-check';
          const btnText = btn.querySelector('.btn-copy-text');
          if (btnText) btnText.textContent = 'Kopyalandı!';

          copyChatBtnTimeout = setTimeout(() => {
            resetCopyButtonUI();
          }, 2000);
        }
        notify('Sohbet başarıyla panoya kopyalandı!');
      };

      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(fullContent)
          .then(setCopiedUI)
          .catch(() => showToast('Panoya kopyalama başarısız oldu.', 'error'));
      } else {
        showToast('Tarayıcınız panoya kopyalamayı desteklemiyor.', 'error');
      }
    }
    window.copyWorkspaceChat = copyWorkspaceChat;

    function resetCopyButtonUI() {
      const btn = document.getElementById('btn-copy-chat');
      if (!btn) return;
      if (copyChatBtnTimeout) {
        clearTimeout(copyChatBtnTimeout);
        copyChatBtnTimeout = null;
      }
      btn.classList.remove('copied');
      const icon = btn.querySelector('i');
      if (icon) icon.className = 'fas fa-copy';
      const btnText = btn.querySelector('.btn-copy-text');
      if (btnText) btnText.textContent = 'Konuşmayı Kopyala';
    }
    window.resetCopyButtonUI = resetCopyButtonUI;

    // Dynamic Textarea Auto-sizing for workspace chat
    document.addEventListener('input', (e) => {
      if (e.target?.id === 'workspace-chat-input') {
        e.target.style.height = 'auto';
        e.target.style.height = `${Math.min(e.target.scrollHeight, 140)}px`;
      }
    });

    // Event Delegation for Citation Hover/Focus Popover & Click Navigation
    document.addEventListener('mouseover', (e) => {
      const citeEl = e.target?.closest?.('.chat-page-cite');
      if (citeEl) {
        showCitationPreviewPopover(citeEl);
        return;
      }
      const inPopover = e.target?.closest?.('#citation-preview-popover');
      if (inPopover) {
        if (_citePopoverHideTimer) {
          clearTimeout(_citePopoverHideTimer);
          _citePopoverHideTimer = null;
        }
      } else if (_activeCitedElement) {
        hideCitationPreviewPopover(false);
      }
    });

    document.addEventListener('focusin', (e) => {
      const citeEl = e.target?.closest?.('.chat-page-cite');
      if (citeEl) {
        showCitationPreviewPopover(citeEl);
      }
    });

    document.addEventListener('focusout', (e) => {
      if (e.target?.closest?.('.chat-page-cite')) {
        hideCitationPreviewPopover(false);
      }
    });

    document.addEventListener('click', (e) => {
      const popJumpBtn = e.target?.closest?.('[data-popover-jump]');
      if (popJumpBtn) {
        e.preventDefault();
        const p = Number.parseInt(popJumpBtn.dataset.popoverJump || '', 10);
        let snip = '';
        try { snip = decodeURIComponent(popJumpBtn.dataset.popoverSnippet || ''); } catch (_e) {}
        if (!Number.isNaN(p) && p >= 1) {
          navigateToCitationWithSpotlight(p, snip);
        }
        return;
      }
      const citeEl = e.target?.closest?.('.chat-page-cite');
      if (citeEl) {
        e.preventDefault();
        const page = Number.parseInt(citeEl.dataset.jumpPage || '', 10);
        if (!Number.isNaN(page) && page >= 1) {
          const snip = _resolveCitationSnippetForPage(citeEl, page);
          navigateToCitationWithSpotlight(page, snip);
        }
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const citeEl = e.target?.closest?.('.chat-page-cite');
      if (citeEl) {
        e.preventDefault();
        const page = Number.parseInt(citeEl.dataset.jumpPage || '', 10);
        if (!Number.isNaN(page) && page >= 1) {
          const snip = _resolveCitationSnippetForPage(citeEl, page);
          navigateToCitationWithSpotlight(page, snip);
        }
      }
    });

    window.sendWorkspaceMessage = sendWorkspaceMessage;
    window.handleWorkspaceChatKey = handleWorkspaceChatKey;
