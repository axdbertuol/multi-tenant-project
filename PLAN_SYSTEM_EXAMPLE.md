# Sistema de Planos - Exemplo de Uso

## Visão Geral

O sistema de planos foi implementado com as entidades solicitadas e integração completa com o sistema de autorização. Aqui estão exemplos práticos de uso.

## Estrutura Implementada

### 1. Entidades de Domínio

#### Plan
- **Campos**: id, name, plan_type, resources, is_active
- **Tipos**: BASIC, PREMIUM, ENTERPRISE
- **Recursos**: chat_whatsapp, chat_iframe com configurações dinâmicas

#### PlanResource
- **Tipos**: CHAT_WHATSAPP, CHAT_IFRAME, CUSTOM
- **Configuração**: api_keys, limits, enabled_features

#### PlanConfiguration
- **Campos**: api_keys, limits, enabled_features, custom_settings

## Exemplo de Uso Completo

### 1. Criar Plano Premium

```python
from src.plans.domain import (
    Plan, PlanType, PlanResource, PlanResourceType, 
    PlanConfiguration, PlanAuthorizationService
)
from decimal import Decimal

# Criar plano Premium
plan = Plan.create(
    name="Plano Premium",
    description="Plano premium com recursos avançados",
    plan_type=PlanType.PREMIUM,
    pricing=Pricing.create_fixed(Decimal("99.00"), Currency.USD),
    max_users=100,
    max_organizations=5
)

# Configuração automática de recursos baseada no tipo
print(plan.resources)
# Output:
{
    "chat_iframe": {
        "enabled": True,
        "api_keys": {"iframe_api_key": "premium-iframe-key"},
        "limits": {"concurrent_sessions": 100, "domains_allowed": 10},
        "enabled_features": ["basic_chat", "emoji_support", "custom_css", "file_upload"]
    },
    "chat_whatsapp": {
        "enabled": True,
        "api_keys": {"whatsapp_api_key": "premium-whatsapp-key"},
        "limits": {"messages_per_day": 5000},
        "enabled_features": ["auto_reply", "business_hours", "template_messages", "media_messages"]
    }
}
```

### 2. Criar Recursos Específicos

```python
# Criar recurso WhatsApp personalizado
whatsapp_resource = PlanResource.create_whatsapp_resource(
    plan_id=plan.id,
    api_key="premium-whatsapp-123",
    messages_per_day=5000,
    webhook_url="https://api.company.com/whatsapp/webhook",
    auto_reply=True
)

# Criar recurso iframe personalizado
iframe_resource = PlanResource.create_iframe_resource(
    plan_id=plan.id,
    api_key="premium-iframe-456",
    concurrent_sessions=100,
    custom_css=True,
    custom_branding=True
)

print(iframe_resource.configuration)
# Output:
{
    "api_keys": {"iframe_api_key": "premium-iframe-456"},
    "limits": {"concurrent_sessions": 100, "domains_allowed": 10},
    "enabled_features": [
        "basic_chat", "file_upload", "emoji_support", 
        "custom_css", "custom_branding", "logo_upload"
    ]
}
```

### 3. Configuração Centralizada

```python
# Criar configuração do plano
config = PlanConfiguration.create_premium_configuration(plan.id)

# Atualizar API keys
config = config.update_api_key("whatsapp_api_key", "premium-whatsapp-123")
config = config.update_api_key("iframe_api_key", "premium-iframe-456")

# Atualizar limites
config = config.update_limit("monthly_messages", 100000)
config = config.update_limit("concurrent_sessions", 200)

# Adicionar feature personalizada
config = config.add_feature("advanced_analytics")

print(config.get_configuration_summary())
# Output:
{
    "api_keys_count": 2,
    "api_key_names": ["whatsapp_api_key", "iframe_api_key"],
    "limits": {
        "monthly_messages": 100000,
        "monthly_api_calls": 500000,
        "storage_mb": 10000,
        "concurrent_sessions": 200,
        "webhook_endpoints": 10
    },
    "enabled_features": [
        "chat_iframe", "chat_whatsapp", "custom_branding",
        "webhook_support", "advanced_analytics", "custom_css",
        "priority_support", "advanced_analytics"
    ]
}
```

### 4. Integração com Autorização

```python
# Verificar acesso de organização a recursos
auth_service = PlanAuthorizationService(
    plan_repository, resource_repository, 
    configuration_repository, org_plan_repository
)

# Validar acesso ao WhatsApp
has_access, message, config =  auth_service.validate_organization_resource_access(
    organization_id=organization_uuid,
    resource_type="chat_whatsapp"
)

if has_access:
    # Verificar API key
    is_valid, msg, api_key =  auth_service.validate_api_key_requirements(
        organization_id=organization_uuid,
        resource_type="chat_whatsapp"
    )
    
    if is_valid:
        print(f"API Key válida: {api_key}")
        
        # Verificar limites de uso
        can_use, limit_msg, remaining =  auth_service.validate_resource_usage_limits(
            organization_id=organization_uuid,
            resource_type="chat_whatsapp",
            usage_type="messages_per_day",
            requested_amount=50
        )
        
        if can_use:
            print(f"Pode usar recurso. Limite restante: {remaining}")
```

