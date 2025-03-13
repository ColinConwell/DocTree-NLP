"""
Rate limiter for Notion API requests.

This module handles rate limiting for Notion API requests to avoid exceeding
the API's limits (3 requests per second).
"""
import time
import logging
from collections import deque
from datetime import datetime
from typing import Deque, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, max_requests: int = 3, time_window: float = 1.0):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_timestamps: Deque[float] = deque(maxlen=max_requests)
        
    def wait_if_needed(self):
        """
        Wait if request limit is reached.
        
        This method will block until it's safe to make another request.
        """
        # If we haven't made enough requests yet, we can proceed immediately
        if len(self.request_timestamps) < self.max_requests:
            self._record_request()
            return
            
        # Check the oldest request in our window
        current_time = time.time()
        oldest_request_time = self.request_timestamps[0]
        time_since_oldest = current_time - oldest_request_time
        
        # If the oldest request is still within our time window, we need to wait
        if time_since_oldest < self.time_window:
            wait_time = self.time_window - time_since_oldest
            logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            
        # Record this request
        self._record_request()
        
    def _record_request(self):
        """Record a request timestamp."""
        self.request_timestamps.append(time.time())
        
    @property
    def requests_in_current_window(self) -> int:
        """
        Get the number of requests in the current time window.
        
        Returns:
            int: Number of requests in the current window
        """
        if not self.request_timestamps:
            return 0
            
        current_time = time.time()
        count = sum(1 for t in self.request_timestamps 
                   if current_time - t <= self.time_window)
        return count