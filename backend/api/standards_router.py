"""Router for browsing Indian Standards, QCOs, and knowledge graph."""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from backend.ingestion.qco_registry import QcoRegistry
from backend.ingestion.standards_loader import StandardsLoader
from backend.models.standard_model import IndianStandard, MandatoryQCO

router = APIRouter(prefix="/api/v1", tags=["standards"])

loader = StandardsLoader()
qco_reg = QcoRegistry()


@router.get("/standards", response_model=list[IndianStandard])
async def list_standards(
    division: str | None = None,
    query: str | None = None,
) -> list[IndianStandard]:
    """Retrieve Indian Standards with optional division or text filter."""
    standards = loader.get_all_standards()
    if division:
        standards = [s for s in standards if s.division.upper() == division.upper()]
    if query:
        q = query.lower()
        standards = [
            s for s in standards
            if q in s.is_code.lower() or q in s.title.lower() or any(q in kw for kw in s.category_keywords)
        ]
    return standards


@router.get("/standards/{is_code}", response_model=IndianStandard)
async def get_standard_by_code(is_code: str) -> IndianStandard:
    """Retrieve single Indian Standard details by IS code."""
    std = loader.get_by_code(is_code)
    if not std:
        raise HTTPException(status_code=404, detail=f"Standard '{is_code}' not found")
    return std


@router.get("/qco-list", response_model=dict[str, MandatoryQCO])
async def list_qcos() -> dict[str, MandatoryQCO]:
    """Retrieve all active Quality Control Orders."""
    return qco_reg.get_all_qcos()


@router.get("/graph", response_model=dict[str, list[dict[str, Any]]])
async def get_knowledge_graph() -> dict[str, list[dict[str, Any]]]:
    """Generate node-link graph data for standard relationship visualization."""
    standards = loader.get_all_standards()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    for s in standards:
        if s.is_code not in seen_nodes:
            nodes.append({"id": s.is_code, "label": s.is_code, "title": s.title, "division": s.division, "is_mandatory": s.mandatory_qco.is_mandatory, "status": s.status.value})
            seen_nodes.add(s.is_code)

        for norm in s.normative_references:
            if norm not in seen_nodes:
                nodes.append({"id": norm, "label": norm, "title": f"Normative Ref {norm}", "division": s.division, "is_mandatory": True, "status": "Active"})
                seen_nodes.add(norm)
            edges.append({"source": s.is_code, "target": norm, "relation": "Normative Reference"})

        for test in s.test_methods:
            code = test.split("(")[0].strip()
            if code not in seen_nodes:
                nodes.append({"id": code, "label": code, "title": test, "division": s.division, "is_mandatory": False, "status": "Active"})
                seen_nodes.add(code)
            edges.append({"source": s.is_code, "target": code, "relation": "Test Method"})

        if s.superseded_by:
            edges.append({"source": s.is_code, "target": s.superseded_by, "relation": "Superseded By"})

    return {"nodes": nodes, "edges": edges}
