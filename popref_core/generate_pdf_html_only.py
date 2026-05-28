# -*- coding: utf-8 -*-
"""
Script pour générer un dossier HTML professionnel à partir des données JSON
Le HTML peut ensuite être imprimé en PDF depuis un navigateur
"""

import json
import sys
import os

def safe_float(value, default=None):
    """
    Convertit une valeur en float de manière sécurisée.
    Gère les cas: None, dict, list, string, number
    """
    if value is None:
        return default
    
    # Si c'est déjà un nombre
    if isinstance(value, (int, float)):
        return float(value)
    
    # Si c'est un dict ou une list (erreur de sérialisation JSON)
    if isinstance(value, (dict, list)):
        return default
    
    # Si c'est une string
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    
    # Autre type
    return default

def format_number(value):
    """Formate un nombre avec des espaces pour les milliers"""
    try:
        if value is None or value == '':
            return ''
        # Convertir en nombre
        num = float(str(value).replace(' ', '').replace(',', '.'))
        # Si c'est un entier
        if num.is_integer():
            return f"{int(num):,}".replace(',', ' ')
        # Si c'est un décimal
        return f"{num:,.2f}".replace(',', ' ').replace('.', ',')
    except:
        return str(value)

def format_number_pop(n):
    """Formate un nombre pour le tableau de population (avec tiret si None)"""
    if n is None:
        return "-"
    try:
        return f"{int(n):,}".replace(",", " ")
    except:
        return str(n)

def format_decimal(n, decimals=2):
    """Formate un décimal avec virgule comme séparateur"""
    if n is None:
        return "-"
    try:
        return f"{float(n):.{decimals}f}".replace(".", ",")
    except:
        return str(n)

