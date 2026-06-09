"""Exceptions métier."""


class AppManagerError(Exception):
    """Erreur de base."""


class ScanError(AppManagerError):
    """Échec du scan."""


class WingetError(AppManagerError):
    """Échec Winget."""


class UninstallError(AppManagerError):
    """Échec désinstallation."""


class UpdateError(AppManagerError):
    """Échec mise à jour."""
