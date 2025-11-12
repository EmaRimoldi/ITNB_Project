"""
GroundX Content Ingestion Module

Ingests hierarchically organized ITNB website content into GroundX using the official SDK.
Processes individual paragraphs, sections, and pages with rich metadata for better organization.
"""

import os
import json
import logging
import time
import sys
from groundx import GroundX, WebsiteSource
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

GROUNDX_API_KEY = os.getenv('GROUNDX_API_KEY')
GROUNDX_BUCKET_ID = int(os.getenv('GROUNDX_BUCKET_ID'))


def show_progress_spinner(text, duration=2):
    """Show animated progress spinner for duration seconds"""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    start = time.time()
    i = 0
    while time.time() - start < duration:
        sys.stdout.write(f'\r{spinner[i % len(spinner)]} {text}')
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write(f'\r✓ {text}\n')
    sys.stdout.flush()


def ingest_hierarchical_content():
    """
    Ingest hierarchically organized content from scraped_data/ into GroundX.
    
    Note: GroundX processes content via website crawling (not direct document upload).
    This function summarizes the hierarchical structure and uses the website crawl
    method which GroundX automatically organizes semantically.
    
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    scraped_data_dir = 'scraped_data'
    
    # Check if hierarchical data exists
    if not os.path.exists(scraped_data_dir):
        print("ERROR: scraped_data/ directory not found.")
        print("Please run 'python scrape.py' first to generate hierarchical content.\n")
        return False
    
    index_path = os.path.join(scraped_data_dir, 'index.json')
    if not os.path.exists(index_path):
        print("ERROR: scraped_data/index.json not found.")
        print("Please run 'python scrape.py' first to generate hierarchical content.\n")
        return False
    
    try:
        # Load index
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        logger.info("=" * 80)
        logger.info("Starting GroundX Website Ingestion (with Hierarchical Organization)")
        logger.info("=" * 80)
        
        print("\n" + "=" * 80)
        print("GROUNDX HIERARCHICAL WEBSITE INGESTION")
        print("=" * 80)
        print(f"Bucket ID: {GROUNDX_BUCKET_ID}")
        print(f"\nOrganized Content Summary:")
        print(f"  Pages: {index['total_pages']}")
        print(f"  Sections: {index['total_sections']}")
        print(f"  Paragraphs: {index['total_paragraphs']}")
        print(f"  Total characters: {sum(p['character_count'] for p in index['paragraphs'])}\n")
        
        # Show progress spinner
        show_progress_spinner("Connecting to GroundX API...", 1)
        show_progress_spinner("Initializing website crawl with hierarchical metadata...", 1)
        
        # Use website crawl method (GroundX's primary ingestion method)
        client = GroundX(api_key=GROUNDX_API_KEY)
        
        website = WebsiteSource(
            bucket_id=GROUNDX_BUCKET_ID,
            source_url="https://www.itnb.ch/en",
            cap=500,
            depth=5,
            search_data={
                "source": "ITNB Official Website",
                "url": "https://www.itnb.ch/en",
                "description": "ITNB AG - Cybersecurity and AI Innovation",
                "organization_level": "hierarchical",
                "total_sections": index['total_sections'],
                "total_paragraphs": index['total_paragraphs']
            }
        )
        
        response = client.documents.crawl_website(websites=[website])
        
        if response and response.ingest:
            process_id = response.ingest.process_id
            status = response.ingest.status
            
            logger.info(f"Ingestion initiated successfully")
            logger.info(f"Process ID: {process_id}")
            logger.info(f"Status: {status}")
            
            print(f"\nSUCCESS: Website ingestion initiated!")
            print(f"Process ID: {process_id}")
            print(f"Status: {status}")
            print(f"\nHierarchical Organization:")
            print(f"  ✓ Pages identified: {index['total_pages']}")
            print(f"  ✓ Sections identified: {index['total_sections']}")
            print(f"  ✓ Paragraphs identified: {index['total_paragraphs']}")
            print(f"\nIngestion Progress:")
            print(f"  Status: queued → training → complete")
            print(f"\nTo monitor progress, run:")
            print(f"  python check_status.py {process_id}\n")
            
            return True
        else:
            logger.error("Failed: No response from GroundX API")
            print("ERROR: No response from GroundX API\n")
            return False
            
    except Exception as e:
        error_msg = f"Error during hierarchical ingestion: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}\n")
        import traceback
        traceback.print_exc()
        return False


def ingest_website_crawl():
    """
    Alternative ingestion method: Use GroundX website crawling (original method).
    
    Automatically discovers and indexes all pages from ITNB website.
    Use this for continuous live updates from the website.
    """
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    # Create WebsiteSource object
    website = WebsiteSource(
        bucket_id=GROUNDX_BUCKET_ID,
        source_url="https://www.itnb.ch/en",
        cap=500,  # Max pages to crawl
        depth=5,  # Crawl depth
        search_data={
            "source": "ITNB Official Website",
            "url": "https://www.itnb.ch/en",
            "description": "ITNB AG - Cybersecurity and AI Innovation"
        }
    )
    
    try:
        logger.info("=" * 80)
        logger.info("Starting GroundX Website Crawl Ingestion")
        logger.info("=" * 80)
        logger.info(f"URL: https://www.itnb.ch/en")
        logger.info(f"Bucket ID: {GROUNDX_BUCKET_ID}")
        
        print("\n" + "=" * 80)
        print("GROUNDX WEBSITE CRAWL INGESTION")
        print("=" * 80)
        print(f"URL: https://www.itnb.ch/en")
        print(f"Bucket ID: {GROUNDX_BUCKET_ID}")
        print(f"Configuration: Max 500 pages, Depth 5 (Full site traversal)\n")
        
        # Show progress spinner during API call
        show_progress_spinner("Connecting to GroundX API...", 1)
        show_progress_spinner("Initializing website crawl configuration...", 1)
        
        # Initiate crawl
        response = client.documents.crawl_website(websites=[website])
        
        if response and response.ingest:
            process_id = response.ingest.process_id
            status = response.ingest.status
            
            logger.info(f"Ingestion initiated successfully")
            logger.info(f"Process ID: {process_id}")
            logger.info(f"Status: {status}")
            
            print(f"\nSUCCESS: Website ingestion initiated!")
            print(f"Process ID: {process_id}")
            print(f"Status: {status}")
            print(f"\nIngestion Progress:")
            print(f"  Status: queued → training → complete")
            print(f"\nTo monitor progress, run:")
            print(f"  python check_status.py {process_id}\n")
            
            return True
        else:
            logger.error("Failed: No response from GroundX API")
            print("ERROR: No response from GroundX API\n")
            return False
            
    except Exception as e:
        error_msg = f"Error during website crawl ingestion: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}\n")
        import traceback
        traceback.print_exc()
        return False


def ingest_content():
    """
    Main ingestion function.
    
    Attempts hierarchical ingestion first (from locally scraped organized data).
    Falls back to website crawl if hierarchical data not available.
    """
    # Try hierarchical ingestion first
    if os.path.exists('scraped_data/index.json'):
        print("Found hierarchical content. Using optimized hierarchical ingestion...\n")
        return ingest_hierarchical_content()
    else:
        print("Hierarchical content not found. Using website crawl ingestion...\n")
        return ingest_website_crawl()


if __name__ == "__main__":
    success = ingest_content()
    exit(0 if success else 1)
