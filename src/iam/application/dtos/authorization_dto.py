from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class AuthorizationRequestDTO(BaseModel):
    """DTO for authorization request."""
    user_id: UUID = Field(..., description="User ID")
    resource_type: str = Field(..., description="Resource type")
    action: str = Field(..., description="Action to perform")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    resource_id: Optional[UUID] = Field(None, description="Specific resource ID")
    user_attributes: Dict[str, Any] = Field(default_factory=dict, description="User attributes")
    resource_attributes: Dict[str, Any] = Field(default_factory=dict, description="Resource attributes")
    environment_attributes: Dict[str, Any] = Field(default_factory=dict, description="Environment attributes")


class AuthorizationResponseDTO(BaseModel):
    """DTO for authorization response."""
    user_id: UUID
    resource_type: str
    action: str
    is_authorized: bool
    decision_reason: str
    rbac_result: Optional[bool] = None
    abac_result: Optional[bool] = None
    applicable_roles: List[str] = Field(default_factory=list)
    applicable_policies: List[str] = Field(default_factory=list)
    evaluation_time_ms: float
    evaluated_at: datetime


class BulkAuthorizationRequestDTO(BaseModel):
    """DTO for bulk authorization request."""
    requests: List[AuthorizationRequestDTO] = Field(..., description="List of authorization requests")


class BulkAuthorizationResponseDTO(BaseModel):
    """DTO for bulk authorization response."""
    results: List[AuthorizationResponseDTO]
    total_requests: int
    authorized_count: int
    denied_count: int
    total_evaluation_time_ms: float


class UserPermissionsResponseDTO(BaseModel):
    """DTO for user permissions response."""
    user_id: UUID
    organization_id: Optional[UUID] = None
    resource_type: Optional[str] = None
    roles: List[str]
    permissions: List[Dict[str, Any]]
    permission_count: int


class RoleAssignmentDTO(BaseModel):
    """DTO for role assignment."""
    user_id: UUID = Field(..., description="User ID")
    role_id: UUID = Field(..., description="Role ID")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    assigned_by: UUID = Field(..., description="User who assigned the role")
    expires_at: Optional[datetime] = Field(None, description="Role expiration date")