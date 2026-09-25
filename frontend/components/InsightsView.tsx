"use client";

import React, { useState, useEffect } from "react";
import {
  fetchSummary,
  fetchExtraction,
  DocumentItem,
  SummaryResponse,
  ExtractionResponse,
} from "@/lib/api";
import {
  Sparkles,
  FileText,
  Calendar,
  Building2,
  DollarSign,
  ShieldAlert,
  ListChecks,
  FileSearch,
} from "lucide-react";

interface InsightsViewProps {
  documents: DocumentItem[];
  selectedDocId: string;
  setSelectedDocId: (id: string) => void;
}

export default function InsightsView({
  documents,
  selectedDocId,
  setSelectedDocId,
}: InsightsViewProps) {
  const [activeTab, setActiveTab] = useState<"summary" | "extraction">("summary");
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
  const [extractionData, setExtractionData] = useState<ExtractionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const loadData = async (docId: string) => {
    if (!docId) return;
    setLoading(true);
    try {
      if (activeTab === "summary") {
        const sum = await fetchSummary(docId);
        setSummaryData(sum);
      } else {
        const ext = await fetchExtraction(docId);
        setExtractionData(ext);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedDocId && selectedDocId !== "all") {
      loadData(selectedDocId);
    }
  }, [selectedDocId, activeTab]);

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Document Intelligence & Insights
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Automated executive summarization and structured entity/clause extraction.
        </p>
      </div>

      {/* Selector & Sub-tab Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-500" />
          <span className="text-xs text-slate-500 font-medium">Select Document:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-w-xs truncate"
          >
            <option value="">Choose a document...</option>
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                {d.filename}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl">
          <button
            onClick={() => setActiveTab("summary")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "summary"
                ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Executive Summary
          </button>
          <button
            onClick={() => setActiveTab("extraction")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "extraction"
                ? "bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Structured Extraction
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {!selectedDocId || selectedDocId === "all" ? (
        <div className="p-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-center text-slate-400 text-sm">
          Please select a document from the dropdown above to view insights.
        </div>
      ) : loading ? (
        <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
          <Sparkles className="w-6 h-6 text-indigo-500 animate-spin" />
          <span>Analyzing document & extracting insights...</span>
        </div>
      ) : activeTab === "summary" && summaryData ? (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="font-bold text-slate-900 dark:text-white text-base">
              {summaryData.filename}
            </h3>
            <span className="text-xs text-slate-400">
              {summaryData.page_count} pages · {summaryData.word_count} words
            </span>
          </div>
          <div className="text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
            {summaryData.summary}
          </div>
        </div>
      ) : activeTab === "extraction" && extractionData ? (
        <div className="space-y-4">
          {/* Top Metadata Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl shadow-sm flex items-center gap-3">
              <FileSearch className="w-8 h-8 text-indigo-500" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Document Type</p>
                <p className="font-bold text-slate-900 dark:text-white text-sm">
                  {extractionData.extracted_data.document_type || "N/A"}
                </p>
              </div>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl shadow-sm flex items-center gap-3">
              <Building2 className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Identified Parties</p>
                <p className="font-bold text-slate-900 dark:text-white text-sm">
                  {extractionData.extracted_data.parties_or_entities?.join(", ") || "None"}
                </p>
              </div>
            </div>
          </div>

          {/* Dates & Financials */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-xs">
                <Calendar className="w-4 h-4" />
                <span>Important Dates & Deadlines</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                {extractionData.extracted_data.important_dates?.length ? (
                  extractionData.extracted_data.important_dates.map((d, i) => (
                    <li key={i} className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
                      <span className="font-semibold text-slate-900 dark:text-white">{d.date}</span>
                      <span className="text-slate-400">{d.description}</span>
                    </li>
                  ))
                ) : (
                  <p className="text-slate-400 italic">No specific dates extracted.</p>
                )}
              </ul>
            </div>

            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-xs">
                <DollarSign className="w-4 h-4" />
                <span>Financial & Payment Terms</span>
              </div>
              <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                {extractionData.extracted_data.financial_terms?.length ? (
                  extractionData.extracted_data.financial_terms.map((f, i) => (
                    <li key={i} className="border-b border-slate-100 dark:border-slate-800 pb-1">
                      <span className="font-semibold text-slate-900 dark:text-white">{f.term}: </span>
                      <span className="text-slate-500">{f.details}</span>
                    </li>
                  ))
                ) : (
                  <p className="text-slate-400 italic">No financial terms extracted.</p>
                )}
              </ul>
            </div>
          </div>

          {/* Key Clauses & Obligations */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 rounded-2xl shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-xs">
              <ListChecks className="w-4 h-4" />
              <span>Key Clauses & Summary Obligations</span>
            </div>
            <div className="space-y-2 text-xs">
              {extractionData.extracted_data.key_clauses?.map((c, i) => (
                <div key={i} className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl space-y-1">
                  <span className="font-bold text-slate-900 dark:text-white">{c.type}</span>
                  <p className="text-slate-600 dark:text-slate-300">{c.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
