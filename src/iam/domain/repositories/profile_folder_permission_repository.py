from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from uuid import UUID

from ..entities.profile_folder_permission import ProfileFolderPermission
from ..value_objects.folder_permission_level import FolderPermissionLevel


class ProfileFolderPermissionRepository(ABC):
    """Repository interface for ProfileFolderPermission entities."""
    
    @abstractmethod
    def save(self, permission: ProfileFolderPermission) -> ProfileFolderPermission:
        """Save a profile folder permission."""
        pass
    
    @abstractmethod
    def get_by_id(self, permission_id: UUID) -> Optional[ProfileFolderPermission]:
        """Get a profile folder permission by its ID."""
        pass
    
    @abstractmethod
    def get_by_profile(self, profile_id: UUID) -> List[ProfileFolderPermission]:
        """Get all folder permissions for a profile."""
        pass
    
    @abstractmethod
    def get_active_by_profile(self, profile_id: UUID) -> List[ProfileFolderPermission]:
        """Get all active folder permissions for a profile."""
        pass
    
    @abstractmethod
    def get_by_profile_and_folder(self, profile_id: UUID, folder_path: str) -> Optional[ProfileFolderPermission]:
        """Get a specific folder permission for a profile."""
        pass
    
    @abstractmethod
    def get_by_folder_path(self, folder_path: str, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions for a specific folder path."""
        pass
    
    @abstractmethod
    def get_by_folder_path_prefix(self, folder_path_prefix: str, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions for folders starting with a path prefix."""
        pass
    
    @abstractmethod
    def get_by_organization(self, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all folder permissions for an organization."""
        pass
    
    @abstractmethod
    def get_active_by_organization(self, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all active folder permissions for an organization."""
        pass
    
    @abstractmethod
    def get_by_permission_level(self, permission_level: FolderPermissionLevel, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions with a specific permission level."""
        pass
    
    @abstractmethod
    def get_by_created_by(self, created_by: UUID, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all permissions created by a specific user."""
        pass
    
    @abstractmethod
    def get_permissions_for_user_profiles(self, user_id: UUID, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all folder permissions for a user's profiles."""
        pass
    
    @abstractmethod
    def get_effective_permissions_for_user(self, user_id: UUID, organization_id: UUID) -> Dict[str, FolderPermissionLevel]:
        """Get effective folder permissions for a user (consolidated from all profiles)."""
        pass
    
    @abstractmethod
    def get_folders_user_can_access(self, user_id: UUID, organization_id: UUID) -> List[str]:
        """Get all folder paths a user can access."""
        pass
    
    @abstractmethod
    def can_user_access_folder(self, user_id: UUID, folder_path: str, organization_id: UUID) -> bool:
        """Check if a user can access a specific folder."""
        pass
    
    @abstractmethod
    def get_user_permission_level_for_folder(self, user_id: UUID, folder_path: str, organization_id: UUID) -> Optional[FolderPermissionLevel]:
        """Get the highest permission level a user has for a specific folder."""
        pass
    
    @abstractmethod
    def get_conflicting_permissions(self, profile_id: UUID, folder_path: str) -> List[ProfileFolderPermission]:
        """Get permissions that conflict with a new permission."""
        pass
    
    @abstractmethod
    def get_hierarchical_permissions(self, profile_id: UUID) -> Dict[str, List[ProfileFolderPermission]]:
        """Get permissions grouped by folder hierarchy."""
        pass
    
    @abstractmethod
    def get_root_folder_permissions(self, organization_id: UUID) -> List[ProfileFolderPermission]:
        """Get all root folder permissions."""
        pass
    
    @abstractmethod
    def get_deep_folder_permissions(self, organization_id: UUID, min_depth: int = 3) -> List[ProfileFolderPermission]:
        """Get permissions for deep folders (high hierarchy level)."""
        pass
    
    @abstractmethod
    def count_by_profile(self, profile_id: UUID) -> int:
        """Count folder permissions for a profile."""
        pass
    
    @abstractmethod
    def count_active_by_profile(self, profile_id: UUID) -> int:
        """Count active folder permissions for a profile."""
        pass
    
    @abstractmethod
    def count_by_organization(self, organization_id: UUID) -> int:
        """Count folder permissions in an organization."""
        pass
    
    @abstractmethod
    def count_active_by_organization(self, organization_id: UUID) -> int:
        """Count active folder permissions in an organization."""
        pass
    
    @abstractmethod
    def count_by_permission_level(self, permission_level: FolderPermissionLevel, organization_id: UUID) -> int:
        """Count permissions by permission level."""
        pass
    
    @abstractmethod
    def delete(self, permission_id: UUID) -> bool:
        """Delete a folder permission."""
        pass
    
    @abstractmethod
    def delete_by_profile(self, profile_id: UUID) -> int:
        """Delete all folder permissions for a profile."""
        pass
    
    @abstractmethod
    def delete_by_folder_path(self, folder_path: str, organization_id: UUID) -> int:
        """Delete all permissions for a specific folder path."""
        pass
    
    @abstractmethod
    def exists_permission(self, profile_id: UUID, folder_path: str) -> bool:
        """Check if a permission exists for a profile and folder."""
        pass
    
    @abstractmethod
    def exists_active_permission(self, profile_id: UUID, folder_path: str) -> bool:
        """Check if an active permission exists for a profile and folder."""
        pass
    
    @abstractmethod
    def bulk_update_status(self, permission_ids: List[UUID], is_active: bool) -> int:
        """Bulk update the active status of multiple permissions."""
        pass
    
    @abstractmethod
    def bulk_update_permission_level(self, permission_ids: List[UUID], permission_level: FolderPermissionLevel) -> int:
        """Bulk update the permission level of multiple permissions."""
        pass
    
    @abstractmethod
    def get_permissions_stats(self, organization_id: UUID) -> Dict[str, int]:
        """Get statistics about permissions in an organization."""
        pass
    
    @abstractmethod
    def get_folder_usage_stats(self, organization_id: UUID) -> Dict[str, int]:
        """Get statistics about folder usage in permissions."""
        pass
    
    @abstractmethod
    def get_recently_created(self, organization_id: UUID, days: int = 7) -> List[ProfileFolderPermission]:
        """Get permissions created within the last N days."""
        pass
    
    @abstractmethod
    def get_recently_updated(self, organization_id: UUID, days: int = 7) -> List[ProfileFolderPermission]:
        """Get permissions updated within the last N days."""
        pass
    
    @abstractmethod
    def cleanup_orphaned_permissions(self, organization_id: UUID) -> int:
        """Clean up permissions for non-existent profiles."""
        pass