import re
from typing import Any
from pydantic import BaseModel, field_validator, validate_email


class Email(BaseModel):
    """Objeto de valor para Email."""

    value: str

    model_config = {"frozen": True}

    @field_validator("value")
    def _validate_email(cls, v: str) -> str:
        if not validate_email(v):
            raise ValueError(f"Invalid email format: {v}")
        return v.lower().strip()

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def domain(self) -> str:
        """Retorna o domínio do email."""
        return self.value.split("@")[1]

    def local_part(self) -> str:
        """Retorna a parte local do email."""
        return self.value.split("@")[0]

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        return False
