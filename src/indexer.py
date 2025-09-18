#!/usr/bin/env python3
"""
Google Indexing API Automation for Blogger
Author: Dr. Carlos Ruiz Viquez
"""

import json
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ratelimit import limits, sleep_and_retry
from tqdm import tqdm
from colorama import init, Fore, Style

from feed_parser import BloggerFeedParser
from rate_limiter import RateLimiter

# Initialize colorama for colored output
init(autoreset=True)

class GoogleIndexer:
    def __init__(self, credentials_path: str):
        """Initialize the Google Indexing API client."""
        self.credentials_path = credentials_path
        self.service = self._build_service()
        self.rate_limiter = RateLimiter()
        self.indexed_urls_file = Path("data/indexed_urls.json")
        self.pending_urls_file = Path("data/pending_urls.json")
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/indexing_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _build_service(self):
        """Build the Google Indexing API service."""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/indexing']
            )
            service = build('indexing', 'v3', credentials=credentials)
            return service
        except Exception as e:
            self.logger.error(f"Failed to build service: {str(e)}")
            raise
            
    def load_indexed_urls(self) -> Dict[str, datetime]:
        """Load previously indexed URLs with timestamps."""
        if self.indexed_urls_file.exists():
            with open(self.indexed_urls_file, 'r') as f:
                data = json.load(f)
                # Convert string timestamps back to datetime
                return {url: datetime.fromisoformat(ts) for url, ts in data.items()}
        return {}
        
    def save_indexed_urls(self, indexed_urls: Dict[str, datetime]):
        """Save indexed URLs with timestamps."""
        data = {url: ts.isoformat() for url, ts in indexed_urls.items()}
        with open(self.indexed_urls_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_pending_urls(self) -> List[str]:
        """Load URLs pending indexing."""
        if self.pending_urls_file.exists():
            with open(self.pending_urls_file, 'r') as f:
                return json.load(f)
        return []
        
    def save_pending_urls(self, urls: List[str]):
        """Save URLs pending indexing."""
        with open(self.pending_urls_file, 'w') as f:
            json.dump(urls, f, indent=2)
            
    @sleep_and_retry
    @limits(calls=10, period=60)  # 10 calls per minute
    def request_indexing(self, url: str, update_type: str = "URL_UPDATED") -> bool:
        """
        Request indexing for a single URL.
        
        Args:
            url: The URL to index
            update_type: Either "URL_UPDATED" or "URL_DELETED"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            body = {
                'url': url,
                'type': update_type
            }
            
            response = self.service.urlNotifications().publish(body=body).execute()
            
            self.logger.info(f"{Fore.GREEN}✓ Successfully indexed: {url}{Style.RESET_ALL}")
            self.logger.debug(f"Response: {response}")
            
            # Update rate limiter
            self.rate_limiter.record_request()
            
            return True
            
        except HttpError as e:
            if e.resp.status == 429:
                self.logger.warning(f"{Fore.YELLOW}⚠ Rate limit hit, backing off...{Style.RESET_ALL}")
                time.sleep(60)  # Wait 1 minute
                return False
            elif e.resp.status == 403:
                self.logger.error(f"{Fore.RED}✗ Permission denied for {url}. Check service account permissions.{Style.RESET_ALL}")
                return False
            else:
                self.logger.error(f"{Fore.RED}✗ HTTP error for {url}: {e}{Style.RESET_ALL}")
                return False
        except Exception as e:
            self.logger.error(f"{Fore.RED}✗ Unexpected error for {url}: {str(e)}{Style.RESET_ALL}")
            return False
            
    def should_reindex(self, url: str, last_indexed: datetime, force: bool = False) -> bool:
        """
        Determine if a URL should be reindexed.
        
        Args:
            url: The URL to check
            last_indexed: When it was last indexed
            force: Force reindexing regardless of time
            
        Returns:
            True if should reindex, False otherwise
        """
        if force:
            return True
            
        # Reindex if older than 7 days
        days_old = (datetime.now() - last_indexed).days
        if days_old > 7:
            self.logger.info(f"URL last indexed {days_old} days ago, reindexing: {url}")
            return True
            
        return False
        
    def batch_index_urls(self, urls: List[str], force: bool = False):
        """
        Index multiple URLs with rate limiting and progress tracking.
        
        Args:
            urls: List of URLs to index
            force: Force reindexing even if recently indexed
        """
        indexed_urls = self.load_indexed_urls()
        pending_urls = []
        
        # Check daily limit
        if self.rate_limiter.daily_requests >= int(os.getenv('MAX_REQUESTS_PER_DAY', 200)):
            self.logger.warning(f"{Fore.YELLOW}Daily limit reached. Saving URLs for tomorrow.{Style.RESET_ALL}")
            self.save_pending_urls(urls)
            return
            
        print(f"\n{Fore.CYAN}Starting batch indexing of {len(urls)} URLs...{Style.RESET_ALL}\n")
        
        with tqdm(total=len(urls), desc="Indexing Progress", unit="url") as pbar:
            for url in urls:
                # Check if already indexed recently
                if url in indexed_urls and not self.should_reindex(url, indexed_urls[url], force):
                    self.logger.info(f"Skipping recently indexed URL: {url}")
                    pbar.update(1)
                    continue
                    
                # Check daily limit
                if self.rate_limiter.daily_requests >= int(os.getenv('MAX_REQUESTS_PER_DAY', 200)):
                    self.logger.warning("Daily limit reached, saving remaining URLs")
                    pending_urls.extend(urls[urls.index(url):])
                    break
                    
                # Request indexing
                success = self.request_indexing(url)
                
                if success:
                    indexed_urls[url] = datetime.now()
                    self.save_indexed_urls(indexed_urls)
                else:
                    pending_urls.append(url)
                    
                pbar.update(1)
                
                # Small delay between requests
                time.sleep(2)
                
        # Save any pending URLs
        if pending_urls:
            existing_pending = self.load_pending_urls()
            all_pending = list(set(existing_pending + pending_urls))
            self.save_pending_urls(all_pending)
            self.logger.info(f"Saved {len(pending_urls)} URLs for later processing")
            
        # Summary
        print(f"\n{Fore.GREEN}Indexing Complete!{Style.RESET_ALL}")
        print(f"Successfully indexed: {len(indexed_urls)}")
        print(f"Pending: {len(pending_urls)}")
        print(f"Daily requests used: {self.rate_limiter.daily_requests}/{os.getenv('MAX_REQUESTS_PER_DAY', 200)}")
        
    def get_indexing_status(self, url: str) -> Optional[Dict]:
        """
        Get the indexing status of a URL.
        
        Args:
            url: The URL to check
            
        Returns:
            Status information or None
        """
        try:
            response = self.service.urlNotifications().getMetadata(url=url).execute()
            return response
        except Exception as e:
            self.logger.error(f"Failed to get status for {url}: {str(e)}")
            return None


def main():
    """Main execution function."""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize components
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    feed_url = os.getenv('BLOGGER_RSS_FEED')
    
    if not credentials_path or not feed_url:
        print(f"{Fore.RED}Error: Missing required environment variables!{Style.RESET_ALL}")
        print("Please check your .env file")
        return
        
    # Parse blog feed
    parser = BloggerFeedParser(feed_url)
    urls = parser.get_all_post_urls()
    
    if not urls:
        print(f"{Fore.YELLOW}No URLs found in feed!{Style.RESET_ALL}")
        return
        
    print(f"{Fore.CYAN}Found {len(urls)} posts in blog feed{Style.RESET_ALL}")
    
    # Initialize indexer
    indexer = GoogleIndexer(credentials_path)
    
    # Check for pending URLs from previous run
    pending_urls = indexer.load_pending_urls()
    if pending_urls:
        print(f"{Fore.YELLOW}Found {len(pending_urls)} pending URLs from previous run{Style.RESET_ALL}")
        urls = pending_urls + urls
        
    # Remove duplicates
    urls = list(dict.fromkeys(urls))
    
    # Start batch indexing
    indexer.batch_index_urls(urls)
    

if __name__ == "__main__":
    main()
