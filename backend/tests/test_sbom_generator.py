import pytest
from unittest.mock import Mock, patch

from app.sbom_generator import SbomGenerator

@pytest.fixture
def mock_client():
    return Mock()

@pytest.fixture
def sbom_generator(mock_client):
    return SbomGenerator(mock_client)

def test_get_software_versions(sbom_generator, mock_client):
    """Test retrieving software versions."""
    # Mock response for version query
    mock_response = {
        "results": {
            "bindings": [
                {"version_id": {"value": "1.0.0"}},
                {"version_id": {"value": "2.0.0"}}
            ]
        }
    }
    mock_client.query.return_value = mock_response
    
    # Call the method
    versions = sbom_generator._get_software_versions("test_software")
    
    # Verify client was called with correct query
    mock_client.query.assert_called_once()
    
    # Verify result structure
    assert len(versions) == 2
    assert versions[0]["version_id"] == "1.0.0"
    assert versions[1]["version_id"] == "2.0.0"

def test_get_dependencies(sbom_generator, mock_client):
    """Test retrieving dependencies."""
    # Mock response for dependency query
    mock_response = {
        "results": {
            "bindings": [
                {
                    "dependency": {"value": "https://w3id.org/secure-chain/Software/dep1"},
                    "dependencyVersion": {"value": "https://w3id.org/secure-chain/SoftwareVersion/dep1#1.0.0"},
                    "depVersionName": {"value": "1.0.0"}
                }
            ]
        }
    }
    
    # Mock response for vulnerability query (empty)
    mock_vuln_response = {
        "results": {
            "bindings": []
        }
    }
    
    # Configure mock client to return different responses
    # We need THREE responses: one for dependencies and two for vulnerabilities
    mock_client.query.side_effect = [mock_response, mock_vuln_response, mock_vuln_response]
    
    # Call the method
    dependencies = sbom_generator._get_dependencies("test_software", "1.0.0")
    
    # Verify client was called with correct queries
    assert mock_client.query.call_count == 3
    
    # Verify result structure
    assert len(dependencies) == 1
    assert dependencies[0]["name"] == "dep1"
    assert dependencies[0]["version_id"] == "1.0.0"
    assert dependencies[0]["dependencies"] == []

def test_circular_dependency_detection(sbom_generator, mock_client):
    """Test detection of circular dependencies."""
    # Create a circular dependency
    sbom_generator.visited.add("test_software:1.0.0")
    
    # Call the method
    dependencies = sbom_generator._get_dependencies("test_software", "1.0.0")
    
    # Verify no queries were made and empty result returned
    mock_client.query.assert_not_called()
    assert dependencies == []

def test_get_vulnerabilities(sbom_generator, mock_client):
    """Test retrieving vulnerabilities."""
    # Mock response for vulnerability query
    mock_response = {
        "results": {
            "bindings": [
                {
                    "vulnerability": {"value": "https://w3id.org/secure-chain/Vulnerability/CVE-2021-12345"},
                    "vulnId": {"value": "CVE-2021-12345"},
                    "vulnType": {"value": "https://w3id.org/secure-chain/VulnerabilityType/CWE-79"}
                }
            ]
        }
    }
    mock_client.query.return_value = mock_response
    
    # Call the method
    vulnerabilities = sbom_generator._get_vulnerabilities("test_software", "1.0.0")
    
    # Verify client was called with correct query
    mock_client.query.assert_called_once()
    
    # Verify result structure
    assert len(vulnerabilities) == 1
    assert vulnerabilities[0]["id"] == "CVE-2021-12345"
    assert vulnerabilities[0]["type"] == "CWE-79"

def test_generate_sbom(sbom_generator, mock_client):
    """Test generating complete SBOM."""
    # Mock responses for all queries
    version_response = {
        "results": {
            "bindings": [
                {"version_id": {"value": "1.0.0"}}
            ]
        }
    }
    
    dependency_response = {
        "results": {
            "bindings": []
        }
    }
    
    vulnerability_response = {
        "results": {
            "bindings": []
        }
    }
    
    # Configure mock client to return different responses
    mock_client.query.side_effect = [version_response, dependency_response, vulnerability_response]
    
    # Call the method
    sbom = sbom_generator.generate_sbom("test_software")
    
    # Verify client was called for all queries
    assert mock_client.query.call_count == 3
    
    # Verify SBOM structure
    assert sbom["name"] == "test_software"
    assert len(sbom["versions"]) == 1
    assert sbom["versions"][0]["version_id"] == "1.0.0"
    assert "generated_at" in sbom
    assert "tool" in sbom