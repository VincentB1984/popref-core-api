from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re
import unicodedata


COMMUNES_WITH_IRIS_MAPS = {
    "audincourt",
    "autun",
    "belfort",
    "besancon",
    "chalon-sur-saone",
    "cosne-cours-sur-loire",
    "dijon",
    "dole",
    "hericourt",
    "le-creusot",
    "lons-le-saunier",
    "macon",
    "montbeliard",
    "montceau-les-mines",
    "nevers",
    "pontarlier",
    "talant",
    "valentigney",
}

GLOBAL_MAP_CANDIDATES = {
    "carte_france_2012_2017": [
        "france_2012_2017.png",
        "France_2012_2017.png",
        "carte_france_2012_2017.png",
        "carte_lissee_france_2012_2017.png",
    ],
    "carte_france_2017_2023": [
        "france_2017_2023.png",
        "France_2017_2023.png",
        "carte_france_2017_2023.png",
        "carte_lissee_france_2017_2023.png",
    ],
    "carte_bfc_2012_2017": [
        "bfc_2012_2017.png",
        "BFC_2012_2017.png",
        "bourgogne_franche_comte_2012_2017.png",
        "carte_bfc_2012_2017.png",
    ],
    "carte_bfc_2017_2023": [
        "bfc_2017_2023.png",
        "BFC_2017_2023.png",
        "bourgogne_franche_comte_2017_2023.png",
        "carte_bfc_2017_2023.png",
    ],
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.replace("'", " ").replace("’", " ")
    ascii_value = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-")
    return ascii_value.casefold()


@dataclass(frozen=True)
class AssetResolution:
    assets: dict[str, str | None]
    diagnostics: dict[str, Any]


def _find_first(asset_dir: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        p = asset_dir / candidate
        if p.exists() and p.is_file():
            return p
    return None


def _find_commune_map(asset_dir: Path, commune_name: str) -> Path | None:
    raw_candidates = [
        f"{commune_name}.png",
        f"{commune_name.replace(' ', '_')}.png",
        f"{slugify(commune_name)}.png",
    ]
    found = _find_first(asset_dir, raw_candidates)
    if found:
        return found

    target_slug = slugify(commune_name)
    for p in asset_dir.glob("*.png"):
        if slugify(p.stem) == target_slug:
            return p
    return None


def resolve_assets(asset_dir: str | Path | None, commune_name: str) -> AssetResolution:
    """Résout les chemins de cartes à partir d’un dossier portable.

    Le dossier attendu contient idéalement cinq images PNG : deux cartes France,
    deux cartes Bourgogne-Franche-Comté et, si disponible, une carte IRIS de la
    commune. La fonction n’échoue pas si les fichiers sont absents : elle renvoie
    simplement des chemins nuls et des diagnostics exploitables par l’interface.
    """
    keys = list(GLOBAL_MAP_CANDIDATES) + ["carte_commune"]
    empty = {key: None for key in keys}
    if not asset_dir:
        return AssetResolution(empty, {"status": "not_configured", "message": "Aucun dossier d’assets de cartes n’a été fourni."})

    root = Path(asset_dir)
    if not root.exists() or not root.is_dir():
        return AssetResolution(empty, {"status": "missing_directory", "message": f"Le dossier d’assets n’existe pas : {root}"})

    assets: dict[str, str | None] = {}
    found: dict[str, str] = {}
    missing: list[str] = []

    for key, candidates in GLOBAL_MAP_CANDIDATES.items():
        path = _find_first(root, candidates)
        assets[key] = str(path) if path else None
        if path:
            found[key] = str(path)
        else:
            missing.append(key)

    commune_slug = slugify(commune_name)
    if commune_slug in COMMUNES_WITH_IRIS_MAPS:
        commune_path = _find_commune_map(root, commune_name)
        assets["carte_commune"] = str(commune_path) if commune_path else None
        if commune_path:
            found["carte_commune"] = str(commune_path)
        else:
            missing.append("carte_commune")
    else:
        assets["carte_commune"] = None

    status = "complete" if not missing else "partial"
    return AssetResolution(
        assets,
        {
            "status": status,
            "asset_dir": str(root),
            "found": found,
            "missing": missing,
            "commune_slug": commune_slug,
        },
    )
