"""Examples demonstrating document permission integration with the authorization system."""

from uuid import UUID, uuid4
from typing import List, Dict, Any
from datetime import datetime, timezone

from ..domain.entities.resource import Resource
from ..domain.entities.policy import Policy, PolicyEffect, PolicyCondition
from ..domain.services.chat_document_authorization_service import ChatDocumentAuthorizationService
from ..domain.constants.document_policies import (
    DocumentPolicyTemplates,
    DocumentAccessValidationHelpers
)
from ..domain.constants.default_roles import DefaultOrganizationRoles


class DocumentPermissionExamples:
    """Examples showing how to use document permissions in practice."""

    def __init__(self, chat_auth_service: ChatDocumentAuthorizationService):
        self.chat_auth_service = chat_auth_service

    def example_1_basic_document_sharing(self) -> Dict[str, Any]:
        """
        Example 1: Basic document sharing with specific roles (RH and DP).
        
        Scenario: Customer uploads a document and wants only "RH" and "DP" roles
        to see AI responses that reference this document.
        """
        # Example organization and users
        org_id = uuid4()
        document_owner_id = uuid4()
        hr_user_id = uuid4()
        dp_user_id = uuid4()
        other_user_id = uuid4()
        document_id = uuid4()

        # Create document resource with role-based sharing
        document_resource = self.chat_auth_service.create_document_resource(
            document_id=document_id,
            title="Employee Handbook 2024",
            owner_id=document_owner_id,
            organization_id=org_id,
            shared_with_roles=["RH", "DP"],  # Only HR and Data Protection roles
            confidentiality_level="internal",
            ai_query_enabled=True,
            training_enabled=False  # Don't include in training
        )

        # Simulate user roles
        user_roles = {
            hr_user_id: ["RH", "member"],
            dp_user_id: ["DP", "member"], 
            other_user_id: ["member"],
            document_owner_id: ["owner"]
        }

        # Test access for different users
        results = {}
        for user_id, roles in user_roles.items():
            # In real implementation, you would call the authorization service
            # For this example, we simulate the access check
            has_access = (
                user_id == document_owner_id or  # Owner always has access
                any(role in ["RH", "DP"] for role in roles)  # Has required role
            )
            
            results[f"user_{str(user_id)[:8]}"] = {
                "roles": roles,
                "can_access_document": has_access,
                "can_ai_query": has_access and document_resource.attributes["ai_query_enabled"]
            }

        return {
            "scenario": "Role-based document sharing",
            "document": {
                "id": str(document_id),
                "title": document_resource.attributes["title"],
                "shared_with_roles": document_resource.attributes["shared_with_roles"],
                "confidentiality_level": document_resource.attributes["confidentiality_level"]
            },
            "access_results": results
        }

    def example_2_user_specific_sharing(self) -> Dict[str, Any]:
        """
        Example 2: Document shared with specific users.
        
        Scenario: Customer uploads a document and shares it with specific users by ID.
        """
        org_id = uuid4()
        document_owner_id = uuid4()
        shared_user_1 = uuid4()
        shared_user_2 = uuid4()
        non_shared_user = uuid4()
        document_id = uuid4()

        # Create document resource with user-specific sharing
        document_resource = self.chat_auth_service.create_document_resource(
            document_id=document_id,
            title="Project Alpha Specifications",
            owner_id=document_owner_id,
            organization_id=org_id,
            shared_with_users=[shared_user_1, shared_user_2],
            confidentiality_level="confidential",
            ai_query_enabled=True,
            download_enabled=False  # Can read but not download
        )

        # Test access for different users
        test_users = [document_owner_id, shared_user_1, shared_user_2, non_shared_user]
        results = {}
        
        for user_id in test_users:
            is_owner = user_id == document_owner_id
            is_shared_with = str(user_id) in document_resource.attributes["shared_with_users"]
            has_access = is_owner or is_shared_with
            
            results[f"user_{str(user_id)[:8]}"] = {
                "is_owner": is_owner,
                "is_shared_with": is_shared_with,
                "can_read": has_access,
                "can_download": is_owner,  # Only owner can download
                "can_ai_query": has_access and document_resource.attributes["ai_query_enabled"]
            }

        return {
            "scenario": "User-specific document sharing",
            "document": {
                "id": str(document_id),
                "title": document_resource.attributes["title"],
                "shared_with_users": document_resource.attributes["shared_with_users"],
                "download_enabled": document_resource.attributes["download_enabled"]
            },
            "access_results": results
        }

    def example_3_confidentiality_levels(self) -> Dict[str, Any]:
        """
        Example 3: Documents with different confidentiality levels.
        
        Scenario: Different documents with varying confidentiality requirements.
        """
        org_id = uuid4()
        owner_id = uuid4()
        
        # Create documents with different confidentiality levels
        documents = [
            {
                "title": "Company Blog Post",
                "confidentiality_level": "public",
                "training_enabled": True,
                "ai_query_enabled": True
            },
            {
                "title": "Internal Process Guide", 
                "confidentiality_level": "internal",
                "training_enabled": True,
                "ai_query_enabled": True
            },
            {
                "title": "Financial Projections",
                "confidentiality_level": "confidential",
                "training_enabled": False,
                "ai_query_enabled": False  # Highly sensitive
            },
            {
                "title": "Board Meeting Minutes",
                "confidentiality_level": "restricted",
                "training_enabled": False,
                "ai_query_enabled": False
            }
        ]

        results = []
        for doc_info in documents:
            doc_id = uuid4()
            doc_resource = self.chat_auth_service.create_document_resource(
                document_id=doc_id,
                title=doc_info["title"],
                owner_id=owner_id,
                organization_id=org_id,
                confidentiality_level=doc_info["confidentiality_level"],
                training_enabled=doc_info["training_enabled"],
                ai_query_enabled=doc_info["ai_query_enabled"]
            )

            # Simulate access for different user clearance levels
            user_clearances = ["public", "internal", "confidential", "restricted"]
            access_by_clearance = {}
            
            for clearance in user_clearances:
                # Simple rule: user can access if their clearance >= document level
                clearance_hierarchy = ["public", "internal", "confidential", "restricted"]
                user_level = clearance_hierarchy.index(clearance)
                doc_level = clearance_hierarchy.index(doc_info["confidentiality_level"])
                
                has_access = user_level >= doc_level
                access_by_clearance[clearance] = {
                    "can_read": has_access,
                    "can_ai_query": has_access and doc_info["ai_query_enabled"],
                    "can_train": has_access and doc_info["training_enabled"]
                }

            results.append({
                "document": {
                    "title": doc_info["title"],
                    "confidentiality_level": doc_info["confidentiality_level"],
                    "training_enabled": doc_info["training_enabled"],
                    "ai_query_enabled": doc_info["ai_query_enabled"]
                },
                "access_by_clearance": access_by_clearance
            })

        return {
            "scenario": "Confidentiality-based access control",
            "documents": results
        }

    def example_4_chat_integration_flow(self) -> Dict[str, Any]:
        """
        Example 4: Complete chat integration flow with document permissions.
        
        Scenario: User asks question in chat, system checks document permissions
        before including documents in AI response.
        """
        org_id = uuid4()
        user_id = uuid4()
        user_roles = ["member", "RH"]
        
        # Create multiple documents with different permissions
        documents = []
        for i, (title, roles, ai_enabled) in enumerate([
            ("HR Policy Manual", ["RH"], True),
            ("General FAQ", [], True),  # No role restriction
            ("Salary Information", ["admin"], True),  # Admin only
            ("Public Documentation", [], True)
        ]):
            doc_id = uuid4()
            doc_resource = self.chat_auth_service.create_document_resource(
                document_id=doc_id,
                title=title,
                owner_id=uuid4(),
                organization_id=org_id,
                shared_with_roles=roles,
                ai_query_enabled=ai_enabled
            )
            documents.append({
                "id": doc_id,
                "title": title,
                "shared_with_roles": roles,
                "ai_query_enabled": ai_enabled
            })

        # Simulate chat query flow
        chat_query = "What is the company's vacation policy?"
        
        # Step 1: Find relevant documents (this would be done by your document search)
        relevant_docs = [doc for doc in documents if "policy" in doc["title"].lower() or "FAQ" in doc["title"]]
        
        # Step 2: Filter documents by user permissions
        accessible_docs = []
        for doc in relevant_docs:
            # Check if user has required role or no role restriction
            has_role_access = (
                not doc["shared_with_roles"] or  # No role restriction
                any(role in user_roles for role in doc["shared_with_roles"])  # Has required role
            )
            
            if has_role_access and doc["ai_query_enabled"]:
                accessible_docs.append(doc)

        # Step 3: Generate response using only accessible documents
        ai_response = {
            "query": chat_query,
            "documents_used": [doc["title"] for doc in accessible_docs],
            "documents_filtered_out": [
                doc["title"] for doc in relevant_docs 
                if doc not in accessible_docs
            ],
            "response": "Based on accessible documents, here is the vacation policy..." if accessible_docs else "I don't have access to documents that can answer this question."
        }

        return {
            "scenario": "Chat integration with document permissions",
            "user_context": {
                "user_id": str(user_id),
                "roles": user_roles
            },
            "all_documents": documents,
            "relevant_documents": [doc["title"] for doc in relevant_docs],
            "ai_response": ai_response
        }

    def example_5_policy_evaluation(self) -> Dict[str, Any]:
        """
        Example 5: How ABAC policies evaluate document access.
        
        Scenario: Show how different policies affect document access decisions.
        """
        org_id = uuid4()
        user_id = uuid4()
        document_id = uuid4()
        owner_id = uuid4()

        # Create sample policies (these would be created by DocumentPolicyTemplates)
        policies = [
            {
                "name": "Document Owner Access",
                "effect": "ALLOW",
                "conditions": [{"attribute": "resource.owner_id", "operator": "eq", "value": str(user_id)}],
                "applies_when": "User is document owner"
            },
            {
                "name": "Role-based Access",
                "effect": "ALLOW", 
                "conditions": [{"attribute": "user_roles", "operator": "intersects", "value": ["RH", "DP"]}],
                "applies_when": "User has RH or DP role"
            },
            {
                "name": "Confidentiality Restriction",
                "effect": "DENY",
                "conditions": [
                    {"attribute": "resource.confidentiality_level", "operator": "eq", "value": "restricted"},
                    {"attribute": "user.clearance_level", "operator": "ne", "value": "restricted"}
                ],
                "applies_when": "Document is restricted but user lacks clearance"
            }
        ]

        # Test different scenarios
        scenarios = [
            {
                "description": "User is document owner",
                "user_context": {"user_id": str(user_id), "roles": ["member"]},
                "document_context": {"owner_id": str(user_id), "confidentiality_level": "internal"},
                "expected_result": "ALLOW (owner access)"
            },
            {
                "description": "User has required role",
                "user_context": {"user_id": str(uuid4()), "roles": ["RH", "member"]},
                "document_context": {"owner_id": str(owner_id), "shared_with_roles": ["RH"]},
                "expected_result": "ALLOW (role-based access)"
            },
            {
                "description": "User lacks required role",
                "user_context": {"user_id": str(uuid4()), "roles": ["member"]},
                "document_context": {"owner_id": str(owner_id), "shared_with_roles": ["admin"]},
                "expected_result": "DENY (no matching role)"
            },
            {
                "description": "Confidentiality restriction",
                "user_context": {"user_id": str(uuid4()), "roles": ["member"], "clearance_level": "internal"},
                "document_context": {"owner_id": str(owner_id), "confidentiality_level": "restricted"},
                "expected_result": "DENY (insufficient clearance)"
            }
        ]

        return {
            "scenario": "ABAC policy evaluation for documents",
            "policies": policies,
            "test_scenarios": scenarios,
            "notes": [
                "Policies are evaluated in priority order",
                "DENY policies override ALLOW policies",
                "Multiple conditions must ALL be true for policy to apply",
                "If no policies apply, access is denied by default"
            ]
        }


def run_all_examples():
    """Run all document permission examples."""
    print("=== Document Permission Integration Examples ===\n")
    
    # Note: In real implementation, you would inject actual services
    # For examples, we create a mock service
    chat_auth_service = None  # MockChatDocumentAuthorizationService()
    examples = DocumentPermissionExamples(chat_auth_service)
    
    example_methods = [
        examples.example_1_basic_document_sharing,
        examples.example_2_user_specific_sharing,
        examples.example_3_confidentiality_levels,
        examples.example_4_chat_integration_flow,
        examples.example_5_policy_evaluation
    ]
    
    for i, method in enumerate(example_methods, 1):
        print(f"--- Example {i}: {method.__doc__.split('.')[0].strip()} ---")
        try:
            result = method()
            print(f"Scenario: {result.get('scenario', 'Unknown')}")
            # Print relevant parts of the result
            if 'access_results' in result:
                print("Access Results:")
                for user, access in result['access_results'].items():
                    print(f"  {user}: {access}")
            print()
        except Exception as e:
            print(f"Example failed: {e}\n")


if __name__ == "__main__":
    run_all_examples()