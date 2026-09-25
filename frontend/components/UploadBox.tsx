"use client"

import { useState } from "react"
import { uploadDocument } from "@/lib/api"

export default function UploadBox() {
  const [loading, setLoading] = useState(false)

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)

    try {
      await uploadDocument(file)
      alert("Upload successful!")
    } catch (err) {
      alert("Upload failed!")
    }

    setLoading(false)
  }

  return (
    <div className="p-4 border rounded-xl">
      <p className="text-sm font-medium mb-2">Upload PDF</p>

      <input
        type="file"
        accept="application/pdf"
        onChange={handleUpload}
        className="text-sm"
      />

      {loading && (
        <p className="text-xs text-gray-500 mt-2">
          Processing document...
        </p>
      )}
    </div>
  )
}