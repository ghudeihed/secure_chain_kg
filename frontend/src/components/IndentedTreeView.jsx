import React, { useState, useEffect } from 'react';
import './IndentedTreeView.css';

const IndentedTreeView = ({ data, format, onNodeClick }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [hoveredNode, setHoveredNode] = useState(null);

  const formatNodeId = (name, versionId) => `${name}-${versionId}`;

  useEffect(() => {
    if (data?.versions && data.versions.length > 0) {
      const rootVersion = data.versions[0];
      const rootNodeId = formatNodeId(data.name, rootVersion.version_id);
      setExpandedNodes(new Set([rootNodeId]));
    }
  }, [data]);

  const toggleNode = (nodeId, event) => {
    event.stopPropagation();
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      newSet.has(nodeId) ? newSet.delete(nodeId) : newSet.add(nodeId);
      return newSet;
    });
  };

  const handleNodeClick = (node, version, event) => {
    // Stop event propagation to prevent parent nodes from being clicked
    event.stopPropagation();
    
    if (onNodeClick) {
      const nodeId = formatNodeId(node.name, version.version_id);
      console.log(`Tree view clicked node: ${nodeId}`);
      onNodeClick(nodeId);
    }
  };

  const handleMouseEnter = (nodeId) => {
    setHoveredNode(nodeId);
  };

  const handleMouseLeave = () => {
    setHoveredNode(null);
  };

  const renderNode = (node, version, level = 0, isRoot = false) => {
    const nodeId = formatNodeId(node.name, version.version_id);
    const isExpanded = expandedNodes.has(nodeId);
    const isHovered = hoveredNode === nodeId;
    const { dependencies = [], vulnerabilities = [] } = version;
    const hasChildren = dependencies.length > 0;
    const hasVulnerabilities = vulnerabilities.length > 0;

    return (
      <div 
        key={nodeId} 
        className={`tree-node ${isHovered ? 'hovered' : ''}`} 
        style={{ paddingLeft: `${level * 20}px` }}
        // Pass the event object to handleNodeClick
        onClick={(e) => handleNodeClick(node, version, e)}
        onMouseEnter={() => handleMouseEnter(nodeId)}
        onMouseLeave={handleMouseLeave}
        data-node-id={nodeId}
      >
        <div
          className={`node-label ${isRoot ? 'root' : ''} ${hasVulnerabilities ? 'vulnerable' : ''}`}
        >
          <span 
            className={`toggle-icon ${hasChildren ? (isExpanded ? 'expanded' : 'collapsed') : 'leaf'}`}
            onClick={(e) => hasChildren && toggleNode(nodeId, e)}
            title={hasChildren ? (isExpanded ? "Collapse" : "Expand") : ""}
          >
            {hasChildren ? (isExpanded ? '▼' : '▶') : '•'}
          </span>
          <span className="node-name">
            {node.name} ({version.version_id})
          </span>
          {hasVulnerabilities && (
            <span className="vulnerability-count">
              {vulnerabilities.length} {vulnerabilities.length === 1 ? 'vulnerability' : 'vulnerabilities'}
            </span>
          )}
          <span className="view-in-graph-hint">
            Click to view in graph
          </span>
        </div>

        {isExpanded && hasChildren && (
          <div className="node-children" onClick={(e) => e.stopPropagation()}>
            {dependencies.map((dep) =>
              renderNode(dep, {
                version_id: dep.version_id,
                dependencies: dep.dependencies,
                vulnerabilities: dep.vulnerabilities,
              }, level + 1)
            )}
          </div>
        )}

        {isExpanded && hasVulnerabilities && (
          <ul className="vulnerability-list" onClick={(e) => e.stopPropagation()}>
            {vulnerabilities.map((vuln) => (
              <li key={vuln.id}>
                {vuln.id}
                {vuln.uri && (
                  <a 
                    href={vuln.uri} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    (Link)
                  </a>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  };

  if (!data?.name || !Array.isArray(data.versions)) {
    return <div className="tree-error">Invalid {format} data for indented view</div>;
  }

  // Sort versions to display the latest as root
  const sortedVersions = [...data.versions].sort((a, b) =>
    b.version_id.localeCompare(a.version_id, undefined, { numeric: true })
  );

  return (
    <div className="indented-tree-wrapper">
      {sortedVersions.map((version, index) =>
        renderNode({ name: data.name }, version, 0, index === 0)
      )}
      <div className="tree-helper">
        <span>▶ Click triangle icons to expand/collapse</span>
        <span>• Click on any component to view it in the graph</span>
      </div>
    </div>
  );
};

export default IndentedTreeView;