"""DTOs for resource management."""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ResourceCreateDTO(BaseModel):
    """DTO for creating a new resource."""
    
    name: str = Field(..., min_length=1, max_length=100, description="Resource name")
    resource_type: str = Field(..., min_length=1, max_length=50, description="Resource type")
    description: Optional[str] = Field(None, max_length=500, description="Resource description")
    organization_id: UUID = Field(..., description="Organization ID this resource belongs to")
    parent_resource_id: Optional[UUID] = Field(None, description="Parent resource ID for hierarchy")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Resource attributes")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Resource name cannot be empty")
        return v.strip()
    
    @field_validator("resource_type")
    @classmethod
    def validate_resource_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Resource type cannot be empty")
        return v.strip()


class ResourceUpdateDTO(BaseModel):
    """DTO for updating an existing resource."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Resource name")
    description: Optional[str] = Field(None, max_length=500, description="Resource description")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Resource attributes")
    is_active: Optional[bool] = Field(None, description="Resource active status")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Resource name cannot be empty")
        return v.strip() if v else None


class ResourceResponseDTO(BaseModel):
    """DTO for resource response data."""
    
    id: UUID
    name: str
    resource_type: str
    description: Optional[str] = None
    organization_id: UUID
    parent_resource_id: Optional[UUID] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class ResourceListResponseDTO(BaseModel):
    """DTO for paginated resource list response."""
    
    resources: list[ResourceResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResourceApplicationDTO(BaseModel):
    """DTO for application resource creation."""
    
    app_type: str = Field(..., description="Application type")
    organization_id: UUID = Field(..., description="Organization ID")
    owner_id: UUID = Field(..., description="Resource owner ID")
    plan_features: Optional[list[str]] = Field(None, description="Plan features to enable")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom configuration")
    
    @field_validator("app_type")
    @classmethod
    def validate_app_type(cls, v: str) -> str:
        valid_types = ["web_chat_app", "management_app", "whatsapp_app", "api_access"]
        if v not in valid_types:
            raise ValueError(f"Invalid app type. Must be one of: {valid_types}")
        return v


class ResourceApplicationResponseDTO(ResourceResponseDTO):
    """DTO for application resource response with app-specific data."""
    
    app_type: str
    app_config: Dict[str, Any]
    resource_id: UUID  # For backward compatibility