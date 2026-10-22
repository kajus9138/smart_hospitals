"""Integração: o MCP server em subprocesso, conversando pelo stdio com o snapshot real."""

import json
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.types import LATEST_PROTOCOL_VERSION

from smart_hospitals.data import get_reference_date, load_snapshot
from tests.mcp_helpers import TOOLS, error_text

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

SERVER_COMMAND = [sys.executable, "-m", "smart_hospitals.mcp_server"]
# Cada tool com argumentos válidos e os campos próprios que a resposta deve trazer.
TOOL_CALLS: list[tuple[str, dict[str, Any], set[str]]] = [
    ("situacao_atual", {}, {"casos_notificados", "casos_est", "nivel_alerta", "rt", "p_rt1"}),
    ("tendencia", {"semanas": 4}, {"semanas", "tendencia_resumo", "rt_medio", "p_rt1_medio"}),
    ("serie_historica", {"inicio": "202401", "fim": "202404"}, {"total_semanas", "serie"}),
    ("comparativo_sazonal", {}, {"semana_epidemiologica", "ano_atual", "media_historica"}),
]
# Passa pelo schema e é barrada pelo módulo de dados, então chega ao log da tool com status=erro.
INVALID_CALL = ("serie_historica", {"inicio": "202404", "fim": "202401"})


@pytest.fixture(scope="module")
def reference_date() -> str:
    return get_reference_date(load_snapshot()).isoformat()


def server_params() -> StdioServerParameters:
    return StdioServerParameters(command=SERVER_COMMAND[0], args=SERVER_COMMAND[1:])


async def test_lists_the_four_tools() -> None:
    async with Client(server_params()) as client:
        tools = await client.list_tools()
    assert {tool.name for tool in tools.tools} == TOOLS


@pytest.mark.parametrize(("tool", "args", "fields"), TOOL_CALLS)
async def test_tool_answers_over_stdio(
    tool: str, args: dict[str, Any], fields: set[str], reference_date: str
) -> None:
    async with Client(server_params()) as client:
        result = await client.call_tool(tool, args)
    assert not result.is_error, error_text(result)
    content = result.structured_content
    assert content is not None
    assert content["data_referencia"] == reference_date
    assert fields <= content.keys()


async def test_invalid_parameter_returns_clear_error() -> None:
    async with Client(server_params()) as client:
        result = await client.call_tool("tendencia", {"semanas": 0})
    assert result.is_error
    assert "semanas" in error_text(result)


def test_stdout_carries_only_protocol_messages(tmp_path: Path) -> None:
    """Fala JSON-RPC cru com o processo: stdout só com mensagens do protocolo, logs no stderr."""
    calls = [*((tool, args) for tool, args, _ in TOOL_CALLS), INVALID_CALL]
    requests: list[dict[str, Any]] = [
        {
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "1.0"},
            },
        },
        {"method": "notifications/initialized"},
        {"method": "tools/list"},
        *({"method": "tools/call", "params": {"name": t, "arguments": a}} for t, a in calls),
    ]
    lines = []
    expected_ids = set()
    for request_id, request in enumerate(requests, start=1):
        message: dict[str, Any] = {"jsonrpc": "2.0", **request}
        if not request["method"].startswith("notifications/"):
            message["id"] = request_id
            expected_ids.add(request_id)
        lines.append(json.dumps(message))

    # stderr vai para arquivo: um pipe não lido pode encher e travar o servidor.
    stderr_path = tmp_path / "stderr.log"
    with (
        stderr_path.open("w") as stderr_file,
        subprocess.Popen(
            SERVER_COMMAND,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
        ) as proc,
    ):
        assert proc.stdin is not None and proc.stdout is not None
        watchdog = threading.Timer(30, proc.kill)
        watchdog.start()
        try:
            proc.stdin.write("\n".join(lines) + "\n")
            proc.stdin.flush()
            responses: dict[int, dict[str, Any]] = {}
            # O stdin só fecha depois de todas as respostas: com EOF o servidor cancela chamadas
            # em curso.
            while responses.keys() != expected_ids and (line := proc.stdout.readline()):
                response = parse_protocol_line(line)
                responses[response.get("id", 0)] = response
            rest, _ = proc.communicate(timeout=30)
            for line in rest.splitlines():
                parse_protocol_line(line)
        except BaseException:
            proc.kill()
            raise
        finally:
            watchdog.cancel()
    stderr = stderr_path.read_text()

    assert responses.keys() == expected_ids, stderr
    assert all(r.get("jsonrpc") == "2.0" and "error" not in r for r in responses.values())
    *ok_ids, invalid_id = sorted(responses)[2:]  # pula initialize e tools/list
    assert not any(responses[i]["result"]["isError"] for i in ok_ids)
    assert responses[invalid_id]["result"]["isError"]

    assert "Iniciando o MCP server dengue-sp" in stderr
    # O handler de log quebra as linhas em colunas; normaliza os espaços antes de procurar.
    statuses = re.findall(r"tool=(\w+) .*?status=(ok|erro)", " ".join(stderr.split()))
    expected = [(tool, "ok") for tool, _, _ in TOOL_CALLS] + [(INVALID_CALL[0], "erro")]
    assert sorted(statuses) == sorted(expected)


def parse_protocol_line(line: str) -> dict[str, Any]:
    try:
        message: dict[str, Any] = json.loads(line)
    except json.JSONDecodeError:
        pytest.fail(f"stdout com conteúdo fora do protocolo: {line!r}")
    return message
