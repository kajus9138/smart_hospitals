---
title: Indicadores de tendência sem previsão numérica
type: decision
permalink: smart-hospitals/decisoes/indicadores-de-tendencia-sem-previsao-numerica
tags:
- decisao
- prd
- indicadores
---

# Indicadores de tendência sem previsão numérica

Origem: PRD seções 3, 5, 6 e 10.

## Decisão
O MCP informa a situação atual e indicadores de tendência já fornecidos pelo InfoDengue (Rt, p_rt1,
nível de alerta, casos estimados por nowcast com intervalo, variação semanal). Não produz previsão
numérica de casos futuros. Para as semanas recentes, usa `casos_est` (nowcast) com intervalo
(mín./máx.) em vez de apenas casos notificados.

## Contexto
- O caso de uso (comprar medicamento antecipadamente) precisa de direção da tendência, não de um número exato.
- Atraso de notificação faz as últimas semanas parecerem em queda quando se olha só os notificados.

## Alternativas descartadas
- Modelo próprio de previsão de casos: adiado para uma fase seguinte.
- Usar só casos notificados nas semanas recentes: subestima a tendência por causa do atraso de notificação.

## Observations
- [decision] Sem previsão numérica na fase 1; só indicadores de tendência #indicadores
- [decision] Semanas recentes usam casos_est (nowcast) com intervalo #indicadores
- [risk] Atraso de notificação distorce as semanas recentes; mitigado com nowcast #dados

## Relations
- part_of [[Decisões do PRD - fase 1]]
- relates_to [[MCP server local via stdio com FastMCP]]
