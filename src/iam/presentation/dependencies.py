from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ..application.use_cases.authentication_use_cases import AuthenticationUseCase
from ..application.use_cases.user_use_cases import UserUseCase
from ..application.use_cases.session_use_cases import SessionUseCase
from ..application.use_cases.authorization_use_cases import AuthorizationUseCase
from ..application.use_cases.role_use_cases import RoleUseCase
from ..application.use_cases.permission_use_cases import PermissionUseCase
from ..application.use_cases.policy_use_cases import PolicyUseCase
from ..application.use_cases.organization_use_cases import OrganizationUseCase
from ..application.use_cases.membership_use_cases import MembershipUseCase
from ..infrastructure.iam_unit_of_work import IAMUnitOfWork


def get_iam_uow(db: Session = Depends(get_db)) -> IAMUnitOfWork:
    """Obtém uma instância de IAMUnitOfWork com todos os repositórios do contexto IAM."""
    return IAMUnitOfWork(
        db, ["user", "user_session", "organization", "user_organization_role", "role", "permission", "policy", "resource"]
    )


def get_auth_use_case(
    uow: IAMUnitOfWork = Depends(get_iam_uow),
) -> AuthenticationUseCase:
    """Obtém AuthenticationUseCase com a dependência UnitOfWork apropriada."""
    return AuthenticationUseCase(uow)


def get_user_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> UserUseCase:
    """Obtém UserUseCase com a dependência UnitOfWork apropriada."""
    return UserUseCase(uow)


def get_session_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> SessionUseCase:
    """Obtém SessionUseCase com a dependência UnitOfWork apropriada."""
    return SessionUseCase(uow)


def get_authorization_use_case(
    uow: IAMUnitOfWork = Depends(get_iam_uow),
) -> AuthorizationUseCase:
    """Obtém AuthorizationUseCase com a dependência UnitOfWork apropriada."""
    return AuthorizationUseCase(uow)


def get_role_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> RoleUseCase:
    """Obtém RoleUseCase com a dependência UnitOfWork apropriada."""
    return RoleUseCase(uow)


def get_permission_use_case(
    uow: IAMUnitOfWork = Depends(get_iam_uow),
) -> PermissionUseCase:
    """Obtém PermissionUseCase com a dependência UnitOfWork apropriada."""
    return PermissionUseCase(uow)


def get_policy_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> PolicyUseCase:
    """Obtém PolicyUseCase com a dependência UnitOfWork apropriada."""
    return PolicyUseCase(uow)


def get_organization_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> OrganizationUseCase:
    """Obtém OrganizationUseCase com a dependência UnitOfWork apropriada."""
    return OrganizationUseCase(uow)


def get_membership_use_case(uow: IAMUnitOfWork = Depends(get_iam_uow)) -> MembershipUseCase:
    """Obtém MembershipUseCase com a dependência UnitOfWork apropriada."""
    return MembershipUseCase(uow)
