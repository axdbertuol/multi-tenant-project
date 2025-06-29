from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List, Set
from pydantic import BaseModel

from ..value_objects.role_name import RoleName


class Role(BaseModel):
    id: UUID
    name: RoleName
    description: str
    organization_id: Optional[UUID] = None  # None for system-wide roles
    parent_role_id: Optional[UUID] = None  # For role inheritance
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    is_system_role: bool = False

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls, 
        name: str, 
        description: str, 
        created_by: UUID,
        organization_id: Optional[UUID] = None,
        parent_role_id: Optional[UUID] = None,
        is_system_role: bool = False
    ) -> "Role":
        return cls(
            id=uuid4(),
            name=RoleName(value=name),
            description=description,
            organization_id=organization_id,
            parent_role_id=parent_role_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            is_active=True,
            is_system_role=is_system_role
        )

    def update_description(self, description: str) -> "Role":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "Role":
        if self.is_system_role:
            raise ValueError("Cannot deactivate system roles")
        
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "Role":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })

    def is_organization_role(self) -> bool:
        """Check if this is an organization-specific role."""
        return self.organization_id is not None

    def is_global_role(self) -> bool:
        """Check if this is a global/system role."""
        return self.organization_id is None

    def can_be_deleted(self) -> tuple[bool, str]:
        """Check if role can be deleted."""
        if self.is_system_role:
            return False, "System roles cannot be deleted"
        
        return True, "Role can be deleted"

    def can_be_modified(self) -> tuple[bool, str]:
        """Check if role can be modified."""
        if self.is_system_role:
            return False, "System roles cannot be modified"
        
        if not self.is_active:
            return False, "Inactive roles cannot be modified"
        
        return True, "Role can be modified"

    def has_parent(self) -> bool:
        """Check if this role inherits from another role."""
        return self.parent_role_id is not None

    def set_parent_role(self, parent_role_id: UUID) -> "Role":
        """Set parent role for inheritance."""
        if self.is_system_role:
            raise ValueError("System roles cannot inherit from other roles")
        
        if parent_role_id == self.id:
            raise ValueError("Role cannot inherit from itself")
        
        return self.model_copy(update={
            "parent_role_id": parent_role_id,
            "updated_at": datetime.utcnow()
        })

    def remove_parent_role(self) -> "Role":
        """Remove parent role inheritance."""
        if self.is_system_role:
            raise ValueError("System roles cannot be modified")
        
        return self.model_copy(update={
            "parent_role_id": None,
            "updated_at": datetime.utcnow()
        })

    def is_descendant_of(self, role_hierarchy: List["Role"], ancestor_id: UUID) -> bool:
        """Check if this role is a descendant of the given ancestor role."""
        if not self.has_parent():
            return False
        
        # Create lookup map for efficiency
        role_map = {role.id: role for role in role_hierarchy}
        
        current_parent_id = self.parent_role_id
        visited = set()  # Prevent infinite loops
        
        while current_parent_id and current_parent_id not in visited:
            if current_parent_id == ancestor_id:
                return True
            
            visited.add(current_parent_id)
            parent_role = role_map.get(current_parent_id)
            
            if not parent_role:
                break
                
            current_parent_id = parent_role.parent_role_id
        
        return False

    def get_role_hierarchy_path(self, role_hierarchy: List["Role"]) -> List[UUID]:
        """Get the complete inheritance path from root to this role."""
        if not self.has_parent():
            return [self.id]
        
        # Create lookup map
        role_map = {role.id: role for role in role_hierarchy}
        
        path = []
        current_role = self
        visited = set()
        
        while current_role and current_role.id not in visited:
            path.insert(0, current_role.id)  # Insert at beginning to get root-to-child order
            visited.add(current_role.id)
            
            if current_role.parent_role_id:
                current_role = role_map.get(current_role.parent_role_id)
            else:
                break
        
        return path

    def validate_inheritance_rules(self, role_hierarchy: List["Role"]) -> tuple[bool, str]:
        """Validate role inheritance rules."""
        if not self.has_parent():
            return True, "Role has no parent"
        
        # Check for circular inheritance
        if self.is_descendant_of(role_hierarchy, self.id):
            return False, "Circular inheritance detected"
        
        # Find parent role
        parent_role = next((r for r in role_hierarchy if r.id == self.parent_role_id), None)
        if not parent_role:
            return False, "Parent role not found"
        
        # Check if parent is active
        if not parent_role.is_active:
            return False, "Cannot inherit from inactive role"
        
        # Check organization scope - child role must be in same or narrower scope
        if self.organization_id and parent_role.organization_id:
            if self.organization_id != parent_role.organization_id:
                return False, "Child role must be in same organization as parent"
        elif self.organization_id and not parent_role.organization_id:
            # OK: organization role can inherit from global role
            pass
        elif not self.organization_id and parent_role.organization_id:
            return False, "Global role cannot inherit from organization role"
        
        return True, "Inheritance rules validated"