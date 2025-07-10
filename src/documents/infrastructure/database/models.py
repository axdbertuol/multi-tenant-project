from sqlalchemy import (
    Column,
    DateTime,
    String,
    Boolean,
    ForeignKey,
    Text,
    Integer,
    Table,
    UniqueConstraint,
    Index,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.shared.infrastructure.database.base import BaseModel
from src.shared.infrastructure.database.connection import Base


# Association table for document folder allowed areas
document_folder_allowed_areas = Table(
    "document_folder_allowed_areas",
    Base.metadata,
    Column(
        "folder_id",
        UUID(as_uuid=True),
        ForeignKey("documents.document_folders.id"),
        primary_key=True,
    ),
    Column(
        "area_id",
        UUID(as_uuid=True),
        ForeignKey("documents.document_areas.id"),
        primary_key=True,
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)


class DocumentAreaModel(BaseModel):
    """SQLAlchemy model for DocumentArea entity."""

    __tablename__ = "document_areas"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    parent_area_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_areas.id"),
        nullable=True,
        index=True,
    )
    folder_path = Column(String(1000), nullable=False, index=True)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_area = Column(Boolean, default=False, nullable=False)

    # Ensure unique area names within organization
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_area_name_org"),
        UniqueConstraint("folder_path", "organization_id", name="uq_area_path_org"),
        Index("ix_area_active", "is_active", "organization_id"),
        Index("ix_area_system", "is_system_area"),
        Index("ix_area_hierarchy", "parent_area_id", "organization_id"),
    )

    # Relationships
    parent_area = relationship(
        "DocumentAreaModel", remote_side="DocumentAreaModel.id", backref="child_areas"
    )


class DocumentFolderModel(BaseModel):
    """SQLAlchemy model for DocumentFolder entity."""

    __tablename__ = "document_folders"

    name = Column(String(255), nullable=False, index=True)
    path = Column(String(1000), nullable=False, index=True)
    area_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_areas.id"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    parent_folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_folders.id"),
        nullable=True,
        index=True,
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    is_virtual = Column(Boolean, default=False, nullable=False)
    extra_data = Column(JSON, nullable=False, default={})

    # Ensure unique paths within organization
    __table_args__ = (
        UniqueConstraint("path", "organization_id", name="uq_folder_path_org"),
        Index("ix_folder_active", "is_active", "organization_id"),
        Index("ix_folder_area", "area_id", "organization_id"),
        Index("ix_folder_hierarchy", "parent_folder_id", "organization_id"),
        Index("ix_folder_virtual", "is_virtual"),
    )

    # Relationships
    area = relationship("DocumentAreaModel", backref="folders")
    parent_folder = relationship(
        "DocumentFolderModel", remote_side="DocumentFolderModel.id", backref="child_folders"
    )
    allowed_areas = relationship(
        "DocumentAreaModel",
        secondary=document_folder_allowed_areas,
        backref="accessible_folders"
    )


class UserDocumentAccessModel(BaseModel):
    """SQLAlchemy model for UserDocumentAccess entity."""

    __tablename__ = "user_document_access"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    area_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_areas.id"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    access_level = Column(String(50), nullable=False, index=True)  # READ, WRITE, FULL
    granted_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    granted_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=True
    )
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=False, default={})

    # Ensure unique active access per user-area pair
    __table_args__ = (
        UniqueConstraint("user_id", "area_id", name="uq_user_area_access"),
        Index("ix_access_active", "is_active", "user_id", "organization_id"),
        Index("ix_access_expires", "expires_at"),
        Index("ix_access_granted", "granted_at"),
        Index("ix_access_level", "access_level", "organization_id"),
    )

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    area = relationship("DocumentAreaModel", backref="user_accesses")
    granted_by_user = relationship("UserModel", foreign_keys=[granted_by])
    revoked_by_user = relationship("UserModel", foreign_keys=[revoked_by])


class DocumentFileModel(BaseModel):
    """SQLAlchemy model for Document Files."""

    __tablename__ = "document_files"

    name = Column(String(255), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=False, index=True)
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_folders.id"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(50), default="pending", nullable=False)
    processing_error = Column(Text, nullable=True)
    tags = Column(ARRAY(String), nullable=False, default=[])
    extra_data = Column(JSON, nullable=False, default={})

    # Ensure unique file paths within organization
    __table_args__ = (
        UniqueConstraint("file_path", "organization_id", name="uq_file_path_org"),
        Index("ix_file_folder", "folder_id", "organization_id"),
        Index("ix_file_processed", "is_processed", "processing_status"),
        Index("ix_file_hash", "file_hash"),
        Index("ix_file_mime", "mime_type"),
        Index("ix_file_tags", "tags", postgresql_using='gin'),
    )

    # Relationships
    folder = relationship("DocumentFolderModel", backref="files")
    uploaded_by_user = relationship("UserModel", foreign_keys=[uploaded_by])


class DocumentVersionModel(BaseModel):
    """SQLAlchemy model for Document Versions."""

    __tablename__ = "document_versions"

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_files.id"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    uploaded_by = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False
    )
    change_notes = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    extra_data = Column(JSON, nullable=False, default={})

    # Ensure unique version numbers per file
    __table_args__ = (
        UniqueConstraint("file_id", "version_number", name="uq_file_version"),
        Index("ix_version_current", "is_current", "file_id"),
        Index("ix_version_hash", "file_hash"),
    )

    # Relationships
    file = relationship("DocumentFileModel", backref="versions")
    uploaded_by_user = relationship("UserModel", foreign_keys=[uploaded_by])


class DocumentAccessLogModel(BaseModel):
    """SQLAlchemy model for Document Access Logs."""

    __tablename__ = "document_access_logs"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("contas.users.id"), nullable=False, index=True
    )
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_files.id"),
        nullable=True,
        index=True,
    )
    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_folders.id"),
        nullable=True,
        index=True,
    )
    area_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.document_areas.id"),
        nullable=True,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contas.organizations.id"),
        nullable=False,
        index=True,
    )
    access_type = Column(String(50), nullable=False, index=True)  # READ, WRITE, DELETE, DOWNLOAD
    action_details = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=False, default={})

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_access_log_user_time", "user_id", "created_at"),
        Index("ix_access_log_file_time", "file_id", "created_at"),
        Index("ix_access_log_org_time", "organization_id", "created_at"),
        Index("ix_access_log_type", "access_type", "success"),
    )

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    file = relationship("DocumentFileModel", foreign_keys=[file_id])
    folder = relationship("DocumentFolderModel", foreign_keys=[folder_id])
    area = relationship("DocumentAreaModel", foreign_keys=[area_id])