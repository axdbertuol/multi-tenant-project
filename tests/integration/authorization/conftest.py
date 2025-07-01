import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import (
    Permission,
    PermissionAction,
)


@pytest.fixture
def creator_id():
    """Fixture for creator user ID."""
    return uuid4()


@pytest.fixture
def org_id():
    """Fixture for organization ID."""
    return uuid4()


@pytest.fixture
def sample_role(creator_id, org_id):
    """Create a sample role for testing."""
    return Role.create(
        name="Sample_Role",
        description="A sample role for testing",
        created_by=creator_id,
        organization_id=org_id,
    )


@pytest.fixture
def sample_system_role(creator_id):
    """Create a sample system role for testing."""
    return Role.create(
        name="System_Admin",
        description="System administrator role",
        created_by=creator_id,
        is_system_role=True,
    )


@pytest.fixture
def sample_permission():
    """Create a sample permission for testing."""
    return Permission.create(
        name="read_users",
        description="Permission to read user data",
        action=PermissionAction.READ,
        resource_type="user",
    )


@pytest.fixture
def default_rh_role(creator_id, org_id):
    """Create the Default_RH role mentioned in the user's scenario."""
    return Role.create(
        name="Default_RH",
        description="Default HR role with common permissions",
        created_by=creator_id,
        organization_id=org_id,
    )


@pytest.fixture
def default_rh_permissions():
    """Create common permissions for Default_RH role."""
    return [
        Permission.create(
            "read_users", "Read user profiles", PermissionAction.READ, "user"
        ),
        Permission.create(
            "update_user_basic",
            "Update basic user info",
            PermissionAction.UPDATE,
            "user_basic",
        ),
        Permission.create(
            "read_organizations",
            "Read organization data",
            PermissionAction.READ,
            "organization",
        ),
        Permission.create(
            "create_reports", "Create basic reports", PermissionAction.CREATE, "report"
        ),
        Permission.create(
            "read_attendance",
            "Read attendance records",
            PermissionAction.READ,
            "attendance",
        ),
        Permission.create(
            "manage_employee_records",
            "Manage employee records",
            PermissionAction.MANAGE,
            "employee_record",
        ),
        Permission.create(
            "generate_hr_reports",
            "Generate HR reports",
            PermissionAction.CREATE,
            "hr_report",
        ),
        Permission.create(
            "manage_benefits",
            "Manage employee benefits",
            PermissionAction.MANAGE,
            "benefits",
        ),
        Permission.create(
            "handle_disciplinary",
            "Handle disciplinary actions",
            PermissionAction.MANAGE,
            "disciplinary",
        ),
        Permission.create(
            "conduct_interviews",
            "Conduct job interviews",
            PermissionAction.EXECUTE,
            "interview",
        ),
    ]


@pytest.fixture
def enhanced_hr_role(creator_id, org_id, default_rh_role):
    """Create an Enhanced_HR role that inherits from Default_RH."""
    return Role.create(
        name="Enhanced_HR",
        description="Enhanced HR role with additional permissions beyond Default_RH",
        created_by=creator_id,
        organization_id=org_id,
        parent_role_id=default_rh_role.id,
    )


@pytest.fixture
def enhanced_hr_permissions():
    """Create additional permissions for Enhanced_HR role."""
    return [
        Permission.create(
            "delete_users", "Delete user accounts", PermissionAction.DELETE, "user"
        ),
        Permission.create(
            "manage_payroll", "Manage payroll data", PermissionAction.MANAGE, "payroll"
        ),
        Permission.create(
            "execute_bulk_operations",
            "Execute bulk user operations",
            PermissionAction.EXECUTE,
            "user_bulk",
        ),
        Permission.create(
            "create_policies", "Create HR policies", PermissionAction.CREATE, "policy"
        ),
        Permission.create(
            "approve_salary_changes",
            "Approve salary changes",
            PermissionAction.UPDATE,
            "salary",
        ),
        Permission.create(
            "manage_hr_policies",
            "Manage HR policies",
            PermissionAction.MANAGE,
            "hr_policy",
        ),
        Permission.create(
            "access_sensitive_data",
            "Access sensitive employee data",
            PermissionAction.READ,
            "sensitive_employee",
        ),
        Permission.create(
            "terminate_employees",
            "Terminate employee contracts",
            PermissionAction.DELETE,
            "employee",
        ),
    ]


