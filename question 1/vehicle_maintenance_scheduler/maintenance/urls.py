"""
URL routing configuration for maintenance application.

Maps URLs to appropriate views and handlers.
"""

from django.urls import path
from .views import ScheduleAPIView, HealthCheckAPIView

app_name = 'maintenance'

urlpatterns = [
    path('schedule/', ScheduleAPIView.as_view(), name='schedule'),
    path('health/', HealthCheckAPIView.as_view(), name='health'),
]
