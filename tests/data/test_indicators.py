"""Testes do cálculo dos indicadores (sem rede)."""

import json
from dataclasses import asdict

import pandas as pd
import pytest

from smart_hospitals.data.indicators import (
    calcular_situacao_atual,
    calcular_tendencia,
    comparativo_sazonal,
    serie_historica,
)
from smart_hospitals.data.loader import load_snapshot


def _with_rt(df: pd.DataFrame, rt: float, p_rt1: float) -> pd.DataFrame:
    return df.assign(Rt=rt, p_rt1=p_rt1)


# --- situação atual ---


def test_situacao_atual_extracts_latest_week(sample_dengue_data: pd.DataFrame) -> None:
    situacao = calcular_situacao_atual(sample_dengue_data)

    assert situacao.data_referencia == "2024-01-29"
    assert situacao.casos_notificados == 200
    assert (situacao.casos_est, situacao.casos_est_min, situacao.casos_est_max) == (220, 200, 240)
    assert situacao.incidencia_100k == 11.0
    assert situacao.nivel_alerta == "amarelo"
    assert (situacao.rt, situacao.p_rt1) == (1.1, 0.72)


def test_situacao_atual_variation_calculation(sample_dengue_data: pd.DataFrame) -> None:
    # (220 - 190) / 190 * 100 = 15,789...
    assert calcular_situacao_atual(sample_dengue_data).variacao_semanal == 15.8


def test_situacao_atual_single_row(sample_dengue_data: pd.DataFrame) -> None:
    assert calcular_situacao_atual(sample_dengue_data.head(1)).variacao_semanal == 0


def test_situacao_atual_semana_anterior_zerada(sample_dengue_data: pd.DataFrame) -> None:
    df = sample_dengue_data.copy()
    df.loc[3, "casos_est"] = 0.0

    assert calcular_situacao_atual(df).variacao_semanal == 0


def test_situacao_atual_nivel_invalido(sample_dengue_data: pd.DataFrame) -> None:
    df = sample_dengue_data.assign(nivel=5)

    with pytest.raises(ValueError, match="Nível de alerta inválido"):
        calcular_situacao_atual(df)


def test_situacao_atual_snapshot_vazio(sample_dengue_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="nenhuma semana"):
        calcular_situacao_atual(sample_dengue_data.head(0))


def test_situacao_atual_intervalo_ausente_vira_none(sample_dengue_data: pd.DataFrame) -> None:
    df = sample_dengue_data.copy()
    df.loc[4, "casos_est_max"] = float("nan")

    situacao = calcular_situacao_atual(df)

    assert situacao.casos_est_max is None
    json.dumps(asdict(situacao))


def test_situacao_atual_nivel_ausente(sample_dengue_data: pd.DataFrame) -> None:
    df = sample_dengue_data.astype({"nivel": object})
    df.loc[4, "nivel"] = None

    with pytest.raises(ValueError, match="Nível de alerta inválido"):
        calcular_situacao_atual(df)


# --- tendência ---


def test_tendencia_alta(sample_dengue_data: pd.DataFrame) -> None:
    tendencia = calcular_tendencia(_with_rt(sample_dengue_data, 1.3, 0.9))

    assert tendencia.tendencia_resumo == "alta"
    assert (tendencia.rt_medio, tendencia.p_rt1_medio) == (1.3, 0.9)


def test_tendencia_rt_alto_sem_confianca_e_estavel(sample_dengue_data: pd.DataFrame) -> None:
    assert calcular_tendencia(_with_rt(sample_dengue_data, 1.3, 0.5)).tendencia_resumo == "estavel"


def test_tendencia_queda(sample_dengue_data: pd.DataFrame) -> None:
    assert calcular_tendencia(_with_rt(sample_dengue_data, 0.8, 0.1)).tendencia_resumo == "queda"


def test_tendencia_estavel(sample_dengue_data: pd.DataFrame) -> None:
    assert calcular_tendencia(_with_rt(sample_dengue_data, 1.0, 0.5)).tendencia_resumo == "estavel"


def test_tendencia_usa_ultimas_n_semanas(sample_dengue_data: pd.DataFrame) -> None:
    tendencia = calcular_tendencia(sample_dengue_data, semanas=2)

    assert [s["SE"] for s in tendencia.semanas] == [202404, 202405]
    assert tendencia.rt_medio == 1.12  # média de 1,15 e 1,1
    assert tendencia.semanas[-1]["data_iniSE"] == "2024-01-29"


def test_tendencia_semanas_invalido(sample_dengue_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="semanas deve ser >= 1"):
        calcular_tendencia(sample_dengue_data, semanas=0)


# --- série histórica ---


