"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
  Label,
} from "@kcontrol/ui";
import { 
  Eye, 
  EyeOff, 
  CheckCircle2, 
  AlertCircle, 
  LogOut, 
  Monitor, 
  Loader2, 
  ShieldCheck, 
  Key, 
  History, 
  Smartphone, 
  Globe,
  ShieldAlert,
  Unlock,
} from "lucide-react";
import { changePassword, logoutUser, fetchMe } from "@/lib/api/auth";
import { listUserSessions, revokeUserSession } from "@/lib/api/admin";
import type { SessionResponse } from "@/lib/types/admin";

function PasswordInput({
  id,
  value,
  onChange,
  placeholder,
  showToggle,
  showPassword,
  onTogglePassword,
}: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  showToggle?: boolean;
  showPassword?: boolean;
  onTogglePassword?: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative group">
      <input
        ref={inputRef}
        id={id}
        type={showPassword ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        required
        className="flex h-9 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm shadow-black/5 placeholder:text-muted-foreground/70 focus-visible:border-ring focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/20 pr-10 bg-background/30 focus:bg-background border-border/40 focus:border-primary/50"
      />
      {showToggle && (
        <button
          type="button"
          onClick={onTogglePassword}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          tabIndex={-1}
        >
          {showPassword ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
        </button>
      )}
    </div>
  );
}

export default function SecurityPage() {
  // ── Change password ──────────────────────────────────────────────────────
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState(false);

  // ── Active sessions ────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionsError, setSessionsError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [revokingAll, setRevokingAll] = useState(false);
  const [confirmRevokeAll, setConfirmRevokeAll] = useState(false);

  const loadSessions = useCallback(async (uid: string) => {
    setSessionsError(null);
    try {
      const data = await listUserSessions(uid, false);
      setSessions(data.sessions);
    } catch (err) {
      setSessionsError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await fetchMe();
        setUserId(me.user_id);
        await loadSessions(me.user_id);
      } catch (err) {
        setSessionsError(err instanceof Error ? err.message : "Failed to load user");
        setSessionsLoading(false);
      }
    })();
  }, [loadSessions]);

  async function handleRevokeSession(sessionId: string) {
    if (!userId) return;
    setRevokingId(sessionId);
    try {
      await revokeUserSession(userId, sessionId);
      await loadSessions(userId);
    } catch (err) {
      setSessionsError(err instanceof Error ? err.message : "Failed to revoke session");
    } finally {
      setRevokingId(null);
    }
  }

  async function handleRevokeAll() {
    if (!userId || sessions.length === 0) return;
    setRevokingAll(true);
    setSessionsError(null);
    try {
      for (const session of sessions) {
        try {
          await revokeUserSession(userId, session.session_id);
        } catch {
          // skip individual failures
        }
      }
      setConfirmRevokeAll(false);
      // After revoking all, user will be logged out — redirect
      logoutUser();
    } catch (err) {
      setSessionsError(err instanceof Error ? err.message : "Failed to revoke sessions");
      setRevokingAll(false);
    }
  }

  function truncateUserAgent(ua: string | null, max = 60): string {
    if (!ua) return "Unknown";
    return ua.length > max ? ua.slice(0, max) + "…" : ua;
  }

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwError(null);
    setPwSuccess(false);

    if (newPw.length < 8) {
      setPwError("New password must be at least 8 characters.");
      return;
    }
    if (newPw !== confirmPw) {
      setPwError("Passwords do not match.");
      return;
    }

    setPwLoading(true);
    try {
      await changePassword(currentPw, newPw);
      setPwSuccess(true);
      setCurrentPw("");
      setNewPw("");
      setConfirmPw("");
    } catch (err) {
      setPwError(err instanceof Error ? err.message : "Failed to change password");
    } finally {
      setPwLoading(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <div className="flex flex-col gap-1 border-b border-border/50 pb-6 mb-2">
        <h2 className="text-3xl font-bold font-secondary tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
          Security Settings
        </h2>
        <p className="text-sm text-muted-foreground max-w-lg">
          Configure your authentication methods, monitor active sessions, and manage your account&apos;s overall security posture.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
        {/* ── Security Status ────────────────────────────── */}
        <div className="lg:col-span-1 border-none flex flex-col">
          <Card className="h-full bg-card/40 backdrop-blur-md border-primary/10 shadow-sm overflow-hidden group">
            <div className="h-1.5 w-full bg-gradient-to-r from-green-500/50 to-emerald-500/50" />
            <CardHeader className="pb-4">
              <div className="flex items-center gap-2 text-primary">
                <ShieldCheck className="h-5 w-5" />
                <CardTitle className="text-base">Security Status</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between p-3 rounded-xl bg-green-500/5 border border-green-500/10">
                <div className="space-y-0.5">
                  <p className="text-[10px] uppercase tracking-wider font-semibold text-green-600 dark:text-green-400">Account Health</p>
                  <p className="text-sm font-medium">Standard Protection</p>
                </div>
                <Badge className="bg-green-500 hover:bg-green-600 border-none px-2 py-0 h-5 text-[10px]">Secure</Badge>
              </div>

              <div className="space-y-4">
                <h4 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/70">Key Metrics</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-muted/30 border border-border/50">
                    <p className="text-[10px] text-muted-foreground mb-1">Sessions</p>
                    <p className="text-xl font-bold font-secondary leading-none">{sessions.length}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-muted/30 border border-border/50">
                    <p className="text-[10px] text-muted-foreground mb-1">Password</p>
                    <p className="text-xs font-semibold text-primary uppercase">Active</p>
                  </div>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                <h4 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/70">Security Checklist</h4>
                <div className="space-y-2">
                  {[
                    "Two-factor authentication (Planned)",
                    "Strong unique password",
                    "Session monitoring active",
                  ].map((text, i) => (
                    <div key={text} className="flex items-center gap-2 text-xs">
                      {i === 0 ? <Unlock className="h-3 w-3 text-muted-foreground/40" /> : <CheckCircle2 className="h-3 w-3 text-green-500" />}
                      <span className={i === 0 ? "text-muted-foreground/60 italic" : "text-foreground/80"}>{text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Change Password ────────────────────────────────────────────────── */}
        <div className="lg:col-span-2 flex flex-col">
          <Card className="h-full bg-card/60 backdrop-blur-sm border-border/60 shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-3 mb-1">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                  <Key className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-lg">Change Password</CardTitle>
                  <CardDescription className="text-xs">
                    Safeguard your account with a strong, rotating password.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {pwSuccess && (
                <div className="flex items-center gap-3 rounded-xl border border-green-500/20 bg-green-500/5 px-4 py-3 mb-6 animate-in zoom-in-95 duration-300">
                  <div className="bg-green-500 rounded-full p-1">
                    <CheckCircle2 className="h-3 w-3 text-white" />
                  </div>
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">Password updated successfully.</p>
                </div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-5">
                <div className="space-y-4 max-w-sm">
                  <div className="space-y-1.5">
                    <Label htmlFor="current-pw" className="text-xs font-semibold text-muted-foreground/80 lowercase tracking-wider">Current password</Label>
                    <PasswordInput
                      id="current-pw"
                      value={currentPw}
                      onChange={setCurrentPw}
                      placeholder="••••••••"
                      showToggle
                      showPassword={showCurrent}
                      onTogglePassword={() => setShowCurrent((v) => !v)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="new-pw" className="text-xs font-semibold text-muted-foreground/80 lowercase tracking-wider">New password</Label>
                    <PasswordInput
                      id="new-pw"
                      value={newPw}
                      onChange={setNewPw}
                      placeholder="Min. 8 characters"
                      showToggle
                      showPassword={showNew}
                      onTogglePassword={() => setShowNew((v) => !v)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="confirm-pw" className="text-xs font-semibold text-muted-foreground/80 lowercase tracking-wider">Confirm password</Label>
                    <PasswordInput
                      id="confirm-pw"
                      value={confirmPw}
                      onChange={setConfirmPw}
                      placeholder="Repeat new password"
                      showToggle
                      showPassword={showConfirm}
                      onTogglePassword={() => setShowConfirm((v) => !v)}
                    />
                  </div>
                </div>

                {pwError && (
                  <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 animate-in slide-in-from-top-1 max-w-sm">
                    <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
                    <p className="text-xs text-red-500 font-medium">{pwError}</p>
                  </div>
                )}

                <Button type="submit" size="sm" className="w-full md:w-auto px-6 h-9 transition-all hover:shadow-lg active:scale-95" disabled={pwLoading || !currentPw || !newPw || !confirmPw}>
                  {pwLoading ? <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />Processing...</> : "Update Password"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ── Active Sessions ──────────────────────────────────────────────── */}
      <Card className="bg-card/60 backdrop-blur-sm border-border/60 shadow-sm overflow-hidden">
        <CardHeader className="border-b border-border/40 bg-muted/20">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-5">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10 text-orange-500 shrink-0">
                <Monitor className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <CardTitle className="text-lg leading-tight">Active Sessions</CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Devices currently authorized to access your account.
                </CardDescription>
              </div>
            </div>
            {sessions.length > 1 && !sessionsLoading && (
              <div className="shrink-0">
                {confirmRevokeAll ? (
                  <div className="flex items-center gap-2 animate-in slide-in-from-right-2">
                    <span className="text-[10px] font-bold text-red-600 uppercase">Revoke Entire Account?</span>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="h-8 px-3 text-xs gap-1.5 shadow-lg shadow-destructive/20"
                      onClick={handleRevokeAll}
                      disabled={revokingAll}
                    >
                      {revokingAll ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <LogOut className="h-3.5 w-3.5" />}
                      Confirm
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 px-3 text-xs bg-background"
                      onClick={() => setConfirmRevokeAll(false)}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs text-destructive border-destructive/30 hover:bg-destructive/10 gap-1.5 transition-all"
                    onClick={() => setConfirmRevokeAll(true)}
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    Log out of all devices
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {sessionsLoading ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary/40" />
              <p className="text-xs text-muted-foreground animate-pulse">Syncing session data...</p>
            </div>
          ) : sessionsError ? (
            <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-4">
              <ShieldAlert className="h-5 w-5 text-red-500" />
              <p className="text-sm font-medium text-red-600 dark:text-red-400">{sessionsError}</p>
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted-foreground border border-dashed rounded-xl">
              <LogOut className="h-8 w-8 opacity-20" />
              <p className="text-sm">No active sessions found.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-border/40 bg-background/20 p-3 hover:border-primary/30 hover:bg-primary/5 transition-all duration-300"
                >
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="p-2 rounded-lg bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary transition-colors shrink-0">
                      {session.user_agent?.toLowerCase().includes("mobile") || session.user_agent?.toLowerCase().includes("iphone") ? (
                        <Smartphone className="h-4 w-4" />
                      ) : (
                        <Globe className="h-4 w-4" />
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-1 flex-1 items-center min-w-0">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-sm font-bold tracking-tight text-foreground/90 truncate">
                          {session.client_ip || "Private IP"}
                        </span>
                        {session.is_impersonation && (
                          <Badge variant="secondary" className="text-[9px] px-1.5 py-0 h-4 uppercase font-bold bg-purple-500/10 text-purple-600 border-none shrink-0">Impersonated</Badge>
                        )}
                      </div>

                      <div className="min-w-0 hidden md:block">
                        <p className="text-[11px] text-muted-foreground/60 font-mono truncate" title={session.user_agent ?? undefined}>
                          {truncateUserAgent(session.user_agent ?? "", 60)}
                        </p>
                      </div>

                      <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground/50">
                        <History className="h-3 w-3" />
                        <span>
                          {new Date(session.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevokeSession(session.session_id)}
                    disabled={revokingId === session.session_id}
                    className="h-8 px-3 text-xs font-semibold text-destructive/70 hover:bg-destructive/10 hover:text-destructive group/btn transition-all shrink-0 self-end sm:self-center"
                  >
                    {revokingId === session.session_id ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <>
                        <LogOut className="h-3 w-3 mr-2 opacity-50 group-hover/btn:opacity-100 transition-opacity" />
                        Terminate
                      </>
                    )}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
