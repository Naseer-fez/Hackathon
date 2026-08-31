"""Safe prompt context builder and template formatters for BIS-SpecAI."""
from __future__ import annotations
from typing import Any
from backend.engine.prompts.evaluation_prompt import EVALUATION_PROMPT_TEMPLATE
from backend.engine.prompts.tender_clause_prompt import TENDER_CLAUSE_PROMPT_TEMPLATE
from backend.engine.prompts.testing_matrix_prompt import TESTING_MATRIX_PROMPT_TEMPLATE
from backend.models.standard_model import IndianStandard

NOT_PROVIDED = "NOT_PROVIDED"


def format_chunk_excerpts(chunks: list[Any] | None) -> str:
    """Format document chunk excerpts into structured citation lines or NOT_PROVIDED."""
    if not chunks:
        return NOT_PROVIDED
    lines: list[str] = []
    for c in chunks[:5]:
        fn = getattr(c, "file_name", None) or (c.get("file_name") if isinstance(c, dict) else "Doc")
        pg = getattr(c, "page_number", None) or (c.get("page_number") if isinstance(c, dict) else 1)
        cl = getattr(c, "clause", None) or (c.get("clause") if isinstance(c, dict) else None)
        snip = (getattr(c, "snippet", None) or (c.get("snippet") if isinstance(c, dict) else ""))[:250].strip()
        cl_str = f", Clause {cl}" if cl else ""
        lines.append(f"- [Source: {fn}, Page {pg}{cl_str}]: {snip}")
    return "\n".join(lines) if lines else NOT_PROVIDED


def format_image_context(img: Any | None) -> str:
    """Format image classification / drawing context or return NOT_PROVIDED."""
    if not img:
        return NOT_PROVIDED
    if isinstance(img, dict):
        cat = img.get("category") or img.get("classification")
        txt = img.get("extracted_text")
        conf = img.get("confidence")
        parts = [f"Classification: {cat}"] if cat else []
        if conf is not None:
            parts.append(f"Confidence: {conf}")
        if txt:
            parts.append(f"Extracted Text/Callouts: {txt[:300]}")
        return "\n".join(parts) if parts else NOT_PROVIDED
    cat = getattr(img, "category", None)
    txt = getattr(img, "extracted_text", None)
    return f"Classification: {cat}\nExtracted Text: {txt[:300]}" if (cat or txt) else NOT_PROVIDED


def build_prompt_context(
    query: str | None = None,
    standard: IndianStandard | None = None,
    qco_alert: str | None = None,
    document_chunks: list[Any] | None = None,
    image_context: Any | None = None,
    detected_language: str | None = None,
    normative_references: list[str] | str | None = None,
    test_methods: list[str] | str | None = None,
) -> dict[str, str]:
    """Construct a complete, safe formatting dictionary with NOT_PROVIDED fallbacks."""
    norm = normative_references or (standard.normative_references if standard else None)
    norm_str = ", ".join(norm) if isinstance(norm, list) and norm else (str(norm) if norm else NOT_PROVIDED)
    tests = test_methods or (standard.test_methods if standard else None)
    test_str = ", ".join(tests) if isinstance(tests, list) and tests else (str(tests) if tests else NOT_PROVIDED)
    code_str = f"{standard.is_code}:{standard.year}" if (standard and standard.year) else (standard.is_code if standard else NOT_PROVIDED)

    return {
        "query": query.strip() if query and query.strip() else NOT_PROVIDED,
        "detected_language": detected_language.strip() if detected_language and detected_language.strip() else "en",
        "image_context": format_image_context(image_context),
        "is_code": code_str,
        "standard_title": standard.title.strip() if (standard and standard.title) else NOT_PROVIDED,
        "standard_scope": standard.scope.strip() if (standard and standard.scope) else NOT_PROVIDED,
        "qco_alert": qco_alert.strip() if (qco_alert and qco_alert.strip()) else NOT_PROVIDED,
        "normative_references": norm_str,
        "test_methods": test_str,
        "document_chunks": format_chunk_excerpts(document_chunks),
    }


def safe_inject(template: str, context: dict[str, str]) -> str:
    """Safely replace {key} placeholders without str.format() KeyError crashes on literal braces."""
    rendered = template
    for key, val in context.items():
        safe_val = str(val) if val and str(val).strip() else NOT_PROVIDED
        rendered = rendered.replace(f"{{{key}}}", safe_val)
    return rendered


def format_evaluation_prompt(**kwargs: Any) -> str:
    """Format EVALUATION_PROMPT_TEMPLATE using safe placeholder injection."""
    return safe_inject(EVALUATION_PROMPT_TEMPLATE, build_prompt_context(**kwargs))


def format_testing_matrix_prompt(**kwargs: Any) -> str:
    """Format TESTING_MATRIX_PROMPT_TEMPLATE using safe placeholder injection."""
    return safe_inject(TESTING_MATRIX_PROMPT_TEMPLATE, build_prompt_context(**kwargs))


def format_tender_clause_prompt(**kwargs: Any) -> str:
    """Format TENDER_CLAUSE_PROMPT_TEMPLATE using safe placeholder injection."""
    return safe_inject(TENDER_CLAUSE_PROMPT_TEMPLATE, build_prompt_context(**kwargs))

