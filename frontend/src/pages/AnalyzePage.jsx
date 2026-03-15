/**
 * Package analysis page — form + results.
 */

import React from 'react';
import AnalyzeForm from '../components/PackageAnalysis/AnalyzeForm';
import AnalysisResult from '../components/PackageAnalysis/AnalysisResult';

export default function AnalyzePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Analyze Package</h1>
      <AnalyzeForm />
      <AnalysisResult />
    </div>
  );
}
