"use client"

import { useState } from "react"
import { askAI } from "@/lib/api"

type Message = {
  role: "user" | "bot"
  text: string
}

export default function ChatBox() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  async function sendMessage() {
    if (!input.trim()) return

    const userMsg: Message = { role: "user", text: input }
    setMessages((prev) => [...prev, userMsg])

    setLoading(true)

    try {
      const res = await askAI(input)

      const botMsg: Message = {
        role: "bot",
        text: res.answer,
      }

      setMessages((prev) => [...prev, botMsg])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: "Error fetching response." },
      ])
    }

    setInput("")
    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full p-6">
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-2xl px-4 py-3 rounded-xl whitespace-pre-wrap text-sm ${
              msg.role === "user"
                ? "ml-auto bg-blue-600 text-white"
                : "bg-gray-100 text-gray-900"
            }`}
          >
            {msg.text}
          </div>
        ))}

        {loading && (
          <div className="text-gray-500 text-sm">Thinking...</div>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2 mt-4">
        <input
          className="flex-1 border rounded-lg px-4 py-2 text-sm"
          placeholder="Ask something about your document..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />

        <button
          onClick={sendMessage}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          Send
        </button>
      </div>
    </div>
  )
}