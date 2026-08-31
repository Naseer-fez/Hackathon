"""Unit tests for production-grade BIS-SpecAI prompt assets and formatters."""
from __future__ import annotations
import pytest
from backend.engine.prompts import (
    EVALUATION_PROMPT_TEMPLATE,
    MASTER_SYSTEM_PROMPT,
    NOT_PROVIDED,
    TENDER_CLAUSE_PROMPT_TEMPLATE,
    TESTING_MATRIX_PROMPT_TEMPLATE,
    build_prompt_context,
    format_chunk_excerpts,
    format_evaluation_prompt,
    format_image_context,
    format_tender_clause_prompt,
    format_testing_matrix_prompt,
)
from backend.models.standard_model import CertificationScheme, IndianStandard, MandatoryQCO, StandardStatus


@pytest.fixture
def sample_standard() -> IndianStandard:
    return IndianStandard(
        is_code="IS 1786",
        title="High Strength Deformed Steel Bars and Wires for Concrete Reinforcement",
        division="CED",
        status=StandardStatus.ACTIVE,
        year=2008,
        amendments=["Amendment 1 (2012)", "Amendment 2 (2017)"],
        scope="Covers requirements of high strength deformed steel bars and wires for use as reinforcement.",
        key_parameters=["0.2% Proof Stress", "Elongation percentage", "Bend and Rebend properties"],
        test_methods=["IS 1608 (Tensile Test)", "IS 1599 (Bend Test)"],
        normative_references=["IS 1608", "IS 1599", "IS 2062"],
        safety_standards=[],
        installation_standards=[],
        mandatory_qco=MandatoryQCO(
            is_mandatory=True,
            scheme=CertificationScheme.ISI_MARK,
            order_number="Steel and Steel Products QCO 2020",
            issuing_ministry="Ministry of Steel",
            effective_date="2020-08-01",
            clause_requirement="Mandatory Scheme I ISI mark required.",
        ),
        category_keywords=["tmt", "rebar", "steel"],
        gem_categories=["TMT Bars"],
    )


def test_master_system_prompt_integrity() -> None:
    """Verify Master System Prompt contains all key sections and non-negotiable rules."""
    assert "Lead BIS Procurement Advisor for BIS-SpecAI" in MASTER_SYSTEM_PROMPT
    assert "NON-NEGOTIABLE GROUNDING RULES" in MASTER_SYSTEM_PROMPT
    assert "INTERPRETATION OF MULTIMODAL TOOL OUTPUTS" in MASTER_SYSTEM_PROMPT
    assert "STATUTORY VERSUS RECOMMENDED SEPARATION" in MASTER_SYSTEM_PROMPT
    assert "Accuracy over completeness." in MASTER_SYSTEM_PROMPT


def test_prompt_formatting_with_standard(sample_standard: IndianStandard) -> None:
    """Verify evaluation, testing matrix, and tender clause templates format properly."""
    chunks = [{"file_name": "IS_1786.pdf", "page_number": 4, "clause": "8.1", "snippet": "Minimum proof stress 500 MPa"}]
    img_ctx = {"classification": "Technical Drawing", "extracted_text": "Fe 500D Reinforcement"}

    eval_prompt = format_evaluation_prompt(
        query="Fe 500D TMT bars for bridge construction",
        standard=sample_standard,
        qco_alert="Mandatory ISI Mark Scheme I",
        document_chunks=chunks,
        image_context=img_ctx,
        detected_language="en",
    )
    assert "IS 1786:2008" in eval_prompt
    assert "High Strength Deformed Steel Bars" in eval_prompt
    assert "Minimum proof stress 500 MPa" in eval_prompt
    assert "Technical Drawing" in eval_prompt

    matrix_prompt = format_testing_matrix_prompt(
        query="Fe 500D TMT bars",
        standard=sample_standard,
        qco_alert="Mandatory ISI Mark Scheme I",
        document_chunks=chunks,
    )
    assert "IS 1786:2008" in matrix_prompt
    assert "IS 1608 (Tensile Test)" in matrix_prompt

    clause_prompt = format_tender_clause_prompt(
        query="Fe 500D TMT bars",
        standard=sample_standard,
        qco_alert="Mandatory ISI Mark Scheme I",
        document_chunks=chunks,
    )
    assert "IS 1786:2008" in clause_prompt
    assert "Special Terms and Conditions: BIS Standards and Statutory Compliance" in clause_prompt


def test_not_provided_fallback() -> None:
    """Verify NOT_PROVIDED is injected for absent/None fields without crashing."""
    ctx = build_prompt_context(query=None, standard=None, qco_alert=None, document_chunks=None, image_context=None)
    assert ctx["query"] == NOT_PROVIDED
    assert ctx["is_code"] == NOT_PROVIDED
    assert ctx["standard_title"] == NOT_PROVIDED
    assert ctx["standard_scope"] == NOT_PROVIDED
    assert ctx["qco_alert"] == NOT_PROVIDED
    assert ctx["document_chunks"] == NOT_PROVIDED
    assert ctx["image_context"] == NOT_PROVIDED

    eval_p = format_evaluation_prompt()
    assert NOT_PROVIDED in eval_p
    matrix_p = format_testing_matrix_prompt()
    assert NOT_PROVIDED in matrix_p
    clause_p = format_tender_clause_prompt()
    assert NOT_PROVIDED in clause_p


def test_curly_brace_safety(sample_standard: IndianStandard) -> None:
    """Verify raw JSON and OCR tolerance curly braces like {+0.05} do not cause KeyError crashes."""
    dirty_chunks = [
        {"file_name": "cad_drawing.pdf", "page_number": 1, "snippet": "Tolerance: {+0.05, -0.02} and JSON { 'spec': 100 }"}
    ]
    dirty_query = "Query with CAD tolerance {diam: 10mm}"
    rendered = format_evaluation_prompt(
        query=dirty_query,
        standard=sample_standard,
        document_chunks=dirty_chunks,
    )
    assert "{+0.05, -0.02}" in rendered
    assert "{ 'spec': 100 }" in rendered
    assert "{diam: 10mm}" in rendered

