// PackageDetailPage - detailed view for a single analyzed package

import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

import { getPackageDetail } from '../services/api';
import Loader from '../components/common/Loader';
import RiskScore from '../components/PackageAnalysis/RiskScore';
import EvidenceCard from '../components/PackageAnalysis/EvidenceCard';
import DependencyGraph from '../components/PackageAnalysis/DependencyGraph';
import AlertCard from '../components/Alerts/AlertCard';

export default function PackageDetailPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    getPackageDetail(id)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || 'Failed to load package');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) return <Loader />;
  if (error)
    return (
      <div className="mt-12 text-center text-red-400">
        <p>{error}</p>
        <Link to="/packages" className="mt-4 inline-block text-cyan-400 underline">
          ← Back to packages
        </Link>
      </div>
    );

  const { package: pkg, analysis, alerts = [], dependencies = [] } = data;

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {pkg.name}{' '}
            <span className="text-base font-normal text-gray-400">v{pkg.version}</span>
          </h1>
          <span className="mt-1 inline-block rounded bg-gray-800 px-2 py-0.5 text-xs uppercase text-gray-400">
            {pkg.registry}
          </span>
        </div>

        <RiskScore score={pkg.risk_score} threatLevel={pkg.threat_level} size="large" />
      </div>

      {/* Analysis breakdown */}
      {analysis && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-200">Detection Breakdown</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(analysis.breakdown || {}).map(([key, value]) => (
              <EvidenceCard
                key={key}
                detector={key}
                result={{
                  score: value?.score || 0,
                  confidence: analysis?.confidence || 0,
                  evidence: {
                    weight: value?.weight || 0,
                    contribution: value?.contribution || 0,
                  },
                }}
              />
            ))}
          </div>
        </section>
      )}

      {/* Dependency graph */}
      {dependencies.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-200">Dependency Graph</h2>
          <DependencyGraph dependencies={dependencies} rootName={pkg.name} />
        </section>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-200">
            Alerts ({alerts.length})
          </h2>
          <div className="space-y-3">
            {alerts.map((a) => (
              <AlertCard key={a.id} alert={a} />
            ))}
          </div>
        </section>
      )}

      <Link to="/packages" className="text-sm text-cyan-400 hover:underline">
        ← Back to packages
      </Link>
    </div>
  );
}
