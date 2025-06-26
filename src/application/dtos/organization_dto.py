from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CreateOrganizationDto(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class UpdateOrganizationDto(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class TransferOwnershipDto(BaseModel):
    new_owner_id: UUID


class AddUserToOrganizationDto(BaseModel):
    user_id: UUID


class OrganizationResponseDto(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    model_config = {"from_attributes": True}


class OrganizationMembershipDto(BaseModel):
    organization: OrganizationResponseDto
    joined_at: datetime

    model_config = {"from_attributes": True}