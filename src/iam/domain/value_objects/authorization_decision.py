from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from enum import Enum


class DecisionResult(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    NOT_APPLICABLE = "not_applicable"


class DecisionReason(BaseModel):
    type: str  # "role", "policy", "ownership", "default"
    message: str
    details: Dict[str, Any]

    model_config = {"frozen": True}


class AuthorizationDecision(BaseModel):
    result: DecisionResult
    reasons: List[DecisionReason]
    evaluated_at: datetime
    evaluation_time_ms: float

    model_config = {"frozen": True}

    @classmethod
    def allow(
        cls, reasons: List[DecisionReason], evaluation_time_ms: float = 0.0
    ) -> "AuthorizationDecision":
        return cls(
            result=DecisionResult.ALLOW,
            reasons=reasons,
            evaluated_at=datetime.now(timezone.utc),
            evaluation_time_ms=evaluation_time_ms,
        )

    @classmethod
    def deny(
        cls, reasons: List[DecisionReason], evaluation_time_ms: float = 0.0
    ) -> "AuthorizationDecision":
        return cls(
            result=DecisionResult.DENY,
            reasons=reasons,
            evaluated_at=datetime.now(timezone.utc),
            evaluation_time_ms=evaluation_time_ms,
        )

    @classmethod
    def not_applicable(
        cls, reasons: List[DecisionReason], evaluation_time_ms: float = 0.0
    ) -> "AuthorizationDecision":
        return cls(
            result=DecisionResult.NOT_APPLICABLE,
            reasons=reasons,
            evaluated_at=datetime.now(timezone.utc),
            evaluation_time_ms=evaluation_time_ms,
        )

    def is_allowed(self) -> bool:
        """Check if the decision allows access."""
        return self.result == DecisionResult.ALLOW

    def is_denied(self) -> bool:
        """Check if the decision denies access."""
        return self.result == DecisionResult.DENY

    def is_not_applicable(self) -> bool:
        """Check if the decision is not applicable."""
        return self.result == DecisionResult.NOT_APPLICABLE

    def get_primary_reason(self) -> Optional[DecisionReason]:
        """Get the primary reason for the decision."""
        return self.reasons[0] if self.reasons else None

    def get_reasons_by_type(self, reason_type: str) -> List[DecisionReason]:
        """Get all reasons of a specific type."""
        return [reason for reason in self.reasons if reason.type == reason_type]

    def add_reason(self, reason: DecisionReason) -> "AuthorizationDecision":
        """Add a reason to the decision."""
        new_reasons = self.reasons.copy()
        new_reasons.append(reason)
        return self.model_copy(update={"reasons": new_reasons})

    def get_summary(self) -> str:
        """Get a summary of the decision."""
        if not self.reasons:
            return f"Access {self.result.value}"

        primary_reason = self.get_primary_reason()
        return f"Access {self.result.value}: {primary_reason.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to dictionary for logging/debugging."""
        return {
            "result": self.result.value,
            "reasons": [
                {
                    "type": reason.type,
                    "message": reason.message,
                    "details": reason.details,
                }
                for reason in self.reasons
            ],
            "evaluated_at": self.evaluated_at.isoformat(),
            "evaluation_time_ms": self.evaluation_time_ms,
        }
