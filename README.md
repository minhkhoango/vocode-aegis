# 🚀 Vocode Analytics Dashboard

A real-time analytics dashboard for Vocode conversation monitoring with Redis stream processing and WebSocket updates.

## 📋 Features

- **Real-time Monitoring** - Live conversation tracking and error monitoring
- **Redis Stream Processing** - Asynchronous event consumption from Vocode streams
- **WebSocket Updates** - Real-time dashboard updates via WebSocket connections
- **Error Tracking** - Comprehensive error logging and drill-down capabilities
- **Health Monitoring** - System health status and Redis connectivity checks
- **Docker Support** - Containerized deployment with Docker Compose

## 🏗️ Architecture

```
Vocode/
├── backend/           # FastAPI backend
│   ├── src/          # Source code
│   │   └── main.py   # Main application
│   ├── tests/        # Test suite
│   └── requirements.txt
├── frontend/         # React frontend
├── docker-compose.yml
└── Makefile
```

## 🚀 Quick Start

### **Using Makefile (Recommended):**
```bash
# Start the dashboard
make start

# Check status
make status

# View logs
make logs

# Stop services
make stop

# Clean up
make clean
```

### **Manual Docker Compose:**
```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## 🧪 Testing

### **Test Structure:**
```
backend/
├── src/              # Source code
│   └── main.py       # Main application
├── tests/            # Test suite
│   └── test_main.py  # Comprehensive tests
├── requirements.txt   # Runtime dependencies
└── requirements-dev.txt # Development dependencies
```

### **Running Tests:**

#### **Install Dependencies:**
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
```

#### **Run All Tests:**
```bash
pytest tests/
```

#### **Run with Coverage:**
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

#### **Run Specific Test Categories:**
```bash
# Unit tests only
pytest tests/ -k "TestVocodeRedisConsumer or TestConnectionManager or TestMetricsAggregator"

# Integration tests only
pytest tests/ -k "TestFastAPIEndpoints or TestWebSocket or TestIntegration"

# Edge case tests only
pytest tests/ -k "TestEdgeCases or TestPerformance"
```

### **Test Coverage:**

#### **Classes Tested:**
- ✅ `VocodeRedisConsumer` - Redis stream processing
- ✅ `ConnectionManager` - WebSocket connection management  
- ✅ `MetricsAggregator` - Real-time metrics calculation
- ✅ `LiveStatus` - System health status
- ✅ `ActiveCallsMetric` - Call count tracking
- ✅ `ErrorSummary` - Error aggregation
- ✅ `DashboardMetrics` - Complete dashboard data

#### **Endpoints Tested:**
- ✅ `GET /` - Frontend serving
- ✅ `GET /health` - Health check
- ✅ `GET /logs/{error_type}` - Error logs API
- ✅ `GET /logs/{error_type}/viewer` - Log viewer page
- ✅ `WebSocket /ws` - Real-time updates

#### **Test Categories:**
- 🧪 **Unit Tests** - Individual component testing
- 🔗 **Integration Tests** - API endpoint testing
- 🎯 **Edge Cases** - Error handling and boundary conditions
- 📊 **Performance Tests** - Resource limits and performance
- 🏗️ **Model Tests** - Pydantic model validation

### **Test Scenarios Covered:**

#### **Redis Consumer Scenarios:**
1. **Normal Operation:**
   - ✅ Successful Redis connection
   - ✅ Stream message processing
   - ✅ Call start/end event handling
   - ✅ Error event processing

2. **Error Handling:**
   - ✅ Redis connection failures
   - ✅ Invalid message formats
   - ✅ Network timeouts
   - ✅ Malformed data

3. **Edge Cases:**
   - ✅ Empty message streams
   - ✅ Invalid stream names
   - ✅ Missing required fields
   - ✅ Buffer overflow protection

#### **WebSocket Scenarios:**
1. **Connection Management:**
   - ✅ Client connection acceptance
   - ✅ Graceful disconnection
   - ✅ Multiple client handling
   - ✅ Connection cleanup

2. **Data Broadcasting:**
   - ✅ Metrics serialization
   - ✅ JSON payload formatting
   - ✅ Disconnected client handling
   - ✅ Broadcast error recovery

#### **API Endpoint Scenarios:**
1. **Health Check:**
   - ✅ Redis connectivity testing
   - ✅ Metrics collection
   - ✅ Error state reporting
   - ✅ Degraded service detection

