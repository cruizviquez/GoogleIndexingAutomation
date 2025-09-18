"""
Rate limiter for Google Indexing API
Tracks daily and per-minute request limits
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class RateLimiter:
    def __init__(self):
        """Initialize the rate limiter."""
        self.data_file = Path("data/rate_limit_data.json")
        self.data_file.parent.mkdir(exist_ok=True)
        self.load_data()
        
    def load_data(self):
        """Load rate limiting data from file."""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.daily_requests = data.get('daily_requests', 0)
                self.last_reset = datetime.fromisoformat(data.get('last_reset', datetime.now().isoformat()))
                self.minute_requests = data.get('minute_requests', [])
        else:
            self.daily_requests = 0
            self.last_reset = datetime.now()
            self.minute_requests = []
            
        # Reset daily counter if needed
        if datetime.now().date() > self.last_reset.date():
            self.daily_requests = 0
            self.last_reset = datetime.now()
            self.save_data()
            
    def save_data(self):
        """Save rate limiting data to file."""
        data = {
            'daily_requests': self.daily_requests,
            'last_reset': self.last_reset.isoformat(),
            'minute_requests': self.minute_requests
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f)
            
    def record_request(self):
        """Record a new request."""
        now = time.time()
        
        # Add to minute requests
        self.minute_requests.append(now)
        
        # Clean old minute requests (older than 60 seconds)
        self.minute_requests = [t for t in self.minute_requests if t > now - 60]
        
        # Increment daily counter
        self.daily_requests += 1
        
        self.save_data()
        
    def can_make_request(self, requests_per_minute: int = 10) -> bool:
        """
        Check if we can make another request.
        
        Args:
            requests_per_minute: Maximum requests per minute
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Clean old minute requests
        self.minute_requests = [t for t in self.minute_requests if t > now - 60]
        
        # Check minute limit
        if len(self.minute_requests) >= requests_per_minute:
            return False
            
        return True
        
    def time_until_next_request(self, requests_per_minute: int = 10) -> float:
        """
        Calculate seconds until next request is allowed.
        
        Args:
            requests_per_minute: Maximum requests per minute
            
        Returns:
            Seconds to wait, 0 if can request now
        """
        if self.can_make_request(requests_per_minute):
            return 0
            
        now = time.time()
        oldest_request = min(self.minute_requests)
        wait_time = 60 - (now - oldest_request) + 1
        
        return max(0, wait_time)
