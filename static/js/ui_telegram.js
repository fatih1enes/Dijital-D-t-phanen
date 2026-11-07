/* ═══════════ ui_telegram.js — Telegram Sync & Auth UI Manager ═══════════ */

let telegramCurrentStep = 1;
let telegramStatusCache = null;

function showTelegramToast(msg, type = 'info') {
  let toast = document.getElementById('telegram-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'telegram-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 30px;
      right: 30px;
      padding: 0.85rem 1.4rem;
      border-radius: 50px;
      font-family: 'Geist', sans-serif;
      font-size: 0.9rem;
      font-weight: 500;
      z-index: 10000;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      opacity: 0;
      transform: translateY(15px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    `;
    document.body.appendChild(toast);
  }

  const isSuccess = type === 'success';
  const isError = type === 'error';
  const isWarning = type === 'warning';

  let bg = '#2563eb'; // Telegram blue
  let icon = 'fab fa-telegram-plane';

  if (isSuccess) {
    bg = '#5f7a4f';
    icon = 'fas fa-check-circle';
  } else if (isError) {
    bg = '#b0473c';
    icon = 'fas fa-exclamation-triangle';
  } else if (isWarning) {
    bg = '#b8862f';
    icon = 'fas fa-info-circle';
  }

  toast.style.background = bg;
  toast.style.color = '#ffffff';
  toast.innerHTML = `<i class="${icon}"></i> <span>${msg}</span>`;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';

  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(15px)';
  }, 4500);
}

function setTelegramStep(stepNumber) {
  telegramCurrentStep = stepNumber;
  const s1 = document.getElementById('tg-step-1');
  const s2 = document.getElementById('tg-step-2');
  const s3 = document.getElementById('tg-step-3');

  if (s1) s1.style.display = stepNumber === 1 ? 'block' : 'none';
  if (s2) s2.style.display = stepNumber === 2 ? 'block' : 'none';
  if (s3) s3.style.display = stepNumber === 3 ? 'block' : 'none';

  // Error cleanups
  const errEl = document.getElementById('tg-modal-error');
  if (errEl) {
    errEl.style.display = 'none';
    errEl.textContent = '';
  }
}

function showTelegramError(msg) {
  const errEl = document.getElementById('tg-modal-error');
  if (errEl) {
    errEl.textContent = msg;
    errEl.style.display = 'block';
  }
}

function _populateTelegramAuthorizedUI(status) {
  document.getElementById('tg-connected-name').textContent = status.first_name || status.username || 'Telegram Kullanıcısı';
  document.getElementById('tg-connected-phone').textContent = status.phone ? `+${status.phone.replace(/^\+/, '')}` : 'Gizli / Belirtilmedi';
  document.getElementById('tg-connected-last-sync').textContent = status.last_sync ? `Son Eşitleme: ${status.last_sync}` : 'Henüz senkronize edilmedi';
  const activeChatInput = document.getElementById('tg-active-chat-input');
  if (activeChatInput) activeChatInput.value = status.chat_id || 'me';

  const syncBtn = document.getElementById('tg-btn-sync-action');
  if (syncBtn) {
    if (status.is_syncing) {
      syncBtn.disabled = true;
      syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Taranıyor...';
    } else {
      syncBtn.disabled = false;
      syncBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Kitapları Şimdi Senkronize Et';
    }
  }

  setTelegramStep(3);
}

function _populateTelegramStep1Defaults(status) {
  if (status.api_id) {
    const idInput = document.getElementById('tg-input-api-id');
    if (idInput && !idInput.value) idInput.value = status.api_id;
  }
  if (status.chat_id) {
    const chatInput = document.getElementById('tg-input-chat-id');
    if (chatInput && !chatInput.value) chatInput.value = status.chat_id;
  }
  setTelegramStep(1);
}

async function openTelegramModal() {
  const modal = document.getElementById('telegram-modal');
  if (!modal) return;

  const errEl = document.getElementById('tg-modal-error');
  if (errEl) errEl.style.display = 'none';

  modal.classList.add('open');
  document.body.classList.add('modal-open');
  document.body.style.overflow = 'hidden';

  // Check connection status
  try {
    const status = await apiTelegramStatus();
    telegramStatusCache = status;

    if (status.authorized) {
      _populateTelegramAuthorizedUI(status);
    } else {
      _populateTelegramStep1Defaults(status);
    }
  } catch (e) {
    console.warn("Telegram status check error:", e);
    setTelegramStep(1);
  }
}

function closeTelegramModal() {
  const modal = document.getElementById('telegram-modal');
  if (modal) modal.classList.remove('open');
  document.body.classList.remove('modal-open');
  document.body.style.overflow = '';
}

function closeTelegramModalBackdrop(e) {
  if (e.target?.id === 'telegram-modal') {
    closeTelegramModal();
  }
}

// ── Step 1: Send confirmation code ──────────────────────────
async function telegramSubmitCredentials() {
  const apiId = document.getElementById('tg-input-api-id')?.value.trim();
  const apiHash = document.getElementById('tg-input-api-hash')?.value.trim();
  const phone = document.getElementById('tg-input-phone')?.value.trim();
  const chatTarget = document.getElementById('tg-input-chat-id')?.value.trim();
  const btn = document.getElementById('tg-btn-send-code');

  if (!apiId || !apiHash || !phone) {
    showTelegramError('Lütfen API ID, API Hash ve Telefon Numarası alanlarını doldurun.');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kod Gönderiliyor...';
  }

  try {
    const res = await apiTelegramSendCode(apiId, apiHash, phone, chatTarget);
    if (res.success) {
      document.getElementById('tg-step-2-phone').textContent = phone;
      // Reset 2FA input state
      const passCont = document.getElementById('tg-2fa-container');
      if (passCont) passCont.style.display = 'none';
      const passInput = document.getElementById('tg-input-password');
      if (passInput) passInput.value = '';

      setTelegramStep(2);
      const codeInput = document.getElementById('tg-input-code');
      if (codeInput) {
        codeInput.value = '';
        setTimeout(() => codeInput.focus(), 150);
      }
    } else {
      showTelegramError(res.error || 'Kod gönderilemedi.');
    }
  } catch (err) {
    showTelegramError(err.message || 'Bir hata oluştu.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = 'Doğrulama Kodu Gönder <i class="fas fa-arrow-right"></i>';
    }
  }
}

function _handleTelegramVerifySuccess(user) {
  showTelegramToast('Telegram hesabınız başarıyla bağlandı!', 'success');
  const userData = user || {};
  document.getElementById('tg-connected-name').textContent = userData.first_name || userData.username || 'Telegram Kullanıcısı';
  document.getElementById('tg-connected-phone').textContent = userData.phone ? `+${userData.phone.replace(/^\+/, '')}` : '—';
  document.getElementById('tg-connected-last-sync').textContent = 'Henüz senkronize edilmedi';

  const activeChatInput = document.getElementById('tg-active-chat-input');
  const chatInput = document.getElementById('tg-input-chat-id');
  if (activeChatInput) {
    activeChatInput.value = chatInput?.value?.trim() || 'me';
  }
  setTelegramStep(3);
}

function _handleTelegram2FARequired(res) {
  const passCont = document.getElementById('tg-2fa-container');
  if (passCont) {
    passCont.style.display = 'block';
    const passInput = document.getElementById('tg-input-password');
    passInput?.focus();
  }
  showTelegramError(res.error || 'Hesabınızda 2FA aktif. Lütfen iki adımlı doğrulama şifrenizi girin.');
}

// ── Step 2: Verify code & 2FA ──────────────────────────────
async function telegramSubmitCode() {
  const code = document.getElementById('tg-input-code')?.value.trim();
  const password = document.getElementById('tg-input-password')?.value.trim();
  const btn = document.getElementById('tg-btn-verify-code');

  if (!code) {
    showTelegramError('Lütfen Telegram veya SMS ile gelen doğrulama kodunu girin.');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Doğrulanıyor...';
  }

  try {
    const res = await apiTelegramVerify(code, password || null);

    if (res.needs_password) {
      _handleTelegram2FARequired(res);
      return;
    }

    if (res.success) {
      _handleTelegramVerifySuccess(res.user);
    } else {
      showTelegramError(res.error || 'Doğrulama başarısız oldu.');
    }
  } catch (err) {
    showTelegramError(err.message || 'Doğrulama sırasında hata oluştu.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-check"></i> Bağlantıyı Tamamla';
    }
  }
}

// ── Step 3: Save Channel Target ─────────────────────────────
async function saveTelegramActiveChat() {
  const input = document.getElementById('tg-active-chat-input');
  const btn = document.getElementById('tg-btn-save-chat');
  if (!input) return;
  const newChat = input.value.trim() || 'me';

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  }

  try {
    await apiTelegramUpdateChannel(newChat);
    showTelegramToast(`Kanal hedefi güncellendi: ${newChat}`, 'success');
  } catch (err) {
    showTelegramToast(`Hata: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-save"></i> Kaydet';
    }
  }
}

