# Documents Context
# Responsible for document access control, folder hierarchy, and area-based permissions
#  Preciso criar um sistema de permissões no bounded context dentro de @src/modules/iam que:
# - Existem Roles(Funções) de gerenciamento da aplicação
# - Cada role terá uma hierarquia maior
# - As roles globais serão: Administrador, Gerenciador, Especialista e Analista
# - Administrador:
#  - Terá permissão para usar tudo
# - Gerenciador:
#  - Terá:
#     - Gerenciamento de usuários: permissão completa
#     - Gerenciamento de documentos e pastas: permissão completa (ler editar e criar pastas)
#     - Uso do RAG: permissão completa
#     - Configurações: permissão parcial
# - Especialista:
#  - Terá:
#     - Gerenciamento de usuários: apenas ler
#     - Gerenciamento de documentos e pastas: ler e editar (não pode criar pastas)
#     - Uso do RAG: permissão concedida apenas pelo Perfil
#     - Configurações: não tem permissão nenhuma
# - Analista:
#   - Terá:
#     - Gerenciamento de usuários: apenas ler
#     - Gerenciamento de documentos e pastas: ler apenas
#     - Uso do RAG: permissão concedida apenas pelo Perfil
#     - Configurações: não tem permissão nenhuma

# Com base nisso:
# - crie os modelos sqlalchemy em @src/modules/iam/infrastructuredatabase/models.py


# Um perfil também será criado para cada usuário.
# Um usuário pode ter mais de um perfil e um perfil pode estar associado a muitos usuários.
# No caso, o administrador e gerenciador vão poder criar.
# Ao criar, poderá escolher uma pasta (a qual tem permissão completa) e setar permissões: ler, editar ou completa para determinado Perfil
#     - Isso significa que:
#         - Se for permissão de ler, então só vai poder ler o que estiver na pasta e também ler o resultado do RAG de acordo com o que estiver na mesma pasta.
#         - Se for editar, poderá ler e editar documentos dentro da pasta e também RAG.
#         - Se for completa, poderá criar pastas, ler, editar e RAG

# Com base nisso:
# - confira em @src/iam e @src/documents se será capaz de criar esses Perfis com o atual codebase.
# - se sim, implemente um caso  de teste e2e simples
# - se não, implemente o que falta para poder criar Perfis.

