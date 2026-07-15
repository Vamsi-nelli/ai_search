"""
Smart Commerce AI — Root URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('products/', include('products.urls')),
    path('search/', include('search.urls')),
    path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ─── Admin customisation ─────────────────────────────────────────────────────
admin.site.site_header = 'Smart Commerce AI'
admin.site.site_title = 'Smart Commerce Admin'
admin.site.index_title = 'Dashboard'
