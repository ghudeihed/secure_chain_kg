import json
import uuid
import logging
import datetime

logger = logging.getLogger(__name__)

class SpdxConverter:
    """Converter for generating SPDX SBOM format."""
    
    def convert(self, sbom):
        """Convert internal SBOM representation to SPDX format."""
        logger.info(f"Converting SBOM to SPDX format for {sbom['name']}")
        
        document_namespace = f"https://example.com/sboms/{uuid.uuid4()}"
        
        # Create SPDX document structure
        spdx_doc = {
            "spdxVersion": "SPDX-2.2",
            "dataLicense": "CC0-1.0",
            "SPDX-ID": "SPDXRef-DOCUMENT",
            "name": f"SBOM for {sbom['name']}",
            "documentNamespace": document_namespace,
            "creationInfo": {
                "created": datetime.datetime.now().isoformat(),
                "creators": ["Tool: Secure-Chain SBOM Generator"],
                "licenseListVersion": "3.11"
            },
            "packages": []
        }
        
        # Process all versions and their dependencies
        self._process_versions(spdx_doc, sbom["name"], sbom["versions"])
        
        return json.dumps(spdx_doc, indent=2)
    
    def _process_versions(self, spdx_doc, software_name, versions):
        """Process software versions and add them to SPDX document."""
        for version in versions:
            # Create package for this version
            package = {
                "name": software_name,
                "SPDX-ID": f"SPDXRef-Package-{software_name}-{version['version_id']}",
                "versionInfo": version["version_id"],
                "downloadLocation": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "externalRefs": []
            }
            
            # Add vulnerability information
            if "vulnerabilities" in version and version["vulnerabilities"]:
                for vuln in version["vulnerabilities"]:
                    package["externalRefs"].append({
                        "referenceCategory": "SECURITY",
                        "referenceType": "cve",
                        "referenceLocator": vuln["id"]
                    })
            
            # Add package to document
            spdx_doc["packages"].append(package)
            
            # Process dependencies recursively
            if "dependencies" in version and version["dependencies"]:
                self._process_dependencies(spdx_doc, version["dependencies"])
    
    def _process_dependencies(self, spdx_doc, dependencies):
        """Process dependencies and add them to SPDX document."""
        for dependency in dependencies:
            # Create package for this dependency
            package = {
                "name": dependency["name"],
                "SPDX-ID": f"SPDXRef-Package-{dependency['name']}-{dependency['version_id']}",
                "versionInfo": dependency["version_id"],
                "downloadLocation": "NOASSERTION",
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "NOASSERTION",
                "externalRefs": []
            }
            
            # Add vulnerability information
            if "vulnerabilities" in dependency and dependency["vulnerabilities"]:
                for vuln in dependency["vulnerabilities"]:
                    package["externalRefs"].append({
                        "referenceCategory": "SECURITY",
                        "referenceType": "cve",
                        "referenceLocator": vuln["id"]
                    })
            
            # Add package to document if not already present
            if not any(p["SPDX-ID"] == package["SPDX-ID"] for p in spdx_doc["packages"]):
                spdx_doc["packages"].append(package)
            
            # Process sub-dependencies recursively
            if "dependencies" in dependency and dependency["dependencies"]:
                self._process_dependencies(spdx_doc, dependency["dependencies"])