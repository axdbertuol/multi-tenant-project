"""
Teste de exemplo para verificar se pytest funciona
"""

import pytest


def test_example():
    """Teste básico de exemplo"""
    assert True


def test_python_version():
    """Verificar se estamos usando Python 3.11+"""
    import sys

    assert sys.version_info >= (3, 11)


@pytest.mark.unit
def test_basic_math():
    """Teste unitário básico"""
    assert 2 + 2 == 4
    assert 10 / 2 == 5


@pytest.mark.unit
def test_imports():
    """Verificar se imports básicos funcionam"""
    try:
        import sys
        import os
        import pathlib

        assert True
    except ImportError:
        pytest.fail("Imports básicos falharam")
