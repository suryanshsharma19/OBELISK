"""Custom exceptions for OBELISK."""

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


class ConfigurationError(ObeliskException): pass

class DatabaseError(ObeliskException): pass

class ModelLoadError(ObeliskException): pass

class RegistryError(ObeliskException): pass

class AnalysisError(ObeliskException): pass

class ValidationError(ObeliskException): pass
