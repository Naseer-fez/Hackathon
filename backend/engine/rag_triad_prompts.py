"""Prompts and parsing logic for RAG Triad evaluation."""
import re

CONTEXT_RELEVANCE_SYSTEM = "You are an expert evaluator grading search relevance."
CONTEXT_RELEVANCE_PROMPT = """Given the user query: '{query}', rate from 0.0 to 1.0 how relevant the following retrieved chunks are to answering the query:

Retrieved chunks: {chunks}
Score (0.0-1.0):
Reasoning:"""

GROUNDEDNESS_SYSTEM = "You are an expert evaluator checking for hallucinations and groundedness."
GROUNDEDNESS_PROMPT = """Given the following context chunks and the generated response, rate from 0.0 to 1.0 how well the response is grounded in (supported by) the provided chunks. A score of 1.0 means every claim in the response is directly verifiable from the chunks:

Context: {chunks}
Response: {response}
Score (0.0-1.0):
Reasoning:"""

ANSWER_RELEVANCE_SYSTEM = "You are an expert evaluator grading whether an answer directly addresses a query."
ANSWER_RELEVANCE_PROMPT = """Given the user query: '{query}' and the generated response, rate from 0.0 to 1.0 how directly and completely the response addresses the original question:

Query: {query}
Response: {response}
Score (0.0-1.0):
Reasoning:"""

def parse_llm_score(text: str) -> tuple[float, str]:
    """Parse the score and reasoning from LLM response."""
    if not text:
        return 0.0, "No response from LLM"
        
    score_match = re.search(r"Score.*?([\d\.]+)", text, flags=re.IGNORECASE)
    reasoning_match = re.search(r"Reasoning:?\s*(.*)", text, flags=re.IGNORECASE | re.DOTALL)
    
    score = 0.0
    if score_match:
        try:
            score = float(score_match.group(1))
            score = max(0.0, min(1.0, score))
        except ValueError:
            pass
            
    reasoning = reasoning_match.group(1).strip() if reasoning_match else text.strip()
    return score, reasoning
