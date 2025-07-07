from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any, List
from uuid import UUID

from ..dependencies import get_application_instance_use_case
from ...application.use_cases.application_instance_use_cases import ApplicationInstanceUseCase

router = APIRouter(prefix="/application-instances", tags=["Application Instances"])


@router.post("/provision", status_code=status.HTTP_201_CREATED)
def provision_instance(
    plan_resource_id: UUID,
    organization_id: UUID,
    instance_name: str,
    owner_id: UUID,
    initial_configuration: Optional[Dict[str, Any]] = None,
    custom_limits: Optional[Dict[str, int]] = None,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Provision a new application instance."""
    try:
        return use_case.provision_instance(
            plan_resource_id=plan_resource_id,
            organization_id=organization_id,
            instance_name=instance_name,
            owner_id=owner_id,
            initial_configuration=initial_configuration,
            custom_limits=custom_limits,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{instance_id}")
def get_instance_by_id(
    instance_id: UUID,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Get application instance by ID."""
    try:
        instance = use_case.get_instance_by_id(instance_id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instance not found",
            )
        return instance
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{instance_id}/configuration")
def update_instance_configuration(
    instance_id: UUID,
    new_configuration: Dict[str, Any],
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Update instance configuration."""
    try:
        return use_case.update_instance_configuration(
            instance_id=instance_id,
            new_configuration=new_configuration,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{instance_id}/api-keys")
def generate_api_keys(
    instance_id: UUID,
    key_types: List[str],
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Generate API keys for an instance."""
    try:
        return use_case.generate_api_keys(
            instance_id=instance_id,
            key_types=key_types,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{instance_id}/health")
def analyze_instance_health(
    instance_id: UUID,
    usage_metrics: Optional[Dict[str, Any]] = None,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Analyze instance health and performance."""
    try:
        return use_case.analyze_instance_health(
            instance_id=instance_id,
            usage_metrics=usage_metrics,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{instance_id}/optimization-suggestions")
def get_configuration_optimization_suggestions(
    instance_id: UUID,
    usage_patterns: Optional[Dict[str, Any]] = None,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Get optimization suggestions for instance configuration."""
    try:
        return use_case.get_configuration_optimization_suggestions(
            instance_id=instance_id,
            usage_patterns=usage_patterns,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{instance_id}/validate-migration")
def validate_instance_migration(
    instance_id: UUID,
    target_plan_resource_id: UUID,
    target_configuration: Dict[str, Any],
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Validate if instance can be migrated to different resource configuration."""
    try:
        return use_case.validate_instance_migration(
            instance_id=instance_id,
            target_plan_resource_id=target_plan_resource_id,
            target_configuration=target_configuration,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{instance_id}/limits/{limit_key}")
def set_custom_limit(
    instance_id: UUID,
    limit_key: str,
    limit_value: int = Query(..., ge=1, description="Limit value to set"),
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Set a custom limit for an instance."""
    try:
        return use_case.set_custom_limit(
            instance_id=instance_id,
            limit_key=limit_key,
            limit_value=limit_value,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{instance_id}/limits/{limit_key}")
def remove_custom_limit(
    instance_id: UUID,
    limit_key: str,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Remove a custom limit from an instance."""
    try:
        return use_case.remove_custom_limit(
            instance_id=instance_id,
            limit_key=limit_key,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{instance_id}/effective-limits")
def get_effective_limits(
    instance_id: UUID,
    organization_id: UUID = Query(..., description="Organization ID for context"),
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Get effective limits for an instance considering all overrides."""
    try:
        return use_case.get_effective_limits(
            instance_id=instance_id,
            organization_id=organization_id,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{instance_id}/deactivate")
def deactivate_instance(
    instance_id: UUID,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Deactivate an application instance."""
    try:
        return use_case.deactivate_instance(instance_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{instance_id}/reactivate")
def reactivate_instance(
    instance_id: UUID,
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """Reactivate an application instance."""
    try:
        return use_case.reactivate_instance(instance_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}")
def list_organization_instances(
    organization_id: UUID,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    use_case: ApplicationInstanceUseCase = Depends(get_application_instance_use_case),
):
    """List all instances for an organization."""
    try:
        return use_case.list_organization_instances(
            organization_id=organization_id,
            is_active=is_active,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))