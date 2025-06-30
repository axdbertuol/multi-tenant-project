from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyCondition(BaseModel):
    attribute: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, contains
    value: Any

    model_config = {"frozen": True}

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        context_value = context.get(self.attribute)

        if context_value is None:
            return False

        if self.operator == "eq":
            return context_value == self.value
        elif self.operator == "ne":
            return context_value != self.value
        elif self.operator == "gt":
            return context_value > self.value
        elif self.operator == "lt":
            return context_value < self.value
        elif self.operator == "gte":
            return context_value >= self.value
        elif self.operator == "lte":
            return context_value <= self.value
        elif self.operator == "in":
            return context_value in self.value
        elif self.operator == "not_in":
            return context_value not in self.value
        elif self.operator == "contains":
            return self.value in context_value

        return False


class Policy(BaseModel):
    id: UUID
    name: str
    description: str
    effect: PolicyEffect
    resource_type: str
    action: str
    conditions: List[PolicyCondition]
    organization_id: Optional[UUID] = None
    created_by: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    priority: int = 0  # Higher number = higher priority

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        effect: PolicyEffect,
        resource_type: str,
        action: str,
        conditions: List[PolicyCondition],
        created_by: UUID,
        organization_id: Optional[UUID] = None,
        priority: int = 0,
    ) -> "Policy":
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            effect=effect,
            resource_type=resource_type,
            action=action,
            conditions=conditions,
            organization_id=organization_id,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            is_active=True,
            priority=priority,
        )

    def evaluate(self, context: Dict[str, Any]) -> Optional[bool]:
        """Evaluate policy against context. Returns None if not applicable."""
        if not self.is_active:
            return None

        # Check if policy applies to this resource type and action
        if (
            context.get("resource_type") != self.resource_type
            or context.get("action") != self.action
        ):
            return None

        # Check organization scope
        if (
            self.organization_id
            and context.get("organization_id") != self.organization_id
        ):
            return None

        # Evaluate all conditions
        for condition in self.conditions:
            if not condition.evaluate(context):
                return None  # Policy doesn't apply

        # All conditions met, return effect
        return self.effect == PolicyEffect.ALLOW

    def update_conditions(self, conditions: List[PolicyCondition]) -> "Policy":
        """Update policy conditions."""
        return self.model_copy(
            update={"conditions": conditions, "updated_at": datetime.now(timezone.utc)}
        )

    def update_priority(self, priority: int) -> "Policy":
        """Update policy priority."""
        return self.model_copy(
            update={"priority": priority, "updated_at": datetime.now(timezone.utc)}
        )

    def deactivate(self) -> "Policy":
        return self.model_copy(update={
            "is_active": False,
            "updated_at": datetime.now(timezone.utc)
        })

    def activate(self) -> "Policy":
        return self.model_copy(
            update={"is_active": True, "updated_at": datetime.now(timezone.utc)}
        )

    def matches_request(
        self, resource_type: str, action: str, organization_id: Optional[UUID] = None
    ) -> bool:
        """Check if policy matches the request."""
        if not self.is_active:
            return False

        if self.resource_type != resource_type or self.action != action:
            return False

        if self.organization_id and self.organization_id != organization_id:
            return False

        return True
