/**
 * Smart Commerce AI — Animations JS (animations.js)
 * Subtle UI animations: scroll reveal, navbar scroll effect, etc.
 */

'use strict';

// ─── Navbar Scroll Effect ─────────────────────────────────────────────────────
(function () {
  const navbar = document.getElementById('main-navbar');
  if (!navbar) return;

  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const current = window.scrollY;
    if (current > 60) {
      navbar.style.boxShadow = '0 4px 24px rgba(0,0,0,0.10)';
    } else {
      navbar.style.boxShadow = '0 2px 12px rgba(0,0,0,0.05)';
    }
    lastScroll = current;
  }, { passive: true });
})();

// ─── Scroll Reveal for Cards ──────────────────────────────────────────────────
(function () {
  const observerOptions = {
    threshold: 0.08,
    rootMargin: '0px 0px -40px 0px',
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('sc-revealed');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  function observeCards() {
    document.querySelectorAll('.product-card:not(.sc-revealed), .how-step:not(.sc-revealed), .cat-card:not(.sc-revealed)').forEach(el => {
      el.classList.add('sc-reveal');
      observer.observe(el);
    });
  }

  // Initial observation
  document.addEventListener('DOMContentLoaded', observeCards);

  // Re-observe after dynamic content injection (search results)
  const resultsGrid = document.getElementById('search-results-grid');
  if (resultsGrid) {
    const mutationObserver = new MutationObserver(() => {
      setTimeout(observeCards, 50);
    });
    mutationObserver.observe(resultsGrid, { childList: true });
  }
})();

// ─── Scroll Reveal CSS injection ─────────────────────────────────────────────
(function () {
  const style = document.createElement('style');
  style.textContent = `
    .sc-reveal {
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.45s ease, transform 0.45s ease;
    }
    .sc-revealed {
      opacity: 1 !important;
      transform: translateY(0) !important;
    }
  `;
  document.head.appendChild(style);
})();

// ─── Hero Search: auto-grow textarea ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  const heroInput = document.getElementById('hero-search-input');
  if (!heroInput) return;
  heroInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 140) + 'px';
  });
});

// ─── Smooth Page Transition ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity 0.25s ease';
  requestAnimationFrame(() => {
    document.body.style.opacity = '1';
  });

  // Smooth out-transition on internal link clicks
  document.querySelectorAll('a[href]:not([href^="#"]):not([href^="http"]):not([href^="mailto"])').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href.startsWith('#') || e.ctrlKey || e.metaKey || e.shiftKey) return;
      e.preventDefault();
      document.body.style.opacity = '0';
      setTimeout(() => { window.location.href = href; }, 180);
    });
  });
});

// ─── Add to Cart Ripple Effect ────────────────────────────────────────────────
document.addEventListener('click', function (e) {
  const btn = e.target.closest('.sc-btn--primary');
  if (!btn) return;
  const ripple = document.createElement('span');
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.cssText = `
    position: absolute;
    border-radius: 50%;
    background: rgba(255,255,255,0.35);
    width: ${size}px;
    height: ${size}px;
    left: ${e.clientX - rect.left - size / 2}px;
    top: ${e.clientY - rect.top - size / 2}px;
    transform: scale(0);
    animation: ripple 0.55s ease-out forwards;
    pointer-events: none;
  `;
  if (getComputedStyle(btn).position === 'static') btn.style.position = 'relative';
  btn.style.overflow = 'hidden';
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

// Inject ripple keyframe
(function () {
  const s = document.createElement('style');
  s.textContent = `@keyframes ripple { to { transform: scale(2.5); opacity: 0; } }`;
  document.head.appendChild(s);
})();
