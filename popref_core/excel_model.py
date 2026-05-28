from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import math
import re

import pandas as pd


REGION_DEPARTMENTS: dict[str, list[str]] = {
    "11": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "24": ["18", "28", "36", "37", "41", "45"],
    "27": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "28": ["14", "27", "50", "61", "76"],
    "32": ["02", "59", "60", "62", "80"],
    "44": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "52": ["44", "49", "53", "72", "85"],
    "53": ["22", "29", "35", "56"],
    "75": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "76": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "84": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "93": ["04", "05", "06", "13", "83", "84"],
    "94": ["2A", "2B"],
}

REGION_NAMES: dict[str, str] = {
    "11": "Île-de-France",
    "24": "Centre-Val de Loire",
    "27": "Bourgogne-Franche-Comté",
    "28": "Normandie",
    "32": "Hauts-de-France",
    "44": "Grand Est",
    "52": "Pays de la Loire",
    "53": "Bretagne",
    "75": "Nouvelle-Aquitaine",
    "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes",
    "93": "Provence-Alpes-Côte d'Azur",
    "94": "Corse",
}

DEPARTMENT_TO_REGION = {
    dep: reg for reg, deps in REGION_DEPARTMENTS.items() for dep in deps
}


@dataclass(frozen=True)
class CommuneSelection:
    code: str
    name: str
    department_code: str
    region_code: str
    region_name: str


def norm_str(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def norm_geo_code(value: Any) -> str:
    text = norm_str(value)
    if text.isdigit() and len(text) < 5:
        return text.zfill(5)
    return text


def norm_local_commune_code(value: Any) -> str:
    text = norm_str(value)
    if text.isdigit():
        return text.zfill(3)
    return text


def to_number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).replace("\xa0", " ").replace(" ", "").replace(",", ".").strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        num = float(text)
        return int(num) if num.is_integer() else num
    except ValueError:
        return None


def clean_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return df.astype(object).where(pd.notna(df), None).to_dict(orient="records")


class PoprefWorkbook:
    """Lecteur métier minimal du fichier Excel Popref.

    Cette classe reproduit d'abord les lectures utilisées par le Shiny pour la
    génération du dossier HTML. Les calculs sont volontairement limités : si une
    valeur existe déjà dans le classeur, elle est lue directement plutôt que
    recalculée.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._sheets = pd.ExcelFile(self.path)

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheets.sheet_names)

    def read(self, sheet: str, header: int | None = 0) -> pd.DataFrame:
        df = pd.read_excel(self.path, sheet_name=sheet, header=header)
        if header is not None:
            df.columns = [str(c).strip() for c in df.columns]
        return df

    def select_commune(self, code_or_name: str) -> CommuneSelection:
        df = self.read("COM")
        query = code_or_name.strip()
        by_code = df["Code géographique"].map(norm_geo_code).eq(norm_geo_code(query))
        by_name = df["Nom"].astype(str).str.casefold().eq(query.casefold())
        match = df[by_code | by_name]
        if match.empty:
            raise ValueError(f"Commune introuvable dans l'onglet COM : {code_or_name}")
        row = match.iloc[0]
        code = norm_geo_code(row["Code géographique"])
        dep = code[:2] if not code.startswith("97") else code[:3]
        region_code = DEPARTMENT_TO_REGION.get(dep, "")
        region_name = REGION_NAMES.get(region_code, "Région")
        return CommuneSelection(
            code=code,
            name=str(row["Nom"]),
            department_code=dep,
            region_code=region_code,
            region_name=region_name,
        )

    def commune_row(self, selection: CommuneSelection) -> dict[str, Any]:
        df = self.read("COM")
        row = df[df["Code géographique"].map(norm_geo_code).eq(selection.code)]
        if row.empty:
            raise ValueError(f"Commune absente de COM : {selection.code}")
        return clean_records(row)[0]

    def region_row(self, selection: CommuneSelection) -> dict[str, Any] | None:
        df = self.read("REG")
        row = df[df["Code géographique"].map(norm_str).eq(selection.region_code)]
        return clean_records(row)[0] if not row.empty else None

    def department_rows_for_region(self, selection: CommuneSelection) -> pd.DataFrame:
        dep_codes = REGION_DEPARTMENTS.get(selection.region_code, [])
        df = self.read("DEP")
        mask = df["Code géographique"].map(lambda x: norm_str(x).zfill(2)).isin(dep_codes)
        return df[mask].copy()

    def pop_city_sheet(self, selection: CommuneSelection) -> pd.DataFrame | None:
        expected = f"pop_{selection.name}"
        sheet = next((s for s in self.sheet_names if s.casefold() == expected.casefold()), None)
        if not sheet:
            return None
        return self.read(sheet, header=0)

    def pop_city_raw(self, selection: CommuneSelection) -> pd.DataFrame | None:
        expected = f"pop_{selection.name}"
        sheet = next((s for s in self.sheet_names if s.casefold() == expected.casefold()), None)
        if not sheet:
            return None
        return self.read(sheet, header=None)

    def rate_row(self, sheet: str, selection: CommuneSelection) -> dict[str, Any] | None:
        df = self.read(sheet)
        local_code = selection.code[-3:]

        def canonical(col: str) -> str:
            return "".join(ch for ch in col.lower() if ch.isalnum())

        dep_col = None
        com_col = None
        name_col = None
        for col in df.columns:
            key = canonical(str(col))
            if key in {"codedepartement", "codedep", "depcode", "dep"}:
                dep_col = col
            elif key in {"codecommune", "codecom", "comcode"}:
                com_col = col
            elif key in {"commune", "libellecommune", "nomcom"}:
                name_col = col

        if dep_col is not None and com_col is not None:
            dep_mask = df[dep_col].map(lambda x: norm_str(x).zfill(2)).eq(selection.department_code)
            com_mask = df[com_col].map(norm_local_commune_code).eq(local_code)
            rows = df[dep_mask & com_mask]
            if not rows.empty:
                return clean_records(rows)[0]

        if name_col is not None:
            rows = df[df[name_col].astype(str).str.casefold().eq(selection.name.casefold())]
            if not rows.empty:
                return clean_records(rows)[0]

        return None

    def rate_minmax(self, sheet: str, value_col: str) -> tuple[float | None, float | None]:
        df = self.read(sheet)
        if value_col not in df.columns:
            return None, None
        values = pd.to_numeric(df[value_col], errors="coerce").dropna()
        if values.empty:
            return None, None
        return float(values.min()), float(values.max())
