---
title: Dashboard Streamlit - decisões de implementação
type: decision
permalink: smart-hospitals/decisoes/dashboard-streamlit-decisoes-de-implementacao
tags:
- decisao
- dashboard
- visualizacao
- task-6
---

# Dashboard Streamlit - decisões de implementação

Origem: task 6, `src/smart_hospitals/dashboard/` em 2026-10-23.

## Decisão
- **Figuras separadas do layout**: `charts.py` tem funções puras que devolvem `go.Figure`, portadas dos
  mockups da seção 6 do notebook e testadas sem Streamlit. `app.py` só monta o layout.
- **Só o aprovado** em `docs/visualizacoes.md` (task 5): série com níveis de alerta (6.1), KPIs com
  `st.metric` (6.2), comparação sazonal (6.3), sparkline (6.4) e medidores Rt/p_rt1 (6.5). O mapa de calor (6.6)
  ficou fora. A data de referência e a SE aparecem no `st.caption` logo abaixo do título.
- **Limiares compartilhados**: `RT_ALTA`, `RT_QUEDA` e `P_RT1_ALTA` ficam em `data/indicators.py`. Tanto
  `calcular_tendencia` quanto os medidores usam essas constantes, para que o medidor não contradiga o rótulo da tendência.
- **Escala do medidor de Rt**: vai até `max(2, ceil(Rt))`. No snapshot, o Rt passa de 2 em 24 semanas (máx. 4,6).
- **Sparkline**: mostra 12 semanas de `casos_est`, mas a tendência vem de `calcular_tendencia` (4 semanas, Rt/p_rt1).
  O título diz "tendência (4 sem.)" para não sugerir que a tendência foi calculada sobre as 12 semanas.
- **Delta dos casos com `delta_color="inverse"`**: aumento de casos aparece em vermelho.
- `st.plotly_chart(fig, width="stretch")`: o `use_container_width` foi removido do Streamlit em 2026.
- **Testes**: `AppTest.from_file` resolve caminho relativo a partir do arquivo de teste, por isso o teste usa caminho
  absoluto. O AppTest executa uma cópia temporária do script, que o coverage não liga ao `app.py`. Por isso o
  `app.py` fica no `omit` do coverage e é coberto pelo smoke test.
- `uv run dashboard` devolve o código de saída do streamlit.

## Alternativas descartadas
- Tudo em `app.py`: as figuras não seriam testáveis e a cobertura dependeria do AppTest.
- Renomear o script para `dengue-dashboard` (sugestão do code review): mantido `dashboard`, como pede a spec da task.

## Limitações conhecidas
- Na comparação sazonal, a SE 53 só existe em 3 anos (2014, 2020, 2025), então a faixa histórica dela é mais pobre.
- `load_snapshot` não valida `nivel` em 1–4. Um nível vazio derrubaria `fig_serie` com `KeyError`. Não ocorre no
  snapshot atual.
- Marcas do eixo log vão de 10 a 100 mil (o mínimo de `casos_est` no snapshot é 38).
- O Streamlit Cloud precisa instalar o pacote `smart_hospitals` (task 8).

## Observations
- [decision] Figuras Plotly em charts.py (puras), layout em app.py #dashboard
- [decision] Limiares de Rt/p_rt1 vivem em indicators.py e são reusados pelos medidores #indicadores
- [decision] Eixo do medidor de Rt se estende além de 2 em surtos #visualizacao
- [fact] AppTest roda uma cópia temporária do script; coverage não mede app.py #testes
- [fact] st.plotly_chart usa width="stretch"; use_container_width foi removido #streamlit

## Relations
- implements [[Portões de aprovação humana do dashboard]]
- depends_on [[Notebook de análise exploratória - decisões]]
- relates_to [[Indicadores do módulo de dados - regras de cálculo]]
- relates_to [[Stack Python e publicação no Streamlit Community Cloud]]
