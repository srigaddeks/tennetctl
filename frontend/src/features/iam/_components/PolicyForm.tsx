"use client";

import { useState } from "react";

import { useToast } from "@/components/toast";
import { Button, Field, Input } from "@/components/ui";
import {
  useCreatePolicy,
  useUpdatePolicy,
} from "@/features/iam/hooks/use-auth-policy";
import { ApiClientError } from "@/lib/api";
import type { AuthPolicyKey, PolicyEntry, VaultValueType } from "@/types/api";

type PolicyFieldDef = {
  key: AuthPolicyKey;
  label: string;
  value_type: VaultValueType;
  default: string | number | boolean;
  hint?: string;
};

const GROUPS: Record<string, PolicyFieldDef[]> = {
  Password: [
    { key: "password.min_length", label: "Min length", value_type: "number", default: 12 },
    { key: "password.require_upper", label: "Require uppercase", value_type: "boolean", default: true },
    { key: "password.require_digit", label: "Require digit", value_type: "boolean", default: true },
    { key: "password.require_symbol", label: "Require symbol", value_type: "boolean", default: false },
    { key: "password.min_unique_chars", label: "Min unique chars", value_type: "number", default: 4 },
  ],
  Lockout: [
    { key: "lockout.threshold_failed_attempts", label: "Failed attempts before lockout", value_type: "number", default: 5 },
    { key: "lockout.window_seconds", label: "Attempt window (s)", value_type: "number", default: 900 },
    { key: "lockout.duration_seconds", label: "Lockout duration (s)", value_type: "number", default: 900 },
  ],
  Session: [
    { key: "session.max_concurrent_per_user", label: "Max concurrent sessions", value_type: "number", default: 10 },
    { key: "session.idle_timeout_seconds", label: "Idle timeout (s)", value_type: "number", default: 1800 },
    { key: "session.absolute_ttl_seconds", label: "Absolute TTL (s)", value_type: "number", default: 604800 },
    { key: "session.eviction_policy", label: "Eviction policy", value_type: "string", default: "oldest", hint: "oldest | newest | none" },
  ],
  "Magic Link": [
    { key: "magic_link.ttl_seconds", label: "Link TTL (s)", value_type: "number", default: 600 },
    { key: "magic_link.rate_limit_per_email", label: "Rate limit per email", value_type: "number", default: 3 },
    { key: "magic_link.rate_window_seconds", label: "Rate window (s)", value_type: "number", default: 900 },
  ],
  OTP: [
    { key: "otp.email_ttl_seconds", label: "OTP TTL (s)", value_type: "number", default: 300 },
    { key: "otp.email_max_attempts", label: "Max attempts", value_type: "number", default: 3 },
    { key: "otp.rate_limit_per_email", label: "Rate limit per email", value_type: "number", default: 3 },
    { key: "otp.rate_window_seconds", label: "Rate window (s)", value_type: "number", default: 900 },
  ],
  "Password Reset": [
    { key: "password_reset.ttl_seconds", label: "Reset token TTL (s)", value_type: "number", default: 900 },
  ],
};

function parseVal(raw: string, type: VaultValueType): unknown {
  if (type === "number") return Number(raw);
  if (type === "boolean") return raw === "true";
  return raw;
}

function toRaw(value: unknown): string {
  if (value === null || value === undefined) return "";
  return String(value);
}

function PolicyField({
  def,
  entry,
  orgId,
}: {
  def: PolicyFieldDef;
  entry: PolicyEntry | undefined;
  orgId?: string | null;
}) {
  const { toast } = useToast();
  const update = useUpdatePolicy();
  const create = useCreatePolicy();
  const currentVal = toRaw(entry?.value ?? def.default);
  const [raw, setRaw] = useState(currentVal);
  const dirty = raw !== currentVal;

  async function save() {
    try {
      if (entry) {
        await update.mutateAsync({ id: entry.id, body: { value: parseVal(raw, def.value_type) } });
      } else {
        await create.mutateAsync({
          key: `iam.policy.${def.key}`,
          value_type: def.value_type,
          value: parseVal(raw, def.value_type),
          scope: orgId ? "org" : "global",
          org_id: orgId ?? null,
          workspace_id: null,
        });
      }
      toast(`${def.label} saved`, "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Save failed";
      toast(msg, "error");
    }
  }

  const inputEl =
    def.value_type === "boolean" ? (
      <select
        className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        data-testid={`policy-field-${def.key}`}
      >
        <option value="true">true</option>
        <option value="false">false</option>
      </select>
    ) : (
      <Input
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        data-testid={`policy-field-${def.key}`}
      />
    );

  return (
    <div className="flex items-end gap-3">
      <div className="flex-1">
        <Field label={def.label} hint={def.hint}>
          {inputEl}
        </Field>
      </div>
      {dirty && (
        <Button
          size="sm"
          onClick={save}
          disabled={update.isPending || create.isPending}
          data-testid={`policy-save-${def.key}`}
        >
          Save
        </Button>
      )}
    </div>
  );
}

export function PolicyForm({
  entries,
  orgId,
}: {
  entries: PolicyEntry[];
  orgId?: string | null;
}) {
  const byKey = Object.fromEntries(
    entries.map((e) => [e.key.replace("iam.policy.", ""), e]),
  );

  return (
    <div className="flex flex-col gap-8" data-testid="policy-form">
      {Object.entries(GROUPS).map(([group, fields]) => (
        <section
          key={group}
          data-testid={`policy-group-${group.toLowerCase().replace(/\s+/g, "-")}`}
        >
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            {group}
          </h3>
          <div className="flex flex-col gap-4 rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
            {fields.map((def) => (
              <PolicyField
                key={def.key}
                def={def}
                entry={byKey[def.key] as PolicyEntry | undefined}
                orgId={orgId}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
