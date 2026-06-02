# Mon Potager — Documentation Projet

## Architecture générale

Application web Python monolythique avec :
- **FastAPI** pour le backend (routes REST + templates Jinja2)
- **SQLAlchemy + SQLite** pour la persistance
- **Jinja2 + Bootstrap 5** pour le rendu côté serveur
- **ChromaDB** pour la recherche sémantique (RAG)
- **opencode serve** pour l'assistant IA (API HTTP)

## Modèles de données (SQLAlchemy)

### `Famille`
- `id`, `nom`, `description`
- Relation 1→N avec `Legume`

### `Legume`
- `id`, `nom`, `nom_scientifique`, `famille_id` (FK → Famille)
- `description`, `conseils_culture`, `exposition`, `sol`, `arrosage`
- Relations 1→N : `varietes`, `calendrier`, `maladies`

### `Variete`
- `id`, `legume_id` (FK → Legume), `nom`, `description`, `particularites`

### `Calendrier`
- `id`, `legume_id` (FK → Legume), `type`, `mois_debut`, `semaine_debut`, `mois_fin`, `semaine_fin`, `details`
- `type` : `semis_serre_chaude`, `semis_serre_froide`, `semis_direct`, `semis_interieur`, `plantation`, `action`, `bouturage`, `recolte`
- Semaines : 1-4 par mois (précision à la semaine près)
- 48 semaines/an (12 mois × 4 semaines)

### `Maladie`
- `id`, `legume_id` (FK → Legume), `type` (maladie/ravageur), `nom`, `symptomes`, `traitement`, `prevention`

### `Potager`
- `id`, `annee`, `nom`, `active`, `notes`, `created_at`
- Relation 1→N avec `PotagerItem`

### `PotagerItem`
- `id`, `potager_id` (FK → Potager), `legume_id` (FK nullable → Legume), `variete_id` (FK nullable → Variete)
- `type`, `nom_custom`, `quantite`, `emplacement`, `compagnons`, `notes`, `ordre`

### `PotagerCalendrier`
- `id`, `item_id` (FK → PotagerItem), `type`, `mois_debut`, `semaine_debut`, `mois_fin`, `semaine_fin`, `details`
- Copie du `Calendrier` du légume à l'ajout, modifiable ensuite individuellement par l'utilisateur

## Routes FastAPI

### Pages publiques
| Route | Template | Description |
|---|---|---|
| `GET /` | `index.html` | Accueil : stats, familles, potagers |
| `GET /legumes` | `legume_list.html` | Liste des légumes (filtrable par famille) |
| `GET /legume/{id}` | `legume_detail.html` | Fiche : infos + onglets variétés/calendrier barres/maladies |
| `GET /legume/{id}/pdf` | `legume_pdf.html` | Version imprimable |
| `GET /familles` | `famille_list.html` | Liste des familles botaniques |
| `GET /recherche` | `search.html` | Recherche plein texte |

### Mon Potager
| Route | Template | Description |
|---|---|---|
| `GET /potager` | `potager_list.html` | Liste des potagers |
| `GET /potager/creer` | `potager_form.html` | Formulaire création |
| `POST /potager/creer` | — | Création |
| `GET /potager/{id}` | `potager_detail.html` | Calendrier barres + vue mensuelle |
| `POST /potager/{id}/ajouter` | — | Ajouter une culture à un potager |

### API / Chat
| Route | Description |
|---|---|
| `GET /api/chat/health` | Vérifie/démarre opencode serve |
| `POST /api/chat/session` | Crée une session de chat |
| `POST /api/chat/send` | Envoie un message (avec contexte RAG) |

### Admin CRUD
| Route | Description |
|---|---|
| `GET /admin` | Dashboard |
| `GET/POST /admin/legumes` | Liste + création légumes |
| `GET/POST /admin/legumes/{id}/editer` | Édition légume |
| `POST /admin/legumes/{id}/supprimer` | Suppression |
| `POST /admin/varietes/{id}/editer` | Édition variété |
| `POST /admin/legumes/{id}/varietes/ajouter` | Ajout variété |
| `POST /admin/calendrier/{id}/editer` | Édition calendrier |
| `POST /admin/legumes/{id}/calendrier/ajouter` | Ajout calendrier |
| `POST /admin/maladies/{id}/editer` | Édition maladie |
| `POST /admin/legumes/{id}/maladies/ajouter` | Ajout maladie |
| `GET/POST /admin/familles` | CRUD familles |
| `GET /admin/rag` | Upload/indexation PDFs |
| `POST /admin/rag/upload` | Import PDF → ChromaDB |

## Système de calendrier (48 semaines)

Le calendrier divise chaque mois en 4 semaines :

```python
TOTAL_WEEKS = 48

def week_pos(mois, semaine):
    return (mois - 1) * 4 + semaine

def bar_style(mois_debut, semaine_debut, mois_fin, semaine_fin):
    start = week_pos(mois_debut, semaine_debut)
    end = week_pos(mois_fin, semaine_fin)
    left = (start - 1) / TOTAL_WEEKS * 100
    width = (end - start + 1) / TOTAL_WEEKS * 100
    return f"left:{left:.2f}%;width:{width:.2f}%;"
```

