---
title: Notebook de análise exploratória - decisões
type: decision
permalink: smart-hospitals/decisoes/notebook-de-analise-exploratoria-decisoes
tags:
- decisao
- notebook
- visualizacao
- task-4
---

# Notebook de análise exploratória - decisões

Origem: task 4, `notebooks/analise_dengue_sp.ipynb` e `docs/visualizacoes.md`, em 2026-10-22.

## Decisão
- **Notebook versionado com saídas** para o responsável revisar no GitHub sem executar. Passa de 500 KB
  (~950 KB), então foi excluído do `check-added-large-files` no pre-commit, como o `uv.lock`.
- **matplotlib/seaborn na análise** (PNG estático, renderiza no GitHub); **Plotly só nos mockups** da
  seção 6, com renderer `notebook_connected` (plotly.js via CDN, não embutido). Os mockups só aparecem no Jupyter.
- **Escala log** na série e no heatmap: 2024 teve ~1,26 mi casos estimados contra 8 a 85 mil nos outros
  anos; em escala linear o surto apaga o resto. O mockup da série principal abre nos últimos 3 anos.
- **Comparação sazonal com mediana** no mockup (média por SE é puxada pelos surtos). O
  `comparativo_sazonal` do módulo usa média: o dashboard deve usar a mesma estatística no gráfico e no card.
- **Banda do nowcast só nas semanas com intervalo** (`casos_est_max > casos_est_min`), desenhada como
  um polígono (`fill="toself"`) por trecho contínuo. No snapshot, só as 10 últimas SEs (202631 a 202640)
  têm intervalo; nas consolidadas min = max = `casos_est` ou o max vem vazio (2015, 2024, 2025). A
  primeira versão usava `fill="tonexty"` sobre a série inteira, e as lacunas do max deixavam a banda
  estranha em 2024/2025. O dashboard (task 6) deve seguir a mesma regra.
- **Spearman calculado como Pearson sobre postos**: `Series.corr(method="spearman")` exige scipy, que
  não é dependência. Crescimento calculado na série completa e só depois filtrado (Rt = 0 nas 5 primeiras SEs de 2010).
- **Teste de integração** (`tests/integration/test_notebook.py`, marker `integration`) executa o notebook
  com nbclient (~6 s); `nbclient`, `nbformat` e `ipykernel` declarados no grupo dev.

## Achados (snapshot até SE 202640)
- SEs 10 a 19 concentram ~44% dos casos do ano (mediana dos anos completos).
- Rt e p_rt1 têm correlação de Spearman ≈ 0,3 a 0,44 com o crescimento dos casos 1 a 8 semanas depois,
  maior entre 3 e 5 semanas.
- Na última semana, 352 notificados contra 1.161 estimados: atraso de notificação reforça o uso do nowcast.

## Alternativas descartadas
- Notebook sem saídas (limpo): o revisor teria de executar para aprovar.
- Reduzir dpi/figuras para caber em 500 KB: só chegou a ~775 KB e piorava a leitura.
- Adicionar scipy só para o Spearman.
- Pizza como único gráfico de distribuição de alertas: mantida, mas acompanhada de barras empilhadas por ano.

## Limitações conhecidas
- Os números citados no texto do notebook são do snapshot atual; após atualizar o CSV, reexecutar e revisar.
- O teste usa o kernelspec `python3`; um kernelspec de usuário com esse nome apontando para outro Python
  sombrearia o do `.venv`.

## Observations
- [decision] Notebook de análise versionado com saídas, fora do limite de 500 KB do pre-commit #notebook
- [decision] Escala log em séries de casos por causa do surto de 2024 #visualizacao
- [decision] Comparação sazonal deve usar a mesma estatística no gráfico e no card #visualizacao
- [fact] Intervalo do nowcast só existe nas semanas recentes; consolidadas têm min = max ou max vazio #infodengue
- [convention] Banda de incerteza só onde max > min, um polígono por trecho contínuo #visualizacao
- [fact] SEs 10-19 concentram ~44% dos casos anuais em SP #sazonalidade
- [fact] Rt/p_rt1 antecipam o crescimento em 3-5 semanas (Spearman ~0,4) #indicadores

## Relations
- implements [[Portões de aprovação humana do dashboard]]
- relates_to [[Indicadores do módulo de dados - regras de cálculo]]
- relates_to [[Indicadores de tendência sem previsão numérica]]
