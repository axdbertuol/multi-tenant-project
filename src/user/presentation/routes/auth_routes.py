from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import Optional

from ..dependencies import get_auth_use_case
from ...application.dtos.auth_dto import (
    LoginDTO,
    AuthResponseDTO,
    LogoutDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
)
from ...application.use_cases.auth_use_cases import AuthenticationUseCase

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extrai informações do cliente da requisição."""
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    return user_agent, ip_address


@router.post("/login", response_model=AuthResponseDTO)
async def login(
    dto: LoginDTO,
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Autentica o usuário e cria uma sessão."""
    try:
        user_agent, ip_address = get_client_info(request)
        dto.user_agent = user_agent
        dto.ip_address = ip_address
        return use_case.login(dto)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
async def logout(
    dto: LogoutDTO,
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Realiza o logout do usuário, revogando a(s) sessão(ões)."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        success = use_case.logout(token, dto)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session",
            )

        return {"message": "Logged out successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=AuthResponseDTO)
async def refresh_session(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Atualiza o token da sessão."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        result = use_case.refresh_session(token)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/validate")
async def validate_session(
    request: Request,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Valida o token da sessão e retorna as informações do usuário."""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
            )

        token = auth_header.split(" ")[1]
        user = use_case.validate_session(token)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
            )

        return {"user": user}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/password-reset/request")
async def request_password_reset(
    dto: PasswordResetRequestDTO,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Solicita a redefinição de senha para o usuário."""
    try:
        use_case.request_password_reset(dto)
        return {"message": "Password reset email sent if account exists"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    dto: PasswordResetConfirmDTO,
    use_case: AuthenticationUseCase = Depends(get_auth_use_case),
):
    """Confirma a redefinição de senha com o token."""
    try:
        success = use_case.confirm_password_reset(dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        return {"message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
