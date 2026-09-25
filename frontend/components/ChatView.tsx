"use client";

import React, { useState, useRef, useEffect } from "react";
import { askAI, DocumentItem, SourceCitation } from "@/lib/api";
import {
  Send,
  Sparkles,
  FileText,
  Bookmark,
  ChevronDown,
  ChevronUp,
  User,
  Bot,
  Info,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  sources?: SourceCitation[];
  timestamp: Date;
}

interface ChatViewProps {
  documents: DocumentItem[];
  selectedDocId: string;
  setSelectedDocId: (id: string) => void;
}

export default function ChatView({
  documents,
  selectedDocId,
  setSelectedDocId,
}: ChatViewProps) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || query).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setQuery("");
    setLoading(true);

    try {
      const res = await askAI(text, selectedDocId);
      const botMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: res.answer,
        sources: res.sources,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: `Error connecting to backend: ${err.message || "Failed to retrieve answer"}`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (msgId: string) => {
    setExpandedSources((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const samplePrompts = [
    "What are the main key points of the uploaded documents?",
    "Summarize the obligations and responsibilities mentioned.",
    "Are there any important dates or deadlines listed?",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] max-w-6xl mx-auto p-4 md:p-6 space-y-4">
      {/* Header & Target Document Selector */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900 dark:text-white text-base">
              Ask AI (Grounded RAG Q&A)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Answers derived strictly from retrieved PDF chunks with citations.
            </p>
          </div>
        </div>

        {/* Document Filter Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Scope:</span>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white text-xs rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-w-xs truncate"
          >
            <option value="all">🌐 All Uploaded Documents ({documents.length})</option>
            {documents.map((d) => (
              <option key={d.document_id} value={d.document_id}>
                📄 {d.filename}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-4 md:p-6 overflow-y-auto space-y-6 shadow-sm">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shadow-inner">
              <Bot className="w-8 h-8" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 dark:text-white text-lg">
                Ask anything about your documents
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                The LLM reads retrieved document chunks and cites exact page numbers. If information isn&apos;t in your PDFs, it will state so safely.
              </p>
            </div>

            <div className="w-full space-y-2 pt-2">
              <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
                Suggested Prompts
              </p>
              {samplePrompts.map((p) => (
                <button
                  key={p}
                  onClick={() => handleSend(p)}
                  className="w-full text-left p-3 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-500/40 text-xs text-slate-700 dark:text-slate-300 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30 transition-all flex items-center justify-between group"
                >
                  <span>{p}</span>
                  <Sparkles className="w-3.5 h-3.5 text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <div
              key={m.id}
              className={`flex gap-3 ${
                m.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {m.role === "assistant" && (
                <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 mt-0.5 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div className="max-w-2xl space-y-2">
                <div
                  className={`p-4 rounded-2xl text-xs leading-relaxed whitespace-pre-wrap ${
                    m.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700/60 rounded-bl-none"
                  }`}
                >
                  {m.text}
                </div>

                {/* Source Citations for Assistant Responses */}
                {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                  <div className="bg-slate-100/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/50 rounded-xl p-3 text-[11px] space-y-2">
                    <button
                      onClick={() => toggleSources(m.id)}
                      className="w-full flex items-center justify-between font-semibold text-slate-600 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400"
                    >
                      <div className="flex items-center gap-1.5">
                        <Bookmark className="w-3.5 h-3.5 text-indigo-500" />
                        <span>Sources Referenced ({m.sources.length})</span>
                      </div>
                      {expandedSources[m.id] ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedSources[m.id] && (
                      <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-700/50">
                        {m.sources.map((s, idx) => (
                          <div
                            key={idx}
                            className="bg-white dark:bg-slate-900 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 space-y-1"
                          >
                            <div className="flex items-center justify-between font-medium text-slate-900 dark:text-white">
                              <span className="truncate flex items-center gap-1">
                                <FileText className="w-3 h-3 text-indigo-500" />
                                {s.document_name}
                              </span>
                              <span className="text-[10px] bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-200 dark:border-indigo-800/40">
                                Page {s.page_number} (Score: {s.score})
                              </span>
                            </div>
                            <p className="text-slate-500 dark:text-slate-400 text-[10px] italic line-clamp-2">
                              &quot;{s.snippet}&quot;
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {m.role === "user" && (
                <div className="w-8 h-8 rounded-xl bg-slate-800 text-white flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex gap-3 items-center text-xs text-slate-500">
            <div className="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center animate-pulse">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-4 py-2.5 rounded-2xl">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500 animate-spin" />
              <span>Retrieving chunks & generating grounded answer...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-3 flex items-center gap-2 shadow-sm shrink-0">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask a question about your documents..."
          className="flex-1 bg-transparent text-xs md:text-sm text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none px-2"
          disabled={loading}
        />
        <button
          onClick={() => handleSend()}
          disabled={!query.trim() || loading}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white p-2.5 rounded-xl transition-all shadow-sm"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
