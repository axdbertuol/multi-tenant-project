from pydantic import BaseModel, field_validator
from typing import Any
import re


class PlanName(BaseModel):
    value: str

    model_config = {"frozen": True}

    @field_validator("value")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Plan name cannot be empty")

        cleaned_name = v.strip()

        if len(cleaned_name) < 2:
            raise ValueError("Plan name must be at least 2 characters long")

        if len(cleaned_name) > 50:
            raise ValueError("Plan name cannot exceed 50 characters")

        # Allow letters, numbers, spaces, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", cleaned_name):
            raise ValueError(
                "Plan name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

        return cleaned_name

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PlanName):
            return self.value == other.value
        return False

    def to_slug(self) -> str:
        """Convert name to URL-friendly slug."""
        return re.sub(r"[^a-zA-Z0-9\-_]", "-", self.value.lower()).strip("-")

    def to_identifier(self) -> str:
        """Convert name to programming identifier format."""
        return re.sub(r"[^a-zA-Z0-9_]", "_", self.value.lower()).strip("_")

    def is_system_plan(self) -> bool:
        """Check if this is a system plan name."""
        system_plans = ["free", "basic", "premium", "enterprise"]
        return self.to_identifier() in system_plans
