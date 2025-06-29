from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from shared.domain.repositories.unit_of_work import UnitOfWork
from ...domain.entities.subscription import Subscription
from ...domain.repositories.subscription_repository import SubscriptionRepository
from ...domain.repositories.plan_repository import PlanRepository
from ...domain.services.subscription_service import SubscriptionService
from ..dtos.subscription_dto import (
    SubscriptionCreateDTO,
    SubscriptionUpdateDTO,
    SubscriptionResponseDTO,
    SubscriptionListResponseDTO,
    SubscriptionUpgradeDTO,
    SubscriptionDowngradeDTO,
    SubscriptionCancellationDTO,
)


class SubscriptionUseCase:
    """Use case for subscription management operations."""

    def __init__(self, uow: UnitOfWork):
        self._subscription_repository: SubscriptionRepository = uow.get_repository("subscription")
        self._plan_repository: PlanRepository = uow.get_repository("plan")
        self._subscription_service = SubscriptionService(uow)
        self._uow = uow

    def create_subscription(
        self, dto: SubscriptionCreateDTO
    ) -> SubscriptionResponseDTO:
        """Create a new subscription."""
        with self._uow:
            # Validate plan exists
            plan = self._plan_repository.find_by_id(dto.plan_id)
            if not plan:
                raise ValueError("Plan not found")

            if not plan.is_active:
                raise ValueError("Plan is not active")

            # Check if organization already has an active subscription
            existing_subscription = (
                self._subscription_repository.find_active_by_organization(
                    dto.organization_id
                )
            )
            if existing_subscription:
                raise ValueError("Organization already has an active subscription")

            # Create subscription
            subscription = self._subscription_service.create_subscription(
                organization_id=dto.organization_id,
                plan_id=dto.plan_id,
                billing_cycle=dto.billing_cycle,
                starts_at=dto.starts_at or datetime.now(timezone.utc),
                metadata=dto.metadata,
            )

        return self._build_subscription_response(subscription)

    def get_subscription_by_id(
        self, subscription_id: UUID
    ) -> Optional[SubscriptionResponseDTO]:
        """Get subscription by ID."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        return self._build_subscription_response(subscription)

    def update_subscription(
        self, subscription_id: UUID, dto: SubscriptionUpdateDTO
    ) -> Optional[SubscriptionResponseDTO]:
        """Update an existing subscription."""
        with self._uow:
            subscription = self._subscription_repository.find_by_id(subscription_id)
            if not subscription:
                return None

            # Update fields
            if dto.billing_cycle is not None:
                subscription.billing_cycle = dto.billing_cycle
            if dto.ends_at is not None:
                subscription.ends_at = dto.ends_at
            if dto.metadata is not None:
                subscription.metadata.update(dto.metadata)

            subscription.updated_at = datetime.now(timezone.utc)

            # Recalculate next billing date if billing cycle changed
            if dto.billing_cycle is not None:
                subscription.next_billing_date = (
                    self._subscription_service.calculate_next_billing_date(
                        subscription.starts_at, subscription.billing_cycle
                    )
                )

            updated_subscription = self._subscription_repository.save(subscription)

        return self._build_subscription_response(updated_subscription)

    def cancel_subscription(
        self, subscription_id: UUID, dto: SubscriptionCancellationDTO
    ) -> Optional[SubscriptionResponseDTO]:
        """Cancel a subscription."""
        with self._uow:
            subscription = self._subscription_repository.find_by_id(subscription_id)
            if not subscription:
                return None

            if subscription.status == "cancelled":
                raise ValueError("Subscription is already cancelled")

            # Cancel subscription
            cancelled_subscription = self._subscription_service.cancel_subscription(
                subscription_id=subscription_id,
                cancel_immediately=dto.cancel_immediately,
                cancellation_reason=dto.cancellation_reason,
            )

            # Store feedback if provided
            if dto.feedback:
                cancelled_subscription.metadata["cancellation_feedback"] = dto.feedback
                self._subscription_repository.save(cancelled_subscription)

        return self._build_subscription_response(cancelled_subscription)

    def upgrade_subscription(
        self, subscription_id: UUID, dto: SubscriptionUpgradeDTO
    ) -> Optional[SubscriptionResponseDTO]:
        """Upgrade a subscription to a higher plan."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        # Validate new plan
        new_plan = self.plan_repository.find_by_id(dto.new_plan_id)
        if not new_plan:
            raise ValueError("New plan not found")

        # Perform upgrade
        upgraded_subscription = self._subscription_service.upgrade_subscription(
            subscription_id=subscription_id,
            new_plan_id=dto.new_plan_id,
            billing_cycle=dto.billing_cycle or subscription.billing_cycle,
            upgrade_immediately=dto.upgrade_immediately,
            prorate=dto.prorate,
        )

        return self._build_subscription_response(upgraded_subscription)

    def downgrade_subscription(
        self, subscription_id: UUID, dto: SubscriptionDowngradeDTO
    ) -> Optional[SubscriptionResponseDTO]:
        """Downgrade a subscription to a lower plan."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        # Validate new plan
        new_plan = self.plan_repository.find_by_id(dto.new_plan_id)
        if not new_plan:
            raise ValueError("New plan not found")

        # Perform downgrade
        downgraded_subscription = self._subscription_service.downgrade_subscription(
            subscription_id=subscription_id,
            new_plan_id=dto.new_plan_id,
            billing_cycle=dto.billing_cycle or subscription.billing_cycle,
            downgrade_at_period_end=dto.downgrade_at_period_end,
        )

        return self._build_subscription_response(downgraded_subscription)

    def list_subscriptions(
        self,
        organization_id: Optional[UUID] = None,
        status: Optional[str] = None,
        plan_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> SubscriptionListResponseDTO:
        """List subscriptions with pagination and filters."""
        offset = (page - 1) * page_size

        subscriptions, total = self._subscription_repository.find_paginated(
            organization_id=organization_id,
            status=status,
            plan_id=plan_id,
            offset=offset,
            limit=page_size,
        )

        subscription_responses = []
        for subscription in subscriptions:
            subscription_responses.append(
                self._build_subscription_response(subscription)
            )

        total_pages = (total + page_size - 1) // page_size

        return SubscriptionListResponseDTO(
            subscriptions=subscription_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_organization_subscription(
        self, organization_id: UUID
    ) -> Optional[SubscriptionResponseDTO]:
        """Get the active subscription for an organization."""
        subscription = self._subscription_repository.find_active_by_organization(
            organization_id
        )
        if not subscription:
            return None

        return self._build_subscription_response(subscription)

    def get_expiring_subscriptions(
        self, days_ahead: int = 7
    ) -> List[SubscriptionResponseDTO]:
        """Get subscriptions expiring within specified days."""
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)

        subscriptions = self._subscription_repository.find_expiring_before(cutoff_date)

        subscription_responses = []
        for subscription in subscriptions:
            subscription_responses.append(
                self._build_subscription_response(subscription)
            )

        return subscription_responses

    def renew_subscription(
        self, subscription_id: UUID
    ) -> Optional[SubscriptionResponseDTO]:
        """Renew a subscription."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        # Renew subscription
        renewed_subscription = self._subscription_service.renew_subscription(
            subscription_id
        )

        return self._build_subscription_response(renewed_subscription)

    def pause_subscription(
        self, subscription_id: UUID
    ) -> Optional[SubscriptionResponseDTO]:
        """Pause a subscription."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        if subscription.status != "active":
            raise ValueError("Can only pause active subscriptions")

        subscription.status = "paused"
        subscription.metadata["paused_at"] = datetime.now(timezone.utc).isoformat()
        subscription.updated_at = datetime.now(timezone.utc)

        updated_subscription = self._subscription_repository.save(subscription)
        return self._build_subscription_response(updated_subscription)

    def resume_subscription(
        self, subscription_id: UUID
    ) -> Optional[SubscriptionResponseDTO]:
        """Resume a paused subscription."""
        subscription = self._subscription_repository.find_by_id(subscription_id)
        if not subscription:
            return None

        if subscription.status != "paused":
            raise ValueError("Can only resume paused subscriptions")

        subscription.status = "active"
        subscription.metadata["resumed_at"] = datetime.now(timezone.utc).isoformat()
        subscription.updated_at = datetime.now(timezone.utc)

        updated_subscription = self._subscription_repository.save(subscription)
        return self._build_subscription_response(updated_subscription)

    def _build_subscription_response(
        self, subscription: Subscription
    ) -> SubscriptionResponseDTO:
        """Build subscription response DTO."""
        # Get plan details
        plan = self._plan_repository.find_by_id(subscription.plan_id)
        plan_name = plan.name if plan else "Unknown Plan"
        plan_type = plan.plan_type if plan else "Unknown"

        return SubscriptionResponseDTO(
            id=subscription.id,
            organization_id=subscription.organization_id,
            plan_id=subscription.plan_id,
            plan_name=plan_name,
            plan_type=plan_type,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            starts_at=subscription.starts_at,
            ends_at=subscription.ends_at,
            next_billing_date=subscription.next_billing_date,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            metadata=subscription.metadata,
            is_trial=subscription.metadata.get("is_trial", False),
        )
