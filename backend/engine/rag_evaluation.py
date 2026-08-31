"""Automated RAG Triad evaluation using LLM-as-judge."""
import json
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from backend.config.settings import app_settings
from backend.metrics import RAG_CONTEXT_RELEVANCE, RAG_GROUNDEDNESS, RAG_ANSWER_RELEVANCE

from backend.engine.llm_orchestrator import LlmOrchestrator
from backend.engine.pipeline import RecommendationPipeline
from backend.engine.rag_triad_prompts import (
    CONTEXT_RELEVANCE_SYSTEM, CONTEXT_RELEVANCE_PROMPT,
    GROUNDEDNESS_SYSTEM, GROUNDEDNESS_PROMPT,
    ANSWER_RELEVANCE_SYSTEM, ANSWER_RELEVANCE_PROMPT,
    parse_llm_score
)

class RagTriadResult(BaseModel):
    """Result of a single RAG triad evaluation."""
    query: str
    context_relevance_score: float  # 0.0 - 1.0
    groundedness_score: float       # 0.0 - 1.0
    answer_relevance_score: float   # 0.0 - 1.0
    overall_score: float            # average of the three
    evaluation_details: dict[str, str]  # per-metric reasoning
    evaluated_at: str               # ISO timestamp

class RagEvaluator:
    """Automated RAG Triad evaluation using LLM-as-judge."""

    def __init__(self) -> None:
        self._llm = LlmOrchestrator()

    async def evaluate_single(
        self, query: str, retrieved_chunks: list[str], generated_response: str
    ) -> RagTriadResult:
        """Evaluate a single query-response pair against the RAG triad."""
        
        chunks_text = "\n".join(retrieved_chunks) if retrieved_chunks else "None"
        
        # 1. Context Relevance
        prompt_cr = CONTEXT_RELEVANCE_PROMPT.format(query=query, chunks=chunks_text)
        resp_cr = await self._llm.generate_text(prompt_cr, system_prompt=CONTEXT_RELEVANCE_SYSTEM)
        score_cr, reason_cr = parse_llm_score(resp_cr)
        
        # 2. Groundedness
        prompt_gr = GROUNDEDNESS_PROMPT.format(chunks=chunks_text, response=generated_response)
        resp_gr = await self._llm.generate_text(prompt_gr, system_prompt=GROUNDEDNESS_SYSTEM)
        score_gr, reason_gr = parse_llm_score(resp_gr)
        
        # 3. Answer Relevance
        prompt_ar = ANSWER_RELEVANCE_PROMPT.format(query=query, response=generated_response)
        resp_ar = await self._llm.generate_text(prompt_ar, system_prompt=ANSWER_RELEVANCE_SYSTEM)
        score_ar, reason_ar = parse_llm_score(resp_ar)
        
        details = {
            "context_relevance": reason_cr,
            "groundedness": reason_gr,
            "answer_relevance": reason_ar
        }
        
        return RagTriadResult(
            query=query,
            context_relevance_score=score_cr,
            groundedness_score=score_gr,
            answer_relevance_score=score_ar,
            overall_score=(score_cr + score_gr + score_ar) / 3.0,
            evaluation_details=details,
            evaluated_at=datetime.now(datetime.UTC).isoformat() if hasattr(datetime, "UTC") else datetime.utcnow().isoformat()
        )

    async def evaluate_batch(
        self, test_cases: list[dict[str, str]]
    ) -> list[RagTriadResult]:
        """Evaluate a batch of test cases."""
        pipeline = RecommendationPipeline()
        
        results = []
        for case in test_cases:
            query = case.get("query", "")
            
            chunks = case.get("chunks")
            response = case.get("response")
            
            if not chunks or not response:
                try:
                    pipeline_res = await pipeline.process_input(query=query)
                    if not chunks:
                        chunks = [ev.snippet for ev in pipeline_res.document_evidences]
                    if not response:
                        if pipeline_res.llm_analysis:
                            response = pipeline_res.llm_analysis.technical_justification
                        else:
                            response = "No response generated."
                except Exception as e:
                    results.append(RagTriadResult(
                        query=query,
                        context_relevance_score=0.0,
                        groundedness_score=0.0,
                        answer_relevance_score=0.0,
                        overall_score=0.0,
                        evaluation_details={"error": f"SKIPPED: Stack unavailable - {str(e)}"},
                        evaluated_at=datetime.now(datetime.UTC).isoformat() if hasattr(datetime, "UTC") else datetime.utcnow().isoformat()
                    ))
                    continue
                    
            res = await self.evaluate_single(query, chunks or [], response or "No response.")
            results.append(res)
        return results

    async def run_golden_dataset_evaluation(self) -> list[RagTriadResult]:
        """Run evaluation against a predefined golden dataset."""
        golden_path = Path(app_settings.storage.rag_golden_dataset)
        
        if not golden_path.exists():
            return []
            
        try:
            with open(golden_path, "r", encoding="utf-8") as f:
                test_cases = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
            
        results = await self.evaluate_batch(test_cases)
        
        if results:
            avg_context = sum(r.context_relevance_score for r in results) / len(results)
            avg_groundedness = sum(r.groundedness_score for r in results) / len(results)
            avg_answer = sum(r.answer_relevance_score for r in results) / len(results)
            
            RAG_CONTEXT_RELEVANCE.set(avg_context)
            RAG_GROUNDEDNESS.set(avg_groundedness)
            RAG_ANSWER_RELEVANCE.set(avg_answer)
            
        return results
