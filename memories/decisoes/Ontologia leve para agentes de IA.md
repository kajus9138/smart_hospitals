---
title: Ontologia leve para agentes de IA
type: decision
permalink: smart-hospitals/decisoes/ontologia-leve-para-agentes-de-ia
tags:
- decisao
- ontologia
- agente
- task-13
- task-14
- task-15
- task-16
- task-17
---

# Ontologia leve para agentes de IA

Origem: fase 2 do PRD (`.taskmaster/docs/prd-fase2.md`, PR #18), tasks 13 a 17, PRs #19 a #23, em
2026-11-04.

## Decisão
- **YAML versionado e escrito à mão** em `docs/ontologia/dengue_sp.yaml`, em português, com as seções
  `metadados`, `conceitos`, `relacoes`, `regras`, `achados` e `orientacoes_agente`.
- **Estilo (RNF06)**: identificadores em `snake_case` sem acento, rótulos legíveis com acento, frases curtas
  e comentários YAML onde ajudam. `id` é único dentro da seção, não entre seções: `comparativo_sazonal` e
  `intervalo_nowcast` aparecem como conceito/regra/achado de propósito.
- **Achados estáticos com validade**: cada achado traz afirmação, evidência, método, origem no notebook,
  `valido_ate_se` (hoje 202640), limitações e implicação para o agente. Um snapshot mais novo derruba os
  testes, o que obriga a revisar a ontologia no mesmo PR. A situação da semana corrente não é achado:
  vem das tools do MCP.
- **Entrega como arquivo no repositório**, que quem configura o agente carrega no contexto: no Claude
  Code, com `@./docs/ontologia/dengue_sp.yaml` no `CLAUDE.md` do agente (exemplo no README); nos demais,
  anexo ou system prompt. O `CLAUDE.md` deste repositório não importa a ontologia: ele orienta o
  desenvolvimento, não o agente hospitalar. O MCP traz os valores; a ontologia diz como lê-los.
- **Consistência por testes**: `tests/test_ontologia.py` confere limiares, `LEVEL_MAP`, colunas, tools,
  validade e parte das evidências contra o código e o snapshot (detalhes em
  [[Testes de consistência da ontologia]]).
- **Tamanho (RNF05)**: até 20 KiB (20 480 bytes, ~5 mil tokens), garantido por `test_tamanho_maximo`;
  a versão 1.0.0 tem 13 788 bytes.

## Contexto
A análise exploratória da fase 1 produziu conhecimento (janela sazonal, anos de surto, Rt como sinal
antecipado, atraso de notificação) que o MCP não transmite: ele devolve números, não interpretação. Esse
conhecimento estava espalhado entre o notebook, as notas de decisão e o módulo de dados. Na revisão da
task 13, a primeira versão divergia do código em pontos sutis (incidência sobre `casos_est`, N semanas da
tendência, fallback 0.0 da variação semanal), o que motivou testar também o texto lido pelo agente.

## Alternativas descartadas
- **OWL/RDF com raciocinador, SPARQL ou banco de grafos**: formal demais; o agente precisa de contexto
  textual legível, não de inferência.
- **Recalcular os achados a partir do snapshot**: os achados vêm de análise do notebook (surtos,
  Spearman, sazonalidade, leitura qualitativa das curvas). Ficam estáticos com data de validade; só as
  evidências que são leitura direta do snapshot (`cobertura`, `atraso_notificacao`) são testadas.

## Adiado
- **Expor a ontologia pelo MCP server (resource ou prompt)**: fora do escopo desta fase pelo PRD, não
  descartado. Acoplaria o arquivo ao servidor e dependeria de o cliente pedir o recurso; reavaliar se
  surgir um cliente que não aceite arquivo de contexto.

## Limitações conhecidas
- Os achados valem para o snapshot até a SE 202640; a maior parte das evidências precisa de revisão
  manual no notebook quando o snapshot mudar.
- A ontologia resume a análise para contexto; não substitui o notebook.
- Pendente: a demonstração do critério de aceite da fase 2 (cliente com a ontologia no contexto e o MCP
  conectado respondendo ao caso de uso da fase 1, citando data de referência, tendência e um achado, sem
  previsão numérica) não foi registrada.

## Observations
- [decision] Ontologia leve em YAML versionado, escrito à mão, sem raciocinador #ontologia
- [decision] Achados estáticos com valido_ate_se; snapshot novo força revisão no mesmo PR #ontologia
- [decision] Ontologia entregue como arquivo de contexto, não como resource do MCP (adiado) #mcp
- [convention] Identificadores em snake_case sem acento; rótulos legíveis com acento #estilo
- [convention] id único dentro da seção, não entre seções #ontologia
- [fact] Limite de 20 KiB testado; versão 1.0.0 com 13 788 bytes #ontologia

## Relations
- relates_to [[Notebook de análise exploratória - decisões]]
- relates_to [[Indicadores do módulo de dados - regras de cálculo]]
- relates_to [[Indicadores de tendência sem previsão numérica]]
- relates_to [[Testes de consistência da ontologia]]
- relates_to [[PyYAML e stubs como dependências de dev]]
- relates_to [[README e conexão do MCP a clientes]]
- relates_to [[MCP server local via stdio com FastMCP]]
