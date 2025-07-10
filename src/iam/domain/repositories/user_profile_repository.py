from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..entities.user_profile import UserProfile


class UserProfileRepository(ABC):
    """Repository interface for UserProfile entities."""
    
    @abstractmethod
    def save(self, user_profile: UserProfile) -> UserProfile:
        """Save a user profile assignment."""
        pass
    
    @abstractmethod
    def get_by_id(self, user_profile_id: UUID) -> Optional[UserProfile]:
        """Get a user profile assignment by its ID."""
        pass
    
    @abstractmethod
    def get_by_user_and_profile(self, user_id: UUID, profile_id: UUID) -> Optional[UserProfile]:
        """Get a user profile assignment by user and profile IDs."""
        pass
    
    @abstractmethod
    def get_by_user(self, user_id: UUID) -> List[UserProfile]:
        """Get all profile assignments for a user."""
        pass
    
    @abstractmethod
    def get_active_by_user(self, user_id: UUID) -> List[UserProfile]:
        """Get all active profile assignments for a user."""
        pass
    
    @abstractmethod
    def get_by_profile(self, profile_id: UUID) -> List[UserProfile]:
        """Get all user assignments for a profile."""
        pass
    
    @abstractmethod
    def get_active_by_profile(self, profile_id: UUID) -> List[UserProfile]:
        """Get all active user assignments for a profile."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[UserProfile]:
        """Get all user profile assignments for an organization."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[UserProfile]:
        """Get all active user profile assignments for an organization."""
        pass
    
    @abstractmethod
    def get_by_user_and_organization(self, user_id: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get all profile assignments for a user in an organization."""
        pass
    
    @abstractmethod
    def get_active_by_user_and_organization(self, user_id: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get all active profile assignments for a user in an organization."""
        pass
    
    @abstractmethod
    def get_expiring_soon(self, organization_id: UUID, days_ahead: int = 7) -> List[UserProfile]:
        """Get user profile assignments expiring soon."""
        pass
    
    @abstractmethod
    def get_expired(self, organization_id: UUID) -> List[UserProfile]:
        """Get expired user profile assignments."""
        pass
    
    @abstractmethod
    def get_by_assigned_by(self, assigned_by: UUID, organization_id: UUID) -> List[UserProfile]:
        """Get user profile assignments created by a specific user."""
        pass
    
    @abstractmethod
    def get_by_date_range(self, start_date: datetime, end_date: datetime, organization_id: UUID) -> List[UserProfile]:
        """Get user profile assignments within a date range."""
        pass
    
    @abstractmethod
    def get_temporary_assignments(self, organization_id: UUID) -> List[UserProfile]:
        """Get all temporary (with expiration) assignments."""
        pass
    
    @abstractmethod
    def get_permanent_assignments(self, organization_id: UUID) -> List[UserProfile]:
        """Get all permanent (without expiration) assignments."""
        pass
    
    @abstractmethod
    def get_revoked_assignments(self, organization_id: UUID) -> List[UserProfile]:
        """Get all revoked assignments."""
        pass
    
    @abstractmethod
    def count_by_profile(self, profile_id: UUID) -> int:
        """Count user assignments for a profile."""
        pass
    
    @abstractmethod
    def count_active_by_profile(self, profile_id: UUID) -> int:
        """Count active user assignments for a profile."""
        pass
    
    @abstractmethod
    def count_by_user(self, user_id: UUID) -> int:
        """Count profile assignments for a user."""
        pass
    
    @abstractmethod
    def count_active_by_user(self, user_id: UUID) -> int:
        """Count active profile assignments for a user."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Count user profile assignments in an organization."""
        pass
    
    @abstractmethod
    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active user profile assignments in an organization."""
        pass
    
    @abstractmethod
    def delete(self, user_profile_id: UUID) -> bool:
        """Delete a user profile assignment."""
        pass
    
    @abstractmethod
    def delete_by_user(self, user_id: UUID) -> int:
        """Delete all profile assignments for a user."""
        pass
    
    @abstractmethod
    def delete_by_profile(self, profile_id: UUID) -> int:
        """Delete all user assignments for a profile."""
        pass
    
    @abstractmethod
    def exists_active_assignment(self, user_id: UUID, profile_id: UUID) -> bool:
        """Check if an active assignment exists between user and profile."""
        pass
    
    @abstractmethod
    def bulk_update_status(self, user_profile_ids: List[UUID], is_active: bool) -> int:
        """Bulk update the active status of multiple assignments."""
        pass
    
    @abstractmethod
    def bulk_extend_expiration(self, user_profile_ids: List[UUID], new_expiration: datetime) -> int:
        """Bulk extend expiration date for multiple assignments."""
        pass
    
    @abstractmethod
    def bulk_revoke(self, user_profile_ids: List[UUID], revoked_by: UUID, reason: str) -> int:
        """Bulk revoke multiple assignments."""
        pass
    
    @abstractmethod
    def get_user_profiles_with_details(self, organization_id: UUID) -> List[tuple[UserProfile, str, str]]:
        """Get user profiles with user and profile names."""
        pass
    
    @abstractmethod
    def get_assignment_history(self, user_id: UUID, profile_id: UUID) -> List[UserProfile]:
        """Get assignment history between a user and profile."""
        pass
    
    @abstractmethod
    def cleanup_expired_assignments(self, organization_id: UUID) -> int:
        """Clean up expired assignments (mark as inactive)."""
        pass