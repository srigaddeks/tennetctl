"use client";

import { useState, Suspense } from "react";
import { Button, Input } from "@kcontrol/ui";
import {
  LockIcon,
  EyeIcon,
  EyeOffIcon,
  CheckCircle2Icon,
  AlertTriangleIcon,
} from "lucide-react";
import { resetPassword } from "@/lib/api/auth";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  if (!token) {
    return (
      <div className="space-y-4">
        <div className="p-4 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md flex items-start gap-3">
          <AlertTriangleIcon className="size-5 mt-0.5 shrink-0" />
          <span>Invalid or missing reset token.</span>
        </div>
        <Button
          variant="link"
          className="px-0 py-0 h-auto font-semibold text-primary"
          asChild
        >
          <Link href="/forgot-password">Request a new reset link</Link>
        </Button>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setIsLoading(true);
      await resetPassword(token, newPassword);
      setSuccess(true);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reset password. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="space-y-4">
        <div className="p-4 text-sm text-emerald-600 bg-emerald-100/10 border border-emerald-500/20 rounded-md flex items-start gap-3">
          <CheckCircle2Icon className="size-5 mt-0.5 shrink-0" />
          <span>
            Your password has been reset successfully. You can now sign in with
            your new password.
          </span>
        </div>
        <Button
          className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
          asChild
        >
          <Link href="/login">
            <span className="font-primary">Sign In</span>
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit}>
      {error && (
        <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md">
          {error}
        </div>
      )}

      <div className="relative h-max">
        <Input
          placeholder="New Password"
          className="peer ps-9 pe-9 border-zinc-200 dark:border-zinc-800"
          type={showPassword ? "text" : "password"}
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          disabled={isLoading}
          required
        />
        <div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
          <LockIcon className="size-4" aria-hidden="true" />
        </div>
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="text-muted-foreground hover:text-foreground absolute inset-y-0 end-0 flex items-center justify-center pe-3 transition-colors focus:outline-none"
          aria-label={showPassword ? "Hide password" : "Show password"}
        >
          {showPassword ? (
            <EyeIcon className="size-4" aria-hidden="true" />
          ) : (
            <EyeOffIcon className="size-4" aria-hidden="true" />
          )}
        </button>
      </div>

      <div className="relative h-max">
        <Input
          placeholder="Confirm Password"
          className="peer ps-9 pe-9 border-zinc-200 dark:border-zinc-800"
          type={showConfirmPassword ? "text" : "password"}
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={isLoading}
          required
        />
        <div className="text-muted-foreground pointer-events-none absolute inset-y-0 start-0 flex items-center justify-center ps-3 peer-disabled:opacity-50">
          <LockIcon className="size-4" aria-hidden="true" />
        </div>
        <button
          type="button"
          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
          className="text-muted-foreground hover:text-foreground absolute inset-y-0 end-0 flex items-center justify-center pe-3 transition-colors focus:outline-none"
          aria-label={
            showConfirmPassword ? "Hide password" : "Show password"
          }
        >
          {showConfirmPassword ? (
            <EyeIcon className="size-4" aria-hidden="true" />
          ) : (
            <EyeOffIcon className="size-4" aria-hidden="true" />
          )}
        </button>
      </div>

      <p className="text-muted-foreground text-xs font-primary">
        Password must be at least 12 characters.
      </p>

      <Button
        type="submit"
        className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
        disabled={isLoading}
      >
        <span className="font-primary">
          {isLoading ? "Please wait..." : "Reset Password"}
        </span>
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
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
              Reset Password
            </h1>
            <p className="text-muted-foreground text-base font-primary">
              Enter your new password
            </p>
          </div>

          <Suspense fallback={null}>
            <ResetPasswordForm />
          </Suspense>

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
        </div>
      </div>
    </main>
  );
}
