/**
 * Minimal footer bar displayed at the bottom of the main content area.
 */

import React from 'react';

export default function Footer() {
  return (
    <footer className="border-t border-gray-700 bg-gray-900 px-4 py-3 text-center text-xs text-gray-500">
      <p>
        OBELISK &mdash; AI-Powered Supply Chain Attack Detection &middot;{' '}
        <a
          href="https://github.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-emerald-400 hover:underline"
        >
          GitHub
        </a>
      </p>
    </footer>
  );
}
