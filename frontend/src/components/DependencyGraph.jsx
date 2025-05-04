import React, { useEffect, useRef, useMemo, useState, forwardRef, useImperativeHandle } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import * as d3 from 'd3';
import { parseSbomData } from '../utils/sbomParser';
import './DependencyGraph.css';

cytoscape.use(dagre);

const DependencyGraph = forwardRef(({ data, format, focusNodeId }, ref) => {
  const containerRef = useRef(null);
  const cyRef = useRef(null);
  const [warning, setWarning] = useState(null);
  const [error, setError] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [currentFocusedNode, setCurrentFocusedNode] = useState(null);
  const animationInProgressRef = useRef(false);
  const layoutFinishedRef = useRef(false);

  useImperativeHandle(ref, () => ({
    zoomToNode: (nodeId) => {
      if (cyRef.current && nodeId) {
        const node = cyRef.current.getElementById(nodeId);
        if (node.length > 0) {
          focusOnNode(node);
        }
      }
    },
    resetFocus: () => {
      if (cyRef.current) {
        resetNodeHighlighting();
        resetView();
      }
    }
  }));

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

  const focusOnNode = (node) => {
    if (animationInProgressRef.current || !layoutFinishedRef.current) {
      console.log("Animation in progress or layout not finished, deferring focus");
      
      if (!layoutFinishedRef.current) {
        setTimeout(() => focusOnNode(node), 500);
      }
      return;
    }
    
    console.log(`Focusing on node: ${node.id()}`);
    animationInProgressRef.current = true;
    
    resetNodeHighlighting();
    setCurrentFocusedNode(node.id());

    node.addClass('highlighted');
    const connectedEdges = node.connectedEdges();
    connectedEdges.addClass('highlighted-edge');
    cyRef.current.fit(undefined, 50);
    
    setTimeout(() => {
      cyRef.current.animation({
        center: {
          eles: node
        },
        zoom: 1.5,
        duration: 400,
        easing: 'ease-out'
      })
      .play()
      .promise('complete')
      .then(() => {
        node.addClass('focus-pulse');
        setTimeout(() => {
          animationInProgressRef.current = false;
          console.log("Focus animation completed");
        }, 300);
      });
    }, 300);
  };

  const resetNodeHighlighting = () => {
    if (cyRef.current) {
      cyRef.current.elements().removeClass('highlighted highlighted-edge focus-pulse');
      setCurrentFocusedNode(null);
    }
  };

  const resetView = () => {
    if (cyRef.current && !animationInProgressRef.current) {
      animationInProgressRef.current = true;
      cyRef.current.animation({
        fit: { padding: 50 },
        duration: 300
      })
      .play()
      .promise('complete')
      .then(() => {
        animationInProgressRef.current = false;
      });
    }
  };

  const applyBetterLayout = () => {
    if (!cyRef.current) return;
    
    console.log("Applying optimized layout strategy");
    
    cyRef.current.layout({
      name: 'grid',
      padding: 30,
      avoidOverlap: true,
      spacingFactor: 1.5,
      animate: false
    }).run();
    
    setTimeout(() => {
      const elementCount = cyRef.current.elements().length;

      let finalLayoutName;
      let layoutOptions = {
        animate: true,
        animationDuration: 800,
        padding: 50,
        fit: true,
        stop: function() {
          console.log("Final layout finished");
          layoutFinishedRef.current = true;
          setIsInitialized(true);
        }
      };
      
      if (elementCount > 100) {
        finalLayoutName = 'cose';
        layoutOptions = {
          ...layoutOptions,
          name: finalLayoutName,
          nodeOverlap: 40,
          idealEdgeLength: 150,
          edgeElasticity: 100,
          nestingFactor: 1.5, 
          gravity: 80,             // Stronger gravity keeps components together
          numIter: 3000,           // More iterations for better layout
          initialTemp: 200,        // Higher temperature allows more movement
          coolingFactor: 0.95,     // Slower cooling for better optimization
          randomize: true,         // Start with random positions for better results
        };
      } 
      else if (elementCount > 50) {
        finalLayoutName = 'cose';
        layoutOptions = {
          ...layoutOptions,
          name: finalLayoutName,
          nodeOverlap: 30,
          idealEdgeLength: 100,
          edgeElasticity: 80,
          nestingFactor: 1.2,
          gravity: 50,
          numIter: 2000,
          initialTemp: 150,
          coolingFactor: 0.95,
          randomize: true,
        };
      }
      else {
        finalLayoutName = 'dagre';
        layoutOptions = {
          ...layoutOptions,
          name: finalLayoutName,
          rankDir: 'LR',          // Left to right layout
          rankSep: 200,           // Large vertical separation between ranks
          nodeSep: 150,           // Large horizontal separation between nodes
          edgeSep: 80,            // Edge separation
          ranker: 'longest-path', // Use longest-path for better hierarchies
        };
      }
      
      console.log(`Applying ${finalLayoutName} layout with optimized parameters`);
      
      cyRef.current.layout(layoutOptions).run();
    }, 200);
  };

  useEffect(() => {
    if (!normalizedData || !containerRef.current) {
      setError(normalizedData ? 'No container available' : `Invalid ${format} data`);
      return;
    }

    layoutFinishedRef.current = false;
    animationInProgressRef.current = false;
    
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
          'transition-property': 'background-color, border-color, border-width, width, height',
          'transition-duration': '0.3s',
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
          'transition-property': 'line-color, width, opacity',
          'transition-duration': '0.3s',
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
      {
        selector: 'node.highlighted',
        style: {
          'border-color': '#E74C3C',
          'border-width': 5,
          'border-style': 'solid',
          'background-color': ele => {
            const color = ele.style('background-color');
            return d3.color(color).brighter(0.5).toString();
          },
          'z-index': 999,
          'overlay-opacity': 0,
          'shadow-blur': 15,
          'shadow-color': '#E74C3C',
          'shadow-opacity': 0.8,
          'shadow-offset-x': 0,
          'shadow-offset-y': 0,
        },
      },
      {
        selector: 'node.focus-pulse',
        style: {
          'width': ele => {
            const currentWidth = ele.style('width');
            return parseFloat(currentWidth) * 1.2;
          },
          'height': ele => {
            const currentHeight = ele.style('height');
            return parseFloat(currentHeight) * 1.2;
          },
          'font-size': '16px',
          'font-weight': 'bold',
          'text-background-opacity': 0.7,
          'text-background-color': '#fff',
          'text-background-shape': 'roundrectangle',
          'text-background-padding': '3px',
        },
      },
      {
        selector: 'edge.highlighted-edge',
        style: {
          'width': 3.5,
          'line-color': '#E74C3C',
          'target-arrow-color': '#E74C3C',
          'source-arrow-color': '#E74C3C',
          'line-style': 'solid',
          'opacity': 1,
          'z-index': 900,
        },
      },
    ];

    const initCytoscape = () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements: elements.map(el => {
          if (!el.data.source) {
            return {
              ...el,
              position: {
                x: Math.random() * containerRef.current.offsetWidth,
                y: Math.random() * containerRef.current.offsetHeight
              }
            };
          }
          return el;
        }),
        style: styles,
        zoom: 1,
        minZoom: 0.2,
        maxZoom: 3,
        wheelSensitivity: 0.2,
        pixelRatio: 'auto',
        
        autoungrabify: false,
        autounselectify: false,
        userZoomingEnabled: true,
        userPanningEnabled: true,
        boxSelectionEnabled: true,
      });

      cyRef.current.on('tap', 'node', function(evt) {
        if (!animationInProgressRef.current && layoutFinishedRef.current) {
          focusOnNode(evt.target);
        }
      });

      cyRef.current.on('mouseover', 'node', evt => showTooltip(evt.target));
      cyRef.current.on('mouseout', 'node', hideTooltips);

      applyBetterLayout();
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
        setTimeout(initCytoscape, 200);
      } else {
        initCytoscape();
      }
    }, 200);

    const resizeObserver = new ResizeObserver(() => {
      if (cyRef.current) {
        cyRef.current.resize();
        
        if (currentFocusedNode && !animationInProgressRef.current) {
          const node = cyRef.current.getElementById(currentFocusedNode);
          if (node.length > 0) {
            cyRef.current.center(node);
          }
        }
      }
    });
    
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      clearTimeout(timeout);
      resizeObserver.disconnect();
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [normalizedData, format]);

  useEffect(() => {
    if (cyRef.current && focusNodeId && isInitialized && layoutFinishedRef.current) {
      console.log("External focus request on node:", focusNodeId);
      const node = cyRef.current.getElementById(focusNodeId);
      
      if (node.length > 0) {
        console.log("Node found, focusing:", focusNodeId);
        setTimeout(() => {
          focusOnNode(node);
        }, 300);
      } else {
        console.log("Node not found:", focusNodeId);
        console.log("Available nodes:", cyRef.current.nodes().map(n => n.id()));
      }
    } else if (cyRef.current && !focusNodeId && isInitialized) {
      resetNodeHighlighting();
      resetView();
    }
  }, [focusNodeId, isInitialized]);

  const zoomIn = () => {
    if (cyRef.current && !animationInProgressRef.current) {
      cyRef.current.animation({
        zoom: cyRef.current.zoom() * 1.2,
        duration: 200
      }).play();
    }
  };
  
  const zoomOut = () => {
    if (cyRef.current && !animationInProgressRef.current) {
      cyRef.current.animation({
        zoom: cyRef.current.zoom() / 1.2,
        duration: 200
      }).play();
    }
  };

  return (
    <div className="dependency-graph-wrapper">
      <div className="dependency-graph-container">
        <div className="graph-controls">
          <button onClick={zoomIn} disabled={animationInProgressRef.current}>Zoom In</button>
          <button onClick={zoomOut} disabled={animationInProgressRef.current}>Zoom Out</button>
          <button onClick={resetView} disabled={animationInProgressRef.current}>Reset View</button>
          {currentFocusedNode && (
            <button 
              onClick={() => {
                if (!animationInProgressRef.current) {
                  resetNodeHighlighting();
                  resetView();
                }
              }}
              className="clear-focus-button"
              disabled={animationInProgressRef.current}
            >
              Clear Focus
            </button>
          )}
        </div>
        {warning && <div className="graph-warning">{warning}</div>}
        {error && <div className="graph-error">{error}</div>}
        {currentFocusedNode && (
          <div className="focus-info">
            Focused on: <strong>{currentFocusedNode}</strong>
          </div>
        )}
        <div ref={containerRef} className="dependency-graph" />
      </div>
      <GraphLegend />
    </div>
  );
});

