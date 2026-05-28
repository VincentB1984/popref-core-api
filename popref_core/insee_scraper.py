from __future__ import annotations

from dataclasses import dataclass, asdict
from io import StringIO
from typing import Any
import re
import unicodedata

import pandas as pd
import requests
from bs4 import BeautifulSoup


INSEE_BASE_URL = "https://www.insee.fr/fr/statistiques/2011101"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}


@dataclass
class InseeScrapeResult:
    status: str
    message: str
    url: str
    data_naissances_deces: dict[str, Any] | None = None
    data_pop_t3: dict[str, Any] | None = None
    data_logements_categories: dict[str, Any] | None = None
    data_logements_historique: dict[str, Any] | None = None
    data_fam_t1: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def strip_accents(value: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", str(value))
        if unicodedata.category(c) != "Mn"
    )


def norm(value: Any) -> str:
    value = "" if value is None else str(value)
    value = strip_accents(value).casefold()
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(part) for part in col if str(part) != "nan").strip() for col in df.columns]
    else:
        df.columns = [str(col).strip() for col in df.columns]
    return df


def to_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).replace("\xa0", " ").strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    # Conserver le signe et le séparateur décimal français ; supprimer les espaces de milliers.
    text = text.replace(" ", "").replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def to_int(value: Any) -> int | None:
    num = to_float(value)
    if num is None:
        return None
    return int(round(num))


def fetch_soup(code_geo: str, type_geo: str, timeout: int = 30) -> tuple[str, BeautifulSoup]:
    if type_geo == "commune":
        geo = f"COM-{str(code_geo).zfill(5)}"
    elif type_geo == "region":
        geo = f"REG-{str(code_geo).zfill(2)}"
    else:
        raise ValueError(f"Type géographique non supporté : {type_geo}")
    url = f"{INSEE_BASE_URL}?geo={geo}"
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding
    return url, BeautifulSoup(response.text, "html.parser")


def table_context(table: Any) -> str:
    parts: list[str] = []
    caption = table.find("caption")
    if caption:
        parts.append(caption.get_text(" ", strip=True))
    previous = table.find_all_previous(limit=6)
    following = table.find_all_next(limit=2)
    for node in reversed(previous):
        if getattr(node, "name", None) in {"h2", "h3", "h4", "p", "span", "div"}:
            txt = node.get_text(" ", strip=True)
            if txt:
                parts.append(txt)
    for node in following:
        if getattr(node, "name", None) in {"h2", "h3", "h4", "p", "span", "div"}:
            txt = node.get_text(" ", strip=True)
            if txt:
                parts.append(txt)
    parts.append(table.get_text(" ", strip=True)[:2000])
    return " ".join(parts)


def html_table_to_df(table: Any) -> pd.DataFrame | None:
    try:
        dfs = pd.read_html(StringIO(str(table)), decimal=",", thousands=" ")
    except ValueError:
        return None
    if not dfs:
        return None
    return flatten_columns(dfs[0])


def all_tables(soup: BeautifulSoup) -> list[tuple[Any, str, pd.DataFrame]]:
    out: list[tuple[Any, str, pd.DataFrame]] = []
    for table in soup.find_all("table"):
        df = html_table_to_df(table)
        if df is None or df.empty:
            continue
        out.append((table, norm(table_context(table)), df))
    return out


def first_text_column(df: pd.DataFrame) -> str:
    return str(df.columns[0])


def find_table(tables: list[tuple[Any, str, pd.DataFrame]], *patterns: str) -> pd.DataFrame | None:
    compiled = [re.compile(pattern, re.I) for pattern in patterns]
    for _, context, df in tables:
        joined = norm(" ".join(map(str, df.columns)) + " " + df.astype(str).head(20).to_string())
        haystack = context + " " + joined
        if all(pattern.search(haystack) for pattern in compiled):
            return df
    return None


