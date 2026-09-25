"use client";

import React from "react";
import { DocumentItem } from "@/lib/api";
import {
  FileText,
  CheckCircle2,
  AlertCircle,
  Database,
  Search,
  MessageSquare,
  GitCompare,
  Sparkles,
  ArrowRight,
  Clock,
} from "lucide-react";
import { NavTab } from "./Sidebar";

interface DashboardViewProps {
  documents: DocumentItem[];
  loading: boolean;
  onNavigate: (tab: NavTab) => void;
  onOpenUpload: () => void;
}

export default function DashboardView({
  documents,
  loading,
  onNavigate,
  onOpenUpload,
}: DashboardViewProps) {
  const totalDocs = documents.length;
  const processedDocs = documents.filter((d) => d.status === "processed").length;
  const failedDocs = documents.filter((d) => d.status === "failed").length;
  const totalChunks = documents.reduce((acc, d) => acc + (d.chunk_count || 0), 0);

  const recentDocs = documents.slice(0, 5);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Enterprise Dashboard
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time status of document ingestion, semantic index, and RAG pipelines.
          </p>
        </div>
        <button
          onClick={onOpenUpload}
          className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-4 py-2.5 rounded-xl shadow-sm transition-all flex items-center gap-2 self-start md:self-auto"
        >
          <Sparkles className="w-4 h-4" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Total Documents
            </p>
            <h3 className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
              {loading ? "..." : totalDocs}
            </h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-800/40 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Processed
            </p>
            <h3 className="text-3xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
              {loading ? "..." : processedDocs}
            </h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/40 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Failures
            </p>
            <h3 className="text-3xl font-bold text-rose-600 dark:text-rose-400 mt-1">
              {loading ? "..." : failedDocs}
            </h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800/40 flex items-center justify-center text-rose-600 dark:text-rose-400">
            <AlertCircle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Indexed Chunks
            </p>
            <h3 className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
              {loading ? "..." : totalChunks}
            </h3>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 border border-indigo-200 dark:border-indigo-800/40 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <Database className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div
          onClick={() => onNavigate("chat")}
          className="bg-gradient-to-br from-indigo-500 to-blue-600 rounded-2xl p-6 text-white cursor-pointer hover:shadow-lg hover:shadow-indigo-500/20 transition-all group relative overflow-hidden"
        >
          <div className="absolute right-0 top-0 translate-x-4 -translate-y-4 w-32 h-32 bg-white/10 rounded-full blur-2xl pointer-events-none" />
          <MessageSquare className="w-8 h-8 mb-4 opacity-90" />
          <h4 className="text-lg font-bold">Ask AI (RAG Q&A)</h4>
          <p className="text-xs text-indigo-100 mt-1 mb-4 leading-relaxed">
            Query across your knowledge base with grounded citations and page references.
          </p>
          <div className="flex items-center text-xs font-semibold text-white group-hover:translate-x-1 transition-transform gap-1">
            <span>Start Chat</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div
          onClick={() => onNavigate("search")}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 cursor-pointer hover:border-indigo-500/50 hover:shadow-md transition-all group"
        >
          <Search className="w-8 h-8 text-indigo-600 dark:text-indigo-400 mb-4" />
          <h4 className="text-lg font-bold text-slate-900 dark:text-white">Semantic Search</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4 leading-relaxed">
            Natural language search over all indexed PDF chunks with cosine relevance scores.
          </p>
          <div className="flex items-center text-xs font-semibold text-indigo-600 dark:text-indigo-400 group-hover:translate-x-1 transition-transform gap-1">
            <span>Explore Search</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>

        <div
          onClick={() => onNavigate("compare")}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 cursor-pointer hover:border-indigo-500/50 hover:shadow-md transition-all group"
        >
          <GitCompare className="w-8 h-8 text-indigo-600 dark:text-indigo-400 mb-4" />
          <h4 className="text-lg font-bold text-slate-900 dark:text-white">Document Comparison</h4>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4 leading-relaxed">
            Compare two contract versions or policies to extract additions, omissions, and risks.
          </p>
          <div className="flex items-center text-xs font-semibold text-indigo-600 dark:text-indigo-400 group-hover:translate-x-1 transition-transform gap-1">
            <span>Compare Docs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </div>
        </div>
      </div>

      {/* Recent Uploads Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-400" />
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Recent Uploads</h3>
          </div>
          <button
            onClick={() => onNavigate("documents")}
            className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline"
          >
            View All ({documents.length})
          </button>
        </div>

        {recentDocs.length === 0 ? (
          <div className="py-8 text-center text-slate-400 text-sm">
            No documents uploaded yet. Click &quot;Upload Document&quot; to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3 rounded-l-lg">Filename</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Pages</th>
                  <th className="p-3">Chunks</th>
                  <th className="p-3 rounded-r-lg">Uploaded At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                {recentDocs.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="p-3 font-medium text-slate-900 dark:text-white max-w-xs truncate">
                      {doc.filename}
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium capitalize ${
                          doc.status === "processed"
                            ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/30"
                            : doc.status === "failed"
                            ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/30"
                            : "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/30"
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="p-3">{doc.page_count}</td>
                    <td className="p-3">{doc.chunk_count}</td>
                    <td className="p-3 text-slate-400">
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString() : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
