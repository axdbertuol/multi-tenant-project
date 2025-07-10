from typing import List, Optional, Dict
from uuid import UUID
from datetime import datetime, timezone

from ...domain.entities.user_profile import UserProfile
from ...domain.repositories.user_profile_repository import UserProfileRepository
from ...domain.repositories.profile_repository import ProfileRepository
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.organization_repository import OrganizationRepository
from ...domain.repositories.profile_folder_permission_repository import ProfileFolderPermissionRepository
from ..dtos.user_profile_dto import (
    UserProfileCreateDTO,
    UserProfileUpdateDTO,
    UserProfileExtendDTO,
    UserProfileRevokeDTO,
    UserProfileResponseDTO,
    UserProfileDetailResponseDTO,
    UserProfileListResponseDTO,
    UserProfileStatsDTO,
    UserProfileFilterDTO,
    UserProfileBulkActionDTO,
    UserProfileBulkActionResponseDTO,
    UserProfileBatchCreateDTO,
    UserProfileBatchCreateResponseDTO,
    UserProfileTransferDTO,
    UserProfileTransferResponseDTO,
    UserProfileHistoryDTO,
    UserProfileHistoryResponseDTO,
    UserContextDTO,
)


class UserProfileUseCase:
    """Use case for user profile assignment operations."""

    def __init__(
        self,
        user_profile_repository: UserProfileRepository,
        profile_repository: ProfileRepository,
        user_repository: UserRepository,
        organization_repository: OrganizationRepository,
        profile_folder_permission_repository: ProfileFolderPermissionRepository,
    ):
        self.user_profile_repository = user_profile_repository
        self.profile_repository = profile_repository
        self.user_repository = user_repository
        self.organization_repository = organization_repository
        self.profile_folder_permission_repository = profile_folder_permission_repository

    def create_assignment(self, dto: UserProfileCreateDTO) -> UserProfileResponseDTO:
        """Create a new user profile assignment."""
        # Validate user exists
        user = self.user_repository.get_by_id(dto.user_id)
        if not user:
            raise ValueError("User not found")

        # Validate profile exists
        profile = self.profile_repository.get_by_id(dto.profile_id)
        if not profile:
            raise ValueError("Profile not found")

        # Validate organization exists
        organization = self.organization_repository.get_by_id(dto.organization_id)
        if not organization:
            raise ValueError("Organization not found")

        # Validate all belong to same organization
        if profile.organization_id != dto.organization_id:
            raise ValueError("Profile must belong to the same organization")

        # Check if user already has this profile assigned
        existing_assignment = self.user_profile_repository.get_by_user_and_profile(
            dto.user_id, dto.profile_id
        )
        if existing_assignment and existing_assignment.is_active:
            raise ValueError("User already has this profile assigned")

        # Validate profile is active
        if not profile.is_active:
            raise ValueError("Cannot assign inactive profile")

        # Create assignment entity
        assignment = UserProfile.create(
            user_id=dto.user_id,
            profile_id=dto.profile_id,
            organization_id=dto.organization_id,
            assigned_by=dto.assigned_by,
            expires_at=dto.expires_at,
            notes=dto.notes,
            extra_data=dto.extra_data,
        )

        # Validate assignment
        is_valid, errors = assignment.validate_assignment()
        if not is_valid:
            raise ValueError(f"Assignment validation failed: {', '.join(errors)}")

        # Save assignment
        saved_assignment = self.user_profile_repository.save(assignment)

        return self._build_assignment_response(saved_assignment)

    def get_assignment_by_id(self, assignment_id: UUID) -> Optional[UserProfileDetailResponseDTO]:
        """Get assignment by ID with full details."""
        assignment = self.user_profile_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        return self._build_assignment_detail_response(assignment)

    def update_assignment(self, assignment_id: UUID, dto: UserProfileUpdateDTO) -> Optional[UserProfileResponseDTO]:
        """Update an existing user profile assignment."""
        assignment = self.user_profile_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        # Check if assignment can be modified
        can_modify, reason = assignment.can_be_modified()
        if not can_modify:
            raise ValueError(f"Assignment cannot be modified: {reason}")

        # Update fields
        updated_assignment = assignment

        if dto.profile_id is not None:
            # Validate new profile exists and is active
            new_profile = self.profile_repository.get_by_id(dto.profile_id)
            if not new_profile:
                raise ValueError("New profile not found")
            if not new_profile.is_active:
                raise ValueError("Cannot assign inactive profile")
            if new_profile.organization_id != assignment.organization_id:
                raise ValueError("New profile must belong to the same organization")

            # Check if user already has this profile assigned (different assignment)
            existing_assignment = self.user_profile_repository.get_by_user_and_profile(
                assignment.user_id, dto.profile_id
            )
            if existing_assignment and existing_assignment.id != assignment_id and existing_assignment.is_active:
                raise ValueError("User already has this profile assigned")

            updated_assignment = updated_assignment.change_profile(dto.profile_id, assignment.assigned_by)

        if dto.expires_at is not None:
            updated_assignment = updated_assignment.extend_expiration(dto.expires_at)

        if dto.notes is not None:
            updated_assignment = updated_assignment.update_notes(dto.notes)

        if dto.extra_data is not None:
            updated_assignment = updated_assignment.update_extra_data(dto.extra_data)

        if dto.is_active is not None:
            if dto.is_active:
                updated_assignment = updated_assignment.activate()
            else:
                updated_assignment = updated_assignment.deactivate()

        # Validate updated assignment
        is_valid, errors = updated_assignment.validate_assignment()
        if not is_valid:
            raise ValueError(f"Assignment validation failed: {', '.join(errors)}")

        # Save updated assignment
        saved_assignment = self.user_profile_repository.save(updated_assignment)

        return self._build_assignment_response(saved_assignment)

    def extend_assignment(self, assignment_id: UUID, dto: UserProfileExtendDTO) -> Optional[UserProfileResponseDTO]:
        """Extend user profile assignment expiration."""
        assignment = self.user_profile_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        can_modify, reason = assignment.can_be_modified()
        if not can_modify:
            raise ValueError(f"Assignment cannot be extended: {reason}")

        # Extend expiration
        if dto.new_expires_at is not None:
            extended_assignment = assignment.extend_expiration(dto.new_expires_at)
        else:
            extended_assignment = assignment.remove_expiration()

        # Add note about extension
        if dto.reason:
            notes = extended_assignment.notes or ""
            extension_note = f"Extended by {dto.extended_by}: {dto.reason}"
            new_notes = f"{notes}\n{extension_note}" if notes else extension_note
            extended_assignment = extended_assignment.update_notes(new_notes)

        # Save extended assignment
        saved_assignment = self.user_profile_repository.save(extended_assignment)

        return self._build_assignment_response(saved_assignment)

    def revoke_assignment(self, assignment_id: UUID, dto: UserProfileRevokeDTO) -> Optional[UserProfileResponseDTO]:
        """Revoke user profile assignment."""
        assignment = self.user_profile_repository.get_by_id(assignment_id)
        if not assignment:
            return None

        if not assignment.is_active:
            raise ValueError("Assignment is already inactive")

        # Revoke assignment
        revoked_assignment = assignment.revoke(dto.revoked_by, dto.reason)

        # Save revoked assignment
        saved_assignment = self.user_profile_repository.save(revoked_assignment)

        return self._build_assignment_response(saved_assignment)

    def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete a user profile assignment."""
        assignment = self.user_profile_repository.get_by_id(assignment_id)
        if not assignment:
            return False

        can_delete, reason = assignment.can_be_deleted()
        if not can_delete:
            raise ValueError(f"Assignment cannot be deleted: {reason}")

        return self.user_profile_repository.delete(assignment_id)

    def list_assignments(
        self,
        filters: Optional[UserProfileFilterDTO] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserProfileListResponseDTO:
        """List user profile assignments with filtering and pagination."""
        assignments = []

        # Apply filters
        if filters:
            if filters.user_id and filters.organization_id:
                assignments = self.user_profile_repository.get_by_user_and_organization(
                    filters.user_id, filters.organization_id
                )
            elif filters.user_id:
                assignments = self.user_profile_repository.get_by_user(filters.user_id)
            elif filters.profile_id:
                assignments = self.user_profile_repository.get_by_profile(filters.profile_id)
            elif filters.organization_id:
                assignments = self.user_profile_repository.get_by_organization(filters.organization_id)
            elif filters.assigned_by:
                assignments = self.user_profile_repository.get_by_assigned_by(
                    filters.assigned_by, filters.organization_id
                )
        else:
            assignments = []

        # Apply additional filters
        if filters and assignments:
            if filters.is_active is not None:
                assignments = [a for a in assignments if a.is_active == filters.is_active]
            if filters.is_expired is not None:
                assignments = [a for a in assignments if a.is_expired() == filters.is_expired]
            if filters.is_revoked is not None:
                assignments = [a for a in assignments if a.is_revoked() == filters.is_revoked]
            if filters.assignment_type:
                assignments = [a for a in assignments if a.get_assignment_type() == filters.assignment_type]
            if filters.status:
                assignments = [a for a in assignments if a.get_status() == filters.status]
            if filters.expiring_within_days is not None:
                assignments = [a for a in assignments if a.is_expiring_soon(filters.expiring_within_days)]

        # Apply pagination
        total = len(assignments)
        offset = (page - 1) * page_size
        paginated_assignments = assignments[offset:offset + page_size]

        assignment_responses = []
        for assignment in paginated_assignments:
            assignment_responses.append(self._build_assignment_response(assignment))

        total_pages = (total + page_size - 1) // page_size

        return UserProfileListResponseDTO(
            assignments=assignment_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_assignment_stats(self, organization_id: UUID) -> UserProfileStatsDTO:
        """Get user profile assignment statistics."""
        all_assignments = self.user_profile_repository.get_by_organization(organization_id)
        active_assignments = [a for a in all_assignments if a.is_active]
        inactive_assignments = [a for a in all_assignments if not a.is_active]
        expired_assignments = [a for a in all_assignments if a.is_expired()]
        expiring_soon_assignments = [a for a in all_assignments if a.is_expiring_soon()]
        revoked_assignments = [a for a in all_assignments if a.is_revoked()]
        temporary_assignments = [a for a in all_assignments if a.is_temporary_assignment()]
        permanent_assignments = [a for a in all_assignments if a.is_permanent_assignment()]

        # Count by profile
        assignments_by_profile = {}
        for assignment in all_assignments:
            profile = self.profile_repository.get_by_id(assignment.profile_id)
            profile_name = profile.name if profile else "Unknown"
            assignments_by_profile[profile_name] = assignments_by_profile.get(profile_name, 0) + 1

        # Count by user
        assignments_by_user = {}
        for assignment in all_assignments:
            user = self.user_repository.get_by_id(assignment.user_id)
            user_name = user.name if user else "Unknown"
            assignments_by_user[user_name] = assignments_by_user.get(user_name, 0) + 1

        # Count by assigner
        assignments_by_assigner = {}
        for assignment in all_assignments:
            assigner = self.user_repository.get_by_id(assignment.assigned_by)
            assigner_name = assigner.name if assigner else "Unknown"
            assignments_by_assigner[assigner_name] = assignments_by_assigner.get(assigner_name, 0) + 1

        # Recent assignments
        recent_assignments = sorted(all_assignments, key=lambda x: x.assigned_at, reverse=True)[:10]
        recent_assignment_responses = [self._build_assignment_response(a) for a in recent_assignments]

        # Expiring assignments
        expiring_assignment_responses = [self._build_assignment_response(a) for a in expiring_soon_assignments]

        return UserProfileStatsDTO(
            total_assignments=len(all_assignments),
            active_assignments=len(active_assignments),
            inactive_assignments=len(inactive_assignments),
            expired_assignments=len(expired_assignments),
            expiring_soon_assignments=len(expiring_soon_assignments),
            revoked_assignments=len(revoked_assignments),
            temporary_assignments=len(temporary_assignments),
            permanent_assignments=len(permanent_assignments),
            assignments_by_profile=assignments_by_profile,
            assignments_by_user=assignments_by_user,
            assignments_by_assigner=assignments_by_assigner,
            recent_assignments=recent_assignment_responses,
            expiring_assignments=expiring_assignment_responses,
        )

    def batch_create_assignments(self, dto: UserProfileBatchCreateDTO) -> UserProfileBatchCreateResponseDTO:
        """Create multiple user profile assignments."""
        created_count = 0
        skipped_count = 0
        error_count = 0
        created_assignments = []
        skipped_assignments = []
        errors = []

        for assignment_dto in dto.assignments:
            try:
                # Override organization and assigned_by if provided at batch level
                if dto.organization_id:
                    assignment_dto.organization_id = dto.organization_id
                if dto.assigned_by:
                    assignment_dto.assigned_by = dto.assigned_by
                if dto.default_expires_at and not assignment_dto.expires_at:
                    assignment_dto.expires_at = dto.default_expires_at

                # Check if assignment already exists
                if dto.skip_existing:
                    existing = self.user_profile_repository.get_by_user_and_profile(
                        assignment_dto.user_id, assignment_dto.profile_id
                    )
                    if existing and existing.is_active:
                        skipped_count += 1
                        skipped_assignments.append(f"User {assignment_dto.user_id} already has profile {assignment_dto.profile_id}")
                        continue

                # Create assignment
                assignment = self.create_assignment(assignment_dto)
                created_assignments.append(assignment)
                created_count += 1

            except ValueError as e:
                error_count += 1
                errors.append(f"Error creating assignment for user {assignment_dto.user_id}: {str(e)}")
            except Exception as e:
                error_count += 1
                errors.append(f"Unexpected error for user {assignment_dto.user_id}: {str(e)}")

        return UserProfileBatchCreateResponseDTO(
            created_count=created_count,
            skipped_count=skipped_count,
            error_count=error_count,
            created_assignments=created_assignments,
            skipped_assignments=skipped_assignments,
            errors=errors,
        )

    def transfer_assignments(self, dto: UserProfileTransferDTO) -> UserProfileTransferResponseDTO:
        """Transfer user assignments from one profile to another."""
        transferred_count = 0
        skipped_count = 0
        error_count = 0
        transferred_assignments = []
        skipped_users = []
        errors = []

        # Validate source and target profiles
        source_profile = self.profile_repository.get_by_id(dto.source_profile_id)
        if not source_profile:
            raise ValueError("Source profile not found")

        target_profile = self.profile_repository.get_by_id(dto.target_profile_id)
        if not target_profile:
            raise ValueError("Target profile not found")

        if not target_profile.is_active:
            raise ValueError("Target profile is not active")

        for user_id in dto.user_ids:
            try:
                # Get current assignment
                current_assignment = self.user_profile_repository.get_by_user_and_profile(
                    user_id, dto.source_profile_id
                )

                if not current_assignment or not current_assignment.is_active:
                    skipped_count += 1
                    skipped_users.append(f"User {user_id} has no active assignment to source profile")
                    continue

                # Check if user already has target profile
                existing_target = self.user_profile_repository.get_by_user_and_profile(
                    user_id, dto.target_profile_id
                )
                if existing_target and existing_target.is_active:
                    skipped_count += 1
                    skipped_users.append(f"User {user_id} already has target profile assigned")
                    continue

                # Deactivate current assignment
                deactivated_assignment = current_assignment.deactivate()
                self.user_profile_repository.save(deactivated_assignment)

                # Create new assignment
                new_assignment = UserProfile.create(
                    user_id=user_id,
                    profile_id=dto.target_profile_id,
                    organization_id=dto.organization_id,
                    assigned_by=dto.transferred_by,
                    expires_at=current_assignment.expires_at if dto.preserve_expiration else None,
                    notes=f"Transferred from {source_profile.name}. {dto.transfer_reason or ''}",
                    extra_data=current_assignment.extra_data,
                )

                saved_assignment = self.user_profile_repository.save(new_assignment)
                transferred_assignments.append(self._build_assignment_response(saved_assignment))
                transferred_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"Error transferring user {user_id}: {str(e)}")

        return UserProfileTransferResponseDTO(
            transferred_count=transferred_count,
            skipped_count=skipped_count,
            error_count=error_count,
            transferred_assignments=transferred_assignments,
            skipped_users=skipped_users,
            errors=errors,
        )

    def get_assignment_history(self, dto: UserProfileHistoryDTO) -> UserProfileHistoryResponseDTO:
        """Get assignment history for a user and profile."""
        history = self.user_profile_repository.get_assignment_history(dto.user_id, dto.profile_id)
        
        # Apply filters
        if not dto.include_revoked:
            history = [h for h in history if not h.is_revoked()]
        if not dto.include_expired:
            history = [h for h in history if not h.is_expired()]
        if dto.date_from:
            history = [h for h in history if h.assigned_at >= dto.date_from]
        if dto.date_to:
            history = [h for h in history if h.assigned_at <= dto.date_to]

        # Sort by assignment date
        history = sorted(history, key=lambda x: x.assigned_at, reverse=True)

        # Build response
        history_responses = [self._build_assignment_response(h) for h in history]
        
        # Find current and last active assignments
        current_assignment = None
        last_active_assignment = None
        
        for assignment in history:
            if assignment.is_active:
                current_assignment = self._build_assignment_response(assignment)
                break
        
        for assignment in history:
            if assignment.is_active or assignment.is_revoked():
                last_active_assignment = self._build_assignment_response(assignment)
                break

        # Build timeline
        timeline = []
        for assignment in history:
            timeline.append({
                "date": assignment.assigned_at.isoformat(),
                "action": "assigned",
                "status": assignment.get_status(),
                "assigned_by": assignment.assigned_by,
                "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
            })
            
            if assignment.is_revoked():
                timeline.append({
                    "date": assignment.revoked_at.isoformat(),
                    "action": "revoked",
                    "status": "revoked",
                    "revoked_by": assignment.revoked_by,
                })

        return UserProfileHistoryResponseDTO(
            user_id=dto.user_id,
            profile_id=dto.profile_id,
            history=history_responses,
            total_assignments=len(history),
            current_assignment=current_assignment,
            last_active_assignment=last_active_assignment,
            assignment_timeline=timeline,
        )

    def get_user_context(self, user_id: UUID, organization_id: UUID) -> UserContextDTO:
        """Get user context with all profile information."""
        # Get active assignments
        active_assignments = self.user_profile_repository.get_active_by_user_and_organization(
            user_id, organization_id
        )

        assignment_responses = []
        effective_permissions = set()
        accessible_folders = set()
        folder_permissions = {}

        for assignment in active_assignments:
            assignment_responses.append(self._build_assignment_response(assignment))

            # Get profile permissions
            profile_permissions = self.profile_folder_permission_repository.get_active_by_profile(
                assignment.profile_id
            )

            for perm in profile_permissions:
                # Add to effective permissions
                effective_permissions.update(perm.get_allowed_actions())
                
                # Add to accessible folders
                accessible_folders.add(perm.folder_path)
                
                # Track highest permission level for each folder
                current_level = folder_permissions.get(perm.folder_path)
                if not current_level or perm.permission_level.is_higher_than(current_level):
                    folder_permissions[perm.folder_path] = perm.permission_level.value

        # Validate context
        validation_errors = []
        for assignment in active_assignments:
            if assignment.is_expired():
                validation_errors.append(f"Assignment {assignment.id} is expired")
            
            profile = self.profile_repository.get_by_id(assignment.profile_id)
            if not profile or not profile.is_active:
                validation_errors.append(f"Profile {assignment.profile_id} is inactive")

        return UserContextDTO(
            user_id=user_id,
            organization_id=organization_id,
            active_profiles=assignment_responses,
            effective_permissions=list(effective_permissions),
            accessible_folders=list(accessible_folders),
            folder_permissions=folder_permissions,
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            last_updated=datetime.now(timezone.utc),
        )

    def bulk_action(self, dto: UserProfileBulkActionDTO) -> UserProfileBulkActionResponseDTO:
        """Perform bulk action on user profile assignments."""
        success_count = 0
        failure_count = 0
        errors = []
        affected_assignments = []
        warnings = []

        for assignment_id in dto.assignment_ids:
            try:
                assignment = self.user_profile_repository.get_by_id(assignment_id)
                if not assignment:
                    failure_count += 1
                    errors.append(f"Assignment {assignment_id} not found")
                    continue

                if dto.action == "activate":
                    if assignment.is_active:
                        warnings.append(f"Assignment {assignment_id} is already active")
                    else:
                        activated_assignment = assignment.activate()
                        self.user_profile_repository.save(activated_assignment)
                        success_count += 1
                        affected_assignments.append(assignment_id)

                elif dto.action == "deactivate":
                    if not assignment.is_active:
                        warnings.append(f"Assignment {assignment_id} is already inactive")
                    else:
                        deactivated_assignment = assignment.deactivate()
                        self.user_profile_repository.save(deactivated_assignment)
                        success_count += 1
                        affected_assignments.append(assignment_id)

                elif dto.action == "extend":
                    if not dto.new_expires_at:
                        failure_count += 1
                        errors.append(f"New expiration date required for extend action")
                        continue
                    
                    can_modify, reason = assignment.can_be_modified()
                    if not can_modify:
                        failure_count += 1
                        errors.append(f"Assignment {assignment_id} cannot be extended: {reason}")
                        continue

                    extended_assignment = assignment.extend_expiration(dto.new_expires_at)
                    self.user_profile_repository.save(extended_assignment)
                    success_count += 1
                    affected_assignments.append(assignment_id)

                elif dto.action == "revoke":
                    if not assignment.is_active:
                        warnings.append(f"Assignment {assignment_id} is already inactive")
                    else:
                        revoked_assignment = assignment.revoke(dto.performed_by, dto.reason)
                        self.user_profile_repository.save(revoked_assignment)
                        success_count += 1
                        affected_assignments.append(assignment_id)

                elif dto.action == "delete":
                    can_delete, reason = assignment.can_be_deleted()
                    if not can_delete:
                        failure_count += 1
                        errors.append(f"Assignment {assignment_id} cannot be deleted: {reason}")
                        continue

                    if self.user_profile_repository.delete(assignment_id):
                        success_count += 1
                        affected_assignments.append(assignment_id)
                    else:
                        failure_count += 1
                        errors.append(f"Failed to delete assignment {assignment_id}")

                else:
                    failure_count += 1
                    errors.append(f"Unknown action: {dto.action}")

            except Exception as e:
                failure_count += 1
                errors.append(f"Error processing assignment {assignment_id}: {str(e)}")

        return UserProfileBulkActionResponseDTO(
            success_count=success_count,
            failure_count=failure_count,
            errors=errors,
            affected_assignments=affected_assignments,
            warnings=warnings,
        )

    def _build_assignment_response(self, assignment: UserProfile) -> UserProfileResponseDTO:
        """Build assignment response DTO."""
        # Get related data
        user = self.user_repository.get_by_id(assignment.user_id)
        profile = self.profile_repository.get_by_id(assignment.profile_id)
        assigned_by_user = self.user_repository.get_by_id(assignment.assigned_by)
        organization = self.organization_repository.get_by_id(assignment.organization_id)

        return UserProfileResponseDTO(
            id=assignment.id,
            user_id=assignment.user_id,
            profile_id=assignment.profile_id,
            organization_id=assignment.organization_id,
            assigned_by=assignment.assigned_by,
            assigned_at=assignment.assigned_at,
            expires_at=assignment.expires_at,
            is_active=assignment.is_active,
            revoked_at=assignment.revoked_at,
            revoked_by=assignment.revoked_by,
            notes=assignment.notes,
            extra_data=assignment.extra_data,
            user_name=user.name if user else None,
            user_email=user.email if user else None,
            profile_name=profile.name if profile else None,
            profile_description=profile.description if profile else None,
            assigned_by_name=assigned_by_user.name if assigned_by_user else None,
            organization_name=organization.name if organization else None,
            status=assignment.get_status(),
            assignment_type=assignment.get_assignment_type(),
            days_until_expiry=assignment.days_until_expiry(),
            is_expired=assignment.is_expired(),
            is_expiring_soon=assignment.is_expiring_soon(),
            assignment_duration_days=assignment.get_assignment_duration(),
        )

    def _build_assignment_detail_response(self, assignment: UserProfile) -> UserProfileDetailResponseDTO:
        """Build detailed assignment response DTO."""
        assignment_response = self._build_assignment_response(assignment)

        # Get related entities
        user = self.user_repository.get_by_id(assignment.user_id)
        profile = self.profile_repository.get_by_id(assignment.profile_id)
        assigned_by_user = self.user_repository.get_by_id(assignment.assigned_by)
        revoked_by_user = self.user_repository.get_by_id(assignment.revoked_by) if assignment.revoked_by else None

        # Get effective permissions
        effective_permissions = []
        accessible_folders = []
        folder_permissions = []
        
        if profile:
            profile_permissions = self.profile_folder_permission_repository.get_active_by_profile(profile.id)
            for perm in profile_permissions:
                effective_permissions.extend(perm.get_allowed_actions())
                accessible_folders.append(perm.folder_path)
                folder_permissions.append({
                    "id": perm.id,
                    "folder_path": perm.folder_path,
                    "permission_level": perm.permission_level.value,
                })

        # Validation
        is_valid, validation_errors = assignment.validate_assignment()
        can_modify, modify_reason = assignment.can_be_modified()
        can_delete, delete_reason = assignment.can_be_deleted()

        return UserProfileDetailResponseDTO(
            **assignment_response.model_dump(),
            profile={
                "id": profile.id,
                "name": profile.name,
                "description": profile.description,
                "is_active": profile.is_active,
            } if profile else None,
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_active": user.is_active,
            } if user else None,
            assigned_by_user={
                "id": assigned_by_user.id,
                "name": assigned_by_user.name,
                "email": assigned_by_user.email,
                "is_active": assigned_by_user.is_active,
            } if assigned_by_user else None,
            revoked_by_user={
                "id": revoked_by_user.id,
                "name": revoked_by_user.name,
                "email": revoked_by_user.email,
                "is_active": revoked_by_user.is_active,
            } if revoked_by_user else None,
            effective_permissions=list(set(effective_permissions)),
            accessible_folders=accessible_folders,
            folder_permissions=folder_permissions,
            validation_errors=validation_errors if not is_valid else [],
            can_be_modified=can_modify,
            can_be_deleted=can_delete,
            modification_reason=modify_reason if not can_modify else None,
            deletion_reason=delete_reason if not can_delete else None,
        )