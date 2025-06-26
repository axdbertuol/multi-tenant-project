from typing import Optional
from sqlalchemy.orm import Session

from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from domain.value_objects.email import Email
from domain.value_objects.password import Password
from infrastructure.database.models import UserModel
from infrastructure.repositories.base_sqlalchemy_repository import SQLAlchemyRepository


class UserRepositoryImpl(SQLAlchemyRepository[User, UserModel], UserRepository):
    def __init__(self, db: Session):
        super().__init__(db, UserModel)

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(value=model.email),
            name=model.name,
            password=Password.from_hash(model.password),
            created_at=model.created_at,
            updated_at=model.updated_at,
            is_active=model.is_active,
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            email=str(user.email.value),
            name=user.name,
            password=user.password.hashed_value,
            created_at=user.created_at,
            updated_at=user.updated_at,
            is_active=user.is_active,
        )

    def _update_model(self, model: UserModel, user: User) -> UserModel:
        model.email = str(user.email.value)
        model.name = user.name
        model.password = user.password.hashed_value
        model.updated_at = user.updated_at
        model.is_active = user.is_active
        return model

    async def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(model) if model else None
