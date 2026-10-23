# Smart Hospitals - Dashboard Epidemiológico Dengue SP

Dashboard e MCP server para o monitoramento epidemiológico da dengue no município de São Paulo, com
dados públicos do [InfoDengue](https://info.dengue.mat.br/). O dashboard serve às pessoas; o MCP
server expõe os mesmos indicadores a agentes de IA (Claude Desktop, Claude Code ou outro cliente MCP).

Dashboard publicado: [Dengue SP - Smart Hospitals](https://smarthospitals-ves4qyrifjnibfba9uxikl.streamlit.app/)

## Requisitos

- Python 3.12
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes; instala o Python 3.12 se faltar)
- `pre-commit` (`uv tool install pre-commit`), só para quem vai fazer commits

## Instalação

```bash
git clone https://github.com/kajus9138/smart_hospitals.git
cd smart_hospitals
uv sync             # cria o .venv com dependências de produção e dev
pre-commit install  # hooks: ruff, mypy, testes e bloqueio da main
```

## Desenvolvimento

Código em `src/smart_hospitals/` (`data/` é o módulo compartilhado entre `dashboard/` e
`mcp_server/`); testes em `tests/`.

```bash
uv run pytest --cov                       # todos os testes, com cobertura (mínimo de 80%)
uv run pytest tests/data/                 # só o módulo de dados
uv run pytest -v                          # saída detalhada
uv run pytest -m "not integration"        # pula MCP via stdio e execução do notebook
uv run ruff check . && uv run mypy .      # lint e tipos
uv run ruff format .                      # formatação
```

O fluxo de trabalho por tarefa (Task Master, branches, revisão, Basic Memory) está em
`dev-workflow.md`; a origem desse fluxo, o template de projeto, em
[`docs/template-workflow.md`](docs/template-workflow.md).

### Atualizar o snapshot de dados

Dashboard, MCP server e testes leem apenas `data/dengue_sp_snapshot.csv` (série semanal de dengue
de São Paulo capital desde a SE 1/2010, todas as colunas da API `alertcity` do InfoDengue). Para
atualizá-lo, sob demanda:

```bash
uv run python scripts/extract_infodengue.py   # opções: --output CAMINHO, --ey-end ANO
```

O script registra em stderr quantas semanas baixou, o intervalo de SEs e o tamanho do arquivo, e
sobrescreve o CSV. Revise o diff do CSV e faça o commit.

### Módulo de dados

`smart_hospitals.data` lê o snapshot e calcula os indicadores usados pelo dashboard e pelo MCP:

```python
from smart_hospitals.data import (
    calcular_situacao_atual,
    calcular_tendencia,
    comparativo_sazonal,
    load_snapshot,
    serie_historica,
)

df = load_snapshot()  # valida colunas e ordena por SE
calcular_situacao_atual(df)  # última SE: nowcast, nível, Rt, variação semanal
calcular_tendencia(df, semanas=4)  # alta / estavel / queda pelas médias de Rt e p_rt1
serie_historica(df, "2024-01-01", "2024-12-31")  # ou por SE: serie_historica(df, 202401, 202452)
comparativo_sazonal(df)  # mesma SE nos anos anteriores
```

Séries e comparativos saem prontos para JSON (datas ISO, valores ausentes como `None`).

### Análise exploratória

`notebooks/analise_dengue_sp.ipynb` analisa o snapshot (série, sazonalidade, Rt, alertas, últimas 12
semanas) e propõe as visualizações do dashboard. Fica versionado com as saídas, para revisão no
GitHub; os mockups Plotly da seção 6 só aparecem no Jupyter. A escolha do responsável vai em
`docs/visualizacoes.md`, que libera a implementação do dashboard.

```bash
uv run jupyter lab notebooks/analise_dengue_sp.ipynb                         # explorar
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/analise_dengue_sp.ipynb
```

Depois de atualizar o snapshot, reexecute com o segundo comando e revise os números citados no texto.

## Dashboard

`src/smart_hospitals/dashboard/` mostra só as visualizações aprovadas em `docs/visualizacoes.md`,
com a data de referência (e a SE) no cabeçalho. As figuras Plotly ficam em `charts.py` e o layout
Streamlit em `app.py`.

```bash
uv run dashboard                  # ou: uv run streamlit run src/smart_hospitals/dashboard/app.py
uv run pytest tests/dashboard -v  # smoke test (AppTest) e testes das figuras
```

O dashboard abre em http://localhost:8501.

### Publicação no Streamlit Community Cloud

O Cloud usa o primeiro arquivo de dependências que encontra (`uv.lock` vem antes de
`requirements.txt`), então instala o ambiente pelo `uv.lock` da raiz, inclusive o pacote
`smart_hospitals`. Não crie arquivo de dependências na raiz nem na pasta do `app.py`: um
`requirements.txt` na raiz seria ignorado e, na pasta do app, qualquer um deles teria prioridade sem
instalar o pacote (`tests/test_deploy.py` verifica isso). Também não há `.streamlit/config.toml`: o
dashboard usa o tema padrão aprovado na task 7. Não há secrets: os
dados vêm do snapshot versionado.

Primeira publicação (manual, feita pelo responsável):

1. Entrar em https://share.streamlit.io com a conta do GitHub dona do repositório.
2. **Create app** → **Deploy a public app from GitHub**.
3. Repositório `kajus9138/smart_hospitals`, branch `main`, arquivo principal
   `src/smart_hospitals/dashboard/app.py`.
4. Em **Advanced settings**, Python **3.12**. A versão do Python só muda apagando e republicando o app.
5. **Deploy** e acompanhar o log do build.

Depois disso, cada merge na `main` republica o app sozinho. Para atualizar os dados, basta
atualizar o snapshot (seção acima) e fazer o merge.

Se algo falhar, leia o log do build antes de mudar o formato. Pontos a conferir no primeiro deploy:

- `load_snapshot` acha o CSV por caminho relativo ao código (`data/` na raiz do repositório). Isso
  exige instalação editável, que é o padrão do `uv sync`. Um `FileNotFoundError` no app indica que o
  Cloud instalou o pacote em `site-packages`.
- O `uv sync` padrão também instala o grupo `dev` (Jupyter, ruff, mypy...). Se o build ficar lento ou
  estourar recursos, vale tirar o grupo `dev` do padrão no `pyproject.toml`.
- Plano B: um `requirements.txt` com as dependências do `pyproject.toml` mais o próprio pacote;
  nesse caso, ajuste `tests/test_deploy.py`.

Checklist após cada publicação:

- [ ] A URL responde HTTP 200.
- [ ] Com o app acordado, a página carrega em menos de 5 s (o despertar do plano gratuito não conta).
- [ ] Série com níveis de alerta, KPIs, sparkline, comparação sazonal e medidores de Rt/p_rt1
      aparecem sem erro.
- [ ] A data de referência e a SE do cabeçalho batem com a última semana do snapshot.
- [ ] A página funciona no Chrome, no Firefox e no Safari (ou no navegador do celular).

## MCP server

Servidor MCP local (SDK `mcp` v2, transporte stdio, somente leitura) que expõe os indicadores para
agentes de IA. Toda resposta traz `data_referencia`, a semana mais recente do snapshot. Não há
previsão numérica de casos: a tendência se avalia por Rt, p_rt1, nível de alerta e `casos_est`
(nowcast, com intervalo).

| Tool | Parâmetros | Retorno |
|---|---|---|
| `situacao_atual` | - | casos notificados, `casos_est` (mín./máx.), incidência/100 mil, nível, Rt, p_rt1, variação semanal |
| `tendencia` | `semanas` (1-52, padrão 4) | indicadores das últimas N semanas + `alta` / `estavel` / `queda` |
| `serie_historica` | `inicio`, `fim` (SE `202401` ou data `2024-01-01`) | série semanal no intervalo |
| `comparativo_sazonal` | `semana` (1-53, padrão: a mais recente) | mesma SE nos anos anteriores (média, mín., máx.) |

```bash
uv run dengue-mcp   # ou: uv run python -m smart_hospitals.mcp_server
```

O servidor fala pelo stdin/stdout, então quem o inicia é o cliente MCP; rodá-lo à mão só serve para
ver se sobe. Para inspecionar as tools no navegador: `uv run mcp dev src/smart_hospitals/mcp_server/server.py`.
Cada chamada é registrada em stderr (tool, parâmetros, duração e status); o stdout é do protocolo.
O snapshot é carregado uma vez, na inicialização: depois de atualizar o CSV, reinicie o servidor
(no Claude Desktop, reinicie o app).

### Conectar ao Claude Code

Na raiz do repositório:

```bash
claude mcp add dengue-sp -- uv run --directory "$PWD" dengue-mcp
```

### Conectar ao Claude Desktop

1. Abra o arquivo de configuração do Claude Desktop (em **Settings → Developer → Edit Config**, ou
   direto no caminho):
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`
2. Acrescente o servidor em `mcpServers`, trocando `/CAMINHO/ABSOLUTO/smart_hospitals` pelo caminho
   do clone (`pwd` na raiz do repositório; no Windows, use `/` ou `\\` no caminho):

   ```json
   {
     "mcpServers": {
       "dengue-sp": {
         "command": "uv",
         "args": ["--directory", "/CAMINHO/ABSOLUTO/smart_hospitals", "run", "dengue-mcp"]
       }
     }
   }
   ```

   O Claude Desktop não herda o `PATH` do terminal: se o servidor não aparecer, troque `"uv"` pelo
   caminho absoluto (`which uv`; no Windows, `where uv`).
3. Reinicie o Claude Desktop (saia do app, não basta fechar a janela). O servidor `dengue-sp` deve
   aparecer entre as ferramentas da conversa com as quatro tools: `situacao_atual`, `tendencia`, `serie_historica` e `comparativo_sazonal`. Os logs do
   servidor ficam em `mcp-server-dengue-sp.log`, na pasta de logs do Claude Desktop.

### Exemplo de uso

Pergunta: "Como está a tendência da dengue em São Paulo?"

O agente chama `situacao_atual`, `tendencia` e `comparativo_sazonal`. Com o snapshot de referência
2026-10-04 (SE 40/2026), as tools devolvem, entre outros campos (valores arredondados):

```json
{"nivel_alerta": "laranja", "casos_est": 1161.0, "casos_est_min": 582.0, "casos_est_max": 3114.0,
 "rt": 0.98, "p_rt1": 0.34, "variacao_semanal": -13.6}
{"tendencia_resumo": "alta", "rt_medio": 1.1, "p_rt1_medio": 0.73}
{"semana_epidemiologica": 40, "ano_atual": 1161, "media_historica": 549.9, "anos_comparados": 16}
```

E a resposta fica assim:

> Na semana de 4/10/2026 (SE 40), São Paulo está em alerta laranja, com cerca de 1.161 casos
> estimados (intervalo de 582 a 3.114), o dobro da média da mesma semana nos 16 anos anteriores
> (550). Nas últimas 4 semanas o Rt médio foi 1,1, com 73% de probabilidade de Rt > 1, e o
> indicador de tendência é de **alta**. Na semana mais recente, porém, o Rt caiu para 0,98 e os casos
> estimados recuaram 13,6%: vale acompanhar as próximas semanas antes de concluir que a alta
> perdeu força.

## Estrutura do projeto

```
smart_hospitals/
├── src/smart_hospitals/
│   ├── data/          # módulo de dados compartilhado (snapshot e indicadores)
│   ├── dashboard/     # aplicação Streamlit (app.py, charts.py)
│   └── mcp_server/    # MCP server (stdio)
├── data/              # snapshot CSV do InfoDengue
├── notebooks/         # análise exploratória
├── tests/             # pytest: data, dashboard, mcp_server, scripts, integration
├── scripts/           # extract_infodengue.py e scripts do template (new-project.sh, setup.sh)
├── docs/              # visualizações aprovadas e guia do fluxo de trabalho
└── memories/          # decisões do projeto (Basic Memory)
```

## Dados

Os dados vêm da API pública do [InfoDengue](https://info.dengue.mat.br/) (endpoint `alertcity`),
projeto da Fiocruz e da FGV:

- Município: São Paulo (IBGE 3550308)
- Doença: dengue
- Período: da semana epidemiológica 1/2010 até a mais recente disponível
- Atualização: manual, sob demanda (veja [Atualizar o snapshot de dados](#atualizar-o-snapshot-de-dados))
