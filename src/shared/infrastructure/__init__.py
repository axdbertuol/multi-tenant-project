# Infrastructure Layer - SQLAlchemy Repository Implementations
#
# This module provides SQLAlchemy implementations for all domain repositories
# across the bounded contexts following the DDD pattern.

from .database.models import (
    # Base
    BaseModel, Base,
    
    # User models
    UserModel, UserSessionModel, SessionStatusEnum,
    
    # Organization models
    OrganizationModel, UserOrganizationRoleModel, OrganizationRoleEnum,
    
    # Authorization models
    RoleModel, PermissionModel, PolicyModel,
    PermissionTypeEnum, PolicyEffectEnum,
    role_permission_association, user_role_assignment,
    
    # Plans models
    PlanModel, PlanResourceModel, SubscriptionModel,
    PlanConfigurationModel, FeatureUsageModel,
    PlanTypeEnum, PlanResourceTypeEnum, SubscriptionStatusEnum, BillingCycleEnum
)

# Repository implementations by bounded context
from user.infrastructure import SqlAlchemyUserRepository, SqlAlchemyUserSessionRepository
from organization.infrastructure import SqlAlchemyOrganizationRepository, SqlAlchemyUserOrganizationRoleRepository
from authorization.infrastructure import SqlAlchemyRoleRepository, SqlAlchemyPermissionRepository, SqlAlchemyPolicyRepository
from plans.infrastructure import SqlAlchemyPlanRepository, SqlAlchemyPlanResourceRepository, SqlAlchemySubscriptionRepository

__all__ = [
    # Database models
    "BaseModel", "Base",
    "UserModel", "UserSessionModel", "SessionStatusEnum",
    "OrganizationModel", "UserOrganizationRoleModel", "OrganizationRoleEnum",
    "RoleModel", "PermissionModel", "PolicyModel",
    "PermissionTypeEnum", "PolicyEffectEnum",
    "role_permission_association", "user_role_assignment",
    "PlanModel", "PlanResourceModel", "SubscriptionModel",
    "PlanConfigurationModel", "FeatureUsageModel",
    "PlanTypeEnum", "PlanResourceTypeEnum", "SubscriptionStatusEnum", "BillingCycleEnum",
    
    # Repository implementations
    "SqlAlchemyUserRepository", "SqlAlchemyUserSessionRepository",
    "SqlAlchemyOrganizationRepository", "SqlAlchemyUserOrganizationRoleRepository",
    "SqlAlchemyRoleRepository", "SqlAlchemyPermissionRepository", "SqlAlchemyPolicyRepository",
    "SqlAlchemyPlanRepository", "SqlAlchemyPlanResourceRepository", "SqlAlchemySubscriptionRepository"
]