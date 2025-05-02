import time
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class Cache:
    """Thread-safe in-memory cache with expiration."""
    
    def __init__(self, default_ttl=600):
        self.cache = {}
        self.lock = Lock()
        self.default_ttl = default_ttl
        
    def get(self, key):
        """Get value from cache if it exists and is not expired."""
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                
                # Check if item is expired
                if item["expiry"] > time.time():
                    return item["value"]
                
                # Remove expired item
                del self.cache[key]
                
        return None
        
    def set(self, key, value, ttl=None):
        """Set value in cache with expiration time."""
        if ttl is None:
            ttl = self.default_ttl
            
        expiry = time.time() + ttl
        
        with self.lock:
            self.cache[key] = {
                "value": value,
                "expiry": expiry
            }
            
    def delete(self, key):
            """Delete item from cache."""
            with self.lock:
                if key in self.cache:
                    del self.cache[key]
                    
    def clear(self):
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            
    def cleanup(self):
        """Remove all expired items from cache."""
        current_time = time.time()
        
        with self.lock:
            keys_to_delete = [
                key for key, item in self.cache.items()
                if item["expiry"] <= current_time
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
                    
            return len(keys_to_delete)