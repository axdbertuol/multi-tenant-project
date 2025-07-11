from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from ...domain.entities.profile_folder_permission import ProfileFolderPermission
from ...domain.value_objects.folder_permission_level import FolderPermissionLevel
from ...domain.repositories.profile_folder_permission_repository import (
    ProfileFolderPermissionRepository,
)
from ...domain.repositories.profile_repository import ProfileRepository
from ...domain.repositories.user_profile_repository import UserProfileRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.organization_repository import OrganizationRepository
from ..dtos.profile_folder_permission_dto import (
    ProfileFolderPermissionCreateDTO,
    ProfileFolderPermissionUpdateDTO,
    ProfileFolderPermissionResponseDTO,
    ProfileFolderPermissionDetailResponseDTO,
    ProfileFolderPermissionListResponseDTO,
    ProfileFolderPermissionStatsDTO,
    ProfileFolderPermissionFilterDTO,
    ProfileFolderPermissionBulkActionDTO,
    ProfileFolderPermissionBulkActionResponseDTO,
    ProfileFolderPermissionValidationDTO,
    ProfileFolderPermissionValidationResponseDTO,
    UserFolderAccessDTO,
    UserFolderAccessResponseDTO,
    FolderPermissionMatrixDTO,
    FolderPermissionMatrixResponseDTO,
)


