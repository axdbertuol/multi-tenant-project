"""JWT service for token generation and validation."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from jose import JWTError, jwt

from shared.infrastructure.config import settings


class JWTTokenPayload:
    """JWT token payload data structure."""
    
    def __init__(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        email: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        exp: Optional[datetime] = None,
        iat: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.organization_id = organization_id
        self.email = email
        self.permissions = permissions or []
        self.roles = roles or []
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.exp = exp or (datetime.utcnow() + settings.jwt_expiration_delta)
        self.iat = iat or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary for JWT encoding."""
        payload = {
            "sub": self.user_id,  # Standard JWT subject claim
            "exp": int(self.exp.timestamp()),  # Standard JWT expiration claim
            "iat": int(self.iat.timestamp()),  # Standard JWT issued at claim
        }
        
        if self.organization_id:
            payload["org_id"] = self.organization_id
        
        if self.email:
            payload["email"] = self.email
        
        if self.permissions:
            payload["permissions"] = self.permissions
        
        if self.roles:
            payload["roles"] = self.roles
        
        if self.user_agent:
            payload["user_agent"] = self.user_agent
        
        if self.ip_address:
            payload["ip_address"] = self.ip_address
        
        return payload
    
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JWTTokenPayload":
        """Create payload from JWT decoded dictionary."""
        return cls(
            user_id=payload["sub"],
            organization_id=payload.get("org_id"),
            email=payload.get("email"),
            permissions=payload.get("permissions", []),
            roles=payload.get("roles", []),
            user_agent=payload.get("user_agent"),
            ip_address=payload.get("ip_address"),
            exp=datetime.fromtimestamp(payload["exp"]) if "exp" in payload else None,
            iat=datetime.fromtimestamp(payload["iat"]) if "iat" in payload else None,
        )


class JWTService:
    """Service for JWT token operations."""
    
    def __init__(self) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        
        # For RS256, we need to handle public/private keys differently
        # For now, fall back to HS256 if RS256 key is not properly configured
        if self._algorithm.startswith("RS") and len(self._secret_key) < 200:
            # RS256 requires a proper private key, fallback to HS256 for development
            self._algorithm = "HS256"
            print("WARNING: RS256 requires proper private key. Falling back to HS256.")
    
    def create_access_token(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        email: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        roles: Optional[List[str]] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a new JWT access token.
        
        Args:
            user_id: User identifier
            organization_id: Organization identifier (for multi-tenant context)
            email: User email (optional)
            permissions: User's effective permissions
            roles: User's role names
            user_agent: Client user agent
            ip_address: Client IP address
            expires_delta: Custom expiration delta, defaults to settings value
        
        Returns:
            Encoded JWT token string
        """
        expire = datetime.utcnow() + (expires_delta or settings.jwt_expiration_delta)
        
        payload = JWTTokenPayload(
            user_id=user_id,
            organization_id=organization_id,
            email=email,
            permissions=permissions,
            roles=roles,
            user_agent=user_agent,
            ip_address=ip_address,
            exp=expire,
        )
        
        encoded_token: str = jwt.encode(
            payload.to_dict(),
            self._secret_key,
            algorithm=self._algorithm
        )
        return encoded_token
    
    def decode_token(self, token: str) -> Optional[JWTTokenPayload]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            JWTTokenPayload if valid, None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return JWTTokenPayload.from_dict(payload)
        except JWTError:
            return None
    
    def is_token_valid(self, token: str) -> bool:
        """
        Check if a JWT token is valid.
        
        Args:
            token: JWT token string
        
        Returns:
            True if valid, False otherwise
        """
        payload = self.decode_token(token)
        if not payload:
            return False
        
        # Check if token is expired
        return payload.exp > datetime.utcnow()
    
    def get_token_user_id(self, token: str) -> Optional[str]:
        """
        Extract user ID from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            User ID if token is valid, None otherwise
        """
        payload = self.decode_token(token)
        return payload.user_id if payload else None
    
    def get_token_organization_id(self, token: str) -> Optional[str]:
        """
        Extract organization ID from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Organization ID if present in valid token, None otherwise
        """
        payload = self.decode_token(token)
        return payload.organization_id if payload else None
    
    def refresh_token(
        self,
        token: str,
        expires_delta: Optional[timedelta] = None,
    ) -> Optional[str]:
        """
        Refresh a JWT token with new expiration.
        
        Args:
            token: Current JWT token
            expires_delta: New expiration delta
        
        Returns:
            New JWT token if current token is valid, None otherwise
        """
        payload = self.decode_token(token)
        if not payload:
            return None
        
        # Create new token with same data but new expiration
        return self.create_access_token(
            user_id=payload.user_id,
            organization_id=payload.organization_id,
            email=payload.email,
            permissions=payload.permissions,
            roles=payload.roles,
            user_agent=payload.user_agent,
            ip_address=payload.ip_address,
            expires_delta=expires_delta,
        )
    
    def has_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if the token holder has a specific permission.
        
        Args:
            token: JWT token string
            required_permission: Permission to check (e.g., "user:read")
        
        Returns:
            True if user has permission, False otherwise
        """
        payload = self.decode_token(token)
        if not payload:
            return False
        
        # Check for exact permission match
        if required_permission in payload.permissions:
            return True
        
        # Check for wildcard permissions
        resource, action = required_permission.split(":", 1) if ":" in required_permission else (required_permission, "")
        
        # Check for resource wildcard (e.g., "user:*")
        if f"{resource}:*" in payload.permissions:
            return True
        
        # Check for global wildcard (e.g., "*:*")
        if "*:*" in payload.permissions:
            return True
        
        # Check for action wildcard (e.g., "*:read")
        if f"*:{action}" in payload.permissions:
            return True
        
        return False
    
    def has_role(self, token: str, required_role: str) -> bool:
        """
        Check if the token holder has a specific role.
        
        Args:
            token: JWT token string
            required_role: Role to check (e.g., "admin")
        
        Returns:
            True if user has role, False otherwise
        """
        payload = self.decode_token(token)
        if not payload:
            return False
        
        return required_role in payload.roles
    
    def get_token_permissions(self, token: str) -> List[str]:
        """
        Extract permissions from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            List of permission strings if token is valid, empty list otherwise
        """
        payload = self.decode_token(token)
        return payload.permissions if payload else []
    
    def get_token_roles(self, token: str) -> List[str]:
        """
        Extract roles from JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            List of role strings if token is valid, empty list otherwise
        """
        payload = self.decode_token(token)
        return payload.roles if payload else []