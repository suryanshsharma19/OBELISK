import React from 'react';
import { DiffEditor } from '@monaco-editor/react';

interface CodeDriftViewerProps {
  originalCode: string;
  modifiedCode: string;
  filename: string;
}

export const CodeDriftViewer: React.FC<CodeDriftViewerProps> = ({ originalCode, modifiedCode, filename }) => {
  const getLanguage = (file: string) => {
    if (file.endsWith('.js') || file.endsWith('.jsx')) return 'javascript';
    if (file.endsWith('.ts') || file.endsWith('.tsx')) return 'typescript';
    if (file.endsWith('.py')) return 'python';
    if (file.endsWith('.json')) return 'json';
    return 'plaintext';
  };

  return (
    <div className="flex flex-col h-[500px] w-full border border-slate-700 rounded-xl overflow-hidden bg-slate-900 shadow-xl">
      <div className="bg-slate-800 px-4 py-2 border-b border-slate-700 flex justify-between">
        <span className="font-mono text-sm text-slate-300">Payload Insertion Diff: {filename}</span>
        <div className="flex space-x-4 font-mono text-xs">
          <span className="text-green-400">Safe Version (Original)</span>
          <span className="text-red-400">Compromised Version (Modified)</span>
        </div>
      </div>
      <div className="flex-1 w-full bg-slate-950">
        <DiffEditor
          key={filename + modifiedCode}
          height="100%"
          language={getLanguage(filename)}
          original={originalCode}
          modified={modifiedCode}
          theme="vs-dark"
          options={{
            readOnly: true,
            renderSideBySide: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
          }}
        />
      </div>
    </div>
  );
};
