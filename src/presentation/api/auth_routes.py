from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from application.use_cases.auth_use_cases import AuthUseCases
from application.use_cases.session_use_cases import SessionUseCases
from application.dtos.auth_dto import SignupDto, LoginDto, AuthResponseDto, UserInfoDto
from application.dtos.session_dto import LogoutDto, LogoutResponseDto, UserSessionsResponseDto
from application.services.jwt_service import JWTService
from domain.repositories.unit_of_work import UnitOfWork
from infrastructure.repositories.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from infrastructure.database.connection import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


def get_unit_of_work(db=Depends(get_db)) -> UnitOfWork:
    return SQLAlchemyUnitOfWork(db)


def get_jwt_service() -> JWTService:
    return JWTService()


def get_auth_use_cases(
    uow: UnitOfWork = Depends(get_unit_of_work),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> AuthUseCases:
    return AuthUseCases(uow, jwt_service)


def get_session_use_cases(
    uow: UnitOfWork = Depends(get_unit_of_work),
    jwt_service: JWTService = Depends(get_jwt_service)
) -> SessionUseCases:
    return SessionUseCases(uow, jwt_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
) -> UserInfoDto:
    token = credentials.credentials
    user = await auth_use_cases.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


@router.post("/signup", response_model=AuthResponseDto, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_dto: SignupDto,
    request: Request,
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        return await auth_use_cases.signup(signup_dto, ip_address, user_agent)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during signup"
        )


@router.post("/login", response_model=AuthResponseDto)
async def login(
    login_dto: LoginDto,
    request: Request,
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        auth_response = await auth_use_cases.login(login_dto, ip_address, user_agent)
        if not auth_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        return auth_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )


@router.get("/me", response_model=UserInfoDto)
async def get_current_user_info(
    current_user: UserInfoDto = Depends(get_current_user)
):
    return current_user


@router.post("/verify-token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_use_cases: AuthUseCases = Depends(get_auth_use_cases)
):
    token = credentials.credentials
    is_valid = await auth_use_cases.verify_token(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return {"valid": True}


@router.post("/logout", response_model=LogoutResponseDto)
async def logout(
    logout_dto: LogoutDto,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: UserInfoDto = Depends(get_current_user),
    session_use_cases: SessionUseCases = Depends(get_session_use_cases)
):
    try:
        token = credentials.credentials
        
        if logout_dto.revoke_all_sessions:
            # Get current session ID from token to exclude it
            jwt_service = JWTService()
            token_payload = jwt_service.verify_token(token)
            current_session_id = token_payload.session_id if token_payload else None
            
            return await session_use_cases.logout_all_sessions(
                user_id=current_user.id,
                except_session_id=current_session_id
            )
        else:
            return await session_use_cases.logout_session(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )


@router.get("/sessions", response_model=UserSessionsResponseDto)
async def get_user_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: UserInfoDto = Depends(get_current_user),
    session_use_cases: SessionUseCases = Depends(get_session_use_cases)
):
    try:
        token = credentials.credentials
        return await session_use_cases.get_user_sessions(
            user_id=current_user.id,
            current_session_token=token
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching sessions"
        )


@router.post("/logout-all", response_model=LogoutResponseDto)
async def logout_all_sessions(
    current_user: UserInfoDto = Depends(get_current_user),
    session_use_cases: SessionUseCases = Depends(get_session_use_cases)
):
    try:
        return await session_use_cases.logout_all_sessions(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during logout"
        )