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
        # Support nested attribute access with dot notation
        context_value = self._get_nested_value(context, self.attribute)

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
        # Document-specific operators
        elif self.operator == "intersects":
            return self._intersects(context_value, self.value)
        elif self.operator == "not_intersects":
            return not self._intersects(context_value, self.value)
        elif self.operator == "has_all":
            return self._has_all(context_value, self.value)
        elif self.operator == "has_any":
            return self._has_any(context_value, self.value)

        return False

    def _get_nested_value(self, context: Dict[str, Any], attribute: str) -> Any:
        """Get value from nested context using dot notation."""
        keys = attribute.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

    def _intersects(self, list1: Any, list2: Any) -> bool:
        """Check if two lists have common elements."""
        if not isinstance(list1, (list, tuple)) or not isinstance(list2, (list, tuple)):
            return False
        return bool(set(list1) & set(list2))

    def _has_all(self, container: Any, required_items: Any) -> bool:
        """Check if container has all required items."""
        if not isinstance(container, (list, tuple)) or not isinstance(required_items, (list, tuple)):
            return False
        return set(required_items).issubset(set(container))

    def _has_any(self, container: Any, items: Any) -> bool:
        """Check if container has any of the specified items."""
        if not isinstance(container, (list, tuple)) or not isinstance(items, (list, tuple)):
            return False
        return bool(set(container) & set(items))


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
        return self.model_copy(
            update={"is_active": False, "updated_at": datetime.now(timezone.utc)}
        )

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
