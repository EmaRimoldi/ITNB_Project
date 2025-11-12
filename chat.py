"""
GroundX Chat Interface Module

Provides an interactive command-line Q&A interface for querying ingested ITNB content.
Demonstrates RAG capabilities by retrieving contextual answers and generating LLM responses.
"""

# Standard library imports for OS operations, logging, system functions
import os
import logging
import sys

# Third-party imports
import requests  # HTTP client for making API calls to LLM endpoint
from groundx import GroundX  # GroundX SDK for RAG (Retrieval-Augmented Generation)
from dotenv import load_dotenv  # Load environment variables from .env file

# Configure logging system to track application behavior and errors
# INFO level captures general operational messages
# Format includes timestamp, severity level, and message content
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)  # Create logger instance for this module

# Load environment variables from .env file into os.environ
# This keeps sensitive credentials out of source code
load_dotenv()

# Retrieve GroundX API credentials from environment variables
# These are used to authenticate with GroundX RAG service
GROUNDX_API_KEY = os.getenv('GROUNDX_API_KEY')  # API key for GroundX authentication
GROUNDX_BUCKET_ID = int(os.getenv('GROUNDX_BUCKET_ID'))  # Bucket ID where documents are stored

# LLM Configuration (as specified in ITNB assessment requirements)
# These credentials connect to the custom OpenAI-compatible inference endpoint
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'inference-llama4-maverick')  # Model name with fallback default
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://maas.ai-2.kvant.cloud')  # API base URL
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # API key for LLM authentication


def generate_llm_response(context, query):
    """
    Generate LLM completion using custom OpenAI-compatible endpoint.
    
    This function implements the "Generation" phase of RAG:
    1. Takes retrieved context from GroundX
    2. Constructs a prompt with system instructions and user query
    3. Calls custom LLM API to generate human-like answer
    
    Args:
        context (str): Retrieved context from GroundX search (relevant document chunks)
        query (str): User's original question
        
    Returns:
        str: LLM-generated response or None on error
    """
    try:
        # Prepare HTTP headers for API authentication
        # Bearer token authentication is standard for OpenAI-compatible APIs
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",  # Authentication token
            "Content-Type": "application/json"  # Specify JSON payload format
        }
        
        # Construct the API request payload following OpenAI chat completions format
        payload = {
            "model": OPENAI_MODEL_NAME,  # Specify which LLM model to use
            "messages": [  # Array of messages forming the conversation
                {
                    "role": "system",  # System message sets behavior/instructions for LLM
                    "content": f"""You are a helpful assistant that answers questions using the provided context.
Use the following information to answer the user's question accurately:

===
{context}
===

Provide a clear, concise answer based only on the information above. If the context doesn't contain enough information, say so."""
                    # System prompt instructs LLM to use only provided context (prevents hallucination)
                },
                {
                    "role": "user",  # User message contains the actual question
                    "content": query  # The question user asked
                }
            ],
            "temperature": 0.7,  # Controls randomness (0.7 = balanced creativity and consistency)
            "max_tokens": 500  # Limit response length to 500 tokens (~375 words)
        }
        
        # Log which LLM and endpoint are being called for debugging/monitoring
        logger.info(f"Calling LLM: {OPENAI_MODEL_NAME} at {OPENAI_API_BASE}")
        
        # Make HTTP POST request to LLM API endpoint
        # Timeout prevents hanging if API is slow or unreachable
        response = requests.post(
            f"{OPENAI_API_BASE}/v1/chat/completions",  # Standard OpenAI-compatible endpoint
            headers=headers,  # Include authentication headers
            json=payload,  # Send payload as JSON
            timeout=30  # Wait maximum 30 seconds for response
        )
        
        # Check if API call was successful (HTTP 200 OK)
        if response.status_code == 200:
            # Parse JSON response from API
            result = response.json()
            # Extract generated text from first choice's message content
            # choices[0] = top-ranked response from model
            return result['choices'][0]['message']['content']
        else:
            # Log error if API returned non-200 status code
            # Include both status code and error message for debugging
            logger.error(f"LLM API error: {response.status_code} - {response.text}")
            return None  # Return None to indicate failure
            
    except Exception as e:
        # Catch any unexpected errors (network issues, JSON parsing errors, etc.)
        logger.error(f"Error generating LLM response: {str(e)}")
        return None  # Return None to indicate failure


