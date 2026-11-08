/* ═══════════ ui_workspace.js — Workspace Reader, PDF.js Engine & Annotations ═══════════ */
    /* ═════════════════════════════════════════════════════════════
       Workspace Reader Functions (Split-Pane PDF + Contextual AI Chat)
       ═════════════════════════════════════════════════════════════ */
    let activeWorkspaceBook = null;
    let isWorkspaceChatLoading = false;
    let isFullBookLoaded = false;
    let activeTypewriterTimer = null;
    let activeTypewriterFullText = '';
    let activeTypewriterContainer = null;
    let isSpeaking = false;

    function jumpToPdfPage(pageNum) {
      const p = Number.parseInt(pageNum, 10);
      if (!p || Number.isNaN(p) || !pdfDoc || p < 1 || p > pdfPageCount) {
        if (typeof showToast === 'function') showToast(`Geçersiz sayfa numarası: ${pageNum}`, 'warning');
        return;
      }
      pdfPageNum = p;
      const pageInput = document.getElementById('pdf-page-num');
      if (pageInput) pageInput.value = p;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
      void renderPdfPageVirtual(p);
      scrollToPage(p);
      if (wrapper) {
        wrapper.classList.add('page-pulse');
        setTimeout(() => wrapper.classList.remove('page-pulse'), 1600);
      }
    }
    window.jumpToPdfPage = jumpToPdfPage;

    function stopChatGeneration() {
      if (activeTypewriterTimer) {
        clearInterval(activeTypewriterTimer);
        activeTypewriterTimer = null;
      }
      if (activeTypewriterContainer && activeTypewriterFullText) {
        activeTypewriterContainer.innerHTML = parseMarkdown(activeTypewriterFullText);
      }
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
      
      // Set loading state
      banner.classList.add('loading');
      icon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
      title.textContent = 'Kitap PDF\'i Gemini\'a yükleniyor...';
      subtitle.textContent = 'Oturum oluşturuluyor (yalnızca ilk defaya mahsustur)';
      btn.disabled = true;
      btn.innerHTML = '<i class="fas fa-hourglass-half"></i> Hazırlanıyor';
      
      try {
        const response = await apiFetch(`/api/workspace/load-book/${activeWorkspaceBook.hash}`, {
          method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
          isFullBookLoaded = true;
          banner.classList.remove('loading');
          banner.classList.add('loaded');
          icon.innerHTML = '<i class="fas fa-circle-check"></i>';
          const charK = Math.round(data.char_count / 1000);
          title.textContent = 'Kitap AI oturumu aktif';
          subtitle.textContent = `${charK}K karakter · Oturum hazır — sorular anında yanıtlanacak`;
          btn.innerHTML = '<i class="fas fa-check"></i> Hazır';
          
          // Inject system message into chat
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
          subtitle.textContent = data.error || 'Bilinmeyen hata';
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-rotate-right"></i> Tekrar Dene';
          
          setTimeout(() => {
            banner.classList.remove('error');
            resetBannerState();
          }, 5000);
        }
      } catch (err) {
        // İsteğe bağlı / sessiz hata toleransı: bağlantı hatası kullanıcıya banner üzerinde bildirilir
        console.warn('loadFullBookToAI hatası:', err);
        banner.classList.remove('loading');
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

    function openWorkspace(book, initialPage = null) {
      activeWorkspaceBook = book;
      
      // Reset copy chat button if active
      resetCopyButtonUI();
      
      // Sync meta text and cover slot
      document.getElementById('workspace-book-cat').textContent = book.category || 'Belge';
      document.getElementById('workspace-book-title').textContent = book.title || 'İsimsiz';
      const coverSlot = document.getElementById('workspace-cover-slot');
      if (coverSlot) {
        coverSlot.innerHTML = book.has_cover
          ? `<img src="/thumbnails/${book.hash}.jpg" alt="${esc(book.title || '')}">`
          : `<i class="fas fa-book-open" style="font-size:0.75rem; color:var(--muted);"></i>`;
      }
      
      // Reset banner
      resetBannerState();

      // Load PDF via custom HTML5 PDF.js Reader
      initCustomPdfViewer(book, initialPage);
      
      // Let the user load the book manually via the banner button
      // setTimeout(() => {
      //   loadFullBookToAI();
      // }, 500);
      
      // Open overlay
      document.getElementById('workspace-reader').classList.add('open');
      document.body.classList.add('modal-open');

      // On mobile viewports, start in immersive reading mode with bottom sheet chat collapsed
      if (window.innerWidth <= 768) {
        const cp = document.getElementById('workspace-chat-pane');
        const tb = document.getElementById('btn-toggle-workspace-chat');
        const lbl = document.getElementById('workspace-chat-toggle-label');
        if (cp) cp.classList.add('collapsed');
        if (tb) tb.classList.remove('active');
        if (lbl) lbl.textContent = 'AI Aç';
      }

      // Load previous persistent chat history from server if exists
      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.innerHTML = `
        <div class="chat-msg chat-ai">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">Merhaba! Şu anda <strong>${esc(book.title)}</strong> eseri üzerinde konuşmaya hazırız. Kitabın ana fikirleri, terimleri veya sormak istediğiniz kısımları hakkında sorular sorabilirsiniz.</div>
        </div>
      `;

      apiFetch(`/api/workspace/chat-history/${book.hash}`)
        .then(res => res.json())
        .then(data => applyWorkspaceChatHistory(data, chatMessages))
        .catch(err => {
          // İsteğe bağlı / sessiz hata toleransı: Geçmiş yüklenemezse varsayılan selamlama kalır
          console.debug('Chat history load error:', err);
        });
      
      // Focus textarea
      setTimeout(() => {
        const textarea = document.getElementById('workspace-chat-input');
        if (textarea) textarea.focus();
      }, 300);
    }

    function openBookWithMorph(cardOrCover, book) {
      const targetBook = book || (typeof allBooks !== 'undefined' ? allBooks.find(b => b.hash === cardOrCover?.dataset?.hash) : null);
      if (!targetBook) return;

      const card = (cardOrCover instanceof HTMLElement) ? (cardOrCover.closest('.book-card') || cardOrCover) : document.querySelector(`.book-card[data-hash="${targetBook.hash}"]`);
      const cover = card ? (card.querySelector('.card-cover') || card) : null;

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        if (typeof closeModalDirect === 'function') closeModalDirect();
        openWorkspace(targetBook);
        return;
      }

      if (cover) cover.style.viewTransitionName = 'book-cover';
      if (typeof closeModalDirect === 'function') closeModalDirect();

      const transition = document.startViewTransition(() => {
        openWorkspace(targetBook);
        const slot = document.getElementById('workspace-cover-slot');
        if (slot) slot.style.viewTransitionName = 'book-cover';
        if (cover) cover.style.viewTransitionName = '';
      });

      transition.finished.finally(() => {
        const slot = document.getElementById('workspace-cover-slot');
        if (slot) slot.style.removeProperty('view-transition-name');
        if (cover) cover.style.removeProperty('view-transition-name');
      });
    }
    window.openBookWithMorph = openBookWithMorph;

    function closeWorkspace() {
      const currentBook = activeWorkspaceBook;
      const card = currentBook ? document.querySelector(`.book-card[data-hash="${currentBook.hash}"]`) : null;
      const cover = card ? (card.querySelector('.card-cover') || card) : null;
      const slot = document.getElementById('workspace-cover-slot');

      const doClose = () => {
        document.getElementById('workspace-reader').classList.remove('open');
        document.body.classList.remove('modal-open');
        
        // Stop ongoing typewriter or TTS
        if (activeTypewriterTimer) {
          clearInterval(activeTypewriterTimer);
          activeTypewriterTimer = null;
        }
        const stopWrap = document.getElementById('workspace-stop-wrap');
        if (stopWrap) stopWrap.style.display = 'none';

        if (window.speechSynthesis?.speaking) {
          window.speechSynthesis.cancel();
        }
        isSpeaking = false;
        const ttsBtn = document.getElementById('pdf-tts-btn');
        if (ttsBtn) {
          ttsBtn.classList.remove('active');
          ttsBtn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }

        // Cleanup custom HTML5 PDF.js Reader resources
        cleanupCustomPdfViewer();
        
        activeWorkspaceBook = null;
        isFullBookLoaded = false;
      };

      if (!document.startViewTransition || window.matchMedia('(prefers-reduced-motion: reduce)').matches || !cover) {
        doClose();
        return;
      }

      if (slot) slot.style.viewTransitionName = 'book-cover';
      const transition = document.startViewTransition(() => {
        doClose();
        if (cover) cover.style.viewTransitionName = 'book-cover';
        if (slot) slot.style.viewTransitionName = '';
      });

      transition.finished.finally(() => {
        if (cover) cover.style.removeProperty('view-transition-name');
        if (slot) slot.style.removeProperty('view-transition-name');
      });
    }

    function handleWorkspaceChatKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        void sendWorkspaceMessage();
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

    function startWorkspaceTypewriter(rawReply, replyId, chatMessages) {
      const targetContainer = document.querySelector(`#${replyId} .chat-msg-text`);
      if (!targetContainer) return;
      const words = (rawReply || '').split(' ');
      const totalWords = words.length || 1;
      // Daktilo efekti en fazla 2.5 saniyede (2500ms) tamamlansın, min 5ms, max 25ms
      const wordDelay = Math.min(25, Math.max(5, Math.floor(2500 / totalWords)));
      let currentText = '';
      let wordIndex = 0;

      const stopWrap = document.getElementById('workspace-stop-wrap');
      if (stopWrap) stopWrap.style.display = 'block';
      activeTypewriterFullText = rawReply;
      activeTypewriterContainer = targetContainer;

      // Smart auto-scroll check: Yalnızca kullanıcı en alttaysa otomatik kaydır, yukarı kaydırdıysa scrollu kilitleme
      const isUserNearBottom = () => {
        if (!chatMessages) return true;
        return (chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight) < 60;
      };

      let lastParagraphCheck = '';
      activeTypewriterTimer = setInterval(() => {
        if (wordIndex < words.length) {
          currentText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
          wordIndex++;

          // Sadece paragraf bitişlerinde (\n\n) veya son kelimede tam markdown parse et; ara kelimelerde ham metin güncelle
          const hasNewParagraph = currentText.includes('\n\n') && currentText.lastIndexOf('\n\n') > lastParagraphCheck.length;
          if (hasNewParagraph) {
            targetContainer.innerHTML = parseMarkdown(currentText);
            lastParagraphCheck = currentText.slice(0, currentText.lastIndexOf('\n\n'));
          } else if (lastParagraphCheck.length === 0) {
            targetContainer.textContent = currentText;
          } else {
            const unrenderedPart = currentText.slice(lastParagraphCheck.length);
            const safeUnrendered = typeof esc === 'function' ? esc(unrenderedPart) : unrenderedPart;
            targetContainer.innerHTML = parseMarkdown(lastParagraphCheck) + '<p>' + safeUnrendered + '</p>';
          }

          if (isUserNearBottom() && chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
        } else {
          clearInterval(activeTypewriterTimer);
          activeTypewriterTimer = null;
          targetContainer.innerHTML = parseMarkdown(rawReply);
          if (isUserNearBottom() && chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
          }
          if (stopWrap) stopWrap.style.display = 'none';
          isWorkspaceChatLoading = false;
        }
      }, wordDelay);
    }

    async function sendWorkspaceMessage() {
      if (isWorkspaceChatLoading || !activeWorkspaceBook) return;
      
      const input = document.getElementById('workspace-chat-input');
      const text = input.value.trim();
      if (!text) return;
      
      // Reset copy button if in copied state
      resetCopyButtonUI();

      input.value = '';
      input.style.height = 'auto'; // Reset size
      
      const chatMessages = document.getElementById('workspace-chat-messages');
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-user">
          <div class="chat-msg-avatar"><i class="fas fa-user"></i></div>
          <div class="chat-msg-text">${esc(text)}</div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      const tempId = `typing-${Date.now()}`;
      const loadingNoticeText = !isFullBookLoaded 
        ? '<div style="font-size: 0.78rem; opacity: 0.85; margin-bottom: 6px;"><i class="fas fa-cloud-arrow-up fa-fade"></i> Kitap PDF\'i Gemini oturumuna yükleniyor, ilk soru biraz sürebilir...</div>' 
        : '';
      chatMessages.insertAdjacentHTML('beforeend', `
        <div class="chat-msg chat-ai" id="${tempId}">
          <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
          <div class="chat-msg-text">
            ${loadingNoticeText}
            <div class="chat-typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      `);
      chatMessages.scrollTop = chatMessages.scrollHeight;
      
      isWorkspaceChatLoading = true;
      
      try {
        const response = await apiFetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            message: text,
            target_book_hash: activeWorkspaceBook.hash,
            load_full_book: isFullBookLoaded
          })
        });
        
        if (!response?.ok) {
          const errDetail = response ? `Sunucu hatası (${response.status})` : 'Sunucuya ulaşılamadı.';
          throw new Error(errDetail);
        }

        const data = await response.json();
        const rawReply = data.response || 'Yanıt alınamadı.';
        
        document.getElementById(tempId)?.remove();
        markSessionLoadedInBanner();
        
        const replyId = `reply-${Date.now()}`;
        chatMessages.insertAdjacentHTML('beforeend', `
          <div class="chat-msg chat-ai" id="${replyId}">
            <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
            <div class="chat-msg-text"></div>
          </div>
        `);
        startWorkspaceTypewriter(rawReply, replyId, chatMessages);
      } catch (err) {
        document.getElementById(tempId)?.remove();
        isWorkspaceChatLoading = false;
        const errText = err?.message || 'Bağlantı hatası: Sunucuya ulaşılamadı.';
        chatMessages.insertAdjacentHTML('beforeend', `
          <div class="chat-msg chat-ai">
            <div class="chat-msg-avatar"><i class="fas fa-wand-magic-sparkles"></i></div>
            <div class="chat-msg-text" style="color: #b0473c;">${esc(errText)}</div>
          </div>
        `);
      } finally {
        if (!activeTypewriterTimer) {
          isWorkspaceChatLoading = false;
          const stopWrap = document.getElementById('workspace-stop-wrap');
          if (stopWrap) stopWrap.style.display = 'none';
        }
        chatMessages.scrollTop = chatMessages.scrollHeight;
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

        // Clean and extract text
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
        } else {
          // Self-contained elegant toast
          let toast = document.getElementById('chat-copy-toast');
          if (!toast) {
            toast = document.createElement('div');
            toast.id = 'chat-copy-toast';
            toast.style.cssText = 'position: fixed; bottom: 30px; right: 30px; background: #5f7a4f; color: #fff; padding: 0.75rem 1.4rem; border-radius: 50px; font-family: Inter, sans-serif; font-size: 0.88rem; font-weight: 600; box-shadow: 0 10px 25px rgba(95,122,79,0.3); z-index: 10000; display: flex; align-items: center; gap: 0.5rem; transition: all 0.3s ease; opacity: 0; transform: translateY(10px);';
            document.body.appendChild(toast);
          }
          toast.innerHTML = `<i class="fas fa-check-circle"></i> ${msg}`;
          toast.style.opacity = '1';
          toast.style.transform = 'translateY(0)';
          setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
          }, 2500);
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
          .catch(err => {
            console.warn('Panoya yazma başarısız, fallback deneniyor:', err);
            fallbackCopy(fullContent);
          });
      } else {
        fallbackCopy(fullContent);
      }

      function fallbackCopy(text) {
        if (navigator?.clipboard?.writeText) {
          navigator.clipboard.writeText(text)
            .then(setCopiedUI)
            .catch(() => showToast('Panoya kopyalama başarısız oldu.', 'error'));
          return;
        }
        showToast('Tarayıcınız panoya kopyalamayı desteklemiyor.', 'error');
      }
    }
    window.copyWorkspaceChat = copyWorkspaceChat;

    let copyChatBtnTimeout = null;
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

    // ─── Workspace Split-Pane Resizer Logic ──────────────────────────────
    document.addEventListener('DOMContentLoaded', () => {
      const handle = document.getElementById('workspace-resize-handle');
      const pdfPane = document.getElementById('workspace-pdf-pane');
      const chatPane = document.getElementById('workspace-chat-pane');
      
      if (!handle || !pdfPane || !chatPane) return;
      
      let isDragging = false;
      
      const onMouseDown = (e) => {
        isDragging = true;
        handle.classList.add('active');
        document.body.style.cursor = 'col-resize';
        // Add a temporary overlay over iframe so mouse events don't get swallowed by pdf
        const iframeMask = document.createElement('div');
        iframeMask.id = 'iframe-drag-mask';
        iframeMask.style.position = 'absolute';
        iframeMask.style.inset = '0';
        iframeMask.style.zIndex = '9999';
        pdfPane.appendChild(iframeMask);
      };
      
      const onMouseMove = (e) => {
        if (!isDragging) return;
        
        const clientX = e.clientX || e.touches?.[0]?.clientX;
        if (!clientX) return;
        
        const totalWidth = window.innerWidth;
        const leftWidthPercent = (clientX / totalWidth) * 100;
        
        // Limits constraints (between 30% and 80%)
        if (leftWidthPercent > 30 && leftWidthPercent < 80) {
          pdfPane.style.flex = leftWidthPercent / 100;
          chatPane.style.flex = (100 - leftWidthPercent) / 100;
        }
      };
      
      const onMouseUp = () => {
        if (!isDragging) return;
        isDragging = false;
        handle.classList.remove('active');
        document.body.style.cursor = '';
        document.getElementById('iframe-drag-mask')?.remove();
      };
      
      handle.addEventListener('mousedown', onMouseDown);
      handle.addEventListener('touchstart', onMouseDown);
      
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('touchmove', onMouseMove);
      
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchend', onMouseUp);
    });

    function toggleWorkspaceChatPane() {
      const chatPane = document.getElementById('workspace-chat-pane');
      const resizeHandle = document.getElementById('workspace-resize-handle');
      const toggleBtn = document.getElementById('btn-toggle-workspace-chat');
      const label = document.getElementById('workspace-chat-toggle-label');
      if (!chatPane) return;

      const isCollapsed = chatPane.classList.toggle('collapsed');
      if (resizeHandle) {
        resizeHandle.style.display = isCollapsed ? 'none' : 'flex';
      }
      if (toggleBtn) {
        toggleBtn.classList.toggle('active', !isCollapsed);
        toggleBtn.title = isCollapsed ? 'AI Asistan Panelini Aç' : 'AI Asistan Panelini Gizle (Odaklı Okuma)';
      }
      if (label) {
        label.textContent = isCollapsed ? 'AI Aç' : 'AI Paneli';
      }

      // Smoothly trigger a resize / refit on the PDF canvas so reader is responsive
      setTimeout(() => {
        if (typeof pdfFitWidth === 'function') {
          pdfFitWidth();
        }
        window.dispatchEvent(new Event('resize'));
      }, 280);
    }
    window.toggleWorkspaceChatPane = toggleWorkspaceChatPane;

    // Mobile bottom sheet velocity drag gesture for reader chat pane
    (function setupMobileChatSheetDrag() {
      const chatPane = document.getElementById('workspace-chat-pane');
      const chatHeader = document.getElementById('workspace-chat-header');
      if (!chatPane || !chatHeader) return;

      let startY = 0;
      let currentY = 0;
      let isDragging = false;
      let startTime = 0;

      chatHeader.addEventListener('touchstart', (e) => {
        if (window.innerWidth > 768) return;
        if (chatPane.classList.contains('collapsed')) return;
        startY = e.touches[0].clientY;
        currentY = startY;
        startTime = Date.now();
        isDragging = true;
        chatPane.style.transition = 'none';
      }, { passive: true });

      window.addEventListener('touchmove', (e) => {
        if (!isDragging || window.innerWidth > 768) return;
        currentY = e.touches[0].clientY;
        const deltaY = currentY - startY;
        if (deltaY > 0) {
          chatPane.style.transform = `translateY(${deltaY}px)`;
        }
      }, { passive: true });

      window.addEventListener('touchend', () => {
        if (!isDragging || window.innerWidth > 768) return;
        isDragging = false;
        chatPane.style.transition = '';
        const deltaY = currentY - startY;
        const elapsed = Date.now() - startTime;
        const velocity = deltaY / Math.max(elapsed, 1);

        if (deltaY > 80 || (velocity > 0.4 && deltaY > 20)) {
          chatPane.style.transform = '';
          if (!chatPane.classList.contains('collapsed')) {
            toggleWorkspaceChatPane();
          }
        } else {
          chatPane.style.transform = '';
        }
      });
    })();


    /* ==========================================================================
       CUSTOM INTERACTIVE HTML5 PDF.JS READER ENGINE WITH ANNOTATIONS & NOTES
       ========================================================================== */
    
    // Keep track of which pages are currently rendered or rendering to avoid duplicate render tasks
    let pdfRenderedPages = {}; // pageNum -> 'done' or 'rendering'
    let pdfRenderTasks = {};   // pageNum -> active PDF.js RenderTask
    let pdfActiveNoteColorClass = 'yellow';
    let pdfActiveNoteColorHex = '#e8dca0';

    function selectModalNoteColor(colorHex, colorClass) {
      pdfActiveNoteColorClass = colorClass;
      pdfActiveNoteColorHex = colorHex;
      
      const colors = ['yellow', 'green', 'blue', 'pink'];
      colors.forEach(c => {
        const btn = document.getElementById(`modal-color-${c}`);
        if (btn) {
          if (c === colorClass) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        }
      });
    }
    
    // PDF Viewer State variables
    let pdfDoc = null;
    let pdfPageNum = 1;
    let pdfPageCount = 0;
    let pdfScale = 1.2;
    let pdfIsRendering = false;
    let pdfPendingPageNum = null;
    let pdfIsFitWidth = false;
    let pdfIsFitHeight = false;
    let saveProgressDebounceTimer = null;
    let pdfIsSpreadMode = localStorage.getItem('pdf_spread_mode') === 'true';

    function updateSpreadUI() {
      const btn = document.getElementById('pdf-spread-btn');
      if (btn) {
        btn.classList.toggle('active', !!pdfIsSpreadMode);
        btn.title = pdfIsSpreadMode ? 'Tek Sayfa Görünümüne Geç' : 'Çift Sayfa Kitap Görünümüne Geç';
      }
    }

    function togglePdfSpreadMode() {
      pdfIsSpreadMode = !pdfIsSpreadMode;
      try {
        localStorage.setItem('pdf_spread_mode', String(pdfIsSpreadMode));
      } catch (_) {}
      updateSpreadUI();
      applySpreadLayout();
      checkVisiblePagesAndRender();
    }
    window.togglePdfSpreadMode = togglePdfSpreadMode;
    window.updateSpreadUI = updateSpreadUI;

    function renderSpreadRows(container, wrappers) {
      let i = 0;
      while (i < wrappers.length) {
        const row = document.createElement('div');
        row.className = 'pdf-spread-row';

        if (i === 0) {
          wrappers[0].classList.remove('spread-left', 'spread-right');
          row.appendChild(wrappers[0]);
          i++;
        } else {
          const leftPage = wrappers[i];
          leftPage.classList.add('spread-left');
          leftPage.classList.remove('spread-right');
          row.appendChild(leftPage);
          i++;

          if (i < wrappers.length) {
            const rightPage = wrappers[i];
            rightPage.classList.add('spread-right');
            rightPage.classList.remove('spread-left');
            row.appendChild(rightPage);
            i++;
          }
        }
        container.appendChild(row);
      }
    }

    function renderSinglePageRows(container, wrappers) {
      wrappers.forEach(w => {
        w.classList.remove('spread-left', 'spread-right');
        container.appendChild(w);
      });
    }

    function applySpreadLayout() {
      const container = document.getElementById('pdf-canvas-container');
      if (!container || !pdfDoc || pdfPageCount === 0) return;

      const isWide = window.innerWidth >= 800;
      const useSpread = pdfIsSpreadMode && isWide;

      const wrappers = [];
      for (let p = 1; p <= pdfPageCount; p++) {
        const w = document.getElementById(`pdf-page-wrapper-${p}`);
        if (w) wrappers.push(w);
      }
      if (wrappers.length === 0) return;

      container.innerHTML = '';

      if (!useSpread) {
        renderSinglePageRows(container, wrappers);
      } else {
        renderSpreadRows(container, wrappers);
      }

      if (pdfPageNum > 0) {
        scrollToPage(pdfPageNum);
      }
    }
    window.applySpreadLayout = applySpreadLayout;
    
    // Annotation variables (Keys are book hashes for sandboxed persistency)
    let pdfHighlights = {}; // pageNum -> Array of {id, text, colorClass, colorHex, coords: [{left, top, width, height}]}
    let pdfNotes = {};      // highlightId -> noteText string
    
    // Temporary selection tracking
    let pdfSelectedText = "";
    let pdfSelectionRanges = [];
    let pdfActiveHighlightIdForNote = null;

    // ═════════════════════════════════════════════════════════════
    // PDF.js Smart Geometric Line & Margin Clamping Selection Engine
    // (Google Chrome PDFium & Adobe Acrobat Reader Standard)
    // Eliminates margin click misses, paragraph bleed-through & whitespace jumping
    // ═════════════════════════════════════════════════════════════
    const activeTextLayersMap = new Map(); // textLayerDiv -> endOfContentDiv
    const pageGeometryCache = new Map();   // pageNum -> geometry
    let selectionChangeAbortController = null;
    let prevSelectionRange = null;
    let isUserSelectingText = false;
    let selectionDragState = null;

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

      // Pointer down: initiate smart geometric selection
      document.addEventListener("pointerdown", (evt) => {
        if (evt.button !== 0 && evt.button !== undefined) return;

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

        // Allow native double/triple-click word/paragraph selection
        if (evt.detail > 1) {
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

        // Prevent erratic native browser selection heuristics from taking over
        evt.preventDefault();

        const isDirectSpanClick = evt.target.tagName === 'SPAN' && evt.target.closest('.textLayer');

        selectionDragState = {
          startX: evt.clientX,
          startY: evt.clientY,
          anchorNode: hit.node,
          anchorOffset: hit.offset,
          anchorTextLayer: textLayer,
          anchorPageWrapper: pageWrapper,
          anchorLineIdx: hit.lineIdx,
          isDragging: false,
          isMarginStart: !isDirectSpanClick
        };

        const sel = window.getSelection();
        try {
          sel.collapse(hit.node, hit.offset);
        } catch (_) {
          // İsteğe bağlı / sessiz hata toleransı: Geçersiz seçim aralığı
        }
      }, { signal });

      // Pointer move: update selection with geometric clamping
      document.addEventListener("pointermove", (evt) => {
        if (!selectionDragState) return;

        const dx = evt.clientX - selectionDragState.startX;
        const dy = evt.clientY - selectionDragState.startY;
        const dist = Math.hypot(dx, dy);

        if (!selectionDragState.isDragging && dist < 3) {
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
        } catch (e) {
          // Cross-boundary selection fallback
        }
      }, { signal });

      // Pointer up: complete selection and position floating action bar
      document.addEventListener("pointerup", (evt) => {
        if (selectionDragState) {
          if (selectionDragState.isDragging) {
            handleTextSelection();
          } else {
            // Simple click without drag: clear selection
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

      // selectionchange: Auxiliary stabilizer for keyboard / touch selection
      document.addEventListener("selectionchange", () => {
        // Skip if custom geometric drag is actively driving setBaseAndExtent
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

    // Initialize custom PDF.js reader for the loaded book
    function setupPdfPages(firstPage, container) {
      let viewport = firstPage.getViewport({ scale: 1.0 });

      if (pdfIsFitWidth) {
        const containerWidth = Math.max(300, container.clientWidth - 48);
        pdfScale = Math.max(0.3, Math.min(4.0, containerWidth / viewport.width));
        updateZoomLabel();
      } else if (pdfIsFitHeight) {
        const containerHeight = Math.max(300, container.clientHeight - 80);
        pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
        updateZoomLabel();
      }

      viewport = firstPage.getViewport({ scale: pdfScale });

      for (let p = 1; p <= pdfPageCount; p++) {
        const pageWrapper = document.createElement('div');
        pageWrapper.className = 'pdf-page-wrapper';
        pageWrapper.id = `pdf-page-wrapper-${p}`;
        pageWrapper.dataset.pageNumber = p;
        pageWrapper.dataset.pageNum = p;
        pageWrapper.style.width = viewport.width + 'px';
        pageWrapper.style.height = viewport.height + 'px';
        pageWrapper.style.marginBottom = '24px';
        pageWrapper.style.position = 'relative';

        const textLayer = document.createElement('div');
        textLayer.className = 'textLayer';
        textLayer.id = `textLayer-${p}`;
        textLayer.style.width = viewport.width + 'px';
        textLayer.style.height = viewport.height + 'px';
        textLayer.style.setProperty('--scale-factor', String(pdfScale));
        pageWrapper.appendChild(textLayer);

        const highlightLayer = document.createElement('div');
        highlightLayer.className = 'pdf-highlight-layer';
        highlightLayer.id = `pdf-highlight-layer-${p}`;
        highlightLayer.style.width = viewport.width + 'px';
        highlightLayer.style.height = viewport.height + 'px';
        pageWrapper.appendChild(highlightLayer);

        container.appendChild(pageWrapper);
      }

      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        applySpreadLayout();
      }

      void renderPdfPageVirtual(pdfPageNum);

      requestAnimationFrame(() => {
        if (pdfPageNum > 1) {
          scrollToPage(pdfPageNum);
        }
        setTimeout(() => {
          if (pdfPageNum > 1) {
            scrollToPage(pdfPageNum);
          }
          checkVisiblePagesAndRender();
        }, 120);
      });
    }

    async function setupLoadedPdf(pdf, book, container, pdfUrl) {
      pdfDoc = pdf;
      pdfPageCount = pdf.numPages;

      document.getElementById('pdf-page-count').textContent = pdfPageCount;
      const pageInput = document.getElementById('pdf-page-num');
      pageInput.max = pdfPageCount;
      pageInput.value = pdfPageNum;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      loadPdfOutline(pdf).catch(err => console.debug("loadPdfOutline error:", err));

      if (container) {
        container.innerHTML = "";
        try {
          const firstPage = await pdf.getPage(1);
          setupPdfPages(firstPage, container);
        } catch (err) {
          console.error("PDF getPage(1) hatası:", err);
        }
      }

      renderNotesSidebar();
    }

    // --- [D2: PDF Pre-Fetching & Skeleton Loader] ---
    const pdfPrefetchCache = new Map();

    function prefetchPdfDocument(hash) {
      if (!hash || !window.pdfjsLib || pdfPrefetchCache.has(hash)) return;
      const pdfUrl = `/api/download/${hash}`;
      try {
        const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
        pdfPrefetchCache.set(hash, {
          task: loadingTask,
          promise: loadingTask.promise
        });
      } catch (e) {
        console.debug('Prefetch silent skip:', e);
      }
    }
    window.prefetchPdfDocument = prefetchPdfDocument;

    function cancelPdfPrefetch(hash) {
      if (!hash || !pdfPrefetchCache.has(hash)) return;
      const item = pdfPrefetchCache.get(hash);
      if (item && item.cleanupTimer) clearTimeout(item.cleanupTimer);
      if (item) {
        item.cleanupTimer = setTimeout(() => {
          try { item.task.destroy(); } catch (_) {}
          pdfPrefetchCache.delete(hash);
        }, 8000);
      }
    }
    window.cancelPdfPrefetch = cancelPdfPrefetch;

    function initCustomPdfViewer(book, initialPage = null) {
      // Reset state
      pdfDoc = null;
      pdfPageNum = (initialPage && initialPage > 0) ? initialPage : (book.okunulan_sayfa || 1);
      pdfPageCount = 0;
      pdfScale = 1.2;
      pdfIsRendering = false;
      pdfPendingPageNum = null;
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      closePdfSearch();
      pdfSearchTextCache = {};
      pdfHighlights = {};
      pdfNotes = {};
      pdfSelectedText = "";
      pdfSelectionRanges = [];
      pdfActiveHighlightIdForNote = null;
      pdfRenderedPages = {};
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};

      // Sync surface mode and toolbar buttons
      const viewer = document.getElementById('custom-pdf-viewer');
      if (viewer) {
        viewer.dataset.surfaceMode = currentReaderSurfaceMode;
      }
      document.querySelectorAll('#reader-surface-group .surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `btn-surface-${currentReaderSurfaceMode}`);
      });

      // Update zoom label to initial
      updateZoomLabel();
      updateSpreadUI();
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');

      // Load annotations: First from localStorage for zero-latency, then sync from server API
      try {
        const savedHighlights = localStorage.getItem(`lib-highlights-${book.hash}`);
        const savedNotes = localStorage.getItem(`lib-notes-${book.hash}`);
        if (savedHighlights) pdfHighlights = JSON.parse(savedHighlights);
        if (savedNotes) pdfNotes = JSON.parse(savedNotes);
      } catch (e) {
        console.error("Local storage okuma hatası:", e);
      }

      apiFetch(`/api/books/${book.hash}/annotations`)
        .then(res => res.json())
        .then(data => {
          if (data?.status === 'success' && Array.isArray(data.annotations) && data.annotations.length > 0) {
            const apiHighlights = {};
            const apiNotes = {};
            data.annotations.forEach(a => {
              const p = a.sayfa_no;
              if (!apiHighlights[p]) apiHighlights[p] = [];
              let coords = [];
              try { coords = JSON.parse(a.koordinatlar || '[]'); } catch (_) {}
              apiHighlights[p].push({
                id: a.id,
                text: a.secilen_metin || '',
                colorClass: a.renk_sinif || 'yellow',
                colorHex: a.renk_hex || '#e8dca0',
                coords: coords
              });
              if (a.not_metni) {
                apiNotes[a.id] = a.not_metni;
              }
            });
            pdfHighlights = apiHighlights;
            pdfNotes = apiNotes;
            // Update local storage cache
            try {
              localStorage.setItem(`lib-highlights-${book.hash}`, JSON.stringify(pdfHighlights));
              localStorage.setItem(`lib-notes-${book.hash}`, JSON.stringify(pdfNotes));
            } catch (_) {
              // İsteğe bağlı / sessiz hata toleransı: localStorage kayıt hatası göz ardı edilir
            }
            renderNotesSidebar();
            if (pdfPageNum) drawPageHighlightsAndNotes(pdfPageNum);
          }
        })
        .catch(err => console.warn("API notları yüklenirken hata:", err));

      // Initialize UI controls
      document.getElementById('pdf-page-num').value = pdfPageNum;
      document.getElementById('pdf-page-count').textContent = "-";
      
      const emptyDiv = `<div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>`;
      document.getElementById('pdf-notes-list').innerHTML = emptyDiv;

      // Hide floating bar
      hideFloatingBar();

      // Begin loading PDF document
      const pdfUrl = `/api/download/${book.hash}`;
      
      if (!window.pdfjsLib) {
        console.error("PDF.js kütüphanesi yüklenemedi.");
        return;
      }

      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.innerHTML = `
          <div class="reader-skeleton-wrap">
            <div class="reader-skeleton-cover-preview">
              ${book.has_cover ? `<img src="/thumbnails/${book.hash}.jpg" alt="">` : '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);"><i class="fas fa-book" style="font-size:2.5rem;"></i></div>'}
            </div>
            <div class="reader-skeleton-page">
              <div class="reader-skeleton-line title"></div>
              <div class="reader-skeleton-line short"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line"></div>
              <div class="reader-skeleton-line medium"></div>
            </div>
          </div>
        `;
      }

      // Check file extension: If .txt, render clean typography reader
      const bookFilename = (book.file || book.dosya_adi || book.title || "").toLowerCase();
      if (bookFilename.endsWith(".txt")) {
        fetch(pdfUrl)
          .then(r => r.text())
          .then(txt => {
            if (container) {
              container.innerHTML = `
                <div style="max-width: 800px; margin: 2rem auto; padding: 3rem 2.5rem; background: var(--paper); border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); font-family: 'Geist', sans-serif; line-height: 1.8; color: var(--ink); white-space: pre-wrap; word-break: break-word; font-size: 1.05rem;">${esc(txt)}</div>
              `;
            }
            document.getElementById('pdf-page-count').textContent = "1";
            document.getElementById('pdf-page-num').value = 1;
            renderNotesSidebar();
          })
          .catch(err => {
            if (container) container.innerHTML = `<div style="padding: 2rem; color: var(--accent); text-align: center;">Metin dosyası yüklenirken hata oluştu: ${esc(String(err))}</div>`;
          });
        return;
      }

      // D2: Use pre-fetched promise if available for zero-latency instant open
      let docPromise = null;
      if (pdfPrefetchCache.has(book.hash)) {
        const cached = pdfPrefetchCache.get(book.hash);
        docPromise = cached.promise;
        pdfPrefetchCache.delete(book.hash);
      } else {
        const loadingTask = window.pdfjsLib.getDocument(pdfUrl);
        docPromise = loadingTask.promise;
      }

      docPromise
        .then(pdf => setupLoadedPdf(pdf, book, container, pdfUrl))
        .catch(function(error) {
          console.error("PDF.js yükleme hatası:", error);
          if (container) {
            container.innerHTML = `<div style="padding: 3rem; text-align: center; color: var(--muted); font-family: 'Geist', sans-serif;"><i class="fas fa-book-open" style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--accent); opacity: 0.8; display: block;"></i><strong>${esc(book.title || 'Belge')}</strong><p style="margin-top: 0.5rem; font-size: 0.9rem;">Bu dosya türü standart PDF olmadığı için gömülü önizleyici yerine AI Asistanı ile doğrudan taranabilir ve soru-cevap yapılabilir.</p><a href="${pdfUrl}" class="btn-import" style="display: inline-block; margin-top: 1rem; text-decoration: none; padding: 0.6rem 1.4rem;" download><i class="fas fa-download"></i> Dosyayı İndir</a></div>`;
          }
        });

      // Bind selection mouse/touch listeners to container
      if (container) {
        container.addEventListener('mouseup', handleTextSelection);
        container.addEventListener('touchend', handleTextSelection);
      }
    }

    // Free resources and bindings on close
    function cleanupCustomPdfViewer() {
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      pdfRenderedPages = {};
      if (pdfDoc && typeof pdfDoc.destroy === 'function') {
        try { pdfDoc.destroy(); } catch (_) {}
      }
      pdfDoc = null;
      hideFloatingBar();
      closePdfSearch();
      pdfSearchTextCache = {};
      if (selectionChangeAbortController) {
        try { selectionChangeAbortController.abort(); } catch (_) {}
        selectionChangeAbortController = null;
      }
      activeTextLayersMap.clear();
      invalidatePageGeometry();
      selectionDragState = null;
      prevSelectionRange = null;
      isUserSelectingText = false;
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.removeEventListener('mouseup', handleTextSelection);
        container.removeEventListener('touchend', handleTextSelection);
      }
    }

    function cleanupOffscreenPage(pNum) {
      if (pdfRenderTasks[pNum]) {
        try { pdfRenderTasks[pNum].cancel(); } catch (_) { /* sessiz iptal */ }
        delete pdfRenderTasks[pNum];
      }
      const canvas = document.getElementById(`pdf-render-canvas-${pNum}`);
      if (canvas) {
        canvas.width = 0;
        canvas.height = 0;
        canvas.remove();
      }
      const textLayer = document.getElementById(`textLayer-${pNum}`);
      if (textLayer) {
        unregisterTextLayerForSelection(textLayer);
        textLayer.innerHTML = "";
      }
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pNum}`);
      if (highlightLayer) highlightLayer.innerHTML = "";
      delete pdfRenderedPages[pNum];
    }

    function updateVisiblePageProgress(mostVisiblePage) {
      if (!mostVisiblePage || Number.isNaN(mostVisiblePage) || pdfPageNum === mostVisiblePage) return;

      pdfPageNum = mostVisiblePage;
      const pageInput = document.getElementById('pdf-page-num');
      if (pageInput) pageInput.value = pdfPageNum;

      const prevBtn = document.getElementById('pdf-prev-btn');
      const nextBtn = document.getElementById('pdf-next-btn');
      if (prevBtn) prevBtn.disabled = (pdfPageNum <= 1);
      if (nextBtn) nextBtn.disabled = (pdfPageNum >= pdfPageCount);

      if (activeWorkspaceBook) {
        activeWorkspaceBook.okunulan_sayfa = pdfPageNum;
        if (typeof allBooks !== 'undefined' && Array.isArray(allBooks)) {
          const cachedBook = allBooks.find(b => (b.hash || b.dosya_hash) === activeWorkspaceBook.hash);
          if (cachedBook) {
            cachedBook.okunulan_sayfa = pdfPageNum;
          }
        }
        if (saveProgressDebounceTimer) {
          clearTimeout(saveProgressDebounceTimer);
        }
        const targetHash = activeWorkspaceBook.hash;
        const targetPage = pdfPageNum;
        saveProgressDebounceTimer = setTimeout(() => {
          apiFetch(`/api/books/${targetHash}/progress`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page: targetPage })
          }).catch(err => console.warn("Okuma ilerlemesi kaydedilemedi:", err));
        }, 400);
      }
    }

    // Dynamic virtual scroll renderer
    function checkVisiblePagesAndRender() {
      if (!pdfDoc) return;
      
      const container = document.getElementById('pdf-canvas-container');
      if (!container) return;
      
      if (pdfPageNum && !Number.isNaN(pdfPageNum) && pdfPageNum >= 1 && !pdfRenderedPages[pdfPageNum]) {
        void renderPdfPageVirtual(pdfPageNum);
      }
      
      const containerRect = container.getBoundingClientRect();
      const wrappers = container.querySelectorAll('.pdf-page-wrapper');
      
      let mostVisiblePage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      let maxVisibleHeight = 0;
      
      wrappers.forEach(wrapper => {
        const pNum = Number.parseInt(wrapper.dataset.pageNum || wrapper.dataset.pageNumber || wrapper.id.replace('pdf-page-wrapper-', ''), 10);
        if (Number.isNaN(pNum) || pNum < 1) return;
        const rect = wrapper.getBoundingClientRect();
        
        const visibleTop = Math.max(rect.top, containerRect.top);
        const visibleBottom = Math.min(rect.bottom, containerRect.bottom);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        
        if (visibleHeight > maxVisibleHeight) {
          maxVisibleHeight = visibleHeight;
          mostVisiblePage = pNum;
        }
        
        const isNearViewport = (rect.bottom >= containerRect.top - rect.height * 1.5 && rect.top <= containerRect.bottom + rect.height * 1.5);
        if (isNearViewport) {
          if (!pdfRenderedPages[pNum]) {
            void renderPdfPageVirtual(pNum);
          }
        } else if (pdfRenderedPages[pNum] === 'done' && !isUserSelectingText) {
          cleanupOffscreenPage(pNum);
        }
      });
      
      updateVisiblePageProgress(mostVisiblePage);
    }

    async function renderTextLayerForPage(page, textLayer, viewport, pageNum) {
      unregisterTextLayerForSelection(textLayer);
      invalidatePageGeometry(pageNum);
      textLayer.innerHTML = "";
      textLayer.style.setProperty('--scale-factor', String(viewport.scale));
      try {
        const textContent = await page.getTextContent();
        const textRenderTask = window.pdfjsLib.renderTextLayer({
          textContentSource: textContent,
          container: textLayer,
          viewport: viewport,
          textDivs: []
        });
        await textRenderTask.promise;

        const endOfContent = document.createElement("div");
        endOfContent.className = "endOfContent";
        textLayer.appendChild(endOfContent);

        registerTextLayerForSelection(textLayer, endOfContent);

        drawPageHighlightsAndNotes(pageNum);
        if (pdfSearchQuery) {
          drawPageSearchHighlights(pageNum);
        }
      } catch (tErr) {
        if (tErr?.name === 'RenderingCancelledException') return;
        console.warn("Text layer render failed:", pageNum, tErr);
      }
    }

    async function renderPdfPageVirtual(pageNum) {
      if (!pdfDoc || !pageNum || Number.isNaN(pageNum) || pageNum < 1 || pageNum > pdfPageCount) return;
      if (pdfRenderedPages[pageNum] === 'done' || pdfRenderedPages[pageNum] === 'rendering') return;
      
      pdfRenderedPages[pageNum] = 'rendering';
      
      if (pdfRenderTasks[pageNum]) {
        try { pdfRenderTasks[pageNum].cancel(); } catch (_) { /* sessiz iptal */ }
        delete pdfRenderTasks[pageNum];
      }
      
      try {
        const page = await pdfDoc.getPage(pageNum);
        const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
        const existingCanvas = document.getElementById(`pdf-render-canvas-${pageNum}`);
        const textLayer = document.getElementById(`textLayer-${pageNum}`);
        const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
        const viewport = page.getViewport({ scale: pdfScale });
        
        if (wrapper) {
          wrapper.style.width = viewport.width + 'px';
          wrapper.style.height = viewport.height + 'px';
          wrapper.style.setProperty('--scale-factor', String(viewport.scale));
        }

        // Çift tamponlama (double-buffering): Eski canvas render bitene kadar yerinde kalır, beyaz flaş engellenir
        if (existingCanvas) {
          existingCanvas.style.width = viewport.width + 'px';
          existingCanvas.style.height = viewport.height + 'px';
        }
        
        const dpr = Math.min(window.devicePixelRatio || 1, 2.5); // Retina netliği & bellek tavanı
        const newCanvas = document.createElement('canvas');
        newCanvas.className = 'pdf-page-canvas';
        newCanvas.width = Math.floor(viewport.width * dpr);
        newCanvas.height = Math.floor(viewport.height * dpr);
        newCanvas.style.width = viewport.width + 'px';
        newCanvas.style.height = viewport.height + 'px';
        
        const ctx = newCanvas.getContext('2d');
        
        if (textLayer) {
          textLayer.style.width = viewport.width + 'px';
          textLayer.style.height = viewport.height + 'px';
          textLayer.style.setProperty('--scale-factor', String(viewport.scale));
        }
        if (highlightLayer) {
          highlightLayer.style.width = viewport.width + 'px';
          highlightLayer.style.height = viewport.height + 'px';
        }
        
        const renderContext = {
          canvasContext: ctx,
          viewport: viewport,
          transform: dpr !== 1 ? [dpr, 0, 0, dpr, 0, 0] : null
        };
        
        const renderTask = page.render(renderContext);
        pdfRenderTasks[pageNum] = renderTask;
        
        await renderTask.promise;
        delete pdfRenderTasks[pageNum];
        pdfRenderedPages[pageNum] = 'done';
        applyChromaGuard(newCanvas, currentReaderSurfaceMode);
        
        // requestAnimationFrame ile atomik ve flaşsız canvas değişimi
        requestAnimationFrame(() => {
          newCanvas.id = `pdf-render-canvas-${pageNum}`;
          if (existingCanvas && existingCanvas.parentNode) {
            existingCanvas.parentNode.replaceChild(newCanvas, existingCanvas);
          } else if (wrapper) {
            wrapper.insertBefore(newCanvas, wrapper.firstChild);
          }
        });
        
        if (textLayer) {
          await renderTextLayerForPage(page, textLayer, viewport, pageNum);
        }
      } catch (err) {
        delete pdfRenderTasks[pageNum];
        if (err?.name === 'RenderingCancelledException') {
          return;
        }
        console.warn("Virtual page render failed:", pageNum, err);
        delete pdfRenderedPages[pageNum];
      }
    }

    // Scroll container layout resizing on zoom/width change
    function resizeAllPagesForZoom() {
      if (!pdfDoc) return;
      
      // Cancel active renders so canvases can resize cleanly
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};
      
      const targetPage = (!Number.isNaN(pdfPageNum) && pdfPageNum >= 1) ? pdfPageNum : 1;
      
      pdfDoc.getPage(targetPage).then(function(samplePage) {
        let viewport = samplePage.getViewport({ scale: 1.0 });
        const container = document.getElementById('pdf-canvas-container');
        if (!container) return;
        
        if (pdfIsFitWidth) {
          const containerWidth = Math.max(300, container.clientWidth - 48);
          pdfScale = Math.max(0.3, Math.min(4.0, containerWidth / viewport.width));
          updateZoomLabel();
        } else if (pdfIsFitHeight) {
          const containerHeight = Math.max(300, container.clientHeight - 80);
          pdfScale = Math.max(0.3, Math.min(4.0, containerHeight / viewport.height));
          updateZoomLabel();
        }
        
        viewport = samplePage.getViewport({ scale: pdfScale });
        pdfRenderedPages = {}; // reset render states to force redraw on scroll check
        invalidatePageGeometry();
        
        for (let p = 1; p <= pdfPageCount; p++) {
          const wrapper = document.getElementById(`pdf-page-wrapper-${p}`);
          if (wrapper) {
            wrapper.style.width = viewport.width + 'px';
            wrapper.style.height = viewport.height + 'px';
            
            // Mevcut canvas'ı hemen silme, yeni boyuta göre CSS ile ölçeklendir (beyaz boşluğu önle)
            const existingCanvas = document.getElementById(`pdf-render-canvas-${p}`);
            if (existingCanvas) {
              existingCanvas.style.width = viewport.width + 'px';
              existingCanvas.style.height = viewport.height + 'px';
            }
            
            const textLayer = document.getElementById(`textLayer-${p}`);
            if (textLayer) {
              textLayer.style.width = viewport.width + 'px';
              textLayer.style.height = viewport.height + 'px';
              textLayer.style.setProperty('--scale-factor', String(pdfScale));
              unregisterTextLayerForSelection(textLayer);
              textLayer.innerHTML = "";
            }
            
            const highlightLayer = document.getElementById(`pdf-highlight-layer-${p}`);
            if (highlightLayer) {
              highlightLayer.style.width = viewport.width + 'px';
              highlightLayer.style.height = viewport.height + 'px';
              highlightLayer.innerHTML = "";
            }
          }
        }
        
        // Render target initial page immediately and keep scroll aligned
        void renderPdfPageVirtual(targetPage);
        scrollToPage(targetPage);
        
        setTimeout(() => {
          checkVisiblePagesAndRender();
        }, 120);
      }).catch(function(err) {
        console.warn("resizeAllPagesForZoom getPage failed:", err);
      });
    }

    function scrollToPage(pageNum) {
      if (pageNum < 1 || pageNum > pdfPageCount) return;
      const container = document.getElementById('pdf-canvas-container');
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper && container) {
        const row = wrapper.closest('.pdf-spread-row');
        const targetTop = row ? (row.offsetTop - 16) : (wrapper.offsetTop - 16);
        container.scrollTo({ top: Math.max(0, targetTop), behavior: 'smooth' });
      } else if (wrapper) {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    function pdfPrevPage() {
      if (pdfPageNum <= 1) return;
      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        if (pdfPageNum <= 3) {
          scrollToPage(1);
        } else {
          const target = (pdfPageNum % 2 === 0) ? (pdfPageNum - 2) : (pdfPageNum - 3);
          scrollToPage(Math.max(1, target));
        }
      } else {
        scrollToPage(pdfPageNum - 1);
      }
      hideFloatingBar();
    }

    function pdfNextPage() {
      if (pdfPageNum >= pdfPageCount) return;
      if (pdfIsSpreadMode && window.innerWidth >= 800) {
        if (pdfPageNum === 1) {
          scrollToPage(Math.min(pdfPageCount, 2));
        } else {
          const target = (pdfPageNum % 2 === 0) ? (pdfPageNum + 2) : (pdfPageNum + 1);
          scrollToPage(Math.min(pdfPageCount, target));
        }
      } else {
        scrollToPage(pdfPageNum + 1);
      }
      hideFloatingBar();
    }

    function pdfGoToPageFromInput() {
      const input = document.getElementById('pdf-page-num');
      let val = Number.parseInt(input.value, 10);
      if (Number.isNaN(val) || val < 1) val = 1;
      if (val > pdfPageCount) val = pdfPageCount;
      scrollToPage(val);
      hideFloatingBar();
    }

    // Zoom Controls & Hardware Acceleration State
    let zoomWillChangeTimer = null;
    function markZoomActive() {
      const container = document.getElementById('pdf-canvas-container');
      if (container) {
        container.classList.add('is-zooming');
      }
      if (zoomWillChangeTimer) clearTimeout(zoomWillChangeTimer);
      zoomWillChangeTimer = setTimeout(() => {
        const c = document.getElementById('pdf-canvas-container');
        if (c) c.classList.remove('is-zooming');
      }, 300);
    }

    function updateZoomLabel() {
      const pct = Math.round(pdfScale * 100);
      document.getElementById('pdf-zoom-percent').textContent = pct + "%";
    }

    function pdfZoomIn() {
      markZoomActive();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');
      pdfScale += 0.15;
      if (pdfScale > 4.0) pdfScale = 4.0;
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfZoomOut() {
      markZoomActive();
      pdfIsFitWidth = false;
      pdfIsFitHeight = false;
      document.getElementById('pdf-fit-width-btn')?.classList.remove('active');
      document.getElementById('pdf-fit-height-btn')?.classList.remove('active');
      pdfScale -= 0.15;
      if (pdfScale < 0.5) pdfScale = 0.5;
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfFitWidth() {
      markZoomActive();
      const btn = document.getElementById('pdf-fit-width-btn');
      const otherBtn = document.getElementById('pdf-fit-height-btn');
      if (pdfIsFitWidth) {
        pdfIsFitWidth = false;
        btn?.classList.remove('active');
        pdfScale = 1.2;
      } else {
        pdfIsFitWidth = true;
        pdfIsFitHeight = false;
        btn?.classList.add('active');
        otherBtn?.classList.remove('active');
      }
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    function pdfFitHeight() {
      markZoomActive();
      const btn = document.getElementById('pdf-fit-height-btn');
      const otherBtn = document.getElementById('pdf-fit-width-btn');
      if (pdfIsFitHeight) {
        pdfIsFitHeight = false;
        btn?.classList.remove('active');
        pdfScale = 1.2;
      } else {
        pdfIsFitHeight = true;
        pdfIsFitWidth = false;
        btn?.classList.add('active');
        otherBtn?.classList.remove('active');
      }
      updateZoomLabel();
      resizeAllPagesForZoom();
      hideFloatingBar();
    }

    // Ctrl + Mouse Wheel ile pürüzsüz zoom desteği
    document.addEventListener('wheel', function(e) {
      if (!e.ctrlKey) return;
      const container = document.getElementById('pdf-canvas-container');
      if (!container || !container.contains(e.target)) return;
      e.preventDefault();
      if (e.deltaY < 0) {
        pdfZoomIn();
      } else {
        pdfZoomOut();
      }
    }, { passive: false });

    // Toggle Notes Sidebar on left
    function toggleNotesSidebar() {
      const sidebar = document.getElementById('pdf-notes-sidebar');
      const btn = document.getElementById('pdf-notes-sidebar-btn');
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        btn.classList.remove('active');
      } else {
        sidebar.classList.add('open');
        btn.classList.add('active');
        renderNotesSidebar();
      }
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

      const rect = range.getBoundingClientRect();
      const viewerRect = document.getElementById('custom-pdf-viewer').getBoundingClientRect();
      const floatingBar = document.getElementById('pdf-floating-bar');
      
      const barLeft = rect.left - viewerRect.left + (rect.width / 2) - 100;
      const barTop = rect.top - viewerRect.top - 48;
      
      floatingBar.style.left = Math.max(10, Math.min(barLeft, viewerRect.width - 210)) + 'px';
      floatingBar.style.top = Math.max(10, barTop) + 'px';
      floatingBar.classList.add('active');

      pdfSelectedText = text;
      pdfSelectionRanges = getSelectionCoordsRelativeToPage(range);
    }

    // Handle Text Selection for highlights & floating bar positioning
    function handleTextSelection() {
      setTimeout(() => {
        const selection = window.getSelection();
        const text = selection.toString().trim();
        if (text.length === 0) {
          hideFloatingBar();
          return;
        }

        const range = selection.getRangeAt(0);
        const container = document.getElementById('pdf-canvas-container');
        if (!container.contains(range.commonAncestorContainer)) {
          hideFloatingBar();
          return;
        }

        const pageWrapper = getPageWrapperFromRange(range);
        if (!pageWrapper) {
          hideFloatingBar();
          return;
        }

        updateFloatingBarPosition(range, text, pageWrapper);
      }, 50);
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

    function extractCharRectsFromNode(node, range) {
      const textContent = node.textContent;
      let start = (node === range.startContainer) ? range.startOffset : 0;
      let end = (node === range.endContainer) ? range.endOffset : textContent.length;
      
      while (start < end && /\s/.test(textContent.charAt(start))) {
        start++;
      }
      while (end > start && /\s/.test(textContent.charAt(end - 1))) {
        end--;
      }
      if (start >= end) return [];

      const charRects = [];
      const tempRange = document.createRange();
      for (let idx = start; idx < end; idx++) {
        if (/\s/.test(textContent.charAt(idx))) continue;
        try {
          tempRange.setStart(node, idx);
          tempRange.setEnd(node, idx + 1);
          const rect = tempRange.getBoundingClientRect();
          if (rect.width > 0 && rect.height > 0) {
            charRects.push({
              left: rect.left,
              right: rect.right,
              top: rect.top,
              bottom: rect.bottom,
              width: rect.width,
              height: rect.height
            });
          }
        } catch (_) {
          // Range sınır toleransı
        }
      }
      return charRects;
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

    // Normalize coordinates relative to page wrapper bounding box with character precision
    function getSelectionCoordsRelativeToPage(range) {
      const startNode = range.commonAncestorContainer;
      const pageWrapper = startNode.nodeType === Node.TEXT_NODE ? 
                          startNode.parentNode.closest('.pdf-page-wrapper') : 
                          startNode.closest('.pdf-page-wrapper');
      
      if (!pageWrapper) return [];
      const wrapperRect = pageWrapper.getBoundingClientRect();
      const root = startNode.nodeType === Node.TEXT_NODE ? startNode.parentNode : startNode;
      const textNodes = collectTextNodesFromRange(range, root);

      if (textNodes.length === 0 && startNode.nodeType === Node.TEXT_NODE && startNode.textContent.trim().length > 0) {
        textNodes.push(startNode);
      }

      const coords = [];
      textNodes.forEach(node => {
        const charRects = extractCharRectsFromNode(node, range);
        if (charRects.length === 0) return;

        const lines = groupCharRectsIntoLines(charRects);
        lines.forEach(line => {
          const w = line.right - line.left;
          if (w < 1.5 || line.height < 1.5) return;
          coords.push({
            left: (line.left - wrapperRect.left) / wrapperRect.width,
            top: (line.top - wrapperRect.top) / wrapperRect.height,
            width: w / wrapperRect.width,
            height: line.height / wrapperRect.height
          });
        });
      });

      // Fallback
      if (coords.length === 0) {
        const rects = range.getClientRects();
        for (const r of rects) {
          if (r.width < 1.5 || r.height < 1.5) continue;
          coords.push({
            left: (r.left - wrapperRect.left) / wrapperRect.width,
            top: (r.top - wrapperRect.top) / wrapperRect.height,
            width: r.width / wrapperRect.width,
            height: r.height / wrapperRect.height
          });
        }
      }
      return coords;
    }

    function generateHighlightId() {
      if (typeof crypto !== 'undefined') {
        if (typeof crypto.randomUUID === 'function') {
          return `hl_${crypto.randomUUID()}`;
        }
        if (crypto.getRandomValues) {
          const arr = new Uint32Array(1);
          crypto.getRandomValues(arr);
          return `hl_${Date.now()}_${arr[0].toString(36)}`;
        }
      }
      return `hl_${Date.now()}_${Date.now().toString(36)}`;
    }

    // Apply Highlighter action
    function applyHighlight(colorHex, colorClass) {
      if (!activeWorkspaceBook || !pdfSelectedText || pdfSelectionRanges.length === 0) return;

      const hlId = generateHighlightId();
      
      if (!pdfHighlights[pdfPageNum]) {
        pdfHighlights[pdfPageNum] = [];
      }

      pdfHighlights[pdfPageNum].push({
        id: hlId,
        text: pdfSelectedText,
        colorClass: colorClass,
        colorHex: colorHex,
        coords: pdfSelectionRanges
      });

      // Save and Draw immediately
      saveAnnotations();
      drawPageHighlightsAndNotes(pdfPageNum);
      renderNotesSidebar();
      clearSelection();
    }

    // Sticky Note Modals Functions
    function openNoteModalForSelection() {
      if (!pdfSelectedText) return;
      
      pdfActiveHighlightIdForNote = generateHighlightId();
      
      // Default to yellow for new selections
      selectModalNoteColor('#e8dca0', 'yellow');
      
      // Populate previews
      document.getElementById('pdf-selected-text-preview').textContent = `"${pdfSelectedText}"`;
      document.getElementById('pdf-note-textarea').value = "";
      
      // Show Modal
      const noteModal = document.getElementById('pdf-note-modal');
      if (noteModal) {
        noteModal.classList.remove('closing');
        noteModal.classList.add('open');
      }
      document.body.classList.add('modal-open');
      setTimeout(() => document.getElementById('pdf-note-textarea')?.focus(), 150);
    }

    function closePdfNoteModalDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('pdf-note-modal', () => {
          pdfActiveHighlightIdForNote = null;
          clearSelection();
        });
      } else {
        document.getElementById('pdf-note-modal')?.classList.remove('open');
        document.body.classList.remove('modal-open');
        pdfActiveHighlightIdForNote = null;
        clearSelection();
      }
    }

    function closePdfNoteModal(e) {
      if (e.target.id === 'pdf-note-modal') {
        closePdfNoteModalDirect();
      }
    }

    function savePdfNote() {
      const textarea = document.getElementById('pdf-note-textarea');
      const noteText = textarea ? textarea.value.trim() : "";

      if (!pdfHighlights[pdfPageNum]) pdfHighlights[pdfPageNum] = [];

      let existingHighlight = pdfHighlights[pdfPageNum].find(h => h.id === pdfActiveHighlightIdForNote);

      if (!noteText && !existingHighlight) {
        closePdfNoteModalDirect();
        return;
      }

      if (existingHighlight) {
        // Update color and text if edited
        existingHighlight.colorClass = pdfActiveNoteColorClass;
        existingHighlight.colorHex = pdfActiveNoteColorHex;
      } else {
        // Create new highlight automatically if applying note from selection
        pdfHighlights[pdfPageNum].push({
          id: pdfActiveHighlightIdForNote,
          text: pdfSelectedText,
          colorClass: pdfActiveNoteColorClass,
          colorHex: pdfActiveNoteColorHex,
          coords: pdfSelectionRanges
        });
      }

      // Store note text mapped to highlight (or remove if emptied)
      if (noteText) {
        pdfNotes[pdfActiveHighlightIdForNote] = noteText;
      } else if (existingHighlight) {
        delete pdfNotes[pdfActiveHighlightIdForNote];
      }

      // Persist and Sync
      saveAnnotations();
      drawPageHighlightsAndNotes(pdfPageNum);
      renderNotesSidebar();
      closePdfNoteModalDirect();
    }

    // Persist to local storage and sync to backend DB
    function saveAnnotations() {
      if (!activeWorkspaceBook) return;
      try {
        localStorage.setItem(`lib-highlights-${activeWorkspaceBook.hash}`, JSON.stringify(pdfHighlights));
        localStorage.setItem(`lib-notes-${activeWorkspaceBook.hash}`, JSON.stringify(pdfNotes));
      } catch (e) {
        console.error("Local storage kaydetme hatası:", e);
      }

      // Sync to SQLite backend API
      const batchList = [];
      Object.keys(pdfHighlights).forEach(pStr => {
        const pNum = Number(pStr);
        (pdfHighlights[pNum] || []).forEach(hl => {
          batchList.push({
            id: hl.id,
            sayfa_no: pNum,
            secilen_metin: hl.text || '',
            not_metni: pdfNotes[hl.id] || '',
            renk_hex: hl.colorHex || '#e8dca0',
            renk_sinif: hl.colorClass || 'yellow',
            koordinatlar: JSON.stringify(hl.coords || [])
          });
        });
      });

      apiFetch(`/api/books/${activeWorkspaceBook.hash}/annotations/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ annotations: batchList })
      }).catch(err => console.warn("Not senkronizasyonu hatası:", err));
    }

    // Render Highlights & Notes overlays absolute coords relative to wrapper width/height
    function drawPageHighlightsAndNotes(pageNum) {
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
      if (!highlightLayer) return;
      highlightLayer.innerHTML = "";

      const pageHls = pdfHighlights[pageNum] || [];
      pageHls.forEach(function(hl) {
        // Draw highlight overlay divs
        hl.coords.forEach(function(coord) {
          const div = document.createElement('div');
          div.className = `rendered-highlight ${hl.colorClass}`;
          div.style.left = (coord.left * 100) + "%";
          div.style.top = (coord.top * 100) + "%";
          div.style.width = (coord.width * 100) + "%";
          div.style.height = (coord.height * 100) + "%";
          div.dataset.hlId = hl.id;
          highlightLayer.appendChild(div);
        });

        // Draw Margin Sticky Note marker if note exists
        if (pdfNotes[hl.id]) {
          const firstCoord = hl.coords[0];
          const pin = document.createElement('div');
          pin.className = 'sticky-note-marker';
          pin.innerHTML = '<i class="fas fa-sticky-note"></i>';
          pin.style.left = "8px"; // place neatly in left margin
          pin.style.top = (firstCoord.top * 100) + "%";
          pin.title = pdfNotes[hl.id];
          pin.onclick = function() {
            // Edit existing note
            editExistingNote(hl.id, hl.text, pdfNotes[hl.id], pageNum);
          };
          highlightLayer.appendChild(pin);
        }
      });
    }

    // Edit note modal trigger
    function editExistingNote(hlId, quote, currentNote, pageNum) {
      pdfActiveHighlightIdForNote = hlId;
      pdfPageNum = pageNum; // sync page context
      
      let hl = null;
      if (pdfHighlights[pageNum]) {
        hl = pdfHighlights[pageNum].find(h => h.id === hlId);
      }
      const activeColorHex = hl ? hl.colorHex : '#e8dca0';
      const activeColorClass = hl ? hl.colorClass : 'yellow';
      selectModalNoteColor(activeColorHex, activeColorClass);
      
      document.getElementById('pdf-selected-text-preview').textContent = `"${quote}"`;
      document.getElementById('pdf-note-textarea').value = currentNote;
      document.getElementById('pdf-note-modal').classList.add('open');
      document.body.classList.add('modal-open');
      document.body.classList.add('modal-open');
      setTimeout(() => document.getElementById('pdf-note-textarea').focus(), 150);
    }

    // Annotation Sidebar populating & interactive jump-to-page trigger
    function renderNotesSidebar() {
      const list = document.getElementById('pdf-notes-list');
      list.innerHTML = "";

      let totalCount = 0;
      
      // Sort pages numerically
      const pages = Object.keys(pdfHighlights).map(Number).sort((a,b) => a-b);
      
      pages.forEach(function(pNum) {
        const pageHls = pdfHighlights[pNum] || [];
        pageHls.forEach(function(hl) {
          totalCount++;
          const hasNote = !!pdfNotes[hl.id];
          
          const div = document.createElement('div');
          div.className = 'pdf-note-item';
          div.onclick = function() {
            jumpToHighlight(pNum, hl.id);
          };

          let noteHtml = "";
          if (hasNote) {
            noteHtml = `<div class="pdf-note-item-text"><i class="fas fa-comment-dots" style="color: var(--accent); margin-right: 0.3rem;"></i> ${esc(pdfNotes[hl.id])}</div>`;
          }

          div.innerHTML = `
            <div class="pdf-note-item-meta">
              <span class="pdf-note-item-page">Sayfa ${pNum}</span>
              <span style="font-size: 0.65rem; opacity: 0.7;">${hasNote ? 'Notlu' : 'İşaretleme'}</span>
            </div>
            <div class="pdf-note-item-quote ${hl.colorClass}">${esc(hl.text)}</div>
            ${noteHtml}
            <div class="pdf-note-item-actions">
              <button class="pdf-note-item-btn btn-edit-note" title="Notu / Alıntıyı Düzenle"><i class="fas fa-edit"></i></button>
              <button class="pdf-note-item-btn delete btn-delete-note" title="Sil"><i class="fas fa-trash-alt"></i></button>
            </div>
          `;
          const editBtn = div.querySelector('.btn-edit-note');
          if (editBtn) {
            editBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              editExistingNote(hl.id, hl.text, pdfNotes[hl.id] || '', pNum);
            });
          }
          const delBtn = div.querySelector('.btn-delete-note');
          if (delBtn) {
            delBtn.addEventListener('click', (e) => {
              e.stopPropagation();
              deleteHighlight(pNum, hl.id);
            });
          }
          list.appendChild(div);
        });
      });

      if (totalCount === 0) {
        list.innerHTML = `<div class="pdf-notes-empty">Bu kitapta henüz hiç işaretleme yapmadınız. Sayfa üzerinde metin seçerek fosforlu kalemle çizebilir veya not alabilirsiniz.</div>`;
      }
    }

    // Jump immediately to specific page and scroll to highlight element
    function jumpToHighlight(pageNum, hlId) {
      pdfPageNum = pageNum;
      document.getElementById('pdf-page-num').value = pageNum;
      
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper) {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Pulse highlighting effect
        setTimeout(() => {
          const highlightEl = document.querySelector(`[data-hl-id="${hlId}"]`);
          if (highlightEl) {
            highlightEl.style.opacity = "0.9";
            setTimeout(() => highlightEl.style.opacity = "", 1500);
          }
        }, 350);
      }
    }

    // Delete Highlight and associated Note
    function deleteHighlight(pageNum, hlId) {
      if (!pdfHighlights[pageNum]) return;
      
      // Filter out
      pdfHighlights[pageNum] = pdfHighlights[pageNum].filter(h => h.id !== hlId);
      if (pdfHighlights[pageNum].length === 0) {
        delete pdfHighlights[pageNum];
      }
      
      // Delete associated note
      if (pdfNotes[hlId]) {
        delete pdfNotes[hlId];
      }

      if (activeWorkspaceBook) {
        apiFetch(`/api/books/${activeWorkspaceBook.hash}/annotations/${hlId}`, {
          method: 'DELETE'
        }).catch(err => console.warn("Not silinirken API hatası:", err));
      }

      try {
        localStorage.setItem(`lib-highlights-${activeWorkspaceBook.hash}`, JSON.stringify(pdfHighlights));
        localStorage.setItem(`lib-notes-${activeWorkspaceBook.hash}`, JSON.stringify(pdfNotes));
      } catch (e) {
        console.error("Local storage silme güncellemesi hatası:", e);
      }

      drawPageHighlightsAndNotes(pageNum);
      renderNotesSidebar();
    }

    // 60FPS fluid virtual page rendering & progress tracking on scroll
    let scrollRaf = 0;
    function onPdfContainerScroll() {
      if (scrollRaf) return;
      scrollRaf = requestAnimationFrame(() => {
        scrollRaf = 0;
        checkVisiblePagesAndRender();
      });
    }

    // ═════════════════════════════════════════════════════════════
    // In-Document Fast PDF Search Engine (Ctrl + F & Live Highlights)
    // ═════════════════════════════════════════════════════════════
    let pdfSearchQuery = "";
    let pdfSearchResults = []; // Array of { pageNum, matchIndex, snippet }
    let pdfSearchCurrentMatchIdx = -1;
    let pdfSearchPageMatchesCount = {}; // pageNum -> count
    let pdfSearchTextCache = {}; // pageNum -> { text: string, textLower: string }
    let isPdfSearchOpen = false;
    let isPdfSearchDrawerOpen = false;
    let pdfSearchDebounceTimer = null;
    let pdfSearchToken = 0; // Incremental cancellation token preventing search race conditions

    // Toggle search bar
    function togglePdfSearch(forceOpen) {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const input = document.getElementById('pdf-search-input');
      if (!searchBar) return;

      const shouldOpen = (forceOpen !== undefined) ? forceOpen : (searchBar.style.display === 'none' || !searchBar.style.display);
      if (shouldOpen) {
        searchBar.style.display = 'block';
        toggleBtn?.classList.add('active');
        isPdfSearchOpen = true;
        setTimeout(() => {
          input?.focus();
          input?.select();
        }, 50);
      } else {
        closePdfSearch();
      }
    }

    function closePdfSearch() {
      const searchBar = document.getElementById('pdf-search-bar');
      const toggleBtn = document.getElementById('pdf-search-btn');
      const drawer = document.getElementById('pdf-search-results-drawer');
      const listBtn = document.getElementById('pdf-search-list-btn');
      if (searchBar) searchBar.style.display = 'none';
      if (drawer) drawer.style.display = 'none';
      toggleBtn?.classList.remove('active');
      listBtn?.classList.remove('active');
      isPdfSearchOpen = false;
      isPdfSearchDrawerOpen = false;
      clearPdfSearch(true); // clear visual highlights
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
      drawer.style.display = isPdfSearchDrawerOpen ? 'block' : 'none';
      if (isPdfSearchDrawerOpen) {
        listBtn?.classList.add('active');
      } else {
        listBtn?.classList.remove('active');
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
        closePdfSearch();
      }
    }

    function collectMatchesForPage(p, pageData, query, normalizedQuery) {
      const textLower = pageData.textLower;
      let pos = 0;
      let pageMatchCount = 0;
      while ((pos = textLower.indexOf(normalizedQuery, pos)) !== -1) {
        const startSnippet = Math.max(0, pos - 35);
        const endSnippet = Math.min(pageData.text.length, pos + query.length + 35);
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

    // Iterative fast page scanner with token-based cancellation
    async function scanPagesIteratively(myToken, pageCount, query, normalizedQuery) {
      for (let p = 1; p <= pageCount; p++) {
        if (myToken !== pdfSearchToken) return false;

        let pageData = pdfSearchTextCache[p];
        if (!pageData) {
          try {
            const page = await pdfDoc.getPage(p);
            if (myToken !== pdfSearchToken) return false;
            const textContent = await page.getTextContent();
            if (myToken !== pdfSearchToken) return false;
            const textParts = textContent.items.map(item => item.str || "");
            const fullText = textParts.join(" ");
            pageData = {
              text: fullText,
              textLower: fullText.toLocaleLowerCase('tr-TR'),
              items: textContent.items
            };
            pdfSearchTextCache[p] = pageData;
          } catch (err) {
            console.warn("Sayfa metni taranamadı:", p, err);
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
      jumpToSearchResult(targetIdx, false);
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
      if (!pdfDoc || !query || query.length < 1) {
        clearPdfSearch(true);
        return;
      }

      const myToken = ++pdfSearchToken;
      pdfSearchQuery = query;
      const normalizedQuery = query.toLocaleLowerCase('tr-TR');
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

    // Jump to specific search match
    function jumpToSearchResult(idx, shouldScrollSmooth) {
      if (idx < 0 || idx >= pdfSearchResults.length) return;
      pdfSearchCurrentMatchIdx = idx;
      updateSearchNavState();

      const match = pdfSearchResults[idx];
      const targetPage = match.pageNum;

      // Scroll to target page
      scrollToPage(targetPage);

      // Draw highlights and activate specific match on target page
      setTimeout(() => {
        drawPageSearchHighlights(targetPage);
        
        // Highlight active marker
        const activeMarker = document.querySelector(`.pdf-search-highlight[data-match-idx="${idx}"]`);
        if (activeMarker) {
          document.querySelectorAll('.pdf-search-highlight.active').forEach(el => el.classList.remove('active'));
          activeMarker.classList.add('active');
          activeMarker.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 120);
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

    function highlightSearchMatchesInSpan(span, normalizedQuery, wrapperRect, pageMatches, state) {
      const text = span.textContent;
      const textLower = text.toLocaleLowerCase('tr-TR');
      let pos = 0;

      while ((pos = textLower.indexOf(normalizedQuery, pos)) !== -1) {
        try {
          const range = document.createRange();
          const textNode = span.firstChild || span;
          if (textNode?.nodeType === Node.TEXT_NODE && pos + pdfSearchQuery.length <= textNode.length) {
            range.setStart(textNode, pos);
            range.setEnd(textNode, pos + pdfSearchQuery.length);
            const rects = range.getClientRects();
            const globalIdx = (state.pointer < pageMatches.length) ? pageMatches[state.pointer].matchIndex : undefined;

            for (const rect of rects) {
              _appendSearchHighlightDiv(rect, wrapperRect, globalIdx, state.highlightLayer);
            }
          }
        } catch (_err) {
          // Range sınır toleransı
        }

        state.pointer++;
        pos += Math.max(1, normalizedQuery.length);
      }
    }

    // Draw visual yellow highlight rects for a given page
    function drawPageSearchHighlights(pageNum) {
      if (!pdfSearchQuery || !pdfSearchPageMatchesCount[pageNum]) return;

      const textLayer = document.getElementById(`textLayer-${pageNum}`);
      const highlightLayer = document.getElementById(`pdf-highlight-layer-${pageNum}`);
      const pageWrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (!textLayer || !highlightLayer || !pageWrapper) return;

      highlightLayer.querySelectorAll('.pdf-search-highlight').forEach(el => el.remove());

      const wrapperRect = pageWrapper.getBoundingClientRect();
      if (wrapperRect.width <= 0 || wrapperRect.height <= 0) return;

      const normalizedQuery = pdfSearchQuery.toLocaleLowerCase('tr-TR');
      const spans = textLayer.querySelectorAll('span:not(.markedContent)');
      const pageMatches = pdfSearchResults.filter(m => m.pageNum === pageNum);
      const state = { pointer: 0, highlightLayer };

      spans.forEach(span => {
        highlightSearchMatchesInSpan(span, normalizedQuery, wrapperRect, pageMatches, state);
      });
    }

    function drawAllVisibleSearchHighlights() {
      if (!pdfDoc || !pdfSearchQuery) return;
      for (let p = 1; p <= pdfPageCount; p++) {
        if (pdfRenderedPages[p] === 'done') {
          drawPageSearchHighlights(p);
        }
      }
    }

    // Global Keyboard Shortcut Listener for Workspace Reader (Ctrl+F, Space, Arrows)
    document.addEventListener('keydown', (e) => {
      const workspaceReader = document.getElementById('workspace-reader');
      const isReaderActive = workspaceReader && (workspaceReader.classList.contains('active') || workspaceReader.classList.contains('open'));

      if (!isReaderActive) return;

      if ((e.ctrlKey || e.metaKey) && (e.key === 'f' || e.key === 'F')) {
        e.preventDefault();
        togglePdfSearch(true);
        return;
      }

      // Guard against typing inside input, textarea or contenteditable
      const activeEl = document.activeElement;
      if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable)) {
        return;
      }

      // Spacebar smooth reading / page advance (Kindle style)
      if (e.key === ' ' || e.code === 'Space') {
        const container = document.getElementById('pdf-canvas-container');
        if (container) {
          e.preventDefault();
          const scrollDistance = container.clientHeight * 0.78;
          if (e.shiftKey) {
            container.scrollBy({ top: -scrollDistance, behavior: 'smooth' });
          } else {
            container.scrollBy({ top: scrollDistance, behavior: 'smooth' });
          }
        }
        return;
      }

      // Page Navigation with Arrow keys
      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault();
        pdfNextPage();
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        pdfPrevPage();
      }
    });

    // Handle window resize dynamically for spread layout
    let resizeSpreadTimer = null;
    window.addEventListener('resize', () => {
      if (resizeSpreadTimer) clearTimeout(resizeSpreadTimer);
      resizeSpreadTimer = setTimeout(() => {
        if (pdfDoc && pdfPageCount > 0 && pdfIsSpreadMode) {
          applySpreadLayout();
        }
      }, 200);
    });

    // Expose all PDF variables globally to window context for templates
    window.pdfPrevPage = pdfPrevPage;
    window.pdfNextPage = pdfNextPage;
    window.togglePdfSpreadMode = togglePdfSpreadMode;
    window.applySpreadLayout = applySpreadLayout;
    window.updateSpreadUI = updateSpreadUI;
    window.pdfGoToPageFromInput = pdfGoToPageFromInput;
    window.pdfZoomIn = pdfZoomIn;
    window.pdfZoomOut = pdfZoomOut;
    window.pdfFitWidth = pdfFitWidth;
    window.pdfFitHeight = pdfFitHeight;
    window.toggleNotesSidebar = toggleNotesSidebar;
    window.applyHighlight = applyHighlight;
    window.clearSelection = clearSelection;
    window.openNoteModalForSelection = openNoteModalForSelection;
    window.closePdfNoteModal = closePdfNoteModal;
    window.closePdfNoteModalDirect = closePdfNoteModalDirect;
    window.savePdfNote = savePdfNote;
    window.deleteHighlight = deleteHighlight;
    window.jumpToHighlight = jumpToHighlight;
    window.onPdfContainerScroll = onPdfContainerScroll;
    window.editExistingNote = editExistingNote;

    // Search Functions globally exposed
    window.togglePdfSearch = togglePdfSearch;
    window.closePdfSearch = closePdfSearch;
    window.clearPdfSearch = clearPdfSearch;
    window.pdfSearchNext = pdfSearchNext;
    window.pdfSearchPrev = pdfSearchPrev;
    window.onPdfSearchInput = onPdfSearchInput;
    window.onPdfSearchKeydown = onPdfSearchKeydown;
    window.togglePdfSearchResultsDrawer = togglePdfSearchResultsDrawer;
    window.jumpToSearchResult = jumpToSearchResult;

    // TOC & TTS Functions
    function toggleTocSidebar() {
      const sidebar = document.getElementById('pdf-toc-sidebar');
      const btn = document.getElementById('pdf-toc-sidebar-btn');
      const notesSidebar = document.getElementById('pdf-notes-sidebar');
      const notesBtn = document.getElementById('pdf-notes-sidebar-btn');
      if (!sidebar) return;

      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        if (btn) btn.classList.remove('active');
      } else {
        if (notesSidebar) {
          notesSidebar.classList.remove('open');
          if (notesBtn) notesBtn.classList.remove('active');
        }
        sidebar.classList.add('open');
        if (btn) btn.classList.add('active');
      }
    }
    window.toggleTocSidebar = toggleTocSidebar;

    async function fetchSynthesizedTocFallback(tocList) {
      try {
        if (activeWorkspaceBook?.hash) {
          const res = await apiFetch(`/api/books/${activeWorkspaceBook.hash}/toc`);
          if (res.ok) {
            const data = await res.json();
            if (data.items && data.items.length > 0) {
              renderSynthesizedToc(data.items);
              return true;
            }
          }
        }
      } catch (e) {
        console.debug('TOC fallback fetch warning:', e);
      }
      tocList.innerHTML = '<div class="pdf-notes-empty">Bu belgede yer imi veya içindekiler tablosu bulunamadı.</div>';
      return false;
    }

    async function loadPdfOutline(pdf) {
      const tocList = document.getElementById('pdf-toc-list');
      if (!tocList) return;
      try {
        const outline = await pdf.getOutline();
        if (!outline || outline.length === 0) {
          tocList.innerHTML = '<div style="padding:1rem; text-align:center; color:var(--muted); font-size:0.8rem;"><i class="fas fa-spinner fa-spin"></i> İçindekiler tablosu taranıyor...</div>';
          await fetchSynthesizedTocFallback(tocList);
          return;
        }
        tocList.innerHTML = '';
        
        function appendItems(items, level = 0) {
          for (const item of items) {
            const div = document.createElement('div');
            div.className = `pdf-toc-item level-${Math.min(level, 2)}`;
            div.innerHTML = `<span>${esc(item.title)}</span><i class="fas fa-chevron-right" style="font-size:0.65rem; opacity:0.4;"></i>`;
            
            div.addEventListener('click', async () => {
              try {
                let dest = item.dest;
                if (typeof dest === 'string') {
                  dest = await pdf.getDestination(dest);
                }
                if (dest && Array.isArray(dest)) {
                  const pageRef = dest[0];
                  const pageIdx = await pdf.getPageIndex(pageRef);
                  jumpToPdfPage(pageIdx + 1);
                }
              } catch (e) {
                console.error('TOC atlama hatası:', e);
              }
            });
            tocList.appendChild(div);
            if (item.items && item.items.length > 0) {
              appendItems(item.items, level + 1);
            }
          }
        }
        appendItems(outline, 0);
      } catch (err) {
        // İsteğe bağlı / sessiz hata toleransı: İçindekiler tablosu okunamadığında boş durum mesajı gösterilir
        console.debug('loadPdfOutline hatası:', err);
        tocList.innerHTML = '<div class="pdf-notes-empty">İçindekiler tablosu okunamadı.</div>';
      }
    }

    function togglePdfTTS() {
      if (!('speechSynthesis' in window)) {
        showToast('Tarayıcınız sesli okuma özelliğini (Web Speech API) desteklemiyor.', 'warning');
        return;
      }

      const btn = document.getElementById('pdf-tts-btn');

      if (window.speechSynthesis.speaking || isSpeaking) {
        window.speechSynthesis.cancel();
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
        showToast('Seslendirme durduruldu.', 'info', 1800);
        return;
      }

      const selection = window.getSelection().toString().trim();
      let textToSpeak = selection;

      if (!textToSpeak && pdfDoc) {
        const activeWrapper = document.getElementById(`pdf-page-wrapper-${pdfPageNum}`);
        if (activeWrapper) {
          textToSpeak = activeWrapper.querySelector('.textLayer')?.innerText?.trim() || '';
        }
      }

      if (!textToSpeak) {
        showToast('Seslendirilecek metin bulunamadı. Lütfen bir metin seçin veya sayfanın tam yüklenmesini bekleyin.', 'warning');
        return;
      }

      const utterance = new SpeechSynthesisUtterance(textToSpeak.slice(0, 3500));
      utterance.lang = 'tr-TR';
      utterance.rate = 1.0;

      utterance.onstart = () => {
        isSpeaking = true;
        if (btn) {
          btn.classList.add('active');
          btn.innerHTML = '<i class="fas fa-stop"></i> Durdur';
        }
        showToast(`Sayfa ${pdfPageNum} seslendiriliyor...`, 'info', 2500);
      };

      utterance.onend = () => {
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
      };

      utterance.onerror = () => {
        isSpeaking = false;
        if (btn) {
          btn.classList.remove('active');
          btn.innerHTML = '<i class="fas fa-volume-high"></i> Dinle';
        }
      };

      window.speechSynthesis.speak(utterance);
    }
    window.togglePdfTTS = togglePdfTTS;

    // Event Delegation for clicking on citation chips inside chat messages
    document.addEventListener('click', (e) => {
      const citeEl = e.target.closest('.chat-page-cite');
      if (citeEl) {
        e.preventDefault();
        const page = citeEl.dataset.jumpPage;
        if (page) {
          jumpToPdfPage(page);
        }
      }
    });

    // Expose functions globally to window context
    window.openWorkspace = openWorkspace;
    window.closeWorkspace = closeWorkspace;
    window.sendWorkspaceMessage = sendWorkspaceMessage;
    window.handleWorkspaceChatKey = handleWorkspaceChatKey;

    function toggleWorkspaceExportMenu() {
      const menu = document.getElementById('workspace-export-menu');
      if (!menu) return;
      menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    }
    window.toggleWorkspaceExportMenu = toggleWorkspaceExportMenu;

    function exportCurrentWorkspaceBook(format) {
      if (!activeWorkspaceBook?.hash) {
        if (typeof showToast === 'function') showToast('Dışa aktarılacak aktif kitap bulunamadı.', 'error');
        return;
      }
      const menu = document.getElementById('workspace-export-menu');
      if (menu) menu.style.display = 'none';
      window.open(`/api/books/${activeWorkspaceBook.hash}/export/${format}`, '_blank');
    }
    window.exportCurrentWorkspaceBook = exportCurrentWorkspaceBook;

    document.addEventListener('click', (e) => {
      const wrap = document.querySelector('.workspace-export-wrapper');
      const menu = document.getElementById('workspace-export-menu');
      if (menu && wrap && !wrap.contains(e.target)) {
        menu.style.display = 'none';
      }
    });

    // Dynamic Connection Status Monitor
    function updateConnectionStatus() {
      const badge = document.getElementById('workspace-status-badge');
      if (!badge) return;

      if (navigator.onLine) {
        badge.classList.remove('offline');
        badge.innerHTML = '<i class="fas fa-robot"></i> <span id="workspace-status-text">AI Asistan Bağlı</span>';
      } else {
        badge.classList.add('offline');
        badge.innerHTML = '<i class="fas fa-triangle-exclamation"></i> <span id="workspace-status-text">Bağlantı Yok</span>';
      }
    }

    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    document.addEventListener('DOMContentLoaded', updateConnectionStatus);

    // --- [7.3] Auto-Synthesized TOC Renderer ---
    function renderSynthesizedToc(items) {
      const tocList = document.getElementById('pdf-toc-list');
      if (!tocList) return;
      tocList.innerHTML = '';
      items.forEach(it => {
        const div = document.createElement('div');
        div.className = `pdf-toc-item level-${Math.min(it.level || 1, 2)}`;
        const srcBadge = it.source === 'auto_detected' ? '<span style="font-size:0.65rem; color:#b8862f; margin-left:4px;">(Otomatik)</span>' : '';
        div.innerHTML = `<span style="flex:1;">${esc(it.title)} ${srcBadge}</span><span style="font-size:0.75rem; color:var(--muted); font-family:var(--font-mono, monospace);">s. ${it.page_number}</span>`;
        div.addEventListener('click', () => {
          jumpToPdfPage(it.target_page || it.page_number);
        });
        tocList.appendChild(div);
      });
    }
    window.renderSynthesizedToc = renderSynthesizedToc;

    // --- [8.1] ChromaGuard™ Smart Surface & Image Preservation ---
    let currentReaderSurfaceMode = 'normal';
    try {
      currentReaderSurfaceMode = localStorage.getItem('pdf_reader_surface_mode') || 'normal';
    } catch (e) {}

    function applySepiaFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        data[i] = Math.min(255, (r * 0.393) + (g * 0.769) + (b * 0.189) + 20);
        data[i + 1] = Math.min(255, (r * 0.349) + (g * 0.686) + (b * 0.168) + 15);
        data[i + 2] = Math.min(255, (r * 0.272) + (g * 0.534) + (b * 0.131) + 10);
      }
    }

    function applyEinkFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const gray = (data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114);
        let val = gray;
        if (gray > 185) {
          val = 245;
        } else if (gray < 75) {
          val = 20;
        }
        data[i] = val;
        data[i + 1] = val;
        data[i + 2] = val;
      }
    }

    function applyChromaGuardFilter(data, len) {
      for (let i = 0; i < len; i += 4) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        const maxC = Math.max(r, g, b);
        const minC = Math.min(r, g, b);
        const chroma = maxC - minC;

        // Chroma guard check: If pixel has significant color (chroma > 28), PRESERVE original colors!
        if (chroma > 28) {
          continue;
        }

        // Low-chroma text/paper: Invert luminance onto dark OLED background (#181a20)
        const lum = (r * 0.299 + g * 0.587 + b * 0.114);
        const invLum = 225 - (lum * 0.78);
        data[i] = Math.max(22, Math.min(235, Math.round(invLum * 0.96)));
        data[i + 1] = Math.max(24, Math.min(235, Math.round(invLum * 0.98)));
        data[i + 2] = Math.max(28, Math.min(240, Math.round(invLum * 1.02)));
      }
    }

    function applyChromaGuard(canvas, mode) {
      // Sepia, e-ink and normal modes are handled via zero-cost GPU CSS filters on [data-surface-mode]
      if (!canvas || mode !== 'chromaguard') return;

      const runTransform = () => {
        try {
          const ctx = canvas.getContext('2d');
          if (!ctx) return;
          const w = canvas.width;
          const h = canvas.height;
          if (!w || !h) return;
          const imgData = ctx.getImageData(0, 0, w, h);
          applyChromaGuardFilter(imgData.data, imgData.data.length);
          ctx.putImageData(imgData, 0, 0);
        } catch (e) {
          console.debug('ChromaGuard pixel transform warning:', e);
        }
      };

      if (typeof window.requestIdleCallback === 'function') {
        window.requestIdleCallback(() => runTransform(), { timeout: 200 });
      } else {
        setTimeout(runTransform, 16);
      }
    }
    window.applyChromaGuard = applyChromaGuard;

    function setReaderSurfaceMode(mode) {
      const prevMode = currentReaderSurfaceMode;
      currentReaderSurfaceMode = mode;
      try {
        localStorage.setItem('pdf_reader_surface_mode', mode);
      } catch (e) {}

      const viewer = document.getElementById('custom-pdf-viewer');
      if (viewer) {
        viewer.dataset.surfaceMode = mode;
      }

      document.querySelectorAll('#reader-surface-group .surface-btn').forEach(btn => {
        btn.classList.toggle('active', btn.id === `btn-surface-${mode}`);
      });

      // Switching between normal, sepia and eink requires ZERO re-renders: GPU CSS filter handles it in 0ms!
      const requiresReRender = (prevMode === 'chromaguard' && mode !== 'chromaguard') || (mode === 'chromaguard');
      if (!requiresReRender) {
        return;
      }

      // Cancel ongoing render tasks and re-render only when entering/leaving ChromaGuard OLED mode
      Object.values(pdfRenderTasks).forEach(task => {
        try { task.cancel(); } catch (_) {}
      });
      pdfRenderTasks = {};

      // Clear render tracker and re-render visible canvases
      pdfRenderedPages = {};
      checkVisiblePagesAndRender();
    }
    window.setReaderSurfaceMode = setReaderSurfaceMode;

    // --- [6.4] Mobile Instant LAN Handoff (QR Code) ---
    let handoffCountdownTimer = null;

    async function openHandoffModal() {
      if (!activeWorkspaceBook) return;
      const modal = document.getElementById('handoff-modal');
      const qrContainer = document.getElementById('handoff-qr-container');
      const urlText = document.getElementById('handoff-url-text');
      const timerEl = document.getElementById('handoff-timer');
      if (!modal || !qrContainer) return;

      modal.classList.remove('closing');
      modal.style.display = 'flex';
      modal.classList.add('open');
      document.body.classList.add('modal-open');
      qrContainer.innerHTML = '<div style="padding:3rem 1rem; color:#888;"><i class="fas fa-spinner fa-spin"></i> QR Kod Üretiliyor...</div>';
      if (urlText) urlText.textContent = '';

      try {
        const res = await apiFetch('/api/auth/handoff-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_hash: activeWorkspaceBook.hash,
            page_number: pdfPageNum || 1,
          }),
        });

        if (!res.ok) {
          qrContainer.innerHTML = '<div style="color:var(--accent); padding:2rem 1rem;">QR kod üretilemedi.</div>';
          return;
        }

        const data = await res.json();
        qrContainer.innerHTML = data.qr_svg;
        if (urlText) urlText.innerHTML = `Bağlantı: <a href="${data.url}" target="_blank" style="color:var(--accent); text-decoration:none;">${data.url}</a>`;

        let remaining = data.expires_in_seconds || 120;
        if (handoffCountdownTimer) clearInterval(handoffCountdownTimer);
        handoffCountdownTimer = setInterval(() => {
          remaining -= 1;
          if (timerEl) timerEl.textContent = `Kod süresi: ${remaining} sn`;
          if (remaining <= 0) {
            clearInterval(handoffCountdownTimer);
            qrContainer.innerHTML = '<div style="color:var(--muted); padding:3rem 1rem;">QR kodun süresi doldu.<br><button class="btn-empty-add" onclick="openHandoffModal()" style="margin-top:0.8rem; font-size:0.8rem;">Yenile</button></div>';
          }
        }, 1000);
      } catch (err) {
        qrContainer.innerHTML = `<div style="color:var(--accent); padding:2rem 1rem;">Hata: ${esc(String(err))}</div>`;
      }
    }
    window.openHandoffModal = openHandoffModal;

    function closeHandoffModal() {
      if (handoffCountdownTimer) {
        clearInterval(handoffCountdownTimer);
        handoffCountdownTimer = null;
      }
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('handoff-modal');
      } else {
        const modal = document.getElementById('handoff-modal');
        if (modal) {
          modal.style.display = 'none';
          modal.classList.remove('open');
        }
        document.body.classList.remove('modal-open');
      }
    }
    window.closeHandoffModal = closeHandoffModal;

    // Direct page teleportation helper
    function openWorkspaceAtPage(bookOrHash, pageNum) {
      let book = bookOrHash;
      if (typeof bookOrHash === 'string') {
        if (typeof allBooks !== 'undefined' && Array.isArray(allBooks)) {
          book = allBooks.find(b => (b.hash || b.dosya_hash) === bookOrHash);
        }
        if (!book) {
          book = { hash: bookOrHash, title: 'Belge', category: 'PDF' };
        }
      }
      openWorkspace(book, pageNum);
      if (pageNum && pageNum > 0) {
        setTimeout(() => {
          jumpToPdfPage(pageNum);
        }, 600);
      }
    }
    window.openWorkspaceAtPage = openWorkspaceAtPage;

    // Listen for DPI changes (e.g. dragging between Retina & standard screens)
    if (typeof window !== 'undefined' && window.matchMedia) {
      const setupDprWatcher = () => {
        const dpr = window.devicePixelRatio || 1;
        const mq = window.matchMedia(`(resolution: ${dpr}dppx)`);
        mq.addEventListener('change', () => {
          if (pdfDoc && typeof isPdfOpen !== 'undefined' && isPdfOpen) {
            Object.keys(pdfRenderedPages).forEach(p => cleanupOffscreenPage(Number(p)));
            if (typeof checkVisiblePagesAndRender === 'function') checkVisiblePagesAndRender();
          }
          setupDprWatcher();
        }, { once: true });
      };
      setupDprWatcher();
    }

