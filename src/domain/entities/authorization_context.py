from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any
from pydantic import BaseModel


class AuthorizationContext(BaseModel):
    """Context information used for ABAC authorization decisions"""
    user_id: UUID
    resource_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    user_attributes: Dict[str, Any] = {}  # department, team, level, etc.
    resource_attributes: Dict[str, Any] = {}  # project_code, classification, owner, etc.
    environment_attributes: Dict[str, Any] = {}  # time, ip_address, location, etc.
    request_attributes: Dict[str, Any] = {}  # action, client_type, etc.

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        user_id: UUID,
        resource_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        environment_attributes: Optional[Dict[str, Any]] = None,
        request_attributes: Optional[Dict[str, Any]] = None,
    ) -> "AuthorizationContext":
        # Add default environment attributes
        env_attrs = environment_attributes or {}
        env_attrs.setdefault("timestamp", datetime.utcnow().isoformat())
        
        return cls(
            user_id=user_id,
            resource_id=resource_id,
            organization_id=organization_id,
            user_attributes=user_attributes or {},
            resource_attributes=resource_attributes or {},
            environment_attributes=env_attrs,
            request_attributes=request_attributes or {},
        )

    def get_attribute(self, attribute_path: str) -> Any:
        """Get attribute value using dot notation (e.g., 'user.department', 'resource.project_code')"""
        parts = attribute_path.split('.')
        if len(parts) != 2:
            return None
            
        category, key = parts
        if category == "user":
            return self.user_attributes.get(key)
        elif category == "resource":
            return self.resource_attributes.get(key)
        elif category == "environment":
            return self.environment_attributes.get(key)
        elif category == "request":
            return self.request_attributes.get(key)
        else:
            return None

    def with_user_attributes(self, **attributes) -> "AuthorizationContext":
        return self.model_copy(update={
            "user_attributes": {**self.user_attributes, **attributes}
        })

    def with_resource_attributes(self, **attributes) -> "AuthorizationContext":
        return self.model_copy(update={
            "resource_attributes": {**self.resource_attributes, **attributes}
        })

    def with_environment_attributes(self, **attributes) -> "AuthorizationContext":
        return self.model_copy(update={
            "environment_attributes": {**self.environment_attributes, **attributes}
        })

    def with_request_attributes(self, **attributes) -> "AuthorizationContext":
        return self.model_copy(update={
            "request_attributes": {**self.request_attributes, **attributes}
        })