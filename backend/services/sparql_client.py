import time
import logging
import hashlib
from typing import Dict, Any, Optional
from cachetools import TTLCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.SPARQLExceptions import QueryBadFormed, EndPointNotFound
from config import settings

logger = logging.getLogger(__name__)

class SparqlClientError(Exception):
    """Custom exception for SPARQL client errors."""
    pass

class SparqlClient:
    """Client for interacting with SPARQL endpoint with caching and error handling.

    Args:
        endpoint_url (str): URL of the SPARQL endpoint.
        cache_expiry (float): Cache expiry time in seconds (default: 600).
        cache_maxsize (int): Maximum number of cached queries (default: 1000).
    """
    
    def __init__(self, endpoint_url: str = settings.SPARQL_ENDPOINT, cache_expiry: float = 600, cache_maxsize: int = 1000):
        self.endpoint = endpoint_url
        self.cache = TTLCache(maxsize=cache_maxsize, ttl=cache_expiry)
        self.cache_expiry = cache_expiry
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((EndPointNotFound, ConnectionError)),
        before_sleep=lambda retry_state: logger.debug(f"Retrying SPARQL query: attempt {retry_state.attempt_number}")
    )
    def query(self, query_template: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a SPARQL query with parameter substitution and caching.

        Args:
            query_template (str): SPARQL query template with placeholders (e.g., '%(key)s').
            params (dict, optional): Parameters to substitute into the query.

        Returns:
            dict: JSON result from the SPARQL endpoint.

        Raises:
            SparqlClientError: If the query fails or is invalid.
        """
        query = self._build_query(query_template, params)
        cache_key = hashlib.sha256(query.encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.cache[cache_key]
        
        try:
            sparql = SPARQLWrapper(self.endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(30)  # Add timeout
            result = sparql.query().convert()
            
            # Cache result
            self.cache[cache_key] = result
            return result
        except QueryBadFormed as e:
            logger.error(f"Invalid SPARQL query: {e}")
            logger.debug(f"Failed query: {query}")
            raise SparqlClientError(f"Invalid SPARQL query: {e}")
        except (EndPointNotFound, ConnectionError) as e:
            logger.error(f"SPARQL endpoint error: {e}")
            logger.debug(f"Failed query: {query}")
            raise SparqlClientError(f"Endpoint error: {e}")
        except Exception as e:
            logger.error(f"Unexpected SPARQL query error: {e}")
            logger.debug(f"Failed query: {query}")
            raise SparqlClientError(f"Unexpected error: {e}")
    
    def _build_query(self, query_template: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build a SPARQL query with parameter substitution.

        Args:
            query_template (str): SPARQL query template.
            params (dict, optional): Parameters to substitute.

        Returns:
            str: Substituted query string.

        Raises:
            ValueError: If parameters are invalid or placeholders are missing.
        """
        if not params:
            return query_template
            
        query = query_template
        for key, value in params.items():
            if not self._is_valid_parameter(value):
                raise ValueError(f"Invalid parameter value: {value}")
                
            placeholder = f"%({key})s"
            if placeholder not in query:
                raise ValueError(f"Placeholder {placeholder} not found in query template")
                
            query = query.replace(placeholder, self._escape_string(value))
            
        # Basic SPARQL syntax check
        if not query.strip().upper().startswith(("SELECT", "ASK", "CONSTRUCT", "DESCRIBE")):
            raise ValueError("Query must start with SELECT, ASK, CONSTRUCT, or DESCRIBE")
            
        return query
    
    def _is_valid_parameter(self, value: Any) -> bool:
        """Validate parameter to prevent SPARQL injection.

        Args:
            value: Parameter value to validate.

        Returns:
            bool: True if the value is safe, False otherwise.
        """
        if not isinstance(value, str):
            return True
            
        # Whitelist: Allow alphanumeric, underscores, hyphens, and basic punctuation
        allowed_pattern = r'^[a-zA-Z0-9_\-\.\:\/]*$'
        import re
        if not re.match(allowed_pattern, value):
            return False
            
        # Block dangerous SPARQL keywords
        dangerous_patterns = [
            "INSERT", "DELETE", "DROP", "LOAD", "CLEAR", "CREATE", 
            "CONSTRUCT", "DESCRIBE", ";", "--", "/*", "*/"
        ]
        for pattern in dangerous_patterns:
            if pattern.upper() in value.upper():
                return False
                
        return True
    
    def _escape_string(self, value: Any) -> str:
        """Escape a string value for SPARQL query.

        Args:
            value: Value to escape.

        Returns:
            str: Escaped string.
        """
        if isinstance(value, str):
            # Comprehensive escaping for SPARQL
            replacements = {
                "\\": "\\\\",
                "\"": "\\\"",
                "\n": "\\n",
                "\r": "\\r",
                "\t": "\\t",
                "<": "\\u003C",
                ">": "\\u003E"
            }
            for old, new in replacements.items():
                value = value.replace(old, new)
            return value
        return str(value)