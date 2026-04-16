"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Building2, User, CheckCircle2, Loader2, ShieldCheck, Mail, KeyRound } from "lucide-react";
import { Button, Input, Logo, ThemeToggle, cn } from "@kcontrol/ui";
import { fetchMe, setUserProperties, requestOTP, verifyOTP } from "@/lib/api/auth";
import { createOrg } from "@/lib/api/orgs";
import { createWorkspace } from "@/lib/api/workspaces";
import { setEntitySetting } from "@/lib/api/admin";

const PRODUCT_ID_KCONTROL = "00000000-0000-0000-0000-000000001201";
const PRODUCT_ID_SANDBOX = "00000000-0000-0000-0000-000000001202";

type AccountKind = "personal" | "business";
type OnboardingStep = "otp" | "profile" | "setup";

interface SetupStep {
  label: string;
  status: "pending" | "running" | "done" | "error";
}

function makeSlug(name: string): string {
  const base = name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 40);
  const suffix = Math.random().toString(36).slice(2, 6);
  return base.length >= 2 ? `${base}-${suffix}` : `org-${suffix}`;
}

export default function OnboardingPage() {
  const router = useRouter();

  // Start on OTP step — verify email first
  const [step, setStep] = useState<OnboardingStep>("otp");
  const [accountKind, setAccountKind] = useState<AccountKind>("personal");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const [businessName, setBusinessName] = useState("");

  // OTP state
  const [otpDigits, setOtpDigits] = useState<string[]>(["", "", "", "", "", ""]);
  const [otpSending, setOtpSending] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpCountdown, setOtpCountdown] = useState(0);
  const [userEmail, setUserEmail] = useState("");
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Setup state
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [setupSteps, setSetupSteps] = useState<SetupStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  // On mount: fetch user and auto-send OTP
  useEffect(() => {
    fetchMe()
      .then((u) => {
        setUserId(u.user_id);
        setUserEmail(u.email);
      })
      .catch(() => router.replace("/login"));
  }, [router]);

  // Auto-send OTP once we have the user email (with retry on failure)
  const otpAutoSent = useRef(false);
  const otpRetryCount = useRef(0);
  useEffect(() => {
    if (userEmail && step === "otp" && !otpAutoSent.current) {
      otpAutoSent.current = true;
      const sendWithRetry = async () => {
        try {
          await handleSendOTP();
        } catch {
          // Auto-retry up to 2 times with 2s delay
          if (otpRetryCount.current < 2) {
            otpRetryCount.current += 1;
            setTimeout(sendWithRetry, 2000);
          }
        }
      };
      sendWithRetry();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userEmail, step]);

  // Countdown timer for resend
  useEffect(() => {
    if (otpCountdown <= 0) return;
    const timer = setTimeout(() => setOtpCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [otpCountdown]);

  function updateStep(index: number, status: SetupStep["status"]) {
    setSetupSteps((prev) =>
      prev.map((s, i) => (i === index ? { ...s, status } : s))
    );
  }

  const canSubmitProfile =
    firstName.trim().length > 0 &&
    lastName.trim().length > 0 &&
    (accountKind === "personal" || businessName.trim().length > 0);

  // ── Send OTP ──
  const handleSendOTP = useCallback(async () => {
    setOtpSending(true);
    setOtpError(null);
    try {
      await requestOTP();
      setOtpSent(true);
      setOtpCountdown(60);
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    } catch (err: unknown) {
      setOtpError(err instanceof Error ? err.message : "Failed to send OTP");
    } finally {
      setOtpSending(false);
    }
  }, []);

  // ── Handle OTP digit input ──
  function handleOtpChange(index: number, value: string) {
    if (!/^\d*$/.test(value)) return;
    const newDigits = [...otpDigits];
    if (value.length > 1) {
      const chars = value.slice(0, 6).split("");
      chars.forEach((c, i) => {
        if (index + i < 6) newDigits[index + i] = c;
      });
      setOtpDigits(newDigits);
      const nextIdx = Math.min(index + chars.length, 5);
      inputRefs.current[nextIdx]?.focus();
    } else {
      newDigits[index] = value;
      setOtpDigits(newDigits);
      if (value && index < 5) inputRefs.current[index + 1]?.focus();
    }
  }

  function handleOtpKeyDown(index: number, e: React.KeyboardEvent) {
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  }

  // ── Verify OTP → go to Profile step ──
  async function handleVerifyOTP() {
    const code = otpDigits.join("");
    if (code.length !== 6) return;
    setOtpVerifying(true);
    setOtpError(null);
    try {
      await verifyOTP(code);
      setStep("profile");
    } catch (err: unknown) {
      setOtpError(err instanceof Error ? err.message : "Verification failed");
      setOtpDigits(["", "", "", "", "", ""]);
      inputRefs.current[0]?.focus();
    } finally {
      setOtpVerifying(false);
    }
  }

  // ── Profile submit → save profile + run setup ──
  async function handleProfileSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userId || !canSubmitProfile) return;

    setError(null);
    setStep("setup");

    const orgName =
      accountKind === "business"
        ? businessName.trim()
        : `${firstName.trim()} ${lastName.trim()}`;

    const steps: SetupStep[] = [
      { label: "Saving your profile", status: "pending" },
      { label: "Creating your organization", status: "pending" },
      { label: "Setting up K-Control workspace", status: "pending" },
      { label: "Setting up K-Control Sandbox", status: "pending" },
      { label: "Finalizing your account", status: "pending" },
    ];
    setSetupSteps(steps);
    setIsSettingUp(true);

    try {
      // Step 1: Save profile
      updateStep(0, "running");
      const profileProps: Record<string, string> = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        display_name: `${firstName.trim()} ${lastName.trim()}`,
      };
      if (phone.trim()) profileProps.phone = phone.trim();
      await setUserProperties(profileProps);
      updateStep(0, "done");

      // Step 2: Create org (backend auto-adds creator as "owner" in org_memberships)
      updateStep(1, "running");
      const org = await createOrg({
        name: orgName,
        slug: makeSlug(orgName),
        org_type_code: accountKind === "business" ? "company" : "personal",
      });
      updateStep(1, "done");

      // Step 3: K-Control workspace (backend auto-adds creator as "owner" in ws_memberships)
      updateStep(2, "running");
      const wsKControl = await createWorkspace(org.id, {
        name: "K-Control",
        slug: makeSlug(`${orgName}-kcontrol`),
        workspace_type_code: "project",
        product_id: PRODUCT_ID_KCONTROL,
        description: "Primary K-Control compliance workspace",
      });
      updateStep(2, "done");

      // Step 4: Sandbox workspace (backend auto-adds creator as "owner" in ws_memberships)
      updateStep(3, "running");
      const wsSandbox = await createWorkspace(org.id, {
        name: "K-Control Sandbox",
        slug: makeSlug(`${orgName}-sandbox`),
        workspace_type_code: "sandbox",
        product_id: PRODUCT_ID_SANDBOX,
        description: "Sandboxed testing instance of K-Control",
      });
      updateStep(3, "done");

      // Step 5: Finalize
      updateStep(4, "running");
      await setEntitySetting("org", org.id, "license_tier", "free").catch(() => {});
      await setUserProperties({
        default_org_id: org.id,
        default_workspace_id: wsKControl.id,
        onboarding_complete: "true",
      });
      updateStep(4, "done");

      await new Promise((r) => setTimeout(r, 600));
      router.replace("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Setup failed. Please try again.");
      setIsSettingUp(false);
      setSetupSteps((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "error" } : s))
      );
    }
  }

  // ── Mask email ──
  function maskEmail(email: string): string {
    const [local, domain] = email.split("@");
    if (!domain) return email;
    const visible = local.slice(0, 2);
    return `${visible}${"*".repeat(Math.max(local.length - 2, 2))}@${domain}`;
  }

  return (
    <main className="relative md:h-screen md:overflow-hidden lg:grid lg:grid-cols-2 bg-background">

      {/* ── Left branding panel ── */}
      <div className="bg-muted/60 relative hidden h-full flex-col border-r p-10 lg:flex overflow-hidden">
        <div
          className="absolute inset-0 z-0 opacity-20"
          style={{
            backgroundImage:
              "linear-gradient(to right, currentColor 1px, transparent 1px), linear-gradient(to bottom, currentColor 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="from-background absolute inset-0 z-10 bg-gradient-to-t to-transparent opacity-60" />

        <div className="z-20 flex items-center gap-2">
          <Logo className="h-8" />
        </div>

        <div className="z-20 mt-auto space-y-8">
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "DPDP", desc: "India Data Protection" },
              { label: "GDPR", desc: "EU Privacy Regulation" },
              { label: "ISO 27001", desc: "Information Security" },
              { label: "SOC 2", desc: "Trust & Availability" },
            ].map((f) => (
              <div
                key={f.label}
                className="rounded-xl border border-border/50 bg-background/30 backdrop-blur-sm px-4 py-3"
              >
                <p className="text-xs font-semibold text-foreground">{f.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{f.desc}</p>
              </div>
            ))}
          </div>

          <div className="max-w-sm space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary shrink-0" />
              <p className="text-sm font-semibold text-foreground tracking-wide uppercase">
                K-Control: Compliance, Built-In by Design
              </p>
            </div>
            <p className="text-lg font-medium leading-relaxed text-foreground/90">
              See what applies. Find what&apos;s missing. Stay audit-ready.
              Enforce DPDP, GDPR, ISO, SOC&nbsp;2, and more automatically.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              K-Control is your AI-powered control and assessment workspace.
              Sign up to access.
            </p>
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="relative flex min-h-screen flex-col justify-center p-4 bg-background">
        <div aria-hidden className="absolute inset-0 isolate contain-strict -z-10 opacity-60">
          <div className="bg-[radial-gradient(68.54%_68.72%_at_55.02%_31.46%,--theme(--color-foreground/.06)_0,hsla(0,0%,55%,.02)_50%,--theme(--color-foreground/.01)_80%)] absolute top-0 right-0 h-320 w-140 -translate-y-87.5 rounded-full" />
          <div className="bg-[radial-gradient(50%_50%_at_50%_50%,--theme(--color-foreground/.04)_0,--theme(--color-foreground/.01)_80%,transparent_100%)] absolute top-0 right-0 h-320 w-60 [translate:5%_-50%] rounded-full" />
        </div>

        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>

        <div className="mx-auto w-full max-w-sm space-y-6">
          <div className="flex items-center gap-2 lg:hidden">
            <Logo className="h-8" />
          </div>

          {/* ── Step indicator ── */}
          <div className="flex items-center gap-2 mb-2">
            {[
              { key: "otp", label: "Verify" },
              { key: "profile", label: "Profile" },
              { key: "setup", label: "Setup" },
            ].map((s, i) => {
              const isActive = s.key === step;
              const isDone =
                (s.key === "otp" && (step === "profile" || step === "setup")) ||
                (s.key === "profile" && step === "setup");
              return (
                <div key={s.key} className="flex items-center gap-2">
                  {i > 0 && <div className={cn("h-px w-6", isDone || isActive ? "bg-primary" : "bg-border")} />}
                  <div className={cn(
                    "flex items-center gap-1.5 text-xs font-medium",
                    isActive && "text-primary",
                    isDone && "text-green-600",
                    !isActive && !isDone && "text-muted-foreground",
                  )}>
                    {isDone ? (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    ) : (
                      <div className={cn(
                        "h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold",
                        isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground",
                      )}>
                        {i + 1}
                      </div>
                    )}
                    {s.label}
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── STEP 1: OTP Verification ── */}
          {step === "otp" && (
            <>
              <div>
                <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                  Verify your email
                </h1>
                <p className="text-muted-foreground text-base mt-1">
                  {otpSent ? (
                    <>We&apos;ve sent a 6-digit code to{" "}
                    <span className="font-medium text-foreground">{maskEmail(userEmail)}</span></>
                  ) : (
                    "We need to verify your email before continuing."
                  )}
                </p>
              </div>

              <div className="space-y-5">
                <div className="flex justify-center">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                    {otpSent ? (
                      <KeyRound className="h-7 w-7 text-primary" />
                    ) : (
                      <Mail className="h-7 w-7 text-primary" />
                    )}
                  </div>
                </div>

                {otpSent && (
                  <div className="space-y-4">
                    <div className="flex justify-center gap-2.5">
                      {otpDigits.map((digit, i) => (
                        <input
                          key={i}
                          ref={(el) => { inputRefs.current[i] = el; }}
                          type="text"
                          inputMode="numeric"
                          maxLength={i === 0 ? 6 : 1}
                          value={digit}
                          onChange={(e) => handleOtpChange(i, e.target.value)}
                          onKeyDown={(e) => handleOtpKeyDown(i, e)}
                          className={cn(
                            "h-12 w-11 rounded-lg border-2 text-center text-xl font-bold transition-all",
                            "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
                            "bg-background text-foreground",
                            digit ? "border-primary" : "border-zinc-200 dark:border-zinc-700",
                          )}
                          disabled={otpVerifying}
                        />
                      ))}
                    </div>

                    {otpError && (
                      <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md text-center">
                        {otpError}
                      </div>
                    )}

                    <Button
                      size="lg"
                      className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
                      disabled={otpDigits.join("").length !== 6 || otpVerifying}
                      onClick={handleVerifyOTP}
                    >
                      {otpVerifying ? (
                        <><Loader2 className="h-4 w-4 animate-spin mr-2" /> Verifying...</>
                      ) : (
                        "Verify & Continue"
                      )}
                    </Button>

                    <div className="text-center">
                      {otpCountdown > 0 ? (
                        <p className="text-sm text-muted-foreground">
                          Resend code in <span className="font-medium text-foreground">{otpCountdown}s</span>
                        </p>
                      ) : (
                        <button
                          type="button"
                          onClick={handleSendOTP}
                          disabled={otpSending}
                          className="text-sm text-primary hover:underline disabled:opacity-50"
                        >
                          {otpSending ? "Sending..." : "Resend OTP"}
                        </button>
                      )}
                    </div>
                  </div>
                )}

                {!otpSent && (
                  <div className="space-y-4">
                    {otpError && (
                      <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md text-center">
                        {otpError}
                      </div>
                    )}
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-5 w-5 animate-spin text-primary mr-2" />
                      <span className="text-sm text-muted-foreground">Sending verification code&hellip;</span>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* ── STEP 2: Profile form ── */}
          {step === "profile" && (
            <>
              {/* Email verified success banner */}
              <div className="flex items-center gap-2 rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950/30 px-4 py-2.5">
                <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                <span className="text-sm text-green-700 dark:text-green-400">
                  Email verified — <span className="font-medium">{userEmail}</span>
                </span>
              </div>

              <div>
                <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                  Set up your account
                </h1>
                <p className="text-muted-foreground text-base mt-1">
                  Just a few details to get you started.
                </p>
              </div>

              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm font-medium">Account type</p>
                  <div className="grid grid-cols-2 gap-2">
                    {([
                      { kind: "personal" as AccountKind, icon: User, label: "Personal" },
                      { kind: "business" as AccountKind, icon: Building2, label: "Business" },
                    ]).map(({ kind, icon: Icon, label }) => (
                      <button
                        key={kind}
                        type="button"
                        onClick={() => setAccountKind(kind)}
                        className={cn(
                          "flex items-center gap-2.5 rounded-lg border px-4 py-3 text-sm font-medium transition-all",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                          accountKind === kind
                            ? "border-primary bg-primary/8 text-foreground"
                            : "border-zinc-200 dark:border-zinc-800 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                        )}
                      >
                        <Icon className={cn("h-4 w-4 shrink-0", accountKind === kind ? "text-primary" : "")} />
                        {label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">First name</label>
                    <Input
                      className="border-zinc-200 dark:border-zinc-800"
                      placeholder="Jane"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">Last name</label>
                    <Input
                      className="border-zinc-200 dark:border-zinc-800"
                      placeholder="Smith"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {accountKind === "business" && (
                  <div className="space-y-1.5">
                    <label className="text-sm font-medium">Business name</label>
                    <Input
                      className="border-zinc-200 dark:border-zinc-800"
                      placeholder="Acme Corp"
                      value={businessName}
                      onChange={(e) => setBusinessName(e.target.value)}
                      required
                    />
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-sm font-medium">
                    Phone{" "}
                    <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <Input
                    className="border-zinc-200 dark:border-zinc-800"
                    placeholder="+1 555 000 0000"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>

                {error && (
                  <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md">
                    {error}
                  </div>
                )}

                <Button
                  type="submit"
                  size="lg"
                  className="w-full bg-[#4e5d72] hover:bg-[#3d4c5f] text-white border-0"
                  disabled={!canSubmitProfile}
                >
                  Continue
                </Button>
              </form>
            </>
          )}

          {/* ── STEP 3: Setup progress ── */}
          {step === "setup" && (
            <>
              <div>
                <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">
                  Setting up your workspace
                </h1>
                <p className="text-muted-foreground text-base mt-1">
                  Just a moment&hellip;
                </p>
              </div>

              <div className="space-y-3 pt-2">
                {setupSteps.map((s, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center">
                      {s.status === "done" && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                      {s.status === "running" && <Loader2 className="h-5 w-5 animate-spin text-primary" />}
                      {s.status === "error" && (
                        <div className="h-4 w-4 rounded-full border-2 border-red-500 flex items-center justify-center">
                          <span className="text-red-500 text-[10px] font-bold leading-none">!</span>
                        </div>
                      )}
                      {s.status === "pending" && (
                        <div className="h-2 w-2 rounded-full bg-border mx-auto" />
                      )}
                    </div>
                    <span className={cn(
                      "text-sm",
                      s.status === "running" && "text-foreground font-medium",
                      s.status === "done" && "text-foreground",
                      s.status === "pending" && "text-muted-foreground",
                      s.status === "error" && "text-red-500",
                    )}>
                      {s.label}
                    </span>
                  </div>
                ))}

                {error && (
                  <div className="pt-3 space-y-3">
                    <div className="p-3 text-sm text-red-500 bg-red-100/10 border border-red-500/20 rounded-md">
                      {error}
                    </div>
                    <Button
                      className="w-full"
                      variant="outline"
                      onClick={() => { setError(null); handleProfileSubmit(new Event("submit") as unknown as React.FormEvent); }}
                    >
                      Retry setup
                    </Button>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
