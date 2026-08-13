"""Popref Local — interface autonome pour Windows.

Le programme démarre un serveur local, accessible uniquement depuis le poste de
l'utilisateur, puis ouvre l'interface dans le navigateur par défaut. Aucun fichier
Excel ni dossier généré ne quitte l'ordinateur, hormis les requêtes INSEE activées
explicitement dans l'interface.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import sys
import threading
import uuid
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from popref_core.assets import resolve_assets
from popref_core.excel_model import PoprefWorkbook, norm_geo_code
from popref_core.generate_pdf_html_only import generate_html
from popref_core.payload_builder import build_payload


APP_NAME = "Popref Local"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def local_data_dir() -> Path:
    """Dossier persistant de l'application, sans dépendre du répertoire de lancement."""
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
    directory = base / "Popref"
    for child in (directory, directory / "imports", directory / "assets", directory / "dossiers", directory / "logs"):
        child.mkdir(parents=True, exist_ok=True)
    return directory


DATA_DIR = local_data_dir()
logging.basicConfig(
    filename=DATA_DIR / "logs" / "popref-local.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ExcelSession:
    id: str
    original_name: str
    excel_path: Path
    assets_dir: Path
    communes: list[dict[str, str]]


@dataclass
class GenerationJob:
    id: str
    status: str
    commune_name: str
    created_at: str
    error: str | None = None
    output_path: Path | None = None
    diagnostic: dict[str, Any] | None = None


SESSIONS: dict[str, ExcelSession] = {}
JOBS: dict[str, GenerationJob] = {}
app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None)


def safe_filename(name: str) -> str:
    """Conserve un nom de fichier lisible sans permettre de sortie de répertoire."""
    return Path(name).name.replace("\x00", "") or "fichier.xlsx"


def list_communes(excel_path: Path) -> list[dict[str, str]]:
    """Lit les valeurs existantes de COM sans reconstituer les données métier."""
    workbook = PoprefWorkbook(excel_path)
    if "COM" not in workbook.sheet_names:
        raise ValueError("Le classeur ne contient pas l'onglet obligatoire « COM ».")
    table = workbook.read("COM")
    required = {"Code géographique", "Nom"}
    missing = required.difference(table.columns)
    if missing:
        raise ValueError("L'onglet COM ne contient pas les colonnes attendues : " + ", ".join(sorted(missing)))

    seen: set[str] = set()
    communes: list[dict[str, str]] = []
    for _, row in table.iterrows():
        code = norm_geo_code(row["Code géographique"])
        name = str(row["Nom"]).strip()
        if len(code) != 5 or not code.isdigit() or not name or code in seen:
            continue
        seen.add(code)
        communes.append({"code": code, "name": name, "label": f"{name} ({code})"})
    if not communes:
        raise ValueError("Aucune commune valide n'a été trouvée dans l'onglet COM.")
    return sorted(communes, key=lambda item: item["name"].casefold())


def run_generation(job: GenerationJob, session: ExcelSession, commune: str, include_insee: bool) -> None:
    """Construit le payload puis le dossier HTML, hors du fil HTTP principal."""
    try:
        job.status = "running"
        logger.info("Génération %s pour %s", job.id, commune)
        resolved_assets = resolve_assets(session.assets_dir, commune)
        payload = build_payload(
            str(session.excel_path),
            commune,
            assets=resolved_assets.assets,
            include_insee=include_insee,
        )
        payload["asset_diagnostics"] = resolved_assets.diagnostics
        output_dir = DATA_DIR / "dossiers" / job.id
        output_dir.mkdir(parents=True, exist_ok=True)
        payload_path = output_dir / "payload.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        commune_safe = "".join(char if char.isalnum() or char in "-_" else "_" for char in payload.get("commune_name", commune))
        html_path = output_dir / f"dossier_population_{commune_safe}.html"
        generate_html(str(payload_path), str(html_path))

        job.output_path = html_path
        job.diagnostic = {
            "commune": payload.get("commune_name", commune),
            "code_insee": payload.get("commune_code", ""),
            "region": payload.get("region_name", ""),
            "insee": payload.get("insee_diagnostics", {}),
            "asset_diagnostics": payload.get("asset_diagnostics", {}),
        }
        job.status = "done"
        logger.info("Génération %s terminée : %s", job.id, html_path)
    except Exception as exc:  # Toute erreur est exposée au client et journalisée localement.
        logger.exception("Échec de la génération %s", job.id)
        job.status = "error"
        job.error = str(exc)


