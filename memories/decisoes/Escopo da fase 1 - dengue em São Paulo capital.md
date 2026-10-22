---
title: Escopo da fase 1 - dengue em São Paulo capital
type: decision
permalink: smart-hospitals/decisoes/escopo-da-fase-1-dengue-em-sao-paulo-capital
tags:
- decisao
- prd
- escopo
---

# Escopo da fase 1 - dengue em São Paulo capital

Origem: PRD seções 4 e 5.

## Decisão
Só dengue, só o município de São Paulo (capital, IBGE 3550308), da SE 1/2010 até a mais recente.
Não será criado agente de IA consumidor nesta fase; a validação é feita conectando um cliente MCP
existente (ex.: Claude Desktop) ao servidor.

## Contexto
É a primeira de uma série de demonstrações; o recorte pequeno permite entregar dashboard e MCP completos
e testados antes de ampliar.

## Alternativas descartadas (adiadas)
- Outros municípios e outras doenças (chikungunya, zika): fora de escopo.
- Construir um agente consumidor próprio: fora de escopo; usar clientes MCP prontos.
- Modelo de previsão de casos futuros: adiado para uma fase seguinte (ver [[Indicadores de tendência sem previsão numérica]]).

## Observations
- [decision] Recorte: dengue, SP capital (IBGE 3550308), desde 2010 #escopo
- [decision] Sem agente consumidor próprio na fase 1 #escopo

## Relations
- part_of [[Decisões do PRD - fase 1]]
