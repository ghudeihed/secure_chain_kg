import json
import logging

logger = logging.getLogger(__name__)

class JsonConverter:
    """Converter for generating JSON SBOM format."""
    
    def convert(self, sbom):
        """Convert internal SBOM representation to JSON."""
        logger.info(f"Converting SBOM to JSON format for {sbom['name']}")
        
        # For JSON format, we can use the internal representation directly
        return json.dumps(sbom, indent=2)