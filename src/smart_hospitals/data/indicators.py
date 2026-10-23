"""Cálculo dos indicadores (situação atual, tendência, série histórica, comparativo sazonal)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

import pandas as pd

AlertLevel = Literal["verde", "amarelo", "laranja", "vermelho"]
Trend = Literal["alta", "estavel", "queda"]

LEVEL_MAP: dict[int, AlertLevel] = {1: "verde", 2: "amarelo", 3: "laranja", 4: "vermelho"}

# Limiares da tendência (calcular_tendencia), também usados nos medidores do dashboard.
RT_ALTA = 1.1
RT_QUEDA = 0.9
P_RT1_ALTA = 0.7

TENDENCIA_COLUMNS = ["SE", "data_iniSE", "casos_est", "Rt", "p_rt1", "nivel"]
SERIE_COLUMNS = [
    "SE",
    "data_iniSE",
    "casos",
    "casos_est",
    "casos_est_min",
    "casos_est_max",
    "Rt",
    "nivel",
]


class ParametroInvalidoError(ValueError):
    """Parâmetro informado pelo usuário fora do formato ou do intervalo aceito."""


@dataclass
class SituacaoAtual:
    data_referencia: str
    casos_notificados: int
    casos_est: float
    casos_est_min: float | None  # None quando o InfoDengue não informa o intervalo
    casos_est_max: float | None
    incidencia_100k: float
    nivel_alerta: AlertLevel
    rt: float
    p_rt1: float
    variacao_semanal: float  # % de casos_est em relação à semana anterior


@dataclass
class Tendencia:
    semanas: list[dict[str, Any]]
    tendencia_resumo: Trend
    rt_medio: float
    p_rt1_medio: float


def _require_rows(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("O snapshot não tem nenhuma semana.")


def _alert_level(nivel: Any) -> AlertLevel:
    try:
        return LEVEL_MAP[int(nivel)]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Nível de alerta inválido: {nivel!r} (esperado 1 a 4)") from exc


def _float_or_none(value: Any) -> float | None:
    return None if pd.isna(value) else float(value)


def _parse_bound(value: str | int) -> pd.Timestamp | int:
    text = str(value).strip()
    if text.isdigit() and len(text) == 6:
        return int(text)
    try:
        return pd.Timestamp(datetime.strptime(text, "%Y-%m-%d"))
    except ValueError:
        raise ParametroInvalidoError(
            f"Valor inválido {value!r}: use SE (AAAASS) ou data (AAAA-MM-DD)"
        ) from None


def _to_records(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    """Registros prontos para JSON: datas em ISO (AAAA-MM-DD) e NaN como None."""
    out = df[columns].copy()
    out["data_iniSE"] = out["data_iniSE"].dt.strftime("%Y-%m-%d")
    out = out.astype(object).where(out.notna(), None)
    return [{str(k): v for k, v in row.items()} for row in out.to_dict("records")]


def calcular_situacao_atual(df: pd.DataFrame) -> SituacaoAtual:
    """Situação da semana mais recente, com variação de casos_est frente à semana anterior."""
    _require_rows(df)
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    variacao = 0.0
    if previous["casos_est"] > 0:
        variacao = (latest["casos_est"] - previous["casos_est"]) / previous["casos_est"] * 100
    return SituacaoAtual(
        data_referencia=latest["data_iniSE"].strftime("%Y-%m-%d"),
        casos_notificados=int(latest["casos"]),
        casos_est=float(latest["casos_est"]),
        casos_est_min=_float_or_none(latest["casos_est_min"]),
        casos_est_max=_float_or_none(latest["casos_est_max"]),
        incidencia_100k=float(latest["p_inc100k"]),
        nivel_alerta=_alert_level(latest["nivel"]),
        rt=float(latest["Rt"]),
        p_rt1=float(latest["p_rt1"]),
        variacao_semanal=round(float(variacao), 1),
    )


def calcular_tendencia(df: pd.DataFrame, semanas: int = 4) -> Tendencia:
    """Tendência das últimas N semanas a partir das médias de Rt e p_rt1.

    alta: Rt médio > 1,1 e p_rt1 médio > 0,7; queda: Rt médio < 0,9; senão estavel.
    """
    _require_rows(df)
    if semanas < 1:
        raise ParametroInvalidoError(f"semanas deve ser >= 1, recebido {semanas}")
    recent = df.tail(semanas)
    rt_medio = float(recent["Rt"].mean())
    p_rt1_medio = float(recent["p_rt1"].mean())
    tendencia: Trend
    if rt_medio > RT_ALTA and p_rt1_medio > P_RT1_ALTA:
        tendencia = "alta"
    elif rt_medio < RT_QUEDA:
        tendencia = "queda"
    else:
        tendencia = "estavel"
    return Tendencia(
        semanas=_to_records(recent, TENDENCIA_COLUMNS),
        tendencia_resumo=tendencia,
        rt_medio=round(rt_medio, 2),
        p_rt1_medio=round(p_rt1_medio, 2),
    )


def serie_historica(df: pd.DataFrame, inicio: str | int, fim: str | int) -> list[dict[str, Any]]:
    """Semanas entre inicio e fim (inclusive), ambos como SE (202401) ou como data (2024-01-01).

    Com datas, entram as semanas que contêm inicio e fim, mesmo que a data caia no meio da semana.
    """
    low, high = _parse_bound(inicio), _parse_bound(fim)
    if isinstance(low, pd.Timestamp) and isinstance(high, pd.Timestamp):
        _check_order(low <= high, inicio, fim)
        dates = df["data_iniSE"]
        mask = (dates > low - pd.Timedelta(days=7)) & (dates <= high)
    elif isinstance(low, int) and isinstance(high, int):
        _check_order(low <= high, inicio, fim)
        mask = (df["SE"] >= low) & (df["SE"] <= high)
    else:
        raise ParametroInvalidoError(
            "inicio e fim devem usar o mesmo formato: SE (AAAASS) ou data (AAAA-MM-DD)"
        )
    return _to_records(df[mask], SERIE_COLUMNS)


def _check_order(ordered: bool, inicio: str | int, fim: str | int) -> None:
    if not ordered:
        raise ParametroInvalidoError(f"inicio ({inicio}) é posterior a fim ({fim})")


def comparativo_sazonal(df: pd.DataFrame, semana: int | None = None) -> dict[str, Any]:
    """Compara casos_est de uma semana do ano de referência com a mesma semana dos anos anteriores.

    O ano de referência é o da SE mais recente; média, mínimo e máximo usam só anos anteriores.
    Sem semana informada, usa a semana mais recente do snapshot.
    """
    _require_rows(df)
    latest_se = int(df["SE"].iloc[-1])
    ano_referencia = latest_se // 100
    if semana is None:
        semana = latest_se % 100
    if not 1 <= semana <= 53:
        raise ParametroInvalidoError(f"semana deve estar entre 1 e 53, recebido {semana}")

    same_week = df[df["SE"] % 100 == semana]
    anos = same_week["SE"] // 100
    anteriores = same_week.loc[anos < ano_referencia, "casos_est"].dropna()
    atual = same_week.loc[anos == ano_referencia, "casos_est"]
    has_history = not anteriores.empty
    return {
        "semana_epidemiologica": semana,
        "ano_referencia": ano_referencia,
        "ano_atual": round(atual.iloc[0]) if not atual.empty and pd.notna(atual.iloc[0]) else None,
        "media_historica": round(float(anteriores.mean()), 1) if has_history else None,
        "minimo": round(anteriores.min()) if has_history else None,
        "maximo": round(anteriores.max()) if has_history else None,
        "anos_comparados": len(anteriores),
    }
