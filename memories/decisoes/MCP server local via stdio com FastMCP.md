---
title: MCP server local via stdio com FastMCP
type: decision
permalink: smart-hospitals/decisoes/mcp-server-local-via-stdio-com-fastmcp
tags:
- decisao
- prd
- mcp
---

# MCP server local via stdio com FastMCP

Origem: PRD seções 4, 5, 6 (RF02), 7 e 8.

## Decisão
MCP server com o SDK oficial `mcp` para Python (FastMCP), transporte stdio, execução local, somente leitura.
Quatro tools, todas retornando a data de referência do snapshot:
- `situacao_atual()`: casos notificados, casos_est (mín./máx.), incidência/100 mil hab., nível de alerta, Rt, p_rt1, variação semanal.
- `tendencia(semanas=4)`: indicadores das últimas N semanas + resumo (alta, estável ou queda) derivado de Rt, p_rt1 e variação semanal.
- `serie_historica(inicio, fim)`: série semanal no intervalo (SE ou datas).
- `comparativo_sazonal(semana=None)`: semana atual (ou informada) vs. mesma semana dos anos anteriores (média, mín., máx.).

Parâmetros são validados (tipos e intervalos) com erro claro; cada tool responde em < 1 s (dados em memória).

## Contexto
Os consumidores nesta fase são clientes MCP locais (Claude Desktop/Claude Code). A demonstração de sucesso
é um cliente MCP responder à pergunta do caso de uso usando as tools.

## Alternativas descartadas
- Publicar o MCP na internet com transporte HTTP: fora de escopo nesta fase (exigiria hospedagem,
  autenticação e exposição pública).
- Tools de escrita/atualização de dados: o MCP é somente leitura (RNF01).

## Observations
- [decision] Transporte stdio, execução local; HTTP fica para fase futura #mcp
- [decision] Quatro tools somente leitura, todas com data de referência #mcp
- [constraint] stdout reservado ao protocolo MCP; logs só em stderr #mcp #observabilidade
- [requirement] Cada tool responde em menos de 1 s localmente #performance

## Relations
- part_of [[Decisões do PRD - fase 1]]
- depends_on [[Módulo de dados compartilhado entre dashboard e MCP]]
- relates_to [[Indicadores de tendência sem previsão numérica]]
