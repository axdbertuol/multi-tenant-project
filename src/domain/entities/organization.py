from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel


class Organization(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    owner_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(cls, name: str, owner_id: UUID, description: Optional[str] = None) -> "Organization":
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
            is_active=True
        )

    def update_name(self, name: str) -> "Organization":
        return self.model_copy(update={
            "name": name,
            "updated_at": datetime.utcnow()
        })

    def update_description(self, description: str) -> "Organization":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def transfer_ownership(self, new_owner_id: UUID) -> "Organization":
        return self.model_copy(update={
            "owner_id": new_owner_id,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "Organization":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Organization":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })