from shared.infrastructure.repositories.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from sqlalchemy.orm import Session
from organization.infrastructure.repositories.sqlalchemy_organization_repository import (
    SqlAlchemyOrganizationRepository,
)
from organization.infrastructure.repositories.sqlalchemy_user_organization_role_repository import (
    SqlAlchemyUserOrganizationRoleRepository,
)


class OrganizationUnitOfWork(SQLAlchemyUnitOfWork):
    _repositories = {}

    def __init__(self, session: Session, repositories: list[str]):
        if "organization" in repositories:
            self._repositories.update({"organization": SqlAlchemyOrganizationRepository(session)})
        if "user_organization_role" in repositories:
            self._repositories.update(
                {"user_organization_role": SqlAlchemyUserOrganizationRoleRepository(session)}
            )

        super().__init__(session)