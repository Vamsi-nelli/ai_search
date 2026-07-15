/**
 * Smart Commerce AI — Search JavaScript (search.js)
 * Handles AI-powered search via fetch(), result rendering, filters, pagination.
 */

'use strict';

// ─── State ────────────────────────────────────────────────────────────────────
const state = {
  query: '',
  results: [],
  currentPage: 1,
  totalPages: 1,
  total: 0,
  isLoading: false,
  currentView: 'grid',
};

// ─── DOM Refs ─────────────────────────────────────────────────────────────────
const getEl = (id) => document.getElementById(id);

// ─── Main Search Entry Point ──────────────────────────────────────────────────

/**
 * triggerSearch — called from template's DOMContentLoaded or search button click.
 * @param {string} [queryOverride] - Optional query override (from URL param).
 */
function triggerSearch(queryOverride) {
  const input = getEl('search-input');
  if (!input) return;

  const q = queryOverride || input.value.trim();
  if (!q) return;

  if (queryOverride) input.value = q;

  state.query = q;
  state.currentPage = 1;
  state.results = [];

  performSearch(q, 1);
}

/**
 * applyFilters — called when "Apply Filters" sidebar button is clicked.
 */
function applyFilters() {
  state.currentPage = 1;
  state.results = [];
  performSearch(state.query, 1);
}

/**
 * loadMore — loads the next page of results.
 */
function loadMore() {
  if (state.currentPage < state.totalPages) {
    state.currentPage++;
    performSearch(state.query, state.currentPage, true);
  }
}

/**
 * clearFilters — resets all sidebar filters and re-runs search.
 */
function clearFilters() {
  const fields = ['filter-category', 'filter-sort'];
  fields.forEach(id => { const el = getEl(id); if (el) el.value = ''; });

  const priceMin = getEl('filter-price-min');
  const priceMax = getEl('filter-price-max');
  if (priceMin) priceMin.value = '';
  if (priceMax) priceMax.value = '';

  const stockCheck = getEl('filter-in-stock');
  if (stockCheck) stockCheck.checked = false;

  document.querySelectorAll('.rating-radio').forEach(r => r.checked = false);

  if (state.query) applyFilters();
}

/**
 * setView — switch between grid and list layout.
 */
function setView(view) {
  state.currentView = view;
  const grid = getEl('search-results-grid');
  if (!grid) return;
  if (view === 'list') {
    grid.classList.add('list-view');
    getEl('view-list-btn')?.classList.add('active');
    getEl('view-grid-btn')?.classList.remove('active');
  } else {
    grid.classList.remove('list-view');
    getEl('view-grid-btn')?.classList.add('active');
    getEl('view-list-btn')?.classList.remove('active');
  }
}

// ─── Core Search Function ─────────────────────────────────────────────────────

async function performSearch(query, page = 1, append = false) {
  if (state.isLoading) return;

  state.isLoading = true;
  showThinking(true);
  hideStates();

  // Build request body
  const body = {
    query,
    page,
    category_id: getEl('filter-category')?.value || null,
    price_min: getEl('filter-price-min')?.value || null,
    price_max: getEl('filter-price-max')?.value || null,
    rating_min: document.querySelector('.rating-radio:checked')?.value || null,
    availability: getEl('filter-in-stock')?.checked ? 'in_stock' : null,
    sort_by: getEl('filter-sort')?.value || '',
  };

  // Remove null values
  Object.keys(body).forEach(k => { if (!body[k]) delete body[k]; });

  try {
    const response = await fetch('/api/search/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error || `HTTP ${response.status}`);
    }

    const data = await response.json();

    // Update state
    state.totalPages = data.total_pages || 1;
    state.total = data.total || 0;

    if (append) {
      state.results = [...state.results, ...data.products];
    } else {
      state.results = data.products;
    }

    // Render
    renderInsight(data);
    renderResults(data.products, append);
    renderResultsHeader(data.total);
    renderPagination();

    if (data.products.length === 0 && !append) {
      showEmptyState();
    }

  } catch (err) {
    console.error('Search error:', err);
    showErrorState(err.message);
  } finally {
    state.isLoading = false;
    showThinking(false);
  }
}

// ─── Rendering Functions ──────────────────────────────────────────────────────

function renderInsight(data) {
  const bar = getEl('ai-insight-bar');
  const text = getEl('ai-insight-text');
  const keywordsWrap = getEl('ai-keywords-wrap');
  if (!bar || !text) return;

  let insightText = '';
  if (data.problem) insightText += `Problem: "${data.problem}"`;
  if (data.category) insightText += ` → Category: ${data.category}`;
  text.textContent = insightText || 'AI analyzed your query';

  if (keywordsWrap && data.keywords?.length) {
    keywordsWrap.innerHTML = data.keywords
      .slice(0, 6)
      .map(k => `<span class="ai-keyword-chip">${escHtml(k)}</span>`)
      .join('');
  }

  bar.style.display = 'flex';
}

