"""Organization management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID

from ..dependencies import get_organization_use_case, get_membership_use_case
from ...application.dtos.organization_dto import (
    OrganizationCreateDTO,
    OrganizationUpdateDTO,
    OrganizationResponseDTO,
    OrganizationListResponseDTO,
)
from ...application.dtos.membership_dto import (
    MembershipCreateDTO,
    MembershipResponseDTO,
    MembershipListResponseDTO,
)
from ...application.use_cases.organization_use_cases import OrganizationUseCase
from ...application.use_cases.membership_use_cases import MembershipUseCase

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post("/", response_model=OrganizationResponseDTO, status_code=status.HTTP_201_CREATED)
def create_organization(
    dto: OrganizationCreateDTO,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Create a new organization (tenant)."""
    try:
        return use_case.create_organization(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{organization_id}", response_model=OrganizationResponseDTO)
def get_organization(
    organization_id: UUID,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Get organization by ID."""
    try:
        organization = use_case.get_organization_by_id(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return organization
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=OrganizationListResponseDTO)
def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    owner_id: Optional[UUID] = Query(None, description="Filter by owner"),
    active_only: bool = Query(True, description="Show only active organizations"),
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """List organizations with pagination."""
    try:
        return use_case.list_organizations(
            page=page, 
            page_size=page_size, 
            owner_id=owner_id,
            active_only=active_only
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{organization_id}", response_model=OrganizationResponseDTO)
def update_organization(
    organization_id: UUID,
    dto: OrganizationUpdateDTO,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Update organization information."""
    try:
        return use_case.update_organization(organization_id, dto)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{organization_id}/deactivate", response_model=OrganizationResponseDTO)
def deactivate_organization(
    organization_id: UUID,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Deactivate organization."""
    try:
        return use_case.deactivate_organization(organization_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{organization_id}/activate", response_model=OrganizationResponseDTO)
def activate_organization(
    organization_id: UUID,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    """Activate organization."""
    try:
        return use_case.activate_organization(organization_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Membership management routes
@router.post("/{organization_id}/members", response_model=MembershipResponseDTO, status_code=status.HTTP_201_CREATED)
def add_organization_member(
    organization_id: UUID,
    dto: MembershipCreateDTO,
    use_case: MembershipUseCase = Depends(get_membership_use_case),
):
    """Add a member to organization."""
    try:
        dto.organization_id = organization_id
        return use_case.add_member(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{organization_id}/members", response_model=MembershipListResponseDTO)
def list_organization_members(
    organization_id: UUID,
    active_only: bool = Query(True, description="Show only active members"),
    use_case: MembershipUseCase = Depends(get_membership_use_case),
):
    """List organization members."""
    try:
        return use_case.list_members(organization_id, active_only=active_only)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{organization_id}/members/{user_id}")
def remove_organization_member(
    organization_id: UUID,
    user_id: UUID,
    removed_by: UUID = Query(..., description="User ID performing the removal"),
    use_case: MembershipUseCase = Depends(get_membership_use_case),
):
    """Remove a member from organization."""
    try:
        success = use_case.remove_member(organization_id, user_id, removed_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization",
            )
        return {"message": "Member removed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{organization_id}/members/{user_id}/role")
def change_member_role(
    organization_id: UUID,
    user_id: UUID,
    new_role_id: UUID = Query(..., description="New role ID"),
    changed_by: UUID = Query(..., description="User ID performing the change"),
    use_case: MembershipUseCase = Depends(get_membership_use_case),
):
    """Change member's role in organization."""
    try:
        success = use_case.change_member_role(organization_id, user_id, new_role_id, changed_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization",
            )
        return {"message": "Member role updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))