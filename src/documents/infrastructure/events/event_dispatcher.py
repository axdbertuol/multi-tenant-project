"""Event dispatcher for the Documents bounded context."""

import logging
from typing import List, Callable, Dict, Any
from abc import ABC, abstractmethod

from .document_events import DocumentEvent

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Base class for event handlers."""
    
    @abstractmethod
    def handle(self, event: DocumentEvent) -> None:
        """Handle the event."""
        pass


class EventDispatcher:
    """
    Event dispatcher for the Documents bounded context.
    
    Manages event handlers and dispatches events to appropriate handlers.
    """

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []

    def register_handler(self, event_type: str, handler: EventHandler) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for event type {event_type}")

    def register_global_handler(self, handler: EventHandler) -> None:
        """Register a global event handler that receives all events."""
        self._global_handlers.append(handler)
        logger.info(f"Registered global handler {handler.__class__.__name__}")

    def unregister_handler(self, event_type: str, handler: EventHandler) -> None:
        """Unregister an event handler for a specific event type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(f"Unregistered handler {handler.__class__.__name__} for event type {event_type}")
            except ValueError:
                logger.warning(f"Handler {handler.__class__.__name__} not found for event type {event_type}")

    def dispatch(self, event: DocumentEvent) -> None:
        """Dispatch an event to all registered handlers."""
        try:
            logger.info(f"Dispatching event {event.event_type} with ID {event.event_id}")
            
            # Dispatch to global handlers
            for handler in self._global_handlers:
                try:
                    handler.handle(event)
                except Exception as e:
                    logger.error(f"Error in global handler {handler.__class__.__name__}: {e}")

            # Dispatch to specific event type handlers
            if event.event_type in self._handlers:
                for handler in self._handlers[event.event_type]:
                    try:
                        handler.handle(event)
                    except Exception as e:
                        logger.error(f"Error in handler {handler.__class__.__name__} for event {event.event_type}: {e}")

        except Exception as e:
            logger.error(f"Error dispatching event {event.event_type}: {e}")


# Global event dispatcher instance
_event_dispatcher = EventDispatcher()


def get_event_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance."""
    return _event_dispatcher


class LoggingEventHandler(EventHandler):
    """Event handler that logs all events."""

    def handle(self, event: DocumentEvent) -> None:
        """Log the event."""
        logger.info(
            f"Event: {event.event_type} | "
            f"ID: {event.event_id} | "
            f"Timestamp: {event.event_timestamp} | "
            f"Organization: {event.organization_id} | "
            f"User: {event.user_id} | "
            f"Correlation: {event.correlation_id}"
        )


class AuditEventHandler(EventHandler):
    """Event handler that creates audit logs for security-relevant events."""

    def __init__(self):
        self.security_events = {
            "user_document_access_granted",
            "user_document_access_revoked",
            "user_document_access_extended",
            "document_area_created",
            "document_area_deleted",
        }

    def handle(self, event: DocumentEvent) -> None:
        """Create audit log for security-relevant events."""
        if event.event_type in self.security_events:
            logger.warning(
                f"AUDIT: {event.event_type} | "
                f"Organization: {event.organization_id} | "
                f"User: {event.user_id} | "
                f"Timestamp: {event.event_timestamp} | "
                f"Event ID: {event.event_id}"
            )


# Register default handlers
_event_dispatcher.register_global_handler(LoggingEventHandler())
_event_dispatcher.register_global_handler(AuditEventHandler())