class GenerateRequest(BaseModel):
    session_id: str
    commune: str
    include_insee: bool = True


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Popref Local</title><style>
:root{--navy:#002b4e;--blue:#0066a6;--gold:#d4a72c;--paper:#f6f8fa;--ink:#14212b;--muted:#61707b;--danger:#a22222}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--paper);color:var(--ink)}
header{background:var(--navy);color:#fff;padding:1rem max(1.25rem,calc((100% - 980px)/2));display:flex;align-items:center;gap:.75rem}.mark{background:var(--gold);color:var(--navy);font-weight:800;border-radius:6px;padding:.3rem .5rem}main{max-width:980px;margin:2.5rem auto;padding:0 1.25rem}.hero{margin-bottom:1.5rem}.hero h1{margin:0 0 .3rem;font-size:2rem}.hero p{margin:0;color:var(--muted)}.card{background:#fff;border:1px solid #dce2e8;border-radius:12px;padding:1.5rem;box-shadow:0 2px 8px #001a3320;margin-top:1rem}.hidden{display:none!important}label{display:block;font-weight:650;margin:1rem 0 .45rem}.drop{border:2px dashed #9dacb8;border-radius:10px;padding:2rem;text-align:center;background:#fbfcfd}.drop input{max-width:100%}button{border:0;border-radius:7px;padding:.7rem 1rem;background:var(--blue);color:#fff;font-weight:650;cursor:pointer;font-size:.95rem}button:disabled{opacity:.55;cursor:not-allowed}.secondary{background:#e7eef4;color:var(--navy)}.row{display:flex;gap:1rem;align-items:end;flex-wrap:wrap}.grow{flex:1 1 380px}.note{font-size:.9rem;color:var(--muted);line-height:1.45}.status{margin-top:1rem;border-left:4px solid var(--blue);padding:.75rem 1rem;background:#eef7fd}.error{border-color:var(--danger);background:#fff2f2;color:#751515}.success{border-color:#188449;background:#effbf3;color:#105d31}.check{display:flex;gap:.55rem;align-items:center;font-weight:400}.check input{width:1.1rem;height:1.1rem}.footer{margin-top:2rem;color:var(--muted);font-size:.83rem}
</style></head><body><header><span class="mark">P</span><strong>Popref Local</strong><span style="opacity:.7">— génération locale de dossiers de population de référence</span></header>
<main><section class="hero"><h1>Nouveau dossier</h1><p>Le classeur et le dossier généré restent sur cet ordinateur.</p></section>
<section id="import-card" class="card"><h2>1. Importer le fichier Excel Popref</h2><div class="drop"><input id="excel" type="file" accept=".xlsx,.xls"><p class="note">Sélectionnez le fichier INSEE au format Excel. Taille maximale : 50 Mo.</p><button id="import">Analyser le fichier</button></div><div id="import-status" class="status hidden"></div></section>
<section id="configure-card" class="card hidden"><h2>2. Configurer le dossier</h2><p id="file-summary" class="note"></p><div class="row"><div class="grow"><label for="commune">Commune</label><input id="commune" list="communes" placeholder="Saisissez un nom ou un code INSEE" style="width:100%;padding:.7rem;border:1px solid #aebbc6;border-radius:7px"><datalist id="communes"></datalist></div></div><label for="assets">Cartes lissées (facultatif)</label><input id="assets" type="file" accept="image/png" multiple><label class="check"><input id="insee" type="checkbox" checked>Enrichir avec les données publiques INSEE (connexion Internet nécessaire)</label><p class="note">La génération complète peut prendre plusieurs dizaines de secondes selon la commune et la disponibilité des pages INSEE.</p><button id="generate">Générer le dossier HTML</button><div id="generation-status" class="status hidden"></div></section>
<p class="footer">Les fichiers sont stockés dans le dossier local <code>Popref</code> de votre profil Windows. Consultez le dossier <code>logs</code en cas de difficulté.</p></main>
<script>
let sessionId=null;
const $=id=>document.getElementById(id); const notice=(id,text,kind='')=>{const el=$(id);el.className='status '+kind;el.textContent=text};
$('import').onclick=async()=>{const file=$('excel').files[0];if(!file){notice('import-status','Sélectionnez d’abord un fichier Excel.','error');return}const data=new FormData();data.append('excel',file);$('import').disabled=true;notice('import-status','Lecture du fichier et chargement des communes…');try{const res=await fetch('/api/import',{method:'POST',body:data});const body=await res.json();if(!res.ok)throw Error(body.detail||'Import impossible');sessionId=body.session_id;$('file-summary').textContent=`${body.original_name} — ${body.communes.length.toLocaleString('fr-FR')} communes disponibles.`;const list=$('communes');list.replaceChildren(...body.communes.map(c=>{const o=document.createElement('option');o.value=c.label;return o}));$('import-card').classList.add('hidden');$('configure-card').classList.remove('hidden')}catch(e){notice('import-status',e.message,'error')}finally{$('import').disabled=false}};
$('generate').onclick=async()=>{if(!sessionId)return;let commune=$('commune').value.trim();const code=commune.match(/\\((\\d{5})\\)$/);if(code)commune=code[1];if(!commune){notice('generation-status','Choisissez une commune.','error');return}const cards=[...$('assets').files];if(cards.length){const form=new FormData();form.append('session_id',sessionId);cards.forEach(f=>form.append('assets',f));const upload=await fetch('/api/assets',{method:'POST',body:form});if(!upload.ok){const b=await upload.json();notice('generation-status',b.detail||'Impossible d’importer les cartes.','error');return}}$('generate').disabled=true;notice('generation-status','Génération du dossier en cours…');try{const res=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:sessionId,commune,include_insee:$('insee').checked})});const body=await res.json();if(!res.ok)throw Error(body.detail||'Génération impossible');const timer=setInterval(async()=>{const poll=await fetch('/api/jobs/'+body.job_id);const j=await poll.json();if(j.status==='done'){clearInterval(timer);notice('generation-status','Dossier généré. Le téléchargement démarre.','success');window.location='/api/jobs/'+body.job_id+'/download';$('generate').disabled=false}else if(j.status==='error'){clearInterval(timer);notice('generation-status','Erreur : '+j.error,'error');$('generate').disabled=false}else notice('generation-status','Génération du dossier en cours…')},1200)}catch(e){notice('generation-status',e.message,'error');$('generate').disabled=false}};
</script></body></html>"""


@app.post("/api/import")
async def import_excel(excel: UploadFile = File(...)) -> dict[str, Any]:
    name = safe_filename(excel.filename or "fichier.xlsx")
    if Path(name).suffix.lower() not in {".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Le fichier doit être au format .xlsx ou .xls.")
    content = await excel.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 50 Mo.")
    session_id = uuid.uuid4().hex
    session_dir = DATA_DIR / "imports" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    excel_path = session_dir / name
    excel_path.write_bytes(content)
    try:
        communes = list_communes(excel_path)
    except Exception as exc:
        excel_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Fichier Popref invalide : {exc}") from exc
    assets_dir = DATA_DIR / "assets" / session_id
    assets_dir.mkdir(parents=True, exist_ok=True)
    SESSIONS[session_id] = ExcelSession(session_id, name, excel_path, assets_dir, communes)
    return {"session_id": session_id, "original_name": name, "communes": communes}


@app.post("/api/assets")
async def import_assets(session_id: str = Form(...), assets: list[UploadFile] = File(...)) -> dict[str, int]:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'import inconnue. Réimportez le fichier Excel.")
    copied = 0
    for asset in assets:
        name = safe_filename(asset.filename or "carte.png")
        if Path(name).suffix.lower() != ".png":
            continue
        content = await asset.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"La carte « {name} » dépasse la limite de 50 Mo.")
        (session.assets_dir / name).write_bytes(content)
        copied += 1
    return {"uploaded": copied}


@app.post("/api/generate")
def generate(request: GenerateRequest) -> dict[str, str]:
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session d'import inconnue. Réimportez le fichier Excel.")
    selected = next((item for item in session.communes if item["code"] == norm_geo_code(request.commune)), None)
    if not selected:
        selected = next((item for item in session.communes if item["name"].casefold() == request.commune.casefold()), None)
    if not selected:
        raise HTTPException(status_code=400, detail="La commune sélectionnée n'est pas présente dans le fichier importé.")
    job = GenerationJob(
        id=uuid.uuid4().hex,
        status="pending",
        commune_name=selected["name"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    JOBS[job.id] = job
    threading.Thread(
        target=run_generation,
        args=(job, session, selected["code"], request.include_insee),
        daemon=True,
    ).start()
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Génération inconnue.")
    response = asdict(job)
    response["output_path"] = str(job.output_path) if job.output_path else None
    return response


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str) -> FileResponse:
    job = JOBS.get(job_id)
    if not job or job.status != "done" or not job.output_path or not job.output_path.exists():
        raise HTTPException(status_code=404, detail="Le dossier n'est pas encore disponible.")
    return FileResponse(job.output_path, media_type="text/html", filename=job.output_path.name)


def available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def main() -> None:
    port = available_port()
    url = f"http://127.0.0.1:{port}"
    logger.info("Démarrage de %s sur %s", APP_NAME, url)
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
