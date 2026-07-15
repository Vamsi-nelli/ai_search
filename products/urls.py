"""Products App — URL Configuration"""

from django.urls import path
from .views import product_detail

app_name = 'products'

urlpatterns = [
    path('<slug:slug>/', product_detail, name='detail'),
]
