#!/bin/bash

echo "🚀 Configurando projeto FastAPI DDD com Poetry..."

# Verificar se Poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry não encontrado. Instalando Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo "✅ Poetry instalado!"
    echo "📝 Adicione o Poetry ao PATH: export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo "🔄 Execute: source ~/.bashrc (ou ~/.zshrc)"
fi

# Configurar Poetry para criar venv no projeto
echo "⚙️  Configurando Poetry..."
poetry config virtualenvs.in-project true

# Instalar dependências
echo "📦 Instalando dependências..."
poetry install

# Verificar se PostgreSQL está rodando
if command -v docker &> /dev/null; then
    echo "🐳 Iniciando PostgreSQL com Docker..."
    docker-compose up -d
else
    echo "⚠️  Docker não encontrado. Configure PostgreSQL manualmente."
fi

# Executar migrações
echo "🗄️  Executando migrações..."
poetry run alembic upgrade head

echo ""
echo "✅ Setup concluído!"
echo ""
echo "🚀 Comandos disponíveis:"
echo "  poetry run dev        # Rodar em modo desenvolvimento"
echo "  poetry run start      # Rodar em produção"
echo "  poetry run migrate    # Aplicar migrações"
echo "  poetry run migration  # Criar nova migração"
echo ""
echo "📖 Ou usando Poetry shell:"
echo "  poetry shell          # Ativar ambiente virtual"
echo "  uvicorn main:app --reload  # Rodar aplicação"
echo ""
echo "🌐 Aplicação estará em: http://localhost:8000"
echo "📚 Documentação em: http://localhost:8000/docs"