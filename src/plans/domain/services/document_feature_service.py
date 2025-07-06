"""Document feature service for managing document capabilities within plans."""

from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from enum import Enum

from ..entities.plan_resource import PlanResource, PlanResourceType
from ..entities.plan import Plan


class DocumentFeatureTier(str, Enum):
    """Document feature tiers for different plan levels."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class DocumentFeatureService:
    """Service for managing document storage features within plans."""

    def __init__(self):
        self._feature_tiers = self._initialize_feature_tiers()

    def _initialize_feature_tiers(self) -> Dict[DocumentFeatureTier, Dict[str, Any]]:
        """Initialize document feature configurations for different tiers."""
        return {
            DocumentFeatureTier.BASIC: {
                "max_documents": 50,
                "max_storage_gb": 1,
                "max_file_size_mb": 10,
                "ai_training_enabled": False,
                "ai_query_enabled": False,
                "document_sharing": False,
                "advanced_permissions": False,
                "supported_formats": ["txt", "md"],
                "features": [
                    "document_upload",
                    "document_download",
                    "basic_search",
                ]
            },
            DocumentFeatureTier.STANDARD: {
                "max_documents": 200,
                "max_storage_gb": 5,
                "max_file_size_mb": 25,
                "ai_training_enabled": True,
                "ai_query_enabled": True,
                "document_sharing": True,
                "advanced_permissions": False,
                "supported_formats": ["pdf", "txt", "docx", "md"],
                "features": [
                    "document_upload",
                    "document_download",
                    "document_preview",
                    "basic_search",
                    "document_sharing",
                    "share_links",
                    "ai_integration",
                    "vector_storage",
                ]
            },
            DocumentFeatureTier.PREMIUM: {
                "max_documents": 1000,
                "max_storage_gb": 20,
                "max_file_size_mb": 50,
                "ai_training_enabled": True,
                "ai_query_enabled": True,
                "document_sharing": True,
                "advanced_permissions": True,
                "supported_formats": ["pdf", "txt", "docx", "md", "pptx", "xlsx"],
                "features": [
                    "document_upload",
                    "document_download",
                    "document_preview",
                    "basic_search",
                    "document_sharing",
                    "share_links",
                    "ai_integration",
                    "vector_storage",
                    "advanced_permissions",
                    "audit_logging",
                    "permission_templates",
                ]
            },
            DocumentFeatureTier.ENTERPRISE: {
                "max_documents": 10000,
                "max_storage_gb": 100,
                "max_file_size_mb": 100,
                "ai_training_enabled": True,
                "ai_query_enabled": True,
                "document_sharing": True,
                "advanced_permissions": True,
                "supported_formats": ["pdf", "txt", "docx", "md", "pptx", "xlsx", "csv", "json"],
                "features": [
                    "document_upload",
                    "document_download",
                    "document_preview",
                    "basic_search",
                    "document_sharing",
                    "share_links",
                    "ai_integration",
                    "vector_storage",
                    "advanced_permissions",
                    "audit_logging",
                    "permission_templates",
                    "bulk_operations",
                    "api_integration",
                    "custom_workflows",
                ]
            }
        }

    def create_document_storage_for_plan(
        self,
        plan_id: UUID,
        tier: DocumentFeatureTier
    ) -> PlanResource:
        """Create document storage resource for a plan based on tier."""
        tier_config = self._feature_tiers[tier]
        
        return PlanResource.create_document_storage_resource(
            plan_id=plan_id,
            max_documents=tier_config["max_documents"],
            max_storage_gb=tier_config["max_storage_gb"],
            ai_training_enabled=tier_config["ai_training_enabled"],
            ai_query_enabled=tier_config["ai_query_enabled"],
            document_sharing=tier_config["document_sharing"],
            advanced_permissions=tier_config["advanced_permissions"],
            supported_formats=tier_config["supported_formats"],
        )

    def get_document_limits_for_tier(self, tier: DocumentFeatureTier) -> Dict[str, int]:
        """Get document limits for a specific tier."""
        tier_config = self._feature_tiers[tier]
        return {
            "max_documents": tier_config["max_documents"],
            "max_storage_gb": tier_config["max_storage_gb"],
            "max_file_size_mb": tier_config["max_file_size_mb"],
        }

    def get_document_features_for_tier(self, tier: DocumentFeatureTier) -> List[str]:
        """Get enabled document features for a specific tier."""
        return self._feature_tiers[tier]["features"]

    def validate_document_usage(
        self,
        document_resource: PlanResource,
        current_documents: int,
        current_storage_gb: float,
        new_document_size_mb: float
    ) -> Tuple[bool, List[str]]:
        """Validate if document upload is within plan limits."""
        if document_resource.resource_type != PlanResourceType.DOCUMENT_STORAGE:
            return False, ["Resource is not a document storage resource"]

        errors = []
        warnings = []

        # Check document count limit
        max_documents = document_resource.get_max_documents()
        if current_documents >= max_documents:
            errors.append(f"Document limit reached ({current_documents}/{max_documents})")

        # Check storage limit
        max_storage_gb = document_resource.get_max_storage_gb()
        new_storage_gb = current_storage_gb + (new_document_size_mb / 1024)
        if new_storage_gb > max_storage_gb:
            errors.append(f"Storage limit would be exceeded ({new_storage_gb:.2f}GB/{max_storage_gb}GB)")

        # Check file size limit
        max_file_size_mb = document_resource.get_max_file_size_mb()
        if new_document_size_mb > max_file_size_mb:
            errors.append(f"File size exceeds limit ({new_document_size_mb:.2f}MB/{max_file_size_mb}MB)")

        # Add warnings for approaching limits
        if current_documents >= max_documents * 0.9:
            warnings.append(f"Approaching document limit ({current_documents}/{max_documents})")

        if new_storage_gb >= max_storage_gb * 0.9:
            warnings.append(f"Approaching storage limit ({new_storage_gb:.2f}GB/{max_storage_gb}GB)")

        return len(errors) == 0, errors + warnings

    def can_use_ai_features(
        self,
        document_resource: PlanResource,
        feature_type: str
    ) -> bool:
        """Check if AI features are available for the document resource."""
        if document_resource.resource_type != PlanResourceType.DOCUMENT_STORAGE:
            return False

        if feature_type == "training":
            return document_resource.is_ai_training_enabled()
        elif feature_type == "query":
            return document_resource.is_ai_query_enabled()
        elif feature_type == "semantic_search":
            return document_resource.get_ai_feature_setting("semantic_search") is True
        
        return False

    def can_use_permission_features(
        self,
        document_resource: PlanResource,
        feature_type: str
    ) -> bool:
        """Check if permission features are available for the document resource."""
        if document_resource.resource_type != PlanResourceType.DOCUMENT_STORAGE:
            return False

        if feature_type == "sharing":
            return document_resource.is_document_sharing_enabled()
        elif feature_type == "advanced_permissions":
            return document_resource.supports_advanced_permissions()
        elif feature_type == "role_based_access":
            return document_resource.get_permission_feature_setting("role_based_access") is True
        elif feature_type == "user_based_access":
            return document_resource.get_permission_feature_setting("user_based_access") is True
        elif feature_type == "confidentiality_levels":
            return document_resource.get_permission_feature_setting("confidentiality_levels") is True
        elif feature_type == "time_based_access":
            return document_resource.get_permission_feature_setting("time_based_access") is True
        
        return False

    def upgrade_document_storage_tier(
        self,
        document_resource: PlanResource,
        new_tier: DocumentFeatureTier
    ) -> PlanResource:
        """Upgrade document storage to a higher tier."""
        new_tier_config = self._feature_tiers[new_tier]
        
        # Update limits
        updated_resource = document_resource.update_document_limits(
            max_documents=new_tier_config["max_documents"],
            max_storage_gb=new_tier_config["max_storage_gb"],
            max_file_size_mb=new_tier_config["max_file_size_mb"]
        )

        # Update AI features
        updated_resource = updated_resource.enable_ai_feature(
            "ai_training_enabled", 
            new_tier_config["ai_training_enabled"]
        )
        updated_resource = updated_resource.enable_ai_feature(
            "ai_query_enabled",
            new_tier_config["ai_query_enabled"]
        )

        # Update permission features
        updated_resource = updated_resource.enable_permission_feature(
            "document_sharing",
            new_tier_config["document_sharing"]
        )
        updated_resource = updated_resource.enable_permission_feature(
            "user_based_access",
            new_tier_config["advanced_permissions"]
        )
        updated_resource = updated_resource.enable_permission_feature(
            "confidentiality_levels",
            new_tier_config["advanced_permissions"]
        )

        # Update enabled features
        for feature in new_tier_config["features"]:
            if not updated_resource.has_feature(feature):
                updated_resource = updated_resource.add_enabled_feature(feature)

        return updated_resource

    def get_tier_by_limits(
        self,
        max_documents: int,
        max_storage_gb: int
    ) -> Optional[DocumentFeatureTier]:
        """Determine tier based on document limits."""
        for tier, config in self._feature_tiers.items():
            if (config["max_documents"] >= max_documents and 
                config["max_storage_gb"] >= max_storage_gb):
                return tier
        return None

    def compare_tiers(
        self,
        current_tier: DocumentFeatureTier,
        target_tier: DocumentFeatureTier
    ) -> Dict[str, Any]:
        """Compare two tiers to show differences."""
        current_config = self._feature_tiers[current_tier]
        target_config = self._feature_tiers[target_tier]

        comparison = {
            "limits": {
                "max_documents": {
                    "current": current_config["max_documents"],
                    "target": target_config["max_documents"],
                    "increase": target_config["max_documents"] - current_config["max_documents"]
                },
                "max_storage_gb": {
                    "current": current_config["max_storage_gb"],
                    "target": target_config["max_storage_gb"],
                    "increase": target_config["max_storage_gb"] - current_config["max_storage_gb"]
                },
                "max_file_size_mb": {
                    "current": current_config["max_file_size_mb"],
                    "target": target_config["max_file_size_mb"],
                    "increase": target_config["max_file_size_mb"] - current_config["max_file_size_mb"]
                }
            },
            "features": {
                "current": set(current_config["features"]),
                "target": set(target_config["features"]),
                "new": set(target_config["features"]) - set(current_config["features"]),
                "removed": set(current_config["features"]) - set(target_config["features"])
            },
            "capabilities": {
                "ai_training": {
                    "current": current_config["ai_training_enabled"],
                    "target": target_config["ai_training_enabled"]
                },
                "ai_query": {
                    "current": current_config["ai_query_enabled"],
                    "target": target_config["ai_query_enabled"]
                },
                "document_sharing": {
                    "current": current_config["document_sharing"],
                    "target": target_config["document_sharing"]
                },
                "advanced_permissions": {
                    "current": current_config["advanced_permissions"],
                    "target": target_config["advanced_permissions"]
                }
            }
        }

        return comparison

    def get_integration_capabilities(
        self,
        document_resource: PlanResource
    ) -> Dict[str, bool]:
        """Get integration capabilities for external microservices."""
        if document_resource.resource_type != PlanResourceType.DOCUMENT_STORAGE:
            return {}

        return {
            # Document microservice integration
            "document_crud": True,  # All tiers support basic CRUD
            "bulk_upload": document_resource.has_feature("bulk_operations"),
            "api_integration": document_resource.has_feature("api_integration"),
            
            # Training microservice integration
            "ai_training_allowed": document_resource.is_ai_training_enabled(),
            "auto_chunking": document_resource.get_ai_feature_setting("auto_chunking") is True,
            "vector_storage": document_resource.has_feature("vector_storage"),
            
            # RAG service integration
            "ai_query_allowed": document_resource.is_ai_query_enabled(),
            "semantic_search": document_resource.get_ai_feature_setting("semantic_search") is True,
            
            # IAM service integration
            "role_based_permissions": document_resource.get_permission_feature_setting("role_based_access") is True,
            "user_based_permissions": document_resource.get_permission_feature_setting("user_based_access") is True,
            "sharing_controls": document_resource.is_document_sharing_enabled(),
            "audit_logging": document_resource.has_feature("audit_logging"),
            
            # MINIO integration
            "minio_storage": True,  # All tiers use MINIO
            "retention_policies": document_resource.get_document_setting("retention_days") is not None,
            "version_control": document_resource.get_document_setting("version_control") is True,
        }