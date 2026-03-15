/**
 * Minimal code viewer with line numbers.
 * Highlights suspicious lines passed via the `highlights` prop.
 */

import React from 'react';

export default function CodeViewer({ code = '', highlights = [], language = 'javascript' }) {
  if (!code) {
    return (
      <div className="rounded-xl border border-gray-700 bg-gray-800 p-5 text-sm text-gray-500">
        No source code provided
      </div>
    );
  }

  const lines = code.split('\n');
  const highlightSet = new Set(highlights);

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-300">Source Code</h4>
      <div className="max-h-96 overflow-auto rounded-lg bg-gray-900 p-3">
        <pre className="text-xs leading-5">
          {lines.map((line, i) => {
            const lineNum = i + 1;
            const isHighlighted = highlightSet.has(lineNum);
            return (
              <div
                key={lineNum}
                className={`flex ${
                  isHighlighted ? 'bg-red-900/30' : ''
                }`}
              >
                <span className="mr-4 inline-block w-8 select-none text-right text-gray-600">
                  {lineNum}
                </span>
                <code className="text-gray-300">{line || ' '}</code>
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
}
