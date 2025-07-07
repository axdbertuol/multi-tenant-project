import enum


class ResourceTypeEnum(str, enum.Enum):
    """Shared resource type enumeration used across modules."""
    
    # Plan resources
    WHATSAPP_APP = "whatsapp_app"
    WEB_CHAT_APP = "web_chat_app"
    MANAGEMENT_APP = "management_app"
    API_ACCESS = "api_access"
    CUSTOM = "custom"
    
    # IAM resources
    USER = "user"
    ORGANIZATION = "organization"
    ROLE = "role"
    PERMISSION = "permission"
    POLICY = "policy"
    SESSION = "session"
    
    # Application resources
    PLAN = "plan"
    SUBSCRIPTION = "subscription"
    FEATURE_USAGE = "feature_usage"