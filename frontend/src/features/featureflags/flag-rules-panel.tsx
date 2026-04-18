"use client";

/**
 * FlagRulesPanel
 *
 * Form-based targeting-rule builder. Replaces the JSON-textarea editor with a
 * guided condition tree UI that produces the same conditions_jsonb output.
 *
 * Layout:
 *   - Environment dropdown at the top
 *   - Ordered list of rules, each collapsed to a summary row
 *   - Expand any row inline to edit (no modal)
 *   - "+ Add rule" expands a blank editor at the bottom
 */

import { useState, useCallback, useReducer } from "react";
import { ChevronDown, ChevronRight, Trash2, Check, X } from "lucide-react";

import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  Field,
  Input,
  Select,
  Skeleton,
} from "@/components/ui";
import {
  useRules,
  useCreateRule,
  useUpdateRule,
  useDeleteRule,
} from "@/features/featureflags/hooks/use-rules-overrides";
import {
  ConditionTreeEditor,
  fromBackend,
  toBackend,
  defaultRoot,
  describeCondition,
  type CondNode,
} from "@/features/featureflags/condition-tree-editor";
import { ApiClientError } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Flag, FlagEnvironment, FlagRule, FlagValueType } from "@/types/api";

// ─── Constants ───────────────────────────────────────────────────────────────

const ENVS: FlagEnvironment[] = ["dev", "staging", "prod", "test"];

const ENV_COLORS: Record<FlagEnvironment, string> = {
  dev:     "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-800 dark:text-blue-300",
  staging: "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/30 dark:border-amber-800 dark:text-amber-300",
  prod:    "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-300",
  test:    "bg-purple-50 border-purple-200 text-purple-700 dark:bg-purple-900/30 dark:border-purple-800 dark:text-purple-300",
};

// ─── parseValue (for string→typed value conversion) ──────────────────────────

function parseValue(raw: string, vt: FlagValueType): unknown {
  if (vt === "boolean") return raw.toLowerCase() === "true";
  if (vt === "number") {
    const n = Number(raw);
    if (Number.isNaN(n)) throw new Error("Value must be a number");
    return n;
  }
  if (vt === "json") {
    try { return JSON.parse(raw); }
    catch { throw new Error("Value must be valid JSON"); }
  }
  return raw;
}

function serializeValue(val: unknown, vt: FlagValueType): string {
  if (vt === "json") return JSON.stringify(val, null, 2);
  if (val === null || val === undefined) return "";
  return String(val);
}

// ─── Editor form state ───────────────────────────────────────────────────────

type EditorState = {
  priority: string;
  condTree: CondNode;
  valueStr: string;
  rollout: number;
  isActive: boolean;
};

type EditorAction =
  | { type: "SET_PRIORITY"; value: string }
  | { type: "SET_COND_TREE"; tree: CondNode }
  | { type: "SET_VALUE_STR"; value: string }
  | { type: "SET_ROLLOUT"; value: number }
  | { type: "SET_ACTIVE"; value: boolean }
  | { type: "RESET"; state: EditorState };

function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case "SET_PRIORITY":   return { ...state, priority: action.value };
    case "SET_COND_TREE":  return { ...state, condTree: action.tree };
    case "SET_VALUE_STR":  return { ...state, valueStr: action.value };
    case "SET_ROLLOUT":    return { ...state, rollout: action.value };
    case "SET_ACTIVE":     return { ...state, isActive: action.value };
    case "RESET":          return action.state;
  }
}

function initialEditorState(rule: FlagRule | null, valueType: FlagValueType): EditorState {
  if (!rule) {
    return {
      priority: "10",
      condTree: defaultRoot(),
      valueStr: valueType === "boolean" ? "true" : "",
      rollout: 100,
      isActive: true,
    };
  }
  return {
    priority: String(rule.priority),
    condTree: fromBackend(rule.conditions as Record<string, unknown>),
    valueStr: serializeValue(rule.value, valueType),
    rollout: rule.rollout_percentage,
    isActive: rule.is_active,
  };
}

// ─── Rollout mini-bar ────────────────────────────────────────────────────────

function RolloutBar({ pct }: { pct: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
        <div
          className="h-full bg-zinc-900 transition-all dark:bg-zinc-100"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="tabular-nums text-xs text-zinc-600 dark:text-zinc-400">{pct}%</span>
    </div>
  );
}

// ─── Inline rollout picker ────────────────────────────────────────────────────

