"""Input validators - each returns (is_valid, error_msg)."""

import re
from urllib.parse import urlparse

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+([.\-+].+)?$")
_PKG_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_.]*$")
_SUPPORTED_REGISTRIES = {"npm", "pypi"}

Result = tuple[bool, str | None]


def validate_package_name(name: str) -> Result:
    if not name:
        return False, "Package name cannot be empty"
    if len(name) > 255:
        return False, "Package name must be 255 characters or fewer"
    if not _PKG_NAME_RE.match(name):
        return False, "Package name contains invalid characters or starts with a dot/hyphen"
    return True, None


def validate_version_format(version: str) -> Result:
    if not version:
        return False, "Version cannot be empty"
    if not _SEMVER_RE.match(version):
        return False, f"Invalid semver format: {version}"
    return True, None


def validate_registry(registry: str) -> Result:
    if registry.lower() not in _SUPPORTED_REGISTRIES:
        return False, f"Unsupported registry: {registry}. Must be one of {_SUPPORTED_REGISTRIES}"
    return True, None


def validate_risk_score(score: float) -> Result:
    if not 0.0 <= score <= 100.0:
        return False, f"Risk score must be between 0 and 100, got {score}"
    return True, None


def validate_url(url: str) -> Result:
    if not url:
        return False, "URL cannot be empty"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "URL must start with http:// or https://"
    if not parsed.netloc:
        return False, "URL is missing a hostname"
    return True, None


def validate_code_content(code: str) -> Result:
    if not code:
        return False, "Code content cannot be empty"
    if len(code) > 100_000:
        return False, f"Code exceeds max length of 100,000 characters ({len(code)})"
    return True, None

