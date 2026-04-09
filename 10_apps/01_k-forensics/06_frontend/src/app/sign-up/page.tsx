"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { CheckCircle, Loader2, User, Building2 } from "lucide-react";
import { signup } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";

type Step = "account-type" | "profile" | "provisioning";
type AccountType = "personal" | "business";

export default function SignUpPage() {
  const router = useRouter();
  const { setSessionFromSignup } = useAuth();

  const [step, setStep] = React.useState<Step>("account-type");
  const [accountType, setAccountType] = React.useState<AccountType>("personal");
  const [form, setForm] = React.useState({
    displayName: "",
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    orgName: "",
  });
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [provisionStage, setProvisionStage] = React.useState(0);
  const [provisionError, setProvisionError] = React.useState("");

  function setField(key: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => ({ ...e, [key]: "" }));
  }

  function validateProfile(): boolean {
    const next: Record<string, string> = {};
    if (!form.username.trim()) next.username = "Username is required.";
    else if (!/^[a-zA-Z0-9_.-]{3,64}$/.test(form.username))
      next.username = "3\u201364 chars: letters, digits, _ . -";
    if (!form.password) next.password = "Password is required.";
    else if (form.password.length < 8) next.password = "At least 8 characters.";
    if (form.password !== form.confirmPassword) next.confirmPassword = "Passwords do not match.";
    if (form.email && !form.email.includes("@")) next.email = "Invalid email address.";
    if (accountType === "business" && !form.orgName.trim())
      next.orgName = "Organisation name is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  function handleAccountTypeNext(type: AccountType) {
    setAccountType(type);
    setStep("profile");
  }

  function handleProfileNext(e: React.FormEvent) {
    e.preventDefault();
    if (!validateProfile()) return;
    setStep("provisioning");
    runProvisioning();
  }

  async function runProvisioning() {
    setProvisionStage(0);
    setProvisionError("");

    await new Promise((r) => setTimeout(r, 400));
    setProvisionStage(1);

    const personalName = form.displayName?.trim() || form.username;
    const effectiveOrgName =
      accountType === "business"
        ? form.orgName
        : `${personalName}'s org`;

    const res = await signup({
      username: form.username,
      password: form.password,
      email: form.email || undefined,
      display_name: form.displayName || undefined,
      account_type: accountType,
      org_name: effectiveOrgName,
      default_workspace_name: "kbio",
    });

    if (!res.ok) {
      setProvisionError(res.error.message);
      setProvisionStage(-1);
      return;
    }

    setProvisionStage(2);
    await new Promise((r) => setTimeout(r, 500));

    setProvisionStage(3);
    await new Promise((r) => setTimeout(r, 600));

    setSessionFromSignup(res.data);

    const org = res.data.org;
    const ws = res.data.workspace;
    if (org && ws) {
      router.replace(`/?org_id=${org.id}&workspace_id=${ws.id}`);
    } else {
      router.replace("/");
    }
  }

  const stepIndex = ["account-type", "profile", "provisioning"].indexOf(step);

  return (
    <div className="min-h-screen flex flex-col items-center pt-15 px-6 pb-10">
      <div className="font-bold text-xl tracking-tight text-foreground mb-8">k-forensics</div>

      {/* Step indicator */}
      <div className="flex items-center gap-0 mb-8">
        {[0, 1, 2].map((i) => (
          <React.Fragment key={i}>
            <div className={cn(
              "w-2.5 h-2.5 rounded-full transition-colors",
              i <= stepIndex ? "bg-foreground" : "bg-surface-3"
            )} />
            {i < 2 && (
              <div className={cn(
                "w-10 h-0.5 transition-colors",
                i < stepIndex ? "bg-foreground" : "bg-surface-3"
              )} />
            )}
          </React.Fragment>
        ))}
      </div>

      {step === "account-type" && (
        <Card className="w-full max-w-[420px]">
          <CardContent className="pt-6">
            <h1 className="text-xl font-bold tracking-tight mb-1">Create your account</h1>
            <p className="text-xs text-foreground-muted mb-6">How will you use k-forensics?</p>
            <div className="grid grid-cols-2 gap-3 mb-5">
              <button
                onClick={() => handleAccountTypeNext("personal")}
                className={cn(
                  "flex flex-col items-center gap-2 p-6 rounded-md border border-border bg-background cursor-pointer transition-colors text-foreground",
                  "hover:border-border-strong",
                  accountType === "personal" && "border-foreground bg-surface-2"
                )}
              >
                <User size={28} className="text-foreground-muted" />
                <span className="text-sm font-semibold">Personal</span>
                <span className="text-xs text-foreground-muted">For individual investigators</span>
              </button>
              <button
                onClick={() => handleAccountTypeNext("business")}
                className={cn(
                  "flex flex-col items-center gap-2 p-6 rounded-md border border-border bg-background cursor-pointer transition-colors text-foreground",
                  "hover:border-border-strong",
                  accountType === "business" && "border-foreground bg-surface-2"
                )}
              >
                <Building2 size={28} className="text-foreground-muted" />
                <span className="text-sm font-semibold">Business</span>
                <span className="text-xs text-foreground-muted">For teams and organisations</span>
              </button>
            </div>
            <p className="text-center text-xs text-foreground-muted">
              Already have an account?{" "}
              <a href="/sign-in" className="text-foreground underline underline-offset-4 hover:text-foreground-muted">Sign in</a>
            </p>
          </CardContent>
        </Card>
      )}

      {step === "profile" && (
        <Card className="w-full max-w-[420px]">
          <CardContent className="pt-6">
            <h1 className="text-xl font-bold tracking-tight mb-1">
              {accountType === "business" ? "Set up your team" : "Create your profile"}
            </h1>
            <form onSubmit={handleProfileNext} className="flex flex-col gap-4 mt-4">
              <FormField id="displayName" label="Display name" optional value={form.displayName} onChange={(v) => setField("displayName", v)} placeholder="Jane Smith" error={errors.displayName} />
              <FormField id="username" label="Username" value={form.username} onChange={(v) => setField("username", v)} placeholder="jane.smith" error={errors.username} autoComplete="username" />
              <FormField id="email" label="Email" optional type="email" value={form.email} onChange={(v) => setField("email", v)} placeholder="jane@example.com" error={errors.email} autoComplete="email" />
              <FormField id="password" label="Password" type="password" value={form.password} onChange={(v) => setField("password", v)} placeholder="Min. 8 characters" error={errors.password} autoComplete="new-password" />
              <FormField id="confirmPassword" label="Confirm password" type="password" value={form.confirmPassword} onChange={(v) => setField("confirmPassword", v)} placeholder="Repeat password" error={errors.confirmPassword} autoComplete="new-password" />
              {accountType === "business" && (
                <FormField id="orgName" label="Organisation name" value={form.orgName} onChange={(v) => setField("orgName", v)} placeholder="Acme Forensics Ltd." error={errors.orgName} />
              )}
              <div className="flex gap-2.5 mt-2">
                <Button type="button" variant="outline" onClick={() => setStep("account-type")}>
                  Back
                </Button>
                <Button type="submit" className="flex-1">
                  Continue
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {step === "provisioning" && (
        <Card className="w-full max-w-[420px] text-center">
          <CardContent className="pt-6">
            <h1 className="text-xl font-bold tracking-tight mb-1">Setting up your workspace</h1>
            <p className="text-xs text-foreground-muted mb-6">Just a moment...</p>

            {provisionStage === -1 ? (
              <div>
                <p className="text-xs text-[color:var(--danger)] mb-5">{provisionError}</p>
                <Button variant="outline" onClick={() => setStep("profile")}>
                  &larr; Back to edit
                </Button>
              </div>
            ) : (
              <div className="flex flex-col gap-3.5 mt-5 text-left">
                <ProvisionRow label="Creating your account" done={provisionStage > 0} active={provisionStage === 0} />
                <ProvisionRow label="Setting up your organisation" done={provisionStage > 1} active={provisionStage === 1} />
                <ProvisionRow label="Configuring your workspace" done={provisionStage > 2} active={provisionStage === 2} />
                <ProvisionRow label="Ready!" done={provisionStage >= 3} active={false} />
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function FormField({
  id, label, optional, value, onChange, placeholder, error, type = "text", autoComplete,
}: {
  id: string; label: string; optional?: boolean; value: string; onChange: (v: string) => void;
  placeholder?: string; error?: string; type?: string; autoComplete?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>
        {label}
        {optional && <span className="font-normal ml-1 normal-case">(optional)</span>}
      </Label>
      <Input
        id={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={error ? "border-[color:var(--danger)]" : undefined}
      />
      {error && <p className="text-[11px] text-[color:var(--danger)]">{error}</p>}
    </div>
  );
}

function ProvisionRow({ label, done, active }: { label: string; done: boolean; active: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="w-5 h-5 shrink-0 flex items-center justify-center">
        {done ? (
          <CheckCircle size={20} className="text-[color:var(--success)]" />
        ) : active ? (
          <Loader2 size={20} className="text-foreground-muted" style={{ animation: "spin 1s linear infinite" }} />
        ) : (
          <div className="w-2 h-2 rounded-full bg-surface-3" />
        )}
      </div>
      <span className={cn(
        "text-sm",
        done ? "text-foreground" : active ? "text-foreground" : "text-foreground-muted"
      )}>
        {label}
      </span>
    </div>
  );
}
