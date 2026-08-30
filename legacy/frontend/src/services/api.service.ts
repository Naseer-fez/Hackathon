import type { GraphData, IndianStandard, MandatoryQCO, RecommendationResponse, TenderAnalysisReport } from "../types";

const API_BASE = "/api/v1";

export async function fetchRecommendations(
  query: string,
  division?: string,
  top_k: number = 5
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_BASE}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, division, top_k }),
  });
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}

export async function analyzeTenderDocument(
  file?: File,
  rawText?: string
): Promise<TenderAnalysisReport> {
  const formData = new FormData();
  if (file) formData.append("file", file);
  if (rawText) formData.append("raw_text", rawText);

  const res = await fetch(`${API_BASE}/analyze-tender`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to analyze tender document");
  return res.json();
}

export async function fetchStandards(
  division?: string,
  query?: string
): Promise<IndianStandard[]> {
  const params = new URLSearchParams();
  if (division) params.append("division", division);
  if (query) params.append("query", query);
  const res = await fetch(`${API_BASE}/standards?${params.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch standards");
  return res.json();
}

export async function fetchKnowledgeGraph(): Promise<GraphData> {
  const res = await fetch(`${API_BASE}/graph`);
  if (!res.ok) throw new Error("Failed to fetch graph data");
  return res.json();
}

export async function fetchQcoList(): Promise<Record<string, MandatoryQCO>> {
  const res = await fetch(`${API_BASE}/qco-list`);
  if (!res.ok) throw new Error("Failed to fetch QCO list");
  return res.json();
}

export async function simulateGemBid(
  bidId: string,
  category: string,
  title: string,
  spec: string
): Promise<{
  bid_id: string;
  status: string;
  compliance_score: number;
  primary_standard: string;
  is_qco_mandatory: boolean;
  qco_order: string;
  recommended_clause: string;
  allied_standards: string[];
}> {
  const res = await fetch(`${API_BASE}/gem-webhook`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      bid_id: bidId,
      category_name: category,
      product_title: title,
      buyer_specifications: spec,
    }),
  });
  if (!res.ok) throw new Error("Failed to validate GeM bid");
  return res.json();
}
