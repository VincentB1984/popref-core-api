# popref-core-api

Microservice FastAPI exposant le moteur de génération `popref_core` via une API REST.
Déployé sur Render, appelé par le serveur Node.js de l'application web Popref.

## Endpoints

- `GET /health` — Vérification que le service tourne et que `popref_core` est importable
- `POST /generate` — Génère un dossier HTML depuis un fichier Excel (base64) et une commune
- `POST /extract-communes` — Extrait la liste des communes depuis un fichier Excel (base64)

## Authentification

Toutes les routes (sauf `/health`) requièrent un header `Authorization: Bearer <POPREF_API_SECRET>`.

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `POPREF_API_SECRET` | Secret partagé avec le serveur Node.js |
| `PORT` | Port d'écoute (injecté automatiquement par Render) |

## Déploiement sur Render

1. Créer un compte sur [render.com](https://render.com)
2. "New Web Service" → connecter ce dépôt GitHub
3. Runtime : **Python 3**
4. Build command : `pip install -r requirements.txt && pip install -e .`
5. Start command : `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Ajouter la variable d'environnement `POPREF_API_SECRET` (valeur aléatoire longue)
7. Copier l'URL du service (ex. `https://popref-core-api.onrender.com`) dans l'application web

## Structure

```
popref-api/
  main.py           ← API FastAPI
  requirements.txt  ← Dépendances Python
  Procfile          ← Commande de démarrage
  render.yaml       ← Config Render
  popref_core/      ← Code source du moteur (copié depuis popref_python/src/popref_core)
```
