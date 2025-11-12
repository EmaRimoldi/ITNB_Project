"""
ITNB Website Content Scraping Module

Purpose:
This module scrapes textual content from https://www.itnb.ch/en and organizes it into
a hierarchical structure. Instead of dumping all content into a single JSON file,
it creates separate files for pages, sections, and paragraphs - making the data
easier to navigate, update, and process for RAG ingestion.

Key Features:
- Hierarchical organization (pages → sections → paragraphs)
- Unique ID generation for each content unit using MD5 hashing
- Recursive crawling with depth and page limits
- BeautifulSoup HTML parsing with content extraction
- Structured file system storage with index

Output Structure:
scraped_data/
  ├── pages/         Individual page JSON files (top-level pages)
  ├── sections/      Semantic sections/topics from each page
  ├── paragraphs/    Individual paragraph units (optimal for RAG chunking)
  ├── index.json     Master metadata file with all IDs and relationships
  └── complete_export.json  Full hierarchical data in one file (for reference)
"""

# === STANDARD LIBRARY IMPORTS ===
import json  # For reading/writing JSON data structures
import os  # For filesystem operations (creating directories, file paths)
import hashlib  # For generating unique MD5 hashes as content IDs

# === THIRD-PARTY IMPORTS ===
import requests  # For making HTTP requests to fetch web pages
from bs4 import BeautifulSoup  # For parsing and navigating HTML content
from urllib.parse import urljoin, urlparse  # For handling relative/absolute URLs


