import type { Globe, ShieldCheck } from "lucide-react";

export type RoleCategory = "platform" | "org-scoped";
export type ActiveTab = "overview" | "capabilities" | "audit";

export type ConfirmAction = {
  title: string;
  body: string;
  variant: "info" | "warning" | "danger";
  confirmLabel: string;
  onConfirm: () => Promise<void>;
};

export type CategoryMeta = {
  label: string;
  icon: typeof Globe;
  borderCls: string;
  numCls: string;
  desc: string;
};

export type RoleTypeBadge = {
  tone: "purple" | "blue";
  label: string;
};

export type StatCard = {
  label: string;
  value: number;
  icon: typeof ShieldCheck;
  borderCls: string;
  numCls: string;
  testId: string;
};
