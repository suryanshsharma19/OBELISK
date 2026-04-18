/**
 * Interactive dependency graph rendered with D3 force simulation.
 * Shows packages as nodes coloured by risk, with edges for dependencies.
 */

import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { THREAT_COLORS } from '../../utils/constants';

function nodeColor(riskScore) {
  if (riskScore >= 80) return THREAT_COLORS.critical;
  if (riskScore >= 60) return THREAT_COLORS.high;
  if (riskScore >= 40) return THREAT_COLORS.medium;
  if (riskScore >= 20) return THREAT_COLORS.low;
  return THREAT_COLORS.safe;
}

function normalizeGraphInput(nodes, edges, dependencies, rootName) {
  if (Array.isArray(nodes) && nodes.length > 0) {
    return { nodes, edges: Array.isArray(edges) ? edges : [] };
  }

  if (!Array.isArray(dependencies) || dependencies.length === 0) {
    return { nodes: [], edges: [] };
  }

  const rootId = rootName || 'package';
  const nextNodes = [
    {
      id: rootId,
      name: rootId,
      riskScore: 0,
      isRoot: true,
    },
  ];
  const nextEdges = [];

  dependencies.forEach((dep) => {
    if (!dep?.name) return;
    nextNodes.push({
      id: dep.name,
      name: dep.name,
      riskScore: dep.risk_score || 0,
      isRoot: false,
    });
    nextEdges.push({ source: rootId, target: dep.name });
  });

  return { nodes: nextNodes, edges: nextEdges };
}

export default function DependencyGraph({ nodes = [], edges = [], dependencies = [], rootName = '' }) {
  const svgRef = useRef(null);
  const graph = normalizeGraphInput(nodes, edges, dependencies, rootName);

  useEffect(() => {
    if (!graph.nodes.length || !svgRef.current) return;

    const width = svgRef.current.clientWidth || 600;
    const height = 400;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3
      .select(svgRef.current)
      .attr('viewBox', [0, 0, width, height]);

    // Build the simulation
    const simulation = d3
      .forceSimulation(graph.nodes)
      .force('link', d3.forceLink(graph.edges).id((d) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Draw edges
    const link = svg
      .append('g')
      .selectAll('line')
      .data(graph.edges)
      .join('line')
      .attr('stroke', '#4b5563')
      .attr('stroke-width', 1.5);

    // Draw nodes
    const node = svg
      .append('g')
      .selectAll('circle')
      .data(graph.nodes)
      .join('circle')
      .attr('r', (d) => (d.isRoot ? 12 : 8))
      .attr('fill', (d) => nodeColor(d.riskScore || 0))
      .attr('stroke', '#1f2937')
      .attr('stroke-width', 2)
      .call(
        d3.drag()
          .on('start', (e, d) => {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (e, d) => {
            d.fx = e.x;
            d.fy = e.y;
          })
          .on('end', (e, d) => {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    // Labels
    const label = svg
      .append('g')
      .selectAll('text')
      .data(graph.nodes)
      .join('text')
      .text((d) => d.name || d.id)
      .attr('font-size', 10)
      .attr('fill', '#9ca3af')
      .attr('dx', 14)
      .attr('dy', 4);

    // Tooltip on hover
    node.append('title').text((d) => `${d.name || d.id} (risk: ${d.riskScore || 0})`);

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node.attr('cx', (d) => d.x).attr('cy', (d) => d.y);
      label.attr('x', (d) => d.x).attr('y', (d) => d.y);
    });

    return () => simulation.stop();
  }, [graph.nodes, graph.edges]);

  if (!graph.nodes.length) {
    return (
      <div className="rounded-xl border border-gray-700 bg-gray-800 p-5 text-sm text-gray-500">
        No dependency data available
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-700 bg-gray-800 p-4">
      <h4 className="mb-3 text-sm font-semibold text-gray-300">Dependency Graph</h4>
      <svg ref={svgRef} className="w-full" style={{ minHeight: 400 }} />
    </div>
  );
}
