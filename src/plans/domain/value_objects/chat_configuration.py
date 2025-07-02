from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
import re


class BusinessHours(BaseModel):
    enabled: bool = False
    start_time: str = "09:00"
    end_time: str = "17:00"
    timezone: str = "UTC"

    model_config = {"frozen": True}

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$", v):
            raise ValueError("Time must be in HH:MM format")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        # Basic timezone validation - in production, use pytz or zoneinfo
        if not v or len(v) > 50:
            raise ValueError("Invalid timezone")
        return v


class ChatWhatsAppConfiguration(BaseModel):
    enabled: bool = False
    phone_number: Optional[str] = None
    webhook_url: Optional[str] = None
    auto_reply: bool = True
    business_hours: BusinessHours = BusinessHours()
    welcome_message: str = "Hello! How can we help you today?"
    away_message: str = (
        "We're currently away. Please leave a message and we'll get back to you soon."
    )

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        # Remove common phone number formatting
        cleaned = re.sub(r"[^\d+]", "", v)

        if not re.match(r"^\+?[1-9]\d{1,14}$", cleaned):
            raise ValueError("Invalid phone number format")

        return cleaned

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        if not re.match(r"^https?://.+", v):
            raise ValueError("Webhook URL must be a valid HTTP/HTTPS URL")

        return v

    @field_validator("welcome_message", "away_message")
    @classmethod
    def validate_messages(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("Message cannot exceed 500 characters")
        return v.strip()

    @classmethod
    def create_default(cls) -> "ChatWhatsAppConfiguration":
        return cls()

    def enable(
        self, phone_number: str, webhook_url: Optional[str] = None
    ) -> "ChatWhatsAppConfiguration":
        return self.model_copy(
            update={
                "enabled": True,
                "phone_number": phone_number,
                "webhook_url": webhook_url,
            }
        )

    def disable(self) -> "ChatWhatsAppConfiguration":
        return self.model_copy(update={"enabled": False})

    def update_business_hours(
        self, business_hours: BusinessHours
    ) -> "ChatWhatsAppConfiguration":
        return self.model_copy(update={"business_hours": business_hours})

    def update_messages(
        self, welcome: Optional[str] = None, away: Optional[str] = None
    ) -> "ChatWhatsAppConfiguration":
        updates = {}
        if welcome is not None:
            updates["welcome_message"] = welcome
        if away is not None:
            updates["away_message"] = away

        return self.model_copy(update=updates)

    def is_properly_configured(self) -> tuple[bool, List[str]]:
        """Check if configuration is valid and complete."""
        issues = []

        if self.enabled:
            if not self.phone_number:
                issues.append("Phone number is required when WhatsApp chat is enabled")

            if self.business_hours.enabled:
                try:
                    start_hour, start_min = map(
                        int, self.business_hours.start_time.split(":")
                    )
                    end_hour, end_min = map(
                        int, self.business_hours.end_time.split(":")
                    )

                    start_minutes = start_hour * 60 + start_min
                    end_minutes = end_hour * 60 + end_min

                    if start_minutes >= end_minutes:
                        issues.append(
                            "Business hours start time must be before end time"
                        )

                except ValueError:
                    issues.append("Invalid business hours time format")

        return len(issues) == 0, issues


class ChatTheme(BaseModel):
    primary_color: str = "#007bff"
    secondary_color: str = "#6c757d"
    font_family: str = "Arial, sans-serif"
    border_radius: int = 8

    model_config = {"frozen": True}

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g., #007bff)")
        return v.lower()

    @field_validator("border_radius")
    @classmethod
    def validate_border_radius(cls, v: int) -> int:
        if not 0 <= v <= 50:
            raise ValueError("Border radius must be between 0 and 50 pixels")
        return v


class ChatIframeConfiguration(BaseModel):
    enabled: bool = False
    theme: ChatTheme = ChatTheme()
    position: str = "bottom-right"
    welcome_message: str = "Hi there! How can we help you?"
    offline_message: str = "We're currently offline. Please leave a message."
    allowed_domains: List[str] = []
    show_agent_avatar: bool = True
    show_timestamps: bool = True
    enable_file_upload: bool = False
    enable_emoji: bool = True

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        valid_positions = ["bottom-right", "bottom-left", "top-right", "top-left"]
        if v not in valid_positions:
            raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
        return v

    @field_validator("welcome_message", "offline_message")
    @classmethod
    def validate_messages(cls, v: str) -> str:
        if len(v) > 200:
            raise ValueError("Message cannot exceed 200 characters")
        return v.strip()

    @field_validator("allowed_domains")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        validated_domains = []

        for domain in v:
            # Basic domain validation
            if not re.match(
                r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$",
                domain,
            ):
                raise ValueError(f"Invalid domain format: {domain}")
            validated_domains.append(domain.lower())

        return validated_domains

    @classmethod
    def create_default(cls) -> "ChatIframeConfiguration":
        return cls()

    def enable(
        self, allowed_domains: Optional[List[str]] = None
    ) -> "ChatIframeConfiguration":
        return self.model_copy(
            update={"enabled": True, "allowed_domains": allowed_domains or []}
        )

    def disable(self) -> "ChatIframeConfiguration":
        return self.model_copy(update={"enabled": False})

    def update_theme(self, theme: ChatTheme) -> "ChatIframeConfiguration":
        return self.model_copy(update={"theme": theme})

    def add_allowed_domain(self, domain: str) -> "ChatIframeConfiguration":
        if domain.lower() not in [d.lower() for d in self.allowed_domains]:
            new_domains = self.allowed_domains + [domain.lower()]
            return self.model_copy(update={"allowed_domains": new_domains})
        return self

    def remove_allowed_domain(self, domain: str) -> "ChatIframeConfiguration":
        new_domains = [d for d in self.allowed_domains if d.lower() != domain.lower()]
        return self.model_copy(update={"allowed_domains": new_domains})

    def update_position(self, position: str) -> "ChatIframeConfiguration":
        return self.model_copy(update={"position": position})

    def update_messages(
        self, welcome: Optional[str] = None, offline: Optional[str] = None
    ) -> "ChatIframeConfiguration":
        updates = {}
        if welcome is not None:
            updates["welcome_message"] = welcome
        if offline is not None:
            updates["offline_message"] = offline

        return self.model_copy(update=updates)

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed to embed the chat."""
        if not self.allowed_domains:  # Empty list means all domains allowed
            return True

        return domain.lower() in [d.lower() for d in self.allowed_domains]

    def get_embed_code(self, organization_id: str, chat_endpoint: str) -> str:
        """Generate iframe embed code."""
        params = {
            "org": organization_id,
            "theme": self.theme.primary_color.replace("#", ""),
            "position": self.position,
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f'''<iframe 
    src="{chat_endpoint}?{param_string}" 
    width="350" 
    height="500" 
    frameborder="0"
    style="position: fixed; {self._get_position_style()}; z-index: 9999;">
</iframe>'''

    def _get_position_style(self) -> str:
        """Get CSS positioning style based on position setting."""
        positions = {
            "bottom-right": "bottom: 20px; right: 20px;",
            "bottom-left": "bottom: 20px; left: 20px;",
            "top-right": "top: 20px; right: 20px;",
            "top-left": "top: 20px; left: 20px;",
        }
        return positions.get(self.position, positions["bottom-right"])

    def to_client_config(self) -> Dict[str, Any]:
        """Get configuration safe for client-side use."""
        return {
            "theme": {
                "primaryColor": self.theme.primary_color,
                "secondaryColor": self.theme.secondary_color,
                "fontFamily": self.theme.font_family,
                "borderRadius": self.theme.border_radius,
            },
            "position": self.position,
            "welcomeMessage": self.welcome_message,
            "offlineMessage": self.offline_message,
            "showAgentAvatar": self.show_agent_avatar,
            "showTimestamps": self.show_timestamps,
            "enableFileUpload": self.enable_file_upload,
            "enableEmoji": self.enable_emoji,
        }
