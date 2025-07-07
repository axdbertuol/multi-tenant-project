from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from ..dependencies import get_usage_tracking_use_case
from ...application.use_cases.usage_tracking_use_cases import UsageTrackingUseCase

router = APIRouter(prefix="/usage-tracking", tags=["Usage Tracking"])


@router.get("/organizations/{organization_id}/dashboard")
def get_organization_analytics_dashboard(
    organization_id: UUID,
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Get comprehensive analytics dashboard for an organization."""
    try:
        return use_case.get_organization_analytics_dashboard(organization_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organizations/{organization_id}/features/{feature_name}/trends")
def get_feature_usage_trends(
    organization_id: UUID,
    feature_name: str,
    periods: int = Query(12, ge=1, le=24, description="Number of periods to analyze"),
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Get detailed usage trends for a specific feature."""
    try:
        return use_case.get_feature_usage_trends(
            organization_id=organization_id,
            feature_name=feature_name,
            periods=periods,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/system-wide/analytics")
def get_system_wide_analytics(
    feature_name: Optional[str] = Query(None, description="Filter by feature name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Get system-wide usage analytics across all organizations."""
    try:
        return use_case.get_system_wide_analytics(
            feature_name=feature_name,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/organizations/{organization_id}/reports/generate")
def generate_usage_report(
    organization_id: UUID,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Generate comprehensive usage report for a date range."""
    try:
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        return use_case.generate_usage_report(
            organization_id=organization_id,
            start_date=start_datetime,
            end_date=end_datetime,
            include_trends=include_trends,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/monthly-reset/bulk")
def reset_monthly_usage_bulk(
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Reset monthly usage for all organizations (scheduled operation)."""
    try:
        return use_case.reset_monthly_usage_bulk()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/organizations/{organization_id}/utilization-analysis")
def get_limit_utilization_analysis(
    organization_id: UUID,
    use_case: UsageTrackingUseCase = Depends(get_usage_tracking_use_case),
):
    """Analyze limit utilization patterns for an organization."""
    try:
        return use_case.get_limit_utilization_analysis(organization_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))