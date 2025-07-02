import factory
from datetime import datetime, timedelta
from uuid import uuid4
from faker import Faker
from src.domain.entities.user_session import UserSession, SessionStatus

fake = Faker()


class UserSessionFactory(factory.Factory):
    """Factory for creating UserSession domain entities for testing."""

    class Meta:
        model = UserSession

    id = factory.LazyFunction(uuid4)
    user_id = factory.LazyFunction(uuid4)
    session_token = factory.LazyAttribute(lambda obj: fake.uuid4())
    status = SessionStatus.ACTIVE
    login_at = factory.LazyFunction(lambda: datetime.utcnow())
    logout_at = None
    expires_at = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(hours=1))
    ip_address = factory.LazyAttribute(lambda obj: fake.ipv4())
    user_agent = factory.LazyAttribute(lambda obj: fake.user_agent())
    created_at = factory.LazyFunction(lambda: datetime.utcnow())
    updated_at = None

    @classmethod
    def create_session(cls, **kwargs):
        """Create a session using the domain factory method."""
        user_id = kwargs.get("user_id", uuid4())
        session_token = kwargs.get("session_token", fake.uuid4())
        expires_at = kwargs.get("expires_at", datetime.utcnow() + timedelta(hours=1))
        ip_address = kwargs.get("ip_address", fake.ipv4())
        user_agent = kwargs.get("user_agent", fake.user_agent())

        return UserSession.create(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @classmethod
    def create_active_session(cls, **kwargs):
        """Create an active session."""
        expires_at = kwargs.get("expires_at", datetime.utcnow() + timedelta(hours=1))
        kwargs["expires_at"] = expires_at
        return cls.create_session(**kwargs)

    @classmethod
    def create_expired_session(cls, **kwargs):
        """Create an expired session."""
        expires_at = kwargs.get("expires_at", datetime.utcnow() - timedelta(hours=1))
        kwargs["expires_at"] = expires_at
        return cls.create_session(**kwargs)

    @classmethod
    def create_logged_out_session(cls, **kwargs):
        """Create a logged out session."""
        session = cls.create_session(**kwargs)
        return session.logout()

    @classmethod
    def create_revoked_session(cls, **kwargs):
        """Create a revoked session."""
        session = cls.create_session(**kwargs)
        return session.revoke()

    @classmethod
    def create_multiple_sessions(cls, count=3, user_id=None, **kwargs):
        """Create multiple sessions for the same user."""
        if user_id is None:
            user_id = uuid4()

        sessions = []
        for _ in range(count):
            session_kwargs = kwargs.copy()
            session_kwargs["user_id"] = user_id
            sessions.append(cls.create_session(**session_kwargs))

        return sessions
