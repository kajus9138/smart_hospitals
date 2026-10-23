"""Atalho para subir o dashboard: uv run dashboard (ou python -m smart_hospitals.dashboard)."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).parent / "app.py"
    result = subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
