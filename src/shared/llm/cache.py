from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResponseCache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.last_cleanup = datetime.now()
    
    def get(self, key: str) -> Optional[str]:
        """Get cache entry if exists and is valid"""
        current_time = datetime.now()
        
        # Check if we need to clean cache (every 5 minutes)
        if (current_time - self.last_cleanup).total_seconds() > 300:
            self.cleanup()
            self.last_cleanup = current_time
        
        if key in self.cache:
            entry = self.cache[key]
            # Check if entry is still valid
            if (current_time - entry['timestamp']).total_seconds() < self.ttl_seconds:
                return entry['response']
        return None
    
    def set(self, key: str, response: str):
        """Cache a response"""
        self.cache[key] = {
            'response': response,
            'timestamp': datetime.now()
        }
    
    def cleanup(self):
        """Clean up expired cache entries"""
        current_time = datetime.now()
        keys_to_delete = []
        
        for key, entry in self.cache.items():
            if (current_time - entry['timestamp']).total_seconds() > self.ttl_seconds:
                keys_to_delete.append(key)
                
        for key in keys_to_delete:
            del self.cache[key]
        
        logger.info(f"Cache cleanup: removed {len(keys_to_delete)} expired entries")