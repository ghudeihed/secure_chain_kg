import React, { useEffect, useRef, useMemo, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import * as d3 from 'd3';
import { parseSbomData } from '../utils/sbomParser';
import './DependencyGraph.css';

// Register the dagre layout
cytoscape.use(dagre);

const DependencyGraph = ({ data, format }) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [warning, setWarning] = useState(null);
  const [error, setError] = useState(null);

  // Normalize SBOM data
  const normalizedData = useMemo(() => {
    try {
      if (!data) {
        throw new Error('No SBOM data provided');
      }
      const parsed = parseSbomData(data, format);
      console.log(`Normalized Data for ${format}:`, JSON.stringify(parsed, null, 2));
      return parsed;
    } catch (error) {
      console.error(`Error parsing SBOM data for ${format}:`, error);
      setError(`Failed to parse ${format} SBOM: ${error.message}`);
      return null;
    }
  }, [data, format]);

  useEffect(() => {
    if (!normalizedData || !containerRef.current) {
      console.log('Missing data or container:', { data: normalizedData, container: containerRef.current });
      setError(normalizedData ? 'No container available for rendering' : `Invalid ${format} data`);
      return;
    }

    // Log initial container dimensions
    console.log('Initial container dimensions:', {
      width: containerRef.current.offsetWidth,
      height: containerRef.current.offsetHeight,
    });

    // Initialize Cytoscape
    const initializeCytoscape = () => {
      try {
        const elements = convertSbomToGraphElements(normalizedData);
        console.log('Graph elements count:', elements.length, 'Elements:', JSON.stringify(elements, null, 2));

        // Check for nodes and edges
        const nodes = elements.filter((el) => el.data.id && !el.data.source);
        const edges = elements.filter((el) => el.data.source && el.data.target);
        console.log(`Nodes: ${nodes.length}, Edges: ${edges.length}`);

        // Calculate max vulnerabilities for color scale
        const maxVulnerabilities = Math.max(
          ...elements
            .filter((el) => el.data.id && !el.data.source)
            .map((el) => (el.data.vulnerabilities || []).length),
          1 // Ensure at least 1 to avoid division by zero
        );
        console.log(`Max vulnerabilities for color scale: ${maxVulnerabilities}`);

        // Create color scale for vulnerabilities
        const vulnColorScale = d3.scaleSequential()
          .domain([0, maxVulnerabilities])
          .interpolator(d3.interpolateReds);

        if (elements.length === 0) {
          setError(`No graph elements generated from ${format} SBOM data`);
          return;
        }
        if (nodes.length > 1 && edges.length === 0) {
          setWarning(`No relationships (edges) generated for ${format} SBOM. Check the SBOM data for missing or incorrect DEPENDS_ON relationships.`);
        }
        if (elements.length === 1) {
          setWarning(`Only one node generated for ${format} SBOM. The data may be incomplete or incorrectly formatted.`);
        }

        cyRef.current = cytoscape({
          container: containerRef.current,
          elements: elements,
          style: [
            {
              selector: 'node',
              style: {
                'background-color': (ele) => {
                  const vulnCount = (ele.data('vulnerabilities') || []).length;
                  return vulnCount > 0 ? vulnColorScale(vulnCount) : '#6FB1FC';
                },
                'border-width': 2,
                'border-color': (ele) => {
                  const vulnCount = (ele.data('vulnerabilities') || []).length;
                  return vulnCount > 0 ? d3.color(vulnColorScale(vulnCount)).darker(1).toString() : '#2980B9';
                },
                'label': 'data(label)',
                'color': '#333',
                'text-valign': 'center',
                'text-halign': 'center',
                'font-size': '14px',
                'text-wrap': 'wrap',
                'text-max-width': '120px',
                'width': 'label',
                'height': 'label',
                'padding': '12px',
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
          ],
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

        cyRef.current.panningEnabled(true);
        cyRef.current.userPanningEnabled(true);

        // Handle node tap to zoom
        cyRef.current.on('tap', 'node', function (evt) {
          const node = evt.target;
          cyRef.current.animate({
            fit: { eles: node, padding: 100 },
            duration: 300,
          });
        });

        // Handle node hover to show tooltip
        cyRef.current.on('mouseover', 'node', function (evt) {
          const node = evt.target;
          const vulnerabilities = node.data('vulnerabilities') || [];
          if (vulnerabilities.length > 0) {
            const position = node.renderedPosition();
            const canvas = containerRef.current;
            const tooltip = document.createElement('div');
            tooltip.className = 'graph-tooltip';
            tooltip.style.position = 'absolute';
            tooltip.style.left = `${position.x + canvas.offsetLeft + 10}px`;
            tooltip.style.top = `${position.y + canvas.offsetTop + 10}px`;

            tooltip.innerHTML = `
              <div class="tooltip-content">
                <strong>${vulnerabilities.length} Vulnerabilities:</strong>
                <ul>
                  ${vulnerabilities.slice(0, 10).map(v => `<li>${v.id}</li>`).join('')}
                  ${vulnerabilities.length > 10 ? `<li>... and ${vulnerabilities.length - 10} more</li>` : ''}
                </ul>
              </div>
            `;
            canvas.appendChild(tooltip);
          }
        });

        cyRef.current.on('mouseout', 'node', function () {
          const tooltips = containerRef.current.querySelectorAll('.graph-tooltip');
          tooltips.forEach(tooltip => tooltip.remove());
        });

        cyRef.current.on('render', () => {
          console.log('Cytoscape rendered, canvas size:', {
            width: cyRef.current.width(),
            height: cyRef.current.height(),
          });
          // Log node styles for debugging
          elements
            .filter((el) => el.data.id && !el.data.source)
            .forEach((el) => {
              console.log(`Node ${el.data.id}: Classes=${el.classes}, Vulnerabilities=${(el.data.vulnerabilities || []).length}`);
            });
        });

        cyRef.current.resize();
        cyRef.current.fit();

        setError(null);
      } catch (error) {
        console.error(`Error initializing Cytoscape for ${format}:`, error);
        setError(`Failed to initialize graph for ${format}: ${error.message}`);
      }
    };

    // Retry initialization if container height is zero
    const attemptInitialization = () => {
      if (containerRef.current.offsetHeight === 0) {
        console.log('Container height is zero, retrying in 100ms');
        setTimeout(attemptInitialization, 100);
      } else {
        initializeCytoscape();
      }
    };

    // Start initialization
    const timeout = setTimeout(attemptInitialization, 100);

    // Resize observer to handle dynamic container changes
    const resizeObserver = new ResizeObserver((entries) => {
      if (cyRef.current && entries[0].contentRect.height > 0) {
        console.log('Container resized:', entries[0].contentRect);
        cyRef.current.resize();
        cyRef.current.fit();
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      clearTimeout(timeout);
      resizeObserver.disconnect();
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [normalizedData, format]);

  const resetZoom = () => {
    if (cyRef.current) {
      cyRef.current.animate({
        fit: { padding: 60 },
        duration: 300,
      });
    }
  };

  const zoomIn = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() * 1.2);
    }
  };

  const zoomOut = () => {
    if (cyRef.current) {
      cyRef.current.zoom(cyRef.current.zoom() / 1.2);
    }
  };

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
        <div ref={containerRef} className="dependency-graph"></div>
      </div>
      <div className="graph-legend">
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#2ECC71' }}></div>
          <div className="legend-label">Root Component</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#6FB1FC' }}></div>
          <div className="legend-label">No Vulnerabilities</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#FFCCCC' }}></div>
          <div className="legend-label">Low Vulnerabilities</div>
        </div>
        <div className="legend-item">
          <div className="legend-color" style={{ backgroundColor: '#8B0000' }}></div>
          <div className="legend-label">High Vulnerabilities</div>
        </div>
      </div>
    </div>
  );
};

// Function to convert normalized SBOM data to Cytoscape elements
const convertSbomToGraphElements = (sbomData) => {
  const elements = [];
  const processedNodes = new Set();

  if (!sbomData?.name || !Array.isArray(sbomData.versions)) {
    console.error(`Invalid SBOM data structure for ${sbomData?.format || 'unknown'}:`, sbomData);
    return elements;
  }

  // Sort versions to select the latest as the root (assuming version_id is comparable, e.g., "1.1.1" > "1.0.0")
  const sortedVersions = [...sbomData.versions].sort((a, b) => {
    return b.version_id.localeCompare(a.version_id, undefined, { numeric: true });
  });

  // Assign root class only to the latest version
  sortedVersions.forEach((version, index) => {
    const nodeId = `${sbomData.name}-${version.version_id}`;
    const isRoot = index === 0; // Only the first (latest) version is root
    elements.push({
      data: {
        id: nodeId,
        label: `${sbomData.name}\n${version.version_id}`,
        hasVulnerabilities: version.vulnerabilities && version.vulnerabilities.length > 0,
        vulnerabilities: version.vulnerabilities || [],
      },
      classes: `${isRoot ? 'root' : ''} ${version.vulnerabilities && version.vulnerabilities.length > 0 ? 'vulnerable' : ''}`.trim(),
    });
    processedNodes.add(nodeId);

    if (version.dependencies) {
      processVersion(version, nodeId, elements, processedNodes);
    }
  });

  console.log('Generated graph elements:', JSON.stringify(elements, null, 2));
  return elements;
};

const processVersion = (version, parentId, elements, processedNodes) => {
  if (!version.dependencies) return;

  for (const dependency of version.dependencies) {
    const nodeId = `${dependency.name}-${dependency.version_id}`;
    if (!processedNodes.has(nodeId)) {
      elements.push({
        data: {
          id: nodeId,
          label: `${dependency.name}\n${dependency.version_id}`,
          hasVulnerabilities: dependency.vulnerabilities && dependency.vulnerabilities.length > 0,
          vulnerabilities: dependency.vulnerabilities || [],
        },
        classes: dependency.vulnerabilities && dependency.vulnerabilities.length > 0 ? 'vulnerable' : '',
      });
      processedNodes.add(nodeId);

      if (dependency.dependencies) {
        processVersion(dependency, nodeId, elements, processedNodes);
      }
    }

    const edgeId = `${parentId}-${nodeId}`;
    elements.push({
      data: {
        id: edgeId,
        source: parentId,
        target: nodeId,
      },
    });
  }
};

export default DependencyGraph;