from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ResourceCategory(str, Enum):
    MESSAGING = "messaging"
    ANALYTICS = "analytics"
    STORAGE = "storage"
    INTEGRATION = "integration"
    SECURITY = "security"
    WORKFLOW = "workflow"


class PlanResource(BaseModel):
    id: UUID
    resource_type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: ResourceCategory
    is_active: bool = True
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        resource_type: str,
        name: str,
        category: ResourceCategory,
        created_by: UUID,
        description: Optional[str] = None,
    ) -> "PlanResource":
        """Create a new plan resource."""
        now = datetime.utcnow()
        
        return cls(
            id=uuid4(),
            resource_type=resource_type,
            name=name,
            description=description,
            category=category,
            is_active=True,
            created_by=created_by,
            created_at=now,
        )

    def deactivate(self) -> "PlanResource":
        """Deactivate the resource."""
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.utcnow(),
            }
        )

    def reactivate(self) -> "PlanResource":
        """Reactivate the resource."""
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_description(self, description: str) -> "PlanResource":
        """Update the resource description."""
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_name(self, name: str) -> "PlanResource":
        """Update the resource name."""
        if not name or len(name) < 1 or len(name) > 100:
            raise ValueError("Resource name must be between 1 and 100 characters")
        
        return self.model_copy(
            update={
                "name": name,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_category(self, category: ResourceCategory) -> "PlanResource":
        """Update the resource category."""
        return self.model_copy(
            update={
                "category": category,
                "updated_at": datetime.utcnow(),
            }
        )

    def is_messaging_resource(self) -> bool:
        """Check if this is a messaging resource."""
        return self.category == ResourceCategory.MESSAGING

    def is_analytics_resource(self) -> bool:
        """Check if this is an analytics resource."""
        return self.category == ResourceCategory.ANALYTICS

    def is_storage_resource(self) -> bool:
        """Check if this is a storage resource."""
        return self.category == ResourceCategory.STORAGE

    def is_integration_resource(self) -> bool:
        """Check if this is an integration resource."""
        return self.category == ResourceCategory.INTEGRATION

    def can_be_used(self) -> tuple[bool, str]:
        """Check if the resource can be used."""
        if not self.is_active:
            return False, "Resource is deactivated"
        
        return True, "Resource is available"

    def get_display_name(self) -> str:
        """Get formatted display name."""
        return f"{self.name} ({self.category.value})"

    def get_resource_summary(self) -> dict:
        """Get a summary of the resource."""
        return {
            "id": str(self.id),
            "resource_type": self.resource_type,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "is_active": self.is_active,
            "display_name": self.get_display_name(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }