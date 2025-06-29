from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository
from ...domain.value_objects.email import Email
from ...domain.value_objects.password import Password
from ...infrastructure.models.database_models import UserModel


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        """Save a user entity."""
        try:
            # Check if user exists
            existing = self.session.get(UserModel, user.id)

            if existing:
                # Update existing user
                existing.email = str(user.email.value)
                existing.name = user.name
                existing.password_hash = user.password.hashed_value
                existing.is_active = user.is_active
                existing.is_verified = user.is_verified
                existing.last_login_at = user.last_login_at
                existing.updated_at = datetime.now(timezone.utc)

                self.session.flush()
                return self._to_domain_entity(existing)
            else:
                # Create new user
                user_model = UserModel(
                    id=user.id,
                    email=str(user.email.value),
                    name=user.name,
                    password_hash=user.password.hash,
                    is_active=user.is_active,
                    is_verified=user.is_verified,
                    last_login_at=user.last_login_at,
                    created_at=user.created_at,
                    updated_at=user.updated_at,
                )

                self.session.add(user_model)
                self.session.flush()
                return self._to_domain_entity(user_model)

        except IntegrityError as e:
            self.session.rollback()
            if "email" in str(e):
                raise ValueError(f"User with email {user.email.value} already exists")
            raise e

    def find_by_id(self, user_id: UUID) -> Optional[User]:
        """Find a user by ID."""
        result = self.session.execute(select(UserModel).where(UserModel.id == user_id))
        user_model = result.scalar_one_or_none()

        if user_model:
            return self._to_domain_entity(user_model)
        return None

    def find_by_email(self, email: Email) -> Optional[User]:
        """Find a user by email."""
        result = self.session.execute(
            select(UserModel).where(UserModel.email == str(email.value))
        )
        user_model = result.scalar_one_or_none()

        if user_model:
            return self._to_domain_entity(user_model)
        return None

    def find_active_users(self) -> List[User]:
        """Find all active users."""
        result = self.session.execute(select(UserModel).where(UserModel.is_active))
        user_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in user_models]

    def find_paginated(
        self,
        offset: int = 0,
        limit: int = 20,
        email_filter: Optional[str] = None,
        name_filter: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[List[User], int]:
        """Find users with pagination and filters."""
        query = select(UserModel)
        count_query = select(UserModel)

        # Apply filters
        if email_filter:
            query = query.where(UserModel.email.ilike(f"%{email_filter}%"))
            count_query = count_query.where(UserModel.email.ilike(f"%{email_filter}%"))

        if name_filter:
            query = query.where(UserModel.name.ilike(f"%{name_filter}%"))
            count_query = count_query.where(UserModel.name.ilike(f"%{name_filter}%"))

        if is_active is not None:
            query = query.where(UserModel.is_active == is_active)
            count_query = count_query.where(UserModel.is_active == is_active)

        # Get total count
        total_result = self.session.execute(count_query)
        total = len(total_result.scalars().all())

        # Get paginated results
        query = query.offset(offset).limit(limit).order_by(UserModel.created_at.desc())
        result = self.session.execute(query)
        user_models = result.scalars().all()

        users = [self._to_domain_entity(model) for model in user_models]
        return users, total

    def delete(self, user_id: UUID) -> bool:
        """Delete a user (hard delete)."""
        result = self.session.execute(delete(UserModel).where(UserModel.id == user_id))
        return result.rowcount > 0

    def exists_by_email(self, email: Email) -> bool:
        """Check if a user with the given email exists."""
        result = self.session.execute(
            select(UserModel.id).where(UserModel.email == str(email.value))
        )
        return result.scalar_one_or_none() is not None

    def count_active_users(self) -> int:
        """Count active users."""
        result = self.session.execute(select(UserModel).where(UserModel.is_active))
        return len(result.scalars().all())

    def find_users_created_after(self, date: datetime) -> List[User]:
        """Find users created after a specific date."""
        result = self.session.execute(
            select(UserModel).where(UserModel.created_at >= date)
        )
        user_models = result.scalars().all()

        return [self._to_domain_entity(model) for model in user_models]

    def update_last_login(self, user_id: UUID, login_time: datetime) -> bool:
        """Update user's last login time."""
        result = self.session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(last_login_at=login_time, updated_at=datetime.now(timezone.utc))
        )
        return result.rowcount > 0

    def _to_domain_entity(self, user_model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity."""
        return User(
            id=user_model.id,
            email=Email(user_model.email),
            name=user_model.name,
            password=Password.from_hash(user_model.password_hash),
            is_active=user_model.is_active,
            is_verified=user_model.is_verified,
            last_login_at=user_model.last_login_at,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )
