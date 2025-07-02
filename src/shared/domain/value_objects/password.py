from pydantic import BaseModel
from typing import Any
import bcrypt


class Password(BaseModel, frozen=True):
    """Password value object with bcrypt encryption."""

    hashed_value: str

    @classmethod
    def create(cls, plain_password: str) -> "Password":
        """Create a new password by hashing the plain text."""
        if not plain_password or len(plain_password.strip()) == 0:
            raise ValueError("Password cannot be empty")

        if len(plain_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return cls(hashed_value=hashed.decode("utf-8"))

    @classmethod
    def from_hash(cls, hashed_password: str) -> "Password":
        """Create password object from existing hash."""
        return cls(hashed_value=hashed_password)

    def verify(self, plain_password: str) -> bool:
        """Verify a plain password against this hashed password."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), self.hashed_value.encode("utf-8")
        )

    def __str__(self) -> str:
        return "[PROTECTED]"

    def __repr__(self) -> str:
        return "Password([PROTECTED])"

    def __hash__(self) -> int:
        return hash(self.hashed_value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Password):
            return False
        return self.hashed_value == other.hashed_value
