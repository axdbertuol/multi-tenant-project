# Test Suite

This directory contains a comprehensive test suite for the multi-tenant FastAPI DDD application, organized by test type first, then by bounded context.

## Test Structure

```
tests/
├── unit/                           # Unit tests (fast, isolated)
│   ├── authorization/              # Authorization bounded context
│   │   ├── domain/
│   │   │   ├── entities/          # Role, Permission, Policy tests
│   │   │   ├── value_objects/     # Authorization value objects
│   │   │   └── services/          # RBAC/ABAC service logic tests
│   │   └── application/
│   │       ├── use_cases/         # Authorization use cases
│   │       └── dtos/              # Authorization DTOs
│   ├── user/                      # User bounded context
│   │   ├── domain/
│   │   │   ├── entities/          # User, UserSession tests
│   │   │   ├── value_objects/     # Email, Password tests
│   │   │   └── services/          # Authentication service tests
│   │   └── application/
│   │       ├── use_cases/         # User management use cases
│   │       └── dtos/              # User DTOs
│   ├── organization/              # Organization bounded context
│   │   ├── domain/
│   │   │   ├── entities/          # Organization entity tests
│   │   │   └── value_objects/     # Organization value objects
│   │   └── application/
│   │       └── use_cases/         # Organization use cases
│   ├── plans/                     # Plans bounded context
│   │   ├── domain/
│   │   │   ├── entities/          # Plan entity tests
│   │   │   └── value_objects/     # Plan value objects
│   │   └── application/
│   │       └── use_cases/         # Plan use cases
│   └── shared/                    # Shared components
│       ├── domain/
│       │   ├── entities/          # Shared domain tests
│       │   └── value_objects/     # Shared value objects
│       └── infrastructure/        # Shared infrastructure
├── integration/                    # Integration tests (real dependencies, cross-layer)
│   ├── authorization/
│   │   ├── application/
│   │   │   └── services/          # Authorization service integration
│   │   └── infrastructure/
│   │       ├── repositories/      # Role/Permission repository tests
│   │       └── database/          # Authorization database tests
│   ├── user/
│   │   ├── application/
│   │   │   └── services/          # User service integration
│   │   └── infrastructure/
│   │       ├── repositories/      # User repository tests
│   │       └── database/          # User database tests
│   ├── organization/
│   │   ├── application/
│   │   │   └── use_cases/         # Organization integration tests
│   │   └── infrastructure/
│   │       └── repositories/      # Organization repository tests
│   ├── plans/
│   │   └── infrastructure/
│   │       └── repositories/      # Plan repository tests
│   └── shared/
│       └── infrastructure/
│           ├── database/          # UoW, shared database tests
│           └── repositories/      # Shared repository tests
├── e2e/                           # End-to-end tests (full application stack)
│   ├── authorization/
│   │   └── api/                   # Role/permission API endpoints
│   ├── user/
│   │   └── api/                   # Authentication endpoints
│   ├── organization/
│   │   └── api/                   # Organization API endpoints
│   ├── plans/
│   │   └── api/                   # Plan API endpoints
│   └── shared/
│       └── api/                   # Cross-cutting API tests
├── fixtures/                      # Test data fixtures
├── factories/                     # Test data factories
├── conftest.py                    # Global pytest configuration
└── README.md                      # This documentation
```

## Test Types

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Mocked
- **Coverage**: Domain logic, business rules, transformations
- **Organization**: By bounded context, then by architectural layer

### Integration Tests
- **Purpose**: Test component interactions with real dependencies
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: Real database, file system
- **Coverage**: Repository implementations, database operations, cross-layer interactions
- **Organization**: By bounded context, focusing on infrastructure and application services

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (5+ seconds per test)
- **Dependencies**: Full application stack
- **Coverage**: API endpoints, authentication flows, complete business scenarios
- **Organization**: By bounded context, focusing on API interactions

## Bounded Contexts

### Authorization
- **Responsibilities**: Roles, permissions, policies, RBAC/ABAC
- **Key Entities**: Role, Permission, Policy, RoleInheritance
- **Key Services**: AuthorizationService, RBACService, ABACService
- **Test Focus**: Role inheritance, permission evaluation, policy enforcement

### User
- **Responsibilities**: User management, authentication, sessions
- **Key Entities**: User, UserSession
- **Key Services**: AuthenticationService, UserDomainService
- **Test Focus**: Authentication flows, session management, user lifecycle

