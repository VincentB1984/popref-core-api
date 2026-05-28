from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import math

import pandas as pd

from .excel_model import PoprefWorkbook, CommuneSelection, to_number, clean_records
from .insee_scraper import scrape_insee_complete, logements_historique_to_rows, logements_taux_to_rows


def round_or_none(value: Any, digits: int = 2) -> float | None:
    num = to_number(value)
    if num is None:
        return None
    return round(float(num), digits)


def annual_growth(start: Any, end: Any, years: int = 6) -> float | None:
    s = to_number(start)
    e = to_number(end)
    if not s or not e:
        return None
    return round(((float(e) / float(s)) ** (1 / years) - 1) * 100, 2)


def encode_png(path: str | Path | None) -> str | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def build_commune_data(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pop_2012": to_number(row.get("Population au 1er janvier 2012")),
        "pop_2017": to_number(row.get("Population au 1er janvier 2017")),
        "pop_2023": to_number(row.get("Population au 1er janvier 2023")),
        "tx_var_annuel": to_number(row.get("Taux de variation annuel moyen 1/1/2017-1/1/2023")),
        "tx_solde_naturel": to_number(row.get("Taux de variation annuel moyen dû au solde naturel 1/1/2017-1/1/2023")),
        "tx_solde_migratoire": to_number(row.get("Taux de variation annuel moyen dû au solde migratoire 1/1/2017-1/1/2023")),
    }


def build_departements_data(workbook: PoprefWorkbook, selection: CommuneSelection) -> list[dict[str, Any]]:
    df = workbook.department_rows_for_region(selection)
    records = []
    for row in clean_records(df):
        records.append({
            "code_dept": str(row.get("Code géographique")).zfill(2),
            "nom_dept": row.get("Nom"),
            "pop_2023": to_number(row.get("Population au 1er janvier 2023")),
            "pop_2017": to_number(row.get("Population au 1er janvier 2017")),
            "pop_2012": to_number(row.get("Population au 1er janvier 2012")),
            "evol_2017_2023": to_number(row.get("Taux de variation annuel moyen 1/1/2017-1/1/2023")),
            "solde_naturel_2017_2023": to_number(row.get("Taux de variation annuel moyen dû au solde naturel 1/1/2017-1/1/2023")),
            "solde_migratoire_2017_2023": to_number(row.get("Taux de variation annuel moyen dû au solde migratoire 1/1/2017-1/1/2023")),
            "evol_2012_2017": to_number(row.get("Taux de variation annuel moyen 1/1/2012-1/1/2017")),
            "solde_naturel_2012_2017": to_number(row.get("Taux de variation annuel moyen dû au solde naturel 1/1/2012-1/1/2017")),
            "solde_migratoire_2012_2017": to_number(row.get("Taux de variation annuel moyen dû au solde migratoire 1/1/2012-1/1/2017")),
        })
    # Le générateur HTML existant calcule et ajoute lui-même la ligne régionale
    # à partir des départements transmis. On ne doit donc pas injecter ici la
    # région comme pseudo-département, sous peine d’obtenir une ligne en trop
    # dans le tableau régional.
    return records


