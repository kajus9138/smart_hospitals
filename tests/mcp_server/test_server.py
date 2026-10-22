"""Testes do MCP server: tools via cliente em memória e um teste de fumaça via stdio."""

import logging
import runpy
import sys
import time
from collections.abc import AsyncIterator
from typing import Any

import pandas as pd
import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.types import CallToolResult, TextContent

from smart_hospitals.data import get_reference_date
from smart_hospitals.mcp_server import server

pytestmark = pytest.mark.anyio

TOOLS = {"situacao_atual", "tendencia", "serie_historica", "comparativo_sazonal"}
VALID_CALLS: list[tuple[str, dict[str, Any]]] = [
    ("situacao_atual", {}),
    ("tendencia", {}),
    ("serie_historica", {"inicio": "202401", "fim": "202405"}),
    ("comparativo_sazonal", {}),
]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client(
    sample_dengue_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[Client]:
    """Cliente em memória com o servidor lendo a amostra fixa em vez do snapshot."""
    monkeypatch.setattr(server, "get_data", lambda: sample_dengue_data)
    async with Client(server.mcp) as mcp_client:
        yield mcp_client


async def call(client: Client, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    result = await client.call_tool(tool, args)
    assert not result.is_error, error_text(result)
    content: dict[str, Any] | None = result.structured_content
    assert content is not None
    return content


def error_text(result: CallToolResult) -> str:
    return " ".join(c.text for c in result.content if isinstance(c, TextContent))


async def test_lists_the_four_tools(client: Client) -> None:
    tools = await client.list_tools()
    assert {tool.name for tool in tools.tools} == TOOLS


@pytest.mark.parametrize(("tool", "args"), VALID_CALLS)
async def test_every_tool_returns_reference_date(
    client: Client, tool: str, args: dict[str, Any]
) -> None:
    result = await call(client, tool, args)
    assert result["data_referencia"] == "2024-01-29"


async def test_situacao_atual(client: Client) -> None:
    result = await call(client, "situacao_atual", {})
    assert result["casos_notificados"] == 200
    assert result["casos_est"] == 220.0
    assert result["casos_est_min"] == 200.0
    assert result["casos_est_max"] == 240.0
    assert result["incidencia_100k"] == 11.0
    assert result["nivel_alerta"] == "amarelo"
    assert result["rt"] == 1.1
    assert result["p_rt1"] == 0.72
    assert result["variacao_semanal"] == 15.8


async def test_tendencia_default_uses_four_weeks(client: Client) -> None:
    result = await call(client, "tendencia", {})
    assert [week["SE"] for week in result["semanas"]] == [202402, 202403, 202404, 202405]
    assert result["tendencia_resumo"] == "alta"
    assert result["rt_medio"] == 1.19
    assert result["p_rt1_medio"] == 0.82


async def test_tendencia_custom_window(client: Client) -> None:
    result = await call(client, "tendencia", {"semanas": 2})
    assert len(result["semanas"]) == 2


@pytest.mark.parametrize("semanas", [0, 53, 100])
async def test_tendencia_rejects_out_of_range(client: Client, semanas: int) -> None:
    result = await client.call_tool("tendencia", {"semanas": semanas})
    assert result.is_error
    assert "semanas" in error_text(result)


async def test_serie_historica_by_se(client: Client) -> None:
    result = await call(client, "serie_historica", {"inicio": "202402", "fim": "202404"})
    assert result["total_semanas"] == 3
    assert [week["SE"] for week in result["serie"]] == [202402, 202403, 202404]
    assert result["serie"][0]["data_iniSE"] == "2024-01-08"


async def test_serie_historica_accepts_se_as_number(client: Client) -> None:
    result = await call(client, "serie_historica", {"inicio": 202402, "fim": 202403})
    assert result["total_semanas"] == 2


async def test_serie_historica_by_date(client: Client) -> None:
    result = await call(client, "serie_historica", {"inicio": "2024-01-10", "fim": "2024-01-20"})
    assert [week["SE"] for week in result["serie"]] == [202402, 202403]


@pytest.mark.parametrize(
    ("inicio", "fim", "message"),
    [
        ("2024-13-01", "202404", "AAAASS"),
        ("2024", "202404", "AAAASS"),
        ("202404", "202401", "posterior"),
        ("202401", "2024-01-20", "mesmo formato"),
    ],
)
async def test_serie_historica_rejects_invalid_bounds(
    client: Client, inicio: str, fim: str, message: str
) -> None:
    result = await client.call_tool("serie_historica", {"inicio": inicio, "fim": fim})
    assert result.is_error
    assert message in error_text(result)


async def test_serie_historica_requires_both_bounds(client: Client) -> None:
    result = await client.call_tool("serie_historica", {"inicio": "202401"})
    assert result.is_error
    assert "fim" in error_text(result)


async def test_comparativo_sazonal_defaults_to_latest_week(client: Client) -> None:
    result = await call(client, "comparativo_sazonal", {})
    assert result["semana_epidemiologica"] == 5
    assert result["ano_referencia"] == 2024
    assert result["ano_atual"] == 220
    assert result["anos_comparados"] == 0
    assert result["media_historica"] is None


async def test_comparativo_sazonal_given_week(client: Client) -> None:
    result = await call(client, "comparativo_sazonal", {"semana": 2})
    assert result["semana_epidemiologica"] == 2
    assert result["ano_atual"] == 130


@pytest.mark.parametrize("semana", [0, 54])
async def test_comparativo_sazonal_rejects_out_of_range(client: Client, semana: int) -> None:
    result = await client.call_tool("comparativo_sazonal", {"semana": semana})
    assert result.is_error
    assert "semana" in error_text(result)


async def test_logs_each_call_with_params_and_duration(
    client: Client, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=server.logger.name):
        await call(client, "tendencia", {"semanas": 2})
        await client.call_tool("serie_historica", {"inicio": "x", "fim": "202401"})
    messages = [r.getMessage() for r in caplog.records if r.name == server.logger.name]
    assert len(messages) == 2
    assert "tool=tendencia params={'semanas': 2}" in messages[0]
    assert "duracao_ms=" in messages[0]
    assert messages[0].endswith("status=ok")
    assert "tool=serie_historica" in messages[1]
    assert "status=erro: Valor inválido 'x'" in messages[1]


@pytest.mark.parametrize("error", [RuntimeError("segredo interno"), ValueError("segredo interno")])
async def test_unexpected_error_is_logged_and_not_leaked(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, error: Exception
) -> None:
    """Só ParametroInvalido chega ao cliente; ValueError interno (ex. NaN) é falha do servidor."""

    def broken() -> pd.DataFrame:
        raise error

    monkeypatch.setattr(server, "get_data", broken)
    with caplog.at_level(logging.INFO, logger=server.logger.name):
        async with Client(server.mcp) as mcp_client:
            result = await mcp_client.call_tool("situacao_atual", {})
    assert result.is_error
    assert "segredo interno" not in error_text(result)
    assert any("status=erro inesperado" in r.getMessage() for r in caplog.records)


async def test_nothing_is_written_to_stdout(
    client: Client, capsys: pytest.CaptureFixture[str]
) -> None:
    for tool, args in VALID_CALLS:
        await call(client, tool, args)
    await client.call_tool("tendencia", {"semanas": 0})
    assert capsys.readouterr().out == ""


async def test_each_tool_answers_under_one_second_with_real_snapshot() -> None:
    server.get_data.cache_clear()
    async with Client(server.mcp) as mcp_client:
        for tool, args in VALID_CALLS:
            start = time.perf_counter()
            await call(mcp_client, tool, args)
            assert time.perf_counter() - start < 1.0, tool


async def test_stdio_smoke() -> None:
    """Sobe o servidor como subprocesso e conversa pelo stdio, como faria um cliente MCP."""
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "smart_hospitals.mcp_server"]
    )
    async with Client(params) as mcp_client:
        tools = await mcp_client.list_tools()
        assert {tool.name for tool in tools.tools} == TOOLS
        result = await call(mcp_client, "situacao_atual", {})
    assert result["data_referencia"] == str(get_reference_date(server.get_data()))


def test_main_loads_snapshot_then_runs_stdio(
    sample_dengue_data: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    loads: list[bool] = []

    def fake_get_data() -> pd.DataFrame:
        loads.append(True)
        return sample_dengue_data

    transports: list[str] = []
    monkeypatch.setattr(server, "get_data", fake_get_data)
    monkeypatch.setattr(server.mcp, "run", transports.append)
    server.main()
    runpy.run_module("smart_hospitals.mcp_server", run_name="__main__")
    assert transports == ["stdio", "stdio"]
    assert len(loads) == 2
