from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.profile import Profile


class ProfileRepository(ABC):
    """Repository interface for Profile entities."""
    
    @abstractmethod
    def save(self, profile: Profile) -> Profile:
        """Save a profile entity."""
        pass
    
    @abstractmethod
    def get_by_id(self, profile_id: UUID) -> Optional[Profile]:
        """Get a profile by its ID."""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str, organization_id: UUID) -> Optional[Profile]:
        """Get a profile by name within an organization."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[Profile]:
        """Get all profiles for an organization."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[Profile]:
        """Get all active profiles for an organization."""
        pass
    
    @abstractmethod
    def get_system_profiles(self) -> List[Profile]:
        """Get all system profiles."""
        pass
    
    @abstractmethod
    def find_by_profile_metadata(self, metadata_key: str, metadata_value: str, organization_id: UUID) -> List[Profile]:
        """Find profiles by profile metadata key-value pair."""
        pass
    
    @abstractmethod
    def search_by_name(self, name_pattern: str, organization_id: UUID) -> List[Profile]:
        """Search profiles by name pattern."""
        pass
    
    @abstractmethod
    def get_profiles_created_by(self, created_by: UUID, organization_id: UUID) -> List[Profile]:
        """Get profiles created by a specific user."""
        pass
    
    @abstractmethod
    def get_profiles_by_status(self, is_active: bool, organization_id: UUID) -> List[Profile]:
        """Get profiles by active status."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Count profiles in an organization."""
        pass
    
    @abstractmethod
    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active profiles in an organization."""
        pass
    
    @abstractmethod
    def delete(self, profile_id: UUID) -> bool:
        """Delete a profile by its ID."""
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str, organization_id: UUID) -> bool:
        """Check if a profile with the given name exists in the organization."""
        pass
    
    @abstractmethod
    def get_recently_created(self, organization_id: UUID, days: int = 7) -> List[Profile]:
        """Get profiles created within the last N days."""
        pass
    
    @abstractmethod
    def get_recently_updated(self, organization_id: UUID, days: int = 7) -> List[Profile]:
        """Get profiles updated within the last N days."""
        pass
    
    @abstractmethod
    def bulk_update_status(self, profile_ids: List[UUID], is_active: bool) -> int:
        """Bulk update the active status of multiple profiles."""
        pass
    
    @abstractmethod
    def get_profiles_with_permissions_count(self, organization_id: UUID) -> List[tuple[Profile, int]]:
        """Get profiles with their permission count."""
        pass