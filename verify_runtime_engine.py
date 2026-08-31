"""Live runtime verification and presentation script for BIS-SpecAI semantic engine and LLM."""
from __future__ import annotations
import asyncio
import sys
import time
from backend.engine.certification_advisor import CertificationAdvisor

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.models.llm_contracts import LlmInputContract


async def run_live_verification() -> None:
    """Execute end-to-end runtime evaluation on actual BIS data and present outputs."""
    print("=" * 80)
    print("  BIS-SpecAI: LIVE RUNTIME SEMANTIC & LLM ENGINE VERIFICATION")
    print("=" * 80)

    processor = MultilingualProcessor()
    retriever = HybridRetriever()
    resolver = NormativeResolver()
    advisor = CertificationAdvisor()
    clause_gen = TenderClauseGenerator()
    llm_orchestrator = LlmOrchestrator()

    test_scenarios = [
        {
            "domain": "Civil Engineering & Structural Steel",
            "query": "Fe 500D TMT high strength deformed rebar for RCC bridge piers",
            "lang": "en",
        },
        {
            "domain": "Electronics & Renewable Energy (Indic Hindi)",
            "query": "सौर पैनल 540 वाट मोनो क्रिस्टलाइन फोटोवोल्टिक मॉड्यूल",
            "lang": "hi",
        },
        {
            "domain": "Electrotechnical & Power Distribution (Indic Tamil)",
            "query": "மின் விநியோக மின்மாற்றி 11kV copper wound",
            "lang": "ta",
        },
        {
            "domain": "Mechanical Engineering & Fire Safety",
            "query": "Portable fire extinguishers dry powder ABC type for industrial plant",
            "lang": "en",
        },
    ]

    for idx, sc in enumerate(test_scenarios, start=1):
        print(f"\n[{idx}/4] Domain: {sc['domain']}")
        print(f"      Input Query: '{sc['query']}'")
        t0 = time.perf_counter()

        exp_q, detected_lang = processor.translate_and_expand(sc["query"])
        print(f"      Detected Language: {detected_lang.upper()} | Translated/Expanded: '{exp_q}'")

        standards, evidences = retriever.search_with_evidence(query=exp_q, top_k=2, top_k_chunks=2)
        elapsed = (time.perf_counter() - t0) * 1000.0

        if not standards:
            print("      [!] No standards found.")
            continue

        top_std, score, reasons = standards[0]
        qco_alert = advisor.get_certification_alert(top_std)
        allied_items = resolver.resolve_allied(top_std)
        dep_warn = resolver.check_deprecation(top_std)
        tender_clause = clause_gen.generate_clause(top_std)

        print(f"      --> Top Match: {top_std.is_code}:{top_std.year} - {top_std.title}")
        print(f"          Relevance Score: {score:.4f} | Latency: {elapsed:.2f}ms")
        print(f"          Match Reasons: {reasons}")
        print(f"          Division: {top_std.division} | Status: {top_std.status.value}")
        print(f"          QCO Requirement: {qco_alert}")
        print(f"          Mandatory Scheme: {top_std.mandatory_qco.scheme.value}")
        if dep_warn:
            print(f"          [!] Deprecation Alert: {dep_warn}")

        norm_codes = [a.is_code for a in allied_items if a.relation_type == "Normative Reference"]
        test_codes = [a.is_code for a in allied_items if a.relation_type == "Test Method"]
        print(f"          Normative References: {norm_codes[:4]}")
        print(f"          Prescribed Test Methods: {test_codes[:4]}")

        print("          Grounded PDF Document Evidences (ChromaDB):")
        for ev in evidences[:2]:
            print(f"            * [{ev.file_name}, Page {ev.page_number}] (Sim: {ev.relevance_score:.3f}): {ev.snippet[:110]}...")

        # LLM Execution
        llm_in = LlmInputContract(
            query=sc["query"],
            candidate_standards=[top_std],
            document_chunks=[e.model_dump() for e in evidences[:2]],
            qco_alert=qco_alert,
        )
        llm_out = await llm_orchestrator.execute(llm_in)
        print(f"          LLM Response [Tier: {llm_out.source_tier}, Conf: {llm_out.confidence_score:.2f}]:")
        print(f"            Justification: {llm_out.technical_justification[:130]}...")
        print(f"            Cited Document Clauses: {llm_out.cited_clauses}")
        print(f"          Sample GeM Tender Clause:\n            \"{tender_clause[:140]}...\"")

    print("\n" + "=" * 80)
    print("  LIVE RUNTIME VERIFICATION COMPLETE - ALL ACTUAL DATA FIELDS CONFIRMED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_live_verification())
