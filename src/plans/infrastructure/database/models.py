from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    Text,
    Enum,
    Integer,
    Numeric,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
import enum

from src.shared.infrastructure.database.base import BaseModel


class PlanTypeEnum(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"
    SUSPENDED = "suspended"


class BillingCycleEnum(str, enum.Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"


class PlanModel(BaseModel):
    """SQLAlchemy model for Plan entity."""

    __tablename__ = "plans"

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False)
    plan_type = Column(Enum(PlanTypeEnum), nullable=False, index=True)
    price_monthly = Column(Numeric(10, 2), nullable=True)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class SubscriptionModel(BaseModel):
    """SQLAlchemy model for Subscription entity."""

    __tablename__ = "subscriptions"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )
    status = Column(
        Enum(SubscriptionStatusEnum),
        nullable=False,
        default=SubscriptionStatusEnum.PENDING,
        index=True,
    )
    billing_cycle = Column(Enum(BillingCycleEnum), nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    subscription_metadata = Column(
        JSON, nullable=False, default={}
    )  # Additional subscription data
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Ensure one active subscription per organization
    __table_args__ = (Index("ix_active_subscription_per_org", "organization_id"),)


class PlanResourceModel(BaseModel):
    """SQLAlchemy model for PlanResource entity - defines available resources."""

    __tablename__ = "plan_resources"

    resource_type = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(
        String(50), nullable=False, index=True
    )  # 'messaging', 'analytics', 'storage'
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)


class PlanResourceFeatureModel(BaseModel):
    """SQLAlchemy model for PlanResourceFeature entity - defines features for resources."""

    __tablename__ = "plan_resource_features"

    resource_id = Column(
        UUID(as_uuid=True), ForeignKey("plan_resources.id"), nullable=False, index=True
    )
    feature_key = Column(String(100), nullable=False, index=True)
    feature_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)

    # Ensure unique feature key per resource
    __table_args__ = (
        UniqueConstraint("resource_id", "feature_key", name="uq_resource_feature_key"),
    )


class PlanResourceLimitModel(BaseModel):
    """SQLAlchemy model for PlanResourceLimit entity - defines limits for resources."""

    __tablename__ = "plan_resource_limits"

    resource_id = Column(
        UUID(as_uuid=True), ForeignKey("plan_resources.id"), nullable=False, index=True
    )
    limit_key = Column(String(100), nullable=False, index=True)
    limit_name = Column(String(200), nullable=False)
    limit_type = Column(
        String(50), nullable=False
    )  # 'count', 'size', 'rate', 'duration'
    default_value = Column(Integer, nullable=True)
    unit = Column(String(20), nullable=True)  # 'per_month', 'MB', 'requests_per_minute'
    description = Column(Text, nullable=True)

    # Ensure unique limit key per resource
    __table_args__ = (
        UniqueConstraint("resource_id", "limit_key", name="uq_resource_limit_key"),
    )


class PlanResourceAssociationModel(BaseModel):
    """SQLAlchemy model for Plan-Resource association."""

    __tablename__ = "plan_resource_associations"

    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )
    resource_id = Column(
        UUID(as_uuid=True), ForeignKey("plan_resources.id"), nullable=False, index=True
    )
    is_included = Column(Boolean, default=True, nullable=False)
    additional_cost = Column(
        Numeric(10, 2), nullable=True
    )  # Extra cost for this resource

    # Ensure unique resource per plan
    __table_args__ = (
        UniqueConstraint("plan_id", "resource_id", name="uq_plan_resource"),
    )


class PlanResourceFeatureConfigModel(BaseModel):
    """SQLAlchemy model for plan-specific feature configurations."""

    __tablename__ = "plan_resource_feature_configs"

    plan_resource_association_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_resource_associations.id"),
        nullable=False,
        index=True,
    )
    feature_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_resource_features.id"),
        nullable=False,
        index=True,
    )
    is_enabled = Column(Boolean, default=True, nullable=False)
    custom_config = Column(JSON, nullable=False, default={})

    # Ensure unique feature config per plan-resource association
    __table_args__ = (
        UniqueConstraint(
            "plan_resource_association_id", "feature_id", name="uq_plan_feature_config"
        ),
    )


class PlanResourceLimitConfigModel(BaseModel):
    """SQLAlchemy model for plan-specific limit configurations."""

    __tablename__ = "plan_resource_limit_configs"

    plan_resource_association_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_resource_associations.id"),
        nullable=False,
        index=True,
    )
    limit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_resource_limits.id"),
        nullable=False,
        index=True,
    )
    limit_value = Column(Integer, nullable=False)
    custom_config = Column(JSON, nullable=False, default={})

    # Ensure unique limit config per plan-resource association
    __table_args__ = (
        UniqueConstraint(
            "plan_resource_association_id", "limit_id", name="uq_plan_limit_config"
        ),
    )


class ApplicationInstanceModel(BaseModel):
    """SQLAlchemy model for ApplicationInstance entity - moved from IAM."""

    __tablename__ = "application_instances"

    plan_resource_id = Column(
        UUID(as_uuid=True), ForeignKey("plan_resources.id"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
        index=True,
    )
    instance_name = Column(String(200), nullable=False)
    configuration = Column(
        JSON, nullable=False, default={}
    )  # Application-specific configuration
    api_keys = Column(JSON, nullable=False, default={})  # Encrypted API keys
    limits_override = Column(
        JSON, nullable=False, default={}
    )  # Custom limits for this instance
    is_active = Column(Boolean, default=True, nullable=False)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Ensure unique instance per organization-resource
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "plan_resource_id", name="uq_org_application_instance"
        ),
        Index("ix_app_instance_lookup", "organization_id", "plan_resource_id"),
        Index("ix_app_instance_active", "is_active", "organization_id"),
    )


class FeatureUsageModel(BaseModel):
    """SQLAlchemy model for FeatureUsage entity."""

    __tablename__ = "feature_usage"

    application_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application_instances.id"),
        nullable=False,
        index=True,
    )
    feature_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_resource_features.id"),
        nullable=False,
        index=True,
    )
    usage_count = Column(Integer, default=0, nullable=False)
    usage_date = Column(DateTime(timezone=True), nullable=False, index=True)
    usage_details = Column(
        JSON, nullable=False, default={}
    )  # Detailed usage information
    cost = Column(Numeric(10, 4), nullable=True)  # Cost associated with usage

    # Indexes for efficient usage queries
    __table_args__ = (
        Index("ix_usage_lookup", "application_instance_id", "feature_id", "usage_date"),
        Index("ix_usage_by_date", "usage_date"),
        Index("ix_usage_by_instance", "application_instance_id", "usage_date"),
    )
