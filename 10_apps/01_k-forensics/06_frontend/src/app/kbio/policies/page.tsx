"use client";

import * as React from "react";
import { ScrollText, ChevronDown, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { listKbioPolicies } from "@/lib/api";
import type { KbioPolicyData } from "@/types/api";

const CATEGORIES = [
  "all", "fraud", "auth", "bot", "compliance", "risk", "trust", "session", "geo", "credential",
] as const;

function actionVariant(action: string): "success" | "warning" | "danger" | "info" | "default" {
  switch (action) {
    case "allow": return "success";
    case "monitor": return "info";
    case "challenge": return "warning";
    case "block": return "danger";
    default: return "default";
  }
}

function categoryVariant(category: string): "success" | "warning" | "danger" | "info" | "default" {
  switch (category) {
    case "fraud": return "danger";
    case "bot": return "danger";
    case "auth": return "info";
    case "trust": return "success";
    case "risk": return "warning";
    case "compliance": return "info";
    case "session": return "default";
    case "geo": return "warning";
    case "credential": return "info";
    default: return "default";
  }
}

const MOCK_POLICIES: KbioPolicyData[] = [
  { id: "pol-001", code: "fraud.velocity_spike", name: "Velocity Spike Detection", description: "Detects sudden increases in input velocity that may indicate automated input or session hijacking.", category: "fraud", default_action: "challenge", severity: 8, conditions: { velocity_threshold: 3.5, window_seconds: 10 }, default_config: { cooldown_minutes: 5, max_challenges: 3 }, tags: "fraud,velocity,automation", version: "1.0.0", is_active: true, created_at: "2026-01-15T00:00:00Z" },
  { id: "pol-002", code: "bot.pattern_replay", name: "Pattern Replay Detection", description: "Identifies mechanical replay of previously captured behavioral patterns, a common bot technique.", category: "bot", default_action: "block", severity: 9, conditions: { similarity_threshold: 0.95, min_events: 50 }, default_config: { block_duration_minutes: 30 }, tags: "bot,replay,automation", version: "1.0.0", is_active: true, created_at: "2026-01-15T00:00:00Z" },
  { id: "pol-003", code: "auth.baseline_deviation", name: "Baseline Deviation Alert", description: "Triggers when a user's behavioral pattern deviates significantly from their established baseline.", category: "auth", default_action: "monitor", severity: 5, conditions: { drift_threshold: 0.6, confidence_min: 0.7 }, default_config: { alert_cooldown_minutes: 15 }, tags: "auth,drift,baseline", version: "1.0.0", is_active: true, created_at: "2026-01-15T00:00:00Z" },
  { id: "pol-004", code: "trust.device_switch", name: "Rapid Device Switch", description: "Flags sessions where a user rapidly switches between devices, which may indicate credential sharing.", category: "trust", default_action: "challenge", severity: 6, conditions: { max_devices_per_hour: 3, window_hours: 1 }, default_config: { challenge_type: "mfa" }, tags: "trust,device,credential", version: "1.0.0", is_active: true, created_at: "2026-01-20T00:00:00Z" },
  { id: "pol-005", code: "risk.new_device_high_value", name: "New Device High-Value Action", description: "Requires additional verification when a high-value action is performed from a previously unseen device.", category: "risk", default_action: "challenge", severity: 7, conditions: { device_age_minutes: 30, action_value_threshold: "high" }, default_config: { verification_type: "step_up" }, tags: "risk,device,high-value", version: "1.0.0", is_active: true, created_at: "2026-01-20T00:00:00Z" },
  { id: "pol-006", code: "compliance.session_timeout", name: "Behavioral Session Timeout", description: "Enforces session timeout based on behavioral inactivity rather than just time-based expiry.", category: "compliance", default_action: "block", severity: 4, conditions: { idle_threshold_minutes: 15, behavioral_idle: true }, default_config: { grace_period_seconds: 60 }, tags: "compliance,session,timeout", version: "1.0.0", is_active: true, created_at: "2026-02-01T00:00:00Z" },
  { id: "pol-007", code: "geo.impossible_travel", name: "Impossible Travel Detection", description: "Detects login attempts from geographically distant locations within an impossibly short time window.", category: "geo", default_action: "block", severity: 9, conditions: { max_speed_kmh: 1000, min_distance_km: 500 }, default_config: { block_duration_minutes: 60 }, tags: "geo,travel,anomaly", version: "1.0.0", is_active: true, created_at: "2026-02-01T00:00:00Z" },
  { id: "pol-008", code: "credential.stuffing_detect", name: "Credential Stuffing Detection", description: "Identifies patterns consistent with credential stuffing attacks based on behavioral uniformity.", category: "credential", default_action: "block", severity: 9, conditions: { uniformity_threshold: 0.9, attempt_window_minutes: 5, min_attempts: 10 }, default_config: { ip_block_duration_minutes: 120 }, tags: "credential,stuffing,attack", version: "1.0.0", is_active: true, created_at: "2026-02-15T00:00:00Z" },
  { id: "pol-009", code: "session.concurrent_limit", name: "Concurrent Session Limit", description: "Limits the number of concurrent active sessions per user based on behavioral profile.", category: "session", default_action: "monitor", severity: 3, conditions: { max_concurrent: 5 }, default_config: { notification: true }, tags: "session,limit,concurrent", version: "1.0.0", is_active: true, created_at: "2026-02-15T00:00:00Z" },
  { id: "pol-010", code: "fraud.typing_anomaly", name: "Typing Rhythm Anomaly", description: "Detects anomalous typing patterns that deviate from the user's established keystroke dynamics.", category: "fraud", default_action: "monitor", severity: 6, conditions: { rhythm_deviation: 0.5, min_keystrokes: 20 }, default_config: { sensitivity: "medium" }, tags: "fraud,keystroke,anomaly", version: "1.0.0", is_active: true, created_at: "2026-03-01T00:00:00Z" },
];

export default function KbioPoliciesPage() {
  const [loading, setLoading] = React.useState(true);
  const [policies, setPolicies] = React.useState<KbioPolicyData[]>([]);
  const [category, setCategory] = React.useState<string>("all");
  const [expanded, setExpanded] = React.useState<string | null>(null);
  const [apiAvailable, setApiAvailable] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await listKbioPolicies({ limit: 100 });
        if (!cancelled && res.ok) {
          setPolicies(res.data.items);
          setApiAvailable(true);
          setLoading(false);
          return;
        }
      } catch {
        // API not available, use mock data
      }
      if (!cancelled) {
        setPolicies(MOCK_POLICIES);
        setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = category === "all"
    ? policies
    : policies.filter((p) => p.category === category);

  if (loading) {
    return (
      <div className="px-8 py-8 max-w-[1100px]">
        <Skeleton className="h-7 w-40 mb-2" />
        <Skeleton className="h-4 w-64 mb-6" />
        <Skeleton className="h-10 w-full mb-4" />
        <Skeleton className="h-[400px] rounded-md" />
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-[1100px]">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <h1 className="text-2xl font-bold tracking-tight">Policy Catalog</h1>
          {!apiAvailable && (
            <Badge variant="warning">mock data</Badge>
          )}
        </div>
        <p className="text-xs text-foreground-muted mt-1">
          Predefined behavioral biometrics policies — view-only catalog
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 mb-4">
        {CATEGORIES.map((cat) => (
          <Button
            key={cat}
            variant={category === cat ? "default" : "outline"}
            size="sm"
            onClick={() => setCategory(cat)}
          >
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
          </Button>
        ))}
        <span className="text-xs text-foreground-muted ml-2">
          {filtered.length} polic{filtered.length !== 1 ? "ies" : "y"}
        </span>
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ScrollText size={14} className="text-foreground-muted" />
            Policies
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Tags</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((p) => (
              <React.Fragment key={p.id}>
                <TableRow
                  className="cursor-pointer"
                  onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                >
                  <TableCell className="w-8 pr-0">
                    {expanded === p.id
                      ? <ChevronDown size={14} className="text-foreground-muted" />
                      : <ChevronRight size={14} className="text-foreground-muted" />
                    }
                  </TableCell>
                  <TableCell>
                    <span className="font-mono text-xs">{p.code}</span>
                  </TableCell>
                  <TableCell className="font-medium text-sm">{p.name}</TableCell>
                  <TableCell>
                    <Badge variant={categoryVariant(p.category)}>{p.category}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={actionVariant(p.default_action)}>{p.default_action}</Badge>
                  </TableCell>
                  <TableCell>
                    <SeverityBar severity={p.severity} />
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {p.tags.split(",").map((t) => (
                        <Badge key={t} variant="outline" className="text-[9px]">
                          {t.trim()}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
                {expanded === p.id && (
                  <TableRow>
                    <TableCell colSpan={7} className="bg-surface-2">
                      <PolicyDetail policy={p} />
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}

function SeverityBar({ severity }: { severity: number }) {
  const pct = (severity / 10) * 100;
  const color = severity >= 8 ? "bg-red-500" : severity >= 5 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-12 rounded-full bg-surface-3 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-foreground-muted">{severity}/10</span>
    </div>
  );
}

function PolicyDetail({ policy }: { policy: KbioPolicyData }) {
  return (
    <Card className="border-0 shadow-none bg-transparent">
      <CardContent className="p-3">
        <div className="space-y-4">
          <div>
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-1">
              Description
            </span>
            <p className="text-sm text-foreground">{policy.description}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-1">
                Conditions
              </span>
              <pre className="text-xs font-mono bg-surface rounded-md p-3 border border-border overflow-auto max-h-40">
                {JSON.stringify(policy.conditions, null, 2)}
              </pre>
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-1">
                Default Config
              </span>
              <pre className="text-xs font-mono bg-surface rounded-md p-3 border border-border overflow-auto max-h-40">
                {JSON.stringify(policy.default_config, null, 2)}
              </pre>
            </div>
          </div>
          <div className="flex gap-6">
            <div>
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-0.5">Version</span>
              <span className="text-xs font-mono">{policy.version}</span>
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-0.5">Status</span>
              <Badge variant={policy.is_active ? "success" : "default"}>
                {policy.is_active ? "active" : "inactive"}
              </Badge>
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold block mb-0.5">Created</span>
              <span className="text-xs">{new Date(policy.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
