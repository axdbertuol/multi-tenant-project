from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.policy import Policy, PolicyEffect


class PolicyRepository(ABC):
    """Policy repository interface for the Authorization bounded context."""

    @abstractmethod
    def save(self, policy: Policy) -> Policy:
        """Save or update a policy."""
        pass

    @abstractmethod
    def get_by_id(self, policy_id: UUID) -> Optional[Policy]:
        """Get policy by ID."""
        pass

    @abstractmethod
    def get_by_name(
        self, name: str, organization_id: Optional[UUID] = None
    ) -> Optional[Policy]:
        """Get policy by name within organization scope."""
        pass

    @abstractmethod
    def get_applicable_policies(
        self, resource_type: str, action: str, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Get policies applicable to a resource type and action."""
        pass

    @abstractmethod
    def get_organization_policies(self, organization_id: UUID) -> List[Policy]:
        """Get all policies for an organization."""
        pass

    @abstractmethod
    def get_global_policies(self) -> List[Policy]:
        """Get all global policies."""
        pass

    @abstractmethod
    def get_policies_by_effect(
        self, effect: PolicyEffect, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Get policies by effect (allow/deny)."""
        pass

    @abstractmethod
    def delete(self, policy_id: UUID) -> bool:
        """Delete policy by ID."""
        pass

    @abstractmethod
    def list_active_policies(
        self, organization_id: Optional[UUID] = None, limit: int = 100, offset: int = 0
    ) -> List[Policy]:
        """List active policies with pagination."""
        pass

    @abstractmethod
    def search_policies(
        self, query: str, organization_id: Optional[UUID] = None, limit: int = 100
    ) -> List[Policy]:
        """Search policies by name or description."""
        pass

    @abstractmethod
    def get_policies_by_priority(
        self, resource_type: str, action: str, organization_id: Optional[UUID] = None
    ) -> List[Policy]:
        """Get policies ordered by priority (highest first)."""
        pass
