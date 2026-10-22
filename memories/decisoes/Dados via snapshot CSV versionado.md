---
title: Dados via snapshot CSV versionado
type: decision
permalink: smart-hospitals/decisoes/dados-via-snapshot-csv-versionado
tags:
- decisao
- prd
- dados
- infodengue
---

# Dados via snapshot CSV versionado

Origem: PRD seções 4, 5, 8 e 11.

## Decisão
Um script de extração em Python (pandas lendo a API do InfoDengue em formato CSV) baixa os dados e grava
um snapshot CSV versionado no repositório. Dashboard, MCP server e testes leem **apenas** o snapshot;
nenhum depende da API em tempo de execução.

## Contexto
- PoC sem banco de dados nem agendador; dashboard no plano gratuito do Streamlit Community Cloud.
- Testes não podem acessar a rede (RNF03) e precisam de dados determinísticos.
- Dashboard e MCP devem expor os mesmos números para a mesma data de referência.

## Alternativas descartadas
- Consultar a API do InfoDengue em tempo de execução (dashboard/MCP): criaria dependência de rede e de
  latência, e os consumidores poderiam ver números diferentes.
- Atualização automática/agendada do snapshot: fora de escopo; a atualização é sob demanda, rodando o
  script manualmente.

## Consequências e riscos
- O snapshot envelhece: a data de referência fica sempre visível no dashboard e vai em toda resposta do MCP.
- Premissa: o CSV fica abaixo de 500 KB (limite do hook `check-added-large-files` do pre-commit).
- Premissa: a API do InfoDengue é pública, sem chave, e tem dados de SP desde 2010.

## Observations
- [decision] Fonte única de dados em runtime é o snapshot CSV versionado #dados
- [decision] Atualização do snapshot é manual, sob demanda #dados
- [risk] Snapshot desatualizado; mitigado exibindo a data de referência #dados
- [constraint] CSV < 500 KB por causa do hook check-added-large-files #pre-commit

## Relations
- part_of [[Decisões do PRD - fase 1]]
- used_by [[Módulo de dados compartilhado entre dashboard e MCP]]
