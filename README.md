# ITNB AI Engineering Internship Technical Assessment - RAG Pipeline

Complete end-to-end RAG pipeline demonstrating website crawling, semantic content ingestion, and AI-powered Q&A using GroundX.

## Project Structure

```
Project_ITNB/
├── scrape.py              # Website scraping (extracts textual content from ITNB website)
├── ingest.py              # Website crawling and semantic ingestion into GroundX bucket
├── chat.py                # Headless Q&A command-line interface (interactive)
├── check_status.py        # Monitor ingestion process status
├── README.md              # Complete documentation with setup and theory answers
├── .env                   # Environment variables (GROUNDX_API_KEY, GROUNDX_BUCKET_ID)
├── requirements.txt       # Python dependencies
├── scraped_data/          # Locally stored scraped website content
└── venv/                  # Python virtual environment
```

## Setup Instructions

### Step 1: Install Python
Ensure Python 3.8+ is installed on your system. Check with:
```powershell
python --version
```

### Step 2: Create and Activate Virtual Environment
```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

Or manually install:
```powershell
pip install groundx python-dotenv requests beautifulsoup4
```

### Step 4: Configure GroundX Credentials
1. Sign up at [GroundX Dashboard](https://console.groundx.ai/)
2. Create a bucket and get your API key
3. Create `.env` file in project root with:
   ```
   GROUNDX_API_KEY=your_api_key_here
   GROUNDX_BUCKET_ID=your_bucket_id_here
   
   # LLM Credentials (for query and chat functions)
   OPENAI_MODEL_NAME=openai/inference-llama4-maverick
   OPENAI_API_BASE=https://maas.ai-2.kvant.cloud
   OPENAI_API_KEY=sk-K_lZO2Ms6cRWurIj8gf5sg
   ```

**Note:** The LLM credentials are provided as part of the ITNB assessment and are used for query/chat functionality with GroundX.

## Complete End-to-End Execution Guide

### Full Workflow: From Crawling to Q&A

Follow these steps in order to test the complete RAG pipeline:

#### 1. Activate Virtual Environment
```powershell
cd c:\Users\erimoldi\Desktop\Project_ITNB
.\venv\Scripts\Activate.ps1
```

### Step 2: Scrape Website Content (Optional - Reference Only)
Extracts and stores textual content locally from https://www.itnb.ch/en:
```powershell
python scrape.py
```

**Output:**
```
SUCCESS: Scraped and saved to scraped_data/itnb_content.json
Content size: 3131 characters
```

**File created:** `scraped_data/` (local reference for debugging)

**Note on crawl4ai:** The assessment recommends using `crawl4ai`, but due to Python 3.14 compatibility issues with lxml dependencies, BeautifulSoup4 is used instead for the local reference scraping. However, the **actual website crawling and ingestion is performed by GroundX's built-in website crawler** (see next step), which automatically discovers and indexes all pages from the ITNB website, not just the homepage. This achieves the full crawling requirement as GroundX indexes ~41+ documents from the entire site.

---

#### 3. Ingest Website into GroundX
Crawls the ITNB website and ingests content into GroundX for semantic search:
```powershell
python ingest.py
```

**Output:**
```
================================================================================
GROUNDX WEBSITE INGESTION
================================================================================
URL: https://www.itnb.ch/en
Bucket ID: 22871
Configuration: Max 500 pages, Depth 5 (Full site traversal)

✓ Connecting to GroundX API...
✓ Initializing website crawl configuration...

SUCCESS: Website ingestion initiated!
Process ID: d68e9662-4890-4b04-a4c8-7d1551d58e84
Status: queued

Ingestion Progress:
  Status: queued → training → complete

To monitor progress, run:
  python check_status.py d68e9662-4890-4b04-a4c8-7d1551d58e84
