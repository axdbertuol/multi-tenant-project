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
    member_count: int = 1
    max_members: Optional[int] = None
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
        max_members: Optional[int] = None,
    ) -> "Organization":
        return cls(
            id=uuid4(),
            name=OrganizationName(value=name),
            description=description,
            owner_id=owner_id,
            settings=OrganizationSettings.create_default(max_users=max_users),
            member_count=1,  # Owner is the first member
            max_members=max_members,
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

    def update_member_count(self, new_count: int) -> "Organization":
        """Update the member count."""
        return self.model_copy(
            update={"member_count": new_count, "updated_at": datetime.utcnow()}
        )

    def update_max_members(self, max_members: Optional[int]) -> "Organization":
        """Update the maximum members limit."""
        return self.model_copy(
            update={"max_members": max_members, "updated_at": datetime.utcnow()}
        )

    def increment_member_count(self) -> "Organization":
        """Increment member count by 1."""
        return self.update_member_count(self.member_count + 1)

    def decrement_member_count(self) -> "Organization":
        """Decrement member count by 1."""
        new_count = max(0, self.member_count - 1)
        return self.update_member_count(new_count)

    def is_owner(self, user_id: UUID) -> bool:
        """Check if user is the owner of this organization."""
        return self.owner_id == user_id

    def can_add_users(self, target_count: Optional[int] = None) -> bool:
        """Check if organization can add more users based on settings and limits."""
        count_to_check = target_count or (self.member_count + 1)
        
        # Check against settings max_users limit
        if count_to_check > self.settings.max_users:
            return False
            
        # Check against max_members limit if set
        if self.max_members is not None and count_to_check > self.max_members:
            return False
            
        return True

    def validate_user_limit(self, new_user_count: int) -> tuple[bool, str]:
        """Validate if organization can support the new user count."""
        # Check settings limit
        if new_user_count > self.settings.max_users:
            return (
                False,
                f"Organization exceeds maximum user limit of {self.settings.max_users}",
            )
        
        # Check max_members limit if set
        if self.max_members is not None and new_user_count > self.max_members:
            return (
                False,
                f"Organization exceeds maximum members limit of {self.max_members}",
            )
            
        return True, "User limit validation passed"

    def validate_member_count_consistency(self) -> tuple[bool, str]:
        """Validate that member_count doesn't exceed limits."""
        if self.max_members is not None and self.member_count > self.max_members:
            return (
                False,
                f"Current member count ({self.member_count}) exceeds max_members limit ({self.max_members})",
            )
        
        if self.member_count > self.settings.max_users:
            return (
                False,
                f"Current member count ({self.member_count}) exceeds settings max_users limit ({self.settings.max_users})",
            )
            
        return True, "Member count consistency validated"
