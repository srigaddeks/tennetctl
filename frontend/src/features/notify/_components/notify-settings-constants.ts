import type {
  NotifyCategoryCode,
  NotifyChannelCode,
  NotifySubscriptionRecipientMode,
} from "@/types/api";

export const CHANNEL_OPTIONS: { id: number; code: NotifyChannelCode; label: string }[] = [
  { id: 1, code: "email",   label: "Email" },
  { id: 2, code: "webpush", label: "Web Push" },
  { id: 3, code: "in_app",  label: "In-app" },
];

export const RECIPIENT_MODES: { value: NotifySubscriptionRecipientMode; label: string; help: string }[] = [
  { value: "actor", label: "Actor (default)",        help: "Notify the user who triggered the audit event." },
  { value: "users", label: "Specific users",         help: "Comma-separated user UUIDs in recipient_filter.user_ids." },
  { value: "roles", label: "Users with role(s)",     help: "Comma-separated role codes (e.g. admin, owner) in recipient_filter.role_codes." },
];

export const CATEGORY_OPTIONS: { id: number; code: NotifyCategoryCode; label: string }[] = [
  { id: 1, code: "transactional", label: "Transactional" },
  { id: 2, code: "critical",      label: "Critical" },
  { id: 3, code: "marketing",     label: "Marketing" },
  { id: 4, code: "digest",        label: "Digest" },
];

export type SmtpConfigOption = { id: string; label: string; key: string };
export type TemplateOption = { id: string; key: string };
