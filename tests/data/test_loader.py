"""Testes da leitura do snapshot (sem rede)."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from smart_hospitals.data.loader import (
    REQUIRED_COLUMNS,
    SNAPSHOT_PATH,
    get_reference_date,
    load_snapshot,
)


def test_load_snapshot_valid(sample_csv_path: Path, sample_dengue_data: pd.DataFrame) -> None:
    df = load_snapshot(sample_csv_path)

    assert len(df) == len(sample_dengue_data)
    assert set(REQUIRED_COLUMNS) <= set(df.columns)


def test_load_snapshot_ordena_por_se(sample_dengue_data: pd.DataFrame, tmp_path: Path) -> None:
    path = tmp_path / "desordenado.csv"
    sample_dengue_data.iloc[::-1].to_csv(path, index=False)

    df = load_snapshot(path)

    assert df["SE"].tolist() == sorted(sample_dengue_data["SE"])
    assert list(df.index) == list(range(len(df)))


def test_load_snapshot_missing_columns(sample_dengue_data: pd.DataFrame, tmp_path: Path) -> None:
    path = tmp_path / "incompleto.csv"
    sample_dengue_data.drop(columns=["Rt", "nivel"]).to_csv(path, index=False)

    with pytest.raises(ValueError, match=r"\['Rt', 'nivel'\]"):
        load_snapshot(path)


def test_load_snapshot_date_parsing(sample_csv_path: Path) -> None:
    df = load_snapshot(sample_csv_path)

    assert pd.api.types.is_datetime64_any_dtype(df["data_iniSE"])


def test_get_reference_date(sample_dengue_data: pd.DataFrame) -> None:
    assert get_reference_date(sample_dengue_data) == date(2024, 1, 29)


def test_load_snapshot_versionado_por_padrao() -> None:
    df = load_snapshot()

    assert SNAPSHOT_PATH.is_file()
    assert df["SE"].is_monotonic_increasing
    assert df["SE"].is_unique
    assert get_reference_date(df) == df["data_iniSE"].iloc[-1].date()


def test_load_snapshot_se_duplicada(sample_dengue_data: pd.DataFrame, tmp_path: Path) -> None:
    path = tmp_path / "duplicado.csv"
    pd.concat([sample_dengue_data, sample_dengue_data.tail(1)]).to_csv(path, index=False)

    with pytest.raises(ValueError, match=r"duplicadas no snapshot: \[202405\]"):
        load_snapshot(path)
