"use client";

import React, { useState } from "react";
import { DocumentItem } from "@/lib/api";
import {
  FileText,
  Trash2,
  RefreshCw,
  Sparkles,
  MessageSquare,
  AlertTriangle,
  Info,
  X,
  FileCheck,
} from "lucide-react";
import { NavTab } from "./Sidebar";

interface DocumentsViewProps {
  documents: DocumentItem[];
  loading: boolean;
  onRefresh: () => void;
  onDelete: (docId: string) => Promise<void>;
  onReprocess: (docId: string) => Promise<void>;
  onNavigate: (tab: NavTab) => void;
  setSelectedDocForInsights: (docId: string) => void;
  setSelectedDocForChat: (docId: string) => void;
}

export default function DocumentsView({
  documents,
  loading,
  onRefresh,
  onDelete,
  onReprocess,
  onNavigate,
  setSelectedDocForInsights,
  setSelectedDocForChat,
}: DocumentsViewProps) {
  const [activeDetailDoc, setActiveDetailDoc] = useState<DocumentItem | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState("");

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to permanently delete "${filename}"?`)) return;
    setActionLoading(docId);
    try {
      await onDelete(docId);
      if (activeDetailDoc?.document_id === docId) setActiveDetailDoc(null);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReprocess = async (docId: string) => {
    setActionLoading(docId);
    try {
      await onReprocess(docId);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Document Repository
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage uploaded PDFs, inspect chunk metadata, reprocess, or delete records.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
            title="Refresh document list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Filter bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center gap-3">
        <FileText className="w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Filter documents by filename..."
          value={searchFilter}
          onChange={(e) => setSearchFilter(e.target.value)}
          className="w-full bg-transparent text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none"
        />
        {searchFilter && (
          <button
            onClick={() => setSearchFilter("")}
            className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            Clear
          </button>
        )}
      </div>

      {/* Document Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="p-4">Document Name</th>
                <th className="p-4">Status</th>
                <th className="p-4">Pages</th>
                <th className="p-4">Chunks</th>
                <th className="p-4">Uploaded</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    {loading ? "Loading documents..." : "No matching documents found."}
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.document_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-medium text-slate-900 dark:text-white max-w-xs">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="truncate">
                          <p className="truncate font-medium" title={doc.filename}>{doc.filename}</p>
                          <p className="text-[10px] text-slate-400 truncate">ID: {doc.document_id}</p>
                        </div>
                      </div>
                    </td>

                    <td className="p-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium capitalize ${
                          doc.status === "processed"
                            ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/30"
                            : doc.status === "failed"
                            ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/30"
                            : "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/30"
                        }`}
                      >
                        {doc.status}
                        {doc.is_scanned && (
                          <span className="text-[9px] bg-amber-200 dark:bg-amber-800 text-amber-900 dark:text-amber-100 px-1 rounded">
                            Scanned
                          </span>
                        )}
                      </span>
                    </td>

                    <td className="p-4 font-semibold">{doc.page_count}</td>
                    <td className="p-4 font-semibold">{doc.chunk_count}</td>
                    <td className="p-4 text-slate-400 whitespace-nowrap">
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : "-"}
                    </td>

                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => setActiveDetailDoc(doc)}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                          title="View Details"
                        >
                          <Info className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => {
                            setSelectedDocForChat(doc.document_id);
                            onNavigate("chat");
                          }}
                          className="p-1.5 rounded-lg text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/50"
                          title="Ask AI about this document"
                        >
                          <MessageSquare className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => {
                            setSelectedDocForInsights(doc.document_id);
                            onNavigate("insights");
                          }}
                          className="p-1.5 rounded-lg text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/50"
                          title="Generate Insights & Extract"
                        >
                          <Sparkles className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleReprocess(doc.document_id)}
                          disabled={actionLoading === doc.document_id}
                          className="p-1.5 rounded-lg text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/50 disabled:opacity-50"
                          title="Reprocess Document"
                        >
                          <RefreshCw className={`w-4 h-4 ${actionLoading === doc.document_id ? "animate-spin" : ""}`} />
                        </button>

                        <button
                          onClick={() => handleDelete(doc.document_id, doc.filename)}
                          disabled={actionLoading === doc.document_id}
                          className="p-1.5 rounded-lg text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/50 disabled:opacity-50"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Detail Modal */}
      {activeDetailDoc && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 relative">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <FileCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base truncate max-w-xs">
                    {activeDetailDoc.filename}
                  </h3>
                  <p className="text-xs text-slate-400">Metadata & System Detail</p>
                </div>
              </div>
              <button
                onClick={() => setActiveDetailDoc(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Document ID</p>
                <p className="font-mono text-slate-900 dark:text-white text-[11px] truncate mt-0.5">
                  {activeDetailDoc.document_id}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Status</p>
                <p className="font-semibold text-slate-900 dark:text-white capitalize mt-0.5">
                  {activeDetailDoc.status}
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Page Count</p>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {activeDetailDoc.page_count} pages
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Indexed Chunks</p>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {activeDetailDoc.chunk_count} chunks
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Word Count</p>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {activeDetailDoc.word_count?.toLocaleString() || 0} words
                </p>
              </div>

              <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <p className="text-slate-400 text-[10px] uppercase font-semibold">Character Count</p>
                <p className="font-semibold text-slate-900 dark:text-white mt-0.5">
                  {activeDetailDoc.character_count?.toLocaleString() || 0} chars
                </p>
              </div>
            </div>

            {activeDetailDoc.error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/30 rounded-xl text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Processing Error:</p>
                  <p className="text-[11px] mt-0.5">{activeDetailDoc.error}</p>
                </div>
              </div>
            )}

            <div className="pt-2 flex justify-end gap-2">
              <button
                onClick={() => setActiveDetailDoc(null)}
                className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
