import React, { useEffect, useRef, useMemo, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import * as d3 from 'd3';
import { parseSbomData } from '../utils/sbomParser';
import './DependencyGraph.css';

cytoscape.use(dagre);

const DependencyGraph = ({ data, format }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [warning, setWarning] = useState(null);
  const [error, setError] = useState(null);

  const normalizedData = useMemo(() => {
    try {
      if (!data) throw new Error('No SBOM data provided');
      const parsed = parseSbomData(data, format);
      return parsed;
    } catch (err) {
      setError(`Failed to parse ${format} SBOM: ${err.message}`);
      return null;
    }
  }, [data, format]);

  useEffect(() => {
    if (!normalizedData || !containerRef.current) {
      setError(normalizedData ? 'No container available' : `Invalid ${format} data`);
      return;
    }

    const elements = convertSbomToGraphElements(normalizedData);
    const nodes = elements.filter(el => el.data.id && !el.data.source);
    const edges = elements.filter(el => el.data.source && el.data.target);

    if (elements.length === 0) {
      setError(`No graph elements generated from ${format} SBOM`);
      return;
    }
    if (nodes.length > 1 && edges.length === 0) {
      setWarning(`No edges found in ${format} SBOM. Check "DEPENDS_ON" relationships.`);
    }
    if (elements.length === 1) {
      setWarning(`Only one node found. ${format} SBOM may be incomplete.`);
    }

    const maxVulns = Math.max(...nodes.map(n => (n.data.vulnerabilities || []).length), 1);
    const vulnColor = d3.scaleSequential().domain([0, maxVulns]).interpolator(d3.interpolateReds);

    const styles = [
      {
        selector: 'node',
        style: {
          'background-color': ele => {
            const count = (ele.data('vulnerabilities') || []).length;
            return count > 0 ? vulnColor(count) : '#6FB1FC';
          },
          'border-color': ele => {
            const count = (ele.data('vulnerabilities') || []).length;
            return count > 0 ? d3.color(vulnColor(count)).darker(1).toString() : '#2980B9';
          },
          'border-width': 2,
          'label': 'data(label)',
          'color': '#333',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '14px',
          'text-wrap': 'wrap',
          'text-max-width': '120px',
          'padding': '12px',
          'width': 'label',
          'height': 'label',
        },
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#95A5A6',
          'target-arrow-color': '#95A5A6',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'arrow-scale': 0.8,
        },
      },
      {
        selector: 'node.root',
        style: {
          'background-color': '#2ECC71',
          'border-color': '#27AE60',
          'border-width': 3,
        },
      },
    ];

    const initCytoscape = () => {
      cyRef.current = cytoscape({
        container: containerRef.current,
        elements,
        style: styles,
        layout: {
          name: elements.length > 50 ? 'cose' : 'dagre',
          rankDir: 'LR',
          nodeSep: 100,
          rankSep: 120,
          padding: 60,
          animate: true,
        },
        zoom: 1,
        minZoom: 0.2,
        maxZoom: 3,
        wheelSensitivity: 0.2,
      });

      cyRef.current.on('tap', 'node', evt => {
        cyRef.current.animate({
          fit: { eles: evt.target, padding: 100 },
          duration: 300,
        });
      });

      cyRef.current.on('mouseover', 'node', evt => showTooltip(evt.target));
      cyRef.current.on('mouseout', 'node', hideTooltips);

      cyRef.current.resize();
      cyRef.current.fit();
    };

    const showTooltip = (node) => {
      const vulnerabilities = node.data('vulnerabilities') || [];
      if (!vulnerabilities.length) return;

      const canvas = containerRef.current;
      const position = node.renderedPosition();
      const tooltip = document.createElement('div');
      tooltip.className = 'graph-tooltip';
      tooltip.style.left = `${position.x + canvas.offsetLeft + 10}px`;
      tooltip.style.top = `${position.y + canvas.offsetTop + 10}px`;
      tooltip.innerHTML = `
        <div class="tooltip-content">
          <strong>${vulnerabilities.length} Vulnerabilities:</strong>
          <ul>
            ${vulnerabilities.slice(0, 10).map(v => `<li>${v.id}</li>`).join('')}
            ${vulnerabilities.length > 10 ? `<li>...and ${vulnerabilities.length - 10} more</li>` : ''}
          </ul>
        </div>
      `;
      tooltip.style.position = 'absolute';
      canvas.appendChild(tooltip);
    };

    const hideTooltips = () => {
      containerRef.current.querySelectorAll('.graph-tooltip').forEach(t => t.remove());
    };

    const timeout = setTimeout(() => {
      if (containerRef.current.offsetHeight === 0) {
        setTimeout(initCytoscape, 100);
      } else {
        initCytoscape();
      }
    }, 100);

    const resizeObserver = new ResizeObserver(([entry]) => {
      if (cyRef.current && entry.contentRect.height > 0) {
        cyRef.current.resize();
        cyRef.current.fit();
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      clearTimeout(timeout);
      resizeObserver.disconnect();
      cyRef.current?.destroy();
    };
  }, [normalizedData, format]);

  const zoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const zoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() / 1.2);
  const resetZoom = () => cyRef.current?.animate({ fit: { padding: 60 }, duration: 300 });

  return (
    <div className="dependency-graph-wrapper">
      <div className="dependency-graph-container">
        <div className="graph-controls">
          <button onClick={zoomIn}>Zoom In</button>
          <button onClick={zoomOut}>Zoom Out</button>
          <button onClick={resetZoom}>Reset View</button>
        </div>
        {warning && <div className="graph-warning">{warning}</div>}
        {error && <div className="graph-error">{error}</div>}
        <div ref={containerRef} className="dependency-graph" />
      </div>
      <GraphLegend />
    </div>
  );
};

const GraphLegend = () => (
  <div className="graph-legend">
    {[
      { color: '#2ECC71', label: 'Root Component' },
      { color: '#6FB1FC', label: 'No Vulnerabilities' },
      { color: '#FFCCCC', label: 'Low Vulnerabilities' },
      { color: '#8B0000', label: 'High Vulnerabilities' },
    ].map(({ color, label }) => (
      <div className="legend-item" key={label}>
        <div className="legend-color" style={{ backgroundColor: color }} />
        <div className="legend-label">{label}</div>
      </div>
    ))}
  </div>
);

const convertSbomToGraphElements = (sbomData) => {
  const elements = [];
  const seen = new Set();

  if (!sbomData?.name || !Array.isArray(sbomData.versions)) return elements;

  const sorted = [...sbomData.versions].sort((a, b) =>
    b.version_id.localeCompare(a.version_id, undefined, { numeric: true })
  );

  sorted.forEach((version, idx) => {
    const id = `${sbomData.name}-${version.version_id}`;
    const node = {
      data: {
        id,
        label: `${sbomData.name}\n${version.version_id}`,
        vulnerabilities: version.vulnerabilities || [],
      },
      classes: `${idx === 0 ? 'root' : ''} ${version.vulnerabilities?.length ? 'vulnerable' : ''}`.trim(),
    };

    elements.push(node);
    seen.add(id);

    version.dependencies?.forEach(dep => processDependency(dep, id, elements, seen));
  });

  return elements;
};

const processDependency = (dep, parentId, elements, seen) => {
  const depId = `${dep.name}-${dep.version_id}`;
  if (!seen.has(depId)) {
    elements.push({
      data: {
        id: depId,
        label: `${dep.name}\n${dep.version_id}`,
        vulnerabilities: dep.vulnerabilities || [],
      },
      classes: dep.vulnerabilities?.length ? 'vulnerable' : '',
    });
    seen.add(depId);

    dep.dependencies?.forEach(child => processDependency(child, depId, elements, seen));
  }

  elements.push({
    data: { id: `${parentId}-${depId}`, source: parentId, target: depId },
  });
};

export default DependencyGraph;
