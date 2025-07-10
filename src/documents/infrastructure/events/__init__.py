"""Documents infrastructure events module."""

from .document_events import (
    DocumentEvent,
    DocumentAreaCreatedEvent,
    DocumentAreaUpdatedEvent,
    DocumentAreaDeletedEvent,
    DocumentFolderCreatedEvent,
    DocumentFolderMovedEvent,
    DocumentFolderDeletedEvent,
    UserDocumentAccessGrantedEvent,
    UserDocumentAccessRevokedEvent,
    UserDocumentAccessExtendedEvent,
)
from .event_dispatcher import (
    EventDispatcher,
    EventHandler,
    get_event_dispatcher,
    LoggingEventHandler,
    AuditEventHandler,
)

__all__ = [
    "DocumentEvent",
    "DocumentAreaCreatedEvent",
    "DocumentAreaUpdatedEvent", 
    "DocumentAreaDeletedEvent",
    "DocumentFolderCreatedEvent",
    "DocumentFolderMovedEvent",
    "DocumentFolderDeletedEvent",
    "UserDocumentAccessGrantedEvent",
    "UserDocumentAccessRevokedEvent",
    "UserDocumentAccessExtendedEvent",
    "EventDispatcher",
    "EventHandler",
    "get_event_dispatcher",
    "LoggingEventHandler",
    "AuditEventHandler",
]