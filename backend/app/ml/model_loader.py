"""Shared model-loading utilities.

Centralises logic for locating, downloading, and caching ML models
so individual detectors don't duplicate boilerplate.

Functions:
    load_pytorch_model:  Load a `.pt` / `.pth` checkpoint
    load_sklearn_model:  Load a joblib-serialised scikit-learn model
    ensure_model_dir:    Create the model directory if missing
    get_model_path:      Resolve a model name to an absolute path
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings
from app.core.exceptions import ModelLoadError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

# Root directory where saved models live
MODEL_ROOT = Path("ml_models/saved_models")


def ensure_model_dir(subdir: str = "") -> Path:
    """Make sure the model directory exists; return the path."""
    path = MODEL_ROOT / subdir if subdir else MODEL_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_path(name: str) -> Path:
    """Resolve a model *name* (e.g. 'codebert') to a directory path."""
    path = MODEL_ROOT / name
    if not path.exists():
        logger.warning("Model directory does not exist: %s", path)
    return path


def load_pytorch_model(path: str | Path, map_location: str = "cpu") -> Any:
    """
    Load a PyTorch checkpoint.

    Returns the loaded state dict or model object.
    Raises ModelLoadError if the file is missing or corrupt.
    """
    path = Path(path)
    if not path.exists():
        raise ModelLoadError(
            f"PyTorch model not found at {path}",
            details={"path": str(path)},
        )
    try:
        import torch
        model = torch.load(path, map_location=map_location)
        logger.info("Loaded PyTorch model from %s", path)
        return model
    except ImportError:
        logger.warning("PyTorch not installed — returning None for %s", path)
        return None
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load PyTorch model: {exc}",
            details={"path": str(path)},
        ) from exc


def load_sklearn_model(path: str | Path) -> Any:
    """
    Load a scikit-learn model serialised with joblib.

    Returns the deserialised estimator.
    Raises ModelLoadError if the file is missing or corrupt.
    """
    path = Path(path)
    if not path.exists():
        raise ModelLoadError(
            f"Sklearn model not found at {path}",
            details={"path": str(path)},
        )
    try:
        import joblib
        model = joblib.load(path)
        logger.info("Loaded sklearn model from %s", path)
        return model
    except ImportError:
        logger.warning("joblib not installed — returning None")
        return None
    except Exception as exc:
        raise ModelLoadError(
            f"Failed to load sklearn model: {exc}",
            details={"path": str(path)},
        ) from exc


def list_available_models() -> list[str]:
    """Return names of model directories under MODEL_ROOT."""
    if not MODEL_ROOT.exists():
        return []
    return [
        entry.name
        for entry in MODEL_ROOT.iterdir()
        if entry.is_dir()
    ]
