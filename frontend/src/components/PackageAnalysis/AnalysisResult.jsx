/**
 * Full analysis result view — assembles RiskScore, evidence cards,
 * optional code viewer, and dependency graph.
 */

import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import RiskScore from './RiskScore';
import EvidenceCard from './EvidenceCard';
import CodeViewer from './CodeViewer';
import DependencyGraph from './DependencyGraph';
import Loader from '../common/Loader';

function buildGraphFromDetection(pkg, detectionDetails) {
  const depEvidence = detectionDetails?.dependency?.evidence || {};
  const deps = Array.isArray(depEvidence.dependencies)
    ? depEvidence.dependencies
    : [];

  if (!pkg?.name || deps.length === 0) return null;

  const nodes = [
    {
      id: pkg.name,
      name: pkg.name,
      riskScore: pkg.risk_score || 0,
      isRoot: true,
    },
  ];
  const edges = [];

  deps.forEach((dep) => {
    if (!dep?.name) return;
    nodes.push({
      id: dep.name,
      name: dep.name,
      riskScore: dep.risk_score || 0,
      isRoot: false,
    });
    edges.push({ source: pkg.name, target: dep.name });
  });

  return { nodes, edges };
}

export default function AnalysisResult() {
  const { analysisResult, analyzing } = useSelector((s) => s.packages);
  const [neutralizing, setNeutralizing] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState('');

  if (analyzing) {
    return <Loader text="Running detectors…" />;
  }

  if (!analysisResult) return null;

  const pkg = analysisResult.package || {};
  const analysis = analysisResult.analysis || {};
  const detectionDetails =
    analysisResult.detection_details || analysisResult.detectionDetails || {};

  const riskScore =
    analysis.risk_score ?? analysisResult.risk_score ?? pkg.risk_score ?? 0;
  const threatLevel =
    analysis.threat_level ?? analysisResult.threat_level ?? pkg.threat_level ?? 'safe';
  const confidence =
    analysis.confidence ?? analysisResult.confidence ?? 0;
  const code = analysisResult.code || '';
  const dependencyGraph =
    analysisResult.dependency_graph || buildGraphFromDetection(pkg, detectionDetails);

  const detectors = Object.entries(detectionDetails);

  const handleNeutralize = async () => {
    setNeutralizing(true);
    try {
      const pkg_id = pkg.id || analysisResult.id || pkg.name || 'unknown';
      const token = localStorage.getItem('obelisk_token');
      const response = await fetch(`/api/v1/packages/${pkg_id}/neutralize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        }
      });
      const data = await response.json();
      if (data.cleanUrl) {
          setDownloadUrl(data.cleanUrl);
      }
    } catch (err) {
      console.error('Failed to neutralize package:', err);
    } finally {
      setNeutralizing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Risk score overview */}
      <div className="flex flex-col items-center justify-between gap-2 rounded-xl border border-gray-700 bg-gray-800 p-6 sm:flex-row sm:gap-8">
        <div className="flex items-center gap-8">
            <RiskScore score={riskScore} threatLevel={threatLevel} size="large" />
            <div className="space-y-1 text-center sm:text-left">
            <p className="text-lg font-bold text-white">
                {(pkg.name || analysisResult.name || 'package')}@{(pkg.version || analysisResult.version || 'unknown')}
            </p>
            <p className="text-sm text-gray-400">
                Overall confidence: {Math.round(confidence * 100)}%
            </p>
            </div>
        </div>

        {riskScore > 75 && (
            <div className="flex flex-col items-end gap-2">
                <button
                  onClick={handleNeutralize}
                  disabled={neutralizing || !!downloadUrl}
                  className="flex items-center gap-2 rounded bg-purple-600 px-4 py-2 font-bold text-white transition hover:bg-purple-700 disabled:opacity-50"
                  title="Surgically remove AST CodeBERT flagged malicious scopes"
                >
                  {neutralizing ? 'Neutralizing...' : downloadUrl ? 'Neutralized' : 'Disarm & Download'}
                </button>
                {downloadUrl && (
                    <a href={downloadUrl} download className="text-sm text-green-400 hover:text-green-300 underline font-mono">
                      Download Safe Source (.tar.gz)
                    </a>
                )}
            </div>
        )}
      </div>

      {/* Detector evidence cards */}
      {detectors.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-300">
            Detection Details
          </h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {detectors.map(([name, result]) => (
              <EvidenceCard key={name} detector={name} result={result} />
            ))}
          </div>
        </div>
      )}

      {/* Source code viewer */}
      {code && <CodeViewer code={code} />}

      {/* Dependency graph */}
      {dependencyGraph && (
        <DependencyGraph
          nodes={dependencyGraph.nodes || []}
          edges={dependencyGraph.edges || []}
        />
      )}
    </div>
  );
}