const GraphLegend = () => (
  <div className="graph-legend">
    {[
      { color: '#2ECC71', label: 'Root Component' },
      { color: '#6FB1FC', label: 'No Vulnerabilities' },
      { color: '#FFCCCC', label: 'Low Vulnerabilities' },
      { color: '#8B0000', label: 'High Vulnerabilities' },
      { 
        color: 'transparent', 
        borderColor: '#E74C3C', 
        borderStyle: 'solid',
        boxShadow: '0 0 10px #E74C3C',
        label: 'Selected Node' 
      },
      { 
        isLine: true, 
        color: '#E74C3C', 
        lineWidth: '3px', 
        label: 'Connected Edges' 
      },
    ].map((item) => (
      <div className="legend-item" key={item.label}>
        {item.isLine ? (
          <div 
            className="legend-line" 
            style={{ 
              backgroundColor: item.color,
              height: item.lineWidth
            }} 
          />
        ) : (
          <div 
            className="legend-color" 
            style={{ 
              backgroundColor: item.color,
              borderColor: item.borderColor || 'transparent',
              borderWidth: item.borderColor ? '4px' : '0',
              borderStyle: item.borderStyle || 'solid',
              boxShadow: item.boxShadow || 'none'
            }} 
          />
        )}
        <div className="legend-label">{item.label}</div>
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