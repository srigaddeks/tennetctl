"use client"

import * as React from "react"
import {
  MessageSquare,
  Send,
  Plus,
  Search,
  Loader2,
  RefreshCw,
  User,
  Clock
} from "lucide-react"

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Input
} from "@kcontrol/ui"

import { 
  listComments, 
  createComment 
} from "@/lib/api/comments"
import { engagementsApi, type EngagementParticipant } from "@/lib/api/engagements"
import { toast } from "sonner"

interface Comment {
  id: string
  entity_type: string
  entity_id: string
  author_user_id: string
  author_display_name: string
  author_email: string
  content: string
  content_format: string
  visibility: string
  reply_count: number
  replies: any[]
  created_at: string
  updated_at: string
}

interface MessagesTabProps {
  engagementId: string
  selectedEntity?: { type: string; id: string; title?: string }
  onEntitySelect?: (entity: { type: string; id: string; title?: string }) => void
  engagements?: Array<{ id: string; engagement_name: string }>  // Optional: for GRC users with multiple engagements
}

const mentionTokenRegex = /@\[([^\]]+)\]\(([0-9a-f-]{36})\)/gi

function stripMentionTokens(content: string | null | undefined): string {
  if (!content) return ""
  return content.replace(mentionTokenRegex, "@$1").trim()
}

