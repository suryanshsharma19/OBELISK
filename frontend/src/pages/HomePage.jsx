/**
 * Landing page — hero section with quick-start CTA.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Search, BarChart2, Bell } from 'lucide-react';

const FEATURES = [
  { icon: Search, title: 'Deep Analysis', desc: 'Scan any npm or PyPI package with 5 ML-powered detectors.' },
  { icon: BarChart2, title: 'Risk Scoring', desc: 'Weighted aggregation with confidence metrics across all signals.' },
  { icon: Bell, title: 'Real-time Alerts', desc: 'Instant notifications when malicious packages are detected.' },
];

export default function HomePage() {
  return (
    <div className="flex flex-col items-center gap-12 py-12">
      {/* Hero */}
      <div className="max-w-2xl space-y-4 text-center">
        <Shield size={56} className="mx-auto text-emerald-400" />
        <h1 className="text-4xl font-extrabold text-white">
          Protect Your Supply Chain
        </h1>
        <p className="text-gray-400">
          OBELISK is an AI-powered system that detects malicious packages in
          the npm and PyPI ecosystems before they reach your codebase.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/analyze"
            className="rounded-lg bg-emerald-600 px-6 py-3 text-sm font-medium text-white hover:bg-emerald-700"
          >
            Analyze a Package
          </Link>
          <Link
            to="/dashboard"
            className="rounded-lg border border-gray-600 px-6 py-3 text-sm font-medium text-gray-300 hover:bg-gray-800"
          >
            View Dashboard
          </Link>
        </div>
      </div>

      {/* Feature cards */}
      <div className="grid w-full max-w-4xl grid-cols-1 gap-6 sm:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, desc }) => (
          <div
            key={title}
            className="rounded-xl border border-gray-700 bg-gray-800 p-6 text-center"
          >
            <Icon size={32} className="mx-auto mb-3 text-emerald-400" />
            <h3 className="mb-1 text-sm font-semibold text-white">{title}</h3>
            <p className="text-xs text-gray-400">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
