---
title: Quality gates no pre-commit
type: decision
permalink: smart-hospitals/decisoes/quality-gates-no-pre-commit
tags:
- decisao
- qualidade
- pre-commit
---

# Quality gates no pre-commit

Origem: task 11 (PR #16), 2026-10-23.

## Decisão
- Os gates de qualidade ficam **só no pre-commit**, sem GitHub Actions na fase 1.
- Hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-toml,
  check-added-large-files (`--maxkb=500`, com exceção para uv.lock e o notebook),
  ruff-check (`--fix --exit-non-zero-on-fix`), ruff-format, block-main, mypy e pytest.
- mypy e pytest rodam como hooks `local` via `uv run`, para usar o ambiente do projeto.
- A cobertura mínima (80%) vem do `[tool.coverage.report] fail_under` no pyproject, sem
  `--cov-fail-under` repetido no hook.
- Ruff: regras E, F, W, I, N, UP, B, C4, SIM e RUF, com isort
  `known-first-party = ["smart_hospitals"]`.
- Por causa da regra N818, exceções terminam em `Error` (`ParametroInvalido` virou
  `ParametroInvalidoError`).

## Contexto
O `.pre-commit-config.yaml` já existia, mas o hook nunca tinha sido instalado
(`.git/hooks/pre-commit` não existia), então nenhum commit passava pelos gates. O
`pre-commit install` é local e não vai para o Git: cada clone precisa rodá-lo, como o
README já indica.

## Alternativas descartadas
- GitHub Actions: fora do escopo da task 11 por decisão do responsável; pode virar outra
  tarefa.
- Itens do detalhamento original: ruff v0.4.4 e hook id `ruff` estão desatualizados (o
  atual é `ruff-check` v0.17.1). `asyncio_mode = "auto"` não se aplica porque o projeto
  usa anyio. O override do mypy para streamlit/mcp é desnecessário porque as duas libs são
  tipadas.
- Ignorar N818: preferimos renomear a exceção.

## Observations
- [decision] Gates de qualidade só no pre-commit na fase 1, sem CI #pre-commit
- [convention] Exceções terminam com sufixo Error (ruff N818) #convencao
- [fact] pre-commit install é local; cada clone precisa rodar #pre-commit
- [convention] Cobertura mínima definida uma vez, no fail_under do pyproject #testes

## Relations
- part_of [[Observabilidade e qualidade da fase 1]]
- relates_to [[MCP server - implementação e erros das tools]]
- relates_to [[Dados via snapshot CSV versionado]]
