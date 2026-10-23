"""Integração: o notebook de análise executa do início ao fim com o snapshot real."""

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

pytestmark = pytest.mark.integration

NOTEBOOK = Path(__file__).resolve().parents[2] / "notebooks" / "analise_dengue_sp.ipynb"


def test_notebook_executa_sem_erros() -> None:
    nb = nbformat.read(NOTEBOOK, as_version=4)  # type: ignore[no-untyped-call]  # nbformat sem tipos
    client = NotebookClient(
        nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": NOTEBOOK.parent}}
    )
    client.execute()  # levanta CellExecutionError se alguma célula falhar
