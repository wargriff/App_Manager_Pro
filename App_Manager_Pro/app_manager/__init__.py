"""App Manager Pro — édition professionnelle."""

from app_manager.application import ApplicationWindow

# Compatibilité v1
Application = ApplicationWindow

__version__ = "2.0.0"
__all__ = ["ApplicationWindow", "Application", "__version__"]
