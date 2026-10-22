---
title: Stack Python e publicação no Streamlit Community Cloud
type: decision
permalink: smart-hospitals/decisoes/stack-python-e-publicacao-no-streamlit-community-cloud
tags:
- decisao
- prd
- stack
---

# Stack Python e publicação no Streamlit Community Cloud

Origem: PRD seções 8 e 11.

## Decisão
- Python 3.12, uv (pyproject.toml + uv.lock).
- Extração: pandas lendo a API do InfoDengue (CSV).
- Análise exploratória: Jupyter notebook (dependência de desenvolvimento) com pandas, numpy, seaborn, matplotlib.
- Dashboard: Streamlit + Plotly (gráficos interativos), publicado direto do repositório no Streamlit Community
  Cloud (plano gratuito); sem etapa de build.
- MCP: SDK oficial `mcp` (FastMCP).

## Contexto
Stack de uma linguagem só para extração, análise, dashboard e MCP, compartilhando o módulo de dados.
O plano gratuito do Streamlit Community Cloud é premissa suficiente para a PoC.

## Alternativas descartadas
O PRD não registra alternativas de stack avaliadas. Seaborn/matplotlib ficam restritos ao notebook; o dashboard usa Plotly
por ser interativo.

## Observations
- [decision] Dashboard em Streamlit + Plotly no Streamlit Community Cloud #stack
- [decision] seaborn/matplotlib só no notebook de análise #stack
- [requirement] Dashboard carrega em < 5 s com o app ativo (sem contar o despertar) #performance

## Relations
- part_of [[Decisões do PRD - fase 1]]
- relates_to [[Observabilidade e qualidade da fase 1]]
