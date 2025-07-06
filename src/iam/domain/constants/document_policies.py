"""Document-specific ABAC policies for fine-grained access control."""

from typing import List, Dict, Any
from uuid import UUID

from ..entities.policy import Policy, PolicyEffect, PolicyCondition


class DocumentPolicyTemplates:
    """Templates for common document access policies."""

    @staticmethod
    def create_document_owner_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy allowing document owners full access to their documents."""
        return Policy.create(
            name="Document Owner Full Access",
            description="Document owners have full access to documents they created",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="*",  # All actions
            conditions=[
                PolicyCondition(
                    attribute="resource_owner_id",
                    operator="eq",
                    value="{user_id}"  # Placeholder replaced at evaluation
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=100
        )

    @staticmethod
    def create_shared_by_role_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy allowing access to documents shared with user's roles."""
        return Policy.create(
            name="Shared Document Access by Role",
            description="Allow access to documents shared with user's roles",
            effect=PolicyEffect.ALLOW,
            resource_type="document", 
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user_roles",
                    operator="intersects",  # User has any of the shared roles
                    value="{resource.shared_with_roles}"
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=90
        )

    @staticmethod
    def create_shared_by_user_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy allowing access to documents shared with specific users."""
        return Policy.create(
            name="Shared Document Access by User",
            description="Allow access to documents shared with specific users",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="read",
            conditions=[
                PolicyCondition(
                    attribute="user_id",
                    operator="in",
                    value="{resource.shared_with_users}"
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=85
        )

    @staticmethod
    def create_ai_query_permission_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy allowing AI to query documents based on user permissions."""
        return Policy.create(
            name="AI Document Query Permission",
            description="Allow AI to query documents that user has read access to",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="ai_query",
            conditions=[
                # User must have read access to the document
                PolicyCondition(
                    attribute="user_can_read_document",
                    operator="eq",
                    value=True
                ),
                # Document must allow AI querying
                PolicyCondition(
                    attribute="resource.ai_query_enabled",
                    operator="eq", 
                    value=True
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=80
        )

    @staticmethod
    def create_confidentiality_level_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy restricting access based on document confidentiality level."""
        return Policy.create(
            name="Confidentiality Level Access Control",
            description="Restrict access to confidential documents based on user clearance",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="*",
            conditions=[
                # Document is confidential
                PolicyCondition(
                    attribute="resource.confidentiality_level",
                    operator="in",
                    value=["confidential", "restricted", "secret"]
                ),
                # User doesn't have required clearance
                PolicyCondition(
                    attribute="user.clearance_level",
                    operator="not_in",
                    value=["confidential", "restricted", "secret"]
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=150  # High priority for security
        )

    @staticmethod
    def create_training_permission_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy controlling which documents can be used for AI training."""
        return Policy.create(
            name="AI Training Permission",
            description="Control which documents can be used for AI training",
            effect=PolicyEffect.ALLOW,
            resource_type="document",
            action="train",
            conditions=[
                # Document explicitly allows training
                PolicyCondition(
                    attribute="resource.training_enabled",
                    operator="eq",
                    value=True
                ),
                # User has training permission for this document
                PolicyCondition(
                    attribute="user_permissions",
                    operator="contains",
                    value="document:train"
                ),
                # Document is not highly confidential
                PolicyCondition(
                    attribute="resource.confidentiality_level",
                    operator="not_in",
                    value=["restricted", "secret"]
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=95
        )

    @staticmethod
    def create_time_based_access_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy for time-based document access (e.g., business hours only)."""
        return Policy.create(
            name="Business Hours Document Access",
            description="Restrict document access to business hours only",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="*",
            conditions=[
                # Document requires business hours access
                PolicyCondition(
                    attribute="resource.business_hours_only",
                    operator="eq",
                    value=True
                ),
                # Current time is outside business hours
                PolicyCondition(
                    attribute="environment.is_business_hours",
                    operator="eq",
                    value=False
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=120
        )

    @staticmethod
    def create_download_restriction_policy(created_by: UUID, organization_id: UUID) -> Policy:
        """Policy restricting document downloads based on document settings."""
        return Policy.create(
            name="Download Restriction Policy",
            description="Restrict downloads for documents marked as non-downloadable",
            effect=PolicyEffect.DENY,
            resource_type="document",
            action="download",
            conditions=[
                PolicyCondition(
                    attribute="resource.download_enabled",
                    operator="eq",
                    value=False
                )
            ],
            created_by=created_by,
            organization_id=organization_id,
            priority=110
        )


class DocumentPolicyConditionOperators:
    """Custom operators for document policy conditions."""
    
    INTERSECTS = "intersects"  # Check if two arrays have common elements
    NOT_INTERSECTS = "not_intersects"  # Check if two arrays have no common elements
    HAS_ALL = "has_all"  # Check if array contains all specified elements
    HAS_ANY = "has_any"  # Check if array contains any of specified elements


class DocumentAccessValidationHelpers:
    """Helper methods for building document access validation context."""

    @staticmethod
    def build_document_context(
        user_id: UUID,
        user_roles: List[str],
        user_permissions: List[str],
        document_attributes: Dict[str, Any],
        environment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build authorization context for document access."""
        return {
            # User context
            "user_id": str(user_id),
            "user_roles": user_roles,
            "user_permissions": user_permissions,
            
            # Resource context
            "resource_type": "document",
            "resource": document_attributes,
            "resource_owner_id": document_attributes.get("owner_id"),
            
            # Environment context
            "environment": environment,
            "is_business_hours": environment.get("is_business_hours", True),
            "request_time": environment.get("request_time"),
            "request_ip": environment.get("request_ip"),
        }

    @staticmethod
    def build_document_attributes(
        document_id: UUID,
        title: str,
        owner_id: UUID,
        organization_id: UUID,
        shared_with_roles: List[str] = None,
        shared_with_users: List[str] = None,
        confidentiality_level: str = "public",
        training_enabled: bool = True,
        ai_query_enabled: bool = True,
        download_enabled: bool = True,
        business_hours_only: bool = False,
        tags: List[str] = None,
        **additional_attributes
    ) -> Dict[str, Any]:
        """Build document attributes for policy evaluation."""
        return {
            "id": str(document_id),
            "title": title,
            "owner_id": str(owner_id),
            "organization_id": str(organization_id),
            "shared_with_roles": shared_with_roles or [],
            "shared_with_users": shared_with_users or [],
            "confidentiality_level": confidentiality_level,
            "training_enabled": training_enabled,
            "ai_query_enabled": ai_query_enabled,
            "download_enabled": download_enabled,
            "business_hours_only": business_hours_only,
            "tags": tags or [],
            **additional_attributes
        }