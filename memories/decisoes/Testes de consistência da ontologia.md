---
title: Testes de consistência da ontologia
type: decision
permalink: smart-hospitals/decisoes/testes-de-consistencia-da-ontologia
tags:
- decisao
- ontologia
- testes
- task-14
---

# Testes de consistência da ontologia

Origem: task 14, PR #22, em 2026-11-04.

## Decisão
- `tests/test_ontologia.py` valida `docs/ontologia/dengue_sp.yaml` contra o código e o snapshot e roda
  no `uv run pytest --cov` padrão e no pre-commit (RNF08).
- Além do escopo literal da task (seções, IDs, relações, limiares, LEVEL_MAP, colunas, tools, validade,
  tamanho), o responsável aprovou verificações extras que fecham brechas de divergência:
  - o texto de `expressao` cita os limiares do código, com número exato (regex: 1.1 não aceita 1.15);
    é o texto que o agente lê, então não pode ficar com número antigo;
  - `semanas_padrao` = padrão de `calcular_tendencia` (via `inspect.signature`);
  - faixas de `nivel_de_alerta` e `tendencia` = `LEVEL_MAP` e `Trend`;
  - `referencia_codigo` existe em `indicators.py`; caminhos de `metadados.origem` existem;
  - `data_referencia` = `data_iniSE` da SE `valido_ate_se`; todos os achados e as SEs citadas nas
    orientações usam a mesma SE dos metadados;
  - evidências de `cobertura` e `atraso_notificacao` batem com o snapshot.
- Tools válidas vêm de `tests/mcp_helpers.TOOLS`, que `test_server.py` já compara com as tools
  registradas no servidor; caminho do YAML resolvido a partir de `__file__`, não do diretório atual.
- Testes validados por mutação manual (limiar no código e na ontologia, relação/coluna/tool/origem
  inexistentes, SE de validade, evidências): cada mutação derruba ao menos um teste.

## Ao atualizar o snapshot
O PR do novo snapshot quebra a validade e as evidências de `cobertura`/`atraso_notificacao`. Revisar
os achados no notebook e atualizar `metadados`, `valido_ate_se` dos achados, as orientações e as
evidências no mesmo PR; só subir a SE sem recalcular as evidências não passa.

## Alternativas descartadas
- `id` único entre seções: mantida a decisão da task 13 (único dentro da seção);
  `comparativo_sazonal` e `intervalo_nowcast` aparecem em mais de uma seção de propósito.
- Validar todas as evidências numéricas dos achados contra o snapshot: exigiria recalcular a análise
  do notebook nos testes (surtos, Spearman, sazonalidade); ficou só o que é leitura direta do snapshot.
- Schema formal (jsonschema/pydantic): uma dependência a mais para um arquivo pequeno escrito à mão.

## Observations
- [decision] Ontologia testada contra constantes, assinaturas e tools do código e contra o snapshot #ontologia
- [convention] Texto lido pelo agente (expressao, orientações) também é testado, não só os campos estruturados #ontologia
- [fact] Novo snapshot quebra os testes da ontologia até os achados serem revisados #snapshot

## Relations
- relates_to [[PyYAML e stubs como dependências de dev]]
- relates_to [[Dados via snapshot CSV versionado]]
- relates_to [[Indicadores do módulo de dados - regras de cálculo]]
- relates_to [[Quality gates no pre-commit]]
