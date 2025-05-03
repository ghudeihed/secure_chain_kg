import React, { useState } from 'react';
import './IndentedTreeView.css';

const IndentedTreeView = ({ data, format }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());

  const toggleNode = (nodeId) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      newSet.has(nodeId) ? newSet.delete(nodeId) : newSet.add(nodeId);
      return newSet;
    });
  };

  const renderNode = (node, version, level = 0, isRoot = false) => {
    const nodeId = `${node.name}-${version.version_id}`;
    const isExpanded = expandedNodes.has(nodeId);
    const { dependencies = [], vulnerabilities = [] } = version;
    const hasChildren = dependencies.length > 0;
    const hasVulnerabilities = vulnerabilities.length > 0;

    return (
      <div key={nodeId} className="tree-node" style={{ paddingLeft: `${level * 20}px` }}>
        <div
          className={`node-label ${isRoot ? 'root' : ''} ${hasVulnerabilities ? 'vulnerable' : ''}`}
          onClick={() => hasChildren && toggleNode(nodeId)}
        >
          <span className={`toggle-icon ${hasChildren ? (isExpanded ? 'expanded' : 'collapsed') : 'leaf'}`}>
            {hasChildren ? (isExpanded ? '▼' : '▶') : '•'}
          </span>
          <span className="node-name">
            {node.name} ({version.version_id})
          </span>
          {hasVulnerabilities && (
            <span className="vulnerability-count">
              ({vulnerabilities.length} vulnerabilities)
            </span>
          )}
        </div>

        {isExpanded && hasChildren && (
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
          <ul className="vulnerability-list">
            {vulnerabilities.map((vuln) => (
              <li key={vuln.id}>
                {vuln.id}
                {vuln.uri && (
                  <a href={vuln.uri} target="_blank" rel="noopener noreferrer">
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
    </div>
  );
};

export default IndentedTreeView;