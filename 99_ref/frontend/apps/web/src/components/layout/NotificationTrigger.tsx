"use client"

import React, { useEffect, useState } from "react"
import { Bell, Check, Clock, ExternalLink, Inbox } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  Badge,
  Button,
  ScrollArea
} from "@kcontrol/ui"
import { getInbox, getUnreadNotificationCount, markInboxRead, type InboxNotificationItem } from "@/lib/api/notifications"

export function NotificationTrigger() {
  const pathname = usePathname()
  const isActive = pathname === "/notifications"
  const [unreadCount, setUnreadCount] = useState(0)
  const [latestNotifications, setLatestNotifications] = useState<InboxNotificationItem[]>([])

  const loadData = async (isMounted: boolean) => {
    try {
      const resp = await getUnreadNotificationCount()
      if (!isMounted) return
      setUnreadCount(resp)
      
      const inbox = await getInbox({ limit: 5, is_read: false })
      if (!isMounted) return
      setLatestNotifications(inbox.items)
    } catch (err) {
      console.error("Failed to load notifications", err)
    }
  }

  useEffect(() => {
    let isMounted = true
    loadData(isMounted)
    // Refresh every 5 minutes
    const interval = setInterval(() => loadData(isMounted), 300_000)
    // Also refresh when the tab becomes visible again
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") loadData(isMounted)
    }
    document.addEventListener("visibilitychange", handleVisibilityChange)
    return () => {
      isMounted = false
      clearInterval(interval)
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [])

  const handleMarkAsRead = async (id: string, e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    try {
      await markInboxRead([id])
      // Trigger a re-load without passing a flag if we're still here
      const count = await getUnreadNotificationCount()
      setUnreadCount(count)
      const inbox = await getInbox({ limit: 5, is_read: false })
      setLatestNotifications(inbox.items)
    } catch (err) {
      console.error("Failed to mark as read", err)
    }
  }

  return (
    <DropdownMenu onOpenChange={(open) => open && loadData(true)}>
      <DropdownMenuTrigger asChild>
        <button
          className={`relative group flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200 outline-none
            ${isActive 
              ? "bg-amber-500/10 text-amber-500 border border-amber-500/20" 
              : "text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent"
            }`}
        >
          <Bell className={`w-4 h-4 transition-transform duration-200 group-hover:scale-110`} />
          {unreadCount > 0 && (
            <Badge 
              className="absolute -top-1 -right-1 h-4 min-w-4 px-1 flex items-center justify-center bg-red-600 text-white text-[10px] font-bold rounded-full border border-background shadow-lg"
            >
              {unreadCount > 9 ? "9+" : unreadCount}
            </Badge>
          )}
        </button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end" className="w-[320px] p-0 overflow-hidden shadow-2xl border-border/50 bg-background/95 backdrop-blur-md"
        onCloseAutoFocus={(e) => e.preventDefault()}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
          <h3 className="text-sm font-bold tracking-tight">Recent Notifications</h3>
          {unreadCount > 0 && (
            <span className="text-[10px] font-bold uppercase tracking-widest text-red-500">{unreadCount} Unread</span>
          )}
        </div>
        
        <ScrollArea className="h-[350px]">
          {latestNotifications.length > 0 ? (
            <div className="py-1">
              {latestNotifications.map((n) => (
                <DropdownMenuItem 
                  key={n.id} 
                  asChild
                  className="group relative px-4 py-3 hover:bg-muted/50 transition-colors border-b border-border/40 last:border-0 outline-none cursor-default focus:bg-muted/50"
                  onSelect={(e) => {
                    // Prevent close if clicking the "mark as read" button specifically
                    if (e.target instanceof HTMLElement && e.target.closest('button')) {
                       e.preventDefault()
                    }
                  }}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1 w-2 h-2 rounded-full bg-blue-500 shrink-0 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                    <div className="flex-1 min-w-0 pr-6">
                      <p className="text-xs font-semibold text-foreground line-clamp-1 mb-0.5">
                        {n.rendered_subject || "System Notification"}
                      </p>
                      <p className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
                        {n.rendered_body}
                      </p>
                      <div className="flex items-center gap-2 mt-2 text-[9px] font-bold uppercase tracking-widest text-muted-foreground/60">
                         <Clock className="w-2.5 h-2.5" />
                         {new Date(n.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                    <button 
                      onClick={(e) => handleMarkAsRead(n.id, e)}
                      className="absolute top-3 right-3 p-1 rounded-md opacity-0 group-hover:opacity-100 hover:bg-blue-500/10 hover:text-blue-500 transition-all text-muted-foreground z-10"
                      title="Mark as read"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </DropdownMenuItem>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 px-4 h-full text-center">
              <div className="w-12 h-12 rounded-full bg-muted/50 flex items-center justify-center mb-3">
                <Inbox className="w-6 h-6 text-muted-foreground/40" />
              </div>
              <p className="text-xs font-medium text-foreground">No unread notifications</p>
              <p className="text-[10px] text-muted-foreground mt-1">You're all caught up!</p>
            </div>
          )}
        </ScrollArea>
        
        <div className="p-2 border-t bg-muted/20">
          <DropdownMenuItem asChild>
            <Link href="/notifications" className="block w-full outline-none">
              <Button variant="ghost" className="w-full justify-between h-9 text-xs font-bold uppercase tracking-widest hover:bg-primary/5 hover:text-primary transition-all">
                See All Notifications
                <ExternalLink className="w-3 h-3 ml-2" />
              </Button>
            </Link>
          </DropdownMenuItem>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
