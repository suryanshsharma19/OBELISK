"""Model loading utilities for PyTorch and sklearn."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings
from app.core.exceptions import ModelLoadError
from app.core.logging import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

MODEL_ROOT = Path("ml_models/saved_models")


def ensure_model_dir(subdir: str = "") -> Path:
    path = MODEL_ROOT / subdir if subdir else MODEL_ROOT
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_model_path(name: str) -> Path:
    path = MODEL_ROOT / name
    if not path.exists():
        logger.warning("Model directory does not exist: %s", path)
    return path


def load_pytorch_model(path: str | Path, map_location: str = "cpu") -> Any:
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
    if not MODEL_ROOT.exists():
        return []
    return [
        entry.name
        for entry in MODEL_ROOT.iterdir()
        if entry.is_dir()
    ]
