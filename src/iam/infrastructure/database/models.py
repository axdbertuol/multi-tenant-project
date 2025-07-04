from sqlalchemy import (
    Column,
    DateTime,
    String,
    Boolean,
    ForeignKey,
    Text,
    Enum,
    Integer,
    Table,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import enum

from src.shared.infrastructure.database.base import BaseModel as SQLBaseModel
from src.shared.infrastructure.database.connection import Base


# Enums
class SessionStatusEnum(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    LOGGED_OUT = "logged_out"
    REVOKED = "revoked"


class PermissionActionEnum(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    MANAGE = "manage"


class PolicyEffectEnum(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"


# Association tables
role_permission_association = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("contas.authorization_roles.id"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("contas.authorization_permissions.id"),
        primary_key=True,
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


user_role_assignment = Table(
    "user_role_assignments",
    Base.metadata,
    Column(
        "user_id", UUID(as_uuid=True), ForeignKey("contas.users.id"), primary_key=True
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("contas.authorization_roles.id"),
        primary_key=True,
    ),
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=True,
    ),
    Column(
        "assigned_by", UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    Column("expires_at", DateTime(timezone=True), nullable=True),
    Column("is_active", Boolean, default=True, nullable=False),
)


# Organization-related models
class OrganizationModel(SQLBaseModel):
    """SQLAlchemy model for Organization entity."""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=False, default={})  # Organization settings as JSON
    member_count = Column(Integer, default=1, nullable=False)
    max_members = Column(Integer, nullable=True)


class UserOrganizationRoleModel(SQLBaseModel):
    """SQLAlchemy model for UserOrganizationRole entity."""

    __tablename__ = "user_organization_roles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.authorization_roles.id"),
        nullable=False,
        index=True,
    )
    assigned_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    assigned_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=True
    )


# User-related models
class UserModel(SQLBaseModel):
    """Modelo SQLAlchemy para a entidade Usuário."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)


class UserSessionModel(SQLBaseModel):
    """Modelo SQLAlchemy para a entidade UserSession."""

    __tablename__ = "user_sessions"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    status = Column(
        Enum(SessionStatusEnum),
        nullable=False,
        default=SessionStatusEnum.ACTIVE,
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_activity_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    logout_at = Column(DateTime(timezone=True), nullable=True)
    _metadata = Column(Text, nullable=True)  # JSON string for additional session data


# Authorization-related models
class RoleModel(SQLBaseModel):
    """SQLAlchemy model for Role entity."""

    __tablename__ = "authorization_roles"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=True,
        index=True,
    )
    parent_role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.authorization_roles.id"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)

    # Ensure unique role names within organization scope (null for global roles)
    __table_args__ = (UniqueConstraint("name", "organization_id"),)


class PermissionModel(SQLBaseModel):
    """SQLAlchemy model for Permission entity."""

    __tablename__ = "authorization_permissions"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    action = Column(Enum(PermissionActionEnum), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_permission = Column(Boolean, default=False, nullable=False)

    # Ensure unique permission names within resource type
    __table_args__ = (UniqueConstraint("name", "resource_type"),)


class PolicyModel(SQLBaseModel):
    """SQLAlchemy model for Policy entity."""

    __tablename__ = "authorization_policies"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    effect = Column(Enum(PolicyEffectEnum), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    conditions = Column(JSON, nullable=False, default=[])  # List of policy conditions
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Index for efficient policy lookup
    __table_args__ = (
        Index("ix_policy_lookup", "resource_type", "action", "organization_id"),
    )


class ResourceModel(SQLBaseModel):
    """SQLAlchemy model for Resource entity."""

    __tablename__ = "authorization_resources"

    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=True,
        index=True,
    )
    attributes = Column(JSON, nullable=False, default={})
    is_active = Column(Boolean, default=True, nullable=False)

    # Unique constraint for resource type and resource ID combination
    __table_args__ = (UniqueConstraint("resource_type", "resource_id"),)
