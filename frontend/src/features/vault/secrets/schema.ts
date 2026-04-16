import { z } from "zod";

// Mirrors backend Pydantic key regex: ^[a-z][a-z0-9._-]{0,127}$
const KEY_RE = /^[a-z][a-z0-9._-]{0,127}$/;

export const secretCreateSchema = z
  .object({
    key: z
      .string()
      .min(1, "required")
      .regex(KEY_RE, "lowercase letter start; a-z 0-9 . _ - only; max 128"),
    value: z.string().min(1, "required").max(65536),
    description: z.string().max(500).optional().or(z.literal("")),
    scope: z.enum(["global", "org", "workspace"]),
    org_id: z.string().optional().or(z.literal("")),
    workspace_id: z.string().optional().or(z.literal("")),
  })
  .superRefine((data, ctx) => {
    if (data.scope === "global") {
      if (data.org_id) {
        ctx.addIssue({ code: "custom", path: ["org_id"], message: "must be empty for scope=global" });
      }
      if (data.workspace_id) {
        ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "must be empty for scope=global" });
      }
    } else if (data.scope === "org") {
      if (!data.org_id) {
        ctx.addIssue({ code: "custom", path: ["org_id"], message: "required for scope=org" });
      }
      if (data.workspace_id) {
        ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "must be empty for scope=org" });
      }
    } else if (data.scope === "workspace") {
      if (!data.org_id) {
        ctx.addIssue({ code: "custom", path: ["org_id"], message: "required for scope=workspace" });
      }
      if (!data.workspace_id) {
        ctx.addIssue({ code: "custom", path: ["workspace_id"], message: "required for scope=workspace" });
      }
    }
  });

export const secretRotateSchema = z.object({
  value: z.string().min(1, "required").max(65536),
  description: z.string().max(500).optional().or(z.literal("")),
});

export type SecretCreateForm = z.infer<typeof secretCreateSchema>;
export type SecretRotateForm = z.infer<typeof secretRotateSchema>;
