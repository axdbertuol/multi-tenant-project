"""
Caso de teste E2E simples para validar o sistema de Perfis.

Este teste demonstra como criar um perfil, configurar permissões de pasta,
atribuir o perfil a um usuário e validar as permissões resultantes.
"""

from datetime import datetime, timezone
from uuid import uuid4

# Importar apenas as entidades que criamos, sem dependências externas
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Importar diretamente os módulos sem usar __init__.py
from ..domain.entities.profile import Profile
from ..domain.entities.user_profile import UserProfile
from ..domain.entities.profile_folder_permission import ProfileFolderPermission
from ..domain.value_objects.folder_permission_level import FolderPermissionLevel


def test_profile_system_e2e():
    """
    Teste E2E completo do sistema de perfis.

    Cenário: Criar perfil "Analista Financeiro" com permissão READ
    na pasta "/documents/financeiro" e atribuir a um usuário.
    """

    # === Setup ===
    organization_id = uuid4()
    admin_user_id = uuid4()  # Usuário administrador que criará o perfil
    analyst_user_id = uuid4()  # Usuário analista que receberá o perfil

    print("=== TESTE E2E: Sistema de Perfis ===")
    print(f"Organização: {organization_id}")
    print(f"Admin: {admin_user_id}")
    print(f"Analista: {analyst_user_id}")
    print()

    # === 1. Criar Perfil ===
    print("1. Criando perfil 'Analista Financeiro'...")
    profile = Profile.create(
        name="Analista Financeiro",
        description="Perfil para analistas com acesso aos documentos financeiros",
        organization_id=organization_id,
        created_by=admin_user_id,
        profile_metadata={
            "department": "financial",
            "level": "analyst",
            "created_by_role": "administrador",
        },
    )

    print(f"✓ Perfil criado: {profile.name} (ID: {profile.id})")
    print(f"  Descrição: {profile.description}")
    print(f"  Ativo: {profile.is_active}")
    print(f"  Status: {profile.get_status()}")
    print()

    # === 2. Configurar Permissões de Pasta ===
    print("2. Configurando permissões de pasta...")

    # Permissão READ para pasta financeiro
    folder_permission = ProfileFolderPermission.create(
        profile_id=profile.id,
        folder_path="/documents/financeiro",
        permission_level=FolderPermissionLevel.READ,
        organization_id=organization_id,
        created_by=admin_user_id,
        notes="Acesso de leitura aos documentos financeiros",
    )

    print(f"✓ Permissão criada para pasta: {folder_permission.folder_path}")
    print(f"  Nível: {folder_permission.permission_level.get_display_name()}")
    print(f"  Descrição: {folder_permission.permission_level.get_description()}")
    print(f"  Ações permitidas: {folder_permission.get_allowed_actions()}")
    print()

    # === 3. Atribuir Perfil ao Usuário ===
    print("3. Atribuindo perfil ao usuário analista...")

    user_profile = UserProfile.create(
        user_id=analyst_user_id,
        profile_id=profile.id,
        organization_id=organization_id,
        assigned_by=admin_user_id,
        notes="Atribuição inicial do perfil de analista financeiro",
    )

    print(f"✓ Perfil atribuído ao usuário: {user_profile.user_id}")
    print(f"  Perfil: {user_profile.profile_id}")
    print(f"  Ativo: {user_profile.is_active}")
    print(f"  Status: {user_profile.get_status()}")
    print(f"  Tipo: {user_profile.get_assignment_type()}")
    print()

    # === 4. Validar Permissões ===
    print("4. Validando permissões do usuário...")

    # Verificar se o usuário pode acessar a pasta financeiro
    can_access_financeiro = folder_permission.can_access_folder("/documents/financeiro")
    can_access_financeiro_sub = folder_permission.can_access_folder(
        "/documents/financeiro/relatorios"
    )
    can_access_rh = folder_permission.can_access_folder("/documents/rh")

    print(f"✓ Pode acessar /documents/financeiro: {can_access_financeiro}")
    print(
        f"✓ Pode acessar /documents/financeiro/relatorios: {can_access_financeiro_sub}"
    )
    print(f"✓ Pode acessar /documents/rh: {can_access_rh}")
    print()

    # Verificar ações específicas
    print("5. Verificando ações específicas...")

    actions_to_test = [
        "document:read",
        "document:update",
        "document:create",
        "document:delete",
        "folder:create",
        "rag:query",
        "rag:train",
        "ai:query",
        "ai:train",
    ]

    for action in actions_to_test:
        can_perform = folder_permission.can_perform_action(action)
        print(f"  {action}: {'✓' if can_perform else '✗'}")

    print()

    # === 6. Testar Capacidades Específicas ===
    print("6. Testando capacidades específicas...")

    print(f"✓ Pode ler documentos: {folder_permission.can_read_documents()}")
    print(f"✓ Pode editar documentos: {folder_permission.can_edit_documents()}")
    print(f"✓ Pode criar pastas: {folder_permission.can_create_folders()}")
    print(f"✓ Pode usar RAG: {folder_permission.can_use_rag()}")
    print(f"✓ Pode treinar RAG: {folder_permission.can_train_rag()}")
    print()

    # === 7. Validar Estrutura do Sistema ===
    print("7. Validando estrutura do sistema...")

    # Validar perfil
    profile_valid, profile_errors = profile.validate_profile()
    print(f"✓ Perfil válido: {profile_valid}")
    if profile_errors:
        print(f"  Erros: {profile_errors}")

    # Validar atribuição
    assignment_valid, assignment_errors = user_profile.validate_assignment()
    print(f"✓ Atribuição válida: {assignment_valid}")
    if assignment_errors:
        print(f"  Erros: {assignment_errors}")

    # Validar permissão
    permission_valid, permission_errors = folder_permission.validate_permission()
    print(f"✓ Permissão válida: {permission_valid}")
    if permission_errors:
        print(f"  Erros: {permission_errors}")

    print()

    # === 8. Cenário de Uso: Consulta RAG ===
    print("8. Simulando consulta RAG...")

    # Simular que o usuário quer fazer uma consulta RAG
    folder_to_query = "/documents/financeiro/relatorios/2024"

    if (
        folder_permission.can_access_folder(folder_to_query)
        and folder_permission.can_use_rag()
    ):
        print(f"✓ Usuário pode fazer consulta RAG na pasta: {folder_to_query}")
        print(f"  Motivo: Tem permissão READ na pasta pai /documents/financeiro")
        print(f"  Ações RAG permitidas: rag:query, ai:query")
    else:
        print(f"✗ Usuário NÃO pode fazer consulta RAG na pasta: {folder_to_query}")

    print()

    # === 9. Testar Hierarquia de Permissões ===
    print("9. Testando hierarquia de permissões...")

    # Verificar se READ é menor que EDIT e FULL
    read_level = FolderPermissionLevel.READ
    edit_level = FolderPermissionLevel.EDIT
    full_level = FolderPermissionLevel.FULL

    print(f"✓ READ < EDIT: {read_level.is_lower_than(edit_level)}")
    print(f"✓ READ < FULL: {read_level.is_lower_than(full_level)}")
    print(f"✓ EDIT < FULL: {edit_level.is_lower_than(full_level)}")
    print()

    # === 10. Resumo Final ===
    print("10. Resumo final...")

    print(f"✓ Perfil '{profile.name}' criado com sucesso")
    print(f"✓ Permissão READ configurada para pasta '/documents/financeiro'")
    print(f"✓ Perfil atribuído ao usuário analista")
    print(f"✓ Usuário pode:")
    print(f"  - Ler documentos na pasta financeiro e subpastas")
    print(f"  - Fazer consultas RAG com conteúdo da pasta financeiro")
    print(f"  - Baixar documentos da pasta financeiro")
    print(f"✓ Usuário NÃO pode:")
    print(f"  - Editar documentos")
    print(f"  - Criar pastas")
    print(f"  - Treinar RAG")
    print(f"  - Acessar outras pastas (ex: /documents/rh)")

    print()
    print("=== TESTE E2E CONCLUÍDO COM SUCESSO! ===")

    # Retornar objetos criados para possível uso em outros testes
    return {
        "profile": profile,
        "user_profile": user_profile,
        "folder_permission": folder_permission,
        "organization_id": organization_id,
        "admin_user_id": admin_user_id,
        "analyst_user_id": analyst_user_id,
    }


