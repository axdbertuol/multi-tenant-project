from typing import List, Dict, Any
from uuid import UUID

from ..entities.authorization_context import AuthorizationContext
from ..entities.policy import Policy
from ..repositories.policy_repository import PolicyRepository
from ..repositories.resource_repository import ResourceRepository
from ..value_objects.authorization_decision import AuthorizationDecision, DecisionReason
from .policy_evaluation_service import PolicyEvaluationService


class ABACService:
    """Attribute-Based Access Control service."""

    def __init__(
        self,
        policy_repository: PolicyRepository,
        resource_repository: ResourceRepository,
        policy_evaluation_service: PolicyEvaluationService,
    ):
        self._policy_repository = policy_repository
        self._resource_repository = resource_repository
        self._policy_evaluation_service = policy_evaluation_service

    def evaluate_policies(self, context: AuthorizationContext) -> AuthorizationDecision:
        """Evaluate ABAC policies for the given context."""
        reasons: List[DecisionReason] = []

        # Enrich context with resource attributes if resource_id is provided
        enriched_context = self._enrich_context_with_resource_attributes(context)

        # Get applicable policies
        applicable_policies = self._policy_repository.get_applicable_policies(
            enriched_context.resource_type,
            enriched_context.action,
            enriched_context.organization_id,
        )

        if not applicable_policies:
            reason = DecisionReason(
                type="abac_no_policies",
                message="No applicable ABAC policies found",
                details={
                    "resource_type": enriched_context.resource_type,
                    "action": enriched_context.action,
                },
            )
            return AuthorizationDecision.not_applicable([reason])

        # Sort policies by priority (highest first)
        sorted_policies = sorted(
            applicable_policies, key=lambda p: p.priority, reverse=True
        )

        # Evaluate policies
        policy_results = []
        for policy in sorted_policies:
            if not policy.is_active:
                continue

            evaluation_result = self._policy_evaluation_service.evaluate_policy(
                policy, enriched_context
            )

            if evaluation_result is not None:  # Policy is applicable
                policy_results.append((policy, evaluation_result))

                reason = DecisionReason(
                    type="policy_evaluation",
                    message=f"Policy '{policy.name}' evaluated to {evaluation_result}",
                    details={
                        "policy_id": str(policy.id),
                        "policy_name": policy.name,
                        "effect": policy.effect.value,
                        "result": evaluation_result,
                        "priority": policy.priority,
                    },
                )
                reasons.append(reason)

        # Apply policy combination logic
        final_decision = self._combine_policy_results(policy_results)

        if final_decision is True:
            return AuthorizationDecision.allow(reasons)
        elif final_decision is False:
            return AuthorizationDecision.deny(reasons)
        else:
            # No applicable policies or all policies were not applicable
            reason = DecisionReason(
                type="abac_not_applicable",
                message="No ABAC policies were applicable to this request",
                details={
                    "evaluated_policies": len(policy_results),
                    "total_policies": len(applicable_policies),
                },
            )
            return AuthorizationDecision.not_applicable([reason])

    def _enrich_context_with_resource_attributes(
        self, context: AuthorizationContext
    ) -> AuthorizationContext:
        """Enrich authorization context with resource attributes."""
        if not context.resource_id:
            return context

        # Get resource from repository
        resource = self._resource_repository.get_by_resource_id(
            context.resource_type, context.resource_id
        )

        if not resource:
            return context

        # Add resource attributes to context
        enriched_context = context
        for key, value in resource.attributes.items():
            enriched_context = enriched_context.add_resource_attribute(key, value)

        # Add common resource attributes
        enriched_context = enriched_context.add_resource_attribute(
            "owner_id", str(resource.owner_id)
        )
        enriched_context = enriched_context.add_resource_attribute(
            "is_active", resource.is_active
        )

        if resource.organization_id:
            enriched_context = enriched_context.add_resource_attribute(
                "organization_id", str(resource.organization_id)
            )

        return enriched_context

    def _combine_policy_results(
        self, policy_results: List[tuple[Policy, bool]]
    ) -> bool | None:
        """Combine policy evaluation results using deny-overrides algorithm."""
        if not policy_results:
            return None

        has_allow = False
        has_deny = False

        for policy, result in policy_results:
            if result:  # Policy condition matched
                if policy.effect.value == "deny":
                    has_deny = True
                elif policy.effect.value == "allow":
                    has_allow = True

        # Deny-overrides: if any policy denies, deny
        if has_deny:
            return False

        # If any policy allows and no policy denies, allow
        if has_allow:
            return True

        # No applicable policies
        return None

    def check_resource_ownership(
        self, user_id: UUID, resource_type: str, resource_id: UUID
    ) -> bool:
        """Check if user owns the resource."""
        resource = self._resource_repository.get_by_resource_id(
            resource_type, resource_id
        )

        if not resource:
            return False

        return resource.is_owned_by(user_id)

    def check_resource_organization_membership(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Check if resource belongs to user's organization."""
        resource = self._resource_repository.get_by_resource_id(
            resource_type, resource_id
        )

        if not resource:
            return False

        return resource.belongs_to_organization(organization_id)

    def evaluate_policy_conditions(
        self, policy: Policy, context: AuthorizationContext
    ) -> tuple[bool, list[dict[str, Any]]]:
        """Evaluate policy conditions against context."""
        condition_results = []
        all_conditions_met = True

        for condition in policy.conditions:
            result = self._policy_evaluation_service.evaluate_condition(
                condition, context.to_dict()
            )
            condition_results.append(
                {"condition": condition.model_dump(), "result": result}
            )
            if not result:
                all_conditions_met = False

        return all_conditions_met, condition_results
