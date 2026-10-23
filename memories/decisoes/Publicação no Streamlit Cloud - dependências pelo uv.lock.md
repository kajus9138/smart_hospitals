---
title: Publicação no Streamlit Cloud - dependências pelo uv.lock
type: decision
permalink: smart-hospitals/decisoes/publicacao-no-streamlit-cloud-dependencias-pelo-uv.lock
tags:
- decisao
- deploy
- streamlit
- task-8
---

# Publicação no Streamlit Cloud - dependências pelo uv.lock

Origem: task 8, PR #13, em 2026-10-23.

## Decisão
- **Sem `requirements.txt`**: o Community Cloud usa só o primeiro arquivo de dependências que encontra, na ordem
  `uv.lock` > `Pipfile` > `environment.yml` > `requirements.txt` > `pyproject.toml`. Ele procura primeiro na pasta
  do entrypoint e depois na raiz. Com o `uv.lock` na raiz, o ambiente sai dele e o pacote `smart_hospitals` é
  instalado (editável, padrão do `uv sync`). Simulado num clone limpo com `uv sync --locked --no-dev`.
- **Sem `.streamlit/config.toml`**: o `[theme]` da spec mudaria o visual aprovado na task 7. O
  `server.headless` não muda nada no Cloud, que já roda headless, e localmente só impede o navegador de abrir.
- `tests/test_deploy.py` falha se aparecer arquivo de dependências na pasta do `app.py` (teria prioridade sobre o
  `uv.lock`) ou `requirements.txt` na raiz.
- Deploy manual pelo responsável em share.streamlit.io: branch `main`, `src/smart_hospitals/dashboard/app.py`,
  Python 3.12. Passo a passo e checklist no README.

## Alternativas descartadas
- `requirements.txt` na raiz (spec original): seria ignorado por causa do `uv.lock` e ainda trazia versões
  desatualizadas (pandas>=2).
- `requirements.txt` na pasta do app: tem prioridade, mas não instala o pacote local sem `-e .`, cuja
  resolução de caminho é frágil. Fica como plano B.

## Riscos a conferir no primeiro deploy
- `load_snapshot` acha o CSV relativo ao código (`parents[3]/data`). Uma instalação não editável quebraria isso.
- O `uv sync` padrão inclui o grupo `dev` (Jupyter etc.), o que deixa o build mais lento.

## Observations
- [decision] Cloud instala pelo uv.lock da raiz; sem requirements.txt #deploy
- [decision] Sem .streamlit/config.toml; tema padrão aprovado #deploy
- [fact] Streamlit Cloud prioriza uv.lock sobre requirements.txt e a pasta do entrypoint sobre a raiz #streamlit
- [risk] SNAPSHOT_PATH depende de instalação editável #deploy

## Relations
- implements [[Stack Python e publicação no Streamlit Community Cloud]]
- depends_on [[Portões de aprovação humana do dashboard]]
- relates_to [[Dashboard Streamlit - decisões de implementação]]
