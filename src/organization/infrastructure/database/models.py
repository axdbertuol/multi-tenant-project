from shared.infrastructure.database.models.base import BaseModel as SQLBaseModel
from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, JSON


class OrganizationModel(SQLBaseModel):
    """SQLAlchemy model for Organization entity."""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=False, default={})  # Organization settings as JSON
    member_count = Column(Integer, default=1, nullable=False)
    max_members = Column(Integer, nullable=True)


class UserOrganizationRoleModel(SQLBaseModel):
    """SQLAlchemy model for UserOrganizationRole entity."""

    __tablename__ = "user_organization_roles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True
    )
    role_id = Column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True
    )
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Ensure unique active membership per user per organization
    __table_args__ = ({"postgresql_where": "is_active = true"},)
