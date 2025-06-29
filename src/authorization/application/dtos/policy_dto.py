from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PolicyEffectEnum(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyConditionDTO(BaseModel):
    """DTO for policy condition."""

    attribute: str = Field(..., description="Attribute name")
    operator: str = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Expected value")

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        valid_operators = [
            "eq",
            "ne",
            "gt",
            "lt",
            "gte",
            "lte",
            "in",
            "not_in",
            "contains",
        ]
        if v not in valid_operators:
            raise ValueError(
                f"Invalid operator. Must be one of: {', '.join(valid_operators)}"
            )
        return v


class PolicyCreateDTO(BaseModel):
    """DTO for creating a new policy."""

    name: str = Field(..., min_length=2, max_length=100, description="Policy name")
    description: str = Field(..., max_length=500, description="Policy description")
    effect: PolicyEffectEnum = Field(..., description="Policy effect (allow/deny)")
    resource_type: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action")
    conditions: List[PolicyConditionDTO] = Field(
        default_factory=list, description="Policy conditions"
    )
    organization_id: Optional[UUID] = Field(
        None, description="Organization ID (None for global policies)"
    )
    priority: int = Field(
        0, ge=0, le=1000, description="Policy priority (higher = more important)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Policy name cannot be empty")
        return v.strip()


class PolicyUpdateDTO(BaseModel):
    """DTO for updating an existing policy."""

    description: Optional[str] = Field(
        None, max_length=500, description="Policy description"
    )
    effect: Optional[PolicyEffectEnum] = Field(None, description="Policy effect")
    conditions: Optional[List[PolicyConditionDTO]] = Field(
        None, description="Policy conditions"
    )
    priority: Optional[int] = Field(None, ge=0, le=1000, description="Policy priority")


class PolicyResponseDTO(BaseModel):
    """DTO for policy response data."""

    id: UUID
    name: str
    description: str
    effect: str
    resource_type: str
    action: str
    conditions: List[Dict[str, Any]]
    organization_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    priority: int

    model_config = {"from_attributes": True}


class PolicyListResponseDTO(BaseModel):
    """DTO for paginated policy list response."""

    policies: List[PolicyResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class PolicyEvaluationRequestDTO(BaseModel):
    """DTO for policy evaluation request."""

    user_id: UUID = Field(..., description="User ID")
    resource_type: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    resource_id: Optional[UUID] = Field(None, description="Resource ID")
    user_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="User attributes"
    )
    resource_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Resource attributes"
    )
    environment_attributes: Dict[str, Any] = Field(
        default_factory=dict, description="Environment attributes"
    )


class PolicyEvaluationResponseDTO(BaseModel):
    """DTO for policy evaluation response."""

    policy_id: UUID
    policy_name: str
    result: Optional[bool]  # None if not applicable
    conditions_met: bool
    condition_results: List[Dict[str, Any]]
    evaluation_time_ms: float
