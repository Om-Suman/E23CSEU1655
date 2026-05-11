# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Prerequisites

- Python 3.8+
- pip
- Virtual environment

### Step 1: Set Up Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
cd vehicle_maintenance_scheduler
pip install -r ../requirements.txt
```

### Step 3: Configure Environment

Edit `.env` in project root:

```
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
EXTERNAL_API_BASE_URL=http://4.224.186.213/evaluation-service
EXTERNAL_API_TOKEN=your-bearer-token-here
```

### Step 4: Initialize Database

```bash
python manage.py migrate
```

### Step 5: Start Server

```bash
python manage.py runserver
```

✅ API available at: `http://localhost:8000/api/schedule/`

---

## 📡 Test the API

### Using cURL

```bash
# Test schedule endpoint
curl -X GET http://localhost:8000/api/schedule/

# Test health check
curl -X GET http://localhost:8000/api/health/
```

### Using Python

```python
import requests

response = requests.get('http://localhost:8000/api/schedule/')
print(response.json())
```

### Using Postman

1. Create new GET request
2. URL: `http://localhost:8000/api/schedule/`
3. Click Send

---

## 📁 Project Structure Overview

```
question 1/
├── logging_middleware/          # Custom logging
│   └── middleware.py
├── vehicle_maintenance_scheduler/   # Django project
│   ├── maintenance/             # Main app
│   │   ├── views.py            # API endpoints
│   │   ├── services.py         # External API calls
│   │   ├── knapsack.py         # Optimization algorithm
│   │   ├── urls.py             # Routing
│   │   ├── serializers.py      # DRF serializers
│   │   ├── models.py           # Database models
│   │   └── migrations/
│   ├── vehicle_maintenance_scheduler/
│   │   ├── settings.py         # Django config
│   │   ├── urls.py             # Project routing
│   │   └── wsgi.py
│   └── manage.py
├── notification_app_be/         # Future notifications
├── .env                         # Environment variables
├── .gitignore
├── requirements.txt
├── README.md                    # Full documentation
└── notification_system_design.md
```

---

## 🔧 Common Commands

### Django Commands

```bash
# Create new migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Admin interface
# Go to: http://localhost:8000/admin/
```

### Server Commands

```bash
# Development server (default)
python manage.py runserver

# Specific port
python manage.py runserver 8080

# All interfaces
python manage.py runserver 0.0.0.0:8000
```

### Database Commands

```bash
# Interactive shell
python manage.py shell

# Example usage:
# >>> from maintenance.services import get_external_api_service
# >>> service = get_external_api_service()
# >>> success, depots, error = service.fetch_depots()
```

---

## 📊 API Response Examples

### Success Response

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
        }
      ]
    }
  ],
  "timestamp": "2024-05-11T10:30:45.123456Z"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Failed to fetch data from external service",
  "details": "Connection error while fetching depots: [error details]"
}
```

---

## 🐛 Troubleshooting

| Issue                                           | Solution                                |
| ----------------------------------------------- | --------------------------------------- |
| `ModuleNotFoundError: No module named 'django'` | Run `pip install -r requirements.txt`   |
| Port 8000 already in use                        | Use `python manage.py runserver 8080`   |
| External API connection error                   | Check `.env` token and base URL         |
| Database errors                                 | Run `python manage.py migrate`          |
| Import errors                                   | Ensure virtual environment is activated |

---

## 📚 Key Files Explained

### services.py

Handles all external API communication with:

- Bearer token authentication
- Error handling and retries
- Timeout management
- Logging

### knapsack.py

Implements the 0/1 Knapsack algorithm:

- Dynamic programming solution
- O(n×W) time complexity
- Task validation
- Batch optimization

### views.py

REST API endpoints:

- GET `/api/schedule/` - Optimization endpoint
- GET `/api/health/` - Health check

### middleware.py

Custom logging:

- Request/response tracking
- Performance monitoring
- Error handling

---

## 🚀 Next Steps

1. **Test locally** - Verify all endpoints work
2. **Review logs** - Check `debug.log` for details
3. **Modify configuration** - Update `.env` for your needs
4. **Deploy** - Follow production deployment guide in README.md
5. **Monitor** - Set up logging and alerts

---

## 📖 For More Details

- **Full Documentation:** See `README.md`
- **Notification System:** See `notification_system_design.md`
- **Code Comments:** Check docstrings in `.py` files

---

## ✨ Key Features

✅ Production-ready Django REST API  
✅ 0/1 Knapsack optimization algorithm  
✅ External API integration with Bearer token  
✅ Comprehensive error handling  
✅ Modular, clean architecture  
✅ Full logging and monitoring  
✅ Database models for auditing  
✅ Scalable design

---

## 💡 Tips

- Always activate virtual environment before development
- Update `.env` with your actual API token
- Check logs for debugging: `debug.log`
- Use Django admin for data inspection
- Monitor queue depth and worker status in production

---

Enjoy building! 🎉
