# Template de workflow com Claude Code

Ponto de partida para novos projetos: PRD → backlog no Task Master → uma branch por tarefa →
plano aprovado → implementação → revisão → PR → decisões registradas no Basic Memory.

O guia completo, com o porquê de cada peça, está em `docs/guia-dev-workflow-claude-code.pdf`.

## Criar um projeto novo

```bash
scripts/new-project.sh ~/projetos/meu-app            # nome do projeto = nome da pasta
scripts/new-project.sh ~/projetos/meu-app meu_app    # ou um nome explícito
```

O script copia o template (sem histórico, segredos, memórias nem tarefas), registra o projeto
no Basic Memory, cria o `.env`, roda `git init -b main`, instala o pre-commit e faz o commit
inicial. Se você clonou o template por outro caminho (ex.: `gh repo create --template`),
rode só `scripts/setup.sh` na raiz do projeto novo.

## O que vem no template

| Arquivo | Papel |
|---|---|
| `CLAUDE.md` | Regras que o Claude Code carrega em toda sessão; importa o `dev-workflow.md` |
| `dev-workflow.md` | O passo a passo por tarefa. Preencha as convenções e os comandos do projeto |
| `.mcp.json` | MCPs do projeto: Task Master e Basic Memory |
| `.claude/settings.json` | Permissões: bloqueia `--no-verify`, push forçado e leitura do `.env` |
| `.pre-commit-config.yaml` | Bloqueia commit na `main` + checagens básicas; ative o hook de testes |
| `.taskmaster/` | Config do Task Master (claude-code + Perplexity) e template de PRD |
| `memories/` | Base do Basic Memory, versionada no Git |
| `scripts/` | `new-project.sh` e `setup.sh` |

## Pré-requisitos (uma vez por máquina)

Node 18+, `uv`, `git`, `gh` autenticado, Claude Code, e:

```bash
npm install -g task-master-ai
uv tool install basic-memory
uv tool install pre-commit
claude mcp add --scope user context7 -- npx -y @upstash/context7-mcp
```

## Desenvolvimento (smart_hospitals)

Python 3.12 gerenciado com `uv`. Código em `src/smart_hospitals/` (`data/` é o módulo compartilhado
entre `dashboard/` e `mcp_server/`); testes em `tests/`.

```bash
uv sync                                   # cria o .venv com dependências de produção e dev
uv run pytest --cov                       # testes (cobertura mínima de 80%)
uv run pytest -m "not integration"        # pula os testes que sobem o MCP via stdio
uv run ruff check . && uv run mypy .      # lint e tipos
uv run ruff format .                      # formatação
pre-commit install                        # hooks: ruff, mypy, testes e bloqueio da main
```

### Atualizar o snapshot de dados

Dashboard, MCP server e testes leem apenas `data/dengue_sp_snapshot.csv` (série semanal de dengue
de São Paulo capital desde a SE 1/2010, todas as colunas da API `alertcity` do InfoDengue). Para
atualizá-lo, sob demanda:

```bash
uv run python scripts/extract_infodengue.py   # opções: --output CAMINHO, --ey-end ANO
```

O script registra em stderr quantas semanas baixou, o intervalo de SEs e o tamanho do arquivo.
Revise o diff do CSV e faça o commit.

### Módulo de dados

`smart_hospitals.data` lê o snapshot e calcula os indicadores usados pelo dashboard e pelo MCP:

```python
from smart_hospitals.data import (
    calcular_situacao_atual, calcular_tendencia, comparativo_sazonal, load_snapshot, serie_historica,
)

df = load_snapshot()                              # valida colunas e ordena por SE
calcular_situacao_atual(df)                       # última SE: nowcast, nível, Rt, variação semanal
calcular_tendencia(df, semanas=4)                 # alta / estavel / queda pelas médias de Rt e p_rt1
serie_historica(df, "2024-01-01", "2024-12-31")   # ou por SE: serie_historica(df, 202401, 202452)
comparativo_sazonal(df)                           # mesma SE nos anos anteriores
```

Séries e comparativos saem prontos para JSON (datas ISO, valores ausentes como `None`).

### MCP server

Servidor MCP local (SDK `mcp` v2, transporte stdio, somente leitura) que expõe os indicadores para
agentes de IA. Toda resposta traz `data_referencia`, a semana mais recente do snapshot.

| Tool | Parâmetros | Retorno |
|---|---|---|
| `situacao_atual` | - | casos notificados, `casos_est` (mín./máx.), incidência/100 mil, nível, Rt, p_rt1, variação semanal |
| `tendencia` | `semanas` (1-52, padrão 4) | indicadores das últimas N semanas + `alta` / `estavel` / `queda` |
| `serie_historica` | `inicio`, `fim` (SE `202401` ou data `2024-01-01`) | série semanal no intervalo |
| `comparativo_sazonal` | `semana` (1-53, padrão: a mais recente) | mesma SE nos anos anteriores (média, mín., máx.) |

```bash
uv run dengue-mcp                                          # ou: uv run python -m smart_hospitals.mcp_server
claude mcp add dengue-sp -- uv run --directory "$PWD" dengue-mcp   # registrar no Claude Code
```

Para inspecionar as tools no navegador: `uv run mcp dev src/smart_hospitals/mcp_server/server.py`.
Cada chamada é registrada em stderr (tool, parâmetros, duração e status); o stdout é do protocolo.
O snapshot é carregado uma vez, na inicialização: depois de atualizar o CSV, reinicie o servidor.