def extract_year_columns(df: pd.DataFrame, allowed: set[int] | None = None) -> dict[int, str]:
    result: dict[int, str] = {}
    for col in df.columns:
        for year in re.findall(r"(?:19|20)\d{2}", str(col)):
            y = int(year)
            if allowed is None or y in allowed:
                result.setdefault(y, str(col))
    return dict(sorted(result.items()))


def extract_naissances_deces(tables: list[tuple[Any, str, pd.DataFrame]]) -> dict[str, Any] | None:
    df = find_table(tables, r"rfd\s*g1|naissances.*deces|nes.*vivants.*decedes")
    if df is None:
        return None
    years = extract_year_columns(df)
    if not years:
        return None
    label_col = first_text_column(df)
    naissances: list[int] = []
    deces: list[int] = []
    kept_years: list[int] = []
    for y, col in years.items():
        n_val = d_val = None
        for _, row in df.iterrows():
            label = norm(row.get(label_col, ""))
            if re.search(r"naissance|nes vivants", label):
                n_val = to_int(row.get(col))
            if re.search(r"deces|decedes", label):
                d_val = to_int(row.get(col))
        if n_val is not None and d_val is not None:
            kept_years.append(y)
            naissances.append(n_val)
            deces.append(d_val)
    if not kept_years:
        return None
    return {"years": kept_years, "naissances": naissances, "deces": deces}


def extract_pop_t3(tables: list[tuple[Any, str, pd.DataFrame]]) -> dict[str, Any] | None:
    df = find_table(tables, r"pop\s*t3|population.*sexe.*age|hommes.*femmes", r"hommes", r"femmes")
    if df is None:
        return None
    cols = list(map(str, df.columns))
    label_col = cols[0]
    homme_col = next((c for c in cols if re.search(r"\bhommes?\b", norm(c))), None)
    femme_col = next((c for c in cols if re.search(r"\bfemmes?\b", norm(c))), None)
    if homme_col is None or femme_col is None:
        # Certaines tables multi-indexées donnent des noms composites ; on tente la détection par position.
        if len(cols) >= 3:
            homme_col, femme_col = cols[1], cols[2]
        else:
            return None
    tranches: list[str] = []
    hommes: list[int] = []
    femmes: list[int] = []
    for _, row in df.iterrows():
        label = str(row.get(label_col, "")).strip()
        nlabel = norm(label)
        if not re.search(r"ans|plus", nlabel) or re.search(r"ensemble|total", nlabel):
            continue
        h = to_int(row.get(homme_col))
        f = to_int(row.get(femme_col))
        if h is not None and f is not None:
            tranches.append(label)
            hommes.append(h)
            femmes.append(f)
    if not tranches:
        return None
    return {"tranches_age": tranches, "hommes": hommes, "femmes": femmes}


def extract_log_t1bis(tables: list[tuple[Any, str, pd.DataFrame]]) -> dict[str, Any] | None:
    # Cibler strictement LOG T1bis : LOG T1 contient les mêmes libellés mais des effectifs, pas des pourcentages.
    df = find_table(tables, r"log\s*t1bis", r"categories.*logements")
    if df is None:
        return None
    years = extract_year_columns(df, {2011, 2016, 2022})
    if not {2011, 2016, 2022}.issubset(years):
        return None
    label_col = first_text_column(df)
    categories: list[str] = []
    values: dict[int, list[float]] = {2011: [], 2016: [], 2022: []}
    for _, row in df.iterrows():
        label = str(row.get(label_col, "")).strip()
        nlabel = norm(label)
        if not re.search(r"residences principales|residences secondaires|logements vacants", nlabel):
            continue
        categories.append(label)
        for year in (2011, 2016, 2022):
            val = to_float(row.get(years[year]))
            values[year].append(val if val is not None else 0.0)
    if not categories:
        return None
    return {
        "categories": categories,
        "taux_2011": values[2011],
        "taux_2016": values[2016],
        "taux_2022": values[2022],
    }


