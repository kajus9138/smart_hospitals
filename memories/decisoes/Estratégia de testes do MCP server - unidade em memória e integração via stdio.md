---
title: Estratégia de testes do MCP server - unidade em memória e integração via stdio
type: decision
permalink: smart-hospitals/decisoes/estrategia-de-testes-do-mcp-server-unidade-em-memoria-e-integracao-via-stdio
tags:
- decisao
- testes
- mcp
- task-10
---

# Estratégia de testes do MCP server - unidade em memória e integração via stdio

Origem: task 10, implementada em `tests/integration/test_mcp_stdio.py` em 2026-10-22.

## Decisão
- **Duas camadas**: `tests/mcp_server/` usa `Client(server.mcp)` em memória com a amostra fixa
  (rápido, mede cobertura); `tests/integration/` sobe `python -m smart_hospitals.mcp_server` em
  subprocesso e fala pelo stdio com o snapshot real em `data/` (sem rede).
- Integração cobre: lista das 4 tools, cada tool com `data_referencia` igual à do snapshot e seus
  campos próprios, erro claro de parâmetro, e um teste com JSON-RPC cru (`subprocess.Popen`) que
  verifica que toda linha do stdout é JSON-RPC 2.0, que cada `id` foi respondido e que os logs
  (inicialização e `tool=... status=ok`) foram para o stderr.
- Marker `integration` registrado no `pyproject.toml`; `uv run pytest -m "not integration"` pula
  esses testes (~6 s) num ciclo rápido.
- Async via plugin `anyio` do pytest + `mcp.Client`; sem `pytest-asyncio`.
- Cobertura mínima de 80% fica só em `[tool.coverage.report] fail_under`; o código que roda no
  subprocesso não entra na medição, e não precisa (a camada em memória já cobre 100% do servidor).

## Contexto
A task sugeria `ClientSession`/`stdio_client` da v1 do SDK, `pytest-asyncio` e `--cov-fail-under` no
`addopts`. Ao testar com stdout cru, descobriu-se que fechar o stdin logo após enviar as requisições
faz o servidor cancelar as `tools/call` em curso (só parte dos ids era respondida).

## Alternativas descartadas
- Fechar o stdin e usar `communicate()`: perde respostas (ver Contexto). O teste lê até receber todos
  os ids e só então fecha o stdin; um `threading.Timer` de 30 s mata o processo se travar.
- `pytest-asyncio`: dependência extra; o `anyio` já vem com o SDK.
- Medir cobertura do subprocesso (`coverage` com `COVERAGE_PROCESS_START`): complexidade sem ganho.

## Observations
- [decision] Integração do MCP sobe o servidor real via stdio, com o snapshot versionado #testes #mcp
- [fact] Com EOF no stdin o servidor MCP cancela chamadas de tool em andamento #mcp
- [fact] O stderr do MCPServer usa handler Rich que quebra o log em colunas; normalizar espaços antes de buscar status= #observabilidade
- [convention] stderr do subprocesso vai para arquivo, não pipe, para não travar o servidor #testes
- [convention] Marker integration para separar testes lentos de subprocesso #testes

## Relations
- implements [[Observabilidade e qualidade da fase 1]]
- relates_to [[MCP server - implementação e erros das tools]]