export function MessagesTab({ 
  engagementId,
  selectedEntity,
  onEntitySelect,
  engagements
}: MessagesTabProps) {
  const [conversations, setConversations] = React.useState<Comment[]>([])
  const [messages, setMessages] = React.useState<Comment[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [loadingMessages, setLoadingMessages] = React.useState(false)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [replyContent, setReplyContent] = React.useState("")
  const [sending, setSending] = React.useState(false)
  const [showNewMessage, setShowNewMessage] = React.useState(false)
  const [newMessageContent, setNewMessageContent] = React.useState("")
  const [participants, setParticipants] = React.useState<EngagementParticipant[]>([])
  const [loadingParticipants, setLoadingParticipants] = React.useState(false)
  const [recipientUserId, setRecipientUserId] = React.useState("")
  const [lastConversationsData, setLastConversationsData] = React.useState("")
  const [lastMessagesData, setLastMessagesData] = React.useState("")

  // Smart background fetch - only updates if data actually changed
  const fetchConversationsBackground = React.useCallback(async () => {
    if (!engagementId) return
    
    try {
      let allComments: any[] = []
      
      if (engagements && engagements.length > 1) {
        const allResults = await Promise.all(
          engagements.map(async (eng) => {
            try {
              const data = await listComments('engagement', eng.id, 1, 50, 'newest', 'external')
              return data.items.map((item: any) => ({
                ...item,
                _engagement_id: eng.id,
                _engagement_name: eng.engagement_name
              }))
            } catch {
              return []
            }
          })
        )
        allComments = allResults.flat()
        allComments.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      } else {
        const data = await listComments('engagement', engagementId, 1, 50, 'newest', 'external')
        allComments = data.items as any[]
      }
      
      const newDataString = JSON.stringify(allComments)
      if (newDataString !== lastConversationsData) {
        setConversations(allComments)
        setLastConversationsData(newDataString)
      }
    } catch (error) {
      console.error("Failed to fetch conversations:", error)
    }
  }, [engagementId, engagements, lastConversationsData])

  const fetchMessagesBackground = React.useCallback(async () => {
    if (!selectedEntity) return
    
    try {
      const data = await listComments(selectedEntity.type, selectedEntity.id, 1, 50, 'oldest', 'external')
      const newDataString = JSON.stringify(data.items)
      if (newDataString !== lastMessagesData) {
        setMessages(data.items as any[])
        setLastMessagesData(newDataString)
      }
    } catch (error) {
      console.error("Failed to fetch messages:", error)
    }
  }, [selectedEntity, lastMessagesData])

  // Fetch conversations
  const fetchConversations = React.useCallback(async () => {
    if (!engagementId) return
    
    setIsLoading(true)
    try {
      let allComments: any[] = []
      
      // If we have multiple engagements (GRC user), fetch from all of them
      if (engagements && engagements.length > 1) {
        const allResults = await Promise.all(
          engagements.map(async (eng) => {
            try {
              const data = await listComments('engagement', eng.id, 1, 50, 'newest', 'external')
              return data.items.map((item: any) => ({
                ...item,
                _engagement_id: eng.id,
                _engagement_name: eng.engagement_name
              }))
            } catch {
              return []
            }
          })
        )
        allComments = allResults.flat()
        // Sort by created_at descending
        allComments.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      } else {
        // Single engagement - use the original behavior
        const data = await listComments('engagement', engagementId, 1, 50, 'newest', 'external')
        allComments = data.items as any[]
      }
      
      setConversations(allComments)
    } catch (error) {
      console.error("Failed to fetch conversations:", error)
    } finally {
      setIsLoading(false)
    }
  }, [engagementId, engagements])

  // Fetch messages for selected entity
  const fetchMessages = React.useCallback(async () => {
    if (!selectedEntity) return
    
    setLoadingMessages(true)
    try {
      const data = await listComments(selectedEntity.type, selectedEntity.id, 1, 50, 'oldest', 'external')
      setMessages(data.items as any[])
    } catch (error) {
      console.error("Failed to fetch messages:", error)
    } finally {
      setLoadingMessages(false)
    }
  }, [selectedEntity])

  const fetchParticipants = React.useCallback(async () => {
    if (!engagementId) return

    setLoadingParticipants(true)
    try {
      const data = await engagementsApi.listEngagementParticipants(engagementId)
      setParticipants(data.filter((participant) => Boolean(participant.user_id)))
    } catch (error) {
      console.error("Failed to fetch engagement participants:", error)
      toast.error(error instanceof Error ? error.message : "Failed to load engagement members")
    } finally {
      setLoadingParticipants(false)
    }
  }, [engagementId])

  React.useEffect(() => {
    fetchConversations()
  }, [fetchConversations])

  React.useEffect(() => {
    fetchParticipants()
  }, [fetchParticipants])

  React.useEffect(() => {
    if (selectedEntity) {
      fetchMessages()
    }
  }, [selectedEntity, fetchMessages])

  // Background polling - fetches every 15 seconds but only updates UI if data changed
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchConversationsBackground()
      if (selectedEntity) {
        fetchMessagesBackground()
      }
    }, 15000)
    return () => clearInterval(interval)
  }, [fetchConversationsBackground, fetchMessagesBackground, selectedEntity])

  // Handle reply
  const handleReply = async () => {
    if (!replyContent.trim() || !selectedEntity) return
    
    setSending(true)
    try {
      await createComment({
        entity_type: selectedEntity.type,
        entity_id: selectedEntity.id,
        content: replyContent,
        content_format: 'markdown',
        visibility: 'external'
      })
      toast.success("Message sent")
      setReplyContent("")
      fetchMessages()
    } catch (error) {
      console.error("Failed to send reply:", error)
      toast.error("Failed to send message")
    } finally {
      setSending(false)
    }
  }

  // Handle new message
  const handleNewMessage = async () => {
    const selectedRecipient = participants.find((participant) => participant.user_id === recipientUserId)
    if (!newMessageContent.trim() || !selectedRecipient) return
    
    setSending(true)
    try {
      const recipientLabel =
        selectedRecipient.display_name ||
        selectedRecipient.email ||
        "Selected member"
      const created = await createComment({
        entity_type: 'engagement',
        entity_id: engagementId,
        content: `@[${recipientLabel}](${selectedRecipient.user_id})\n\n${newMessageContent.trim()}`,
        content_format: 'markdown',
        visibility: 'external'
      })
      toast.success("Message sent")
      setNewMessageContent("")
      setRecipientUserId("")
      setShowNewMessage(false)
      fetchConversations()
      onEntitySelect?.({
        type: 'engagement',
        id: engagementId,
        title: stripMentionTokens(created.content).substring(0, 50) || recipientLabel,
      })
    } catch (error) {
      console.error("Failed to send message:", error)
      toast.error(error instanceof Error ? error.message : "Failed to send message")
    } finally {
      setSending(false)
    }
  }

  // Group conversations by engagement (not author) to prevent duplicate conversations when users reply
  const groupedConversations = React.useMemo(() => {
    const grouped = new Map<string, Comment & { message_count: number; participants: Set<string> }>()
    
    conversations.forEach(conv => {
      const engId = (conv as any)._engagement_id || conv.entity_id
      const existing = grouped.get(engId)
      
      if (!existing) {
        const participants = new Set<string>()
        participants.add(conv.author_display_name)
        grouped.set(engId, { ...conv, message_count: 1, participants })
      } else {
        existing.participants.add(conv.author_display_name)
        // Keep the most recent message for this engagement
        if (new Date(conv.created_at) > new Date(existing.created_at)) {
          grouped.set(engId, { ...conv, message_count: (existing.message_count || 1) + 1, participants: existing.participants })
        } else {
          existing.message_count = (existing.message_count || 1) + 1
        }
      }
    })
    
    return Array.from(grouped.values()).sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  }, [conversations])

  // Filter grouped conversations
  const filteredConversations = React.useMemo(() => {
    if (!searchQuery) return groupedConversations
    
    const query = searchQuery.toLowerCase()
    return groupedConversations.filter(conv => 
      conv.content?.toLowerCase().includes(query) ||
      conv.author_display_name?.toLowerCase().includes(query)
    )
  }, [groupedConversations, searchQuery])

  return (
    <div className="grid grid-cols-12 gap-6 h-[600px]">
      {/* Conversations List */}
      <div className="col-span-4 flex flex-col">
        <Card className="border-none shadow-lg flex-1 flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-bold uppercase tracking-widest">Conversations</CardTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => setShowNewMessage(true)}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-0">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                <MessageSquare className="h-8 w-8 mb-2 opacity-20" />
                <p className="text-sm">No conversations yet</p>
              </div>
            ) : (
              <div className="divide-y divide-muted/50">
                {filteredConversations.map(conv => {
                  // For multi-engagement scenarios, use the cached engagement info
                  const convEngId = (conv as any)._engagement_id || conv.entity_id || engagementId
                  return (
                  <button
                    key={convEngId}
                    onClick={() =>
                      onEntitySelect?.({
                        type: 'engagement',
                        id: convEngId,
                        title: stripMentionTokens(conv.content).substring(0, 50),
                      })
                    }
                    className={`
                      w-full px-4 py-3 text-left hover:bg-muted/30 transition-all
                      ${selectedEntity?.id === convEngId ? 'bg-primary/5 border-l-2 border-primary' : ''}
                    `}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">
                        {Array.from(conv.participants).join(', ')}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(conv.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground line-clamp-2">
                      {stripMentionTokens(conv.content)}
                    </p>
                    {conv.message_count > 1 && (
                      <Badge variant="secondary" className="mt-2 text-xs">
                        {conv.message_count} messages
                      </Badge>
                    )}
                    {conv.reply_count > 0 && (
                      <Badge variant="outline" className="mt-2 ml-2 text-xs">
                        {conv.reply_count} {conv.reply_count === 1 ? 'reply' : 'replies'}
                      </Badge>
                    )}
                  </button>
                )})}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Message Thread */}
      <div className="col-span-8 flex flex-col">
        <Card className="border-none shadow-lg flex-1 flex flex-col">
          {selectedEntity ? (
            <>
              <CardHeader className="pb-3 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold">
                      {selectedEntity.title || "Message Thread"}
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      {selectedEntity.type === 'request' ? 'Evidence Request' : 'Conversation'}
                    </p>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={fetchMessages}
                    disabled={loadingMessages}
                  >
                    <RefreshCw className={`h-4 w-4 ${loadingMessages ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                {loadingMessages ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
                    <MessageSquare className="h-8 w-8 mb-2 opacity-20" />
                    <p className="text-sm">No messages yet</p>
                    <p className="text-xs">Start the conversation</p>
                  </div>
                ) : (
                  [...messages].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map(msg => (
                    <div 
                      key={msg.id}
                      className={`flex gap-3 ${msg.author_display_name === 'You' ? 'flex-row-reverse' : ''}`}
                    >
                      <div className="flex-shrink-0">
                        <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                          <User className="h-4 w-4 text-primary" />
                        </div>
                      </div>
                      <div className={`flex-1 ${msg.author_display_name === 'You' ? 'text-right' : ''}`}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium">{msg.author_display_name}</span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(msg.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className={`
                          inline-block p-3 rounded-lg text-sm
                          ${msg.author_display_name === 'You' 
                            ? 'bg-primary/10 text-primary' 
                            : 'bg-muted'
                          }
                        `}>
                          {stripMentionTokens(msg.content)}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
              <div className="p-4 border-t">
                <div className="flex gap-2">
                  <textarea
                    placeholder="Type your reply..."
                    value={replyContent}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setReplyContent(e.target.value)}
                    className="flex-1 min-h-[80px] p-2 border rounded-md resize-none"
                    onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        handleReply()
                      }
                    }}
                  />
                  <Button 
                    onClick={handleReply}
                    disabled={!replyContent.trim() || sending}
                    className="self-end"
                  >
                    {sending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
              <MessageSquare className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm font-medium">Select a conversation</p>
              <p className="text-xs">Choose a conversation from the list to view messages</p>
            </div>
          )}
        </Card>
      </div>

      {/* New Message Dialog */}
      {showNewMessage && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg">
            <CardHeader>
              <CardTitle>New Message</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Send to</label>
                <select
                  value={recipientUserId}
                  onChange={(e) => setRecipientUserId(e.target.value)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  disabled={loadingParticipants || sending}
                >
                  <option value="">
                    {loadingParticipants ? "Loading engagement members..." : "Select an engagement member"}
                  </option>
                  {participants.map((participant) => {
                    const label =
                      participant.display_name ||
                      participant.email ||
                      participant.user_id
                    return (
                      <option key={participant.user_id} value={participant.user_id}>
                        {label}
                        {participant.membership_type_code ? ` • ${participant.membership_type_code}` : ""}
                      </option>
                    )
                  })}
                </select>
                <p className="text-xs text-muted-foreground">
                  Only active members of this engagement can be selected.
                </p>
              </div>
              <textarea
                placeholder="Type your message..."
                value={newMessageContent}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewMessageContent(e.target.value)}
                className="min-h-[120px] w-full p-2 border rounded-md resize-none"
              />
              <div className="flex justify-end gap-2">
                <Button 
                  variant="outline"
                  onClick={() => {
                    setShowNewMessage(false)
                    setRecipientUserId("")
                    setNewMessageContent("")
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleNewMessage}
                  disabled={!newMessageContent.trim() || !recipientUserId || sending}
                >
                  {sending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4 mr-2" />
                  )}
                  Send
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
