import React, { useState } from 'react';
import './IndentedTreeView.css';

const IndentedTreeView = ({ data, format }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  // Toggle node expansion state
  const toggleNode = (nodeId) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Render a single node and its children recursively
  const renderNode = (node, version, level = 0, isRoot = false) => {
    const nodeId = `${node.name}-${version.version_id}`;
    const isExpanded = expandedNodes.has(nodeId);
    const vulnerabilities = version.vulnerabilities || [];
    const hasVulnerabilities = vulnerabilities.length > 0;
    const dependencies = version.dependencies || [];

    return (
      <div key={nodeId} className="tree-node" style={{ paddingLeft: `${level * 20}px` }}>
        <div
          className={`node-label ${hasVulnerabilities ? 'vulnerable' : ''} ${isRoot ? 'root' : ''}`}
          onClick={() => toggleNode(nodeId)}
        >
          <span className={`toggle-icon ${isExpanded ? 'expanded' : 'collapsed'}`}>
            {dependencies.length > 0 ? (isExpanded ? '▼' : '▶') : '•'}
          </span>
          <span className="node-name">{node.name} ({version.version_id})</span>
          {hasVulnerabilities && (
            <span className="vulnerability-count">({vulnerabilities.length} vulnerabilities)</span>
          )}
        </div>
        {isExpanded && dependencies.length > 0 && (
          <div className="node-children">
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
          <div className="vulnerability-list">
            <ul>
              {vulnerabilities.map((vuln) => (
                <li key={vuln.id}>
                  {vuln.id} {vuln.uri && <a href={vuln.uri} target="_blank" rel="noopener noreferrer">(Link)</a>}
                </li>
              ))}
            </ul>
          </div>
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
    </div>
  );
};

export default IndentedTreeView;