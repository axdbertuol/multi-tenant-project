from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from ..application.dtos.organization_dto import (
    OrganizationCreateDTO,
    OrganizationUpdateDTO,
    OrganizationSettingsUpdateDTO,
    OrganizationResponseDTO,
    OrganizationListResponseDTO,
    OrganizationDetailResponseDTO,
)
from ..application.use_cases.organization_use_cases import OrganizationUseCase
from .dependencies import get_organization_use_case


organization_router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationOwnershipTransferRequest(BaseModel):
    new_owner_id: UUID


@organization_router.post(
    "/",
    response_model=OrganizationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization. The creator becomes the owner.",
)
def create_organization(
    organization_data: OrganizationCreateDTO,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationResponseDTO:
    try:
        return use_case.create_organization(organization_data, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization",
        )


@organization_router.get(
    "/",
    response_model=OrganizationListResponseDTO,
    summary="List Organizations",
    description="Get a paginated list of organizations.",
)
def list_organizations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of organizations per page"),
    active_only: bool = Query(True, description="Filter for active organizations only"),
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationListResponseDTO:
    try:
        return use_case.list_organizations(page, page_size, active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list organizations",
        )


@organization_router.get(
    "/{organization_id}",
    response_model=OrganizationResponseDTO,
    summary="Get Organization",
    description="Get organization details by ID.",
)
def get_organization(
    organization_id: UUID,
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationResponseDTO:
    try:
        organization = use_case.get_organization_by_id(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return organization
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization",
        )


@organization_router.get(
    "/{organization_id}/detail",
    response_model=OrganizationDetailResponseDTO,
    summary="Get Organization Detail",
    description="Get detailed organization information including members.",
)
def get_organization_detail(
    organization_id: UUID,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationDetailResponseDTO:
    try:
        organization = use_case.get_organization_detail(organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return organization
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get organization detail",
        )


@organization_router.put(
    "/{organization_id}",
    response_model=OrganizationResponseDTO,
    summary="Update Organization",
    description="Update organization information.",
)
def update_organization(
    organization_id: UUID,
    update_data: OrganizationUpdateDTO,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationResponseDTO:
    try:
        return use_case.update_organization(organization_id, update_data, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization",
        )


@organization_router.put(
    "/{organization_id}/settings",
    response_model=OrganizationResponseDTO,
    summary="Update Organization Settings",
    description="Update organization settings.",
)
def update_organization_settings(
    organization_id: UUID,
    settings_data: OrganizationSettingsUpdateDTO,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationResponseDTO:
    try:
        return use_case.update_organization_settings(
            organization_id, settings_data, current_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization settings",
        )


@organization_router.post(
    "/{organization_id}/transfer-ownership",
    response_model=OrganizationResponseDTO,
    summary="Transfer Ownership",
    description="Transfer organization ownership to another user.",
)
def transfer_ownership(
    organization_id: UUID,
    transfer_request: OrganizationOwnershipTransferRequest,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> OrganizationResponseDTO:
    try:
        return use_case.transfer_ownership(
            organization_id, current_user_id, transfer_request.new_owner_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transfer ownership",
        )


@organization_router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate Organization",
    description="Deactivate an organization.",
)
def deactivate_organization(
    organization_id: UUID,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
):
    try:
        use_case.deactivate_organization(organization_id, current_user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate organization",
        )


@organization_router.get(
    "/user/{user_id}",
    response_model=List[OrganizationResponseDTO],
    summary="Get User Organizations",
    description="Get all organizations where a user is a member.",
)
def get_user_organizations(
    user_id: UUID,
    current_user_id: UUID = Depends(),  # This would come from auth middleware
    use_case: OrganizationUseCase = Depends(get_organization_use_case),
) -> List[OrganizationResponseDTO]:
    try:
        return use_case.get_user_organizations(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user organizations",
        )