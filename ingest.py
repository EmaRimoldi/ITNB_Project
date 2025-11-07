"""
GroundX Content Ingestion Module

Ingests the ITNB website content into GroundX using the official SDK.
Supports both website crawling and document ingestion with comprehensive logging.
"""

import os
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


def ingest_content():
    """
    Crawl and ingest the ITNB website into GroundX.
    
    Uses the GroundX SDK to crawl https://www.itnb.ch/en and ingest content
    into the specified bucket. Logs success/failure for each operation.
    
    Returns:
        bool: True if ingestion was successfully initiated, False otherwise
    """
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    # Create WebsiteSource object
    website = WebsiteSource(
        bucket_id=GROUNDX_BUCKET_ID,
        source_url="https://www.itnb.ch/en",
        cap=500,  # Max pages to crawl (increased for deeper exploration)
        depth=5,  # Crawl depth (max allowed by subscription plan)
        search_data={
            "source": "ITNB Official Website",
            "url": "https://www.itnb.ch/en",
            "description": "ITNB AG - Cybersecurity and AI Innovation"
        }
    )
    
    try:
        logger.info("=" * 80)
        logger.info("Starting GroundX Website Ingestion")
        logger.info("=" * 80)
        logger.info(f"URL: https://www.itnb.ch/en")
        logger.info(f"Bucket ID: {GROUNDX_BUCKET_ID}")
        
        print("\n" + "=" * 80)
        print("GROUNDX WEBSITE INGESTION")
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
        error_msg = f"Error during ingestion: {str(e)}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = ingest_content()
    exit(0 if success else 1)
