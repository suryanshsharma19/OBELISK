import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { API_BASE_URL } from '../../utils/constants';

interface BlastRadiusProps {
  pkgName: string;
}

interface Node extends d3.SimulationNodeDatum {
  id: string;
  group: number;
  infected: boolean;
  layer: number;
  risk_score: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  infected: boolean;
}

export const BlastRadius: React.FC<BlastRadiusProps> = ({ pkgName }) => {
  const d3Container = useRef<SVGSVGElement>(null);
  const [impactedCount, setImpactedCount] = useState(0);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Initial Root Node
    const initialNodes: Node[] = [{ id: pkgName, group: 1, infected: true, layer: 0, risk_score: 100 }];
    setNodes(initialNodes);
    
    // Connect to SSE API
    const eventSource = new EventSource(`${API_BASE_URL}/api/v1/graph/blast-radius/${pkgName}`);
    
    eventSource.onmessage = (event) => {
      const parsedData = JSON.parse(event.data);
      
      if (parsedData.event === 'error') {
        setError(parsedData.data);
        eventSource.close();
      } else if (parsedData.event === 'done') {
        eventSource.close();
      } else if (parsedData.event === 'layer') {
        const layerData = parsedData.data;
        setNodes(prev => {
            const newNodes = [...prev];
            const newLinks = [...links];
            let addedCount = 0;
            
            layerData.forEach((item: any) => {
              if (!newNodes.find(n => n.id === item.name)) {
                newNodes.push({ id: item.name, group: 2, infected: true, layer: item.path.length, risk_score: item.risk_score });
                addedCount++;
              }
              // Add links based on the path
              const parent = item.path.length >= 2 ? item.path[item.path.length - 2] : pkgName;
              if (parent && !newLinks.find(l => (l.source === parent && l.target === item.name))) {
                  newLinks.push({ source: parent, target: item.name, infected: true });
              }
            });
            
            setLinks(newLinks);
            setImpactedCount(prevCount => prevCount + addedCount);
            return newNodes;
        });
      }
    };

    return () => {
      if (eventSource.readyState === 1) {
          eventSource.close();
      }
    };
  }, [pkgName]);

  useEffect(() => {
    if (nodes.length === 0 || !d3Container.current) return;

    const svg = d3.select(d3Container.current);
    svg.selectAll("*").remove();

    const width = d3Container.current.parentElement?.clientWidth || 800;
    const height = d3Container.current.parentElement?.clientHeight || 600;

    // Use viewBox to make sure it scales properly and set view space
    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(20).iterations(2));

    const link = svg.append("g")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 2)
      .attr("stroke", d => d.infected ? "#ff0000" : "#999")
      // Red pulsing link animation
      .attr("stroke-dasharray", "5,5")
      .style("animation", "dash 1s linear infinite");

    const node = svg.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", d => d.layer === 0 ? 15 : 10)
      .attr("fill", d => d.infected ? "#ff0000" : "#69b3a2");
      
    // Pulse animation for the root
    node.filter(d => d.layer === 0)
        .html("<animate attributeName='r' values='15;20;15' dur='1s' repeatCount='indefinite' />");

    node.append("title")
      .text(d => d.id);

    simulation.on("tick", () => {
      // Constrain nodes to stay within the SVG boundaries
      node
        .attr("cx", d => d.x = Math.max(15, Math.min(width - 15, d.x!)))
        .attr("cy", d => d.y = Math.max(15, Math.min(height - 15, d.y!)));

      link
        .attr("x1", d => (d.source as Node).x!)
        .attr("y1", d => (d.source as Node).y!)
        .attr("x2", d => (d.target as Node).x!)
        .attr("y2", d => (d.target as Node).y!);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links]);

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 text-white p-4 rounded-xl shadow-lg border border-slate-700">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold font-mono tracking-tight">
            Blast Radius Simulator 
            <span className="text-sm font-normal text-slate-400 ml-2">Target: {pkgName}</span>
        </h2>
        <div className="bg-red-500/20 border border-red-500/50 px-4 py-2 rounded-lg text-red-400 font-mono">
            Impacted Repositories: <span className="font-bold text-red-500 text-xl">{impactedCount}</span>
        </div>
      </div>
      
      {error && (
          <div className="text-red-500 mb-2 p-2 bg-red-900/30 rounded border border-red-800">
              Error loading graph: {error}
          </div>
      )}

      <div className="flex-1 w-full h-full min-h-[500px] bg-slate-950 rounded-lg overflow-hidden border border-slate-800 relative">
        <svg ref={d3Container} className="w-full h-full" />
      </div>
    </div>
  );
};
