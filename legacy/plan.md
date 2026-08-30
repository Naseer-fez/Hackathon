🎯 Agent Task: Indian Standards Recommendation Engine
ROLE
You are a Senior Developer at Google with deep expertise in building production-grade AI systems. You are tasked with building the application layer of an AI-powered recommendation engine for Indian Standards (IS) identification in e-procurement portals.

📋 PROJECT OVERVIEW
Problem
Government departments, PSEs, and procurement agencies struggle to identify the correct Indian Standards when preparing tender specifications due to:

Large volume of published standards
Overlapping scopes
Frequent revisions
Complex normative/cross-referenced standards
Solution
Build an AI-powered recommendation engine that:

Accepts product descriptions, technical specs, or tender documents as input
Recommends the most relevant Indian Standard(s) using semantic understanding (not keyword matching)
Identifies allied standards — normative references, test methods, terminology, safety, installation, and related product standards
Highlights latest published versions and amendments
Suggests mandatory certification requirements (BIS Product Certification, CRS, Hallmarking, etc.)
Supports multilingual input and natural language queries
✅ ALREADY DONE — DO NOT REBUILD THESE
⚠️ The following are COMPLETE. Do NOT touch, modify, or rebuild them. Simply USE them.

Component
Status
Indian Standards data scraping	✅ Complete
Vector database	✅ Ready and populated
Embedded search capability	✅ Available via vector DB

🛠️ MANDATORY: USE REPOSITORY SKILLS
⚠️ CRITICAL INSTRUCTION: You MUST use the existing skills/tools available in this repository. Do NOT build from scratch.

Skill Utilization Map
Pipeline Stage
Repository Skill to Use
Purpose
PDF Input	PDF OCR Reader skill	Extract text from uploaded PDFs
Image Handling	Image Classifier skill	Classify embedded images — locally
Standards Search	Vector DB (already ready)	Semantic search across Indian Standards
LLM Processing	LLM Abstraction Endpoint skill	Standardize & generate final response
Voice I/O	Text-to-Speech / Speech-to-Text skill	Voice conversion — locally

🏗️ ARCHITECTURE REQUIREMENTS
1. Pipeline Flow
text

[User Input: PDF / Voice / Text]
        │
        ▼
[PDF OCR Skill] ──→ Raw extracted text
        │
        ▼
[Image Classifier Skill] ──→ Process images (LOCAL)
        │
        ▼
[Vector DB] ──→ Relevant Indian Standards (ALREADY READY)
        │
        ▼
[LLM Abstraction Endpoint]
        │   ├─ PRIMARY: Cloud LLM
        │   └─ FALLBACK: Local LLM (automatic, silent)
        │
        ▼
[Text-to-Speech Skill] ──→ Optional voice output (LOCAL)
        │
        ▼
[Final Output to User]
2. LLM Configuration — Cloud-First with Seamless Local Fallback
⚠️ THIS IS THE MOST CRITICAL PART OF THE ARCHITECTURE

text

┌─────────────────────────────────────────────┐
│         LLM ABSTRACTION LAYER               │
│                                             │
│  Input: Standardized data contract          │
│         (extracted text + vector DB results) │
│                     │                       │
│                     ▼                       │
│         ┌─────────────────────┐             │
│         │  Router / Orchestrator │           │
│         └──────────┬──────────┘             │
│                    │                        │
│          ┌────────┴────────┐                │
│          ▼                 ▼                │
│   ┌─────────────┐  ┌─────────────┐          │
│   │ CLOUD LLM   │  │ LOCAL LLM   │          │
│   │ (Primary)   │  │ (Fallback)  │          │
│   └──────┬──────┘  └──────┬──────┘          │
│          │                │                 │
│          └────────┬───────┘                 │
│                   ▼                         │
│  Output: Standardized response contract     │
│          (identical format, either source)  │
└─────────────────────────────────────────────┘
Rules:

Cloud is default — faster, more scalable
If cloud fails (timeout, error, rate limit, network down) → instantly and silently switch to local
Zero user interruption — no error, no spinner, no indication of fallback
Output format is locked — identical structure regardless of which model served it
Single endpoint for the rest of the pipeline to call
Primary model: Qwen 2.5 8B or equivalent lightweight model
3. Local Processing Requirements
Image classification: LOCAL — no external API
Text-to-Speech / Speech-to-Text: LOCAL — no external API
LLM fallback: LOCAL — only when cloud fails
4. Abstraction Principles
Every module = clean interface (input schema → output schema)
No tight coupling between any two stages
Any component replaceable by modifying only its own module
System feels like one single service to the end user
📁 FILE SCRAPPING INSTRUCTION
Scrape the repository files to:

Understand the existing skill implementations (OCR, classifier, TTS/STT)
Identify input/output formats for each skill
Understand the vector DB schema and query interface
Find any existing LLM abstraction code to extend
Identify any local model loading mechanisms for fallback
✅ DELIVERABLES
Pipeline integration — wire existing skills together, don't rebuild them
LLM Abstraction Layer — cloud-primary + silent-local-fallback
Vector DB query integration — connect search results into the LLM input
Voice I/O integration — local TTS/STT wired into the pipeline
Modular structure — any component swappable without side effects
🚫 CONSTRAINTS
Do NOT rebuild the vector DB or re-scrape data — it's DONE
Do NOT reinvent existing skills — USE them
Do NOT hardcode LLM-specific logic outside the abstraction layer
Do NOT use external APIs for image classification or voice — LOCAL only
Do NOT let cloud failure reach the user — local fallback must be instant and silent