import { z } from "zod";

const KEY_RE = /^[a-z][a-z0-9._-]{0,127}$/;

// Raw form schema — value is entered as a string and converted per value_type
// on submit. This keeps react-hook-form Input elements simple.
export const configCreateSchema = z
  .object({
    key: z
      .string()
      .min(1, "required")
      .regex(KEY_RE, "lowercase letter start; a-z 0-9 . _ - only; max 128"),
    value_type: z.enum(["boolean", "string", "number", "json"]),
    value_raw: z.string().min(1, "required"),
    description: z.string().max(500).optional().or(z.literal("")),
    scope: z.enum(["global", "org", "workspace"]),
    org_id: z.string().optional().or(z.literal("")),
    workspace_id: z.string().optional().or(z.literal("")),
  })
  .superRefine((data, ctx) => {
    // Scope-shape checks mirror the secrets schema.
    if (data.scope === "global") {
      if (data.org_id) ctx.addIssue({ code: "custom", path: ["org_id"], message: "must be empty for scope=global" });
      if (data.workspace_id) ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "must be empty for scope=global" });
    } else if (data.scope === "org") {
      if (!data.org_id) ctx.addIssue({ code: "custom", path: ["org_id"], message: "required for scope=org" });
      if (data.workspace_id) ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "must be empty for scope=org" });
    } else if (data.scope === "workspace") {
      if (!data.org_id) ctx.addIssue({ code: "custom", path: ["org_id"], message: "required for scope=workspace" });
      if (!data.workspace_id) ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "required for scope=workspace" });
    }
    // Value-shape checks against declared type.
    const v = data.value_raw;
    if (data.value_type === "boolean") {
      if (v !== "true" && v !== "false") {
        ctx.addIssue({ code: "custom", path: ["value_raw"], message: "must be 'true' or 'false'" });
      }
    } else if (data.value_type === "number") {
      if (isNaN(Number(v))) {
        ctx.addIssue({ code: "custom", path: ["value_raw"], message: "must be a number" });
      }
    } else if (data.value_type === "json") {
      try {
        JSON.parse(v);
      } catch {
        ctx.addIssue({ code: "custom", path: ["value_raw"], message: "must be valid JSON" });
      }
    }
    // 'string' accepts anything.
  });

export const configUpdateValueSchema = z.object({
  value_raw: z.string().min(1, "required"),
});

export type ConfigCreateForm = z.infer<typeof configCreateSchema>;
export type ConfigUpdateValueForm = z.infer<typeof configUpdateValueSchema>;

export function parseValue(raw: string, value_type: string): unknown {
  if (value_type === "boolean") return raw === "true";
  if (value_type === "number") return Number(raw);
  if (value_type === "json") return JSON.parse(raw);
  return raw; // string
}

export function stringifyValue(value: unknown, value_type: string): string {
  if (value_type === "json") return JSON.stringify(value, null, 2);
  if (value_type === "boolean") return value ? "true" : "false";
  return String(value);
}