Dans le template, les barres sont positionnées en `absolute` dans un conteneur `relative` avec la grille des 12 mois affichée en en-tête. Chaque type d'entrée a une couleur dédiée (`TYPE_COLORS`).

## Assistant IA (opencode)

### Client HTTP (`ai_client.py`)
- L'agent est auto-démarré en subprocess si nécessaire (`opencode serve --port 4096`)
- Endpoints utilisés : `/global/health`, `/session` (POST), `/session/{id}/message` (POST)
- Un system prompt spécialisé jardinage est envoyé à chaque message
- Le contexte de la page en cours (`page_context` dans le template) est transmis au système

### Chat flottant (`chat_bubble.html`, `chat.js`, `chat.css`)
- Bulle fixée en bas à droite
- Input text + « Envoyer » dans la bulle ouverte
- Envoie `session_id`, `text` et `context` (extrait de `#chat-context`) à `/api/chat/send`
- L'historique s'affiche dans la bulle, chargé au clic

## RAG (ChromaDB)

### `rag.py`
- Utilise ChromaDB PersistentClient avec collection `potager_docs`
- Embedding : modèle par défaut de ChromaDB (pas de sentence-transformers requis)
- Chunking : par mots, 800 mots par chunk, 150 de recouvrement
- `ingest_pdf()` : extrait le texte via `pypdf`, découpe en chunks, indexe dans ChromaDB
- `get_context(query, k=3)` : recherche les k chunks les plus proches et les formate pour le prompt

### Intégration dans le chat
Dans `POST /api/chat/send` :
1. `rag_engine.get_context(text, k=3)` récupère les documents pertinents
2. S'ils existent, ils sont insérés dans `full_context` avec la mention « Documents de référence »
3. `full_context` est passé comme `system` supplémentaire à opencode

## Seed data

Quatre légumes réalistes (français) avec :
- **Ail** (Alliacées) : 6 variétés, 6 entrées calendrier, 5 maladies
- **Poivron** (Solanacées) : 6 variétés, 9 entrées calendrier, 6 maladies
- **Potimarron** (Cucurbitacées) : 6 variétés, 9 entrées calendrier, 6 maladies
- **Épinard** (Chénopodiacées) : 6 variétés, 8 entrées calendrier, 6 maladies

Chaque entrée calendrier est définie par `(type, mois_debut, semaine_debut, mois_fin, semaine_fin, details)`.

## Structure du projet

```
potager-app/
├── run.py                    # uvicorn --reload
├── requirements.txt          # fastapi, uvicorn, sqlalchemy, jinja2, python-multipart
├── README.md
├── PROJECT.md
├── data/
│   ├── potager.db            # SQLite (auto-créé)
│   └── rag/                  # ChromaDB + PDFs (auto-créé)
│       ├── chroma/
│       └── pdfs/
└── app/
    ├── __init__.py
    ├── main.py               # FastAPI app, toutes les routes
    ├── models.py             # SQLAlchemy models
    ├── database.py           # Engine SQLite + get_db()
    ├── seed.py               # Données seed (4 légumes)
    ├── ai_client.py          # Client HTTP opencode serve
    ├── rag.py                # RAG ChromaDB
    ├── static/
    │   ├── style.css         # Thème vert, cards, responsive
    │   ├── chat.js           # Chat flottant JS
    │   └── chat.css          # Styles de la bulle chat
    └── templates/
        ├── base.html         # Layout : navbar, footer, chat_bubble
        ├── index.html
        ├── legume_list.html
        ├── legume_detail.html
        ├── legume_pdf.html
        ├── famille_list.html
        ├── search.html
        ├── chat_bubble.html  # Bulle flottante
        ├── potager_list.html
        ├── potager_form.html
        ├── potager_detail.html
        ├── admin.html
        ├── admin_legumes.html
        ├── admin_legume_edit.html
        ├── admin_familles.html
        └── admin_rag.html
```

## Pour recréer cette application

1. Créer le projet FastAPI avec SQLAlchemy + SQLite
2. Définir les 7 modèles (Famille, Legume, Variete, Calendrier, Maladie, Potager, PotagerItem, PotagerCalendrier)
3. Implémenter le système de calendrier à 48 semaines avec `week_pos()` et `bar_style()`
4. Créer les templates Bootstrap 5 avec héritage Jinja2
5. Ajouter les routes CRUD admin
6. Implémenter `ai_client.py` : HTTP vers opencode serve avec auto-démarrage
7. Implémenter `rag.py` : ChromaDB PersistentClient, chunking par mots, `pypdf` pour l'extraction
8. Intégrer RAG dans le chat : `get_context()` → `system` prompt enrichi
9. Ajouter la bulle chat flottante avec contexte de page
