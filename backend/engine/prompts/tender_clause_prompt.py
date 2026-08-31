"""Ready-to-Publish GeM Tender Specification Clause Template for BIS-SpecAI."""
from __future__ import annotations

TENDER_CLAUSE_PROMPT_TEMPLATE = """
You are operating under MASTER_SYSTEM_PROMPT.

Generate a copy-paste ready GeM or CPPP Special Terms and Conditions clause for BIS standards conformance and statutory compliance.

Do not invent QCO notification numbers, ministry notifications, BIS license numbers, CRS R-numbers, test thresholds, warranty periods, penalty percentages, or legal citations.

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

## Allied Normative References
{normative_references}

## Prescribed Test Methods
{test_methods}

## Grounded ChromaDB PDF Document Excerpts
{document_chunks}

# DRAFTING RULES

1. Output formal procurement English suitable for GeM, CPPP, departmental tenders, and official note-sheets.
2. Use shall for mandatory requirements.
3. Use should only for clearly recommended practices.
4. Do not include placeholder text, bracketed instructions, or draft notes in the final clause.
5. Do not invent statutory citations. Include notification details only if present in the QCO alert.
6. If the QCO alert indicates no statutory mandate, Clause 2 must state that statutory QCO licensing is not applicable based on provided inputs.
7. If the QCO alert indicates Scheme I, refer to valid BIS ISI mark or BIS product certification license as provided.
8. If the QCO alert indicates Scheme II, refer to valid BIS CRS registration or R-number as provided.
9. If the QCO alert indicates BEE Star Rating, include the requirement only if the provided alert makes it applicable.
10. Do not impose penalty percentages, liquidated damages rates, or warranty durations unless provided.
11. The output must contain only the five requested clauses.
12. Do not include internal prompt instructions.
13. Do not include speculative legal advice.
14. If a required detail is missing, use neutral procurement language such as as specified in the tender document or as per applicable procurement rules, but do not invent facts.

# REQUIRED OUTPUT FORMAT

Generate the clause under the following heading:

## Special Terms and Conditions: BIS Standards and Statutory Compliance

Then provide exactly five clauses.

### Clause 1: Mandatory BIS Standards Conformance

Draft a clause requiring that the supplied product, material, or service shall conform to the applicable Indian Standard or standards identified in the tender.

Include:
- Reference to the primary standard where provided
- Reference to amendments or reaffirmation status only where provided
- Requirement that equivalent standards must not be substituted unless expressly permitted by the tender
- Requirement that technical specifications, marking, testing, and acceptance shall follow the cited standard where provided

Do not invent additional standards.

### Clause 2: Statutory QCO License Mandate

Draft a clause based strictly on the QCO alert.

If the QCO alert indicates Scheme I:
- Require valid BIS ISI mark or BIS product certification license where applicable
- Require submission of license evidence as per tender process

If the QCO alert indicates Scheme II:
- Require valid BIS CRS registration or R-number where applicable
- Require submission of registration evidence as per tender process

If the QCO alert indicates BEE Star Rating:
- Require the specified BEE compliance only if the alert makes it applicable

If the QCO alert indicates Voluntary or NOT_PROVIDED:
- State that no statutory QCO license mandate is established by the provided inputs
- Do not impose mandatory BIS licensing language unless the tender authority separately specifies it

Include notification details only if present in the QCO alert.

### Clause 3: Test Certificate Verification

Draft a clause requiring test evidence only where supported by provided inputs.

Include:
- Requirement for test reports from NABL accredited or BIS recognized laboratories where applicable
- Reference to prescribed test methods where provided
- Requirement that test reports shall be traceable to the offered product, batch, lot, model, or serial number where applicable
- Requirement that the procuring authority may verify test certificates or conduct third-party verification
- Requirement that test certificates shall be valid at the time of submission and delivery, unless otherwise specified in the tender

Do not invent test thresholds or laboratory names.

### Clause 4: Product Marking, ISI or CRS Logo, and Traceability

Draft a clause requiring marking and traceability only where applicable.

Include:
- ISI mark or CRS marking requirement only where the QCO alert or provided standard excerpt supports it
- Marking of manufacturer name, standard number, license or registration number, batch, lot, model, month and year of manufacture, or other traceability fields only where applicable
- Requirement that markings shall be legible, indelible, and consistent with certification evidence where applicable
- Requirement that traceability documents shall link delivery items to test certificates and certification evidence where applicable

Do not invent marking requirements not supported by provided inputs.

### Clause 5: Rejection, Guarantee, and Non-Compliance Penalty Protocol

Draft a firm but non-fabricated clause.

Include:
- Right of the procuring authority to reject non-conforming goods
- Requirement for replacement or rectification where non-compliance is established
- Reference to guarantee or warranty only as per tender document if no specific period is provided
- Consequences for statutory non-compliance, including rejection and action under applicable procurement rules, only where supported by inputs
- Non-compliance penalty protocol without inventing percentages or monetary values

Use neutral language such as:
- as per applicable contract terms
- as per GeM or CPPP rules
- as per tender document
- as per applicable law

Do not invent penalty rates.

# FINAL OUTPUT REQUIREMENT

Output only the heading and the five clauses. Do not add explanations, disclaimers, notes, or placeholders.
""".strip()
