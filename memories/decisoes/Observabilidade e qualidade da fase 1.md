---
title: Observabilidade e qualidade da fase 1
type: decision
permalink: smart-hospitals/decisoes/observabilidade-e-qualidade-da-fase-1
tags:
- decisao
- prd
- qualidade
- observabilidade
---

# Observabilidade e qualidade da fase 1

Origem: PRD seções 7 e 9.

## Decisão
- Logs: o MCP registra cada chamada de tool (nome, parâmetros, duração, sucesso/erro) em stderr; o stdout
  fica reservado ao protocolo MCP. O script de extração registra quantas semanas baixou e o intervalo coberto.
- Testes: pytest + pytest-cov, cobertura mínima de 80% no módulo de dados e no MCP server; testes usam o
  snapshot (ou amostra fixa) e não acessam a rede; teste de fumaça do dashboard com `streamlit.testing.AppTest`.
- Aceite: dashboard publicado responde HTTP 200; MCP iniciado via stdio lista as tools e responde a cada uma
  com dados válidos.
- Ferramentas: ruff (lint e formatação) e mypy, também via pre-commit.
- Segurança: dados públicos e agregados, sem dados de pacientes; nenhum segredo versionado.

## Contexto
Com transporte stdio, qualquer print no stdout corrompe o protocolo, por isso o log vai para stderr.

## Alternativas descartadas
- Testes acessando a API do InfoDengue: descartado; testes são offline e determinísticos.
- Métricas/tracing além de logs: não registrado no PRD; observabilidade mínima é suficiente para a PoC.

## Observations
- [convention] Logs em stderr; nada além do protocolo MCP no stdout #observabilidade
- [requirement] Cobertura >= 80% no módulo de dados e no MCP server #testes
- [convention] Testes não acessam a rede #testes

## Relations
- part_of [[Decisões do PRD - fase 1]]
- relates_to [[MCP server local via stdio com FastMCP]]
