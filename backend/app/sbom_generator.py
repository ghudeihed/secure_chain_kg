import logging
import uuid
import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryTemplates:
    """Container for SPARQL query templates."""
    software_version: str = """
        SELECT ?version_id
        WHERE {
          ?software <http://schema.org/name> "%(software_name)s" .
          ?software <https://w3id.org/secure-chain/hasSoftwareVersion> ?version .
          ?version <https://w3id.org/secure-chain/versionName> ?version_id .
        }
    """
    
    dependency: str = """
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
    
    vulnerability: str = """
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
    
    def __init__(self, sparql_client, max_depth: int = 10):
        """Initialize SBOM generator with SPARQL client and configuration."""
        self.client = sparql_client
        self.max_depth = max_depth
        self.queries = QueryTemplates()
        self.visited: Set[str] = set()
        
    def generate_sbom(self, software_name: str) -> Dict[str, Any]:
        """Generate SBOM for a software component."""
        logger.info(f"Generating SBOM for software: {software_name}")
        
        try:
            sbom = {
                "id": str(uuid.uuid4()),
                "name": software_name,
                "versions": self._get_software_versions(software_name),
                "generated_at": self._get_timestamp(),
                "tool": {
                    "name": "Secure-Chain SBOM Generator",
                    "version": "1.0.0"
                }
            }
            
            for version in sbom["versions"]:
                version["dependencies"] = self._get_dependencies(
                    software_name, 
                    version["version_id"]
                )
                version["vulnerabilities"] = self._get_vulnerabilities(
                    software_name, 
                    version["version_id"]
                )
                
            return sbom
            
        except Exception as e:
            logger.error(f"Failed to generate SBOM for {software_name}: {str(e)}")
            raise SbomGenerationError(f"SBOM generation failed: {str(e)}") from e
    
    def _get_software_versions(self, software_name: str) -> List[Dict[str, str]]:
        """Retrieve all versions for a software component."""
        logger.debug(f"Getting versions for software: {software_name}")
        
        result = self.client.query(
            self.queries.software_version,
            {"software_name": software_name}
        )
        
        versions = [
            {"version_id": binding["version_id"]["value"]}
            for binding in result["results"]["bindings"]
        ]
        
        logger.debug(f"Found {len(versions)} versions for software: {software_name}")
        return versions
    
    def _get_dependencies(self, software_name: str, version_id: str, depth: int = 0) -> List[Dict[str, Any]]:
        """Recursively get dependencies for a software version."""
        if depth > self.max_depth:
            logger.warning(f"Maximum dependency depth reached for {software_name} {version_id}")
            return []
            
        dep_key = f"{software_name}:{version_id}"
        if dep_key in self.visited:
            logger.debug(f"Circular dependency detected: {dep_key}")
            return []
            
        self.visited.add(dep_key)
        logger.debug(f"Getting dependencies for {software_name} {version_id} (depth: {depth})")
        
        try:
            result = self.client.query(
                self.queries.dependency,
                {"software_name": software_name, "version_id": version_id}
            )
            
            dependencies = []
            for binding in result["results"]["bindings"]:
                dep_uri = binding["dependency"]["value"]
                dep_name = dep_uri.split("/")[-1]
                dep_version = binding["depVersionName"]["value"]
                
                sub_dep_key = f"{dep_name}:{dep_version}"
                if sub_dep_key in self.visited:
                    continue
                    
                dependency = {
                    "name": dep_name,
                    "version_id": dep_version,
                    "dependencies": self._get_dependencies(dep_name, dep_version, depth + 1),
                    "vulnerabilities": self._get_vulnerabilities(dep_name, dep_version)
                }
                
                dependencies.append(dependency)
                
            return dependencies
            
        finally:
            self.visited.remove(dep_key)
    
    def _get_vulnerabilities(self, software_name: str, version_id: str) -> List[Dict[str, str]]:
        """Retrieve vulnerabilities for a software version."""
        logger.debug(f"Getting vulnerabilities for {software_name} {version_id}")
        
        result = self.client.query(
            self.queries.vulnerability,
            {"software_name": software_name, "version_id": version_id}
        )
        
        vulnerabilities = []
        for binding in result["results"]["bindings"]:
            vulnerability = {
                "id": binding["vulnId"]["value"],
                "uri": binding["vulnerability"]["value"]
            }
            
            if "vulnType" in binding:
                vuln_type_uri = binding["vulnType"]["value"]
                vulnerability["type"] = vuln_type_uri.split("/")[-1]
                
            vulnerabilities.append(vulnerability)
            
        return vulnerabilities
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.datetime.now().isoformat()

class SbomGenerationError(Exception):
    """Custom exception for SBOM generation errors."""
    pass