"""
App Manager Pro — package Python (dossier `app_manager`).

Projet sur disque : App_Manager_Pro/
Code source actif : app_manager/ (voir ARCHITECTURE.md)

Ne pas dupliquer la logique dans services/ ou ui/ : ce sont des alias.
"""

from app_manager.application import ApplicationWindow

Application = ApplicationWindow

__version__ = "2.1.0"
__all__ = ["ApplicationWindow", "Application", "__version__"]
