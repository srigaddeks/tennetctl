"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  Field,
  Input,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
// Select is kept — still used by the Create Override modal for env + entity type pickers.
import {
  useCreateOverride,
  useDeleteOverride,
  useOverrides,
} from "@/features/featureflags/hooks/use-rules-overrides";
import { ApiClientError } from "@/lib/api";
import type {
  Flag,
  FlagEnvironment,
  FlagOverrideEntityType,
} from "@/types/api";

const ENVS: FlagEnvironment[] = ["dev", "staging", "prod", "test"];
const ENTITY_TYPES: FlagOverrideEntityType[] = [
  "user",
  "org",
  "application",
  "workspace",
  "role",
  "group",
];

function parseValue(raw: string, vt: string): unknown {
  if (vt === "boolean") return raw.toLowerCase() === "true";
  if (vt === "number") {
    const n = Number(raw);
    if (Number.isNaN(n)) throw new Error("invalid number");
    return n;
  }
  if (vt === "json") return JSON.parse(raw);
  return raw;
}

export function FlagOverridesPanel({ flag }: { flag: Flag }) {
  const { toast } = useToast();
  const [env, setEnv] = useState<FlagEnvironment>("prod");
  const [openCreate, setOpenCreate] = useState(false);
  const { data: ovs, isLoading } = useOverrides(flag.id, env);
  const del = useDeleteOverride();

  return (
    <>
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-zinc-500">Environment:</span>
          {ENVS.map((e) => {
            const active = env === e;
            const tone = e === "dev"
              ? "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
              : e === "staging"
              ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
              : e === "prod"
              ? "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "border-purple-300 bg-purple-50 text-purple-700 dark:border-purple-800 dark:bg-purple-900/30 dark:text-purple-300";
            return (
              <button
                key={e}
                type="button"
                onClick={() => setEnv(e)}
                className={
                  "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium transition " +
                  (active
                    ? tone
                    : "border-zinc-200 bg-white text-zinc-500 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400 dark:hover:bg-zinc-900")
                }
                data-testid={`override-env-${e}`}
              >
                {e}
              </button>
            );
          })}
        </div>
        <Button onClick={() => setOpenCreate(true)}>+ Add override</Button>
      </div>
      {isLoading && <Skeleton className="h-12 w-full" />}
      {ovs && ovs.items.length === 0 && (
        <EmptyState
          title="No overrides for this environment"
          description="Overrides force a specific value for a specific entity (user / org / application / etc.). Higher precedence than rules."
          action={
            <Button onClick={() => setOpenCreate(true)}>+ Add override</Button>
          }
        />
      )}
      {ovs && ovs.items.length > 0 && (
        <Table>
          <THead>
            <tr>
              <TH>Entity</TH>
              <TH>Value</TH>
              <TH>Reason</TH>
              <TH>Status</TH>
              <TH />
            </tr>
          </THead>
          <TBody>
            {ovs.items.map((o) => (
              <TR key={o.id}>
                <TD>
                  <Badge tone="purple">{o.entity_type}</Badge>
                  <span className="ml-1.5 font-mono text-[10px] text-zinc-500">
                    {o.entity_id.slice(0, 12)}…
                  </span>
                </TD>
                <TD>
                  <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] dark:bg-zinc-800">
                    {JSON.stringify(o.value)}
                  </code>
                </TD>
                <TD>
                  <span className="text-xs text-zinc-600 dark:text-zinc-400">
                    {o.reason ?? "—"}
                  </span>
                </TD>
                <TD>
                  <Badge tone={o.is_active ? "emerald" : "zinc"}>
                    {o.is_active ? "active" : "inactive"}
                  </Badge>
                </TD>
                <TD className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      if (!confirm("Delete override?")) return;
                      try {
                        await del.mutateAsync(o.id);
                        toast("Deleted", "success");
                      } catch (err) {
                        const m =
                          err instanceof ApiClientError
                            ? err.message
                            : String(err);
                        toast(m, "error");
                      }
                    }}
                  >
                    Delete
                  </Button>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      {openCreate && (
        <CreateOverrideDialog
          flag={flag}
          env={env}
          open={openCreate}
          onClose={() => setOpenCreate(false)}
        />
      )}
    </>
  );
}

function CreateOverrideDialog({
  flag,
  env,
  open,
  onClose,
}: {
  flag: Flag;
  env: FlagEnvironment;
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateOverride();
  const [entityType, setEntityType] = useState<FlagOverrideEntityType>("user");
  const [entityId, setEntityId] = useState("");
  const [valueStr, setValueStr] = useState("true");
  const [reason, setReason] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const val = parseValue(valueStr, flag.value_type);
      await create.mutateAsync({
        flag_id: flag.id,
        environment: env,
        entity_type: entityType,
        entity_id: entityId,
        value: val,
        reason: reason || undefined,
      });
      toast("Override added", "success");
      onClose();
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : err instanceof Error
            ? err.message
            : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={`New override — ${env}`}>
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Entity type" required>
            <Select
              value={entityType}
              onChange={(e) =>
                setEntityType(e.target.value as FlagOverrideEntityType)
              }
              data-testid="override-entity-type"
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </Field>
          <Field
            label={`Value (${flag.value_type})`}
            required
          >
            {flag.value_type === "boolean" ? (
              <Select
                value={valueStr}
                onChange={(e) => setValueStr(e.target.value)}
              >
                <option value="true">true</option>
                <option value="false">false</option>
              </Select>
            ) : (
              <Input
                value={valueStr}
                onChange={(e) => setValueStr(e.target.value)}
                data-testid="override-value"
              />
            )}
          </Field>
        </div>
        <Field label="Entity ID" required hint="UUID of the entity to target">
          <Input
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            placeholder="019d9540-..."
            className="font-mono text-xs"
            data-testid="override-entity-id"
          />
        </Field>
        <Field label="Reason" hint="optional, for audit / UX">
          <Textarea
            rows={2}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </Field>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-override-submit"
          >
            Add override
          </Button>
        </div>
      </form>
    </Modal>
  );
}
