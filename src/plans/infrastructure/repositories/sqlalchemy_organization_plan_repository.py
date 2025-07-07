from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, func, DateTime
from sqlalchemy.exc import IntegrityError

from ...domain.entities.organization_plan import OrganizationPlan, SubscriptionStatus, BillingCycle
from ...domain.repositories.organization_plan_repository import OrganizationPlanRepository
from ..database.models import SubscriptionModel


class SqlAlchemyOrganizationPlanRepository(OrganizationPlanRepository):
    """SQLAlchemy implementation of OrganizationPlanRepository using SubscriptionModel."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, organization_plan: OrganizationPlan) -> OrganizationPlan:
        """Save or update an organization plan."""
        try:
            existing = self.session.get(SubscriptionModel, organization_plan.id)

            if existing:
                existing.status = organization_plan.status.value
                existing.billing_cycle = organization_plan.billing_cycle.value
                existing.starts_at = organization_plan.started_at
                existing.ends_at = organization_plan.expires_at
                existing.cancelled_at = organization_plan.cancelled_at
                existing.subscription_metadata = {
                    "feature_overrides": organization_plan.feature_overrides,
                    "limit_overrides": organization_plan.limit_overrides,
                    "auto_renew": organization_plan.auto_renew,
                    "suspended_at": organization_plan.suspended_at.isoformat() if organization_plan.suspended_at else None,
                    "trial_ends_at": organization_plan.trial_ends_at.isoformat() if organization_plan.trial_ends_at else None,
                }
                existing.updated_at = organization_plan.updated_at or datetime.now(timezone.utc)
                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                subscription_model = SubscriptionModel(
                    id=organization_plan.id,
                    organization_id=organization_plan.organization_id,
                    plan_id=organization_plan.plan_id,
                    status=organization_plan.status.value,
                    billing_cycle=organization_plan.billing_cycle.value,
                    starts_at=organization_plan.started_at,
                    ends_at=organization_plan.expires_at,
                    cancelled_at=organization_plan.cancelled_at,
                    subscription_metadata={
                        "feature_overrides": organization_plan.feature_overrides,
                        "limit_overrides": organization_plan.limit_overrides,
                        "auto_renew": organization_plan.auto_renew,
                        "suspended_at": organization_plan.suspended_at.isoformat() if organization_plan.suspended_at else None,
                        "trial_ends_at": organization_plan.trial_ends_at.isoformat() if organization_plan.trial_ends_at else None,
                    },
                    created_at=organization_plan.created_at,
                    updated_at=organization_plan.updated_at,
                )
                self.session.add(subscription_model)
                self.session.flush()
                return self._to_domain_entity(subscription_model)

        except IntegrityError as e:
            raise ValueError(f"Error saving organization plan: {str(e)}")

    def get_by_id(self, organization_plan_id: UUID) -> Optional[OrganizationPlan]:
        """Get organization plan by ID."""
        subscription_model = self.session.get(SubscriptionModel, organization_plan_id)
        return self._to_domain_entity(subscription_model) if subscription_model else None

    def get_by_organization_id(self, organization_id: UUID) -> Optional[OrganizationPlan]:
        """Get current plan for an organization."""
        result = self.session.execute(
            select(SubscriptionModel)
            .where(
                and_(
                    SubscriptionModel.organization_id == organization_id,
                    SubscriptionModel.status.in_(["active", "suspended"])
                )
            )
            .order_by(SubscriptionModel.created_at.desc())
            .limit(1)
        )
        subscription_model = result.scalar_one_or_none()
        return self._to_domain_entity(subscription_model) if subscription_model else None

    def get_organization_plan_history(self, organization_id: UUID) -> List[OrganizationPlan]:
        """Get plan history for an organization."""
        result = self.session.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.organization_id == organization_id)
            .order_by(SubscriptionModel.created_at.desc())
        )
        subscription_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in subscription_models]

    def get_by_plan_id(self, plan_id: UUID) -> List[OrganizationPlan]:
        """Get all organizations using a specific plan."""
        result = self.session.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.plan_id == plan_id)
            .order_by(SubscriptionModel.created_at.desc())
        )
        subscription_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in subscription_models]

    def get_expiring_plans(self, days_ahead: int = 7) -> List[OrganizationPlan]:
        """Get plans expiring within specified days."""
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        result = self.session.execute(
            select(SubscriptionModel)
            .where(
                and_(
                    SubscriptionModel.status == "active",
                    SubscriptionModel.ends_at <= cutoff_date,
                    SubscriptionModel.ends_at.is_not(None)
                )
            )
            .order_by(SubscriptionModel.ends_at.asc())
        )
        subscription_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in subscription_models]

    def get_trial_ending_plans(self, days_ahead: int = 3) -> List[OrganizationPlan]:
        """Get plans with trials ending within specified days."""
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        result = self.session.execute(
            select(SubscriptionModel)
            .where(
                and_(
                    SubscriptionModel.status == "active",
                    SubscriptionModel.subscription_metadata["trial_ends_at"].astext.is_not(None),
                    func.cast(SubscriptionModel.subscription_metadata["trial_ends_at"].astext, DateTime) <= cutoff_date
                )
            )
            .order_by(SubscriptionModel.created_at.desc())
        )
        subscription_models = result.scalars().all()
        
        # Filter in Python since complex JSON date comparisons are tricky in SQL
        trial_ending = []
        for model in subscription_models:
            metadata = model.subscription_metadata or {}
            trial_ends_str = metadata.get("trial_ends_at")
            if trial_ends_str:
                try:
                    trial_ends_at = datetime.fromisoformat(trial_ends_str.replace('Z', '+00:00'))
                    if trial_ends_at <= cutoff_date:
                        trial_ending.append(self._to_domain_entity(model))
                except (ValueError, TypeError):
                    continue
        
        return trial_ending

    def get_by_status(self, status: SubscriptionStatus) -> List[OrganizationPlan]:
        """Get organization plans by status."""
        result = self.session.execute(
            select(SubscriptionModel)
            .where(SubscriptionModel.status == status.value)
            .order_by(SubscriptionModel.created_at.desc())
        )
        subscription_models = result.scalars().all()
        return [self._to_domain_entity(model) for model in subscription_models]

    def delete(self, organization_plan_id: UUID) -> bool:
        """Delete organization plan by ID."""
        result = self.session.execute(
            delete(SubscriptionModel).where(SubscriptionModel.id == organization_plan_id)
        )
        return result.rowcount > 0

    def count_active_subscriptions(self, plan_id: Optional[UUID] = None) -> int:
        """Count active subscriptions, optionally filtered by plan."""
        query = select(func.count(SubscriptionModel.id)).where(
            SubscriptionModel.status == "active"
        )
        
        if plan_id:
            query = query.where(SubscriptionModel.plan_id == plan_id)
        
        result = self.session.execute(query)
        return result.scalar() or 0

    def get_organizations_with_feature(
        self, feature_name: str, enabled: bool = True
    ) -> List[UUID]:
        """Get organization IDs that have a specific feature enabled/disabled."""
        result = self.session.execute(
            select(SubscriptionModel.organization_id)
            .where(
                and_(
                    SubscriptionModel.status == "active",
                    SubscriptionModel.subscription_metadata.has_key("feature_overrides")
                )
            )
        )
        
        # Filter in Python since complex JSON queries are database-specific
        organization_ids = []
        for row in result.fetchall():
            org_id = row[0]
            # Get the subscription to check feature overrides
            subscription = self.session.execute(
                select(SubscriptionModel)
                .where(SubscriptionModel.organization_id == org_id)
                .limit(1)
            ).scalar_one_or_none()
            
            if subscription and subscription.subscription_metadata:
                feature_overrides = subscription.subscription_metadata.get("feature_overrides", {})
                feature_enabled = feature_overrides.get(feature_name, not enabled)  # Default opposite of what we're looking for
                
                if feature_enabled == enabled:
                    organization_ids.append(org_id)
        
        return organization_ids

    def cleanup_expired_plans(self) -> int:
        """Update status of expired plans. Returns count of updated plans."""
        now = datetime.now(timezone.utc)
        
        result = self.session.execute(
            update(SubscriptionModel)
            .where(
                and_(
                    SubscriptionModel.status == "active",
                    SubscriptionModel.ends_at <= now,
                    SubscriptionModel.ends_at.is_not(None)
                )
            )
            .values(status="expired", updated_at=now)
        )
        
        return result.rowcount

    def _to_domain_entity(self, subscription_model: SubscriptionModel) -> OrganizationPlan:
        """Convert SQLAlchemy model to domain entity."""
        metadata = subscription_model.subscription_metadata or {}
        
        # Parse datetime strings from metadata
        suspended_at = None
        trial_ends_at = None
        
        if metadata.get("suspended_at"):
            try:
                suspended_at = datetime.fromisoformat(metadata["suspended_at"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        
        if metadata.get("trial_ends_at"):
            try:
                trial_ends_at = datetime.fromisoformat(metadata["trial_ends_at"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                pass
        
        return OrganizationPlan(
            id=subscription_model.id,
            organization_id=subscription_model.organization_id,
            plan_id=subscription_model.plan_id,
            status=SubscriptionStatus(subscription_model.status),
            billing_cycle=BillingCycle(subscription_model.billing_cycle),
            feature_overrides=metadata.get("feature_overrides", {}),
            limit_overrides=metadata.get("limit_overrides", {}),
            started_at=subscription_model.starts_at,
            expires_at=subscription_model.ends_at,
            cancelled_at=subscription_model.cancelled_at,
            suspended_at=suspended_at,
            trial_ends_at=trial_ends_at,
            auto_renew=metadata.get("auto_renew", True),
            created_at=subscription_model.created_at,
            updated_at=subscription_model.updated_at,
        )