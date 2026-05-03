import React, { useState, useEffect } from 'react';
import { CodeDriftViewer } from './CodeDriftViewer';
import { API_BASE_URL } from '../../utils/constants';

interface TimelineItem {
  version: string;
  score: number;
  malicious_file: string | null;
  diff: string | null;
}

interface VersionSliderProps {
  pkgName: string;
}

export const VersionSlider: React.FC<VersionSliderProps> = ({ pkgName }) => {
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [viewIndex, setViewIndex] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const token = localStorage.getItem('obelisk_token');
        const res = await fetch(`${API_BASE_URL}/api/v1/forensics/timeline/${pkgName}`, {
          headers: {
             ...(token && { Authorization: `Bearer ${token}` })
          }
        });
        const data = await res.json();
        setTimeline(data);
        if (data.length > 0) {
          // Find first incident of high score or default to end
          const incidentIdx = data.findIndex((v: TimelineItem) => v.score > 75);
          const defaultIdx = incidentIdx !== -1 ? incidentIdx : data.length - 1;
          setCurrentIndex(defaultIdx);
          setViewIndex(defaultIdx);
        }
      } catch (err) {
        console.error('Failed to fetch forensics timeline:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTimeline();
  }, [pkgName]);

  // Debounce the viewer index so Monaco Editor isn't thrashed during range scrubbing
  useEffect(() => {
    const timer = setTimeout(() => {
      setViewIndex(currentIndex);
    }, 150);
    return () => clearTimeout(timer);
  }, [currentIndex]);

  if (loading) return <div className="text-gray-400 p-4">Loading history forensics for {pkgName}...</div>;
  if (!timeline.length) return <div className="text-red-400 p-4">Failed to load history versions.</div>;

  const currentVersion = timeline[currentIndex]; // For the UI sliders
  const renderVersion = timeline[viewIndex]; // For the Heavy Monaco Component

  const originalCode = viewIndex > 0 
    ? (timeline[viewIndex - 1].diff ? `# Safe state before compromise` : `# Original safe source file`) 
    : `# Earliest retrieved version`;

  return (
    <div className="flex flex-col gap-6 w-full text-white bg-slate-950 p-6 rounded-xl mb-4 shadow-2xl border border-slate-700">
      <div className="flex justify-between items-center border-b border-slate-700 pb-4">
        <h2 className="text-xl font-bold font-mono tracking-tight">Time-Travel Account Takeover Forensics</h2>
        <div className="flex items-center gap-4">
          <div className="text-sm font-mono text-slate-400">Selected Version:</div>
          <div className="bg-slate-800 border border-slate-600 px-3 py-1 rounded text-blue-400 font-bold">v{currentVersion.version}</div>
          <div className={`px-4 py-2 text-xl font-black rounded-lg ${currentVersion.score > 75 ? 'bg-red-500/20 border border-red-500 text-red-500' : 'bg-green-500/20 border border-green-500 text-green-500'}`}>
            Risk: {currentVersion.score}
          </div>
        </div>
      </div>

      <div className="flex flex-col py-4 gap-2">
        <div className="flex justify-between font-mono text-xs text-slate-500 px-1">
          {timeline.map((t, idx) => (
            <span key={t.version} className={idx === currentIndex ? "text-blue-400 font-bold" : ""}>
              {t.version}
              {t.score > 75 && <span className="text-red-500 ml-1">⚠</span>}
            </span>
          ))}
        </div>
        <input 
          type="range"
          min="0"
          max={timeline.length - 1}
          value={currentIndex}
          onChange={(e) => setCurrentIndex(Number(e.target.value))}
          className="w-full h-3 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          title="Scrub to change versions and view payload drifts"
        />
        <div className="text-center text-xs mt-2 text-slate-400">Slide to investigate history and flag compromised versions.</div>
      </div>

      <div className="mt-2 min-h-[500px]">
        {renderVersion.score > 75 && renderVersion.malicious_file ? (
          <CodeDriftViewer 
            key={renderVersion.version}
            filename={renderVersion.malicious_file} 
            originalCode={originalCode} 
            modifiedCode={renderVersion.diff || ''} 
          />
        ) : (
          <div className="h-[500px] w-full flex items-center justify-center bg-slate-900 rounded-xl border border-dashed border-green-800 text-green-400 font-mono tracking-tight text-xl opacity-70">
            No Malicious Payloads Detected in v{renderVersion.version}
          </div>
        )}
      </div>
    </div>
  );
};
