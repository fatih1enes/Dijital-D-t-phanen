/* ════════════════════════════════════════════════════════════════════════════════
 * workspace_tts.js — Natural Turkish Studio Neural TTS & 60fps Karaoke Tracking
 * ════════════════════════════════════════════════════════════════════════════════ */

    const _ttsAudioCache = new Map();
    let _ttsAudioEl = null;
    let _ttsSentences = [];
    let _ttsSentenceIdx = 0;
    let _ttsActivePage = 1;
    let _ttsIsPaused = false;
    let _ttsSessionId = 0;
    let _ttsRafId = 0;
    let _ttsCurrentWords = [];
    let _ttsCurrentSpoken = '';
    let _ttsVoice = 'tr-TR-EmelNeural';
    let _ttsRate = 1.0;

    try {
      _ttsVoice = localStorage.getItem('kutuphane_tts_voice') || 'tr-TR-EmelNeural';
      _ttsRate = Number.parseFloat(localStorage.getItem('kutuphane_tts_rate') || '1.0') || 1.0;
    } catch (_e) {}

    function _localSplitSentencesFallback(rawText) {
      if (!rawText) return [];
      const cleaned = rawText
        .replace(/\u00ad/g, '')
        .replace(/([a-zçğıöşüA-ZÇĞİÖŞÜ]{2,})-\s*\n\s*([a-zçğıöşü]{2,})/g, '$1$2')
        .replace(/\s+/g, ' ')
        .trim();
      if (!cleaned) return [];
      const parts = cleaned.split(/(?<=[.!?…])\s+/);
      return parts.map(s => s.trim()).filter(s => s.length >= 2);
    }

    function _extractReadablePageText(pageNum) {
      if (isDocReaderMode && Array.isArray(docReaderPages) && docReaderPages[pageNum - 1]) {
        const pg = docReaderPages[pageNum - 1];
        const blocks = Array.isArray(pg.blocks) ? pg.blocks : [];
        return blocks.map(b => b.text || '').filter(Boolean).join('. ');
      }
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (wrapper) {
        const docBody = wrapper.querySelector('.doc-sheet-body');
        if (docBody) return docBody.innerText.trim();
        const tl = wrapper.querySelector('.textLayer');
        if (tl) {
          const spans = tl.querySelectorAll('span');
          if (spans.length > 0) {
            return Array.from(spans).map(sp => sp.textContent || '').join(' ').replace(/\s+/g, ' ').trim();
          }
          return tl.innerText.trim();
        }
      }
      if (pdfSearchTextCache && pdfSearchTextCache[pageNum]) {
        return String(pdfSearchTextCache[pageNum]).trim();
      }
      return '';
    }

    function _clearAllTtsKaraokeLayers() {
      document.querySelectorAll('.pdf-tts-layer').forEach(layer => {
        layer.innerHTML = '';
      });
      document.querySelectorAll('.doc-tts-active-block').forEach(el => {
        el.classList.remove('doc-tts-active-block');
      });
    }

    function _highlightSentenceOnPageDom(pageNum, sentenceText, activeWordText = '') {
      _clearAllTtsKaraokeLayers();
      const wrapper = document.getElementById(`pdf-page-wrapper-${pageNum}`);
      if (!wrapper || !sentenceText) return;

      if (isDocReaderMode) {
        const blocks = wrapper.querySelectorAll('.doc-sheet-body p, .doc-sheet-body h1, .doc-sheet-body h2, .doc-sheet-body h3, .doc-sheet-body blockquote');
        const probe = sentenceText.slice(0, 32).toLowerCase();
        for (const blk of blocks) {
          if ((blk.textContent || '').toLowerCase().includes(probe)) {
            blk.classList.add('doc-tts-active-block');
            break;
          }
        }
        return;
      }

      const ttsLayer = document.getElementById(`pdf-tts-layer-${pageNum}`);
      const textLayer = document.getElementById(`textLayer-${pageNum}`);
      if (!ttsLayer || !textLayer) return;

      const spans = Array.from(textLayer.querySelectorAll('span:not(.markedContent)'));
      if (spans.length === 0) return;

      const wrapRect = wrapper.getBoundingClientRect();
      if (wrapRect.width <= 0 || wrapRect.height <= 0) return;

      const cleanProbeWords = sentenceText
        .toLowerCase()
        .replace(/[^\p{L}\p{N}\s]/gu, ' ')
        .split(/\s+/)
        .filter(w => w.length >= 3)
        .slice(0, 6);

      const activeClean = activeWordText.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
      const frag = document.createDocumentFragment();
      let matchedSentenceSpans = 0;

      for (const sp of spans) {
        const spTxt = (sp.textContent || '').toLowerCase();
        if (!spTxt.trim()) continue;
        const isSentenceMatch = cleanProbeWords.length > 0 && cleanProbeWords.some(pw => spTxt.includes(pw));
        if (!isSentenceMatch && matchedSentenceSpans > 8) continue;

        if (isSentenceMatch) {
          matchedSentenceSpans++;
          const r = sp.getBoundingClientRect();
          if (r.width <= 0 || r.height <= 0) continue;
          const box = document.createElement('div');
          const isWordHit = activeClean.length >= 2 && spTxt.includes(activeClean);
          box.className = isWordHit ? 'tts-karaoke-word-box' : 'tts-karaoke-sentence-box';
          box.style.left = `${(r.left - wrapRect.left).toFixed(1)}px`;
          box.style.top = `${(r.top - wrapRect.top).toFixed(1)}px`;
          box.style.width = `${r.width.toFixed(1)}px`;
          box.style.height = `${r.height.toFixed(1)}px`;
          frag.appendChild(box);
        }
      }
      ttsLayer.appendChild(frag);
    }

    function _renderLiveKaraokeCaption(spokenText, words, currentMs) {
      const capEl = document.getElementById('tts-live-caption');
      if (!capEl) return;
      if (!Array.isArray(words) || words.length === 0) {
        capEl.textContent = spokenText || '';
        return;
      }

      let activeIdx = -1;
      for (let i = 0; i < words.length; i++) {
        if (currentMs >= words[i].start_ms && currentMs <= words[i].end_ms + 80) {
          activeIdx = i;
          break;
        }
        if (currentMs >= words[i].start_ms) {
          activeIdx = i;
        }
      }

      const htmlParts = words.map((w, idx) => {
        const safeW = esc(w.t || '');
        return idx === activeIdx
          ? `<mark class="tts-caption-word-active">${safeW}</mark>`
          : safeW;
      });
      capEl.innerHTML = htmlParts.join(' ');

      if (activeIdx >= 0 && words[activeIdx]?.t) {
        _highlightSentenceOnPageDom(_ttsActivePage, _ttsCurrentSpoken, words[activeIdx].t);
      }
    }

    function _startKaraokeRafLoop(mySession) {
      if (_ttsRafId) cancelAnimationFrame(_ttsRafId);
      const tick = () => {
        if (!isSpeaking || mySession !== _ttsSessionId || !_ttsAudioEl || _ttsIsPaused) {
          _ttsRafId = 0;
          return;
        }
        const curMs = (_ttsAudioEl.currentTime || 0) * 1000.0;
        _renderLiveKaraokeCaption(_ttsCurrentSpoken, _ttsCurrentWords, curMs);
        _ttsRafId = requestAnimationFrame(tick);
      };
      _ttsRafId = requestAnimationFrame(tick);
    }

    function _syncTtsButtonsUI() {
      const toolbarBtn = document.getElementById('pdf-tts-btn');
      const mobLabel = document.getElementById('mob-tts-label');
      const playerEl = document.getElementById('tts-mini-player');
      const playPauseBtn = document.getElementById('tts-play-pause-btn');
      const voiceSel = document.getElementById('tts-voice-select');
      const rateSel = document.getElementById('tts-rate-select');

      if (voiceSel && voiceSel.value !== _ttsVoice) voiceSel.value = _ttsVoice;
      if (rateSel && Number.parseFloat(rateSel.value) !== _ttsRate) rateSel.value = String(_ttsRate);

      if (isSpeaking) {
        if (toolbarBtn) {
          toolbarBtn.classList.add('active');
          toolbarBtn.innerHTML = '<i class="fas fa-stop"></i> <span class="pdf-btn-label">Durdur</span>';
        }
        if (mobLabel) mobLabel.textContent = 'Seslendirmeyi Durdur';
        if (playerEl) playerEl.style.display = 'flex';
        if (playPauseBtn) {
          playPauseBtn.innerHTML = _ttsIsPaused
            ? '<i class="fas fa-play"></i>'
            : '<i class="fas fa-pause"></i>';
        }
      } else {
        if (toolbarBtn) {
          toolbarBtn.classList.remove('active');
          toolbarBtn.innerHTML = '<i class="fas fa-volume-high"></i> <span class="pdf-btn-label">Dinle</span>';
        }
        if (mobLabel) mobLabel.textContent = 'Kitabı Sesli Dinle';
        if (playerEl) playerEl.style.display = 'none';
      }
    }

    async function _fetchSynthesizedSentence(sentenceText) {
      const key = `${_ttsVoice}|${_ttsRate}|${sentenceText}`;
      if (_ttsAudioCache.has(key)) {
        return _ttsAudioCache.get(key);
      }
      const p = apiFetch('/api/tts/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: sentenceText,
          voice: _ttsVoice,
          rate: _ttsRate
        })
      })
        .then(r => (r && r.ok) ? r.json() : { available: false })
        .catch(() => ({ available: false }));

      _ttsAudioCache.set(key, p);
      if (_ttsAudioCache.size > 40) {
        const oldest = _ttsAudioCache.keys().next().value;
        _ttsAudioCache.delete(oldest);
      }
      return p;
    }

    async function _loadSentencesForPage(pageNum, explicitText = '') {
      let rawText = explicitText || _extractReadablePageText(pageNum);
      if (!rawText && pdfDoc && pageNum >= 1 && pageNum <= pdfPageCount) {
        await renderPdfPageVirtual(pageNum);
        rawText = _extractReadablePageText(pageNum);
      }
      if (!rawText) return [];
      try {
        const res = await apiFetch('/api/tts/split-sentences', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: rawText.slice(0, 25000) })
        });
        if (res?.ok) {
          const data = await res.json();
          if (Array.isArray(data?.sentences) && data.sentences.length > 0) {
            return data.sentences;
          }
        }
      } catch (_e) {}
      return _localSplitSentencesFallback(rawText);
    }

    function _playBrowserSpeechFallback(sentenceText, mySession) {
      if (!('speechSynthesis' in window)) {
        stopNeuralTTS();
        return;
      }
      const badge = document.getElementById('tts-engine-badge');
      if (badge) badge.textContent = 'Tarayıcı Ses';
      const cap = document.getElementById('tts-live-caption');
      if (cap) cap.textContent = sentenceText;
      _highlightSentenceOnPageDom(_ttsActivePage, sentenceText);

      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(sentenceText);
      utt.lang = _ttsVoice.startsWith('en-') ? 'en-US' : 'tr-TR';
      utt.rate = _ttsRate;
      utt.onend = () => {
        if (mySession !== _ttsSessionId || !isSpeaking || _ttsIsPaused) return;
        void _advanceToNextSentence(mySession);
      };
      utt.onerror = () => {
        if (mySession === _ttsSessionId) stopNeuralTTS();
      };
      window.speechSynthesis.speak(utt);
    }

    async function _playCurrentSentence(mySession) {
      if (!isSpeaking || mySession !== _ttsSessionId) return;
      if (_ttsSentenceIdx < 0 || _ttsSentenceIdx >= _ttsSentences.length) {
        stopNeuralTTS();
        return;
      }

      const sentence = _ttsSentences[_ttsSentenceIdx];
      _ttsCurrentSpoken = sentence;
      _ttsCurrentWords = [];
      const capEl = document.getElementById('tts-live-caption');
      if (capEl) capEl.textContent = sentence;
      _highlightSentenceOnPageDom(_ttsActivePage, sentence);

      // Lookahead pre-fetch next sentence (zero gap!)
      if (_ttsSentenceIdx + 1 < _ttsSentences.length) {
        void _fetchSynthesizedSentence(_ttsSentences[_ttsSentenceIdx + 1]);
      }

      const synthData = await _fetchSynthesizedSentence(sentence);
      if (!isSpeaking || mySession !== _ttsSessionId) return;

      if (!synthData?.available || !synthData.audio_url) {
        _playBrowserSpeechFallback(sentence, mySession);
        return;
      }

      const badge = document.getElementById('tts-engine-badge');
      if (badge) badge.textContent = _ttsVoice.includes('Ahmet') ? 'Ahmet · Stüdyo' : (_ttsVoice.includes('Emel') ? 'Emel · Stüdyo' : 'Aria · Studio');

      _ttsCurrentSpoken = synthData.spoken_text || sentence;
      _ttsCurrentWords = Array.isArray(synthData.words) ? synthData.words : [];

      if (!_ttsAudioEl) {
        _ttsAudioEl = new Audio();
        _ttsAudioEl.preload = 'auto';
      }
      _ttsAudioEl.onended = () => {
        if (mySession !== _ttsSessionId || !isSpeaking || _ttsIsPaused) return;
        void _advanceToNextSentence(mySession);
      };
      _ttsAudioEl.onerror = () => {
        if (mySession !== _ttsSessionId || !isSpeaking) return;
        _playBrowserSpeechFallback(sentence, mySession);
      };

      _ttsAudioEl.src = synthData.audio_url;
      try {
        await _ttsAudioEl.play();
        if (mySession === _ttsSessionId && !_ttsIsPaused) {
          _startKaraokeRafLoop(mySession);
        }
      } catch (_playErr) {
        if (mySession === _ttsSessionId) {
          _playBrowserSpeechFallback(sentence, mySession);
        }
      }
    }

    async function _advanceToNextSentence(mySession) {
      if (!isSpeaking || mySession !== _ttsSessionId) return;
      if (_ttsSentenceIdx + 1 < _ttsSentences.length) {
        _ttsSentenceIdx++;
        await _playCurrentSentence(mySession);
        return;
      }
      // Auto-advance to next page for continuous hands-free book listening!
      if (_ttsActivePage < pdfPageCount) {
        const nextPage = _ttsActivePage + 1;
        _ttsActivePage = nextPage;
        scrollToPage(nextPage);
        const nextSentences = await _loadSentencesForPage(nextPage);
        if (!isSpeaking || mySession !== _ttsSessionId) return;
        if (nextSentences.length > 0) {
          _ttsSentences = nextSentences;
          _ttsSentenceIdx = 0;
          await _playCurrentSentence(mySession);
          return;
        }
      }
      stopNeuralTTS();
      if (typeof showToast === 'function') showToast('Sayfa seslendirmesi tamamlandı.', 'success', 2200);
    }

    function stopNeuralTTS() {
      ++_ttsSessionId;
      isSpeaking = false;
      _ttsIsPaused = false;
      if (_ttsRafId) {
        cancelAnimationFrame(_ttsRafId);
        _ttsRafId = 0;
      }
      if (_ttsAudioEl) {
        try {
          _ttsAudioEl.pause();
          _ttsAudioEl.removeAttribute('src');
          _ttsAudioEl.load();
        } catch (_e) {}
      }
      if ('speechSynthesis' in window) {
        try { window.speechSynthesis.cancel(); } catch (_e) {}
      }
      _ttsSentences = [];
      _ttsCurrentWords = [];
      _clearAllTtsKaraokeLayers();
      _syncTtsButtonsUI();
    }
    window.stopNeuralTTS = stopNeuralTTS;

    async function togglePdfTTS() {
      if (isSpeaking) {
        stopNeuralTTS();
        return;
      }
      if (!pdfDoc && !isDocReaderMode) return;

      const selectedText = window.getSelection?.()?.toString()?.trim() || '';
      const mySession = ++_ttsSessionId;
      isSpeaking = true;
      _ttsIsPaused = false;
      _ttsActivePage = pdfPageNum || 1;
      _syncTtsButtonsUI();

      const capEl = document.getElementById('tts-live-caption');
      if (capEl) capEl.textContent = 'Doğal Türkçe ses hazırlanıyor...';

      const sentences = await _loadSentencesForPage(_ttsActivePage, selectedText);
      if (mySession !== _ttsSessionId || !isSpeaking) return;

      if (!sentences || sentences.length === 0) {
        stopNeuralTTS();
        if (typeof showToast === 'function') {
          showToast('Bu sayfada seslendirilecek metin bulunamadı.', 'warning');
        }
        return;
      }

      _ttsSentences = sentences;
      _ttsSentenceIdx = 0;
      await _playCurrentSentence(mySession);
    }
    window.togglePdfTTS = togglePdfTTS;

    function ttsTogglePlayPause() {
      if (!isSpeaking) return;
      _ttsIsPaused = !_ttsIsPaused;
      if (_ttsIsPaused) {
        if (_ttsAudioEl) {
          try { _ttsAudioEl.pause(); } catch (_e) {}
        }
        if ('speechSynthesis' in window) {
          try { window.speechSynthesis.pause(); } catch (_e) {}
        }
      } else {
        if (_ttsAudioEl && _ttsAudioEl.src) {
          _ttsAudioEl.play().catch(() => {});
          _startKaraokeRafLoop(_ttsSessionId);
        } else if ('speechSynthesis' in window) {
          try { window.speechSynthesis.resume(); } catch (_e) {}
        }
      }
      _syncTtsButtonsUI();
    }
    window.ttsTogglePlayPause = ttsTogglePlayPause;

    function ttsStepSentence(delta) {
      if (!isSpeaking || !_ttsSentences.length) return;
      const nextIdx = Math.max(0, Math.min(_ttsSentences.length - 1, _ttsSentenceIdx + delta));
      _ttsSentenceIdx = nextIdx;
      _ttsIsPaused = false;
      const mySession = ++_ttsSessionId;
      if (_ttsAudioEl) {
        try { _ttsAudioEl.pause(); } catch (_e) {}
      }
      if ('speechSynthesis' in window) {
        try { window.speechSynthesis.cancel(); } catch (_e) {}
      }
      _syncTtsButtonsUI();
      void _playCurrentSentence(mySession);
    }
    window.ttsStepSentence = ttsStepSentence;

    function onTtsVoiceChange(newVoice) {
      _ttsVoice = newVoice || 'tr-TR-EmelNeural';
      try { localStorage.setItem('kutuphane_tts_voice', _ttsVoice); } catch (_e) {}
      if (isSpeaking) {
        ttsStepSentence(0);
      }
    }
    window.onTtsVoiceChange = onTtsVoiceChange;

    function onTtsRateChange(newRate) {
      _ttsRate = Math.max(0.5, Math.min(2.0, Number.parseFloat(newRate) || 1.0));
      try { localStorage.setItem('kutuphane_tts_rate', String(_ttsRate)); } catch (_e) {}
      if (isSpeaking) {
        ttsStepSentence(0);
      }
    }
    window.onTtsRateChange = onTtsRateChange;
