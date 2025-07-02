from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ..application.use_cases.organization_use_cases import OrganizationUseCase
from ..application.use_cases.membership_use_cases import MembershipUseCase
from ..infrastructure.organization_unit_of_work import OrganizationUnitOfWork


def get_organization_uow(db: Session = Depends(get_db)) -> OrganizationUnitOfWork:
    """Get an OrganizationUnitOfWork instance with organization and user_organization_role repositories."""
    return OrganizationUnitOfWork(db, ["organization", "user_organization_role"])


def get_organization_use_case(
    uow: OrganizationUnitOfWork = Depends(get_organization_uow),
) -> OrganizationUseCase:
    """Get organization use case with proper UnitOfWork dependency."""
    return OrganizationUseCase(uow)


def get_membership_use_case(
    uow: OrganizationUnitOfWork = Depends(get_organization_uow),
) -> MembershipUseCase:
    """Get membership use case with proper UnitOfWork dependency."""
    return MembershipUseCase(uow)
