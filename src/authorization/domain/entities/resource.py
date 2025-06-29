from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel


class Resource(BaseModel):
    id: UUID
    resource_type: str  # e.g., "user", "organization", "chat", "plan"
    resource_id: UUID  # ID of the actual resource
    owner_id: UUID
    organization_id: Optional[UUID] = None
    attributes: Dict[str, Any]  # For ABAC - resource attributes
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls, 
        resource_type: str, 
        resource_id: UUID, 
        owner_id: UUID,
        organization_id: Optional[UUID] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> "Resource":
        return cls(
            id=uuid4(),
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            organization_id=organization_id,
            attributes=attributes or {},
            created_at=datetime.utcnow(),
            is_active=True
        )

    def update_attributes(self, attributes: Dict[str, Any]) -> "Resource":
        """Update resource attributes for ABAC."""
        return self.model_copy(update={
            "attributes": {**self.attributes, **attributes},
            "updated_at": datetime.utcnow()
        })

    def set_attribute(self, key: str, value: Any) -> "Resource":
        """Set a single attribute."""
        new_attributes = self.attributes.copy()
        new_attributes[key] = value
        
        return self.model_copy(update={
            "attributes": new_attributes,
            "updated_at": datetime.utcnow()
        })

    def remove_attribute(self, key: str) -> "Resource":
        """Remove an attribute."""
        new_attributes = self.attributes.copy()
        new_attributes.pop(key, None)
        
        return self.model_copy(update={
            "attributes": new_attributes,
            "updated_at": datetime.utcnow()
        })

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get attribute value."""
        return self.attributes.get(key, default)

    def has_attribute(self, key: str) -> bool:
        """Check if resource has specific attribute."""
        return key in self.attributes

    def is_owned_by(self, user_id: UUID) -> bool:
        """Check if resource is owned by specific user."""
        return self.owner_id == user_id

    def belongs_to_organization(self, organization_id: UUID) -> bool:
        """Check if resource belongs to specific organization."""
        return self.organization_id == organization_id

    def deactivate(self) -> "Resource":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Resource":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })

    def transfer_ownership(self, new_owner_id: UUID) -> "Resource":
        """Transfer resource ownership."""
        return self.model_copy(update={
            "owner_id": new_owner_id,
            "updated_at": datetime.utcnow()
        })