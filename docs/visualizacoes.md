# Visualizações Aprovadas para o Dashboard

Portão de aprovação humana 1: marque as visualizações que devem entrar no dashboard. A implementação
(task 6) só começa depois que este arquivo estiver preenchido. As propostas, os achados que as
justificam e os mockups estão na seção 6 de
[`notebooks/analise_dengue_sp.ipynb`](../notebooks/analise_dengue_sp.ipynb) (os mockups Plotly só
aparecem abrindo o notebook no Jupyter).

## Aprovado por: Kaique
## Data: 2026-10-23

### Visualizações selecionadas:
- [x] Série temporal principal com níveis de alerta — `casos_est` com intervalo do nowcast, faixas
  pelo nível de alerta, escala log e seletor de período (notebook 6.1)
- [x] Card de situação atual (KPIs) — casos estimados e variação semanal, nível de alerta, Rt,
  incidência por 100 mil (notebook 6.2)
- [x] Gráfico de comparação sazonal — ano corrente sobre a mediana e a faixa mín.–máx. dos anos
  anteriores, por SE (notebook 6.3)
- [x] Mini-gráfico de tendência recente — sparkline das últimas 12 semanas com o rótulo
  alta / estável / queda (notebook 6.4)
- [x] Indicadores Rt e probabilidade de transmissão em crescimento — dois medidores lado a lado:
  Rt com faixas de queda / estável / alta e p_rt1 de 0 a 100% com destaque acima de 70%
  (notebook 6.5)
- [ ] Mapa de calor histórico — SE × ano em escala log, opcional (notebook 6.6)

### Observações:
[Comentários do responsável]
