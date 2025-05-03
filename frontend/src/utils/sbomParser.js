export const parseSbomData = (data, format) => {
  try {
    switch (format.toLowerCase()) {
      case 'json':
      case 'spdx':
      case 'cyclonedx':
        return parseCustomJson(data);
      default:
        throw new Error(`Unsupported SBOM format: ${format}`);
    }
  } catch (error) {
    console.error(`Failed to parse ${format} SBOM:`, error);
    throw new Error(`Failed to parse ${format} SBOM: ${error.message}`);
  }
};

// Unified parser for all supported formats
const parseCustomJson = (data) => {
  if (!data || typeof data !== 'object' || !data.name || !Array.isArray(data.versions)) {
    throw new Error('Invalid SBOM format: missing required fields (name or versions)');
  }

  return {
    name: data.name,
    versions: data.versions.map((version) => ({
      version_id: version.version_id || 'unknown',
      dependencies: version.dependencies || [],
      vulnerabilities: version.vulnerabilities || [],
    })),
  };
};
