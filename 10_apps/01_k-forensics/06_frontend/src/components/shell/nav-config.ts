import {
  LayoutGrid,
  Users,
  Settings,
  Activity,
  Shield,
  Fingerprint,
  Cpu,
  ScrollText,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
};

export type NavGroup = {
  label: string;
  items: NavItem[];
};

export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { label: "Dashboard", href: "/", icon: LayoutGrid },
    ],
  },
  {
    label: "Behavioral Intelligence",
    items: [
      { label: "kbio Overview", href: "/kbio", icon: Activity },
      { label: "Sessions", href: "/kbio/sessions", icon: Cpu },
      { label: "User Profiles", href: "/kbio/users", icon: Fingerprint },
      { label: "Devices", href: "/kbio/devices", icon: Shield },
      { label: "Policies", href: "/kbio/policies", icon: ScrollText },
    ],
  },
  {
    label: "Administration",
    items: [
      { label: "Team", href: "/settings/members", icon: Users },
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export const SETTINGS_TABS = [
  { id: "profile", label: "Profile", href: "/settings/profile" },
  { id: "orgs", label: "Organizations", href: "/settings/orgs" },
  { id: "workspaces", label: "Workspaces", href: "/settings/workspaces" },
  { id: "members", label: "Members", href: "/settings/members" },
  { id: "password", label: "Password", href: "/settings/password" },
] as const;
