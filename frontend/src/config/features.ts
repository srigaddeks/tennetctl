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
    description: "Envelope-encrypted secret storage. Values are shown once at create / rotate and never re-displayed.",
    basePath: "/vault",
    testId: "nav-feature-vault",
    subFeatures: [
      { href: "/vault", label: "All secrets", testId: "nav-vault-secrets" },
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
