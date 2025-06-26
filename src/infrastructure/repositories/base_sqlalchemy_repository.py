from abc import abstractmethod
from typing import Generic, TypeVar, List, Optional, Type
from uuid import UUID
from sqlalchemy.orm import Session

from domain.repositories.base_repository import Repository

DomainEntity = TypeVar('DomainEntity')
DatabaseModel = TypeVar('DatabaseModel')


class SQLAlchemyRepository(Repository[DomainEntity], Generic[DomainEntity, DatabaseModel]):
    def __init__(self, db: Session, model_class: Type[DatabaseModel]):
        self.db = db
        self.model_class = model_class

    @abstractmethod
    def _to_domain(self, model: DatabaseModel) -> DomainEntity:
        pass

    @abstractmethod
    def _to_model(self, entity: DomainEntity) -> DatabaseModel:
        pass

    @abstractmethod
    def _update_model(self, model: DatabaseModel, entity: DomainEntity) -> DatabaseModel:
        pass

    async def create(self, entity: DomainEntity) -> DomainEntity:
        model = self._to_model(entity)
        self.db.add(model)
        self.db.flush()  # Flush to get the ID but don't commit
        self.db.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, entity_id: UUID) -> Optional[DomainEntity]:
        model = self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        return self._to_domain(model) if model else None

    async def get_all(self) -> List[DomainEntity]:
        models = self.db.query(self.model_class).all()
        return [self._to_domain(model) for model in models]

    async def update(self, entity: DomainEntity) -> DomainEntity:
        model = self.db.query(self.model_class).filter(self.model_class.id == entity.id).first()
        if model:
            updated_model = self._update_model(model, entity)
            self.db.flush()  # Flush changes but don't commit
            self.db.refresh(updated_model)
            return self._to_domain(updated_model)
        raise ValueError(f"Entity with id {entity.id} not found")

    async def delete(self, entity_id: UUID) -> bool:
        model = self.db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        if model:
            self.db.delete(model)
            self.db.flush()  # Flush changes but don't commit
            return True
        return False