class ITNBScraper:
    """
    Hierarchical web scraper for ITNB website.
    
    This class implements intelligent web scraping that organizes content into
    a three-level hierarchy optimized for RAG (Retrieval-Augmented Generation):
    
    Organization Structure:
    1. Pages: Top-level web pages (e.g., /en, /en/about, /en/services)
    2. Sections: Semantic sections within pages (e.g., "Introduction", "Features")
    3. Paragraphs: Individual text chunks (optimal for vector embedding and retrieval)
    
    Design Rationale:
    - Pages provide context about where content comes from
    - Sections group related information logically
    - Paragraphs are the ideal granularity for RAG retrieval (not too large, not too small)
    
    Attributes:
        base_url (str): Starting URL for crawling (default: https://www.itnb.ch/en)
        max_pages (int): Maximum number of pages to scrape (prevents infinite crawling)
        visited_urls (set): Tracks visited URLs to avoid duplicate scraping
        pages (list): Collected page data dictionaries
        sections (list): Collected section data dictionaries
        paragraphs (list): Collected paragraph data dictionaries
        index (dict): Master index with metadata and cross-references
    """
    
    def __init__(self, base_url="https://www.itnb.ch/en", max_pages=20):
        """
        Initialize the ITNB scraper with configuration.
        
        Args:
            base_url (str): Starting URL for crawling (should be the English version)
            max_pages (int): Maximum pages to scrape (safety limit to prevent runaway crawling)
        """
        # Store configuration parameters
        self.base_url = base_url  # Root URL to start scraping from
        self.max_pages = max_pages  # Safety limit for number of pages
        
        # Initialize tracking structures
        self.visited_urls = set()  # Prevent re-scraping same URL (deduplication)
        
        # Initialize data storage lists (will hold extracted content)
        self.pages = []  # List of page dictionaries
        self.sections = []  # List of section dictionaries
        self.paragraphs = []  # List of paragraph dictionaries
        
        # Initialize master index (metadata about all scraped content)
        # This acts as a "table of contents" for the hierarchical structure
        self.index = {
            "base_url": base_url,  # Root URL being scraped
            "total_pages": 0,  # Count of pages (updated after scraping)
            "total_sections": 0,  # Count of sections (updated after scraping)
            "total_paragraphs": 0,  # Count of paragraphs (updated after scraping)
            "pages": [],  # List of page metadata (id, title, url)
            "sections": [],  # List of section metadata (id, title, page_id)
            "paragraphs": []  # List of paragraph metadata (id, section_id, page_id)
        }
    
    def scrape_website(self):
        """
        Main orchestration method: Crawl ITNB website and extract hierarchical content.
        
        This method coordinates the entire scraping process:
        1. Start crawling from base_url
        2. Recursively discover and scrape linked pages
        3. Extract and organize content hierarchically
        4. Save all data to disk in organized structure
        
        Returns:
            bool: True if scraping completed successfully, False if errors occurred
        """
        # Display scraping configuration to user
        print(f"Starting hierarchical scraping of {self.base_url}...")
        print(f"Max pages: {self.max_pages}\n")
        
        try:
            # === CRAWLING PHASE ===
            # Start recursive crawling from the base URL with depth 0
            # depth=0 means this is the starting page
            self._scrape_page(self.base_url, 0)
            
            # === SAVING PHASE ===
            # After crawling completes, save all collected data to disk
            # This creates the hierarchical file structure
            self._save_organized_data()
            
            # === SUCCESS SUMMARY ===
            # Display statistics about what was scraped
            print(f"\n✓ Scraping completed successfully!")
            print(f"  Pages scraped: {len(self.pages)}")  # Number of unique pages visited
            print(f"  Sections extracted: {len(self.sections)}")  # Number of semantic sections
            print(f"  Paragraphs extracted: {len(self.paragraphs)}")  # Number of paragraph chunks
            # Calculate total character count across all paragraphs
            print(f"  Total characters: {sum(len(p['content']) for p in self.paragraphs)}")
            
            return True  # Indicate successful scraping
            
        except Exception as e:
            # === ERROR HANDLING ===
            # If any error occurs during scraping, catch it and report to user
            print(f"ERROR: Scraping failed: {str(e)}")
            # Print full stack trace for debugging
            import traceback
            traceback.print_exc()
            return False  # Indicate scraping failure
    
    def _scrape_page(self, url, depth, max_depth=2):
        """
        Recursively scrape pages with depth limit.
        """
        if depth > max_depth or len(self.visited_urls) >= self.max_pages:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        page_num = len(self.visited_urls)
        
        print(f"[{page_num}] Scraping: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page content
            page_data = self._extract_page_content(url, soup)
            if page_data:
                self.pages.append(page_data)
                self.index["pages"].append({
                    "id": page_data["id"],
                    "title": page_data["title"],
                    "url": page_data["url"]
                })
            
            # Extract sections and paragraphs
            self._extract_sections_and_paragraphs(url, soup, page_data["id"] if page_data else None)
            
        except Exception as e:
            print(f"  ✗ Error scraping {url}: {str(e)}")
    
    def _extract_page_content(self, url, soup):
        """
        Extract main content from a page.
        """
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get page title
        title_tag = soup.find('h1')
        if not title_tag:
            title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else urlparse(url).netloc
        
        # Get all body text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not content or len(content) < 50:
            return None
        
        page_id = self._generate_id(url)
        
        page_data = {
            "id": page_id,
            "title": title,
            "url": url,
            "content": content,
            "character_count": len(content)
        }
        
        return page_data
    
    def _extract_sections_and_paragraphs(self, url, soup, page_id):
        """
        Extract sections and paragraphs from a page by breaking text into logical chunks.
        """
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get all text content
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = '\n'.join(chunk for chunk in chunks if chunk)
        
        if not content or len(content) < 100:
            return
        
        # Split into sentences/sections for better organization
        # Use common delimiters to create sections
        sections_text = content.split('\n\n')  # Split by double newlines
        
        section_counter = 0
        paragraph_counter = 0
        
        for section_text in sections_text:
            if len(section_text) < 30:  # Skip tiny sections
                continue
            
            # Treat each major section as a section
            section_counter += 1
            section_title = section_text.split('\n')[0][:50]  # First 50 chars as title
            section_id = self._generate_id(f"{url}#{section_counter}#{section_title}")
            
            section_data = {
                "id": section_id,
                "page_id": page_id,
                "title": section_title,
                "url": url,
                "paragraph_count": 0
            }
            
            # Split section into paragraphs (by newlines or by character limit)
            paragraphs = []
            
            # Strategy: Split by newlines, or if too long, split by sentences
            if '\n' in section_text:
                para_candidates = section_text.split('\n')
            else:
                # Split long sections into ~200 char chunks
                para_candidates = []
                text_parts = section_text.split('. ')
                current_para = ""
                
                for part in text_parts:
                    if len(current_para) + len(part) > 200:
                        if current_para:
                            para_candidates.append(current_para.strip())
                        current_para = part
                    else:
                        current_para += ". " + part if current_para else part
                
                if current_para:
                    para_candidates.append(current_para.strip())
            
            # Process paragraphs
            para_count = 0
            for para_text in para_candidates:
                para_text = para_text.strip()
                
                if len(para_text) > 20:  # Only save substantial paragraphs
                    paragraph_counter += 1
                    para_count += 1
                    
                    para_id = self._generate_id(f"{url}#para#{paragraph_counter}")
                    
                    paragraph_data = {
                        "id": para_id,
                        "section_id": section_id,
                        "page_id": page_id,
                        "content": para_text,
                        "character_count": len(para_text),
                        "url": url
                    }
                    self.paragraphs.append(paragraph_data)
                    
                    self.index["paragraphs"].append({
                        "id": para_id,
                        "section_id": section_id,
                        "page_id": page_id,
                        "character_count": len(para_text)
                    })
            
            # Only save section if it has paragraphs
            if para_count > 0:
                section_data["paragraph_count"] = para_count
                self.sections.append(section_data)
                
                self.index["sections"].append({
                    "id": section_id,
                    "title": section_title,
                    "page_id": page_id
                })
    
    def _generate_id(self, text):
        """Generate a unique ID based on text hash."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _save_organized_data(self):
        """
        Save scraped data in hierarchical directory structure.
        """
        base_dir = 'scraped_data'
        
        # Create directories
        dirs = [
            base_dir,
            os.path.join(base_dir, 'pages'),
            os.path.join(base_dir, 'sections'),
            os.path.join(base_dir, 'paragraphs')
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Save pages
        for page in self.pages:
            file_path = os.path.join(base_dir, 'pages', f"{page['id']}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(page, f, ensure_ascii=False, indent=2)
        
        # Save sections
        for section in self.sections:
            file_path = os.path.join(base_dir, 'sections', f"{section['id']}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(section, f, ensure_ascii=False, indent=2)
        
        # Save paragraphs
        for para in self.paragraphs:
            file_path = os.path.join(base_dir, 'paragraphs', f"{para['id']}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(para, f, ensure_ascii=False, indent=2)
        
        # Update and save index
        self.index["total_pages"] = len(self.pages)
        self.index["total_sections"] = len(self.sections)
        self.index["total_paragraphs"] = len(self.paragraphs)
        
        index_path = os.path.join(base_dir, 'index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
        
        # Save complete hierarchical export (for reference)
        complete_export = {
            "metadata": {
                "base_url": self.base_url,
                "total_pages": len(self.pages),
                "total_sections": len(self.sections),
                "total_paragraphs": len(self.paragraphs)
            },
            "pages": self.pages,
            "sections": self.sections,
            "paragraphs": self.paragraphs
        }
        
        export_path = os.path.join(base_dir, 'complete_export.json')
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(complete_export, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Data saved to {base_dir}/")
        print(f"  - pages/        ({len(self.pages)} files)")
        print(f"  - sections/     ({len(self.sections)} files)")
        print(f"  - paragraphs/   ({len(self.paragraphs)} files)")
        print(f"  - index.json    (metadata index)")
        print(f"  - complete_export.json (full hierarchical data)")


def scrape_itnb():
    """
    Main scraping function - maintains backward compatibility.
    """
    scraper = ITNBScraper(base_url="https://www.itnb.ch/en", max_pages=20)
    return scraper.scrape_website()


if __name__ == "__main__":
    success = scrape_itnb()
    exit(0 if success else 1)