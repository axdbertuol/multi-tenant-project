from fastapi import Depends
from sqlalchemy.orm import Session

from ...application.services.onboarding_service import OnboardingService
from ...application.use_cases.onboard_tenant import OnboardTenantUseCase
from ...infrastructure.services.iam_service_impl import IamServiceImpl
from ...infrastructure.services.plans_service_impl import PlansServiceImpl
from ...infrastructure.repositories.sqlalchemy_onboarding_repository import SqlAlchemyOnboardingRepository

# Import IAM dependencies
from ....iam.application.use_cases import (
    OrganizationUseCase,
    UserUseCase,
    MembershipUseCase,
    RoleUseCase,
    AuthorizationSubjectUseCase,
)
from ....iam.domain.services import OrganizationRoleSetupService
from ....iam.infrastructure import IAMUnitOfWork

# Import Plans dependencies
from ....plans.application.use_cases.plan_use_cases import PlanUseCase
from ....plans.infrastructure.plans_unit_of_work import PlansUnitOfWork

# Import shared dependencies
from ....shared.infrastructure.database.session import get_session


def get_iam_unit_of_work(session: Session = Depends(get_session)) -> IAMUnitOfWork:
    """Get IAM unit of work."""
    return IAMUnitOfWork(session)


def get_plans_unit_of_work(session: Session = Depends(get_session)) -> PlansUnitOfWork:
    """Get Plans unit of work."""
    return PlansUnitOfWork(session)


def get_organization_use_case(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> OrganizationUseCase:
    """Get organization use case."""
    return OrganizationUseCase(iam_uow)


def get_user_use_case(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> UserUseCase:
    """Get user use case."""
    return UserUseCase(iam_uow)


def get_membership_use_case(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> MembershipUseCase:
    """Get membership use case."""
    return MembershipUseCase(iam_uow)


def get_role_use_case(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> RoleUseCase:
    """Get role use case."""
    return RoleUseCase(iam_uow)


def get_authorization_subject_use_case(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> AuthorizationSubjectUseCase:
    """Get authorization subject use case."""
    return AuthorizationSubjectUseCase(iam_uow)


def get_organization_role_setup_service(iam_uow: IAMUnitOfWork = Depends(get_iam_unit_of_work)) -> OrganizationRoleSetupService:
    """Get organization role setup service."""
    return OrganizationRoleSetupService(iam_uow)


def get_plan_use_case(plans_uow: PlansUnitOfWork = Depends(get_plans_unit_of_work)) -> PlanUseCase:
    """Get plan use case."""
    return PlanUseCase(plans_uow)


def get_iam_service(
    organization_use_case: OrganizationUseCase = Depends(get_organization_use_case),
    user_use_case: UserUseCase = Depends(get_user_use_case),
    membership_use_case: MembershipUseCase = Depends(get_membership_use_case),
    role_use_case: RoleUseCase = Depends(get_role_use_case),
    authorization_subject_use_case: AuthorizationSubjectUseCase = Depends(get_authorization_subject_use_case),
    organization_role_setup_service: OrganizationRoleSetupService = Depends(get_organization_role_setup_service),
) -> IamServiceImpl:
    """Get IAM service implementation."""
    return IamServiceImpl(
        organization_use_case=organization_use_case,
        user_use_case=user_use_case,
        membership_use_case=membership_use_case,
        role_use_case=role_use_case,
        authorization_subject_use_case=authorization_subject_use_case,
        organization_role_setup_service=organization_role_setup_service,
    )


def get_plans_service(
    plan_use_case: PlanUseCase = Depends(get_plan_use_case),
    plans_uow: PlansUnitOfWork = Depends(get_plans_unit_of_work),
) -> PlansServiceImpl:
    """Get Plans service implementation."""
    return PlansServiceImpl(
        plan_use_case=plan_use_case,
        uow=plans_uow,
    )


def get_onboarding_repository(session: Session = Depends(get_session)) -> SqlAlchemyOnboardingRepository:
    """Get onboarding repository."""
    return SqlAlchemyOnboardingRepository(session)


def get_onboard_tenant_use_case(
    iam_service: IamServiceImpl = Depends(get_iam_service),
    plans_service: PlansServiceImpl = Depends(get_plans_service),
    onboarding_repository: SqlAlchemyOnboardingRepository = Depends(get_onboarding_repository),
) -> OnboardTenantUseCase:
    """Get onboard tenant use case."""
    return OnboardTenantUseCase(
        iam_service=iam_service,
        plans_service=plans_service,
        onboarding_repository=onboarding_repository,
    )


def get_onboarding_service(
    onboard_tenant_use_case: OnboardTenantUseCase = Depends(get_onboard_tenant_use_case),
) -> OnboardingService:
    """Get onboarding service."""
    return OnboardingService(onboard_tenant_use_case)