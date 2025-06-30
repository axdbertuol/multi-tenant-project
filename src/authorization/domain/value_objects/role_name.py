from pydantic import BaseModel, field_validator
from typing import Any
import re


class RoleName(BaseModel):
    value: str

    model_config = {"frozen": True}

    @field_validator("value")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Role name cannot be empty")

        cleaned_name = v.strip().lower()

        if len(cleaned_name) < 2:
            raise ValueError("Role name must be at least 2 characters long")

        if len(cleaned_name) > 50:
            raise ValueError("Role name cannot exceed 50 characters")

        # Allow letters, numbers, and underscores only
        if not re.match(r"^[a-z0-9_]+$", cleaned_name):
            raise ValueError(
                "Role name can only contain lowercase letters, numbers, and underscores"
            )

        # Must start with a letter
        if not cleaned_name[0].isalpha():
            raise ValueError("Role name must start with a letter")

        return cleaned_name

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RoleName):
            return self.value == other.value
        return False

    def is_system_role(self) -> bool:
        """Check if this is a system role (starts with 'system_')."""
        return self.value.startswith("system_")

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        return self.value.replace("_", " ").title()
