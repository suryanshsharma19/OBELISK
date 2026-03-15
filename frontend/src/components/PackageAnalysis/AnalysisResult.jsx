/**
 * Full analysis result view — assembles RiskScore, evidence cards,
 * optional code viewer, and dependency graph.
 */

import React from 'react';
import { useSelector } from 'react-redux';
import RiskScore from './RiskScore';
import EvidenceCard from './EvidenceCard';
import CodeViewer from './CodeViewer';
import DependencyGraph from './DependencyGraph';
import Loader from '../common/Loader';

export default function AnalysisResult() {
  const { analysisResult, analyzing } = useSelector((s) => s.packages);

  if (analyzing) {
    return <Loader text="Running detectors…" />;
  }

  if (!analysisResult) return null;

  const {
    risk_score = 0,
    threat_level = 'safe',
    confidence = 0,
    detection_details = {},
    code,
    dependency_graph,
  } = analysisResult;

  const detectors = Object.entries(detection_details);

  return (
    <div className="space-y-6">
      {/* Risk score overview */}
      <div className="flex flex-col items-center gap-2 rounded-xl border border-gray-700 bg-gray-800 p-6 sm:flex-row sm:gap-8">
        <RiskScore score={risk_score} threatLevel={threat_level} />
        <div className="space-y-1 text-center sm:text-left">
          <p className="text-lg font-bold text-white">
            {analysisResult.name}@{analysisResult.version}
          </p>
          <p className="text-sm text-gray-400">
            Overall confidence: {Math.round(confidence * 100)}%
          </p>
        </div>
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
      {dependency_graph && (
        <DependencyGraph
          nodes={dependency_graph.nodes || []}
          edges={dependency_graph.edges || []}
        />
      )}
    </div>
  );
}
