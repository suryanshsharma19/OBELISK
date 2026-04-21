/**
 * Start / stop controls for the background registry crawler.
 */

import React, { useState } from 'react';
import { Play, Square } from 'lucide-react';
import { startCrawler, stopCrawler } from '../../services/api';
import { REGISTRIES } from '../../utils/constants';

export default function CrawlerControls({ isRunning, onRefresh }) {
  const [registry, setRegistry] = useState('npm');
  const [loading, setLoading] = useState(false);

  const handleStart = async () => {
    setLoading(true);
    try {
      await startCrawler({ registry });
      onRefresh?.();
    } catch (err) {
      console.error('Failed to start crawler:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await stopCrawler();
      onRefresh?.();
    } catch (err) {
      console.error('Failed to stop crawler:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      <select
        value={registry}
        onChange={(e) => setRegistry(e.target.value)}
        disabled={isRunning}
        className="rounded-lg border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-300 focus:border-neon-500 focus:outline-none disabled:opacity-50"
      >
        {REGISTRIES.map((r) => (
          <option key={r} value={r}>{r}</option>
        ))}
      </select>

      {isRunning ? (
        <button
          onClick={handleStop}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
        >
          <Square size={16} />
          {loading ? 'Stopping…' : 'Stop Crawler'}
        </button>
      ) : (
        <button
          onClick={handleStart}
          disabled={loading}
          className="flex items-center gap-2 rounded-lg bg-neon-600 px-4 py-2 text-sm font-medium text-white hover:bg-neon-700 disabled:opacity-50"
        >
          <Play size={16} />
          {loading ? 'Starting…' : 'Start Crawler'}
        </button>
      )}
    </div>
  );
}
