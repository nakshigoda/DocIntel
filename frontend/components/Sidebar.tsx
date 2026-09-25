"use client";

import React from "react";
import {
  LayoutDashboard,
  FileText,
  Search,
  MessageSquare,
  GitCompare,
  Sparkles,
  ShieldCheck,
  Upload,
} from "lucide-react";

export type NavTab = "dashboard" | "documents" | "search" | "chat" | "compare" | "insights";

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  documentCount: number;
  onOpenUploadModal: () => void;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  documentCount,
  onOpenUploadModal,
}: SidebarProps) {
  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "documents", label: "Documents", icon: FileText, badge: documentCount },
    { id: "search", label: "Semantic Search", icon: Search },
    { id: "chat", label: "Ask AI (RAG)", icon: MessageSquare },
    { id: "compare", label: "Document Compare", icon: GitCompare },
    { id: "insights", label: "Insights & Extract", icon: Sparkles },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col h-screen border-r border-slate-800 shrink-0">
      {/* Brand Header */}
      <div className="p-5 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
              DocIntel <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">AI</span>
            </h1>
            <p className="text-[11px] text-slate-400">Enterprise Doc Platform</p>
          </div>
        </div>
      </div>

      {/* Quick Upload Button */}
      <div className="p-4">
        <button
          onClick={onOpenUploadModal}
          className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white py-2.5 px-4 rounded-xl font-medium text-sm shadow-md shadow-indigo-600/25 transition-all flex items-center justify-center gap-2 group"
        >
          <Upload className="w-4 h-4 transition-transform group-hover:-translate-y-0.5" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        <div className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-2">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id as NavTab)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-indigo-600/15 text-indigo-400 border border-indigo-500/20"
                  : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  isActive ? "bg-indigo-500/20 text-indigo-300" : "bg-slate-800 text-slate-400"
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Groq + ChromaDB</span>
        </div>
        <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400">v2.0</span>
      </div>
    </aside>
  );
}
