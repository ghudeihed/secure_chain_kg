
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Pydantic models for request/response
class SoftwareInfo(BaseModel):
    """Information about a software."""
    id: str
    name: str
    description: Optional[str] = None

class VersionInfo(BaseModel):
    """Information about a software version."""
    id: str
    name: str
    software_id: str
    software_name: str

class DependencyInfo(BaseModel):
    """Information about a dependency."""
    id: str
    name: str
    version: str
    vulnerabilities: List[Dict[str, Any]] = []

class SBOMRequest(BaseModel):
    """Request model for generating SBOM."""
    software_id: str
    format: str = "spdx"  # Default format
    include_vulnerabilities: bool = False
    include_dependencies: bool = False
    include_licenses: bool = False
    include_metadata: bool = False

class SBOMResponse(BaseModel):
    """Response model for SBOM generation."""
    sbom_id: str
    software_id: str
    format: str
    content: Dict[str, Any]

class VulnerabilityInfo(BaseModel):
    """Information about a vulnerability."""
    id: str
    name: str
    description: Optional[str] = None
    type: Optional[str] = None

class LicenseInfo(BaseModel):
    """Information about a license."""
    id: str
    name: str
    url: Optional[str] = None
    description: Optional[str] = None

class MetadataInfo(BaseModel):
    """Information about metadata."""
    id: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None