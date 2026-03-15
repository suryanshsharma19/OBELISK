// Client-side validation helpers

const PACKAGE_NAME_RE = /^(@[a-z0-9-~][a-z0-9-._~]*\/)?[a-z0-9-~][a-z0-9-._~]*$/;
const SEMVER_RE = /^\d+\.\d+\.\d+(-[\w.]+)?(\+[\w.]+)?$/;

export function isValidPackageName(name) {
  if (!name || typeof name !== 'string') return false;
  if (name.length > 214) return false;
  return PACKAGE_NAME_RE.test(name);
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
  } else if (!isValidPackageName(name.trim())) {
    errors.name = 'Invalid package name format';
  }

  if (version && !isValidVersion(version.trim())) {
    errors.version = 'Invalid version (use semver, e.g. 1.2.3)';
  }

  if (registry && !['npm', 'pypi'].includes(registry)) {
    errors.registry = 'Registry must be npm or pypi';
  }

  return Object.keys(errors).length ? errors : null;
}
