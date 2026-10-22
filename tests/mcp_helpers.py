"""Constantes e utilitários compartilhados pelos testes do MCP server."""

from mcp.types import CallToolResult, TextContent

TOOLS = {"situacao_atual", "tendencia", "serie_historica", "comparativo_sazonal"}


def error_text(result: CallToolResult) -> str:
    return " ".join(c.text for c in result.content if isinstance(c, TextContent))
