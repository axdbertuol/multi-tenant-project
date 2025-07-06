"""External API Gateway Service for microservice integration."""

from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum

from .document_authorization_service import DocumentAuthorizationService
from .authorization_service import AuthorizationService
from ..entities.resource import Resource


class ExternalServiceType(str, Enum):
    """Types of external services that can integrate."""
    DOCUMENT_SERVICE = "document_service"
    TRAINING_SERVICE = "training_service"
    RAG_SERVICE = "rag_service"
    MINIO_SERVICE = "minio_service"


class ExternalAPIGatewayService:
    """
    API Gateway service for external microservices to interact with IAM.
    
    This service provides a clean interface for external services to:
    - Validate document permissions
    - Check user access rights
    - Get organization context
    - Log access events
    """

    def __init__(
        self,
        document_auth_service: DocumentAuthorizationService,
        authorization_service: AuthorizationService
    ):
        self.document_auth_service = document_auth_service
        self.authorization_service = authorization_service

    # Document Service Integration APIs
    def validate_document_upload(
        self,
        user_id: UUID,
        organization_id: UUID,
        file_name: str,
        file_size_mb: float,
        file_format: str,
        application_context: str = "management_app"
    ) -> Dict[str, Any]:
        """
        Validate if user can upload a document.
        
        Used by document microservice before accepting uploads.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "limits": dict,
                "metadata": dict
            }
        """
        try:
            # Check if user has document creation permission
            can_create = self.authorization_service.can_user_access_resource(
                user_id=user_id,
                resource_type="document",
                resource_id=organization_id,  # Organization-level check
                action="create",
                additional_context={
                    "application": application_context,
                    "file_format": file_format,
                    "file_size_mb": file_size_mb
                }
            )

            if not can_create:
                return {
                    "allowed": False,
                    "reason": "User does not have permission to upload documents",
                    "limits": {},
                    "metadata": {}
                }

            # TODO: In production, get actual plan limits from Plans service
            # For now, return placeholder limits
            limits = {
                "max_file_size_mb": 50,
                "allowed_formats": ["pdf", "txt", "docx", "md"],
                "daily_upload_limit": 100
            }

            # Validate file constraints
            if file_size_mb > limits["max_file_size_mb"]:
                return {
                    "allowed": False,
                    "reason": f"File size {file_size_mb}MB exceeds limit of {limits['max_file_size_mb']}MB",
                    "limits": limits,
                    "metadata": {}
                }

            if file_format.lower() not in limits["allowed_formats"]:
                return {
                    "allowed": False,
                    "reason": f"File format '{file_format}' not supported",
                    "limits": limits,
                    "metadata": {
                        "supported_formats": limits["allowed_formats"]
                    }
                }

            return {
                "allowed": True,
                "reason": "Upload approved",
                "limits": limits,
                "metadata": {
                    "user_id": str(user_id),
                    "organization_id": str(organization_id),
                    "application": application_context,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }

        except Exception as e:
            return {
                "allowed": False,
                "reason": f"Validation failed: {str(e)}",
                "limits": {},
                "metadata": {"error": True}
            }

    def validate_document_access(
        self,
        user_id: UUID,
        document_id: UUID,
        action: str,
        application_context: str = "management_app"
    ) -> Dict[str, Any]:
        """
        Validate document access for external services.
        
        Used by document/RAG services before serving documents.
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "permissions": dict,
                "context": dict
            }
        """
        try:
            allowed = self.document_auth_service.can_user_access_document(
                user_id=user_id,
                document_id=document_id,
                action=action,
                application_context=application_context
            )

            if allowed:
                # Get full permission set for this document
                permissions = self.document_auth_service.get_user_document_permissions(
                    user_id=user_id,
                    document_id=document_id,
                    application_context=application_context
                )

                return {
                    "allowed": True,
                    "reason": "Access granted",
                    "permissions": permissions,
                    "context": {
                        "user_id": str(user_id),
                        "document_id": str(document_id),
                        "action": action,
                        "application": application_context,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                }
            else:
                return {
                    "allowed": False,
                    "reason": "Access denied",
                    "permissions": {},
                    "context": {}
                }

        except Exception as e:
            return {
                "allowed": False,
                "reason": f"Access validation failed: {str(e)}",
                "permissions": {},
                "context": {"error": True}
            }

    def get_accessible_documents_for_training(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Get documents accessible for AI training.
        
        Used by training microservice to filter training data.
        
        Returns:
            {
                "accessible_documents": list,
                "denied_documents": list,
                "summary": dict
            }
        """
        try:
            accessible_docs, denied_reasons = self.document_auth_service.validate_training_document_access(
                user_id=user_id,
                organization_id=organization_id,
                document_ids=document_ids
            )

            denied_docs = [
                doc_id for doc_id in document_ids 
                if doc_id not in accessible_docs
            ]

            return {
                "accessible_documents": [str(doc_id) for doc_id in accessible_docs],
                "denied_documents": [str(doc_id) for doc_id in denied_docs],
                "summary": {
                    "total_requested": len(document_ids),
                    "accessible_count": len(accessible_docs),
                    "denied_count": len(denied_docs),
                    "access_rate": len(accessible_docs) / len(document_ids) if document_ids else 0,
                    "denied_reasons": denied_reasons
                }
            }

        except Exception as e:
            return {
                "accessible_documents": [],
                "denied_documents": [str(doc_id) for doc_id in document_ids],
                "summary": {
                    "total_requested": len(document_ids),
                    "accessible_count": 0,
                    "denied_count": len(document_ids),
                    "access_rate": 0,
                    "error": str(e)
                }
            }

    def create_document_in_iam(
        self,
        document_id: UUID,
        title: str,
        owner_id: UUID,
        organization_id: UUID,
        document_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a document in IAM system.
        
        Called by document service after successful upload to MINIO.
        
        Returns:
            {
                "success": bool,
                "resource": dict,
                "permissions": dict
            }
        """
        try:
            # Extract permission settings from metadata
            shared_with_roles = document_metadata.get("shared_with_roles", [])
            shared_with_users = document_metadata.get("shared_with_users", [])
            confidentiality_level = document_metadata.get("confidentiality_level", "public")
            ai_training_enabled = document_metadata.get("ai_training_enabled", True)
            ai_query_enabled = document_metadata.get("ai_query_enabled", True)

            # Create document resource in IAM
            document_resource = self.document_auth_service.create_document_resource(
                document_id=document_id,
                title=title,
                owner_id=owner_id,
                organization_id=organization_id,
                shared_with_roles=shared_with_roles,
                shared_with_users=[UUID(uid) for uid in shared_with_users if isinstance(uid, str)],
                confidentiality_level=confidentiality_level,
                ai_training_enabled=ai_training_enabled,
                ai_query_enabled=ai_query_enabled,
                **document_metadata
            )

            return {
                "success": True,
                "resource": {
                    "id": str(document_resource.id),
                    "resource_type": document_resource.resource_type,
                    "resource_id": document_resource.resource_id,
                    "organization_id": str(document_resource.organization_id),
                    "owner_id": str(document_resource.owner_id),
                    "attributes": document_resource.attributes
                },
                "permissions": {
                    "shared_with_roles": shared_with_roles,
                    "shared_with_users": shared_with_users,
                    "confidentiality_level": confidentiality_level,
                    "ai_training_enabled": ai_training_enabled,
                    "ai_query_enabled": ai_query_enabled
                }
            }

        except Exception as e:
            return {
                "success": False,
                "resource": {},
                "permissions": {},
                "error": str(e)
            }

    # RAG Service Integration APIs
    def get_rag_query_context(
        self,
        user_id: UUID,
        organization_id: UUID,
        query: str,
        application_context: str = "web_chat_app"
    ) -> Dict[str, Any]:
        """
        Get context for RAG query with permission filtering.
        
        Used by RAG service to get user-accessible document context.
        
        Returns:
            {
                "allowed": bool,
                "user_context": dict,
                "filters": dict,
                "metadata": dict
            }
        """
        try:
            # Check if user has basic AI query permission
            can_query = self.authorization_service.has_permission(
                user_id=user_id,
                permission="document:ai_query"
            )

            if not can_query:
                return {
                    "allowed": False,
                    "user_context": {},
                    "filters": {},
                    "metadata": {"reason": "User lacks ai_query permission"}
                }

            # Create permission context for RAG filtering
            user_context = self.document_auth_service.create_permission_context_for_external_service(
                user_id=user_id,
                organization_id=organization_id,
                application_context=application_context
            )

            # Create filters for vector search
            filters = {
                "organization_id": str(organization_id),
                "ai_query_enabled": True,
                "application_context": application_context
            }

            return {
                "allowed": True,
                "user_context": user_context,
                "filters": filters,
                "metadata": {
                    "query": query,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service": "rag_service"
                }
            }

        except Exception as e:
            return {
                "allowed": False,
                "user_context": {},
                "filters": {},
                "metadata": {"error": str(e)}
            }

    # General Integration APIs
    def validate_service_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        service_type: ExternalServiceType,
        service_action: str
    ) -> Dict[str, bool]:
        """
        Validate if user can access external service functionality.
        
        Returns permissions for various service actions.
        """
        try:
            permissions = {}

            if service_type == ExternalServiceType.DOCUMENT_SERVICE:
                permissions = {
                    "upload_documents": self.authorization_service.has_permission(user_id, "document:create"),
                    "download_documents": self.authorization_service.has_permission(user_id, "document:read"),
                    "update_documents": self.authorization_service.has_permission(user_id, "document:update"),
                    "delete_documents": self.authorization_service.has_permission(user_id, "document:delete"),
                    "share_documents": self.authorization_service.has_permission(user_id, "document:share"),
                }

            elif service_type == ExternalServiceType.TRAINING_SERVICE:
                permissions = {
                    "access_training_data": self.authorization_service.has_permission(user_id, "document:train"),
                    "trigger_training": self.authorization_service.has_permission(user_id, "training:execute"),
                    "view_training_status": self.authorization_service.has_permission(user_id, "training:read"),
                }

            elif service_type == ExternalServiceType.RAG_SERVICE:
                permissions = {
                    "query_documents": self.authorization_service.has_permission(user_id, "document:ai_query"),
                    "access_vector_search": self.authorization_service.has_permission(user_id, "document:ai_cite"),
                    "view_chat_history": self.authorization_service.has_permission(user_id, "conversation:read"),
                }

            elif service_type == ExternalServiceType.MINIO_SERVICE:
                permissions = {
                    "upload_files": self.authorization_service.has_permission(user_id, "storage:write"),
                    "download_files": self.authorization_service.has_permission(user_id, "storage:read"),
                    "delete_files": self.authorization_service.has_permission(user_id, "storage:delete"),
                }

            return permissions

        except Exception:
            return {}

    def log_external_service_access(
        self,
        user_id: UUID,
        service_type: ExternalServiceType,
        action: str,
        resource_id: Optional[UUID] = None,
        success: bool = True,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log access from external services for audit purposes.
        
        Used by all external services to maintain audit trail.
        """
        try:
            self.document_auth_service.log_document_access(
                user_id=user_id,
                document_id=resource_id,
                action=f"{service_type.value}:{action}",
                allowed=success,
                application_context=service_type.value,
                additional_context=additional_context or {},
                reason="External service access"
            )
        except Exception:
            # Fail silently for logging errors
            pass

    def get_organization_integration_settings(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Get organization-specific integration settings.
        
        Used by external services to configure their behavior per organization.
        
        Returns:
            {
                "document_settings": dict,
                "ai_settings": dict,
                "storage_settings": dict,
                "security_settings": dict
            }
        """
        try:
            # TODO: In production, get actual settings from Plans/Organization services
            # For now, return reasonable defaults
            return {
                "document_settings": {
                    "max_file_size_mb": 50,
                    "supported_formats": ["pdf", "txt", "docx", "md"],
                    "auto_processing": True,
                    "version_control": False
                },
                "ai_settings": {
                    "training_enabled": True,
                    "query_enabled": True,
                    "auto_chunking": True,
                    "semantic_search": True,
                    "content_filtering": True
                },
                "storage_settings": {
                    "minio_bucket": f"org-{organization_id}",
                    "retention_days": None,
                    "encryption_enabled": True,
                    "backup_enabled": True
                },
                "security_settings": {
                    "audit_logging": True,
                    "permission_inheritance": True,
                    "fail_safe_mode": True,
                    "rate_limiting": True
                }
            }

        except Exception:
            return {}

    def health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint for external services.
        
        Returns current status of IAM system dependencies.
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "document_authorization": "healthy",
                "authorization_service": "healthy",
                "database": "healthy"  # In production, check actual DB health
            },
            "version": "1.0.0"
        }