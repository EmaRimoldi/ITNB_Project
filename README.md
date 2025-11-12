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
│ 1. SCRAPING LAYER (scrape.py)                                  │
│    - URL: https://www.itnb.ch/en                               │
│    - Tool: BeautifulSoup4 (HTML parsing)                       │
│    - Output: scraped_data/itnb_content.json                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│ 2. INGESTION LAYER (ingest.py)                                 │
│    - Service: GroundX Official SDK                             │
│    - Operation: Website crawling with semantic indexing        │
│    - Result: 41 documents indexed and searchable               │
│    - Status: Asynchronous (check_status.py to monitor)        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│ 3. RETRIEVAL & Q&A LAYER (chat.py)                             │
│    - API: GroundX Search (client.search.content())             │
│    - Input: User natural language queries                      │
│    - Output: Relevance-ranked results with source URLs        │
│    - Interface: Interactive headless CLI                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stage 2: Theoretical Design Questions & Answers

### Question 1: Role-Based Access Control (RBAC) Implementation

**Design Overview:**

To implement document-level access control in GroundX for an enterprise RAG system, I would use a **metadata-based filtering approach** combined with runtime authorization checks.

**1. Document-User Association:**

During ingestion, attach permission metadata to each document using GroundX's `search_data` parameter:
```python
search_data={
  "department": "sales",
  "access_level": "manager",
  "confidentiality": "internal"
}
```

Synchronize permissions from source systems (SharePoint, Azure AD) to maintain a separate access control database (PostgreSQL) mapping users to authorized departments/roles. This ensures permissions mirror organizational structure.

**2. Query-Time Enforcement:**

Before each query, authenticate the user and fetch their roles. Construct dynamic GroundX filters that restrict results:
```python
authorized_depts = get_user_departments(user_id)
response = client.search.content(
  query=user_query,
  filter={"department": {"$in": authorized_depts}}
)
```

For complex scenarios, combine filters:
```python
filter={
  "$and": [
    {"department": user_department},
    {"confidentiality": {"$lte": user_clearance_level}}
  ]
}
```

**3. Security Considerations:**

- **Sync Lag**: Permission changes in source systems (user role updates) may not reflect immediately. Mitigation: Implement event-driven webhooks for real-time sync plus periodic batch reconciliation.
- **Filter Performance**: Complex filters add latency. Mitigation: Cache user permission sets and index metadata fields.
- **Privilege Escalation**: Never allow user-controlled filter input. Always construct filters server-side from authenticated context.
- **Audit Compliance**: Log all queries with {user_id, query, filters_applied, timestamp} for regulatory compliance.
- **Metadata Limitations**: Flat key-value metadata struggles with hierarchical permissions (nested groups). Consider external policy engines (e.g., Open Policy Agent) for complex rules.

This architecture balances security, performance, and maintainability for enterprise-scale RBAC in RAG systems.

---

### Question 2: Scaling RAG for Large and Dynamic Knowledge Bases

**Architecture Overview:**

For the Sovereign Orchestrator AI Concierge, I would design an **event-driven, connection-based RAG system** that handles thousands of frequently changing documents while empowering users through governed self-service.

**1. Handling Large-Scale, Dynamic Document Sets:**

**Event-Driven Ingestion:**
- Connect to enterprise data sources (SharePoint, Teams, Confluence) via **webhooks** to capture real-time document events (created/modified/deleted)
- Use **message queues** (Kafka, RabbitMQ) to buffer events and enable **incremental ingestion** (process only changed documents, not entire corpus)
- Implement **batch processing** (every 5-10 minutes or 100 documents) to balance freshness with efficiency

**Change Tracking:**
- Maintain changelog with document hashes to detect modifications
- Support versioning for audit trails and rollback capabilities

**2. User-Empowered Document Management:**

**Yes, but through Connection Governance—not manual uploads:**

Users (team leads, department managers) should manage **data source connections**, not individual files:
- **Connect** SharePoint folders → auto-ingest all documents
- **Connect** Confluence spaces → sync knowledge base
- **Connect** Teams channels → index meeting notes

**Why Connections Beat Uploads:**
- **Scalability**: 100 connections > 10,000 file uploads
- **Freshness**: Connected sources auto-update; uploads become stale
- **Compliance**: Source system permissions/audit logs preserved
- **Ownership**: Clear responsibility chain maintained

**User Portal Capabilities:**
```
✅ Connect new data sources (with IT approval)
✅ Pause/resume ingestion per source
✅ Set refresh frequency (real-time/hourly/daily)
✅ Tag/categorize documents
✅ Archive documents (soft delete with recovery)

❌ No direct file uploads
❌ No permission bypasses
❌ No permanent deletions (retention policy enforced)
```

**3. Algorithms & Automation for Efficiency:**

**Intelligent Processing Pipeline:**

- **Automated Classification**: ML agent categorizes documents on ingestion (department, document_type, sensitivity, urgency) for smart routing
- **Metadata Enrichment**: Extract entities (people, projects, dates), topics, and summaries using NER and key-phrase extraction
- **Semantic Deduplication**: Use embedding similarity (cosine > 0.95) to detect and merge duplicates, keeping the latest version
- **Multi-Index Routing**: Route documents to specialized sub-indexes (HR Knowledge Base, Critical Info, Temporal Knowledge) based on classification
- **Usage-Based Re-ranking**: Track user engagement (clicks, citations) and recompute document scores:
  ```python
  score = base_relevance × popularity × freshness_decay
  ```
- **Lifecycle Management**: Automatic archival after retention period, permanent deletion after recovery window

**Multi-Agent Query Workflow:**
```
Query → Classification Agent (intent + routing)
      → Authorization Agent (RBAC filters)
      → Retrieval Agent (search with filters)
      → Synthesis Agent (coherent answer + citations)
```

**Scalability Summary:**

| Challenge | Solution |
|-----------|----------|
| Volume | Event-driven incremental ingestion |
| Freshness | Real-time webhooks + message queues |
| Management | Connection-based (not file uploads) |
| Quality | Auto classification + deduplication |
| Performance | Multi-index routing + usage-based ranking |

This architecture scales to **millions of documents** while maintaining sub-second query latency and up-to-date content—critical for enterprise AI concierges like Sovereign Orchestrator.

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