def search_and_display(query):
    """
    Execute the complete RAG pipeline: Retrieve context from GroundX, then Generate LLM response.
    
    This is the main orchestration function implementing the 2-stage RAG architecture:
    1. Retrieval Stage: Query GroundX vector database for semantically relevant documents
    2. Generation Stage: Use LLM to generate natural language answer from retrieved context
    
    Args:
        query (str): User's natural language question or search query
        
    Returns:
        bool: True if search and LLM generation succeeded, False if no results or errors occurred
    """
    # Initialize GroundX SDK client with API authentication
    # This client manages all communication with the GroundX RAG platform
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    try:
        # Log the user's query for monitoring and debugging
        logger.info(f"Query: {query}")
        
        # === RETRIEVAL STAGE ===
        # Execute semantic search against the GroundX knowledge base
        # This returns document chunks most relevant to the user's query
        response = client.search.content(
            id=GROUNDX_BUCKET_ID,  # Target specific bucket containing ITNB website content
            query=query  # User's natural language question
        )
        
        # Validate that API returned a response with search results
        if response and response.search:
            # Extract search results from API response
            search_data = response.search
            
            # === VALIDATION: Check for empty results ===
            # If no documents match the query, inform user that topic is not in knowledge base
            if not search_data.results or search_data.count == 0:
                # Display formatted "no results" message to user
                print("\n" + "=" * 80)  # Visual separator line
                print("❌ NO INFORMATION FOUND")
                print("=" * 80)
                print("\nSorry, this information is not present on the ITNB website.")
                print("Please try rephrasing your question or ask about different topics.\n")
                print("=" * 80 + "\n")
                # Log warning for analytics/debugging
                logger.warning(f"No results found for query: {query}")
                return False  # Indicate search failure
            
            # === VALIDATION: Check relevance score ===
            # Relevance score measures semantic similarity between query and documents
            # Scores below 50 indicate poor match (likely off-topic or out-of-scope question)
            if search_data.score < 50:
                # Warn user that results may not be accurate due to low relevance
                print("\n" + "=" * 80)
                print("⚠️  LOW RELEVANCE")
                print("=" * 80)
                print("\nThe information found has low relevance to your question.")
                print("This content might not be present on the ITNB website.")
                print("Please try asking something else.\n")
                print("=" * 80 + "\n")
                # Log warning with actual score for threshold tuning
                logger.warning(f"Low relevance score ({search_data.score:.2f}) for query: {query}")
                return False  # Reject low-quality results
            
            # === CONTEXT EXTRACTION ===
            # Extract the text content from search results to use as LLM context
            # This text contains the relevant information needed to answer the question
            context = search_data.text if search_data.text else ""
            
            # === GENERATION STAGE ===
            # Call custom LLM endpoint to generate human-like answer using retrieved context
            # The LLM will synthesize information from context into a coherent response
            llm_response = generate_llm_response(context, query)
            
            # === DISPLAY RESULTS ===
            # Print formatted answer header
            print("\n" + "=" * 80)
            print("✅ ANSWER")
            print("=" * 80)
            
            # Display the generated answer to the user
            print("")  # Empty line for readability
            if llm_response:
                # Successfully generated LLM response - display it
                print(llm_response)
            elif context:
                # Fallback: If LLM generation failed, show raw retrieved context
                # This ensures user still gets some information even if generation fails
                logger.warning("LLM generation failed, showing raw context")
                # Truncate very long context to avoid overwhelming user
                if len(context) > 1500:
                    print(context[:1500] + "\n\n[... answer truncated for readability ...]")
                else:
                    print(context)
            else:
                # Neither LLM response nor context available - inform user
                print("No detailed answer available.")
            
            # === DISPLAY METADATA ===
            # Show additional information about search results (score, source URL, etc.)
            if search_data.results:
                # Get the top-ranked result (most relevant document)
                top_result = search_data.results[0]
                # Display metadata separator
                print("\n" + "-" * 80)
                # Show relevance score (helps user judge answer quality)
                print(f"📊 Relevance Score: {search_data.score:.2f}")
                # Show total number of matching documents found
                print(f"📄 Results Found: {search_data.count}")
                # Display source URL if available (allows user to verify information)
                if top_result.source_url:
                    print(f"🔗 Source: {top_result.source_url}")
                    logger.info(f"Source: {top_result.source_url}")
                
                # Log successful search operation for monitoring
                logger.info(f"Search successful - {search_data.count} results, score: {search_data.score:.2f}")
            
            # Display closing separator
            print("=" * 80 + "\n")
            return True  # Indicate successful search and generation
        else:
            # API returned response but without search results (unexpected situation)
            print("\n" + "=" * 80)
            print("❌ NO INFORMATION FOUND")
            print("=" * 80)
            print("\nThis information is not present on the ITNB website.")
            print("Please try asking about different topics.\n")
            print("=" * 80 + "\n")
            # Log warning for debugging API response issues
            logger.warning(f"No response from GroundX for query: {query}")
            return False  # Indicate search failure
            
    except Exception as e:
        # Catch any unexpected errors (network issues, API errors, etc.)
        error_msg = f"Search error: {str(e)}"
        # Display user-friendly error message
        print(f"\n❌ Error: {error_msg}\n")
        # Log detailed error for debugging
        logger.error(error_msg)
        return False  # Indicate search failure


