from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel


class Role(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_system: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(cls, name: str, description: Optional[str] = None, is_system: bool = False) -> "Role":
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            is_system=is_system,
            created_at=datetime.utcnow(),
            is_active=True
        )

    def update_name(self, name: str) -> "Role":
        return self.model_copy(update={
            "name": name,
            "updated_at": datetime.utcnow()
        })

    def update_description(self, description: str) -> "Role":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "Role":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Role":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })