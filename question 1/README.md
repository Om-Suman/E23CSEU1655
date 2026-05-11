# Vehicle Maintenance Scheduler Microservice

A production-ready Django REST API microservice for optimizing vehicle maintenance task scheduling across multiple depots using 0/1 Knapsack Dynamic Programming algorithm.

## Overview

This microservice integrates with an external evaluation service to fetch depot and vehicle maintenance task information, then applies a sophisticated knapsack optimization algorithm to maximize maintenance impact while respecting mechanic hour constraints.

### Key Features

- **RESTful API**: Clean, documented endpoints following REST principles
- **Knapsack Optimization**: Dynamic programming algorithm for optimal task selection
- **External API Integration**: Seamless integration with external evaluation service
- **Bearer Token Authentication**: Secure API communication
- **Comprehensive Logging**: Request/response tracking and performance monitoring
- **Error Handling**: Robust error handling with detailed error messages
- **Modular Architecture**: Clean separation of concerns (services, views, serializers)
- **Production-Ready**: Security best practices, configuration management, scalable design

## Project Structure

```
question 1/
├── logging_middleware/
│   ├── __init__.py
│   └── middleware.py              # Custom logging and error handling
├── vehicle_maintenance_scheduler/
│   ├── manage.py
│   ├── vehicle_maintenance_scheduler/
│   │   ├── __init__.py
│   │   ├── settings.py            # Django settings
│   │   ├── urls.py                # Project URL routing
│   │   └── wsgi.py                # WSGI configuration
│   └── maintenance/
│       ├── migrations/
│       ├── __init__.py
│       ├── admin.py               # Django admin config
│       ├── apps.py                # App configuration
│       ├── models.py              # Database models
│       ├── serializers.py         # DRF serializers
│       ├── views.py               # API views
│       ├── urls.py                # App URL routing
│       ├── services.py            # External API service
│       └── knapsack.py            # Optimization algorithm
├── notification_app_be/           # Future notification system
│   └── README.md
├── .gitignore
├── .env
├── requirements.txt
└── notification_system_design.md
```

## API Endpoints

### 1. Schedule Optimization Endpoint

**GET** `/api/schedule/`

Returns optimized vehicle maintenance task assignments for all depots.

**Request:**

```bash
curl -X GET http://localhost:8000/api/schedule/
```

**Response (Success):**

```json
{
  "success": true,
  "results": [
    {
      "depotId": 1,
      "mechanicHours": 60,
      "totalImpact": 120,
      "selectedTasks": [
        {
          "TaskID": "abc",
          "Duration": 5,
          "Impact": 10
        },
        {
          "TaskID": "def",
          "Duration": 10,
          "Impact": 20
        }
      ]
    },
    {
      "depotId": 2,
      "mechanicHours": 40,
      "totalImpact": 85,
      "selectedTasks": [
        {
          "TaskID": "ghi",
          "Duration": 8,
          "Impact": 25
        }
      ]
    }
  ],
  "timestamp": "2024-05-11T10:30:45.123Z"
}
```

**Response (Error):**

```json
{
  "success": false,
  "error": "Failed to fetch data from external service",
  "details": "Connection error while fetching depots: [Connection details]"
}
```

### 2. Health Check Endpoint

**GET** `/api/health/`

Check the service health status.

**Request:**

```bash
curl -X GET http://localhost:8000/api/health/
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2024-05-11T10:30:45.123Z",
  "service": "vehicle_maintenance_scheduler"
}
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Virtual environment tool (venv recommended)

### Installation

#### 1. Create and Activate Virtual Environment

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Edit the `.env` file in the project root and set:

```
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

EXTERNAL_API_BASE_URL=http://4.224.186.213/evaluation-service
EXTERNAL_API_TOKEN=your-bearer-token-here

DATABASE_URL=sqlite:///db.sqlite3
```

**Important:** Update `EXTERNAL_API_TOKEN` with your actual bearer token.

#### 4. Navigate to Django Project

```bash
cd vehicle_maintenance_scheduler
```

#### 5. Run Migrations

```bash
python manage.py migrate
```

#### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

#### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

### Development Server Commands

```bash
# Start development server
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000

