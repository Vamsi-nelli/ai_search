"""Search App — URL Configuration"""

from django.urls import path
from .views import search_page

app_name = 'search'

urlpatterns = [
    path('', search_page, name='search'),
]
