/* ═══════════ websocket.js — Real-time WebSocket Connection & Log Streaming ═══════════ */

let logBatchQueue = [];
let logBatchTimer = null;
let wsBooksDebounceTimer = null;

function debouncedLoadBooksWs(page = 1, append = false) {
  if (wsBooksDebounceTimer) clearTimeout(wsBooksDebounceTimer);
  wsBooksDebounceTimer = setTimeout(() => {
    wsBooksDebounceTimer = null;
    if (typeof loadBooksFromAPI === 'function') {
      void loadBooksFromAPI(page, append);
    }
  }, 300);
}

function setLogsConnectionStatus(status) {
  const prev = window._wsConnectionState;
  window._wsConnectionState = status;

  const indicator = document.getElementById('logs-status-indicator');
  const text = document.getElementById('logs-status-text');
  if (indicator && text) {
    indicator.className = `logs-status-pill status-${status}`;
    if (status === 'online') {
      text.textContent = 'Canlı';
    } else if (status === 'reconnecting') {
      text.textContent = 'Yeniden bağlanıyor…';
    } else {
      text.textContent = 'Çevrimdışı';
    }
  }

  const labelText = status === 'online'
    ? 'Canlı'
    : (status === 'reconnecting' ? 'Yeniden bağlanıyor…' : 'Çevrimdışı');

  const opsWs = document.getElementById('ops-ws-status');
  if (opsWs) opsWs.textContent = labelText;

  const emptyWs = document.getElementById('ops-empty-ws-status');
  if (emptyWs) emptyWs.textContent = labelText;

  const livePulse = document.getElementById('ops-live-pulse');
  if (livePulse && !livePulse.classList.contains('pulse-active')) {
    const pulseCls = status === 'online' ? 'idle' : (status === 'reconnecting' ? 'reconnecting' : 'offline');
    livePulse.className = `ops-live-pulse ops-header-indicator pulse-${pulseCls}`;
  }

  const opsToggle = document.getElementById('ops-toggle');
  if (opsToggle) {
    opsToggle.classList.toggle('is-ws-reconnecting', status === 'reconnecting');
    opsToggle.classList.toggle('is-ws-offline', status !== 'online' && status !== 'reconnecting');
  }

  if (prev !== status && typeof scheduleOpsUIUpdate === 'function' && window.lastActiveTasks) {
    scheduleOpsUIUpdate(window.lastActiveTasks, window.lastArchivedTasks || {});
  }
}
window.setLogsConnectionStatus = setLogsConnectionStatus;

function processIncomingLogBatch() {
  if (logBatchQueue.length === 0) return;
  const incoming = logBatchQueue;
  logBatchQueue = [];

  for (const l of incoming) {
    window.cachedLogs.push(l);
    if (l.level === 'ERROR') {
      window.unreadLogErrors = (window.unreadLogErrors || 0) + 1;
    }
  }

  if (window.cachedLogs.length > 2000) {
    window.cachedLogs.splice(0, window.cachedLogs.length - 2000);
  }

  updateHeaderLogsBadge();
  updateCategoryCounters();

  const modal = document.getElementById('logs-modal');
  if (modal?.classList?.contains('open') && !window.isLogLivePaused) {
    renderLogsModalBody();
  }
}

function queueIncomingLog(logEntry) {
  logBatchQueue.push(logEntry);
  if (!logBatchTimer) {
    logBatchTimer = setTimeout(() => {
      logBatchTimer = null;
      processIncomingLogBatch();
    }, 80);
  }
}

let wsHeartbeatInterval = null;
let wsHeartbeatTimeout = null;

function startHeartbeat() {
  stopHeartbeat();
  wsHeartbeatInterval = setInterval(() => {
    if (window.ws?.readyState === WebSocket.OPEN) {
      try {
        window.ws.send(JSON.stringify({ type: "ping", ts: Date.now() }));
      } catch (_err) {
        // Socket send error caught silently during heartbeat ping
      }
      wsHeartbeatTimeout = setTimeout(() => {
        console.warn("[WS] Heartbeat timeout. Soket sıfırlanıyor...");
        if (window.ws) {
          try { window.ws.close(); } catch (_closeErr) { /* Ignore close failure */ }
        }
      }, 10000);
    }
  }, 25000);
}

function stopHeartbeat() {
  if (wsHeartbeatInterval) clearInterval(wsHeartbeatInterval);
  if (wsHeartbeatTimeout) clearTimeout(wsHeartbeatTimeout);
  wsHeartbeatInterval = null;
  wsHeartbeatTimeout = null;
}

function handleWsTaskMessage(data) {
  if (!data?.task_id || !data?.task) return;
  const tid = data.task_id;
  const task = data.task;

  if (task.status === 'success' || task.status === 'error') {
    window.lastArchivedTasks[tid] = task;
    delete window.lastActiveTasks[tid];
  } else {
    window.lastActiveTasks[tid] = task;
  }

  if (typeof scheduleOpsUIUpdate === 'function') {
    scheduleOpsUIUpdate(window.lastActiveTasks, window.lastArchivedTasks);
  } else if (typeof updateOpsUI === 'function') {
    updateOpsUI(window.lastActiveTasks, window.lastArchivedTasks);
  }
  if (typeof updateUploadCards === 'function') {
    updateUploadCards({ ...window.lastActiveTasks, ...window.lastArchivedTasks });
  }
}

