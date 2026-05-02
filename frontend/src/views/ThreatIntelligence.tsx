import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import Loader from '../components/common/Loader';

import { API_BASE_URL } from '../utils/constants';

export default function ThreatIntelligence() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCTI = async () => {
      try {
        const token = localStorage.getItem('obelisk_token');
        const res = await fetch(`${API_BASE_URL}/api/stats/threat-intelligence`, {
          headers: {
            ...(token && { Authorization: `Bearer ${token}` })
          }
        });
        if (!res.ok) throw new Error('API returned ' + res.status);
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchCTI();
  }, []);

  if (loading) return <Loader text="Mapping Threat Actors..." />;
  if (error) return <div className="text-red-500 p-8 text-center text-xl">Failed to load Threat Intel: {error}</div>;

  // Group by Cluster ID
  const clusters: any = {};
  data.forEach((pkg) => {
    const cti = pkg.cti_attribution;
    const cid = cti?.cluster_id ?? -1;
    if (!clusters[cid]) {
      clusters[cid] = {
        name: cti?.actor_profile?.name || `Cluster ${cid}`,
        desc: cti?.actor_profile?.description,
        x: [], y: [], z: [],
        text: []
      };
    }
    clusters[cid].x.push(cti.coordinates[0]);
    clusters[cid].y.push(cti.coordinates[1]);
    clusters[cid].z.push(cti.coordinates[2]);
    clusters[cid].text.push(`${pkg.name} | Conf: ${cti.confidence}%`);
  });

  const plotData = Object.values(clusters).map((cluster: any, idx) => ({
    x: cluster.x,
    y: cluster.y,
    z: cluster.z,
    text: cluster.text,
    mode: 'markers',
    type: 'scatter3d',
    name: cluster.name,
    marker: {
      size: 6,
      opacity: 0.8,
      line: {
          color: 'rgba(217, 217, 217, 0.14)',
          width: 0.5
      }
    }
  }));

  const layout = {
      title: 'Threat Actor Clustering (DBSCAN 3D Feature Space)',
      autosize: true,
      paper_bgcolor: '#0f172a',
      plot_bgcolor: '#0f172a',
      font: { color: '#e2e8f0' },
      scene: {
          xaxis: { title: 'Code Entropy', backgroundcolor: '#1e293b', gridcolor: '#334155' },
          yaxis: { title: 'Network C2 IPs', backgroundcolor: '#1e293b', gridcolor: '#334155' },
          zaxis: { title: 'FS Targets', backgroundcolor: '#1e293b', gridcolor: '#334155' },
      },
      margin: {
          l: 0, r: 0, b: 0, t: 30
      }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-900 p-6 text-white pb-20">
      <div className="mb-4 space-y-2">
        <h1 className="text-3xl font-black font-mono tracking-tight text-blue-500">Cyber Threat Intelligence (CTI)</h1>
        <p className="text-slate-400 font-mono text-sm max-w-4xl">
          Unsupervised ML mapping of distinct malicious packages grouped by their behavioral and code signatures to attribute campaigns to specific cybercriminal entities.
        </p>
      </div>

      <div className="flex flex-wrap gap-4 mb-4">
        {Object.values(clusters).map((c: any) => (
           <div key={c.name} className="flex items-center space-x-2 bg-slate-800 p-2 rounded border border-slate-700">
               <div className="text-sm font-bold text-slate-200">{c.name}</div>
               <div className="text-xs text-slate-500">{c.desc}</div>
           </div>
        ))}
      </div>

      <div className="flex-1 w-full rounded-xl overflow-hidden shadow-2xl border border-slate-700 bg-slate-800">
        <Plot
          data={plotData as any}
          layout={layout as any}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
}
