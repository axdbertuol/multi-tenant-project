from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from typing import List
from uuid import UUID

from ..dependencies import get_session_use_case
from ...application.dtos.session_dto import (
    SessionCreateDTO,
    SessionResponseDTO,
    SessionListResponseDTO,
)
from ...application.use_cases.session_use_cases import SessionUseCase

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def get_auth_token(request: Request) -> str:
    """Extract and validate authorization token from request."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
        )
    return auth_header.split(" ")[1]


@router.post("/", response_model=SessionResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_session(
    dto: SessionCreateDTO,
    request: Request,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Create a new user session."""
    try:
        # Add client info to DTO
        dto.user_agent = request.headers.get("user-agent")
        dto.ip_address = request.client.host if request.client else None
        
        return use_case.create_session(dto)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponseDTO)
async def get_session_by_id(
    session_id: UUID,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Get session by ID."""
    try:
        session = use_case.get_session_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-token/{token}", response_model=SessionResponseDTO)
async def get_session_by_token(
    token: str,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Get session by token."""
    try:
        session = use_case.get_session_by_token(token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/user/{user_id}", response_model=SessionListResponseDTO)
async def get_user_sessions(
    user_id: UUID,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Get all sessions for a user."""
    try:
        return use_case.get_user_sessions(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{session_id}")
async def revoke_session(
    session_id: UUID,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Revoke a specific session."""
    try:
        success = use_case.revoke_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return {"message": "Session revoked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/by-token/{token}")
async def revoke_session_by_token(
    token: str,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Revoke session by token."""
    try:
        success = use_case.revoke_session_by_token(token)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        return {"message": "Session revoked successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/user/{user_id}/all")
async def revoke_all_user_sessions(
    user_id: UUID,
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Revoke all sessions for a user."""
    try:
        count = use_case.revoke_all_user_sessions(user_id)
        return {"message": f"Revoked {count} sessions"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{session_id}/extend", response_model=SessionResponseDTO)
async def extend_session(
    session_id: UUID,
    hours: int = Query(24, ge=1, le=720, description="Hours to extend session"),
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Extend session duration."""
    try:
        session = use_case.extend_session(session_id, hours)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or invalid",
            )
        return session
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_sessions(
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Clean up expired sessions."""
    try:
        count = use_case.cleanup_expired_sessions()
        return {"message": f"Cleaned up {count} expired sessions"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/validate/{token}")
async def validate_session_access(
    token: str,
    permissions: List[str] = Query(None, description="Required permissions"),
    use_case: SessionUseCase = Depends(get_session_use_case),
):
    """Validate session and optional permissions."""
    try:
        valid = use_case.validate_session_access(token, permissions)
        return {"valid": valid, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))