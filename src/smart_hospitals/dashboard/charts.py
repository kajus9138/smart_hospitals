"""Figuras Plotly do dashboard, uma por visualização aprovada em docs/visualizacoes.md.

Portadas dos mockups da seção 6 de notebooks/analise_dengue_sp.ipynb.
"""

import math
from typing import cast

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from smart_hospitals.data.indicators import (
    LEVEL_MAP,
    P_RT1_ALTA,
    RT_ALTA,
    RT_QUEDA,
    AlertLevel,
    SituacaoAtual,
    Trend,
)

LEVEL_COLORS: dict[AlertLevel, str] = {
    "verde": "#2e7d32",
    "amarelo": "#f9a825",
    "laranja": "#ef6c00",
    "vermelho": "#c62828",
}
LEVEL_NAMES: list[AlertLevel] = [LEVEL_MAP[n] for n in sorted(LEVEL_MAP)]
TREND_LABELS: dict[Trend, str] = {"alta": "alta", "estavel": "estável", "queda": "queda"}

SPARKLINE_WEEKS = 12
TENDENCIA_WEEKS = 4  # janela padrão de calcular_tendencia
P_RT1_LIMIAR = round(P_RT1_ALTA * 100)  # em %, como no medidor
RT_ESCALA_MIN = 2.0  # o eixo do medidor de Rt cresce além disso quando o Rt passa de 2 (surtos)


