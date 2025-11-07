"""
GroundX Chat Interface Module

Provides an interactive command-line Q&A interface for querying ingested ITNB content.
Demonstrates RAG capabilities by retrieving and displaying contextual answers with sources.
"""

import os
import logging
import sys
from groundx import GroundX
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


def search_and_display(query):
    """
    Search GroundX bucket and display results in professional format.
    
    Args:
        query (str): User's question or search query
        
    Returns:
        bool: True if search succeeded with results, False otherwise
    """
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    try:
        logger.info(f"Query: {query}")
        
        # Search the bucket
        response = client.search.content(
            id=GROUNDX_BUCKET_ID,
            query=query
        )
        
        if response and response.search:
            search_data = response.search
            
            # Display results header
            print("\n" + "=" * 80)
            print("SEARCH RESULTS")
            print("=" * 80)
            
            # Display metadata
            print(f"\nResults Found: {search_data.count}")
            print(f"Relevance Score: {search_data.score:.2f}")
            
            # Display answer (LLM-optimized text)
            print("\n" + "-" * 80)
            print("ANSWER")
            print("-" * 80)
            if search_data.text:
                answer_text = search_data.text
                # Limit output for readability
                if len(answer_text) > 1200:
                    print(answer_text[:1200] + "\n[... truncated for display]")
                else:
                    print(answer_text)
            else:
                print("(No results)")
            
            # Display top result with source information
            if search_data.results:
                top_result = search_data.results[0]
                print("\n" + "-" * 80)
                print("TOP RESULT")
                print("-" * 80)
                print(f"Score: {top_result.score:.2f}")
                if top_result.source_url:
                    print(f"Source: {top_result.source_url}")
                    logger.info(f"Source: {top_result.source_url}")
                
                logger.info(f"Search successful - {search_data.count} results found")
                print("\n" + "=" * 80 + "\n")
                return True
            
            return True
        else:
            print("\nNo results found for this query.")
            logger.warning(f"No results found for query: {query}")
            return False
            
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(f"\nError: {error_msg}")
        logger.error(error_msg)
        return False


def display_header():
    """Display professional welcome header."""
    print("\n" + "=" * 80)
    print("ITNB KNOWLEDGE BASE - QUESTION & ANSWER INTERFACE")
    print("=" * 80)
    print("\nThis interface allows you to query the ingested ITNB website content.")
    print("Powered by GroundX RAG (Retrieval-Augmented Generation).\n")
    print("Commands:")
    print("  - Type your question and press Enter to search")
    print("  - Type 'exit', 'quit', or 'q' to exit")
    print("  - Press Ctrl+C to interrupt at any time\n")
    print("=" * 80 + "\n")


def main():
    """Main interactive chat loop."""
    display_header()
    logger.info("Chat session started")
    
    query_count = 0
    
    while True:
        try:
            # Get user input
            question = input("Enter your question: ").strip()
            
            if not question:
                print("Please enter a valid question.\n")
                continue
            
            # Check for exit commands
            if question.lower() in ['exit', 'quit', 'q']:
                print("\nSession ended. Thank you for using ITNB Knowledge Base.\n")
                logger.info(f"Chat session ended after {query_count} queries")
                break
            
            # Process query
            query_count += 1
            print(f"\nProcessing query {query_count}...\n")
            search_and_display(question)
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted by user. Goodbye.\n")
            logger.info(f"Session interrupted after {query_count} queries")
            break
        except EOFError:
            # Handle end of input (e.g., when piping input)
            print("\nEnd of input reached. Goodbye.\n")
            logger.info(f"Session ended (EOF) after {query_count} queries")
            break
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\nError: {error_msg}\n")
            logger.error(error_msg)


if __name__ == "__main__":
    main()
