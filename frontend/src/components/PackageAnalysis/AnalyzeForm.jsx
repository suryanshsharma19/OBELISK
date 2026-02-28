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
          className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none"
        />
        {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Version */}
        <div>
          <label className="mb-1 block text-sm text-gray-400">Version</label>
          <input
            name="version"
            value={form.version}
            onChange={handleChange}
            placeholder="e.g. 4.18.0 (optional)"
            className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none"
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
            className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
          >
            {REGISTRIES.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Optional source code */}
      <div>
        <label className="mb-1 block text-sm text-gray-400">Source Code (optional)</label>
        <textarea
          name="code"
          value={form.code}
          onChange={handleChange}
          rows={5}
          placeholder="Paste package source code for deeper analysis…"
          className="w-full rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 font-mono text-xs text-white placeholder-gray-500 focus:border-emerald-500 focus:outline-none"
        />
      </div>

      <button
        type="submit"
        disabled={analyzing}
        className="flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        <Search size={16} />
        {analyzing ? 'Analyzing…' : 'Analyze'}
      </button>
    </form>
  );
}
