"""Initialisation de l'application (logging, chemins)."""

from app_manager.core.logging_config import setup_logging


def bootstrap() -> None:
    setup_logging()
