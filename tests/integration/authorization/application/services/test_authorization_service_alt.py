import pytest
from uuid import uuid4
from unittest.mock import Mock

from src.authorization.domain.entities.authorization_context import AuthorizationContext
from src.authorization.domain.entities.role import Role
from src.authorization.domain.entities.permission import Permission, PermissionAction
from src.authorization.domain.entities.policy import Policy, PolicyEffect, PolicyCondition
from src.authorization.domain.entities.resource import Resource
from src.authorization.domain.services.authorization_service import AuthorizationService
from src.authorization.domain.services.rbac_service import RBACService
from src.authorization.domain.services.abac_service import ABACService
from src.authorization.domain.services.policy_evaluation_service import PolicyEvaluationService
from src.authorization.domain.value_objects.authorization_decision import AuthorizationDecision, DecisionResult


@pytest.fixture
def mock_rbac_service():
    return Mock(spec=RBACService)

@pytest.fixture
def mock_abac_service():
    return Mock(spec=ABACService)

@pytest.fixture
def authorization_service(mock_rbac_service, mock_abac_service):
    return AuthorizationService(rbac_service=mock_rbac_service, abac_service=mock_abac_service)

@pytest.fixture
def sample_context():
    return AuthorizationContext.create(
        user_id=uuid4(),
        resource_type="document",
        action="read",
        organization_id=uuid4(),
        resource_id=uuid4()
    )

def test_authorize_rbac_allow_no_abac(authorization_service, mock_rbac_service, mock_abac_service, sample_context):
    mock_rbac_service.authorize.return_value = AuthorizationDecision.allow(reasons=[])
    mock_abac_service.evaluate_policies.return_value = AuthorizationDecision.not_applicable(reasons=[])

    decision = authorization_service.authorize(sample_context)

    assert decision.is_allowed()

def test_authorize_rbac_allow_abac_deny(authorization_service, mock_rbac_service, mock_abac_service, sample_context):
    mock_rbac_service.authorize.return_value = AuthorizationDecision.allow(reasons=[])
    mock_abac_service.evaluate_policies.return_value = AuthorizationDecision.deny(reasons=[])

    decision = authorization_service.authorize(sample_context)

    assert decision.is_denied()

def test_authorize_rbac_deny_abac_allow(authorization_service, mock_rbac_service, mock_abac_service, sample_context):
    mock_rbac_service.authorize.return_value = AuthorizationDecision.deny(reasons=[])
    mock_abac_service.evaluate_policies.return_value = AuthorizationDecision.allow(reasons=[])

    decision = authorization_service.authorize(sample_context)

    assert decision.is_allowed()

def test_authorize_both_deny(authorization_service, mock_rbac_service, mock_abac_service, sample_context):
    mock_rbac_service.authorize.return_value = AuthorizationDecision.deny(reasons=[])
    mock_abac_service.evaluate_policies.return_value = AuthorizationDecision.deny(reasons=[])

    decision = authorization_service.authorize(sample_context)

    assert decision.is_denied()
