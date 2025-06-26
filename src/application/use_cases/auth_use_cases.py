from typing import Optional
from domain.repositories.unit_of_work import UnitOfWork
from domain.entities.user import User
from application.dtos.auth_dto import SignupDto, LoginDto, AuthResponseDto, UserInfoDto
from application.services.jwt_service import JWTService
from application.use_cases.session_use_cases import SessionUseCases


class AuthUseCases:
    def __init__(self, uow: UnitOfWork, jwt_service: JWTService):
        self.uow = uow
        self.jwt_service = jwt_service
        self.session_use_cases = SessionUseCases(uow, jwt_service)
    
    def _to_user_info_dto(self, user: User) -> UserInfoDto:
        return UserInfoDto(
            id=user.id,
            email=str(user.email.value),
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def signup(self, signup_dto: SignupDto, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuthResponseDto:
        async with self.uow:
            existing_user = await self.uow.users.get_by_email(signup_dto.email)
            if existing_user:
                raise ValueError(f"User with email {signup_dto.email} already exists")
            
            user = User.create(
                email=signup_dto.email,
                name=signup_dto.name,
                password=signup_dto.password
            )
            
            created_user = await self.uow.users.create(user)
            
            # Create session for the new user
            session, access_token = await self.session_use_cases.create_session(
                user_id=created_user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return AuthResponseDto(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.jwt_service.access_token_expire_minutes * 60,
                user=self._to_user_info_dto(created_user)
            )
    
    async def login(self, login_dto: LoginDto, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[AuthResponseDto]:
        async with self.uow:
            user = await self.uow.users.get_by_email(login_dto.email)
            if not user:
                return None
            
            if not user.is_active:
                raise ValueError("User account is deactivated")
            
            if not user.verify_password(login_dto.password):
                return None
            
            # Create session for the login
            session, access_token = await self.session_use_cases.create_session(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return AuthResponseDto(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.jwt_service.access_token_expire_minutes * 60,
                user=self._to_user_info_dto(user)
            )
    
    async def get_current_user(self, token: str) -> Optional[UserInfoDto]:
        # Validate session first
        session = await self.session_use_cases.validate_session(token)
        if not session:
            return None
        
        token_payload = self.jwt_service.verify_token(token)
        if not token_payload:
            return None
        
        async with self.uow:
            user = await self.uow.users.get_by_id(token_payload.user_id)
            if not user or not user.is_active:
                return None
            
            return self._to_user_info_dto(user)
    
    async def verify_token(self, token: str) -> bool:
        session = await self.session_use_cases.validate_session(token)
        return session is not None
    
    async def logout(self, token: str) -> bool:
        """Logout current session."""
        try:
            await self.session_use_cases.logout_session(token)
            return True
        except ValueError:
            return False