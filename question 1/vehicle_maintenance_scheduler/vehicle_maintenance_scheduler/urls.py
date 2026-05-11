"""
URL configuration for vehicle_maintenance_scheduler project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('maintenance.urls')),
]
