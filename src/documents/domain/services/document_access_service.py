from typing import List, Optional, Set, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from ..entities.document_area import DocumentArea
from ..entities.document_folder import DocumentFolder
from ..entities.user_document_access import UserDocumentAccess
from ..value_objects.access_level import AccessLevel
from ..value_objects.folder_path import FolderPath
from ..repositories.document_area_repository import DocumentAreaRepository
from ..repositories.document_folder_repository import DocumentFolderRepository
from ..repositories.user_document_access_repository import UserDocumentAccessRepository
from ...application.contracts.iam_contract import IAMContract


class DocumentAccessService:
    """
    Domain Service para controle de acesso a documentos.
    
    Centraliza as regras de negócio para verificação de permissões
    e controle de acesso hierárquico a documentos e pastas.
    """

    def __init__(
        self,
        document_area_repository: DocumentAreaRepository,
        document_folder_repository: DocumentFolderRepository,
        user_document_access_repository: UserDocumentAccessRepository,
        iam_contract: IAMContract,
    ):
        self._document_area_repository = document_area_repository
        self._document_folder_repository = document_folder_repository
        self._user_document_access_repository = user_document_access_repository
        self._iam_contract = iam_contract

    def can_user_access_folder(
        self,
        user_id: UUID,
        folder_path: str,
        organization_id: UUID,
        required_action: str = "read"
    ) -> Tuple[bool, str]:
        """
        Verifica se um usuário pode acessar uma pasta específica para uma ação.
        
        Args:
            user_id: ID do usuário
            folder_path: Caminho da pasta
            organization_id: ID da organização
            required_action: Ação requerida (read, write, delete, etc.)
        
        Returns:
            Tupla (pode_acessar, motivo)
        """
        # Verificar se usuário está ativo na organização via IAM
        if not self._iam_contract.verify_user_active(user_id, organization_id):
            return False, "User is not active in organization"

        # Obter acessos ativos do usuário
        user_accesses = self._user_document_access_repository.get_active_by_user(user_id)
        
        # Filtrar por organização
        org_accesses = [access for access in user_accesses if access.organization_id == organization_id]
        
        if not org_accesses:
            return False, "User has no document access in organization"

        # Obter áreas do usuário
        user_area_ids = [access.area_id for access in org_accesses]
        user_areas = []
        
        for area_id in user_area_ids:
            area = self._document_area_repository.get_by_id(area_id)
            if area and area.is_active:
                user_areas.append(area)

        if not user_areas:
            return False, "User has no active areas"

        # Verificar se alguma área permite acesso à pasta
        for area in user_areas:
            if area.can_access_folder(folder_path):
                # Verificar se o nível de acesso permite a ação
                user_access = next(
                    (access for access in org_accesses if access.area_id == area.id),
                    None
                )
                
                if user_access and user_access.access_level.can_perform_action(required_action):
                    return True, f"Access granted via area '{area.name}'"

        return False, f"No area grants '{required_action}' access to folder"

    def get_user_accessible_folders(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> List[str]:
        """
        Retorna lista de caminhos de pastas que o usuário pode acessar.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Lista de caminhos de pastas acessíveis
        """
        # Verificar se usuário está ativo
        if not self._iam_contract.verify_user_active(user_id, organization_id):
            return []

        # Obter acessos ativos do usuário
        user_accesses = self._user_document_access_repository.get_active_by_user(user_id)
        
        # Filtrar por organização
        org_accesses = [access for access in user_accesses if access.organization_id == organization_id]
        
        if not org_accesses:
            return []

        accessible_paths = set()

        # Para cada área que o usuário tem acesso
        for access in org_accesses:
            area = self._document_area_repository.get_by_id(access.area_id)
            if area and area.is_active:
                # Obter todas as áreas da hierarquia
                hierarchy = self._document_area_repository.get_hierarchy_for_area(area.id)
                
                # Adicionar caminhos acessíveis
                area_paths = area.get_accessible_paths(hierarchy)
                accessible_paths.update(area_paths)

        return sorted(list(accessible_paths))

    def get_user_areas_with_access_levels(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> List[Tuple[DocumentArea, AccessLevel]]:
        """
        Retorna áreas que o usuário tem acesso junto com seus níveis.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Lista de tuplas (área, nível_de_acesso)
        """
        # Verificar se usuário está ativo
        if not self._iam_contract.verify_user_active(user_id, organization_id):
            return []

        # Obter acessos ativos do usuário
        user_accesses = self._user_document_access_repository.get_active_by_user(user_id)
        
        # Filtrar por organização
        org_accesses = [access for access in user_accesses if access.organization_id == organization_id]
        
        result = []
        
        for access in org_accesses:
            area = self._document_area_repository.get_by_id(access.area_id)
            if area and area.is_active:
                result.append((area, access.access_level))

        return result

    def get_highest_access_level_for_folder(
        self,
        user_id: UUID,
        folder_path: str,
        organization_id: UUID
    ) -> Optional[AccessLevel]:
        """
        Retorna o maior nível de acesso do usuário para uma pasta específica.
        
        Args:
            user_id: ID do usuário
            folder_path: Caminho da pasta
            organization_id: ID da organização
            
        Returns:
            Maior nível de acesso ou None se não tiver acesso
        """
        user_areas_with_levels = self.get_user_areas_with_access_levels(user_id, organization_id)
        
        highest_level = None
        
        for area, access_level in user_areas_with_levels:
            if area.can_access_folder(folder_path):
                if highest_level is None or access_level.is_higher_than(highest_level):
                    highest_level = access_level

        return highest_level

    def validate_area_hierarchy_consistency(
        self,
        area: DocumentArea,
        all_areas: List[DocumentArea]
    ) -> Tuple[bool, List[str]]:
        """
        Valida a consistência da hierarquia de uma área.
        
        Args:
            area: Área a ser validada
            all_areas: Todas as áreas da organização
            
        Returns:
            Tupla (is_valid, error_messages)
        """
        errors = []
        
        # Validar hierarquia básica
        is_valid, message = area.validate_hierarchy(all_areas)
        if not is_valid:
            errors.append(message)

        # Validar se não há conflitos de caminhos
        for other_area in all_areas:
            if other_area.id != area.id and other_area.organization_id == area.organization_id:
                if other_area.folder_path == area.folder_path:
                    errors.append(f"Folder path conflict with area '{other_area.name}'")

        # Validar se área pai permite acesso ao caminho da área filha
        if area.parent_area_id:
            parent_area = next(
                (a for a in all_areas if a.id == area.parent_area_id),
                None
            )
            
            if parent_area:
                if not parent_area.can_access_folder(area.folder_path):
                    errors.append("Parent area cannot access child area folder path")

        return len(errors) == 0, errors

    def can_user_create_folder_in_path(
        self,
        user_id: UUID,
        parent_folder_path: str,
        organization_id: UUID
    ) -> Tuple[bool, str]:
        """
        Verifica se usuário pode criar uma pasta em um caminho específico.
        
        Args:
            user_id: ID do usuário
            parent_folder_path: Caminho da pasta pai
            organization_id: ID da organização
            
        Returns:
            Tupla (pode_criar, motivo)
        """
        return self.can_user_access_folder(
            user_id=user_id,
            folder_path=parent_folder_path,
            organization_id=organization_id,
            required_action="create"
        )

    def can_user_delete_folder(
        self,
        user_id: UUID,
        folder_path: str,
        organization_id: UUID
    ) -> Tuple[bool, str]:
        """
        Verifica se usuário pode deletar uma pasta.
        
        Args:
            user_id: ID do usuário
            folder_path: Caminho da pasta
            organization_id: ID da organização
            
        Returns:
            Tupla (pode_deletar, motivo)
        """
        return self.can_user_access_folder(
            user_id=user_id,
            folder_path=folder_path,
            organization_id=organization_id,
            required_action="delete"
        )

    def get_effective_permissions_for_user(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> Dict[str, Set[str]]:
        """
        Retorna mapa de permissões efetivas do usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Dicionário {folder_path: {actions}}
        """
        permissions_map = {}
        user_areas_with_levels = self.get_user_areas_with_access_levels(user_id, organization_id)
        
        for area, access_level in user_areas_with_levels:
            # Obter hierarquia da área
            hierarchy = self._document_area_repository.get_hierarchy_for_area(area.id)
            accessible_paths = area.get_accessible_paths(hierarchy)
            
            allowed_actions = set(access_level.get_allowed_actions())
            
            for path in accessible_paths:
                if path in permissions_map:
                    # Mesclar com permissões existentes (maior nível ganha)
                    permissions_map[path].update(allowed_actions)
                else:
                    permissions_map[path] = allowed_actions.copy()

        return permissions_map

    def validate_folder_creation_request(
        self,
        user_id: UUID,
        organization_id: UUID,
        parent_folder_path: str,
        new_folder_name: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Valida uma solicitação de criação de pasta.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            parent_folder_path: Caminho da pasta pai
            new_folder_name: Nome da nova pasta
            
        Returns:
            Tupla (pode_criar, motivo, caminho_completo)
        """
        try:
            # Validar se pode criar na pasta pai
            can_create, reason = self.can_user_create_folder_in_path(
                user_id, parent_folder_path, organization_id
            )
            
            if not can_create:
                return False, reason, None

            # Validar nome da pasta
            try:
                parent_path = FolderPath(path=parent_folder_path)
                full_path = parent_path.join(new_folder_name)
            except ValueError as e:
                return False, f"Invalid folder name or path: {e}", None

            # Verificar se pasta já existe
            if self._document_folder_repository.exists_by_path(full_path.path, organization_id):
                return False, "Folder already exists", None

            return True, "Folder creation allowed", full_path.path

        except Exception as e:
            return False, f"Validation error: {e}", None

    def get_folder_access_summary(
        self,
        folder_path: str,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Retorna resumo de acesso para uma pasta.
        
        Args:
            folder_path: Caminho da pasta
            organization_id: ID da organização
            
        Returns:
            Dicionário com resumo de acesso
        """
        # Obter áreas que podem acessar a pasta
        accessible_areas = []
        all_areas = self._document_area_repository.get_active_by_organization(organization_id)
        
        for area in all_areas:
            if area.can_access_folder(folder_path):
                accessible_areas.append(area)

        # Obter usuários que podem acessar
        accessible_users = []
        for area in accessible_areas:
            users_in_area = self._user_document_access_repository.get_active_by_area(area.id)
            accessible_users.extend(users_in_area)

        # Remover duplicatas de usuários
        unique_users = {}
        for user_access in accessible_users:
            if user_access.user_id not in unique_users:
                unique_users[user_access.user_id] = user_access

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

    def cleanup_expired_access(self) -> int:
        """
        Limpa acessos expirados do sistema.
        
        Returns:
            Número de acessos limpos
        """
        return self._user_document_access_repository.cleanup_expired_access()

    def get_access_statistics_for_organization(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de acesso para uma organização.
        
        Args:
            organization_id: ID da organização
            
        Returns:
            Dicionário com estatísticas
        """
        total_access = self._user_document_access_repository.count_by_organization(organization_id)
        active_access_records = self._user_document_access_repository.get_active_by_organization(organization_id)
        expired_access = self._user_document_access_repository.get_expired(organization_id)
        expiring_soon = self._user_document_access_repository.get_expiring_soon(organization_id)

        total_areas = self._document_area_repository.count_by_organization(organization_id)
        active_areas = self._document_area_repository.count_active_by_organization(organization_id)

        total_folders = self._document_folder_repository.count_by_organization(organization_id)

        # Agrupar por nível de acesso
        access_by_level = {}
        for access in active_access_records:
            level = access.access_level.value
            access_by_level[level] = access_by_level.get(level, 0) + 1

        return {
            "total_access_records": total_access,
            "active_access_records": len(active_access_records),
            "expired_access_records": len(expired_access),
            "expiring_soon_access_records": len(expiring_soon),
            "total_areas": total_areas,
            "active_areas": active_areas,
            "total_folders": total_folders,
            "access_by_level": access_by_level,
            "unique_users_with_access": len(set(access.user_id for access in active_access_records)),
        }

    def validate_user_document_access(
        self,
        user_id: UUID,
        organization_id: UUID,
        document_path: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Valida acesso de usuário a documento com detalhes completos.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            document_path: Caminho do documento
            action: Ação requerida
            
        Returns:
            Dicionário com detalhes da validação
        """
        can_access, reason = self.can_user_access_folder(
            user_id, document_path, organization_id, action
        )

        # Obter detalhes do usuário
        user_accesses = self._user_document_access_repository.get_active_by_user(user_id)
        org_accesses = [access for access in user_accesses if access.organization_id == organization_id]

        # Obter áreas do usuário
        user_areas = []
        for access in org_accesses:
            area = self._document_area_repository.get_by_id(access.area_id)
            if area:
                user_areas.append({
                    "area_id": str(area.id),
                    "area_name": area.name,
                    "access_level": access.access_level.value,
                    "can_access_path": area.can_access_folder(document_path)
                })

        return {
            "user_id": str(user_id),
            "organization_id": str(organization_id),
            "document_path": document_path,
            "action": action,
            "can_access": can_access,
            "reason": reason,
            "user_areas": user_areas,
            "validated_at": datetime.now().isoformat(),
        }