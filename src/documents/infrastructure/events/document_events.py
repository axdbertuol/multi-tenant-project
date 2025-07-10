"""Document events for the Documents bounded context."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel


class DocumentEvent(BaseModel):
    """Base class for all document events."""
    event_id: str
    event_type: str
    event_timestamp: datetime
    organization_id: UUID
    user_id: Optional[UUID] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

    @classmethod
    def create_event_id(cls) -> str:
        """Generate a unique event ID."""
        from uuid import uuid4
        return str(uuid4())


class DocumentAreaCreatedEvent(DocumentEvent):
    """Event fired when a document area is created."""
    event_type: str = "document_area_created"
    area_id: UUID
    area_name: str
    folder_path: str
    parent_area_id: Optional[UUID] = None
    is_system_area: bool = False

    @classmethod
    def create(
        cls,
        area_id: UUID,
        area_name: str,
        folder_path: str,
        organization_id: UUID,
        created_by: UUID,
        parent_area_id: Optional[UUID] = None,
        is_system_area: bool = False,
        correlation_id: Optional[str] = None,
    ) -> "DocumentAreaCreatedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=created_by,
            area_id=area_id,
            area_name=area_name,
            folder_path=folder_path,
            parent_area_id=parent_area_id,
            is_system_area=is_system_area,
            correlation_id=correlation_id,
        )


class DocumentAreaUpdatedEvent(DocumentEvent):
    """Event fired when a document area is updated."""
    event_type: str = "document_area_updated"
    area_id: UUID
    area_name: str
    previous_values: Dict[str, Any]
    updated_fields: Dict[str, Any]

    @classmethod
    def create(
        cls,
        area_id: UUID,
        area_name: str,
        organization_id: UUID,
        updated_by: UUID,
        previous_values: Dict[str, Any],
        updated_fields: Dict[str, Any],
        correlation_id: Optional[str] = None,
    ) -> "DocumentAreaUpdatedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=updated_by,
            area_id=area_id,
            area_name=area_name,
            previous_values=previous_values,
            updated_fields=updated_fields,
            correlation_id=correlation_id,
        )


class DocumentAreaDeletedEvent(DocumentEvent):
    """Event fired when a document area is deleted."""
    event_type: str = "document_area_deleted"
    area_id: UUID
    area_name: str
    folder_path: str
    was_system_area: bool

    @classmethod
    def create(
        cls,
        area_id: UUID,
        area_name: str,
        folder_path: str,
        organization_id: UUID,
        deleted_by: UUID,
        was_system_area: bool = False,
        correlation_id: Optional[str] = None,
    ) -> "DocumentAreaDeletedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=deleted_by,
            area_id=area_id,
            area_name=area_name,
            folder_path=folder_path,
            was_system_area=was_system_area,
            correlation_id=correlation_id,
        )


class DocumentFolderCreatedEvent(DocumentEvent):
    """Event fired when a document folder is created."""
    event_type: str = "document_folder_created"
    folder_id: UUID
    folder_name: str
    folder_path: str
    area_id: UUID
    parent_path: Optional[str] = None

    @classmethod
    def create(
        cls,
        folder_id: UUID,
        folder_name: str,
        folder_path: str,
        area_id: UUID,
        organization_id: UUID,
        created_by: UUID,
        parent_path: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> "DocumentFolderCreatedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=created_by,
            folder_id=folder_id,
            folder_name=folder_name,
            folder_path=folder_path,
            area_id=area_id,
            parent_path=parent_path,
            correlation_id=correlation_id,
        )


class DocumentFolderMovedEvent(DocumentEvent):
    """Event fired when a document folder is moved."""
    event_type: str = "document_folder_moved"
    folder_id: UUID
    folder_name: str
    old_path: str
    new_path: str
    area_id: UUID

    @classmethod
    def create(
        cls,
        folder_id: UUID,
        folder_name: str,
        old_path: str,
        new_path: str,
        area_id: UUID,
        organization_id: UUID,
        moved_by: UUID,
        correlation_id: Optional[str] = None,
    ) -> "DocumentFolderMovedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=moved_by,
            folder_id=folder_id,
            folder_name=folder_name,
            old_path=old_path,
            new_path=new_path,
            area_id=area_id,
            correlation_id=correlation_id,
        )


class DocumentFolderDeletedEvent(DocumentEvent):
    """Event fired when a document folder is deleted."""
    event_type: str = "document_folder_deleted"
    folder_id: UUID
    folder_name: str
    folder_path: str
    area_id: UUID

    @classmethod
    def create(
        cls,
        folder_id: UUID,
        folder_name: str,
        folder_path: str,
        area_id: UUID,
        organization_id: UUID,
        deleted_by: UUID,
        correlation_id: Optional[str] = None,
    ) -> "DocumentFolderDeletedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=deleted_by,
            folder_id=folder_id,
            folder_name=folder_name,
            folder_path=folder_path,
            area_id=area_id,
            correlation_id=correlation_id,
        )


class UserDocumentAccessGrantedEvent(DocumentEvent):
    """Event fired when user document access is granted."""
    event_type: str = "user_document_access_granted"
    access_id: UUID
    target_user_id: UUID
    area_id: UUID
    access_level: str
    expires_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        access_id: UUID,
        target_user_id: UUID,
        area_id: UUID,
        access_level: str,
        organization_id: UUID,
        granted_by: UUID,
        expires_at: Optional[datetime] = None,
        correlation_id: Optional[str] = None,
    ) -> "UserDocumentAccessGrantedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=granted_by,
            access_id=access_id,
            target_user_id=target_user_id,
            area_id=area_id,
            access_level=access_level,
            expires_at=expires_at,
            correlation_id=correlation_id,
        )


class UserDocumentAccessRevokedEvent(DocumentEvent):
    """Event fired when user document access is revoked."""
    event_type: str = "user_document_access_revoked"
    access_id: UUID
    target_user_id: UUID
    area_id: UUID
    access_level: str
    revocation_reason: Optional[str] = None

    @classmethod
    def create(
        cls,
        access_id: UUID,
        target_user_id: UUID,
        area_id: UUID,
        access_level: str,
        organization_id: UUID,
        revoked_by: UUID,
        revocation_reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> "UserDocumentAccessRevokedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=revoked_by,
            access_id=access_id,
            target_user_id=target_user_id,
            area_id=area_id,
            access_level=access_level,
            revocation_reason=revocation_reason,
            correlation_id=correlation_id,
        )


class UserDocumentAccessExtendedEvent(DocumentEvent):
    """Event fired when user document access is extended."""
    event_type: str = "user_document_access_extended"
    access_id: UUID
    target_user_id: UUID
    area_id: UUID
    previous_expires_at: Optional[datetime]
    new_expires_at: Optional[datetime]
    extension_reason: Optional[str] = None

    @classmethod
    def create(
        cls,
        access_id: UUID,
        target_user_id: UUID,
        area_id: UUID,
        organization_id: UUID,
        extended_by: UUID,
        previous_expires_at: Optional[datetime],
        new_expires_at: Optional[datetime],
        extension_reason: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> "UserDocumentAccessExtendedEvent":
        return cls(
            event_id=cls.create_event_id(),
            event_timestamp=datetime.now(timezone.utc),
            organization_id=organization_id,
            user_id=extended_by,
            access_id=access_id,
            target_user_id=target_user_id,
            area_id=area_id,
            previous_expires_at=previous_expires_at,
            new_expires_at=new_expires_at,
            extension_reason=extension_reason,
            correlation_id=correlation_id,
        )