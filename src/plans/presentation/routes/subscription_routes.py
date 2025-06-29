from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID

from ..dependencies import get_subscription_use_case
from ...application.dtos.subscription_dto import (
    SubscriptionCreateDTO,
    SubscriptionUpdateDTO,
    SubscriptionResponseDTO,
    SubscriptionListResponseDTO,
    SubscriptionUpgradeDTO,
    SubscriptionDowngradeDTO,
    SubscriptionCancellationDTO,
)
from ...application.use_cases.subscription_use_cases import SubscriptionUseCase

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=SubscriptionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    dto: SubscriptionCreateDTO,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Create a new subscription."""
    try:
        return use_case.create_subscription(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{subscription_id}", response_model=SubscriptionResponseDTO)
async def get_subscription_by_id(
    subscription_id: UUID,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Get subscription by ID."""
    try:
        subscription = use_case.get_subscription_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=SubscriptionListResponseDTO)
async def list_subscriptions(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    plan_id: Optional[UUID] = Query(None, description="Filter by plan"),
    status: Optional[str] = Query(None, description="Filter by status"),
    billing_cycle: Optional[str] = Query(None, description="Filter by billing cycle"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """List subscriptions with pagination and filters."""
    try:
        return use_case.list_subscriptions(
            organization_id=organization_id,
            plan_id=plan_id,
            status=status,
            billing_cycle=billing_cycle,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/organization/{organization_id}", response_model=SubscriptionResponseDTO)
async def get_organization_subscription(
    organization_id: UUID,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Get active subscription for an organization."""
    try:
        subscription = use_case.get_organization_subscription(organization_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found for organization",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{subscription_id}", response_model=SubscriptionResponseDTO)
async def update_subscription(
    subscription_id: UUID,
    dto: SubscriptionUpdateDTO,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Update subscription information."""
    try:
        subscription = use_case.update_subscription(subscription_id, dto)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/activate", response_model=SubscriptionResponseDTO)
async def activate_subscription(
    subscription_id: UUID,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Activate a subscription."""
    try:
        subscription = use_case.activate_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponseDTO)
async def cancel_subscription(
    subscription_id: UUID,
    dto: SubscriptionCancellationDTO,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Cancel a subscription."""
    try:
        subscription = use_case.cancel_subscription(subscription_id, dto)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/suspend", response_model=SubscriptionResponseDTO)
async def suspend_subscription(
    subscription_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for suspension"),
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Suspend a subscription."""
    try:
        subscription = use_case.suspend_subscription(subscription_id, reason)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/reactivate", response_model=SubscriptionResponseDTO)
async def reactivate_subscription(
    subscription_id: UUID,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Reactivate a suspended subscription."""
    try:
        subscription = use_case.reactivate_subscription(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/upgrade", response_model=SubscriptionResponseDTO)
async def upgrade_subscription(
    subscription_id: UUID,
    dto: SubscriptionUpgradeDTO,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Upgrade a subscription to a higher plan."""
    try:
        subscription = use_case.upgrade_subscription(subscription_id, dto)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/downgrade", response_model=SubscriptionResponseDTO)
async def downgrade_subscription(
    subscription_id: UUID,
    dto: SubscriptionDowngradeDTO,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Downgrade a subscription to a lower plan."""
    try:
        subscription = use_case.downgrade_subscription(subscription_id, dto)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{subscription_id}/extend")
async def extend_subscription(
    subscription_id: UUID,
    extension_days: int = Query(..., ge=1, le=3650, description="Days to extend subscription"),
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Extend subscription end date."""
    try:
        success = use_case.extend_subscription(subscription_id, extension_days)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return {"message": f"Subscription extended by {extension_days} days"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{subscription_id}/billing-history")
async def get_subscription_billing_history(
    subscription_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Get subscription billing history."""
    try:
        history = use_case.get_subscription_billing_history(
            subscription_id, page, page_size
        )
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return history
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{subscription_id}/usage")
async def get_subscription_usage(
    subscription_id: UUID,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Get subscription usage statistics."""
    try:
        usage = use_case.get_subscription_usage(subscription_id, start_date, end_date)
        if not usage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return usage
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: UUID,
    use_case: SubscriptionUseCase = Depends(get_subscription_use_case),
):
    """Delete a subscription (admin only)."""
    try:
        success = use_case.delete_subscription(subscription_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )
        return {"message": "Subscription deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))