// ── Step 3: Trigger Sync ────────────────────────────────────
async function telegramTriggerSync() {
  const btn = document.getElementById('tg-btn-sync-action');
  const activeChatInput = document.getElementById('tg-active-chat-input');
  const chatInput = document.getElementById('tg-input-chat-id');
  const chatTarget = activeChatInput?.value?.trim() || chatInput?.value?.trim() || 'me';
  const resetCursor = !!document.getElementById('tg-reset-cursor')?.checked;

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Taranıyor...';
  }

  try {
    await apiTelegramSync(chatTarget, resetCursor);
    showTelegramToast('Telegram senkronizasyonu başlatıldı! Kitaplar ana ekranda canlı işlenecektir.', 'info');
    closeTelegramModal();

    // Ensure main screen grid is visible so user watches live cards appear
    if (typeof updateLibraryZoneVisibility === 'function') {
      updateLibraryZoneVisibility(true);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Open operations center so user also sees terminal logs
    const opsCenter = document.getElementById('ops-center');
    if (opsCenter) opsCenter.classList.add('active');

  } catch (err) {
    showTelegramToast(`Hata: ${err.message}`, 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-sync-alt"></i> Kitapları Şimdi Senkronize Et';
    }
  }
}

// ── Step 3: Disconnect Account ──────────────────────────────
async function telegramDisconnectAccount() {
  if (!confirm("Telegram bağlantısını kesmek ve kayıtlı oturumu kaldırmak istediğinize emin misiniz?")) {
    return;
  }

  const btn = document.getElementById('tg-btn-disconnect');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Kesiliyor...';
  }

  try {
    await apiTelegramDisconnect();
    showTelegramToast('Telegram bağlantısı başarıyla kesildi.', 'success');
    setTelegramStep(1);
  } catch (err) {
    showTelegramError(err.message || 'Bağlantı kesilemedi.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-unlink"></i> Hesabı Ayır';
    }
  }
}

// Expose globally
window.openTelegramModal = openTelegramModal;
window.closeTelegramModal = closeTelegramModal;
window.closeTelegramModalBackdrop = closeTelegramModalBackdrop;
window.setTelegramStep = setTelegramStep;
window.telegramSubmitCredentials = telegramSubmitCredentials;
window.telegramSubmitCode = telegramSubmitCode;
window.saveTelegramActiveChat = saveTelegramActiveChat;
window.telegramTriggerSync = telegramTriggerSync;
window.telegramDisconnectAccount = telegramDisconnectAccount;
window.showTelegramToast = showTelegramToast;
