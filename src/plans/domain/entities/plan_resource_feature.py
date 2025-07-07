from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PlanResourceFeature(BaseModel):
    id: UUID
    resource_id: UUID
    feature_key: str = Field(..., min_length=1, max_length=100)
    feature_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        resource_id: UUID,
        feature_key: str,
        feature_name: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> "PlanResourceFeature":
        """Create a new plan resource feature."""
        now = datetime.utcnow()
        
        return cls(
            id=uuid4(),
            resource_id=resource_id,
            feature_key=feature_key,
            feature_name=feature_name,
            description=description,
            is_default=is_default,
            created_at=now,
        )

    def update_name(self, feature_name: str) -> "PlanResourceFeature":
        """Update the feature name."""
        if not feature_name or len(feature_name) < 1 or len(feature_name) > 200:
            raise ValueError("Feature name must be between 1 and 200 characters")
        
        return self.model_copy(
            update={
                "feature_name": feature_name,
                "updated_at": datetime.utcnow(),
            }
        )

    def update_description(self, description: str) -> "PlanResourceFeature":
        """Update the feature description."""
        return self.model_copy(
            update={
                "description": description,
                "updated_at": datetime.utcnow(),
            }
        )

    def set_as_default(self) -> "PlanResourceFeature":
        """Mark this feature as default for the resource."""
        return self.model_copy(
            update={
                "is_default": True,
                "updated_at": datetime.utcnow(),
            }
        )

    def unset_as_default(self) -> "PlanResourceFeature":
        """Unmark this feature as default for the resource."""
        return self.model_copy(
            update={
                "is_default": False,
                "updated_at": datetime.utcnow(),
            }
        )

    def validate_feature_key(self) -> tuple[bool, str]:
        """Validate the feature key format."""
        if not self.feature_key:
            return False, "Feature key cannot be empty"
        
        if len(self.feature_key) < 1 or len(self.feature_key) > 100:
            return False, "Feature key must be between 1 and 100 characters"
        
        # Basic alphanumeric and underscore validation
        if not self.feature_key.replace("_", "").replace("-", "").isalnum():
            return False, "Feature key can only contain letters, numbers, underscores, and hyphens"
        
        return True, "Feature key is valid"

    def get_feature_identifier(self) -> str:
        """Get a unique identifier for this feature."""
        return f"{self.resource_id}:{self.feature_key}"

    def is_required_feature(self) -> bool:
        """Check if this is a required/default feature."""
        return self.is_default

    def get_display_name(self) -> str:
        """Get formatted display name."""
        default_indicator = " (Default)" if self.is_default else ""
        return f"{self.feature_name}{default_indicator}"

    def create_feature_config(
        self, is_enabled: bool = True, custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a feature configuration dict."""
        return {
            "feature_id": str(self.id),
            "feature_key": self.feature_key,
            "feature_name": self.feature_name,
            "is_enabled": is_enabled,
            "is_default": self.is_default,
            "custom_config": custom_config or {},
        }

    def get_feature_summary(self) -> Dict[str, Any]:
        """Get a summary of the feature."""
        return {
            "id": str(self.id),
            "resource_id": str(self.resource_id),
            "feature_key": self.feature_key,
            "feature_name": self.feature_name,
            "description": self.description,
            "is_default": self.is_default,
            "feature_identifier": self.get_feature_identifier(),
            "display_name": self.get_display_name(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }