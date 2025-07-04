import factory
from datetime import datetime
from uuid import uuid4
from faker import Faker
from src.iam.domain.entities.organization import Organization

fake = Faker()


class OrganizationFactory(factory.Factory):
    """Factory for creating Organization domain entities for testing."""

    class Meta:
        model = Organization

    id = factory.LazyFunction(uuid4)
    name = factory.LazyAttribute(lambda obj: fake.company())
    description = factory.LazyAttribute(lambda obj: fake.text(max_nb_chars=200))
    owner_id = factory.LazyFunction(uuid4)
    created_at = factory.LazyFunction(lambda: datetime.utcnow())
    updated_at = None
    is_active = True

    @classmethod
    def create_organization(cls, **kwargs):
        """Create an organization using the domain factory method."""
        name = kwargs.get("name", fake.company())
        owner_id = kwargs.get("owner_id", uuid4())
        description = kwargs.get("description", fake.text(max_nb_chars=200))

        return Organization.create(
            name=name, owner_id=owner_id, description=description
        )

    @classmethod
    def create_active_organization(cls, **kwargs):
        """Create an active organization."""
        org = cls.create_organization(**kwargs)
        return org.activate() if not org.is_active else org

    @classmethod
    def create_inactive_organization(cls, **kwargs):
        """Create an inactive organization."""
        org = cls.create_organization(**kwargs)
        return org.deactivate() if org.is_active else org
