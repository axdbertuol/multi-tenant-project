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
from sqlalchemy.sql import func
import enum

from src.shared.infrastructure.database.base import BaseModel


class PlanTypeEnum(str, enum.Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PlanResourceTypeEnum(str, enum.Enum):
    WHATSAPP_APP = "whatsapp_app"
    WEB_CHAT_APP = "web_chat_app"
    MANAGEMENT_APP = "management_app"
    API_ACCESS = "api_access"
    CUSTOM = "custom"


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
    resources = Column(JSON, nullable=False, default={})  # Plan resources configuration
    price_monthly = Column(Numeric(10, 2), nullable=True)
    price_yearly = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    features = Column(JSON, nullable=False, default=[])  # List of plan features
    limits = Column(JSON, nullable=False, default={})  # Plan limits configuration


class PlanResourceModel(BaseModel):
    """SQLAlchemy model for PlanResource entity."""

    __tablename__ = "plan_resources"

    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.plans.id"), nullable=False, index=True
    )
    resource_type = Column(Enum(PlanResourceTypeEnum), nullable=False, index=True)
    configuration = Column(
        JSON, nullable=False, default={}
    )  # Resource-specific configuration
    is_enabled = Column(Boolean, default=True, nullable=False)
    limits = Column(JSON, nullable=False, default={})  # Resource limits

    # Ensure unique resource type per plan
    __table_args__ = (
        UniqueConstraint("plan_id", "resource_type", name="uq_plan_resource_type"),
    )


class SubscriptionModel(BaseModel):
    """SQLAlchemy model for Subscription entity."""

    __tablename__ = "subscriptions"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.plans.id"), nullable=False, index=True
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

    # Ensure one active subscription per organization
    # __table_args__ = ({"postgresql_where": "status = 'active'"},)


class PlanConfigurationModel(BaseModel):
    """SQLAlchemy model for PlanConfiguration entity."""

    __tablename__ = "plan_configurations"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.plans.id"), nullable=False, index=True
    )
    configuration_data = Column(
        JSON, nullable=False, default={}
    )  # Configuration settings
    api_keys = Column(JSON, nullable=False, default={})  # Encrypted API keys
    limits = Column(JSON, nullable=False, default={})  # Custom limits
    is_active = Column(Boolean, default=True, nullable=False)

    # Ensure unique configuration per organization-plan
    __table_args__ = (
        UniqueConstraint(
            "plan_id", "organization_id", name="uq_plan_organization_type"
        ),
    )


class FeatureUsageModel(BaseModel):
    """SQLAlchemy model for FeatureUsage entity."""

    __tablename__ = "feature_usage"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    resource_type = Column(String(50), nullable=False, index=True)
    feature_name = Column(String(100), nullable=False, index=True)
    usage_count = Column(Integer, default=0, nullable=False)
    usage_date = Column(DateTime(timezone=True), nullable=False, index=True)
    usage_details = Column(
        JSON, nullable=False, default={}
    )  # Detailed usage information
    cost = Column(Numeric(10, 4), nullable=True)  # Cost associated with usage

    # Index for efficient usage queries
    __table_args__ = (
        Index("ix_usage_lookup", "organization_id", "resource_type", "usage_date"),
    )
