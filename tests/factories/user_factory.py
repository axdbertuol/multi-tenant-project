import factory
from datetime import datetime
from uuid import uuid4
from faker import Faker
from src.iam.domain.entities.user import User
from src.iam.domain.value_objects.email import Email
from src.iam.domain.value_objects.password import Password

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for creating User domain entities for testing."""

    class Meta:
        model = User

    id = factory.LazyFunction(uuid4)
    email = factory.LazyAttribute(lambda obj: Email(value=fake.email()))
    name = factory.LazyAttribute(lambda obj: fake.name())
    password = factory.LazyAttribute(lambda obj: Password.create("Password123!"))
    created_at = factory.LazyFunction(lambda: datetime.utcnow())
    updated_at = None
    is_active = True

    @classmethod
    def create_user(cls, **kwargs):
        """Create a user using the domain factory method."""
        email = kwargs.get("email", fake.email())
        name = kwargs.get("name", fake.name())
        password = kwargs.get("password", "Password123!")

        return User.create(email=email, name=name, password=password)

    @classmethod
    def create_active_user(cls, **kwargs):
        """Create an active user."""
        user = cls.create_user(**kwargs)
        return user.activate() if not user.is_active else user

    @classmethod
    def create_inactive_user(cls, **kwargs):
        """Create an inactive user."""
        user = cls.create_user(**kwargs)
        return user.deactivate() if user.is_active else user


class EmailFactory(factory.Factory):
    """Factory for creating Email value objects."""

    class Meta:
        model = Email

    value = factory.LazyAttribute(lambda obj: fake.email())


class PasswordFactory(factory.Factory):
    """Factory for creating Password value objects."""

    class Meta:
        model = Password

    @classmethod
    def create_password(cls, plain_password="Password123!"):
        """Create a password from plain text."""
        return Password.create(plain_password)

    @classmethod
    def create_from_hash(cls, hashed_password):
        """Create a password from existing hash."""
        return Password.from_hash(hashed_password)
