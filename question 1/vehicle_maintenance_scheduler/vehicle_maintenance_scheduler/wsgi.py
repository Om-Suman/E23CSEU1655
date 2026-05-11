"""
WSGI config for vehicle_maintenance_scheduler project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vehicle_maintenance_scheduler.settings')

application = get_wsgi_application()
