# BIS-SpecAI: AI-Powered Indian Standards (BIS) Recommendation Engine & Procurement Assistant

An intelligent, AI-driven recommendation and specification compliance engine designed for e-Procurement portals (GeM, CPPP, State/PSU Tenders). It automates the discovery of Indian Standards (IS), resolves multi-level normative reference graphs, tracks latest reaffirmations and amendments, enforces mandatory Quality Control Orders (QCOs), and supports multilingual Indic natural language queries.

---

## 🌟 Key Capabilities

1. **Semantic Standard Discovery**: Hybrid neural search combining dense vector embeddings (`sentence-transformers`), lexical matching, and IS code exact matching with Reciprocal Rank Fusion (RRF).
2. **Allied & Normative Graph Resolution**: Traverses multi-relational graphs linking primary product standards to:
   - **Normative References**: Mandatory dependent standards
   - **Test Method Standards**: Exact testing protocols (tensile, dielectric, chemical)
   - **Safety Standards**: Statutory safety codes
   - **Installation Standards**: Field installation and commissioning codes of practice
3. **Quality Control Order (QCO) Enforcement**: Automatically checks statutory Gazette orders by DPIIT, MeitY, Ministry of Power, Ministry of Steel, and Ministry of Textiles for mandatory **ISI Mark (Scheme I)** and **CRS (Scheme II)** compliance.
4. **Deprecation & Supersession Alerts**: Instantly flags outdated standard citations (e.g. `IS 1786:1985` -> `IS 1786:2008 R-2023`, `IS 1293:2005` -> `IS 1293:2019`).
5. **Multilingual Indic Query Processing**: Real-time translation and term normalization for Hindi (`सौर पैनल`, `सरिया`, `स्ट्रीट लाइट`), Tamil, Telugu, and Bengali queries.
6. **Tender Specification Auditor**: Multi-format document parser (PDF, DOCX, TXT) extracting line items, auditing compliance gaps, and calculating mandatory QCO coverage score.
7. **Specification Clause Generator**: 1-click generation of legally compliant, GeM-ready tender specification clauses with exact IS citations, amendment clauses, and testing mandates.
8. **GeM & e-Procurement Webhook Integration**: RESTful endpoint (`/api/v1/gem-webhook`) enabling automated bid validation during e-bid creation.

---

## 🏗️ Architecture

```
d:\CODE\Hackathon/
├── backend/
│   ├── config/              # YAML-based configuration & Pydantic settings
│   │   ├── config.yaml
│   │   └── settings.py
│   ├── data/                # Seed generators & Indian Standards dataset
│   │   ├── civil_standards.py
│   │   ├── electrical_standards.py
│   │   ├── electronics_solar_standards.py
│   │   ├── mech_safety_standards.py
│   │   ├── seed_generator.py
│   │   └── standards_database.json
│   ├── engine/              # AI semantic search & resolution algorithms
│   │   ├── multilingual_processor.py
│   │   ├── embedding_service.py
│   │   ├── hybrid_retriever.py
│   │   ├── normative_resolver.py
│   │   ├── certification_advisor.py
│   │   └── tender_clause_generator.py
│   ├── parsers/             # Document extraction (PDF, DOCX, TXT)
│   │   ├── document_parser.py
│   │   └── spec_extractor.py
│   ├── ingestion/           # Scrapers & registries
│   │   ├── bis_scraper.py
│   │   ├── standards_loader.py
│   │   └── qco_registry.py
│   ├── api/                 # FastAPI REST routers
│   │   ├── recommendation_router.py
│   │   ├── tender_router.py
│   │   ├── standards_router.py
│   │   └── gem_webhook_router.py
│   └── main.py              # Application entry point
├── frontend/                # Vite + React + TypeScript + Tailwind UI
│   ├── src/
│   │   ├── components/      # Decomposed modular UI components (<100 lines)
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript definitions
│   └── package.json
└── tests/                   # Full pytest test suite (100% passing)
```

---

## 🚀 Quickstart

### 1. Run Backend Tests
```powershell
python -m pytest tests/ -v
```

### 2. Start Backend Server
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive Swagger API documentation is available at: `http://127.0.0.1:8000/docs`

### 3. Start Frontend UI
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/recommend` | Natural language / Multilingual standard recommendation |
| `POST` | `/api/v1/analyze-tender` | Multi-format tender document audit (PDF/DOCX/Text) |
| `GET` | `/api/v1/standards` | Search and filter Indian Standards database |
| `GET` | `/api/v1/standards/{is_code}` | Detailed standard metadata and allied relations |
| `GET` | `/api/v1/graph` | Multi-relational knowledge graph data |
| `GET` | `/api/v1/qco-list` | Active Quality Control Orders registry |
| `POST` | `/api/v1/gem-webhook` | GeM portal real-time bid validation simulator |
| `GET` | `/api/v1/health` | Service health status |
