---
title: Portões de aprovação humana do dashboard
type: decision
permalink: smart-hospitals/decisoes/portoes-de-aprovacao-humana-do-dashboard
tags:
- decisao
- prd
- processo
---

# Portões de aprovação humana do dashboard

Origem: PRD seção 4.

## Decisão
Dois portões humanos no fluxo do dashboard:
1. Após a análise no notebook, o responsável humano preenche `docs/visualizacoes.md` com as visualizações
   escolhidas. A implementação do dashboard só começa depois disso.
2. Após o protótipo local, o responsável humano valida o design. A publicação só acontece depois dessa aprovação.

## Contexto
O notebook só sugere visualizações; quem decide o que vai para o painel é o humano. Risco de falhas de
layout listado no PRD (seção 10).

## Alternativas descartadas
- Agente escolher as visualizações e publicar sem revisão: descartado; escolha e design ficam com o humano.

## Observations
- [decision] docs/visualizacoes.md preenchido por humano antes de implementar o dashboard #processo
- [decision] Publicação só após validação humana do protótipo #processo

## Relations
- part_of [[Decisões do PRD - fase 1]]
- relates_to [[Stack Python e publicação no Streamlit Community Cloud]]
