from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class UserInfo(BaseModel):
    """User information from IAM context."""
    id: UUID
    email: str
    name: str
    organization_id: UUID
    is_active: bool


class ManagementFunctionInfo(BaseModel):
    """Management function information from IAM context."""
    id: UUID
    name: str
    description: str
    organization_id: UUID
    permissions: List[str]
    is_active: bool


class UserManagementAssignment(BaseModel):
    """User management function assignment from IAM context."""
    user_id: UUID
    organization_id: UUID
    function_id: UUID
    function_name: str
    permissions: List[str]
    assigned_at: datetime
    is_active: bool


class IAMContract(ABC):
    """
    Contract interface for Documents context to interact with IAM context.
    This defines what Documents context needs from IAM without creating tight coupling.
    """
    
    @abstractmethod
    def get_user_info(self, user_id: UUID) -> Optional[UserInfo]:
        """Get user information by ID."""
        pass
    
    @abstractmethod
    def verify_user_active(self, user_id: UUID, organization_id: UUID) -> bool:
        """Verify if user is active in the organization."""
        pass
    
    @abstractmethod
    def get_management_function_info(self, function_id: UUID) -> Optional[ManagementFunctionInfo]:
        """Get management function information by ID."""
        pass
    
    @abstractmethod
    def get_user_management_assignment(
        self, user_id: UUID, organization_id: UUID
    ) -> Optional[UserManagementAssignment]:
        """Get user's management function assignment for an organization."""
        pass
    
    @abstractmethod
    def verify_management_permission(
        self, user_id: UUID, organization_id: UUID, permission: str
    ) -> bool:
        """Verify if user has a specific management permission."""
        pass
    
    @abstractmethod
    def get_organization_users(self, organization_id: UUID) -> List[UserInfo]:
        """Get all users in an organization."""
        pass
    
    @abstractmethod
    def verify_organization_access(self, user_id: UUID, organization_id: UUID) -> bool:
        """Verify if user has access to an organization."""
        pass