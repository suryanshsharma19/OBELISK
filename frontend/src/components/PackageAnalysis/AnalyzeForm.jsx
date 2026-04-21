/**
 * Package analysis form — name, version, registry, optional code.
 * Validates locally, then dispatches the Redux analyze thunk.
 */

import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Search } from 'lucide-react';
import { analyzePackage } from '../../store/slices/packagesSlice';
import { addToast } from '../../store/slices/uiSlice';
import { validateAnalyzeForm } from '../../utils/validators';
import { REGISTRIES } from '../../utils/constants';

export default function AnalyzeForm() {
  const dispatch = useDispatch();
  const analyzing = useSelector((s) => s.packages.analyzing);

  const [form, setForm] = useState({
    name: '',
    version: '',
    registry: 'npm',
    code: '',
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    // Clear field error on edit
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateAnalyzeForm(form);
    if (validationErrors) {
      setErrors(validationErrors);
      return;
    }

    try {
      await dispatch(analyzePackage(form)).unwrap();
      dispatch(addToast({ message: 'Analysis complete', type: 'success' }));
    } catch (err) {
      dispatch(addToast({ message: err || 'Analysis failed', type: 'error' }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-gray-700 bg-gray-800 p-6">
      <h2 className="text-lg font-semibold text-white">Analyze Package</h2>

      {/* Package name */}
      <div>
        <label className="mb-1 block text-sm text-gray-400">Package Name *</label>
        <input
          name="name"
          value={form.name}
          onChange={handleChange}
          placeholder="e.g. express, lodash"
          className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-neon-500 focus:outline-none"
        />
        {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Version */}
        <div>
          <label className="mb-1 block text-sm text-gray-400">Version *</label>
          <input
            name="version"
            value={form.version}
            onChange={handleChange}
            placeholder="e.g. 4.18.0"
            className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-neon-500 focus:outline-none"
          />
          {errors.version && <p className="mt-1 text-xs text-red-400">{errors.version}</p>}
        </div>

        {/* Registry */}
        <div>
          <label className="mb-1 block text-sm text-gray-400">Registry</label>
          <select
            name="registry"
            value={form.registry}
            onChange={handleChange}
            className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white focus:border-neon-500 focus:outline-none"
          >
            {REGISTRIES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Optional source code */}
      <div>
        <div className="flex justify-between items-end mb-1">
          <label className="block text-sm text-gray-400">Source Code (optional)</label>
          <label className="cursor-pointer flex items-center gap-1 text-xs text-primary-container hover:text-white transition-colors bg-surface-variant px-2 py-1 border border-outline-variant rounded">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            UPLOAD FILE
            <input 
              type="file" 
              className="hidden" 
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (e) => {
                  const content = e.target?.result;
                  if (typeof content === 'string') {
                    setForm(prev => ({ ...prev, code: content }));
                  }
                };
                reader.readAsText(file);
              }}
              accept=".js,.ts,.jsx,.tsx,.json,.py,.java,.go,.rb,.php,.txt" 
            />
          </label>
        </div>
        <textarea
          name="code"
          value={form.code}
          onChange={handleChange}
          rows={5}
          placeholder="Paste package source code for deeper analysis…"
          className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 font-mono text-xs text-white placeholder-gray-500 focus:border-neon-500 focus:outline-none"
        />
      </div>

      <button
        type="submit"
        disabled={analyzing}
        className="flex items-center gap-2 rounded-lg bg-neon-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-neon-700 disabled:opacity-50"
      >
        <Search size={16} />
        {analyzing ? 'Analyzing…' : 'Analyze'}
      </button>
    </form>
  );
}
