import pytest
from unittest.mock import MagicMock
from services.sbom_generator import SbomGenerator, Sbom
from services.sparql_client import SparqlClient

@pytest.fixture
def sparql_client():
    return MagicMock(spec=SparqlClient)

@pytest.fixture
def sbom_generator(sparql_client):
    return SbomGenerator(sparql_client)

def test_generate_sbom(sparql_client, sbom_generator):
    mock_result = {"results": {"bindings": [{"version_id": {"value": "1.0.0"}}]}}
    sparql_client.query.side_effect = [
        mock_result,  # Versions
        {"results": {"bindings": []}},  # Dependencies
        {"results": {"bindings": []}}   # Vulnerabilities
    ]
    
    sbom = sbom_generator.generate_sbom("test-software")
    assert isinstance(sbom, Sbom)
    assert sbom.name == "test-software"
    assert len(sbom.versions) == 1
    assert sbom.versions[0].version_id == "1.0.0"

def test_invalid_software_name(sbom_generator):
    with pytest.raises(ValueError, match="Invalid software name"):
        sbom_generator.generate_sbom("invalid;DROP")

def test_sparql_error(sparql_client, sbom_generator):
    sparql_client.query.side_effect = Exception("Connection refused")
    with pytest.raises(Exception, match="Connection refused"):
        sbom_generator.generate_sbom("test-software")