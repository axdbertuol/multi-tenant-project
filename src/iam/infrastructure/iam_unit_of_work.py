from shared.infrastructure.repositories.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from .repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from .repositories.sqlalchemy_user_session_repository import (
    SqlAlchemyUserSessionRepository,
)
from .repositories.sqlalchemy_role_repository import SqlAlchemyRoleRepository
from .repositories.sqlalchemy_permission_repository import (
    SqlAlchemyPermissionRepository,
)
from .repositories.sqlalchemy_policy_repository import SqlAlchemyPolicyRepository
from .repositories.sqlalchemy_organization_repository import SqlAlchemyOrganizationRepository
from .repositories.sqlalchemy_user_organization_role_repository import SqlAlchemyUserOrganizationRoleRepository
from .repositories.sqlalchemy_authorization_subject_repository import SqlAlchemyAuthorizationSubjectRepository

from sqlalchemy.orm import Session


class IAMUnitOfWork(SQLAlchemyUnitOfWork):
    """Implementação da Unidade de Trabalho para o contexto de IAM."""

    _repositories = {}

    def __init__(self, session: Session, repositories: list[str]):
        # User-related repositories
        if "user" in repositories:
            self._repositories.update({"user": SqlAlchemyUserRepository(session)})
        if "user_session" in repositories:
            self._repositories.update(
                {"user_session": SqlAlchemyUserSessionRepository(session)}
            )

        # Organization-related repositories
        if "organization" in repositories:
            self._repositories.update({"organization": SqlAlchemyOrganizationRepository(session)})
        if "user_organization_role" in repositories:
            self._repositories.update(
                {"user_organization_role": SqlAlchemyUserOrganizationRoleRepository(session)}
            )

        # Authorization-related repositories
        if "role" in repositories:
            self._repositories.update({"role": SqlAlchemyRoleRepository(session)})
        if "permission" in repositories:
            self._repositories.update(
                {"permission": SqlAlchemyPermissionRepository(session)}
            )
        if "policy" in repositories:
            self._repositories.update({"policy": SqlAlchemyPolicyRepository(session)})
        if "authorization_subject" in repositories:
            self._repositories.update(
                {"authorization_subject": SqlAlchemyAuthorizationSubjectRepository(session)}
            )

        super().__init__(session)

    def get_repository(self, name):
        return self._repositories.get(name)
