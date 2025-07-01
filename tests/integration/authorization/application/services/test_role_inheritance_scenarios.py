import pytest
from datetime import datetime
from uuid import uuid4, UUID
from typing import Dict, List

from authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from authorization.domain.services.role_inheritance_service import RoleInheritanceService
from authorization.application.use_cases.role_use_cases import RoleUseCase
from authorization.application.dtos.role_dto import RoleCreateDTO, RoleUpdateDTO


class TestRoleInheritanceScenarios:
    """Integration tests for complex role inheritance scenarios in real-world contexts."""
    
    def setup_method(self):
        """Set up realistic HR/business role hierarchy test scenario."""
        self.inheritance_service = RoleInheritanceService()
        self.creator_id = uuid4()
        self.org_id = uuid4()
        
        # Create realistic company role hierarchy
        self.setup_company_roles()
        self.setup_permissions()

    def setup_company_roles(self):
        """Set up a realistic company role hierarchy."""
        # Base roles
        self.employee_base = Role.create(
            "Employee_Base",
            "Basic employee permissions",
            self.creator_id,
            self.org_id
        )
        
        self.manager_base = Role.create(
            "Manager_Base", 
            "Basic manager permissions",
            self.creator_id,
            self.org_id,
            parent_role_id=self.employee_base.id
        )
        
        # HR roles hierarchy
        self.hr_assistant = Role.create(
            "HR_Assistant",
            "HR assistant with basic HR permissions", 
            self.creator_id,
            self.org_id,
            parent_role_id=self.employee_base.id
        )
        
        self.default_rh = Role.create(
            "Default_RH",
            "Default HR role with common permissions",
            self.creator_id,
            self.org_id,
            parent_role_id=self.hr_assistant.id
        )
        
        self.senior_hr = Role.create(
            "Senior_HR",
            "Senior HR role with enhanced permissions",
            self.creator_id,
            self.org_id,
            parent_role_id=self.default_rh.id
        )
        
        self.hr_manager = Role.create(
            "HR_Manager",
            "HR Manager with full HR permissions",
            self.creator_id,
            self.org_id,
            parent_role_id=self.manager_base.id  # Also inherits from manager track
        )
        
        # Finance roles
        self.finance_analyst = Role.create(
            "Finance_Analyst",
            "Finance analyst role",
            self.creator_id,
            self.org_id,
            parent_role_id=self.employee_base.id
        )
        
        self.finance_manager = Role.create(
            "Finance_Manager",
            "Finance manager role",
            self.creator_id,
            self.org_id,
            parent_role_id=self.manager_base.id
        )
        
        # Cross-functional roles
        self.compliance_officer = Role.create(
            "Compliance_Officer",
            "Compliance officer with cross-functional access",
            self.creator_id,
            self.org_id,
            parent_role_id=self.senior_hr.id  # Inherits from HR but has additional compliance permissions
        )

    def setup_permissions(self):
        """Set up permissions for each role level."""
        # Employee base permissions
        self.employee_permissions = [
            Permission.create("read_own_profile", "Read own user profile", PermissionAction.READ, "user_profile"),
            Permission.create("update_own_basic_info", "Update own basic info", PermissionAction.UPDATE, "user_basic"),
            Permission.create("read_company_directory", "Read company directory", PermissionAction.READ, "directory"),
            Permission.create("submit_time_off", "Submit time off requests", PermissionAction.CREATE, "time_off_request")
        ]
        
        # Manager base permissions (additional to employee)
        self.manager_permissions = [
            Permission.create("read_team_profiles", "Read team member profiles", PermissionAction.READ, "team_user"),
            Permission.create("approve_time_off", "Approve team time off", PermissionAction.UPDATE, "time_off_approval"),
            Permission.create("create_team_reports", "Create team reports", PermissionAction.CREATE, "team_report"),
            Permission.create("manage_team_tasks", "Manage team task assignments", PermissionAction.MANAGE, "team_task")
        ]
        
        # HR Assistant permissions
        self.hr_assistant_permissions = [
            Permission.create("read_all_employees", "Read all employee profiles", PermissionAction.READ, "all_users"),
            Permission.create("update_employee_basic", "Update employee basic info", PermissionAction.UPDATE, "employee_basic"),
            Permission.create("process_onboarding", "Process new employee onboarding", PermissionAction.CREATE, "onboarding")
        ]
        
        # Default_RH permissions (your specific use case)
        self.default_rh_permissions = [
            Permission.create("manage_employee_records", "Manage employee records", PermissionAction.MANAGE, "employee_record"),
            Permission.create("generate_hr_reports", "Generate HR reports", PermissionAction.CREATE, "hr_report"),
            Permission.create("manage_benefits", "Manage employee benefits", PermissionAction.MANAGE, "benefits"),
            Permission.create("handle_disciplinary", "Handle disciplinary actions", PermissionAction.MANAGE, "disciplinary"),
            Permission.create("conduct_interviews", "Conduct job interviews", PermissionAction.EXECUTE, "interview")
        ]
        
        # Senior HR additional permissions
        self.senior_hr_permissions = [
            Permission.create("approve_salary_changes", "Approve salary changes", PermissionAction.UPDATE, "salary"),
            Permission.create("manage_hr_policies", "Manage HR policies", PermissionAction.MANAGE, "hr_policy"),
            Permission.create("access_sensitive_data", "Access sensitive employee data", PermissionAction.READ, "sensitive_employee"),
            Permission.create("terminate_employees", "Terminate employee contracts", PermissionAction.DELETE, "employee")
        ]
        
        # HR Manager permissions
        self.hr_manager_permissions = [
            Permission.create("strategic_hr_planning", "Strategic HR planning", PermissionAction.MANAGE, "hr_strategy"),
            Permission.create("budget_management", "Manage HR budget", PermissionAction.MANAGE, "hr_budget"),
            Permission.create("vendor_management", "Manage HR vendors", PermissionAction.MANAGE, "hr_vendor")
        ]
        
        # Finance permissions
        self.finance_permissions = [
            Permission.create("read_financial_data", "Read financial data", PermissionAction.READ, "finance"),
            Permission.create("create_financial_reports", "Create financial reports", PermissionAction.CREATE, "finance_report"),
            Permission.create("manage_budgets", "Manage departmental budgets", PermissionAction.MANAGE, "budget")
        ]
        
        # Compliance-specific permissions
        self.compliance_permissions = [
            Permission.create("audit_hr_processes", "Audit HR processes", PermissionAction.EXECUTE, "hr_audit"),
            Permission.create("ensure_legal_compliance", "Ensure legal compliance", PermissionAction.MANAGE, "compliance"),
            Permission.create("investigate_violations", "Investigate policy violations", PermissionAction.EXECUTE, "investigation")
        ]

    def get_all_roles(self) -> List[Role]:
        """Get all roles in the test hierarchy."""
        return [
            self.employee_base, self.manager_base,
            self.hr_assistant, self.default_rh, self.senior_hr, self.hr_manager,
            self.finance_analyst, self.finance_manager,
            self.compliance_officer
        ]

    def get_role_permissions_map(self) -> Dict[UUID, List[Permission]]:
        """Get mapping of role IDs to their direct permissions."""
        return {
            self.employee_base.id: self.employee_permissions,
            self.manager_base.id: self.manager_permissions,
            self.hr_assistant.id: self.hr_assistant_permissions,
            self.default_rh.id: self.default_rh_permissions,
            self.senior_hr.id: self.senior_hr_permissions,
            self.hr_manager.id: self.hr_manager_permissions,
            self.finance_analyst.id: self.finance_permissions,
            self.finance_manager.id: [],  # Inherits from manager_base only
            self.compliance_officer.id: self.compliance_permissions
        }

    def test_default_rh_role_inheritance_scenario(self):
        """Test the specific Default_RH inheritance scenario mentioned by user."""
        all_roles = self.get_all_roles()
        role_permissions = self.get_role_permissions_map()
        
        # Test Default_RH has expected inheritance chain
        hierarchy_path = self.default_rh.get_role_hierarchy_path(all_roles)
        expected_path = [self.employee_base.id, self.hr_assistant.id, self.default_rh.id]
        assert hierarchy_path == expected_path
        
        # Calculate effective permissions for Default_RH
        effective_permissions = self.inheritance_service.calculate_inherited_permissions(
            self.default_rh, all_roles, role_permissions
        )
        
        # Should have permissions from Employee_Base + HR_Assistant + Default_RH
        expected_permission_count = (
            len(self.employee_permissions) + 
            len(self.hr_assistant_permissions) + 
            len(self.default_rh_permissions)
        )
        assert len(effective_permissions) == expected_permission_count
        
        # Verify specific permissions are present
        permission_names = [p.name.value for p in effective_permissions]
        
        # From Employee_Base
        assert "read_own_profile" in permission_names
        assert "submit_time_off" in permission_names
        
        # From HR_Assistant
        assert "read_all_employees" in permission_names
        assert "process_onboarding" in permission_names
        
        # From Default_RH
        assert "manage_employee_records" in permission_names
        assert "conduct_interviews" in permission_names

    def test_creating_enhanced_role_inheriting_from_default_rh(self):
        """Test creating a new role that inherits from Default_RH with additional permissions."""
        # Create Enhanced_RH role inheriting from Default_RH
        enhanced_rh = Role.create(
            "Enhanced_RH",
            "Enhanced HR role with additional permissions beyond Default_RH",
            self.creator_id,
            self.org_id,
            parent_role_id=self.default_rh.id
        )
        
        # Define exclusive permissions for Enhanced_RH
        enhanced_permissions = [
            Permission.create("manage_advanced_analytics", "Manage advanced HR analytics", PermissionAction.MANAGE, "hr_analytics"),
            Permission.create("configure_automated_workflows", "Configure HR automation", PermissionAction.MANAGE, "hr_automation"),
            Permission.create("access_executive_reports", "Access executive-level HR reports", PermissionAction.READ, "executive_report"),
            Permission.create("manage_global_policies", "Manage company-wide HR policies", PermissionAction.MANAGE, "global_policy")
        ]
        
        # Update role hierarchy and permissions
        all_roles = self.get_all_roles() + [enhanced_rh]
        role_permissions = self.get_role_permissions_map()
        role_permissions[enhanced_rh.id] = enhanced_permissions
        
        # Validate inheritance rules
        is_valid, message = enhanced_rh.validate_inheritance_rules(all_roles)
        assert is_valid is True
        
        # Calculate effective permissions
        effective_permissions = self.inheritance_service.calculate_inherited_permissions(
            enhanced_rh, all_roles, role_permissions
        )
        
        # Should have all Default_RH permissions plus enhanced permissions
        expected_count = (
            len(self.employee_permissions) +
            len(self.hr_assistant_permissions) +
            len(self.default_rh_permissions) +
            len(enhanced_permissions)
        )
        assert len(effective_permissions) == expected_count
        
        # Verify inheritance chain
        hierarchy_path = enhanced_rh.get_role_hierarchy_path(all_roles)
        expected_path = [
            self.employee_base.id,
            self.hr_assistant.id, 
            self.default_rh.id,
            enhanced_rh.id
        ]
        assert hierarchy_path == expected_path
        
        # Verify exclusive permissions are present
        permission_names = [p.name.value for p in effective_permissions]
        assert "manage_advanced_analytics" in permission_names
        assert "configure_automated_workflows" in permission_names
        
        # Verify inherited permissions still work
        assert "manage_employee_records" in permission_names  # From Default_RH
        assert "read_all_employees" in permission_names  # From HR_Assistant
        assert "read_own_profile" in permission_names  # From Employee_Base

    def test_complex_multi_inheritance_simulation(self):
        """Test simulating multiple inheritance through composition for complex scenarios."""
        # Create a role that needs both HR and Finance capabilities
        hr_finance_hybrid = Role.create(
            "HR_Finance_Hybrid",
            "Hybrid role with both HR and Finance capabilities",
            self.creator_id,
            self.org_id,
            parent_role_id=self.default_rh.id  # Inherits HR capabilities
        )
        
        # Add finance permissions directly to simulate multiple inheritance
        hybrid_permissions = [
            # Finance permissions (simulating inheritance from finance track)
            Permission.create("read_payroll_finances", "Read payroll financial data", PermissionAction.READ, "payroll_finance"),
            Permission.create("manage_hr_budget", "Manage HR department budget", PermissionAction.MANAGE, "hr_budget"),
            Permission.create("approve_hr_expenses", "Approve HR-related expenses", PermissionAction.UPDATE, "hr_expense"),
            
            # Unique hybrid permissions
            Permission.create("reconcile_hr_finance", "Reconcile HR and finance data", PermissionAction.EXECUTE, "hr_finance_reconciliation"),
            Permission.create("generate_cost_per_hire", "Generate cost-per-hire reports", PermissionAction.CREATE, "cost_per_hire_report")
        ]
        
        all_roles = self.get_all_roles() + [hr_finance_hybrid]
        role_permissions = self.get_role_permissions_map()
        role_permissions[hr_finance_hybrid.id] = hybrid_permissions
        
        effective_permissions = self.inheritance_service.calculate_inherited_permissions(
            hr_finance_hybrid, all_roles, role_permissions
        )
        
        permission_names = [p.name.value for p in effective_permissions]
        
        # Should have HR capabilities (inherited)
        assert "manage_employee_records" in permission_names
        assert "read_all_employees" in permission_names
        
        # Should have finance capabilities (direct)
        assert "read_payroll_finances" in permission_names
        assert "manage_hr_budget" in permission_names
        
        # Should have unique hybrid capabilities
        assert "reconcile_hr_finance" in permission_names
        assert "generate_cost_per_hire" in permission_names

    def test_role_hierarchy_validation_in_complex_organization(self):
        """Test comprehensive role hierarchy validation in complex organizational structure."""
        all_roles = self.get_all_roles()
        errors = self.inheritance_service.validate_role_hierarchy(all_roles)
        
        # Should have no validation errors
        assert len(errors) == 0
        
        # Test role tree structure
        role_tree = self.inheritance_service.build_role_tree(all_roles)
        
        # Employee_Base should be at root level
        root_roles = role_tree.get("root", [])
        assert self.employee_base in root_roles
        
        # Manager_Base should inherit from Employee_Base
        employee_children = role_tree.get(self.employee_base.id, [])
        assert self.manager_base in employee_children
        assert self.hr_assistant in employee_children
        assert self.finance_analyst in employee_children

    def test_permission_conflict_resolution_in_inheritance(self):
        """Test how permission conflicts are resolved in complex inheritance."""
        # Create scenario where child role overrides parent permission
        specialized_rh = Role.create(
            "Specialized_RH",
            "Specialized HR role with permission overrides",
            self.creator_id,
            self.org_id,
            parent_role_id=self.default_rh.id
        )
        
        # Override a permission from parent with more specific version
        specialized_permissions = [
            Permission.create(
                "manage_employee_records_advanced",
                "Advanced employee record management with audit trail",
                PermissionAction.MANAGE,
                "employee_record"  # Same resource type as parent
            ),
            Permission.create(
                "exclusive_specialized_function",
                "Function only available to specialized role",
                PermissionAction.EXECUTE,
                "specialized_function"
            )
        ]
        
        all_roles = self.get_all_roles() + [specialized_rh]
        role_permissions = self.get_role_permissions_map()
        role_permissions[specialized_rh.id] = specialized_permissions
        
        effective_permissions = self.inheritance_service.calculate_inherited_permissions(
            specialized_rh, all_roles, role_permissions
        )
        
        # Check for permission conflicts on same resource
        employee_record_permissions = [
            p for p in effective_permissions 
            if p.resource_type == "employee_record" and p.action == PermissionAction.MANAGE
        ]
        
        # Should have only one MANAGE permission for employee_record resource
        # (child overrides parent due to inheritance order)
        assert len(employee_record_permissions) == 1
        assert employee_record_permissions[0].name.value == "manage_employee_records_advanced"

    def test_user_with_multiple_roles_permission_aggregation(self):
        """Test permission aggregation for users with multiple roles."""
        # Simulate user with multiple roles
        user_role_ids = [
            self.default_rh.id,
            self.finance_analyst.id,  # User also has finance responsibilities
            self.compliance_officer.id  # User also handles compliance
        ]
        
        all_roles = self.get_all_roles()
        role_permissions = self.get_role_permissions_map()
        
        effective_permissions = self.inheritance_service.get_effective_permissions_for_user_roles(
            user_role_ids, all_roles, role_permissions
        )
        
        permission_names = [p.name.value for p in effective_permissions]
        
        # Should have permissions from all role hierarchies
        # From Default_RH hierarchy
        assert "manage_employee_records" in permission_names
        assert "read_all_employees" in permission_names
        
        # From Finance role
        assert "read_financial_data" in permission_names
        assert "create_financial_reports" in permission_names
        
        # From Compliance role (and its inheritance from Senior_HR)
        assert "audit_hr_processes" in permission_names
        assert "access_sensitive_data" in permission_names  # Inherited from Senior_HR

    def test_role_inheritance_performance_with_realistic_hierarchy(self):
        """Test performance characteristics with realistic role hierarchy size."""
        # Create larger, more realistic hierarchy
        extended_roles = self.get_all_roles()
        
        # Add department-specific roles
        departments = ["Engineering", "Sales", "Marketing", "Operations", "Legal"]
        
        for dept in departments:
            # Department base role
            dept_base = Role.create(
                f"{dept}_Base",
                f"Base role for {dept} department",
                self.creator_id,
                self.org_id,
                parent_role_id=self.employee_base.id
            )
            extended_roles.append(dept_base)
            
            # Department manager
            dept_manager = Role.create(
                f"{dept}_Manager",
                f"Manager role for {dept} department",
                self.creator_id,
                self.org_id,
                parent_role_id=self.manager_base.id
            )
            extended_roles.append(dept_manager)
            
            # Senior roles
            dept_senior = Role.create(
                f"Senior_{dept}",
                f"Senior role for {dept} department",
                self.creator_id,
                self.org_id,
                parent_role_id=dept_base.id
            )
            extended_roles.append(dept_senior)
        
        # Test hierarchy operations on larger dataset
        errors = self.inheritance_service.validate_role_hierarchy(extended_roles)
        assert len(errors) == 0  # Should handle larger hierarchy without issues
        
        # Test specific role calculations
        engineering_manager = next(r for r in extended_roles if r.name.value == "Engineering_Manager")
        hierarchy_path = engineering_manager.get_role_hierarchy_path(extended_roles)
        
        # Should have proper inheritance: Employee_Base -> Manager_Base -> Engineering_Manager
        assert len(hierarchy_path) == 3
        assert hierarchy_path[0] == self.employee_base.id
        assert hierarchy_path[1] == self.manager_base.id
        assert hierarchy_path[2] == engineering_manager.id

    def test_role_deactivation_cascade_effects(self):
        """Test effects of role deactivation on inheritance chains."""
        all_roles = self.get_all_roles()
        
        # Test what happens when Default_RH is deactivated
        deactivated_default_rh = self.default_rh.deactivate()
        roles_with_deactivated = [
            r if r.id != self.default_rh.id else deactivated_default_rh 
            for r in all_roles
        ]
        
        # Senior_HR should now be invalid because it inherits from inactive Default_RH
        is_valid, message = self.senior_hr.validate_inheritance_rules(roles_with_deactivated)
        assert is_valid is False
        assert "Cannot inherit from inactive role" in message
        
        # Compliance_Officer should also be invalid (inherits from Senior_HR which inherits from inactive Default_RH)
        is_valid, message = self.compliance_officer.validate_inheritance_rules(roles_with_deactivated)
        assert is_valid is False

    def test_cross_organizational_role_inheritance_restrictions(self):
        """Test that roles cannot inherit across organizational boundaries."""
        other_org_id = uuid4()
        
        # Create role in different organization
        other_org_default_rh = Role.create(
            "Other_Org_Default_RH",
            "Default RH role in different organization",
            self.creator_id,
            other_org_id
        )
        
        # Try to create role in current org inheriting from other org
        can_inherit, reason = self.inheritance_service.can_role_inherit_from(
            self.senior_hr, other_org_default_rh, [self.senior_hr, other_org_default_rh]
        )
        
        assert can_inherit is False
        assert "same organization" in reason