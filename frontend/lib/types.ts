export interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: string | Date
}

export interface Session {
  id: string
  title: string
  lastMessage?: string
  updatedAt: string | Date
  createdAt: string | Date
}

export interface Conversation {
  sessionId: string
  messages: Message[]
}