# Run with autoreload disabled
python manage.py runserver --nothreading --noreload
```

## Testing the API

### Using cURL

```bash
# Test schedule optimization endpoint
curl -X GET http://localhost:8000/api/schedule/

# Test health check
curl -X GET http://localhost:8000/api/health/
```

### Using Python

```python
import requests

# Test schedule endpoint
response = requests.get('http://localhost:8000/api/schedule/')
print(response.json())

# Test health check
response = requests.get('http://localhost:8000/api/health/')
print(response.json())
```

### Using Postman

1. Open Postman
2. Create new GET request
3. Enter URL: `http://localhost:8000/api/schedule/`
4. Click Send

## External API Integration

The microservice communicates with an external evaluation service using Bearer token authentication.

### External API Configuration

**Base URL:** `http://4.224.186.213/evaluation-service`

**Authentication:**

```
Authorization: Bearer {EXTERNAL_API_TOKEN}
```

### API Endpoints Called

#### 1. Get Depots

**Endpoint:** `GET /depots`

**Response:**

```json
{
  "depots": [
    {
      "ID": 1,
      "MechanicHours": 60
    },
    {
      "ID": 2,
      "MechanicHours": 40
    }
  ]
}
```

#### 2. Get Vehicles

**Endpoint:** `GET /vehicles`

**Response:**

```json
{
  "vehicles": [
    {
      "TaskID": "abc",
      "Duration": 5,
      "Impact": 10
    },
    {
      "TaskID": "def",
      "Duration": 10,
      "Impact": 20
    }
  ]
}
```

## Algorithm: 0/1 Knapsack Dynamic Programming

The microservice uses the 0/1 Knapsack algorithm to solve the task selection problem:

### Problem Statement

For each depot, select the optimal subset of vehicle maintenance tasks such that:

- Total Duration ≤ MechanicHours (knapsack capacity)
- Total Impact is maximized (objective function)

### Algorithm Overview

**Time Complexity:** O(n × W) where n = number of tasks, W = mechanic hours
**Space Complexity:** O(n × W)

**Steps:**

1. Create DP table: `dp[i][w]` = maximum impact using first i tasks with w hours
2. Initialize base case: `dp[0][w] = 0` for all w
3. For each task i and each weight w:
   - If task doesn't fit: `dp[i][w] = dp[i-1][w]`
   - If task fits: `dp[i][w] = max(dp[i-1][w], dp[i-1][w-duration] + impact)`
4. Backtrack to find selected tasks

### Example

**Depot:** 60 mechanic hours
**Tasks:**
| TaskID | Duration | Impact |
|--------|----------|--------|
| A | 5 | 10 |
| B | 10 | 20 |
| C | 15 | 30 |
| D | 20 | 40 |

**Optimal Selection:**

- Tasks: B, C, D
- Total Duration: 10 + 15 + 20 = 45 hours (≤ 60)
- Total Impact: 20 + 30 + 40 = 90 (maximized)

## Error Handling

The service implements comprehensive error handling:

### Error Scenarios

| Scenario                      | Status Code | Response                        |
| ----------------------------- | ----------- | ------------------------------- |
| External API timeout          | 502         | Failed to fetch data            |
| Invalid external API response | 502         | Invalid JSON response           |
| Empty data from external API  | 400         | No depots or vehicles available |
| Invalid task data             | 500         | Task validation error           |
| Internal server error         | 500         | Internal server error           |

### Error Response Format

```json
{
  "success": false,
  "error": "Main error message",
  "details": "Detailed error information"
}
```

## Logging

The service provides comprehensive logging for debugging and monitoring.

### Log Levels

- **DEBUG:** Detailed algorithm execution and variable values
- **INFO:** Request/response flow, data fetch operations
- **WARNING:** Empty data, validation issues, slow requests
- **ERROR:** API failures, validation errors
- **CRITICAL:** System-level failures

### Log Files

- Console output (real-time)
- `debug.log` (file-based logging)

### Log Format

```
[LEVEL] [TIMESTAMP] [MODULE] [MESSAGE]
```

### Example Logs

