"""Application settings configuration."""

from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator, validator
from pydantic_settings import BaseSettings

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings configuration."""

    # Database settings
    database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/ddd_app",
        env="DATABASE_URL",
    )

    # External API settings
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # JWT settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production", env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=15, env="JWT_EXPIRATION_MINUTES")
    jwt_refresh_expiration_hours: int = Field(
        default=24, env="JWT_REFRESH_EXPIRATION_HOURS"
    )

    # Session settings (for backward compatibility with existing sessions)
    session_expiration_hours: int = Field(default=24, env="SESSION_EXPIRATION_HOURS")
    session_remember_me_hours: int = Field(
        default=720, env="SESSION_REMEMBER_ME_HOURS"
    )  # 30 days

    @field_validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key is set for production."""
        if v == "your-secret-key-change-in-production":
            # For development, generate a warning but allow it
            print("WARNING: Using default JWT secret key. Change this in production!")
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

    @field_validator("jwt_algorithm")  # noqa: F821
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm is supported."""
        supported_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in supported_algorithms:
            raise ValueError(f"JWT algorithm must be one of: {supported_algorithms}")
        return v

    @property
    def jwt_expiration_delta(self) -> timedelta:
        """Get JWT expiration as timedelta (short-lived for security)."""
        return timedelta(minutes=self.jwt_expiration_minutes)

    @property
    def jwt_refresh_expiration_delta(self) -> timedelta:
        """Get JWT refresh expiration as timedelta."""
        return timedelta(hours=self.jwt_refresh_expiration_hours)

    @property
    def session_expiration_delta(self) -> timedelta:
        """Get session expiration as timedelta."""
        return timedelta(hours=self.session_expiration_hours)

    @property
    def session_remember_me_delta(self) -> timedelta:
        """Get remember me session expiration as timedelta."""
        return timedelta(hours=self.session_remember_me_hours)

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
