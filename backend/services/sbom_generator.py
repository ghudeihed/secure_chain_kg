import logging
import uuid
import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from services.sparql_client import SparqlClient, SparqlClientError
from config import settings

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
  ?dependency <http://schema.org/name> ?depName .
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

class Vulnerability(BaseModel):
    id: str
    uri: str
    type: Optional[str] = None

class Dependency(BaseModel):
    name: str
    version_id: str
    dependencies: List["Dependency"] = Field(default_factory=list)
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)

class Version(BaseModel):
    version_id: str
    dependencies: List[Dependency] = Field(default_factory=list)
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)

class Sbom(BaseModel):
    name: str
    versions: List[Version] = Field(default_factory=list)
    generated_at: str
    tool: Dict[str, str]

class SbomGenerator:
    """Generator for Software Bill of Materials (SBOM) based on SPARQL queries.

    Args:
        sparql_client (SparqlClient): SPARQL client for querying the knowledge graph.
        max_depth (int): Maximum recursion depth for dependencies (default: from config).
    """
    
    def __init__(self, sparql_client: SparqlClient, max_depth: int = settings.SBOM_MAX_DEPTH):
        self.client = sparql_client
        self.max_depth = max_depth
        self.visited: set[str] = set()  # For circular dependency detection
        
    def generate_sbom(self, software_name: str) -> Sbom:
        """Generate SBOM for a software component.

        Args:
            software_name (str): Name of the software component.

        Returns:
            Sbom: Pydantic model containing the SBOM structure.

        Raises:
            ValueError: If software_name is invalid.
            SparqlClientError: If SPARQL queries fail.
        """
        if not self._is_valid_software_name(software_name):
            raise ValueError(f"Invalid software name: {software_name}")
            
        logger.info(f"Generating SBOM for software: {software_name}")
        self.visited.clear()  # Reset visited set for new SBOM
        
        try:
            sbom = Sbom(
                name=software_name,
                versions=self._get_software_versions(software_name),
                generated_at=self._get_timestamp(),
                tool={
                    "name": settings.SBOM_TOOL_NAME,
                    "version": settings.SBOM_TOOL_VERSION
                }
            )
            
            for version in sbom.versions:
                version.dependencies = self._get_dependencies(software_name, version.version_id)
                version.vulnerabilities = self._get_vulnerabilities(software_name, version.version_id)
                
            return sbom
        except SparqlClientError as e:
            logger.error(f"Failed to generate SBOM: {e}")
            raise
    
    def _get_software_versions(self, software_name: str) -> List[Version]:
        """Get all versions for a software component.

        Args:
            software_name (str): Software name.

        Returns:
            List[Version]: List of version models.
        """
        logger.debug(f"Getting versions for software: {software_name}")
        
        try:
            query_result = self.client.query(SOFTWARE_VERSION_QUERY, {"software_name": software_name})
            versions = []
            
            for result in query_result["results"]["bindings"]:
                version_id = result.get("version_id", {}).get("value")
                if not version_id:
                    logger.warning(f"Missing version_id in result for {software_name}")
                    continue
                versions.append(Version(version_id=version_id))
                
            logger.debug(f"Found {len(versions)} versions for software: {software_name}")
            return versions
        except SparqlClientError as e:
            logger.error(f"Failed to get versions for {software_name}: {e}")
            raise
    
    def _get_dependencies(self, software_name: str, version_id: str, depth: int = 0) -> List[Dependency]:
        """Get dependencies for a software version recursively.

        Args:
            software_name (str): Software name.
            version_id (str): Version identifier.
            depth (int): Current recursion depth.

        Returns:
            List[Dependency]: List of dependency models.
        """
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
            dependencies = []
            query_result = self.client.query(DEPENDENCY_QUERY, {
                "software_name": software_name,
                "version_id": version_id
            })
            
            for result in query_result["results"]["bindings"]:
                dep_name = result.get("depName", {}).get("value")
                dep_version = result.get("depVersionName", {}).get("value")
                if not (dep_name and dep_version):
                    logger.warning(f"Missing depName or depVersionName in result for {software_name}")
                    continue
                    
                sub_dep_key = f"{dep_name}:{dep_version}"
                if sub_dep_key in self.visited:
                    continue
                    
                sub_dependencies = self._get_dependencies(dep_name, dep_version, depth + 1)
                dependencies.append(Dependency(
                    name=dep_name,
                    version_id=dep_version,
                    dependencies=sub_dependencies,
                    vulnerabilities=self._get_vulnerabilities(dep_name, dep_version)
                ))
                
            self.visited.remove(dep_key)
            return dependencies
        except SparqlClientError as e:
            logger.error(f"Failed to get dependencies for {software_name} {version_id}: {e}")
            raise
    
    def _get_vulnerabilities(self, software_name: str, version_id: str) -> List[Vulnerability]:
        """Get vulnerabilities for a software version.

        Args:
            software_name (str): Software name.
            version_id (str): Version identifier.

        Returns:
            List[Vulnerability]: List of vulnerability models.
        """
        logger.debug(f"Getting vulnerabilities for {software_name} {version_id}")
        
        try:
            query_result = self.client.query(VULNERABILITY_QUERY, {
                "software_name": software_name,
                "version_id": version_id
            })
            
            vulnerabilities = []
            for result in query_result["results"]["bindings"]:
                vuln_id = result.get("vulnId", {}).get("value")
                vuln_uri = result.get("vulnerability", {}).get("value")
                if not (vuln_id and vuln_uri):
                    logger.warning(f"Missing vulnId or vulnerability URI for {software_name} {version_id}")
                    continue
                    
                vulnerability = Vulnerability(id=vuln_id, uri=vuln_uri)
                if "vulnType" in result and result["vulnType"].get("value"):
                    vuln_type = result["vulnType"]["value"].split("/")[-1]
                    vulnerability.type = vuln_type
                    
                vulnerabilities.append(vulnerability)
                
            return vulnerabilities
        except SparqlClientError as e:
            logger.error(f"Failed to get vulnerabilities for {software_name} {version_id}: {e}")
            raise
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format.

        Returns:
            str: ISO-formatted timestamp.
        """
        return datetime.datetime.now().isoformat()
    
    def _is_valid_software_name(self, software_name: str) -> bool:
        """Validate software name to prevent injection.

        Args:
            software_name (str): Software name to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        import re
        return bool(software_name and re.match(r'^[a-zA-Z0-9_\-\.\:\/]*$', software_name))