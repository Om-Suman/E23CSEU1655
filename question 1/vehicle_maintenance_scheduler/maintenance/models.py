"""
Django models for maintenance application.

Currently using stateless architecture with external API integration.
Models can be extended as needed for caching or audit logging.
"""

from django.db import models


class AuditLog(models.Model):
    """
    Audit log for API requests and responses.
    
    Useful for debugging, monitoring, and compliance tracking.
    """
    
    class Status(models.TextChoices):
        """Status choices for API requests."""
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'
        ERROR = 'error', 'Error'
    
    endpoint = models.CharField(
        max_length=255,
        help_text='API endpoint called'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESS
    )
    request_data = models.JSONField(
        default=dict,
        help_text='Request parameters'
    )
    response_data = models.JSONField(
        default=dict,
        help_text='Response data'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error details if request failed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['endpoint', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f'{self.endpoint} - {self.status} ({self.created_at})'


class ScheduleCache(models.Model):
    """
    Cache for schedule optimization results.
    
    Reduces API calls and computation time for repeated requests.
    """
    
    cache_key = models.CharField(
        max_length=255,
        unique=True,
        help_text='Unique cache identifier'
    )
    result = models.JSONField(
        help_text='Cached optimization result'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text='Cache expiration time'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'Cache: {self.cache_key}'
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at
