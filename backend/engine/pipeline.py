"""Unified multi-modal pipeline for Indian Standards recommendation and QCO compliance."""
from __future__ import annotations
import base64
import tempfile
from pydantic import BaseModel, Field
from backend.engine.certification_advisor import CertificationAdvisor
from backend.engine.hybrid_retriever import HybridRetriever
from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.engine.multilingual_processor import MultilingualProcessor
from backend.engine.normative_resolver import NormativeResolver
from backend.engine.tender_clause_generator import TenderClauseGenerator
from backend.engine.voice_service import VoiceService
from backend.models.llm_contracts import LlmInputContract, LlmStandardizedResponse
from backend.models.recommendation_model import DocumentChunkEvidence, StandardRecommendation
from backend.parsers.document_parser import DocumentParser
from backend.parsers.image_classifier import ImageClassificationResult, ImageClassifier


class PipelineResponse(BaseModel):
    """Unified response contract for multi-modal standard identification."""
    query: str
    detected_language: str
    extracted_text_snippet: str = ""
    image_analysis: ImageClassificationResult | None = None
    recommendations: list[StandardRecommendation] = Field(default_factory=list)
    document_evidences: list[DocumentChunkEvidence] = Field(default_factory=list)
    llm_analysis: LlmStandardizedResponse | None = None
    voice_audio_base64: str | None = None


class RecommendationPipeline:
    """End-to-end multi-modal recommendation engine orchestrator."""

    def __init__(self) -> None:
        self._multi = MultilingualProcessor()
        self._retriever = HybridRetriever()
        self._resolver = NormativeResolver()
        self._advisor = CertificationAdvisor()
        self._clause_gen = TenderClauseGenerator()
        self._doc_parser = DocumentParser()
        self._image_clf = ImageClassifier()
        self._voice_svc = VoiceService()
        self._llm = LlmOrchestrator()

    async def process_input(
        self, query: str | None = None, pdf_bytes: bytes | None = None,
        image_bytes: bytes | None = None, audio_bytes: bytes | None = None,
        division: str | None = None, generate_voice_response: bool = False,
    ) -> PipelineResponse:
        """Process any input modality and produce standardized recommendations."""
        raw_parts: list[str] = []
        eff_query = (query or "").strip()
        img_res: ImageClassificationResult | None = None

        if audio_bytes:
            txt = self._voice_svc.transcribe_audio(audio_bytes)
            if txt:
                eff_query = f"{eff_query} {txt}".strip()
        if image_bytes:
            img_res = self._image_clf.classify(image_bytes)
            if img_res.extracted_text:
                raw_parts.append(img_res.extracted_text)
        if pdf_bytes:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                ptxt = self._doc_parser.extract_text_from_pdf(tmp.name)
                if ptxt:
                    raw_parts.append(ptxt)

        comb_txt = " ".join(raw_parts)
        sq = eff_query or (comb_txt[:300] if comb_txt else "General Indian Standards")
        exp_q, lang = self._multi.translate_and_expand(sq)
        matches, evidences = self._retriever.search_with_evidence(query=exp_q, division=division, top_k=5, top_k_chunks=5)

        recs = [
            StandardRecommendation(
                standard=s, relevance_score=round(sc, 4), match_reasons=rs,
                allied_standards=self._resolver.resolve_allied(s),
                document_evidences=[e for e in evidences if e.matched_standard == s.is_code] or evidences[:2],
                certification_alert=self._advisor.get_certification_alert(s),
                deprecation_warning=self._resolver.check_deprecation(s), sample_tender_clause=self._clause_gen.generate_clause(s),
            )
            for s, sc, rs in matches
        ]
        llm_in = LlmInputContract(
            query=sq, extracted_text=comb_txt, detected_language=lang,
            candidate_standards=[m[0] for m in matches], document_chunks=[e.model_dump() for e in evidences],
            image_context=img_res.model_dump() if img_res else {}, qco_alert=recs[0].certification_alert if recs else "",
        )
        llm_out = await self._llm.execute(llm_in)
        v_b64 = base64.b64encode(self._voice_svc.synthesize_speech(llm_out.technical_justification)).decode("ascii") if (generate_voice_response and llm_out) else None

        return PipelineResponse(
            query=sq, detected_language=lang, extracted_text_snippet=comb_txt[:300],
            image_analysis=img_res, recommendations=recs, document_evidences=evidences,
            llm_analysis=llm_out, voice_audio_base64=v_b64,
        )
