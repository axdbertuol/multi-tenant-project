"""Chat document authorization service for validating document access in chat context."""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime

from .authorization_service import AuthorizationService
from .rbac_service import RBACService
from .abac_service import ABACService
from ..entities.authorization_context import AuthorizationContext
from ..entities.resource import Resource
from ..constants.document_policies import DocumentAccessValidationHelpers


class ChatDocumentAuthorizationService:
    """Service for validating document access in chat applications (iframe/whatsapp)."""

    def __init__(
        self,
        authorization_service: AuthorizationService,
        rbac_service: RBACService,
        abac_service: ABACService
    ):
        self.authorization_service = authorization_service
        self.rbac_service = rbac_service
        self.abac_service = abac_service

    def can_user_access_document_in_chat(
        self,
        user_id: UUID,
        document_id: UUID,
        action: str = "ai_query",
        chat_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user can access a document in chat context.
        
        Args:
            user_id: ID of the user requesting access
            document_id: ID of the document
            action: Action being performed (ai_query, read, download, etc.)
            chat_context: Additional chat context (session, channel, etc.)
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            return self.authorization_service.can_user_access_resource(
                user_id=user_id,
                resource_type="document",
                resource_id=document_id,
                action=action,
                additional_context=chat_context or {}
            )
        except Exception:
            # Fail securely - deny access on any error
            return False

    def filter_accessible_documents_for_chat(
        self,
        user_id: UUID,
        document_ids: List[UUID],
        action: str = "ai_query",
        chat_context: Optional[Dict[str, Any]] = None
    ) -> List[UUID]:
        """
        Filter a list of documents to only those accessible by the user in chat context.
        
        Args:
            user_id: ID of the user
            document_ids: List of document IDs to filter
            action: Action being performed
            chat_context: Additional chat context
            
        Returns:
            List of document IDs the user can access
        """
        accessible_docs = []
        
        for doc_id in document_ids:
            if self.can_user_access_document_in_chat(
                user_id=user_id,
                document_id=doc_id,
                action=action,
                chat_context=chat_context
            ):
                accessible_docs.append(doc_id)
        
        return accessible_docs

    def get_user_document_permissions(
        self,
        user_id: UUID,
        document_id: UUID,
        chat_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Get all document permissions for a user in chat context.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document
            chat_context: Additional chat context
            
        Returns:
            Dictionary mapping action names to permission status
        """
        actions = [
            "read", "download", "ai_query", "ai_cite", "share"
        ]
        
        permissions = {}
        for action in actions:
            permissions[action] = self.can_user_access_document_in_chat(
                user_id=user_id,
                document_id=document_id,
                action=action,
                chat_context=chat_context
            )
        
        return permissions

    def validate_document_for_ai_training(
        self,
        user_id: UUID,
        document_id: UUID,
        training_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Validate if a document can be used for AI training.
        
        Args:
            user_id: ID of the user requesting training
            document_id: ID of the document
            training_context: Additional training context
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check if user has training permission
        can_train = self.can_user_access_document_in_chat(
            user_id=user_id,
            document_id=document_id,
            action="train",
            chat_context=training_context
        )
        
        if not can_train:
            return False, "User does not have permission to use this document for training"
        
        return True, "Document approved for training"

    def create_document_resource(
        self,
        document_id: UUID,
        title: str,
        owner_id: UUID,
        organization_id: UUID,
        shared_with_roles: List[str] = None,
        shared_with_users: List[UUID] = None,
        confidentiality_level: str = "public",
        training_enabled: bool = True,
        ai_query_enabled: bool = True,
        download_enabled: bool = True,
        business_hours_only: bool = False,
        tags: List[str] = None,
        **additional_attributes
    ) -> Resource:
        """
        Create a Resource entity for a document with appropriate attributes.
        
        This integrates documents into the existing Resource system for authorization.
        """
        # Build document attributes for authorization
        document_attributes = DocumentAccessValidationHelpers.build_document_attributes(
            document_id=document_id,
            title=title,
            owner_id=owner_id,
            organization_id=organization_id,
            shared_with_roles=shared_with_roles or [],
            shared_with_users=[str(uid) for uid in (shared_with_users or [])],
            confidentiality_level=confidentiality_level,
            training_enabled=training_enabled,
            ai_query_enabled=ai_query_enabled,
            download_enabled=download_enabled,
            business_hours_only=business_hours_only,
            tags=tags or [],
            **additional_attributes
        )
        
        return Resource.create(
            resource_type="document",
            resource_id=str(document_id),
            owner_id=owner_id,
            organization_id=organization_id,
            attributes=document_attributes
        )

    def update_document_sharing(
        self,
        document_resource: Resource,
        shared_with_roles: List[str] = None,
        shared_with_users: List[UUID] = None
    ) -> Resource:
        """
        Update document sharing settings.
        
        Args:
            document_resource: Existing document resource
            shared_with_roles: List of role names to share with
            shared_with_users: List of user IDs to share with
            
        Returns:
            Updated resource with new sharing settings
        """
        new_attributes = document_resource.attributes.copy()
        
        if shared_with_roles is not None:
            new_attributes["shared_with_roles"] = shared_with_roles
        
        if shared_with_users is not None:
            new_attributes["shared_with_users"] = [str(uid) for uid in shared_with_users]
        
        return document_resource.update_attributes(new_attributes)

    def check_bulk_document_access(
        self,
        user_id: UUID,
        document_operations: List[Dict[str, Any]],
        chat_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Check access for multiple document operations in bulk.
        
        Args:
            user_id: ID of the user
            document_operations: List of operations with format:
                [{"document_id": UUID, "action": str, "metadata": dict}, ...]
            chat_context: Additional chat context
            
        Returns:
            List of results with format:
                [{"document_id": UUID, "action": str, "allowed": bool, "reason": str}, ...]
        """
        results = []
        
        for operation in document_operations:
            document_id = operation.get("document_id")
            action = operation.get("action", "read")
            
            allowed = self.can_user_access_document_in_chat(
                user_id=user_id,
                document_id=document_id,
                action=action,
                chat_context=chat_context
            )
            
            results.append({
                "document_id": document_id,
                "action": action,
                "allowed": allowed,
                "reason": "Access granted" if allowed else "Access denied",
                "metadata": operation.get("metadata", {})
            })
        
        return results

    def get_accessible_documents_by_tags(
        self,
        user_id: UUID,
        tags: List[str],
        action: str = "ai_query",
        chat_context: Optional[Dict[str, Any]] = None
    ) -> List[UUID]:
        """
        Get documents accessible to user filtered by tags.
        
        This method would typically integrate with a document repository
        to first find documents by tags, then filter by permissions.
        
        Args:
            user_id: ID of the user
            tags: List of tags to filter by
            action: Action being performed
            chat_context: Additional chat context
            
        Returns:
            List of accessible document IDs
        """
        # This is a placeholder - in real implementation,
        # you would integrate with your document service/repository
        # to get documents by tags, then filter by permissions
        
        # Example integration:
        # document_ids = document_repository.find_by_tags(tags, user_organization_id)
        # return self.filter_accessible_documents_for_chat(
        #     user_id, document_ids, action, chat_context
        # )
        
        return []  # Placeholder

    def log_document_access(
        self,
        user_id: UUID,
        document_id: UUID,
        action: str,
        allowed: bool,
        chat_context: Optional[Dict[str, Any]] = None,
        reason: str = ""
    ) -> None:
        """
        Log document access for audit purposes.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document
            action: Action that was attempted
            allowed: Whether access was granted
            chat_context: Chat context information
            reason: Reason for the decision
        """
        # This would integrate with your logging/audit system
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "document_id": str(document_id),
            "action": action,
            "allowed": allowed,
            "reason": reason,
            "chat_context": chat_context or {},
            "service": "chat_document_authorization"
        }
        
        # Example: logger.info("Document access", extra=log_entry)
        # Example: audit_service.log_access(log_entry)
        pass