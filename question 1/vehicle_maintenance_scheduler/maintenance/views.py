"""
API views for vehicle maintenance scheduler microservice.

Implements the GET /api/schedule/ endpoint with optimization logic.
"""

import logging
from datetime import datetime
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import get_external_api_service
from .knapsack import get_knapsack_optimizer
from .serializers import ScheduleResponseSerializer, ErrorResponseSerializer

logger = logging.getLogger(__name__)


class ScheduleAPIView(APIView):
    """
    API endpoint for vehicle maintenance schedule optimization.
    
    Fetches depot and vehicle data from external API, applies knapsack
    optimization algorithm, and returns optimal task assignments per depot.
    
    Methods:
        GET: Get optimized maintenance schedule
    """
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for schedule optimization.
        
        Returns:
            JSON response with optimization results or error details
        """
        try:
            # Log request
            logger.info(f'Schedule optimization request received from {request.META.get("REMOTE_ADDR")}')
            
            # Fetch data from external APIs
            api_service = get_external_api_service()
            success, data, error = api_service.fetch_all_data()
            
            if not success:
                logger.error(f'External API error: {error}')
                return self._error_response(
                    message='Failed to fetch data from external service',
                    details=error,
                    status_code=status.HTTP_502_BAD_GATEWAY
                )
            
            depots = data.get('depots', [])
            vehicles = data.get('vehicles', [])
            
            # Validate fetched data
            if not depots or not vehicles:
                logger.warning('Empty depots or vehicles data from external API')
                return self._error_response(
                    message='No depots or vehicles available',
                    details='External API returned empty data',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f'Fetched {len(depots)} depots and {len(vehicles)} vehicles')
            
            # Run optimization
            optimizer = get_knapsack_optimizer()
            results = optimizer.batch_optimize(depots, vehicles)
            
            if not results:
                logger.error('Optimization returned no results')
                return self._error_response(
                    message='Optimization failed',
                    details='Unable to process depots or vehicles',
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Prepare success response
            response_data = {
                'success': True,
                'results': results,
                'timestamp': timezone.now()
            }
            
            # Validate response format
            serializer = ScheduleResponseSerializer(data=response_data)
            if not serializer.is_valid():
                logger.error(f'Response validation error: {serializer.errors}')
                return self._error_response(
                    message='Internal response validation error',
                    details=str(serializer.errors),
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            logger.info(f'Schedule optimization completed. Results: {len(results)} depots processed')
            
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.exception(f'Unexpected error during schedule optimization: {str(e)}')
            return self._error_response(
                message='Internal server error',
                details=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _error_response(
        self,
        message: str,
        details: str = '',
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> Response:
        """
        Create standardized error response.
        
        Args:
            message: Main error message
            details: Detailed error information
            status_code: HTTP status code
            
        Returns:
            Response object with error data
        """
        response_data = {
            'success': False,
            'error': message,
        }
        
        if details:
            response_data['details'] = details
        
        serializer = ErrorResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status_code)
        
        # Fallback if serializer validation fails
        return Response(response_data, status=status_code)


class HealthCheckAPIView(APIView):
    """
    Health check endpoint for monitoring.
    
    Methods:
        GET: Check service health
    """
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for health check.
        
        Returns:
            JSON response with service status
        """
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'service': 'vehicle_maintenance_scheduler'
        })
