"use client"

import { useEffect, useRef } from "react"
import { ChatMessage } from "./chat-message"
import { ChatInput } from "./chat-input"
import type { Message } from "@/lib/types"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Spinner } from "@/components/ui/spinner"

interface ChatWindowProps {
  messages: Message[]
  onSendMessage: (message: string) => void
  isLoading?: boolean
  sessionTitle?: string
}

export function ChatWindow({ messages, onSendMessage, isLoading, sessionTitle }: ChatWindowProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="flex flex-col h-full bg-card rounded-2xl shadow-lg border border-border overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-card">
        <h2 className="text-lg font-semibold text-card-foreground">{sessionTitle || "Chatbot"}</h2>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-6 py-4" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p className="text-center">Start the conversation by sending a message</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Spinner className="h-4 w-4" />
                <span className="text-sm">Typing...</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="px-6 py-4 border-t border-border bg-card">
        <ChatInput onSend={onSendMessage} disabled={isLoading} />
      </div>
    </div>
  )
}
