# Arquitetura DDD - Sistema Multi-Tenant

## Visão Geral

Este documento descreve a arquitetura Domain-Driven Design (DDD) implementada no sistema multi-tenant, organizada em bounded contexts bem definidos.

## Bounded Contexts

### 1. User Context (`src/user/`)

**Responsabilidade**: Gestão de usuários, autenticação e sessões.

**Entidades Principais**:
- `User`: Entidade agregada principal para dados do usuário
- `UserSession`: Sessões de usuário com controle de expiração

**Value Objects**:
- `Email`: Validação e formatação de email
- `Password`: Hash e verificação de senhas com bcrypt

**Repositórios**:
- `UserRepository`: Interface para persistência de usuários
- `UserSessionRepository`: Interface para gestão de sessões

**Serviços de Domínio**:
- `UserDomainService`: Regras de negócio específicas de usuário
- `AuthenticationService`: Lógica de autenticação e sessões

**Regras de Negócio**:
- Validação de força de senha (maiúscula, minúscula, número)
- Email único por usuário
- Controle de sessões ativas
- Validação de ativação/desativação de usuários

### 2. Organization Context (`src/organization/`)

**Responsabilidade**: Gestão de organizações e papéis de usuários.

**Entidades Principais**:
- `Organization`: Entidade agregada para organizações
- `UserOrganizationRole`: Relacionamento usuário-organização com papéis

**Value Objects**:
- `OrganizationName`: Validação de nomes de organização
- `OrganizationSettings`: Configurações e limites organizacionais

**Repositórios**:
- `OrganizationRepository`: Interface para persistência de organizações
- `UserOrganizationRoleRepository`: Interface para papéis de usuário

**Serviços de Domínio**:
- `OrganizationDomainService`: Regras de negócio organizacionais
- `MembershipService`: Gestão de membros e transferência de propriedade

**Regras de Negócio**:
- Limite máximo de usuários por organização
- Transferência de propriedade entre usuários
- Validação de nomes únicos de organização
- Controle de papéis (Owner, Admin, Member, Viewer)

### 3. Authorization Context (`src/authorization/`)

**Responsabilidade**: Controle de acesso baseado em RBAC + ABAC.

**Entidades Principais**:
- `Role`: Papéis do sistema
- `Permission`: Permissões granulares
- `Resource`: Recursos protegidos com atributos
- `Policy`: Políticas ABAC para controle de acesso
- `AuthorizationContext`: Contexto para decisões de autorização

**Value Objects**:
- `RoleName`: Validação de nomes de papéis
- `PermissionName`: Validação de nomes de permissões
- `AuthorizationDecision`: Resultado de decisões de autorização

**Repositórios**:
- `RoleRepository`: Interface para persistência de papéis
- `PermissionRepository`: Interface para persistência de permissões
- `ResourceRepository`: Interface para recursos protegidos
- `PolicyRepository`: Interface para políticas ABAC
- `RolePermissionRepository`: Interface para relacionamentos

**Serviços de Domínio**:
- `AuthorizationService`: Serviço principal de autorização
- `RBACService`: Implementação de Role-Based Access Control
- `ABACService`: Implementação de Attribute-Based Access Control
- `PolicyEvaluationService`: Avaliação de políticas ABAC

**Regras de Negócio**:
- Combinação de RBAC e ABAC (deny-overrides)
- Avaliação de políticas por prioridade
- Validação de contexto de autorização
- Permissões hierárquicas e wildcards

### 4. Plans Context (`src/plans/`)

**Responsabilidade**: Gestão de planos, recursos e uso de funcionalidades.

**Entidades Principais**:
- `Plan`: Planos disponíveis com recursos e limites
- `PlanFeature`: Funcionalidades configuráveis dos planos
- `OrganizationPlan`: Assinatura de organizações a planos
- `FeatureUsage`: Controle de uso de recursos por período

**Value Objects**:
- `PlanName`: Validação de nomes de planos
- `Pricing`: Modelo de preços flexível (fixo, por usuário, etc.)
- `ChatWhatsAppConfiguration`: Configuração do WhatsApp
- `ChatIframeConfiguration`: Configuração do chat iframe

**Repositórios**:
- `PlanRepository`: Interface para persistência de planos
- `OrganizationPlanRepository`: Interface para assinaturas
- `FeatureUsageRepository`: Interface para controle de uso
- `PlanFeatureRepository`: Interface para funcionalidades