### Organization
- **Responsibilities**: Multi-tenancy, organization management
- **Key Entities**: Organization, UserOrganizationRole
- **Key Services**: OrganizationService
- **Test Focus**: Multi-tenant isolation, organization operations

### Plans
- **Responsibilities**: Subscription plans, billing tiers
- **Key Entities**: Plan
- **Key Services**: PlanService
- **Test Focus**: Plan management, billing logic

### Shared
- **Responsibilities**: Common utilities, cross-cutting concerns
- **Key Components**: Database connections, shared value objects
- **Test Focus**: Infrastructure components, shared utilities

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
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# End-to-end tests only
poetry run pytest tests/e2e/

# Exclude slow tests
poetry run pytest -m "not slow"
```

### Run by Bounded Context
```bash
# All authorization tests
poetry run pytest tests/*/authorization/

# All user tests
poetry run pytest tests/*/user/

# All organization tests
poetry run pytest tests/*/organization/

# Authorization unit tests only
poetry run pytest tests/unit/authorization/

# User integration tests only
poetry run pytest tests/integration/user/
```

### Run by Specific Component
```bash
# Domain entity tests
poetry run pytest tests/unit/*/domain/entities/

# Repository integration tests
poetry run pytest tests/integration/*/infrastructure/repositories/

# API endpoint tests
poetry run pytest tests/e2e/*/api/

# Authorization service tests (all types)
poetry run pytest -k "authorization_service"
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
- Coverage configuration

### Fixtures (`conftest.py`)
- **Global** (`tests/conftest.py`): Database session management, test client setup
- **Bounded Context** (`tests/*/context/conftest.py`): Context-specific fixtures
- **Test Type** (`tests/type/conftest.py`): Type-specific configuration

## Test Factories

### User Factory (`tests/factories/user_factory.py`)
- Creates domain User entities
- Provides helper methods for different user states
- Uses Faker for realistic test data

### Session Factory (`tests/factories/session_factory.py`)
- Creates UserSession entities
- Supports different session states (active, expired, logged out)
- Generates realistic session data

### Role/Permission Factories (`tests/factories/`)
- Creates authorization entities
- Supports role hierarchies
- Generates complex permission scenarios

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
- Use descriptive test names following the pattern: `test_should_<expected_outcome>_when_<condition>`
- Follow AAA pattern (Arrange, Act, Assert)
- Group related tests in classes
- Use parametrized tests for similar scenarios

### Integration Tests
- Use fresh database for each test
- Test real database constraints
- Verify data persistence
- Test error conditions
- Focus on component interactions

### E2E Tests
- Test complete user workflows
- Use realistic data
- Test both success and failure paths
- Verify HTTP status codes and response format
- Minimize external dependencies

### Organization Guidelines
- **Test Location**: Place tests close to the functionality they test
- **Naming**: Use descriptive names that explain the test purpose
- **Dependencies**: Keep bounded context tests independent
- **Shared Code**: Use factories for test data, fixtures for common setups
- **Documentation**: Document complex test scenarios and setup requirements

## Continuous Integration

Tests are designed to run in CI environments with:
- Isolated test database per bounded context
- Parallel test execution by bounded context
- Comprehensive coverage reporting
- Fast feedback on failures
- Selective test execution based on changed code

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.authorization` - Authorization context tests
- `@pytest.mark.user` - User context tests
- `@pytest.mark.organization` - Organization context tests

## Coverage Goals

- **Unit Tests**: 90%+ coverage of domain and application layers
- **Integration Tests**: 80%+ coverage of infrastructure layer  
- **E2E Tests**: 100% coverage of critical user workflows
- **Per Bounded Context**: 85%+ overall coverage

## Debugging Tests

```bash
# Debug specific test
poetry run pytest tests/path/to/test.py::test_name -v -s

# Use pytest debugger
poetry run pytest tests/path/to/test.py::test_name --pdb

# Debug tests in specific bounded context
poetry run pytest tests/unit/authorization/ -v -s

# Debug with IDE
# Set breakpoints and run tests in debug mode
```

## Migration Notes

This test structure was refactored from a mixed organization to a consistent **test type → bounded context → layer** structure to:

- Improve test discoverability
- Enable better CI/CD parallelization
- Align with Domain-Driven Design principles
- Simplify maintenance and onboarding

When adding new tests:
1. Identify the appropriate bounded context
2. Choose the correct test type (unit/integration/e2e)
3. Place in the corresponding architectural layer
4. Follow established naming conventions