### 5. Exemplo de JSON Completo

```json
{
  "plan": {
    "name": "Plano Premium",
    "plan_type": "premium",
    "is_active": true,
    "resources": {
      "chat_whatsapp": {
        "enabled": true,
        "api_keys": {"whatsapp_api_key": "premium-whatsapp-123"},
        "limits": {"messages_per_day": 5000},
        "enabled_features": ["auto_reply", "business_hours", "template_messages"]
      },
      "chat_iframe": {
        "enabled": true,
        "api_keys": {"iframe_api_key": "premium-iframe-456"},
        "limits": {"concurrent_sessions": 100, "domains_allowed": 10},
        "enabled_features": ["custom_css", "file_upload", "custom_branding"]
      }
    }
  },
  "resources": [
    {
      "resource_type": "chat_whatsapp",
      "configuration": {
        "api_keys": {"whatsapp_api_key": "premium-whatsapp-123"},
        "limits": {"messages_per_day": 5000},
        "features": {
          "webhook_url": "https://api.company.com/webhook",
          "auto_reply": true,
          "business_hours": true,
          "template_messages": true
        }
      },
      "is_active": true
    },
    {
      "resource_type": "chat_iframe",
      "configuration": {
        "api_keys": {"iframe_api_key": "premium-iframe-456"},
        "limits": {"concurrent_sessions": 100, "domains_allowed": 10},
        "enabled_features": ["custom_css", "file_upload", "custom_branding"]
      },
      "is_active": true
    }
  ],
  "configuration": {
    "api_keys": {
      "whatsapp_api_key": "premium-whatsapp-123",
      "iframe_api_key": "premium-iframe-456"
    },
    "limits": {
      "monthly_messages": 100000,
      "monthly_api_calls": 500000,
      "storage_mb": 10000,
      "concurrent_sessions": 100,
      "webhook_endpoints": 10
    },
    "enabled_features": [
      "chat_iframe",
      "chat_whatsapp",
      "custom_branding",
      "webhook_support",
      "advanced_analytics",
      "custom_css",
      "priority_support"
    ]
  }
}
```

## Integração com Autorização

### 1. Verificação de Acesso

```python
# Antes de conceder permissões, verificar se organização tem o recurso
 def check_resource_permission(user_id: UUID, organization_id: UUID, resource: str):
    # 1. Verificar se usuário pertence à organização (Organization Context)
    membership_service = MembershipService(...)
    has_membership =  membership_service.can_user_perform_action(
        user_id, organization_id, "use_features"
    )
    
    if not has_membership:
        return False, "User not authorized in organization"
    
    # 2. Verificar se organização tem acesso ao recurso (Plans Context)
    plan_auth_service = PlanAuthorizationService(...)
    has_resource, message, config =  plan_auth_service.validate_organization_resource_access(
        organization_id, resource
    )
    
    if not has_resource:
        return False, f"Organization plan does not include {resource}: {message}"
    
    # 3. Verificar API keys obrigatórias
    has_api_key, key_message, api_key =  plan_auth_service.validate_api_key_requirements(
        organization_id, resource
    )
    
    if not has_api_key:
        return False, f"Required API key missing: {key_message}"
    
    return True, "Access granted"
```

### 2. Validação de Configurações

```python
# Validar se todas as configurações obrigatórias estão presentes
 def validate_plan_setup(plan_id: UUID):
    plan =  plan_repository.get_by_id(plan_id)
    
    validation_errors = []
    
    for resource_type in plan.resources.keys():
        is_valid, errors = plan.validate_resource_requirements(resource_type)
        if not is_valid:
            validation_errors.extend([f"{resource_type}: {error}" for error in errors])
    
    return len(validation_errors) == 0, validation_errors
```

## Repositórios Implementados

### PlanRepository
- `save()`, `get_by_id()`, `assign_to_organization()`
- `validate_plan_resources()`, `get_plans_with_resource()`

### PlanResourceRepository
- `save()`, `get_by_plan_and_type()`, `update_configuration()`
- `validate_api_key_uniqueness()`, `get_resources_with_api_key()`

### PlanConfigurationRepository
- `save()`, `get_by_plan_id()`, `update_api_keys()`
- `update_limits()`, `update_enabled_features()`

## Benefícios da Implementação

1. **Configurações Dinâmicas**: API keys e limites configuráveis por plano
2. **Validação Integrada**: Verificação automática de requisitos antes do acesso
3. **Flexibilidade**: Recursos podem ser ativados/desativados independentemente
4. **Segurança**: API keys obrigatórias para recursos específicos
5. **Escalabilidade**: Novos tipos de recursos facilmente adicionáveis