function _handleTelegramDownloadingStatus(data) {
  if (window._lastTgDlFilename !== data.filename) {
    window._lastTgDlFilename = data.filename;
    showTelegramToast(data.message || 'Telegram belgesi indiriliyor...', 'info');
  }
  if (typeof handleTelegramDownloadingCard === 'function' && data.filename) {
    handleTelegramDownloadingCard(data.filename, data.message, data.percent, data.speed);
  }
}

function handleWsTelegramSyncMessage(data) {
  if (typeof showTelegramToast !== 'function' || !data) return;
  const status = data.status;

  switch (status) {
    case 'started':
      showTelegramToast(data.message || 'Telegram taranıyor...', 'info');
      break;
    case 'downloading':
      _handleTelegramDownloadingStatus(data);
      break;
    case 'already_exists':
      if (typeof handleTelegramCardSkipped === 'function' && data.filename) {
        handleTelegramCardSkipped(data.filename, data.message);
      }
      break;
    case 'finished':
      showTelegramToast(data.message || 'Telegram senkronizasyonu tamamlandı.', 'success');
      if (typeof cleanupTelegramDlCards === 'function') cleanupTelegramDlCards();
      debouncedLoadBooksWs(1, false);
      break;
    case 'flood_wait':
      showTelegramToast(data.message, 'warning');
      if (typeof cleanupTelegramDlCards === 'function') cleanupTelegramDlCards();
      break;
    case 'error':
      showTelegramToast(data.message, 'error');
      if (typeof cleanupTelegramDlCards === 'function') cleanupTelegramDlCards();
      break;
    default:
      break;
  }
}

function handleWsTelegramStatusMessage(data) {
  if (data?.authorized && typeof showTelegramToast === 'function') {
    showTelegramToast(`Telegram bağlandı: ${data.user?.first_name || ''}`, 'success');
  }
}

function initWebSocket() {
  if (window.wsReconnectTimer) {
    clearTimeout(window.wsReconnectTimer);
    window.wsReconnectTimer = null;
  }

  // Safely detach and close any existing socket to prevent zombie sockets
  if (window.ws) {
    try {
      window.ws.onopen = null;
      window.ws.onmessage = null;
      window.ws.onerror = null;
      window.ws.onclose = null;
      if (window.ws.readyState === WebSocket.OPEN || window.ws.readyState === WebSocket.CONNECTING) {
        window.ws.close();
      }
    } catch (_err) {
      // Socket detachment error ignored during cleanup
    }
    window.ws = null;
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  setLogsConnectionStatus('reconnecting');

  try {
    window.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
  } catch (_e) {
    setLogsConnectionStatus('offline');
    scheduleReconnect();
    return;
  }

  function scheduleReconnect() {
    if (window.wsReconnectTimer) return;
    let rnd = 0.5;
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const arr = new Uint32Array(1);
      crypto.getRandomValues(arr);
      rnd = arr[0] / 0xFFFFFFFF;
    }
    const jitter = 0.85 + rnd * 0.3;
    const delay = Math.floor(Math.min((window.wsReconnectDelay || 1500) * 1.5, 15000) * jitter);
    window.wsReconnectTimer = setTimeout(() => {
      window.wsReconnectTimer = null;
      window.wsReconnectDelay = Math.min(Math.round((window.wsReconnectDelay || 1500) * 1.5), 15000);
      initWebSocket();
    }, delay);
  }

  window.ws.onopen = () => {
    window.wsReconnectDelay = 1500; // Reset backoff on successful connection
    setLogsConnectionStatus('online');
    startHeartbeat();
  };

  window.ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "pong") {
        if (wsHeartbeatTimeout) {
          clearTimeout(wsHeartbeatTimeout);
          wsHeartbeatTimeout = null;
        }
        return;
      }
      if (msg.type === "log") {
        queueIncomingLog(msg.data);
      } else if (msg.type === "log_cleared") {
        window.cachedLogs = [];
        window.unreadLogErrors = 0;
        updateHeaderLogsBadge();
        updateCategoryCounters();
        renderLogsModalBody();
      } else if (msg.type === "library_update") {
        debouncedLoadBooksWs(1, false);
      } else if (msg.type === "task") {
        handleWsTaskMessage(msg.data);
      } else if (msg.type === "telegram_sync") {
        handleWsTelegramSyncMessage(msg.data);
      } else if (msg.type === "telegram_status") {
        handleWsTelegramStatusMessage(msg.data);
      }
    } catch (e) {
      // Ignored non-json ws frame
    }
  };

  window.ws.onerror = () => {
    setLogsConnectionStatus('reconnecting');
  };

  window.ws.onclose = () => {
    stopHeartbeat();
    setLogsConnectionStatus('offline');
    scheduleReconnect();
  };
}

window.addEventListener('online', () => {
  window.wsReconnectDelay = 1500;
  if (window.ws?.readyState !== WebSocket.OPEN && window.ws?.readyState !== WebSocket.CONNECTING) {
    initWebSocket();
  }
});
