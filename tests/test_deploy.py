"""Arquivos que o Streamlit Community Cloud lê na publicação do dashboard."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "src" / "smart_hospitals" / "dashboard"

# Arquivos de dependência reconhecidos pelo Cloud, em ordem de prioridade. Ele procura primeiro na
# pasta do app.py e depois na raiz, e usa só o primeiro que encontrar.
ARQUIVOS_DEPENDENCIAS = [
    "uv.lock",
    "Pipfile",
    "environment.yml",
    "requirements.txt",
    "pyproject.toml",
]


def test_raiz_tem_uv_lock() -> None:
    assert (ROOT / "uv.lock").is_file()


@pytest.mark.parametrize("nome", ARQUIVOS_DEPENDENCIAS)
def test_pasta_do_app_nao_tem_arquivo_de_dependencias(nome: str) -> None:
    # Um arquivo aqui teria prioridade sobre o uv.lock da raiz e o pacote smart_hospitals não
    # seria instalado.
    assert not (APP_DIR / nome).exists()


def test_raiz_nao_tem_requirements_txt() -> None:
    # Seria ignorado (o uv.lock vem antes) e ficaria dessincronizado do pyproject.toml.
    assert not (ROOT / "requirements.txt").exists()