O sistema está pronto para uso e totalmente integrado com o sistema de autorização existente!

The **Resource model** in the provided code is structured to represent both **static and dynamic metadata** about resources in a system, with a focus on **flexibility**, **access control**, and **integration with authorization policies**. Below is a breakdown of its key components and structure:

---

### 1. **Core Fields**
#### **Static Metadata**
These fields define fixed, structural properties of the resource:
- **`resource_type`** (`str`):  
  A categorical identifier (e.g., `"user"`, `"organization"`, `"chat"`, `"plan"`). Used for grouping and policy scoping .
- **`resource_id`** (`UUID`):  
  A unique identifier for the specific instance of the resource (e.g., a user’s UUID).
- **`owner_id`** (`UUID`):  
  Links the resource to its owner (e.g., a user who created or manages the resource).
- **`organization_id`** (`UUID`, optional):  
  Associates the resource with an organization for multi-tenancy support .
- **`created_at`** (`datetime`):  
  Timestamp of resource creation.
- **`updated_at`** (`datetime`, optional):  
  Timestamp of the last modification.
- **`is_active`** (`bool`, default `True`):  
  Indicates whether the resource is active or archived.

#### **Dynamic Metadata (`attributes`)**  
- **`attributes`** (`Dict[str, Any]`):  
  A **JSON column** storing **flexible, key-value metadata** (e.g., `{"classification": "confidential", "owner_department": "engineering"}`).  
  - **Purpose**: Enables **Attribute-Based Access Control (ABAC)** by allowing policies to reference dynamic attributes (e.g., `"resource.classification == 'public'"`) .  
  - **Example**: A dataset resource might have attributes like `{"sensitivity": "high", "project_code": "PROJ-123"}` to enforce access rules based on data sensitivity or project ownership .

---

### 2. **Methods for Managing Attributes**
The model includes methods to manipulate dynamic attributes:
- **`update_attributes(attributes: Dict[str, Any]) -> Resource`**  
  Merges new attributes into the existing dictionary.
- **`set_attribute(key: str, value: Any) -> Resource`**  
  Sets a single attribute key-value pair.
- **`remove_attribute(key: str) -> Resource`**  
  Removes an attribute by key.
- **`get_attribute(key: str, default: Any = None) -> Any`**  
  Retrieves an attribute value or returns a default if missing.
- **`has_attribute(key: str) -> bool`**  
  Checks if an attribute exists .

These methods ensure programmatic updates to the `attributes` dictionary while maintaining immutability via `model_copy` (Pydantic’s frozen model pattern).

---

### 3. **Integration with Authorization**
The `attributes` field plays a critical role in **policy evaluation**:
- Policies reference resource attributes in conditions (via `PolicyCondition`). For example:
  ```python
  PolicyCondition(attribute="classification", operator="eq", value="public")
  ```
  This allows rules like *"Allow access if the resource’s classification is public"* .
- During authorization, resource attributes are merged into the `AuthorizationContext`, making them accessible to policy evaluators .

---

### 4. **Database Mapping**
The `ResourceModel` class maps to the `authorization_resources` table in the database:
- **Fields**:  
  - `resource_type`: Indexed for fast lookups by type.  
  - `resource_id`: Indexed to ensure uniqueness per resource type.  
  - `attributes`: Stored as a JSON column for dynamic metadata.  
- **Constraints**:  
  - A composite unique constraint ensures no duplicate `(resource_type, resource_id)` pairs.  
  - Indexes optimize queries for common operations like filtering by `owner_id` or `organization_id` .

---

### 5. **Use Cases and Flexibility**
The model supports scenarios requiring **dynamic access control**:
- **Example 1**:  
  A `dataset` resource with attributes like `{"owner_department": "finance", "access_level": "read-only"}` can enforce policies like *"Users in the finance department can read this dataset"*.
- **Example 2**:  
  A `chat` resource might track attributes like `{"participants": ["user1", "user2"]}` to restrict access to authorized participants only .

---

### 6. **Comparison to General Resource Models**
From the web_search content:
- The model aligns with **resource management principles** (e.g., defining structure and metadata , but extends it with **ABAC-specific features** (e.g., dynamic attributes for policy evaluation .  
- Unlike rigid models (e.g., SAP’s resource model for bundling static properties , this design emphasizes **flexibility** via JSON storage and programmatic updates.

---

### Summary
The Resource model combines **static identifiers** (e.g., `resource_type`, `owner_id`) with **dynamic attributes** to enable fine-grained, context-aware access control. Its structure supports:
1. **Scalable resource management** via UUIDs and multi-tenancy.
2. **Policy-driven authorization** through ABAC-compatible attributes.
3. **Extensibility** for domain-specific metadata without schema changes.

This design is ideal for systems requiring adaptive access controls, such as SaaS platforms or data governance frameworks .