 Plano de Implementação: Funções e Áreas para Gerenciamento e Acesso │ │
│ │  a Documentos                                                       │ │
│ │                                                                     │ │
│ │ Análise da Nova Diretriz                                            │ │
│ │                                                                     │ │
│ │ Funções (ex: admin, gerenciador, membro)                            │ │
│ │                                                                     │ │
│ │ - Controlam exclusivamente permissões na plataforma de              │ │
│ │ gerenciamento                                                       │ │
│ │ - Substituem o uso atual de Role para contexto de gerenciamento     │ │
│ │ - Não afetam outros contextos do sistema (chat, API, etc.)          │ │
│ │                                                                     │ │
│ │ Áreas (ex: RH, RH-junior)                                           │ │
│ │                                                                     │ │
│ │ - Controlam acesso hierárquico a pastas/arquivos para o LLM         │ │
│ │ - Exemplo: usuário na Área "RH" acessa pasta "RH" e todas as        │ │
│ │ subpastas recursivamente                                            │ │
│ │ - Definição granular de quem pode acessar cada recurso documental   │ │
│ │                                                                     │ │
│ │ 1. Novas Entidades de Domínio                                       │ │
│ │                                                                     │ │
│ │ Entidade ManagementFunction                                         │ │
│ │                                                                     │ │
│ │ class ManagementFunction(BaseModel):                                │ │
│ │     id: UUID                                                        │ │
│ │     name: str  # "admin", "gerenciador", "membro"                   │ │
│ │     description: str                                                │ │
│ │     organization_id: UUID                                           │ │
│ │     permissions: List[str]  # Permissões específicas de             │ │
│ │ gerenciamento                                                       │ │
│ │     created_at: datetime                                            │ │
│ │     is_active: bool = True                                          │ │
│ │                                                                     │ │
│ │ Entidade DocumentArea                                               │ │
│ │                                                                     │ │
│ │ class DocumentArea(BaseModel):                                      │ │
│ │     id: UUID                                                        │ │
│ │     name: str  # "RH", "RH-junior", "Financeiro"                    │ │
│ │     description: str                                                │ │
│ │     organization_id: UUID                                           │ │
│ │     parent_area_id: Optional[UUID]  # Hierarquia de áreas           │ │
│ │     folder_path: str  # Caminho da pasta no sistema                 │ │
│ │     created_at: datetime                                            │ │
│ │     is_active: bool = True                                          │ │
│ │                                                                     │ │
│ │ Entidade DocumentFolder                                             │ │
│ │                                                                     │ │
│ │ class DocumentFolder(BaseModel):                                    │ │
│ │     id: UUID                                                        │ │
│ │     name: str                                                       │ │
│ │     path: str  # Caminho completo da pasta                          │ │
│ │     area_id: UUID  # Área que tem acesso                            │ │
│ │     organization_id: UUID                                           │ │
│ │     parent_folder_id: Optional[UUID]  # Estrutura hierárquica       │ │
│ │     allowed_areas: List[UUID]  # Áreas que podem acessar            │ │
│ │     created_at: datetime                                            │ │
│ │     is_active: bool = True                                          │ │
│ │                                                                     │ │
│ │ Entidade UserFunctionArea                                           │ │
│ │                                                                     │ │
│ │ class UserFunctionArea(BaseModel):                                  │ │
│ │     id: UUID                                                        │ │
│ │     user_id: UUID                                                   │ │
│ │     organization_id: UUID                                           │ │
│ │     function_id: UUID  # Função de gerenciamento                    │ │
│ │     area_id: UUID  # Área de documentos                             │ │
│ │     assigned_by: UUID                                               │ │
│ │     assigned_at: datetime                                           │ │
│ │     is_active: bool = True                                          │ │
│ │                                                                     │ │
│ │ 2. Modificações no Sistema Atual                                    │ │
│ │                                                                     │ │
│ │ Manter Role para Outros Contextos                                   │ │
│ │                                                                     │ │
│ │ - Roles continuam existindo para chat, API, outros módulos          │ │
│ │ - Apenas contexto de gerenciamento usa ManagementFunction           │ │
│ │                                                                     │ │
│ │ Expandir Permission para Contextos                                  │ │
│ │                                                                     │ │
│ │ class Permission(BaseModel):                                        │ │
│ │     # ... campos existentes ...                                     │ │
│ │     context: str  # "management", "chat", "api", "document"         │ │
│ │                                                                     │ │
│ │     def is_management_permission(self) -> bool:                     │ │
│ │         return self.context == "management"                         │ │
│ │                                                                     │ │
│ │ Atualizar Resource para Suporte a Pastas                            │ │
│ │                                                                     │ │
│ │ class Resource(BaseModel):                                          │ │
│ │     # ... campos existentes ...                                     │ │
│ │     folder_path: Optional[str] = None  # Para recursos tipo FOLDER  │ │
│ │     area_restrictions: List[UUID] = []  # Áreas que podem acessar   │ │
│ │                                                                     │ │
│ │ 3. Serviços de Domínio                                              │ │
│ │                                                                     │ │
│ │ ManagementFunctionService                                           │ │
│ │                                                                     │ │
│ │ - Gerencia funções de gerenciamento                                 │ │
│ │ - Valida permissões específicas de gerenciamento                    │ │
│ │ - Integra com sistema de autenticação                               │ │
│ │                                                                     │ │
│ │ DocumentAreaService                                                 │ │
│ │                                                                     │ │
│ │ - Gerencia áreas e hierarquias                                      │ │
│ │ - Calcula acesso recursivo a pastas                                 │ │
│ │ - Valida permissões de acesso a documentos                          │ │
│ │                                                                     │ │
│ │ DocumentAccessService                                               │ │
│ │                                                                     │ │
│ │ - Determina se usuário pode acessar documento/pasta                 │ │
│ │ - Implementa lógica de herança hierárquica                          │ │
│ │ - Integra com políticas existentes (ABAC)                           │ │
│ │                                                                     │ │
│ │ FolderHierarchyService                                              │ │
│ │                                                                     │ │
│ │ - Gerencia estrutura hierárquica de pastas                          │ │
│ │ - Calcula acesso recursivo baseado em áreas                         │ │
│ │ - Sincroniza com sistema de arquivos                                │ │
│ │                                                                     │ │
│ │ 4. Integração com Sistema Existente                                 │ │
│ │                                                                     │ │
│ │ Políticas ABAC para Documentos                                      │ │
│ │                                                                     │ │
│ │ Atualizar DocumentPolicyTemplates para incluir:                     │ │
│ │ def create_area_based_access_policy(created_by: UUID,               │ │
│ │ organization_id: UUID) -> Policy:                                   │ │
│ │     return Policy.create(                                           │ │
│ │         name="Area-based Document Access",                          │ │
│ │         description="Allow access to documents based on user's      │ │
│ │ area",                                                              │ │
│ │         effect=PolicyEffect.ALLOW,                                  │ │
│ │         resource_type="document",                                   │ │
│ │         action="read",                                              │ │
│ │         conditions=[                                                │ │
│ │             PolicyCondition(                                        │ │
│ │                 attribute="user_areas",                             │ │
│ │                 operator="intersects",                              │ │
│ │                 value="{resource.allowed_areas}"                    │ │
│ │             )                                                       │ │
│ │         ],                                                          │ │
│ │         created_by=created_by,                                      │ │
│ │         organization_id=organization_id,                            │ │
│ │         priority=85                                                 │ │
│ │     )                                                               │ │
│ │                                                                     │ │
│ │ Atualizar JWTAuthenticationContext                                  │ │
│ │                                                                     │ │
│ │ class JWTAuthenticationContext:                                     │ │
│ │     # ... campos existentes ...                                     │ │
│ │     management_function: Optional[str] = None                       │ │
│ │     document_areas: List[str] = []                                  │ │
│ │                                                                     │ │
│ │     def has_management_permission(self, permission: str) -> bool:   │ │
│ │         # Verificar permissões de função de gerenciamento           │ │
│ │                                                                     │ │
│ │     def can_access_document_area(self, area: str) -> bool:          │ │
│ │         # Verificar acesso à área de documentos                     │ │
│ │                                                                     │ │
│ │ 5. Camada de Aplicação                                              │ │
│ │                                                                     │ │
│ │ Novos DTOs                                                          │ │
│ │                                                                     │ │
│ │ class ManagementFunctionDTO(BaseModel):                             │ │
│ │     name: str                                                       │ │
│ │     description: str                                                │ │
│ │     permissions: List[str]                                          │ │
│ │                                                                     │ │
│ │ class DocumentAreaDTO(BaseModel):                                   │ │
│ │     name: str                                                       │ │
│ │     description: str                                                │ │
│ │     parent_area_id: Optional[UUID]                                  │ │
│ │     folder_path: str                                                │ │
│ │                                                                     │ │
│ │ class UserFunctionAreaAssignmentDTO(BaseModel):                     │ │
│ │     user_id: UUID                                                   │ │
│ │     function_id: UUID                                               │ │
│ │     area_id: UUID                                                   │ │
│ │                                                                     │ │
│ │ Novos Casos de Uso                                                  │ │
│ │                                                                     │ │
│ │ - AssignUserFunctionAreaUseCase                                     │ │
│ │ - ManageDocumentAreasUseCase                                        │ │
│ │ - ValidateDocumentAccessUseCase                                     │ │
│ │ - SetupFolderHierarchyUseCase                                       │ │
│ │                                                                     │ │
│ │ 6. Infraestrutura                                                   │ │
│ │                                                                     │ │
│ │ Novos Repositórios                                                  │ │
│ │                                                                     │ │
│ │ - ManagementFunctionRepository                                      │ │
│ │ - DocumentAreaRepository                                            │ │
│ │ - DocumentFolderRepository                                          │ │
│ │ - UserFunctionAreaRepository                                        │ │
│ │                                                                     │ │
│ │ Integração com Storage                                              │ │
│ │                                                                     │ │
│ │ - Conectar com sistema de arquivos real                             │ │
│ │ - Sincronizar pastas virtuais com pastas físicas                    │ │
│ │ - Implementar cache de estrutura de pastas                          │ │
│ │                                                                     │ │
│ │ 7. Camada de Apresentação                                           │ │
│ │                                                                     │ │
│ │ Novos Endpoints                                                     │ │
│ │                                                                     │ │
│ │ # Gerenciamento de Funções                                          │ │
│ │ POST /management/functions                                          │ │
│ │ GET /management/functions                                           │ │
│ │ PUT /management/functions/{id}                                      │ │
│ │                                                                     │ │
│ │ # Gerenciamento de Áreas                                            │ │
│ │ POST /document/areas                                                │ │
│ │ GET /document/areas                                                 │ │
│ │ PUT /document/areas/{id}                                            │ │
│ │                                                                     │ │
│ │ # Atribuição de Função+Área                                         │ │
│ │ POST /users/{user_id}/function-area                                 │ │
│ │ GET /users/{user_id}/function-area                                  │ │
│ │                                                                     │ │
│ │ Middleware de Validação                                             │ │
│ │                                                                     │ │
│ │ - Verificar função de gerenciamento em endpoints admin              │ │
│ │ - Validar acesso a área em endpoints de documentos                  │ │
│ │ - Manter compatibilidade com sistema atual                          │ │
│ │                                                                     │ │
│ │ 8. Configuração Padrão                                              │ │
│ │                                                                     │ │
│ │ Funções Padrão de Gerenciamento                                     │ │
│ │                                                                     │ │
│ │ {                                                                   │ │
│ │   "admin": {                                                        │ │
│ │     "permissions": ["management:*"],                                │ │
│ │     "description": "Acesso total ao gerenciamento"                  │ │
│ │   },                                                                │ │
│ │   "gerenciador": {                                                  │ │
│ │     "permissions": ["management:read", "management:update",         │ │
│ │ "users:manage"],                                                    │ │
│ │     "description": "Gerenciamento limitado"                         │ │
│ │   },                                                                │ │
│ │   "membro": {                                                       │ │
│ │     "permissions": ["management:read"],                             │ │
│ │     "description": "Apenas visualização"                            │ │
│ │   }                                                                 │ │
│ │ }                                                                   │ │
│ │                                                                     │ │
│ │ Áreas Padrão de Documentos                                          │ │
│ │                                                                     │ │
│ │ {                                                                   │ │
│ │   "areas": [                                                        │ │
│ │     {                                                               │ │
│ │       "name": "RH",                                                 │ │
│ │       "folder_path": "/documents/RH",                               │ │
│ │       "description": "Documentos de Recursos Humanos"               │ │
│ │     },                                                              │ │
│ │     {                                                               │ │
│ │       "name": "RH-junior",                                          │ │
│ │       "parent_area": "RH",                                          │ │
│ │       "folder_path": "/documents/RH/junior",                        │ │
│ │       "description": "Documentos RH nível junior"                   │ │
│ │     }                                                               │ │
│ │   ]                                                                 │ │
│ │ }                                                                   │ │
│ │                                                                     │ │
│ │ 9. Migração e Coexistência                                          │ │
│ │                                                                     │ │
│ │ Fase 1: Implementação Paralela                                      │ │
│ │                                                                     │ │
│ │ - Manter sistema atual funcionando                                  │ │
│ │ - Implementar funções e áreas como novos módulos                    │ │
│ │ - Dupla validação (role + função) temporariamente                   │ │
│ │                                                                     │ │
│ │ Fase 2: Transição Gradual                                           │ │
│ │                                                                     │ │
│ │ - Migrar endpoints de gerenciamento para usar funções               │ │
│ │ - Implementar acesso a documentos por área                          │ │
│ │ - Manter compatibilidade com APIs existentes                        │ │
│ │                                                                     │ │
│ │ Fase 3: Consolidação                                                │ │
│ │                                                                     │ │
│ │ - Remover código legado de roles em contexto de gerenciamento       │ │
│ │ - Otimizar queries de acesso a documentos                           │ │
│ │ - Documentar novo sistema                                           │ │
│ │                                                                     │ │
│ │ 10. Benefícios da Implementação                                     │ │
│ │                                                                     │ │
│ │ 1. Separação Clara de Responsabilidades                             │ │
│ │   - Funções: controle de gerenciamento                              │ │
│ │   - Áreas: controle de documentos                                   │ │
│ │ 2. Flexibilidade Hierárquica                                        │ │
│ │   - Áreas podem ter subáreas                                        │ │
│ │   - Acesso recursivo a pastas                                       │ │
│ │ 3. Escalabilidade                                                   │ │
│ │   - Fácil adição de novas funções/áreas                             │ │
│ │   - Suporte a múltiplas organizações                                │ │
│ │ 4. Integração com LLM                                               │ │
│ │   - Controle granular de acesso a documentos                        │ │
│ │   - Suporte a políticas de privacidade                              │ │
│ │ 5. Compatibilidade                                                  │ │
│ │   - Coexistência com sistema atual                                  │ │
│ │   - Migração gradual sem interrupção                                │ │
│ │                                                                     │ │
│ │ 11. Casos de Uso Práticos                                           │ │
│ │                                                                     │ │
│ │ Exemplo 1: Usuário RH                                               │ │
│ │                                                                     │ │
│ │ - Função: "gerenciador" (pode gerenciar usuários)                   │ │
│ │ - Área: "RH" (acesso a /documents/RH/*)                             │ │
│ │ - Pode gerenciar membros E acessar documentos de RH                 │ │
│ │                                                                     │ │
│ │ Exemplo 2: Usuário RH Junior                                        │ │
│ │                                                                     │ │
│ │ - Função: "membro" (só visualização)                                │ │
│ │ - Área: "RH-junior" (acesso a /documents/RH/junior/*)               │ │
│ │ - Não pode gerenciar, mas acessa documentos específicos             │ │
│ │                                                                     │ │
│ │ Exemplo 3: Admin                                                    │ │
│ │                                                                     │ │
│ │ - Função: "admin" (acesso total)                                    │ │
│ │ - Área: "Todas" (acesso a todos os documentos)                      │ │
│ │ - Controle total da plataforma                                      │ │
│ │                                                                     │ │
│ │ Esta implementação atende perfeitamente à nova diretriz, separando  │ │
│ │ claramente o controle de gerenciamento do controle de acesso a      │ │
│ │ documentos, enquanto mantém compatibilidade com o sistema           │ │
│ │ existente.   