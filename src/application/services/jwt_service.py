import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from application.dtos.auth_dto import TokenPayloadDto


class JWTService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    def create_access_token(self, user_id: UUID, email: str, session_id: Optional[UUID] = None) -> tuple[str, datetime]:
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "user_id": str(user_id),
            "email": email,
            "exp": expire,
            "iat": now
        }
        
        if session_id:
            payload["session_id"] = str(session_id)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token, expire
    
    def verify_token(self, token: str) -> Optional[TokenPayloadDto]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            user_id = UUID(payload.get("user_id"))
            email = payload.get("email")
            session_id = UUID(payload.get("session_id")) if payload.get("session_id") else None
            exp = datetime.fromtimestamp(payload.get("exp"))
            iat = datetime.fromtimestamp(payload.get("iat"))
            
            if not user_id or not email:
                return None
                
            return TokenPayloadDto(
                user_id=user_id,
                email=email,
                session_id=session_id,
                exp=exp,
                iat=iat
            )
        except (JWTError, ValueError, TypeError):
            return None
    
    def is_token_expired(self, token: str) -> bool:
        payload_data = self.verify_token(token)
        if not payload_data:
            return True
        
        return datetime.utcnow() > payload_data.exp