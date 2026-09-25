"use client";

import React, { useState } from "react";
import { searchDocuments, DocumentItem, SearchHit } from "@/lib/api";
import { Search as SearchIcon, FileText, Sparkles, SlidersHorizontal } from "lucide-react";

interface SearchViewProps {
  documents: DocumentItem[];
}

export default function SearchView({ documents }: SearchViewProps) {
  const [query, setQuery] = useState("");
  const [selectedDocId, setSelectedDocId] = useState("all");
  const [results, setResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setSearched(true);
    try {
      const res = await searchDocuments(query, selectedDocId);
      setResults(res.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          Semantic Vector Search
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Perform high-precision cosine similarity vector search across all indexed document chunks.
        </p>
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleSearch} className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200/80 dark:border-slate-700/60">
          <SearchIcon className="w-5 h-5 text-indigo-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a natural language query (e.g. 'annual leave entitlement', 'payment terms')"
            className="flex-1 bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-medium text-xs px-4 py-2 rounded-lg transition-all shadow-sm flex items-center gap-1.5"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{loading ? "Searching..." : "Search"}</span>
          </button>
        </div>

        {/* Filter controls */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
            <span>Filter Document:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="bg-transparent border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1 text-slate-700 dark:text-slate-300 focus:outline-none"
            >
              <option value="all">All Documents ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.document_id} value={d.document_id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>
          {searched && <span>Showing top {results.length} vector hits</span>}
        </div>
      </form>

      {/* Results List */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-500 animate-spin" />
            <span>Embedding query & searching vector index...</span>
          </div>
        ) : searched && results.length === 0 ? (
          <div className="p-12 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-center text-slate-400 text-sm">
            No matching chunks found for your query. Try rephrasing or selecting another document.
          </div>
        ) : (
          results.map((hit, idx) => (
            <div
              key={idx}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3 hover:border-indigo-500/40 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-white text-sm">
                      {hit.document_name}
                    </h4>
                    <p className="text-[11px] text-slate-400">Page {hit.page_number}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40 px-2.5 py-1 rounded-full">
                    Similarity Score: {(hit.score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-xl text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-mono">
                {hit.snippet}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