@pytest.fixture
def role_hierarchy(creator_id, org_id):
    """Create a complex role hierarchy for testing."""
    # Employee base
    employee_base = Role.create(
        "Employee_Base", "Base employee role", creator_id, org_id
    )

    # Manager base (inherits from employee)
    manager_base = Role.create(
        "Manager_Base",
        "Base manager role",
        creator_id,
        org_id,
        parent_role_id=employee_base.id,
    )

    # HR Assistant (inherits from employee)
    hr_assistant = Role.create(
        "HR_Assistant",
        "HR assistant role",
        creator_id,
        org_id,
        parent_role_id=employee_base.id,
    )

    # Default_RH (inherits from HR assistant)
    default_rh = Role.create(
        "Default_RH",
        "Default HR role",
        creator_id,
        org_id,
        parent_role_id=hr_assistant.id,
    )

    # Senior HR (inherits from Default_RH)
    senior_hr = Role.create(
        "Senior_HR", "Senior HR role", creator_id, org_id, parent_role_id=default_rh.id
    )

    return {
        "employee_base": employee_base,
        "manager_base": manager_base,
        "hr_assistant": hr_assistant,
        "default_rh": default_rh,
        "senior_hr": senior_hr,
    }


@pytest.fixture
def mock_uow():
    """Create a mock unit of work for testing."""
    mock_uow = Mock()
    mock_uow.__enter__ = Mock(return_value=mock_uow)
    mock_uow.__exit__ = Mock(return_value=None)
    return mock_uow


@pytest.fixture
def mock_role_repository():
    """Create a mock role repository for testing."""
    return Mock()


@pytest.fixture
def mock_permission_repository():
    """Create a mock permission repository for testing."""
    return Mock()


@pytest.fixture
def mock_role_permission_repository():
    """Create a mock role-permission repository for testing."""
    return Mock()


@pytest.fixture
def configured_mock_uow(
    mock_uow,
    mock_role_repository,
    mock_permission_repository,
    mock_role_permission_repository,
):
    """Create a configured mock unit of work with repositories."""

    def get_repository(name):
        if name == "role":
            return mock_role_repository
        elif name == "permission":
            return mock_permission_repository
        elif name == "role_permission":
            return mock_role_permission_repository
        return None

    mock_uow.get_repository.side_effect = get_repository
    return mock_uow


@pytest.fixture
def sample_policies():
    """Create sample policies for testing."""
    return [
        {
            "name": "HR_Access_Policy",
            "description": "Policy for HR access control",
            "rules": {
                "resource": "employee_data",
                "action": "read",
                "conditions": [
                    "user.department == 'HR'",
                    "user.role in ['Default_RH', 'Enhanced_HR']",
                ],
            },
        },
        {
            "name": "Manager_Approval_Policy",
            "description": "Policy for manager approvals",
            "rules": {
                "resource": "time_off_request",
                "action": "approve",
                "conditions": [
                    "user.role contains 'Manager'",
                    "request.employee in user.managed_employees",
                ],
            },
        },
    ]


# Test data constants for edge cases
INVALID_ROLE_NAMES = [
    "",  # Empty name
    "a",  # Too short
    "a" * 101,  # Too long
    "Role With Invalid Chars!@#",  # Invalid characters
    "role-with-dashes",  # Dashes not allowed
    "123StartWithNumber",  # Starting with number
]

VALID_ROLE_NAMES = [
    "Valid_Role_Name",
    "HR_Manager_Level_2",
    "Finance_Analyst",
    "IT_Administrator",
    "Marketing_Coordinator",
]

ACTIONS = [
    PermissionAction.CREATE,
    PermissionAction.READ,
    PermissionAction.UPDATE,
    PermissionAction.DELETE,
    PermissionAction.EXECUTE,
    PermissionAction.MANAGE,
]

RESOURCE_TYPES = [
    "user",
    "organization",
    "project",
    "document",
    "financial_data",
    "hr_record",
    "system_setting",
    "report",
    "audit_log",
    "notification",
]

# Edge case scenarios for testing
CIRCULAR_INHERITANCE_SCENARIOS = [
    # Simple circle: A -> B -> A
    {"roles": ["A", "B"], "inheritance": [("B", "A"), ("A", "B")]},
    # Complex circle: A -> B -> C -> D -> A
    {
        "roles": ["A", "B", "C", "D"],
        "inheritance": [("B", "A"), ("C", "B"), ("D", "C"), ("A", "D")],
    },
    # Self-reference: A -> A
    {"roles": ["A"], "inheritance": [("A", "A")]},
]

CROSS_ORGANIZATION_SCENARIOS = [
    {
        "org1_roles": ["HR_Manager", "Finance_Manager"],
        "org2_roles": ["IT_Manager", "Sales_Manager"],
        "invalid_inheritance": [("org2.IT_Manager", "org1.HR_Manager")],
    }
]
