from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.exc import IntegrityError

from ...domain.entities.feature_usage import FeatureUsage, UsagePeriod
from ...domain.repositories.feature_usage_repository import FeatureUsageRepository
from ..database.models import FeatureUsageModel


class SqlAlchemyFeatureUsageRepository(FeatureUsageRepository):
    """SQLAlchemy implementation of FeatureUsageRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, feature_usage: FeatureUsage) -> FeatureUsage:
        """Save or update feature usage."""
        try:
            existing = self.session.get(FeatureUsageModel, feature_usage.id)

            if existing:
                existing.current_usage = feature_usage.current_usage
                existing.limit_value = feature_usage.limit_value
                existing.metadata = feature_usage.metadata
                existing.updated_at = feature_usage.updated_at or datetime.now(timezone.utc)
                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                usage_model = FeatureUsageModel(
                    id=feature_usage.id,
                    organization_id=feature_usage.organization_id,
                    feature_name=feature_usage.feature_name,
                    usage_period=feature_usage.usage_period.value,
                    period_start=feature_usage.period_start,
                    period_end=feature_usage.period_end,
                    current_usage=feature_usage.current_usage,
                    limit_value=feature_usage.limit_value,
                    metadata=feature_usage.metadata,
                    created_at=feature_usage.created_at,
                    updated_at=feature_usage.updated_at,
                )
                self.session.add(usage_model)
                self.session.flush()
                return self._to_domain_entity(usage_model)

        except IntegrityError as e:
            raise ValueError(f"Error saving feature usage: {str(e)}")

    def get_by_id(self, usage_id: UUID) -> Optional[FeatureUsage]:
        """Get feature usage by ID."""
        usage_model = self.session.get(FeatureUsageModel, usage_id)
        return self._to_domain_entity(usage_model) if usage_model else None

    def get_current_usage(
        self, organization_id: UUID, feature_name: str, period: UsagePeriod
    ) -> Optional[FeatureUsage]:
        """Get current usage for organization and feature."""
        now = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(FeatureUsageModel).where(
                and_(
                    FeatureUsageModel.organization_id == organization_id,
                    FeatureUsageModel.feature_name == feature_name,
                    FeatureUsageModel.usage_period == period.value,
                    FeatureUsageModel.period_start <= now,
                    FeatureUsageModel.period_end >= now,
                )
            )
        )
        usage_model = result.scalar_one_or_none()
        return self._to_domain_entity(usage_model) if usage_model else None

    def get_organization_usage(
        self,
        organization_id: UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> List[FeatureUsage]:
        """Get all usage records for an organization."""
        query = select(FeatureUsageModel).where(
            FeatureUsageModel.organization_id == organization_id
        )

        if period_start:
            query = query.where(FeatureUsageModel.period_start >= period_start)
        if period_end:
            query = query.where(FeatureUsageModel.period_end <= period_end)

        result = self.session.execute(query.order_by(FeatureUsageModel.period_start.desc()))
        usage_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in usage_models]

    def get_feature_usage_across_organizations(
        self,
        feature_name: str,
        period: UsagePeriod,
        period_start: Optional[datetime] = None,
    ) -> List[FeatureUsage]:
        """Get usage for a specific feature across all organizations."""
        query = select(FeatureUsageModel).where(
            and_(
                FeatureUsageModel.feature_name == feature_name,
                FeatureUsageModel.usage_period == period.value,
            )
        )

        if period_start:
            query = query.where(FeatureUsageModel.period_start >= period_start)

        result = self.session.execute(query.order_by(FeatureUsageModel.current_usage.desc()))
        usage_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in usage_models]

    def get_organizations_exceeding_limit(
        self, feature_name: str, threshold_percent: float = 0.8
    ) -> List[UUID]:
        """Get organizations exceeding usage threshold for a feature."""
        now = datetime.now(timezone.utc)
        
        result = self.session.execute(
            select(FeatureUsageModel.organization_id).where(
                and_(
                    FeatureUsageModel.feature_name == feature_name,
                    FeatureUsageModel.period_start <= now,
                    FeatureUsageModel.period_end >= now,
                    FeatureUsageModel.limit_value > 0,  # Exclude unlimited
                    FeatureUsageModel.current_usage >= (FeatureUsageModel.limit_value * threshold_percent),
                )
            )
        )
        
        return [row[0] for row in result.fetchall()]

    def increment_usage(
        self,
        organization_id: UUID,
        feature_name: str,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeatureUsage:
        """Increment usage for organization and feature."""
        now = datetime.now(timezone.utc)
        
        # Try to find existing current usage record
        existing = self.session.execute(
            select(FeatureUsageModel).where(
                and_(
                    FeatureUsageModel.organization_id == organization_id,
                    FeatureUsageModel.feature_name == feature_name,
                    FeatureUsageModel.period_start <= now,
                    FeatureUsageModel.period_end >= now,
                )
            )
        ).scalar_one_or_none()

        if existing:
            # Update existing record
            existing.current_usage += amount
            if metadata:
                existing.metadata.update(metadata)
            existing.updated_at = now
            self.session.flush()
            return self._to_domain_entity(existing)
        else:
            # This should not happen in normal flow, but handle gracefully
            raise ValueError(f"No current usage record found for organization {organization_id} and feature {feature_name}")

    def reset_usage_for_period(
        self, organization_id: UUID, feature_name: str, period: UsagePeriod
    ) -> bool:
        """Reset usage for new billing period."""
        now = datetime.now(timezone.utc)
        period_start, period_end = FeatureUsage._calculate_period_boundaries(now, period)
        
        result = self.session.execute(
            update(FeatureUsageModel)
            .where(
                and_(
                    FeatureUsageModel.organization_id == organization_id,
                    FeatureUsageModel.feature_name == feature_name,
                    FeatureUsageModel.usage_period == period.value,
                )
            )
            .values(
                current_usage=0,
                period_start=period_start,
                period_end=period_end,
                metadata={},
                updated_at=now,
            )
        )
        
        return result.rowcount > 0

    def delete(self, usage_id: UUID) -> bool:
        """Delete usage record by ID."""
        result = self.session.execute(
            delete(FeatureUsageModel).where(FeatureUsageModel.id == usage_id)
        )
        return result.rowcount > 0

    def delete_old_records(self, older_than_days: int = 365) -> int:
        """Delete usage records older than specified days."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        
        result = self.session.execute(
            delete(FeatureUsageModel).where(
                FeatureUsageModel.period_end < cutoff_date
            )
        )
        
        return result.rowcount

    def get_usage_summary(
        self, organization_id: UUID, period_start: datetime, period_end: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Get usage summary for organization within period."""
        result = self.session.execute(
            select(
                FeatureUsageModel.feature_name,
                func.sum(FeatureUsageModel.current_usage).label("total_usage"),
                func.max(FeatureUsageModel.limit_value).label("max_limit"),
                func.count(FeatureUsageModel.id).label("record_count"),
            )
            .where(
                and_(
                    FeatureUsageModel.organization_id == organization_id,
                    FeatureUsageModel.period_start >= period_start,
                    FeatureUsageModel.period_end <= period_end,
                )
            )
            .group_by(FeatureUsageModel.feature_name)
        )
        
        summary = {}
        for row in result.fetchall():
            feature_name = row.feature_name
            total_usage = row.total_usage or 0
            max_limit = row.max_limit or 0
            record_count = row.record_count or 0
            
            summary[feature_name] = {
                "total_usage": total_usage,
                "limit_value": max_limit,
                "record_count": record_count,
                "usage_percentage": (total_usage / max_limit * 100) if max_limit > 0 else 0,
                "is_unlimited": max_limit == -1,
            }
        
        return summary

    def get_usage_trends(
        self, organization_id: UUID, feature_name: str, periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get usage trends for feature over specified periods."""
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=periods * 30)  # Approximate monthly periods
        
        result = self.session.execute(
            select(
                FeatureUsageModel.period_start,
                FeatureUsageModel.period_end,
                FeatureUsageModel.current_usage,
                FeatureUsageModel.limit_value,
            )
            .where(
                and_(
                    FeatureUsageModel.organization_id == organization_id,
                    FeatureUsageModel.feature_name == feature_name,
                    FeatureUsageModel.period_start >= cutoff_date,
                )
            )
            .order_by(FeatureUsageModel.period_start.desc())
            .limit(periods)
        )
        
        trends = []
        for row in result.fetchall():
            usage_percentage = (row.current_usage / row.limit_value * 100) if row.limit_value > 0 else 0
            
            trends.append({
                "period_start": row.period_start.isoformat(),
                "period_end": row.period_end.isoformat(),
                "usage": row.current_usage,
                "limit": row.limit_value,
                "usage_percentage": usage_percentage,
                "is_unlimited": row.limit_value == -1,
            })
        
        return trends

    def bulk_reset_monthly_usage(self) -> int:
        """Reset monthly usage for all organizations at month end."""
        now = datetime.now(timezone.utc)
        
        # Calculate new monthly period
        period_start, period_end = FeatureUsage._calculate_period_boundaries(now, UsagePeriod.MONTHLY)
        
        result = self.session.execute(
            update(FeatureUsageModel)
            .where(
                and_(
                    FeatureUsageModel.usage_period == UsagePeriod.MONTHLY.value,
                    FeatureUsageModel.period_end < now,  # Only reset expired periods
                )
            )
            .values(
                current_usage=0,
                period_start=period_start,
                period_end=period_end,
                metadata={},
                updated_at=now,
            )
        )
        
        return result.rowcount

    def _to_domain_entity(self, usage_model: FeatureUsageModel) -> FeatureUsage:
        """Convert SQLAlchemy model to domain entity."""
        return FeatureUsage(
            id=usage_model.id,
            organization_id=usage_model.organization_id,
            feature_name=usage_model.feature_name,
            usage_period=UsagePeriod(usage_model.usage_period),
            period_start=usage_model.period_start,
            period_end=usage_model.period_end,
            current_usage=usage_model.current_usage,
            limit_value=usage_model.limit_value,
            metadata=usage_model.metadata or {},
            created_at=usage_model.created_at,
            updated_at=usage_model.updated_at,
        )