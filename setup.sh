#!/bin/bash

echo "🚀 Configurando a aplicação FastAPI DDD..."

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -e .

# Criar banco de dados (se não existir)
echo "🗄️  Configurando banco de dados..."
echo "Certifique-se de que o PostgreSQL está rodando e o banco 'ddd_app' existe"

# Executar migrações
echo "🔄 Executando migrações..."
alembic upgrade head

echo "✅ Configuração concluída!"
echo ""
echo "Para rodar a aplicação:"
echo "  python main.py"
echo "  ou"
echo "  uvicorn run:app --reload"
echo ""
echo "A aplicação estará disponível em: http://localhost:8000"
echo "Documentação em: http://localhost:8000/docs"