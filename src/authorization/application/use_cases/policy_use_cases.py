from datetime import datetime, timezone
from typing import List, Optional, Dict
from uuid import UUID

from ...domain.entities.policy import Policy
from ...domain.entities.authorization_context import AuthorizationContext
from ...domain.repositories.policy_repository import PolicyRepository
from ...domain.services.abac_service import AbacService
from ..dtos.policy_dto import (
    PolicyCreateDTO,
    PolicyUpdateDTO,
    PolicyResponseDTO,
    PolicyListResponseDTO,
    PolicyEvaluationRequestDTO,
    PolicyEvaluationResponseDTO,
)


class PolicyUseCase:
    """Use case for policy management operations."""

    def __init__(self, policy_repository: PolicyRepository, abac_service: AbacService):
        self.policy_repository = policy_repository
        self.abac_service = abac_service

    def create_policy(
        self, dto: PolicyCreateDTO, created_by: UUID
    ) -> PolicyResponseDTO:
        """Create a new policy."""
        # Create policy entity
        policy = Policy(
            name=dto.name,
            description=dto.description,
            effect=dto.effect,
            resource_type=dto.resource_type,
            action=dto.action,
            conditions=dto.conditions,
            organization_id=dto.organization_id,
            created_by=created_by,
            priority=dto.priority,
            created_at=datetime.now(timezone.utc),
        )

        # Save policy
        saved_policy = self.policy_repository.save(policy)

        return self._build_policy_response(saved_policy)

    def get_policy_by_id(self, policy_id: UUID) -> Optional[PolicyResponseDTO]:
        """Get policy by ID."""
        policy = self.policy_repository.find_by_id(policy_id)
        if not policy:
            return None

        return self._build_policy_response(policy)

    def update_policy(
        self, policy_id: UUID, dto: PolicyUpdateDTO
    ) -> Optional[PolicyResponseDTO]:
        """Update an existing policy."""
        policy = self.policy_repository.find_by_id(policy_id)
        if not policy:
            return None

        # Update fields
        if dto.description is not None:
            policy.description = dto.description
        if dto.effect is not None:
            policy.effect = dto.effect
        if dto.conditions is not None:
            policy.conditions = dto.conditions
        if dto.priority is not None:
            policy.priority = dto.priority

        policy.updated_at = datetime.now(timezone.utc)

        # Save policy
        updated_policy = self.policy_repository.save(policy)

        return self._build_policy_response(updated_policy)

    def delete_policy(self, policy_id: UUID) -> bool:
        """Delete a policy (soft delete)."""
        policy = self.policy_repository.find_by_id(policy_id)
        if not policy:
            return False

        policy.is_active = False
        policy.updated_at = datetime.now(timezone.utc)
        self.policy_repository.save(policy)

        return True

    def list_policies(
        self,
        organization_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PolicyListResponseDTO:
        """List policies with pagination and filters."""
        offset = (page - 1) * page_size

        policies, total = self.policy_repository.find_paginated(
            organization_id=organization_id,
            resource_type=resource_type,
            action=action,
            offset=offset,
            limit=page_size,
        )

        policy_responses = [self._build_policy_response(policy) for policy in policies]

        total_pages = (total + page_size - 1) // page_size

        return PolicyListResponseDTO(
            policies=policy_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_policies_by_resource_and_action(
        self, resource_type: str, action: str, organization_id: Optional[UUID] = None
    ) -> List[PolicyResponseDTO]:
        """Get policies for specific resource type and action."""
        policies = self.policy_repository.find_by_resource_and_action(
            resource_type, action, organization_id
        )

        return [self._build_policy_response(policy) for policy in policies]

    def evaluate_policies(
        self, request_dto: PolicyEvaluationRequestDTO
    ) -> List[PolicyEvaluationResponseDTO]:
        """Evaluate policies for a specific request."""
        # Get applicable policies
        policies = self.policy_repository.find_by_resource_and_action(
            request_dto.resource_type, request_dto.action, request_dto.organization_id
        )

        # Create authorization context
        context = AuthorizationContext(
            user_id=request_dto.user_id,
            organization_id=request_dto.organization_id,
            resource_id=request_dto.resource_id,
            resource_type=request_dto.resource_type,
            action=request_dto.action,
            user_attributes=request_dto.user_attributes,
            resource_attributes=request_dto.resource_attributes,
            environment_attributes=request_dto.environment_attributes,
        )

        # Evaluate each policy
        evaluation_results = []

        for policy in policies:
            start_time = datetime.now(timezone.utc)

            # Evaluate policy conditions
            (
                conditions_met,
                condition_results,
            ) = self.abac_service.evaluate_policy_conditions(policy, context)

            # Determine result based on conditions
            result = None
            if conditions_met:
                result = policy.effect == "allow"

            end_time = datetime.now(timezone.utc)
            evaluation_time_ms = (end_time - start_time).total_seconds() * 1000

            evaluation_results.append(
                PolicyEvaluationResponseDTO(
                    policy_id=policy.id,
                    policy_name=policy.name,
                    result=result,
                    conditions_met=conditions_met,
                    condition_results=condition_results,
                    evaluation_time_ms=evaluation_time_ms,
                )
            )

        return evaluation_results

    def get_organization_policies(
        self, organization_id: UUID
    ) -> List[PolicyResponseDTO]:
        """Get all policies for an organization."""
        policies = self.policy_repository.find_by_organization(organization_id)
        return [self._build_policy_response(policy) for policy in policies]

    def get_global_policies(self) -> List[PolicyResponseDTO]:
        """Get all global policies."""
        policies = self.policy_repository.find_global_policies()
        return [self._build_policy_response(policy) for policy in policies]

    def duplicate_policy(
        self,
        policy_id: UUID,
        new_name: str,
        created_by: UUID,
        organization_id: Optional[UUID] = None,
    ) -> Optional[PolicyResponseDTO]:
        """Duplicate an existing policy with a new name."""
        original_policy = self.policy_repository.find_by_id(policy_id)
        if not original_policy:
            return None

        # Create new policy with same configuration but different name
        new_policy = Policy(
            name=new_name,
            description=f"Copy of {original_policy.description}",
            effect=original_policy.effect,
            resource_type=original_policy.resource_type,
            action=original_policy.action,
            conditions=original_policy.conditions.copy(),
            organization_id=organization_id or original_policy.organization_id,
            created_by=created_by,
            priority=original_policy.priority,
            created_at=datetime.now(timezone.utc),
        )

        saved_policy = self.policy_repository.save(new_policy)
        return self._build_policy_response(saved_policy)

    def bulk_update_priority(
        self, policy_priorities: Dict[UUID, int]
    ) -> List[PolicyResponseDTO]:
        """Update priorities for multiple policies."""
        updated_policies = []

        for policy_id, new_priority in policy_priorities.items():
            policy = self.policy_repository.find_by_id(policy_id)
            if policy:
                policy.priority = new_priority
                policy.updated_at = datetime.now(timezone.utc)
                updated_policy = self.policy_repository.save(policy)
                updated_policies.append(updated_policy)

        return [self._build_policy_response(policy) for policy in updated_policies]

    def _build_policy_response(self, policy: Policy) -> PolicyResponseDTO:
        """Build policy response DTO."""
        return PolicyResponseDTO(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            effect=policy.effect,
            resource_type=policy.resource_type,
            action=policy.action,
            conditions=[condition.model_dump() for condition in policy.conditions],
            organization_id=policy.organization_id,
            created_by=policy.created_by,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
            is_active=policy.is_active,
            priority=policy.priority,
        )
