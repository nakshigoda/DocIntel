"use client";

import React, { useState, useRef } from "react";
import { uploadDocument } from "@/lib/api";
import { Upload, X, CheckCircle2, AlertCircle, Sparkles, FileText } from "lucide-react";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export default function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileSelect = (selectedFile: File) => {
    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setIsError(true);
      setStatusMsg("Only PDF files are allowed.");
      return;
    }
    if (selectedFile.size > 20 * 1024 * 1024) {
      setIsError(true);
      setStatusMsg("File size exceeds 20 MB limit.");
      return;
    }
    setFile(selectedFile);
    setIsError(false);
    setStatusMsg(null);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;
    setUploading(true);
    setStatusMsg("Uploading & extracting PDF text...");
    setIsError(false);

    try {
      const res = await uploadDocument(file);
      setStatusMsg(res.message || "Document processed & indexed successfully!");
      setTimeout(() => {
        onUploadSuccess();
        onClose();
        setFile(null);
        setStatusMsg(null);
      }, 1500);
    } catch (err: any) {
      setIsError(true);
      setStatusMsg(err.message || "Failed to process document.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 relative">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-slate-900 dark:text-white font-bold text-base">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <span>Upload Document</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            const dropped = e.dataTransfer.files?.[0];
            if (dropped) handleFileSelect(dropped);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            dragOver
              ? "border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/30"
              : "border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 hover:bg-slate-50 dark:hover:bg-slate-800/50"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFileSelect(f);
            }}
          />

          <div className="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto mb-3">
            <Upload className="w-6 h-6" />
          </div>

          <p className="text-sm font-semibold text-slate-900 dark:text-white">
            Click to upload or drag & drop
          </p>
          <p className="text-xs text-slate-400 mt-1">PDF documents up to 20 MB</p>
        </div>

        {/* Selected File Card */}
        {file && (
          <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              <FileText className="w-4 h-4 text-indigo-500 shrink-0" />
              <span className="text-xs font-medium text-slate-900 dark:text-white truncate">
                {file.name}
              </span>
              <span className="text-[10px] text-slate-400 shrink-0">
                ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFile(null);
              }}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Status Message */}
        {statusMsg && (
          <div
            className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
              isError
                ? "bg-rose-50 dark:bg-rose-950/40 text-rose-600 border border-rose-200"
                : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 border border-emerald-200"
            }`}
          >
            {isError ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle2 className="w-4 h-4 shrink-0" />}
            <span>{statusMsg}</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white font-medium text-xs px-5 py-2 rounded-xl transition-all shadow-sm flex items-center gap-2"
          >
            {uploading ? (
              <>
                <Sparkles className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <span>Start Upload</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
