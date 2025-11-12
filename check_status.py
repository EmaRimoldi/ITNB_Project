"""
GroundX Ingestion Status Monitoring Module

Purpose:
This module monitors the progress of GroundX ingestion processes using visual
progress indicators. After running ingest.py, use this tool to track when
content indexing is complete and ready for searching.

Key Features:
- Check ingestion status by process ID
- Visual progress bar with status stages (queued → training → complete)
- Continuous monitoring mode (auto-refresh until complete)
- Document count tracking
- User-friendly formatted output

Ingestion Stages:
1. queued: Waiting in GroundX processing queue
2. training: Extracting text, creating embeddings, indexing
3. complete: Ready for semantic search in chat.py

Usage Examples:
  python check_status.py <process_id>                    # Single status check
  python check_status.py <process_id> --continuous       # Auto-refresh every 5s
"""

# === STANDARD LIBRARY IMPORTS ===
import os  # For environment variable access
import sys  # For command-line argument parsing (sys.argv)
import time  # For sleep delays in continuous monitoring

# === THIRD-PARTY IMPORTS ===
from groundx import GroundX  # GroundX SDK for API communication
from dotenv import load_dotenv  # Load .env configuration

# === ENVIRONMENT CONFIGURATION ===
# Load environment variables from .env file
load_dotenv()

# Retrieve GroundX API key for authentication
GROUNDX_API_KEY = os.getenv('GROUNDX_API_KEY')


def draw_progress_bar(status, completed=0, total=None):
    """
    Draw a visual ASCII progress bar based on ingestion status.
    
    This function creates a user-friendly visual representation of the
    ingestion process, making it easy to understand progress at a glance.
    
    Args:
        status (str): Current status ('queued', 'training', or 'complete')
        completed (int): Number of documents successfully indexed (optional)
        total (int/None): Total documents to index (optional, for percentage calc)
        
    Returns:
        str: Formatted progress bar string with percentage and status
        
    Example Output:
        [████████████████████░░░░░░░░░░░░░░░░░░░░] 50% - TRAINING
        [████████████████████████████████████████] 100% - Complete (42 documents indexed)
    """
    # Map status strings to percentage completion
    # This provides consistent progress visualization across different stages
    status_stages = {
        'queued': 0,      # 0% - Just added to queue, not started yet
        'training': 50,   # 50% - Processing: extracting text, creating embeddings
        'complete': 100   # 100% - Fully indexed and ready for search
    }
    
    # Get progress percentage for current status (default to 0 if unknown status)
    progress = status_stages.get(status, 0)
    
    # Configure progress bar visual dimensions
    bar_length = 40  # Total width of progress bar in characters
    
    # Calculate how many characters should be filled
    filled = int(bar_length * progress / 100)
    
    # Build progress bar using Unicode block characters
    # █ = filled section (dark block)
    # ░ = unfilled section (light block)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    # Format output based on completion status
    if status == 'complete' and total:
        # Show document count when complete
        return f"[{bar}] {progress}% - Complete ({total} documents indexed)"
    else:
        # Show status name for in-progress stages
        return f"[{bar}] {progress}% - {status.upper()}"


