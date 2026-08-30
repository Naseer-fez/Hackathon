---
name: bis-specai
description: >-
  Workflows for the Bureau of Indian Standards (BIS) Recommendation Engine,
  Quality Control Order (QCO) compliance evaluation, normative reference graph
  resolution, and GeM/CPPP tender specification clause generation. Use when
  working on Indian Standards, procurement specifications, or BIS e-procurement
  integrations.
---

# BIS-SpecAI Domain Skill

## Overview
This skill guides the development, querying, and verification of the Indian Standards (IS) recommendation system and e-procurement assistants.

## Recommendation Pipeline Protocol
1. **Query Ingestion & Indic Processing**:
   - Detect script (Latin, Devanagari, Tamil, Telugu, Bengali) using `MultilingualProcessor`.
   - Translate domain terms into technical keywords (e.g. `सौर पैनल` -> `solar photovoltaic`).
2. **Hybrid Semantic Retrieval**:
   - Compute dense vector embeddings using `EmbeddingService` (with automatic offline fallback).
   - Compute lexical fuzzy matching on title, keywords, and IS code numbers.
   - Combine scores using Reciprocal Rank Fusion (RRF) with configurable `hybrid_alpha`.
3. **Allied & Normative Standards Resolution**:
   - Resolve Normative References (mandatory dependent standards).
   - Resolve Test Methods (IS codes for tensile, dielectric, photometric, chemical tests).
   - Resolve Safety & Installation Codes (e.g., `IS 302`, `IS 732`, `IS 14489`).
   - Detect and flag superseded or withdrawn standards (e.g., `IS 1786:1985` -> `IS 1786:2008`).
4. **Mandatory QCO Compliance Enforcement**:
   - Query `QcoRegistry` for active Gazette notifications from DPIIT, Ministry of Steel, MeitY, etc.
   - Enforce mandatory certification schemes:
     - **ISI Mark (Scheme I)**: Require valid BIS CML license in bids.
     - **CRS (Scheme II)**: Require valid R-number registration.
     - **BEE Star Rating**: Enforce energy efficiency labels.
5. **Tender Specification Clause Generation**:
   - Use `TenderClauseGenerator` to construct ready-to-paste GeM/CPPP specification clauses.

## Testing & Verification
- Run full pytest test suite: `python run_all.py --test` or `python -m pytest tests/ -v`.
- Build frontend verification: `cd frontend && npm run build`.
