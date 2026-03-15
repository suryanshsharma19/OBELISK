"""Custom exception classes."""

from __future__ import annotations

from typing import Any


class ObeliskException(Exception):

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class ConfigurationError(ObeliskException):
    """Raised when required runtime configuration is invalid or missing."""


class DatabaseError(ObeliskException):
    """Raised when database access or persistence fails."""


class ModelLoadError(ObeliskException):
    """Raised when an ML model cannot be loaded."""


class RegistryError(ObeliskException):
    """Raised when upstream package registry communication fails."""


class AnalysisError(ObeliskException):
    """Raised when the analysis pipeline fails to complete."""


class ValidationError(ObeliskException):
    """Raised when domain validation fails."""
