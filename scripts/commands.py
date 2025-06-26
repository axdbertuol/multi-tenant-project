#!/usr/bin/env python3.11
"""
Scripts para usar com Poetry
"""

import subprocess
import sys
import os
from pathlib import Path


def dev():
    """Rodar aplicação em modo desenvolvimento"""
    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    cmd = ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]
    subprocess.run(cmd, env=env)


def start():
    """Rodar aplicação em modo produção"""
    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    cmd = ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
    subprocess.run(cmd, env=env)


def migrate():
    """Aplicar migrações do banco de dados"""
    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    cmd = ["alembic", "upgrade", "head"]
    subprocess.run(cmd, env=env)


def migration():
    """Criar nova migração"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--message", help="Mensagem da migração")
    args, unknown = parser.parse_known_args()

    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    cmd = ["alembic", "revision", "--autogenerate"]
    if args.message:
        cmd.extend(["-m", args.message])

    subprocess.run(cmd, env=env)


def test():
    """Executar testes"""
    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    cmd = ["pytest"]
    subprocess.run(cmd, env=env)


def format_code():
    """Formatar código com black e isort"""
    print("🎨 Formatando código...")
    subprocess.run(["black", "src/"])
    subprocess.run(["isort", "src/"])
    print("✅ Código formatado!")


def lint():
    """Verificar qualidade do código"""
    print("🔍 Verificando código...")

    # Definir PYTHONPATH para incluir src/
    env = os.environ.copy()
    src_path = Path(__file__).parent.parent / "src"
    env["PYTHONPATH"] = str(src_path) + ":" + env.get("PYTHONPATH", "")

    result1 = subprocess.run(["flake8", "src/"], env=env)
    result2 = subprocess.run(["mypy", "src/"], env=env)

    if result1.returncode == 0 and result2.returncode == 0:
        print("✅ Código está OK!")
    else:
        print("❌ Problemas encontrados no código")
        sys.exit(1)


def check_env():
    """Verificar ambiente e configurações"""
    print("🔍 Verificando ambiente...")

    # Verificar Python
    print(f"✅ Python {sys.version}")

    # Verificar .env
    if Path(".env").exists():
        print("✅ Arquivo .env encontrado")
    else:
        print("⚠️  Arquivo .env não encontrado")

    # Verificar estrutura src
    if Path("src").exists():
        print("✅ Diretório src/ encontrado")
    else:
        print("❌ Diretório src/ não encontrado")

    print("🎉 Verificação concluída!")


if __name__ == "__main__":
    # Para executar diretamente: python scripts/commands.py dev
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command in globals():
            globals()[command]()
        else:
            print(f"Comando '{command}' não encontrado")
            print(
                "Comandos disponíveis: dev, start, migrate, migration, test, format_code, lint, check_env"
            )
    else:
        print("Uso: python scripts/commands.py <comando>")
        print(
            "Comandos: dev, start, migrate, migration, test, format_code, lint, check_env"
        )
