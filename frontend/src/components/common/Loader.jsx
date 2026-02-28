/**
 * Reusable loading spinner with optional label.
 *
 * Usage:
 *   <Loader />            — default spinner
 *   <Loader text="Analyzing…" />  — with custom text
 *   <Loader fullPage />           — centred on the viewport
 */

import React from 'react';

export default function Loader({ text = 'Loading…', fullPage = false }) {
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-400 border-t-transparent" />
      <span className="text-sm text-gray-400">{text}</span>
    </div>
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
}
