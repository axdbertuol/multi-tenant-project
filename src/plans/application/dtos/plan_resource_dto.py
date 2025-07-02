from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from ...domain.entities.plan_resource import PlanResourceType


class PlanResourceCreateDTO(BaseModel):
    """DTO for creating a new plan resource."""

    plan_id: UUID = Field(..., description="Plan ID")
    resource_type: PlanResourceType = Field(..., description="Resource type")
    configuration: Dict[str, Any] = Field(..., description="Resource configuration")
    is_enabled: bool = Field(True, description="Whether resource is enabled")

    @field_validator("configuration")
    @classmethod
    def validate_configuration(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        resource_type = info.data.get("resource_type")

        if resource_type == PlanResourceType.CHAT_WHATSAPP:
            required_fields = ["api_key", "webhook_url", "phone_number"]
            for field in required_fields:
                if field not in v:
                    raise ValueError(
                        f"WhatsApp configuration missing required field: {field}"
                    )

        elif resource_type == PlanResourceType.CHAT_IFRAME:
            required_fields = ["iframe_url", "allowed_domains"]
            for field in required_fields:
                if field not in v:
                    raise ValueError(
                        f"Iframe configuration missing required field: {field}"
                    )

        return v


class PlanResourceUpdateDTO(BaseModel):
    """DTO for updating an existing plan resource."""

    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Resource configuration"
    )
    is_enabled: Optional[bool] = Field(None, description="Whether resource is enabled")

    @field_validator("configuration")
    @classmethod
    def validate_configuration(
        cls, v: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        if v is None:
            return v

        # Basic validation - specific validation will be done in use case
        if not isinstance(v, dict):
            raise ValueError("Configuration must be a dictionary")

        return v


class PlanResourceResponseDTO(BaseModel):
    """DTO for plan resource response data."""

    id: UUID
    plan_id: UUID
    plan_name: str
    resource_type: str
    configuration: Dict[str, Any]
    is_enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    usage_count: int  # Number of times this resource has been used

    model_config = {"from_attributes": True}


class PlanResourceListResponseDTO(BaseModel):
    """DTO for paginated plan resource list response."""

    resources: List[PlanResourceResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlanResourceTestDTO(BaseModel):
    """DTO for testing plan resource configuration."""

    plan_id: UUID = Field(..., description="Plan ID")
    resource_type: PlanResourceType = Field(..., description="Resource type")
    test_configuration: Dict[str, Any] = Field(..., description="Configuration to test")
    test_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Test parameters"
    )


class PlanResourceTestResponseDTO(BaseModel):
    """DTO for plan resource test response."""

    success: bool
    resource_type: str
    test_results: Dict[str, Any]
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class PlanResourceUsageDTO(BaseModel):
    """DTO for plan resource usage data."""

    resource_id: UUID
    organization_id: UUID
    resource_type: str
    usage_date: datetime
    usage_count: int
    usage_details: Dict[str, Any] = Field(default_factory=dict)
    cost: Optional[float] = None


class PlanResourceUsageResponseDTO(BaseModel):
    """DTO for plan resource usage response."""

    resource_id: UUID
    resource_type: str
    total_usage: int
    usage_period: str
    usage_breakdown: Dict[str, Any]
    cost_breakdown: Dict[str, float]
    usage_trends: List[Dict[str, Any]] = Field(default_factory=list)
