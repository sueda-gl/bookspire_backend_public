from typing import Optional
import asyncio
from datetime import datetime, timedelta

class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class RateLimiter:
    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire rate limit permission"""
        async with self.lock:
            now = datetime.now()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(minutes=1)]
            
            if len(self.requests) >= self.requests_per_minute:
                raise RateLimitError("Rate limit exceeded. Please wait before making more requests.")
            
            self.requests.append(now)