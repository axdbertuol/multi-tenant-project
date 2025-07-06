# Default Configurations

Este diretório contém as configurações padrão do sistema em formato JSON, organizadas por domínio.

## Estrutura de Diretórios

```
defaults/
├── roles/                      # Configurações de roles e permissões
│   └── default_roles.json
├── applications/               # Configurações de aplicações
│   ├── application_types.json  # Tipos de aplicação e metadados
│   ├── plan_configurations.json # Configurações por plano
│   └── app_configs/            # Configurações específicas por app
│       ├── web_chat_app.json
│       ├── whatsapp_app.json
│       ├── document_storage.json
│       ├── management_app.json
│       └── api_access.json
└── subscription/               # Configurações de subscription
    └── trial_settings.json
```

## Configurações de Roles (`roles/default_roles.json`)

Define as roles padrão criadas para cada nova organização:

- **owner**: Acesso completo à organização
- **admin**: Acesso administrativo com algumas restrições
- **member**: Acesso padrão para membros da organização
- **viewer**: Acesso somente leitura

Cada role contém:
- `description`: Descrição da role
- `permissions`: Lista de permissões (formato `resource:action`)
- `is_system_role`: Se é uma role do sistema
- `can_be_deleted`: Se pode ser deletada

## Configurações de Aplicações

### Tipos de Aplicação (`applications/application_types.json`)

Define os tipos de aplicação disponíveis:
- `name`: Nome exibido da aplicação
- `description`: Descrição da aplicação
- `icon`: Ícone da aplicação
- `category`: Categoria da aplicação
- `default_features`: Features padrão habilitadas
- `required_permissions`: Permissões necessárias para usar

### Configurações por Plano (`applications/plan_configurations.json`)

Define quais aplicações e features são habilitadas por plano:
- **basic**: Aplicações básicas (web_chat, management, document_storage)
- **premium**: Adiciona API access e features avançadas
- **enterprise**: Adiciona WhatsApp e features enterprise

### Configurações Específicas (`applications/app_configs/`)

Cada tipo de aplicação tem sua configuração específica:

#### Web Chat App (`web_chat_app.json`)
- `widget_config`: Aparência do widget (posição, cores, tema)
- `chat_config`: Comportamento do chat (mensagens, notificações)
- `business_hours`: Horários de funcionamento
- `security_config`: Configurações de segurança
- `api_config`: Configurações de API e webhooks

#### WhatsApp App (`whatsapp_app.json`)
- `whatsapp_config`: Configuração da API do WhatsApp Business
- `template_config`: Templates de mensagem padrão
- `business_hours`: Horários de atendimento
- `auto_responder`: Configurações de resposta automática

#### Document Storage (`document_storage.json`)
- `storage_config`: Limites de armazenamento e tipos de arquivo
- `ai_config`: Configurações de IA (query, training, similarity)
- `access_config`: Configurações de acesso e compartilhamento
- `folder_structure`: Estrutura de pastas padrão

#### Management App (`management_app.json`)
- `dashboard_config`: Configuração do dashboard
- `analytics_config`: Configurações de analytics
- `notification_config`: Configurações de notificação

#### API Access (`api_access.json`)
- `api_config`: Configurações de API (rate limit, endpoints)
- `security_config`: Configurações de segurança
- `documentation_config`: Configurações de documentação

## Configurações de Trial (`subscription/trial_settings.json`)

Define as configurações para subscriptions trial:
- `trial_config`: Duração, ciclo de billing, metadata
- `trial_limits`: Limites específicos para trial
- `trial_features`: Features habilitadas/desabilitadas no trial

## Templates Dinâmicos

O sistema suporta templates dinâmicos nas configurações:

- `generated_uuid`: Substituído por um UUID único
- `{organization_id}`: Substituído pelo ID da organização

Exemplo:
```json
{
  "api_key": "generated_uuid",
  "docs_url": "/api/docs/org/{organization_id}"
}
```

## Carregamento das Configurações

As configurações são carregadas automaticamente pelo `ConfigurationLoaderService`:

```python
from shared.infrastructure.config import get_configuration_loader

loader = get_configuration_loader()

# Carregar configurações
roles = loader.load_default_roles()
app_types = loader.load_application_types()
plans = loader.load_plan_configurations()
trial_settings = loader.load_trial_settings()

# Carregar configuração específica de app
web_chat_config = loader.get_default_app_configuration('web_chat_app', org_id)
```

## Fallback e Cache

- **Fallback**: Se um arquivo JSON não for encontrado ou for inválido, o sistema usa valores hardcoded como fallback
- **Cache**: As configurações são carregadas uma vez e ficam em cache para performance
- **Reload**: Use `loader.reload_cache()` para recarregar as configurações

## Modificando Configurações

1. Edite os arquivos JSON neste diretório
2. As mudanças são aplicadas automaticamente na próxima inicialização
3. Para aplicar imediatamente em desenvolvimento, use `loader.reload_cache()`

## Validação

Todos os arquivos JSON são validados durante o carregamento. Se houver erro de sintaxe, o sistema usa valores de fallback e registra um log de erro.

## Ambientes

Diferentes ambientes podem ter configurações diferentes:
- Desenvolvimento: Use as configurações padrão
- Staging: Sobrescreva apenas os valores necessários
- Produção: Configure valores específicos de produção

Exemplo para ambientes:
```bash
# Usar configurações específicas de produção
export CONFIG_BASE_PATH="/etc/myapp/config"
```