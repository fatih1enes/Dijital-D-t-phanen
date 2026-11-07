/* ═══════════ ui_chat_settings.js — Assistant Drawer, Settings & Analytics ═══════════ */
    function startChatTypewriter(rawReply, msgEl, chatBody) {
      if (!msgEl) return;
      const body = chatBody || document.getElementById('chat-body');
      const words = (rawReply || '').split(' ');
      const totalWords = words.length || 1;
      const wordDelay = Math.min(25, Math.max(5, Math.floor(2500 / totalWords)));
      let currentText = '';
      let wordIndex = 0;

      const isUserNearBottom = () => {
        if (!body) return true;
        return (body.scrollHeight - body.scrollTop - body.clientHeight) < 60;
      };

      let lastParagraphCheck = '';
      const timer = setInterval(() => {
        if (wordIndex < words.length) {
          currentText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
          wordIndex++;

          const hasNewParagraph = currentText.includes('\n\n') && currentText.lastIndexOf('\n\n') > lastParagraphCheck.length;
          if (hasNewParagraph) {
            msgEl.innerHTML = parseMarkdown(currentText);
            lastParagraphCheck = currentText.slice(0, currentText.lastIndexOf('\n\n'));
          } else if (lastParagraphCheck.length === 0) {
            msgEl.textContent = currentText;
          } else {
            const unrenderedPart = currentText.slice(lastParagraphCheck.length);
            const safeUnrendered = typeof esc === 'function' ? esc(unrenderedPart) : unrenderedPart;
            msgEl.innerHTML = parseMarkdown(lastParagraphCheck) + '<p>' + safeUnrendered + '</p>';
          }

          if (isUserNearBottom() && body) {
            body.scrollTop = body.scrollHeight;
          }
        } else {
          clearInterval(timer);
          msgEl.innerHTML = parseMarkdown(rawReply);
          if (isUserNearBottom() && body) {
            body.scrollTop = body.scrollHeight;
          }
        }
      }, wordDelay);
    }
    window.startChatTypewriter = startChatTypewriter;

    function sendMessage() {
      const input = document.getElementById('chat-input');
      const sendBtn = document.querySelector('.btn-send');
      const text = input.value.trim();
      if (!text || text.length > 1000) return;

      // Lock UI
      input.disabled = true;
      if (sendBtn) sendBtn.disabled = true;

      addChatMessage('sender', text);
      input.value = '';
      updateChatCounter(); // Reset counter

      const aiMsgId = 'ai-typing-' + Date.now();
      addChatMessage('ai', 'Düşünüyorum...', aiMsgId);

      apiFetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
        .then(r => r ? r.json() : null)
        .then(data => {
          const msgEl = document.getElementById(aiMsgId);
          if (msgEl) {
            startChatTypewriter(data?.response || '', msgEl);
          }
        })
        .catch(err => {
          const msgEl = document.getElementById(aiMsgId);
          if (msgEl) msgEl.textContent = "Hata oluştu. Lütfen tekrar dene.";
        })
        .finally(() => {
          // Unlock UI
          input.disabled = false;
          if (sendBtn) sendBtn.disabled = false;
          input.focus();
        });
    }

    function addChatMessage(type, text, id = null) {
      const body = document.getElementById('chat-body');
      if (!body) return;
      const msg = document.createElement('div');
      msg.className = `chat-msg chat-${type}`;
      
      if (type === 'ai') {
        msg.innerHTML = parseMarkdown(text);
      } else {
        msg.textContent = text;
      }
      
      if (id) msg.id = id;
      body.appendChild(msg);
      body.scrollTop = body.scrollHeight;
    }

    const DEFAULT_CASCADE_MODELS = [
      "gemini-3.8-flash",
      "gemini-3.7-flash",
      "gemini-3.6-flash",
      "gemini-3.5-flash",
      "gemini-3.5-flash-lite"
    ];

    function populateCascadeSlots(models) {
      const list = Array.isArray(models) && models.length ? models : DEFAULT_CASCADE_MODELS;
      for (let i = 0; i < 5; i++) {
        const el = document.getElementById(`cascade-model-${i}`);
        if (el) {
          el.value = (list[i] || '').trim();
        }
      }
    }

    function getCascadeSlots() {
      const models = [];
      for (let i = 0; i < 5; i++) {
        const el = document.getElementById(`cascade-model-${i}`);
        if (el) {
          const val = (el.value || '').trim();
          if (val) models.push(val);
        }
      }
      return models.length ? models : [...DEFAULT_CASCADE_MODELS];
    }

    function resetCascadeModelsToDefault() {
      populateCascadeSlots(DEFAULT_CASCADE_MODELS);
    }
    window.resetCascadeModelsToDefault = resetCascadeModelsToDefault;

    function populateServerOcrVisionSettings(data) {
      document.getElementById('set-pages').value = data.max_pages || 20;
      document.getElementById('set-ocr-pages').value = data.ocr_pages || 20;
      document.getElementById('set-vision-pages').value = data.vision_pages || 20;
      document.getElementById('set-vision-dim').value = data.vision_max_image_dim || 1200;
      document.getElementById('set-vision-quality').value = data.vision_jpeg_quality || 82;
      document.getElementById('set-tesseract-cmd').value = data.tesseract_cmd || '';
      if (document.getElementById('set-watchfolder-enabled')) {
        document.getElementById('set-watchfolder-enabled').checked = Boolean(data.watchfolder_enabled);
      }
      if (document.getElementById('set-watchfolder-path')) {
        document.getElementById('set-watchfolder-path').value = data.watchfolder_path || '';
      }
      const maxChars = data.ai_max_chars || 50000;
      document.getElementById('set-ai-max-chars').value = maxChars;
      document.getElementById('ai-max-chars-val').innerText = maxChars;
    }

    function _populateApiKeyAndModel(data) {
      if (data.has_gemini_key || data.has_ai_api_key) {
        const keyEl = document.getElementById('set-api-key');
        if (keyEl && !keyEl.value) keyEl.placeholder = "•••••••• (Sunucuda Yapılandırılmış)";
      } else if (data.ai_api_key && !data.ai_api_key.startsWith('••')) {
        document.getElementById('set-api-key').value = data.ai_api_key;
      }
      if (data.gemini_model) {
        localStorage.setItem('gemini_model', data.gemini_model);
        if ((data.ai_provider || document.getElementById('set-ai-provider')?.value || 'gemini') === 'gemini') {
          const mn = document.getElementById('set-ai-model-name');
          if (mn) mn.value = data.gemini_model;
        }
      }
    }

    function populateServerAISettingsFields(data) {
      if (data.ai_provider) document.getElementById('set-ai-provider').value = data.ai_provider;
      _populateApiKeyAndModel(data);
      if (data.ai_base_url) document.getElementById('set-ai-base-url').value = data.ai_base_url;
      if (data.gemini_cascade_mode !== undefined && document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = Boolean(data.gemini_cascade_mode);
        localStorage.setItem('gemini_cascade_mode', Boolean(data.gemini_cascade_mode));
      }
      if (Array.isArray(data.gemini_cascade_models)) {
        populateCascadeSlots(data.gemini_cascade_models);
        localStorage.setItem('gemini_cascade_models', JSON.stringify(data.gemini_cascade_models));
      }
      updateAIUI();
    }

    function _applyPasswordStateBadge(hasPassword, pwdBadge, pwdInput, removePwdBtn) {
      if (hasPassword) {
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
          pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
          pwdBadge.style.color = '#5f7a4f';
        }
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = '•••••••• (Şifre Belirlenmiş)';
        }
        if (removePwdBtn) removePwdBtn.style.display = 'inline-flex';
      } else {
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#b8862f;"></i> Şifre Belirlenmemiş';
          pwdBadge.style.background = 'rgba(184,134,47, 0.12)';
          pwdBadge.style.color = '#b8862f';
        }
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = 'Erişim şifresi belirleyin...';
        }
        if (removePwdBtn) removePwdBtn.style.display = 'none';
      }
    }

    function populateServerSecuritySettings(data) {
      const pwdInput = document.getElementById('set-access-password');
      const pwdBadge = document.getElementById('sec-pwd-status-badge');
      const removePwdBtn = document.getElementById('btn-remove-access-pwd');
      const phoneUrlDisplay = document.getElementById('phone-connection-url-display');
      const opdsUrlDisplay = document.getElementById('opds-connection-url-display');
      const phoneUrl = data.phone_url || (window.location.protocol + '//' + window.location.hostname + ':8000');
      if (phoneUrlDisplay) phoneUrlDisplay.textContent = phoneUrl;
      if (opdsUrlDisplay) opdsUrlDisplay.textContent = phoneUrl.replace(/\/$/, '') + '/opds';

      _applyPasswordStateBadge(data.has_access_password, pwdBadge, pwdInput, removePwdBtn);
    }

    function syncOpenSettingsFromServer(data) {
      if (!data) return;
      window.appSettings = data;
      populateServerOcrVisionSettings(data);
      populateServerAISettingsFields(data);

      const tsStatus = document.getElementById('tesseract-status');
      if (tsStatus) {
        const cmd = (data.tesseract_cmd || '').trim();
        if (cmd) {
          tsStatus.innerHTML = '<i class="fas fa-check-circle" style="color:#4caf50; margin-right:0.3rem;"></i> Tesseract yolu ayarlanmış: <code style="font-size:0.7rem;">' + esc(cmd) + '</code>';
        } else {
          tsStatus.innerHTML = '<i class="fas fa-info-circle" style="color:var(--accent); margin-right:0.3rem;"></i> Tesseract yolu belirtilmemiş. Sistem PATH\'ten otomatik bulunmaya çalışılacak.';
        }
      }

      populateServerSecuritySettings(data);
    }

    function getModelPlaceholder(provider) {
      if (provider === 'gemini') return 'gemini-3.5-flash-lite';
      if (provider === 'ollama') return 'Örn: llama3';
      return 'Örn: local-model';
    }

    function _getSavedGeminiModel() {
      let savedGemini = localStorage.getItem('gemini_model');
      if (!savedGemini || savedGemini.includes('3.1') || savedGemini.includes('1.5')) {
        savedGemini = 'gemini-3.5-flash-lite';
        localStorage.setItem('gemini_model', 'gemini-3.5-flash-lite');
      }
      return savedGemini;
    }

    function _getSavedCascadeModels() {
      let savedCascadeModels = null;
      try {
        const raw = localStorage.getItem('gemini_cascade_models');
        if (raw) savedCascadeModels = JSON.parse(raw);
      } catch {
        // Ignore parse errors on corrupted local cache
      }
      if (!savedCascadeModels && window.appSettings?.gemini_cascade_models) {
        savedCascadeModels = window.appSettings.gemini_cascade_models;
      }
      return savedCascadeModels || DEFAULT_CASCADE_MODELS;
    }

    // --- Yeni Fonksiyonlar (Settings & Edit) ---
    function openSettings() {
      try {
        const { provider, apiKey, baseUrl, modelName } = getAISettings();
        const providerEl = document.getElementById('set-ai-provider');
        const apiKeyEl = document.getElementById('set-api-key');
        const baseUrlEl = document.getElementById('set-ai-base-url');
        const modelNameEl = document.getElementById('set-ai-model-name');
        const modal = document.getElementById('settings-modal');

        const savedGemini = _getSavedGeminiModel();

        if (providerEl) providerEl.value = provider;
        if (apiKeyEl) apiKeyEl.value = apiKey;
        if (baseUrlEl) baseUrlEl.value = baseUrl;
        if (modelNameEl) {
          modelNameEl.value = provider === 'gemini' ? savedGemini : modelName;
          modelNameEl.placeholder = getModelPlaceholder(provider);
        }
        if (document.getElementById('set-gemini-cascade-mode')) {
          const savedCascade = localStorage.getItem('gemini_cascade_mode');
          document.getElementById('set-gemini-cascade-mode').checked = savedCascade !== null ? savedCascade === 'true' : true;
        }

        populateCascadeSlots(_getSavedCascadeModels());

        updateAIUI();
        
        if (modal) {
          modal.classList.remove('closing');
          modal.classList.add('open');
          document.body.classList.add('modal-open');
          switchSettingsTab('ai');
        }
      } catch (err) {
        console.error("openSettings error:", err);
      }

      apiFetch('/api/settings')
        .then(r => r ? r.json() : null)
        .then(syncOpenSettingsFromServer)
        .catch(err => console.error("openSettings settings fetch error:", err));
    }

    function _loadSettingsFromLocalStorage() {
      const provider = localStorage.getItem('ai_provider') || 'gemini';
      const apiKey = localStorage.getItem('ai_api_key') || '';
      const baseUrl = localStorage.getItem('ai_base_url') || '';
      let geminiModel = localStorage.getItem('gemini_model') || 'gemini-3.5-flash-lite';
      if (!geminiModel || geminiModel.includes('3.1') || geminiModel.includes('1.5')) {
        geminiModel = 'gemini-3.5-flash-lite';
        localStorage.setItem('gemini_model', 'gemini-3.5-flash-lite');
      }
      const ollamaModel = localStorage.getItem('ollama_model') || '';
      const lmstudioModel = localStorage.getItem('lmstudio_model') || '';

      let savedCascadeModels = null;
      try {
        const raw = localStorage.getItem('gemini_cascade_models');
        if (raw) savedCascadeModels = JSON.parse(raw);
      } catch {
        // Ignore cache read errors
      }

      return {
        ai_provider: provider,
        ai_api_key: apiKey,
        ai_base_url: baseUrl,
        gemini_model: geminiModel,
        ollama_model: ollamaModel,
        lmstudio_model: lmstudioModel,
        vision_pages: Number.parseInt(localStorage.getItem('vision_pages') || '20', 10),
        vision_max_image_dim: Number.parseInt(localStorage.getItem('vision_max_image_dim') || '1200', 10),
        vision_jpeg_quality: Number.parseInt(localStorage.getItem('vision_jpeg_quality') || '82', 10),
        ai_max_chars: Number.parseInt(localStorage.getItem('ai_max_chars') || '50000', 10),
        gemini_cascade_mode: localStorage.getItem('gemini_cascade_mode') !== null ? localStorage.getItem('gemini_cascade_mode') === 'true' : true,
        gemini_cascade_models: savedCascadeModels || DEFAULT_CASCADE_MODELS
      };
    }

    function _populateSettingsInputs(settings) {
      if (document.getElementById('set-ai-provider')) document.getElementById('set-ai-provider').value = settings.ai_provider;
      if (document.getElementById('set-api-key')) document.getElementById('set-api-key').value = settings.ai_api_key;
      if (document.getElementById('set-ai-base-url')) document.getElementById('set-ai-base-url').value = settings.ai_base_url;
      if (document.getElementById('set-ai-model-name')) {
        let model = settings.lmstudio_model;
        if (settings.ai_provider === 'gemini') model = settings.gemini_model;
        else if (settings.ai_provider === 'ollama') model = settings.ollama_model;
        document.getElementById('set-ai-model-name').value = model;
      }
      if (document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = settings.gemini_cascade_mode;
      }
      populateCascadeSlots(settings.gemini_cascade_models);
      
      const maxChars = settings.ai_max_chars || 50000;
      if (document.getElementById('set-ai-max-chars')) {
        document.getElementById('set-ai-max-chars').value = maxChars;
        document.getElementById('ai-max-chars-val').innerText = maxChars;
      }
      updateAIUI();
    }

    function _applyServerAiCredentials(data) {
      if (data.ai_provider) {
        document.getElementById('set-ai-provider').value = data.ai_provider;
      }
      const keyEl = document.getElementById('set-api-key');
      if (data.has_gemini_key || data.has_ai_api_key) {
        if (keyEl && !keyEl.value) keyEl.placeholder = "•••••••• (Sunucuda Yapılandırılmış)";
      } else if (data.ai_api_key && !data.ai_api_key.startsWith('••') && keyEl) {
        keyEl.value = data.ai_api_key;
      }
      if (data.ai_base_url) {
        document.getElementById('set-ai-base-url').value = data.ai_base_url;
      }
      if (data.gemini_model) {
        localStorage.setItem('gemini_model', data.gemini_model);
        const currProv = data.ai_provider || document.getElementById('set-ai-provider')?.value || 'gemini';
        if (currProv === 'gemini') {
          const mn = document.getElementById('set-ai-model-name');
          if (mn) mn.value = data.gemini_model;
        }
      }
    }

    function _applyServerCascadeAndWatchfolder(data) {
      if (data.gemini_cascade_mode !== undefined && document.getElementById('set-gemini-cascade-mode')) {
        document.getElementById('set-gemini-cascade-mode').checked = Boolean(data.gemini_cascade_mode);
        localStorage.setItem('gemini_cascade_mode', Boolean(data.gemini_cascade_mode));
      }
      if (data.gemini_cascade_models && Array.isArray(data.gemini_cascade_models)) {
        populateCascadeSlots(data.gemini_cascade_models);
        localStorage.setItem('gemini_cascade_models', JSON.stringify(data.gemini_cascade_models));
      }
      if (data.watchfolder_enabled !== undefined && document.getElementById('set-watchfolder-enabled')) {
        document.getElementById('set-watchfolder-enabled').checked = !!data.watchfolder_enabled;
      }
      if (data.watchfolder_path !== undefined && document.getElementById('set-watchfolder-path')) {
        document.getElementById('set-watchfolder-path').value = data.watchfolder_path || '';
      }
    }

    function _applyServerSettingsToUI(data) {
      _applyServerAiCredentials(data);
      _applyServerCascadeAndWatchfolder(data);
      updateAIUI();
    }

    async function loadSettings() {
      try {
        window.appSettings = _loadSettingsFromLocalStorage();
        _populateSettingsInputs(window.appSettings);

        // Then, try to sync with server
        const res = await apiFetch('/api/settings');
        if (res?.ok) {
          const data = await res.json();
          window.appSettings = { ...window.appSettings, ...data };
          _applyServerSettingsToUI(data);
        }
      } catch (e) {
        console.error("Settings load failed:", e);
      }
    }

    function _collectNumericSettings() {
      const rawVPages = Number.parseInt(document.getElementById('set-vision-pages')?.value, 10);
      const rawVDim = Number.parseInt(document.getElementById('set-vision-dim')?.value, 10);
      const rawVQual = Number.parseInt(document.getElementById('set-vision-quality')?.value, 10);
      const rawMaxPages = Number.parseInt(document.getElementById('set-pages')?.value, 10);
      const rawOcrPages = Number.parseInt(document.getElementById('set-ocr-pages')?.value, 10);
      const rawMaxChars = Number.parseInt(document.getElementById('set-ai-max-chars')?.value, 10);

      return {
        vPages: Number.isNaN(rawVPages) ? 20 : rawVPages,
        vDim: Number.isNaN(rawVDim) ? 1200 : rawVDim,
        vQual: Number.isNaN(rawVQual) ? 82 : rawVQual,
        maxPages: Number.isNaN(rawMaxPages) ? 20 : rawMaxPages,
        ocrPages: Number.isNaN(rawOcrPages) ? 20 : rawOcrPages,
        maxChars: Number.isNaN(rawMaxChars) ? 50000 : rawMaxChars
      };
    }

    function _handleSettingsSaveSuccess(settings, saveBtn, originalHtml) {
      window.appSettings = { ...window.appSettings, ...settings };
      if (settings.access_password) {
        const pwdBadge = document.getElementById('sec-pwd-status-badge');
        if (pwdBadge) {
          pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
          pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
          pwdBadge.style.color = '#5f7a4f';
        }
        const pwdInput = document.getElementById('set-access-password');
        if (pwdInput) {
          pwdInput.value = '';
          pwdInput.placeholder = '•••••••• (Şifre Belirlenmiş)';
        }
        const removePwdBtn = document.getElementById('btn-remove-access-pwd');
        if (removePwdBtn) removePwdBtn.style.display = 'inline-flex';
      }
      if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-check"></i> <span>Kaydedildi</span>';
        saveBtn.style.background = '#5f7a4f';
      }
      showToast('Ayarlar başarıyla kaydedildi.', 'success');
      setTimeout(() => {
        closeSettingsDirect();
        if (saveBtn) {
          saveBtn.innerHTML = originalHtml;
          saveBtn.disabled = false;
          saveBtn.style.background = '';
        }
      }, 450);
    }

    function _persistSettingsLocally(aiConfig, num, cascadeMode, cascadeModels) {
      const { provider, apiKey, isPlaceholderMasked, baseUrl, modelName } = aiConfig;
      localStorage.setItem('ai_provider', provider);
      if (apiKey && !apiKey.startsWith('••') && !apiKey.includes('•')) {
        localStorage.setItem('ai_api_key', apiKey);
      } else if (!apiKey && !isPlaceholderMasked) {
        localStorage.removeItem('ai_api_key');
      }
      localStorage.setItem('ai_base_url', baseUrl);

      const modelKeyMap = { gemini: 'gemini_model', ollama: 'ollama_model', lmstudio: 'lmstudio_model' };
      const targetKey = modelKeyMap[provider];
      if (targetKey) {
        localStorage.setItem(targetKey, modelName);
      }

      localStorage.setItem('vision_pages', num.vPages);
      localStorage.setItem('vision_max_image_dim', num.vDim);
      localStorage.setItem('vision_jpeg_quality', num.vQual);
      localStorage.setItem('gemini_cascade_mode', cascadeMode);
      localStorage.setItem('gemini_cascade_models', JSON.stringify(cascadeModels));
    }

    function _buildSettingsPayload(aiConfig, num, cascadeMode, cascadeModels) {
      const { provider, apiKey, baseUrl, modelName } = aiConfig;
      const settings = {
        max_pages: num.maxPages,
        ocr_pages: num.ocrPages,
        vision_pages: num.vPages,
        vision_max_image_dim: num.vDim,
        vision_jpeg_quality: num.vQual,
        tesseract_cmd: document.getElementById('set-tesseract-cmd')?.value || '',
        ai_provider: provider || 'gemini',
        ai_base_url: baseUrl || '',
        ai_max_chars: num.maxChars,
        gemini_cascade_mode: cascadeMode,
        gemini_cascade_models: cascadeModels,
        watchfolder_enabled: document.getElementById('set-watchfolder-enabled')?.checked || false,
        watchfolder_path: document.getElementById('set-watchfolder-path')?.value.trim() || '',
      };

      const accessPwdInput = document.getElementById('set-access-password');
      const accessPwd = accessPwdInput ? accessPwdInput.value.trim() : '';
      if (accessPwd && !accessPwd.startsWith('••')) {
        settings.access_password = accessPwd;
      }

      if (apiKey && !apiKey.startsWith('••') && !apiKey.includes('•')) {
        settings.ai_api_key = apiKey;
      }

      const modelPropMap = { gemini: 'gemini_model', ollama: 'ollama_model', lmstudio: 'lmstudio_model' };
      const targetProp = modelPropMap[provider];
      if (targetProp) {
        settings[targetProp] = modelName;
      }

      return settings;
    }

    function saveSettings() {
      const provider = document.getElementById('set-ai-provider').value;
      const keyEl = document.getElementById('set-api-key');
      const apiKey = keyEl ? keyEl.value.trim() : '';
      const keyPlaceholder = keyEl ? (keyEl.placeholder || '') : '';
      const isPlaceholderMasked = keyPlaceholder.includes('•');
      const baseUrl = document.getElementById('set-ai-base-url').value;
      const modelName = document.getElementById('set-ai-model-name').value;
      const num = _collectNumericSettings();
      const geminiCascadeMode = document.getElementById('set-gemini-cascade-mode') ? document.getElementById('set-gemini-cascade-mode').checked : true;
      const cascadeModels = getCascadeSlots();

      const aiConfig = { provider, apiKey, isPlaceholderMasked, baseUrl, modelName };
      _persistSettingsLocally(aiConfig, num, geminiCascadeMode, cascadeModels);
      const settings = _buildSettingsPayload(aiConfig, num, geminiCascadeMode, cascadeModels);

      const saveBtn = document.getElementById('btn-save-settings');
      const originalHtml = saveBtn ? saveBtn.innerHTML : '';
      if (saveBtn) {
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Kaydediliyor...</span>';
        saveBtn.disabled = true;
      }

      apiFetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      })
        .then(res => {
          if (res?.ok) {
            _handleSettingsSaveSuccess(settings, saveBtn, originalHtml);
          } else {
            if (saveBtn) {
              saveBtn.innerHTML = originalHtml;
              saveBtn.disabled = false;
            }
            showToast('Ayarlar kaydedilirken hata oluştu.', 'error');
          }
        })
        .catch(_err => {
          if (saveBtn) {
            saveBtn.innerHTML = originalHtml;
            saveBtn.disabled = false;
          }
          showToast('Bağlantı hatası.', 'error');
        });
    }

    function switchSettingsTab(tabName) {
      const tabBtns = document.querySelectorAll('.settings-tab-btn');
      const tabPanes = document.querySelectorAll('.settings-tab-pane');
      tabBtns.forEach(btn => btn.classList.remove('active'));
      tabPanes.forEach(pane => pane.classList.remove('active'));

      const activeBtn = document.getElementById(`tab-btn-${tabName}`);
      const activePane = document.getElementById(`tab-pane-${tabName}`);
      if (activeBtn) activeBtn.classList.add('active');
      if (activePane) {
        activePane.getBoundingClientRect(); // Clean reflow for restartable spring slide
        activePane.classList.add('active');
      }

      const settingsBody = document.querySelector('#settings-modal .settings-body');
      if (settingsBody) {
        settingsBody.scrollTop = 0;
      }
    }
    window.switchSettingsTab = switchSettingsTab;

    function toggleAccessPasswordVisibility() {
      const input = document.getElementById('set-access-password');
      const icon = document.getElementById('btn-toggle-pwd-icon');
      if (!input) return;
      if (input.type === 'password') {
        input.type = 'text';
        if (icon) {
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        }
      } else {
        input.type = 'password';
        if (icon) {
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }
    }
    window.toggleAccessPasswordVisibility = toggleAccessPasswordVisibility;

    async function saveAccessPasswordDirect() {
      const input = document.getElementById('set-access-password');
      if (!input) return;
      const pwd = input.value.trim();
      if (!pwd) {
        showToast('Lütfen önce bir şifre girin.', 'warning');
        input.focus();
        return;
      }
      if (pwd.startsWith('••')) {
        showToast('Mevcut şifreniz zaten aktif.', 'info');
        return;
      }
      const saveBtn = document.getElementById('btn-save-access-pwd');
      const origHtml = saveBtn ? saveBtn.innerHTML : '';
      if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Kaydediliyor...</span>';
      }
      try {
        const res = await apiFetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_password: pwd })
        });
        if (res?.ok) {
          const pwdBadge = document.getElementById('sec-pwd-status-badge');
          if (pwdBadge) {
            pwdBadge.innerHTML = '<i class="fas fa-check-circle" style="color:#5f7a4f;"></i> Şifre Aktif';
            pwdBadge.style.background = 'rgba(95,122,79, 0.12)';
            pwdBadge.style.color = '#5f7a4f';
          }
          input.value = '';
          input.placeholder = '•••••••• (Şifre Belirlenmiş)';
          const removeBtn = document.getElementById('btn-remove-access-pwd');
          if (removeBtn) removeBtn.style.display = 'inline-flex';
          showToast('Erişim şifresi başarıyla kaydedildi ve aktif edildi!', 'success');
        } else {
          showToast('Şifre kaydedilirken hata oluştu.', 'error');
        }
      } catch (e) {
        console.error('saveAccessPasswordDirect error:', e);
        showToast('Bağlantı hatası oluştu.', 'error');
      } finally {
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.innerHTML = origHtml;
        }
      }
    }
    window.saveAccessPasswordDirect = saveAccessPasswordDirect;

    async function removeAccessPassword() {
      const ok = await (window.showAppConfirm ? window.showAppConfirm('Erişim şifresini kaldırmak istediğinizden emin misiniz?\n(Uzaktan telefon bağlantısı için şifre gereklidir)', 'Şifreyi Kaldır', 'Kaldır', true) : Promise.resolve(confirm('Erişim şifresini kaldırmak istediğinizden emin misiniz?')));
      if (!ok) {
        return;
      }
      try {
        const res = await apiFetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_password: '__REMOVE__' })
        });
        if (res?.ok) {
          const pwdBadge = document.getElementById('sec-pwd-status-badge');
          if (pwdBadge) {
            pwdBadge.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#b8862f;"></i> Şifre Belirlenmemiş';
            pwdBadge.style.background = 'rgba(184,134,47, 0.12)';
            pwdBadge.style.color = '#b8862f';
          }
          const pwdInput = document.getElementById('set-access-password');
          if (pwdInput) {
            pwdInput.value = '';
            pwdInput.placeholder = 'Erişim şifresi belirleyin...';
          }
          const removePwdBtn = document.getElementById('btn-remove-access-pwd');
          if (removePwdBtn) removePwdBtn.style.display = 'none';
          showToast('Erişim şifresi kaldırıldı.', 'success');
        } else {
          showToast('Şifre kaldırılırken hata oluştu.', 'error');
        }
      } catch (err) {
        console.error('removeAccessPassword error:', err);
        showToast('Bağlantı hatası.', 'error');
      }
    }
    window.removeAccessPassword = removeAccessPassword;

    function copyPhoneConnectionUrl() {
      const codeEl = document.getElementById('phone-connection-url-display');
      if (!codeEl) return;
      const url = codeEl.textContent.trim();
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('Bağlantı adresi kopyalandı: ' + url, 'success');
        }).catch(() => {
          fallbackCopyUrl(url);
        });
      } else {
        fallbackCopyUrl(url);
      }
    }

    function copyOpdsConnectionUrl() {
      const codeEl = document.getElementById('opds-connection-url-display');
      if (!codeEl) return;
      const url = codeEl.textContent.trim();
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url).then(() => {
          showToast('OPDS katalog adresi kopyalandı: ' + url, 'success');
        }).catch(() => {
          fallbackCopyUrl(url);
        });
      } else {
        fallbackCopyUrl(url);
      }
    }
    window.copyOpdsConnectionUrl = copyOpdsConnectionUrl;
    function fallbackCopyUrl(url) {
      if (navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(url)
          .then(() => showToast('Bağlantı adresi kopyalandı: ' + url, 'success'))
          .catch(() => showToast('Adres: ' + url, 'info'));
        return;
      }
      showToast('Bağlantı adresi: ' + url, 'info');
    }
    window.copyPhoneConnectionUrl = copyPhoneConnectionUrl;



    function closeSettings(e) { if (e.target === document.getElementById('settings-modal')) closeSettingsDirect(); }
    function closeSettingsDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('settings-modal');
      } else {
        const modal = document.getElementById('settings-modal');
        if (modal) modal.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    }

    function closeColModal(e) { if (e.target === document.getElementById('col-modal')) closeColModalDirect(); }
    function closeColModalDirect() {
      if (typeof window.closeModalWithAnimation === 'function') {
        window.closeModalWithAnimation('col-modal');
      } else {
        const modal = document.getElementById('col-modal');
        if (modal) modal.classList.remove('open');
        document.body.classList.remove('modal-open');
      }
    }

    function toggleEditMode(hash) {
      const form = document.getElementById(`edit-form-${hash}`);
      form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }

    function saveBookEdit(hash) {
      const data = {
        kitap_adi: document.getElementById(`edit-title-${hash}`).value,
        yazar: document.getElementById(`edit-author-${hash}`).value,
        ozet: document.getElementById(`edit-summary-${hash}`).value
      };
      apiFetch(`/api/books/${hash}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
        .then(r => r ? r.json() : null)
        .then(() => {
          showToast('Kitap bilgileri güncellendi.', 'success');
          closeModalDirect();
          if (typeof loadBooksFromAPI === 'function') {
            return loadBooksFromAPI();
          }
          return null;
        })
        .catch(err => {
          console.error("saveBookEdit error:", err);
          showToast('Kitap güncellenirken hata oluştu.', 'error');
        });
    }

    function toggleAssistant() {
      const panel = document.getElementById('chat-panel');
      if (!panel) return;
      if (panel.classList.contains('active')) {
        panel.classList.add('closing');
        panel.classList.remove('active');
        setTimeout(() => {
          panel.classList.remove('closing');
        }, 150);
      } else {
        panel.classList.remove('closing');
        panel.classList.add('active');
        // Mutual Exclusion: Close Process Center
        const ops = document.getElementById('ops-center');
        if (ops) ops.classList.remove('active');

        // Auto Focus: Focus on input when panel opens
        const input = document.getElementById('chat-input');
        if (input) setTimeout(() => input.focus(), 280);
      }
    }

    function toggleOps() {
      const ops = document.getElementById('ops-center');
      const isActive = ops.classList.toggle('active');
      if (isActive) {
        // Mutual Exclusion: Close Assistant Panel
        const chat = document.getElementById('chat-panel');
        if (chat) chat.classList.remove('active');
        if (typeof fetchTasksFromAPI === 'function') {
          void fetchTasksFromAPI();
        }
      }
    }

    function toggleArchive() {
      openLogsModal();
    }


    // --- STATS DASHBOARD & CHARTS ---
    // â•â•â•â•â•â•â•â•â•â• STATS DASHBOARD â•â•â•â•â•â•â•â•â•â•


    async function loadStats() {
      try {
        const res = await apiFetch('/api/stats');
        const data = await res.json();
        renderStatCards(data.general);
        renderDonutChart(data.categories);
        renderBarChart(data.monthly);
      } catch {
        // UI fallback when statistics endpoint is unreachable
      }
    }

    function renderStatCards(g) {
      const cards = [
        { value: g.total_books, label: 'Toplam Kitap', icon: 'fa-book' },
        { value: g.unique_authors, label: 'Farklı Yazar', icon: 'fa-pen-nib' },
        { value: g.unique_categories, label: 'Kategori', icon: 'fa-layer-group' },
        { value: g.total_favorites, label: 'Favori', icon: 'fa-heart' },
      ];
      document.getElementById('stats-cards').innerHTML = cards.map(c => `
    <div class="stat-card">
      <div class="stat-card-value">${c.value}</div>
      <div class="stat-card-label"><i class="fas ${c.icon}" style="margin-right:4px;color:var(--accent)"></i> ${c.label}</div>
    </div>
  `).join('');
    }

    function renderDonutChart(categories) {
      if (!categories || categories.length === 0) {
        document.getElementById('donut-chart').innerHTML = '<div style="color:var(--muted);font-size:0.8rem;">Veri yok</div>';
        return;
      }
      const total = categories.reduce((s, c) => s + c.count, 0);
      const top = categories.slice(0, 8);
      const otherCount = categories.slice(8).reduce((s, c) => s + c.count, 0);
      if (otherCount > 0) top.push({ name: 'Diğer', count: otherCount });

      const size = 160, cx = 80, cy = 80, r = 60, circumference = 2 * Math.PI * r;
      let offset = 0;
      let paths = '';
      top.forEach((c, i) => {
        const pct = c.count / total;
        const dashLen = pct * circumference;
        const color = DONUT_COLORS[i % DONUT_COLORS.length];
        paths += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="24"
      stroke-dasharray="${dashLen} ${circumference - dashLen}" stroke-dashoffset="${-offset}"
      style="transition: stroke-dashoffset 0.6s"/>`;
        offset += dashLen;
      });

      const legend = top.map((c, i) => `
    <div class="donut-legend-item">
      <span class="donut-legend-dot" style="background:${DONUT_COLORS[i % DONUT_COLORS.length]}"></span>
      <span>${esc(c.name)}</span>
      <span class="donut-legend-count">${c.count}</span>
    </div>
  `).join('');

      document.getElementById('donut-chart').innerHTML = `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform:rotate(-90deg)">
      ${paths}
    </svg>
    <div class="donut-legend">${legend}</div>
  `;
    }

    function renderBarChart(monthly) {
      if (!monthly || monthly.length === 0) {
        document.getElementById('bar-chart').innerHTML = '<div style="color:var(--muted);font-size:0.8rem;">Henüz veri yok</div>';
        return;
      }
      const maxVal = Math.max(...monthly.map(m => m.count), 1);
      const months = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];
      document.getElementById('bar-chart').innerHTML = monthly.map(m => {
        const pct = (m.count / maxVal) * 100;
        const [, mo] = m.month.split('-');
        const label = months[Number.parseInt(mo, 10) - 1] || m.month;
        return `
      <div class="bar-col">
        <span class="bar-value">${m.count}</span>
        <div class="bar-fill" style="height:${Math.max(pct, 4)}%"></div>
        <span class="bar-label">${label}</span>
      </div>
    `;
      }).join('');
    }

    // â•â•â•â•â•â•â•â•â•â• DRAG & DROP SORT â•â•â•â•â•â•â•â•â•â•




