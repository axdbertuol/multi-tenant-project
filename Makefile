.PHONY: help install dev start migrate migration test clean format lint check docker-up docker-down docker-build docker-full docker-logs setup

help:
	@echo "🚀 FastAPI DDD Project (Python 3.11) - Comandos disponíveis:"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install     - Instalar dependências com Poetry"
	@echo "  make setup       - Setup completo (deps + db + migrate)"
	@echo ""
	@echo "🏃 Executar (Local):"
	@echo "  make dev         - Rodar em modo desenvolvimento"
	@echo "  make start       - Rodar em modo produção"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-up   - Subir PostgreSQL"
	@echo "  make docker-full - Subir aplicação completa"
	@echo "  make docker-build- Construir imagem"
	@echo "  make docker-logs - Ver logs da aplicação"
	@echo "  make docker-down - Parar todos os services"
	@echo ""
	@echo "🗄️  Banco de dados:"
	@echo "  make migrate     - Aplicar migrações"
	@echo "  make migration   - Criar nova migração"
	@echo ""
	@echo "🧪 Qualidade:"
	@echo "  make test        - Executar testes"
	@echo "  make format      - Formatar código"
	@echo "  make lint        - Verificar código"
	@echo "  make check       - Verificar ambiente"
	@echo ""
	@echo "🧹 Limpeza:"
	@echo "  make clean       - Limpar arquivos temporários"

install:
	@echo "📦 Instalando dependências..."
	poetry install

dev:
	@echo "🚀 Iniciando servidor de desenvolvimento..."
	poetry run dev

start:
	@echo "🚀 Iniciando servidor..."
	poetry run start

migrate:
	@echo "🗄️  Aplicando migrações..."
	poetry run migrate

migration:
	@echo "🗄️  Criando nova migração..."
	poetry run migration

test:
	@echo "🧪 Executando testes..."
	poetry run test

format:
	@echo "🎨 Formatando código..."
	poetry run format

lint:
	@echo "🔍 Verificando código..."
	poetry run lint

check:
	@echo "🔍 Verificando ambiente..."
	poetry run check

docker-up:
	@echo "🐳 Subindo PostgreSQL..."
	docker-compose up -d postgres

docker-down:
	@echo "🐳 Parando services..."
	docker-compose down

docker-build:
	@echo "🏗️  Construindo imagem Docker..."
	docker-compose build

docker-full:
	@echo "🐳 Subindo aplicação completa..."
	docker-compose up -d

docker-logs:
	@echo "📄 Logs da aplicação..."
	docker-compose logs -f app

clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

setup: install docker-up migrate
	@echo "✅ Setup completo!"
	@echo "🚀 Execute: make dev"