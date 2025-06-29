from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class FeatureType(str, Enum):
    BOOLEAN = "boolean"
    NUMERIC = "numeric"
    STRING = "string"
    OBJECT = "object"


class FeatureCategory(str, Enum):
    COMMUNICATION = "communication"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    SECURITY = "security"
    CUSTOMIZATION = "customization"
    SUPPORT = "support"


class PlanFeature(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: str
    feature_type: FeatureType
    category: FeatureCategory
    default_value: Any
    configuration_schema: Dict[str, Any]  # JSON schema for feature configuration
    is_system_feature: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True

    model_config = {"frozen": True}

    @classmethod
    def create(
        cls,
        name: str,
        display_name: str,
        description: str,
        feature_type: FeatureType,
        category: FeatureCategory,
        default_value: Any = None,
        configuration_schema: Optional[Dict[str, Any]] = None,
        is_system_feature: bool = False
    ) -> "PlanFeature":
        return cls(
            id=uuid4(),
            name=name,
            display_name=display_name,
            description=description,
            feature_type=feature_type,
            category=category,
            default_value=default_value,
            configuration_schema=configuration_schema or {},
            is_system_feature=is_system_feature,
            created_at=datetime.utcnow(),
            is_active=True
        )

    @classmethod
    def create_chat_whatsapp_feature(cls) -> "PlanFeature":
        """Create the chat_whatsapp feature."""
        return cls.create(
            name="chat_whatsapp",
            display_name="WhatsApp Chat Integration",
            description="Enable WhatsApp chat integration for customer communication",
            feature_type=FeatureType.OBJECT,
            category=FeatureCategory.COMMUNICATION,
            default_value=False,
            configuration_schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "phone_number": {"type": "string"},
                    "webhook_url": {"type": "string"},
                    "auto_reply": {"type": "boolean"},
                    "business_hours": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "start_time": {"type": "string"},
                            "end_time": {"type": "string"},
                            "timezone": {"type": "string"}
                        }
                    }
                }
            },
            is_system_feature=True
        )

    @classmethod
    def create_chat_iframe_feature(cls) -> "PlanFeature":
        """Create the chat_iframe feature."""
        return cls.create(
            name="chat_iframe",
            display_name="Embeddable Chat Widget",
            description="Embed chat widget on websites using iframe",
            feature_type=FeatureType.OBJECT,
            category=FeatureCategory.COMMUNICATION,
            default_value=False,
            configuration_schema={
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean"},
                    "theme": {
                        "type": "object",
                        "properties": {
                            "primary_color": {"type": "string"},
                            "secondary_color": {"type": "string"},
                            "font_family": {"type": "string"},
                            "border_radius": {"type": "number"}
                        }
                    },
                    "position": {
                        "type": "string",
                        "enum": ["bottom-right", "bottom-left", "top-right", "top-left"]
                    },
                    "welcome_message": {"type": "string"},
                    "offline_message": {"type": "string"},
                    "allowed_domains": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            is_system_feature=True
        )

    def update_description(self, description: str) -> "PlanFeature":
        return self.model_copy(update={
            "description": description,
            "updated_at": datetime.utcnow()
        })

    def update_default_value(self, default_value: Any) -> "PlanFeature":
        return self.model_copy(update={
            "default_value": default_value,
            "updated_at": datetime.utcnow()
        })

    def update_configuration_schema(self, schema: Dict[str, Any]) -> "PlanFeature":
        return self.model_copy(update={
            "configuration_schema": schema,
            "updated_at": datetime.utcnow()
        })

    def deactivate(self) -> "PlanFeature":
        if self.is_system_feature:
            raise ValueError("Cannot deactivate system features")
        
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.utcnow()
        })

    def activate(self) -> "PlanFeature":
        return self.model_copy(update={
            "is_active": True,
            "updated_at": datetime.utcnow()
        })

    def validate_configuration(self, config: Any) -> tuple[bool, str]:
        """Validate a configuration against the schema."""
        # Basic validation - in a real implementation, use jsonschema library
        if self.feature_type == FeatureType.BOOLEAN and not isinstance(config, bool):
            return False, "Configuration must be a boolean value"
        
        if self.feature_type == FeatureType.NUMERIC and not isinstance(config, (int, float)):
            return False, "Configuration must be a numeric value"
        
        if self.feature_type == FeatureType.STRING and not isinstance(config, str):
            return False, "Configuration must be a string value"
        
        if self.feature_type == FeatureType.OBJECT and not isinstance(config, dict):
            return False, "Configuration must be an object"
        
        return True, "Configuration is valid"

    def get_typed_default_value(self) -> Any:
        """Get default value with proper typing."""
        if self.feature_type == FeatureType.BOOLEAN:
            return bool(self.default_value) if self.default_value is not None else False
        elif self.feature_type == FeatureType.NUMERIC:
            return self.default_value if self.default_value is not None else 0
        elif self.feature_type == FeatureType.STRING:
            return str(self.default_value) if self.default_value is not None else ""
        elif self.feature_type == FeatureType.OBJECT:
            return self.default_value if self.default_value is not None else {}
        
        return self.default_value

    def is_chat_feature(self) -> bool:
        """Check if this is a chat-related feature."""
        return self.name in ["chat_whatsapp", "chat_iframe"] or self.category == FeatureCategory.COMMUNICATION