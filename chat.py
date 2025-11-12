"""
GroundX Chat Interface Module

Provides an interactive command-line Q&A interface for querying ingested ITNB content.
Demonstrates RAG capabilities by retrieving contextual answers and generating LLM responses.
"""

import os
import logging
import sys
import requests
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

# LLM Configuration (as specified in assessment)
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME', 'inference-llama4-maverick')
OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://maas.ai-2.kvant.cloud')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def generate_llm_response(context, query):
    """
    Generate LLM completion using custom OpenAI-compatible endpoint.
    
    Args:
        context (str): Retrieved context from GroundX search
        query (str): User's original question
        
    Returns:
        str: LLM-generated response or None on error
    """
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": OPENAI_MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": f"""You are a helpful assistant that answers questions using the provided context.
Use the following information to answer the user's question accurately:

===
{context}
===

Provide a clear, concise answer based only on the information above. If the context doesn't contain enough information, say so."""
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        logger.info(f"Calling LLM: {OPENAI_MODEL_NAME} at {OPENAI_API_BASE}")
        
        response = requests.post(
            f"{OPENAI_API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"LLM API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating LLM response: {str(e)}")
        return None


def search_and_display(query):
    """
    Search GroundX bucket, retrieve context, and generate LLM response.
    
    Args:
        query (str): User's question or search query
        
    Returns:
        bool: True if search and generation succeeded, False otherwise
    """
    # Initialize GroundX client
    client = GroundX(api_key=GROUNDX_API_KEY)
    
    try:
        logger.info(f"Query: {query}")
        
        # Search the bucket with GroundX
        response = client.search.content(
            id=GROUNDX_BUCKET_ID,
            query=query
        )
        
        if response and response.search:
            search_data = response.search
            
            # Check if we have meaningful results
            if not search_data.results or search_data.count == 0:
                print("\n" + "=" * 80)
                print("❌ NO INFORMATION FOUND")
                print("=" * 80)
                print("\nSorry, this information is not present on the ITNB website.")
                print("Please try rephrasing your question or ask about different topics.\n")
                print("=" * 80 + "\n")
                logger.warning(f"No results found for query: {query}")
                return False
            
            # Check relevance score threshold
            if search_data.score < 50:
                print("\n" + "=" * 80)
                print("⚠️  LOW RELEVANCE")
                print("=" * 80)
                print("\nThe information found has low relevance to your question.")
                print("This content might not be present on the ITNB website.")
                print("Please try asking something else.\n")
                print("=" * 80 + "\n")
                logger.warning(f"Low relevance score ({search_data.score:.2f}) for query: {query}")
                return False
            
            # Extract context from GroundX search results
            context = search_data.text if search_data.text else ""
            
            # Generate LLM response using custom endpoint
            llm_response = generate_llm_response(context, query)
            
            # Display results header
            print("\n" + "=" * 80)
            print("✅ ANSWER")
            print("=" * 80)
            
            # Display LLM-generated answer
            print("")
            if llm_response:
                print(llm_response)
            elif context:
                # Fallback to raw context if LLM fails
                logger.warning("LLM generation failed, showing raw context")
                if len(context) > 1500:
                    print(context[:1500] + "\n\n[... answer truncated for readability ...]")
                else:
                    print(context)
            else:
                print("No detailed answer available.")
            
            # Display source information
            if search_data.results:
                top_result = search_data.results[0]
                print("\n" + "-" * 80)
                print(f"📊 Relevance Score: {search_data.score:.2f}")
                print(f"📄 Results Found: {search_data.count}")
                if top_result.source_url:
                    print(f"🔗 Source: {top_result.source_url}")
                    logger.info(f"Source: {top_result.source_url}")
                
                logger.info(f"Search successful - {search_data.count} results, score: {search_data.score:.2f}")
            
            print("=" * 80 + "\n")
            return True
        else:
            print("\n" + "=" * 80)
            print("❌ NO INFORMATION FOUND")
            print("=" * 80)
            print("\nThis information is not present on the ITNB website.")
            print("Please try asking about different topics.\n")
            print("=" * 80 + "\n")
            logger.warning(f"No response from GroundX for query: {query}")
            return False
            
    except Exception as e:
        error_msg = f"Search error: {str(e)}"
        print(f"\n❌ Error: {error_msg}\n")
        logger.error(error_msg)
        return False


def display_header():
    """Display professional welcome header."""
    print("\n" + "=" * 80)
    print("🤖 ITNB KNOWLEDGE BASE - Q&A CHATBOT")
    print("=" * 80)
    print("\nAsk me anything about ITNB!")
    print("Powered by GroundX RAG (Retrieval-Augmented Generation).\n")
    print("Commands:")
    print("  💬 Type your question and press Enter")
    print("  🚪 Type 'exit', 'quit', or 'q' to quit")
    print("  ⚡ Press Ctrl+C to interrupt at any time\n")
    print("Examples:")
    print("  - What is ITNB?")
    print("  - Tell me about Sovereign Cloud")
    print("  - What services does ITNB offer?")
    print("  - Who are the cybersecurity experts at ITNB?\n")
    print("=" * 80 + "\n")


def main():
    """Main interactive chat loop."""
    display_header()
    logger.info("Chat session started")
    
    query_count = 0
    
    while True:
        try:
            # Get user input with better prompt
            question = input("💬 You: ").strip()
            
            if not question:
                print("⚠️  Please enter a valid question.\n")
                continue
            
            # Check for exit commands
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n" + "=" * 80)
                print(f"👋 Session ended. You asked {query_count} questions.")
                print("Thank you for using ITNB Knowledge Base!")
                print("=" * 80 + "\n")
                logger.info(f"Chat session ended after {query_count} queries")
                break
            
            # Process query
            query_count += 1
            print(f"\n🔍 Searching... (Query #{query_count})")
            search_and_display(question)
            
        except KeyboardInterrupt:
            print("\n\n" + "=" * 80)
            print(f"⚡ Interrupted! You asked {query_count} questions.")
            print("=" * 80 + "\n")
            logger.info(f"Session interrupted after {query_count} queries")
            break
        except EOFError:
            # Handle end of input (e.g., when piping input)
            print("\n" + "=" * 80)
            print(f"👋 Session ended. You asked {query_count} questions.")
            print("=" * 80 + "\n")
            logger.info(f"Session ended (EOF) after {query_count} queries")
            break
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"\n❌ Error: {error_msg}\n")
            logger.error(error_msg)


if __name__ == "__main__":
    main()
