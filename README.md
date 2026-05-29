# App Manager Pro

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-GUI-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-darkgreen?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Development-orange?style=for-the-badge)

Gestionnaire d’applications **Windows** en Python : scan, recherche, lancement et désinstallation depuis une interface sombre moderne (CustomTkinter).

> Le code source se trouve dans le dossier [`App_Manager_Pro/`](App_Manager_Pro/readme.md).

---

## Fonctionnalités

| Domaine | Description |
|--------|-------------|
| **Scan registre** | Détection des programmes installés via les clés `Uninstall` (HKLM / WOW6432 / HKCU). |
| **Scan portable** | Recherche parallèle d’exécutables sur les disques (avec exclusions et cache SQLite). |
| **Winget** | Import de la liste `winget list` pour enrichir le catalogue. |
| **Liste virtualisée** | Affichage fluide de milliers d’entrées (pool de widgets + défilement canvas). |
| **Recherche** | Filtrage en temps réel par nom. |
| **Catégories** | Filtres **Programmes** / **Jeux** (heuristique sur le nom et le chemin). |
| **Icônes** | Extraction locale + fallback réseau (Pillow / `requests`). |
| **Désinstallation** | Commandes registre, MSI et suppression sécurisée des dossiers autorisés. |
| **Raccourcis** | `Ctrl+R` : relancer le scan · `Échap` : quitter proprement. |

---

## Prérequis

- **Windows 10/11**
- **Python 3.12** (recommandé)
- **winget** (optionnel, pour le scan Winget)
- Droits suffisants pour lire le registre et parcourir `Program Files`

---

## Installation

```powershell
cd App_Manager_Pro
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Lancement

```powershell
cd App_Manager_Pro
python main.py
```

Au démarrage, utilisez **Scanner** dans la barre latérale (ou `Ctrl+R`) pour charger les applications.

---

## Interface

- **Barre latérale** : Programmes, Jeux, Scanner, Stop.
- **Zone centrale** : recherche + liste avec icônes, taille et source (`registry`, `portable`, `winget`, etc.).
- **Actions par ligne** : ouvrir le dossier, lancer l’exécutable, désinstaller.

---

## Architecture

```text
App_Manager_Pro/
├── main.py              # Point d’entrée, fenêtre, raccourcis, fermeture propre
├── ui.py                # Interface CustomTkinter et logique d’affichage
├── scanner.py           # Scan registre + portable, workers, cache
├── scanner_cache.py     # Cache SQLite des résultats de scan
├── winget_manager.py    # Parsing de `winget list`
├── uninstaller.py       # Désinstallation (registre, MSI, dossiers)
├── icon_manager.py      # Icônes Windows / images distantes
├── utils.py             # Utilitaires (chemins, lancement, etc.)
├── launcher_config.py   # Configuration des lanceurs / jeux
├── launcher_manager.py  # Gestion et scan des lanceurs
├── launcher_scanner.py  # Détection des jeux (Steam, Epic, etc.)
├── uninstaller/         # Scripts de désinstallation spécialisés
│   └── unreal engine.py
├── requirements.txt     # Dépendances Python
├── scanner_cache.db     # Généré au runtime
└── .gitignore
```

Documentation détaillée : [App_Manager_Pro/readme.md](App_Manager_Pro/readme.md).

---

## Sécurité

- La désinstallation refuse les chemins système (`windows`, `system32`, etc.).
- Seuls les emplacements usuels (`Program Files`, `AppData`, …) peuvent être supprimés manuellement.

---

## Licence

Projet en développement actif — usage personnel / éducatif sauf mention contraire.

---

## Auteur

**wargriff** — [App_Manager_Pro](https://github.com/wargriff/App_Manager_Pro)
