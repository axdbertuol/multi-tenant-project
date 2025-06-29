# Test Suite

This directory contains a comprehensive test suite for the multi-tenant FastAPI DDD application, organized by test type and architecture layers.

## Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/
│   │   ├── entities/        # Domain entity tests
│   │   ├── value_objects/   # Value object tests
│   │   └── repositories/    # Repository interface tests
│   ├── application/
│   │   ├── use_cases/       # Business logic tests
│   │   ├── services/        # Application service tests
│   │   └── dtos/            # DTO validation tests
│   ├── infrastructure/      # Infrastructure layer tests
│   └── presentation/        # API layer tests
├── integration/             # Integration tests (database, external services)
│   ├── infrastructure/
│   │   ├── repositories/    # Repository implementation tests
│   │   └── database/        # Database operation tests
│   ├── application/         # Cross-layer integration tests
│   └── domain/              # Domain integration tests
├── e2e/                     # End-to-end tests (full application stack)
│   └── api/                 # API endpoint tests
├── fixtures/                # Test data fixtures
├── factories/               # Test data factories
└── shared/                  # Shared test utilities
```

## Test Types

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked
- **Coverage**: Domain logic, business rules, transformations

### Integration Tests
- **Purpose**: Test component interactions with real dependencies
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Real database, file system
- **Coverage**: Repository implementations, database operations, cross-layer interactions

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (5+ seconds per test)
- **Dependencies**: Full application stack
- **Coverage**: API endpoints, authentication flows, complete business scenarios

## Running Tests

### Prerequisites
1. Install test dependencies:
   ```bash
   poetry install --with dev
   ```

2. Set up test database:
   ```bash
   # Create test database
   createdb ddd_app_test
   
   # Or set custom test database URL
   export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/test_db"
   ```

### Run All Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Run by Test Type
```bash
# Unit tests only (fast)
poetry run pytest -m unit

# Integration tests only
poetry run pytest -m integration

# End-to-end tests only
poetry run pytest -m e2e

# Exclude slow tests
poetry run pytest -m "not slow"
```

### Run by Module
```bash
# Domain layer tests
poetry run pytest tests/unit/domain/

# Authentication tests
poetry run pytest tests/e2e/api/test_auth_endpoints.py

# Repository tests
poetry run pytest tests/integration/infrastructure/repositories/
```

### Verbose Output
```bash
# Detailed output
poetry run pytest -v

# Show stdout
poetry run pytest -s

# Stop on first failure
poetry run pytest -x
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Markers for test categorization
- Warning filters
-  test support

### Fixtures (`conftest.py`)
- Database session management
- Test client setup
- Dependency injection overrides
- Sample data fixtures

## Test Factories

### User Factory (`tests/factories/user_factory.py`)
- Creates domain User entities
- Provides helper methods for different user states
- Uses Faker for realistic test data

### Session Factory (`tests/factories/session_factory.py`)
- Creates UserSession entities
- Supports different session states (active, expired, logged out)
- Generates realistic session data

## Test Data

### Fixtures (`tests/fixtures/`)
- Pre-configured test data
- Authentication helpers
- Common test scenarios

### Sample Data
- Realistic email addresses
- Secure password handling
- IP addresses and user agents

## Best Practices

### Unit Tests
- Mock external dependencies
- Test one thing at a time
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

### Integration Tests
- Use fresh database for each test
- Test real database constraints
- Verify data persistence
- Test error conditions

### E2E Tests
- Test complete user workflows
- Use realistic data
- Test both success and failure paths
- Verify HTTP status codes and response format

### General Guidelines
- Keep tests independent
- Use factories for test data
- Clean up after tests
- Document complex test scenarios

## Continuous Integration

Tests are designed to run in CI environments with:
- Isolated test database
- Parallel test execution
- Comprehensive coverage reporting
- Fast feedback on failures

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.io` -  tests

## Coverage Goals

- **Unit Tests**: 90%+ coverage of domain and application layers
- **Integration Tests**: 80%+ coverage of infrastructure layer
- **E2E Tests**: 100% coverage of critical user workflows

## Debugging Tests

```bash
# Debug specific test
poetry run pytest tests/path/to/test.py::test_name -v -s

# Use pytest debugger
poetry run pytest tests/path/to/test.py::test_name --pdb

# Debug with IDE
# Set breakpoints and run tests in debug mode
```