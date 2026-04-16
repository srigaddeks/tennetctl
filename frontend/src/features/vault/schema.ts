import { z } from "zod";

// Mirrors backend Pydantic key regex: ^[a-z][a-z0-9._-]{0,127}$
const KEY_RE = /^[a-z][a-z0-9._-]{0,127}$/;

export const secretCreateSchema = z.object({
  key: z
    .string()
    .min(1, "required")
    .regex(KEY_RE, "lowercase letter start; a-z 0-9 . _ - only; max 128"),
  value: z.string().min(1, "required").max(65536),
  description: z.string().max(500).optional().or(z.literal("")),
});

export const secretRotateSchema = z.object({
  value: z.string().min(1, "required").max(65536),
  description: z.string().max(500).optional().or(z.literal("")),
});

export type SecretCreateForm = z.infer<typeof secretCreateSchema>;
export type SecretRotateForm = z.infer<typeof secretRotateSchema>;
