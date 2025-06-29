from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel


class Permission(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(cls, name: str, resource: str, action: str, description: Optional[str] = None) -> "Permission":
        return cls(
            id=uuid4(),
            name=name,
            resource=resource,
            action=action,
            description=description,
            created_at=datetime.utcnow(),
            is_active=True
        )

    def update_name(self, name: str) -> "Permission":
        return self.model_copy(update={
            "name": name,
            "updated_at": datetime.utcnow()
        })

    def update_description(self, description: str) -> "Permission":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "Permission":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Permission":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })