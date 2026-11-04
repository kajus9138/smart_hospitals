---
title: PyYAML e stubs como dependências de dev
type: decision
permalink: smart-hospitals/decisoes/py-yaml-e-stubs-como-dependencias-de-dev
tags:
- decisao
- dependencias
- mypy
- task-15
---

# PyYAML e stubs como dependências de dev

Origem: task 15, em 2026-11-04.

## Decisão
- `pyyaml>=6.0` declarado explicitamente no grupo `dev` do `pyproject.toml` (antes vinha só como
  dependência transitiva, via jupyter/mcp). Fica em `dev` porque só os testes de validação da
  ontologia (`docs/ontologia/dengue_sp.yaml`, task 14) leem YAML; o app e o MCP server não.
- `types-PyYAML` também no grupo `dev`. A spec tratava os stubs como opcionais ("se der erro"), mas
  o erro foi reproduzido: com `mypy --strict`, `import yaml` falha com
  `Library stubs not installed for "yaml" [import-untyped]`. Como o mypy verifica `tests/`, o hook
  do pre-commit quebraria na task 14 sem os stubs.
- Adicionados com `uv add --dev`, que atualiza o `uv.lock`. O deploy não muda: o Streamlit Cloud
  instala pelo `uv.lock`, que já inclui o grupo `dev`.

## Alternativas descartadas
- Depender da instalação transitiva: frágil se jupyter/mcp deixarem de puxar o pyyaml.
- Override `ignore_missing_imports` para `yaml` no mypy: perde a checagem de tipos, e existem stubs
  oficiais (typeshed).
- pyyaml em dependências de produção: nenhum código de runtime usa YAML.

## Observations
- [decision] pyyaml e types-PyYAML no grupo dev, não em produção #dependencias
- [fact] mypy strict exige types-PyYAML para `import yaml` #mypy
- [convention] Libs sem tipagem própria entram com o pacote de stubs, não com ignore_missing_imports #mypy

## Relations
- relates_to [[Quality gates no pre-commit]]
- relates_to [[Publicação no Streamlit Cloud - dependências pelo uv.lock]]
- relates_to [[Stack Python e publicação no Streamlit Community Cloud]]
