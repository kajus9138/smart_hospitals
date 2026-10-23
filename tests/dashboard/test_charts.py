"""Testes das figuras do dashboard (sem rede, sem Streamlit)."""

from typing import Any

import numpy as np
import pandas as pd

from smart_hospitals.dashboard.charts import (
    LEVEL_NAMES,
    faixas_de_nivel,
    fig_medidores,
    fig_sazonal,
    fig_serie,
    fig_sparkline,
    fmt_int,
    preparar,
    texto_nivel_alerta,
)
from smart_hospitals.data.indicators import calcular_situacao_atual


def _bands(fig: Any) -> list[Any]:
    return [t for t in fig.data if t.fill == "toself"]


def test_fmt_int_uses_brazilian_thousands_separator() -> None:
    assert fmt_int(1_234_567.4) == "1.234.567"
    assert fmt_int(12) == "12"


def test_preparar_adds_columns_without_mutating(sample_dengue_data: pd.DataFrame) -> None:
    dados = preparar(sample_dengue_data)

    assert dados["ano"].tolist() == [2024] * 5
    assert dados["semana"].tolist() == [1, 2, 3, 4, 5]
    assert dados["nivel_nome"].tolist() == ["amarelo", "laranja", "laranja", "laranja", "amarelo"]
    assert "nivel_nome" not in sample_dengue_data.columns


def test_faixas_de_nivel_groups_contiguous_weeks(sample_dengue_data: pd.DataFrame) -> None:
    faixas = faixas_de_nivel(preparar(sample_dengue_data))

    assert faixas["nivel"].tolist() == ["amarelo", "laranja", "amarelo"]
    assert (
        faixas["inicio"].tolist()
        == pd.to_datetime(["2024-01-01", "2024-01-08", "2024-01-29"]).tolist()
    )
    # fim exclusivo: a semana seguinte à última do trecho
    assert (
        faixas["fim"].tolist()
        == pd.to_datetime(["2024-01-08", "2024-01-29", "2024-02-05"]).tolist()
    )


def test_fig_serie_has_one_legend_entry_per_alert_level(sample_dengue_data: pd.DataFrame) -> None:
    fig = fig_serie(preparar(sample_dengue_data))

    legend = [t.name for t in fig.data if t.legendgroup == "alerta"]
    assert legend == LEVEL_NAMES
    assert len(fig.layout.shapes) == 3  # um vrect por trecho de nível


def test_fig_serie_draws_band_only_on_weeks_with_interval(
    sample_dengue_data: pd.DataFrame,
) -> None:
    dados = sample_dengue_data.copy()
    # semanas 1 e 4 consolidadas (min = max) e semana 3 com max vazio: sobram os trechos [2] e [5]
    dados.loc[[0, 3], "casos_est_max"] = dados.loc[[0, 3], "casos_est_min"]
    dados.loc[2, "casos_est_max"] = np.nan

    bands = _bands(fig_serie(preparar(dados)))

    assert len(bands) == 2
    assert [b.showlegend for b in bands] == [True, False]
    assert list(bands[0].y) == [150.0, 110.0]
    assert list(bands[1].y) == [240.0, 200.0]


def test_fig_serie_without_interval_has_no_band(sample_dengue_data: pd.DataFrame) -> None:
    dados = sample_dengue_data.assign(casos_est_max=np.nan)

    fig = fig_serie(preparar(dados))

    assert _bands(fig) == []
    assert fig.data[-1].name == "casos estimados"


def test_fig_sazonal_compares_with_previous_years_median(
    multi_year_data: pd.DataFrame,
) -> None:
    fig = fig_sazonal(preparar(multi_year_data))
    traces = {t.name: t for t in fig.data}

    assert list(traces["mediana histórica"].y) == [200.0, 300.0]
    assert list(traces["mín. a máx. (2022 a 2023)"].y) == [100.0, 200.0]
    assert list(traces["2024"].x) == [1]
    assert list(traces["2024"].y) == [500.0]
    assert fig.layout.yaxis.type == "log"


def test_fig_sparkline_shows_last_12_weeks_and_trend(sample_dengue_data: pd.DataFrame) -> None:
    dados = pd.concat([sample_dengue_data] * 3, ignore_index=True)  # 15 linhas

    fig = fig_sparkline(dados, "estavel")

    assert len(fig.data[0].y) == 12
    assert "tendência (4 sem.): estável" in fig.layout.title.text


def test_fig_medidores_show_rt_and_p_rt1_percent(sample_dengue_data: pd.DataFrame) -> None:
    situacao = calcular_situacao_atual(sample_dengue_data)

    rt, p_rt1 = fig_medidores(situacao).data

    assert rt.value == situacao.rt
    assert p_rt1.value == situacao.p_rt1 * 100
    assert p_rt1.gauge.threshold.value == 70


def test_fig_medidores_extends_rt_axis_during_outbreaks(sample_dengue_data: pd.DataFrame) -> None:
    situacao = calcular_situacao_atual(sample_dengue_data.assign(Rt=3.2))

    rt, _ = fig_medidores(situacao).data

    assert tuple(rt.gauge.axis.range) == (0, 4)
    assert rt.gauge.steps[-1].range == (1.1, 4)


def test_texto_nivel_alerta_uses_level_color() -> None:
    assert texto_nivel_alerta("laranja") == ':color[Laranja]{foreground="#ef6c00"}'


def test_fig_medidores_titles_fit_in_half_width(sample_dengue_data: pd.DataFrame) -> None:
    fig = fig_medidores(calcular_situacao_atual(sample_dengue_data))

    # títulos longos quebrados em linhas para não serem cortados na coluna
    assert all(len(line) <= 30 for a in fig.layout.annotations for line in a.text.split("<br>"))
