import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import axios from 'axios';
import qs from 'qs';
import DependencyGraph from './DependencyGraph';
import IndentedTreeView from './IndentedTreeView';
import './SBOMGenerator.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const SBOMGenerator = () => {
  const [softwareName, setSoftwareName] = useState('');
  const [format, setFormat] = useState('json');
  const [sbomData, setSbomData] = useState({ json: null, spdx: null, cyclonedx: null });
  const [downloadUrls, setDownloadUrls] = useState({ json: null, spdx: null, cyclonedx: null });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({ json: null, spdx: null, cyclonedx: null });
  const [viewMode, setViewMode] = useState('graph');
  const [focusNodeId, setFocusNodeId] = useState(null);
  const [viewTransitioning, setViewTransitioning] = useState(false);
  const graphRef = useRef(null);

  useEffect(() => {
    return () => {
      Object.values(downloadUrls).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [downloadUrls]);

  const generateSBOM = async () => {
    if (!softwareName) {
      setErrors({
        json: 'Software name is required.',
        spdx: 'Software name is required.',
        cyclonedx: 'Software name is required.',
      });
      return;
    }

    setLoading(true);
    setErrors({ json: null, spdx: null, cyclonedx: null });
    setSbomData({ json: null, spdx: null, cyclonedx: null });
    setDownloadUrls((prev) => {
      Object.values(prev).forEach((url) => url && URL.revokeObjectURL(url));
      return { json: null, spdx: null, cyclonedx: null };
    });
    setFocusNodeId(null);

    const formats = ['json', 'spdx', 'cyclonedx'];
    const requests = formats.map((fmt) =>
      axios
        .post(
          `${API_BASE_URL}/api/sbom/generate`,
          qs.stringify({ software_name: softwareName, format: fmt }),
          { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
        )
        .catch((err) => ({ error: err, format: fmt }))
    );

    try {
      const responses = await Promise.all(requests);
      const newSbomData = {};
      const newDownloadUrls = {};
      const newErrors = {};

      responses.forEach((response, index) => {
        const fmt = formats[index];
        if (response.error) {
          let errorMessage = `Failed to generate ${fmt.toUpperCase()} SBOM`;
          if (response.error.response?.data?.detail) {
            errorMessage = Array.isArray(response.error.response.data.detail)
              ? response.error.response.data.detail
                  .map((e) => `Missing: ${e.loc.join('.')}`)
                  .join('; ')
              : response.error.response.data.detail;
          }
          newErrors[fmt] = errorMessage;
        } else {
          newSbomData[fmt] = response.data;
          const fileExtension = fmt === 'json' ? 'json' : `${fmt}.json`;
          const blob = new Blob([JSON.stringify(response.data, null, 2)], {
            type: 'application/json',
          });
          newDownloadUrls[fmt] = URL.createObjectURL(blob);
        }
      });

      setSbomData(newSbomData);
      setDownloadUrls(newDownloadUrls);
      setErrors(newErrors);
    } catch (err) {
      const errorMessage = 'Unexpected error generating SBOMs';
      setErrors({
        json: errorMessage,
        spdx: errorMessage,
        cyclonedx: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    generateSBOM();
  };

  const handleNodeClick = (nodeId) => {
    if (viewTransitioning) {
      return;
    }
    
    console.log(`Tree node clicked: ${nodeId}`);
    
    if (viewMode === 'graph') {
      setFocusNodeId(nodeId);
      return;
    }

    setViewTransitioning(true);
    setViewMode('graph');
    setTimeout(() => {
      setFocusNodeId(nodeId);
      setViewTransitioning(false);
    }, 300);
  };

  const renderErrors = () => {
    const activeErrors = Object.entries(errors).filter(([, err]) => err);
    if (!activeErrors.length) return null;

    return (
      <div className="error-message" role="alert">
        <h2>Error</h2>
        {activeErrors.map(([fmt, err]) => (
          <p key={fmt}>{fmt.toUpperCase()}: {err}</p>
        ))}
      </div>
    );
  };

  const renderResults = () => {
    if (!Object.values(sbomData).some((data) => data)) return null;

    return (
      <div className="results-container">
        <h2>Results for {sbomData[format]?.name || softwareName}</h2>
        <div className="result-actions">
          {Object.entries(downloadUrls).map(([fmt, url]) =>
            url ? (
              <a
                key={fmt}
                href={url}
                download={`sbom-${sbomData[fmt]?.name || softwareName}-${fmt}.json`}
                className={`download-button ${fmt}-download`}
              >
                Download {fmt.toUpperCase()}
              </a>
            ) : null
          )}
          <button
            className="toggle-view-button"
            onClick={() => {
              if (viewTransitioning) return;
              
              setViewTransitioning(true);
              if (viewMode === 'graph') {
                setFocusNodeId(null);
              }
              setViewMode(viewMode === 'graph' ? 'tree' : 'graph');
              setTimeout(() => {
                setViewTransitioning(false);
              }, 300);
            }}
            disabled={viewTransitioning}
            aria-label={`Switch to ${viewMode === 'graph' ? 'Tree' : 'Graph'} view`}
          >
            Switch to {viewMode === 'graph' ? 'Tree' : 'Graph'} View
          </button>
        </div>
        <div className="visualization-container">
          <div className="visualization-panel">
            <h3>{viewMode === 'graph' ? 'Dependency Graph' : 'Tree View'}</h3>
            {sbomData[format] ? (
              viewMode === 'graph' ? (
                <>
                  <DependencyGraph 
                    data={sbomData[format]} 
                    format={format} 
                    focusNodeId={focusNodeId}
                    ref={graphRef}
                  />
                  <p className="visualization-help">
                    * Red nodes indicate components with vulnerabilities
                    {focusNodeId && " • Click 'Clear Focus' to reset view"}
                  </p>
                </>
              ) : (
                <>
                  <IndentedTreeView 
                    data={sbomData[format]} 
                    format={format} 
                    onNodeClick={handleNodeClick}
                  />
                  <p className="visualization-help">
                    * Click on any component to see it in the graph view
                  </p>
                </>
              )
            ) : (
              <p>No data available for {format.toUpperCase()} format</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.innerHTML = `
      .visualization-panel {
        border: none !important;
      }
      .dependency-graph-container {
        border: none !important;
      }
      .dependency-graph {
        border: none !important;
      }
      
      /* Define a subtle animation for the focus transition */
      @keyframes fadeIn {
        from { opacity: 0.7; }
        to { opacity: 1; }
      }
      
      .focus-info {
        animation: fadeIn 0.5s ease-in-out;
      }
    `;
    document.head.appendChild(styleEl);
    
    return () => {
      document.head.removeChild(styleEl);
    };
  }, []);

  return (
    <div className="sbom-generator">
      <header className="app-header">
        <h1>SBOM Construction Tool</h1>
        <p>Generate Software Bill of Materials</p>
      </header>
      <div className="main-content">
        <div className="form-container">
          <form onSubmit={handleSubmit} aria-labelledby="form-title">
            <h2 id="form-title" className="visually-hidden">
              SBOM Generation Form
            </h2>
            <div className="form-group">
              <label htmlFor="software-name">Software Name:</label>
              <input
                id="software-name"
                type="text"
                value={softwareName}
                onChange={(e) => setSoftwareName(e.target.value)}
                placeholder="e.g., libxml2"
                required
                aria-required="true"
              />
            </div>
            <button
              type="submit"
              className="generate-button"
              disabled={loading || !softwareName}
              aria-busy={loading}
            >
              {loading ? 'Generating...' : 'Generate SBOMs'}
            </button>
          </form>
        </div>
        {renderErrors()}
        {renderResults()}
      </div>
    </div>
  );
};

SBOMGenerator.propTypes = {
  softwareName: PropTypes.string,
  format: PropTypes.oneOf(['json', 'spdx', 'cyclonedx']),
  sbomData: PropTypes.shape({
    json: PropTypes.object,
    spdx: PropTypes.object,
    cyclonedx: PropTypes.object,
  }),
  downloadUrls: PropTypes.shape({
    json: PropTypes.string,
    spdx: PropTypes.string,
    cyclonedx: PropTypes.string,
  }),
  errors: PropTypes.shape({
    json: PropTypes.string,
    spdx: PropTypes.string,
    cyclonedx: PropTypes.string,
  }),
  viewMode: PropTypes.oneOf(['graph', 'tree']),
  focusNodeId: PropTypes.string,
  viewTransitioning: PropTypes.bool,
};

export default SBOMGenerator;