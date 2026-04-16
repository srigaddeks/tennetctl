"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { acceptInvitation, acceptInvitationPublic, declineInvitation, InviteUserNotFoundError, previewInvitation, type InvitationPreview } from "@/lib/api/admin";
import {
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@kcontrol/ui";
import { CheckCircle2, AlertCircle, Loader2, XCircle, Mail, ShieldCheck } from "lucide-react";

const GRC_ROLE_LABELS: Record<string, string> = {
  grc_lead: "GRC Lead",
  grc_sme: "GRC Subject Matter Expert",
  grc_engineer: "GRC Engineer",
  grc_ciso: "CISO",
  grc_lead_auditor: "Lead Auditor",
  grc_staff_auditor: "Staff Auditor",
  grc_vendor: "Vendor",
};

interface AcceptResult {
  message: string;
  scope: string;
  org_id: string | null;
  workspace_id: string | null;
  role: string | null;
  grc_role_code: string | null;
}

type PageState =
  | { kind: "loading" }
  | { kind: "confirm"; token: string; preview: InvitationPreview | null }
  | { kind: "accepting" }
  | { kind: "declining" }
  | { kind: "success"; result: AcceptResult }
  | { kind: "declined" }
  | { kind: "error"; message: string; canRetry: boolean };

function AcceptInviteContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [state, setState] = useState<PageState>({ kind: "loading" });
  // Set by login redirect — signals that the user just logged in and we should auto-accept
  const autoAccept = searchParams.get("auto_accept") === "1";

  useEffect(() => {
    if (!token) {
      setState({ kind: "error", message: "Invalid invitation link", canRetry: false });
      return;
    }

    if (autoAccept) {
      // User just logged in as the invited email — attempt accept immediately
      setState({ kind: "accepting" });
      acceptInvitation(token)
        .then((data) => {
          const r = data as AcceptResult;
          // Pre-select the invited org/workspace so dashboard shows the right context
          if (r.org_id) localStorage.setItem("kcontrol:selectedOrgId", r.org_id);
          if (r.workspace_id) localStorage.setItem("kcontrol:selectedWorkspaceId", r.workspace_id);
          setState({ kind: "success", result: r });
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : "Failed to accept invitation";
          if (message === "401") {
            // Session not established yet — send back to login
            const returnUrl = `/accept-invite?token=${encodeURIComponent(token)}`;
            router.replace(`/login?returnUrl=${encodeURIComponent(returnUrl)}&invite_token=${encodeURIComponent(token)}`);
            return;
          }
          setState({ kind: "error", message, canRetry: false });
        });
      return;
    }

    previewInvitation(token).then((preview) => {
      setState({ kind: "confirm", token, preview });
    }).catch(() => {
      setState({ kind: "confirm", token, preview: null });
    });
  }, [token, autoAccept]);

  const handleAccept = useCallback(async (inviteToken: string, preview: InvitationPreview | null) => {
    setState({ kind: "accepting" });
    try {
      const result = await acceptInvitationPublic(inviteToken);
      // Pre-select org/workspace so the dashboard shows the right context after login
      if (result.org_id) localStorage.setItem("kcontrol:selectedOrgId", result.org_id);
      if (result.workspace_id) localStorage.setItem("kcontrol:selectedWorkspaceId", result.workspace_id);
      setState({
        kind: "success",
        result: {
          message: result.message,
          scope: result.scope,
          org_id: result.org_id,
          workspace_id: result.workspace_id,
          role: result.role,
          grc_role_code: result.grc_role_code,
        },
      });
    } catch (err: unknown) {
      if (err instanceof InviteUserNotFoundError) {
        // No account yet — run signup. The register page fetches the email from the token.
        router.replace(`/register?invite_token=${encodeURIComponent(inviteToken)}`);
        return;
      }
      const message = err instanceof Error ? err.message : "Failed to accept invitation";
      setState({ kind: "error", message, canRetry: true });
    }
    // preview unused in the public-accept path; kept in signature for compatibility with the confirm screen.
    void preview;
  }, [router]);

  const handleDecline = useCallback(async (inviteToken: string) => {
    setState({ kind: "declining" });
    try {
      await declineInvitation(inviteToken);
      setState({ kind: "declined" });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to decline invitation";
      if (message.includes("401") || message.toLowerCase().includes("unauthorized")) {
        const returnUrl = `/accept-invite?token=${encodeURIComponent(inviteToken)}`;
        router.replace(`/login?returnUrl=${encodeURIComponent(returnUrl)}`);
        return;
      }
      setState({ kind: "error", message, canRetry: true });
    }
  }, [router]);

  // ── No token ──────────────────────────────────────────────────────────────
  if (!token && state.kind === "error") {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <AlertCircle className="h-10 w-10 text-destructive mb-2" />
          <CardTitle>Invalid Link</CardTitle>
          <CardDescription>{state.message}</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Button variant="outline" onClick={() => router.push("/login")}>Go to Login</Button>
        </CardContent>
      </Card>
    );
  }

  // ── Loading / in-flight ───────────────────────────────────────────────────
  if (state.kind === "loading" || state.kind === "accepting" || state.kind === "declining") {
    const label = state.kind === "accepting" ? "Accepting invitation..."
      : state.kind === "declining" ? "Declining invitation..."
      : "Loading...";
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <Loader2 className="h-10 w-10 animate-spin text-muted-foreground mb-2" />
          <CardTitle>{label}</CardTitle>
          <CardDescription>Please wait a moment.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // ── Confirmation ──────────────────────────────────────────────────────────
  if (state.kind === "confirm") {
    const { preview } = state;
    const scopeName = preview?.workspace_name ?? preview?.org_name ?? null;
    const isGrc = !!preview?.grc_role_code;
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          {isGrc ? (
            <ShieldCheck className="h-10 w-10 text-primary mb-2" />
          ) : (
            <Mail className="h-10 w-10 text-primary mb-2" />
          )}
          <CardTitle>You&apos;ve Been Invited</CardTitle>
          <CardDescription>
            {scopeName
              ? `You've been invited to join ${scopeName}.`
              : "You have a pending invitation to join this platform."}
            {isGrc && preview?.grc_role_code && (
              <> Your role will be <strong>{GRC_ROLE_LABELS[preview.grc_role_code] ?? preview.grc_role_code}</strong>.</>
            )}
          </CardDescription>
        </CardHeader>
        {preview && (
          <CardContent className="pb-0">
            <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm border rounded-lg p-3 bg-muted/30 mb-4">
              {preview.org_name && (
                <>
                  <dt className="text-muted-foreground">Organization</dt>
                  <dd className="font-medium">{preview.org_name}</dd>
                </>
              )}
              {preview.workspace_name && (
                <>
                  <dt className="text-muted-foreground">Workspace</dt>
                  <dd className="font-medium">{preview.workspace_name}</dd>
                </>
              )}
              {preview.grc_role_code && (
                <>
                  <dt className="text-muted-foreground">GRC Role</dt>
                  <dd className="font-medium text-primary">{GRC_ROLE_LABELS[preview.grc_role_code] ?? preview.grc_role_code}</dd>
                </>
              )}
            </dl>
          </CardContent>
        )}
        <CardContent className="flex justify-center gap-3 pt-2">
          <Button variant="outline" onClick={() => handleDecline(state.token)}>
            Decline
          </Button>
          <Button onClick={() => handleAccept(state.token, state.preview)}>
            {state.preview && !state.preview.user_exists ? "Sign Up & Accept" : "Accept Invitation"}
          </Button>
        </CardContent>
      </Card>
    );
  }

  // ── Success ───────────────────────────────────────────────────────────────
  if (state.kind === "success") {
    const { result } = state;
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <CheckCircle2 className="h-10 w-10 text-green-500 mb-2" />
          <CardTitle>Invitation Accepted</CardTitle>
          <CardDescription>{result.message}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Scope</dt>
            <dd className="font-medium capitalize">{result.scope}</dd>
            {result.role && (
              <>
                <dt className="text-muted-foreground">Role</dt>
                <dd className="font-medium capitalize">{result.role}</dd>
              </>
            )}
            {result.grc_role_code && (
              <>
                <dt className="text-muted-foreground flex items-center gap-1"><ShieldCheck className="h-3.5 w-3.5" /> GRC Role</dt>
                <dd className="font-medium text-primary">{GRC_ROLE_LABELS[result.grc_role_code] ?? result.grc_role_code}</dd>
              </>
            )}
          </dl>
          <div className="flex justify-center pt-2">
            {autoAccept ? (
              <Button onClick={() => router.push("/dashboard")}>Go to Dashboard</Button>
            ) : (
              <Button onClick={() => router.push("/login")}>Sign In to Continue</Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // ── Declined ──────────────────────────────────────────────────────────────
  if (state.kind === "declined") {
    return (
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <XCircle className="h-10 w-10 text-muted-foreground mb-2" />
          <CardTitle>Invitation Declined</CardTitle>
          <CardDescription>
            You have declined this invitation. If this was a mistake, contact the person who invited you.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center">
          <Button variant="outline" onClick={() => router.push("/login")}>Go to Login</Button>
        </CardContent>
      </Card>
    );
  }

  // ── Error ─────────────────────────────────────────────────────────────────
  return (
    <Card className="w-full max-w-md">
      <CardHeader className="items-center text-center">
        <AlertCircle className="h-10 w-10 text-destructive mb-2" />
        <CardTitle>Something Went Wrong</CardTitle>
        <CardDescription>{state.message}</CardDescription>
      </CardHeader>
      <CardContent className="flex justify-center gap-3">
        {state.canRetry && token && (
          <Button onClick={() => handleAccept(token, null)}>Retry</Button>
        )}
        <Button variant="outline" onClick={() => router.push("/login")}>Go to Login</Button>
      </CardContent>
    </Card>
  );
}

export default function AcceptInvitePage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Suspense
        fallback={
          <Card className="w-full max-w-md">
            <CardHeader className="items-center text-center">
              <Loader2 className="h-10 w-10 animate-spin text-muted-foreground mb-2" />
              <CardTitle>Loading...</CardTitle>
            </CardHeader>
          </Card>
        }
      >
        <AcceptInviteContent />
      </Suspense>
    </div>
  );
}