def extract_log_t1(tables: list[tuple[Any, str, pd.DataFrame]]) -> dict[str, Any] | None:
    # Cibler strictement LOG T1 historique et exclure LOG T1bis.
    df = find_table(tables, r"log\s*t1\b|evolution.*nombre.*logements|1968.*1975.*1982", r"residences.*principales|logements.*vacants")
    if df is None:
        return None
    years = extract_year_columns(df)
    if not years:
        return None
    label_col = first_text_column(df)
    historique: dict[str, list[dict[str, Any]]] = {}
    for _, row in df.iterrows():
        label = str(row.get(label_col, "")).strip()
        nlabel = norm(label)
        if not re.search(r"ensemble.*logements|residences principales|residences secondaires|logements vacants", nlabel):
            continue
        serie: list[dict[str, Any]] = []
        for year, col in years.items():
            serie.append({"Annee": year, "Effectif": to_int(row.get(col)) or 0})
        historique[label] = serie
    if not historique:
        return None
    return {"years": list(years.keys()), "historique": historique}


def extract_fam_t1(tables: list[tuple[Any, str, pd.DataFrame]]) -> list[dict[str, Any]] | None:
    df = find_table(tables, r"fam\s*t1|menages.*composition")
    if df is None:
        return None
    return df.where(pd.notna(df), None).to_dict(orient="records")


def scrape_insee_complete(code_geo: str, type_geo: str) -> dict[str, Any]:
    try:
        url, soup = fetch_soup(code_geo, type_geo)
        tables = all_tables(soup)
        data_naissances_deces = extract_naissances_deces(tables)
        data_pop_t3 = extract_pop_t3(tables)
        data_logements_categories = extract_log_t1bis(tables)
        data_logements_historique = extract_log_t1(tables)
        data_fam_t1 = extract_fam_t1(tables)
        extracted = [
            data_naissances_deces,
            data_pop_t3,
            data_logements_categories,
            data_logements_historique,
            data_fam_t1,
        ]
        count = sum(1 for item in extracted if item)
        result = InseeScrapeResult(
            status="success" if count else "error",
            message=f"Extraction réussie : {count} tableaux sur 5",
            url=url,
            data_naissances_deces=data_naissances_deces,
            data_pop_t3=data_pop_t3,
            data_logements_categories=data_logements_categories,
            data_logements_historique=data_logements_historique,
            data_fam_t1=data_fam_t1,
        )
        return result.to_dict()
    except Exception as exc:  # noqa: BLE001 - journalisation explicite pour diagnostic métier
        return InseeScrapeResult(status="error", message=f"Erreur : {exc}", url="").to_dict()


def logements_historique_to_rows(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data or not data.get("historique"):
        return []
    hist = data["historique"]
    years = data.get("years") or []

    def find_series(pattern: str) -> dict[int, int]:
        for category, serie in hist.items():
            if re.search(pattern, norm(category)):
                return {int(item["Annee"]): int(item.get("Effectif") or 0) for item in serie}
        return {}

    principales = find_series(r"residences principales")
    secondaires = find_series(r"residences secondaires")
    vacants = find_series(r"logements vacants")
    rows = []
    for year in years:
        y = int(year)
        rows.append({
            "Année": y,
            "Résidences principales": principales.get(y),
            "Résidences secondaires et logements occasionnels": secondaires.get(y),
            "Logements vacants": vacants.get(y),
        })
    return rows


def logements_taux_to_rows(data: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not data or not data.get("categories"):
        return []
    rows = []
    for i, category in enumerate(data.get("categories", [])):
        rows.append({
            "Catégorie": category,
            "2011": (data.get("taux_2011") or [None])[i] if i < len(data.get("taux_2011") or []) else None,
            "2016": (data.get("taux_2016") or [None])[i] if i < len(data.get("taux_2016") or []) else None,
            "2022": (data.get("taux_2022") or [None])[i] if i < len(data.get("taux_2022") or []) else None,
        })
    return rows
