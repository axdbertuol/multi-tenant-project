from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AuthorizationContext(BaseModel):
    """Context for authorization decisions containing all relevant information."""
    
    user_id: UUID
    organization_id: Optional[UUID]
    resource_type: str
    resource_id: Optional[UUID]
    action: str
    user_attributes: Dict[str, Any]
    resource_attributes: Dict[str, Any]
    environment_attributes: Dict[str, Any]
    request_time: datetime
    
    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        user_id: UUID,
        resource_type: str,
        action: str,
        organization_id: Optional[UUID] = None,
        resource_id: Optional[UUID] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        environment_attributes: Optional[Dict[str, Any]] = None
    ) -> "AuthorizationContext":
        return cls(
            user_id=user_id,
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            user_attributes=user_attributes or {},
            resource_attributes=resource_attributes or {},
            environment_attributes=environment_attributes or {},
            request_time=datetime.utcnow()
        )

    def add_user_attribute(self, key: str, value: Any) -> "AuthorizationContext":
        """Add user attribute to context."""
        new_attributes = self.user_attributes.copy()
        new_attributes[key] = value
        return self.model_copy(update={"user_attributes": new_attributes})

    def add_resource_attribute(self, key: str, value: Any) -> "AuthorizationContext":
        """Add resource attribute to context."""
        new_attributes = self.resource_attributes.copy()
        new_attributes[key] = value
        return self.model_copy(update={"resource_attributes": new_attributes})

    def add_environment_attribute(self, key: str, value: Any) -> "AuthorizationContext":
        """Add environment attribute to context."""
        new_attributes = self.environment_attributes.copy()
        new_attributes[key] = value
        return self.model_copy(update={"environment_attributes": new_attributes})

    def get_user_attribute(self, key: str, default: Any = None) -> Any:
        """Get user attribute value."""
        return self.user_attributes.get(key, default)

    def get_resource_attribute(self, key: str, default: Any = None) -> Any:
        """Get resource attribute value."""
        return self.resource_attributes.get(key, default)

    def get_environment_attribute(self, key: str, default: Any = None) -> Any:
        """Get environment attribute value."""
        return self.environment_attributes.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for policy evaluation."""
        return {
            "user_id": str(self.user_id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "action": self.action,
            "request_time": self.request_time.isoformat(),
            **self.user_attributes,
            **{f"resource_{k}": v for k, v in self.resource_attributes.items()},
            **{f"env_{k}": v for k, v in self.environment_attributes.items()}
        }

    def is_same_organization(self, other_org_id: Optional[UUID]) -> bool:
        """Check if context belongs to same organization."""
        return self.organization_id == other_org_id

    def is_resource_owner(self) -> bool:
        """Check if user is the resource owner."""
        return self.get_resource_attribute("owner_id") == str(self.user_id)

    def get_user_roles(self) -> List[str]:
        """Get user roles from context."""
        return self.get_user_attribute("roles", [])

    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.get_user_roles()