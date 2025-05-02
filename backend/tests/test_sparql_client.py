import pytest
import time
from unittest.mock import Mock, patch

# You don't need sys.path manipulation with pytest
from app.sparql_client import SparqlClient

@pytest.fixture
def sparql_client():
    return SparqlClient("http://example.com/sparql", cache_expiry=60)

def test_build_query_no_params(sparql_client):
    """Test query building with no parameters."""
    query_template = "SELECT * WHERE { ?s ?p ?o }"
    result = sparql_client._build_query(query_template)
    assert result == query_template

def test_build_query_with_params(sparql_client):
    """Test query building with parameters."""
    query_template = "SELECT * WHERE { ?s ?p \"%(value)s\" }"
    params = {"value": "test"}
    result = sparql_client._build_query(query_template, params)
    assert result == "SELECT * WHERE { ?s ?p \"test\" }"

def test_parameter_validation(sparql_client):
    """Test parameter validation for injection prevention."""
    # Valid parameter
    assert sparql_client._is_valid_parameter("test")
    
    # Invalid parameters with SPARQL injection attempts
    assert not sparql_client._is_valid_parameter("test INSERT DATA")
    assert not sparql_client._is_valid_parameter("test; DROP")
    assert not sparql_client._is_valid_parameter("test/* comment */")

@patch('app.sparql_client.SPARQLWrapper')
def test_query_execution(mock_sparql_wrapper, sparql_client):
    """Test query execution with mocked SPARQLWrapper."""
    # Setup mock
    mock_instance = Mock()
    mock_sparql_wrapper.return_value = mock_instance
    mock_result = {"results": {"bindings": []}}
    mock_instance.query.return_value.convert.return_value = mock_result
    
    # Execute query
    query = "SELECT * WHERE { ?s ?p ?o }"
    result = sparql_client.query(query)
    
    # Verify SPARQLWrapper was called correctly
    mock_sparql_wrapper.assert_called_once_with("http://example.com/sparql")
    mock_instance.setQuery.assert_called_once_with(query)
    mock_instance.setReturnFormat.assert_called_once()
    mock_instance.query.assert_called_once()
    
    # Verify result
    assert result == mock_result

def test_query_caching(sparql_client):
    """Test that queries are cached and reused."""
    # Mock the SPARQLWrapper to avoid HTTP requests
    with patch('app.sparql_client.SPARQLWrapper') as mock_sparql_wrapper:
        # Configure mock to return a result
        mock_instance = Mock()
        mock_sparql_wrapper.return_value = mock_instance
        mock_result = {"results": {"bindings": []}}
        mock_instance.query.return_value.convert.return_value = mock_result
        
        # Use a simple query
        query = "SELECT * WHERE { ?s ?p ?o }"
        
        # First call - should execute the query
        result1 = sparql_client.query(query)
        
        # At this point, the result should be cached
        # Let's verify the cache has the result
        cache_key = hash(query)
        assert cache_key in sparql_client.cache
        
        # Replace the mock with a failing mock to prove cache is used
        mock_instance.query.side_effect = Exception("This should not be called")
        
        # Second call - should use cache instead of calling the SPARQL endpoint
        result2 = sparql_client.query(query)
        
        # If we got here without an exception, cache was used
        # Also verify the results are the same
        assert result1 == result2
        
        # Verify SPARQLWrapper.query was called exactly once
        assert mock_instance.query.call_count == 1