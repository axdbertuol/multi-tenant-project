from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from ...domain.entities.plan import PlanType


class PlanCreateDTO(BaseModel):
    """DTO for creating a new plan."""
    name: str = Field(..., min_length=2, max_length=100, description="Plan name")
    description: str = Field(..., max_length=500, description="Plan description")
    plan_type: PlanType = Field(..., description="Plan type")
    resources: Dict[str, Any] = Field(default_factory=dict, description="Plan resources configuration")
    price_monthly: Optional[float] = Field(None, ge=0, description="Monthly price")
    price_yearly: Optional[float] = Field(None, ge=0, description="Yearly price")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Plan name cannot be empty')
        return v.strip()
    
    @field_validator('resources')
    @classmethod
    def validate_resources(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        # Validate resource structure for known resource types
        for resource_type, config in v.items():
            if resource_type in ['chat_whatsapp', 'chat_iframe']:
                if not isinstance(config, dict):
                    raise ValueError(f"Resource {resource_type} must be a dictionary")
                if 'enabled' not in config:
                    raise ValueError(f"Resource {resource_type} must have 'enabled' field")
        return v


class PlanUpdateDTO(BaseModel):
    """DTO for updating an existing plan."""
    description: Optional[str] = Field(None, max_length=500, description="Plan description")
    resources: Optional[Dict[str, Any]] = Field(None, description="Plan resources configuration")
    price_monthly: Optional[float] = Field(None, ge=0, description="Monthly price")
    price_yearly: Optional[float] = Field(None, ge=0, description="Yearly price")
    
    @field_validator('resources')
    @classmethod
    def validate_resources(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        
        # Validate resource structure for known resource types
        for resource_type, config in v.items():
            if resource_type in ['chat_whatsapp', 'chat_iframe']:
                if not isinstance(config, dict):
                    raise ValueError(f"Resource {resource_type} must be a dictionary")
                if 'enabled' not in config:
                    raise ValueError(f"Resource {resource_type} must have 'enabled' field")
        return v


class PlanResponseDTO(BaseModel):
    """DTO for plan response data."""
    id: UUID
    name: str
    description: str
    plan_type: str
    resources: Dict[str, Any]
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    subscription_count: int  # Number of active subscriptions
    
    model_config = {"from_attributes": True}


class PlanListResponseDTO(BaseModel):
    """DTO for paginated plan list response."""
    plans: List[PlanResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlanResourceConfigDTO(BaseModel):
    """DTO for plan resource configuration."""
    resource_type: str = Field(..., description="Resource type (e.g., chat_whatsapp, chat_iframe)")
    enabled: bool = Field(..., description="Whether resource is enabled")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Resource-specific configuration")
    limits: Dict[str, Any] = Field(default_factory=dict, description="Resource limits")


class PlanValidationRequestDTO(BaseModel):
    """DTO for plan validation request."""
    organization_id: UUID = Field(..., description="Organization ID")
    plan_id: UUID = Field(..., description="Plan ID")
    resource_type: str = Field(..., description="Resource type to validate")
    action: str = Field(..., description="Action to validate")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class PlanValidationResponseDTO(BaseModel):
    """DTO for plan validation response."""
    is_allowed: bool
    plan_name: str
    resource_type: str
    action: str
    reason: str
    current_usage: Optional[Dict[str, Any]] = None
    limits: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)