def test_serie_historica_filtering(sample_dengue_data: pd.DataFrame) -> None:
    serie = serie_historica(sample_dengue_data, "202402", "202404")

    assert [s["SE"] for s in serie] == [202402, 202403, 202404]
    assert serie[0]["data_iniSE"] == "2024-01-08"


def test_serie_historica_por_data(sample_dengue_data: pd.DataFrame) -> None:
    serie = serie_historica(sample_dengue_data, "2024-01-08", "2024-01-22")

    assert [s["SE"] for s in serie] == [202402, 202403, 202404]


def test_serie_historica_formatos_misturados(sample_dengue_data: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="mesmo formato"):
        serie_historica(sample_dengue_data, 202401, "2024-01-22")


def test_serie_historica_data_no_meio_da_semana(sample_dengue_data: pd.DataFrame) -> None:
    # 10/01 cai na semana iniciada em 08/01; 24/01, na iniciada em 22/01
    serie = serie_historica(sample_dengue_data, "2024-01-10", "2024-01-24")

    assert [s["SE"] for s in serie] == [202402, 202403, 202404]


@pytest.mark.parametrize("inicio", ["2024/01/08", "abc", "2024-1"])
def test_serie_historica_formato_invalido(sample_dengue_data: pd.DataFrame, inicio: str) -> None:
    with pytest.raises(ValueError, match="Valor inválido"):
        serie_historica(sample_dengue_data, inicio, "2024-01-22")


@pytest.mark.parametrize(("inicio", "fim"), [(202404, 202402), ("2024-01-22", "2024-01-08")])
def test_serie_historica_intervalo_invertido(
    sample_dengue_data: pd.DataFrame, inicio: str | int, fim: str | int
) -> None:
    with pytest.raises(ValueError, match="posterior a fim"):
        serie_historica(sample_dengue_data, inicio, fim)


def test_serie_historica_empty(sample_dengue_data: pd.DataFrame) -> None:
    assert serie_historica(sample_dengue_data, 202301, 202352) == []


def test_serie_historica_nan_vira_none(multi_year_data: pd.DataFrame) -> None:
    serie = serie_historica(multi_year_data, 202401, 202401)

    assert serie[0]["casos_est_max"] is None
    json.dumps(serie)


# --- comparativo sazonal ---


def test_comparativo_sazonal_default_week(multi_year_data: pd.DataFrame) -> None:
    assert comparativo_sazonal(multi_year_data) == {
        "semana_epidemiologica": 1,
        "ano_referencia": 2024,
        "ano_atual": 500,
        "media_historica": 200.0,  # 2022 (100) e 2023 (300); o ano de referência fica de fora
        "minimo": 100,
        "maximo": 300,
        "anos_comparados": 2,
    }


def test_comparativo_sazonal_specific_week(multi_year_data: pd.DataFrame) -> None:
    comparativo = comparativo_sazonal(multi_year_data, semana=2)

    # a SE 02 ainda não ocorreu no ano de referência
    assert comparativo["ano_atual"] is None
    assert comparativo["media_historica"] == 300.0
    assert comparativo["anos_comparados"] == 2


def test_comparativo_sazonal_sem_anos_anteriores(sample_dengue_data: pd.DataFrame) -> None:
    comparativo = comparativo_sazonal(sample_dengue_data)

    assert comparativo["ano_atual"] == 220
    assert comparativo["media_historica"] is None
    assert comparativo["minimo"] is None
    assert comparativo["anos_comparados"] == 0


def test_comparativo_sazonal_arredonda_e_ignora_nan(multi_year_data: pd.DataFrame) -> None:
    df = multi_year_data.copy()
    df.loc[0, "casos_est"] = 99.9  # 2022
    df.loc[4, "casos_est"] = float("nan")  # ano de referência

    comparativo = comparativo_sazonal(df)

    assert comparativo["minimo"] == 100
    assert comparativo["ano_atual"] is None


@pytest.mark.parametrize("semana", [0, 54])
def test_comparativo_sazonal_semana_invalida(multi_year_data: pd.DataFrame, semana: int) -> None:
    with pytest.raises(ValueError, match="entre 1 e 53"):
        comparativo_sazonal(multi_year_data, semana=semana)


# --- integração com o snapshot versionado ---


def test_indicadores_no_snapshot_versionado() -> None:
    df = load_snapshot()

    situacao = calcular_situacao_atual(df)
    tendencia = calcular_tendencia(df)
    comparativo = comparativo_sazonal(df)

    assert situacao.data_referencia == df["data_iniSE"].iloc[-1].strftime("%Y-%m-%d")
    assert comparativo["anos_comparados"] >= 10
    json.dumps([tendencia.semanas, comparativo, serie_historica(df, 201001, 202653)])