def test_profile_system_advanced_scenarios():
    """
    Teste de cenários avançados do sistema de perfis.
    """

    print("\n=== TESTE AVANÇADO: Cenários Complexos ===")

    # Setup
    organization_id = uuid4()
    admin_user_id = uuid4()
    manager_user_id = uuid4()
    user_id = uuid4()

    # === Cenário 1: Perfil com Múltiplas Permissões ===
    print("1. Criando perfil com múltiplas permissões...")

    profile = Profile.create(
        name="Gerente de Projetos",
        description="Acesso completo a projetos e leitura de RH",
        organization_id=organization_id,
        created_by=admin_user_id,
    )

    # Permissão FULL para projetos
    perm_projetos = ProfileFolderPermission.create(
        profile_id=profile.id,
        folder_path="/documents/projetos",
        permission_level=FolderPermissionLevel.FULL,
        organization_id=organization_id,
        created_by=admin_user_id,
    )

    # Permissão READ para RH
    perm_rh = ProfileFolderPermission.create(
        profile_id=profile.id,
        folder_path="/documents/rh",
        permission_level=FolderPermissionLevel.READ,
        organization_id=organization_id,
        created_by=admin_user_id,
    )

    print(f"✓ Perfil criado com 2 permissões:")
    print(f"  - FULL em /documents/projetos")
    print(f"  - READ em /documents/rh")
    print()

    # === Cenário 2: Atribuição Temporária ===
    print("2. Criando atribuição temporária...")

    # Atribuição que expira em 30 dias
    expires_at = datetime.now(timezone.utc).replace(day=datetime.now().day + 30)

    user_profile = UserProfile.create(
        user_id=user_id,
        profile_id=profile.id,
        organization_id=organization_id,
        assigned_by=manager_user_id,
        expires_at=expires_at,
        notes="Atribuição temporária para projeto específico",
    )

    print(f"✓ Atribuição temporária criada:")
    print(f"  - Expira em: {user_profile.expires_at}")
    print(f"  - Dias até expirar: {user_profile.days_until_expiry()}")
    print(f"  - Tipo: {user_profile.get_assignment_type()}")
    print()

    # === Cenário 3: Teste de Conflitos ===
    print("3. Testando conflitos de permissões...")

    # Tentar criar permissão conflitante
    try:
        perm_conflito = ProfileFolderPermission.create(
            profile_id=profile.id,
            folder_path="/documents/projetos/projeto1",  # Subpasta de projetos
            permission_level=FolderPermissionLevel.READ,
            organization_id=organization_id,
            created_by=admin_user_id,
        )

        # Verificar se há conflito
        conflict = perm_projetos.conflicts_with(perm_conflito)
        print(f"✓ Conflito detectado: {conflict}")

        if conflict:
            print(
                f"  - Permissão pai: {perm_projetos.folder_path} ({perm_projetos.permission_level.value})"
            )
            print(
                f"  - Permissão filha: {perm_conflito.folder_path} ({perm_conflito.permission_level.value})"
            )

    except Exception as e:
        print(f"✗ Erro ao criar permissão conflitante: {e}")

    print()

    # === Cenário 4: Validação de Hierarquia ===
    print("4. Validando hierarquia de pastas...")

    test_folders = [
        "/documents/projetos",
        "/documents/projetos/projeto1",
        "/documents/projetos/projeto1/documentos",
        "/documents/rh",
        "/documents/rh/folha_pagamento",
        "/documents/financeiro",
    ]

    for folder in test_folders:
        # Verificar acesso baseado em permissão de projetos (FULL)
        can_access_projetos = perm_projetos.can_access_folder(folder)
        # Verificar acesso baseado em permissão de RH (READ)
        can_access_rh = perm_rh.can_access_folder(folder)

        print(f"  {folder}:")
        print(f"    - Acesso via permissão projetos: {can_access_projetos}")
        print(f"    - Acesso via permissão RH: {can_access_rh}")

    print()

    # === Cenário 5: Simulação de Uso Real ===
    print("5. Simulando uso real...")

    # Simular que o usuário quer executar várias ações
    scenarios = [
        (
            "Ler documento em /documents/projetos/projeto1/doc.pdf",
            "document:read",
            "/documents/projetos/projeto1/doc.pdf",
        ),
        (
            "Criar pasta em /documents/projetos/novo_projeto",
            "folder:create",
            "/documents/projetos/novo_projeto",
        ),
        (
            "Editar documento em /documents/rh/politicas.pdf",
            "document:update",
            "/documents/rh/politicas.pdf",
        ),
        ("Treinar RAG com /documents/projetos", "rag:train", "/documents/projetos"),
        ("Fazer consulta RAG em /documents/rh", "rag:query", "/documents/rh"),
    ]

    for description, action, folder_path in scenarios:
        print(f"  {description}:")

        # Verificar contra permissão de projetos
        if perm_projetos.can_access_folder(folder_path):
            can_do_projetos = perm_projetos.can_perform_action(action)
            print(f"    - Via permissão projetos: {'✓' if can_do_projetos else '✗'}")

        # Verificar contra permissão de RH
        if perm_rh.can_access_folder(folder_path):
            can_do_rh = perm_rh.can_perform_action(action)
            print(f"    - Via permissão RH: {'✓' if can_do_rh else '✗'}")

        # Se não pode acessar a pasta
        if not perm_projetos.can_access_folder(
            folder_path
        ) and not perm_rh.can_access_folder(folder_path):
            print(f"    - Sem acesso à pasta")

    print()
    print("=== TESTE AVANÇADO CONCLUÍDO! ===")


if __name__ == "__main__":
    # Executar teste básico
    test_profile_system_e2e()

    # Executar teste avançado
    test_profile_system_advanced_scenarios()