def fmt_int(valor: float) -> str:
    """Inteiro com separador de milhar brasileiro (1.234)."""
    return f"{valor:,.0f}".replace(",", ".")


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta ano, semana e nome do nível de alerta ao snapshot (sem alterar o original)."""
    out = df.copy()
    out["ano"] = out["SE"] // 100
    out["semana"] = out["SE"] % 100
    out["nivel_nome"] = out["nivel"].map(LEVEL_MAP)
    return out


def faixas_de_nivel(dados: pd.DataFrame) -> pd.DataFrame:
    """Trechos contínuos com o mesmo nível de alerta (início, fim exclusivo, nível)."""
    trecho = (dados["nivel"] != dados["nivel"].shift()).cumsum()
    faixas = dados.groupby(trecho).agg(
        inicio=("data_iniSE", "first"), ultima=("data_iniSE", "last"), nivel=("nivel_nome", "first")
    )
    faixas["fim"] = faixas["ultima"] + pd.Timedelta(days=7)
    return faixas.drop(columns="ultima").reset_index(drop=True)


def eixo_casos_log(fig: go.Figure) -> None:
    """Eixo y em log com marcas legíveis (100, 1 mil, 10 mil...) e números no formato brasileiro."""
    marcas = [10, 30, 100, 300, 1_000, 3_000, 10_000, 30_000, 100_000]
    rotulos = [f"{v // 1000} mil" if v >= 1000 else str(v) for v in marcas]
    fig.update_yaxes(
        type="log", tickvals=marcas, ticktext=rotulos, title="Casos por semana (escala logarítmica)"
    )
    fig.update_layout(separators=",.")  # decimal com vírgula e milhar com ponto, também no hover


def fig_serie(dados: pd.DataFrame) -> go.Figure:
    """Série de casos_est com faixas por nível de alerta e intervalo do nowcast (6.1)."""
    fig = go.Figure()
    # Faixas de vrect não entram na legenda: um marcador vazio por nível faz esse papel.
    for nome in LEVEL_NAMES:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                name=nome,
                marker={
                    "symbol": "square",
                    "size": 14,
                    "color": LEVEL_COLORS[nome],
                    "opacity": 0.4,
                },
                legendgroup="alerta",
                legendgrouptitle_text="Nível de alerta",
            )
        )
    for f in faixas_de_nivel(dados).itertuples():
        cor = LEVEL_COLORS[cast(AlertLevel, f.nivel)]
        fig.add_vrect(x0=f.inicio, x1=f.fim, fillcolor=cor, opacity=0.2, line_width=0)
    # O InfoDengue só informa intervalo nas semanas de nowcast (as mais recentes); nas consolidadas
    # min = max = casos_est ou max vem vazio. A banda é um polígono por trecho contínuo de semanas
    # com intervalo, para não ligar trechos separados por lacunas.
    com_intervalo = dados["casos_est_max"] > dados["casos_est_min"]
    intervalo_txt = np.where(
        com_intervalo,
        " ("
        + dados["casos_est_min"].map(fmt_int)
        + " a "
        + dados["casos_est_max"].map(fmt_int)
        + ")",
        "",
    )
    trechos = dados[com_intervalo].groupby((~com_intervalo).cumsum()[com_intervalo])
    for i, (_, t) in enumerate(trechos):
        fig.add_trace(
            go.Scatter(
                x=pd.concat([t["data_iniSE"], t["data_iniSE"][::-1]]),
                y=pd.concat([t["casos_est_max"], t["casos_est_min"][::-1]]),
                fill="toself",
                fillcolor="rgba(0,0,0,0.15)",
                line_width=0,
                hoverinfo="skip",
                name="intervalo do nowcast (semanas recentes)",
                legendgroup="intervalo",
                showlegend=i == 0,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=dados["data_iniSE"],
            y=dados["casos_est"],
            name="casos estimados",
            line={"color": "black", "width": 1.5},
            customdata=np.column_stack([dados["SE"], dados["nivel_nome"], intervalo_txt]),
            hovertemplate=(
                "SE %{customdata[0]}<br>%{y:,.0f} casos%{customdata[2]}<br>nível %{customdata[1]}"
            ),
        )
    )
    ultima = dados["data_iniSE"].iloc[-1]
    fig.update_xaxes(
        type="date",  # explícito: os marcadores da legenda vêm antes da série e não têm datas
        range=[ultima - pd.DateOffset(years=3), ultima],
        rangeslider_visible=True,
        rangeselector={
            "buttons": [
                {"count": 6, "label": "6m", "step": "month", "stepmode": "backward"},
                {"count": 1, "label": "1a", "step": "year", "stepmode": "backward"},
                {"count": 3, "label": "3a", "step": "year", "stepmode": "backward"},
                {"step": "all", "label": "tudo"},
            ]
        },
    )
    eixo_casos_log(fig)
    fig.update_layout(
        title="Casos estimados de dengue — São Paulo", height=480, hovermode="x unified"
    )
    return fig


def fig_sazonal(dados: pd.DataFrame) -> go.Figure:
    """Ano de referência sobre a mediana e a faixa mín. a máx. dos anos anteriores, por SE (6.3).

    Mesma base de comparativo_sazonal (só anos anteriores ao da SE mais recente), mas com mediana:
    a média por semana é puxada pelos surtos (2024).
    """
    ano_ref = int(dados["ano"].iloc[-1])
    anteriores = dados[dados["ano"] < ano_ref]
    faixa = anteriores.groupby("semana")["casos_est"].agg(["min", "median", "max"])
    atual = dados[dados["ano"] == ano_ref].set_index("semana")["casos_est"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=faixa.index, y=faixa["max"], line_width=0, showlegend=False, hoverinfo="skip")
    )
    fig.add_trace(
        go.Scatter(
            x=faixa.index,
            y=faixa["min"],
            fill="tonexty",
            line_width=0,
            fillcolor="rgba(21,101,192,0.15)",
            hoverinfo="skip",
            name=f"mín. a máx. ({anteriores['ano'].min()} a {ano_ref - 1})",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=faixa.index,
            y=faixa["median"],
            name="mediana histórica",
            line={"color": "#1565c0", "dash": "dash"},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=atual.index, y=atual.values, name=str(ano_ref), line={"color": "black", "width": 2.5}
        )
    )
    eixo_casos_log(fig)
    fig.update_xaxes(title="semana epidemiológica")
    fig.update_layout(
        title=f"{ano_ref} comparado aos anos anteriores", height=420, hovermode="x unified"
    )
    return fig


def fig_sparkline(dados: pd.DataFrame, tendencia: Trend) -> go.Figure:
    """casos_est das últimas 12 semanas, sem eixos, com a tendência como título (6.4)."""
    recentes = dados.tail(SPARKLINE_WEEKS)
    fig = go.Figure(
        go.Scatter(
            x=recentes["data_iniSE"],
            y=recentes["casos_est"],
            mode="lines+markers",
            line={"color": "black"},
            marker={"size": 4},
            hovertemplate="%{x|%d/%m}: %{y:,.0f}<extra></extra>",
        )
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        height=140,
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        separators=",.",
        title={
            "text": (
                f"{SPARKLINE_WEEKS} semanas · tendência ({TENDENCIA_WEEKS} sem.): "
                f"{TREND_LABELS[tendencia]}"
            ),
            "font": {"size": 13},
        },
    )
    return fig


def fig_medidores(situacao: SituacaoAtual) -> go.Figure:
    """Medidores do Rt e da probabilidade de transmissão em crescimento (p_rt1) (6.5)."""
    rt_max = max(RT_ESCALA_MIN, math.ceil(situacao.rt))
    # Títulos como subplot_titles ficam na mesma altura (o do Indicator acompanha o medidor).
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "indicator"}] * 2],
        subplot_titles=["Rt (número de reprodução)", "Probabilidade de transmissão em crescimento"],
        horizontal_spacing=0.15,
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=situacao.rt,
            number={"valueformat": ".2f"},
            gauge={
                "axis": {"range": [0, rt_max]},
                "bar": {"color": "black", "thickness": 0.25},
                "steps": [
                    {"range": [0, RT_QUEDA], "color": "#a5d6a7"},
                    {"range": [RT_QUEDA, RT_ALTA], "color": "#fff59d"},
                    {"range": [RT_ALTA, rt_max], "color": "#ef9a9a"},
                ],
                "threshold": {"line": {"color": "#c62828", "width": 3}, "value": 1},
            },
        ),
        1,
        1,
    )
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=situacao.p_rt1 * 100,
            number={"suffix": "%", "valueformat": ".0f"},
            gauge={
                "axis": {"range": [0, 100], "ticksuffix": "%"},
                "bar": {"color": "black", "thickness": 0.25},
                "steps": [
                    {"range": [0, P_RT1_LIMIAR], "color": "#eeeeee"},
                    {"range": [P_RT1_LIMIAR, 100], "color": "#ef9a9a"},
                ],
                "threshold": {"line": {"color": "#c62828", "width": 3}, "value": P_RT1_LIMIAR},
            },
        ),
        1,
        2,
    )
    fig.update_annotations(yshift=20, font_size=15)
    fig.update_layout(height=320, margin={"t": 80, "b": 20}, separators=",.")
    return fig
