from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional
from pydantic import BaseModel, Field

from domain.value_objects.email import Email
from domain.value_objects.password import Password


class User(BaseModel):
    id: UUID
    email: Email
    name: str
    password: Password
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"arbitrary_types_allowed": True}

    @classmethod
    def create(cls, email: str, name: str, password: str) -> "User":
        return cls(
            id=uuid4(),
            email=Email(value=email),
            name=name,
            password=Password.create(password),
            created_at=datetime.utcnow(),
            is_active=True
        )

    def update_name(self, name: str) -> "User":
        return self.model_copy(update={
            "name": name,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "User":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "User":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })
    
    def change_password(self, new_password: str) -> "User":
        return self.model_copy(update={
            "password": Password.create(new_password),
            "updated_at": datetime.utcnow()
        })
    
    def verify_password(self, plain_password: str) -> bool:
        return self.password.verify(plain_password)