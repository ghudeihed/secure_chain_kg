// frontend/src/utils/sbomParser.js
export const parseSbomData = (data, format) => {
  console.log(`Parsing SBOM data for format: ${format}`, JSON.stringify(data, null, 2));
  try {
    switch (format.toLowerCase()) {
      case 'json':
        return parseCustomJson(data);
      case 'spdx':
        return parseSpdx(data);
      case 'cyclonedx':
        return parseCycloneDx(data);
      default:
        throw new Error(`Unsupported SBOM format: ${format}`);
    }
  } catch (error) {
    console.error(`Error parsing ${format} SBOM:`, error);
    throw new Error(`Failed to parse ${format} SBOM: ${error.message}`);
  }
};

// Custom JSON parser
const parseCustomJson = (data) => {
  if (!data || !data.name || !Array.isArray(data.versions)) {
    throw new Error('Invalid custom JSON format: missing name or versions');
  }
  console.log('Parsed JSON data:', data);
  return {
    name: data.name,
    versions: data.versions.map((version) => ({
      version_id: version.version_id || 'unknown',
      dependencies: version.dependencies || [],
      vulnerabilities: version.vulnerabilities || [],
    })),
  };
};

// SPDX JSON parser (based on SPDX 2.3 JSON schema)
const parseSpdx = (data) => {
  console.log('SPDX input data:', JSON.stringify(data, null, 2));
  if (!data) {
    throw new Error('Invalid SPDX JSON format: data is null or undefined');
  }

  return parseCustomJson(data); // Reuse custom JSON parser for SPDX
};

// CycloneDX JSON parser (based on CycloneDX 1.5 JSON schema)
const parseCycloneDx = (data) => {
  console.log('CycloneDX input data:', JSON.stringify(data, null, 2));
  if (!data) {
    throw new Error('Invalid CycloneDX JSON format: data is null or undefined');
  }
  
  return parseCustomJson(data); // Reuse custom JSON parser for CycloneDX
};