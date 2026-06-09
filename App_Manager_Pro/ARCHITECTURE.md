# Architecture App_Manager_Pro

| Dossier | Rôle |
|---------|------|
| `App_Manager_Pro/` | Projet (PyCharm, GitHub) |
| `app_manager/` | Package Python (`import app_manager`) |

## Code actif

- `presentation/` — interface
- `infrastructure/` — scanner, winget, fichiers
- `domain/` — catalogue, filtres, **dedup** (anti-doublons)
- `application/` — cas d’usage
- `config/`, `core/`

## Alias (ne pas dupliquer la logique)

- `services/` → `infrastructure/`
- `ui/` → `presentation/`
- `models/` → `domain/models/`

Lancement : `python main.py`
