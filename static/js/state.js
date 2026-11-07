/* ═══════════ state.js — Global State & Constants ═══════════ */
var allBooks = [];
var currentPage = 1;
var totalBooks = 0;
var isLoadingMore = false;
var allCollections = [];
var activeCategory = 'all';
var activeCollection = 'all';
var currentView = 'grid';
var sortCol = -1, sortDir = 1;
var opsActiveTab = 'all';
var lastActiveTasks = {};
var lastArchivedTasks = {};
var pendingUploads = new Set();
var uploadingCards = new Map();   // tempId -> {card, bar, label}
var taskToTemp = new Map();       // taskId -> tempId
var telegramDlCards = new Map();   // filename -> tempId
var currentModalHash = null;      // Track open book in modal
var isSelectionMode = false;      // Is bulk selection mode active?
var selectedBooks = new Set();    // Hash list of selected books
var showOnlyFav = false;          // Is "Show favorites only" active?
var appSettings = {};             // Sunucudan gelen ayarlar
var completedTasks = new Set();
var currentLogCategory = 'all';
var currentLogLevel = 'all';
var currentLogSearch = '';
var isLogLivePaused = false;
var isLogAutoScroll = true;
var unreadLogErrors = 0;
var cachedLogs = [];
var ws = null;
var wsReconnectTimer = null;
var wsReconnectDelay = 1500;
var colTargetHash = null;
var dragSrcEl = null;
var customOrder = JSON.parse(localStorage.getItem('kutuphane-custom-order') || 'null');
var network = null;
var networkFocusBookHash = null;
var isDeepSearchActive = false;


const BOOK_ICON_LG = `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" style="color:var(--sepia-light)"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;
const BOOK_ICON_SM = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:var(--sepia-light)"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`;
const DONUT_COLORS = ['#6e614c', '#82745e', '#e8a87c', '#82745e', '#b9b3a6', '#e6e1d6', '#5a8a6e', '#7eb8a0', '#4a7a9b', '#7fb3d4', '#9b6ea0', '#c49bc7'];

/* ═══════════ Toast Notification System ═══════════ */
function showToast(message, type = 'info', duration = 3800) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;

  const iconMap = {
    success: 'fa-circle-check',
    error: 'fa-circle-exclamation',
    warning: 'fa-triangle-exclamation',
    info: 'fa-circle-info'
  };
  const icon = iconMap[type] || 'fa-circle-info';

  const escapeHtml = (str) => {
    return (str || '').toString()
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  };
  const formattedMsg = escapeHtml(message).replaceAll('\n', '<br>');

  toast.innerHTML = `
    <div class="toast-icon"><i class="fas ${icon}"></i></div>
    <div class="toast-content">${formattedMsg}</div>
    <button class="toast-close" onclick="this.closest('.toast-item').remove()" aria-label="Kapat">&times;</button>
  `;

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  let dismissTimer = setTimeout(() => {
    toast.classList.remove('show');
    toast.classList.add('hide');
    setTimeout(() => toast.remove(), 280);
  }, duration);

  toast.addEventListener('mouseenter', () => clearTimeout(dismissTimer));
  toast.addEventListener('mouseleave', () => {
    dismissTimer = setTimeout(() => {
      toast.classList.remove('show');
      toast.classList.add('hide');
      setTimeout(() => toast.remove(), 280);
    }, 1200);
  });
}

window.showToast = showToast;
window.showNotification = showToast;
window.toast = {
  success: (msg, dur) => showToast(msg, 'success', dur),
  error: (msg, dur) => showToast(msg, 'error', dur || 5000),
  warning: (msg, dur) => showToast(msg, 'warning', dur),
  info: (msg, dur) => showToast(msg, 'info', dur)
};

