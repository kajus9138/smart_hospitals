---
title: Decisões do PRD - fase 1
type: decision
permalink: smart-hospitals/decisoes/decisoes-do-prd-fase-1
tags:
- decisao
- prd
---

# Decisões do PRD - fase 1

Índice das decisões tomadas no PRD da fase 1 (`.taskmaster/docs/prd.txt`, refinado no commit a2e87cd,
backlog gerado no commit 8936114). Cada nota registra decisão, contexto e alternativas descartadas.

Objetivo da fase: dashboard claro e informativo + MCP server que dê aos agentes de IA hospitalares um
panorama da situação epidemiológica da dengue. Usuário-alvo fictício: tomador de decisão de alta hierarquia
de um hospital (ex.: "tenho poucas doses do medicamento X; qual a tendência de casos?").

## Observations
- [context] PoC para validar a viabilidade de hospitais inteligentes no SUS, desenvolvida em São Paulo #prd
- [decision] Fase 1 entrega dashboard publicado + MCP server local; nada de agente consumidor #escopo

## Relations
- contains [[Escopo da fase 1 - dengue em São Paulo capital]]
- contains [[Dados via snapshot CSV versionado]]
- contains [[Módulo de dados compartilhado entre dashboard e MCP]]
- contains [[MCP server local via stdio com FastMCP]]
- contains [[Indicadores de tendência sem previsão numérica]]
- contains [[Stack Python e publicação no Streamlit Community Cloud]]
- contains [[Portões de aprovação humana do dashboard]]
- contains [[Observabilidade e qualidade da fase 1]]
