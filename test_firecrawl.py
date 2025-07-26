#!/usr/bin/env python3
"""Test Firecrawl search functionality"""

import os
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load environment variables from .env.local
    project_root = Path(__file__).parent
    env_path = project_root / ".env.local"
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed")

try:
    from firecrawl import FirecrawlApp
except ImportError:
    print("Error: firecrawl package not found. Please install with: pip install firecrawl-py")
    exit(1)

# Initialize Firecrawl
firecrawl = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_KEY", ""),
    api_url=os.getenv("FIRECRAWL_BASE_URL")
)

print(f"Firecrawl API Key configured: {'Yes' if os.getenv('FIRECRAWL_KEY') else 'No'}")

# Test a simple search
try:
    result = firecrawl.search(query="Tesla stock", limit=1)
    print(f"Search result type: {type(result)}")
    print(f"Search success: {result.success}")
    
    if result.data:
        first_url = result.data[0]["url"]
        print(f"Testing scrape for: {first_url}")
        
        # Test basic scraping
        try:
            scrape_result = firecrawl.scrape_url(first_url)
            print(f"Scrape result type: {type(scrape_result)}")
            print(f"Scrape result attributes: {[attr for attr in dir(scrape_result) if not attr.startswith('_')]}")
            
            if hasattr(scrape_result, 'markdown'):
                print(f"Markdown content length: {len(scrape_result.markdown) if scrape_result.markdown else 0}")
                if scrape_result.markdown:
                    print(f"First 200 chars: {scrape_result.markdown[:200]}")
            
            if hasattr(scrape_result, 'content'):
                print(f"Content length: {len(scrape_result.content) if scrape_result.content else 0}")
                
            if hasattr(scrape_result, 'model_dump'):
                dump = scrape_result.model_dump()
                print(f"Model dump keys: {dump.keys()}")
                
        except Exception as scrape_error:
            print(f"Basic scrape failed: {scrape_error}")
            
            # Try with a simpler URL
            simple_url = "https://www.tesla.com/"
            print(f"Trying simpler URL: {simple_url}")
            try:
                scrape_result = firecrawl.scrape_url(simple_url)
                print(f"Simple scrape success!")
                print(f"Content available: {hasattr(scrape_result, 'content') and bool(scrape_result.content)}")
                print(f"Markdown available: {hasattr(scrape_result, 'markdown') and bool(scrape_result.markdown)}")
            except Exception as simple_error:
                print(f"Simple scrape also failed: {simple_error}")
        
except Exception as e:
    print(f"Error during search: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
