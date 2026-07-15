"""Search App — Admin"""

from django.contrib import admin
from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user_query', 'detected_problem', 'detected_category', 'results_count', 'searched_at')
    search_fields = ('user_query', 'detected_problem', 'detected_category')
    list_filter = ('detected_category', 'searched_at')
    readonly_fields = ('user_query', 'detected_problem', 'detected_category', 'generated_keywords', 'results_count', 'searched_at')
    ordering = ('-searched_at',)
