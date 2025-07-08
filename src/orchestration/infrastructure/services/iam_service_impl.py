from typing import Protocol, Optional
from uuid import UUID

from ...application.use_cases.onboard_tenant import IamService
from ....iam.application.use_cases import (
    OrganizationUseCase,
    UserUseCase,
    MembershipUseCase,
    RoleUseCase,
    AuthorizationSubjectUseCase,
)
from ....iam.application.dtos import (
    OrganizationCreateDTO,
    UserOrganizationAssignmentDTO,
    RoleAssignmentDTO,
    AuthorizationSubjectCreateDTO,
)
from ....iam.domain.services import OrganizationRoleSetupService
from ....iam.domain.constants import DefaultRoles


class IamServiceImpl(IamService):
    def __init__(
        self,
        organization_use_case: OrganizationUseCase,
        user_use_case: UserUseCase,
        membership_use_case: MembershipUseCase,
        role_use_case: RoleUseCase,
        authorization_subject_use_case: AuthorizationSubjectUseCase,
        organization_role_setup_service: OrganizationRoleSetupService,
    ):
        self.organization_use_case = organization_use_case
        self.user_use_case = user_use_case
        self.membership_use_case = membership_use_case
        self.role_use_case = role_use_case
        self.authorization_subject_use_case = authorization_subject_use_case
        self.organization_role_setup_service = organization_role_setup_service

    def create_tenant(self, tenant_name: str, domain: str = None) -> str:
        """Create a new tenant organization."""
        create_dto = OrganizationCreateDTO(
            name=tenant_name,
            domain=domain,
            settings={"is_active": True, "created_via": "onboarding"},
        )
        
        organization = self.organization_use_case.create_organization(create_dto)
        
        # Setup default roles and permissions for the organization
        self.organization_role_setup_service.setup_default_roles_for_organization(
            organization.id
        )
        
        return str(organization.id)

    def assign_user_to_tenant(self, user_id: str, tenant_id: str) -> None:
        """Assign user to tenant organization."""
        assignment_dto = UserOrganizationAssignmentDTO(
            user_id=UUID(user_id),
            organization_id=UUID(tenant_id),
        )
        
        self.membership_use_case.add_user_to_organization(assignment_dto)

    def create_tenant_admin_role(self, tenant_id: str, user_id: str) -> None:
        """Assign admin/owner role to user in tenant organization."""
        # Get the organization owner role
        owner_role = self.role_use_case.get_role_by_name_and_organization(
            DefaultRoles.ORGANIZATION_OWNER.value, UUID(tenant_id)
        )
        
        if not owner_role:
            raise ValueError(f"Owner role not found for organization {tenant_id}")
        
        # Assign the owner role to the user
        role_assignment_dto = RoleAssignmentDTO(
            user_id=UUID(user_id),
            role_id=owner_role.id,
            organization_id=UUID(tenant_id),
        )
        
        self.membership_use_case.assign_role_to_user(role_assignment_dto)
        
        # Create authorization subject for the user in this organization
        auth_subject_dto = AuthorizationSubjectCreateDTO(
            user_id=UUID(user_id),
            organization_id=UUID(tenant_id),
            subject_type="user",
            metadata={"created_via": "onboarding", "role": "owner"},
        )
        
        self.authorization_subject_use_case.create_authorization_subject(auth_subject_dto)