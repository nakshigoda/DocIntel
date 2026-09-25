"use client";

import React, { useState } from "react";
import { compareDocuments, DocumentItem, ComparisonResponse } from "@/lib/api";
import { GitCompare, Sparkles, FileText, ArrowRight, AlertCircle } from "lucide-react";

interface CompareViewProps {
  documents: DocumentItem[];
}

export default function CompareView({ documents }: CompareViewProps) {
  const [docA, setDocA] = useState("");
  const [docB, setDocB] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!docA || !docB) {
      setError("Please select two documents to compare.");
      return;
    }
    if (docA === docB) {
      setError("Please select two different documents.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const res = await compareDocuments(docA, docB);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to compare documents.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Document Comparison & Difference Analysis
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Select two documents to identify additions, omissions, modified clauses, and contractual risk impact.
        </p>
      </div>

      {/* Selectors */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          {/* Doc A */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-500" />
              <span>Document A (Base Version)</span>
            </label>
            <select
              value={docA}
              onChange={(e) => setDocA(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-xs rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select Document A...</option>
              {documents.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename} ({d.page_count} pages)
                </option>
              ))}
            </select>
          </div>

          {/* Doc B */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-blue-500" />
              <span>Document B (Compared Version)</span>
            </label>
            <select
              value={docB}
              onChange={(e) => setDocB(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-xs rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select Document B...</option>
              {documents.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename} ({d.page_count} pages)
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/30 rounded-xl text-xs text-rose-600 dark:text-rose-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={handleCompare}
            disabled={!docA || !docB || docA === docB || loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-medium text-xs px-5 py-2.5 rounded-xl transition-all shadow-sm flex items-center gap-2"
          >
            <GitCompare className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            <span>{loading ? "Analyzing Differences..." : "Compare Documents"}</span>
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {result && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-sm">
              <Sparkles className="w-4 h-4" />
              <span>Comparison Analysis Report</span>
            </div>
            <div className="text-xs text-slate-400">
              {result.document_a.filename} vs {result.document_b.filename}
            </div>
          </div>

          <div className="prose dark:prose-invert max-w-none text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap font-sans">
            {result.comparison}
          </div>
        </div>
      )}
    </div>
  );
}
