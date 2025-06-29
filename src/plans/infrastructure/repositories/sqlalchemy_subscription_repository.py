from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_
from sqlalchemy.exc import IntegrityError

from ...domain.entities.subscription import Subscription, SubscriptionStatus, BillingCycle
from ...domain.repositories.subscription_repository import SubscriptionRepository
from ...infrastructure.database.models import (
    SubscriptionModel,
    SubscriptionStatusEnum,
    BillingCycleEnum,
)


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    """SQLAlchemy implementation of SubscriptionRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, subscription: Subscription) -> Subscription:
        """Save a subscription entity."""
        try:
            # Check if subscription exists
            existing = self.session.get(SubscriptionModel, subscription.id)

            if existing:
                # Update existing subscription
                existing.organization_id = subscription.organization_id
                existing.plan_id = subscription.plan_id
                existing.status = SubscriptionStatusEnum(subscription.status.value)
                existing.billing_cycle = BillingCycleEnum(subscription.billing_cycle.value)
                existing.starts_at = subscription.starts_at
                existing.ends_at = subscription.ends_at
                existing.next_billing_date = subscription.next_billing_date
                existing.cancelled_at = subscription.cancelled_at
                existing.metadata = subscription.metadata
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new subscription
                subscription_model = SubscriptionModel(
                    id=subscription.id,
                    organization_id=subscription.organization_id,
                    plan_id=subscription.plan_id,
                    status=SubscriptionStatusEnum(subscription.status.value),
                    billing_cycle=BillingCycleEnum(subscription.billing_cycle.value),
                    starts_at=subscription.starts_at,
                    ends_at=subscription.ends_at,
                    next_billing_date=subscription.next_billing_date,
                    cancelled_at=subscription.cancelled_at,
                    metadata=subscription.metadata,
                    created_at=subscription.created_at,
                    updated_at=subscription.updated_at,
                )

                self.session.add(subscription_model)
                self.session.flush()
                return self._to_domain_entity(subscription_model)

        except IntegrityError as e:
            raise e

    def find_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        """Find a subscription by ID."""
        result = self.session.execute(
            select(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        )
        subscription_model = result.scalar_one_or_none()

        if subscription_model:
            return self._to_domain_entity(subscription_model)
        return None

    def find_by_organization(self, organization_id: UUID) -> List[Subscription]:
        """Find all subscriptions for an organization."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.organization_id == organization_id
            )
        )
        subscription_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in subscription_models]

    def find_active_by_organization(
        self, organization_id: UUID
    ) -> Optional[Subscription]:
        """Find active subscription for an organization."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                and_(
                    SubscriptionModel.organization_id == organization_id,
                    SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                )
            )
        )
        subscription_model = result.scalar_one_or_none()

        if subscription_model:
            return self._to_domain_entity(subscription_model)
        return None

    def find_by_plan(self, plan_id: UUID) -> List[Subscription]:
        """Find all subscriptions for a plan."""
        result = self.session.execute(
            select(SubscriptionModel).where(SubscriptionModel.plan_id == plan_id)
        )
        subscription_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in subscription_models]

    def find_by_status(self, status: str) -> List[Subscription]:
        """Find subscriptions by status."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.status == SubscriptionStatusEnum(status)
            )
        )
        subscription_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in subscription_models]

    def find_expiring_before(self, date: datetime) -> List[Subscription]:
        """Find subscriptions expiring before a date."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                and_(
                    SubscriptionModel.ends_at <= date,
                    SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                )
            )
        )
        subscription_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in subscription_models]

    def find_due_for_billing(self, date: datetime) -> List[Subscription]:
        """Find subscriptions due for billing."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                and_(
                    SubscriptionModel.next_billing_date <= date,
                    SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                )
            )
        )
        subscription_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in subscription_models]

    def find_paginated(
        self,
        organization_id: Optional[UUID] = None,
        plan_id: Optional[UUID] = None,
        status: Optional[str] = None,
        billing_cycle: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Subscription], int]:
        """Find subscriptions with pagination and filters."""
        query = select(SubscriptionModel)
        count_query = select(SubscriptionModel)

        # Apply filters
        if organization_id:
            query = query.where(SubscriptionModel.organization_id == organization_id)
            count_query = count_query.where(
                SubscriptionModel.organization_id == organization_id
            )

        if plan_id:
            query = query.where(SubscriptionModel.plan_id == plan_id)
            count_query = count_query.where(SubscriptionModel.plan_id == plan_id)

        if status:
            query = query.where(
                SubscriptionModel.status == SubscriptionStatusEnum(status)
            )
            count_query = count_query.where(
                SubscriptionModel.status == SubscriptionStatusEnum(status)
            )

        if billing_cycle:
            query = query.where(
                SubscriptionModel.billing_cycle == BillingCycleEnum(billing_cycle)
            )
            count_query = count_query.where(
                SubscriptionModel.billing_cycle == BillingCycleEnum(billing_cycle)
            )

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(SubscriptionModel.created_at.desc())
        )
        result = self.session.execute(query)
        subscription_models = result.scalars().all()

        subscriptions = [self._to_domain_entity(model) for model in subscription_models]
        return subscriptions, total

    def delete(self, subscription_id: UUID) -> bool:
        """Delete a subscription (hard delete)."""
        result = self.session.execute(
            delete(SubscriptionModel).where(SubscriptionModel.id == subscription_id)
        )
        return result.rowcount > 0

    def update_status(self, subscription_id: UUID, status: str) -> bool:
        """Update subscription status."""
        result = self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(
                status=SubscriptionStatusEnum(status),
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def cancel_subscription(
        self,
        subscription_id: UUID,
        cancelled_at: datetime,
        cancellation_reason: Optional[str] = None,
    ) -> bool:
        """Cancel a subscription."""
        update_values = {
            "status": SubscriptionStatusEnum.CANCELLED,
            "cancelled_at": cancelled_at,
            "updated_at": datetime.now(timezone.utc),
        }

        result = self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(**update_values)
        )

        # Update metadata with cancellation reason if provided
        if cancellation_reason and result.rowcount > 0:
            subscription = self.find_by_id(subscription_id)
            if subscription:
                subscription.metadata["cancellation_reason"] = cancellation_reason
                self.save(subscription)

        return result.rowcount > 0

    def update_billing_date(
        self, subscription_id: UUID, next_billing_date: datetime
    ) -> bool:
        """Update subscription billing date."""
        result = self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(
                next_billing_date=next_billing_date,
                updated_at=datetime.now(timezone.utc),
            )
        )
        return result.rowcount > 0

    def extend_subscription(
        self, subscription_id: UUID, new_end_date: datetime
    ) -> bool:
        """Extend subscription end date."""
        result = self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(ends_at=new_end_date, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def change_plan(self, subscription_id: UUID, new_plan_id: UUID) -> bool:
        """Change subscription plan."""
        result = self.session.execute(
            update(SubscriptionModel)
            .where(SubscriptionModel.id == subscription_id)
            .values(plan_id=new_plan_id, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def get_active_subscriptions_count(self) -> int:
        """Get count of active subscriptions."""
        result = self.session.execute(
            select(SubscriptionModel).where(
                SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE
            )
        )
        return len(result.scalars().all())

    def get_revenue_by_period(self, start_date: datetime, end_date: datetime) -> dict:
        """Get revenue data for a period."""
        # This would typically involve joining with billing/payment tables
        # For now, return a placeholder implementation
        result = self.session.execute(
            select(SubscriptionModel).where(
                and_(
                    SubscriptionModel.created_at >= start_date,
                    SubscriptionModel.created_at <= end_date,
                    SubscriptionModel.status == SubscriptionStatusEnum.ACTIVE,
                )
            )
        )
        subscriptions = result.scalars().all()

        return {
            "subscription_count": len(subscriptions),
            "period_start": start_date,
            "period_end": end_date,
        }

    def _to_domain_entity(self, subscription_model: SubscriptionModel) -> Subscription:
        """Convert SQLAlchemy model to domain entity."""
        return Subscription(
            id=subscription_model.id,
            organization_id=subscription_model.organization_id,
            plan_id=subscription_model.plan_id,
            status=SubscriptionStatus(subscription_model.status.value),
            billing_cycle=BillingCycle(subscription_model.billing_cycle.value),
            starts_at=subscription_model.starts_at,
            ends_at=subscription_model.ends_at,
            next_billing_date=subscription_model.next_billing_date,
            cancelled_at=subscription_model.cancelled_at,
            metadata=subscription_model.metadata or {},
            created_at=subscription_model.created_at,
            updated_at=subscription_model.updated_at,
        )
