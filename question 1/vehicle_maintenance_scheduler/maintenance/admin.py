"""
Django admin configuration for maintenance application.
"""

from django.contrib import admin
from .models import AuditLog, ScheduleCache


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AuditLog model."""
    
    list_display = ('endpoint', 'status', 'created_at')
    list_filter = ('status', 'endpoint', 'created_at')
    search_fields = ('endpoint', 'error_message')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Request Details', {
            'fields': ('endpoint', 'request_data')
        }),
        ('Response Details', {
            'fields': ('status', 'response_data', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ScheduleCache)
class ScheduleCacheAdmin(admin.ModelAdmin):
    """Admin configuration for ScheduleCache model."""
    
    list_display = ('cache_key', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('cache_key',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Cache Details', {
            'fields': ('cache_key', 'result')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
