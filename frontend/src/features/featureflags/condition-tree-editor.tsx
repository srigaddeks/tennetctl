"use client";

/**
 * ConditionTreeEditor
 *
 * Renders a recursive, form-based editor for the conditions_jsonb tree.
 * The tree shape:
 *   group:     { op: "and"|"or", children: CondNode[] }
 *   not-group: { op: "not", child: CondNode }
 *   leaf:      { op: "eq"|"neq"|"in"|"startswith"|"endswith"|"contains"|"gt"|"gte"|"lt"|"lte"|"exists", attr, value|values }
 *   literal:   { op: "true" } | { op: "false" }
 *
 * The editor works against a stable internal tree where every node has a
 * generated `_id` (never sent to the backend). On every change it calls
 * `onChange(toBackend(draft))` to give the parent the clean backend shape.
 */

import { useCallback, useId } from "react";
import { Plus, Trash2 } from "lucide-react";

import { cn } from "@/lib/cn";

// ─── Types ───────────────────────────────────────────────────────────────────

export type LeafOp =
  | "eq" | "neq" | "in"
  | "startswith" | "endswith" | "contains"
  | "gt" | "gte" | "lt" | "lte"
  | "exists";

export type GroupOp = "and" | "or";

export type CondNode =
  | { _id: string; op: GroupOp; children: CondNode[] }
  | { _id: string; op: "not"; child: CondNode }
  | { _id: string; op: LeafOp; attr: string; value: string }
  | { _id: string; op: "true" }
  | { _id: string; op: "false" };

// ─── Unique id ───────────────────────────────────────────────────────────────

let _seq = 0;
function nextId() {
  return `n${++_seq}`;
}

// ─── Serialise / deserialise ─────────────────────────────────────────────────

export function fromBackend(raw: Record<string, unknown>): CondNode {
  const op = raw.op as string;

  if (op === "and" || op === "or") {
    const children = (raw.children as Record<string, unknown>[] | undefined) ?? [];
    return {
      _id: nextId(),
      op: op as GroupOp,
      children: children.map(fromBackend),
    };
  }
  if (op === "not") {
    return {
      _id: nextId(),
      op: "not",
      child: fromBackend((raw.child as Record<string, unknown>) ?? { op: "true" }),
    };
  }
  if (op === "in") {
    const values: unknown[] = (raw.values as unknown[]) ?? [];
    return {
      _id: nextId(),
      op: "in",
      attr: String(raw.attr ?? ""),
      value: values.map(String).join(", "),
    };
  }
  if (op === "true" || op === "false") {
    return { _id: nextId(), op };
  }
  // Leaf ops with a single value
  return {
    _id: nextId(),
    op: op as LeafOp,
    attr: String(raw.attr ?? ""),
    value: String(raw.value ?? ""),
  };
}

export function toBackend(node: CondNode): Record<string, unknown> {
  if (node.op === "and" || node.op === "or") {
    return { op: node.op, children: node.children.map(toBackend) };
  }
  if (node.op === "not") {
    return { op: "not", child: toBackend(node.child) };
  }
  if (node.op === "true" || node.op === "false") {
    return { op: node.op };
  }
  if (node.op === "in") {
    const values = node.value
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return { op: "in", attr: node.attr, values };
  }
  // Remaining ops are leaf ops with attr + value — narrow via type guard.
  if (
    node.op === "eq" ||
    node.op === "neq" ||
    node.op === "startswith" ||
    node.op === "endswith" ||
    node.op === "contains" ||
    node.op === "gt" ||
    node.op === "gte" ||
    node.op === "lt" ||
    node.op === "lte" ||
    node.op === "exists"
  ) {
    return { op: node.op, attr: node.attr, value: coerceValue(node.op, node.value) };
  }
  return { op: "true" };
}

function coerceValue(op: LeafOp, raw: string): unknown {
  if (op === "gt" || op === "gte" || op === "lt" || op === "lte") {
    const n = Number(raw);
    return Number.isNaN(n) ? raw : n;
  }
  return raw;
}

