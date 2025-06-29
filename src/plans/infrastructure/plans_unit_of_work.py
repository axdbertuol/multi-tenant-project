from shared.infrastructure.repositories.sqlalchemy_unit_of_work import (
    SQLAlchemyUnitOfWork,
)
from sqlalchemy.orm import Session
from plans.infrastructure.repositories.sqlalchemy_plan_repository import (
    SqlAlchemyPlanRepository,
)
from plans.infrastructure.repositories.sqlalchemy_plan_resource_repository import (
    SqlAlchemyPlanResourceRepository,
)
from plans.infrastructure.repositories.sqlalchemy_subscription_repository import (
    SqlAlchemySubscriptionRepository,
)


class PlansUnitOfWork(SQLAlchemyUnitOfWork):
    _repositories = {}

    def __init__(self, session: Session, repositories: list[str]):
        if "plan" in repositories:
            self._repositories.update({"plan": SqlAlchemyPlanRepository(session)})
        if "plan_resource" in repositories:
            self._repositories.update({"plan_resource": SqlAlchemyPlanResourceRepository(session)})
        if "subscription" in repositories:
            self._repositories.update({"subscription": SqlAlchemySubscriptionRepository(session)})

        super().__init__(session)