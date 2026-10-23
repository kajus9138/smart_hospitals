---
title: MCP server - implementação e erros das tools
type: decision
permalink: smart-hospitals/decisoes/mcp-server-implementacao-e-erros-das-tools
tags:
- decisao
- mcp
- observabilidade
- task-9
---

# MCP server - implementação e erros das tools

Origem: task 9, implementada em `src/smart_hospitals/mcp_server/server.py` em 2026-10-22.

## Decisão
- `MCPServer("dengue-sp")` do SDK `mcp` 2.3 com quatro tools síncronas e finas que delegam ao módulo de
  dados; todas devolvem `data_referencia`. Entradas: `dengue-mcp` (`project.scripts`) e
  `python -m smart_hospitals.mcp_server`.
- **Validação em duas camadas**: tipo e intervalo pelo schema (`Annotated[int, Field(ge=1, le=52)]`);
  formato de SE/data e ordem do intervalo pelo módulo de dados. `inicio`/`fim` aceitam `str | int`
  (agentes mandam SE como número JSON). `semana` vai até 53, como o módulo de dados.
- **Erros**: o módulo de dados levanta `ParametroInvalidoError` (subclasse de `ValueError`) só para erro de
  parâmetro; o decorator `@logged` converte em `ToolError`, cuja mensagem chega ao modelo. Qualquer outra
  exceção (inclusive `ValueError` interno, como NaN em `int()`) é logada com traceback e o cliente recebe
  só "Error executing tool X".
- **Log (RNF02)**: `@logged` registra tool, parâmetros, `duracao_ms` e status em stderr. Chamadas barradas
  pelo schema não chegam ao decorator; o SDK as registra ("Tool 'x' rejected arguments").
- **Dados**: `get_data()` com `functools.cache`, chamado em `main()` antes de `mcp.run("stdio")`, para não
  haver carga concorrente em threads na primeira chamada. Atualizou o CSV → reiniciar o servidor.
- **Testes**: `Client(mcp)` em memória (plugin `anyio` do pytest, sem `pytest-asyncio`) e um teste de
  fumaça que sobe o servidor por stdio em subprocesso.

## Contexto
O código sugerido na task usava `mcp.server.Server` com `@app.tool()` (não existe no servidor low-level)
e levantava `ValueError`; na v2 só a mensagem de `ToolError` chega ao cliente. A revisão de código
apontou que converter todo `ValueError` mascarava bugs de dados como erro do usuário.

## Alternativas descartadas
- Converter todo `ValueError` em `ToolError`: expõe mensagens internas do pandas e perde o traceback.
- Middleware do servidor para log: pega também as rejeições de schema, mas trabalha com parâmetros
  brutos de JSON-RPC; o log do SDK já cobre essas rejeições.
- Recarregar o snapshot por mtime: desnecessário com atualização sob demanda e servidor local.

## Limitações conhecidas
- NaN em Rt/p_rt1 na semana mais recente sairia como `NaN` no JSON (não ocorre no snapshot atual;
  ver [[Indicadores do módulo de dados - regras de cálculo]]).

## Observations
- [decision] Só ParametroInvalidoError vira ToolError; erro interno fica genérico para o cliente #mcp
- [convention] Tools do MCP são finas: validação de schema + delegação ao módulo de dados #mcp
- [decision] Snapshot carregado na inicialização; reiniciar após atualizar o CSV #mcp #dados
- [fact] O SDK mcp v2 loga em stderr as chamadas rejeitadas pelo schema #observabilidade

## Relations
- implements [[MCP server local via stdio com FastMCP]]
- implements [[Observabilidade e qualidade da fase 1]]
- depends_on [[Indicadores do módulo de dados - regras de cálculo]]
