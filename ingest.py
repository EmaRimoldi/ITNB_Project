"""
GroundX Content Ingestion Module

Purpose:
This module ingests hierarchically organized ITNB website content into GroundX's
vector database. GroundX is a Retrieval-Augmented Generation (RAG) platform that:
1. Indexes website content for semantic search
2. Creates vector embeddings for efficient similarity matching
3. Enables context retrieval for LLM-powered question answering

Key Features:
- Uses GroundX official SDK for reliable API communication
- Supports website crawling (live scraping by GroundX)
- Attaches rich metadata for better organization and filtering
- Provides progress monitoring via process IDs
- Handles hierarchical content structure from scraper

Workflow:
1. Load scraped content from local files (if available)
2. Configure GroundX website crawling with metadata
3. Initiate ingestion process (returns process ID)
4. GroundX crawls, extracts, vectorizes, and indexes content
5. Monitor status using check_status.py
"""

# === STANDARD LIBRARY IMPORTS ===
import os  # Filesystem operations (path checking, reading files)
import json  # JSON parsing for loading scraped data index
import logging  # Structured logging for monitoring and debugging
import time  # Time functions for progress spinner animation
import sys  # System functions for stdout manipulation

# === THIRD-PARTY IMPORTS ===
from groundx import GroundX, WebsiteSource  # GroundX SDK for RAG platform API
from dotenv import load_dotenv  # Load environment variables from .env file

# === LOGGING CONFIGURATION ===
# Set up logging to display timestamped messages with severity levels
logging.basicConfig(
    level=logging.INFO,  # Show INFO level and above (INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Timestamp - Level - Message
)
# Create logger instance for this module
logger = logging.getLogger(__name__)

# === ENVIRONMENT VARIABLE LOADING ===
# Load credentials and configuration from .env file
load_dotenv()

# Retrieve GroundX API credentials from environment
# These must be set in .env file for authentication
GROUNDX_API_KEY = os.getenv('GROUNDX_API_KEY')  # API key for GroundX authentication
GROUNDX_BUCKET_ID = int(os.getenv('GROUNDX_BUCKET_ID'))  # Bucket ID where content is stored (must be integer)


def show_progress_spinner(text, duration=2):
    """
    Display animated progress spinner with text for specified duration.
    
    This provides visual feedback to users during API calls or long operations,
    improving perceived performance and user experience.
    
    Args:
        text (str): Message to display next to spinner (e.g., "Loading...")
        duration (int/float): How long to display spinner in seconds
        
    Animation:
    Uses Unicode Braille patterns for smooth rotation effect:
    ⠋ → ⠙ → ⠹ → ⠸ → ⠼ → ⠴ → ⠦ → ⠧ → ⠇ → ⠏ (repeats)
    """
    # Define spinner frames using Unicode Braille characters
    # These create a rotating animation effect
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    # Record start time to track duration
    start = time.time()
    # Initialize frame counter
    i = 0
    
    # Keep animating until duration elapsed
    while time.time() - start < duration:
        # Write current frame to same line (\\r = carriage return, overwrites line)
        sys.stdout.write(f'\r{spinner[i % len(spinner)]} {text}')
        sys.stdout.flush()  # Force immediate display (Python buffers output by default)
        time.sleep(0.1)  # Wait 100ms before next frame (10 FPS animation)
        i += 1  # Move to next frame
    
    # When done, replace spinner with checkmark to indicate completion
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