function InlineRolloutPicker({
  ruleId,
  current,
}: {
  ruleId: string;
  current: number;
}) {
  const { toast } = useToast();
  const update = useUpdateRule();
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(current);

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => { setDraft(current); setEditing(true); }}
        title="Click to change rollout %"
        className="group flex items-center gap-2"
        data-testid={`rule-rollout-${ruleId}`}
      >
        <RolloutBar pct={current} />
        <span className="hidden text-[11px] text-zinc-400 group-hover:inline dark:text-zinc-500">edit</span>
      </button>
    );
  }

  async function save() {
    try {
      await update.mutateAsync({ id: ruleId, body: { rollout_percentage: draft } });
      toast("Rollout updated", "success");
    } catch (err) {
      toast(err instanceof ApiClientError ? err.message : String(err), "error");
    }
    setEditing(false);
  }

  return (
    <div className="flex items-center gap-1.5">
      <input
        type="range"
        min={0}
        max={100}
        value={draft}
        onChange={(e) => setDraft(Number(e.target.value))}
        className="w-20"
        data-testid={`rule-rollout-${ruleId}`}
      />
      <span className="w-8 text-center text-[11px] tabular-nums text-zinc-600 dark:text-zinc-400">
        {draft}%
      </span>
      <button
        type="button"
        onClick={save}
        disabled={update.isPending}
        className="rounded-md p-0.5 text-emerald-600 transition hover:bg-emerald-50 dark:hover:bg-emerald-950/30"
      >
        <Check className="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        onClick={() => setEditing(false)}
        className="rounded-md p-0.5 text-zinc-400 transition hover:bg-zinc-100 dark:hover:bg-zinc-800"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

// ─── Rule editor (inline expand) ─────────────────────────────────────────────

function RuleEditor({
  flag,
  env,
  rule,
  onDone,
}: {
  flag: Flag;
  env: FlagEnvironment;
  rule: FlagRule | null; // null = new rule
  onDone: () => void;
}) {
  const { toast } = useToast();
  const createRule = useCreateRule();
  const updateRule = useUpdateRule();
  const isNew = rule === null;

  const initState = initialEditorState(rule, flag.value_type);
  const [state, dispatch] = useReducer(editorReducer, initState);

  const setCondTree = useCallback((tree: CondNode) => {
    dispatch({ type: "SET_COND_TREE", tree });
  }, []);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    try {
      const conditions = toBackend(state.condTree) as Record<string, unknown>;
      const value = parseValue(state.valueStr, flag.value_type);
      const priority = Number(state.priority);
      if (Number.isNaN(priority)) throw new Error("Priority must be a number");

      if (isNew) {
        await createRule.mutateAsync({
          flag_id: flag.id,
          environment: env,
          priority,
          conditions,
          value,
          rollout_percentage: state.rollout,
        });
        toast("Rule created", "success");
      } else {
        await updateRule.mutateAsync({
          id: rule.id,
          body: {
            priority,
            conditions,
            value,
            rollout_percentage: state.rollout,
            is_active: state.isActive,
          },
        });
        toast("Rule saved", "success");
      }
      onDone();
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

  function onCancel() {
    dispatch({ type: "RESET", state: initState });
    onDone();
  }

  const isPending = createRule.isPending || updateRule.isPending;

  return (
    <form
      onSubmit={onSave}
      className="border-t border-zinc-100 bg-zinc-50/50 px-4 py-4 dark:border-zinc-800 dark:bg-zinc-900/30"
    >
      {/* Priority + rollout */}
      <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Field label="Priority" hint="lower = checked first">
          <Input
            type="number"
            value={state.priority}
            onChange={(e) => dispatch({ type: "SET_PRIORITY", value: e.target.value })}
            data-testid={`rule-priority-${rule?.id ?? "new"}`}
            className="text-sm"
          />
        </Field>

        <div className="col-span-2 flex flex-col gap-1.5">
          <label className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
            Rollout: <span className="font-bold">{state.rollout}%</span>
          </label>
          <p className="text-[11px] text-zinc-400 dark:text-zinc-500">
            Of users matching the conditions, {state.rollout}% see this rule&apos;s value. Split is deterministic per user+flag.
          </p>
          <input
            type="range"
            min={0}
            max={100}
            value={state.rollout}
            onChange={(e) => dispatch({ type: "SET_ROLLOUT", value: Number(e.target.value) })}
            className="w-full"
            data-testid={`rule-rollout-${rule?.id ?? "new"}`}
          />
        </div>

        {!isNew && (
          <Field label="Status">
            <Select
              value={state.isActive ? "active" : "inactive"}
              onChange={(e) =>
                dispatch({ type: "SET_ACTIVE", value: e.target.value === "active" })
              }
            >
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </Select>
          </Field>
        )}
      </div>

      {/* Condition tree */}
      <div className="mb-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Conditions — IF
        </p>
        <ConditionTreeEditor
          value={state.condTree}
          onChange={setCondTree}
        />
      </div>

      {/* Value */}
      <div className="mb-4">
        <Field
          label={`Return value (${flag.value_type})`}
          hint="served when this rule matches"
        >
          {flag.value_type === "boolean" ? (
            <Select
              value={state.valueStr}
              onChange={(e) => dispatch({ type: "SET_VALUE_STR", value: e.target.value })}
              data-testid={`rule-value-${rule?.id ?? "new"}`}
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </Select>
          ) : flag.value_type === "json" ? (
            <textarea
              rows={3}
              value={state.valueStr}
              onChange={(e) => dispatch({ type: "SET_VALUE_STR", value: e.target.value })}
              placeholder='{"variant":"B"}'
              data-testid={`rule-value-${rule?.id ?? "new"}`}
              className={cn(
                "w-full rounded-lg border border-zinc-200 bg-white px-3 py-2 font-mono text-xs text-zinc-900 shadow-sm transition",
                "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
                "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50",
                "dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
              )}
            />
          ) : (
            <Input
              value={state.valueStr}
              onChange={(e) => dispatch({ type: "SET_VALUE_STR", value: e.target.value })}
              placeholder={flag.value_type === "number" ? "42" : "my-value"}
              data-testid={`rule-value-${rule?.id ?? "new"}`}
            />
          )}
        </Field>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-2 border-t border-zinc-100 pt-3 dark:border-zinc-800">
        <Button variant="ghost" size="sm" type="button" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="submit"
          size="sm"
          loading={isPending}
          data-testid={`save-rule-${rule?.id ?? "new"}`}
        >
          {isNew ? "Add rule" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}

// ─── Collapsed rule row ───────────────────────────────────────────────────────

function RuleRow({
  rule,
  flag,
  isEditing,
  onToggleEdit,
  onDelete,
}: {
  rule: FlagRule;
  flag: Flag;
  isEditing: boolean;
  onToggleEdit: () => void;
  onDelete: () => void;
}) {
  const summary = describeCondition(rule.conditions as Record<string, unknown>);
  const activeColor = rule.is_active
    ? "bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-300"
    : "bg-zinc-100 border-zinc-200 text-zinc-500 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-400";

  return (
    <div
      className={cn(
        "border-b border-zinc-100 dark:border-zinc-800",
        !rule.is_active && "opacity-60"
      )}
      data-testid={`rule-row-${rule.id}`}
    >
      {/* Summary row */}
      <div className="grid grid-cols-[auto_1fr_auto] items-center gap-x-3 px-4 py-3">
        {/* Priority badge + expand toggle */}
        <button
          type="button"
          onClick={onToggleEdit}
          className="flex items-center gap-1.5 text-left"
          aria-expanded={isEditing}
          title={isEditing ? "Collapse" : "Expand to edit"}
        >
          <Badge tone="zinc" data-testid={`rule-priority-${rule.id}`}>
            #{rule.priority}
          </Badge>
          {isEditing
            ? <ChevronDown className="h-3.5 w-3.5 text-zinc-400" />
            : <ChevronRight className="h-3.5 w-3.5 text-zinc-400" />}
        </button>

        {/* Condition summary */}
        <div className="min-w-0">
          <p className="truncate text-xs text-zinc-700 dark:text-zinc-300">
            <span className="mr-1 font-semibold text-zinc-500 dark:text-zinc-400">IF</span>
            {summary}
          </p>
          <div className="mt-0.5 flex items-center gap-3 text-[11px] text-zinc-400 dark:text-zinc-500">
            <span>
              RETURN{" "}
              <code className="rounded bg-zinc-100 px-1 py-0.5 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                {JSON.stringify(rule.value)}
              </code>
            </span>
            <span className="h-3 w-px bg-zinc-200 dark:bg-zinc-700" />
            <span className="inline-flex items-center gap-1">
              ROLL OUT TO:
              <InlineRolloutPicker ruleId={rule.id} current={rule.rollout_percentage} />
            </span>
          </div>
        </div>

        {/* Status + actions */}
        <div className="flex shrink-0 items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
              activeColor
            )}
          >
            {rule.is_active ? "active" : "inactive"}
          </span>
          <button
            type="button"
            onClick={onToggleEdit}
            className="rounded-md px-2 py-1 text-xs font-medium text-zinc-500 transition hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-50"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={onDelete}
            title="Delete rule"
            data-testid={`delete-rule-${rule.id}`}
            className="rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Inline editor (expanded) */}
      {isEditing && (
        <RuleEditor
          flag={flag}
          env={rule.environment}
          rule={rule}
          onDone={onToggleEdit}
        />
      )}
    </div>
  );
}

// ─── Main panel ───────────────────────────────────────────────────────────────

export function FlagRulesPanel({ flag }: { flag: Flag }) {
  const { toast } = useToast();
  const [env, setEnv] = useState<FlagEnvironment>("prod");
  const [expandedRuleId, setExpandedRuleId] = useState<string | null>(null);
  const [addingNew, setAddingNew] = useState(false);

  const { data: rules, isLoading } = useRules(flag.id, env);
  const del = useDeleteRule();

  function toggleEdit(id: string) {
    setExpandedRuleId((cur) => (cur === id ? null : id));
    setAddingNew(false);
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this rule?")) return;
    try {
      await del.mutateAsync(id);
      toast("Rule deleted", "success");
      if (expandedRuleId === id) setExpandedRuleId(null);
    } catch (err) {
      toast(err instanceof ApiClientError ? err.message : String(err), "error");
    }
  }

  const sorted = [...(rules?.items ?? [])].sort((a, b) => a.priority - b.priority);

  return (
    <div className="space-y-4">
      {/* Header bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Environment:</span>
          <div className="flex items-center gap-1">
            {ENVS.map((e) => (
              <button
                key={e}
                type="button"
                onClick={() => {
                  setEnv(e);
                  setExpandedRuleId(null);
                  setAddingNew(false);
                }}
                data-testid="rules-env-picker"
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition",
                  env === e
                    ? ENV_COLORS[e]
                    : "border-zinc-200 bg-white text-zinc-500 hover:border-zinc-400 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400"
                )}
              >
                {e}
              </button>
            ))}
          </div>
        </div>

        <Button
          size="sm"
          onClick={() => {
            setAddingNew(true);
            setExpandedRuleId(null);
          }}
          data-testid="add-rule"
        >
          + Add rule
        </Button>
      </div>

      {/* Loading */}
      {isLoading && <Skeleton className="h-16 w-full" />}

      {/* Rule list */}
      {!isLoading && sorted.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          {sorted.map((rule) => (
            <RuleRow
              key={rule.id}
              rule={rule}
              flag={flag}
              isEditing={expandedRuleId === rule.id}
              onToggleEdit={() => toggleEdit(rule.id)}
              onDelete={() => handleDelete(rule.id)}
            />
          ))}

          {/* Inline new-rule editor at bottom of list */}
          {addingNew && (
            <div className="border-t border-dashed border-zinc-200 dark:border-zinc-700">
              <div className="px-4 pt-3">
                <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
                  New rule — {env}
                </p>
              </div>
              <RuleEditor
                flag={flag}
                env={env}
                rule={null}
                onDone={() => setAddingNew(false)}
              />
            </div>
          )}
        </div>
      )}

      {/* Empty state — no rules */}
      {!isLoading && sorted.length === 0 && !addingNew && (
        <EmptyState
          title="No rules yet"
          description="The flag returns its environment default (or global default) for every request. Add a rule to target specific users or segments."
          action={
            <Button onClick={() => setAddingNew(true)} data-testid="add-rule">
              + Add rule
            </Button>
          }
        />
      )}

      {/* New-rule editor when list is empty */}
      {!isLoading && sorted.length === 0 && addingNew && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          <div className="border-b border-dashed border-zinc-200 px-4 pt-3 dark:border-zinc-700">
            <p className="text-xs font-semibold text-zinc-500 dark:text-zinc-400">
              New rule — {env}
            </p>
          </div>
          <RuleEditor
            flag={flag}
            env={env}
            rule={null}
            onDone={() => setAddingNew(false)}
          />
        </div>
      )}
    </div>
  );
}
