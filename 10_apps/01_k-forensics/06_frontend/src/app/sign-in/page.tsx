"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export default function SignInPage() {
  const { signIn, status } = useAuth();
  const router = useRouter();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (status === "authenticated") router.replace("/");
  }, [status, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const res = await signIn(username, password);
    setLoading(false);
    if (res.ok) router.push("/");
    else setError(res.message);
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6 p-6">
      <div className="font-bold text-xl tracking-tight text-foreground">k-forensics</div>
      <Card className="w-full max-w-[380px]">
        <CardContent className="pt-6">
          <h1 className="text-lg font-semibold mb-5">Sign in</h1>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-xs text-[color:var(--danger)]">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Signing in\u2026" : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-xs text-foreground-muted text-center">
            No account?{" "}
            <Link href="/sign-up" className="text-foreground underline underline-offset-4 hover:text-foreground-muted">
              Create one
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
