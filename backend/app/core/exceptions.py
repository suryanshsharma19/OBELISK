"""Custom exceptions for OBELISK - Supply Chain Attack Detector."""

from __future__ import annotations

from typing import Any


class ObeliskException(Exception):
    """Base exception for all OBELISK errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | details={self.details}"
        return self.message


class ConfigurationError(ObeliskException):
    """Raised when there is a configuration issue."""


class DatabaseError(ObeliskException):
    """Raised on database connection or query errors."""


class ModelLoadError(ObeliskException):
    """Raised when an ML model fails to load."""


class RegistryError(ObeliskException):
    """Raised on npm/PyPI registry API errors."""


class AnalysisError(ObeliskException):
    """Raised when package analysis fails."""


class ValidationError(ObeliskException):
    """Raised on input validation errors."""