// ─── Natural language description (exported for collapsed row view) ───────────

export function describeCondition(raw: Record<string, unknown>): string {
  const op = raw.op as string;

  if (op === "true") return "always";
  if (op === "false") return "never";
  if (op === "not") {
    const inner = raw.child as Record<string, unknown> | undefined;
    return `NOT (${inner ? describeCondition(inner) : "?"})`;
  }
  if (op === "and" || op === "or") {
    const children = (raw.children as Record<string, unknown>[] | undefined) ?? [];
    if (children.length === 0) return op.toUpperCase();
    return children.map(describeCondition).join(` ${op.toUpperCase()} `);
  }

  const attr = String(raw.attr ?? "?");
  const val = raw.value;
  const vals = raw.values;

  switch (op) {
    case "eq":        return `${attr} IS ${val}`;
    case "neq":       return `${attr} IS NOT ${val}`;
    case "in":        return `${attr} IN [${(vals as unknown[] | undefined)?.join(", ")}]`;
    case "startswith":return `${attr} STARTS WITH ${val}`;
    case "endswith":  return `${attr} ENDS WITH ${val}`;
    case "contains":  return `${attr} CONTAINS ${val}`;
    case "gt":        return `${attr} > ${val}`;
    case "gte":       return `${attr} >= ${val}`;
    case "lt":        return `${attr} < ${val}`;
    case "lte":       return `${attr} <= ${val}`;
    case "exists":    return `${attr} EXISTS`;
    default:          return `${attr} ${op} ${val ?? ""}`;
  }
}

// ─── Helpers to build default nodes ─────────────────────────────────────────

export function defaultLeaf(): CondNode {
  return { _id: nextId(), op: "eq", attr: "", value: "" };
}

export function defaultGroup(op: GroupOp = "and"): CondNode {
  return { _id: nextId(), op, children: [defaultLeaf()] };
}

export function defaultRoot(): CondNode {
  return defaultGroup("and");
}

// ─── Common attrs datalist ────────────────────────────────────────────────────

const COMMON_ATTRS = [
  "user.id",
  "user.email",
  "user.tier",
  "user.role",
  "user.plan",
  "user.country",
  "user.mfa_enabled",
  "org.id",
  "org.slug",
  "org.plan",
  "workspace.id",
  "workspace.slug",
  "application.id",
];

const LEAF_OPS: { value: LeafOp; label: string }[] = [
  { value: "eq",         label: "equals" },
  { value: "neq",        label: "not equals" },
  { value: "in",         label: "in (list)" },
  { value: "startswith", label: "starts with" },
  { value: "endswith",   label: "ends with" },
  { value: "contains",   label: "contains" },
  { value: "gt",         label: "greater than" },
  { value: "gte",        label: "greater than or equal" },
  { value: "lt",         label: "less than" },
  { value: "lte",        label: "less than or equal" },
  { value: "exists",     label: "exists" },
];

function needsValue(op: LeafOp): "text" | "number" | "csv" | "none" {
  if (op === "exists") return "none";
  if (op === "in") return "csv";
  if (["gt", "gte", "lt", "lte"].includes(op)) return "number";
  return "text";
}

// ─── Tree mutators (immutable) ───────────────────────────────────────────────

type Updater = (node: CondNode) => CondNode;

function updateNode(tree: CondNode, id: string, updater: Updater): CondNode {
  if (tree._id === id) return updater(tree);

  if (tree.op === "and" || tree.op === "or") {
    return {
      ...tree,
      children: tree.children.map((c) => updateNode(c, id, updater)),
    };
  }
  if (tree.op === "not") {
    return { ...tree, child: updateNode(tree.child, id, updater) };
  }
  return tree;
}

function deleteNode(tree: CondNode, id: string): CondNode | null {
  if (tree._id === id) return null;

  if (tree.op === "and" || tree.op === "or") {
    const children = tree.children
      .map((c) => deleteNode(c, id))
      .filter((c): c is CondNode => c !== null);
    return { ...tree, children };
  }
  if (tree.op === "not") {
    // If child is deleted, replace with literal true
    const newChild = deleteNode(tree.child, id);
    if (newChild === null) return { ...tree, child: { _id: nextId(), op: "true" } };
    return { ...tree, child: newChild };
  }
  return tree;
}

