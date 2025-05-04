import time
import logging
from typing import Dict, Any, Optional
from SPARQLWrapper import SPARQLWrapper, JSON
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    result: Dict[str, Any]
    timestamp: float

class SparqlClient:
    """Client for interacting with SPARQL endpoints with caching and error handling."""
    
    DEFAULT_CACHE_EXPIRY: int = 600  # 10 minutes in seconds
    
    def __init__(self, endpoint_url: str, cache_expiry: int = DEFAULT_CACHE_EXPIRY):
        """Initialize the SPARQL client with given endpoint and cache settings."""
        self.endpoint = endpoint_url
        self.cache: Dict[int, CacheEntry] = {}
        self.cache_expiry = cache_expiry
        self.sparql = SPARQLWrapper(endpoint_url)
        self.sparql.setReturnFormat(JSON)
        
    def query(self, query_template: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a SPARQL query with parameter substitution and caching."""
        query = self._build_query(query_template, params)
        cache_key = hash(query)
        
        # Check cache
        cached = self._get_cached_result(cache_key)
        if cached:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return cached
            
        try:
            # Execute query
            self.sparql.setQuery(query)
            result = self.sparql.query().convert()
            
            # Store in cache
            self.cache[cache_key] = CacheEntry(
                result=result,
                timestamp=time.time()
            )
            
            return result
        except Exception as e:
            logger.error(f"SPARQL query error: {str(e)}")
            logger.debug(f"Failed query: {query}")
            raise SparqlQueryError(f"Failed to execute SPARQL query: {str(e)}") from e
    
    def _get_cached_result(self, cache_key: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if available and not expired."""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry.timestamp < self.cache_expiry:
                return entry.result
            else:
                del self.cache[cache_key]
        return None
    
    def _build_query(self, query_template: str, params: Optional[Dict[str, str]]) -> str:
        """Build a SPARQL query with safe parameter substitution."""
        if not params:
            return query_template
            
        query = query_template
        for key, value in params.items():
            if not self._is_valid_parameter(value):
                raise ValueError(f"Invalid parameter value for {key}: {value}")
                
            placeholder = f"%({key})s"
            query = query.replace(placeholder, self._escape_string(value))
            
        return query
    
    @staticmethod
    def _is_valid_parameter(value: str) -> bool:
        """Validate parameter to prevent SPARQL injection."""
        if not isinstance(value, str):
            return False
            
        dangerous_patterns = {
            "INSERT", "DELETE", "DROP", "LOAD", "CLEAR", "CREATE",
            "CONSTRUCT", "DESCRIBE", ";", "--", "/*", "*/"
        }
        
        return not any(pattern.upper() in value.upper() for pattern in dangerous_patterns)
    
    @staticmethod
    def _escape_string(value: str) -> str:
        """Escape special characters in string for safe SPARQL query."""
        if not isinstance(value, str):
            return str(value)
            
        escape_chars = {
            "\\": "\\\\",
            "\"": "\\\"",
            "\n": "\\n",
            "\r": "\\r",
            "\t": "\\t"
        }
        
        for src, dst in escape_chars.items():
            value = value.replace(src, dst)
        return value

class SparqlQueryError(Exception):
    """Custom exception for SPARQL query errors."""
    pass