from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import Request

from domain.repositories.unit_of_work import UnitOfWork
from domain.entities.user_session import UserSession
from application.dtos.session_dto import (
    SessionInfoDto, UserSessionsResponseDto, LogoutDto, 
    LogoutResponseDto, SessionStatsDto
)
from application.services.jwt_service import JWTService


class SessionUseCases:
    def __init__(self, uow: UnitOfWork, jwt_service: JWTService):
        self.uow = uow
        self.jwt_service = jwt_service

    def _to_session_info_dto(self, session: UserSession, current_session_id: Optional[UUID] = None) -> SessionInfoDto:
        return SessionInfoDto(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            login_at=session.login_at,
            logout_at=session.logout_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            is_current=session.id == current_session_id,
            session_duration=session.get_session_duration()
        )

    async def create_session(
        self, 
        user_id: UUID, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None
    ) -> tuple[UserSession, str]:
        """Create a new user session and return session with JWT token."""
        async with self.uow:
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(minutes=self.jwt_service.access_token_expire_minutes)
            
            # Create session without token first
            session = UserSession.create(
                user_id=user_id,
                session_token="",  # Will be updated with actual JWT
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Create the session in database to get the ID
            created_session = await self.uow.user_sessions.create(session)
            
            # Get user for JWT creation
            user = await self.uow.users.get_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Create JWT token with session ID
            access_token, _ = self.jwt_service.create_access_token(
                user_id=user.id,
                email=str(user.email.value),
                session_id=created_session.id
            )
            
            # Update session with the actual JWT token
            updated_session = created_session.model_copy(update={
                "session_token": access_token,
                "updated_at": datetime.utcnow()
            })
            
            final_session = await self.uow.user_sessions.update(updated_session)
            return final_session, access_token

    async def logout_session(self, session_token: str) -> LogoutResponseDto:
        """Logout a specific session."""
        async with self.uow:
            session = await self.uow.user_sessions.get_by_session_token(session_token)
            if not session:
                raise ValueError("Session not found")
            
            if not session.is_active():
                raise ValueError("Session is not active")
            
            logged_out_session = session.logout()
            await self.uow.user_sessions.update(logged_out_session)
            
            return LogoutResponseDto(
                message="Session logged out successfully",
                revoked_sessions_count=1
            )

    async def logout_all_sessions(self, user_id: UUID, except_session_id: Optional[UUID] = None) -> LogoutResponseDto:
        """Logout all sessions for a user, optionally excluding current session."""
        async with self.uow:
            if except_session_id:
                # Get all active sessions except the current one
                all_sessions = await self.uow.user_sessions.get_active_sessions_by_user_id(user_id)
                sessions_to_logout = [s for s in all_sessions if s.id != except_session_id]
                
                count = 0
                for session in sessions_to_logout:
                    logged_out_session = session.logout()
                    await self.uow.user_sessions.update(logged_out_session)
                    count += 1
                
                return LogoutResponseDto(
                    message=f"Logged out {count} other sessions",
                    revoked_sessions_count=count
                )
            else:
                # Logout all sessions using repository method
                count = await self.uow.user_sessions.expire_sessions_by_user_id(user_id)
                return LogoutResponseDto(
                    message=f"Logged out all {count} sessions",
                    revoked_sessions_count=count
                )

    async def get_user_sessions(self, user_id: UUID, current_session_token: Optional[str] = None) -> UserSessionsResponseDto:
        """Get all sessions for a user."""
        async with self.uow:
            sessions = await self.uow.user_sessions.get_all_sessions_by_user_id(user_id)
            
            # Determine current session ID from token
            current_session_id = None
            if current_session_token:
                token_payload = self.jwt_service.verify_token(current_session_token)
                if token_payload and token_payload.session_id:
                    current_session_id = token_payload.session_id
            
            session_dtos = [
                self._to_session_info_dto(session, current_session_id) 
                for session in sessions
            ]
            
            active_count = sum(1 for session in sessions if session.is_active())
            
            return UserSessionsResponseDto(
                sessions=session_dtos,
                total_sessions=len(sessions),
                active_sessions=active_count
            )

    async def revoke_session(self, session_id: UUID, admin_user_id: UUID) -> LogoutResponseDto:
        """Revoke a session (admin action)."""
        async with self.uow:
            session = await self.uow.user_sessions.get_by_id(session_id)
            if not session:
                raise ValueError("Session not found")
            
            revoked_session = session.revoke()
            await self.uow.user_sessions.update(revoked_session)
            
            return LogoutResponseDto(
                message="Session revoked by admin",
                revoked_sessions_count=1
            )

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        async with self.uow:
            return await self.uow.user_sessions.cleanup_expired_sessions()

    async def get_session_stats(self, user_id: UUID) -> SessionStatsDto:
        """Get session statistics for a user."""
        async with self.uow:
            sessions = await self.uow.user_sessions.get_all_sessions_by_user_id(user_id)
            
            stats = {
                "total_sessions": len(sessions),
                "active_sessions": 0,
                "expired_sessions": 0,
                "logged_out_sessions": 0,
                "revoked_sessions": 0
            }
            
            for session in sessions:
                if session.status.value == "active" and session.is_active():
                    stats["active_sessions"] += 1
                elif session.status.value == "expired" or (session.status.value == "active" and session.is_expired()):
                    stats["expired_sessions"] += 1
                elif session.status.value == "logged_out":
                    stats["logged_out_sessions"] += 1
                elif session.status.value == "revoked":
                    stats["revoked_sessions"] += 1
            
            return SessionStatsDto(**stats)

    async def validate_session(self, session_token: str) -> Optional[UserSession]:
        """Validate if a session is still active and not expired."""
        async with self.uow:
            session = await self.uow.user_sessions.get_by_session_token(session_token)
            if not session:
                return None
            
            if not session.is_active():
                return None
            
            # Auto-expire if needed
            if session.is_expired():
                expired_session = session.expire()
                await self.uow.user_sessions.update(expired_session)
                return None
            
            return session