"""
Microservice FastAPI — popref_core
Expose le moteur de génération Popref via une API REST.
Déployé sur Render, appelé par le serveur Node.js de l'application web.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Popref Core API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────
API_SECRET = os.environ.get("POPREF_API_SECRET", "")


def check_auth(authorization: str | None) -> None:
    if not API_SECRET:
        return  # No secret configured → open (dev mode)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    if authorization.removeprefix("Bearer ").strip() != API_SECRET:
        raise HTTPException(status_code=403, detail="Invalid token")


# ── Schemas ───────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    excel_b64: str          # Base64-encoded Excel file bytes
    commune: str            # Commune name or INSEE code
    include_insee: bool = False
    assets: dict[str, str] = {}  # { assetKey: base64_png_bytes }


class GenerateResponse(BaseModel):
    html_b64: str           # Base64-encoded HTML output
    payload_json: dict[str, Any]
    stderr: str = ""


class HealthResponse(BaseModel):
    status: str
    python: str
    popref_core: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse)
def health():
    try:
        import popref_core  # noqa: F401
        core_status = "ok"
    except ImportError as e:
        core_status = f"error: {e}"
    return {
        "status": "ok",
        "python": sys.version,
        "popref_core": core_status,
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(
    req: GenerateRequest,
    authorization: str | None = Header(default=None),
):
    check_auth(authorization)

    tmp_dir = tempfile.mkdtemp(prefix="popref-")
    try:
        # Write Excel file
        excel_path = Path(tmp_dir) / "input.xlsx"
        excel_path.write_bytes(base64.b64decode(req.excel_b64))

        # Write asset PNGs
        assets_dir = Path(tmp_dir) / "assets"
        assets_dir.mkdir()
        for asset_key, asset_b64 in req.assets.items():
            (assets_dir / asset_key).write_bytes(base64.b64decode(asset_b64))

        json_out = Path(tmp_dir) / "payload.json"
        html_out = Path(tmp_dir) / "dossier.html"

        cmd = [
            sys.executable, "-m", "popref_core.cli",
            "--excel", str(excel_path),
            "--commune", req.commune,
            "--json", str(json_out),
            "--html", str(html_out),
        ]
        if req.include_insee:
            cmd.append("--include-insee")
        if any(assets_dir.iterdir()):
            cmd += ["--assets-dir", str(assets_dir)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"popref_core exited with code {result.returncode}",
                    "stderr": result.stderr[-3000:],
                    "stdout": result.stdout[-1000:],
                },
            )

        html_bytes = html_out.read_bytes() if html_out.exists() else b""
        payload = json.loads(json_out.read_text(encoding="utf-8")) if json_out.exists() else {}

        return {
            "html_b64": base64.b64encode(html_bytes).decode(),
            "payload_json": payload,
            "stderr": result.stderr[-500:],
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/extract-communes")
def extract_communes(
    body: dict,
    authorization: str | None = Header(default=None),
):
    """Extract commune list from an Excel file (base64-encoded)."""
    check_auth(authorization)

    excel_b64 = body.get("excel_b64", "")
    if not excel_b64:
        raise HTTPException(status_code=400, detail="Missing excel_b64")

    tmp_dir = tempfile.mkdtemp(prefix="popref-extract-")
    try:
        excel_path = Path(tmp_dir) / "input.xlsx"
        excel_path.write_bytes(base64.b64decode(excel_b64))

        import math
        import pandas as pd

        wb_com = pd.read_excel(str(excel_path), sheet_name="COM", header=None)
        pcap_col = None
        name_col = None
        for col in wb_com.columns:
            vals = wb_com[col].astype(str).str.strip()
            if vals.str.match(r"^\d{5}$").any():
                pcap_col = col
            if vals.str.len().gt(3).sum() > 5 and not vals.str.match(r"^\d").any():
                name_col = col

        communes = []
        if pcap_col is not None and name_col is not None:
            for _, row in wb_com.iterrows():
                code = str(row[pcap_col]).strip()
                name = str(row[name_col]).strip()
                if not code or not name or code == "nan" or name == "nan":
                    continue
                if not code.isdigit() or len(code) != 5:
                    continue
                dep_code = code[:2] if not code.startswith("97") else code[:3]
                communes.append({
                    "code": code,
                    "name": name,
                    "departement": dep_code,
                    "region": "",
                })

        return {"communes": communes}

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
