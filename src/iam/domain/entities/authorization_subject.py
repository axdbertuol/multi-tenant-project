from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AuthorizationSubject(BaseModel):
    """Domain entity representing an authorization subject (lightweight reference for permission checks)."""

    id: UUID = Field(default_factory=uuid4)
    subject_type: str = Field(..., min_length=1, max_length=50)
    subject_id: UUID = Field(...)
    organization_id: Optional[UUID] = Field(None)
    owner_id: UUID = Field(...)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(None)

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        subject_type: str,
        subject_id: UUID,
        owner_id: UUID,
        organization_id: Optional[UUID] = None,
        is_active: bool = True,
    ) -> "AuthorizationSubject":
        """Create a new authorization subject."""
        cls._validate_subject_type(subject_type)
        
        return cls(
            subject_type=subject_type,
            subject_id=subject_id,
            owner_id=owner_id,
            organization_id=organization_id,
            is_active=is_active,
        )

    def update_owner(self, new_owner_id: UUID) -> "AuthorizationSubject":
        """Transfer ownership to a new user."""
        return self.model_copy(
            update={
                "owner_id": new_owner_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def update_organization(self, organization_id: Optional[UUID]) -> "AuthorizationSubject":
        """Update the organization association."""
        return self.model_copy(
            update={
                "organization_id": organization_id,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def activate(self) -> "AuthorizationSubject":
        """Activate the authorization subject."""
        if self.is_active:
            return self
        
        return self.model_copy(
            update={
                "is_active": True,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def deactivate(self) -> "AuthorizationSubject":
        """Deactivate the authorization subject."""
        if not self.is_active:
            return self
        
        return self.model_copy(
            update={
                "is_active": False,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    def is_owned_by(self, user_id: UUID) -> bool:
        """Check if the subject is owned by a specific user."""
        return self.owner_id == user_id

    def belongs_to_organization(self, organization_id: UUID) -> bool:
        """Check if the subject belongs to a specific organization."""
        return self.organization_id == organization_id

    def is_global_subject(self) -> bool:
        """Check if this is a global subject (not tied to an organization)."""
        return self.organization_id is None

    def get_subject_identifier(self) -> str:
        """Get a unique identifier for the subject."""
        org_part = f"org_{self.organization_id}" if self.organization_id else "global"
        return f"{self.subject_type}:{self.subject_id}@{org_part}"

    def get_display_name(self) -> str:
        """Get a human-readable display name."""
        status = "Active" if self.is_active else "Inactive"
        org_info = f" (Org: {self.organization_id})" if self.organization_id else " (Global)"
        return f"{self.subject_type.title()} Subject{org_info} - {status}"

    @staticmethod
    def _validate_subject_type(subject_type: str) -> None:
        """Validate subject type format and constraints."""
        if not subject_type or not subject_type.strip():
            raise ValueError("Subject type cannot be empty")
        
        if len(subject_type) > 50:
            raise ValueError("Subject type cannot exceed 50 characters")
        
        # Allow alphanumeric, underscores, and hyphens
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', subject_type):
            raise ValueError("Subject type can only contain alphanumeric characters, underscores, and hyphens")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entity to a dictionary representation."""
        return {
            "id": str(self.id),
            "subject_type": self.subject_type,
            "subject_id": str(self.subject_id),
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "owner_id": str(self.owner_id),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "subject_identifier": self.get_subject_identifier(),
            "display_name": self.get_display_name(),
            "is_global": self.is_global_subject(),
        }

    def __str__(self) -> str:
        """String representation of the authorization subject."""
        return self.get_display_name()

    def __repr__(self) -> str:
        """Developer-friendly representation of the authorization subject."""
        return (
            f"AuthorizationSubject("
            f"id={self.id}, "
            f"subject_type='{self.subject_type}', "
            f"subject_id={self.subject_id}, "
            f"owner_id={self.owner_id}, "
            f"organization_id={self.organization_id}, "
            f"is_active={self.is_active}"
            f")"
        )