```

**Configuration:**
- `cap: 500` - Crawls up to 500 pages from the site
- `depth: 5` - Traverses 5 levels deep (full site hierarchy)
- Applies metadata for better search organization

**Important:** The ingestion is **asynchronous**. The GroundX backend processes the website in the background.

---

#### 4. Monitor Ingestion Progress (With Visual Progress Bar)
Check the status of ingestion using the Process ID from step 3:

**Single Check:**
```powershell
python check_status.py d68e9662-4890-4b04-a4c8-7d1551d58e84
```

**Output:**
```
================================================================================
INGESTION PROCESS STATUS
================================================================================
Process ID: d68e9662-4890-4b04-a4c8-7d1551d58e84
Status: TRAINING
[████████████████████░░░░░░░░░░░░░░░░░░░░] 50% - TRAINING

⏳ Processing in progress... Check again in a few seconds.
================================================================================
```

**Continuous Monitoring (Auto-checks every 5 seconds):**
```powershell
python check_status.py d68e9662-4890-4b04-a4c8-7d1551d58e84 --continuous
```

This will automatically monitor until status shows `complete`:
```
================================================================================
INGESTION PROCESS STATUS
================================================================================
Process ID: d68e9662-4890-4b04-a4c8-7d1551d58e84
Status: COMPLETE
[████████████████████████████████████████] 100% - Complete (52 documents indexed)

