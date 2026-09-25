"use client";

import React, { useState, useEffect, useCallback } from "react";
import Sidebar, { NavTab } from "@/components/Sidebar";
import DashboardView from "@/components/DashboardView";
import DocumentsView from "@/components/DocumentsView";
import ChatView from "@/components/ChatView";
import SearchView from "@/components/SearchView";
import CompareView from "@/components/CompareView";
import InsightsView from "@/components/InsightsView";
import UploadModal from "@/components/UploadModal";
import {
  fetchDocuments,
  deleteDocument,
  reprocessDocument,
  DocumentItem,
} from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<NavTab>("dashboard");
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const [selectedDocForChat, setSelectedDocForChat] = useState("all");
  const [selectedDocForInsights, setSelectedDocForInsights] = useState("");

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDocuments();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleDelete = async (docId: string) => {
    await deleteDocument(docId);
    await loadDocuments();
  };

  const handleReprocess = async (docId: string) => {
    await reprocessDocument(docId);
    await loadDocuments();
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 font-sans overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        documentCount={documents.length}
        onOpenUploadModal={() => setIsUploadOpen(true)}
      />

      {/* Main Content View Container */}
      <main className="flex-1 overflow-y-auto">
        {activeTab === "dashboard" && (
          <DashboardView
            documents={documents}
            loading={loading}
            onNavigate={setActiveTab}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        )}

        {activeTab === "documents" && (
          <DocumentsView
            documents={documents}
            loading={loading}
            onRefresh={loadDocuments}
            onDelete={handleDelete}
            onReprocess={handleReprocess}
            onNavigate={setActiveTab}
            setSelectedDocForInsights={setSelectedDocForInsights}
            setSelectedDocForChat={setSelectedDocForChat}
          />
        )}

        {activeTab === "chat" && (
          <ChatView
            documents={documents}
            selectedDocId={selectedDocForChat}
            setSelectedDocId={setSelectedDocForChat}
          />
        )}

        {activeTab === "search" && <SearchView documents={documents} />}

        {activeTab === "compare" && <CompareView documents={documents} />}

        {activeTab === "insights" && (
          <InsightsView
            documents={documents}
            selectedDocId={selectedDocForInsights}
            setSelectedDocId={setSelectedDocForInsights}
          />
        )}
      </main>

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={loadDocuments}
      />
    </div>
  );
}