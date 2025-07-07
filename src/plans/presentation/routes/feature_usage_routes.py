from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from ..dependencies import get_feature_usage_use_case
from ...application.use_cases.feature_usage_use_cases import FeatureUsageUseCase

router = APIRouter(prefix="/feature-usage", tags=["Feature Usage"])


@router.post("/track")
def track_feature_usage(
    organization_id: UUID,
    feature_name: str,
    amount: int = Query(1, ge=1, description="Amount of usage to track"),
    metadata: Optional[Dict[str, Any]] = None,
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Track feature usage for an organization."""
    try:
        return use_case.track_feature_usage(
            organization_id=organization_id,
            feature_name=feature_name,
            amount=amount,
            metadata=metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}/summary")
def get_organization_usage_summary(
    organization_id: UUID,
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get comprehensive usage summary for an organization."""
    try:
        return use_case.get_organization_usage_summary(organization_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}/features/{feature_name}")
def get_feature_usage_details(
    organization_id: UUID,
    feature_name: str,
    period: str = Query("monthly", description="Usage period: hourly, daily, weekly, monthly"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get detailed usage information for a specific feature."""
    try:
        from ...domain.entities.feature_usage import UsagePeriod
        period_enum = UsagePeriod(period.upper())
        
        usage = use_case.get_feature_usage_details(
            organization_id=organization_id,
            feature_name=feature_name,
            period=period_enum,
        )
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usage data not found",
            )
        return usage
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/organizations/{organization_id}/check-access")
def check_feature_access(
    organization_id: UUID,
    feature_name: str,
    requested_amount: int = Query(1, ge=1, description="Amount to check access for"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Check if organization can use a feature."""
    try:
        return use_case.check_feature_access(
            organization_id=organization_id,
            feature_name=feature_name,
            requested_amount=requested_amount,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}/analytics/{feature_name}")
def get_usage_analytics(
    organization_id: UUID,
    feature_name: str,
    periods: int = Query(12, ge=1, le=24, description="Number of periods to analyze"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get usage analytics and trends for a feature."""
    try:
        return use_case.get_usage_analytics(
            organization_id=organization_id,
            feature_name=feature_name,
            periods=periods,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}/history")
def get_feature_usage_history(
    organization_id: UUID,
    feature_name: Optional[str] = Query(None, description="Filter by feature name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get historical usage data for an organization."""
    try:
        period_start = None
        period_end = None
        
        if start_date:
            period_start = datetime.fromisoformat(start_date)
        if end_date:
            period_end = datetime.fromisoformat(end_date)
            
        return use_case.get_feature_usage_history(
            organization_id=organization_id,
            feature_name=feature_name,
            period_start=period_start,
            period_end=period_end,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/organizations/{organization_id}/reset-usage")
def reset_feature_usage(
    organization_id: UUID,
    feature_name: str,
    period: str = Query("monthly", description="Usage period to reset"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Reset usage for a specific feature and period."""
    try:
        from ...domain.entities.feature_usage import UsagePeriod
        period_enum = UsagePeriod(period.upper())
        
        return use_case.reset_feature_usage(
            organization_id=organization_id,
            feature_name=feature_name,
            period=period_enum,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/near-limits")
def get_organizations_near_limits(
    threshold_percent: float = Query(0.8, ge=0.1, le=1.0, description="Threshold percentage"),
    feature_name: Optional[str] = Query(None, description="Filter by feature name"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get organizations approaching their usage limits."""
    try:
        return use_case.get_organizations_near_limits(
            threshold_percent=threshold_percent,
            feature_name=feature_name,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/create-record")
def create_usage_record(
    organization_id: UUID,
    feature_name: str,
    usage_period: str,
    limit_value: int,
    current_usage: int = Query(0, ge=0, description="Initial usage amount"),
    metadata: Optional[Dict[str, Any]] = None,
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Create a new usage record."""
    try:
        from ...domain.entities.feature_usage import UsagePeriod
        period_enum = UsagePeriod(usage_period.upper())
        
        return use_case.create_usage_record(
            organization_id=organization_id,
            feature_name=feature_name,
            usage_period=period_enum,
            limit_value=limit_value,
            current_usage=current_usage,
            metadata=metadata,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/organizations/{organization_id}/limits/{feature_name}")
def update_usage_limit(
    organization_id: UUID,
    feature_name: str,
    new_limit: int = Query(..., ge=1, description="New limit value"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Update the usage limit for a feature."""
    try:
        return use_case.update_usage_limit(
            organization_id=organization_id,
            feature_name=feature_name,
            new_limit=new_limit,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/features/{feature_name}/cross-organization")
def get_feature_usage_across_organizations(
    feature_name: str,
    period: str = Query("monthly", description="Usage period"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Get usage statistics for a feature across all organizations."""
    try:
        from ...domain.entities.feature_usage import UsagePeriod
        period_enum = UsagePeriod(period.upper())
        
        return use_case.get_feature_usage_across_organizations(
            feature_name=feature_name,
            period=period_enum,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/cleanup")
def cleanup_old_usage_records(
    older_than_days: int = Query(365, ge=30, le=3650, description="Delete records older than days"),
    use_case: FeatureUsageUseCase = Depends(get_feature_usage_use_case),
):
    """Clean up old usage records."""
    try:
        return use_case.cleanup_old_usage_records(older_than_days=older_than_days)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))