def generate_html(data_json_file, output_html):
    """Génère un fichier HTML professionnel"""
    
    # Charger les données JSON
    with open(data_json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    commune_name = data.get('commune_name', 'Commune')
    commune_code = data.get('commune_code', '')
    region_name = data.get('region_name', 'Région')
    region_code = data.get('region_code', '')
    
    # Vérifier si la commune est en Bourgogne-Franche-Comté (code région 27)
    is_bfc = str(region_code) == '27'
    
    data_commune = data.get('data_commune', [])
    data_departements = data.get('data_departements', [])
    data_logements_historique = data.get('data_logements_historique', [])
    data_logements_taux = data.get('data_logements_taux', [])
    data_nd_commune = data.get('data_naissances_deces_commune', None)
    data_nd_region = data.get('data_naissances_deces_region', None)
    data_pop_commune = data.get('data_pop_commune', None)
    data_pop_region = data.get('data_pop_region', None)
    
    # Taux pour les bâtons de gendarmes (3 années)
    taux_internet_2023 = data.get('taux_internet_2023', None)
    taux_internet_2024 = data.get('taux_internet_2024', None)
    taux_internet_2025 = data.get('taux_internet_2025', None)
    taux_flne_2023 = data.get('taux_flne_2023', None)
    taux_flne_2024 = data.get('taux_flne_2024', None)
    taux_flne_2025 = data.get('taux_flne_2025', None)
    taux_fane_2023 = data.get('taux_fane_2023', None)
    taux_fane_2024 = data.get('taux_fane_2024', None)
    taux_fane_2025 = data.get('taux_fane_2025', None)
    taux_internet_2023_min = data.get('taux_internet_2023_min', None)
    taux_internet_2023_max = data.get('taux_internet_2023_max', None)
    taux_internet_2024_min = data.get('taux_internet_2024_min', None)
    taux_internet_2024_max = data.get('taux_internet_2024_max', None)
    taux_internet_2025_min = data.get('taux_internet_2025_min', None)
    taux_internet_2025_max = data.get('taux_internet_2025_max', None)
    taux_flne_2023_min = data.get('taux_flne_2023_min', None)
    taux_flne_2023_max = data.get('taux_flne_2023_max', None)
    taux_flne_2024_min = data.get('taux_flne_2024_min', None)
    taux_flne_2024_max = data.get('taux_flne_2024_max', None)
    taux_flne_2025_min = data.get('taux_flne_2025_min', None)
    taux_flne_2025_max = data.get('taux_flne_2025_max', None)
    taux_fane_2023_min = data.get('taux_fane_2023_min', None)
    taux_fane_2023_max = data.get('taux_fane_2023_max', None)
    taux_fane_2024_min = data.get('taux_fane_2024_min', None)
    taux_fane_2024_max = data.get('taux_fane_2024_max', None)
    taux_fane_2025_min = data.get('taux_fane_2025_min', None)
    taux_fane_2025_max = data.get('taux_fane_2025_max', None)
    
    # Images de cartes (base64)
    carte_france_2012_2017 = data.get('carte_france_2012_2017', None)
    carte_france_2017_2023 = data.get('carte_france_2017_2023', None)
    carte_bfc_2012_2017 = data.get('carte_bfc_2012_2017', None)
    carte_bfc_2017_2023 = data.get('carte_bfc_2017_2023', None)
    carte_commune = data.get('carte_commune', None)
    
    # Données pop_ville (décomposition population)
    data_pop_ville = data.get('data_pop_ville', None)
    
    # Convertir data_commune en liste si c'est un objet
    if data_commune and not isinstance(data_commune, list):
        data_commune = [data_commune]
    
    # Début du HTML
    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dossier Population - {commune_name}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        @page {{
            size: A4 landscape;
            margin: 1.5cm;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: white;
            font-size: 13pt;
        }}
        
        .page {{
            page-break-after: always;
            min-height: 25cm;
        }}
        
        .header {{
            display: flex;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #003366;
        }}
        
        .logo {{
            width: 80px;
            height: 80px;
            margin-right: 20px;
        }}
        
        h1 {{
            color: #003366;
            font-size: 30px;
            margin: 0;
            text-align: center;
            flex: 1;
        }}
        
        h2 {{
            color: #003366;
            font-size: 22px;
            margin: 25px 0 12px 0;
            padding-bottom: 5px;
            border-bottom: 2px solid #003366;
        }}
        
        h3 {{
            color: #555;
            font-size: 17px;
            margin: 15px 0 8px 0;
        }}
        
        table {{
            width: 95%;
            border-collapse: collapse;
            margin: 15px auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-size: 12pt;
        }}
        
        th {{
            background: linear-gradient(to bottom, #f5e6d3, #e8d4b8);
            color: #333;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #d0c0a8;
        }}
        
        th.numeric {{
            text-align: right;
        }}
        
        td {{
            padding: 8px 10px;
            border: 1px solid #ddd;
        }}
        
        td.label {{
            font-weight: 500;
            background-color: #fafafa;
        }}
        
        td.numeric {{
            text-align: right;
            font-family: 'Courier New', monospace;
        }}
        
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        tr:hover {{
            background-color: #f0f0f0;
        }}
        
        .source {{
            font-style: italic;
            color: #666;
            font-size: 11pt;
            margin: 5px 0;
        }}
        
        .note {{
            color: #555;
            font-size: 11pt;
            margin: 5px 0 15px 0;
            line-height: 1.4;
        }}
        
        .chart-container {{
            width: 100%;
            height: 650px;
            margin: 20px auto;
            max-width: 95%;
        }}
        
        .chart-row {{
            display: flex;
            gap: 20px;
            margin: 20px auto;
            max-width: 95%;
        }}
        
        .chart-half {{
            flex: 1;
            height: 600px;
        }}
        
        .carte-iris-container {{
            page-break-inside: avoid;
            text-align: center;
            margin: 20px auto;
        }}
        
        .carte-iris-container img {{
            max-width: 90%;
            max-height: 18cm;
            object-fit: contain;
        }}
        
        @media print {{
            body {{
                padding: 0;
            }}
            .page {{
                page-break-after: always;
            }}
            .chart-container, .chart-half, .carte-iris-container {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>

<div class="page" style="position: relative; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; min-height: 25cm;">
    <img src="https://journeeseconomieautrement.fr/wp-content/uploads/2025/10/partenaire-insee-bfc-2025-500.jpg" alt="Logo Insee BFC" style="position: absolute; top: 30px; left: 30px; height: 250px;">
    <img src="https://static.neopse.com/thumbs/p/2073/site/09/be/d4/09bed445042831eb30e35c4c8147186d64e64e67.png?v=v1" alt="Logo Recensement 2026" style="position: absolute; top: 30px; right: 30px; height: 250px;">
    <div style="max-width: 800px;">
        <h1 style="font-size: 72px; font-weight: bold; margin: 40px 0; border: none; line-height: 1.3;">Dossier Population<br>de référence 2023</h1>
        <h2 style="font-size: 56px; color: #003366; margin: 60px 0; border: none; font-weight: bold;">{commune_name}</h2>
        <p style="font-size: 24px; color: #666; margin-top: 80px;">Code commune : {commune_code}</p>
        <p style="font-size: 24px; color: #666;">Région : {region_name}</p>
    </div>
</div>
'''
    
    # Ajouter les pages de cartes si les images existent
    if carte_france_2012_2017 or carte_france_2017_2023:
        html += '''<div class="page">
    <h1 style="text-align: center; color: #003366; margin-bottom: 40px;">Évolution démographique en France métropolitaine</h1>
    <div style="display: flex; gap: 20px; justify-content: center; align-items: center;">'''
        
        if carte_france_2012_2017:
            html += f'''
        <div style="flex: 1; text-align: center;">
            <img src="{carte_france_2012_2017}" alt="Carte France 2012-2017" style="max-width: 100%; height: auto;">
        </div>'''
        
        if carte_france_2017_2023:
            html += f'''
        <div style="flex: 1; text-align: center;">
            <img src="{carte_france_2017_2023}" alt="Carte France 2017-2023" style="max-width: 100%; height: auto;">
        </div>'''
        
        html += '''
    </div>
</div>
'''
    
    # Afficher les cartes BFC uniquement si la commune est en Bourgogne-Franche-Comté
    if is_bfc and (carte_bfc_2012_2017 or carte_bfc_2017_2023):
        html += '''<div class="page">
    <h1 style="text-align: center; color: #003366; margin-bottom: 40px;">Évolution démographique en région Bourgogne-Franche-Comté</h1>
    <div style="display: flex; gap: 20px; justify-content: center; align-items: center;">'''
        
        if carte_bfc_2012_2017:
            html += f'''
        <div style="flex: 1; text-align: center;">
            <img src="{carte_bfc_2012_2017}" alt="Carte BFC 2012-2017" style="max-width: 100%; height: auto;">
        </div>'''
        
        if carte_bfc_2017_2023:
            html += f'''
        <div style="flex: 1; text-align: center;">
            <img src="{carte_bfc_2017_2023}" alt="Carte BFC 2017-2023" style="max-width: 100%; height: auto;">
        </div>'''
        
        html += '''
    </div>
</div>
'''
    
    html += '''<div class="page">
    <h2>Évolution de la population de la commune</h2>
    <table>
        <tr>
            <th style="width: 60%;">Indicateur</th>
            <th class="numeric">Valeur</th>
        </tr>
'''
    
    # Données commune
    if len(data_commune) > 0:
        row = data_commune[0]
        
        # Mapping des clés vers des labels lisibles
        labels = {
            'pop_2012': 'Population au 1er janvier 2012',
            'pop_2017': 'Population au 1er janvier 2017',
            'pop_2023': 'Population au 1er janvier 2023',
            'tx_var_annuel': 'Taux de variation annuel moyen 1/1/2017-1/1/2023 (%)',
            'tx_solde_naturel': 'Taux de variation dû au solde naturel (%)',
            'tx_solde_migratoire': 'Taux de variation dû au solde migratoire (%)'
        }
        
        for key, val in row.items():
            label = labels.get(key, key)
            formatted_val = format_number(val)
            html += f'        <tr>\n'
            html += f'            <td class="label">{label}</td>\n'
            html += f'            <td class="numeric">{formatted_val}</td>\n'
            html += f'        </tr>\n'
    
    html += '''    </table>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Les données présentent l'évolution démographique de la commune avec les taux de variation dus au solde naturel (naissances - décès) et au solde migratoire (arrivées - départs).</p>
    
    <h2>Évolution démographique régionale</h2>
    <table>
        <tr>
            <th rowspan="2" style="width: 25%;">Départements</th>
            <th colspan="3" style="text-align: center;">Variation 2012-2017</th>
            <th colspan="3" style="text-align: center;">Variation 2017-2023</th>
        </tr>
        <tr>
            <th class="numeric">Moyenne<br>annuelle (%)</th>
            <th class="numeric">... dû au<br>solde<br>naturel<br>(en‰)</th>
            <th class="numeric">... dû au<br>solde<br>migratoire<br>(en‰)</th>
            <th class="numeric">Moyenne<br>annuelle (%)</th>
            <th class="numeric">... dû au<br>solde<br>naturel<br>(en‰)</th>
            <th class="numeric">... dû au<br>solde<br>migratoire<br>(en‰)</th>
        </tr>
'''
    
    # Données départements
    def get_color_style(value):
        """Retourne le style de couleur selon la valeur (bleu positif, rouge négatif)"""
        try:
            num = float(str(value).replace(' ', '').replace(',', '.'))
            if num > 0:
                return 'color: #0066CC;'  # Bleu pour positif
            elif num < 0:
                return 'color: #CC0000;'  # Rouge pour négatif
            else:
                return ''
        except:
            return ''
    
    for row in data_departements:
        nom_dept = row.get('nom_dept', '')
        # Période 2017-2023
        evol_2017_2023_raw = row.get('evol_2017_2023', '')
        evol_2017_2023 = format_number(evol_2017_2023_raw)
        solde_nat_2017_2023_raw = row.get('solde_naturel_2017_2023', '')
        solde_nat_2017_2023 = format_number(solde_nat_2017_2023_raw)
        solde_mig_2017_2023_raw = row.get('solde_migratoire_2017_2023', '')
        solde_mig_2017_2023 = format_number(solde_mig_2017_2023_raw)
        # Période 2012-2017
        evol_2012_2017_raw = row.get('evol_2012_2017', '')
        evol_2012_2017 = format_number(evol_2012_2017_raw)
        solde_nat_2012_2017_raw = row.get('solde_naturel_2012_2017', '')
        solde_nat_2012_2017 = format_number(solde_nat_2012_2017_raw)
        solde_mig_2012_2017_raw = row.get('solde_migratoire_2012_2017', '')
        solde_mig_2012_2017 = format_number(solde_mig_2012_2017_raw)
        
        # Couleurs pour les variations
        color_evol_2017_2023 = get_color_style(evol_2017_2023_raw)
        color_nat_2017_2023 = get_color_style(solde_nat_2017_2023_raw)
        color_mig_2017_2023 = get_color_style(solde_mig_2017_2023_raw)
        color_evol_2012_2017 = get_color_style(evol_2012_2017_raw)
        color_nat_2012_2017 = get_color_style(solde_nat_2012_2017_raw)
        color_mig_2012_2017 = get_color_style(solde_mig_2012_2017_raw)
        
        html += f'        <tr>\n'
        html += f'            <td class="label">{nom_dept}</td>\n'
        html += f'            <td class="numeric" style="font-weight: bold; {color_evol_2012_2017}">{evol_2012_2017}</td>\n'
        html += f'            <td class="numeric" style="{color_nat_2012_2017}">{solde_nat_2012_2017}</td>\n'
        html += f'            <td class="numeric" style="{color_mig_2012_2017}">{solde_mig_2012_2017}</td>\n'
        html += f'            <td class="numeric" style="font-weight: bold; {color_evol_2017_2023}">{evol_2017_2023}</td>\n'
        html += f'            <td class="numeric" style="{color_nat_2017_2023}">{solde_nat_2017_2023}</td>\n'
        html += f'            <td class="numeric" style="{color_mig_2017_2023}">{solde_mig_2017_2023}</td>\n'
        html += f'        </tr>\n'
    
    # Calculer les totaux régionaux
    if data_departements:
        # Sommes des populations
        total_pop_2012 = sum([row.get('pop_2012', 0) or 0 for row in data_departements])
        total_pop_2017 = sum([row.get('pop_2017', 0) or 0 for row in data_departements])
        total_pop_2023 = sum([row.get('pop_2023', 0) or 0 for row in data_departements])
        
        # Calcul des évolutions moyennes pour la région
        if total_pop_2017 > 0:
            evol_region_2017_2023 = ((total_pop_2023 - total_pop_2017) / total_pop_2017) * 100 / 6
        else:
            evol_region_2017_2023 = 0
            
        if total_pop_2012 > 0:
            evol_region_2012_2017 = ((total_pop_2017 - total_pop_2012) / total_pop_2012) * 100 / 5
        else:
            evol_region_2012_2017 = 0
        
        # Calcul des soldes moyens pondérés pour la région
        # Pour 2017-2023
        solde_nat_2017_2023_sum = 0
        solde_mig_2017_2023_sum = 0
        for row in data_departements:
            pop = row.get('pop_2017', 0) or 0
            if pop > 0:
                solde_nat_2017_2023_sum += (row.get('solde_naturel_2017_2023', 0) or 0) * pop
                solde_mig_2017_2023_sum += (row.get('solde_migratoire_2017_2023', 0) or 0) * pop
        
        if total_pop_2017 > 0:
            solde_nat_region_2017_2023 = solde_nat_2017_2023_sum / total_pop_2017
            solde_mig_region_2017_2023 = solde_mig_2017_2023_sum / total_pop_2017
        else:
            solde_nat_region_2017_2023 = 0
            solde_mig_region_2017_2023 = 0
        
        # Pour 2012-2017
        solde_nat_2012_2017_sum = 0
        solde_mig_2012_2017_sum = 0
        for row in data_departements:
            pop = row.get('pop_2012', 0) or 0
            if pop > 0:
                solde_nat_2012_2017_sum += (row.get('solde_naturel_2012_2017', 0) or 0) * pop
                solde_mig_2012_2017_sum += (row.get('solde_migratoire_2012_2017', 0) or 0) * pop
        
        if total_pop_2012 > 0:
            solde_nat_region_2012_2017 = solde_nat_2012_2017_sum / total_pop_2012
            solde_mig_region_2012_2017 = solde_mig_2012_2017_sum / total_pop_2012
        else:
            solde_nat_region_2012_2017 = 0
            solde_mig_region_2012_2017 = 0
        
        # Formater les valeurs
        evol_region_2012_2017_fmt = format_number(evol_region_2012_2017)
        solde_nat_region_2012_2017_fmt = format_number(solde_nat_region_2012_2017)
        solde_mig_region_2012_2017_fmt = format_number(solde_mig_region_2012_2017)
        evol_region_2017_2023_fmt = format_number(evol_region_2017_2023)
        solde_nat_region_2017_2023_fmt = format_number(solde_nat_region_2017_2023)
        solde_mig_region_2017_2023_fmt = format_number(solde_mig_region_2017_2023)
        
        # Couleurs
        color_evol_2012_2017 = get_color_style(evol_region_2012_2017)
        color_nat_2012_2017 = get_color_style(solde_nat_region_2012_2017)
        color_mig_2012_2017 = get_color_style(solde_mig_region_2012_2017)
        color_evol_2017_2023 = get_color_style(evol_region_2017_2023)
        color_nat_2017_2023 = get_color_style(solde_nat_region_2017_2023)
        color_mig_2017_2023 = get_color_style(solde_mig_region_2017_2023)
        
        # Ajouter la ligne de total régional
        html += f'''        <tr style="background-color: #e8f4f8; font-weight: bold;">
            <td class="label" style="font-weight: bold;">{region_name}</td>
            <td class="numeric" style="font-weight: bold; {color_evol_2012_2017}">{evol_region_2012_2017_fmt}</td>
            <td class="numeric" style="{color_nat_2012_2017}">{solde_nat_region_2012_2017_fmt}</td>
            <td class="numeric" style="{color_mig_2012_2017}">{solde_mig_region_2012_2017_fmt}</td>
            <td class="numeric" style="font-weight: bold; {color_evol_2017_2023}">{evol_region_2017_2023_fmt}</td>
            <td class="numeric" style="{color_nat_2017_2023}">{solde_nat_region_2017_2023_fmt}</td>
            <td class="numeric" style="{color_mig_2017_2023}">{solde_mig_region_2017_2023_fmt}</td>
        </tr>
'''
    
    html += f'''    </table>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Évolution annuelle moyenne de la population entre 2012-2017 et 2017-2023 pour les départements de la région {region_name}, avec décomposition en solde naturel et solde migratoire.</p>
</div>

'''
    
    # PAGE 2 : Naissances/Décès
    if data_nd_commune and data_nd_commune.get('years'):
        html += '''<div class="page">
    <h2>Naissances et Décès</h2>
    <div class="chart-row">
        <div class="chart-half" id="chart_nd_commune"></div>
        <div class="chart-half" id="chart_nd_region"></div>
    </div>
    <p class="source">Source : Insee, État civil</p>
    <p class="note">Lecture : Évolution du nombre de naissances et de décès sur la période. Le graphique de gauche présente les données de la commune, celui de droite les données de la région.</p>
'''
        
        # Générer les graphiques avec Plotly
        years_commune = data_nd_commune.get('years', [])
        naissances_commune = data_nd_commune.get('naissances', [])
        deces_commune = data_nd_commune.get('deces', [])
        
        html += f'''
    <script>
        var trace_naiss_c = {{
            x: {json.dumps(years_commune)},
            y: {json.dumps(naissances_commune)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Naissances',
            line: {{color: 'green', width: 3}},
            marker: {{size: 8}}
        }};
        var trace_deces_c = {{
            x: {json.dumps(years_commune)},
            y: {json.dumps(deces_commune)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Décès',
            line: {{color: 'red', width: 3}},
            marker: {{size: 8}}
        }};
        var layout_c = {{
            title: 'Commune : {commune_name}',
            xaxis: {{title: 'Année'}},
            yaxis: {{title: 'Nombre'}},
            showlegend: true,
            legend: {{x: 0.1, y: 1}}
        }};
        Plotly.newPlot('chart_nd_commune', [trace_naiss_c, trace_deces_c], layout_c, {{responsive: true}});
'''
        
        if data_nd_region and data_nd_region.get('years'):
            years_region = data_nd_region.get('years', [])
            naissances_region = data_nd_region.get('naissances', [])
            deces_region = data_nd_region.get('deces', [])
            
            html += f'''
        var trace_naiss_r = {{
            x: {json.dumps(years_region)},
            y: {json.dumps(naissances_region)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Naissances',
            line: {{color: 'green', width: 3}},
            marker: {{size: 8}}
        }};
        var trace_deces_r = {{
            x: {json.dumps(years_region)},
            y: {json.dumps(deces_region)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Décès',
            line: {{color: 'red', width: 3}},
            marker: {{size: 8}}
        }};
        var layout_r = {{
            title: 'Région : {region_name}',
            xaxis: {{title: 'Année'}},
            yaxis: {{title: 'Nombre'}},
            showlegend: true,
            legend: {{x: 0.1, y: 1}}
        }};
        Plotly.newPlot('chart_nd_region', [trace_naiss_r, trace_deces_r], layout_r, {{responsive: true}});
'''
        
        html += '''    </script>
</div>

'''
    
    # Ajouter le tableau de décomposition de la population si les données sont disponibles
    if data_pop_ville:
        # Utiliser les fonctions globales format_number_pop et format_decimal
        html += f'''<div class="page">
    <h1 style="text-align: center; color: #003366; margin-bottom: 30px;">Éléments de calcul des populations de référence - {commune_name}</h1>
    
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 17px;">
        <thead>
            <tr style="background-color: #003366; color: white;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;"></th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">2017</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">2023</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Évolution annuelle moyenne 2017/2023</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background-color: #e8f4f8;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Population municipale</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pop_mun_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pop_mun_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_decimal(data_pop_ville.get('evol_pop_mun'))} %</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont Population des ménages</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_menages_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_menages_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;"></td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont en hôtel hors adresses d'habitation</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('en_hotel_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('en_hotel_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;"></td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont en logement des communautés</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('en_log_comm_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('en_log_comm_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;"></td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont Population des communautés</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_communautes_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_communautes_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;"></td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont Population HMSA</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_hmsa_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_hmsa_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;"></td>
            </tr>
            <tr style="background-color: #e8f4f8;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Population comptée à part</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pcap_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pcap_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_decimal(data_pop_ville.get('evol_pcap'))} %</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Population totale</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pop_totale_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_number_pop(data_pop_ville.get('pop_totale_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{format_decimal(data_pop_ville.get('evol_pop_totale'))} %</td>
            </tr>
        </tbody>
    </table>
    
    <h2 style="color: #003366; margin-top: 40px; margin-bottom: 20px;">Éléments du calcul de la population municipale</h2>
    
    <table style="width: 100%; border-collapse: collapse; font-size: 17px;">
        <thead>
            <tr style="background-color: #003366; color: white;">
                <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Éléments du calcul</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">2017</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">2023</th>
                <th style="padding: 12px; text-align: right; border: 1px solid #ddd;">Contribution à l'évolution</th>
            </tr>
        </thead>
        <tbody>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd;">Population des communautés</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_communautes_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_communautes_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('contrib_communautes'))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Population des ménages</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_menages_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('pop_menages_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('contrib_menages'))}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont nombre de logements</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('logements_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_number_pop(data_pop_ville.get('logements_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('contrib_logements'))}</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont taux de résidence principale (%)</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('taux_rp_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('taux_rp_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('contrib_taux_rp'))}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #ddd; padding-left: 30px; font-style: italic;">dont nombre de personnes par résidence principale</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('pers_par_rp_2017'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('pers_par_rp_2023'))}</td>
                <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{format_decimal(data_pop_ville.get('contrib_pers_par_rp'))}</td>
            </tr>
        </tbody>
    </table>
    
    <p style="margin-top: 30px; font-size: 15px; color: #666; font-style: italic;">Source : Insee, recensements de la population 2017 et 2023.</p>
</div>
'''
    # PAGE 3 : Pyramide des âges
    if data_pop_commune and data_pop_commune.get('tranches_age'):
        html += '''<div class="page">
    <h2>Pyramide des âges - Comparaison Commune / Région</h2>
    <div class="chart-container" id="chart_pyramide"></div>
    <p class="source">Source : Insee, Recensement de la population</p>
    <p class="note">Lecture : Répartition de la population par tranche d'âge et par sexe. Les barres représentent la commune, les courbes avec marqueurs représentent la région.</p>
'''
        
        tranches_age = data_pop_commune.get('tranches_age', [])
        hommes_commune = data_pop_commune.get('hommes', [])
        femmes_commune = data_pop_commune.get('femmes', [])
        
        # Calculer les pourcentages pour la commune
        total_commune = sum([h + f for h, f in zip(hommes_commune, femmes_commune)])
        hommes_pct_c = [100 * h / total_commune if total_commune > 0 else 0 for h in hommes_commune]
        femmes_pct_c = [-100 * f / total_commune if total_commune > 0 else 0 for f in femmes_commune]
        
        html += f'''
    <script>
        var trace_femmes_c = {{
            y: {json.dumps(tranches_age)},
            x: {json.dumps(femmes_pct_c)},
            type: 'bar',
            orientation: 'h',
            name: 'Femmes - Commune',
            marker: {{color: 'pink'}}
        }};
        var trace_hommes_c = {{
            y: {json.dumps(tranches_age)},
            x: {json.dumps(hommes_pct_c)},
            type: 'bar',
            orientation: 'h',
            name: 'Hommes - Commune',
            marker: {{color: 'lightblue'}}
        }};
        var traces = [trace_femmes_c, trace_hommes_c];
'''
        
        if data_pop_region and data_pop_region.get('tranches_age'):
            hommes_region = data_pop_region.get('hommes', [])
            femmes_region = data_pop_region.get('femmes', [])
            
            total_region = sum([h + f for h, f in zip(hommes_region, femmes_region)])
            hommes_pct_r = [100 * h / total_region if total_region > 0 else 0 for h in hommes_region]
            femmes_pct_r = [-100 * f / total_region if total_region > 0 else 0 for f in femmes_region]
            
            html += f'''
        var trace_femmes_r = {{
            y: {json.dumps(tranches_age)},
            x: {json.dumps(femmes_pct_r)},
            type: 'scatter',
            mode: 'lines+markers',
            orientation: 'h',
            name: 'Femmes - Région',
            line: {{color: 'rgb(255, 20, 147)', width: 2}},
            marker: {{color: 'rgb(255, 20, 147)', size: 6}}
        }};
        var trace_hommes_r = {{
            y: {json.dumps(tranches_age)},
            x: {json.dumps(hommes_pct_r)},
            type: 'scatter',
            mode: 'lines+markers',
            orientation: 'h',
            name: 'Hommes - Région',
            line: {{color: 'rgb(0, 100, 200)', width: 2}},
            marker: {{color: 'rgb(0, 100, 200)', size: 6}}
        }};
        traces.push(trace_femmes_r);
        traces.push(trace_hommes_r);
'''
        
        html += f'''
        var layout_pyr = {{
            title: 'Pyramide des âges - {commune_name} vs {region_name}',
            xaxis: {{
                title: 'Pourcentage de la population',
                tickvals: [-10, -5, 0, 5, 10],
                ticktext: ['10%', '5%', '0%', '5%', '10%']
            }},
            yaxis: {{
                title: 'Tranche d\\'\u00e2ge',
                autorange: true
            }},
            barmode: 'overlay',
            showlegend: true
        }};
        Plotly.newPlot('chart_pyramide', traces, layout_pyr, {{responsive: true}});
    </script>
</div>

'''
    
    # PAGE 4 : Logements
    html += '''<div class="page">
    <h2>Évolution du nombre de logements</h2>
    <table>
        <tr>
            <th style="width: 15%;">Année</th>
            <th class="numeric">Résidences principales</th>
            <th class="numeric">Résidences secondaires</th>
            <th class="numeric">Logements vacants</th>
        </tr>
'''
    
    for row in data_logements_historique:
        annee = row.get('categorie', row.get('Année', ''))
        principales = format_number(row.get('Résidences principales', ''))
        secondaires = format_number(row.get('Résidences secondaires et logements occasionnels', ''))
        vacants = format_number(row.get('Logements vacants', ''))
        
        html += f'        <tr>\n'
        html += f'            <td class="label">{annee}</td>\n'
        html += f'            <td class="numeric">{principales}</td>\n'
        html += f'            <td class="numeric">{secondaires}</td>\n'
        html += f'            <td class="numeric">{vacants}</td>\n'
        html += f'        </tr>\n'
    
    html += '''    </table>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Évolution du parc de logements par catégorie depuis 1968. Les résidences principales sont les logements occupés de manière habituelle et à titre principal.</p>
'''
    
    # Générer le graphique base 100
    if len(data_logements_historique) > 0:
        html += '''
    <h2>Évolution des logements (Base 100 en 1968)</h2>
    <div class="chart-container" id="chart_logements_base100"></div>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Évolution indexée du nombre de logements par catégorie (base 100 en 1968).</p>
'''
        annees = []
        principales_base100 = []
        secondaires_base100 = []
        vacants_base100 = []
        
        principales_1968 = None
        secondaires_1968 = None
        vacants_1968 = None
        
        for row in data_logements_historique:
            annee = row.get('categorie', row.get('Année', ''))
            principales = row.get('Résidences principales', 0)
            secondaires = row.get('Résidences secondaires et logements occasionnels', 0)
            vacants = row.get('Logements vacants', 0)
            
            try:
                annees.append(int(annee))
                principales = float(principales) if principales else 0
                secondaires = float(secondaires) if secondaires else 0
                vacants = float(vacants) if vacants else 0
                
                if principales_1968 is None:
                    principales_1968 = principales if principales > 0 else 1
                    secondaires_1968 = secondaires if secondaires > 0 else 1
                    vacants_1968 = vacants if vacants > 0 else 1
                
                principales_base100.append(100 * principales / principales_1968)
                secondaires_base100.append(100 * secondaires / secondaires_1968)
                vacants_base100.append(100 * vacants / vacants_1968)
            except:
                pass
        
        html += f'''
    <script>
        var trace_principales = {{
            x: {json.dumps(annees)},
            y: {json.dumps(principales_base100)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Résidences principales',
            line: {{color: 'blue', width: 3}},
            marker: {{size: 8}}
        }};
        var trace_secondaires = {{
            x: {json.dumps(annees)},
            y: {json.dumps(secondaires_base100)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Résidences secondaires',
            line: {{color: 'orange', width: 3}},
            marker: {{size: 8}}
        }};
        var trace_vacants = {{
            x: {json.dumps(annees)},
            y: {json.dumps(vacants_base100)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Logements vacants',
            line: {{color: 'red', width: 3}},
            marker: {{size: 8}}
        }};
        var layout_log = {{
            xaxis: {{title: 'Année'}},
            yaxis: {{title: 'Indice (base 100 en 1968)'}},
            showlegend: true,
            legend: {{x: 0.1, y: 1}}
        }};
        Plotly.newPlot('chart_logements_base100', [trace_principales, trace_secondaires, trace_vacants], layout_log, {{responsive: true}});
    </script>
'''
    
    # Tableau des taux de logements
    if len(data_logements_taux) > 0:
        html += '''    <h2>Répartition des logements (%)</h2>
    <table>
        <tr>
            <th style="width: 40%;">Type de logement</th>
            <th class="numeric">2011</th>
            <th class="numeric">2016</th>
            <th class="numeric">2022</th>
        </tr>
'''
        
        for row in data_logements_taux:
            categorie = row.get('type', row.get('Catégorie', ''))
            taux_2011 = format_number(row.get('2011', ''))
            taux_2016 = format_number(row.get('2016', ''))
            taux_2022 = format_number(row.get('2022', ''))
            
            html += f'        <tr>\n'
            html += f'            <td class="label">{categorie}</td>\n'
            html += f'            <td class="numeric">{taux_2011}</td>\n'
            html += f'            <td class="numeric">{taux_2016}</td>\n'
            html += f'            <td class="numeric">{taux_2022}</td>\n'
            html += f'        </tr>\n'
        
        html += '''    </table>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Part de chaque catégorie de logements dans le total des logements de la commune.</p>
'''
    
    # Page des bâtons de gendarmes (taux 2023-2025)
    has_flne = any([taux_flne_2023, taux_flne_2024, taux_flne_2025])
    has_fane = any([taux_fane_2023, taux_fane_2024, taux_fane_2025])
    has_internet = any([taux_internet_2023, taux_internet_2024, taux_internet_2025])
    if has_internet or has_flne or has_fane:
        html += '''<div class="page">
    <h2>Indicateurs 2025</h2>
    <div style="display: flex; justify-content: space-around; margin: 30px 0;">'''
        
        # Bâtons de gendarmes pour Internet (2023, 2024, 2025)
        if has_internet:
            html += '''
        <div style="text-align: center; flex: 1; padding: 30px; margin: 10px;">
            <h3 style="margin-bottom: 40px;">Taux de réponse Internet (2023-2025)</h3>
            <div style="display: flex; justify-content: space-around; align-items: flex-end;">'''
            
            # Internet 2023
            if taux_internet_2023 is not None:
                taux_val = safe_float(taux_internet_2023, 0)
                taux_min = safe_float(taux_internet_2023_min, 0)
                taux_max = safe_float(taux_internet_2023_max, 100)
                # Calculer les positions Y (inversées car Y=0 est en haut)
                y_max = 20 + (100 - taux_max) / 100 * 360  # Haut du bâton
                y_min = 20 + (100 - taux_min) / 100 * 360  # Bas du bâton
                y_commune = 20 + (100 - taux_val) / 100 * 360  # Position de la commune
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF6600" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF6600" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2023</p>
                </div>'''
            
            # Internet 2024
            if taux_internet_2024 is not None:
                taux_val = safe_float(taux_internet_2024, 0)
                taux_min = safe_float(taux_internet_2024_min, 0)
                taux_max = safe_float(taux_internet_2024_max, 100)
                y_max = 20 + (100 - taux_max) / 100 * 360
                y_min = 20 + (100 - taux_min) / 100 * 360
                y_commune = 20 + (100 - taux_val) / 100 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF6600" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF6600" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2024</p>
                </div>'''
            
            # Internet 2025
            if taux_internet_2025 is not None:
                taux_val = safe_float(taux_internet_2025, 0)
                taux_min = safe_float(taux_internet_2025_min, 0)
                taux_max = safe_float(taux_internet_2025_max, 100)
                y_max = 20 + (100 - taux_max) / 100 * 360
                y_min = 20 + (100 - taux_min) / 100 * 360
                y_commune = 20 + (100 - taux_val) / 100 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF6600" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF6600" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2025</p>
                </div>'''
            
            html += '''
            </div>
        </div>'''
        
        # Bâtons de gendarmes pour FLNE (2023, 2024, 2025)
        if has_flne:
            html += '''
        <div style="text-align: center; flex: 1; padding: 30px; margin: 10px;">
            <h3 style="margin-bottom: 40px;">Taux FLNE (2023-2025)</h3>
            <div style="display: flex; justify-content: space-around; align-items: flex-end;">'''
            
            # FLNE 2023
            if taux_flne_2023 is not None:
                taux_val = safe_float(taux_flne_2023, 0)
                taux_min = safe_float(taux_flne_2023_min, 0)
                taux_max = safe_float(taux_flne_2023_max, 15)
                y_max = 20 + (15 - taux_max) / 15 * 360
                y_min = 20 + (15 - taux_min) / 15 * 360
                y_commune = 20 + (15 - taux_val) / 15 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#2196F3" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#2196F3" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2023</p>
                </div>'''
            
            # FLNE 2024
            if taux_flne_2024 is not None:
                taux_val = safe_float(taux_flne_2024, 0)
                taux_min = safe_float(taux_flne_2024_min, 0)
                taux_max = safe_float(taux_flne_2024_max, 15)
                y_max = 20 + (15 - taux_max) / 15 * 360
                y_min = 20 + (15 - taux_min) / 15 * 360
                y_commune = 20 + (15 - taux_val) / 15 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#2196F3" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#2196F3" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2024</p>
                </div>'''
            
            # FLNE 2025
            if taux_flne_2025 is not None:
                taux_val = safe_float(taux_flne_2025, 0)
                taux_min = safe_float(taux_flne_2025_min, 0)
                taux_max = safe_float(taux_flne_2025_max, 15)
                y_max = 20 + (15 - taux_max) / 15 * 360
                y_min = 20 + (15 - taux_min) / 15 * 360
                y_commune = 20 + (15 - taux_val) / 15 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#2196F3" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#2196F3" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2025</p>
                </div>'''
            
            html += '''
            </div>
        </div>'''
        
        # Bâtons de gendarmes pour FANE (2023, 2024, 2025)
        # On affiche les 3 bâtons côte à côte
        if taux_fane_2023 is not None or taux_fane_2024 is not None or taux_fane_2025 is not None:
            html += '''
        <div style="text-align: center; flex: 1; padding: 30px; margin: 10px;">
            <h3 style="margin-bottom: 40px;">Taux FANE (2023-2025)</h3>
            <div style="display: flex; justify-content: space-around; align-items: flex-end;">'''
            
            # FANE 2023
            if taux_fane_2023 is not None:
                taux_val = safe_float(taux_fane_2023, 0)
                taux_min = safe_float(taux_fane_2023_min, 0)
                taux_max = safe_float(taux_fane_2023_max, 6)
                y_max = 20 + (6 - taux_max) / 6 * 360
                y_min = 20 + (6 - taux_min) / 6 * 360
                y_commune = 20 + (6 - taux_val) / 6 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF9800" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF9800" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2023</p>
                </div>'''
            
            # FANE 2024
            if taux_fane_2024 is not None:
                taux_val = safe_float(taux_fane_2024, 0)
                taux_min = safe_float(taux_fane_2024_min, 0)
                taux_max = safe_float(taux_fane_2024_max, 6)
                y_max = 20 + (6 - taux_max) / 6 * 360
                y_min = 20 + (6 - taux_min) / 6 * 360
                y_commune = 20 + (6 - taux_val) / 6 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF9800" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF9800" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2024</p>
                </div>'''
            
            # FANE 2025
            if taux_fane_2025 is not None:
                taux_val = safe_float(taux_fane_2025, 0)
                taux_min = safe_float(taux_fane_2025_min, 0)
                taux_max = safe_float(taux_fane_2025_max, 6)
                y_max = 20 + (6 - taux_max) / 6 * 360
                y_min = 20 + (6 - taux_min) / 6 * 360
                y_commune = 20 + (6 - taux_val) / 6 * 360
                html += f'''
                <div style="text-align: center;">
                    <svg width="100" height="400">
                        <line x1="30" y1="{y_max}" x2="30" y2="{y_min}" stroke="#FF9800" stroke-width="8"/>
                        <line x1="30" y1="{y_commune}" x2="80" y2="{y_commune}" stroke="#FF9800" stroke-width="8"/>
                        <text x="57" y="{y_commune - 15}" font-size="16" font-weight="bold" fill="#FF6600" text-anchor="middle">{taux_val:.1f}%</text>
                        <text x="85" y="{y_max + 5}" font-size="10" fill="#666">{taux_max:.1f}%</text>
                        <text x="85" y="{y_min + 5}" font-size="10" fill="#666">{taux_min:.1f}%</text>
                    </svg>
                    <p style="margin-top: 10px; font-size: 15px; font-weight: bold;">2025</p>
                </div>'''
            
            html += '''
            </div>
        </div>'''
        
        html += '''    </div>
    <p class="source">Source : Insee, Recensements de la population</p>
    <p class="note">Lecture : Les barres horizontales indiquent la position de la commune par rapport \u00e0 l\'ensemble des grandes communes de la r\u00e9gion pour chaque indicateur. Le marqueur repr\u00e9sente le taux de la commune sur une \u00e9chelle allant de 0 \u00e0 100%.</p>
</div>

'''
    
    
    # Ajouter la page de la carte de la commune si elle existe
    if carte_commune:
        html += f'''<div class="page">
    <h1 style="text-align: center; color: #003366; margin-bottom: 30px;">Population par IRIS en 2023 - {commune_name}</h1>
    <div class="carte-iris-container">
        <img src="{carte_commune}" alt="Carte {commune_name}">
    </div>
</div>
'''
    
    html += '''<script>
// Attendre que Plotly soit chargé
if (typeof Plotly === 'undefined') {
    console.error('Plotly n\\'est pas chargé !');
}
</script>

</body>
</html>
'''
    
    # Écrire le fichier HTML
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Fichier HTML généré : {output_html}")
    print()
    print("👉 Pour générer le PDF :")
    print("   1. Ouvrez le fichier dans votre navigateur (Chrome/Edge)")
    print("   2. Ctrl+P (Imprimer)")
    print("   3. Sélectionnez 'Enregistrer en PDF'")
    print("   4. Ajustez les marges si nécessaire")
    print("   5. Cliquez sur 'Enregistrer'")
    print()
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_pdf_html_only.py <data.json> <output.html>")
        sys.exit(1)
    
    data_json_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        success = generate_html(data_json_file, output_file)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
