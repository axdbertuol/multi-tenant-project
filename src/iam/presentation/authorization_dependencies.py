from fastapi import Depends
from sqlalchemy.orm import Session

from shared.infrastructure.database.connection import get_db
from ..infrastructure.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from ..infrastructure.repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from ..application.use_cases.role_use_cases import RoleUseCase
from ..application.use_cases.permission_use_cases import PermissionUseCase


def get_role_repository(db: Session = Depends(get_db)) -> SqlAlchemyRoleRepository:
    """Get role repository dependency."""
    return SqlAlchemyRoleRepository(db)


def get_permission_repository(
    db: Session = Depends(get_db),
) -> SqlAlchemyPermissionRepository:
    """Get permission repository dependency."""
    return SqlAlchemyPermissionRepository(db)


def get_role_use_case(
    role_repo: SqlAlchemyRoleRepository = Depends(get_role_repository),
    permission_repo: SqlAlchemyPermissionRepository = Depends(
        get_permission_repository
    ),
) -> RoleUseCase:
    """Get role use case dependency."""
    return RoleUseCase(role_repo, permission_repo)


def get_permission_use_case(
    permission_repo: SqlAlchemyPermissionRepository = Depends(
        get_permission_repository
    ),
) -> PermissionUseCase:
    """Get permission use case dependency."""
    return PermissionUseCase(permission_repo)
