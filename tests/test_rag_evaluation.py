"""Tests for automated RAG Triad evaluation."""
import json
import pytest
from pathlib import Path
from backend.engine.rag_evaluation import RagEvaluator, RagTriadResult
from backend.config.settings import app_settings

from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
@patch("backend.engine.rag_evaluation.LlmOrchestrator")
async def test_evaluate_single(mock_llm_class) -> None:
    """Test evaluation of a single query-response pair."""
    # Setup mock
    mock_llm = AsyncMock()
    mock_llm.generate_text.return_value = "Score: 0.9\nReasoning: This is a test reason."
    mock_llm_class.return_value = mock_llm
    
    evaluator = RagEvaluator()
    result = await evaluator.evaluate_single(
        query="What BIS standard applies to TMT steel bars?",
        retrieved_chunks=["IS 1786 covers TMT steel bars"],
        generated_response="The standard for TMT steel bars is IS 1786."
    )
    
    assert isinstance(result, RagTriadResult)
    assert 0.0 <= result.context_relevance_score <= 1.0
    assert 0.0 <= result.groundedness_score <= 1.0
    assert 0.0 <= result.answer_relevance_score <= 1.0
    assert 0.0 <= result.overall_score <= 1.0
    
    assert "context_relevance" in result.evaluation_details
    assert "groundedness" in result.evaluation_details
    assert "answer_relevance" in result.evaluation_details
    assert result.query == "What BIS standard applies to TMT steel bars?"
    assert mock_llm.generate_text.call_count == 3

@pytest.mark.asyncio
@patch("backend.engine.rag_evaluation.RecommendationPipeline")
@patch("backend.engine.rag_evaluation.LlmOrchestrator")
async def test_run_golden_dataset_evaluation(mock_llm_class, mock_pipeline_class) -> None:
    """Test that golden dataset evaluation parses the JSON and runs."""
    mock_llm = AsyncMock()
    mock_llm.generate_text.return_value = "Score: 0.95\nReasoning: Golden."
    mock_llm_class.return_value = mock_llm
    
    mock_pipeline = AsyncMock()
    # Provide a minimal mock PipelineResponse
    mock_pipeline_res = AsyncMock()
    mock_pipeline_res.document_evidences = [AsyncMock(snippet="Mock snippet for evidence")]
    mock_pipeline_res.llm_analysis = AsyncMock(technical_justification="Mock justification")
    mock_pipeline.process_input.return_value = mock_pipeline_res
    mock_pipeline_class.return_value = mock_pipeline
    
    # Ensure the golden dataset file exists for the test
    dataset_path = Path(app_settings.storage.rag_golden_dataset)
    assert dataset_path.exists(), f"Golden dataset missing at {dataset_path}"
    
    # Verify JSON parses correctly
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) >= 5
    assert "query" in data[0]
    assert "expected_standard" in data[0]
    
    # Run the evaluator
    evaluator = RagEvaluator()
    results = await evaluator.run_golden_dataset_evaluation()
    
    assert len(results) == len(data)
    assert isinstance(results[0], RagTriadResult)