**Serviços de Domínio**:
- `PlanManagementService`: Gestão de planos e comparações
- `SubscriptionService`: Gestão de assinaturas organizacionais
- `UsageTrackingService`: Controle e analytics de uso
- `FeatureAccessService`: Acesso a recursos específicos

**Recursos Principais**:
- `chat_whatsapp`: Integração com WhatsApp Business
- `chat_iframe`: Widget de chat embarcável

**Regras de Negócio**:
- Limites de uso por período (mensal, anual)
- Configurações personalizadas por organização
- Controle de trial e renovações automáticas
- Hierarquia de planos (Free → Basic → Premium → Enterprise)

## Dependências Entre Contextos

### Dependências Diretas

```
Authorization → User (consulta informações do usuário)
Authorization → Organization (consulta papéis organizacionais)
Plans → Organization (assinaturas por organização)
Organization → User (membership de usuários)
```

### Dependências Através de IDs

Os contextos se comunicam principalmente através de UUIDs, mantendo baixo acoplamento:

- `Authorization` usa `user_id` e `organization_id` 
- `Plans` usa `organization_id`
- `Organization` usa `user_id` para propriedade e membros

### Eventos de Domínio (Futuro)

Para reduzir acoplamento, considerar implementar eventos:

```
UserCreated → Organization (criar organização padrão)
OrganizationCreated → Plans (assinatura do plano free)
PlanChanged → Authorization (atualizar permissões)
UserRoleChanged → Authorization (invalidar cache)
```

## Estrutura de Diretórios

```
src/
├── user/
│   └── domain/
│       ├── entities/
│       ├── value_objects/
│       ├── repositories/
│       └── services/
├── organization/
│   └── domain/
│       ├── entities/
│       ├── value_objects/
│       ├── repositories/
│       └── services/
├── authorization/
│   └── domain/
│       ├── entities/
│       ├── value_objects/
│       ├── repositories/
│       └── services/
└── plans/
    └── domain/
        ├── entities/
        ├── value_objects/
        ├── repositories/
        └── services/
```

## Princípios Aplicados

### 1. Aggregate Design
- Cada contexto tem agregados bem definidos
- Consistência transacional dentro do agregado
- Referências entre agregados via IDs

### 2. Ubiquitous Language
- Terminologia consistente em cada contexto
- Nomes expressivos para entidades e serviços
- Separação clara de responsabilidades

### 3. Domain Services
- Lógica de domínio que não pertence a uma entidade específica
- Coordenação entre entidades do mesmo contexto
- Regras de negócio complexas encapsuladas

### 4. Value Objects
- Validação e formatação de dados
- Imutabilidade garantida
- Comportamentos específicos encapsulados

### 5. Repository Pattern
- Abstração da persistência
- Interfaces no domínio, implementação na infraestrutura
- Facilita testes e mudanças de tecnologia

## Casos de Uso Principais

### 1. Autenticação de Usuário
```
User Context: Validar credenciais
Authorization Context: Carregar permissões
Plans Context: Verificar recursos disponíveis
```

### 2. Criação de Organização
```
Organization Context: Criar organização
Plans Context: Assinar plano free
Authorization Context: Criar recursos protegidos
```

### 3. Uso de Funcionalidade
```
Plans Context: Verificar acesso e limites
Authorization Context: Validar permissões
Plans Context: Registrar uso
```

### 4. Upgrade de Plano
```
Plans Context: Validar upgrade
Plans Context: Migrar assinatura
Authorization Context: Atualizar permissões
```

## Benefícios da Arquitetura

### 1. Manutenibilidade
- Contextos independentes e focados
- Baixo acoplamento entre domínios
- Facilita mudanças e evoluções

### 2. Testabilidade
- Unidades bem definidas para teste
- Interfaces mocáveis
- Isolamento de responsabilidades

### 3. Escalabilidade
- Contextos podem evoluir independentemente
- Possibilidade de microsserviços futuros
- Deploy e desenvolvimento em paralelo

### 4. Clareza de Negócio
- Linguagem ubíqua por contexto
- Regras de negócio explícitas
- Facilita comunicação com stakeholders

## Próximos Passos

1. **Implementação da Camada de Aplicação**: Use cases e DTOs
2. **Implementação da Infraestrutura**: Repositórios SQLAlchemy
3. **Implementação da Apresentação**: APIs REST
4. **Eventos de Domínio**: Para comunicação assíncrona
5. **Testes de Integração**: Entre contextos
6. **Monitoramento**: Observabilidade e métricas