def display_header():
    """
    Display professional welcome header and usage instructions.
    
    This function prints a formatted welcome message when the chatbot starts,
    including:
    - Application title and branding
    - Brief description of capabilities
    - Available commands (how to use the chatbot)
    - Example questions to help users get started
    """
    # Display top border with visual emphasis
    print("\n" + "=" * 80)
    # Main title with emoji icon for visual appeal
    print("🤖 ITNB KNOWLEDGE BASE - Q&A CHATBOT")
    print("=" * 80)
    
    # Brief description of chatbot's purpose
    print("\nAsk me anything about ITNB!")
    # Technical credit: Explain the underlying technology (RAG = Retrieval-Augmented Generation)
    print("Powered by GroundX RAG (Retrieval-Augmented Generation).\n")
    
    # === COMMANDS SECTION ===
    # Explain how to interact with the chatbot
    print("Commands:")
    # Primary action: How to ask a question
    print("  💬 Type your question and press Enter")
    # Exit commands: Multiple options for user convenience
    print("  🚪 Type 'exit', 'quit', or 'q' to quit")
    # Emergency interrupt: Keyboard shortcut for immediate stop
    print("  ⚡ Press Ctrl+C to interrupt at any time\n")
    
    # === EXAMPLES SECTION ===
    # Provide sample questions to demonstrate capabilities and guide users
    print("Examples:")
    print("  - What is ITNB?")  # General company information
    print("  - Tell me about Sovereign Cloud")  # Specific product/service
    print("  - What services does ITNB offer?")  # Service overview
    print("  - Who are the cybersecurity experts at ITNB?\n")  # Team/people information
    
    # Display bottom border
    print("=" * 80 + "\n")


def main():
    """
    Main interactive chat loop - the entry point for the chatbot application.
    
    This function implements the interactive command-line interface where users
    can continuously ask questions until they decide to exit. It handles:
    - Welcome message display
    - User input collection
    - Query processing and response generation
    - Exit conditions and error handling
    - Session statistics tracking
    """
    # Display welcome header with instructions when chatbot starts
    display_header()
    # Log session start for monitoring and analytics
    logger.info("Chat session started")
    
    # Track number of questions asked during this session (for statistics)
    query_count = 0
    
    # === MAIN INTERACTIVE LOOP ===
    # Continue running until user explicitly exits or interrupts
    while True:
        try:
            # === USER INPUT ===
            # Get user's question from command line
            # .strip() removes leading/trailing whitespace for cleaner processing
            question = input("💬 You: ").strip()
            
            # === VALIDATION: Check for empty input ===
            # If user just pressed Enter without typing, prompt them again
            if not question:
                print("⚠️  Please enter a valid question.\n")
                continue  # Skip to next iteration of loop
            
            # === EXIT CONDITION: Check for quit commands ===
            # Allow multiple exit phrases for user convenience
            # .lower() makes check case-insensitive (EXIT, exit, Exit all work)
            if question.lower() in ['exit', 'quit', 'q']:
                # Display farewell message with session statistics
                print("\n" + "=" * 80)
                print(f"👋 Session ended. You asked {query_count} questions.")
                print("Thank you for using ITNB Knowledge Base!")
                print("=" * 80 + "\n")
                # Log session end with statistics for analytics
                logger.info(f"Chat session ended after {query_count} queries")
                break  # Exit the while loop, ending program
            
            # === PROCESS QUERY ===
            # Increment query counter for this session
            query_count += 1
            # Display search indicator with query number (helps user track conversation)
            print(f"\n🔍 Searching... (Query #{query_count})")
            # Execute the RAG pipeline: retrieve context and generate answer
            search_and_display(question)
            
        except KeyboardInterrupt:
            # === INTERRUPT HANDLING ===
            # User pressed Ctrl+C to forcefully stop the program
            # Provide graceful exit with statistics
            print("\n\n" + "=" * 80)
            print(f"⚡ Interrupted! You asked {query_count} questions.")
            print("=" * 80 + "\n")
            # Log interruption for monitoring
            logger.info(f"Session interrupted after {query_count} queries")
            break  # Exit loop cleanly
            
        except EOFError:
            # === END OF INPUT HANDLING ===
            # Handle EOF (End Of File) condition - occurs when input stream ends
            # This can happen when piping input: echo "question" | python chat.py
            print("\n" + "=" * 80)
            print(f"👋 Session ended. You asked {query_count} questions.")
            print("=" * 80 + "\n")
            # Log EOF condition for debugging piped input scenarios
            logger.info(f"Session ended (EOF) after {query_count} queries")
            break  # Exit loop gracefully
            
        except Exception as e:
            # === UNEXPECTED ERROR HANDLING ===
            # Catch any other unexpected errors to prevent program crash
            # This ensures user always gets feedback even when errors occur
            error_msg = f"Unexpected error: {str(e)}"
            # Display user-friendly error message
            print(f"\n❌ Error: {error_msg}\n")
            # Log full error details for debugging
            logger.error(error_msg)
            # Note: Loop continues after error (doesn't break) so user can keep asking questions


# === PROGRAM ENTRY POINT ===
# This block ensures main() only runs when script is executed directly
# (not when imported as a module by another script)
if __name__ == "__main__":
    main()  # Start the interactive chatbot
