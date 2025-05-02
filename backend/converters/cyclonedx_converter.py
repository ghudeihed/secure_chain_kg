import json
import uuid
import logging
import datetime

logger = logging.getLogger(__name__)

class CycloneDXConverter:
    """Converter for generating CycloneDX SBOM format."""
    
    def convert(self, sbom):
        """Convert internal SBOM representation to CycloneDX format."""
        logger.info(f"Converting SBOM to CycloneDX format for {sbom['name']}")
        
        # Create CycloneDX document structure
        cyclonedx_doc = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.3",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "tools": [
                    {
                        "vendor": "SecureChain",
                        "name": "SBOM Generator",
                        "version": "1.0.0"
                    }
                ]
            },
            "components": []
        }
        
        # Process all versions and their dependencies
        self._process_versions(cyclonedx_doc, sbom["name"], sbom["versions"])
        
        return json.dumps(cyclonedx_doc, indent=2)
    
    def _process_versions(self, cyclonedx_doc, software_name, versions):
        """Process software versions and add them to CycloneDX document."""
        for version in versions:
            # Create component for this version
            component = {
                "type": "library",
                "name": software_name,
                "version": version["version_id"],
                "purl": f"pkg:generic/{software_name}@{version['version_id']}",
                "bom-ref": f"{software_name}@{version['version_id']}"
            }
            
            # Add vulnerability information
            if "vulnerabilities" in version and version["vulnerabilities"]:
                if "vulnerabilities" not in cyclonedx_doc:
                    cyclonedx_doc["vulnerabilities"] = []
                
                for vuln in version["vulnerabilities"]:
                    vulnerability = {
                        "id": vuln["id"],
                        "affects": [
                            {
                                "ref": component["bom-ref"]
                            }
                        ]
                    }
                    
                    if "type" in vuln:
                        vulnerability["cwes"] = [int(vuln["type"].replace("CWE-", ""))]
                        
                    cyclonedx_doc["vulnerabilities"].append(vulnerability)
            
            # Add component to document
            cyclonedx_doc["components"].append(component)
            
            # Process dependencies recursively
            if "dependencies" in version and version["dependencies"]:
                self._process_dependencies(cyclonedx_doc, version["dependencies"])
                
                # Add dependency references
                dependencies = []
                for dep in version["dependencies"]:
                    dependencies.append({
                        "ref": f"{dep['name']}@{dep['version_id']}"
                    })
                
                if dependencies:
                    component["dependencies"] = dependencies
    
    def _process_dependencies(self, cyclonedx_doc, dependencies):
        """Process dependencies and add them to CycloneDX document."""
        for dependency in dependencies:
            # Create component for this dependency
            component = {
                "type": "library",
                "name": dependency["name"],
                "version": dependency["version_id"],
                "purl": f"pkg:generic/{dependency['name']}@{dependency['version_id']}",
                "bom-ref": f"{dependency['name']}@{dependency['version_id']}"
            }
            
            # Check if component already exists
            if not any(c["bom-ref"] == component["bom-ref"] for c in cyclonedx_doc["components"]):
                # Add vulnerability information
                if "vulnerabilities" in dependency and dependency["vulnerabilities"]:
                    if "vulnerabilities" not in cyclonedx_doc:
                        cyclonedx_doc["vulnerabilities"] = []
                    
                    for vuln in dependency["vulnerabilities"]:
                        vulnerability = {
                            "id": vuln["id"],
                            "affects": [
                                {
                                    "ref": component["bom-ref"]
                                }
                            ]
                        }
                        
                        if "type" in vuln:
                            vulnerability["cwes"] = [int(vuln["type"].replace("CWE-", ""))]
                            
                        cyclonedx_doc["vulnerabilities"].append(vulnerability)
                
                # Add component to document
                cyclonedx_doc["components"].append(component)
            
            # Process sub-dependencies recursively
            if "dependencies" in dependency and dependency["dependencies"]:
                self._process_dependencies(cyclonedx_doc, dependency["dependencies"])
                
                # Add dependency references
                sub_dependencies = []
                for dep in dependency["dependencies"]:
                    sub_dependencies.append({
                        "ref": f"{dep['name']}@{dep['version_id']}"
                    })
                
                if sub_dependencies:
                    # Find the component in the document and add dependencies
                    for c in cyclonedx_doc["components"]:
                        if c["bom-ref"] == component["bom-ref"]:
                            c["dependencies"] = sub_dependencies
                            break