"""
Django REST Framework serializers for maintenance application.

Handles serialization and validation of request/response data.
"""

from rest_framework import serializers
from typing import Dict, List, Any


class TaskSerializer(serializers.Serializer):
    """Serializer for maintenance task objects."""
    
    TaskID = serializers.CharField(required=True, max_length=255)
    Duration = serializers.IntegerField(required=True, min_value=0)
    Impact = serializers.IntegerField(required=True, min_value=0)
    
    def validate(self, data):
        """Validate task data."""
        if data['Duration'] == 0 and data['Impact'] == 0:
            raise serializers.ValidationError(
                'Task must have either non-zero Duration or Impact'
            )
        return data


class DepotSerializer(serializers.Serializer):
    """Serializer for depot objects."""
    
    ID = serializers.IntegerField(required=True, min_value=1)
    MechanicHours = serializers.IntegerField(required=True, min_value=1)


class SelectedTaskSerializer(serializers.Serializer):
    """Serializer for selected task in results."""
    
    TaskID = serializers.CharField()
    Duration = serializers.IntegerField()
    Impact = serializers.IntegerField()


class DepotResultSerializer(serializers.Serializer):
    """Serializer for optimization result per depot."""
    
    depotId = serializers.IntegerField()
    mechanicHours = serializers.IntegerField()
    totalImpact = serializers.IntegerField()
    selectedTasks = SelectedTaskSerializer(many=True)


class ScheduleResponseSerializer(serializers.Serializer):
    """Serializer for complete schedule optimization response."""
    
    success = serializers.BooleanField()
    results = DepotResultSerializer(many=True)
    error = serializers.CharField(required=False, allow_blank=True)
    timestamp = serializers.DateTimeField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    
    success = serializers.BooleanField(default=False)
    error = serializers.CharField()
    details = serializers.CharField(required=False, allow_blank=True)
