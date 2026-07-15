"""
Search App — Search Service
Converts AI-extracted intent (keywords, category) into ranked Django ORM queries.
Combines: ILIKE, Full Text Search, Trigram Similarity, Tag matching.
"""

import logging
from typing import Optional
from django.db.models import QuerySet, Q, Value, FloatField, Case, When, IntegerField
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from products.models import Product, Category

logger = logging.getLogger(__name__)


def build_search_queryset(
    keywords: list[str],
    category_name: Optional[str] = None,
    filters: Optional[dict] = None,
) -> QuerySet:
    """
    Build a ranked product queryset from AI-extracted keywords and category.

    Ranking priority (highest to lowest):
      1. AI keyword match in product name (ILIKE)
      2. Tag array overlap
      3. Full-text search vector rank
      4. Trigram similarity on name
      5. Category match bonus
      6. Rating
      7. Popularity (review_count)

    Args:
        keywords: List of product keywords from Grok AI.
        category_name: Optional category name to boost results from.
        filters: Optional dict of additional filters (price_min, price_max, etc.)

    Returns:
        Ranked QuerySet of active Products.
    """
    if not keywords:
        return Product.objects.none()

    filters = filters or {}
    qs = Product.objects.filter(is_active=True).select_related('brand', 'category')

    # ─── 1. Build combined Q filter (ILIKE on name, description, tags) ────
    q_filter = Q()
    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        q_filter |= Q(name__icontains=kw)
        q_filter |= Q(short_description__icontains=kw)
        q_filter |= Q(full_description__icontains=kw)
        q_filter |= Q(tags__contains=[kw])

    # Try searching with keyword filters
    keyword_qs = qs.filter(q_filter)

    # ─── 2. Category filter fallback ─────────────────────────────────────
    if category_name:
        cat_filter = Q(category__name__icontains=category_name)
        # If strict keyword matching returns nothing, fall back to matching the category generally
        if not keyword_qs.exists():
            qs = qs.filter(cat_filter)
        else:
            qs = keyword_qs.filter(cat_filter) | keyword_qs
    else:
        qs = keyword_qs

    if not qs.exists() and category_name:
        # Complete fallback to category products if all else failed
        qs = Product.objects.filter(is_active=True, category__name__icontains=category_name).select_related('brand', 'category')

    # ─── 3. Full Text Search ──────────────────────────────────────────────
    search_phrase = ' '.join(keywords)
    search_query = SearchQuery(search_phrase, search_type='websearch')
    search_vector = SearchVector('name', weight='A') + SearchVector('short_description', weight='B') + SearchVector('full_description', weight='C')
    fts_rank = SearchRank(search_vector, search_query)

    # ─── 4. Trigram similarity on product name ────────────────────────────
    trigram_sim = TrigramSimilarity('name', search_phrase)

    # ─── 5. Combined Scoring ──────────────────────────────────────────────
    # We want to boost items where the keywords strictly match in name/tags/description
    # Create keyword matches score
    keyword_match_score = Value(0, output_field=IntegerField())
    for keyword in keywords:
        kw = keyword.strip()
        if not kw:
            continue
        keyword_match_score += Case(
            When(name__icontains=kw, then=Value(10)),
            default=Value(0),
            output_field=IntegerField()
        )
        keyword_match_score += Case(
            When(tags__contains=[kw], then=Value(8)),
            default=Value(0),
            output_field=IntegerField()
        )
        keyword_match_score += Case(
            When(short_description__icontains=kw, then=Value(5)),
            default=Value(0),
            output_field=IntegerField()
        )

    category_bonus = Case(
        When(category__name__icontains=category_name or '', then=Value(15)),
        default=Value(0),
        output_field=IntegerField(),
    )

    qs = (
        qs
        .annotate(
            keyword_score=keyword_match_score,
            fts_rank=fts_rank,
            trigram_sim=trigram_sim,
            category_bonus=category_bonus,
        )
        .order_by(
            '-keyword_score',
            '-category_bonus',
            '-fts_rank',
            '-trigram_sim',
            '-rating',
            '-review_count',
        )
    )

    # ─── 6. Apply additional sidebar filters ──────────────────────────────
    qs = _apply_filters(qs, filters)

    return qs


def _apply_filters(qs: QuerySet, filters: dict) -> QuerySet:
    """Apply sidebar filters from the search page."""
    if price_min := filters.get('price_min'):
        qs = qs.filter(price__gte=float(price_min))
    if price_max := filters.get('price_max'):
        qs = qs.filter(price__lte=float(price_max))
    if brand_id := filters.get('brand'):
        qs = qs.filter(brand_id=brand_id)
    if category_id := filters.get('category_id'):
        qs = qs.filter(category_id=category_id)
    if rating_min := filters.get('rating_min'):
        qs = qs.filter(rating__gte=float(rating_min))
    if availability := filters.get('availability'):
        if availability == 'in_stock':
            qs = qs.filter(stock__gt=0)

    # Sort override
    sort_by = filters.get('sort_by', '')
    if sort_by == 'price_asc':
        qs = qs.order_by('price')
    elif sort_by == 'price_desc':
        qs = qs.order_by('-price')
    elif sort_by == 'rating':
        qs = qs.order_by('-rating', '-review_count')
    elif sort_by == 'newest':
        qs = qs.order_by('-created_at')

    return qs


def serialize_products(products: QuerySet, limit: int = 20) -> list[dict]:
    """Serialize product queryset to list of dicts for JSON API response."""
    result = []
    for p in products[:limit]:
        result.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price': float(p.price),
            'discount_price': float(p.discount_price) if p.discount_price else None,
            'effective_price': p.effective_price,
            'discount_percentage': p.discount_percentage,
            'rating': float(p.rating),
            'review_count': p.review_count,
            'image': p.image,
            'short_description': p.short_description,
            'category': p.category.name if p.category else '',
            'brand': p.brand.name if p.brand else '',
            'in_stock': p.in_stock,
            'tags': p.tags,
        })
    return result
