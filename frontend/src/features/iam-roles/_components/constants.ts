import { Building2, Globe } from "lucide-react";
import { z } from "zod";

import type { RoleType } from "@/types/api";

import type { CategoryMeta, RoleCategory, RoleTypeBadge } from "./types";

export const CATEGORY_META: Record<RoleCategory, CategoryMeta> = {
  platform: {
    label: "Platform",
    icon: Globe,
    borderCls: "border-l-violet-500",
    numCls: "text-violet-600 dark:text-violet-400",
    desc: "Roles without an org (org_id = NULL) — apply across the whole platform",
  },
  "org-scoped": {
    label: "Org-scoped",
    icon: Building2,
    borderCls: "border-l-blue-500",
    numCls: "text-blue-600 dark:text-blue-400",
    desc: "Roles bound to a specific org",
  },
};

export const ROLE_TYPE_BADGE: Record<RoleType, RoleTypeBadge> = {
  system: { tone: "purple", label: "system" },
  custom: { tone: "blue", label: "custom" },
};

export const CODE_RE = /^[a-z][a-z0-9_]{1,62}$/;

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 62);
}

export const createSchema = z.object({
  org_id: z.string().optional(),
  role_type: z.enum(["system", "custom"]),
  code: z.string().regex(CODE_RE, "Must be lowercase_snake_case (a–z, 0–9, _)"),
  label: z.string().min(1, "Required"),
  description: z.string().optional(),
});
export type CreateForm = z.infer<typeof createSchema>;

export const updateSchema = z.object({
  label: z.string().min(1, "Required").optional(),
  description: z.string().optional(),
  is_active: z.boolean().optional(),
});
export type UpdateForm = z.infer<typeof updateSchema>;
