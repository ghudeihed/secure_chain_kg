import time
import logging
from SPARQLWrapper import SPARQLWrapper, JSON

logger = logging.getLogger(__name__)

class SparqlClient:
    """Client for interacting with SPARQL endpoint with caching and error handling."""
    
    def __init__(self, endpoint_url, cache_expiry=600):  # 10-minute default cache
        self.endpoint = endpoint_url
        self.cache = {}  # Simple in-memory cache
        self.cache_expiry = cache_expiry
        
    def query(self, query_template, params=None):
        """Execute a SPARQL query with parameter substitution and caching."""
        query = self._build_query(query_template, params)
        cache_key = hash(query)
        
        # Check cache first
        if cache_key in self.cache and time.time() - self.cache[cache_key]['timestamp'] < self.cache_expiry:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.cache[cache_key]['result']
        
        try:
            # Execute SPARQL query
            sparql = SPARQLWrapper(self.endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            result = sparql.query().convert()
            
            # Cache result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
        except Exception as e:
            logger.error(f"SPARQL query error: {e}")
            logger.debug(f"Failed query: {query}")
            raise
    
    def _build_query(self, query_template, params=None):
        """Build a SPARQL query with parameter substitution."""
        if not params:
            return query_template
            
        # Simple string substitution with validation
        query = query_template
        for key, value in params.items():
            # Validate parameter to prevent injection
            if not self._is_valid_parameter(value):
                raise ValueError(f"Invalid parameter value: {value}")
                
            # Replace parameter in query
            placeholder = f"%({key})s"
            query = query.replace(placeholder, self._escape_string(value))
            
        return query
    
    def _is_valid_parameter(self, value):
        """Validate parameter to prevent SPARQL injection."""
        # Implement validation logic based on expected parameter types
        if isinstance(value, str):
            # Check for SPARQL injection patterns
            dangerous_patterns = [
                "INSERT", "DELETE", "DROP", "LOAD", "CLEAR", "CREATE", 
                "CONSTRUCT", "DESCRIBE", ";", "--", "/*", "*/"
            ]
            
            for pattern in dangerous_patterns:
                if pattern.upper() in value.upper():
                    return False
                    
        return True
    
    def _escape_string(self, value):
        """Escape a string value for SPARQL query."""
        if isinstance(value, str):
            # Escape special characters
            return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")
        return str(value)