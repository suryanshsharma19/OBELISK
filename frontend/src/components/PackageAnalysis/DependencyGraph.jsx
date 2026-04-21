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
    return { 
      nodes: nodes.map(n => ({ ...n })), 
      edges: Array.isArray(edges) ? edges.map(e => ({ ...e })) : [] 
    };
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
    const height = 450;

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3
      .select(svgRef.current)
      .attr('viewBox', [0, 0, width, height])
      .style('background-color', '#131313'); // Aegis Void Black

    // Add zoom wrapper container
    const g = svg.append('g');

    // Pan and Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });
    svg.call(zoom);

    // Build the simulation with tighter gravity to keep node clusters
    const simulation = d3
      .forceSimulation(graph.nodes)
      .force('link', d3.forceLink(graph.edges).id((d) => d.id).distance(200))
      .force('charge', d3.forceManyBody().strength(-900))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(45)); // Prevent overlap

    // Draw sharp, transparent-ish edges
    const link = g
      .append('g')
      .selectAll('line')
      .data(graph.edges)
      .join('line')
      .attr('stroke', '#333333')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4 2'); // Terminal style dotted lines

    // Brutalist square nodes
    const rootSize = 24;
    const nodeSize = 16;

    const node = g
      .append('g')
      .selectAll('rect')
      .data(graph.nodes)
      .join('rect')
      .attr('width', (d) => (d.isRoot ? rootSize : nodeSize))
      .attr('height', (d) => (d.isRoot ? rootSize : nodeSize))
      .attr('fill', (d) => nodeColor(d.riskScore || 0))
      .attr('stroke', '#000000') // Hard boundaries
      .attr('stroke-width', 3)
      .attr('cursor', 'grab')
      .call(
        d3.drag()
          .on('start', function(e, d) {
            if (!e.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
            d3.select(this).attr('cursor', 'grabbing');
          })
          .on('drag', (e, d) => {
            d.fx = e.x;
            d.fy = e.y;
          })
          .on('end', function(e, d) {
            if (!e.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
            d3.select(this).attr('cursor', 'grab');
          }),
      );

    // Monospace sharp labels
    const label = g
      .append('g')
      .selectAll('text')
      .data(graph.nodes)
      .join('text')
      .text((d) => (d.name || d.id).toUpperCase())
      .attr('font-size', 10)
      .attr('font-family', '"JetBrains Mono", monospace')
      .attr('font-weight', 'bold')
      .attr('fill', '#ffffff')
      .style('pointer-events', 'none')
      .attr('dx', (d) => (d.isRoot ? rootSize + 8 : nodeSize + 8))
      .attr('dy', (d) => (d.isRoot ? rootSize / 2 + 4 : nodeSize / 2 + 4));

    // Tooltip on hover
    node.append('title').text((d) => `MODULE: ${d.name || d.id}\nRISK: ${d.riskScore || 0}`);

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);

      node
        .attr('x', (d) => d.x - (d.isRoot ? rootSize / 2 : nodeSize / 2))
        .attr('y', (d) => d.y - (d.isRoot ? rootSize / 2 : nodeSize / 2));

      label.attr('x', (d) => d.x).attr('y', (d) => d.y);
    });

    return () => simulation.stop();
  }, [graph.nodes, graph.edges]);

  if (!graph.nodes.length) {
    return (
      <div className="border-2 border-outline-variant bg-surface-container font-mono p-4 text-outline uppercase text-xs">
        [SYS_ERROR] NO DEPENDENCY TOPOLOGY DISCOVERED
      </div>
    );
  }

  return (
    <div className="border-2 border-outline-variant bg-[#131313] p-0 relative group shadow-lg">
      <div className="absolute top-0 left-0 bg-primary-container text-on-primary-container px-3 py-1 font-mono text-[10px] uppercase font-bold z-10 border-b-2 border-r-2 border-outline-variant">
        DEPENDENCY_TOPOLOGY
      </div>
      <svg ref={svgRef} className="w-full cursor-crosshair z-0" style={{ minHeight: 450 }} />
    </div>
  );
}