function addChildToGroup(tree: CondNode, groupId: string, child: CondNode): CondNode {
  if (tree.op === "and" || tree.op === "or") {
    if (tree._id === groupId) {
      return { ...tree, children: [...tree.children, child] };
    }
    return { ...tree, children: tree.children.map((c) => addChildToGroup(c, groupId, child)) };
  }
  if (tree.op === "not") {
    return { ...tree, child: addChildToGroup(tree.child, groupId, child) };
  }
  return tree;
}

// ─── Leaf row ────────────────────────────────────────────────────────────────

function LeafRow({
  node,
  path,
  onUpdate,
  onDelete,
  canDelete,
  listId,
}: {
  node: CondNode & { op: LeafOp; attr: string; value: string };
  path: string;
  onUpdate: (id: string, updater: Updater) => void;
  onDelete: (id: string) => void;
  canDelete: boolean;
  listId: string;
}) {
  const valKind = needsValue(node.op);

  function setAttr(attr: string) {
    onUpdate(node._id, (n) => ({ ...n, attr } as CondNode));
  }
  function setOp(op: LeafOp) {
    onUpdate(node._id, (n) => ({ ...n, op } as CondNode));
  }
  function setValue(value: string) {
    onUpdate(node._id, (n) => ({ ...n, value } as CondNode));
  }

  return (
    <div className="flex items-center gap-2 flex-wrap" data-testid={`condition-${path}`}>
      {/* Attribute */}
      <div className="relative min-w-[140px] max-w-[200px] flex-1">
        <input
          type="text"
          list={listId}
          value={node.attr}
          onChange={(e) => setAttr(e.target.value)}
          placeholder="user.tier"
          data-testid={`attr-input-${path}`}
          className={cn(
            "w-full rounded-lg border border-zinc-200 bg-white px-2.5 py-1.5 text-xs text-zinc-900 shadow-sm transition",
            "placeholder:text-zinc-400",
            "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
            "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:placeholder:text-zinc-500",
            "dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
          )}
        />
      </div>

      {/* Operator */}
      <select
        value={node.op}
        onChange={(e) => setOp(e.target.value as LeafOp)}
        data-testid={`op-select-${path}`}
        className={cn(
          "rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-xs text-zinc-900 shadow-sm transition",
          "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
          "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50",
          "dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
        )}
      >
        {LEAF_OPS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>

      {/* Value */}
      {valKind !== "none" && (
        <div className="min-w-[120px] max-w-[220px] flex-1">
          <input
            type={valKind === "number" ? "number" : "text"}
            value={node.value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={
              valKind === "csv"    ? "admin, owner" :
              valKind === "number" ? "18" :
              "value"
            }
            data-testid={`value-input-${path}`}
            className={cn(
              "w-full rounded-lg border border-zinc-200 bg-white px-2.5 py-1.5 text-xs text-zinc-900 shadow-sm transition",
              "placeholder:text-zinc-400",
              "focus:border-zinc-900 focus:outline-none focus:ring-1 focus:ring-zinc-900",
              "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50 dark:placeholder:text-zinc-500",
              "dark:focus:border-zinc-100 dark:focus:ring-zinc-100"
            )}
          />
        </div>
      )}
      {valKind === "none" && (
        <span className="text-[11px] italic text-zinc-400">(attribute presence)</span>
      )}

      {/* Delete */}
      {canDelete && (
        <button
          type="button"
          onClick={() => onDelete(node._id)}
          title="Remove condition"
          className="rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

// ─── Group block ─────────────────────────────────────────────────────────────

function GroupBlock({
  node,
  path,
  depth,
  isRoot,
  onUpdate,
  onDelete,
  listId,
}: {
  node: CondNode & { op: GroupOp; children: CondNode[] };
  path: string;
  depth: number;
  isRoot: boolean;
  onUpdate: (id: string, updater: Updater) => void;
  onDelete: (id: string) => void;
  listId: string;
}) {
  const toggleOp = useCallback(() => {
    onUpdate(node._id, (n) => ({
      ...n,
      op: (n.op as GroupOp) === "and" ? "or" : "and",
    } as CondNode));
  }, [node._id, onUpdate]);

  function addLeaf() {
    onUpdate(node._id, (n) => {
      if (n.op !== "and" && n.op !== "or") return n;
      return { ...n, children: [...n.children, defaultLeaf()] };
    });
  }

  function addGroup() {
    onUpdate(node._id, (n) => {
      if (n.op !== "and" && n.op !== "or") return n;
      return { ...n, children: [...n.children, defaultGroup()] };
    });
  }

  const borderCls =
    depth === 0
      ? "border-zinc-200 dark:border-zinc-700"
      : depth === 1
        ? "border-blue-200 dark:border-blue-800"
        : "border-purple-200 dark:border-purple-800";

  const opBtnCls =
    node.op === "and"
      ? "bg-blue-600 text-white dark:bg-blue-500"
      : "bg-amber-500 text-white dark:bg-amber-400 dark:text-zinc-900";

  return (
    <div
      className={cn(
        "rounded-xl border p-3 space-y-2",
        borderCls,
        depth > 0 && "ml-4"
      )}
      data-testid={`condition-${path}`}
    >
      {/* Group header */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleOp}
          title="Toggle AND/OR"
          data-testid={`op-select-${path}`}
          className={cn(
            "rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide transition",
            opBtnCls
          )}
        >
          {node.op}
        </button>
        <span className="text-[11px] text-zinc-400 dark:text-zinc-500">
          {node.op === "and" ? "all must match" : "any must match"}
        </span>
        {!isRoot && (
          <button
            type="button"
            onClick={() => onDelete(node._id)}
            title="Remove group"
            className="ml-auto rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Children */}
      {node.children.map((child, idx) => (
        <NodeRenderer
          key={child._id}
          node={child}
          path={`${path}.${idx}`}
          depth={depth + 1}
          isRoot={false}
          onUpdate={onUpdate}
          onDelete={onDelete}
          listId={listId}
          canDelete={node.children.length > 1 || !isRoot}
        />
      ))}

      {/* Add buttons */}
      <div className="flex items-center gap-2 pt-1">
        <button
          type="button"
          onClick={addLeaf}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <Plus className="h-3 w-3" /> Add condition
        </button>
        <button
          type="button"
          onClick={addGroup}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-zinc-600 transition hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <Plus className="h-3 w-3" /> Add group
        </button>
      </div>
    </div>
  );
}

// ─── Not block ───────────────────────────────────────────────────────────────

function NotBlock({
  node,
  path,
  depth,
  onUpdate,
  onDelete,
  listId,
}: {
  node: CondNode & { op: "not"; child: CondNode };
  path: string;
  depth: number;
  onUpdate: (id: string, updater: Updater) => void;
  onDelete: (id: string) => void;
  listId: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-red-200 p-3 dark:border-red-800",
        depth > 0 && "ml-4"
      )}
      data-testid={`condition-${path}`}
    >
      <div className="mb-2 flex items-center gap-2">
        <span className="rounded-md bg-red-100 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-red-700 dark:bg-red-900/50 dark:text-red-300">
          NOT
        </span>
        <button
          type="button"
          onClick={() => onDelete(node._id)}
          title="Remove NOT"
          className="ml-auto rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
      <NodeRenderer
        node={node.child}
        path={`${path}.child`}
        depth={depth + 1}
        isRoot={false}
        onUpdate={onUpdate}
        onDelete={onDelete}
        listId={listId}
        canDelete={false}
      />
    </div>
  );
}

// ─── Literal row ─────────────────────────────────────────────────────────────

function LiteralRow({
  node,
  path,
  onUpdate,
  onDelete,
  canDelete,
}: {
  node: CondNode & { op: "true" | "false" };
  path: string;
  onUpdate: (id: string, updater: Updater) => void;
  onDelete: (id: string) => void;
  canDelete: boolean;
}) {
  return (
    <div className="flex items-center gap-2" data-testid={`condition-${path}`}>
      <select
        value={node.op}
        onChange={(e) =>
          onUpdate(node._id, () => ({ _id: node._id, op: e.target.value as "true" | "false" }))
        }
        data-testid={`op-select-${path}`}
        className={cn(
          "rounded-lg border border-zinc-200 bg-white px-2 py-1.5 text-xs text-zinc-900 shadow-sm",
          "dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-50"
        )}
      >
        <option value="true">always match</option>
        <option value="false">never match</option>
      </select>
      {canDelete && (
        <button
          type="button"
          onClick={() => onDelete(node._id)}
          className="rounded-md p-1 text-zinc-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/30 dark:hover:text-red-400"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
}

// ─── Node renderer (dispatch by op) ─────────────────────────────────────────

function NodeRenderer({
  node,
  path,
  depth,
  isRoot,
  onUpdate,
  onDelete,
  listId,
  canDelete,
}: {
  node: CondNode;
  path: string;
  depth: number;
  isRoot: boolean;
  onUpdate: (id: string, updater: Updater) => void;
  onDelete: (id: string) => void;
  listId: string;
  canDelete: boolean;
}) {
  if (node.op === "and" || node.op === "or") {
    return (
      <GroupBlock
        node={node as CondNode & { op: GroupOp; children: CondNode[] }}
        path={path}
        depth={depth}
        isRoot={isRoot}
        onUpdate={onUpdate}
        onDelete={onDelete}
        listId={listId}
      />
    );
  }
  if (node.op === "not") {
    return (
      <NotBlock
        node={node as CondNode & { op: "not"; child: CondNode }}
        path={path}
        depth={depth}
        onUpdate={onUpdate}
        onDelete={onDelete}
        listId={listId}
      />
    );
  }
  if (node.op === "true" || node.op === "false") {
    return (
      <LiteralRow
        node={node as CondNode & { op: "true" | "false" }}
        path={path}
        onUpdate={onUpdate}
        onDelete={onDelete}
        canDelete={canDelete}
      />
    );
  }
  // Leaf
  return (
    <LeafRow
      node={node as CondNode & { op: LeafOp; attr: string; value: string }}
      path={path}
      onUpdate={onUpdate}
      onDelete={onDelete}
      canDelete={canDelete}
      listId={listId}
    />
  );
}

// ─── Public component ────────────────────────────────────────────────────────

export function ConditionTreeEditor({
  value,
  onChange,
}: {
  value: CondNode;
  onChange: (node: CondNode) => void;
}) {
  const listId = useId();

  function handleUpdate(id: string, updater: Updater) {
    onChange(updateNode(value, id, updater));
  }

  function handleDelete(id: string) {
    const next = deleteNode(value, id);
    if (next !== null) onChange(next);
  }

  return (
    <div className="space-y-2">
      <datalist id={listId}>
        {COMMON_ATTRS.map((a) => (
          <option key={a} value={a} />
        ))}
      </datalist>

      <NodeRenderer
        node={value}
        path="root"
        depth={0}
        isRoot
        onUpdate={handleUpdate}
        onDelete={handleDelete}
        listId={listId}
        canDelete={false}
      />

      {/* Quick-add literal at root for when user wants always/never rule */}
      {(value.op === "and" || value.op === "or") && (
        <div className="flex items-center gap-2 pl-1">
          <button
            type="button"
            onClick={() => {
              const withLit: CondNode = {
                ...(value as CondNode & { op: GroupOp; children: CondNode[] }),
                children: [
                  ...(value as CondNode & { op: GroupOp; children: CondNode[] }).children,
                  { _id: nextId(), op: "true" },
                ],
              };
              onChange(withLit);
            }}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-zinc-400 transition hover:bg-zinc-100 dark:hover:bg-zinc-800"
          >
            <Plus className="h-3 w-3" /> Add literal
          </button>
        </div>
      )}
    </div>
  );
}
