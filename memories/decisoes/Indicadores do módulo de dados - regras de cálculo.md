---
title: Indicadores do módulo de dados - regras de cálculo
type: decision
permalink: smart-hospitals/decisoes/indicadores-do-modulo-de-dados-regras-de-calculo
tags:
- decisao
- dados
- indicadores
- task-3
---

# Indicadores do módulo de dados - regras de cálculo

Origem: task 3, implementada em `src/smart_hospitals/data/` (loader.py, indicators.py) em 2026-10-22.

## Decisão
- **Situação atual**: última SE do snapshot; variação semanal sobre `casos_est` (nowcast), 0 se só há uma
  semana ou a anterior é 0. `casos_est_min`/`casos_est_max` podem ser `None` (o InfoDengue deixa o intervalo
  vazio em 40 semanas do snapshot, inclusive em 2024 e 2025).
- **Tendência** (últimas N=4 semanas): Rt médio > 1,1 e p_rt1 médio > 0,7 → `alta`; Rt médio < 0,9 →
  `queda`; senão `estavel`.
- **Comparativo sazonal**: média/mín./máx. usam só anos **anteriores** ao ano de referência (o da SE mais
  recente); `ano_atual` é `None` se a semana ainda não ocorreu no ano. Valores arredondados (não truncados).
- **Série histórica**: aceita SE (`202401`) ou data ISO (`2024-01-01`), sem misturar; com datas entram as
  semanas que *contêm* início e fim. Intervalo invertido ou formato inválido → `ValueError`.
- **Saída pronta para JSON**: registros com data ISO e NaN → `None`, para o MCP devolver direto.
- O loader rejeita colunas faltando e SE duplicada, e devolve tudo ordenado por SE. As funções assumem
  essa ordenação.

## Contexto
O código sugerido na task incluía o ano atual na "média histórica" e pegava `ano_atual` da última linha
encontrada, que pode ser de um ano anterior. A docstring de `serie_historica` prometia aceitar datas, mas o
código não aceitava. `to_dict("records")` devolvia `pd.Timestamp`, que não serializa em JSON.

## Alternativas descartadas
- Média histórica incluindo o ano atual: compara o ano consigo mesmo e esconde surtos.
- Converter NaN para 0: inventaria um intervalo de confiança.

## Limitações conhecidas
- `SNAPSHOT_PATH` é relativo ao checkout (`parents[3]`). Funciona no Streamlit Cloud e no MCP local,
  mas não em uma instalação via wheel.
- NaN em Rt/p_rt1 nas semanas da janela não é tratado (não ocorre no snapshot atual).

## Observations
- [decision] Comparativo sazonal compara só com anos anteriores ao de referência #indicadores
- [decision] Saída do módulo de dados é serializável em JSON (ISO, NaN→None) #dados
- [fact] casos_est_max vem vazio em 40 semanas do snapshot #infodengue
- [convention] Funções de indicadores assumem df ordenado por SE, como devolve load_snapshot #dados

## Relations
- implements [[Módulo de dados compartilhado entre dashboard e MCP]]
- refines [[Indicadores de tendência sem previsão numérica]]
- depends_on [[Extração do InfoDengue - formato real da API]]
