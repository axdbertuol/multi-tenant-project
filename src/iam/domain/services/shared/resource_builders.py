"""Resource and context builders for IAM services."""

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
from datetime import datetime, timezone

from ...entities.authorization_context import AuthorizationContext
from ...entities.resource import Resource


class ResourceAttributeBuilder:
    """Builder for resource attributes and metadata."""

    @staticmethod
    def build_base_attributes(
        name: str,
        description: Optional[str] = None,
        owner_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        **additional_attributes
    ) -> Dict[str, Any]:
        """
        Build base resource attributes.
        
        Used in: ResourceApplicationService, DocumentAuthorizationService
        """
        base_attrs = {
            "name": name,
            "description": description or f"Resource: {name}",
            "owner_id": str(owner_id) if owner_id else None,
            "organization_id": str(organization_id) if organization_id else None,
            "created_at": (created_at or datetime.now(timezone.utc)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "status": "active",
        }
        
        # Add any additional attributes
        base_attrs.update(additional_attributes)
        
        return base_attrs

    @staticmethod
    def build_application_attributes(
        app_type: str,
        app_name: str,
        app_description: Optional[str] = None,
        enabled_features: Optional[List[str]] = None,
        required_permissions: Optional[List[str]] = None,
        app_config: Optional[Dict[str, Any]] = None,
        **base_attributes
    ) -> Dict[str, Any]:
        """
        Build application-specific resource attributes.
        
        Used in: ResourceApplicationService
        """
        app_attrs = ResourceAttributeBuilder.build_base_attributes(
            name=app_name,
            description=app_description,
            **base_attributes
        )
        
        app_attrs.update({
            "app_type": app_type,
            "app_name": app_name,
            "app_description": app_description or f"{app_type} application",
            "enabled_features": enabled_features or [],
            "required_permissions": required_permissions or [],
            "app_config": app_config or {},
            "category": "application",
        })
        
        return app_attrs

    @staticmethod
    def build_document_attributes(
        doc_name: str,
        doc_type: str,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None,
        checksum: Optional[str] = None,
        access_level: str = "private",
        **base_attributes
    ) -> Dict[str, Any]:
        """
        Build document-specific resource attributes.
        
        Used in: DocumentAuthorizationService
        """
        doc_attrs = ResourceAttributeBuilder.build_base_attributes(
            name=doc_name,
            **base_attributes
        )
        
        doc_attrs.update({
            "doc_type": doc_type,
            "file_size": file_size,
            "mime_type": mime_type,
            "checksum": checksum,
            "access_level": access_level,
            "category": "document",
        })
        
        return doc_attrs

    @staticmethod
    def build_metadata_attributes(
        metadata_type: str,
        metadata_value: Any,
        version: Optional[str] = None,
        **base_attributes
    ) -> Dict[str, Any]:
        """
        Build metadata-specific resource attributes.
        
        Used in: Various services for metadata resources
        """
        metadata_attrs = ResourceAttributeBuilder.build_base_attributes(
            name=f"{metadata_type}_metadata",
            **base_attributes
        )
        
        metadata_attrs.update({
            "metadata_type": metadata_type,
            "metadata_value": metadata_value,
            "version": version or "1.0",
            "category": "metadata",
        })
        
        return metadata_attrs

    @staticmethod
    def add_security_attributes(
        attributes: Dict[str, Any],
        is_public: bool = False,
        encryption_enabled: bool = False,
        access_control_enabled: bool = True,
        audit_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Add security-related attributes to resource.
        
        Used in: Various services for security-sensitive resources
        """
        security_attrs = {
            "is_public": is_public,
            "encryption_enabled": encryption_enabled,
            "access_control_enabled": access_control_enabled,
            "audit_enabled": audit_enabled,
            "security_level": "high" if encryption_enabled else "standard",
        }
        
        attributes.update(security_attrs)
        return attributes

    @staticmethod
    def add_audit_attributes(
        attributes: Dict[str, Any],
        created_by: Optional[UUID] = None,
        updated_by: Optional[UUID] = None,
        audit_trail: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Add audit-related attributes to resource.
        
        Used in: Various services for auditable resources
        """
        audit_attrs = {
            "created_by": str(created_by) if created_by else None,
            "updated_by": str(updated_by) if updated_by else None,
            "audit_trail": audit_trail or [],
            "audit_enabled": True,
        }
        
        attributes.update(audit_attrs)
        return attributes


class AuthorizationContextBuilder:
    """Builder for authorization contexts."""

    @staticmethod
    def build_basic_context(
        user_id: UUID,
        resource_type: str,
        action: str,
        resource_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> AuthorizationContext:
        """
        Build basic authorization context.
        
        Used in: AuthorizationService, ABACService, RBACService
        """
        return AuthorizationContext.create(
            user_id=user_id,
            resource_type=resource_type,
            action=action,
            resource_id=resource_id,
            organization_id=organization_id
        )

    @staticmethod
    def build_context_with_attributes(
        user_id: UUID,
        resource_type: str,
        action: str,
        resource_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        user_attributes: Optional[Dict[str, Any]] = None,
        resource_attributes: Optional[Dict[str, Any]] = None,
        environment_attributes: Optional[Dict[str, Any]] = None
    ) -> AuthorizationContext:
        """
        Build authorization context with custom attributes.
        
        Used in: ABACService, PolicyEvaluationService
        """
        context = AuthorizationContextBuilder.build_basic_context(
            user_id=user_id,
            resource_type=resource_type,
            action=action,
            resource_id=resource_id,
            organization_id=organization_id
        )
        
        # Add custom attributes
        if user_attributes:
            for key, value in user_attributes.items():
                context = context.add_user_attribute(key, value)
        
        if resource_attributes:
            for key, value in resource_attributes.items():
                context = context.add_resource_attribute(key, value)
        
        if environment_attributes:
            for key, value in environment_attributes.items():
                context = context.add_environment_attribute(key, value)
        
        return context

    @staticmethod
    def enrich_context_with_resource(
        context: AuthorizationContext,
        resource: Resource
    ) -> AuthorizationContext:
        """
        Enrich authorization context with resource attributes.
        
        Used in: ABACService, DocumentAuthorizationService
        """
        enriched_context = context
        
        # Add resource attributes
        for key, value in resource.attributes.items():
            enriched_context = enriched_context.add_resource_attribute(key, value)
        
        # Add standard resource attributes
        enriched_context = enriched_context.add_resource_attribute(
            "owner_id", str(resource.owner_id)
        )
        enriched_context = enriched_context.add_resource_attribute(
            "is_active", resource.is_active
        )
        
        if resource.organization_id:
            enriched_context = enriched_context.add_resource_attribute(
                "organization_id", str(resource.organization_id)
            )
        
        return enriched_context


class ConfigurationBuilder:
    """Builder for configuration objects."""

    @staticmethod
    def build_default_config(
        config_type: str,
        config_data: Dict[str, Any],
        organization_id: Optional[UUID] = None,
        version: str = "1.0"
    ) -> Dict[str, Any]:
        """
        Build default configuration object.
        
        Used in: ResourceApplicationService, OrganizationRoleSetupService
        """
        config = {
            "config_type": config_type,
            "version": version,
            "organization_id": str(organization_id) if organization_id else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "config_data": config_data,
        }
        
        return config

    @staticmethod
    def merge_configurations(
        base_config: Dict[str, Any],
        override_config: Dict[str, Any],
        merge_strategy: str = "override"
    ) -> Dict[str, Any]:
        """
        Merge two configuration objects.
        
        Used in: ResourceApplicationService for plan-based configurations
        """
        if merge_strategy == "override":
            merged = base_config.copy()
            merged.update(override_config)
            return merged
        elif merge_strategy == "deep_merge":
            return ConfigurationBuilder._deep_merge(base_config, override_config)
        else:
            return base_config

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigurationBuilder._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result

    @staticmethod
    def apply_template_variables(
        config: Dict[str, Any],
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Apply template variables to configuration.
        
        Used in: ResourceApplicationService for dynamic configurations
        """
        def replace_in_value(value):
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    value = value.replace(f"{{{var_name}}}", var_value)
                # Handle special cases
                if value == "generated_uuid":
                    value = str(uuid4())
                return value
            elif isinstance(value, dict):
                return {k: replace_in_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_in_value(item) for item in value]
            else:
                return value
        
        return {k: replace_in_value(v) for k, v in config.items()}