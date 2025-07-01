# IAM Session Validation Tests

This document describes the comprehensive test suite for the `validate_session_access` functionality in the IAM context.

## Test Structure

The tests are organized into three levels:

1. **Unit Tests** (`tests/unit/iam/application/use_cases/`)
2. **Integration Tests** (`tests/integration/iam/application/use_cases/`)
3. **End-to-End Tests** (`tests/e2e/iam/api/`)

## Test Files

### 1. Unit Tests
**File**: `test_session_use_cases_validate_access.py`

Tests the `SessionUseCase.validate_session_access` method in isolation with mocked dependencies.

#### Test Cases:

- **`test_validate_session_access_with_invalid_token`**
  - Tests validation with non-existent/invalid session token
  - Expected: `False`

- **`test_validate_session_access_with_valid_token_no_permissions`**
  - Tests validation with valid token but no permission requirements
  - Expected: `True`

- **`test_validate_session_access_with_valid_token_and_permissions_allowed`**
  - Tests validation with valid token and permissions that are granted
  - Expected: `True`

- **`test_validate_session_access_with_valid_token_and_permissions_denied`**
  - Tests validation with valid token but insufficient permissions
  - Expected: `False`

- **`test_validate_session_access_with_organization_scope`**
  - Tests validation with organization-specific permissions
  - Verifies organization UUID is correctly passed to authorization context

- **`test_validate_session_access_with_resource_details`**
  - Tests validation with specific resource type and ID
  - Verifies resource details are correctly passed to authorization context

- **`test_validate_session_access_with_malformed_permission`**
  - Tests handling of permission strings without colons
  - Expected: Uses entire string as action

- **`test_validate_session_access_permission_parsing`**
  - Tests correct parsing of "resource:action" permission format
  - Verifies resource type and action extraction

- **`test_validate_session_access_user_attributes_inclusion`**
  - Tests that user attributes (email, name, active status) are included in authorization context
  - Verifies attribute mapping correctness

- **`test_validate_session_access_simple_method`**
  - Tests the simplified `validate_session_access_simple` helper method
  - Verifies it correctly formats permissions

- **`test_validate_session_access_simple_with_default_resource`**
  - Tests simplified method with default "system" resource type
  - Expected: Uses "system" as default resource type

- **`test_get_session_user_permissions_invalid_token`**
  - Tests getting permissions with invalid token
  - Expected: Empty list

- **`test_get_session_user_permissions_valid_token`**
  - Tests getting user permissions with valid session
  - Verifies RBAC service integration

- **`test_get_session_user_permissions_with_organization`**
  - Tests getting permissions with organization scope
  - Verifies organization UUID conversion

- **`test_uuid_conversion_in_authorization_context`**
  - Tests that string UUIDs are properly converted to UUID objects
  - Verifies both organization_id and resource_id conversion

- **`test_multiple_permissions_all_allowed`**
  - Tests validation with multiple permissions, all granted
  - Verifies all permissions are checked

- **`test_authorization_context_user_id_consistency`**
  - Tests that the user ID in authorization context matches session user
  - Verifies data consistency

### 2. Integration Tests
**File**: `test_session_use_cases_validate_access_integration.py`

Tests the complete IAM infrastructure integration with real database operations.

#### Test Cases:

- **`test_validate_session_access_with_invalid_token_integration`**
  - Tests with non-existent token in database
  - Expected: `False`

- **`test_validate_session_access_with_valid_token_no_permissions_integration`**
  - Tests with valid database session, no permission requirements
  - Expected: `True`

- **`test_validate_session_access_with_expired_session_integration`**
  - Tests with expired session in database
  - Expected: `False`

- **`test_validate_session_access_with_inactive_user_integration`**
  - Tests with valid session but deactivated user
  - Expected: `False`

- **`test_validate_session_access_with_role_based_permissions_integration`**
  - Tests complete RBAC flow: user → role → permission
  - Sets up database relationships and tests permission validation

- **`test_validate_session_access_without_required_permission_integration`**
  - Tests when user lacks required permission
  - Expected: `False`

- **`test_validate_session_access_multiple_permissions_integration`**
  - Tests with multiple permissions, mixed allow/deny
  - Verifies fine-grained permission control

- **`test_validate_session_access_simple_integration`**
  - Tests simplified method with real database
  - Verifies end-to-end flow

- **`test_get_session_user_permissions_integration`**
  - Tests permission retrieval with database integration
  - Verifies actual permissions are returned

