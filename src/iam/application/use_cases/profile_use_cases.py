from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ...domain.entities.profile import Profile
from ...domain.repositories.profile_repository import ProfileRepository
from ...domain.repositories.user_profile_repository import UserProfileRepository
from ...domain.repositories.profile_folder_permission_repository import ProfileFolderPermissionRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.organization_repository import OrganizationRepository
from ..dtos.profile_dto import (
    ProfileCreateDTO,
    ProfileUpdateDTO,
    ProfileResponseDTO,
    ProfileDetailResponseDTO,
    ProfileListResponseDTO,
    ProfileStatsDTO,
    ProfileFilterDTO,
    ProfileSearchDTO,
    ProfileBulkActionDTO,
    ProfileBulkActionResponseDTO,
    ProfileValidationDTO,
    ProfileValidationResponseDTO,
    ProfileCloneDTO,
    ProfileCloneResponseDTO,
    ProfileUsageStatsDTO,
)


class ProfileUseCase:
    """Use case for profile management operations."""

    def __init__(
        self,
        profile_repository: ProfileRepository,
        user_profile_repository: UserProfileRepository,
        profile_folder_permission_repository: ProfileFolderPermissionRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
    ):
        self.profile_repository = profile_repository
        self.user_profile_repository = user_profile_repository
        self.profile_folder_permission_repository = profile_folder_permission_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository

    def create_profile(self, dto: ProfileCreateDTO) -> ProfileResponseDTO:
        """Create a new profile."""
        # Validate user exists and has permission to create profiles
        creator = self.user_repository.get_by_id(dto.created_by)
        if not creator:
            raise ValueError("Creator user not found")

        # Validate organization exists
        organization = self.organization_repository.get_by_id(dto.organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Check if profile with same name already exists
        if self.profile_repository.exists_by_name(dto.name, dto.organization_id):
            raise ValueError(f"Profile with name '{dto.name}' already exists in this organization")

        # Create profile entity
        profile = Profile.create(
            name=dto.name,
            description=dto.description,
            organization_id=dto.organization_id,
            created_by=dto.created_by,
            is_system_profile=dto.is_system_profile,
            profile_metadata=dto.profile_metadata,
        )

        # Validate profile before saving
        is_valid, errors = profile.validate_profile()
        if not is_valid:
            raise ValueError(f"Profile validation failed: {', '.join(errors)}")

        # Save profile
        saved_profile = self.profile_repository.save(profile)

        return self._build_profile_response(saved_profile)

    def get_profile_by_id(self, profile_id: UUID) -> Optional[ProfileDetailResponseDTO]:
        """Get profile by ID with full details."""
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            return None

        return self._build_profile_detail_response(profile)

    def update_profile(self, profile_id: UUID, dto: ProfileUpdateDTO) -> Optional[ProfileResponseDTO]:
        """Update an existing profile."""
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            return None

        # Check if profile can be modified
        can_modify, reason = profile.can_be_modified()
        if not can_modify:
            raise ValueError(f"Profile cannot be modified: {reason}")

        # Update fields
        updated_profile = profile
        if dto.name is not None:
            # Check if new name conflicts with existing profiles
            if dto.name != profile.name and self.profile_repository.exists_by_name(dto.name, profile.organization_id):
                raise ValueError(f"Profile with name '{dto.name}' already exists in this organization")
            updated_profile = updated_profile.update_name(dto.name)

        if dto.description is not None:
            updated_profile = updated_profile.update_description(dto.description)

        if dto.profile_metadata is not None:
            updated_profile = updated_profile.update_profile_metadata(dto.profile_metadata)

        if dto.is_active is not None:
            if dto.is_active:
                updated_profile = updated_profile.activate()
            else:
                updated_profile = updated_profile.deactivate()

        # Validate updated profile
        is_valid, errors = updated_profile.validate_profile()
        if not is_valid:
            raise ValueError(f"Profile validation failed: {', '.join(errors)}")

        # Save updated profile
        saved_profile = self.profile_repository.save(updated_profile)

        return self._build_profile_response(saved_profile)

    def delete_profile(self, profile_id: UUID) -> bool:
        """Delete a profile."""
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            return False

        # Check if profile can be deleted
        can_delete, reason = profile.can_be_deleted()
        if not can_delete:
            raise ValueError(f"Profile cannot be deleted: {reason}")

        # Check if profile has active user assignments
        active_assignments = self.user_profile_repository.get_active_by_profile(profile_id)
        if active_assignments:
            raise ValueError(f"Cannot delete profile with {len(active_assignments)} active user assignments")

        # Delete related permissions first
        self.profile_folder_permission_repository.delete_by_profile(profile_id)

        # Delete profile
        return self.profile_repository.delete(profile_id)

    def list_profiles(
        self,
        filters: Optional[ProfileFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ProfileListResponseDTO:
        """List profiles with filtering and pagination."""
        profiles = []

        # Apply filters
        if filters:
            if filters.organization_id:
                if filters.is_active is not None:
                    profiles = self.profile_repository.get_profiles_by_status(
                        filters.is_active, filters.organization_id
                    )
                else:
                    profiles = self.profile_repository.get_by_organization(filters.organization_id)
            elif filters.created_by:
                profiles = self.profile_repository.get_profiles_created_by(
                    filters.created_by, filters.organization_id
                )
            elif filters.is_system_profile is not None:
                if filters.is_system_profile:
                    profiles = self.profile_repository.get_system_profiles()
                else:
                    # Get non-system profiles for organization
                    all_profiles = self.profile_repository.get_by_organization(filters.organization_id)
                    profiles = [p for p in all_profiles if not p.is_system_profile]
        else:
            profiles = []

        # Apply additional filters
        if filters:
            if filters.name:
                profiles = [p for p in profiles if filters.name.lower() in p.name.lower()]
            if filters.has_users is not None:
                for profile in profiles:
                    user_count = self.user_profile_repository.count_active_by_profile(profile.id)
                    if filters.has_users and user_count == 0:
                        profiles.remove(profile)
                    elif not filters.has_users and user_count > 0:
                        profiles.remove(profile)
            if filters.has_permissions is not None:
                for profile in profiles:
                    permission_count = self.profile_folder_permission_repository.count_active_by_profile(profile.id)
                    if filters.has_permissions and permission_count == 0:
                        profiles.remove(profile)
                    elif not filters.has_permissions and permission_count > 0:
                        profiles.remove(profile)

        # Apply pagination
        total = len(profiles)
        offset = (page - 1) * page_size
        paginated_profiles = profiles[offset:offset + page_size]

        profile_responses = []
        for profile in paginated_profiles:
            profile_responses.append(self._build_profile_response(profile))

        total_pages = (total + page_size - 1) // page_size

        return ProfileListResponseDTO(
            profiles=profile_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_profile_stats(self, organization_id: UUID) -> ProfileStatsDTO:
        """Get profile statistics for an organization."""
        all_profiles = self.profile_repository.get_by_organization(organization_id)
        active_profiles = [p for p in all_profiles if p.is_active]
        inactive_profiles = [p for p in all_profiles if not p.is_active]
        system_profiles = [p for p in all_profiles if p.is_system_profile]
        user_profiles = [p for p in all_profiles if not p.is_system_profile]

        # Count profiles with users and permissions
        profiles_with_users = 0
        profiles_with_permissions = 0
        
        for profile in all_profiles:
            if self.user_profile_repository.count_active_by_profile(profile.id) > 0:
                profiles_with_users += 1
            if self.profile_folder_permission_repository.count_active_by_profile(profile.id) > 0:
                profiles_with_permissions += 1

        # Get profiles by creator
        profiles_by_creator = {}
        for profile in all_profiles:
            creator = self.user_repository.get_by_id(profile.created_by)
            creator_name = creator.name if creator else "Unknown"
            profiles_by_creator[creator_name] = profiles_by_creator.get(creator_name, 0) + 1

        # Get recent profiles
        recent_profiles = self.profile_repository.get_recently_created(organization_id, days=30)
        recent_profile_responses = [self._build_profile_response(p) for p in recent_profiles]

        # Get most used profiles
        most_used_profiles = []
        for profile in all_profiles:
            user_count = self.user_profile_repository.count_active_by_profile(profile.id)
            if user_count > 0:
                most_used_profiles.append((self._build_profile_response(profile), user_count))
        
        most_used_profiles.sort(key=lambda x: x[1], reverse=True)
        most_used_profiles = most_used_profiles[:10]  # Top 10

        return ProfileStatsDTO(
            total_profiles=len(all_profiles),
            active_profiles=len(active_profiles),
            inactive_profiles=len(inactive_profiles),
            system_profiles=len(system_profiles),
            user_profiles=len(user_profiles),
            profiles_with_users=profiles_with_users,
            profiles_with_permissions=profiles_with_permissions,
            profiles_by_creator=profiles_by_creator,
            recent_profiles=recent_profile_responses,
            most_used_profiles=most_used_profiles,
        )

    def validate_profile(self, dto: ProfileValidationDTO) -> ProfileValidationResponseDTO:
        """Validate a profile."""
        profile = self.profile_repository.get_by_id(dto.profile_id)
        if not profile:
            return ProfileValidationResponseDTO(
                is_valid=False,
                validation_type=dto.validation_type,
                issues=[{"type": "error", "message": "Profile not found"}],
            )

        issues = []
        fixed_issues = []
        recommendations = []

        # Basic validation
        is_valid, errors = profile.validate_profile()
        if not is_valid:
            for error in errors:
                issues.append({"type": "error", "message": error})

        # Permission validation
        if dto.validation_type in ["full", "permissions"]:
            permissions = self.profile_folder_permission_repository.get_active_by_profile(profile.id)
            if not permissions:
                issues.append({"type": "warning", "message": "Profile has no folder permissions"})
                recommendations.append("Consider adding folder permissions to make this profile useful")

            # Check for conflicting permissions
            for i, perm1 in enumerate(permissions):
                for perm2 in permissions[i + 1:]:
                    if perm1.conflicts_with(perm2):
                        issues.append({
                            "type": "error",
                            "message": f"Conflicting permissions: {perm1.folder_path} and {perm2.folder_path}"
                        })

        # User assignment validation
        if dto.validation_type == "full":
            active_assignments = self.user_profile_repository.get_active_by_profile(profile.id)
            if not active_assignments:
                issues.append({"type": "info", "message": "Profile has no active user assignments"})

            # Check for expired assignments
            for assignment in active_assignments:
                if assignment.is_expired():
                    issues.append({
                        "type": "warning",
                        "message": f"User assignment {assignment.id} is expired but still active"
                    })
                    if dto.fix_issues:
                        updated_assignment = assignment.deactivate()
                        self.user_profile_repository.save(updated_assignment)
                        fixed_issues.append({
                            "type": "fix",
                            "message": f"Deactivated expired assignment {assignment.id}"
                        })

        return ProfileValidationResponseDTO(
            is_valid=len([i for i in issues if i["type"] == "error"]) == 0,
            validation_type=dto.validation_type,
            issues=issues,
            fixed_issues=fixed_issues,
            recommendations=recommendations,
        )

    def clone_profile(self, dto: ProfileCloneDTO) -> ProfileCloneResponseDTO:
        """Clone a profile."""
        source_profile = self.profile_repository.get_by_id(dto.source_profile_id)
        if not source_profile:
            raise ValueError("Source profile not found")

        target_organization_id = dto.target_organization_id or source_profile.organization_id

        # Check if new name conflicts
        if self.profile_repository.exists_by_name(dto.new_name, target_organization_id):
            raise ValueError(f"Profile with name '{dto.new_name}' already exists in target organization")

        # Create cloned profile
        cloned_profile = Profile.create(
            name=dto.new_name,
            description=dto.new_description or source_profile.description,
            organization_id=target_organization_id,
            created_by=dto.cloned_by,
            is_system_profile=False,  # Cloned profiles are never system profiles
            profile_metadata=source_profile.profile_metadata if dto.clone_profile_metadata else {},
        )

        saved_cloned_profile = self.profile_repository.save(cloned_profile)

        cloned_permissions_count = 0
        cloned_users_count = 0
        warnings = []

        # Clone permissions
        if dto.clone_permissions:
            source_permissions = self.profile_folder_permission_repository.get_active_by_profile(source_profile.id)
            for perm in source_permissions:
                try:
                    cloned_permission = perm.model_copy(update={
                        "id": uuid4(),
                        "profile_id": saved_cloned_profile.id,
                        "organization_id": target_organization_id,
                        "created_by": dto.cloned_by,
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": None,
                    })
                    self.profile_folder_permission_repository.save(cloned_permission)
                    cloned_permissions_count += 1
                except Exception as e:
                    warnings.append(f"Failed to clone permission for {perm.folder_path}: {str(e)}")

        # Clone user assignments
        if dto.clone_users:
            source_assignments = self.user_profile_repository.get_active_by_profile(source_profile.id)
            for assignment in source_assignments:
                try:
                    # Only clone if user exists in target organization
                    if target_organization_id == source_profile.organization_id:
                        cloned_assignment = assignment.model_copy(update={
                            "id": uuid4(),
                            "profile_id": saved_cloned_profile.id,
                            "assigned_by": dto.cloned_by,
                            "assigned_at": datetime.now(timezone.utc),
                            "revoked_at": None,
                            "revoked_by": None,
                        })
                        self.user_profile_repository.save(cloned_assignment)
                        cloned_users_count += 1
                    else:
                        warnings.append(f"Skipped cloning user assignment for different organization")
                except Exception as e:
                    warnings.append(f"Failed to clone user assignment: {str(e)}")

        return ProfileCloneResponseDTO(
            original_profile=self._build_profile_response(source_profile),
            cloned_profile=self._build_profile_response(saved_cloned_profile),
            cloned_permissions_count=cloned_permissions_count,
            cloned_users_count=cloned_users_count,
            warnings=warnings,
        )

    def get_profile_usage_stats(self, profile_id: UUID) -> ProfileUsageStatsDTO:
        """Get usage statistics for a profile."""
        profile = self.profile_repository.get_by_id(profile_id)
        if not profile:
            raise ValueError("Profile not found")

        # Get user assignments
        all_assignments = self.user_profile_repository.get_by_profile(profile_id)
        active_assignments = [a for a in all_assignments if a.is_active]
        inactive_assignments = [a for a in all_assignments if not a.is_active]

        # Get permissions
        permissions = self.profile_folder_permission_repository.get_active_by_profile(profile_id)
        
        # Count accessible folders
        folders_accessible = len(set(perm.folder_path for perm in permissions))

        # Get last assignment date
        last_assignment_date = None
        most_recent_user = None
        if all_assignments:
            latest_assignment = max(all_assignments, key=lambda x: x.assigned_at)
            last_assignment_date = latest_assignment.assigned_at
            user = self.user_repository.get_by_id(latest_assignment.user_id)
            most_recent_user = user.name if user else "Unknown"

        # Calculate usage score
        usage_score = self._calculate_profile_usage_score(profile, active_assignments, permissions)

        # Generate recommendations
        recommendations = []
        if len(active_assignments) == 0:
            recommendations.append("Profile has no active users - consider assigning users or archiving")
        if len(permissions) == 0:
            recommendations.append("Profile has no folder permissions - add permissions to make it useful")
        if usage_score < 30:
            recommendations.append("Low usage score - review if this profile is still needed")

        return ProfileUsageStatsDTO(
            profile_id=profile_id,
            profile_name=profile.name,
            active_users=len(active_assignments),
            inactive_users=len(inactive_assignments),
            total_users=len(all_assignments),
            permissions_count=len(permissions),
            folders_accessible=folders_accessible,
            last_assignment_date=last_assignment_date,
            most_recent_user=most_recent_user,
            usage_score=usage_score,
            recommendations=recommendations,
        )

    def bulk_action(self, dto: ProfileBulkActionDTO) -> ProfileBulkActionResponseDTO:
        """Perform bulk action on profiles."""
        success_count = 0
        failure_count = 0
        errors = []
        affected_profiles = []
        warnings = []

        for profile_id in dto.profile_ids:
            try:
                profile = self.profile_repository.get_by_id(profile_id)
                if not profile:
                    failure_count += 1
                    errors.append(f"Profile {profile_id} not found")
                    continue

                if dto.action == "activate":
                    if profile.is_active:
                        warnings.append(f"Profile {profile_id} is already active")
                    else:
                        activated_profile = profile.activate()
                        self.profile_repository.save(activated_profile)
                        success_count += 1
                        affected_profiles.append(profile_id)

                elif dto.action == "deactivate":
                    if not profile.is_active:
                        warnings.append(f"Profile {profile_id} is already inactive")
                    else:
                        deactivated_profile = profile.deactivate()
                        self.profile_repository.save(deactivated_profile)
                        success_count += 1
                        affected_profiles.append(profile_id)

                elif dto.action == "delete":
                    can_delete, reason = profile.can_be_deleted()
                    if not can_delete:
                        failure_count += 1
                        errors.append(f"Profile {profile_id} cannot be deleted: {reason}")
                        continue

                    # Check for active assignments
                    active_assignments = self.user_profile_repository.get_active_by_profile(profile_id)
                    if active_assignments:
                        failure_count += 1
                        errors.append(f"Profile {profile_id} has {len(active_assignments)} active assignments")
                        continue

                    # Delete permissions first
                    self.profile_folder_permission_repository.delete_by_profile(profile_id)
                    
                    # Delete profile
                    if self.profile_repository.delete(profile_id):
                        success_count += 1
                        affected_profiles.append(profile_id)
                    else:
                        failure_count += 1
                        errors.append(f"Failed to delete profile {profile_id}")

                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")

            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing profile {profile_id}: {str(e)}")

        return ProfileBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_profiles=affected_profiles,
            warnings=warnings,
        )

    def _build_profile_response(self, profile: Profile) -> ProfileResponseDTO:
        """Build profile response DTO."""
        # Get related data
        creator = self.user_repository.get_by_id(profile.created_by)
        organization = self.organization_repository.get_by_id(profile.organization_id)
        
        # Get counts
        user_count = self.user_profile_repository.count_active_by_profile(profile.id)
        permission_count = self.profile_folder_permission_repository.count_active_by_profile(profile.id)

        return ProfileResponseDTO(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            organization_id=profile.organization_id,
            created_by=profile.created_by,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            is_active=profile.is_active,
            is_system_profile=profile.is_system_profile,
            profile_metadata=profile.profile_metadata,
            created_by_name=creator.name if creator else None,
            organization_name=organization.name if organization else None,
            user_count=user_count,
            permission_count=permission_count,
            status=profile.get_status(),
        )

    def _build_profile_detail_response(self, profile: Profile) -> ProfileDetailResponseDTO:
        """Build detailed profile response DTO."""
        profile_response = self._build_profile_response(profile)
        
        # Get permissions
        permissions = self.profile_folder_permission_repository.get_active_by_profile(profile.id)
        permission_responses = []
        for perm in permissions:
            # This would need proper conversion - simplified for now
            permission_responses.append({
                "id": perm.id,
                "folder_path": perm.folder_path,
                "permission_level": perm.permission_level.value,
            })

        # Get user assignments
        assignments = self.user_profile_repository.get_active_by_profile(profile.id)
        user_responses = []
        for assignment in assignments:
            user = self.user_repository.get_by_id(assignment.user_id)
            user_responses.append({
                "id": assignment.id,
                "user_id": assignment.user_id,
                "user_name": user.name if user else "Unknown",
                "assigned_at": assignment.assigned_at,
            })

        # Validation
        is_valid, validation_errors = profile.validate_profile()

        return ProfileDetailResponseDTO(
            **profile_response.model_dump(),
            permissions=permission_responses,
            users=user_responses,
            creation_age_days=profile.get_creation_age_days(),
            last_update_age_days=profile.get_last_update_age_days(),
            is_recently_created=profile.is_recently_created(),
            is_recently_updated=profile.is_recently_updated(),
            can_be_deleted=profile.can_be_deleted()[0],
            can_be_modified=profile.can_be_modified()[0],
            validation_errors=validation_errors if not is_valid else [],
        )

    def _calculate_profile_usage_score(self, profile: Profile, active_assignments: list, permissions: list) -> float:
        """Calculate usage score for a profile (0-100)."""
        score = 0.0
        
        # Base score for being active
        if profile.is_active:
            score += 20
        
        # Score for having users
        if active_assignments:
            score += min(30, len(active_assignments) * 5)  # Up to 30 points
        
        # Score for having permissions
        if permissions:
            score += min(30, len(permissions) * 3)  # Up to 30 points
        
        # Score for recent activity
        if profile.is_recently_created() or profile.is_recently_updated():
            score += 10
        
        # Score for having profile_metadata (indicates thoughtful setup)
        if profile.profile_metadata:
            score += 10
        
        return min(100.0, score)