from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID

from ..dependencies import get_plan_resource_use_case
from ...application.dtos.plan_resource_dto import (
    PlanResourceCreateDTO,
    PlanResourceUpdateDTO,
    PlanResourceResponseDTO,
    PlanResourceListResponseDTO,
    PlanResourceTestDTO,
    PlanResourceTestResponseDTO,
    PlanResourceUsageDTO,
    PlanResourceUsageResponseDTO,
)
from ...application.use_cases.plan_resource_use_cases import PlanResourceUseCase

router = APIRouter(prefix="/plan-resources", tags=["Plan Resources"])


@router.post(
    "/", response_model=PlanResourceResponseDTO, status_code=status.HTTP_201_CREATED
)
def create_plan_resource(
    dto: PlanResourceCreateDTO,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Create a new plan resource."""
    try:
        return use_case.create_plan_resource(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{resource_id}", response_model=PlanResourceResponseDTO)
def get_plan_resource_by_id(
    resource_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get plan resource by ID."""
    try:
        resource = use_case.get_resource_by_id(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PlanResourceListResponseDTO)
def list_plan_resources(
    plan_id: Optional[UUID] = Query(None, description="Filter by plan ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """List plan resources with pagination and filters."""
    try:
        return use_case.list_plan_resources(
            plan_id=plan_id,
            resource_type=resource_type,
            is_enabled=is_enabled,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/plan/{plan_id}")
def get_plan_resources(
    plan_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get all resources for a specific plan."""
    try:
        return use_case.get_plan_resources(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{resource_id}", response_model=PlanResourceResponseDTO)
def update_plan_resource(
    resource_id: UUID,
    dto: PlanResourceUpdateDTO,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Update plan resource configuration."""
    try:
        resource = use_case.update_plan_resource(resource_id, dto)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_id}/enable", response_model=PlanResourceResponseDTO)
def enable_plan_resource(
    resource_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Enable a plan resource."""
    try:
        resource = use_case.enable_resource(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_id}/disable", response_model=PlanResourceResponseDTO)
def disable_plan_resource(
    resource_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Disable a plan resource."""
    try:
        resource = use_case.disable_resource(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/test", response_model=PlanResourceTestResponseDTO)
def test_resource_configuration(
    dto: PlanResourceTestDTO,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Test a plan resource configuration."""
    try:
        return use_case.test_resource_configuration(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/usage", status_code=status.HTTP_201_CREATED)
def record_resource_usage(
    dto: PlanResourceUsageDTO,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Record usage of a plan resource."""
    try:
        success = use_case.record_resource_usage(dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to record usage",
            )
        return {"message": "Usage recorded successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{resource_id}/usage", response_model=PlanResourceUsageResponseDTO)
def get_resource_usage(
    resource_id: UUID,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get usage statistics for a plan resource."""
    try:
        from datetime import datetime

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return use_case.get_resource_usage(resource_id, start_dt, end_dt)
    except ValueError as e:
        if "time data" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_id}/duplicate", response_model=PlanResourceResponseDTO)
def duplicate_resource(
    resource_id: UUID,
    target_plan_id: UUID = Query(..., description="Target plan ID"),
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Duplicate a resource to another plan."""
    try:
        resource = use_case.duplicate_resource(resource_id, target_plan_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{resource_id}")
def delete_plan_resource(
    resource_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Delete a plan resource."""
    try:
        success = use_case.delete_plan_resource(resource_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan resource not found",
            )
        return {"message": "Plan resource deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/types/{resource_type}/defaults")
def get_resource_type_defaults(
    resource_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get default configuration for a resource type."""
    try:
        from ...domain.entities.plan_resource import PlanResourceType
        from ...domain.services.plan_resource_service import PlanResourceService

        # Validate resource type
        try:
            resource_type_enum = PlanResourceType(resource_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource type: {resource_type}",
            )

        service = PlanResourceService()
        defaults = service.get_default_configuration(resource_type_enum)
        schema = service.get_configuration_schema(resource_type_enum)

        return {
            "resource_type": resource_type,
            "default_configuration": defaults,
            "configuration_schema": schema,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/types/{resource_type}/schema")
def get_resource_type_schema(
    resource_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get configuration schema for a resource type."""
    try:
        from ...domain.entities.plan_resource import PlanResourceType
        from ...domain.services.plan_resource_service import PlanResourceService

        # Validate resource type
        try:
            resource_type_enum = PlanResourceType(resource_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resource type: {resource_type}",
            )

        service = PlanResourceService()
        schema = service.get_configuration_schema(resource_type_enum)

        return {
            "resource_type": resource_type,
            "configuration_schema": schema,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
