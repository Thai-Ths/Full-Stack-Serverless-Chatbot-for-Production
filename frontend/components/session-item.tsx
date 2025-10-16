"use client"

import type { Session } from "@/lib/types"
import { cn } from "@/lib/utils"
import { MessageSquare } from "lucide-react"

interface SessionItemProps {
  session: Session
  isActive?: boolean
  onClick: () => void
}

export function SessionItem({ session, isActive, onClick }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left px-4 py-3 rounded-lg transition-colors hover:bg-sidebar-accent group",
        isActive && "bg-sidebar-accent",
      )}
    >
      <div className="flex items-start gap-3">
        <MessageSquare className="h-5 w-5 text-sidebar-foreground/60 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-sm text-sidebar-foreground truncate">{session.title}</h3>
          {session.lastMessage && (
            <p className="text-xs text-sidebar-foreground/60 truncate mt-1">{session.lastMessage}</p>
          )}
          <span className="text-xs text-sidebar-foreground/40 mt-1 block">
            {new Date(session.updatedAt).toLocaleDateString("th-TH", {
              day: "numeric",
              month: "short",
            })}
          </span>
        </div>
      </div>
    </button>
  )
}