2. **Error Logs:**
   - ✅ Error type filtering
   - ✅ Timestamp sorting
   - ✅ Limit parameter handling
   - ✅ Empty result handling

3. **Frontend Serving:**
   - ✅ Static file serving
   - ✅ Missing file handling
   - ✅ HTML content generation
   - ✅ Error page fallback

### **Performance Tests:**
- ✅ Error buffer max size (1000 entries)
- ✅ Active calls never negative
- ✅ Memory usage monitoring
- ✅ Connection pool limits
- ✅ High error rate handling
- ✅ Multiple WebSocket connections
- ✅ Large error buffer processing
- ✅ Concurrent API requests

### **Error Handling Tests:**
- ✅ Redis connection loss
- ✅ WebSocket disconnections
- ✅ HTTP request timeouts
- ✅ Invalid JSON payloads
- ✅ Malformed timestamps
- ✅ Missing required fields
- ✅ Type conversion errors

### **CI Integration:**

#### **GitHub Actions Example:**
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/
      - name: Generate coverage
        run: |
          cd backend
          pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### **Success Criteria:**
A test run is considered successful when:
- ✅ All tests pass (0 failures)
- ✅ Coverage > 90%
- ✅ No critical warnings
- ✅ Performance within limits
- ✅ All error paths tested

**Total Test Count:** 50+ comprehensive tests  
**Coverage Target:** 100%  
**Test Categories:** 5 main categories  
**Runtime:** ~30 seconds  
**Dependencies:** 7 test packages

## 🔧 Development

### **Project Structure:**
```
Vocode/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI application
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_main.py     # Comprehensive test suite
│   ├── requirements.txt      # Runtime dependencies
│   └── requirements-dev.txt  # Development dependencies
├── frontend/
│   ├── src/
│   └── public/
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── README.md
```

### **Dependencies:**

#### **Runtime Dependencies (`requirements.txt`):**
```
fastapi==0.111.0
uvicorn==0.30.1
redis==5.0.1
pydantic==2.7.1
pydantic-settings==2.0.0
```

#### **Development Dependencies (`requirements-dev.txt`):**
```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-cov==4.1.0
httpx==0.25.2
flake8==6.1.0
mypy==1.7.1
black==23.11.0
isort==5.12.0
```

### **Code Quality:**
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/ tests/
```

## 🌐 API Endpoints

### **Health Check:**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "redis_connected": true,
  "active_calls": 5,
  "error_count": 2
}
```

### **Error Logs:**
```http
GET /logs/{error_type}?limit=50
```

**Response:**
```json
{
  "errors": [
    {
      "timestamp": "1704110400000",
      "error_type": "connection_timeout",
      "message": "Redis connection failed",
      "severity": "high",
      "conversation_id": "conv-123"
    }
  ]
}
```

### **WebSocket:**
```javascript
const ws = new WebSocket('ws://localhost:3001/ws');
ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('Live metrics:', metrics);
};
```

## 🐳 Docker Deployment

### **Services:**
- **vocode-analytics-dashboard** - FastAPI backend (port 3001)
- **redis** - Redis server (port 6379)
- **redis-commander** - Redis management UI (port 8081)

### **Environment Variables:**
```bash
REDIS_HOST=redis
REDIS_PORT=6379
DASHBOARD_REFRESH_INTERVAL=5000
LOG_LEVEL=INFO
```

## 📊 Monitoring

### **Health Status:**
- 🟢 **Green** - System healthy (≤3 recent errors)
- 🟡 **Yellow** - Warning (4-10 recent errors)
- 🔴 **Red** - Critical (>10 recent errors)

### **Metrics:**
- **Active Calls** - Real-time call count
- **Error Summary** - 24-hour error aggregation
- **Live Status** - System health indicator
- **Error Logs** - Detailed error tracking

## 🔍 Troubleshooting

### **Common Issues:**

#### **Dashboard Not Loading:**
```bash
# Check container status
make status

# View logs
make logs

# Restart services
make restart
```

#### **Redis Connection Issues:**
```bash
# Check Redis connectivity
docker compose exec vocode-analytics-dashboard redis-cli ping

# View Redis logs
docker compose logs redis
```

#### **Test Failures:**
```bash
# Install dependencies
cd backend
pip install -r requirements.txt -r requirements-dev.txt

# Run tests with verbose output
pytest tests/ -v

# Run specific failing test
pytest tests/test_main.py::TestVocodeRedisConsumer::test_init_success -v
```

## 📝 License

This project is licensed under the MIT License. 