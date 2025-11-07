"""
ITNB Website Content Scraping Module

Scrapes textual content from https://www.itnb.ch/en and stores it locally.
Uses BeautifulSoup for HTML parsing and text extraction.

Note: The assessment recommends using crawl4ai, but due to Python 3.14 
compatibility issues with lxml dependencies, BeautifulSoup is used instead,
achieving the same outcome: extracting and cleaning textual content.
"""

import json
import os
import requests
from bs4 import BeautifulSoup


def scrape_itnb():
    """
    Scrape ITNB website and extract textual content.
    
    Fetches https://www.itnb.ch/en, removes scripts/styles, cleans whitespace,
    and saves the structured data locally as JSON.
    """
    url = "https://www.itnb.ch/en"
    
    print(f"Scraping {url}...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract and clean text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Structure data
        cleaned_data = [{
            'title': 'ITNB Website Content',
            'content': text,
            'url': url,
            'source': 'https://www.itnb.ch/en'
        }]
        
        # Save locally
        os.makedirs('scraped_data', exist_ok=True)
        output_file = 'scraped_data/itnb_content.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
        print(f"SUCCESS: Scraped and saved to {output_file}")
        print(f"Content size: {len(text)} characters")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to scrape {url}: {str(e)}")
        return False


if __name__ == "__main__":
    success = scrape_itnb()
    exit(0 if success else 1)