✓ Ingestion Complete! Documents are ready for search.
================================================================================
```

**Progress Stages:**
- `queued` (0%) → `training` (50%) → `complete` (100%)

---

#### 5. Run Interactive Q&A Chat
Start the headless command-line chat interface to query the ingested content:
```powershell
python chat.py
```

The chat interface allows unlimited natural language queries about ITNB content with relevance scoring and source attribution. Type `exit` or `quit` to exit gracefully.

## Technical Architecture

### Data Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SCRAPING LAYER (scrape.py)                                   │
│    - URL: https://www.itnb.ch/en                                │
│    - Tool: BeautifulSoup4 (HTML parsing)                        │
│    - Output: scraped_data/itnb_content.json                     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│ 2. INGESTION LAYER (ingest.py)                                  │
│    - Service: GroundX Official SDK                              │
│    - Operation: Website crawling with semantic indexing         │
│    - Result: 41 documents indexed and searchable                │
│    - Status: Asynchronous (check_status.py to monitor)          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│ 3. RETRIEVAL & Q&A LAYER (chat.py)                              │
│    - API: GroundX Search (client.search.content())              │
│    - Input: User natural language queries                       │
│    - Output: Relevance-ranked results with source URLs          │
│    - Interface: Interactive headless CLI                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 2: Theoretical Design Questions & Answers

### Question 1: Role-Based Access Control (RBAC) Implementation

To implement document-level access control in GroundX for an enterprise RAG system, I would use a metadata-based filtering approach combined with runtime authorization checks. This design balances security, performance, and maintainability while leveraging GroundX's native capabilities.

The first step involves associating documents with user permissions during ingestion. When documents are ingested via the GroundX SDK, we attach permission metadata to each document using the `search_data` parameter. For example, we might tag documents with attributes like department ("sales"), access_level ("manager"), and confidentiality ("internal"). To ensure these permissions stay synchronized with organizational reality, we would maintain a separate access control database, such as PostgreSQL, that mirrors permissions from enterprise systems like SharePoint folder permissions and Azure AD group memberships. This creates a reliable source of truth that maps users to authorized departments and roles.

At query time, enforcement happens through dynamic filtering. Before processing any query, the system authenticates the user and retrieves their roles from the directory service. Using this information, we construct GroundX filter queries that restrict search results to only documents the user is authorized to access. For instance, if a user belongs to the sales department, the filter would specify `{"department": {"$in": ["sales"]}}`. For more complex scenarios involving multiple permission dimensions, we can combine filters using logical operators to check both department membership and confidentiality clearance levels simultaneously.

Several security considerations must be addressed in this architecture. Permission synchronization lag poses a risk when users lose access in source systems but retain access in GroundX temporarily. This can be mitigated through event-driven webhooks for real-time synchronization combined with periodic batch reconciliation jobs. Filter performance can become a concern with complex permission hierarchies, so caching user permission sets and indexing metadata fields becomes essential. To prevent privilege escalation attacks, filters must always be constructed server-side from authenticated user context—never from user-supplied input. For regulatory compliance, all queries should be logged with user ID, query text, applied filters, and timestamps. Finally, GroundX's flat key-value metadata model may struggle with deeply hierarchical permissions like nested groups, so external policy engines such as Open Policy Agent might be necessary for complex enterprise rules.

---

### Question 2: Scaling RAG for Large and Dynamic Knowledge Bases

For the Sovereign Orchestrator AI Concierge, I would design an event-driven, connection-based RAG system that handles thousands of frequently changing documents while empowering users through governed self-service. This architecture prioritizes real-time freshness, scalability, and intelligent automation.

Handling large-scale, dynamic document sets requires moving away from traditional batch processing toward event-driven ingestion. The system would connect to enterprise data sources like SharePoint, Teams, and Confluence through webhooks that capture document events in real-time—whether documents are created, modified, or deleted. These events flow into message queues such as Kafka or RabbitMQ, which decouple event arrival from processing and provide resilience against traffic spikes. The key innovation is incremental ingestion: instead of re-processing thousands of documents, the system processes only what has changed. To balance freshness with efficiency, documents are batched—processing either every 5-10 minutes or when 100 documents accumulate, whichever comes first. A changelog system maintains document hashes to detect modifications and supports versioning for audit trails and rollback capabilities.

User empowerment is critical, but it must be implemented through connection governance rather than manual file uploads. Instead of asking users to upload thousands of individual files, team leads and department managers should manage data source connections. For example, they can connect SharePoint folders to automatically ingest all contained documents, link Confluence spaces to synchronize knowledge bases, or authorize Teams channels to index meeting notes. This connection-based approach offers several advantages: managing 100 connections is far more scalable than managing 10,000 file uploads; connected sources automatically update while uploaded files become stale; source system permissions and audit logs are preserved; and there's a clear ownership chain from source owner to document owner to GroundX administrator. Users can connect new data sources (with IT approval), pause or resume ingestion per source, set refresh frequencies, tag documents for organization, and archive documents with recovery periods. However, they cannot directly upload files, modify source system permissions, permanently delete documents before retention periods expire, or bypass access controls.

To keep retrieval efficient and up-to-date at scale, the system employs intelligent automation throughout the document lifecycle. An automated classification agent categorizes documents on ingestion—determining department, document type, sensitivity level, and urgency—which enables smart routing to specialized indexes. Metadata enrichment extracts entities like people names, project codes, and dates using named entity recognition, along with key topics and document summaries. Semantic deduplication compares document embeddings to detect near-duplicates (cosine similarity above 0.95) and automatically keeps the most recent or comprehensive version. Documents are routed to specialized sub-indexes based on their classification: HR documents go to an HR Knowledge Base, security advisories to a Critical Info high-priority index, and meeting notes to a Temporal Knowledge index with time-decay ranking. The system continuously re-ranks documents based on user engagement—tracking clicks and citations to compute relevance scores that factor in base semantic relevance, popularity, and freshness decay. Finally, lifecycle management automatically archives documents after retention periods and permanently deletes them after recovery windows expire. At query time, a multi-agent workflow orchestrates the response: a classification agent determines query intent and routing, an authorization agent applies RBAC filters, a retrieval agent searches with those filters and ranks results, and a synthesis agent combines everything into a coherent answer with citations. This architecture scales to millions of documents while maintaining sub-second query latency and up-to-date content—essential requirements for enterprise AI concierges like the Sovereign Orchestrator.

---



## Final Deliverables Checklist

### Code
- [x] `scrape.py` - Website scraping module
- [x] `ingest.py` - GroundX ingestion module
- [x] `chat.py` - Interactive Q&A interface
- [x] `check_status.py` - Process status monitoring utility
- [x] `.env` - Environment configuration (credentials required)
- [x] `requirements.txt` - Python dependencies
- [x] `.gitignore` - Git exclusions

### Documentation
- [x] `README.md` - Complete with setup, usage, and design answers
- [x] This file includes 2000+ words of architectural guidance

---

## Author

Prepared as part of ITNB AI Engineering Internship Technical Assessment
Date: November 2025
Version: 1.0
