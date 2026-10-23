"""Dashboard da dengue em São Paulo com as visualizações aprovadas em docs/visualizacoes.md.

Executar com: uv run streamlit run src/smart_hospitals/dashboard/app.py
"""

import pandas as pd
import streamlit as st

from smart_hospitals.dashboard.charts import (
    fig_medidores,
    fig_sazonal,
    fig_serie,
    fig_sparkline,
    fmt_int,
    preparar,
    texto_nivel_alerta,
)
from smart_hospitals.data import (
    calcular_situacao_atual,
    calcular_tendencia,
    get_reference_date,
    load_snapshot,
)

st.set_page_config(page_title="Dengue SP - Smart Hospitals", page_icon="🏥", layout="wide")


@st.cache_data(ttl=3600)
def load_data() -> pd.DataFrame:
    return preparar(load_snapshot())


df = load_data()
data_ref = get_reference_date(df)
situacao = calcular_situacao_atual(df)
tendencia = calcular_tendencia(df)

st.title("Dashboard Epidemiológico - Dengue São Paulo")
st.caption(
    f"📅 Data de referência: {data_ref.strftime('%d/%m/%Y')} "
    f"(Semana Epidemiológica {df.iloc[-1]['SE']})"
)

# Situação atual (KPIs) em grade 2x2, para os rótulos caberem inteiros, e tendência recente ao lado
kpis, spark = st.columns([2, 1])
with kpis:
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    c1.metric(
        "Casos estimados na semana",
        fmt_int(situacao.casos_est),
        delta=f"{situacao.variacao_semanal:+.1f}".replace(".", ",") + "% vs. semana anterior",
        delta_color="inverse",  # aumento de casos é ruim
        help=f"Nowcast do InfoDengue; notificados até agora: {fmt_int(situacao.casos_notificados)}",
        border=True,
    )
    c2.metric(
        "Nível de alerta",
        texto_nivel_alerta(situacao.nivel_alerta),
        help="Nível do InfoDengue: verde, amarelo, laranja ou vermelho",
        border=True,
    )
    c3.metric("Rt", f"{situacao.rt:.2f}".replace(".", ","), border=True)
    c4.metric(
        "Incidência por 100 mil hab.",
        f"{situacao.incidencia_100k:.1f}".replace(".", ","),
        border=True,
    )
with spark:
    # sem barra de ferramentas: ela cobriria o título com a tendência
    st.plotly_chart(
        fig_sparkline(df, tendencia.tendencia_resumo),
        width="stretch",
        config={"displayModeBar": False},
    )

st.plotly_chart(fig_serie(df), width="stretch")

sazonal, medidores = st.columns(2)
with sazonal:
    st.plotly_chart(fig_sazonal(df), width="stretch")
with medidores:
    st.plotly_chart(fig_medidores(situacao), width="stretch")
