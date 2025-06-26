# FastAPI DDD Application

Uma aplicação FastAPI seguindo os princípios de Domain Driven Design com PostgreSQL.

## Estrutura do Projeto

```
src/
├── domain/                 # Camada de domínio
│   ├── entities/          # Entidades de negócio
│   ├── value_objects/     # Objetos de valor
│   └── repositories/      # Interfaces de repositório
├── application/           # Camada de aplicação
│   ├── dtos/             # Data Transfer Objects
│   ├── services/         # Serviços de aplicação
│   └── use_cases/        # Casos de uso
├── infrastructure/       # Camada de infraestrutura
│   ├── database/         # Configurações de banco
│   └── repositories/     # Implementações de repositório
└── presentation/         # Camada de apresentação
    └── api/              # Rotas da API
```

## Requisitos

- Python 3.11+
- PostgreSQL
- Poetry (recomendado) ou pip

## Configuração

### 🥇 Opção 1: Poetry (Recomendado)

```bash
# Setup completo com um comando
make setup

# Ou manualmente:
poetry install              # Instalar dependências
docker-compose up -d        # PostgreSQL
poetry run alembic upgrade head  # Migrações
make dev                    # Rodar aplicação
```

**Comandos Poetry disponíveis:**
```bash
make help           # Ver todos os comandos
make dev            # Desenvolvimento (auto-reload)
make start          # Produção
make migrate        # Aplicar migrações
make migration      # Criar migração
make test           # Executar testes
make format         # Formatar código
```

**Scripts Poetry diretos:**
```bash
poetry run dev        # Desenvolvimento
poetry run start      # Produção
poetry run migrate    # Aplicar migrações
poetry run migration  # Criar migração
poetry run test       # Executar testes
poetry run format     # Formatar código
poetry run lint       # Verificar código
poetry run check      # Verificar ambiente
```

### 🥈 Opção 2: Pip Tradicional

```bash
# 1. Subir PostgreSQL
docker-compose up -d

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar migrações
alembic upgrade head

# 4. Rodar aplicação
python main.py
```

### 🐳 Opção 3: Docker (Isolado)

```bash
# Construir e rodar tudo com Docker
make docker-build
make docker-full

# Ver logs
make docker-logs

# Parar
make docker-down
```

### 🧪 Teste Rápido (sem instalar)

```bash
python3.11 test_imports.py
# ou
python3 test_imports.py
```

## API Endpoints

- `GET /` - Página inicial
- `GET /health` - Health check
- `GET /docs` - Documentação Swagger
- `POST /api/v1/users` - Criar usuário
- `GET /api/v1/users` - Listar usuários
- `GET /api/v1/users/{id}` - Buscar usuário por ID
- `PUT /api/v1/users/{id}` - Atualizar usuário
- `DELETE /api/v1/users/{id}` - Deletar usuário
- `PATCH /api/v1/users/{id}/activate` - Ativar usuário
- `PATCH /api/v1/users/{id}/deactivate` - Desativar usuário

## Funcionalidades

- ✅ Domain Driven Design (DDD)
- ✅ Pydantic para validação e serialização
- ✅ Unit of Work pattern
- ✅ Repository pattern genérico
- ✅ PostgreSQL com SQLAlchemy
- ✅ Alembic para migrações
- ✅ Documentação automática com Swagger

## Desenvolvimento

### Com Poetry (Recomendado)
```bash
poetry shell                # Ativar ambiente virtual
make dev                    # Rodar com auto-reload
# ou
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Com Pip
```bash
uvicorn run:app --reload --host 0.0.0.0 --port 8000
```

### URLs da Aplicação
- **API**: http://localhost:8000
- **Documentação**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Comandos Úteis
```bash
make help           # Ver todos os comandos disponíveis
make format         # Formatar código (black + isort)
make lint           # Verificar qualidade do código
make test           # Executar testes
make clean          # Limpar arquivos temporários
```