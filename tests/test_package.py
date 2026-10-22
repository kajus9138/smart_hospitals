"""Teste de fumaça: o pacote e seus subpacotes são importáveis."""

import importlib

import pytest

import smart_hospitals


@pytest.mark.parametrize(
    "module",
    [
        "smart_hospitals.data",
        "smart_hospitals.data.loader",
        "smart_hospitals.data.indicators",
        "smart_hospitals.dashboard",
        "smart_hospitals.mcp_server",
    ],
)
def test_submodule_imports(module: str) -> None:
    assert importlib.import_module(module) is not None


def test_version_matches_metadata() -> None:
    from importlib.metadata import version

    assert smart_hospitals.__version__ == version("smart-hospitals")
