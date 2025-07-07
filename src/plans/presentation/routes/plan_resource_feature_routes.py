from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..dependencies import get_plan_resource_feature_use_case
from ...application.use_cases.plan_resource_feature_use_cases import PlanResourceFeatureUseCase

router = APIRouter(prefix="/plan-resource-features", tags=["Plan Resource Features"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_feature(
    resource_id: UUID,
    feature_key: str,
    feature_name: str,
    description: Optional[str] = None,
    is_default: bool = Query(False, description="Set as default feature"),
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Create a new plan resource feature."""
    try:
        return use_case.create_feature(
            resource_id=resource_id,
            feature_key=feature_key,
            feature_name=feature_name,
            description=description,
            is_default=is_default,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{feature_id}")
def get_feature_by_id(
    feature_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Get a plan resource feature by ID."""
    try:
        feature = use_case.get_feature_by_id(feature_id)
        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature not found",
            )
        return feature
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{feature_id}")
def update_feature(
    feature_id: UUID,
    feature_name: Optional[str] = None,
    description: Optional[str] = None,
    is_default: Optional[bool] = None,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Update an existing plan resource feature."""
    try:
        return use_case.update_feature(
            feature_id=feature_id,
            feature_name=feature_name,
            description=description,
            is_default=is_default,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/validate-dependencies")
def validate_feature_dependencies(
    feature_key: str,
    resource_category: str,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Validate feature dependencies and conflicts."""
    try:
        from ...domain.entities.plan_resource import ResourceCategory
        category_enum = ResourceCategory(resource_category)
        
        return use_case.validate_feature_dependencies(feature_key, category_enum)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/recommendations")
def get_recommended_features(
    resource_type: str = Query(..., description="Resource type"),
    resource_category: str = Query(..., description="Resource category"),
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Get recommended features for a resource type."""
    try:
        from ...domain.entities.plan_resource import ResourceCategory
        category_enum = ResourceCategory(resource_category)
        
        return use_case.get_recommended_features(resource_type, category_enum)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{feature_id}/validate-configuration")
def validate_feature_configuration(
    feature_id: UUID,
    configuration: Dict[str, Any],
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Validate feature configuration."""
    try:
        return use_case.validate_feature_configuration(feature_id, configuration)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/features/{feature_key}/usage-patterns")
def analyze_feature_usage_patterns(
    feature_key: str,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Analyze usage patterns for a specific feature."""
    try:
        return use_case.analyze_feature_usage_patterns(feature_key)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/optimization-suggestions")
def get_feature_optimization_suggestions(
    resource_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Get optimization suggestions for resource features."""
    try:
        return use_case.get_feature_optimization_suggestions(resource_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}/compatibility-matrix")
def get_feature_compatibility_matrix(
    resource_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Get compatibility matrix for features in a resource."""
    try:
        return use_case.get_feature_compatibility_matrix(resource_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/resources/{resource_id}")
def list_resource_features(
    resource_id: UUID,
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """List all features for a resource."""
    try:
        return use_case.list_resource_features(
            resource_id=resource_id,
            is_default=is_default,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{feature_id}")
def delete_feature(
    feature_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Delete a plan resource feature."""
    try:
        return use_case.delete_feature(feature_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{feature_id}/set-default")
def set_feature_as_default(
    feature_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Set a feature as default for the resource."""
    try:
        return use_case.set_feature_as_default(feature_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{feature_id}/unset-default")
def unset_feature_as_default(
    feature_id: UUID,
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Unset a feature as default for the resource."""
    try:
        return use_case.unset_feature_as_default(feature_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/resources/{resource_id}/bulk-update")
def bulk_update_features(
    resource_id: UUID,
    feature_updates: List[Dict[str, Any]],
    use_case: PlanResourceFeatureUseCase = Depends(get_plan_resource_feature_use_case),
):
    """Bulk update multiple features for a resource."""
    try:
        return use_case.bulk_update_features(
            resource_id=resource_id,
            feature_updates=feature_updates,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))