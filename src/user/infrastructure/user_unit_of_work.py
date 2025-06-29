from shared.infrastructure.repositories.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from sqlalchemy.orm import Session
from user.infrastructure.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from user.infrastructure.repositories.sqlalchemy_user_session_repository import (
    SqlAlchemyUserSessionRepository,
)


class UserUnitOfWork(SQLAlchemyUnitOfWork):
    _repositories = {}

    def __init__(self, session: Session, repositories: list[str]):
        if "user" in repositories:
            self._repositories.update({"user": SqlAlchemyUserRepository(session)})
        if "user_session" in repositories:
            self._repositories.update(
                {"user_session": SqlAlchemyUserSessionRepository(session)}
            )

        super().__init__(session)
