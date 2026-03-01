/**
 * Crawler status monitor — shows run state, counts, and live feed.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { getCrawlerStatus } from '../../services/api';
import { POLL_INTERVAL } from '../../utils/constants';
import CrawlerControls from './CrawlerControls';
import LiveFeed from './LiveFeed';
import Loader from '../common/Loader';

export default function CrawlerMonitor() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getCrawlerStatus();
      setStatus(data);
    } catch (err) {
      console.error('Crawler status fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (loading) return <Loader fullPage text="Loading crawler status…" />;

  const isRunning = status?.is_running ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Registry Crawler</h1>
        <CrawlerControls isRunning={isRunning} onRefresh={fetchStatus} />
      </div>

      {/* Status card */}
      <div className="rounded-xl border border-gray-700 bg-gray-800 p-5">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-gray-500">Status</p>
            <p className={`text-sm font-semibold ${isRunning ? 'text-emerald-400' : 'text-gray-400'}`}>
              {isRunning ? 'Running' : 'Stopped'}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Packages Scanned</p>
            <p className="text-sm font-semibold text-white">
              {status?.packages_scanned ?? 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Threats Found</p>
            <p className="text-sm font-semibold text-red-400">
              {status?.threats_found ?? 0}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Registry</p>
            <p className="text-sm font-semibold text-white">
              {status?.registry || '—'}
            </p>
          </div>
        </div>
      </div>

      {/* Live feed */}
      <LiveFeed />
    </div>
  );
}
