"""Módulo de dados compartilhado entre o dashboard e o MCP server."""

from smart_hospitals.data.indicators import (
    AlertLevel,
    ParametroInvalido,
    SituacaoAtual,
    Tendencia,
    Trend,
    calcular_situacao_atual,
    calcular_tendencia,
    comparativo_sazonal,
    serie_historica,
)
from smart_hospitals.data.loader import SNAPSHOT_PATH, get_reference_date, load_snapshot

__all__ = [
    "SNAPSHOT_PATH",
    "AlertLevel",
    "ParametroInvalido",
    "SituacaoAtual",
    "Tendencia",
    "Trend",
    "calcular_situacao_atual",
    "calcular_tendencia",
    "comparativo_sazonal",
    "get_reference_date",
    "load_snapshot",
    "serie_historica",
]
