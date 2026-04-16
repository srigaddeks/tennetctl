"use client"

import * as React from "react"
import {
  UserCheck,
  Calendar,
  Clock,
  Loader2,
  RefreshCw,
  Trash2
} from "lucide-react"

import {
  Button,
  Card,
  CardContent,
  Badge,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from "@kcontrol/ui"

import { engagementsApi, type AuditAccessToken } from "@/lib/api/engagements"
import { toast } from "sonner"

type AccessToken = AuditAccessToken

interface MyAccessTabProps {
  engagementId: string
}

export function MyAccessTab({
  engagementId
}: MyAccessTabProps) {
  const [accessTokens, setAccessTokens] = React.useState<AccessToken[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [revokeTokenId, setRevokeTokenId] = React.useState<string | null>(null)
  const [isRevoking, setIsRevoking] = React.useState(false)

  // Fetch access tokens
  const fetchAccessTokens = React.useCallback(async () => {
    if (!engagementId) return

    setIsLoading(true)
    try {
      const data = await engagementsApi.listAccessTokens(engagementId, false)
      setAccessTokens(data)
    } catch (error) {
      console.error("Failed to fetch access tokens:", error)
      toast.error("Failed to load access tokens")
    } finally {
      setIsLoading(false)
    }
  }, [engagementId])

  // Revoke access token
  const handleRevokeToken = React.useCallback(async (tokenId: string) => {
    setIsRevoking(true)
    try {
      await engagementsApi.revokeAccessToken(engagementId, tokenId)
      setAccessTokens(prev =>
        prev.map(token =>
          token.id === tokenId ? { ...token, is_revoked: true } : token
        )
      )
      toast.success("Access token revoked successfully")
      setRevokeTokenId(null)
    } catch (error) {
      console.error("Failed to revoke token:", error)
      toast.error("Failed to revoke access token")
    } finally {
      setIsRevoking(false)
    }
  }, [engagementId])

  React.useEffect(() => {
    fetchAccessTokens()
  }, [fetchAccessTokens])

  // Real-time polling every 60 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchAccessTokens()
    }, 60000)
    return () => clearInterval(interval)
  }, [fetchAccessTokens])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">My Access</h2>
          <p className="text-sm text-muted-foreground">
            {accessTokens.filter(t => !t.is_revoked).length} active {accessTokens.filter(t => !t.is_revoked).length === 1 ? 'token' : 'tokens'}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchAccessTokens}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Access Table */}
      <Card className="border-none shadow-lg overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : accessTokens.filter(t => !t.is_revoked).length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <UserCheck className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm font-medium">No active access tokens</p>
              <p className="text-xs">Access tokens will appear here when auditors are granted access</p>
            </div>
          ) : (
            <div className="divide-y divide-muted/50">
              {accessTokens
                .filter(t => !t.is_revoked)
                .map(token => (
                <div
                  key={token.id}
                  className="grid grid-cols-7 gap-4 px-6 py-4 hover:bg-muted/30 transition-all items-center"
                >
                  <div className="col-span-2 flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <UserCheck className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{token.auditor_email}</p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <Badge variant="default" className="text-xs">
                      Active
                    </Badge>
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {token.last_accessed_at ? (
                      <>
                        <Clock className="h-3 w-3 mr-1 flex-shrink-0" />
                        {new Date(token.last_accessed_at).toLocaleDateString()}
                      </>
                    ) : (
                      "-"
                    )}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    <Calendar className="h-3 w-3 mr-1 flex-shrink-0" />
                    {new Date(token.expires_at).toLocaleDateString()}
                  </div>
                  <div className="flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setRevokeTokenId(token.id)}
                      disabled={isRevoking}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Revoke Confirmation Dialog */}
      <Dialog open={!!revokeTokenId} onOpenChange={(open: boolean) => !open && setRevokeTokenId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke Access Token?</DialogTitle>
            <DialogDescription>
              Revoking this access token will immediately revoke the auditor's access. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="bg-muted p-4 rounded-md text-sm">
            <p className="text-foreground">
              <strong>Email:</strong> {accessTokens.find(t => t.id === revokeTokenId)?.auditor_email}
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRevokeTokenId(null)}
              disabled={isRevoking}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => revokeTokenId && handleRevokeToken(revokeTokenId)}
              disabled={isRevoking}
            >
              {isRevoking ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Revoking...
                </>
              ) : (
                "Revoke Access"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
