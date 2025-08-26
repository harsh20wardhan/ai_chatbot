# FastAPI Backend Testing Guide

This document provides comprehensive information about testing the FastAPI backend that replaces the Cloudflare Workers API.

## Test Overview

The test suite is designed to verify:

1. **API Compatibility** - Ensures the FastAPI backend maintains compatibility with the original Cloudflare Workers API
2. **Health Checks** - Verifies all health check endpoints work correctly
3. **Middleware** - Tests CORS, authentication, error handling, and performance middleware
4. **Services** - Validates that all service layer components are properly integrated

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python run_tests.py

# Run compatibility check only
python run_tests.py check
```

### Individual Test Categories

```bash
# Health check tests
pytest tests/test_health.py -v

# API compatibility tests
pytest tests/test_api_compatibility.py -v

# Middleware tests
pytest tests/test_middleware.py -v

# Service layer tests
pytest tests/test_services.py -v
```

### Advanced Testing

```bash
# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_health.py::TestHealthEndpoints::test_basic_health_check -v

# Run with detailed output
pytest -v --tb=long

# Run async tests only
pytest -k "async" -v
```

## Test Categories

### 1. Health Check Tests (`test_health.py`)

Tests all health check endpoints to ensure proper monitoring:

- ✅ Basic health check (`/health`)
- ✅ Liveness check (`/live`) 
- ✅ Readiness check (`/ready`)
- ✅ Detailed health check (`/health/detailed`)
- ✅ Database health check (`/health/database`)
- ✅ Qdrant health check (`/health/qdrant`)
- ✅ Bedrock health check (`/health/bedrock`)
- ✅ Supabase health check (`/health/supabase`)
- ✅ Services health check (`/health/services`)

### 2. API Compatibility Tests (`test_api_compatibility.py`)

Ensures the FastAPI backend maintains compatibility with the original API:

- ✅ Root endpoint format
- ✅ API info endpoint
- ✅ CORS headers
- ✅ Error response format
- ✅ All endpoint existence checks:
  - Authentication endpoints
  - Bot management endpoints
  - Document management endpoints
  - Crawling endpoints
  - Embedding endpoints
  - Chat endpoints
  - Admin endpoints
  - Analytics endpoints
  - Widget endpoints
- ✅ Request validation
- ✅ Response headers

### 3. Middleware Tests (`test_middleware.py`)

Tests all middleware components:

- ✅ CORS middleware
- ✅ Performance middleware (timing headers)
- ✅ Error handling middleware
- ✅ Request size limiting
- ✅ Rate limiting
- ✅ Authentication middleware
- ✅ Middleware order
- ✅ Error correlation IDs

### 4. Service Tests (`test_services.py`)

Validates service layer integration:

- ✅ CrawlerService availability and methods
- ✅ ParserService availability and methods
- ✅ EmbeddingService availability and methods
- ✅ RAGService availability and methods
- ✅ RealtimeCrawlService availability and methods
- ✅ Service dependencies
- ✅ Service configuration

## Test Configuration

### Environment Setup

Tests use the same configuration as the main application but with mocked external services:

```python
# Mock services are automatically configured in conftest.py
- Mock Qdrant client
- Mock Bedrock client  
- Mock Supabase client
```

### Test Database

Tests can use either:
1. **Mocked database** (default) - Fast, no external dependencies
2. **Test database** - Real database for integration testing

To use a test database, set:
```bash
export TEST_DATABASE_URL="your-test-database-url"
```

### Authentication Testing

Tests include mock authentication:
```python
# Mock JWT token for testing protected endpoints
auth_headers = {"Authorization": "Bearer mock-jwt-token"}
```

## Expected Test Results

### Passing Tests ✅

All tests should pass in a properly configured environment:

```
Health Checks: PASSED
API Compatibility: PASSED  
Middleware: PASSED
Services: PASSED
```

### Common Test Failures ❌

#### Missing Dependencies
```
ImportError: No module named 'fastapi'
```
**Solution:** Install dependencies with `pip install -r requirements.txt`

#### Configuration Issues
```
ValueError: Missing required environment variables
```
**Solution:** Copy `.env.example` to `.env` and configure required variables

#### Service Connection Failures
```
ConnectionError: Unable to connect to Qdrant
```
**Solution:** Tests use mocked services by default. Check mock configuration in `conftest.py`

#### Database Connection Issues
```
asyncpg.exceptions.ConnectionDoesNotExistError
```
**Solution:** Tests can run without database. For integration testing, configure test database.

## Test Data Management

### Fixtures

The test suite includes comprehensive fixtures:

- `mock_user` - Mock user data
- `mock_bot` - Mock bot data  
- `auth_headers` - Authentication headers
- `mock_qdrant_client` - Mocked Qdrant client
- `mock_bedrock_client` - Mocked Bedrock client
- `mock_supabase_client` - Mocked Supabase client

### Cleanup

Tests automatically clean up test data:
```python
@pytest.fixture
async def cleanup_test_data():
    # Automatic cleanup after tests
```

## Integration Testing

### Full Stack Testing

To test with real services (not recommended for CI):

1. Start required services:
   ```bash
   # Start Qdrant
   docker run -p 6333:6333 qdrant/qdrant
   
   # Start Ollama
   ollama serve
   ```

2. Configure real service URLs in test environment

3. Run integration tests:
   ```bash
   pytest --integration -v
   ```

### API Testing with Real Requests

```bash
# Start the FastAPI server
uvicorn main:app --reload

# Test with curl
curl http://localhost:8000/health
curl http://localhost:8000/api
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test FastAPI Backend

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        python run_tests.py
```

## Performance Testing

### Load Testing

```bash
# Install locust
pip install locust

# Run load tests (create locustfile.py first)
locust -f locustfile.py --host=http://localhost:8000
```

### Memory Testing

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler main.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the `fastapi-backend` directory
   - Check that all dependencies are installed
   - Verify Python path includes current directory

2. **Async Test Issues**
   - Ensure `pytest-asyncio` is installed
   - Use `@pytest.mark.asyncio` for async tests
   - Check event loop configuration

3. **Mock Service Issues**
   - Verify mock fixtures are properly configured
   - Check that mocks return expected data types
   - Ensure mocks are applied to correct modules

### Debug Mode

Run tests with debug output:
```bash
pytest -v --tb=long --capture=no
```

### Test Coverage

Generate coverage report:
```bash
pytest --cov=. --cov-report=html --cov-report=term
open htmlcov/index.html
```

## Contributing

When adding new tests:

1. Follow existing test patterns
2. Use appropriate fixtures
3. Mock external services
4. Include both positive and negative test cases
5. Update this documentation

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `TestClassName`
- Test methods: `test_method_name`
- Async tests: `async def test_async_method`

### Test Organization

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures and configuration
├── test_health.py       # Health check tests
├── test_api_compatibility.py  # API compatibility tests
├── test_middleware.py   # Middleware tests
├── test_services.py     # Service layer tests
└── integration/         # Integration tests (optional)
```

This comprehensive test suite ensures the FastAPI backend maintains full compatibility with the original Cloudflare Workers API while providing robust monitoring and error handling capabilities.