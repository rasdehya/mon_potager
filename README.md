# Mon Potager - Guide de Culture

Application web de gestion potagère avec assistant IA et base documentaire.

## Fonctionnalités

- **Fiches légumes** : 4 légumes seed (ail, poivron, potimarron, épinard) avec variétés, calendrier de culture à la semaine près, maladies et traitements
- **Calendrier** : barres horizontales positionnées sur 48 semaines, type par couleur (semis, plantation, récolte, action)
- **Mon Potager** : planification annuelle des cultures, calendrier global et mensuel
- **Assistant IA** : chat flottant contextuel connecté à opencode serve (auto-démarrage)
- **RAG** : import de PDFs avec ChromaDB pour enrichir les réponses de l'assistant
- **Admin CRUD** : gestion complète des légumes, variétés, calendrier, maladies, familles
- **Recherche** : plein texte sur les légumes et variétés
- **Fiches PDF** : version imprimable des fiches légumes

## Installation

```bash
git clone <repo>
cd potager-app

# Avec uv (recommandé)
uv venv
uv sync

# Ou avec pip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install chromadb pypdf httpx  # RAG + AI client
```

## Utilisation

```bash
uv run python run.py
# ou
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Ouvrir http://localhost:8000

## Configuration

| Variable | Défaut | Description |
|---|---|---|
| `OPENCODE_SERVER_URL` | `http://localhost:4096` | URL du serveur opencode |
| `OPENCODE_SERVER_PORT` | `4096` | Port du serveur opencode |
| `OPENCODE_SERVER_PASSWORD` | `""` | Mot de passe (auth Basic) |
| `OPENCODE_BIN` | `opencode` | Binaire opencode |

## Déploiement

```bash
# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# Ou avec systemd / Docker
```

**Prérequis** : Python 3.12+, [opencode](https://opencode.ai) installé pour le chat IA.

## Structure

```
potager-app/
├── run.py              # Point d'entrée dev
├── app/
│   ├── main.py         # Routes FastAPI
│   ├── models.py       # Modèles SQLAlchemy
│   ├── database.py     # Connexion SQLite
│   ├── seed.py         # Données initiales
│   ├── ai_client.py    # Client API opencode
│   ├── rag.py          # Moteur RAG ChromaDB
│   ├── static/         # CSS, JS chat
│   └── templates/      # Jinja2 templates
└── data/               # SQLite + RAG (chroma, pdfs)
```
