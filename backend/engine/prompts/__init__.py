"""Production-grade prompt assets and formatters for BIS-SpecAI."""
from __future__ import annotations

from backend.engine.prompts.evaluation_prompt import EVALUATION_PROMPT_TEMPLATE
from backend.engine.prompts.prompt_formatter import (
    NOT_PROVIDED,
    build_prompt_context,
    format_chunk_excerpts,
    format_evaluation_prompt,
    format_image_context,
    format_tender_clause_prompt,
    format_testing_matrix_prompt,
)
from backend.engine.prompts.system_prompt import MASTER_SYSTEM_PROMPT
from backend.engine.prompts.tender_clause_prompt import TENDER_CLAUSE_PROMPT_TEMPLATE
from backend.engine.prompts.testing_matrix_prompt import TESTING_MATRIX_PROMPT_TEMPLATE

__all__ = [
    "MASTER_SYSTEM_PROMPT",
    "EVALUATION_PROMPT_TEMPLATE",
    "TESTING_MATRIX_PROMPT_TEMPLATE",
    "TENDER_CLAUSE_PROMPT_TEMPLATE",
    "NOT_PROVIDED",
    "build_prompt_context",
    "format_chunk_excerpts",
    "format_image_context",
    "format_evaluation_prompt",
    "format_testing_matrix_prompt",
    "format_tender_clause_prompt",
]
