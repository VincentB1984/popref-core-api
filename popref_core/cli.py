from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .payload_builder import build_payload
from .assets import resolve_assets


def write_json(payload: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Construire un payload Popref Python depuis le fichier Excel d'entrée.")
    parser.add_argument("--excel", required=True, help="Chemin du fichier Excel Popref.")
    parser.add_argument("--commune", required=True, help="Nom ou code géographique de la commune.")
    parser.add_argument("--json", required=True, help="Chemin du JSON de sortie.")
    parser.add_argument("--html", help="Chemin HTML à générer avec le générateur existant.")
    parser.add_argument("--include-insee", action="store_true", help="Interroger l’INSEE et inclure logements, pyramide des âges et naissances-décès.")
    parser.add_argument("--assets-dir", help="Dossier portable contenant les cartes lissées PNG à intégrer au dossier généré.")
    parser.add_argument("--carte-france-2012-2017")
    parser.add_argument("--carte-france-2017-2023")
    parser.add_argument("--carte-bfc-2012-2017")
    parser.add_argument("--carte-bfc-2017-2023")
    parser.add_argument("--carte-commune")
    args = parser.parse_args(argv)

    resolved = resolve_assets(args.assets_dir, args.commune)
    cli_assets = {
        "carte_france_2012_2017": args.carte_france_2012_2017,
        "carte_france_2017_2023": args.carte_france_2017_2023,
        "carte_bfc_2012_2017": args.carte_bfc_2012_2017,
        "carte_bfc_2017_2023": args.carte_bfc_2017_2023,
        "carte_commune": args.carte_commune,
    }
    assets = {**resolved.assets, **{k: v for k, v in cli_assets.items() if v}}

    payload = build_payload(
        args.excel,
        args.commune,
        assets=assets,
        include_insee=args.include_insee,
    )
    payload["asset_diagnostics"] = resolved.diagnostics
    json_path = Path(args.json)
    write_json(payload, json_path)

    if args.html:
        generator = Path(__file__).with_name("generate_pdf_html_only.py")
        subprocess.run(
            [sys.executable, str(generator), str(json_path), args.html],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