def build_pop_ville_data(workbook: PoprefWorkbook, selection: CommuneSelection) -> dict[str, Any] | None:
    df = workbook.pop_city_sheet(selection)
    if df is None or len(df) < 34:
        return None

    # Avec pandas header=0, la ligne Excel 2 est index 0 et la ligne Excel 8 est index 6.
    r2023 = df.iloc[0]
    r2017 = df.iloc[6]

    pop_mun_2023 = to_number(r2023.get("Population municipale"))
    pop_mun_2017 = to_number(r2017.get("Population municipale"))
    pcap_2023 = to_number(r2023.get("PCAP"))
    pcap_2017 = to_number(r2017.get("PCAP"))
    pop_totale_2023 = (pop_mun_2023 or 0) + (pcap_2023 or 0)
    pop_totale_2017 = (pop_mun_2017 or 0) + (pcap_2017 or 0)

    # Le bloc des contributions est repéré par son libellé plutôt que par un index fixe.
    contrib_row = None
    first_col = df.columns[0]
    for _, row in df.iterrows():
        if str(row.get(first_col, "")).strip().casefold() == "sexennale 2017-2023":
            contrib_row = row
            break

    return {
        "pop_totale_2017": pop_totale_2017,
        "pop_totale_2023": pop_totale_2023,
        "evol_pop_totale": annual_growth(pop_totale_2017, pop_totale_2023),
        "pcap_2017": pcap_2017,
        "pcap_2023": pcap_2023,
        "evol_pcap": annual_growth(pcap_2017, pcap_2023),
        "pop_mun_2017": pop_mun_2017,
        "pop_mun_2023": pop_mun_2023,
        "evol_pop_mun": annual_growth(pop_mun_2017, pop_mun_2023),
        "pop_menages_2017": to_number(r2017.get("Population")),
        "pop_menages_2023": to_number(r2023.get("Population")),
        "en_hotel_2017": to_number(r2017.get("en hôtel hors adresses d'habitation")),
        "en_hotel_2023": to_number(r2023.get("en hôtel hors adresses d'habitation")),
        "en_log_comm_2017": to_number(r2017.get("en logement des communautés")),
        "en_log_comm_2023": to_number(r2023.get("en logement des communautés")),
        "pop_communautes_2017": to_number(r2017.get("Population des communautés")),
        "pop_communautes_2023": to_number(r2023.get("Population des communautés")),
        "pop_hmsa_2017": to_number(r2017.get("Population HMSA")),
        "pop_hmsa_2023": to_number(r2023.get("Population HMSA")),
        "contrib_population": to_number(contrib_row.iloc[1]) if contrib_row is not None else None,
        "contrib_communautes": to_number(contrib_row.iloc[2]) if contrib_row is not None else None,
        "contrib_hmsa": to_number(contrib_row.iloc[3]) if contrib_row is not None else None,
        "contrib_menages": to_number(contrib_row.iloc[4]) if contrib_row is not None else None,
        "logements_2017": to_number(r2017.get("Nombre de logements BSA (total de calage)")),
        "logements_2023": to_number(r2023.get("Nombre de logements BSA (total de calage)")),
        "contrib_logements": to_number(contrib_row.iloc[5]) if contrib_row is not None else None,
        "contrib_taux_rp": to_number(contrib_row.iloc[6]) if contrib_row is not None else None,
        "pers_par_rp_2017": to_number(r2017.get("Nombre de personnes par résidences principales")),
        "pers_par_rp_2023": to_number(r2023.get("Nombre de personnes par résidences principales")),
        "taux_rp_2017": to_number(r2017.get("Taux de résidence principal")),
        "taux_rp_2023": to_number(r2023.get("Taux de résidence principal")),
        "contrib_pers_par_rp": to_number(contrib_row.iloc[7]) if contrib_row is not None else None,
    }


