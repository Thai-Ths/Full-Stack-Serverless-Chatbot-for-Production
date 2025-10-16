"use client"

import { useState, useEffect } from "react"
import { ChatWindow } from "@/components/chat-window"
import { HistorySidebar } from "@/components/history-sidebar"
import type { Message, Session } from "@/lib/types"
import { sendMessage, fetchSessions, fetchConversation } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Menu, X } from "lucide-react"
import { cn } from "@/lib/utils"

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>()
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const [isLoadingSessions, setIsLoadingSessions] = useState(true)
  const { toast } = useToast()

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setIsLoadingSessions(true)
      const data = await fetchSessions()
      setSessions(data)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load conversation history",
        variant: "destructive",
      })
    } finally {
      setIsLoadingSessions(false)
    }
  }

  const loadConversation = async (sessionId: string) => {
    try {
      setIsLoading(true)
      const data = await fetchConversation(sessionId)
      setMessages(data.messages)
      setActiveSessionId(sessionId)
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load conversation",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await sendMessage(content, activeSessionId)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response.message || response.response,
        role: "assistant",
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])

      // Update session ID if new session was created
      if (response.session_id && !activeSessionId) {
        setActiveSessionId(response.session_id)
        await loadSessions()
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to send message",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = () => {
    setActiveSessionId(undefined)
    setMessages([])
  }

  const handleSelectSession = (sessionId: string) => {
    loadConversation(sessionId)
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId)

  return (
    <div className="h-screen w-full gradient-bg overflow-hidden">
      <div className="container mx-auto h-full py-4 px-4 md:py-6 md:px-6">
        <div className="flex h-full gap-4">
          {/* Mobile Sidebar Toggle */}
          <Button
            variant="outline"
            size="icon"
            className={cn("fixed top-4 left-4 z-50 md:hidden bg-card shadow-lg", isSidebarOpen && "left-[280px]")}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            {isSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>

          {/* Sidebar */}
          <aside
            className={cn(
              "w-[280px] shrink-0 transition-transform duration-300 md:translate-x-0",
              !isSidebarOpen && "-translate-x-full md:translate-x-0",
              "fixed md:relative inset-y-0 left-0 z-40 md:z-0",
              "h-screen md:h-full pt-4 md:pt-0",
            )}
          >
            <div className="h-full rounded-2xl overflow-hidden shadow-lg">
              <HistorySidebar
                sessions={sessions}
                activeSessionId={activeSessionId}
                onSelectSession={handleSelectSession}
                onNewChat={handleNewChat}
                isLoading={isLoadingSessions}
              />
            </div>
          </aside>

          {/* Main Chat Area */}
          <main className="flex-1 min-w-0">
            <ChatWindow
              messages={messages}
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              sessionTitle={activeSession?.title}
            />
          </main>
        </div>
      </div>
    </div>
  )
}
