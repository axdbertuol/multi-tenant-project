from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..dependencies import get_plan_resource_limit_use_case
from ...application.use_cases.plan_resource_limit_use_cases import PlanResourceLimitUseCase

router = APIRouter(prefix="/plan-resource-limits", tags=["Plan Resource Limits"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_limit(
    resource_id: UUID,
    limit_type: str,
    limit_value: int = Query(..., ge=1, description="Limit value"),
    period: str = Query(..., description="Period: hourly, daily, weekly, monthly, concurrent"),
    is_hard_limit: bool = Query(True, description="Whether this is a hard limit"),
    metadata: Optional[Dict[str, Any]] = None,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Create a new plan resource limit."""
    try:
        return use_case.create_limit(
            resource_id=resource_id,
            limit_type=limit_type,
            limit_value=limit_value,
            period=period,
            is_hard_limit=is_hard_limit,
            metadata=metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{limit_id}")
def get_limit_by_id(
    limit_id: UUID,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Get a plan resource limit by ID."""
    try:
        limit = use_case.get_limit_by_id(limit_id)
        if not limit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Limit not found",
            )
        return limit
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{limit_id}")
def update_limit(
    limit_id: UUID,
    limit_value: Optional[int] = Query(None, ge=1, description="New limit value"),
    period: Optional[str] = Query(None, description="New period"),
    is_hard_limit: Optional[bool] = Query(None, description="Whether this is a hard limit"),
    is_active: Optional[bool] = Query(None, description="Whether limit is active"),
    metadata: Optional[Dict[str, Any]] = None,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Update an existing plan resource limit."""
    try:
        return use_case.update_limit(
            limit_id=limit_id,
            limit_value=limit_value,
            period=period,
            is_hard_limit=is_hard_limit,
            is_active=is_active,
            metadata=metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate-configuration")
def validate_limit_configuration(
    resource_id: UUID,
    limit_type: str,
    limit_value: int = Query(..., ge=1, description="Limit value to validate"),
    period: str = Query(..., description="Period to validate"),
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Validate limit configuration for a resource."""
    try:
        return use_case.validate_limit_configuration(
            resource_id=resource_id,
            limit_type=limit_type,
            limit_value=limit_value,
            period=period,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}")
def get_resource_limits(
    resource_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Get all limits for a specific resource."""
    try:
        return use_case.get_resource_limits(
            resource_id=resource_id,
            is_active=is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/effective-limits")
def calculate_effective_limits(
    resource_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID for context"),
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Calculate effective limits considering plan and organization overrides."""
    try:
        return use_case.calculate_effective_limits(
            resource_id=resource_id,
            organization_id=organization_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/usage-patterns")
def analyze_limit_usage_patterns(
    resource_id: UUID,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Analyze usage patterns against limits for a resource."""
    try:
        return use_case.analyze_limit_usage_patterns(resource_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/optimization-suggestions")
def get_limit_optimization_suggestions(
    resource_id: UUID,
    usage_data: Optional[Dict[str, Any]] = None,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Get optimization suggestions for resource limits."""
    try:
        return use_case.get_limit_optimization_suggestions(
            resource_id=resource_id,
            usage_data=usage_data,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resources/{resource_id}/validate-compatibility")
def validate_limit_compatibility(
    resource_id: UUID,
    limit_configurations: List[Dict[str, Any]],
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Validate compatibility between multiple limit configurations."""
    try:
        return use_case.validate_limit_compatibility(
            resource_id=resource_id,
            limit_configurations=limit_configurations,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/violation-history")
def get_limit_violation_history(
    resource_id: UUID,
    limit_type: Optional[str] = Query(None, description="Filter by limit type"),
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Get history of limit violations for a resource."""
    try:
        return use_case.get_limit_violation_history(
            resource_id=resource_id,
            limit_type=limit_type,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{limit_id}")
def delete_limit(
    limit_id: UUID,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Delete a plan resource limit."""
    try:
        return use_case.delete_limit(limit_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{limit_id}/activate")
def activate_limit(
    limit_id: UUID,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Activate a plan resource limit."""
    try:
        return use_case.activate_limit(limit_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{limit_id}/deactivate")
def deactivate_limit(
    limit_id: UUID,
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Deactivate a plan resource limit."""
    try:
        return use_case.deactivate_limit(limit_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/resources/{resource_id}/bulk-update")
def bulk_update_limits(
    resource_id: UUID,
    limit_updates: List[Dict[str, Any]],
    use_case: PlanResourceLimitUseCase = Depends(get_plan_resource_limit_use_case),
):
    """Bulk update multiple limits for a resource."""
    try:
        return use_case.bulk_update_limits(
            resource_id=resource_id,
            limit_updates=limit_updates,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))