def build_rates(workbook: PoprefWorkbook, selection: CommuneSelection) -> dict[str, Any]:
    row_2025 = workbook.rate_row("Taux", selection) or {}
    row_2024 = workbook.rate_row("Taux2024", selection) or {}
    row_2023 = workbook.rate_row("Taux2023", selection) or {}
    fane_2025 = workbook.rate_row("FANE2025", selection) or {}
    fane_2024 = workbook.rate_row("FANE2024", selection) or {}
    fane_2023 = workbook.rate_row("FANE2023", selection) or {}

    internet_2023_col = "Tx_reponse_internet"
    internet_2024_col = "Tx_reponse_internet"
    internet_2025_col = "Tx_reponse_internet"
    flne_2023_col = "Tx_FLNE"
    flne_2024_col = "Tx_FLNE"
    flne_2025_col = "Tx_FLNE"

    ti23_min, ti23_max = workbook.rate_minmax("Taux2023", internet_2023_col)
    ti24_min, ti24_max = workbook.rate_minmax("Taux2024", internet_2024_col)
    ti25_min, ti25_max = workbook.rate_minmax("Taux", internet_2025_col)
    fl23_min, fl23_max = workbook.rate_minmax("Taux2023", flne_2023_col)
    fl24_min, fl24_max = workbook.rate_minmax("Taux2024", flne_2024_col)
    fl25_min, fl25_max = workbook.rate_minmax("Taux", flne_2025_col)
    fa23_min, fa23_max = workbook.rate_minmax("FANE2023", "TX_FANE")
    fa24_min, fa24_max = workbook.rate_minmax("FANE2024", "TX_FANE")
    fa25_min, fa25_max = workbook.rate_minmax("FANE2025", "TX_FANE")

    return {
        "taux_internet_2023": to_number(row_2023.get("Tx_reponse_internet")),
        "taux_internet_2024": to_number(row_2024.get("Tx_reponse_internet")),
        "taux_internet_2025": to_number(row_2025.get("Tx_reponse_internet")),
        "taux_flne_2023": to_number(row_2023.get("Tx_FLNE")),
        "taux_flne_2024": to_number(row_2024.get("Tx_FLNE")),
        "taux_flne_2025": to_number(row_2025.get("Tx_FLNE")),
        "taux_fane_2023": to_number(fane_2023.get("TX_FANE")),
        "taux_fane_2024": to_number(fane_2024.get("TX_FANE")),
        "taux_fane_2025": to_number(fane_2025.get("TX_FANE")),
        "taux_internet_2023_min": ti23_min,
        "taux_internet_2023_max": ti23_max,
        "taux_internet_2024_min": ti24_min,
        "taux_internet_2024_max": ti24_max,
        "taux_internet_2025_min": ti25_min,
        "taux_internet_2025_max": ti25_max,
        "taux_flne_2023_min": fl23_min,
        "taux_flne_2023_max": fl23_max,
        "taux_flne_2024_min": fl24_min,
        "taux_flne_2024_max": fl24_max,
        "taux_flne_2025_min": fl25_min,
        "taux_flne_2025_max": fl25_max,
        "taux_fane_2023_min": fa23_min,
        "taux_fane_2023_max": fa23_max,
        "taux_fane_2024_min": fa24_min,
        "taux_fane_2024_max": fa24_max,
        "taux_fane_2025_min": fa25_min,
        "taux_fane_2025_max": fa25_max,
    }


def build_payload(
    excel_path: str | Path,
    commune: str,
    *,
    assets: dict[str, str | Path | None] | None = None,
    include_insee: bool = False,
) -> dict[str, Any]:
    workbook = PoprefWorkbook(excel_path)
    selection = workbook.select_commune(commune)
    commune_row = workbook.commune_row(selection)
    assets = assets or {}

    insee_commune: dict[str, Any] | None = None
    insee_region: dict[str, Any] | None = None
    if include_insee:
        insee_commune = scrape_insee_complete(selection.code, "commune")
        insee_region = scrape_insee_complete(selection.region_code, "region")

    payload: dict[str, Any] = {
        "commune_name": selection.name,
        "commune_code": selection.code,
        "region_name": selection.region_name,
        "region_code": selection.region_code,
        "data_commune": build_commune_data(commune_row),
        "data_departements": build_departements_data(workbook, selection),
        "data_logements_historique": logements_historique_to_rows(insee_commune.get("data_logements_historique")) if insee_commune else [],
        "data_logements_taux": logements_taux_to_rows(insee_commune.get("data_logements_categories")) if insee_commune else [],
        "data_naissances_deces_commune": insee_commune.get("data_naissances_deces") if insee_commune else None,
        "data_naissances_deces_region": insee_region.get("data_naissances_deces") if insee_region else None,
        "data_pop_commune": insee_commune.get("data_pop_t3") if insee_commune else None,
        "data_pop_region": insee_region.get("data_pop_t3") if insee_region else None,
        "insee_diagnostics": {
            "commune": {"status": insee_commune.get("status"), "message": insee_commune.get("message"), "url": insee_commune.get("url")} if insee_commune else None,
            "region": {"status": insee_region.get("status"), "message": insee_region.get("message"), "url": insee_region.get("url")} if insee_region else None,
        },
        "carte_france_2012_2017": encode_png(assets.get("carte_france_2012_2017")),
        "carte_france_2017_2023": encode_png(assets.get("carte_france_2017_2023")),
        "carte_bfc_2012_2017": encode_png(assets.get("carte_bfc_2012_2017")),
        "carte_bfc_2017_2023": encode_png(assets.get("carte_bfc_2017_2023")),
        "carte_commune": encode_png(assets.get("carte_commune")),
        "data_pop_ville": build_pop_ville_data(workbook, selection),
    }
    payload.update(build_rates(workbook, selection))
    return payload
