from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel

from ..value_objects.organization_name import OrganizationName
from ..value_objects.organization_settings import OrganizationSettings


class Organization(BaseModel):
    id: UUID
    name: OrganizationName
    description: Optional[str] = None
    owner_id: UUID
    settings: OrganizationSettings
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        name: str,
        owner_id: UUID,
        description: Optional[str] = None,
        max_users: int = 10,
    ) -> "Organization":
        return cls(
            id=uuid4(),
            name=OrganizationName(value=name),
            description=description,
            owner_id=owner_id,
            settings=OrganizationSettings.create_default(max_users=max_users),
            created_at=datetime.utcnow(),
            is_active=True,
        )

    def update_name(self, name: str) -> "Organization":
        return self.model_copy(
            update={
                "name": OrganizationName(value=name),
                "updated_at": datetime.utcnow(),
            }
        )

    def update_description(self, description: str) -> "Organization":
        return self.model_copy(
            update={"description": description, "updated_at": datetime.utcnow()}
        )

    def transfer_ownership(self, new_owner_id: UUID) -> "Organization":
        return self.model_copy(
            update={"owner_id": new_owner_id, "updated_at": datetime.utcnow()}
        )

    def update_settings(self, settings: OrganizationSettings) -> "Organization":
        return self.model_copy(
            update={"settings": settings, "updated_at": datetime.utcnow()}
        )

    def deactivate(self) -> "Organization":
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.utcnow()}
        )

    def activate(self) -> "Organization":
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.utcnow()}
        )

    def is_owner(self, user_id: UUID) -> bool:
        """Check if user is the owner of this organization."""
        return self.owner_id == user_id

    def can_add_users(self, current_user_count: int) -> bool:
        """Check if organization can add more users based on settings."""
        return current_user_count < self.settings.max_users

    def validate_user_limit(self, new_user_count: int) -> tuple[bool, str]:
        """Validate if organization can support the new user count."""
        if new_user_count > self.settings.max_users:
            return (
                False,
                f"Organization exceeds maximum user limit of {self.settings.max_users}",
            )
        return True, "User limit validation passed"
