from typing import Dict, Any, Optional
from datetime import datetime

from ..entities.policy import Policy, PolicyCondition
from ..entities.authorization_context import AuthorizationContext


class PolicyEvaluationService:
    """Service for evaluating ABAC policies against authorization contexts."""

    def evaluate_policy(
        self, policy: Policy, context: AuthorizationContext
    ) -> Optional[bool]:
        """Evaluate a policy against an authorization context."""
        if not policy.is_active:
            return None

        # Check if policy applies to this request
        if not self._policy_applies_to_context(policy, context):
            return None

        # Convert context to evaluation dictionary
        evaluation_context = context.to_dict()

        # Add computed attributes
        evaluation_context.update(self._get_computed_attributes(context))

        # Evaluate all conditions
        all_conditions_met = True
        for condition in policy.conditions:
            if not self._evaluate_condition(condition, evaluation_context):
                all_conditions_met = False
                break

        if all_conditions_met:
            # All conditions met, return policy effect
            return policy.effect.value == "allow"

        # Conditions not met, policy doesn't apply
        return None

    def _policy_applies_to_context(
        self, policy: Policy, context: AuthorizationContext
    ) -> bool:
        """Check if policy applies to the authorization context."""
        # Check resource type
        if policy.resource_type != context.resource_type:
            return False

        # Check action
        if policy.action != context.action:
            return False

        # Check organization scope
        if policy.organization_id and policy.organization_id != context.organization_id:
            return False

        return True

    def _evaluate_condition(
        self, condition: PolicyCondition, context: Dict[str, Any]
    ) -> bool:
        """Evaluate a single policy condition."""
        try:
            return condition.evaluate(context)
        except Exception:
            # If condition evaluation fails, consider it false
            return False

    def _get_computed_attributes(self, context: AuthorizationContext) -> Dict[str, Any]:
        """Get computed attributes for policy evaluation."""
        now = datetime.utcnow()

        computed = {
            # Time-based attributes
            "current_hour": now.hour,
            "current_day_of_week": now.weekday(),  # 0 = Monday
            "current_month": now.month,
            "current_year": now.year,
            "is_weekend": now.weekday() >= 5,
            "is_business_hours": 9 <= now.hour <= 17,
            # Request attributes
            "is_same_user": str(context.user_id)
            == context.get_resource_attribute("owner_id"),
            "is_same_organization": (
                context.organization_id
                and str(context.organization_id)
                == context.get_resource_attribute("organization_id")
            ),
            # Derived attributes
            "resource_age_days": self._calculate_resource_age_days(context),
            "user_role_count": len(context.get_user_attribute("roles", [])),
        }

        return computed

    def _calculate_resource_age_days(self, context: AuthorizationContext) -> int:
        """Calculate resource age in days."""
        created_at_str = context.get_resource_attribute("created_at")
        if not created_at_str:
            return 0

        try:
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(
                    created_at_str.replace("Z", "+00:00")
                )
            else:
                created_at = created_at_str

            age = datetime.now(timezone.utc) - created_at
            return age.days
        except Exception:
            return 0

    def test_policy_condition(
        self, condition: PolicyCondition, test_context: Dict[str, Any]
    ) -> bool:
        """Test a policy condition with provided context (for testing/debugging)."""
        return self._evaluate_condition(condition, test_context)

    def validate_policy_conditions(self, policy: Policy) -> tuple[bool, list[str]]:
        """Validate policy conditions for syntax and logic errors."""
        errors = []

        for i, condition in enumerate(policy.conditions):
            # Check attribute name
            if not condition.attribute:
                errors.append(f"Condition {i + 1}: attribute name is empty")
                continue

            # Check operator
            valid_operators = [
                "eq",
                "ne",
                "gt",
                "lt",
                "gte",
                "lte",
                "in",
                "not_in",
                "contains",
            ]
            if condition.operator not in valid_operators:
                errors.append(
                    f"Condition {i + 1}: invalid operator '{condition.operator}'"
                )

            # Check value type for specific operators
            if condition.operator in ["in", "not_in"] and not isinstance(
                condition.value, list
            ):
                errors.append(
                    f"Condition {i + 1}: operator '{condition.operator}' requires list value"
                )

            if condition.operator in ["gt", "lt", "gte", "lte"]:
                if not isinstance(condition.value, (int, float)):
                    errors.append(
                        f"Condition {i + 1}: operator '{condition.operator}' requires numeric value"
                    )

        return len(errors) == 0, errors

    def explain_policy_evaluation(
        self, policy: Policy, context: AuthorizationContext
    ) -> Dict[str, Any]:
        """Explain how a policy was evaluated (for debugging)."""
        explanation = {
            "policy_id": str(policy.id),
            "policy_name": policy.name,
            "policy_applies": self._policy_applies_to_context(policy, context),
            "conditions": [],
            "overall_result": None,
        }

        if not explanation["policy_applies"]:
            explanation["reason"] = "Policy does not apply to this context"
            return explanation

        evaluation_context = context.to_dict()
        evaluation_context.update(self._get_computed_attributes(context))

        all_conditions_met = True
        for i, condition in enumerate(policy.conditions):
            condition_result = self._evaluate_condition(condition, evaluation_context)

            explanation["conditions"].append(
                {
                    "index": i,
                    "attribute": condition.attribute,
                    "operator": condition.operator,
                    "expected_value": condition.value,
                    "actual_value": evaluation_context.get(condition.attribute),
                    "result": condition_result,
                }
            )

            if not condition_result:
                all_conditions_met = False

        if all_conditions_met:
            explanation["overall_result"] = policy.effect.value == "allow"
        else:
            explanation["overall_result"] = None
            explanation["reason"] = "Not all conditions were met"

        return explanation
