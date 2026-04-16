"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@kcontrol/ui";
import { CheckCircle2, AlertCircle, Pencil, X, ShieldAlert, Link2, Building2, Layers, Globe, Mail, Phone, User, Clock, MapPin, Calendar, ExternalLink } from "lucide-react";
import { fetchMe, fetchUserProperties, setUserProperties, requestEmailVerification, verifyEmail, fetchUserAccounts } from "@/lib/api/auth";
import { listOrgs } from "@/lib/api/orgs";
import { listWorkspaces } from "@/lib/api/workspaces";
import type { AuthUserResponse } from "@/lib/types/auth";
import type { UserAccountResponse } from "@/lib/types/admin";
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs";

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-10 rounded-lg bg-muted animate-pulse" />
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const [user, setUser] = useState<AuthUserResponse | null>(null);
  const [props, setProps] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);

  // Editing state
  const [editing, setEditing] = useState(false);
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [username, setUsername] = useState("");
  const [timezone, setTimezone] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Email verification state
  const [verificationRequested, setVerificationRequested] = useState(false);
  const [verificationToken, setVerificationToken] = useState("");
  const [verificationSending, setVerificationSending] = useState(false);
  const [verificationVerifying, setVerificationVerifying] = useState(false);
  const [verificationError, setVerificationError] = useState<string | null>(null);
  const [verificationSuccess, setVerificationSuccess] = useState(false);

  // Linked accounts state
  const [accounts, setAccounts] = useState<UserAccountResponse[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsError, setAccountsError] = useState<string | null>(null);

  // Default org/workspace state
  const [orgs, setOrgs] = useState<OrgResponse[]>([]);
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>("");
  const [selectedWsId, setSelectedWsId] = useState<string>("");
  const [defaultSaving, setDefaultSaving] = useState(false);
  const [defaultSaveError, setDefaultSaveError] = useState<string | null>(null);
  const [defaultSaveSuccess, setDefaultSaveSuccess] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchMe(),
      fetchUserProperties().catch(() => ({} as Record<string, string>)),
      listOrgs().catch(() => [] as OrgResponse[]),
    ])
      .then(async ([me, userProps, userOrgs]) => {
        setUser(me);
        setProps(userProps);
        setFirstName(userProps["first_name"] ?? "");
        setLastName(userProps["last_name"] ?? "");
        setPhone(userProps["phone"] ?? "");
        setUsername(userProps["username"] ?? me.username ?? "");
        setTimezone(userProps["timezone"] ?? "");
        setOrgs(userOrgs);

        const defaultOrgId = userProps["default_org_id"] ?? userOrgs[0]?.id ?? "";
        setSelectedOrgId(defaultOrgId);
        setSelectedWsId(userProps["default_workspace_id"] ?? "");

        if (defaultOrgId) {
          const wsList = await listWorkspaces(defaultOrgId).catch(() => [] as WorkspaceResponse[]);
          setWorkspaces(wsList);
        }
      })
      .catch(() => null)
      .finally(() => setIsLoading(false));
  }, []);

  // Reload workspaces when org selection changes
  useEffect(() => {
    if (!selectedOrgId) { setWorkspaces([]); setSelectedWsId(""); return; }
    listWorkspaces(selectedOrgId)
      .then((wsList) => {
        setWorkspaces(wsList);
        // Only reset ws selection if we switched to a different org
        setSelectedWsId((prev) => (wsList.some((w) => w.id === prev) ? prev : wsList[0]?.id ?? ""));
      })
      .catch(() => setWorkspaces([]));
  }, [selectedOrgId]);

  useEffect(() => {
    fetchUserAccounts()
      .then(setAccounts)
      .catch((err) => setAccountsError(err instanceof Error ? err.message : "Failed to load accounts"))
      .finally(() => setAccountsLoading(false));
  }, []);

  async function handleRequestVerification() {
    setVerificationSending(true);
    setVerificationError(null);
    try {
      await requestEmailVerification();
      setVerificationRequested(true);
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : "Failed to send verification email");
    } finally {
      setVerificationSending(false);
    }
  }

  async function handleVerifyEmail(e: React.FormEvent) {
    e.preventDefault();
    if (!verificationToken.trim()) return;
    setVerificationVerifying(true);
    setVerificationError(null);
    try {
      await verifyEmail(verificationToken.trim());
      setVerificationSuccess(true);
      // Refresh user data to reflect verified status
      const me = await fetchMe();
      setUser(me);
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setVerificationVerifying(false);
    }
  }

  async function handleSaveDefaults(e: React.FormEvent) {
    e.preventDefault();
    setDefaultSaving(true);
    setDefaultSaveError(null);
    setDefaultSaveSuccess(false);
    try {
      const updates: Record<string, string> = {};
      if (selectedOrgId) updates["default_org_id"] = selectedOrgId;
      if (selectedWsId) updates["default_workspace_id"] = selectedWsId;
      await setUserProperties(updates);
      setProps((prev) => ({ ...prev, ...updates }));
      setDefaultSaveSuccess(true);
    } catch (err) {
      setDefaultSaveError(err instanceof Error ? err.message : "Failed to save defaults");
    } finally {
      setDefaultSaving(false);
    }
  }

  const displayName =
    [props["first_name"], props["last_name"]].filter(Boolean).join(" ") ||
    props["display_name"] ||
    user?.username ||
    null;

  const initials =
    props["first_name"] && props["last_name"]
      ? `${props["first_name"][0]}${props["last_name"][0]}`.toUpperCase()
      : props["first_name"]
      ? props["first_name"][0].toUpperCase()
      : user?.email?.[0]?.toUpperCase() ?? "?";

  function startEdit() {
    setFirstName(props["first_name"] ?? "");
    setLastName(props["last_name"] ?? "");
    setPhone(props["phone"] ?? "");
    setUsername(props["username"] ?? user?.username ?? "");
    setTimezone(props["timezone"] ?? "");
    setSaveError(null);
    setSaveSuccess(false);
    setEditing(true);
  }

  function cancelEdit() {
    setEditing(false);
    setSaveError(null);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      const updates: Record<string, string> = {};
      if (firstName.trim()) updates["first_name"] = firstName.trim();
      if (lastName.trim()) updates["last_name"] = lastName.trim();
      if (phone.trim()) updates["phone"] = phone.trim();
      if (username.trim()) updates["username"] = username.trim();
      if (timezone) updates["timezone"] = timezone;

      const displayNameValue = [firstName.trim(), lastName.trim()].filter(Boolean).join(" ");
      if (displayNameValue) updates["display_name"] = displayNameValue;

      await setUserProperties(updates);

      setProps((prev) => ({ ...prev, ...updates }));
      setSaveSuccess(true);
      setEditing(false);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-6xl space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="flex flex-col gap-1">
        <h2 className="text-3xl font-bold tracking-tight text-foreground bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/60">Profile</h2>
        <p className="text-muted-foreground text-sm max-w-lg">
          Personalize your account, manage connected organizations, and control your security preferences.
        </p>
      </div>

      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl border bg-card/30 backdrop-blur-sm p-6 md:p-10 transition-all hover:border-primary/20">
        <div className="absolute top-0 right-0 p-8 opacity-5 hidden md:block">
           <User size={120} strokeWidth={1} />
        </div>
        <div className="flex flex-col md:flex-row items-center md:items-start gap-6 md:gap-10 relative z-10">
          <div className="relative group">
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary to-primary-foreground opacity-20 blur-xl group-hover:opacity-40 transition-opacity" />
            <div className="h-28 w-28 rounded-full bg-gradient-to-tr from-primary/20 via-primary/5 to-background border-4 border-background flex items-center justify-center text-primary text-4xl font-bold shadow-2xl relative">
              {initials}
            </div>
            {!editing && (
              <button 
                onClick={startEdit}
                className="absolute bottom-1 right-1 h-9 w-9 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-lg border-2 border-background hover:scale-110 transition-transform"
              >
                <Pencil className="h-4 w-4" />
              </button>
            )}
          </div>
          <div className="flex-1 text-center md:text-left space-y-3">
             <div className="space-y-1">
               <h1 className="text-3xl font-extrabold text-foreground tracking-tight">{displayName ?? "Account Holder"}</h1>
               <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-muted-foreground mt-2">
                 <div className="flex items-center gap-1.5 text-sm font-medium">
                   <Mail className="h-4 w-4 text-primary/60" />
                   {user?.email}
                 </div>
                 {props["phone"] && (
                   <div className="flex items-center gap-1.5 text-sm font-medium border-l pl-4 border-border/50">
                     <Phone className="h-4 w-4 text-primary/60" />
                     {props["phone"]}
                   </div>
                 )}
                 {props["timezone"] && (
                   <div className="flex items-center gap-1.5 text-sm font-medium border-l pl-4 border-border/50">
                     <Clock className="h-4 w-4 text-primary/60" />
                     {props["timezone"]}
                   </div>
                 )}
               </div>
             </div>
             <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 pt-2">
               <Badge variant={user?.email_verified ? "default" : "outline"} className={user?.email_verified ? "bg-green-500/10 text-green-500 border-green-500/30 hover:bg-green-500/20" : "bg-amber-500/10 text-amber-500 border-amber-500/30 hover:bg-amber-500/20"}>
                 {user?.email_verified ? <CheckCircle2 className="h-3 w-3 mr-1" /> : <AlertCircle className="h-3 w-3 mr-1" />}
                 {user?.email_verified ? "Verified" : "Unverified"}
               </Badge>
               <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">
                 {user?.account_status?.replace(/_/g, " ") ?? "Active"}
               </Badge>
             </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">

      {/* Identity card */}
      <Card className="border-none shadow-none bg-transparent">
        <CardHeader className="px-0 pt-0">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Identity</CardTitle>
              <CardDescription>Your personal information and contact details.</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {!editing && !isLoading && (
                <Button variant="outline" size="sm" onClick={startEdit} className="gap-2 rounded-full hover:bg-primary hover:text-primary-foreground transition-all">
                  <Pencil className="h-4 w-4" />
                  Edit Profile
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="px-0">
          <div className="rounded-2xl border bg-card p-6 md:p-8 space-y-8">
          {isLoading ? (
            <LoadingSkeleton />
          ) : (
            <>
              {/* Verification Prompt inside card */}
              {!isLoading && user?.email_verified === false && !verificationSuccess && (
                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 animate-in fade-in slide-in-from-top-2 duration-500">
                  {!verificationRequested ? (
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center text-amber-600">
                          <ShieldAlert className="h-5 w-5" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-amber-900 dark:text-amber-100">Verification Required</h4>
                          <p className="text-xs text-amber-800/70 dark:text-amber-200/50">Verify your email to secure your account.</p>
                        </div>
                      </div>
                      <Button 
                        size="sm" 
                        onClick={handleRequestVerification} 
                        disabled={verificationSending}
                        className="w-full sm:w-auto bg-amber-600 hover:bg-amber-700 text-white rounded-full px-6 shadow-lg shadow-amber-600/20"
                      >
                        {verificationSending ? "Sending…" : "Verify Now"}
                      </Button>
                    </div>
                  ) : (
                    <form onSubmit={handleVerifyEmail} className="space-y-4">
                      <div className="flex items-center gap-3 mb-2">
                        <ShieldAlert className="h-5 w-5 text-amber-600" />
                        <h4 className="text-sm font-bold text-amber-900 dark:text-amber-100">Enter Verification Code</h4>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="verification-token-inner" className="text-[10px] font-bold uppercase tracking-wider text-amber-900/50 dark:text-amber-100/50">Verification Token</Label>
                        <div className="flex flex-col sm:flex-row gap-2">
                          <Input
                            id="verification-token-inner"
                            value={verificationToken}
                            onChange={(e) => setVerificationToken(e.target.value)}
                            placeholder="Paste code from email"
                            className="rounded-xl border-amber-500/30 focus:ring-amber-500/20 flex-1"
                          />
                          <Button 
                            type="submit" 
                            size="sm" 
                            className="bg-amber-600 hover:bg-amber-700 text-white rounded-xl px-8"
                            disabled={verificationVerifying || !verificationToken.trim()}
                          >
                            {verificationVerifying ? "Verifying…" : "Verify"}
                          </Button>
                        </div>
                        {verificationError && <p className="text-[10px] text-red-500 font-medium">{verificationError}</p>}
                      </div>
                    </form>
                  )}
                </div>
              )}

              {/* Verification Success message */}
              {verificationSuccess && (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-green-500/5 border border-green-500/20 animate-in fade-in slide-in-from-top-2 duration-500">
                  <div className="h-10 w-10 rounded-full bg-green-500/10 flex items-center justify-center text-green-600">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-green-900 dark:text-green-100">Account Verified</h4>
                    <p className="text-xs text-green-800/70 dark:text-green-200/50">Your email has been successfully verified.</p>
                  </div>
                </div>
              )}

              {/* Avatar + name row */}
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xl font-bold select-none shrink-0">
                  {initials}
                </div>
                <div className="min-w-0">
                  <p className="text-base font-semibold text-foreground truncate">
                    {displayName ?? "—"}
                  </p>
                  <p className="text-sm text-muted-foreground truncate">
                    {user?.email}
                  </p>
                </div>
              </div>

              <div className="border-t border-border" />

              {/* Save success banner */}
              {saveSuccess && (
                <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                  <p className="text-sm text-green-600 dark:text-green-400">Profile updated successfully.</p>
                </div>
              )}

              {editing ? (
                <form onSubmit={handleSave} className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div className="space-y-1">
                      <Label htmlFor="first-name">First Name</Label>
                      <Input
                        id="first-name"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="First name"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="last-name">Last Name</Label>
                      <Input
                        id="last-name"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Last name"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    <div className="space-y-1">
                      <Label htmlFor="username">Username</Label>
                      <Input
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="e.g. johndoe"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="phone">Phone</Label>
                      <Input
                        id="phone"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="e.g. +1 555 000 0000"
                        type="tel"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="timezone">Timezone</Label>
                    <select
                      id="timezone"
                      value={timezone}
                      onChange={(e) => setTimezone(e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    >
                      <option value="">— Not set —</option>
                      {Intl.supportedValuesOf("timeZone").map((tz) => (
                        <option key={tz} value={tz}>{tz.replace(/_/g, " ")}</option>
                      ))}
                    </select>
                  </div>

                  {saveError && (
                    <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
                      <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                      <p className="text-sm text-red-500">{saveError}</p>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-1">
                    <Button type="submit" size="sm" disabled={saving}>
                      {saving ? "Saving…" : "Save changes"}
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={cancelEdit} disabled={saving}>
                      <X className="h-3.5 w-3.5 mr-1" />
                      Cancel
                    </Button>
                  </div>
                </form>
              ) : (
                  <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                    {[
                      { label: "First Name", value: props["first_name"] || "—", icon: User },
                      { label: "Last Name", value: props["last_name"] || "—", icon: User },
                      { label: "Email Address", value: user?.email ?? "—", icon: Mail },
                      { label: "Username", value: props["username"] || user?.username || "—", icon: Globe },
                      { label: "Phone Number", value: props["phone"] || "—", icon: Phone },
                      { label: "Timezone", value: props["timezone"]?.replace(/_/g, " ") || "Not set", icon: Clock },
                    ].map(({ label, value, icon: Icon }) => (
                      <div key={label} className="group p-4 rounded-xl border bg-muted/30 transition-all hover:bg-muted/50 hover:border-primary/20">
                        <div className="flex items-center gap-3 mb-1">
                          <Icon className="h-4 w-4 text-primary/40 group-hover:text-primary transition-colors" />
                          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70">
                            {label}
                          </span>
                        </div>
                        <span className="text-sm font-semibold text-foreground block truncate pl-7">{value}</span>
                      </div>
                    ))}
                  </div>
              )}
            </>
          )}
          </div>
        </CardContent>
      </Card>

      </div>

      {/* Sidebar Column */}
      <div className="space-y-8 lg:pt-16">
        <div className="lg:sticky lg:top-8 space-y-8">
          
          {/* Default Org & Workspace card */}
          {!isLoading && (
            <Card className="rounded-2xl border bg-card transition-all hover:shadow-lg hover:border-primary/20 overflow-hidden">
              <CardHeader className="border-b bg-muted/30">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-primary/5 flex items-center justify-center text-primary">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">Environment</CardTitle>
                    <CardDescription className="text-xs">
                      Default landing settings.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <form onSubmit={handleSaveDefaults} className="space-y-6">
                  <div className="space-y-4">
                    {/* Org selector */}
                    <div className="space-y-2">
                      <Label htmlFor="default-org" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70 flex items-center gap-2">
                        <Building2 className="h-3 w-3" />
                        Default Organization
                      </Label>
                      {orgs.length === 0 ? (
                        <p className="text-xs text-muted-foreground p-3 border rounded-lg bg-muted/20 text-center">No organizations found.</p>
                      ) : (
                        <select
                          id="default-org"
                          value={selectedOrgId}
                          onChange={(e) => setSelectedOrgId(e.target.value)}
                          className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all hover:border-primary/50"
                        >
                          <option value="">— Select organization —</option>
                          {orgs.map((org) => (
                            <option key={org.id} value={org.id}>
                              {org.name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Workspace selector */}
                    <div className="space-y-2">
                      <Label htmlFor="default-ws" className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70 flex items-center gap-2">
                        <Layers className="h-3 w-3" />
                        Default Workspace
                      </Label>
                      {!selectedOrgId ? (
                        <p className="text-xs text-muted-foreground p-3 border rounded-lg bg-muted/20 text-center">Select an organization first.</p>
                      ) : workspaces.length === 0 ? (
                        <p className="text-xs text-muted-foreground p-3 border rounded-lg bg-muted/20 text-center">No workspaces found.</p>
                      ) : (
                        <select
                          id="default-ws"
                          value={selectedWsId}
                          onChange={(e) => setSelectedWsId(e.target.value)}
                          className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all hover:border-primary/50"
                        >
                          <option value="">— Select workspace —</option>
                          {workspaces.map((ws) => (
                            <option key={ws.id} value={ws.id}>
                              {ws.name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </div>

                  {/* Unsaved indicator */}
                  {(selectedOrgId !== (props["default_org_id"] ?? "") || selectedWsId !== (props["default_workspace_id"] ?? "")) && (
                    <div className="flex items-center gap-2 text-amber-600 bg-amber-500/5 p-2 rounded-lg border border-amber-500/20">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      <p className="text-[10px] font-medium leading-tight">Unsaved workspace changes.</p>
                    </div>
                  )}

                  {defaultSaveSuccess && (
                    <div className="flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-2 py-1.5 animate-in fade-in fill-mode-both">
                      <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
                      <p className="text-[10px] text-green-600 font-medium">Saved!</p>
                    </div>
                  )}
                  
                  {defaultSaveError && (
                    <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-2 py-1.5 animate-in fade-in fill-mode-both">
                      <AlertCircle className="h-3 w-3 text-red-500 shrink-0" />
                      <p className="text-[10px] text-red-500 font-medium">{defaultSaveError}</p>
                    </div>
                  )}

                  <Button
                    type="submit"
                    size="sm"
                    disabled={defaultSaving || !selectedOrgId || !selectedWsId}
                    className="w-full rounded-xl text-xs"
                  >
                    {defaultSaving ? "Saving…" : "Save Preferences"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Linked Accounts card */}
          <Card className="rounded-2xl border transition-all hover:shadow-lg hover:border-primary/20">
            <CardHeader className="border-b bg-muted/30">
              <div className="flex items-center gap-3">
                <Link2 className="h-4 w-4 text-primary/60" />
                <CardTitle className="text-lg">Connected Accounts</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {accountsLoading ? (
                <LoadingSkeleton />
              ) : accountsError ? (
                <div className="flex items-center gap-2 rounded-xl bg-red-500/10 p-3 text-red-500 border border-red-500/20 text-xs">
                  <AlertCircle className="h-3 w-3" />
                  {accountsError}
                </div>
              ) : accounts.length === 0 ? (
                <div className="text-center py-6 space-y-2">
                  <Globe className="h-8 w-8 text-muted-foreground/20 mx-auto" strokeWidth={1} />
                  <p className="text-xs text-muted-foreground">No accounts connected.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {accounts.map((account, idx) => (
                    <div
                      key={`${account.account_type}-${idx}`}
                      className="group flex items-center justify-between rounded-xl border p-3 hover:bg-muted/30 transition-all hover:border-primary/20"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-primary/5 flex items-center justify-center">
                           <Globe size={16} className="text-primary/60 group-hover:text-primary transition-colors" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-sm font-semibold capitalize">
                            {account.account_type.replace(/_/g, " ")}
                          </span>
                          <span className="text-[10px] text-muted-foreground font-medium">
                            {account.is_primary ? "Default Identity" : "Alternative Login"}
                          </span>
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={`text-[10px] px-1.5 py-0 rounded-md ${
                          account.is_active
                            ? "text-green-600 border-green-500/30 bg-green-500/5"
                            : "text-red-500 border-red-500/30 bg-red-500/5"
                        }`}
                      >
                        {account.is_active ? "Live" : "Inactive"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  </div>
  );
}
