const API_BASE = "http://127.0.0.1:8000";

export interface DocumentItem {
  document_id: string;
  filename: string;
  stored_filename?: string;
  status: "uploaded" | "processing" | "processed" | "failed";
  page_count: number;
  word_count: number;
  character_count: number;
  chunk_count: number;
  file_size_bytes?: number;
  is_scanned: boolean;
  uploaded_at: string;
  processed_at?: string;
  error?: string;
}

export interface DocumentListResponse {
  total: number;
  skip: number;
  limit: number;
  documents: DocumentItem[];
}

export interface SearchHit {
  document_id: string;
  document_name: string;
  page_number: number;
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchHit[];
  total: number;
}

export interface SourceCitation {
  document_id: string;
  document_name: string;
  page_number: number;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  query: string;
  answer: string;
  sources: SourceCitation[];
}

export interface SummaryResponse {
  document_id: string;
  filename: string;
  page_count: number;
  word_count: number;
  summary: string;
}

export interface ExtractedData {
  document_type?: string;
  title_or_subject?: string;
  parties_or_entities?: string[];
  important_dates?: { date: string; description: string }[];
  financial_terms?: { term: string; details: string }[];
  obligations_and_duties?: string[];
  key_clauses?: { type: string; summary: string }[];
  summary_entities?: string[];
  [key: string]: any;
}

export interface ExtractionResponse {
  document_id: string;
  filename: string;
  extracted_data: ExtractedData;
}

export interface ComparisonResponse {
  document_a: { document_id: string; filename: string; page_count: number };
  document_b: { document_id: string; filename: string; page_count: number };
  comparison: string;
}

// ── API Methods ─────────────────────────────────────────────────────────────

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchDocuments(): Promise<DocumentListResponse> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function fetchDocumentDetail(docId: string): Promise<DocumentItem & { chroma_chunk_count: number; file_on_disk: boolean }> {
  const res = await fetch(`${API_BASE}/documents/${docId}`);
  if (!res.ok) throw new Error("Failed to fetch document details");
  return res.json();
}

export async function deleteDocument(docId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete document");
  return res.json();
}

export async function reprocessDocument(docId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/documents/${docId}/reprocess`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reprocess document");
  return res.json();
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function searchDocuments(query: string, docId: string = "all"): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(query)}&document_id=${encodeURIComponent(docId)}`);
  if (!res.ok) throw new Error("Search request failed");
  return res.json();
}

export async function askAI(query: string, docId: string = "all"): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat?query=${encodeURIComponent(query)}&document_id=${encodeURIComponent(docId)}`);
  if (!res.ok) throw new Error("Chat request failed");
  return res.json();
}

export async function fetchSummary(docId: string): Promise<SummaryResponse> {
  const res = await fetch(`${API_BASE}/summarize/${docId}`, { method: "POST" });
  if (!res.ok) throw new Error("Summarization failed");
  return res.json();
}

export async function fetchExtraction(docId: string): Promise<ExtractionResponse> {
  const res = await fetch(`${API_BASE}/extract/${docId}`, { method: "POST" });
  if (!res.ok) throw new Error("Extraction failed");
  return res.json();
}

export async function compareDocuments(docIdA: string, docIdB: string): Promise<ComparisonResponse> {
  const res = await fetch(`${API_BASE}/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id_a: docIdA, document_id_b: docIdB }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Comparison failed" }));
    throw new Error(err.detail || "Comparison failed");
  }
  return res.json();
}