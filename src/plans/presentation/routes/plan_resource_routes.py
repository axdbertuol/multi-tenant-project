from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..dependencies import get_plan_resource_use_case
from ...application.use_cases.plan_resource_use_cases import PlanResourceUseCase

router = APIRouter(prefix="/plan-resources", tags=["Plan Resources"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_resource(
    resource_type: str,
    name: str,
    category: str,
    created_by: UUID,
    description: Optional[str] = None,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Create a new plan resource."""
    try:
        # Convert category string to enum
        from ...domain.entities.plan_resource import ResourceCategory
        category_enum = ResourceCategory(category)
        
        return use_case.create_resource(
            resource_type=resource_type,
            name=name,
            category=category_enum,
            created_by=created_by,
            description=description,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{resource_id}")
def get_resource_by_id(
    resource_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get plan resource by ID."""
    try:
        resource = use_case.get_resource_by_id(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/")
def list_resources(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """List plan resources with pagination and filters."""
    try:
        category_enum = None
        if category:
            from ...domain.entities.plan_resource import ResourceCategory
            category_enum = ResourceCategory(category)
            
        return use_case.list_resources(
            category=category_enum,
            is_active=is_active,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{resource_id}")
def update_resource(
    resource_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Update an existing plan resource."""
    try:
        category_enum = None
        if category:
            from ...domain.entities.plan_resource import ResourceCategory
            category_enum = ResourceCategory(category)
            
        resource = use_case.update_resource(
            resource_id=resource_id,
            name=name,
            description=description,
            category=category_enum,
            is_active=is_active,
        )
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_type}/validate-compatibility")
def validate_resource_compatibility(
    resource_type: str,
    plan_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Validate if a resource type is compatible with a plan type."""
    try:
        return use_case.validate_resource_compatibility(resource_type, plan_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/recommendations/{category}")
def get_recommended_resources(
    category: str,
    plan_type: str = Query(..., description="Plan type to get recommendations for"),
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get recommended resources for a category and plan type."""
    try:
        from ...domain.entities.plan_resource import ResourceCategory
        category_enum = ResourceCategory(category)
        
        return use_case.get_recommended_resources(category_enum, plan_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_type}/analyze-dependencies")
def analyze_resource_dependencies(
    resource_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Analyze dependencies and conflicts for a resource."""
    try:
        return use_case.analyze_resource_dependencies(resource_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_type}/validate-configuration")
def validate_resource_configuration(
    resource_type: str,
    configuration: Dict[str, Any],
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Validate resource configuration."""
    try:
        return use_case.validate_resource_configuration(resource_type, configuration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{resource_type}/usage-patterns")
def get_resource_usage_patterns(
    resource_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get usage patterns for a resource type."""
    try:
        return use_case.get_resource_usage_patterns(resource_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/plans/{plan_id}/optimization-suggestions")
def get_plan_resource_optimization_suggestions(
    plan_id: UUID,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get optimization suggestions for plan resources."""
    try:
        return use_case.get_plan_resource_optimization_suggestions(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{resource_type}/test-configuration")
def test_resource_configuration(
    resource_type: str,
    configuration: Dict[str, Any],
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Test a resource configuration to ensure it works properly."""
    try:
        return use_case.test_resource_configuration(resource_type, configuration)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{resource_type}/health-status")
def get_resource_health_status(
    resource_type: str,
    use_case: PlanResourceUseCase = Depends(get_plan_resource_use_case),
):
    """Get health status for a specific resource type across all plans."""
    try:
        return use_case.get_resource_health_status(resource_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))