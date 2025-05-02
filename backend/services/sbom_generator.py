import logging
import uuid

logger = logging.getLogger(__name__)

# SPARQL query templates
SOFTWARE_VERSION_QUERY = """
SELECT ?version_id
WHERE {
  ?software <http://schema.org/name> "%(software_name)s" .
  ?software <https://w3id.org/secure-chain/hasSoftwareVersion> ?version .
  ?version <https://w3id.org/secure-chain/versionName> ?version_id .
}
"""

DEPENDENCY_QUERY = """
SELECT ?dependency ?dependencyVersion ?depVersionName
WHERE {
  ?software <http://schema.org/name> "%(software_name)s" .
  ?software <https://w3id.org/secure-chain/hasSoftwareVersion> ?version .
  ?version <https://w3id.org/secure-chain/versionName> "%(version_id)s" .
  ?version <https://w3id.org/secure-chain/dependsOn> ?depVersion .
  ?depVersion <https://w3id.org/secure-chain/versionName> ?depVersionName .
  ?dependency <https://w3id.org/secure-chain/hasSoftwareVersion> ?depVersion .
}
"""

VULNERABILITY_QUERY = """
SELECT ?vulnerability ?vulnId ?vulnType
WHERE {
  ?software <http://schema.org/name> "%(software_name)s" .
  ?software <https://w3id.org/secure-chain/hasSoftwareVersion> ?version .
  ?version <https://w3id.org/secure-chain/versionName> "%(version_id)s" .
  ?version <https://w3id.org/secure-chain/vulnerableTo> ?vulnerability .
  ?vulnerability <http://schema.org/identifier> ?vulnId .
  OPTIONAL { ?vulnerability <https://w3id.org/secure-chain/vulnerabilityType> ?vulnType . }
}
"""

class SbomGenerator:
    """Generator for Software Bill of Materials (SBOM) based on SPARQL queries."""
    
    def __init__(self, sparql_client):
        self.client = sparql_client
        self.visited = set()  # For circular dependency detection
        
    def generate_sbom(self, software_name):
        """Generate SBOM for a software component."""
        logger.info(f"Generating SBOM for software: {software_name}")
        
        # Create root SBOM structure
        sbom = {
            "name": software_name,
            "versions": self._get_software_versions(software_name),
            "generated_at": self._get_timestamp(),
            "tool": {
                "name": "Secure-Chain SBOM Generator",
                "version": "1.0.0"
            }
        }
        
        # Process each version
        for version in sbom["versions"]:
            # Get dependencies recursively
            dependencies = self._get_dependencies(software_name, version["version_id"])
            version["dependencies"] = dependencies
            
            # Get vulnerabilities for this version
            vulnerabilities = self._get_vulnerabilities(software_name, version["version_id"])
            version["vulnerabilities"] = vulnerabilities
            
        return sbom
    
    def _get_software_versions(self, software_name):
        """Get all versions for a software component."""
        logger.debug(f"Getting versions for software: {software_name}")
        
        query_result = self.client.query(SOFTWARE_VERSION_QUERY, {"software_name": software_name})
        versions = []
        
        for result in query_result["results"]["bindings"]:
            version_id = result["version_id"]["value"]
            versions.append({
                "version_id": version_id
            })
            
        logger.debug(f"Found {len(versions)} versions for software: {software_name}")
        return versions
    
    def _get_dependencies(self, software_name, version_id, depth=0, max_depth=10):
        """Get dependencies for a software version recursively."""
        # Prevent infinite recursion
        if depth > max_depth:
            logger.warning(f"Maximum dependency depth reached for {software_name} {version_id}")
            return []
            
        # Detect circular dependencies
        dep_key = f"{software_name}:{version_id}"
        if dep_key in self.visited:
            logger.debug(f"Circular dependency detected: {dep_key}")
            return []
            
        self.visited.add(dep_key)
        logger.debug(f"Getting dependencies for {software_name} {version_id} (depth: {depth})")
        
        # Query for dependencies
        dependencies = []
        query_result = self.client.query(DEPENDENCY_QUERY, {
            "software_name": software_name,
            "version_id": version_id
        })
        
        for result in query_result["results"]["bindings"]:
            dep_uri = result["dependency"]["value"]
            dep_name = dep_uri.split("/")[-1]  # Extract name from URI
            dep_version = result["depVersionName"]["value"]
            
            # Skip if already processed in this branch
            sub_dep_key = f"{dep_name}:{dep_version}"
            if sub_dep_key in self.visited:
                continue
                
            # Recursively get sub-dependencies
            sub_dependencies = self._get_dependencies(dep_name, dep_version, depth + 1, max_depth)
            
            dependency = {
                "name": dep_name,
                "version_id": dep_version,
                "dependencies": sub_dependencies,
                "vulnerabilities": self._get_vulnerabilities(dep_name, dep_version)
            }
            
            dependencies.append(dependency)
            
        # Remove from visited so other branches can include this dependency
        self.visited.remove(dep_key)
        
        return dependencies
    
    def _get_vulnerabilities(self, software_name, version_id):
        """Get vulnerabilities for a software version."""
        logger.debug(f"Getting vulnerabilities for {software_name} {version_id}")
        
        query_result = self.client.query(VULNERABILITY_QUERY, {
            "software_name": software_name,
            "version_id": version_id
        })
        
        vulnerabilities = []
        for result in query_result["results"]["bindings"]:
            vuln_uri = result["vulnerability"]["value"]
            vuln_id = result["vulnId"]["value"]
            
            vulnerability = {
                "id": vuln_id,
                "uri": vuln_uri
            }
            
            # Add vulnerability type if available
            if "vulnType" in result:
                vuln_type_uri = result["vulnType"]["value"]
                vuln_type = vuln_type_uri.split("/")[-1]  # Extract type from URI
                vulnerability["type"] = vuln_type
                
            vulnerabilities.append(vulnerability)
            
        return vulnerabilities
    
    def _get_timestamp(self):
        """Get current timestamp in ISO format."""
        import datetime
        return datetime.datetime.now().isoformat()