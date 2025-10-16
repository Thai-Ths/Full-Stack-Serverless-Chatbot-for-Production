import type { Session, Conversation } from "./types"

export async function sendMessage(message: string, sessionId?: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!res.ok) throw new Error("Failed to send message")
  return res.json()
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/sessions`)
  if (!res.ok) throw new Error("Failed to fetch sessions")
  const data = await res.json()
  // Backend returns { sessions: [...] } with snake_case fields.
  const rawSessions = Array.isArray(data?.sessions) ? data.sessions : []
  return rawSessions.map((s: any) => {
    const id = s.session_id ?? s.id ?? ""
    const lastMessage: string | undefined = s.last_message || undefined
    const createdAt = s.created_at ? new Date(s.created_at) : new Date()
    const updatedAt = s.last_message_timestamp
      ? new Date(s.last_message_timestamp)
      : createdAt
    const title = lastMessage
      ? lastMessage
      : id
      ? `Session ${String(id).slice(0, 8)}`
      : "แชทใหม่"

    const session: Session = {
      id: String(id),
      title,
      lastMessage,
      createdAt,
      updatedAt,
    }
    return session
  })
}

export async function fetchConversation(sessionId: string): Promise<Conversation> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/conversation/${sessionId}`)
  if (!res.ok) throw new Error("Failed to fetch conversation")
  const data = await res.json()
  const messages = Array.isArray(data?.messages) ? data.messages : []
  // Ensure each message has an id and normalize timestamp
  const normalized = messages.map((m: any, idx: number) => ({
    id: m.id ? String(m.id) : `${sessionId}-${idx}`,
    content: m.content ?? "",
    role: m.role === "user" ? "user" : "assistant",
    timestamp: m.timestamp ?? new Date().toISOString(),
  }))
  return {
    sessionId: data?.session_id ?? sessionId,
    messages: normalized,
  }
}
