export type SubFeatureNav = {
  href: string;
  label: string;
  testId: string;
};

export type FeatureNav = {
  key: string;
  label: string;
  description: string;
  basePath: string;
  testId: string;
  subFeatures: SubFeatureNav[];
};

export const FEATURES: FeatureNav[] = [
  {
    key: "overview",
    label: "Overview",
    description: "Landing hub — every installed feature at a glance.",
    basePath: "/",
    testId: "nav-feature-overview",
    subFeatures: [],
  },
  {
    key: "iam",
    label: "Identity",
    description: "Tenancy + identity: orgs, workspaces, users, roles, groups, applications.",
    basePath: "/iam",
    testId: "nav-feature-iam",
    subFeatures: [
      { href: "/iam/orgs", label: "Orgs", testId: "nav-orgs" },
      { href: "/iam/workspaces", label: "Workspaces", testId: "nav-workspaces" },
      { href: "/iam/users", label: "Users", testId: "nav-users" },
      { href: "/iam/memberships", label: "Memberships", testId: "nav-memberships" },
      { href: "/iam/roles", label: "Roles", testId: "nav-roles" },
      { href: "/iam/groups", label: "Groups", testId: "nav-groups" },
      { href: "/iam/applications", label: "Applications", testId: "nav-applications" },
      { href: "/iam/security/policy", label: "Auth Policy", testId: "nav-iam-policy" },
      { href: "/iam/security/portal-views", label: "Portal Views", testId: "nav-iam-portal-views" },
    ],
  },
  {
    key: "feature-flags",
    label: "Feature Flags",
    description: "Flags with targeting rules, per-entity overrides, permissions, deterministic rollout.",
    basePath: "/feature-flags",
    testId: "nav-feature-flags",
    subFeatures: [
      { href: "/feature-flags", label: "All flags", testId: "nav-flags-list" },
      { href: "/feature-flags/evaluate", label: "Evaluator", testId: "nav-flags-evaluator" },
    ],
  },
  {
    key: "vault",
    label: "Vault",
    description: "Envelope-encrypted secrets (write-only after create) + plaintext typed configs (viewable + editable). Both scoped global / org / workspace.",
    basePath: "/vault",
    testId: "nav-feature-vault",
    subFeatures: [
      { href: "/vault/secrets", label: "Secrets", testId: "nav-vault-secrets" },
      { href: "/vault/configs", label: "Configs",  testId: "nav-vault-configs" },
    ],
  },
  {
    key: "monitoring",
    label: "Monitoring",
    description: "Unified logs, metrics, traces, and dashboards over the Monitoring Query DSL.",
    basePath: "/monitoring",
    testId: "nav-feature-monitoring",
    subFeatures: [
      { href: "/monitoring", label: "Overview", testId: "nav-monitoring-overview" },
      { href: "/monitoring/logs", label: "Logs", testId: "nav-monitoring-logs" },
      { href: "/monitoring/metrics", label: "Metrics", testId: "nav-monitoring-metrics" },
      { href: "/monitoring/traces", label: "Traces", testId: "nav-monitoring-traces" },
      { href: "/monitoring/dashboards", label: "Dashboards", testId: "nav-monitoring-dashboards" },
      { href: "/monitoring/alerts", label: "Alerts", testId: "nav-monitoring-alerts" },
      { href: "/monitoring/alerts/rules", label: "Alert Rules", testId: "nav-monitoring-alert-rules" },
      { href: "/monitoring/alerts/silences", label: "Silences", testId: "nav-monitoring-silences" },
    ],
  },
  {
    key: "audit",
    label: "Audit",
    description: "PostHog-class event analytics over the append-only audit log. Filter by actor/org/event, inspect metadata, trace spans, aggregate.",
    basePath: "/audit",
    testId: "nav-feature-audit",
    subFeatures: [
      { href: "/audit", label: "Explorer", testId: "nav-audit-explorer" },
      { href: "/audit/authz", label: "AuthZ Explorer", testId: "nav-audit-authz" },
    ],
  },
  {
    key: "notify",
    label: "Notify",
    description: "Core notification primitive. Templates, subscriptions, unified delivery tracking across email / web push / in-app, transactional send API, per-user preferences.",
    basePath: "/notify",
    testId: "nav-feature-notify",
    subFeatures: [
      { href: "/notify/templates",   label: "Templates",   testId: "nav-notify-templates" },
      { href: "/notify/deliveries",  label: "Deliveries",  testId: "nav-notify-deliveries" },
      { href: "/notify/send",        label: "Send API",    testId: "nav-notify-send" },
      { href: "/notify/preferences", label: "Preferences", testId: "nav-notify-preferences" },
      { href: "/notify/settings",    label: "Settings",    testId: "nav-notify-settings" },
    ],
  },
  {
    key: "account",
    label: "Account",
    description: "Personal settings: active sessions, API keys, security.",
    basePath: "/account",
    testId: "nav-feature-account",
    subFeatures: [
      { href: "/account/sessions", label: "Sessions", testId: "nav-account-sessions" },
      { href: "/account/api-keys", label: "API Keys", testId: "nav-account-api-keys" },
      { href: "/account/security", label: "Security", testId: "nav-account-security" },
    ],
  },
  {
    key: "nodes",
    label: "Node Catalog",
    description: "Live registry of every feature, sub-feature, and node currently installed.",
    basePath: "/nodes",
    testId: "nav-feature-nodes",
    subFeatures: [
      { href: "/nodes", label: "All nodes", testId: "nav-nodes-all" },
    ],
  },
  {
    key: "system",
    label: "System",
    description: "Platform operations: module status, pool depth, worker lag, migration history.",
    basePath: "/system",
    testId: "nav-feature-system",
    subFeatures: [
      { href: "/system/health", label: "Health", testId: "nav-system-health" },
    ],
  },
];

export function activeFeature(pathname: string): FeatureNav {
  const matched = FEATURES
    .filter((f) => (f.basePath === "/" ? pathname === "/" : pathname === f.basePath || pathname.startsWith(f.basePath + "/")))
    .sort((a, b) => b.basePath.length - a.basePath.length)[0];
  return matched ?? FEATURES[0];
}

export function activeSubFeatureHref(pathname: string, feature: FeatureNav): string | null {
  const exact = feature.subFeatures.find((i) => i.href === pathname);
  if (exact) return exact.href;
  const prefixed = feature.subFeatures
    .filter((i) => pathname === i.href || pathname.startsWith(i.href + "/"))
    .sort((a, b) => b.href.length - a.href.length)[0];
  return prefixed?.href ?? null;
}
