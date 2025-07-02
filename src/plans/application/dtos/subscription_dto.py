from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycleEnum(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionCreateDTO(BaseModel):
    """DTO for creating a new subscription."""

    organization_id: UUID = Field(..., description="Organization ID")
    plan_id: UUID = Field(..., description="Plan ID")
    billing_cycle: BillingCycleEnum = Field(..., description="Billing cycle")
    starts_at: Optional[datetime] = Field(None, description="Subscription start date")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    @field_validator("starts_at")
    @classmethod
    def validate_starts_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.now():
            raise ValueError("Subscription start date cannot be in the past")
        return v


class SubscriptionUpdateDTO(BaseModel):
    """DTO for updating an existing subscription."""

    billing_cycle: Optional[BillingCycleEnum] = Field(None, description="Billing cycle")
    ends_at: Optional[datetime] = Field(None, description="Subscription end date")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class SubscriptionResponseDTO(BaseModel):
    """DTO for subscription response data."""

    id: UUID
    organization_id: UUID
    plan_id: UUID
    plan_name: str
    plan_type: str
    status: str
    billing_cycle: str
    starts_at: datetime
    ends_at: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: dict
    is_trial: bool = False

    model_config = {"from_attributes": True}


class SubscriptionListResponseDTO(BaseModel):
    """DTO for paginated subscription list response."""

    subscriptions: List[SubscriptionResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class SubscriptionUpgradeDTO(BaseModel):
    """DTO for subscription upgrade request."""

    new_plan_id: UUID = Field(..., description="New plan ID")
    billing_cycle: Optional[BillingCycleEnum] = Field(
        None, description="Billing cycle for new plan"
    )
    upgrade_immediately: bool = Field(
        True, description="Whether to upgrade immediately"
    )
    prorate: bool = Field(True, description="Whether to prorate the charges")


class SubscriptionDowngradeDTO(BaseModel):
    """DTO for subscription downgrade request."""

    new_plan_id: UUID = Field(..., description="New plan ID")
    billing_cycle: Optional[BillingCycleEnum] = Field(
        None, description="Billing cycle for new plan"
    )
    downgrade_at_period_end: bool = Field(
        True, description="Whether to downgrade at the end of current period"
    )


class SubscriptionCancellationDTO(BaseModel):
    """DTO for subscription cancellation request."""

    cancel_immediately: bool = Field(False, description="Whether to cancel immediately")
    cancellation_reason: Optional[str] = Field(
        None, max_length=500, description="Reason for cancellation"
    )
    feedback: Optional[str] = Field(None, max_length=1000, description="User feedback")
