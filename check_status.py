"""
Check the status of an ingestion process with visual progress indicator
"""
import os
import sys
import time
from groundx import GroundX
from dotenv import load_dotenv

load_dotenv()

GROUNDX_API_KEY = os.getenv('GROUNDX_API_KEY')


def draw_progress_bar(status, completed=0, total=None):
    """Draw a visual progress bar based on status"""
    status_stages = {
        'queued': 0,
        'training': 50,
        'complete': 100
    }
    
    progress = status_stages.get(status, 0)
    bar_length = 40
    filled = int(bar_length * progress / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    if status == 'complete' and total:
        return f"[{bar}] {progress}% - Complete ({total} documents indexed)"
    else:
        return f"[{bar}] {progress}% - {status.upper()}"


def check_status(process_id):
    """Check the status of an ingestion process"""
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    try:
        response = client.documents.get_processing_status_by_id(process_id=process_id)
        
        if response and response.ingest:
            status = response.ingest.status
            completed_count = 0
            
            # Try to extract completion count
            if hasattr(response.ingest, 'progress') and response.ingest.progress:
                progress = response.ingest.progress
                if hasattr(progress, 'complete') and progress.complete:
                    complete = progress.complete
                    if hasattr(complete, 'total'):
                        completed_count = complete.total
            
            print(f"\n" + "=" * 80)
            print("INGESTION PROCESS STATUS")
            print("=" * 80)
            print(f"Process ID: {process_id}")
            print(f"Status: {status.upper()}")
            print(draw_progress_bar(status, completed_count))
            
            if completed_count > 0:
                print(f"Documents Indexed: {completed_count}")
            
            if status == 'complete':
                print(f"\n✓ Ingestion Complete! Documents are ready for search.")
            elif status == 'training':
                print(f"\n⏳ Processing in progress... Check again in a few seconds.")
            elif status == 'queued':
                print(f"\n⏳ Waiting to start processing...")
            
            print("=" * 80 + "\n")
            return response
        else:
            print("✗ No response from API")
            return None
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def check_status_continuous(process_id, max_attempts=60):
    """Continuously check status until complete or max attempts"""
    attempt = 0
    while attempt < max_attempts:
        print(f"Check {attempt + 1}/{max_attempts}...")
        response = check_status(process_id)
        
        if response and response.ingest and response.ingest.status == 'complete':
            print("✓ Ingestion completed successfully!")
            return True
        
        attempt += 1
        if attempt < max_attempts:
            print("Waiting 5 seconds before next check...\n")
            time.sleep(5)
    
    print("✗ Max attempts reached. Process may still be running.")
    return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_id = sys.argv[1]
        
        # Check if --continuous flag is provided
        continuous = '--continuous' in sys.argv
        
        if continuous:
            check_status_continuous(process_id)
        else:
            check_status(process_id)
    else:
        print("Usage: python check_status.py <process_id> [--continuous]")
        print("\nExamples:")
        print("  python check_status.py daa8e33b-43db-40e3-9f27-b12063f21c53")
        print("  python check_status.py daa8e33b-43db-40e3-9f27-b12063f21c53 --continuous")
