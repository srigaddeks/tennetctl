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
import {
  useCreateRule,
  useDeleteRule,
  useRules,
} from "@/features/featureflags/hooks/use-rules-overrides";
import { ApiClientError } from "@/lib/api";
import type { Flag, FlagEnvironment } from "@/types/api";

const ENVS: FlagEnvironment[] = ["dev", "staging", "prod", "test"];

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

export function FlagRulesPanel({ flag }: { flag: Flag }) {
  const { toast } = useToast();
  const [env, setEnv] = useState<FlagEnvironment>("prod");
  const [openCreate, setOpenCreate] = useState(false);
  const { data: rules, isLoading } = useRules(flag.id, env);
  const del = useDeleteRule();

  return (
    <>
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Environment:</span>
          <Select
            value={env}
            onChange={(e) => setEnv(e.target.value as FlagEnvironment)}
            className="w-40"
            data-testid="rules-env-picker"
          >
            {ENVS.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </Select>
        </div>
        <Button
          onClick={() => setOpenCreate(true)}
          data-testid="open-create-rule"
        >
          + Add rule
        </Button>
      </div>
      {isLoading && <Skeleton className="h-12 w-full" />}
      {rules && rules.items.length === 0 && (
        <EmptyState
          title="No rules for this environment"
          description="Rules let you serve different values based on who's asking — user attrs, org membership, etc. Walked in priority order; first match wins."
          action={
            <Button onClick={() => setOpenCreate(true)}>+ Add rule</Button>
          }
        />
      )}
      {rules && rules.items.length > 0 && (
        <Table>
          <THead>
            <tr>
              <TH>Priority</TH>
              <TH>Conditions</TH>
              <TH>Value</TH>
              <TH>Rollout</TH>
              <TH>Status</TH>
              <TH />
            </tr>
          </THead>
          <TBody>
            {rules.items.map((r) => (
              <TR key={r.id}>
                <TD>
                  <Badge tone="zinc">#{r.priority}</Badge>
                </TD>
                <TD>
                  <pre className="max-w-sm overflow-x-auto whitespace-pre-wrap font-mono text-[10px] leading-snug text-zinc-700 dark:text-zinc-300">
                    {JSON.stringify(r.conditions, null, 1)}
                  </pre>
                </TD>
                <TD>
                  <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[11px] dark:bg-zinc-800">
                    {JSON.stringify(r.value)}
                  </code>
                </TD>
                <TD>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 overflow-hidden rounded bg-zinc-200 dark:bg-zinc-800">
                      <div
                        className="h-full bg-zinc-900 dark:bg-zinc-100"
                        style={{ width: `${r.rollout_percentage}%` }}
                      />
                    </div>
                    <span className="text-xs">{r.rollout_percentage}%</span>
                  </div>
                </TD>
                <TD>
                  <Badge tone={r.is_active ? "emerald" : "zinc"}>
                    {r.is_active ? "active" : "inactive"}
                  </Badge>
                </TD>
                <TD className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      if (!confirm("Delete rule?")) return;
                      try {
                        await del.mutateAsync(r.id);
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
        <CreateRuleDialog
          flag={flag}
          env={env}
          open={openCreate}
          onClose={() => setOpenCreate(false)}
        />
      )}
    </>
  );
}

function CreateRuleDialog({
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
  const create = useCreateRule();
  const [priority, setPriority] = useState("10");
  const [conditions, setConditions] = useState(
    '{"op": "eq", "attr": "country", "value": "US"}'
  );
  const [valueStr, setValueStr] = useState("true");
  const [rollout, setRollout] = useState(100);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const cond = JSON.parse(conditions);
      const val = parseValue(valueStr, flag.value_type);
      await create.mutateAsync({
        flag_id: flag.id,
        environment: env,
        priority: Number(priority),
        conditions: cond,
        value: val,
        rollout_percentage: rollout,
      });
      toast("Rule added", "success");
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
    <Modal
      open={open}
      onClose={onClose}
      title={`New rule — ${env}`}
      description="First matching rule wins. Lower priority = checked first."
      size="lg"
    >
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Priority" required hint="lower = first">
            <Input
              type="number"
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              data-testid="rule-priority"
            />
          </Field>
          <Field
            label={`Rollout: ${rollout}%`}
            hint="0 = never, 100 = always (when conditions match)"
          >
            <input
              type="range"
              min={0}
              max={100}
              value={rollout}
              onChange={(e) => setRollout(Number(e.target.value))}
              className="mt-2 w-full"
              data-testid="rule-rollout"
            />
          </Field>
        </div>
        <Field
          label="Conditions (JSON)"
          hint={
            'ops: and/or/not, eq/neq/in, startswith/endswith/contains, gt/gte/lt/lte, exists, true/false'
          }
        >
          <Textarea
            rows={4}
            value={conditions}
            onChange={(e) => setConditions(e.target.value)}
            className="font-mono text-xs"
            data-testid="rule-conditions"
          />
        </Field>
        <Field
          label={`Value (${flag.value_type})`}
          hint="value to serve when this rule matches"
        >
          {flag.value_type === "boolean" ? (
            <Select value={valueStr} onChange={(e) => setValueStr(e.target.value)}>
              <option value="true">true</option>
              <option value="false">false</option>
            </Select>
          ) : (
            <Input
              value={valueStr}
              onChange={(e) => setValueStr(e.target.value)}
              data-testid="rule-value"
              placeholder={flag.value_type === "json" ? '{"variant":"B"}' : ""}
            />
          )}
        </Field>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-rule-submit"
          >
            Add rule
          </Button>
        </div>
      </form>
    </Modal>
  );
}