```
INFO 2024-05-11 10:30:45 maintenance [REQUEST] GET /api/schedule/ | IP: 127.0.0.1 | User: Anonymous
INFO 2024-05-11 10:30:45 maintenance Fetching depots from http://4.224.186.213/evaluation-service/depots
INFO 2024-05-11 10:30:46 maintenance Successfully fetched 2 depots
INFO 2024-05-11 10:30:46 maintenance Successfully fetched 5 vehicles
INFO 2024-05-11 10:30:46 maintenance Optimization complete. Max impact: 90, Selected 3 tasks
INFO 2024-05-11 10:30:46 maintenance Schedule optimization completed. Results: 2 depots processed
INFO 2024-05-11 10:30:46 maintenance [RESPONSE] GET /api/schedule/ | Status: 200 | Duration: 1.234s
```

## Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn vehicle_maintenance_scheduler.wsgi:application --bind 0.0.0.0:8000 --workers 4

# With additional options
gunicorn vehicle_maintenance_scheduler.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread \
  --max-requests 1000 \
  --timeout 60
```

### Environment Configuration for Production

```
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

EXTERNAL_API_BASE_URL=http://4.224.186.213/evaluation-service
EXTERNAL_API_TOKEN=your-production-token

DATABASE_URL=postgresql://user:password@localhost/dbname
```

### Security Checklist

- [ ] Change `SECRET_KEY` to a random string
- [ ] Set `DEBUG=False`
- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Update `EXTERNAL_API_TOKEN` with production token
- [ ] Use PostgreSQL or other production database
- [ ] Enable HTTPS
- [ ] Set `CSRF_TRUSTED_ORIGINS`
- [ ] Configure CORS headers if needed
- [ ] Use environment secrets management
- [ ] Enable rate limiting
- [ ] Configure proper logging
- [ ] Set up monitoring and alerting

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (nginx, HAProxy)
- Run multiple Gunicorn workers
- Implement caching for external API responses
- Use message queue (Celery with Redis) for async tasks

### Vertical Scaling

- Increase worker processes
- Optimize database queries
- Cache frequently accessed data
- Reduce external API calls

### Database Optimization

- Use connection pooling
- Index frequently queried fields
- Archive old audit logs
- Monitor query performance

### Caching Strategy

The `ScheduleCache` model can be used to cache results:

```python
# Implement caching in views.py
cache_key = generate_cache_key(depots, vehicles)
cached_result = ScheduleCache.objects.filter(
    cache_key=cache_key,
    expires_at__gt=timezone.now()
).first()

if cached_result:
    return cached_result.result
```

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'django'"

**Solution:**

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

#### 2. "ConnectionError: Failed to establish a new connection"

**Solution:**

- Verify external API URL is correct
- Check network connectivity
- Verify bearer token is valid

#### 3. "SyntaxError: invalid syntax"

**Solution:**

- Ensure Python 3.8+ is used
- Check for file encoding issues
- Verify no syntax errors in .env file

#### 4. Port 8000 already in use

**Solution:**

```bash
# Run on different port
python manage.py runserver 8080
```

#### 5. Database error

**Solution:**

```bash
# Delete database and migrations
rm db.sqlite3
rm maintenance/migrations/0*.py

# Recreate migrations
python manage.py makemigrations
python manage.py migrate
```

## Contributing Guidelines

1. **Code Style:** Follow PEP 8
2. **Comments:** Add docstrings to all functions and classes
3. **Testing:** Write unit tests for new functionality
4. **Documentation:** Update README for new features
5. **Git:** Use meaningful commit messages

### Docstring Format

```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """
    Brief description of the function.

    Detailed description explaining what the function does,
    including any important behavior or side effects.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        CustomException: When this happens
    """
```

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs for error details
3. Verify external API configuration
4. Check environment variables

## Version History

### v1.0.0 (2024-05-11)

- Initial release
- Basic API endpoints
- Knapsack algorithm implementation
- External API integration
- Logging middleware
- Comprehensive documentation

## Future Enhancements

- [ ] Implement caching layer for API responses
- [ ] Add request/response validation middleware
- [ ] Implement rate limiting per client
- [ ] Add WebSocket support for real-time updates
- [ ] Implement batch processing for large datasets
- [ ] Add analytics and reporting
- [ ] Implement notification system integration
- [ ] Add API versioning
- [ ] Implement request signing
- [ ] Add comprehensive test suite
