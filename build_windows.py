"""Build Windows de Popref Local, lancé dans GitHub Actions sur windows-latest."""
from __future__ import annotations

import subprocess
import sys


def main() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--noconsole",
        "--name",
        "Popref",
        "--collect-all",
        "plotly",
        "--collect-all",
        "pandas",
        "--collect-all",
        "openpyxl",
        "--collect-all",
        "bs4",
        "--hidden-import",
        "multipart.multipart",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "local_app.py",
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
