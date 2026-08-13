"""Validation réelle de Popref Local à partir d’un classeur INSEE.

Exemple :
    python validate_reference.py /chemin/01_france_2023_geo2025.xlsx 01001
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from popref_core.generate_pdf_html_only import generate_html
from popref_core.payload_builder import build_payload
from popref_core.excel_model import PoprefWorkbook


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python validate_reference.py <fichier.xlsx> <code_insee>")
        return 2
    excel_path = Path(sys.argv[1]).resolve()
    commune_code = sys.argv[2].strip()
    if not excel_path.exists():
        print(f"Fichier introuvable : {excel_path}")
        return 2

    workbook = PoprefWorkbook(excel_path)
    communes = workbook.read("COM")
    selection = workbook.select_commune(commune_code)
    print(f"Classeur : {excel_path.name} ({excel_path.stat().st_size / 1024 / 1024:.1f} Mo)")
    print(f"Feuilles : {len(workbook.sheet_names)}")
    print(f"Communes disponibles : {len(communes)}")
    print(f"Commune testée : {selection.name} ({selection.code}), {selection.region_name}")

    print("Collecte des données INSEE et construction du dossier…")
    payload = build_payload(
        excel_path,
        selection.code,
        assets={},
        include_insee=True,
    )
    out_dir = Path("validation-output") / selection.code
    out_dir.mkdir(parents=True, exist_ok=True)
    payload_path = out_dir / "payload.json"
    html_path = out_dir / "dossier_population.html"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    generate_html(str(payload_path), str(html_path))

    required_payload_keys = {
        "commune_name",
        "commune_code",
        "region_name",
        "data_commune",
        "data_departements",
        "data_pop_ville",
        "insee_diagnostics",
    }
    missing = required_payload_keys.difference(payload)
    if missing:
        raise RuntimeError("Clés manquantes dans le payload : " + ", ".join(sorted(missing)))
    if not html_path.exists() or html_path.stat().st_size < 10_000:
        raise RuntimeError("Le HTML généré est absent ou anormalement petit.")
    html = html_path.read_text(encoding="utf-8")
    if selection.name not in html:
        raise RuntimeError("Le nom de la commune est absent du dossier HTML.")

    print(f"HTML généré : {html_path.resolve()} ({html_path.stat().st_size / 1024:.0f} Ko)")
    print("Diagnostic INSEE :")
    print(json.dumps(payload.get("insee_diagnostics", {}), ensure_ascii=False, indent=2))
    print("VALIDATION RÉUSSIE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
