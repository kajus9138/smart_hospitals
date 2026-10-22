"""Baixa a série de dengue de São Paulo capital do InfoDengue e grava o snapshot CSV versionado.

Uso: uv run python scripts/extract_infodengue.py [--output CAMINHO] [--ey-end ANO]

Os logs vão para stderr. Este é o único ponto do projeto que acessa a API do InfoDengue;
dashboard, MCP server e testes leem apenas o snapshot.
"""

import argparse
import io
import logging
import sys
from datetime import date
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

logger = logging.getLogger(__name__)

BASE_URL = "https://info.dengue.mat.br/api/alertcity"
GEOCODE_SAO_PAULO = 3550308
EY_START = 2010
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "dengue_sp_snapshot.csv"
TIMEOUT_SECONDS = 120

# Colunas que o módulo de dados usa; o snapshot guarda todas as colunas devolvidas pela API.
REQUIRED_COLUMNS = (
    "data_iniSE",
    "SE",
    "casos_est",
    "casos_est_min",
    "casos_est_max",
    "casos",
    "p_rt1",
    "p_inc100k",
    "Rt",
    "nivel",
    "receptivo",
)


def build_url(
    geocode: int = GEOCODE_SAO_PAULO,
    disease: str = "dengue",
    ey_start: int = EY_START,
    ey_end: int | None = None,
) -> str:
    """Monta a URL da API alertcity em formato CSV.

    ``ew_end=53`` cobre os anos epidemiológicos com 53 semanas (ex.: 2014, 2020, 2025).
    """
    params = {
        "geocode": geocode,
        "disease": disease,
        "format": "csv",
        "ew_start": 1,
        "ew_end": 53,
        "ey_start": ey_start,
        "ey_end": ey_end if ey_end is not None else date.today().year,
    }
    return f"{BASE_URL}?{urlencode(params)}"


def fetch_infodengue_data(url: str, timeout: float = TIMEOUT_SECONDS) -> pd.DataFrame:
    """Lê o CSV da API, valida as colunas obrigatórias e ordena por semana epidemiológica."""
    logger.info("Baixando dados de %s", url)
    try:
        with urlopen(url, timeout=timeout) as response:
            content = response.read()
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Falha ao acessar o InfoDengue em {url}: {exc}") from exc
    df = pd.read_csv(io.BytesIO(content))
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes na resposta do InfoDengue: {', '.join(missing)}")
    if df.empty:
        raise ValueError("A API do InfoDengue não devolveu nenhuma semana")
    if not df["SE"].is_unique:
        raise ValueError("A API do InfoDengue devolveu semanas epidemiológicas duplicadas")
    df = df.sort_values("SE").reset_index(drop=True)
    logger.info(
        "Baixadas %d semanas, da SE %d à SE %d", len(df), df["SE"].iloc[0], df["SE"].iloc[-1]
    )
    return df


def save_snapshot(df: pd.DataFrame, path: Path) -> None:
    """Grava o snapshot em UTF-8 e registra o tamanho do arquivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    logger.info("Snapshot salvo em %s (%.1f KB)", path, path.stat().st_size / 1024)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Gera o snapshot CSV de dengue de SP")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="CSV de saída")
    parser.add_argument("--ey-end", type=int, default=None, help="último ano (padrão: atual)")
    args = parser.parse_args(argv)

    df = fetch_infodengue_data(build_url(ey_end=args.ey_end))
    save_snapshot(df, args.output)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    main()
