---
title: Módulo de dados compartilhado entre dashboard e MCP
type: decision
permalink: smart-hospitals/decisoes/modulo-de-dados-compartilhado-entre-dashboard-e-mcp
tags:
- decisao
- prd
- arquitetura
---

# Módulo de dados compartilhado entre dashboard e MCP

Origem: PRD seção 8.

## Decisão
Dashboard e MCP server são processos independentes que importam um mesmo módulo de dados em Python,
responsável por ler o snapshot, limpar os dados e calcular os indicadores.
"Situação atual" = a semana epidemiológica mais recente presente no snapshot; essa data de referência
é sempre informada pelo dashboard e pelo MCP.

    API InfoDengue -> script de extração -> snapshot CSV (versionado)
                                                 |
                                       módulo de dados (Python)
                                         |                  |
                     Dashboard Streamlit (Streamlit Cloud)  MCP server (FastMCP, stdio, local)

## Contexto
O agente de IA e o humano olhando o dashboard precisam ver os mesmos números; a regra de cálculo fica num
lugar só e é testada uma vez (meta de cobertura de 80% vale para este módulo).

## Alternativas descartadas
- Cada consumidor calcular seus próprios indicadores: risco de divergência entre dashboard e MCP.
- Dashboard e MCP no mesmo processo: o dashboard roda no Streamlit Cloud e o MCP roda localmente via stdio,
  então os processos são separados por natureza.

## Observations
- [decision] Lógica de dados e indicadores vive num módulo único, importado por dashboard e MCP #arquitetura
- [convention] "Situação atual" é a SE mais recente do snapshot e sempre vem com a data de referência #dados

## Relations
- part_of [[Decisões do PRD - fase 1]]
- depends_on [[Dados via snapshot CSV versionado]]
- used_by [[MCP server local via stdio com FastMCP]]
