"""
External API service for fetching depot and vehicle data.

This module handles all communication with the external evaluation service
including authentication and error handling.
"""

import logging
import requests
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class ExternalAPIError(Exception):
    """Custom exception for external API errors."""
    pass


class ExternalAPIService:
    """
    Service class for interacting with external APIs.
    
    Handles authentication, data fetching, and error management
    for depot and vehicle endpoints.
    """
    
    def __init__(self):
        """Initialize the service with configuration from Django settings."""
        self.base_url = settings.EXTERNAL_API_CONFIG['BASE_URL']
        self.token = settings.EXTERNAL_API_CONFIG['TOKEN']
        self.timeout = settings.EXTERNAL_API_CONFIG['TIMEOUT']
        self.headers = self._prepare_headers()
    
    def _prepare_headers(self) -> Dict[str, str]:
        """
        Prepare HTTP headers with Bearer token authentication.
        
        Returns:
            Dict containing authorization and content-type headers.
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
    
    def fetch_depots(self) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Fetch depot information from external API.
        
        Returns:
            Tuple of (success: bool, data: Optional[List], error: Optional[str])
        """
        endpoint = f'{self.base_url}/depots'
        
        try:
            logger.info(f'Fetching depots from {endpoint}')
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            depots = data.get('depots', [])
            
            logger.info(f'Successfully fetched {len(depots)} depots')
            return True, depots, None
            
        except Timeout:
            error_msg = f'Request to {endpoint} timed out after {self.timeout}s'
            logger.error(error_msg)
            return False, None, error_msg
            
        except ConnectionError as e:
            error_msg = f'Connection error while fetching depots: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except requests.exceptions.HTTPError as e:
            error_msg = f'HTTP error {e.response.status_code}: {e.response.text}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except ValueError as e:
            error_msg = f'Invalid JSON response from depots endpoint: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except RequestException as e:
            error_msg = f'Request error while fetching depots: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
    
    def fetch_vehicles(self) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        """
        Fetch vehicle maintenance task information from external API.
        
        Returns:
            Tuple of (success: bool, data: Optional[List], error: Optional[str])
        """
        endpoint = f'{self.base_url}/vehicles'
        
        try:
            logger.info(f'Fetching vehicles from {endpoint}')
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            vehicles = data.get('vehicles', [])
            
            logger.info(f'Successfully fetched {len(vehicles)} vehicles')
            return True, vehicles, None
            
        except Timeout:
            error_msg = f'Request to {endpoint} timed out after {self.timeout}s'
            logger.error(error_msg)
            return False, None, error_msg
            
        except ConnectionError as e:
            error_msg = f'Connection error while fetching vehicles: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except requests.exceptions.HTTPError as e:
            error_msg = f'HTTP error {e.response.status_code}: {e.response.text}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except ValueError as e:
            error_msg = f'Invalid JSON response from vehicles endpoint: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
            
        except RequestException as e:
            error_msg = f'Request error while fetching vehicles: {str(e)}'
            logger.error(error_msg)
            return False, None, error_msg
    
    def fetch_all_data(self) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Fetch both depots and vehicles in a single call.
        
        Returns:
            Tuple of (success: bool, data: Optional[Dict], error: Optional[str])
        """
        # Fetch depots
        depots_success, depots, depots_error = self.fetch_depots()
        if not depots_success:
            return False, None, f'Failed to fetch depots: {depots_error}'
        
        # Fetch vehicles
        vehicles_success, vehicles, vehicles_error = self.fetch_vehicles()
        if not vehicles_success:
            return False, None, f'Failed to fetch vehicles: {vehicles_error}'
        
        return True, {
            'depots': depots,
            'vehicles': vehicles
        }, None


def get_external_api_service() -> ExternalAPIService:
    """
    Factory function to get an instance of ExternalAPIService.
    
    Returns:
        ExternalAPIService instance.
    """
    return ExternalAPIService()
