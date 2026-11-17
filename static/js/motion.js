/* ═══════════ motion.js — "Kâğıt ve Mürekkep" Merkezi Hareket Motoru ═══════════
 * Tekrar kullanılabilir WAAPI / CSS animationend / View Transitions sarmalayıcısı.
 * Kurallar: yalnızca transform & opacity, sıfır gereksiz rAF döngüsü, tam reduced-motion saygısı.
 */
(function () {
  'use strict';

  const EASE_OUT = 'cubic-bezier(0.22, 1, 0.36, 1)';
  const EASE_MORPH = 'cubic-bezier(0.32, 0.72, 0, 1)';
  const EASE_SPRING = 'linear(0, 0.402 7.4%, 0.711 15.3%, 0.929 23.7%, 1.008 33.3%, 1.067 41.6%, 1.059 49.2%, 1.015 61.5%, 0.999 74%, 1)';

  function resolveEl(target) {
    if (!target) return null;
    if (typeof target === 'string') return document.querySelector(target);
    return target instanceof Element ? target : null;
  }

  function reduced() {
    return Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function _finiteAnims(el) {
    if (typeof el.getAnimations !== 'function') return [];
    return el.getAnimations({ subtree: false }).filter((a) => {
      try {
        const iters = a.effect && typeof a.effect.getComputedTiming === 'function'
          ? a.effect.getComputedTiming().iterations
          : 1;
        return iters !== Infinity;
      } catch (_) {
        return true;
      }
    });
  }

  function waitAnimations(el) {
    return new Promise((resolve) => {
      let resolved = false;
      const safetyTimer = setTimeout(() => done(), 650);
      const done = () => {
        if (resolved) return;
        resolved = true;
        clearTimeout(safetyTimer);
        el.removeEventListener('animationend', done);
        el.removeEventListener('animationcancel', done);
        resolve();
      };

      el.addEventListener('animationend', done, { once: true });
      el.addEventListener('animationcancel', done, { once: true });

      requestAnimationFrame(() => {
        if (resolved) return;
        if (!el.isConnected) {
          done();
          return;
        }
        const anims = _finiteAnims(el);
        if (anims.length > 0) {
          Promise.allSettled(anims.map((a) => a.finished)).then(done);
        } else {
          requestAnimationFrame(() => {
            if (resolved) return;
            const retryAnims = _finiteAnims(el);
            if (retryAnims.length > 0) {
              Promise.allSettled(retryAnims.map((a) => a.finished)).then(done);
            } else {
              done();
            }
          });
        }
      });
    });
  }

  /**
   * Öğeyi kökeniyle ve kâğıt yerleşimiyle sahneye alır.
   */
  function enter(target, opts = {}) {
    const el = resolveEl(target);
    if (!el) return Promise.resolve();

    const {
      className = 'm-enter',
      addClass = null,
      removeClass = null,
      origin = null,
      focusEl = null,
      showDisplay = null,
      cleanExitClass = 'closing'
    } = opts;

    el._motionToken = (el._motionToken || 0) + 1;
    const myToken = el._motionToken;

    el.classList.remove('m-exit', cleanExitClass);
    if (removeClass) el.classList.remove(removeClass);
    if (showDisplay !== null) el.style.display = showDisplay;
    if (origin) el.style.transformOrigin = origin;
    if (addClass) el.classList.add(addClass);

    if (reduced()) {
      if (focusEl) {
        const f = resolveEl(focusEl);
        if (f && typeof f.focus === 'function') f.focus();
      }
      return Promise.resolve();
    }

    if (className) {
      el.classList.remove(className);
      void el.offsetWidth;
      el.classList.add(className);
    }

    if (focusEl) {
      requestAnimationFrame(() => {
        if (el._motionToken !== myToken) return;
        const f = resolveEl(focusEl);
        if (f && typeof f.focus === 'function') f.focus();
      });
    }

    return waitAnimations(el).then(() => {
      if (el._motionToken === myToken && className && className === 'm-enter') {
        el.classList.remove('m-enter');
      }
    });
  }

  /**
   * Öğeyi animasyon/transition bitiminde temiz biçimde kapatır (animationend / finished tabanlı).
   */
  function exit(target, opts = {}) {
    const el = resolveEl(target);
    if (!el) return Promise.resolve();

    const {
      className = 'closing',
      removeClass = null,
      hideDisplay = false,
      afterFn = null
    } = opts;

    el._motionToken = (el._motionToken || 0) + 1;
    const myToken = el._motionToken;

    if (removeClass) el.classList.remove(removeClass);
    el.classList.remove('m-enter');

    const finalize = () => {
      if (el._motionToken !== myToken) return;
      if (className) el.classList.remove(className);
      if (hideDisplay) el.style.display = 'none';
      if (typeof afterFn === 'function') afterFn(el);
    };

    if (reduced()) {
      finalize();
      return Promise.resolve();
    }

    if (className) el.classList.add(className);

    return waitAnimations(el).then(finalize);
  }

  /**
   * Liste/ızgara öğelerine sınırlı, hafif kademeli giriş uygular.
   */
  function stagger(nodes, opts = {}) {
    const list = Array.from(nodes || []).filter((n) => n && n.nodeType === 1);
    if (!list.length || reduced()) return;

    const {
      limit = 12,
      step = 28,
      maxDelay = 308,
      y = 10,
      duration = 260,
      easing = EASE_OUT
    } = opts;

    const slice = list.slice(0, limit);
    slice.forEach((node, idx) => {
      if (node._staggerAnim) {
        try { node._staggerAnim.cancel(); } catch (_) {}
        node._staggerAnim = null;
      }
      if (typeof node.animate === 'function') {
        const delay = Math.min(idx * step, maxDelay);
        const anim = node.animate([
          { opacity: 0, transform: `translate3d(0, ${y}px, 0)` },
          { opacity: 1, transform: 'translate3d(0, 0, 0)' }
        ], {
          duration,
          delay,
          easing,
          fill: 'backwards'
        });
        node._staggerAnim = anim;
        anim.addEventListener('finish', () => {
          if (node._staggerAnim === anim) node._staggerAnim = null;
        }, { once: true });
      }
    });
  }

  /**
   * FLIP konum geçişi (yalnızca transform: translate3d ile).
   * Kullanım A: Motion.flip(items, () => mutate(), opts)
   * Kullanım B: Motion.flip(containerOrItems, prevRectsMap, opts)
   */
  function flip(target, mutateOrPrevRects, opts = {}) {
    if (!target) return;
    const {
      duration = 280,
      spring = false,
      selector = null,
      newlyRevealed = []
    } = opts;

    let elements = [];
    if (target instanceof Element) {
      elements = selector
        ? Array.from(target.querySelectorAll(selector))
        : Array.from(target.children);
    } else if (target && typeof target[Symbol.iterator] === 'function') {
      elements = Array.from(target).filter((n) => n instanceof Element);
    }

    if (reduced()) {
      if (typeof mutateOrPrevRects === 'function') mutateOrPrevRects();
      return;
    }

    let prevRects = null;
    if (typeof mutateOrPrevRects === 'function') {
      prevRects = new Map();
      for (const el of elements) {
        if (el.style.display === 'none') continue;
        const r = el.getBoundingClientRect();
        if (r.width && r.height) prevRects.set(el, r);
      }
      mutateOrPrevRects();
      if (target instanceof Element && selector) {
        elements = Array.from(target.querySelectorAll(selector));
      } else if (target instanceof Element) {
        elements = Array.from(target.children);
      }
    } else if (mutateOrPrevRects instanceof Map) {
      prevRects = mutateOrPrevRects;
    }

    let easing = spring ? EASE_SPRING : EASE_OUT;
    if (spring && window.CSS && typeof CSS.supports === 'function' && !CSS.supports('animation-timing-function', EASE_SPRING)) {
      easing = 'cubic-bezier(0.25, 1.25, 0.4, 1)';
    }

    const vh = window.innerHeight || 900;
    const moves = [];

    if (prevRects && prevRects.size > 0) {
      const resolvedPairs = [];
      prevRects.forEach((oldRect, key) => {
        const el = key instanceof Element
          ? key
          : (target instanceof Element ? target.querySelector(`[data-hash="${key}"], [data-task-id="${key}"]`) : null);
        if (!el || !el.isConnected || el.style.display === 'none') return;
        // Cancel any in-flight FLIP animation BEFORE measuring newRect so interrupted transforms never accumulate!
        if (el._flipAnim) {
          try { el._flipAnim.cancel(); } catch (_) {}
          el._flipAnim = null;
        }
        resolvedPairs.push([el, oldRect]);
      });

      for (const [el, oldRect] of resolvedPairs) {
        const newRect = el.getBoundingClientRect();
        if (!newRect.width || newRect.bottom < -180 || newRect.top > vh + 240) continue;
        const dx = oldRect.left - newRect.left;
        const dy = oldRect.top - newRect.top;
        if (Math.abs(dx) > 1.5 || Math.abs(dy) > 1.5) {
          moves.push({ el, dx, dy });
        }
      }
    }

    for (const { el, dx, dy } of moves) {
      if (typeof el.animate === 'function') {
        try {
          el._flipAnim = el.animate([
            { transform: `translate3d(${dx}px, ${dy}px, 0)` },
            { transform: 'none' }
          ], { duration, easing });
        } catch (_) {
          el._flipAnim = el.animate([
            { transform: `translate3d(${dx}px, ${dy}px, 0)` },
            { transform: 'none' }
          ], { duration, easing: EASE_OUT });
        }
        const a = el._flipAnim;
        a.addEventListener('finish', () => {
          if (el._flipAnim === a) el._flipAnim = null;
        }, { once: true });
      }
    }

    if (newlyRevealed && newlyRevealed.length) {
      const visibleNew = newlyRevealed.filter((el) => {
        if (!el || !el.isConnected || el.style.display === 'none') return false;
        const r = el.getBoundingClientRect();
        return r.width && r.bottom >= -120 && r.top <= vh + 200;
      });
      stagger(visibleNew, { limit: 12, step: 22, y: 12, duration: 280 });
    }
  }

  /**
   * Segmented control aktif göstergesini yalnızca transform (translate3d + scaleX/scaleY) ile kaydırır.
   */
  function glidePill(containerOrSelector, prevBtn, nextBtn, prevRectOverride = null) {
    if (reduced()) return;
    const container = typeof containerOrSelector === 'string'
      ? document.querySelector(containerOrSelector)
      : containerOrSelector;
    if (!container || !prevBtn || !nextBtn || prevBtn === nextBtn) return;
    if (!container.contains(prevBtn) || !container.contains(nextBtn)) return;

    const cRect = container.getBoundingClientRect();
    const pRect = prevRectOverride || prevBtn.getBoundingClientRect();
    const nRect = nextBtn.getBoundingClientRect();
    if (!pRect.width || !nRect.width || !pRect.height || !nRect.height) return;

    container.querySelectorAll('.seg-glide-indicator').forEach((el) => el.remove());

    const pill = document.createElement('span');
    pill.className = 'seg-glide-indicator';
    pill.style.width = `${nRect.width}px`;
    pill.style.height = `${nRect.height}px`;
    const targetStyle = window.getComputedStyle(nextBtn);
    if (targetStyle.borderRadius) {
      pill.style.borderRadius = targetStyle.borderRadius;
    }

    const xFrom = pRect.left - cRect.left + container.scrollLeft;
    const yFrom = pRect.top - cRect.top + container.scrollTop;
    const xTo = nRect.left - cRect.left + container.scrollLeft;
    const yTo = nRect.top - cRect.top + container.scrollTop;
    const sx = pRect.width / nRect.width;
    const sy = pRect.height / nRect.height;

    container.appendChild(pill);
    nextBtn.classList.add('is-gliding-target');

    let cleaned = false;
    const cleanup = () => {
      if (cleaned) return;
      cleaned = true;
      pill.remove();
      nextBtn.classList.remove('is-gliding-target');
    };

    if (typeof pill.animate === 'function') {
      const anim = pill.animate([
        { transform: `translate3d(${xFrom}px, ${yFrom}px, 0) scale(${sx.toFixed(4)}, ${sy.toFixed(4)})` },
        { transform: `translate3d(${xTo}px, ${yTo}px, 0) scale(1, 1)` }
      ], {
        duration: 280,
        easing: EASE_OUT
      });
      anim.addEventListener('finish', cleanup, { once: true });
      anim.addEventListener('cancel', cleanup, { once: true });
    } else {
      cleanup();
    }
  }

  /**
   * View Transitions API sarmalayıcısı (tarayıcı desteği veya reduced-motion yoksa zarif fallback).
   */
  function transition(fn, opts = {}) {
    if (typeof fn !== 'function') return Promise.resolve();
    const { name = null, fromEl = null, toEl = null } = opts;

    const src = resolveEl(fromEl);

    if (!document.startViewTransition || reduced()) {
      fn();
      return Promise.resolve();
    }

    if (src && name) {
      src.style.viewTransitionName = name;
    }

    let vt;
    try {
      vt = document.startViewTransition(() => {
        if (src && name) {
          src.style.removeProperty('view-transition-name');
        }
        fn();
        if (name) {
          const dst = typeof toEl === 'function' ? resolveEl(toEl()) : resolveEl(toEl);
          if (dst) dst.style.viewTransitionName = name;
        }
      });
    } catch (_) {
      if (src && name) src.style.removeProperty('view-transition-name');
      fn();
      return Promise.resolve();
    }

    return vt.finished.finally(() => {
      if (src && name) src.style.removeProperty('view-transition-name');
      if (name) {
        const dst = typeof toEl === 'function' ? resolveEl(toEl()) : resolveEl(toEl);
        if (dst) dst.style.removeProperty('view-transition-name');
      }
    });
  }

  const Motion = {
    EASE_OUT,
    EASE_MORPH,
    EASE_SPRING,
    reduced,
    enter,
    exit,
    stagger,
    flip,
    glidePill,
    transition
  };

  window.Motion = Motion;
  window.isMotionReduced = reduced;
  window.animateSegmentedPill = glidePill;
})();
