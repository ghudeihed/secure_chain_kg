import React, { useState } from 'react';
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

  const generateSBOM = async () => {
    console.log('Submitting:', { softwareName });
    setLoading(true);
    setErrors({ json: null, spdx: null, cyclonedx: null });
    setSbomData({ json: null, spdx: null, cyclonedx: null });
    setDownloadUrls({ json: null, spdx: null, cyclonedx: null });

    if (!softwareName) {
      setErrors({
        json: 'Please enter a software name.',
        spdx: 'Please enter a software name.',
        cyclonedx: 'Please enter a software name.',
      });
      setLoading(false);
      return;
    }

    const formats = ['json', 'spdx', 'cyclonedx'];
    const requests = formats.map((fmt) =>
      axios.post(
        `${API_BASE_URL}/api/sbom/generate`,
        qs.stringify({
          software_name: softwareName,
          format: fmt,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      ).catch((err) => ({ error: err, format: fmt }))
    );

    try {
      const responses = await Promise.all(requests);
      const newSbomData = { json: null, spdx: null, cyclonedx: null };
      const newDownloadUrls = { json: null, spdx: null, cyclonedx: null };
      const newErrors = { json: null, spdx: null, cyclonedx: null };

      responses.forEach((response, index) => {
        const fmt = formats[index];
        if (response.error) {
          console.error(`Error generating SBOM for ${fmt}:`, response.error);
          let errorMessage = `Error generating ${fmt} SBOM`;
          if (response.error.response?.data?.detail) {
            if (Array.isArray(response.error.response.data.detail)) {
              errorMessage = response.error.response.data.detail
                .map((e) => `Missing required field: ${e.loc.join('.')}`)
                .join('; ');
            } else {
              errorMessage = response.error.response.data.detail;
            }
          }
          newErrors[fmt] = errorMessage;
        } else {
          console.log(`Raw API Response for ${fmt}:`, JSON.stringify(response.data, null, 2));
          newSbomData[fmt] = response.data;

          const fileExtension = fmt === 'json' ? 'json' : fmt === 'spdx' ? 'spdx.json' : 'cyclonedx.json';
          const blobData = JSON.stringify(response.data, null, 2);
          const jsonBlob = new Blob([blobData], { type: 'application/json' });
          const url = URL.createObjectURL(jsonBlob);
          newDownloadUrls[fmt] = url;
        }
      });

      setSbomData(newSbomData);
      setDownloadUrls(newDownloadUrls);
      setErrors(newErrors);
    } catch (err) {
      console.error('Unexpected error during SBOM generation:', err);
      setErrors({
        json: 'Unexpected error generating JSON SBOM',
        spdx: 'Unexpected error generating SPDX SBOM',
        cyclonedx: 'Unexpected error generating CycloneDX SBOM',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    generateSBOM();
  };

  return (
    <div className="sbom-generator">
      <header className="app-header">
        <h1>SBOM Construction Tool</h1>
        <p>Generate Software Bill of Materials from the Secure Chain Knowledge Graph</p>
      </header>
      <div className="main-content">
        <div className="form-container">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="software-name">Software Name:</label>
              <input
                id="software-name"
                type="text"
                value={softwareName}
                onChange={(e) => {
                  console.log('Software Name:', e.target.value);
                  setSoftwareName(e.target.value);
                }}
                placeholder="Enter software name (e.g., libxml2)"
                required
              />
            </div>
            {/* <div className="form-group">
              <label htmlFor="format">Display Format:</label>
              <select
                id="format"
                value={format}
                onChange={(e) => {
                  console.log('Format:', e.target.value);
                  setFormat(e.target.value);
                }}
              >
                <option value="json">JSON</option>
                <option value="spdx">SPDX</option>
                <option value="cyclonedx">CycloneDX</option>
              </select>
            </div> */}
            <button
              type="submit"
              className="generate-button"
              disabled={!softwareName || loading}
            >
              {loading ? 'Generating...' : 'Generate SBOMs'}
            </button>
          </form>
        </div>
        {Object.values(errors).some((err) => err) && (
          <div className="error-message">
            <h2>Error</h2>
            {errors.json && <p>JSON: {errors.json}</p>}
            {errors.spdx && <p>SPDX: {errors.spdx}</p>}
            {errors.cyclonedx && <p>CycloneDX: {errors.cyclonedx}</p>}
          </div>
        )}
        {Object.values(sbomData).some((data) => data) && (
          <div className="results-container">
            <h2>Results for {sbomData[format]?.name || softwareName}</h2>
            <div className="result-actions">
              {downloadUrls.json && (
                <a
                  href={downloadUrls.json}
                  download={`sbom-${sbomData.json?.name || softwareName}-json.json`}
                  className="download-button json-download"
                >
                  Download JSON
                </a>
              )}
              {downloadUrls.spdx && (
                <a
                  href={downloadUrls.spdx}
                  download={`sbom-${sbomData.spdx?.name || softwareName}-spdx.json`}
                  className="download-button spdx-download"
                >
                  Download SPDX
                </a>
              )}
              {downloadUrls.cyclonedx && (
                <a
                  href={downloadUrls.cyclonedx}
                  download={`sbom-${sbomData.cyclonedx?.name || softwareName}-cyclonedx.json`}
                  className="download-button cyclonedx-download"
                >
                  Download CycloneDX
                </a>
              )}
              <button
                className="toggle-view-button"
                onClick={() => setViewMode(viewMode === 'graph' ? 'tree' : 'graph')}
              >
                Switch to {viewMode === 'graph' ? 'Indented Tree' : 'Graph'} View
              </button>
            </div>
            <div className="visualization-container">
              <div className="visualization-panel">
                <h3>{viewMode === 'graph' ? 'Dependency Graph' : 'Indented Tree View'}</h3>
                {sbomData[format] ? (
                  viewMode === 'graph' ? (
                    <>
                      <DependencyGraph data={sbomData[format]} format={format} />
                      <p className="visualization-help">* Red nodes indicate components with vulnerabilities</p>
                    </>
                  ) : (
                    <IndentedTreeView data={sbomData[format]} format={format} />
                  )
                ) : (
                  <p>No data available for {format} format</p>
                )}
              </div>
            </div>
            {/* <div className="data-container">
              <h3>SBOM Data ({format})</h3>
              {sbomData[format] ? (
                <pre className="sbom-json">{JSON.stringify(sbomData[format], null, 2)}</pre>
              ) : (
                <p>No data available for {format} format</p>
              )}
            </div> */}
          </div>
        )}
      </div>
    </div>
  );
};

export default SBOMGenerator;