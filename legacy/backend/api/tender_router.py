"""Router for tender document parsing and compliance auditing."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile
from backend.config.settings import app_settings
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.models.recommendation_model import StandardRecommendation
from backend.models.tender_model import TenderAnalysisReport
from backend.parsers.document_parser import DocumentParser
from backend.parsers.spec_extractor import SpecExtractor

router = APIRouter(prefix="/api/v1", tags=["tenders"])

doc_parser = DocumentParser()
extractor = SpecExtractor()
retriever = HybridRetriever()
resolver = NormativeResolver()
cert_advisor = CertificationAdvisor()
clause_gen = TenderClauseGenerator()


@router.post("/analyze-tender", response_model=TenderAnalysisReport)
async def analyze_tender(
    file: UploadFile | None = File(None),
    raw_text: str | None = Form(None),
) -> TenderAnalysisReport:
    """Analyze tender document or text for Indian Standard compliance."""
    doc_name = "raw_tender_text.txt"
    text_content = ""

    if file and file.filename:
        doc_name = file.filename
        upload_dir = Path(app_settings.storage.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / file.filename
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
        text_content = doc_parser.extract_text_from_file(dest_path)
    elif raw_text:
        text_content = raw_text

    items = extractor.split_into_items(text_content)
    issues = extractor.identify_compliance_issues(items)
    generated_clauses: list[str] = []

    for item in items:
        query = f"{item.product_title} {item.spec_summary}"
        matches = retriever.search(query=query, top_k=2)
        recs: list[StandardRecommendation] = []
        for std, score, reasons in matches:
            allied = resolver.resolve_allied(std)
            dep = resolver.check_deprecation(std)
            alert = cert_advisor.get_certification_alert(std)
            cl = clause_gen.generate_clause(std)
            recs.append(
                StandardRecommendation(
                    standard=std,
                    relevance_score=round(score, 4),
                    match_reasons=reasons,
                    allied_standards=allied,
                    certification_alert=alert,
                    deprecation_warning=dep,
                    sample_tender_clause=cl,
                )
            )
            generated_clauses.append(f"### Item #{item.item_id}: {item.product_title}\n{cl}")
        item.recommended_standards = recs

    qco_count = sum(1 for it in items if it.recommended_standards and it.recommended_standards[0].standard.mandatory_qco.is_mandatory)
    total_recs = len(items) if items else 1
    coverage = round((qco_count / total_recs) * 100.0, 1)

    return TenderAnalysisReport(
        document_name=doc_name,
        extracted_items_count=len(items),
        items=items,
        compliance_issues=issues,
        mandatory_qco_coverage=coverage,
        complete_spec_clause_text="\n\n".join(generated_clauses),
    )
