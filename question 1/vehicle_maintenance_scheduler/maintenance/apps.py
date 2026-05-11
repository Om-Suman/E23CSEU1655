"""
App configuration for maintenance application.
"""

from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    """Configuration class for the maintenance app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'
