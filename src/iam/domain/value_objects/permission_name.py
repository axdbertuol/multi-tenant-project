from pydantic import BaseModel, field_validator
from typing import Any
import re


class PermissionName(BaseModel):
    value: str

    model_config = {"frozen": True}

    @field_validator('value')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Permission name cannot be empty")
        
        cleaned_name = v.strip().lower()
        
        if len(cleaned_name) < 3:
            raise ValueError("Permission name must be at least 3 characters long")
        
        if len(cleaned_name) > 100:
            raise ValueError("Permission name cannot exceed 100 characters")
        
        # Allow letters, numbers, underscores, and colons
        if not re.match(r'^[a-z0-9_:]+$', cleaned_name):
            raise ValueError("Permission name can only contain lowercase letters, numbers, underscores, and colons")
        
        # Must start with a letter
        if not cleaned_name[0].isalpha():
            raise ValueError("Permission name must start with a letter")
        
        return cleaned_name

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PermissionName):
            return self.value == other.value
        return False

    def get_resource_type(self) -> str:
        """Extract resource type from permission name (before first colon)."""
        if ':' in self.value:
            return self.value.split(':')[0]
        return self.value

    def get_action(self) -> str:
        """Extract action from permission name (after first colon)."""
        if ':' in self.value:
            parts = self.value.split(':', 1)
            return parts[1] if len(parts) > 1 else ""
        return ""

    def is_resource_permission(self) -> bool:
        """Check if this is a resource-specific permission (contains colon)."""
        return ':' in self.value

    def matches_pattern(self, pattern: str) -> bool:
        """Check if permission matches a pattern (supports wildcards)."""
        if pattern == "*":
            return True
        
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return self.value.startswith(prefix)
        
        return self.value == pattern

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        return self.value.replace('_', ' ').replace(':', ' - ').title()