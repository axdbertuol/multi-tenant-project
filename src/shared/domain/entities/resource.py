from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class ResourceType(str, Enum):
    PROJECT = "project"
    DOCUMENT = "document"
    DATASET = "dataset"
    REPORT = "report"
    DASHBOARD = "dashboard"
    FOLDER = "folder"
    CUSTOM = "custom"


class Resource(BaseModel):
    id: UUID
    name: str
    resource_type: ResourceType
    description: Optional[str] = None
    parent_id: Optional[UUID] = None  # For hierarchical resources
    organization_id: Optional[UUID] = None  # Multi-tenant support
    metadata: Dict[str, Any] = {}  # Flexible attributes (project_code, department, etc.)
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        name: str,
        resource_type: ResourceType,
        description: Optional[str] = None,
        parent_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Resource":
        return cls(
            id=uuid4(),
            name=name,
            resource_type=resource_type,
            description=description,
            parent_id=parent_id,
            organization_id=organization_id,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            is_active=True,
        )

    def update_metadata(self, metadata: Dict[str, Any]) -> "Resource":
        return self.model_copy(update={
            "metadata": {**self.metadata, **metadata},
            "updated_at": datetime.utcnow()
        })

    def set_parent(self, parent_id: UUID) -> "Resource":
        return self.model_copy(update={
            "parent_id": parent_id,
            "updated_at": datetime.utcnow()
        })

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