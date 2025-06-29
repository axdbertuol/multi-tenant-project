# Authorization Service Integration Tests

This directory contains comprehensive integration tests for the `AuthorizationService.authorize()` function, covering various scenarios including role inheritance, RBAC+ABAC combinations, and edge cases.

## Test Files

### 1. `test_authorization_service_integration.py`
**Main integration tests for core authorization scenarios:**

- ✅ **RBAC Allow + No ABAC**: Basic role-based access control
- ✅ **RBAC Allow + ABAC Deny**: RBAC permits but ABAC policies deny
- ✅ **RBAC Deny + ABAC Allow**: RBAC denies but ABAC policies allow
- ✅ **Both Deny**: Both RBAC and ABAC deny access
- ✅ **No Roles/Policies**: Default deny when no authorization rules exist
- ✅ **Wildcard Permissions**: Resource-level and global wildcard permissions
- ✅ **Multiple Policies**: Policy combination with deny-overrides algorithm
- ✅ **Resource Enrichment**: Context enrichment with resource attributes
- ✅ **Error Handling**: Exception handling and error decision reasons
- ✅ **Performance Metrics**: Evaluation time tracking
- ✅ **Helper Methods**: `can_user_access_resource`, `check_multiple_permissions`
- ✅ **User Attributes**: Context with user attribute-based conditions

### 2. `test_authorization_service_edge_cases.py`
**Edge cases and boundary conditions:**

- ✅ **Inactive Entities**: Inactive roles, permissions, and policies
- ✅ **Null Values**: `None` resource_id and organization_id handling
- ✅ **Performance**: Long evaluation times and timing consistency
- ✅ **Empty Conditions**: Policies with empty condition arrays
- ✅ **Policy Priorities**: Conflicting priorities and combination logic
- ✅ **Policy Evaluation Null**: Non-applicable policy conditions
- ✅ **Malformed Data**: Invalid context attributes and data structures
- ✅ **Recursive References**: Self-referencing policy conditions
- ✅ **Large Scale**: Many policies (100+) performance testing
- ✅ **Timing Accuracy**: Consistent evaluation time measurement

### 3. `test_authorization_service_role_inheritance.py`
**Role inheritance scenarios (as requested):**

- ✅ **RH Example**: `rh_gerente` inheriting from `rh_assistente`
- ✅ **Deep Hierarchy**: 3-level inheritance (employee → supervisor → manager)
- ✅ **Broken Chains**: Missing parent roles in inheritance chain
- ✅ **Inactive Parents**: Child roles with inactive parent roles
- ✅ **Circular Prevention**: Handling circular inheritance references
- ✅ **Multiple Paths**: Users with multiple roles having different inheritance
- ✅ **Performance**: Deep inheritance hierarchy (10 levels) performance

## Test Scenarios Coverage

### 📋 Authorization Combinations
| RBAC Result | ABAC Result | Expected Decision | Test Coverage |
|-------------|-------------|-------------------|---------------|
| Allow       | No Policies | Allow            | ✅             |
| Allow       | Allow       | Allow            | ✅             |
| Allow       | Deny        | Deny             | ✅             |
| Allow       | Not Applicable | Allow         | ✅             |
| Deny        | Allow       | Allow            | ✅             |
| Deny        | Deny        | Deny             | ✅             |
| Deny        | Not Applicable | Deny          | ✅             |
| No Roles    | Any         | Deny             | ✅             |

### 🏗️ Role Inheritance Patterns
| Pattern | Description | Test Coverage |
|---------|-------------|---------------|
| Linear Chain | A → B → C | ✅ |
| Broken Chain | A → ❌ → C | ✅ |
| Multiple Roots | User has roles from different trees | ✅ |
| Deep Hierarchy | 10+ levels deep | ✅ |
| Circular References | A → B → A (prevented) | ✅ |
| Inactive Parents | Parent roles deactivated | ✅ |

### 🔍 Edge Cases & Error Conditions
| Category | Scenarios | Test Coverage |
|----------|-----------|---------------|
| **Data Integrity** | Inactive roles, permissions, policies | ✅ |
| **Null Handling** | None values in context | ✅ |
| **Performance** | Large datasets, deep hierarchies | ✅ |
| **Error Recovery** | Exceptions, malformed data | ✅ |
| **Policy Logic** | Empty conditions, conflicting priorities | ✅ |

## Example: RH Role Inheritance Test

```python
def test_rh_gerente_inherits_from_assistente():
    # Setup: rh_assistente has basic permissions
    rh_assistente = Role.create("rh_assistente", "HR Assistant", ...)
    rh_assistente_permissions = ["read_users", "read_reports"]
    
    # Setup: rh_gerente inherits from assistente + additional permissions
    rh_gerente = Role.create("rh_gerente", "HR Manager", 
                            parent_role_id=rh_assistente.id, ...)
    rh_gerente_permissions = ["manage_users", "approve_requests"]
    
    # Test: rh_gerente can access inherited permissions
    context = AuthorizationContext.create(
        user_id=user_with_rh_gerente_role,
        resource_type="user", 
        action="read"  # From parent role
    )
    
    decision = authorization_service.authorize(context)
    
    # Assert: Access granted via inheritance
    assert decision.is_allowed()
    assert "rbac_allow" in [r.type for r in decision.reasons]
```

## Running the Tests

### Run All Authorization Tests
```bash
pytest tests/integration/application/services/ -v
```

### Run Specific Test File
```bash
# Core integration tests
pytest tests/integration/application/services/test_authorization_service_integration.py -v

# Edge cases
pytest tests/integration/application/services/test_authorization_service_edge_cases.py -v

# Role inheritance (including RH example)
pytest tests/integration/application/services/test_authorization_service_role_inheritance.py -v
```

### Run with Coverage
```bash
pytest tests/integration/application/services/ --cov=src.authorization.domain.services.authorization_service --cov-report=html
```

### Run Performance Tests Only
```bash
pytest tests/integration/application/services/ -k "performance" -v
```

## Key Testing Principles

### 🎯 **Comprehensive Coverage**
- **Happy Path**: All standard authorization flows
- **Error Paths**: Exception handling and graceful degradation
- **Edge Cases**: Boundary conditions and unusual data states
- **Performance**: Large datasets and deep inheritance chains

### 🔒 **Security Focus**
- **Default Deny**: Ensures secure-by-default behavior
- **Privilege Escalation**: Tests inheritance doesn't grant unintended access
- **Data Isolation**: Multi-tenant boundary enforcement
- **Policy Combination**: Correct deny-overrides implementation

### ⚡ **Performance Validation**
- **Timing Metrics**: Evaluation time tracking and consistency
- **Scalability**: Large number of policies and deep role hierarchies
- **Caching Effects**: Repeated authorization call performance

### 🧪 **Test Quality**
- **Isolation**: Each test is independent and atomic
- **Mocking**: Proper repository and service mocking
- **Assertions**: Comprehensive result and reason validation
- **Documentation**: Clear test descriptions and expected behaviors

## Integration with CI/CD

These tests are designed to run in CI/CD pipelines with:
- **Fast execution** (< 30 seconds for full suite)
- **Reliable mocking** (no external dependencies)
- **Clear failure reporting** (detailed assertion messages)
- **Coverage reporting** (tracks authorization logic coverage)

## Maintenance Notes

When modifying the `AuthorizationService.authorize()` function:

1. **Update corresponding tests** for any logic changes
2. **Add new test cases** for new features or edge cases
3. **Verify inheritance tests** still pass with role hierarchy changes
4. **Check performance benchmarks** for any timing regressions
5. **Update documentation** for new authorization behaviors