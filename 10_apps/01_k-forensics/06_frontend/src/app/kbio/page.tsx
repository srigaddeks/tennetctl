"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  Activity, Cpu, AlertTriangle, Bot, ShieldCheck, Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import { scoreColor, trustColor, formatScore, truncateId } from "@/lib/kbio-utils";
import type { KbioOverviewStats, KbioSessionData } from "@/types/api";

const MOCK_STATS: KbioOverviewStats = {
  total_sessions: 1247,
  active_sessions: 23,
  avg_drift_score: 0.18,
  anomaly_alerts: 7,
  bot_detections: 3,
  avg_trust_score: 0.82,
};

const MOCK_SESSIONS: KbioSessionData[] = [
  { id: "sess-a1b2c3d4-e5f6-7890-abcd-ef1234567890", sdk_session_id: "sdk-001", user_hash: "usr_h4sh_001_abc", device_uuid: "dev-001", status: "active", trust_level: "high", drift_score: 0.12, anomaly_score: 0.08, trust_score: 0.91, bot_score: 0.02, baseline_quality: "strong", pulse_count: 342, created_at: "2026-04-09T08:00:00Z", last_active_at: "2026-04-09T14:32:00Z" },
  { id: "sess-b2c3d4e5-f6a7-8901-bcde-f12345678901", sdk_session_id: "sdk-002", user_hash: "usr_h4sh_002_def", device_uuid: "dev-002", status: "active", trust_level: "medium", drift_score: 0.45, anomaly_score: 0.32, trust_score: 0.67, bot_score: 0.05, baseline_quality: "established", pulse_count: 128, created_at: "2026-04-09T09:15:00Z", last_active_at: "2026-04-09T14:28:00Z" },
  { id: "sess-c3d4e5f6-a7b8-9012-cdef-123456789012", sdk_session_id: "sdk-003", user_hash: "usr_h4sh_003_ghi", device_uuid: "dev-003", status: "terminated", trust_level: "low", drift_score: 0.78, anomaly_score: 0.65, trust_score: 0.35, bot_score: 0.12, baseline_quality: "forming", pulse_count: 56, created_at: "2026-04-09T07:30:00Z", last_active_at: "2026-04-09T12:45:00Z" },
  { id: "sess-d4e5f6a7-b8c9-0123-defa-234567890123", sdk_session_id: "sdk-004", user_hash: "usr_h4sh_004_jkl", device_uuid: "dev-004", status: "active", trust_level: "high", drift_score: 0.05, anomaly_score: 0.03, trust_score: 0.95, bot_score: 0.01, baseline_quality: "strong", pulse_count: 891, created_at: "2026-04-08T22:00:00Z", last_active_at: "2026-04-09T14:30:00Z" },
  { id: "sess-e5f6a7b8-c9d0-1234-efab-345678901234", sdk_session_id: "sdk-005", user_hash: "usr_h4sh_005_mno", device_uuid: "dev-005", status: "terminated", trust_level: "critical", drift_score: 0.92, anomaly_score: 0.88, trust_score: 0.11, bot_score: 0.85, baseline_quality: "insufficient", pulse_count: 14, created_at: "2026-04-09T10:00:00Z", last_active_at: "2026-04-09T10:12:00Z" },
  { id: "sess-f6a7b8c9-d0e1-2345-fabc-456789012345", sdk_session_id: "sdk-006", user_hash: "usr_h4sh_006_pqr", device_uuid: "dev-006", status: "active", trust_level: "high", drift_score: 0.09, anomaly_score: 0.04, trust_score: 0.89, bot_score: 0.01, baseline_quality: "strong", pulse_count: 567, created_at: "2026-04-08T18:00:00Z", last_active_at: "2026-04-09T14:25:00Z" },
  { id: "sess-a7b8c9d0-e1f2-3456-abcd-567890123456", sdk_session_id: "sdk-007", user_hash: "usr_h4sh_007_stu", device_uuid: "dev-007", status: "active", trust_level: "medium", drift_score: 0.38, anomaly_score: 0.22, trust_score: 0.72, bot_score: 0.06, baseline_quality: "established", pulse_count: 203, created_at: "2026-04-09T06:00:00Z", last_active_at: "2026-04-09T14:20:00Z" },
  { id: "sess-b8c9d0e1-f2a3-4567-bcde-678901234567", sdk_session_id: "sdk-008", user_hash: "usr_h4sh_008_vwx", device_uuid: "dev-008", status: "terminated", trust_level: "low", drift_score: 0.67, anomaly_score: 0.55, trust_score: 0.42, bot_score: 0.18, baseline_quality: "forming", pulse_count: 89, created_at: "2026-04-09T04:00:00Z", last_active_at: "2026-04-09T11:30:00Z" },
  { id: "sess-c9d0e1f2-a3b4-5678-cdef-789012345678", sdk_session_id: "sdk-009", user_hash: "usr_h4sh_009_yza", device_uuid: "dev-009", status: "active", trust_level: "high", drift_score: 0.15, anomaly_score: 0.10, trust_score: 0.88, bot_score: 0.03, baseline_quality: "strong", pulse_count: 445, created_at: "2026-04-08T20:00:00Z", last_active_at: "2026-04-09T14:18:00Z" },
  { id: "sess-d0e1f2a3-b4c5-6789-defa-890123456789", sdk_session_id: "sdk-010", user_hash: "usr_h4sh_010_bcd", device_uuid: "dev-010", status: "active", trust_level: "medium", drift_score: 0.52, anomaly_score: 0.41, trust_score: 0.58, bot_score: 0.09, baseline_quality: "established", pulse_count: 167, created_at: "2026-04-09T11:00:00Z", last_active_at: "2026-04-09T14:15:00Z" },
];

type StatCardProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
};

function StatCard({ icon, label, value, trend, trendUp }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3.5 py-4">
        <div className="w-9 h-9 rounded-md bg-surface-2 flex items-center justify-center text-foreground-muted shrink-0">
          {icon}
        </div>
        <div className="flex flex-col gap-0.5 min-w-0">
          <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">
            {label}
          </span>
          <span className="text-xl font-bold tracking-tight">{value}</span>
          {trend && (
            <span className={cn(
              "text-[10px] font-medium",
              trendUp ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400",
            )}>
              {trend}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function KbioOverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const stats = MOCK_STATS;
  const sessions = MOCK_SESSIONS;

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  if (loading) {
    return (
      <div className="px-8 py-8 max-w-[1100px]">
        <div className="mb-8">
          <Skeleton className="h-7 w-48 mb-2" />
          <Skeleton className="h-4 w-72" />
        </div>
        <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5 mb-10">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-[1100px]">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">kbio Overview</h1>
        <p className="text-xs text-foreground-muted mt-1">
          Behavioral biometrics intelligence — real-time session monitoring
        </p>
      </div>

      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5 mb-10">
        <StatCard
          icon={<Cpu size={18} />}
          label="Total Sessions"
          value={stats.total_sessions.toLocaleString()}
          trend="+12% this week"
          trendUp
        />
        <StatCard
          icon={<Activity size={18} />}
          label="Active Sessions"
          value={String(stats.active_sessions)}
          trend="5 new today"
          trendUp
        />
        <StatCard
          icon={<Zap size={18} />}
          label="Avg Drift Score"
          value={formatScore(stats.avg_drift_score)}
          trend="Stable"
          trendUp
        />
        <StatCard
          icon={<AlertTriangle size={18} />}
          label="Anomaly Alerts"
          value={String(stats.anomaly_alerts)}
          trend="+2 since yesterday"
          trendUp={false}
        />
        <StatCard
          icon={<Bot size={18} />}
          label="Bot Detections"
          value={String(stats.bot_detections)}
          trend="1 new today"
          trendUp={false}
        />
        <StatCard
          icon={<ShieldCheck size={18} />}
          label="Avg Trust Score"
          value={formatScore(stats.avg_trust_score)}
          trend="Healthy"
          trendUp
        />
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Session ID</TableHead>
              <TableHead>User Hash</TableHead>
              <TableHead>Drift</TableHead>
              <TableHead>Trust</TableHead>
              <TableHead>Bot</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Active</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sessions.map((s) => (
              <TableRow
                key={s.id}
                className="cursor-pointer"
                onClick={() => router.push(`/kbio/sessions/${s.id}`)}
              >
                <TableCell>
                  <span className="font-mono text-xs">{truncateId(s.id, 12)}</span>
                </TableCell>
                <TableCell>
                  <span className="font-mono text-xs">{truncateId(s.user_hash, 12)}</span>
                </TableCell>
                <TableCell>
                  <span className={cn("font-mono text-xs font-semibold", scoreColor(s.drift_score))}>
                    {formatScore(s.drift_score)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className={cn("font-mono text-xs font-semibold", trustColor(s.trust_score))}>
                    {formatScore(s.trust_score)}
                  </span>
                </TableCell>
                <TableCell>
                  <span className={cn("font-mono text-xs font-semibold", scoreColor(s.bot_score))}>
                    {formatScore(s.bot_score)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={s.status === "active" ? "success" : "default"}>
                    {s.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-foreground-muted text-xs">
                  {new Date(s.last_active_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
