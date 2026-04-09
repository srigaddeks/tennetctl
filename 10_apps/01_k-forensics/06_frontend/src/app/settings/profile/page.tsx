"use client";

import * as React from "react";
import { toast } from "sonner";
import { useAuth } from "@/lib/auth-context";
import { patchUser } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ProfilePage() {
  const { status, ...rest } = useAuth();
  const accessToken = status === "authenticated" ? (rest as { accessToken: string }).accessToken : null;
  const me = status === "authenticated"
    ? (rest as { me: { user_id: string; username: string | null; email: string | null; session_id: string } }).me
    : null;

  const [email, setEmail] = React.useState(me?.email ?? "");
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (me?.email) setEmail(me.email);
  }, [me?.email]);

  if (!accessToken || !me) return null;

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const res = await patchUser(me!.user_id, { email }, accessToken!);
    setSaving(false);
    if (res.ok) toast.success("Email updated");
    else toast.error(res.error.message);
  }

  return (
    <section>
      <h2 className="text-base font-semibold mb-1">Profile</h2>
      <p className="text-xs text-foreground-muted mb-5">Manage your account information.</p>

      <Card className="max-w-[480px]">
        <CardContent className="pt-5">
          <div className="flex gap-4 items-center mb-6">
            <div className="w-[52px] h-[52px] rounded-full bg-surface-2 text-foreground-muted flex items-center justify-center text-xl font-bold">
              {(me.username ?? "?")[0].toUpperCase()}
            </div>
            <div>
              <div className="font-semibold text-[15px]">{me.username}</div>
              <div className="text-xs text-foreground-muted font-mono">{me.user_id}</div>
            </div>
          </div>

          <form onSubmit={handleSave} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Username</Label>
              <Input value={me.username ?? ""} disabled className="opacity-50" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Email</Label>
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
