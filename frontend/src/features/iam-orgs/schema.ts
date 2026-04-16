import { z } from "zod";

const SLUG_RE = /^[a-z][a-z0-9-]{1,62}$/;

export const orgCreateSchema = z.object({
  slug: z
    .string()
    .regex(SLUG_RE, "lowercase, starts with letter, hyphens allowed"),
  display_name: z.string().min(1, "required").max(128),
});

export const orgUpdateSchema = z.object({
  slug: z
    .string()
    .regex(SLUG_RE, "lowercase, starts with letter, hyphens allowed")
    .optional()
    .or(z.literal("")),
  display_name: z.string().min(1, "required").max(128).optional(),
});

export type OrgCreateForm = z.infer<typeof orgCreateSchema>;
export type OrgUpdateForm = z.infer<typeof orgUpdateSchema>;
