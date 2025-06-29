import re
from pydantic import BaseModel, field_validator
from typing import Any


class Email(BaseModel):
    value: str

    model_config = {"frozen": True}

    @field_validator('value')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not cls._is_valid_email(v):
            raise ValueError(f"Invalid email format: {v}")
        return v

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Email):
            return self.value == other.value
        return False