"use client";

import { useState } from "react";
import { Button, Input } from "@kcontrol/ui";
import { AtSignIcon, ArrowLeftIcon, MailIcon } from "lucide-react";
import { forgotPassword } from "@/lib/api/auth";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [login, setLogin] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      setError(null);
      await forgotPassword(login);
      setSuccess(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to send reset link. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

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
          <div className="flex flex-col space-y-1">
            <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
              Forgot Password
            </h1>
            <p className="text-muted-foreground text-base font-primary">
              Enter your email and we&apos;ll send you a reset link
            </p>
          </div>

          {success ? (
            <div className="space-y-4">
              <div className="p-4 text-sm text-emerald-600 bg-emerald-100/10 border border-emerald-500/20 rounded-md flex items-start gap-3">
                <MailIcon className="size-5 mt-0.5 shrink-0" />
                <span>
                  If an account exists with that email, you&apos;ll receive a
                  reset link shortly.
                </span>
              </div>
              <Button
                variant="link"
                className="px-0 py-0 h-auto font-semibold text-primary"
                asChild
              >
                <Link href="/login">
                  <ArrowLeftIcon className="size-4 me-1" />
                  Back to Sign In
                </Link>
              </Button>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={handleSubmit}>
              {error && (
                <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md">
                  {error}
                </div>
              )}

              <div className="relative h-max">
                <Input
                  placeholder="Email or username"
                  className="peer ps-9 border-zinc-200 dark:border-zinc-800"
                  type="text"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  disabled={isLoading}
                  required
                />
                <div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
                  <AtSignIcon className="size-4" aria-hidden="true" />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
                disabled={isLoading}
              >
                <span className="font-primary">
                  {isLoading ? "Please wait..." : "Send Reset Link"}
                </span>
              </Button>
            </form>
          )}

          {!success && (
            <div className="text-muted-foreground text-center text-sm">
              Remember your password?{" "}
              <Button
                variant="link"
                className="px-0 py-0 h-auto font-semibold text-primary"
                asChild
              >
                <Link href="/login">Sign In</Link>
              </Button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
