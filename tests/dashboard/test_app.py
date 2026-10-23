"""Smoke test do dashboard com o snapshot real e teste do atalho de linha de comando."""

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from smart_hospitals.dashboard import __main__ as dashboard_main
from smart_hospitals.data import get_reference_date, load_snapshot

# AppTest resolve caminhos relativos a partir do arquivo de teste, não do diretório atual.
APP_PATH = str(
    Path(__file__).resolve().parents[2] / "src" / "smart_hospitals" / "dashboard" / "app.py"
)


def test_dashboard_loads() -> None:
    """Smoke test: verify dashboard loads without exceptions."""
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    assert not at.exception
    assert "Dengue" in at.title[0].value


def test_dashboard_shows_reference_date_and_approved_visualizations() -> None:
    df = load_snapshot()
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)

    caption = at.caption[0].value
    assert get_reference_date(df).strftime("%d/%m/%Y") in caption
    assert str(df["SE"].iloc[-1]) in caption
    assert [m.label for m in at.metric] == [
        "Casos estimados na semana",
        "Nível de alerta",
        "Rt",
        "Incidência por 100 mil hab.",
    ]
    # sparkline, série principal, comparação sazonal e medidores
    assert len(at.get("plotly_chart")) == 4


def test_main_runs_streamlit_on_app_and_propagates_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=3)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(SystemExit) as exit_info:
        dashboard_main.main()

    assert exit_info.value.code == 3
    (cmd,) = calls
    assert cmd[:4] == [sys.executable, "-m", "streamlit", "run"]
    assert Path(cmd[4]).name == "app.py"
