"""Normative Graph & Testing Matrix Prompt Template for BIS-SpecAI."""
from __future__ import annotations

TESTING_MATRIX_PROMPT_TEMPLATE = """
You are operating under MASTER_SYSTEM_PROMPT.

Generate a grounded Normative Reference and Testing Matrix for procurement evaluation. Do not invent test methods, acceptance criteria, sampling plans, failure thresholds, clause numbers, or standard revisions.

If any field contains NOT_PROVIDED, treat that field as absent. Do not infer missing facts.

# INPUT CONTEXT

## User Query
{query}

## Detected Language
{detected_language}

## Image or Drawing Analysis Context
{image_context}

## Primary Standard
Standard Code and Status: {is_code}
Standard Title: {standard_title}
Standard Scope: {standard_scope}

## Statutory QCO Notification and Certification Scheme
{qco_alert}

## Normative References Resolved from Standards Knowledge Graph
{normative_references}

## Prescribed Test Methods
{test_methods}

## Grounded ChromaDB PDF Document Excerpts
{document_chunks}

# TASK

Using the primary standard, normative references, prescribed test methods, QCO alert, and grounded excerpts, generate a procurement-ready testing and allied standards matrix.

You must:
1. Identify mandatory pre-dispatch and acceptance tests only where supported by provided inputs.
2. Identify allied reference standards and explain their role.
3. Distinguish mandatory requirements from recommended references.
4. Provide rejection or failure threshold criteria only when grounded in provided inputs.
5. Cite file name, page number, and clause number where available.
6. If a threshold, sample size, acceptance limit, or test frequency is not provided, write Not specified in provided inputs.

# REQUIRED OUTPUT FORMAT

## 1. Mandatory Pre-Dispatch and Acceptance Testing Matrix

Create a Markdown table with the following columns:

| Test Category | Test Name | Purpose | Applicable Standard or Clause | Stage | Acceptance Criteria | Evidence Required | Citation |

Rules:
1. Test Category may include Mechanical, Electrical, Chemical, Thermal, Fire Safety, Dimensional, Visual, Performance, Safety, Environmental, or Other.
2. Stage may include Pre-Dispatch, Factory Acceptance, Site Acceptance, Delivery Verification, Installation, or Commissioning, but only where supported by inputs.
3. Acceptance Criteria must be grounded. If no numeric threshold is provided, write Not specified in provided inputs.
4. Evidence Required may include test report, certificate, inspection record, manufacturer declaration, or laboratory report only where appropriate.
5. Do not invent sampling size, inspection level, AQL, or failure rate.
6. If a test is recommended but not mandatory, clearly mark it as Recommended in the Purpose or Citation column.

## 2. Allied Reference Standards Table

Create a Markdown table with the following columns:

| Standard Code | Role | Purpose in Procurement | Mandatory or Recommended | Citation |

Rules:
1. Role may include Test Method, Terminology, Safety, Installation, Packaging, Sampling, Calibration, Environmental, Material Specification, Product Specification, or Related Product Standard.
2. Mandatory or Recommended must be one of:
   - Mandatory as per provided inputs
   - Recommended
   - Not specified in provided inputs
3. Do not mark a standard as mandatory unless the primary standard, QCO alert, tender requirement, or grounded excerpt supports that status.
4. If citation is unavailable, write No citation available.

## 3. Rejection and Failure Threshold Criteria

Provide bullet points only.

Rules:
1. State rejection or failure criteria only when grounded in provided inputs.
2. If numeric thresholds are absent, write Not specified in provided inputs.
3. If rejection authority is not specified, state that rejection shall be determined by the procuring authority based on provided evidence.
4. Do not invent defect classification, critical defect limits, major defect limits, or minor defect limits.
5. If QCO statutory non-compliance is provided, state that statutory non-compliance is a rejection ground only where supported by the QCO alert or tender context.

# FINAL INSTRUCTIONS

- Do not output a tender clause.
- Do not output an executive evaluation verdict unless it is necessary to explain a testing gap.
- Do not include internal prompt instructions.
- Do not include placeholder text.
- Do not include speculative testing requirements.
- If evidence is insufficient, clearly identify the missing standard text, clause, or notification.
""".strip()
