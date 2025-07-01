import re
from typing import Any
import bcrypt
from pydantic import BaseModel


class Password(BaseModel, frozen=True):
    """Objeto de valor para Senha com criptografia bcrypt e regras de validação."""

    hashed_value: str

    @classmethod
    def create(cls, plain_password: str) -> "Password":
        """Cria uma nova senha fazendo hash do texto simples."""
        cls._validate_password_strength(plain_password)

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return cls(hashed_value=hashed.decode("utf-8"))

    @classmethod
    def from_hash(cls, hashed_password: str) -> "Password":
        """Cria um objeto de senha a partir de um hash existente."""
        return cls(hashed_value=hashed_password)

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        """Valida a força da senha de acordo com as regras de negócio."""
        if not password or len(password.strip()) == 0:
            raise ValueError("Password cannot be empty")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if len(password) > 128:
            raise ValueError("Password cannot exceed 128 characters")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")

    def verify(self, plain_password: str) -> bool:
        """Verifica uma senha simples em relação a esta senha hash."""
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
