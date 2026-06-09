# App Manager Pro

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-GUI-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-darkgreen?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Development-orange?style=for-the-badge)

Gestionnaire d’applications **Windows** en Python : scan, recherche, lancement et désinstallation depuis une interface sombre moderne (CustomTkinter).

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
python main.py
```

Au démarrage, utilisez **Scanner** dans la barre latérale (ou `Ctrl+R`) pour charger les applications.

---

## Interface

- **Barre latérale** : Programmes, Jeux, Scanner, Stop.
- **Zone centrale** : recherche + liste avec icônes, taille et source (`registry`, `portable`, `winget`, etc.).
- **Actions par ligne** : ouvrir le dossier, lancer l’exécutable, désinstaller.

---

## Architecture Pro (v2.1)

> **Important :** le dossier projet s’appelle `App_Manager_Pro`, le package Python `app_manager`.  
> Ce ne sont **pas** deux applications. Détails : [ARCHITECTURE.md](ARCHITECTURE.md).

Architecture **Clean / layered** — une seule source de vérité par fonction :

```text
App_Manager_Pro/                    ← Projet (PyCharm, Git)
├── main.py                           ← Point d’entrée
├── ARCHITECTURE.md
├── requirements.txt
│
└── app_manager/                      ← Package Python importé
    ├── config/                       settings, theme
    ├── core/                         logging, enums, exceptions
    ├── domain/                       métier + dédoublonnage
    │   ├── models/app_item.py
    │   ├── catalog/app_catalog.py
    │   ├── dedup/app_deduplicator.py ← Supprime les programmes en double
    │   └── filters/app_filter.py
    ├── infrastructure/               scanner, winget, uninstall, icônes
    ├── application/                  cas d’usage + fenêtre
    ├── presentation/                 interface (code UI actif)
    └── scripts/

    services/  ui/  models/            ← ALIAS uniquement (pas de logique)
```

Fichiers à la racine (`scanner.py`, `ui.py`, …) : raccourcis pour anciens imports PyCharm.

### Couches

| Couche | Rôle |
|--------|------|
| **presentation** | Affichage CustomTkinter, événements utilisateur |
| **application** | Cas d’usage : scan, MAJ, désinstallation |
| **domain** | Modèles, catalogue, règles de filtrage |
| **infrastructure** | Windows, Winget, fichiers, registre |
| **core** | Enums, exceptions, logging |

### PyCharm

1. **Run → Edit Configurations → App Manager Pro**
2. Script : `App_Manager_Pro/main.py`
3. Working directory : `App_Manager_Pro`
4. `App_Manager_Pro` → **Mark Directory as → Sources Root**
5. Relancer PyCharm si les imports ne se résolvent pas

### Lancer

```powershell
cd App_Manager_Pro
python main.py
# ou
python -m app_manager
```

---

## Configuration

| Fichier / variable | Rôle |
|------------------|------|
| `scanner_cache.db` | Cache des programmes déjà vus (accélère les scans suivants). |
| `launcher_config.py` | Chemins et options pour les lanceurs de jeux. |
| Constantes dans `scanner.py` | `MAX_WORKERS`, `MAX_DEPTH`, `MIN_EXE_SIZE`, listes d’exclusion. |

---

## Sécurité

- La désinstallation refuse les chemins système (`windows`, `system32`, etc.).
- Seuls les emplacements « classiques » (`Program Files`, `AppData`, …) peuvent être supprimés manuellement.
- Vérifiez toujours l’entrée avant de désinstaller un logiciel inconnu.

---

## Dépannage

| Problème | Piste |
|----------|--------|
| Liste vide après scan | Lancer en administrateur ; vérifier l’antivirus ; attendre la fin des deux scans (Winget + disque). |
| Scan très long | Normal au premier lancement ; le cache SQLite accélère les suivants. |
| Erreur winget | Installer [App Installer](https://aka.ms/getwinget) ou ignorer (le scan disque/registre reste actif). |
| Icônes manquantes | Connexion Internet pour le fallback ; sinon icône par défaut. |

---

## Développement

```powershell
# Depuis App_Manager_Pro
python main.py
```

Pistes d’évolution : tests sur `Uninstaller._parse_line`, profils utilisateur, export JSON du catalogue.

---

## Licence

Projet en développement actif — usage personnel / éducatif sauf mention contraire.

---

## Auteur

**wargriff** — [App_Manager_Pro](https://github.com/wargriff/App_Manager_Pro)
