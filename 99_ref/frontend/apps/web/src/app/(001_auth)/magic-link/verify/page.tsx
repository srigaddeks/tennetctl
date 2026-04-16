"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2Icon, CheckCircle2Icon, AlertCircleIcon } from "lucide-react";
import { Button } from "@kcontrol/ui";
import Link from "next/link";
import { verifyMagicLink } from "@/lib/api/auth";
import { setAccessToken } from "@/lib/api/apiClient";
import { useAccess } from "@/components/providers/AccessProvider";

function MagicLinkVerifyInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { refreshAccess } = useAccess();
  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [errorMessage, setErrorMessage] = useState("");

  const verify = useCallback(async () => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setErrorMessage("No login token found in the URL.");
      return;
    }
    try {
      const data = await verifyMagicLink(token);
      // Store access token in memory
      setAccessToken(data.access_token);
      // Store refresh token in httpOnly cookie via Next.js route handler
      await fetch("/api/auth/set-refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: data.refresh_token }),
      });
      await refreshAccess();
      setStatus("success");
      // Route assignee/external users to their tasks page, not the main dashboard
      const userCategory = data.user?.user_category;
      if (userCategory && userCategory !== "full") {
        router.replace("/assignee/tasks");
      } else {
        router.replace("/dashboard");
      }
    } catch (err: unknown) {
      setStatus("error");
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "This login link is invalid or has expired."
      );
    }
  }, [searchParams, router, refreshAccess]);

  useEffect(() => {
    verify();
  }, [verify]);

  return (
    <main className="relative min-h-screen bg-background">
      <div
        aria-hidden
        className="absolute inset-0 isolate contain-strict -z-10 opacity-60"
      >
        <div className="bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,--theme(--color-foreground/.06)_0,hsla(0,0%,55%,.02)_50%,--theme(--color-foreground/.01)_80%)] absolute top-0 right-0 h-320 w-140 -translate-y-87.5 rounded-full" />
        <div className="bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] absolute top-0 right-0 h-320 w-60 [translate:5%_-50%] rounded-full" />
        <div className="bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] absolute top-0 right-0 h-320 w-60 -translate-y-87.5 rounded-full" />
      </div>
      <div className="flex min-h-screen flex-col justify-center p-4">
        <div className="mx-auto space-y-4 sm:w-sm w-full max-w-sm">
          {status === "verifying" && (
            <div className="flex flex-col items-center space-y-4 text-center">
              <Loader2Icon className="size-8 animate-spin text-muted-foreground" />
              <div className="space-y-1">
                <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                  Signing you in
                </h1>
                <p className="text-muted-foreground text-base font-primary">
                  Verifying your login link...
                </p>
              </div>
            </div>
          )}

          {status === "success" && (
            <div className="flex flex-col items-center space-y-4 text-center">
              <CheckCircle2Icon className="size-8 text-emerald-500" />
              <div className="space-y-1">
                <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                  Signed in
                </h1>
                <p className="text-muted-foreground text-base font-primary">
                  Redirecting you...
                </p>
              </div>
            </div>
          )}

          {status === "error" && (
            <div className="space-y-4">
              <div className="flex flex-col items-center space-y-4 text-center">
                <AlertCircleIcon className="size-8 text-red-500" />
                <div className="space-y-1">
                  <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                    Link invalid
                  </h1>
                  <p className="text-muted-foreground text-base font-primary">
                    {errorMessage}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Button
                  className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
                  asChild
                >
                  <Link href="/magic-link">
                    <span className="font-primary">Request a new login link</span>
                  </Link>
                </Button>
                <Button
                  variant="link"
                  className="px-0 py-0 h-auto font-semibold text-primary"
                  asChild
                >
                  <Link href="/login">Back to sign in</Link>
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default function MagicLinkVerifyPage() {
  return (
    <Suspense>
      <MagicLinkVerifyInner />
    </Suspense>
  );
}