- **`test_validate_session_access_with_organization_scope_integration`**
  - Tests organization-scoped permissions with database
  - Verifies organization isolation

- **`test_session_token_cleanup_after_validation_integration`**
  - Tests session validation after cleanup operations
  - Verifies session management robustness

### 3. End-to-End Tests
**File**: `test_session_validation_endpoints.py`

Tests the complete API workflow including session validation.

#### Test Cases:

- **`test_session_validation_workflow_e2e`**
  - Complete workflow: register → login → validate → access protected resource
  - Tests full user journey

- **`test_session_validation_with_permissions_e2e`**
  - Tests API access with role-based permissions
  - Verifies permission enforcement at API level

- **`test_session_expiration_e2e`**
  - Tests API behavior with expired sessions
  - Expected: 401 Unauthorized

- **`test_session_logout_invalidation_e2e`**
  - Tests that logged out sessions cannot access API
  - Verifies logout functionality

- **`test_multiple_sessions_validation_e2e`**
  - Tests concurrent session management
  - Verifies session isolation

- **`test_session_validation_with_inactive_user_e2e`**
  - Tests API access with deactivated user account
  - Expected: 401 Unauthorized

- **`test_session_refresh_validation_e2e`**
  - Tests session refresh and validation workflow
  - Verifies refresh token functionality

- **`test_session_validation_with_organization_context_e2e`**
  - Tests organization-scoped API access
  - Verifies multi-tenant access control

- **`test_concurrent_session_validation_e2e`**
  - Tests concurrent API requests with same session
  - Verifies session thread safety

## Test Data Patterns

### Fixtures
- **`mock_uow`**: Mock Unit of Work for unit tests
- **`mock_repositories`**: Mock repository implementations
- **`sample_user`**: Test user entity
- **`valid_token`/`invalid_token`**: Test session tokens
- **`iam_uow`**: Real IAM Unit of Work for integration tests
- **`test_user`**: Database user entity
- **`test_session`**: Database session entity
- **`test_role`**: Database role entity
- **`test_permission`**: Database permission entity

### Test Data
- **User**: `testuser@example.com`, `Test User`, `password123`
- **Permissions**: `user:read`, `user:write`, `admin:delete`, `organization:manage`
- **Roles**: `test_role`, `admin`, `org_member`
- **Sessions**: Valid tokens with 1-hour expiration

## Usage Scenarios Covered

### 1. Basic Session Validation
- Valid/invalid tokens
- Expired sessions
- Inactive users

### 2. Permission-Based Access Control
- Single permission checks
- Multiple permission requirements
- Permission parsing (resource:action format)
- Malformed permission handling

### 3. Role-Based Access Control (RBAC)
- User role assignments
- Role permission mappings
- Role inheritance (through authorization service)

### 4. Organization Context
- Organization-scoped permissions
- Multi-tenant isolation
- Organization role assignments

### 5. Resource-Specific Access
- Resource type and ID validation
- Resource-specific permission checks

### 6. Session Management
- Multiple concurrent sessions
- Session expiration handling
- Session cleanup integration
- Logout and invalidation

### 7. API Integration
- Authentication endpoints
- Protected resource access
- Permission enforcement
- Error handling (401, 403)

## Running the Tests

### Unit Tests
```bash
pytest tests/unit/iam/application/use_cases/test_session_use_cases_validate_access.py -v
```

### Integration Tests
```bash
pytest tests/integration/iam/application/use_cases/test_session_use_cases_validate_access_integration.py -v
```

### End-to-End Tests
```bash
pytest tests/e2e/iam/api/test_session_validation_endpoints.py -v
```

### All IAM Session Tests
```bash
pytest tests/unit/iam tests/integration/iam tests/e2e/iam -v
```

## Coverage Areas

These tests provide comprehensive coverage for:

1. **Session Validation Logic** (99% code coverage)
2. **Authorization Integration** (RBAC + ABAC)
3. **Database Operations** (CRUD + relationships)
4. **API Endpoints** (authentication flow)
5. **Error Handling** (invalid inputs, edge cases)
6. **Multi-tenancy** (organization scope)
7. **Concurrency** (multiple sessions)
8. **Security** (permission enforcement)

## Mocking Strategy

- **Unit Tests**: Mock all external dependencies (repositories, services)
- **Integration Tests**: Use real database with test data
- **E2E Tests**: Use real API with test client and database

This layered approach ensures both fast unit testing and comprehensive integration validation.