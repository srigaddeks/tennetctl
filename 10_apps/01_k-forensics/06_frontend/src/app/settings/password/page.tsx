"use client";

import * as React from "react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { login } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function PasswordPage() {
  const { status, ...rest } = useAuth();
  const me = status === "authenticated"
    ? (rest as { me: { username: string | null } }).me
    : null;

  const [current, setCurrent] = React.useState("");
  const [next, setNext] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState("");

  if (!me) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (next !== confirm) { setError("Passwords don't match"); return; }
    if (next.length < 8) { setError("Password must be at least 8 characters"); return; }

    setSaving(true);
    const verifyRes = await login(me!.username ?? "", current);
    if (!verifyRes.ok) { setSaving(false); setError("Current password is incorrect"); return; }

    setSaving(false);
    setError("");
    toast.error("Password change is not yet supported by the API — contact your platform admin.");
  }

  return (
    <section>
      <h2 className="text-base font-semibold mb-1">Change password</h2>
      <p className="text-xs text-foreground-muted mb-5">Update your login password.</p>

      <Card className="max-w-[420px]">
        <CardContent className="pt-5">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Current password</Label>
              <Input type="password" value={current} onChange={e => setCurrent(e.target.value)} autoComplete="current-password" required />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>New password</Label>
              <Input type="password" value={next} onChange={e => setNext(e.target.value)} autoComplete="new-password" required />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Confirm new password</Label>
              <Input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} autoComplete="new-password" required />
            </div>
            {error && <p className="text-xs text-[color:var(--danger)]">{error}</p>}
            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? "Verifying…" : "Change password"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
