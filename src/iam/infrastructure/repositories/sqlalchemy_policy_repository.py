from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, and_
from sqlalchemy.exc import IntegrityError

from ...domain.entities.policy import Policy, PolicyCondition
from ...domain.repositories.policy_repository import PolicyRepository
from ...infrastructure.database.models import (
    PolicyModel,
    PolicyEffectEnum,
)


class SqlAlchemyPolicyRepository(PolicyRepository):
    """SQLAlchemy implementation of PolicyRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, policy: Policy) -> Policy:
        """Save a policy entity."""
        try:
            # Check if policy exists
            existing = self.session.get(PolicyModel, policy.id)

            if existing:
                # Update existing policy
                existing.name = policy.name
                existing.description = policy.description
                existing.effect = PolicyEffectEnum(policy.effect)
                existing.resource_type = policy.resource_type
                existing.action = policy.action
                existing.conditions = [
                    condition.to_dict() for condition in policy.conditions
                ]
                existing.organization_id = policy.organization_id
                existing.created_by = policy.created_by
                existing.priority = policy.priority
                existing.is_active = policy.is_active
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new policy
                policy_model = PolicyModel(
                    id=policy.id,
                    name=policy.name,
                    description=policy.description,
                    effect=PolicyEffectEnum(policy.effect),
                    resource_type=policy.resource_type,
                    action=policy.action,
                    conditions=[
                        condition.model_dump() for condition in policy.conditions
                    ],
                    organization_id=policy.organization_id,
                    created_by=policy.created_by,
                    priority=policy.priority,
                    is_active=policy.is_active,
                    created_at=policy.created_at,
                    updated_at=policy.updated_at,
                )

                self.session.add(policy_model)
                self.session.flush()
                return self._to_domain_entity(policy_model)

        except IntegrityError as e:
            self.session.rollback()
            raise e

    def find_by_id(self, policy_id: UUID) -> Optional[Policy]:
        """Find a policy by ID."""
        result = self.session.execute(
            select(PolicyModel).where(PolicyModel.id == policy_id)
        )
        policy_model = result.scalar_one_or_none()

        if policy_model:
            return self._to_domain_entity(policy_model)
        return None

    def find_by_name(
        self, name: str, organization_id: Optional[UUID] = None
    ) -> Optional[Policy]:
        """Find a policy by name within organization scope."""
        result = self.session.execute(
            select(PolicyModel).where(
                and_(
                    PolicyModel.name == name,
                    PolicyModel.organization_id == organization_id,
                )
            )
        )
        policy_model = result.scalar_one_or_none()

        if policy_model:
            return self._to_domain_entity(policy_model)
        return None

    def find_by_resource_and_action(
        self, resource_type: str, action: str, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Find policies for specific resource type and action."""
        query_conditions = [
            PolicyModel.resource_type == resource_type,
            PolicyModel.action == action,
            PolicyModel.is_active,
        ]

        # Include both organization-specific and global policies
        if organization_id:
            org_condition = (PolicyModel.organization_id == organization_id) | (
                PolicyModel.organization_id.is_(None)
            )
            query_conditions.append(org_condition)
        else:
            query_conditions.append(PolicyModel.organization_id.is_(None))

        result = self.session.execute(
            select(PolicyModel)
            .where(and_(*query_conditions))
            .order_by(PolicyModel.priority.desc())
        )
        policy_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in policy_models]

    def find_by_resource_type(
        self, resource_type: str, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Find policies for a specific resource type."""
        query_conditions = [
            PolicyModel.resource_type == resource_type,
            PolicyModel.is_active,
        ]

        if organization_id:
            org_condition = (PolicyModel.organization_id == organization_id) | (
                PolicyModel.organization_id.is_(None)
            )
            query_conditions.append(org_condition)
        else:
            query_conditions.append(PolicyModel.organization_id.is_(None))

        result = self.session.execute(
            select(PolicyModel)
            .where(and_(*query_conditions))
            .order_by(PolicyModel.priority.desc())
        )
        policy_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in policy_models]

    def find_by_organization(self, organization_id: UUID) -> List[Policy]:
        """Find policies for an organization."""
        result = self.session.execute(
            select(PolicyModel)
            .where(
                and_(
                    PolicyModel.organization_id == organization_id,
                    PolicyModel.is_active,
                )
            )
            .order_by(PolicyModel.priority.desc())
        )
        policy_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in policy_models]

    def find_global_policies(self) -> List[Policy]:
        """Find all global policies."""
        result = self.session.execute(
            select(PolicyModel)
            .where(and_(PolicyModel.organization_id.is_(None), PolicyModel.is_active))
            .order_by(PolicyModel.priority.desc())
        )
        policy_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in policy_models]

    def find_by_effect(
        self, effect: str, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Find policies by effect (allow/deny)."""
        query_conditions = [
            PolicyModel.effect == PolicyEffectEnum(effect),
            PolicyModel.is_active,
        ]

        if organization_id:
            org_condition = (PolicyModel.organization_id == organization_id) | (
                PolicyModel.organization_id.is_(None)
            )
            query_conditions.append(org_condition)

        result = self.session.execute(
            select(PolicyModel)
            .where(and_(*query_conditions))
            .order_by(PolicyModel.priority.desc())
        )
        policy_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in policy_models]

    def find_paginated(
        self,
        organization_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        effect: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Policy], int]:
        """Find policies with pagination and filters."""
        query = select(PolicyModel)
        count_query = select(PolicyModel)

        # Apply filters
        if organization_id is not None:
            org_condition = (PolicyModel.organization_id == organization_id) | (
                PolicyModel.organization_id.is_(None)
            )
            query = query.where(org_condition)
            count_query = count_query.where(org_condition)

        if resource_type:
            query = query.where(PolicyModel.resource_type == resource_type)
            count_query = count_query.where(PolicyModel.resource_type == resource_type)

        if action:
            query = query.where(PolicyModel.action == action)
            count_query = count_query.where(PolicyModel.action == action)

        if effect:
            query = query.where(PolicyModel.effect == PolicyEffectEnum(effect))
            count_query = count_query.where(
                PolicyModel.effect == PolicyEffectEnum(effect)
            )

        if is_active is not None:
            query = query.where(PolicyModel.is_active == is_active)
            count_query = count_query.where(PolicyModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(PolicyModel.priority.desc(), PolicyModel.created_at.desc())
        )
        result = self.session.execute(query)
        policy_models = result.scalars().all()

        policies = [self._to_domain_entity(model) for model in policy_models]
        return policies, total

    def delete(self, policy_id: UUID) -> bool:
        """Delete a policy (hard delete)."""
        result = self.session.execute(
            delete(PolicyModel).where(PolicyModel.id == policy_id)
        )
        return result.rowcount > 0

    def search(
        self,
        query: Optional[str] = None,
        organization_id: Optional[UUID] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Policy], int]:
        """Search policies with text query."""
        db_query = select(PolicyModel)
        count_query = select(PolicyModel)

        # Apply text search
        if query:
            search_filter = (
                PolicyModel.name.ilike(f"%{query}%")
                | PolicyModel.description.ilike(f"%{query}%")
                | PolicyModel.resource_type.ilike(f"%{query}%")
                | PolicyModel.action.ilike(f"%{query}%")
            )
            db_query = db_query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply organization filter
        if organization_id is not None:
            org_condition = (PolicyModel.organization_id == organization_id) | (
                PolicyModel.organization_id.is_(None)
            )
            db_query = db_query.where(org_condition)
            count_query = count_query.where(org_condition)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        db_query = (
            db_query.offset(offset)
            .limit(limit)
            .order_by(PolicyModel.priority.desc(), PolicyModel.created_at.desc())
        )
        result = self.session.execute(db_query)
        policy_models = result.scalars().all()

        policies = [self._to_domain_entity(model) for model in policy_models]
        return policies, total

    def get_resource_types(self) -> List[str]:
        """Get all unique resource types."""
        result = self.session.execute(select(PolicyModel.resource_type).distinct())
        return [row[0] for row in result.fetchall()]

    def get_actions(self) -> List[str]:
        """Get all unique actions."""
        result = self.session.execute(select(PolicyModel.action).distinct())
        return [row[0] for row in result.fetchall()]

    def count_policies_by_organization(self, organization_id: UUID) -> int:
        """Count policies for an organization."""
        result = self.session.execute(
            select(PolicyModel).where(
                and_(
                    PolicyModel.organization_id == organization_id,
                    PolicyModel.is_active,
                )
            )
        )
        return len(result.scalars().all())

    def _to_domain_entity(self, policy_model: PolicyModel) -> Policy:
        """Convert SQLAlchemy model to domain entity."""
        conditions = [
            PolicyCondition.from_dict(condition_dict)
            for condition_dict in policy_model.conditions
        ]

        return Policy(
            id=policy_model.id,
            name=policy_model.name,
            description=policy_model.description,
            effect=policy_model.effect.value,
            resource_type=policy_model.resource_type,
            action=policy_model.action,
            conditions=conditions,
            organization_id=policy_model.organization_id,
            created_by=policy_model.created_by,
            priority=policy_model.priority,
            is_active=policy_model.is_active,
            created_at=policy_model.created_at,
            updated_at=policy_model.updated_at,
        )
