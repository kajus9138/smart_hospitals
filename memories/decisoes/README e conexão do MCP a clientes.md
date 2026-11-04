---
title: README e conexão do MCP a clientes
type: decision
permalink: smart-hospitals/decisoes/readme-e-conexao-do-mcp-a-clientes
tags:
- decisao
- documentacao
- mcp
- ontologia
- task-12
- task-16
---

# README e conexão do MCP a clientes

Origem: task 12, em 2026-10-23.

## Decisão
- O `README.md` é só do smart_hospitals; o texto do template de workflow foi para
  `docs/template-workflow.md`, com link no README.
- Claude Desktop: `"command": "uv", "args": ["--directory", "<caminho>", "run", "dengue-mcp"]`, sem a
  chave `cwd`. Claude Code: `claude mcp add dengue-sp -- uv run --directory "$PWD" dengue-mcp`.
- O exemplo de uso do MCP no README usa saídas reais das tools (snapshot de referência 2026-10-04) e
  não traz previsão numérica nem recomendação de compra.
- Licença não citada: o repositório não tem `LICENSE`; a escolha fica com o responsável.

## Contexto
A task sugeria `cwd` no `claude_desktop_config.json` e um exemplo com números inventados. A
documentação oficial do MCP (via Context7) configura servidores uv com `--directory`, e o exemplo
inventado contradizia [[Indicadores de tendência sem previsão numérica]].

## Alternativas descartadas
- Chave `cwd` no config do Claude Desktop: não aparece na documentação oficial.
- Manter o texto do template no topo do README: confundia quem chega ao repositório do projeto.
- Adicionar LICENSE MIT: decisão do titular, fora do escopo da task.

## Ontologia no README (task 16, PR #23, 2026-11-04)
- Seção "Ontologia para agentes de IA" entre o exemplo de uso do MCP e a estrutura do projeto; carga no
  Claude Code por `@./docs/ontologia/dengue_sp.yaml` no `CLAUDE.md` (sintaxe conferida via Context7:
  caminho relativo ao arquivo que importa; crases e blocos de código não importam).
- "Atualizar a ontologia" diz o que os testes cobrem e o que não: só as evidências de `cobertura` e
  `atraso_notificacao` são conferidas contra o snapshot; as demais (surtos, sazonalidade, Rt) exigem
  revisão manual no notebook. Revisões do InfoDengue nas semanas recentes quebram `atraso_notificacao`
  mesmo sem SE nova.
- Descartado: copiar o texto da task, que citava um teste inexistente (`test_ontologia_validade_snapshot`)
  e prometia mais do que os testes garantem.

## Lição: task-master update-task --append
- O `--append` passa a nota pela IA do task-master, que a reescreve (incluiu números de linha do README) e
  re-serializa o `tasks.json` (ids string ↔ int). Commitar o `tasks.json` em commit `chore` separado.
- `update-subtask` falha em task sem subtarefas; nesses casos usar `update-task --append`.

## Observations
- [decision] Claude Desktop sobe o servidor com `uv --directory <caminho> run dengue-mcp` #mcp
- [convention] Exemplos de saída na documentação vêm de execuções reais das tools #documentacao
- [fact] A URL do Streamlit Cloud responde 303 em loop sem cookies; com cookie jar, 200 #deploy

## Relations
- documents [[MCP server - implementação e erros das tools]]
- relates_to [[Publicação no Streamlit Cloud - dependências pelo uv.lock]]
