"""Misc helper functions."""

import hashlib
import re
from datetime import datetime, timezone


def get_current_timestamp() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def calculate_threat_level(risk_score: float) -> str:
    if risk_score < 20:
        return "safe"
    if risk_score < 40:
        return "low"
    if risk_score < 60:
        return "medium"
    if risk_score < 80:
        return "high"
    return "critical"


def sanitize_package_name(name: str) -> str:
    name = name.strip().lower()
    name = name.replace(" ", "-")
    return re.sub(r"[^a-z0-9\-._]", "", name)


def validate_version(version: str) -> bool:
    return bool(re.match(r"^\d+\.\d+\.\d+.*$", version))


def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def format_file_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def generate_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

