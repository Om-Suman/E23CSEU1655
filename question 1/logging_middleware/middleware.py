"""
Custom logging middleware for request/response tracking.

Provides comprehensive logging for all HTTP requests and responses
for debugging and monitoring purposes.
"""

import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging HTTP requests and responses.
    
    Captures request metadata, execution time, and response status
    for comprehensive audit trails.
    """
    
    def process_request(self, request):
        """
        Process incoming request.
        
        Args:
            request: Django request object
        """
        # Store request start time
        request._start_time = time.time()
        
        # Log request details
        logger.info(
            f'[REQUEST] {request.method} {request.path} | '
            f'IP: {self._get_client_ip(request)} | '
            f'User: {request.user.username if request.user.is_authenticated else "Anonymous"}'
        )
    
    def process_response(self, request, response):
        """
        Process outgoing response.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Response object
        """
        # Calculate execution time
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        else:
            duration = 0
        
        # Extract status code
        status_code = response.status_code
        
        # Log response details
        logger.info(
            f'[RESPONSE] {request.method} {request.path} | '
            f'Status: {status_code} | '
            f'Duration: {duration:.3f}s'
        )
        
        # Log response body for debugging (truncated for large responses)
        if status_code >= 400:
            try:
                if hasattr(response, 'data'):
                    logger.warning(f'Error response data: {response.data}')
            except Exception:
                pass
        
        return response
    
    def process_exception(self, request, exception):
        """
        Process uncaught exceptions.
        
        Args:
            request: Django request object
            exception: Exception that occurred
            
        Returns:
            None
        """
        logger.error(
            f'[EXCEPTION] {request.method} {request.path} | '
            f'Exception: {type(exception).__name__} - {str(exception)}'
        )
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """
        Extract client IP address from request.
        
        Handles X-Forwarded-For header for proxied requests.
        
        Args:
            request: Django request object
            
        Returns:
            Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware for global error handling and formatting.
    
    Ensures consistent error response format across the application.
    """
    
    def process_exception(self, request, exception):
        """
        Handle uncaught exceptions with consistent format.
        
        Args:
            request: Django request object
            exception: Exception that occurred
            
        Returns:
            JsonResponse with standardized error format or None
        """
        logger.exception(f'Unhandled exception: {str(exception)}')
        
        # Return standardized error response
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'details': str(exception) if logger.level == logging.DEBUG else 'An unexpected error occurred'
        }, status=500)


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware for performance monitoring and metrics.
    
    Tracks slow requests and logs performance metrics for optimization.
    """
    
    SLOW_REQUEST_THRESHOLD = 2.0  # seconds
    
    def process_request(self, request):
        """Store request start time for performance tracking."""
        request._monitor_start_time = time.time()
    
    def process_response(self, request, response):
        """
        Log slow requests and performance metrics.
        
        Args:
            request: Django request object
            response: Django response object
            
        Returns:
            Response object
        """
        if hasattr(request, '_monitor_start_time'):
            duration = time.time() - request._monitor_start_time
            
            if duration > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f'[SLOW_REQUEST] {request.method} {request.path} took {duration:.3f}s '
                    f'(threshold: {self.SLOW_REQUEST_THRESHOLD}s)'
                )
        
        return response
