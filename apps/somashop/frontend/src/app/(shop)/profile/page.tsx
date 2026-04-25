"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getMe, setToken } from "@/lib/api";

type Me = {
  user: { id: string; display_name?: string | null };
  session: { id: string; org_id: string | null; workspace_id: string | null };
};

type State =
  | { status: "loading" }
  | { status: "ok"; me: Me }
  | { status: "anon" };

export default function ProfilePage() {
  const router = useRouter();
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    void getMe().then((me) => {
      if (!me) setState({ status: "anon" });
      else setState({ status: "ok", me: me as Me });
    });
  }, []);

  function signOut() {
    setToken(null);
    router.push("/signin");
  }

  if (state.status === "loading") {
    return <p style={{ color: "var(--text-muted)" }}>Loading…</p>;
  }
  if (state.status === "anon") {
    return (
      <div className="max-w-reading">
        <h1 className="font-heading text-3xl font-bold mb-4">Sign in</h1>
        <p style={{ color: "var(--text-secondary)" }} className="mb-6">
          Sign in to view your subscription and delivery details.
        </p>
        <Link href="/signin" className="btn btn-primary">
          Sign in →
        </Link>
      </div>
    );
  }

  const me = state.me;
  return (
    <div className="max-w-reading">
      <p
        className="text-xs tracking-[0.2em] uppercase mb-3"
        style={{ color: "var(--text-muted)" }}
      >
        Your account
      </p>
      <h1 className="font-heading text-4xl font-bold mb-8">
        {me.user.display_name || "Welcome"}
      </h1>

      <section
        className="card p-6 mb-8 space-y-4"
      >
        <div>
          <p
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Customer ID
          </p>
          <p className="font-mono text-sm" style={{ color: "var(--text-secondary)" }}>
            {me.user.id}
          </p>
        </div>
        <div>
          <p
            className="text-xs tracking-[0.15em] uppercase mb-1"
            style={{ color: "var(--text-muted)" }}
          >
            Account type
          </p>
          <p style={{ color: "var(--text-secondary)" }}>
            Soma Delights customer
          </p>
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <Link href="/orders" className="btn btn-ghost">
          See your orders
        </Link>
        <Link href="/products" className="btn btn-ghost">
          Browse menu
        </Link>
        <button onClick={signOut} className="btn btn-primary">
          Sign out
        </button>
      </div>

      <p
        className="mt-12 text-sm leading-relaxed"
        style={{ color: "var(--text-muted)" }}
      >
        Need to update your delivery address? Cancel a subscription? Reply to
        your last delivery confirmation message — we'll handle it. Self-serve
        editing is coming.
      </p>
    </div>
  );
}
