"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { requestMobileOtp, setToken, verifyMobileOtp } from "@/lib/api";

type Step = "phone" | "code";

export default function SignInPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>("phone");
  const [phone, setPhone] = useState("+91");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [debugCode, setDebugCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendOtp(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const r = await requestMobileOtp(phone.trim());
      setDebugCode(r.debug_code ?? null);
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send code");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const r = await verifyMobileOtp({
        phone_e164: phone.trim(),
        code: code.trim(),
        display_name: name.trim() || undefined,
      });
      setToken(r.token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex" style={{ background: "var(--bg-page)" }}>
      {/* Left: brand panel */}
      <aside
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-16"
        style={{ background: "var(--bg-inverse)", color: "var(--text-on-inverse)" }}
      >
        <div className="font-heading text-2xl font-bold">Soma Delights</div>
        <div>
          <h1 className="font-heading text-5xl font-extrabold leading-tight tracking-tight">
            Quiet luxury,
            <br />
            radically transparent.
          </h1>
          <p
            className="mt-6 text-base leading-relaxed max-w-md"
            style={{ color: "var(--grey-300)" }}
          >
            Cold-pressed daily. Six ingredients or fewer. Delivered in
            Hyderabad before breakfast.
          </p>
        </div>
        <p className="text-xs tracking-[0.2em] uppercase" style={{ color: "var(--grey-400)" }}>
          Powered by tennetctl
        </p>
      </aside>

      {/* Right: form */}
      <main className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <h2 className="font-heading text-3xl font-bold mb-2">
            {step === "phone" ? "Sign in" : "Verify your number"}
          </h2>
          <p
            className="mb-8 text-sm leading-relaxed"
            style={{ color: "var(--text-muted)" }}
          >
            {step === "phone"
              ? "Enter your mobile number. We'll send a one-time code by SMS."
              : "Enter the 6-digit code we just sent you."}
          </p>

          {step === "phone" && (
            <form onSubmit={handleSendOtp} className="space-y-4">
              <div>
                <label
                  className="block text-xs tracking-[0.15em] uppercase mb-2"
                  style={{ color: "var(--text-muted)" }}
                >
                  Mobile number
                </label>
                <input
                  className="input"
                  type="tel"
                  placeholder="+91 9876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                />
              </div>
              <div>
                <label
                  className="block text-xs tracking-[0.15em] uppercase mb-2"
                  style={{ color: "var(--text-muted)" }}
                >
                  Your name (optional)
                </label>
                <input
                  className="input"
                  type="text"
                  placeholder="Lakshmi"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              {error && (
                <p className="text-sm" style={{ color: "var(--status-error)" }}>
                  {error}
                </p>
              )}
              <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                {loading ? "Sending..." : "Send code →"}
              </button>
            </form>
          )}

          {step === "code" && (
            <form onSubmit={handleVerify} className="space-y-4">
              <div>
                <label
                  className="block text-xs tracking-[0.15em] uppercase mb-2"
                  style={{ color: "var(--text-muted)" }}
                >
                  6-digit code
                </label>
                <input
                  className="input mono text-center text-xl tracking-[0.4em]"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  placeholder="••••••"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              {debugCode && (
                <div
                  className="text-xs p-3 rounded font-mono"
                  style={{
                    background: "var(--bg-muted)",
                    color: "var(--text-muted)",
                    border: "1px solid var(--border)",
                  }}
                >
                  Stub mode (no Twilio configured) — debug code:{" "}
                  <span className="font-bold" style={{ color: "var(--text-primary)" }}>
                    {debugCode}
                  </span>
                </div>
              )}
              {error && (
                <p className="text-sm" style={{ color: "var(--status-error)" }}>
                  {error}
                </p>
              )}
              <button type="submit" className="btn btn-primary w-full" disabled={loading}>
                {loading ? "Verifying..." : "Verify + sign in →"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep("phone");
                  setCode("");
                  setError(null);
                }}
                className="btn btn-ghost w-full"
              >
                Use a different number
              </button>
            </form>
          )}
        </div>
      </main>
    </div>
  );
}
