from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID

from ..dependencies import get_plan_use_case
from ...application.dtos.plan_dto import (
    PlanCreateDTO,
    PlanUpdateDTO,
    PlanResponseDTO,
    PlanListResponseDTO,
)
from ...application.use_cases.plan_use_cases import PlanUseCase

router = APIRouter(prefix="/plans", tags=["Plans"])


@router.post("/", response_model=PlanResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_plan(
    dto: PlanCreateDTO,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Create a new plan."""
    try:
        return use_case.create_plan(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{plan_id}", response_model=PlanResponseDTO)
async def get_plan_by_id(
    plan_id: UUID,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Get plan by ID."""
    try:
        plan = use_case.get_plan_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PlanListResponseDTO)
async def list_plans(
    plan_type: Optional[str] = Query(None, description="Filter by plan type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """List plans with pagination and filters."""
    try:
        return use_case.list_plans(
            plan_type=plan_type,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{plan_id}", response_model=PlanResponseDTO)
async def update_plan(
    plan_id: UUID,
    dto: PlanUpdateDTO,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Update plan information."""
    try:
        plan = use_case.update_plan(plan_id, dto)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{plan_id}/activate", response_model=PlanResponseDTO)
async def activate_plan(
    plan_id: UUID,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Activate a plan."""
    try:
        plan = use_case.activate_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{plan_id}/deactivate", response_model=PlanResponseDTO)
async def deactivate_plan(
    plan_id: UUID,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Deactivate a plan."""
    try:
        plan = use_case.deactivate_plan(plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: UUID,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Delete a plan."""
    try:
        success = use_case.delete_plan(plan_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return {"message": "Plan deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{plan_id}/pricing")
async def get_plan_pricing(
    plan_id: UUID,
    billing_cycle: Optional[str] = Query("monthly", description="Billing cycle"),
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Get plan pricing information."""
    try:
        pricing = use_case.get_plan_pricing(plan_id, billing_cycle)
        if not pricing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return pricing
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{plan_id}/features")
async def get_plan_features(
    plan_id: UUID,
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Get plan features and limits."""
    try:
        features = use_case.get_plan_features(plan_id)
        if not features:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return features
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{plan_id}/duplicate", response_model=PlanResponseDTO)
async def duplicate_plan(
    plan_id: UUID,
    new_name: str = Query(..., description="Name for the duplicated plan"),
    use_case: PlanUseCase = Depends(get_plan_use_case),
):
    """Duplicate an existing plan."""
    try:
        plan = use_case.duplicate_plan(plan_id, new_name)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))