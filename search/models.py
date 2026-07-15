"""
Search App — Models
Tracks user search history for analytics and improvement.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField


class SearchHistory(models.Model):
    """
    Records every AI-powered search for analytics.
    Stores the original query, AI-detected intent, and generated keywords.
    """

    user_query = models.TextField()
    detected_problem = models.CharField(max_length=255, blank=True)
    detected_category = models.CharField(max_length=100, blank=True)
    generated_keywords = ArrayField(
        models.CharField(max_length=100),
        blank=True,
        default=list,
    )
    results_count = models.PositiveIntegerField(default=0)
    searched_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = 'Search Histories'
        ordering = ['-searched_at']

    def __str__(self) -> str:
        return f'"{self.user_query}" → {self.detected_problem}'
