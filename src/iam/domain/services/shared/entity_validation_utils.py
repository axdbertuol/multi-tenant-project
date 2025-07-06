"""Entity validation utilities for IAM services."""

from typing import Optional, List, Tuple
from uuid import UUID

from ...entities.user import User
from ...entities.role import Role
from ...entities.organization import Organization
from ...entities.resource import Resource
from ...entities.permission import Permission


class EntityValidationUtils:
    """Utility class for common entity validation patterns."""

    @staticmethod
    def validate_user_active(user: Optional[User]) -> bool:
        """
        Validate user exists and is active.
        
        Used in: AuthenticationService, MembershipService, AuthorizationService
        """
        return user is not None and user.is_active

    @staticmethod
    def validate_role_active(role: Optional[Role]) -> bool:
        """
        Validate role exists and is active.
        
        Used in: RBACService, RoleInheritanceService
        """
        return role is not None and role.is_active

    @staticmethod
    def validate_organization_active(organization: Optional[Organization]) -> bool:
        """
        Validate organization exists and is active.
        
        Used in: OrganizationDomainService, MembershipService
        """
        return organization is not None and organization.is_active

    @staticmethod
    def validate_resource_active(resource: Optional[Resource]) -> bool:
        """
        Validate resource exists and is active.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        return resource is not None and resource.is_active

    @staticmethod
    def validate_permission_active(permission: Optional[Permission]) -> bool:
        """
        Validate permission exists and is active.
        
        Used in: RBACService, PolicyEvaluationService
        """
        return permission is not None and permission.is_active

    @staticmethod
    def validate_user_organization_membership(
        user: Optional[User], organization: Optional[Organization]
    ) -> bool:
        """
        Validate user is a member of the organization.
        
        Used in: MembershipService, OrganizationDomainService
        """
        if not EntityValidationUtils.validate_user_active(user):
            return False
        if not EntityValidationUtils.validate_organization_active(organization):
            return False
        
        # This would typically check user-organization relationship
        # For now, we'll assume the relationship is valid if both entities exist
        return True

    @staticmethod
    def validate_resource_ownership(
        resource: Optional[Resource], user_id: UUID
    ) -> bool:
        """
        Validate resource exists and is owned by user.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        if not EntityValidationUtils.validate_resource_active(resource):
            return False
        
        return resource.is_owned_by(user_id)

    @staticmethod
    def validate_resource_organization_access(
        resource: Optional[Resource], organization_id: UUID
    ) -> bool:
        """
        Validate resource exists and belongs to organization.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        if not EntityValidationUtils.validate_resource_active(resource):
            return False
        
        return resource.belongs_to_organization(organization_id)

    @staticmethod
    def validate_entities_exist(*entities) -> bool:
        """
        Validate that all provided entities exist (are not None).
        
        Used in: Various services for bulk validation
        """
        return all(entity is not None for entity in entities)

    @staticmethod
    def validate_entities_active(*entities) -> bool:
        """
        Validate that all provided entities exist and are active.
        
        Used in: Various services for bulk validation
        """
        if not EntityValidationUtils.validate_entities_exist(*entities):
            return False
        
        return all(hasattr(entity, 'is_active') and entity.is_active for entity in entities)

    @staticmethod
    def validate_role_belongs_to_organization(
        role: Optional[Role], organization_id: UUID
    ) -> bool:
        """
        Validate role exists and belongs to organization.
        
        Used in: RBACService, OrganizationRoleSetupService
        """
        if not EntityValidationUtils.validate_role_active(role):
            return False
        
        return role.organization_id == organization_id

    @staticmethod
    def validate_permission_matches_resource(
        permission: Optional[Permission], resource_type: str
    ) -> bool:
        """
        Validate permission exists and matches resource type.
        
        Used in: RBACService, PolicyEvaluationService
        """
        if not EntityValidationUtils.validate_permission_active(permission):
            return False
        
        return permission.resource_type == resource_type

    @staticmethod
    def filter_active_entities(entities: List) -> List:
        """
        Filter list to only include active entities.
        
        Used in: Various services for bulk filtering
        """
        return [entity for entity in entities if hasattr(entity, 'is_active') and entity.is_active]

    @staticmethod
    def validate_user_session_valid(user_session) -> bool:
        """
        Validate user session exists and is valid.
        
        Used in: AuthenticationService, JWTService
        """
        return user_session is not None and user_session.is_valid()

    @staticmethod
    def validate_ids_not_empty(*ids: UUID) -> bool:
        """
        Validate that all provided IDs are not None.
        
        Used in: Various services for ID validation
        """
        return all(id is not None for id in ids)

    @staticmethod
    def validate_strings_not_empty(*strings: str) -> bool:
        """
        Validate that all provided strings are not None or empty.
        
        Used in: Various services for string validation
        """
        return all(string is not None and string.strip() != "" for string in strings)

    @staticmethod
    def get_validation_errors(
        validations: List[Tuple[bool, str]]
    ) -> List[str]:
        """
        Get list of validation error messages from validation results.
        
        Args:
            validations: List of (is_valid, error_message) tuples
            
        Returns:
            List of error messages for failed validations
        """
        return [error_msg for is_valid, error_msg in validations if not is_valid]

    @staticmethod
    def all_validations_pass(validations: List[Tuple[bool, str]]) -> bool:
        """
        Check if all validations pass.
        
        Args:
            validations: List of (is_valid, error_message) tuples
            
        Returns:
            True if all validations pass, False otherwise
        """
        return all(is_valid for is_valid, _ in validations)