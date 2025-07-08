from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.management_function import ManagementFunction
from ..entities.user_function_area import UserFunctionArea
from ..entities.permission import Permission, PermissionContext
from ..repositories.management_function_repository import ManagementFunctionRepository
from ..repositories.user_function_area_repository import UserFunctionAreaRepository
from ..repositories.permission_repository import PermissionRepository


class ManagementFunctionService:
    """
    Serviço de domínio para gerenciamento de funções de gerenciamento.
    
    Controla as regras de negócio relacionadas a funções que controlam
    permissões exclusivamente na plataforma de gerenciamento.
    """
    
    def __init__(
        self,
        management_function_repository: ManagementFunctionRepository,
        user_function_area_repository: UserFunctionAreaRepository,
        permission_repository: PermissionRepository,
    ):
        self.management_function_repository = management_function_repository
        self.user_function_area_repository = user_function_area_repository
        self.permission_repository = permission_repository
    
    def create_function(
        self,
        name: str,
        description: str,
        organization_id: UUID,
        permissions: List[str],
        created_by: UUID,
        is_system_function: bool = False,
    ) -> ManagementFunction:
        """
        Cria uma nova função de gerenciamento.
        
        Args:
            name: Nome da função
            description: Descrição da função
            organization_id: ID da organização
            permissions: Lista de permissões
            created_by: ID do usuário que criou
            is_system_function: Se é uma função do sistema
        """
        # Verificar se já existe função com esse nome na organização
        existing_function = self.management_function_repository.get_by_name_and_organization(
            name, organization_id
        )
        if existing_function:
            raise ValueError(f"Function with name '{name}' already exists in organization")
        
        # Validar permissões
        valid_permissions = self._validate_management_permissions(permissions)
        if not valid_permissions:
            raise ValueError("Invalid management permissions provided")
        
        # Criar função
        function = ManagementFunction.create(
            name=name,
            description=description,
            organization_id=organization_id,
            permissions=permissions,
            created_by=created_by,
            is_system_function=is_system_function,
        )
        
        return self.management_function_repository.save(function)
    
    def update_function_permissions(
        self,
        function_id: UUID,
        permissions: List[str],
        updated_by: UUID,
    ) -> ManagementFunction:
        """
        Atualiza as permissões de uma função.
        
        Args:
            function_id: ID da função
            permissions: Nova lista de permissões
            updated_by: ID do usuário que atualizou
        """
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            raise ValueError(f"Function {function_id} not found")
        
        # Validar permissões
        valid_permissions = self._validate_management_permissions(permissions)
        if not valid_permissions:
            raise ValueError("Invalid management permissions provided")
        
        # Atualizar função
        updated_function = function.update_permissions(permissions)
        
        return self.management_function_repository.save(updated_function)
    
    def assign_function_to_user(
        self,
        user_id: UUID,
        function_id: UUID,
        area_id: UUID,
        organization_id: UUID,
        assigned_by: UUID,
    ) -> UserFunctionArea:
        """
        Atribui uma função a um usuário.
        
        Args:
            user_id: ID do usuário
            function_id: ID da função
            area_id: ID da área
            organization_id: ID da organização
            assigned_by: ID do usuário que fez a atribuição
        """
        # Verificar se função existe
        function = self.management_function_repository.get_by_id(function_id)
        if not function:
            raise ValueError(f"Function {function_id} not found")
        
        if not function.is_active:
            raise ValueError("Cannot assign inactive function")
        
        # Verificar se usuário já tem função na organização
        existing_assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if existing_assignment and existing_assignment.is_active:
            raise ValueError("User already has an active function assignment in this organization")
        
        # Criar atribuição
        assignment = UserFunctionArea.create(
            user_id=user_id,
            organization_id=organization_id,
            function_id=function_id,
            area_id=area_id,
            assigned_by=assigned_by,
        )
        
        return self.user_function_area_repository.save(assignment)
    
    def change_user_function(
        self,
        user_id: UUID,
        new_function_id: UUID,
        organization_id: UUID,
        changed_by: UUID,
    ) -> UserFunctionArea:
        """
        Muda a função de um usuário.
        
        Args:
            user_id: ID do usuário
            new_function_id: ID da nova função
            organization_id: ID da organização
            changed_by: ID do usuário que fez a mudança
        """
        # Verificar se nova função existe
        new_function = self.management_function_repository.get_by_id(new_function_id)
        if not new_function:
            raise ValueError(f"Function {new_function_id} not found")
        
        if not new_function.is_active:
            raise ValueError("Cannot assign inactive function")
        
        # Obter atribuição atual
        current_assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not current_assignment:
            raise ValueError("User has no current function assignment in this organization")
        
        # Atualizar função
        updated_assignment = current_assignment.change_function(new_function_id, changed_by)
        
        return self.user_function_area_repository.save(updated_assignment)
    
    def revoke_user_function(
        self,
        user_id: UUID,
        organization_id: UUID,
        revoked_by: UUID,
        reason: Optional[str] = None,
    ) -> UserFunctionArea:
        """
        Revoga a função de um usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            revoked_by: ID do usuário que revogou
            reason: Motivo da revogação
        """
        # Obter atribuição atual
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment:
            raise ValueError("User has no function assignment in this organization")
        
        if not assignment.is_active:
            raise ValueError("Function assignment is already inactive")
        
        # Revogar função
        revoked_assignment = assignment.revoke(revoked_by, reason)
        
        return self.user_function_area_repository.save(revoked_assignment)
    
    def get_user_management_permissions(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> List[str]:
        """
        Obtém as permissões de gerenciamento de um usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Lista de permissões de gerenciamento
        """
        # Obter atribuição do usuário
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_valid():
            return []
        
        # Obter função
        function = self.management_function_repository.get_by_id(assignment.function_id)
        if not function or not function.is_active:
            return []
        
        return function.permissions
    
    def user_has_management_permission(
        self,
        user_id: UUID,
        organization_id: UUID,
        permission: str,
    ) -> bool:
        """
        Verifica se um usuário tem uma permissão de gerenciamento específica.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            permission: Permissão a verificar
            
        Returns:
            True se o usuário tem a permissão
        """
        # Obter atribuição do usuário
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_valid():
            return False
        
        # Obter função
        function = self.management_function_repository.get_by_id(assignment.function_id)
        if not function or not function.is_active:
            return False
        
        return function.has_permission(permission)
    
    def get_function_by_name(
        self,
        name: str,
        organization_id: UUID,
    ) -> Optional[ManagementFunction]:
        """
        Obtém uma função pelo nome e organização.
        
        Args:
            name: Nome da função
            organization_id: ID da organização
            
        Returns:
            Função encontrada ou None
        """
        return self.management_function_repository.get_by_name_and_organization(
            name, organization_id
        )
    
    def get_users_by_function(
        self,
        function_id: UUID,
        organization_id: UUID,
    ) -> List[UserFunctionArea]:
        """
        Obtém todos os usuários que têm uma função específica.
        
        Args:
            function_id: ID da função
            organization_id: ID da organização
            
        Returns:
            Lista de atribuições de usuários
        """
        return self.user_function_area_repository.get_by_function_and_organization(
            function_id, organization_id
        )
    
    def setup_default_functions_for_organization(
        self,
        organization_id: UUID,
        created_by: UUID,
    ) -> List[ManagementFunction]:
        """
        Configura as funções padrão para uma organização.
        
        Args:
            organization_id: ID da organização
            created_by: ID do usuário que criou
            
        Returns:
            Lista de funções criadas
        """
        default_functions = [
            {
                "name": "admin",
                "description": "Administrador com acesso total ao gerenciamento",
                "permissions": ["management:*"],
            },
            {
                "name": "gerenciador",
                "description": "Gerenciador com acesso limitado ao gerenciamento",
                "permissions": [
                    "management:read",
                    "management:update",
                    "users:read",
                    "users:manage",
                    "areas:read",
                    "areas:manage",
                ],
            },
            {
                "name": "membro",
                "description": "Membro com acesso apenas de leitura",
                "permissions": ["management:read"],
            },
        ]
        
        created_functions = []
        for func_data in default_functions:
            try:
                function = self.create_function(
                    name=func_data["name"],
                    description=func_data["description"],
                    organization_id=organization_id,
                    permissions=func_data["permissions"],
                    created_by=created_by,
                    is_system_function=True,
                )
                created_functions.append(function)
            except ValueError:
                # Função já existe, pular
                continue
        
        return created_functions
    
    def _validate_management_permissions(self, permissions: List[str]) -> bool:
        """
        Valida se as permissões são válidas para gerenciamento.
        
        Args:
            permissions: Lista de permissões
            
        Returns:
            True se todas as permissões são válidas
        """
        valid_management_permissions = [
            "management:read",
            "management:create",
            "management:update",
            "management:delete",
            "management:manage",
            "management:*",
            "users:read",
            "users:create",
            "users:update",
            "users:delete",
            "users:manage",
            "users:*",
            "organizations:read",
            "organizations:update",
            "organizations:manage",
            "roles:read",
            "roles:create",
            "roles:update",
            "roles:delete",
            "roles:manage",
            "functions:read",
            "functions:create",
            "functions:update",
            "functions:delete",
            "functions:manage",
            "areas:read",
            "areas:create",
            "areas:update",
            "areas:delete",
            "areas:manage",
            "*:*",
        ]
        
        return all(perm in valid_management_permissions for perm in permissions)