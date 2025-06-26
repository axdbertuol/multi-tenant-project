from typing import Optional
from application.use_cases.auth_use_cases import AuthUseCases
from application.dtos.auth_dto import SignupDto, LoginDto, AuthResponseDto, UserInfoDto


class AuthService:
    """Application service facade for authentication operations."""
    
    def __init__(self, auth_use_cases: AuthUseCases):
        self.auth_use_cases = auth_use_cases
    
    async def signup(self, signup_dto: SignupDto) -> AuthResponseDto:
        return await self.auth_use_cases.signup(signup_dto)
    
    async def login(self, login_dto: LoginDto) -> Optional[AuthResponseDto]:
        return await self.auth_use_cases.login(login_dto)
    
    async def get_current_user(self, token: str) -> Optional[UserInfoDto]:
        return await self.auth_use_cases.get_current_user(token)
    
    def verify_token(self, token: str) -> bool:
        return self.auth_use_cases.verify_token(token)