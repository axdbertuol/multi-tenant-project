from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from ..entities.document_area import DocumentArea
from ..entities.document_folder import DocumentFolder
from ..entities.user_function_area import UserFunctionArea
from ..entities.management_function import ManagementFunction
from ..entities.policy import Policy
from ..repositories.document_area_repository import DocumentAreaRepository
from ..repositories.document_folder_repository import DocumentFolderRepository
from ..repositories.user_function_area_repository import UserFunctionAreaRepository
from ..repositories.management_function_repository import ManagementFunctionRepository
from ..repositories.policy_repository import PolicyRepository
from .policy_evaluation_service import PolicyEvaluationService


class DocumentAccessService:
    """
    Serviço de domínio para controle de acesso a documentos.
    
    Determina se usuários podem acessar documentos/pastas específicos
    baseado em suas áreas e implementa lógica de herança hierárquica.
    """
    
    def __init__(
        self,
        document_area_repository: DocumentAreaRepository,
        document_folder_repository: DocumentFolderRepository,
        user_function_area_repository: UserFunctionAreaRepository,
        management_function_repository: ManagementFunctionRepository,
        policy_repository: PolicyRepository,
        policy_evaluation_service: PolicyEvaluationService,
    ):
        self.document_area_repository = document_area_repository
        self.document_folder_repository = document_folder_repository
        self.user_function_area_repository = user_function_area_repository
        self.management_function_repository = management_function_repository
        self.policy_repository = policy_repository
        self.policy_evaluation_service = policy_evaluation_service
    
    def can_user_access_document(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_path: str,
        action: str = "read",
    ) -> Tuple[bool, str]:
        """
        Verifica se um usuário pode acessar um documento.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            document_path: Caminho do documento
            action: Ação a ser realizada (read, write, delete, etc.)
            
        Returns:
            Tuple com (pode_acessar, motivo)
        """
        # Verificar se usuário tem atribuição válida
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_valid():
            return False, "User has no valid function/area assignment"
        
        # Verificar se usuário tem função ativa
        function = self.management_function_repository.get_by_id(assignment.function_id)
        if not function or not function.is_active:
            return False, "User function is inactive"
        
        # Verificar se usuário tem área ativa
        area = self.document_area_repository.get_by_id(assignment.area_id)
        if not area or not area.is_active:
            return False, "User area is inactive"
        
        # Verificar acesso baseado em área
        area_access = self._check_area_access(user_id, organization_id, document_path)
        if not area_access[0]:
            return area_access
        
        # Verificar permissões de função de gerenciamento
        management_access = self._check_management_permissions(
            function, document_path, action
        )
        if not management_access[0]:
            return management_access
        
        # Verificar políticas ABAC
        policy_access = self._check_policy_access(
            user_id, organization_id, document_path, action
        )
        if not policy_access[0]:
            return policy_access
        
        return True, "Access granted"
    
    def can_user_access_folder(
        self,
        user_id: UUID,
        organization_id: UUID,
        folder_path: str,
        action: str = "read",
    ) -> Tuple[bool, str]:
        """
        Verifica se um usuário pode acessar uma pasta.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            folder_path: Caminho da pasta
            action: Ação a ser realizada
            
        Returns:
            Tuple com (pode_acessar, motivo)
        """
        # Verificar se usuário tem atribuição válida
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_valid():
            return False, "User has no valid function/area assignment"
        
        # Obter área do usuário
        user_area = self.document_area_repository.get_by_id(assignment.area_id)
        if not user_area or not user_area.is_active:
            return False, "User area is inactive"
        
        # Obter todas as áreas da organização para calcular hierarquia
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        # Obter áreas acessíveis pelo usuário
        accessible_areas = self._get_user_accessible_areas(user_area, all_areas)
        
        # Verificar se alguma área acessível permite acesso à pasta
        for area in accessible_areas:
            if area.can_access_folder(folder_path):
                return True, f"Access granted via area: {area.name}"
        
        return False, "No accessible area grants access to this folder"
    
    def get_user_accessible_documents(
        self,
        user_id: UUID,
        organization_id: UUID,
        folder_path: Optional[str] = None,
    ) -> List[str]:
        """
        Obtém todos os documentos acessíveis por um usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            folder_path: Pasta específica para filtrar (opcional)
            
        Returns:
            Lista de caminhos de documentos acessíveis
        """
        # Verificar se usuário tem atribuição válida
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment or not assignment.is_valid():
            return []
        
        # Obter área do usuário
        user_area = self.document_area_repository.get_by_id(assignment.area_id)
        if not user_area or not user_area.is_active:
            return []
        
        # Obter todas as áreas da organização
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        # Obter áreas acessíveis
        accessible_areas = self._get_user_accessible_areas(user_area, all_areas)
        
        # Obter caminhos de pastas acessíveis
        accessible_paths = []
        for area in accessible_areas:
            accessible_paths.extend(area.get_accessible_paths(all_areas))
        
        # Filtrar por pasta específica se fornecida
        if folder_path:
            accessible_paths = [
                path for path in accessible_paths
                if path.startswith(folder_path)
            ]
        
        return accessible_paths
    
    def get_folder_access_summary(
        self,
        folder_path: str,
        organization_id: UUID,
    ) -> Dict[str, Any]:
        """
        Obtém um resumo de acesso para uma pasta.
        
        Args:
            folder_path: Caminho da pasta
            organization_id: ID da organização
            
        Returns:
            Dicionário com resumo de acesso
        """
        # Obter áreas que podem acessar a pasta
        accessible_areas = []
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        for area in all_areas:
            if area.is_active and area.can_access_folder(folder_path):
                accessible_areas.append(area)
        
        # Obter usuários que podem acessar
        accessible_users = []
        for area in accessible_areas:
            users_in_area = self.user_function_area_repository.get_by_area(area.id)
            active_users = [u for u in users_in_area if u.is_active]
            accessible_users.extend(active_users)
        
        # Remover duplicatas
        unique_users = {}
        for user in accessible_users:
            unique_users[user.user_id] = user
        
        return {
            "folder_path": folder_path,
            "organization_id": str(organization_id),
            "accessible_areas": [
                {
                    "id": str(area.id),
                    "name": area.name,
                    "folder_path": area.folder_path,
                }
                for area in accessible_areas
            ],
            "accessible_users_count": len(unique_users),
            "total_areas": len(all_areas),
            "areas_with_access": len(accessible_areas),
            "access_percentage": (len(accessible_areas) / len(all_areas) * 100) if all_areas else 0,
        }
    
    def validate_document_access_request(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_path: str,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Valida uma solicitação de acesso a documento com detalhes.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            document_path: Caminho do documento
            action: Ação solicitada
            context: Contexto adicional
            
        Returns:
            Dicionário com resultado da validação
        """
        context = context or {}
        
        # Verificar acesso básico
        can_access, reason = self.can_user_access_document(
            user_id, organization_id, document_path, action
        )
        
        # Obter detalhes da atribuição do usuário
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        assignment_details = {}
        if assignment:
            function = self.management_function_repository.get_by_id(assignment.function_id)
            area = self.document_area_repository.get_by_id(assignment.area_id)
            
            assignment_details = {
                "function_name": function.name if function else "Unknown",
                "area_name": area.name if area else "Unknown",
                "is_active": assignment.is_active,
                "expires_at": assignment.expires_at.isoformat() if assignment.expires_at else None,
            }
        
        return {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "document_path": document_path,
            "action": action,
            "can_access": can_access,
            "reason": reason,
            "assignment_details": assignment_details,
            "validated_at": datetime.utcnow().isoformat(),
            "context": context,
        }
    
    def _check_area_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_path: str,
    ) -> Tuple[bool, str]:
        """
        Verifica acesso baseado em área.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            document_path: Caminho do documento
            
        Returns:
            Tuple com (pode_acessar, motivo)
        """
        # Obter atribuição do usuário
        assignment = self.user_function_area_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not assignment:
            return False, "User has no area assignment"
        
        # Obter área do usuário
        user_area = self.document_area_repository.get_by_id(assignment.area_id)
        if not user_area:
            return False, "User area not found"
        
        # Obter todas as áreas para calcular hierarquia
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        # Obter áreas acessíveis
        accessible_areas = self._get_user_accessible_areas(user_area, all_areas)
        
        # Verificar se alguma área permite acesso
        for area in accessible_areas:
            if area.can_access_folder(document_path):
                return True, f"Access granted via area: {area.name}"
        
        return False, "No accessible area grants access to this document"
    
    def _check_management_permissions(
        self,
        function: ManagementFunction,
        document_path: str,
        action: str,
    ) -> Tuple[bool, str]:
        """
        Verifica permissões de função de gerenciamento.
        
        Args:
            function: Função de gerenciamento
            document_path: Caminho do documento
            action: Ação solicitada
            
        Returns:
            Tuple com (pode_acessar, motivo)
        """
        # Mapear ação para permissão
        action_permission_map = {
            "read": "document:read",
            "write": "document:update",
            "create": "document:create",
            "delete": "document:delete",
            "share": "document:share",
            "download": "document:download",
            "ai_query": "document:ai_query",
            "train": "document:train",
        }
        
        required_permission = action_permission_map.get(action, f"document:{action}")
        
        # Verificar se função tem permissão
        if function.has_permission(required_permission):
            return True, f"Access granted via function permission: {required_permission}"
        
        # Verificar permissões wildcard
        if function.has_permission("document:*"):
            return True, "Access granted via document wildcard permission"
        
        if function.has_permission("*:*"):
            return True, "Access granted via global wildcard permission"
        
        return False, f"Function lacks required permission: {required_permission}"
    
    def _check_policy_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_path: str,
        action: str,
    ) -> Tuple[bool, str]:
        """
        Verifica acesso baseado em políticas ABAC.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            document_path: Caminho do documento
            action: Ação solicitada
            
        Returns:
            Tuple com (pode_acessar, motivo)
        """
        # Obter políticas aplicáveis
        policies = self.policy_repository.get_by_organization_and_resource(
            organization_id, "document"
        )
        
        if not policies:
            return True, "No policies to evaluate"
        
        # Construir contexto de autorização
        context = {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "resource_type": "document",
            "resource_path": document_path,
            "action": action,
        }
        
        # Avaliar políticas
        for policy in policies:
            if policy.is_active:
                decision = self.policy_evaluation_service.evaluate_policy(
                    policy, context
                )
                
                if decision.effect == "deny":
                    return False, f"Access denied by policy: {policy.name}"
        
        return True, "Policy evaluation passed"
    
    def _get_user_accessible_areas(
        self,
        user_area: DocumentArea,
        all_areas: List[DocumentArea],
    ) -> List[DocumentArea]:
        """
        Obtém todas as áreas acessíveis por um usuário.
        
        Args:
            user_area: Área principal do usuário
            all_areas: Todas as áreas da organização
            
        Returns:
            Lista de áreas acessíveis
        """
        accessible_areas = [user_area]
        
        # Adicionar áreas pai (usuário pode acessar hierarquia para cima)
        hierarchy_path = user_area.get_hierarchy_path(all_areas)
        for area_id in hierarchy_path:
            if area_id != user_area.id:
                area = next((a for a in all_areas if a.id == area_id), None)
                if area and area.is_active:
                    accessible_areas.append(area)
        
        return accessible_areas
    
    def create_area_access_log(
        self,
        user_id: UUID,
        organization_id: UUID,
        resource_path: str,
        action: str,
        access_granted: bool,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Cria um log de acesso a área.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            resource_path: Caminho do recurso
            action: Ação realizada
            access_granted: Se o acesso foi concedido
            reason: Motivo da decisão
            
        Returns:
            Dicionário com log de acesso
        """
        return {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "resource_path": resource_path,
            "action": action,
            "access_granted": access_granted,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }