---
title: Extração do InfoDengue - formato real da API
type: decision
permalink: smart-hospitals/decisoes/extracao-do-info-dengue-formato-real-da-api
tags:
- decisao
- dados
- infodengue
- task-2
---

# Extração do InfoDengue - formato real da API

Origem: task 2 (PR #5), verificado na API em 2026-10-22.

## Decisão
- `scripts/extract_infodengue.py` usa `alertcity` com `ew_end=53` (não 52) e ordena o resultado por `SE` crescente.
- O snapshot `data/dengue_sp_snapshot.csv` guarda **todas** as 30 colunas da API (cópia bruta); o módulo de
  dados escolhe as colunas que usa.
- Colunas obrigatórias validadas na extração: data_iniSE, SE, casos_est, casos_est_min, casos_est_max,
  casos, p_rt1, p_inc100k, Rt, nivel, receptivo. A extração também rejeita SE duplicada.
- O download usa `urlopen` com timeout de 120 s; os testes leem uma amostra real via `file://`, sem rede.

## Contexto
- A tarefa original citava a coluna `receptession_t`, que não existe; a equivalente é `receptivo`.
- Com `ew_end=52` sumiam as SEs 201453, 202053 e 202553 (anos com 53 semanas).
- A API devolve as semanas em ordem decrescente.
- Snapshot inicial: 875 semanas (201001–202640), 203 KB; cresce ~12 KB/ano, folga até o limite de 500 KB.

## Alternativas descartadas
- Guardar só o subconjunto de colunas (~76 KB): perderia campos possivelmente úteis (pop, nivel_inc, clima).
- `pd.read_csv(url)` direto: sem timeout e com erro de rede pouco claro.

## Observations
- [fact] SE de anos com 53 semanas exige ew_end=53 na API alertcity #infodengue
- [fact] A API alertcity devolve semanas em ordem decrescente #infodengue
- [decision] Snapshot guarda todas as colunas da API #dados
- [convention] Scripts em scripts/ são importáveis nos testes via pythonpath do pytest #testes

## Relations
- refines [[Dados via snapshot CSV versionado]]
- used_by [[Módulo de dados compartilhado entre dashboard e MCP]]
