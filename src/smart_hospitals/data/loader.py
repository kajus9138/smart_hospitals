"""Leitura e validação do snapshot CSV do InfoDengue."""

from datetime import date
from pathlib import Path

import pandas as pd

SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "data" / "dengue_sp_snapshot.csv"

REQUIRED_COLUMNS = (
    "data_iniSE",
    "SE",
    "casos",
    "casos_est",
    "casos_est_min",
    "casos_est_max",
    "Rt",
    "p_rt1",
    "nivel",
    "p_inc100k",
)


def load_snapshot(path: Path | None = None) -> pd.DataFrame:
    """Lê o snapshot, valida as colunas usadas e devolve as semanas em ordem crescente de SE."""
    df = pd.read_csv(path or SNAPSHOT_PATH)
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes no snapshot: {missing}")
    duplicated = sorted(df.loc[df["SE"].duplicated(), "SE"].unique().tolist())
    if duplicated:
        raise ValueError(f"Semanas epidemiológicas duplicadas no snapshot: {duplicated}")
    df["data_iniSE"] = pd.to_datetime(df["data_iniSE"])
    return df.sort_values("SE").reset_index(drop=True)


def get_reference_date(df: pd.DataFrame) -> date:
    """Data de início da semana epidemiológica mais recente do snapshot."""
    reference: date = df["data_iniSE"].max().date()
    return reference
