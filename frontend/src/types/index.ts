export interface MandatoryQCO {
  is_mandatory: boolean;
  scheme: string;
  order_number: string;
  issuing_ministry: string;
  effective_date: string;
  clause_requirement: string;
}

export interface IndianStandard {
  is_code: string;
  title: string;
  division: string;
  status: string;
  superseded_by?: string | null;
  year: number;
  reaffirmation_year?: number | null;
  amendments: string[];
  scope: string;
  key_parameters: string[];
  test_methods: string[];
  normative_references: string[];
  safety_standards: string[];
  installation_standards: string[];
  mandatory_qco: MandatoryQCO;
  category_keywords: string[];
  gem_categories: string[];
}

export interface AlliedStandardItem {
  is_code: string;
  title: string;
  relation_type: string;
  status: string;
  is_mandatory: boolean;
  details: string;
}

export interface StandardRecommendation {
  standard: IndianStandard;
  relevance_score: number;
  match_reasons: string[];
  allied_standards: AlliedStandardItem[];
  certification_alert: string;
  deprecation_warning?: string | null;
  sample_tender_clause: string;
}

export interface RecommendationResponse {
  query: string;
  detected_language: string;
  translated_query: string;
  total_matches: number;
  recommendations: StandardRecommendation[];
  latency_ms: number;
}

export interface ImageClassificationResult {
  category: string;
  confidence: number;
  dimensions: [number, number];
  aspect_ratio: number;
  is_technical_drawing: boolean;
  extracted_text: string;
  technical_attributes?: Record<string, unknown>;
}

export interface LlmStandardizedResponse {
  query: string;
  primary_is_code: string;
  primary_title: string;
  technical_justification: string;
  qco_compliance_verdict: string;
  mandatory_test_methods: string[];
  allied_standards_summary: string[];
  confidence_score: number;
  source_tier: string;
}

export interface PipelineResponse {
  query: string;
  detected_language: string;
  extracted_text_snippet?: string;
  image_analysis?: ImageClassificationResult | null;
  recommendations: StandardRecommendation[];
  llm_analysis?: LlmStandardizedResponse | null;
  voice_audio_base64?: string | null;
}

export interface ExtractedLineItem {
  item_id: number;
  product_title: string;
  spec_summary: string;
  cited_standards: string[];
  outdated_citations: string[];
  recommended_standards: StandardRecommendation[];
}

export interface ComplianceIssue {
  severity: "HIGH" | "MEDIUM" | "LOW";
  category: string;
  issue_text: string;
  corrective_action: string;
}

export interface TenderAnalysisReport {
  document_name: string;
  extracted_items_count: number;
  items: ExtractedLineItem[];
  compliance_issues: ComplianceIssue[];
  mandatory_qco_coverage: number;
  complete_spec_clause_text: string;
  raw_text?: string;
}

export interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    title: string;
    division: string;
    is_mandatory: boolean;
    status: string;
  }>;
  edges: Array<{
    source: string;
    target: string;
    relation: string;
  }>;
}
