"use client"

import { MessageSquarePlus } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

export function FeedbackTrigger() {
  const pathname = usePathname()
  const isActive = pathname === "/feedback"

  return (
    <Link
      href="/feedback"
      aria-label="Feedback and Support"
      className={`group flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-medium transition-all duration-200 
        ${isActive 
          ? "bg-sky-500/15 text-sky-400 border border-sky-500/20" 
          : "text-muted-foreground hover:text-foreground hover:bg-sky-500/5 hover:border-sky-500/20 border border-transparent"
        }`}
    >
      <MessageSquarePlus className={`w-3.5 h-3.5 transition-transform duration-200 group-hover:scale-110 
        ${isActive ? "text-sky-400" : "text-muted-foreground group-hover:text-sky-400"}`} 
      />
      <span>Feedback</span>
    </Link>
  )
}
