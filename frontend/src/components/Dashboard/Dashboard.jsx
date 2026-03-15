/**
 * Dashboard container — fetches stats & alerts, then composes
 * StatsCards, ThreatChart, ThreatDistribution, and RecentAlerts.
 */

import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchAlerts } from '../../store/slices/alertsSlice';
import { getStatsOverview, getStatsTrend } from '../../services/api';
import { POLL_INTERVAL } from '../../utils/constants';
import StatsCards from './StatsCards';
import ThreatChart from './ThreatChart';
import ThreatDistribution from './ThreatDistribution';
import RecentAlerts from './RecentAlerts';
import Loader from '../common/Loader';

export default function Dashboard() {
  const dispatch = useDispatch();
  const alerts = useSelector((s) => s.alerts.list);

  const [stats, setStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch dashboard data on mount and poll periodically
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [overview, trendData] = await Promise.all([
          getStatsOverview(),
          getStatsTrend(7),
        ]);
        if (!cancelled) {
          setStats(overview);
          setTrend(trendData.trend || []);
        }
      } catch (err) {
        console.error('Dashboard fetch failed:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    dispatch(fetchAlerts({ limit: 5 }));

    const interval = setInterval(load, POLL_INTERVAL);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [dispatch]);

  if (loading) return <Loader fullPage text="Loading dashboard…" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Dashboard</h1>

      <StatsCards stats={stats} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ThreatChart trend={trend} />
        </div>
        <ThreatDistribution distribution={stats?.threat_distribution} />
      </div>

      <RecentAlerts alerts={alerts} />
    </div>
  );
}
