"""
Blogger RSS Feed Parser
Extracts all post URLs from a Blogger RSS/Atom feed
"""

import feedparser
import logging
from typing import List, Optional
from urllib.parse import urlparse
import requests
from datetime import datetime


class BloggerFeedParser:
    def __init__(self, feed_url: str):
        """Initialize the feed parser."""
        self.feed_url = feed_url
        self.logger = logging.getLogger(__name__)
        
    def get_all_post_urls(self, max_results: int = 500) -> List[str]:
        """
        Get all post URLs from the Blogger feed.
        
        Args:
            max_results: Maximum number of results to fetch
            
        Returns:
            List of post URLs
        """
        urls = []
        
        try:
            # Parse the feed
            feed = feedparser.parse(self.feed_url)
            
            if feed.bozo:
                self.logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return urls
                
            # Extract URLs from entries
            for entry in feed.entries:
                if hasattr(entry, 'link'):
                    url = entry.

"""
Blogger RSS Feed Parser
Extracts all post URLs from a Blogger RSS/Atom feed
"""

import feedparser
import logging
from typing import List, Optional
from urllib.parse import urlparse
import requests
from datetime import datetime


class BloggerFeedParser:
    def __init__(self, feed_url: str):
        """Initialize the feed parser."""
        self.feed_url = feed_url
        self.logger = logging.getLogger(__name__)
        
    def get_all_post_urls(self, max_results: int = 500) -> List[str]:
        """
        Get all post URLs from the Blogger feed.
        
        Args:
            max_results: Maximum number of results to fetch
            
        Returns:
            List of post URLs
        """
        urls = []
        
        try:
            # Parse the feed
            feed = feedparser.parse(self.feed_url)
            
            if feed.bozo:
                self.logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return urls
                
            # Extract URLs from entries
            for entry in feed.entries:
                if hasattr(entry, 'link'):
                    url = entry.link
                    # Filter out non-post URLs
                    if self._is_valid_post_url(url):
                        urls.append(url)
                        
                # Also check alternate links
                if hasattr(entry, 'links'):
                    for link in entry.links:
                        if link.get('rel') == 'alternate' and link.get('type') == 'text/html':
                            url = link.get('href')
                            if url and self._is_valid_post_url(url):
                                urls.append(url)
                                
            # Remove duplicates while preserving order
            urls = list(dict.fromkeys(urls))
            
            self.logger.info(f"Found {len(urls)} valid post URLs")
            return urls[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error fetching feed: {str(e)}")
            return urls
            
    def _is_valid_post_url(self, url: str) -> bool:
        """
        Check if a URL is a valid blog post URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid post URL, False otherwise
        """
        if not url:
            return False
            
        # Parse the URL
        parsed = urlparse(url)
        
        # Check if it's a valid post URL (ends with .html)
        if parsed.path.endswith('.html'):
            # Exclude certain paths
            excluded_paths = ['/p/', '/search', '/feeds/', '?m=1', '?m=0']
            for excluded in excluded_paths:
                if excluded in parsed.path or excluded in url:
                    return False
            return True
            
        return False
        
    def get_recent_posts(self, days: int = 7) -> List[str]:
        """
        Get posts published in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent post URLs
        """
        recent_urls = []
        cutoff_date = datetime.now().timestamp() - (days * 86400)
        
        try:
            feed = feedparser.parse(self.feed_url)
            
            for entry in feed.entries:
                if hasattr(entry, 'published_parsed'):
                    published = datetime(*entry.published_parsed[:6]).timestamp()
                    if published > cutoff_date and hasattr(entry, 'link'):
                        if self._is_valid_post_url(entry.link):
                            recent_urls.append(entry.link)
                            
            return recent_urls
            
        except Exception as e:
            self.logger.error(f"Error getting recent posts: {str(e)}")
            return recent_urls



