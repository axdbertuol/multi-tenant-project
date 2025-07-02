from typing import Dict, Any, Optional, List
import requests
import time
from urllib.parse import urlparse

from ..entities.plan_resource import PlanResourceType


class PlanResourceService:
    """Domain service for plan resource configuration and testing."""

    def validate_configuration(
        self, resource_type: PlanResourceType, configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and normalize resource configuration based on type."""
        if resource_type == PlanResourceType.CHAT_WHATSAPP:
            return self._validate_whatsapp_configuration(configuration)
        elif resource_type == PlanResourceType.CHAT_IFRAME:
            return self._validate_iframe_configuration(configuration)
        elif resource_type == PlanResourceType.CUSTOM:
            return self._validate_custom_configuration(configuration)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

    def test_configuration(
        self,
        resource_type: PlanResourceType,
        configuration: Dict[str, Any],
        test_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Test a resource configuration and return test results."""
        test_parameters = test_parameters or {}

        if resource_type == PlanResourceType.CHAT_WHATSAPP:
            return self._test_whatsapp_configuration(configuration, test_parameters)
        elif resource_type == PlanResourceType.CHAT_IFRAME:
            return self._test_iframe_configuration(configuration, test_parameters)
        elif resource_type == PlanResourceType.CUSTOM:
            return self._test_custom_configuration(configuration, test_parameters)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

    def _validate_whatsapp_configuration(
        self, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate WhatsApp chat resource configuration."""
        validated_config = {}

        # Required fields
        if "api_key" not in config or not config["api_key"]:
            raise ValueError("WhatsApp API key is required")
        validated_config["api_key"] = str(config["api_key"]).strip()

        if "phone_number" not in config or not config["phone_number"]:
            raise ValueError("WhatsApp phone number is required")
        validated_config["phone_number"] = str(config["phone_number"]).strip()

        # Optional fields with defaults
        validated_config["messages_per_day"] = int(config.get("messages_per_day", 1000))
        validated_config["auto_reply"] = bool(config.get("auto_reply", True))
        validated_config["business_verification"] = bool(
            config.get("business_verification", False)
        )

        # Webhook configuration
        if "webhook_url" in config and config["webhook_url"]:
            webhook_url = str(config["webhook_url"]).strip()
            if not self._is_valid_url(webhook_url):
                raise ValueError("Invalid webhook URL format")
            validated_config["webhook_url"] = webhook_url

        if "webhook_secret" in config:
            validated_config["webhook_secret"] = str(config["webhook_secret"])

        # Rate limiting
        validated_config["rate_limit_per_minute"] = int(
            config.get("rate_limit_per_minute", 60)
        )
        validated_config["burst_limit"] = int(config.get("burst_limit", 10))

        # Message templates
        if "welcome_message" in config:
            validated_config["welcome_message"] = str(config["welcome_message"])[:500]

        if "default_response" in config:
            validated_config["default_response"] = str(config["default_response"])[:500]

        return validated_config

    def _validate_iframe_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate iframe chat resource configuration."""
        validated_config = {}

        # Required fields
        if "widget_id" not in config or not config["widget_id"]:
            raise ValueError("Widget ID is required")
        validated_config["widget_id"] = str(config["widget_id"]).strip()

        # Domain restrictions
        if "allowed_domains" in config:
            domains = config["allowed_domains"]
            if isinstance(domains, str):
                domains = [d.strip() for d in domains.split(",") if d.strip()]
            elif isinstance(domains, list):
                domains = [str(d).strip() for d in domains if str(d).strip()]
            else:
                raise ValueError("allowed_domains must be a string or list")

            # Validate domain formats
            validated_domains = []
            for domain in domains:
                if self._is_valid_domain(domain):
                    validated_domains.append(domain.lower())
                else:
                    raise ValueError(f"Invalid domain format: {domain}")
            validated_config["allowed_domains"] = validated_domains

        # Appearance settings
        validated_config["theme"] = config.get("theme", "light")
        if validated_config["theme"] not in ["light", "dark", "auto"]:
            validated_config["theme"] = "light"

        validated_config["primary_color"] = config.get("primary_color", "#007bff")
        validated_config["position"] = config.get("position", "bottom-right")
        if validated_config["position"] not in [
            "bottom-right",
            "bottom-left",
            "top-right",
            "top-left",
        ]:
            validated_config["position"] = "bottom-right"

        # Size settings
        validated_config["width"] = min(max(int(config.get("width", 350)), 250), 500)
        validated_config["height"] = min(max(int(config.get("height", 500)), 300), 800)

        # Behavior settings
        validated_config["auto_open"] = bool(config.get("auto_open", False))
        validated_config["show_agent_avatar"] = bool(
            config.get("show_agent_avatar", True)
        )
        validated_config["enable_file_upload"] = bool(
            config.get("enable_file_upload", True)
        )
        validated_config["enable_emoji"] = bool(config.get("enable_emoji", True))

        # Custom branding
        if "company_name" in config:
            validated_config["company_name"] = str(config["company_name"])[:100]

        if "agent_name" in config:
            validated_config["agent_name"] = str(config["agent_name"])[:50]

        if "welcome_message" in config:
            validated_config["welcome_message"] = str(config["welcome_message"])[:500]

        return validated_config

    def _validate_custom_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate custom resource configuration."""
        # For custom resources, we perform basic validation
        validated_config = {}

        # Ensure configuration is not empty
        if not config:
            raise ValueError("Custom resource configuration cannot be empty")

        # Copy all fields, ensuring they are JSON serializable
        for key, value in config.items():
            if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                validated_config[key] = value
            else:
                # Convert to string for non-JSON serializable types
                validated_config[key] = str(value)

        return validated_config

    def _test_whatsapp_configuration(
        self, config: Dict[str, Any], test_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test WhatsApp configuration."""
        results = {
            "success": True,
            "tests_performed": [],
            "api_connection": False,
            "webhook_reachable": False,
            "response_time_ms": 0,
        }

        start_time = time.time()

        try:
            # Test 1: API Key validation
            results["tests_performed"].append("api_key_validation")
            api_key = config.get("api_key")
            phone_number = config.get("phone_number")

            if len(api_key) < 10:
                results["success"] = False
                results["api_connection"] = False
                results["error"] = "API key appears to be invalid (too short)"
            else:
                results["api_connection"] = True

            # Test 2: Webhook reachability (if configured)
            if "webhook_url" in config and config["webhook_url"]:
                results["tests_performed"].append("webhook_reachability")
                webhook_url = config["webhook_url"]

                try:
                    # Test webhook with a simple HEAD request
                    response = requests.head(webhook_url, timeout=5)
                    if response.status_code < 500:  # Accept 2xx, 3xx, 4xx as reachable
                        results["webhook_reachable"] = True
                    else:
                        results["webhook_reachable"] = False
                        results["webhook_error"] = f"HTTP {response.status_code}"
                except requests.RequestException as e:
                    results["webhook_reachable"] = False
                    results["webhook_error"] = str(e)
            else:
                results["webhook_reachable"] = True  # No webhook to test

            # Test 3: Rate limiting validation
            results["tests_performed"].append("rate_limit_validation")
            rate_limit = config.get("rate_limit_per_minute", 60)
            if rate_limit <= 0 or rate_limit > 1000:
                results["success"] = False
                results["rate_limit_error"] = (
                    "Rate limit should be between 1-1000 messages per minute"
                )

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        end_time = time.time()
        results["response_time_ms"] = int((end_time - start_time) * 1000)

        return results

    def _test_iframe_configuration(
        self, config: Dict[str, Any], test_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test iframe configuration."""
        results = {
            "success": True,
            "tests_performed": [],
            "widget_valid": False,
            "domains_valid": False,
            "load_time_ms": 0,
        }

        start_time = time.time()

        try:
            # Test 1: Widget ID validation
            results["tests_performed"].append("widget_validation")
            widget_id = config.get("widget_id")

            if len(widget_id) >= 8:  # Basic length check
                results["widget_valid"] = True
            else:
                results["success"] = False
                results["widget_error"] = "Widget ID appears to be invalid"

            # Test 2: Domain validation
            results["tests_performed"].append("domain_validation")
            allowed_domains = config.get("allowed_domains", [])

            if isinstance(allowed_domains, list) and len(allowed_domains) > 0:
                valid_domains = all(
                    self._is_valid_domain(domain) for domain in allowed_domains
                )
                results["domains_valid"] = valid_domains
                if not valid_domains:
                    results["success"] = False
                    results["domain_error"] = "One or more domains are invalid"
            else:
                results["domains_valid"] = True  # No domain restrictions

            # Test 3: Configuration completeness
            results["tests_performed"].append("configuration_completeness")
            required_fields = ["widget_id"]
            missing_fields = [
                field for field in required_fields if not config.get(field)
            ]

            if missing_fields:
                results["success"] = False
                results["missing_fields"] = missing_fields

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        end_time = time.time()
        results["load_time_ms"] = int((end_time - start_time) * 1000)

        return results

    def _test_custom_configuration(
        self, config: Dict[str, Any], test_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test custom resource configuration."""
        results = {
            "success": True,
            "tests_performed": ["basic_validation"],
            "configuration_valid": False,
        }

        try:
            # Basic validation - ensure config is not empty and has required structure
            if not config:
                results["success"] = False
                results["error"] = "Configuration is empty"
            elif not isinstance(config, dict):
                results["success"] = False
                results["error"] = "Configuration must be a dictionary"
            else:
                results["configuration_valid"] = True

        except Exception as e:
            results["success"] = False
            results["error"] = str(e)

        return results

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in [
                "http",
                "https",
            ]
        except Exception:
            return False

    def _is_valid_domain(self, domain: str) -> bool:
        """Check if domain format is valid."""
        if not domain:
            return False

        # Remove protocol if present
        if domain.startswith(("http://", "https://")):
            domain = domain.split("://", 1)[1]

        # Remove path if present
        domain = domain.split("/")[0]

        # Basic domain validation
        if "." not in domain:
            return False

        parts = domain.split(".")
        return all(part and part.replace("-", "").isalnum() for part in parts)

    def get_default_configuration(
        self, resource_type: PlanResourceType
    ) -> Dict[str, Any]:
        """Get default configuration for a resource type."""
        if resource_type == PlanResourceType.CHAT_WHATSAPP:
            return {
                "messages_per_day": 1000,
                "auto_reply": True,
                "business_verification": False,
                "rate_limit_per_minute": 60,
                "burst_limit": 10,
                "welcome_message": "Welcome! How can I help you today?",
                "default_response": "Thank you for your message. We'll get back to you soon.",
            }
        elif resource_type == PlanResourceType.CHAT_IFRAME:
            return {
                "theme": "light",
                "primary_color": "#007bff",
                "position": "bottom-right",
                "width": 350,
                "height": 500,
                "auto_open": False,
                "show_agent_avatar": True,
                "enable_file_upload": True,
                "enable_emoji": True,
                "welcome_message": "Hello! How can we assist you?",
            }
        elif resource_type == PlanResourceType.CUSTOM:
            return {
                "description": "Custom resource configuration",
                "enabled": True,
            }
        else:
            return {}

    def get_configuration_schema(
        self, resource_type: PlanResourceType
    ) -> Dict[str, Any]:
        """Get configuration schema for a resource type."""
        if resource_type == PlanResourceType.CHAT_WHATSAPP:
            return {
                "type": "object",
                "required": ["api_key", "phone_number"],
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "WhatsApp Business API key",
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "WhatsApp business phone number",
                    },
                    "messages_per_day": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100000,
                    },
                    "auto_reply": {"type": "boolean"},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "webhook_secret": {"type": "string"},
                    "rate_limit_per_minute": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 1000,
                    },
                    "burst_limit": {"type": "integer", "minimum": 1, "maximum": 100},
                    "welcome_message": {"type": "string", "maxLength": 500},
                    "default_response": {"type": "string", "maxLength": 500},
                },
            }
        elif resource_type == PlanResourceType.CHAT_IFRAME:
            return {
                "type": "object",
                "required": ["widget_id"],
                "properties": {
                    "widget_id": {
                        "type": "string",
                        "description": "Unique widget identifier",
                    },
                    "allowed_domains": {"type": "array", "items": {"type": "string"}},
                    "theme": {"type": "string", "enum": ["light", "dark", "auto"]},
                    "primary_color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                    "position": {
                        "type": "string",
                        "enum": [
                            "bottom-right",
                            "bottom-left",
                            "top-right",
                            "top-left",
                        ],
                    },
                    "width": {"type": "integer", "minimum": 250, "maximum": 500},
                    "height": {"type": "integer", "minimum": 300, "maximum": 800},
                    "auto_open": {"type": "boolean"},
                    "show_agent_avatar": {"type": "boolean"},
                    "enable_file_upload": {"type": "boolean"},
                    "enable_emoji": {"type": "boolean"},
                    "company_name": {"type": "string", "maxLength": 100},
                    "agent_name": {"type": "string", "maxLength": 50},
                    "welcome_message": {"type": "string", "maxLength": 500},
                },
            }
        elif resource_type == PlanResourceType.CUSTOM:
            return {
                "type": "object",
                "description": "Custom resource configuration schema (flexible)",
                "additionalProperties": True,
            }
        else:
            return {"type": "object", "additionalProperties": False}
