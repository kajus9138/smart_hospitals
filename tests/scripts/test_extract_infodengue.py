"""Testes do script de extração do InfoDengue (offline: usam uma amostra real gravada em disco)."""

import logging
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

import extract_infodengue as extract

SAMPLE_CSV = Path(__file__).parent / "fixtures" / "infodengue_sample.csv"
SAMPLE_URL = SAMPLE_CSV.as_uri()


def test_build_url_usa_parametros_de_sao_paulo() -> None:
    url = extract.build_url(ey_end=2026)

    parsed = urlparse(url)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == extract.BASE_URL
    assert parse_qs(parsed.query) == {
        "geocode": ["3550308"],
        "disease": ["dengue"],
        "format": ["csv"],
        "ew_start": ["1"],
        "ew_end": ["53"],
        "ey_start": ["2010"],
        "ey_end": ["2026"],
    }


def test_build_url_usa_ano_atual_por_padrao() -> None:
    query = parse_qs(urlparse(extract.build_url()).query)
    assert query["ey_end"] == [str(date.today().year)]


def test_fetch_ordena_por_semana_e_preserva_colunas() -> None:
    df = extract.fetch_infodengue_data(SAMPLE_URL)

    assert df["SE"].tolist() == [201001, 201453, 202552, 202553, 202601]
    assert set(extract.REQUIRED_COLUMNS) <= set(df.columns)
    assert list(df.columns) == list(pd.read_csv(SAMPLE_CSV).columns)
    assert list(df.index) == list(range(len(df)))


def test_fetch_registra_semanas_e_intervalo(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        extract.fetch_infodengue_data(SAMPLE_URL)

    assert "Baixadas 5 semanas, da SE 201001 à SE 202601" in caplog.text


def test_fetch_falha_sem_colunas_obrigatorias(tmp_path: Path) -> None:
    csv = tmp_path / "incompleto.csv"
    pd.read_csv(SAMPLE_CSV).drop(columns=["Rt", "nivel"]).to_csv(csv, index=False)

    with pytest.raises(ValueError, match="Rt, nivel"):
        extract.fetch_infodengue_data(csv.as_uri())


def test_fetch_falha_sem_semanas(tmp_path: Path) -> None:
    csv = tmp_path / "vazio.csv"
    pd.read_csv(SAMPLE_CSV).head(0).to_csv(csv, index=False)

    with pytest.raises(ValueError, match="nenhuma semana"):
        extract.fetch_infodengue_data(csv.as_uri())


def test_fetch_falha_com_semanas_duplicadas(tmp_path: Path) -> None:
    csv = tmp_path / "duplicado.csv"
    sample = pd.read_csv(SAMPLE_CSV)
    pd.concat([sample, sample.head(1)]).to_csv(csv, index=False)

    with pytest.raises(ValueError, match="duplicadas"):
        extract.fetch_infodengue_data(csv.as_uri())


def test_fetch_falha_com_erro_de_rede(tmp_path: Path) -> None:
    url = (tmp_path / "inexistente.csv").as_uri()

    with pytest.raises(RuntimeError, match="Falha ao acessar o InfoDengue"):
        extract.fetch_infodengue_data(url)


def test_saida_padrao_fica_na_raiz_do_repositorio() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    assert repo_root / "data" / "dengue_sp_snapshot.csv" == extract.DEFAULT_OUTPUT


def test_main_grava_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def fake_build_url(**kwargs: int | None) -> str:
        assert kwargs == {"ey_end": 2026}
        return SAMPLE_URL

    monkeypatch.setattr(extract, "build_url", fake_build_url)
    output = tmp_path / "saida" / "snapshot.csv"

    with caplog.at_level(logging.INFO):
        extract.main(["--output", str(output), "--ey-end", "2026"])

    saved = pd.read_csv(output, encoding="utf-8")
    assert saved["SE"].tolist() == [201001, 201453, 202552, 202553, 202601]
    assert saved["municipio_nome"].unique().tolist() == ["São Paulo"]
    assert f"Snapshot salvo em {output}" in caplog.text
    assert "KB" in caplog.text
