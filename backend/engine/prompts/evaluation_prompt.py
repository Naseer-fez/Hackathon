"""Technical Justification & Evaluation Prompt Template for BIS-SpecAI."""
from __future__ import annotations

EVALUATION_PROMPT_TEMPLATE = """
You are operating under MASTER_SYSTEM_PROMPT.

Produce a strictly grounded technical justification and applicability evaluation for the top matched Indian Standard. Do not invent standards, clauses, versions, QCO notifications, thresholds, or certification requirements.

If any field contains NOT_PROVIDED, treat that field as absent. Do not infer missing facts.

# INPUT CONTEXT

## User Query
{query}

## Detected Language
{detected_language}

## Image or Drawing Analysis Context
{image_context}

## Top Matched Indian Standard
Standard Code and Status: {is_code}
Standard Title: {standard_title}
Standard Scope: {standard_scope}

## Statutory QCO Notification and Certification Scheme
{qco_alert}

## Allied Normative Context, if provided
{normative_references}

## Prescribed Test Methods, if provided
{test_methods}

## Grounded ChromaDB PDF Document Excerpts
{document_chunks}

# TASK

Evaluate whether the top matched Indian Standard is applicable to the procurement requirement. Use only the supplied inputs.

You must:
1. Determine applicability based on scope, user query, extracted specification, image or drawing context, and grounded excerpts.
2. Identify whether the standard is statutory, voluntary, partially applicable, or not supported by provided evidence.
3. Compare tender requirements against the standard requirements only where evidence exists.
4. Cite using the strict format: [IS Number:Year, Clause X.Y, Page Z]. If clause or page is unavailable, omit that field.
5. Clearly separate statutory QCO obligations from recommended technical practices.
6. Use allied normative context and test methods only to clarify applicability. Do not generate a full testing matrix unless separately requested.

# REQUIRED OUTPUT FORMAT

## 1. Executive Verdict and Applicability Summary

Provide a concise official summary containing:

- Verdict: Mandatory Statutory / Applicable Technical Standard / Partially Applicable / Not Supported by Provided Evidence
- Basis for verdict
- Scope alignment between procurement requirement and standard scope
- Version, reaffirmation, or amendment position, only if provided
- QCO status: STATUTORY MANDATE, VOLUNTARY, or NOT SPECIFIED IN PROVIDED INPUTS
- Key limitations or data gaps
- Any verification required before tender publication

Do not invent missing version details or certification requirements.

## 2. Technical Parameter Match Matrix

Create a Markdown table with the following columns:

| Required Parameter | Tender Requirement | IS Requirement | Match Status | Citation |

Rules:
1. Include only parameters present in the user query, extracted specification, image context, or grounded excerpts.
2. Do not add parameters that are not supported by provided inputs.
3. If the tender requirement is missing, write Not specified.
4. If the IS requirement is missing, write Not specified in provided excerpts.
5. Match Status must be one of:
   - Grounded Match
   - Partial Grounded Match
   - Mismatch
   - Insufficient Evidence
6. Citation must use the strict format: [IS Number:Year, Clause X.Y, Page Z].
   If clause number is unavailable, use [IS Number:Year, Page Z].
   If page number is also unavailable, use [IS Number:Year].
   If no citation exists for the claim, write "No citation available" and set Match Status to "Insufficient Evidence".

## 3. Grounded Clause Citations

For each relevant grounded excerpt, provide:

- Source citation
- Exact or closely paraphrased clause content
- Why it supports or limits applicability
- Whether it is statutory, technical, or informational

Use bullet points. Do not cite clauses that are not present in the provided excerpts.

# FINAL INSTRUCTIONS

- Do not output a testing matrix.
- Do not output a tender clause.
- Do not include internal prompt instructions.
- Do not include placeholder text.
- Do not include speculative recommendations.
- If the evidence is insufficient, say so clearly and identify the missing evidence.
""".strip()