class ProfileFolderPermissionUseCase:
    """Use case for profile folder permission operations."""

    def __init__(
        self,
        profile_folder_permission_repository: ProfileFolderPermissionRepository,
        profile_repository: ProfileRepository,
        user_profile_repository: UserProfileRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ):
        self.profile_folder_permission_repository = profile_folder_permission_repository
        self.profile_repository = profile_repository
        self.user_profile_repository = user_profile_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def create_permission(
        self, dto: ProfileFolderPermissionCreateDTO
    ) -> ProfileFolderPermissionResponseDTO:
        """Create a new profile folder permission."""
        # Validate profile exists
        profile = self.profile_repository.get_by_id(dto.profile_id)
        if not profile:
            raise ValueError("Profile not found")

        # Validate organization exists
        organization = self.organization_repository.get_by_id(dto.organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Validate profile belongs to organization
        if profile.organization_id != dto.organization_id:
            raise ValueError("Profile must belong to the same organization")

        # Validate profile is active
        if not profile.is_active:
            raise ValueError("Cannot create permission for inactive profile")

        # Check if permission already exists for this profile and folder
        existing_permission = (
            self.profile_folder_permission_repository.get_by_profile_and_folder(
                dto.profile_id, dto.folder_path
            )
        )
        if existing_permission and existing_permission.is_active:
            raise ValueError(
                f"Permission already exists for profile {dto.profile_id} and folder {dto.folder_path}"
            )

        # Check for conflicting permissions
        conflicting_permissions = (
            self.profile_folder_permission_repository.get_conflicting_permissions(
                dto.profile_id, dto.folder_path
            )
        )
        if conflicting_permissions:
            conflicts = [
                f"{p.folder_path} ({p.permission_level.value})"
                for p in conflicting_permissions
            ]
            raise ValueError(f"Conflicting permissions found: {', '.join(conflicts)}")

        # Create permission entity
        permission = ProfileFolderPermission.create(
            profile_id=dto.profile_id,
            folder_path=dto.folder_path,
            permission_level=dto.permission_level,
            organization_id=dto.organization_id,
            created_by=dto.created_by,
            notes=dto.notes,
            extra_data=dto.extra_data,
        )

        # Validate permission
        is_valid, errors = permission.validate_permission()
        if not is_valid:
            raise ValueError(f"Permission validation failed: {', '.join(errors)}")

        # Save permission
        saved_permission = self.profile_folder_permission_repository.save(permission)

        return self._build_permission_response(saved_permission)

    def get_permission_by_id(
        self, permission_id: UUID
    ) -> Optional[ProfileFolderPermissionDetailResponseDTO]:
        """Get permission by ID with full details."""
        permission = self.profile_folder_permission_repository.get_by_id(permission_id)
        if not permission:
            return None

        return self._build_permission_detail_response(permission)

    def update_permission(
        self, permission_id: UUID, dto: ProfileFolderPermissionUpdateDTO
    ) -> Optional[ProfileFolderPermissionResponseDTO]:
        """Update an existing profile folder permission."""
        permission = self.profile_folder_permission_repository.get_by_id(permission_id)
        if not permission:
            return None

        # Update fields
        updated_permission = permission

        if dto.permission_level is not None:
            updated_permission = updated_permission.update_permission_level(
                dto.permission_level
            )

        if dto.folder_path is not None:
            # Check if new folder path conflicts
            if dto.folder_path != permission.folder_path:
                existing_permission = (
                    self.profile_folder_permission_repository.get_by_profile_and_folder(
                        permission.profile_id, dto.folder_path
                    )
                )
                if (
                    existing_permission
                    and existing_permission.is_active
                    and existing_permission.id != permission_id
                ):
                    raise ValueError(
                        f"Permission already exists for folder {dto.folder_path}"
                    )

            updated_permission = updated_permission.update_folder_path(dto.folder_path)

        if dto.notes is not None:
            updated_permission = updated_permission.update_notes(dto.notes)

        if dto.extra_data is not None:
            updated_permission = updated_permission.update_extra_data(dto.extra_data)

        if dto.is_active is not None:
            if dto.is_active:
                updated_permission = updated_permission.activate()
            else:
                updated_permission = updated_permission.deactivate()

        # Validate updated permission
        is_valid, errors = updated_permission.validate_permission()
        if not is_valid:
            raise ValueError(f"Permission validation failed: {', '.join(errors)}")

        # Save updated permission
        saved_permission = self.profile_folder_permission_repository.save(
            updated_permission
        )

        return self._build_permission_response(saved_permission)

    def delete_permission(self, permission_id: UUID) -> bool:
        """Delete a profile folder permission."""
        permission = self.profile_folder_permission_repository.get_by_id(permission_id)
        if not permission:
            return False

        return self.profile_folder_permission_repository.delete(permission_id)

    def list_permissions(
        self,
        filters: Optional[ProfileFolderPermissionFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProfileFolderPermissionListResponseDTO:
        """List profile folder permissions with filtering and pagination."""
        permissions = []

        # Apply filters
        if filters:
            if filters.profile_id:
                if filters.is_active is not None:
                    permissions = (
                        self.profile_folder_permission_repository.get_active_by_profile(
                            filters.profile_id
                        )
                        if filters.is_active
                        else []
                    )
                else:
                    permissions = (
                        self.profile_folder_permission_repository.get_by_profile(
                            filters.profile_id
                        )
                    )
            elif filters.organization_id:
                if filters.is_active is not None:
                    permissions = (
                        self.profile_folder_permission_repository.get_active_by_organization(
                            filters.organization_id
                        )
                        if filters.is_active
                        else []
                    )
                else:
                    permissions = (
                        self.profile_folder_permission_repository.get_by_organization(
                            filters.organization_id
                        )
                    )
            elif filters.folder_path:
                permissions = (
                    self.profile_folder_permission_repository.get_by_folder_path(
                        filters.folder_path, filters.organization_id
                    )
                )
            elif filters.folder_path_prefix:
                permissions = (
                    self.profile_folder_permission_repository.get_by_folder_path_prefix(
                        filters.folder_path_prefix, filters.organization_id
                    )
                )
            elif filters.permission_level:
                permissions = (
                    self.profile_folder_permission_repository.get_by_permission_level(
                        filters.permission_level, filters.organization_id
                    )
                )
            elif filters.created_by:
                permissions = (
                    self.profile_folder_permission_repository.get_by_created_by(
                        filters.created_by, filters.organization_id
                    )
                )
        else:
            permissions = []

        # Apply additional filters
        if filters and permissions:
            if filters.is_root_folder is not None:
                permissions = [
                    p
                    for p in permissions
                    if p.is_root_folder_permission() == filters.is_root_folder
                ]
            if filters.min_folder_depth is not None:
                permissions = [
                    p
                    for p in permissions
                    if p.get_folder_depth() >= filters.min_folder_depth
                ]
            if filters.max_folder_depth is not None:
                permissions = [
                    p
                    for p in permissions
                    if p.get_folder_depth() <= filters.max_folder_depth
                ]

        # Apply pagination
        total = len(permissions)
        offset = (page - 1) * page_size
        paginated_permissions = permissions[offset : offset + page_size]

        permission_responses = []
        for permission in paginated_permissions:
            permission_responses.append(self._build_permission_response(permission))

        total_pages = (total + page_size - 1) // page_size

        return ProfileFolderPermissionListResponseDTO(
            permissions=permission_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_permission_stats(
        self, organization_id: UUID
    ) -> ProfileFolderPermissionStatsDTO:
        """Get permission statistics for an organization."""
        all_permissions = self.profile_folder_permission_repository.get_by_organization(
            organization_id
        )
        active_permissions = [p for p in all_permissions if p.is_active]
        inactive_permissions = [p for p in all_permissions if not p.is_active]

        # Count by permission level
        permissions_by_level = {}
        for permission in all_permissions:
            level = permission.permission_level.value
            permissions_by_level[level] = permissions_by_level.get(level, 0) + 1

        # Count by folder
        permissions_by_folder = {}
        for permission in all_permissions:
            folder = permission.folder_path
            permissions_by_folder[folder] = permissions_by_folder.get(folder, 0) + 1

        # Count by profile
        permissions_by_profile = {}
        for permission in all_permissions:
            profile = self.profile_repository.get_by_id(permission.profile_id)
            profile_name = profile.name if profile else "Unknown"
            permissions_by_profile[profile_name] = (
                permissions_by_profile.get(profile_name, 0) + 1
            )

        # Count by creator
        permissions_by_creator = {}
        for permission in all_permissions:
            creator = self.user_repository.get_by_id(permission.created_by)
            creator_name = creator.name if creator else "Unknown"
            permissions_by_creator[creator_name] = (
                permissions_by_creator.get(creator_name, 0) + 1
            )

        # Count root and deep permissions
        root_folder_permissions = len(
            [p for p in all_permissions if p.is_root_folder_permission()]
        )
        deep_folder_permissions = len(
            [p for p in all_permissions if p.get_folder_depth() >= 3]
        )

        # Get recent permissions
        recent_permissions = (
            self.profile_folder_permission_repository.get_recently_created(
                organization_id, days=30
            )
        )
        recent_permission_responses = [
            self._build_permission_response(p) for p in recent_permissions
        ]

        # Get most used folders
        most_used_folders = sorted(
            permissions_by_folder.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Calculate permission level distribution
        total_permissions = len(all_permissions)
        permission_level_distribution = {}
        if total_permissions > 0:
            for level, count in permissions_by_level.items():
                permission_level_distribution[level] = (count / total_permissions) * 100

        return ProfileFolderPermissionStatsDTO(
            total_permissions=total_permissions,
            active_permissions=len(active_permissions),
            inactive_permissions=len(inactive_permissions),
            permissions_by_level=permissions_by_level,
            permissions_by_folder=permissions_by_folder,
            permissions_by_profile=permissions_by_profile,
            permissions_by_creator=permissions_by_creator,
            root_folder_permissions=root_folder_permissions,
            deep_folder_permissions=deep_folder_permissions,
            recent_permissions=recent_permission_responses,
            most_used_folders=most_used_folders,
            permission_level_distribution=permission_level_distribution,
        )

    def validate_permission(
        self, dto: ProfileFolderPermissionValidationDTO
    ) -> ProfileFolderPermissionValidationResponseDTO:
        """Validate a profile folder permission."""
        validation_errors = []
        validation_warnings = []
        conflicts = []
        hierarchy_issues = []
        recommendations = []

        # Check if profile exists
        profile = self.profile_repository.get_by_id(dto.profile_id)
        if not profile:
            validation_errors.append("Profile not found")
            return ProfileFolderPermissionValidationResponseDTO(
                is_valid=False,
                validation_errors=validation_errors,
            )

        # Check if profile is active
        if not profile.is_active:
            validation_errors.append("Profile is not active")

        # Check if profile belongs to organization
        if profile.organization_id != dto.organization_id:
            validation_errors.append(
                "Profile does not belong to the specified organization"
            )

        # Validate folder path format
        if not ProfileFolderPermission._validate_folder_path(dto.folder_path):
            validation_errors.append(f"Invalid folder path format: {dto.folder_path}")

        # Check for existing permission
        existing_permission = (
            self.profile_folder_permission_repository.get_by_profile_and_folder(
                dto.profile_id, dto.folder_path
            )
        )
        if existing_permission and existing_permission.is_active:
            validation_errors.append(
                "Permission already exists for this profile and folder"
            )

        # Check for conflicts
        if dto.check_conflicts:
            conflicting_permissions = (
                self.profile_folder_permission_repository.get_conflicting_permissions(
                    dto.profile_id, dto.folder_path
                )
            )
            if conflicting_permissions:
                conflicts = [p.id for p in conflicting_permissions]
                validation_warnings.append(
                    f"Found {len(conflicting_permissions)} conflicting permissions"
                )

        # Check hierarchy
        if dto.check_hierarchy:
            # Check if this is a reasonable folder structure
            folder_depth = dto.folder_path.count("/") - 2  # Subtract 2 for /documents/
            if folder_depth > 5:
                validation_warnings.append(
                    "Folder is very deep in hierarchy (> 5 levels)"
                )
                recommendations.append("Consider flattening the folder structure")

            # Check for parent folder permissions
            parent_path = "/".join(dto.folder_path.split("/")[:-1])
            if parent_path != "/documents":
                parent_permissions = (
                    self.profile_folder_permission_repository.get_by_folder_path(
                        parent_path, dto.organization_id
                    )
                )
                if parent_permissions:
                    parent_permission = next(
                        (
                            p
                            for p in parent_permissions
                            if p.profile_id == dto.profile_id
                        ),
                        None,
                    )
                    if parent_permission:
                        if parent_permission.permission_level.is_higher_than(
                            dto.permission_level
                        ):
                            validation_warnings.append(
                                f"Parent folder has higher permission level ({parent_permission.permission_level.value})"
                            )
                            recommendations.append(
                                "Consider using the parent folder permission instead"
                            )

        # Generate recommendations
        if dto.permission_level == FolderPermissionLevel.FULL:
            recommendations.append(
                "FULL permission grants extensive access - ensure this is necessary"
            )

        if dto.folder_path.endswith("/temp") or dto.folder_path.endswith("/tmp"):
            recommendations.append(
                "Temporary folders may not need persistent permissions"
            )

        return ProfileFolderPermissionValidationResponseDTO(
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            conflicts=conflicts,
            hierarchy_issues=hierarchy_issues,
            recommendations=recommendations,
        )

    def check_user_folder_access(
        self, dto: UserFolderAccessDTO
    ) -> UserFolderAccessResponseDTO:
        """Check if a user can access a specific folder."""
        # Get user's active profile assignments
        user_assignments = (
            self.user_profile_repository.get_active_by_user_and_organization(
                dto.user_id, dto.organization_id
            )
        )

        can_access = False
        permission_level = None
        allowed_actions = []
        access_reason = None
        applicable_profiles = []
        applicable_permissions = []

        # Check each profile assignment
        for assignment in user_assignments:
            profile_permissions = (
                self.profile_folder_permission_repository.get_active_by_profile(
                    assignment.profile_id
                )
            )

            for permission in profile_permissions:
                if permission.can_access_folder(dto.folder_path):
                    can_access = True

                    # Use the highest permission level found
                    if (
                        permission_level is None
                        or permission.permission_level.is_higher_than(permission_level)
                    ):
                        permission_level = permission.permission_level
                        allowed_actions = permission.get_allowed_actions()

                    # Track which profile and permission grants access
                    profile = self.profile_repository.get_by_id(assignment.profile_id)
                    if profile:
                        applicable_profiles.append(profile.name)
                    applicable_permissions.append(permission.id)

                    access_reason = f"Access granted through profile '{profile.name}' with {permission.permission_level.value} permission on {permission.folder_path}"

        # Check specific action if requested
        if dto.requested_action and can_access:
            if permission_level and not permission_level.can_perform_action(
                dto.requested_action
            ):
                can_access = False
                access_reason = f"User can access folder but cannot perform action '{dto.requested_action}'"

        return UserFolderAccessResponseDTO(
            user_id=dto.user_id,
            folder_path=dto.folder_path,
            can_access=can_access,
            permission_level=permission_level,
            allowed_actions=list(set(allowed_actions)),
            access_reason=access_reason,
            applicable_profiles=list(set(applicable_profiles)),
            applicable_permissions=list(set(applicable_permissions)),
        )

    def get_folder_permission_matrix(
        self, dto: FolderPermissionMatrixDTO
    ) -> FolderPermissionMatrixResponseDTO:
        """Get folder permission matrix for an organization."""
        # Get all permissions for organization
        all_permissions = (
            self.profile_folder_permission_repository.get_active_by_organization(
                dto.organization_id
            )
        )

        # Filter by specific folders if requested
        if dto.folder_paths:
            all_permissions = [
                p for p in all_permissions if p.folder_path in dto.folder_paths
            ]

        # Filter by specific profiles if requested
        if dto.profile_ids:
            all_permissions = [
                p for p in all_permissions if p.profile_id in dto.profile_ids
            ]

        # Include inactive permissions if requested
        if dto.include_inactive:
            inactive_permissions = (
                self.profile_folder_permission_repository.get_by_organization(
                    dto.organization_id
                )
            )
            inactive_permissions = [p for p in inactive_permissions if not p.is_active]
            all_permissions.extend(inactive_permissions)

        # Build matrix
        matrix = {}
        folder_paths = set()
        profile_names = set()

        for permission in all_permissions:
            folder_path = permission.folder_path
            profile = self.profile_repository.get_by_id(permission.profile_id)
            profile_name = (
                profile.name if profile else f"Profile-{permission.profile_id}"
            )

            if folder_path not in matrix:
                matrix[folder_path] = {}

            matrix[folder_path][profile_name] = permission.permission_level.value
            folder_paths.add(folder_path)
            profile_names.add(profile_name)

        # Calculate summary
        permission_summary = {}
        for permission in all_permissions:
            level = permission.permission_level.value
            permission_summary[level] = permission_summary.get(level, 0) + 1

        return FolderPermissionMatrixResponseDTO(
            organization_id=dto.organization_id,
            matrix=matrix,
            folder_paths=sorted(list(folder_paths)),
            profile_names=sorted(list(profile_names)),
            permission_summary=permission_summary,
            generated_at=datetime.now(timezone.utc),
        )

    def bulk_action(
        self, dto: ProfileFolderPermissionBulkActionDTO
    ) -> ProfileFolderPermissionBulkActionResponseDTO:
        """Perform bulk action on profile folder permissions."""
        success_count = 0
        failure_count = 0
        errors = []
        affected_permissions = []
        warnings = []

        for permission_id in dto.permission_ids:
            try:
                permission = self.profile_folder_permission_repository.get_by_id(
                    permission_id
                )
                if not permission:
                    failure_count += 1
                    errors.append(f"Permission {permission_id} not found")
                    continue

                if dto.action == "activate":
                    if permission.is_active:
                        warnings.append(f"Permission {permission_id} is already active")
                    else:
                        activated_permission = permission.activate()
                        self.profile_folder_permission_repository.save(
                            activated_permission
                        )
                        success_count += 1
                        affected_permissions.append(permission_id)

                elif dto.action == "deactivate":
                    if not permission.is_active:
                        warnings.append(
                            f"Permission {permission_id} is already inactive"
                        )
                    else:
                        deactivated_permission = permission.deactivate()
                        self.profile_folder_permission_repository.save(
                            deactivated_permission
                        )
                        success_count += 1
                        affected_permissions.append(permission_id)

                elif dto.action == "update_level":
                    if not dto.new_permission_level:
                        failure_count += 1
                        errors.append(
                            "New permission level required for update_level action"
                        )
                        continue

                    if permission.permission_level == dto.new_permission_level:
                        warnings.append(
                            f"Permission {permission_id} already has level {dto.new_permission_level.value}"
                        )
                    else:
                        updated_permission = permission.update_permission_level(
                            dto.new_permission_level
                        )
                        self.profile_folder_permission_repository.save(
                            updated_permission
                        )
                        success_count += 1
                        affected_permissions.append(permission_id)

                elif dto.action == "delete":
                    if self.profile_folder_permission_repository.delete(permission_id):
                        success_count += 1
                        affected_permissions.append(permission_id)
                    else:
                        failure_count += 1
                        errors.append(f"Failed to delete permission {permission_id}")

                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")

            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing permission {permission_id}: {str(e)}")

        return ProfileFolderPermissionBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_permissions=affected_permissions,
            warnings=warnings,
        )

    def _build_permission_response(
        self, permission: ProfileFolderPermission
    ) -> ProfileFolderPermissionResponseDTO:
        """Build permission response DTO."""
        # Get related data
        profile = self.profile_repository.get_by_id(permission.profile_id)
        creator = self.user_repository.get_by_id(permission.created_by)
        organization = self.organization_repository.get_by_id(
            permission.organization_id
        )

        return ProfileFolderPermissionResponseDTO(
            id=permission.id,
            profile_id=permission.profile_id,
            folder_path=permission.folder_path,
            permission_level=permission.permission_level,
            organization_id=permission.organization_id,
            created_by=permission.created_by,
            created_at=permission.created_at,
            updated_at=permission.updated_at,
            is_active=permission.is_active,
            notes=permission.notes,
            extra_data=permission.extra_data,
            profile_name=profile.name if profile else None,
            profile_description=profile.description if profile else None,
            created_by_name=creator.name if creator else None,
            organization_name=organization.name if organization else None,
            permission_level_display=permission.permission_level.get_display_name(),
            permission_level_description=permission.permission_level.get_description(),
            allowed_actions=permission.get_allowed_actions(),
            folder_depth=permission.get_folder_depth(),
            relative_path=permission.get_relative_path(),
            folder_name=permission.get_folder_name(),
            status=permission.get_status(),
            can_create_folders=permission.can_create_folders(),
            can_edit_documents=permission.can_edit_documents(),
            can_read_documents=permission.can_read_documents(),
            can_use_rag=permission.can_use_rag(),
            can_train_rag=permission.can_train_rag(),
        )

    def _build_permission_detail_response(
        self, permission: ProfileFolderPermission
    ) -> ProfileFolderPermissionDetailResponseDTO:
        """Build detailed permission response DTO."""
        permission_response = self._build_permission_response(permission)

        # Get related entities
        profile = self.profile_repository.get_by_id(permission.profile_id)
        creator = self.user_repository.get_by_id(permission.created_by)

        # Get hierarchical information
        parent_folder_path = permission.get_parent_folder_path()

        # Get child folders (simplified - would need proper implementation)
        child_folders = []

        # Get conflicting permissions
        conflicting_permissions = (
            self.profile_folder_permission_repository.get_conflicting_permissions(
                permission.profile_id, permission.folder_path
            )
        )
        conflicting_permission_ids = [
            p.id for p in conflicting_permissions if p.id != permission.id
        ]

        # Get hierarchical permissions
        hierarchical_permissions = []

        # Validation
        is_valid, validation_errors = permission.validate_permission()

        return ProfileFolderPermissionDetailResponseDTO(
            **permission_response.model_dump(),
            profile={
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "is_active": profile.is_active,
            }
            if profile
            else None,
            created_by_user={
                "id": creator.id,
                "name": creator.name,
                "email": creator.email,
                "is_active": creator.is_active,
            }
            if creator
            else None,
            parent_folder_path=parent_folder_path,
            child_folders=child_folders,
            conflicting_permissions=conflicting_permission_ids,
            hierarchical_permissions=hierarchical_permissions,
            validation_errors=validation_errors if not is_valid else [],
            is_root_folder=permission.is_root_folder_permission(),
            creation_age_days=permission.get_creation_age_days(),
            last_update_age_days=permission.get_last_update_age_days(),
            is_recently_created=permission.is_recently_created(),
            is_recently_updated=permission.is_recently_updated(),
        )
