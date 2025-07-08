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
    folder_path: Optional[str] = None  # For folder-type resources
    area_restrictions: List[UUID] = []  # Areas that can access this resource
    metadata: Dict[
        str, Any
    ] = {}  # Flexible attributes (project_code, department, etc.)
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
        folder_path: Optional[str] = None,
        area_restrictions: Optional[List[UUID]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Resource":
        return cls(
            id=uuid4(),
            name=name,
            resource_type=resource_type,
            description=description,
            parent_id=parent_id,
            organization_id=organization_id,
            folder_path=folder_path,
            area_restrictions=area_restrictions or [],
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            is_active=True,
        )

    def update_metadata(self, metadata: Dict[str, Any]) -> "Resource":
        return self.model_copy(
            update={
                "metadata": {**self.metadata, **metadata},
                "updated_at": datetime.utcnow(),
            }
        )

    def set_parent(self, parent_id: UUID) -> "Resource":
        return self.model_copy(
            update={"parent_id": parent_id, "updated_at": datetime.utcnow()}
        )

    def deactivate(self) -> "Resource":
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.utcnow()}
        )

    def activate(self) -> "Resource":
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.utcnow()}
        )
    
    def set_folder_path(self, folder_path: str) -> "Resource":
        """Set the folder path for this resource."""
        return self.model_copy(
            update={"folder_path": folder_path, "updated_at": datetime.utcnow()}
        )
    
    def add_area_restriction(self, area_id: UUID) -> "Resource":
        """Add an area restriction to this resource."""
        if area_id not in self.area_restrictions:
            new_restrictions = self.area_restrictions + [area_id]
            return self.model_copy(
                update={"area_restrictions": new_restrictions, "updated_at": datetime.utcnow()}
            )
        return self
    
    def remove_area_restriction(self, area_id: UUID) -> "Resource":
        """Remove an area restriction from this resource."""
        if area_id in self.area_restrictions:
            new_restrictions = [aid for aid in self.area_restrictions if aid != area_id]
            return self.model_copy(
                update={"area_restrictions": new_restrictions, "updated_at": datetime.utcnow()}
            )
        return self
    
    def set_area_restrictions(self, area_restrictions: List[UUID]) -> "Resource":
        """Set the area restrictions for this resource."""
        return self.model_copy(
            update={"area_restrictions": area_restrictions, "updated_at": datetime.utcnow()}
        )
    
    def can_be_accessed_by_area(self, area_id: UUID) -> bool:
        """Check if this resource can be accessed by the given area."""
        # If no restrictions, resource is public
        if not self.area_restrictions:
            return True
        
        return area_id in self.area_restrictions
    
    def is_folder_resource(self) -> bool:
        """Check if this resource is a folder."""
        return self.resource_type == ResourceType.FOLDER
    
    def is_document_resource(self) -> bool:
        """Check if this resource is a document."""
        return self.resource_type == ResourceType.DOCUMENT
    
    def has_folder_path(self) -> bool:
        """Check if this resource has a folder path."""
        return self.folder_path is not None and self.folder_path.strip() != ""
    
    def get_folder_path(self) -> str:
        """Get the folder path or empty string if not set."""
        return self.folder_path or ""
    
    def is_restricted_resource(self) -> bool:
        """Check if this resource has area restrictions."""
        return len(self.area_restrictions) > 0
