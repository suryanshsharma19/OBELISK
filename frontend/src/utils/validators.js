// Client-side validation helpers

const NPM_PACKAGE_NAME_RE = /^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$/;
const PYPI_PACKAGE_NAME_RE = /^[a-zA-Z0-9\-.*_+!']+$/;
const SEMVER_RE = /^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$/;

export function isValidPackageName(name, registry = 'npm') {
  if (!name || typeof name !== 'string') return false;
  if (name.length > 214) return false;
  
  if (registry === 'pypi') {
    return PYPI_PACKAGE_NAME_RE.test(name);
  }
  
  return NPM_PACKAGE_NAME_RE.test(name);
}

export function isValidVersion(version) {
  if (!version || typeof version !== 'string') return false;
  return SEMVER_RE.test(version);
}

export function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

export function validateAnalyzeForm({ name, version, registry }) {
  const errors = {};

  if (!name?.trim()) {
    errors.name = 'Package name is required';
  } else if (!isValidPackageName(name.trim(), registry)) {
    errors.name = 'Invalid package name format';
  }

  if (!version?.trim()) {
    errors.version = 'Version is required';
  } else if (!isValidVersion(version.trim())) {
    errors.version = 'Invalid version (use semver, e.g. 1.2.3)';
  }

  if (registry && !['npm', 'pypi'].includes(registry)) {
    errors.registry = 'Registry must be npm or pypi';
  }

  return Object.keys(errors).length ? errors : null;
}
