from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.document_area import DocumentArea
from ..entities.document_folder import DocumentFolder
from ..entities.user_document_access import UserDocumentAccess
from ..repositories.document_area_repository import DocumentAreaRepository
from ..repositories.document_folder_repository import DocumentFolderRepository
from ..repositories.user_document_access_repository import UserDocumentAccessRepository
from ...application.contracts.iam_contract import IAMContract


class DocumentAreaService:
    """
    Serviço de domínio para gerenciamento de áreas de documentos.
    
    Controla as regras de negócio relacionadas a áreas que controlam
    acesso hierárquico a pastas/arquivos para o LLM.
    """
    
    def __init__(
        self,
        document_area_repository: DocumentAreaRepository,
        document_folder_repository: DocumentFolderRepository,
        user_document_access_repository: UserDocumentAccessRepository,
        iam_contract: IAMContract,
    ):
        self.document_area_repository = document_area_repository
        self.document_folder_repository = document_folder_repository
        self.user_document_access_repository = user_document_access_repository
        self.iam_contract = iam_contract
    
    def create_area(
        self,
        name: str,
        description: str,
        organization_id: UUID,
        folder_path: str,
        created_by: UUID,
        parent_area_id: Optional[UUID] = None,
        is_system_area: bool = False,
    ) -> DocumentArea:
        """
        Cria uma nova área de documentos.
        
        Args:
            name: Nome da área
            description: Descrição da área
            organization_id: ID da organização
            folder_path: Caminho da pasta
            created_by: ID do usuário que criou
            parent_area_id: ID da área pai (opcional)
            is_system_area: Se é uma área do sistema
        """
        # Verificar se usuário tem permissão para criar área
        if not self.iam_contract.verify_management_permission(
            created_by, organization_id, "management:create_area"
        ):
            raise ValueError("User lacks permission to create areas")
        
        # Verificar se já existe área com esse nome na organização
        existing_area = self.document_area_repository.get_by_name_and_organization(
            name, organization_id
        )
        if existing_area:
            raise ValueError(f"Area with name '{name}' already exists in organization")
        
        # Verificar se caminho já está em uso
        existing_path = self.document_area_repository.get_by_folder_path_and_organization(
            folder_path, organization_id
        )
        if existing_path:
            raise ValueError(f"Folder path '{folder_path}' already in use")
        
        # Se tem área pai, validar hierarquia
        if parent_area_id:
            parent_area = self.document_area_repository.get_by_id(parent_area_id)
            if not parent_area:
                raise ValueError(f"Parent area {parent_area_id} not found")
            
            if parent_area.organization_id != organization_id:
                raise ValueError("Parent area must be in same organization")
            
            if not parent_area.is_active:
                raise ValueError("Cannot create child of inactive parent area")
        
        # Criar área
        area = DocumentArea.create(
            name=name,
            description=description,
            organization_id=organization_id,
            folder_path=folder_path,
            created_by=created_by,
            parent_area_id=parent_area_id,
            is_system_area=is_system_area,
        )
        
        # Salvar área
        saved_area = self.document_area_repository.save(area)
        
        # Criar pasta correspondente
        self._create_folder_for_area(saved_area)
        
        return saved_area
    
    def update_area_folder_path(
        self,
        area_id: UUID,
        new_folder_path: str,
        updated_by: UUID,
    ) -> DocumentArea:
        """
        Atualiza o caminho da pasta de uma área.
        
        Args:
            area_id: ID da área
            new_folder_path: Novo caminho da pasta
            updated_by: ID do usuário que atualizou
        """
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")
        
        # Verificar se usuário tem permissão para atualizar área
        if not self.iam_contract.verify_management_permission(
            updated_by, area.organization_id, "management:update_area"
        ):
            raise ValueError("User lacks permission to update areas")
        
        # Verificar se novo caminho já está em uso
        existing_path = self.document_area_repository.get_by_folder_path_and_organization(
            new_folder_path, area.organization_id
        )
        if existing_path and existing_path.id != area_id:
            raise ValueError(f"Folder path '{new_folder_path}' already in use")
        
        # Atualizar área
        updated_area = area.update_folder_path(new_folder_path)
        
        # Salvar área
        saved_area = self.document_area_repository.save(updated_area)
        
        # Atualizar pasta correspondente
        self._update_folder_for_area(saved_area)
        
        return saved_area
    
    def assign_area_to_user(
        self,
        user_id: UUID,
        area_id: UUID,
        organization_id: UUID,
        assigned_by: UUID,
    ) -> UserDocumentAccess:
        """
        Atribui uma área a um usuário.
        
        Args:
            user_id: ID do usuário
            area_id: ID da área
            organization_id: ID da organização
            assigned_by: ID do usuário que fez a atribuição
        """
        # Verificar se usuário tem permissão para atribuir área
        if not self.iam_contract.verify_management_permission(
            assigned_by, organization_id, "management:assign_area"
        ):
            raise ValueError("User lacks permission to assign areas")
        
        # Verificar se área existe
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")
        
        if not area.is_active:
            raise ValueError("Cannot assign inactive area")
        
        # Verificar se usuário está ativo na organização
        if not self.iam_contract.verify_user_active(user_id, organization_id):
            raise ValueError("User is not active in organization")
        
        # Verificar se usuário já tem acesso
        existing_access = self.user_document_access_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if existing_access and existing_access.is_active:
            # Atualizar área existente
            updated_access = existing_access.update_area(area_id)
            return self.user_document_access_repository.save(updated_access)
        else:
            # Criar novo acesso
            new_access = UserDocumentAccess.create(
                user_id=user_id,
                organization_id=organization_id,
                area_id=area_id,
                assigned_by=assigned_by,
            )
            return self.user_document_access_repository.save(new_access)
    
    def get_user_accessible_areas(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> List[DocumentArea]:
        """
        Obtém todas as áreas acessíveis por um usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Lista de áreas acessíveis
        """
        # Verificar se usuário está ativo
        if not self.iam_contract.verify_user_active(user_id, organization_id):
            return []
        
        # Obter acesso do usuário
        user_access = self.user_document_access_repository.get_by_user_and_organization(
            user_id, organization_id
        )
        
        if not user_access or not user_access.is_valid():
            return []
        
        # Obter área principal do usuário
        primary_area = self.document_area_repository.get_by_id(user_access.area_id)
        if not primary_area:
            return []
        
        # Obter todas as áreas da organização para calcular hierarquia
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        # Calcular áreas acessíveis (área principal + áreas pai)
        accessible_areas = []
        
        # Adicionar área principal
        accessible_areas.append(primary_area)
        
        # Adicionar áreas pai (usuário pode acessar hierarquia para cima)
        hierarchy_path = primary_area.get_hierarchy_path(all_areas)
        for area_id in hierarchy_path:
            if area_id != primary_area.id:
                area = next((a for a in all_areas if a.id == area_id), None)
                if area and area.is_active:
                    accessible_areas.append(area)
        
        return accessible_areas
    
    def get_user_accessible_folder_paths(
        self,
        user_id: UUID,
        organization_id: UUID,
    ) -> List[str]:
        """
        Obtém todos os caminhos de pastas acessíveis por um usuário.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            
        Returns:
            Lista de caminhos de pastas acessíveis
        """
        accessible_areas = self.get_user_accessible_areas(user_id, organization_id)
        
        folder_paths = []
        for area in accessible_areas:
            # Adicionar caminho da área
            folder_paths.append(area.folder_path)
            
            # Adicionar acesso recursivo (subpastas)
            folder_paths.append(area.folder_path.rstrip("/") + "/*")
        
        return list(set(folder_paths))  # Remover duplicatas
    
    def user_can_access_folder(
        self,
        user_id: UUID,
        organization_id: UUID,
        folder_path: str,
    ) -> bool:
        """
        Verifica se um usuário pode acessar uma pasta específica.
        
        Args:
            user_id: ID do usuário
            organization_id: ID da organização
            folder_path: Caminho da pasta
            
        Returns:
            True se o usuário pode acessar a pasta
        """
        accessible_areas = self.get_user_accessible_areas(user_id, organization_id)
        
        for area in accessible_areas:
            if area.can_access_folder(folder_path):
                return True
        
        return False
    
    def get_areas_by_folder_path(
        self,
        folder_path: str,
        organization_id: UUID,
    ) -> List[DocumentArea]:
        """
        Obtém todas as áreas que podem acessar um caminho de pasta.
        
        Args:
            folder_path: Caminho da pasta
            organization_id: ID da organização
            
        Returns:
            Lista de áreas que podem acessar a pasta
        """
        all_areas = self.document_area_repository.get_by_organization(organization_id)
        
        accessible_areas = []
        for area in all_areas:
            if area.is_active and area.can_access_folder(folder_path):
                accessible_areas.append(area)
        
        return accessible_areas
    
    def create_default_areas(self, organization_id: UUID) -> List[DocumentArea]:
        """
        Cria áreas padrão para uma organização.
        
        Args:
            organization_id: ID da organização
            
        Returns:
            Lista de áreas padrão criadas
        """
        # Obter informações da organização via IAM
        org_users = self.iam_contract.get_organization_users(organization_id)
        if not org_users:
            raise ValueError("No users found in organization")
        
        # Usar o primeiro usuário como criador (idealmente seria o admin)
        created_by = org_users[0].id
        
        default_areas = [
            {
                "name": "Documentos Gerais",
                "description": "Documentos gerais da organização",
                "folder_path": f"/documents/org_{organization_id}/geral",
            },
            {
                "name": "RH",
                "description": "Documentos de Recursos Humanos",
                "folder_path": f"/documents/org_{organization_id}/rh",
            },
            {
                "name": "Financeiro",
                "description": "Documentos financeiros",
                "folder_path": f"/documents/org_{organization_id}/financeiro",
            },
            {
                "name": "TI",
                "description": "Documentos de Tecnologia da Informação",
                "folder_path": f"/documents/org_{organization_id}/ti",
            },
        ]
        
        created_areas = []
        for area_data in default_areas:
            try:
                area = self.create_area(
                    name=area_data["name"],
                    description=area_data["description"],
                    organization_id=organization_id,
                    folder_path=area_data["folder_path"],
                    created_by=created_by,
                    is_system_area=True,
                )
                created_areas.append(area)
            except ValueError:
                # Área já existe, pular
                continue
        
        return created_areas
    
    def validate_area_hierarchy(
        self,
        area_id: UUID,
    ) -> tuple[bool, str]:
        """
        Valida a hierarquia de uma área.
        
        Args:
            area_id: ID da área
            
        Returns:
            Tuple com (is_valid, error_message)
        """
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            return False, f"Area {area_id} not found"
        
        # Obter todas as áreas da organização
        all_areas = self.document_area_repository.get_by_organization(area.organization_id)
        
        return area.validate_hierarchy(all_areas)
    
    def get_accessible_folders(self, area: DocumentArea) -> List[str]:
        """
        Obtém pastas acessíveis por uma área.
        
        Args:
            area: Área de documentos
            
        Returns:
            Lista de caminhos de pastas acessíveis
        """
        # Obter todas as áreas da organização
        all_areas = self.document_area_repository.get_by_organization(area.organization_id)
        
        return area.get_accessible_paths(all_areas)
    
    def _create_folder_for_area(self, area: DocumentArea) -> DocumentFolder:
        """
        Cria uma pasta correspondente para uma área.
        
        Args:
            area: Área de documentos
            
        Returns:
            Pasta criada
        """
        folder = DocumentFolder.create(
            name=area.name,
            path=area.folder_path,
            area_id=area.id,
            organization_id=area.organization_id,
            created_by=area.created_by,
            is_virtual=True,  # Pastas de área são virtuais
        )
        
        return self.document_folder_repository.save(folder)
    
    def _update_folder_for_area(self, area: DocumentArea) -> DocumentFolder:
        """
        Atualiza a pasta correspondente de uma área.
        
        Args:
            area: Área de documentos
            
        Returns:
            Pasta atualizada
        """
        # Buscar pasta existente
        existing_folders = self.document_folder_repository.get_by_area(area.id)
        
        if existing_folders:
            # Atualizar primeira pasta encontrada
            existing_folder = existing_folders[0]
            updated_folder = existing_folder.update_name(area.name)
            return self.document_folder_repository.save(updated_folder)
        else:
            # Criar nova pasta se não existir
            return self._create_folder_for_area(area)
    
    def get_area_statistics(
        self,
        area_id: UUID,
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de uma área.
        
        Args:
            area_id: ID da área
            
        Returns:
            Dicionário com estatísticas
        """
        area = self.document_area_repository.get_by_id(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")
        
        # Contar usuários na área
        users_in_area = self.user_document_access_repository.get_by_area(area_id)
        active_users = [u for u in users_in_area if u.is_active]
        
        # Contar pastas na área
        folders_in_area = self.document_folder_repository.get_by_area(area_id)
        active_folders = [f for f in folders_in_area if f.is_active]
        
        # Obter áreas filhas
        child_areas = self.document_area_repository.get_by_parent_area(area_id)
        
        return {
            "area_id": str(area_id),
            "area_name": area.name,
            "folder_path": area.folder_path,
            "total_users": len(users_in_area),
            "active_users": len(active_users),
            "total_folders": len(folders_in_area),
            "active_folders": len(active_folders),
            "child_areas": len(child_areas),
            "is_active": area.is_active,
            "created_at": area.created_at.isoformat(),
        }