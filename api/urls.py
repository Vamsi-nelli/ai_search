from django.urls import path
from .views import ChatAPIView, ResetDBAPIView, DBStatsAPIView

app_name = 'api'

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('reset-db/', ResetDBAPIView.as_view(), name='reset_db'),
    path('db-stats/', DBStatsAPIView.as_view(), name='db_stats'),
]
