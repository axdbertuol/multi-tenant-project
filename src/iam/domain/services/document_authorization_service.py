"""Document authorization service for validating document access across applications and microservices."""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone
import logging

from .authorization_service import AuthorizationService
from .rbac_service import RBACService
from .abac_service import ABACService
from ..entities.resource import Resource
from ..constants.document_policies import DocumentAccessValidationHelpers
from ..repositories.resource_repository import ResourceRepository


class DocumentAuthorizationService:
    """
    Core document authorization service for multi-application and microservice integration.
    
    This service provides permission validation for documents across:
    - Management app (document CRUD)
    - Chat applications (iframe/whatsapp)
    - External microservices (document service, training service, RAG service)
    """

    def __init__(
        self,
        authorization_service: AuthorizationService,
        rbac_service: RBACService,
        abac_service: ABACService,
        resource_repository: Optional[ResourceRepository] = None
    ):
        self.authorization_service = authorization_service
        self.rbac_service = rbac_service
        self.abac_service = abac_service
        self.resource_repository = resource_repository
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def can_user_access_document(
        self,
        user_id: UUID,
        document_id: UUID,
        action: str = "read",
        application_context: str = "management_app",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if user can access a document for a specific action and application.
        
        This is the primary method for external microservices to validate document access.
        
        Args:
            user_id: ID of the user requesting access
            document_id: ID of the document
            action: Action being performed (read, write, delete, ai_query, train, etc.)
            application_context: Application making the request (management_app, web_chat_app, whatsapp_app)
            additional_context: Additional context (session info, etc.)
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            context = additional_context or {}
            context["application"] = application_context
            
            return self.authorization_service.can_user_access_resource(
                user_id=user_id,
                resource_type="document",
                resource_id=document_id,
                action=action,
                additional_context=context
            )
        except Exception:
            # Fail securely - deny access on any error
            return False

    def validate_bulk_document_access(
        self,
        user_id: UUID,
        document_ids: List[UUID],
        action: str = "read",
        application_context: str = "management_app"
    ) -> Dict[UUID, bool]:
        """
        Validate access to multiple documents efficiently.
        
        Optimized for external services that need to check many documents.
        
        Args:
            user_id: ID of the user
            document_ids: List of document IDs to check
            action: Action being performed
            application_context: Application context
            
        Returns:
            Dictionary mapping document_id to permission status
        """
        results = {}
        
        # For now, iterate through documents
        # In production, this could be optimized with batch operations
        for doc_id in document_ids:
            results[doc_id] = self.can_user_access_document(
                user_id=user_id,
                document_id=doc_id,
                action=action,
                application_context=application_context
            )
        
        return results

    def get_user_document_permissions(
        self,
        user_id: UUID,
        document_id: UUID,
        application_context: str = "management_app"
    ) -> Dict[str, bool]:
        """
        Get all document permissions for a user.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document
            application_context: Application context
            
        Returns:
            Dictionary mapping action names to permission status
        """
        actions = [
            "read", "create", "update", "delete", "share", 
            "download", "ai_query", "ai_cite", "train", "manage"
        ]
        
        permissions = {}
        for action in actions:
            permissions[action] = self.can_user_access_document(
                user_id=user_id,
                document_id=document_id,
                action=action,
                application_context=application_context
            )
        
        return permissions

    def create_document_resource(
        self,
        document_id: UUID,
        title: str,
        owner_id: UUID,
        organization_id: UUID,
        shared_with_roles: List[str] = None,
        shared_with_users: List[UUID] = None,
        confidentiality_level: str = "public",
        ai_query_enabled: bool = True,
        training_enabled: bool = True,
        download_enabled: bool = True,
        tags: List[str] = None,
        **additional_attributes
    ) -> Resource:
        """
        Create a Resource entity for a document with appropriate attributes.
        
        This integrates documents into the existing Resource system for authorization.
        Used by external document services to register documents with the IAM system.
        """
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

    def update_document_permissions(
        self,
        document_resource: Resource,
        shared_with_roles: Optional[List[str]] = None,
        shared_with_users: Optional[List[UUID]] = None,
        confidentiality_level: Optional[str] = None,
        ai_query_enabled: Optional[bool] = None,
        training_enabled: Optional[bool] = None
    ) -> Resource:
        """
        Update document permissions and return updated resource.
        
        Used by external document services to update document permissions.
        
        Args:
            document_resource: Existing document resource
            shared_with_roles: New roles to share with
            shared_with_users: New users to share with
            confidentiality_level: New confidentiality level
            ai_query_enabled: New AI query setting
            training_enabled: New training setting
            
        Returns:
            Updated resource with new permission settings
        """
        new_attributes = document_resource.attributes.copy()
        
        if shared_with_roles is not None:
            new_attributes["shared_with_roles"] = shared_with_roles
        
        if shared_with_users is not None:
            new_attributes["shared_with_users"] = [str(uid) for uid in shared_with_users]
        
        if confidentiality_level is not None:
            new_attributes["confidentiality_level"] = confidentiality_level
            
        if ai_query_enabled is not None:
            new_attributes["ai_query_enabled"] = ai_query_enabled
            
        if training_enabled is not None:
            new_attributes["training_enabled"] = training_enabled
        
        return document_resource.update_attributes(new_attributes)

    def get_accessible_documents_for_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        action: str = "read",
        application_context: str = "management_app",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UUID]:
        """
        Get documents accessible to a user for specific action.
        
        Args:
            user_id: ID of the user
            organization_id: Organization scope
            action: Action being performed
            application_context: Application context
            filters: Additional filters (tags, content type, etc.)
            
        Returns:
            List of accessible document IDs
        """
        if not self.resource_repository:
            return []
        
        try:
            # Get all document resources in the organization
            document_resources = self.resource_repository.find_by_organization_and_type(
                organization_id, "document"
            )
            
            accessible_documents = []
            
            # Filter documents by user permissions
            for resource in document_resources:
                document_id = UUID(resource.resource_id)
                
                # Check if user can access this document
                if self.can_user_access_document(
                    user_id=user_id,
                    document_id=document_id,
                    action=action,
                    application_context=application_context
                ):
                    # Apply additional filters if provided
                    if filters:
                        if self._matches_filters(resource, filters):
                            accessible_documents.append(document_id)
                    else:
                        accessible_documents.append(document_id)
            
            return accessible_documents
            
        except Exception:
            # Fail securely - return empty list on error
            return []
    
    def _matches_filters(self, resource: Resource, filters: Dict[str, Any]) -> bool:
        """Check if a resource matches the provided filters."""
        try:
            for filter_key, filter_value in filters.items():
                if filter_key == "tags":
                    resource_tags = resource.get_attribute("tags", [])
                    if isinstance(filter_value, list):
                        # Check if resource has any of the specified tags
                        if not any(tag in resource_tags for tag in filter_value):
                            return False
                    else:
                        if filter_value not in resource_tags:
                            return False
                elif filter_key == "confidentiality_level":
                    resource_level = resource.get_attribute("confidentiality_level", "public")
                    if resource_level != filter_value:
                        return False
                elif filter_key == "content_type":
                    resource_type = resource.get_attribute("content_type", "")
                    if resource_type != filter_value:
                        return False
                else:
                    # Generic attribute matching
                    resource_value = resource.get_attribute(filter_key)
                    if resource_value != filter_value:
                        return False
            return True
        except Exception:
            return False

    def validate_training_document_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_ids: List[UUID]
    ) -> Tuple[List[UUID], List[str]]:
        """
        Validate which documents can be used for AI training.
        
        Used by training microservices to filter training data.
        
        Args:
            user_id: ID of the user requesting training
            organization_id: Organization context
            document_ids: List of document IDs to validate
            
        Returns:
            Tuple of (accessible_document_ids, access_denied_reasons)
        """
        accessible_docs = []
        denied_reasons = []
        
        training_permissions = self.validate_bulk_document_access(
            user_id=user_id,
            document_ids=document_ids,
            action="train",
            application_context="training_service"
        )
        
        for doc_id, can_train in training_permissions.items():
            if can_train:
                accessible_docs.append(doc_id)
            else:
                denied_reasons.append(f"Training denied for document {doc_id}")
        
        return accessible_docs, denied_reasons

    def create_permission_context_for_external_service(
        self,
        user_id: UUID,
        organization_id: UUID,
        application_context: str,
        document_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive permission context for external services.
        
        This provides all the context external services need for permission-aware operations.
        
        Args:
            user_id: ID of the user
            organization_id: Organization context
            application_context: Application making the request
            document_ids: Optional list of specific documents to check
            
        Returns:
            Permission context dictionary for external service use
        """
        # Get user roles and permissions (would integrate with user service)
        user_roles = self._get_user_roles(user_id, organization_id)
        user_permissions = self._get_user_permissions(user_id)
        
        context = {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "application": application_context,
            "user_roles": user_roles,
            "user_permissions": user_permissions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add document-specific permissions if requested
        if document_ids:
            document_permissions = {}
            for doc_id in document_ids:
                document_permissions[str(doc_id)] = self.get_user_document_permissions(
                    user_id=user_id,
                    document_id=doc_id,
                    application_context=application_context
                )
            context["document_permissions"] = document_permissions
        
        return context

    def _get_user_roles(self, user_id: UUID, organization_id: UUID) -> List[str]:
        """Get user's roles in the organization."""
        return self.rbac_service.get_user_roles_in_organization(user_id, organization_id)

    def _get_user_permissions(self, user_id: UUID) -> List[str]:
        """Get user's permissions."""
        try:
            return self.authorization_service.get_user_permissions(user_id)
        except Exception:
            return []

    def log_document_access(
        self,
        user_id: UUID,
        document_id: Optional[UUID],
        action: str,
        allowed: bool,
        application_context: str = "unknown",
        additional_context: Optional[Dict[str, Any]] = None,
        reason: str = ""
    ) -> None:
        """
        Log document access for audit purposes.
        
        Args:
            user_id: ID of the user
            document_id: ID of the document (if applicable)
            action: Action that was attempted
            allowed: Whether access was granted
            application_context: Application that made the request
            additional_context: Additional context information
            reason: Reason for the decision
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": str(user_id),
            "document_id": str(document_id) if document_id else None,
            "action": action,
            "allowed": allowed,
            "application": application_context,
            "reason": reason,
            "context": additional_context or {},
            "service": "document_authorization"
        }
        
        # Log as structured JSON for audit systems
        if allowed:
            self.logger.info(
                "Document access granted",
                extra={"audit_log": log_entry}
            )
        else:
            self.logger.warning(
                "Document access denied",
                extra={"audit_log": log_entry}
            )