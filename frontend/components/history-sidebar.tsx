"use client"

import { SessionItem } from "./session-item"
import type { Session } from "@/lib/types"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Plus, History, MessageSquare } from "lucide-react"
import { Spinner } from "@/components/ui/spinner"

interface HistorySidebarProps {
  sessions: Session[]
  activeSessionId?: string
  onSelectSession: (sessionId: string) => void
  onNewChat: () => void
  isLoading?: boolean
}

export function HistorySidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  isLoading,
}: HistorySidebarProps) {
  return (
    <div className="flex flex-col h-full bg-sidebar border-r border-sidebar-border">
      {/* Header */}
      <div className="px-4 py-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-sidebar-foreground" />
            <h2 className="font-semibold text-sidebar-foreground">Conversation History</h2>
          </div>
        </div>
        <Button onClick={onNewChat} className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1 px-2 py-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Spinner className="h-6 w-6" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <MessageSquare className="h-12 w-12 text-sidebar-foreground/20 mb-3" />
            <p className="text-sm text-sidebar-foreground/60">No conversation history yet</p>
          </div>
        ) : (
          <div className="space-y-1">
            {sessions
              .slice()
              .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
              .map((session) => (
                <SessionItem
                  key={session.id}
                  session={session}
                  isActive={session.id === activeSessionId}
                  onClick={() => onSelectSession(session.id)}
                />
              ))}
          </div>
        )}
      </ScrollArea>
    </div>
  )
}