def check_status(process_id):
    """
    Check the current status of a GroundX ingestion process.
    
    This function queries the GroundX API to retrieve the latest status
    of an ingestion process and displays it with a visual progress bar.
    
    Args:
        process_id (str): UUID of the ingestion process (returned by ingest.py)
        
    Returns:
        response object: GroundX API response with status details, or None on error
        
    Process Flow:
    1. Initialize GroundX client with API key
    2. Query API for process status by ID
    3. Parse response to extract status and document count
    4. Display formatted status with progress bar
    5. Provide user-friendly status message
    """
    # Initialize GroundX SDK client for API communication
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    try:
        # === API CALL ===
        # Query GroundX for ingestion process status
        response = client.documents.get_processing_status_by_id(process_id=process_id)
        
        # === RESPONSE VALIDATION ===
        # Check if API returned valid response with ingestion data
        if response and response.ingest:
            # Extract status from response (queued/training/complete)
            status = response.ingest.status
            # Initialize document counter (will try to extract from response)
            completed_count = 0
            
            # === EXTRACT DOCUMENT COUNT ===
            # Try to extract number of documents indexed (nested structure varies by API version)
            if hasattr(response.ingest, 'progress') and response.ingest.progress:
                progress = response.ingest.progress
                if hasattr(progress, 'complete') and progress.complete:
                    complete = progress.complete
                    if hasattr(complete, 'total'):
                        completed_count = complete.total
            
            # === DISPLAY STATUS ===
            # Print formatted status information with visual separator
            print(f"\n" + "=" * 80)
            print("INGESTION PROCESS STATUS")
            print("=" * 80)
            print(f"Process ID: {process_id}")  # Show UUID for reference
            print(f"Status: {status.upper()}")  # Show status in uppercase for emphasis
            print(draw_progress_bar(status, completed_count))  # Visual progress bar
            
            # Show document count if available
            if completed_count > 0:
                print(f"Documents Indexed: {completed_count}")
            
            # === STATUS-SPECIFIC MESSAGES ===
            # Provide context-appropriate message based on current status
            if status == 'complete':
                # Success message when indexing is done
                print(f"\n✓ Ingestion Complete! Documents are ready for search.")
            elif status == 'training':
                # In-progress message with guidance to wait
                print(f"\n⏳ Processing in progress... Check again in a few seconds.")
            elif status == 'queued':
                # Waiting message when process hasn't started yet
                print(f"\n⏳ Waiting to start processing...")
            
            # Display closing separator
            print("=" * 80 + "\n")
            return response  # Return response for further processing if needed
        else:
            # API returned response but without expected ingestion data
            print("✗ No response from API")
            return None
            
    except Exception as e:
        # Catch any API errors or network issues
        print(f"✗ Error: {str(e)}")
        return None


def check_status_continuous(process_id, max_attempts=60):
    """
    Continuously monitor ingestion status until completion or timeout.
    
    This function automatically checks status every 5 seconds, providing
    real-time updates without manual re-running. Useful when waiting for
    long-running ingestion processes to complete.
    
    Args:
        process_id (str): UUID of the ingestion process to monitor
        max_attempts (int): Maximum number of status checks before giving up (default: 60)
                           With 5s delay, max_attempts=60 means 5 minutes total
        
    Returns:
        bool: True if ingestion completed successfully, False if timed out or failed
        
    Workflow:
    1. Check status using check_status() function
    2. If complete, return success
    3. If not complete, wait 5 seconds
    4. Repeat until complete or max_attempts reached
    """
    # Initialize attempt counter
    attempt = 0
    
    # Keep checking until max attempts reached
    while attempt < max_attempts:
        # Display current attempt number (helps user track progress)
        print(f"Check {attempt + 1}/{max_attempts}...")
        
        # Query current ingestion status
        response = check_status(process_id)
        
        # === CHECK FOR COMPLETION ===
        # If status is 'complete', ingestion is done successfully
        if response and response.ingest and response.ingest.status == 'complete':
            print("✓ Ingestion completed successfully!")
            return True  # Exit with success
        
        # Increment attempt counter
        attempt += 1
        
        # === WAIT BEFORE NEXT CHECK ===
        # Don't check immediately - wait 5 seconds to avoid spamming API
        if attempt < max_attempts:
            print("Waiting 5 seconds before next check...\n")
            time.sleep(5)  # Delay 5 seconds
    
    # === TIMEOUT REACHED ===
    # Max attempts exhausted without completion
    print("✗ Max attempts reached. Process may still be running.")
    print("Try checking manually later or increase max_attempts.")
    return False  # Exit with failure (timeout)


# === PROGRAM ENTRY POINT ===
# This block runs when script is executed directly (not imported)
if __name__ == "__main__":
    # === COMMAND-LINE ARGUMENT PARSING ===
    # Check if user provided process_id as command-line argument
    if len(sys.argv) > 1:
        # Get process_id from first command-line argument
        process_id = sys.argv[1]
        
        # Check if --continuous flag is provided (enables auto-refresh mode)
        continuous = '--continuous' in sys.argv
        
        # === EXECUTION MODE SELECTION ===
        if continuous:
            # Continuous monitoring mode (auto-refresh every 5s)
            check_status_continuous(process_id)
        else:
            # Single check mode (check once and exit)
            check_status(process_id)
    else:
        # === USAGE HELP ===
        # No arguments provided - show usage instructions
        print("Usage: python check_status.py <process_id> [--continuous]")
        print("\nExamples:")
        print("  python check_status.py daa8e33b-43db-40e3-9f27-b12063f21c53")
        print("  python check_status.py daa8e33b-43db-40e3-9f27-b12063f21c53 --continuous")
        print("\nFlags:")
        print("  --continuous    Auto-refresh every 5 seconds until complete")
        print("\nNote:")
        print("  Process IDs are returned by ingest.py after initiating ingestion.")