function renderResultsHeader(total) {
  const header = getEl('results-header');
  const countEl = getEl('results-count');
  if (!header || !countEl) return;
  countEl.textContent = `${total.toLocaleString()} product${total !== 1 ? 's' : ''} found`;
  header.style.display = 'flex';
}

function renderResults(products, append = false) {
  const grid = getEl('search-results-grid');
  if (!grid) return;

  if (!append) {
    grid.innerHTML = '';
    if (state.currentView === 'list') grid.classList.add('list-view');
  }

  if (!products || products.length === 0) return;

  products.forEach((product, index) => {
    const card = createProductCard(product);
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    grid.appendChild(card);

    // Staggered fade-in
    setTimeout(() => {
      card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, Math.min(index * 40, 400));
  });
}

function renderPagination() {
  const wrap = getEl('pagination-wrap');
  const btn = getEl('load-more-btn');
  if (!wrap || !btn) return;
  if (state.currentPage < state.totalPages) {
    wrap.style.display = 'block';
    btn.disabled = false;
    btn.innerHTML = `<i class="bi bi-arrow-down-circle me-2"></i>Load More Products`;
  } else {
    wrap.style.display = 'none';
  }
}

function createProductCard(p) {
  const card = document.createElement('article');
  card.className = 'product-card';
  card.dataset.productId = p.id;

  const priceBadge = p.discount_percentage > 0
    ? `<span class="product-badge product-badge--discount">-${p.discount_percentage}%</span>` : '';
  const outOfStock = !p.in_stock
    ? `<span class="product-badge product-badge--out">Out of Stock</span>` : '';

  const starsHtml = renderStars(p.rating);
  const discountPriceHtml = p.discount_price
    ? `<span class="product-price-old">₹${p.price.toFixed(2)}</span>` : '';

  card.innerHTML = `
    <a href="/products/${p.slug}/" class="product-card-link" aria-label="${escHtml(p.name)}">
      <div class="product-body">
        <span class="product-category">${escHtml(p.category || '')}</span>
        <h3 class="product-name">${escHtml(p.name)}</h3>
        <p class="product-desc">${escHtml(truncate(p.short_description, 80))}</p>
        <div class="product-rating" aria-label="Rating ${p.rating} out of 5">
          ${starsHtml}
          <span class="rating-count">(${(p.review_count || 0).toLocaleString()})</span>
        </div>
        <div class="product-price-row">
          <span class="product-price">₹${(p.effective_price || p.price).toFixed(2)}</span>
          ${discountPriceHtml}
        </div>
      </div>
    </a>
    <div class="product-footer">
      <span class="product-brand">${escHtml(p.brand || '')}</span>
      <a href="/products/${p.slug}/" class="sc-btn sc-btn--primary sc-btn--sm">
        View <i class="bi bi-arrow-right ms-1"></i>
      </a>
    </div>`;

  return card;
}

function renderStars(rating) {
  let html = '';
  for (let i = 1; i <= 5; i++) {
    if (i <= Math.floor(rating)) {
      html += '<i class="bi bi-star-fill star-filled"></i>';
    } else {
      html += '<i class="bi bi-star star-empty"></i>';
    }
  }
  return html;
}

// ─── UI Helpers ───────────────────────────────────────────────────────────────

function showThinking(show) {
  const bar = getEl('ai-thinking-bar');
  if (!bar) return;
  bar.style.display = show ? 'block' : 'none';

  if (show) {
    const messages = [
      'Analyzing your problem with Grok AI...',
      'Understanding your intent...',
      'Extracting search keywords...',
      'Finding matching products...',
    ];
    let i = 0;
    const textEl = getEl('ai-thinking-text');
    if (textEl && !showThinking._interval) {
      showThinking._interval = setInterval(() => {
        if (textEl) textEl.textContent = messages[i % messages.length];
        i++;
      }, 900);
    }
  } else {
    if (showThinking._interval) {
      clearInterval(showThinking._interval);
      showThinking._interval = null;
    }
  }
}

function hideStates() {
  const ids = ['empty-state', 'error-state'];
  ids.forEach(id => { const el = getEl(id); if (el) el.style.display = 'none'; });
}

function showEmptyState() {
  const el = getEl('empty-state');
  if (el) el.style.display = 'block';
  const header = getEl('results-header');
  if (header) header.style.display = 'none';
}

function showErrorState(msg) {
  const el = getEl('error-state');
  const title = getEl('error-title');
  const desc = getEl('error-desc');
  if (el) el.style.display = 'block';
  if (title) title.textContent = 'Search Failed';
  if (desc) desc.textContent = msg || 'Please check your connection and try again.';
}

// ─── Utilities ────────────────────────────────────────────────────────────────

function getCsrfToken() {
  const el = document.querySelector('[name=csrfmiddlewaretoken]');
  if (el) return el.value;
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function truncate(str, max) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}

// ─── Event Listeners ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  const searchInput = getEl('search-input');
  const searchBtn = getEl('search-btn');

  if (searchInput) {
    searchInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        triggerSearch();
      }
    });
  }

  if (searchBtn) {
    searchBtn.addEventListener('click', function () {
      triggerSearch();
    });
  }
});
