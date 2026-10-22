"""Fixtures compartilhadas dos testes."""

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Backend dos testes async (plugin anyio do pytest)."""
    return "asyncio"


@pytest.fixture
def sample_dengue_data() -> pd.DataFrame:
    """Cinco semanas fixas de 2024 (sem acesso à rede)."""
    return pd.DataFrame(
        {
            "SE": [202401, 202402, 202403, 202404, 202405],
            "data_iniSE": pd.to_datetime(
                ["2024-01-01", "2024-01-08", "2024-01-15", "2024-01-22", "2024-01-29"]
            ),
            "casos": [100, 120, 150, 180, 200],
            "casos_est": [110.0, 130.0, 160.0, 190.0, 220.0],
            "casos_est_min": [90.0, 110.0, 140.0, 170.0, 200.0],
            "casos_est_max": [130.0, 150.0, 180.0, 210.0, 240.0],
            "Rt": [1.1, 1.2, 1.3, 1.15, 1.1],
            "p_rt1": [0.75, 0.85, 0.92, 0.80, 0.72],
            "nivel": [2, 3, 3, 3, 2],
            "p_inc100k": [5.5, 6.5, 8.0, 9.5, 11.0],
        }
    )


@pytest.fixture
def sample_csv_path(sample_dengue_data: pd.DataFrame, tmp_path: Path) -> Path:
    """Grava a amostra num CSV temporário."""
    csv_path = tmp_path / "test_snapshot.csv"
    sample_dengue_data.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def multi_year_data() -> pd.DataFrame:
    """SEs 01 e 02 de 2022 e 2023 e só a SE 01 de 2024 (ano de referência)."""
    se = [202201, 202202, 202301, 202302, 202401]
    return pd.DataFrame(
        {
            "SE": se,
            "data_iniSE": pd.to_datetime(
                ["2022-01-02", "2022-01-09", "2023-01-01", "2023-01-08", "2023-12-31"]
            ),
            "casos": [10, 20, 30, 40, 50],
            "casos_est": [100.0, 200.0, 300.0, 400.0, 500.0],
            "casos_est_min": [90.0, 190.0, 290.0, 390.0, 490.0],
            "casos_est_max": [110.0, 210.0, 310.0, 410.0, float("nan")],
            "Rt": [0.8] * len(se),
            "p_rt1": [0.1] * len(se),
            "nivel": [1] * len(se),
            "p_inc100k": [1.0] * len(se),
        }
    )
