import pytest
import hashlib
from unittest.mock import patch
from services.sparql_client import SparqlClient, SparqlClientError

@pytest.fixture
def client():
    return SparqlClient(endpoint_url="http://test-endpoint", cache_expiry=1)

def test_query_success(client):
    mock_result = {"results": {"bindings": [{"x": {"value": "test"}}]}}
    with patch("SPARQLWrapper.SPARQLWrapper.query") as mock_query:
        mock_query.return_value.convert.return_value = mock_result
        result = client.query("SELECT ?x WHERE { ?x a ?type }")
        assert result == mock_result
        assert client.cache  # Cache should be populated

def test_query_cache_hit(client):
    mock_result = {"results": {"bindings": [{"x": {"value": "test"}}]}}
    client.cache[hashlib.sha256("SELECT ?x WHERE { ?x a ?type }".encode()).hexdigest()] = mock_result
    result = client.query("SELECT ?x WHERE { ?x a ?type }")
    assert result == mock_result

def test_query_invalid_param(client):
    with pytest.raises(ValueError, match="Invalid parameter value"):
        client.query("SELECT ?x WHERE { ?x a %(type)s }", params={"type": "DELETE"})

def test_query_endpoint_error(client):
    with patch("SPARQLWrapper.SPARQLWrapper.query") as mock_query:
        mock_query.side_effect = ConnectionError("Endpoint unreachable")
        with pytest.raises(SparqlClientError, match="Cannot connect to SPARQL endpoint"):
            client.query("SELECT ?x WHERE { ?x a ?type }")