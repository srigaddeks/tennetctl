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
import { listKbioSessions } from "@/lib/api";
import type { KbioOverviewStats, KbioSessionData } from "@/types/api";

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

function deriveStats(sessions: KbioSessionData[]): KbioOverviewStats {
  const active = sessions.filter((s) => s.status === "active");
  const driftSum = sessions.reduce((a, s) => a + s.drift_score, 0);
  const trustSum = sessions.reduce((a, s) => a + s.trust_score, 0);
  const anomalyAlerts = sessions.filter((s) => s.anomaly_score > 0.5).length;
  const botDetections = sessions.filter((s) => s.bot_score > 0.5).length;
  return {
    total_sessions: sessions.length,
    active_sessions: active.length,
    avg_drift_score: sessions.length ? driftSum / sessions.length : 0,
    anomaly_alerts: anomalyAlerts,
    bot_detections: botDetections,
    avg_trust_score: sessions.length ? trustSum / sessions.length : 0,
  };
}

export default function KbioOverviewPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [sessions, setSessions] = React.useState<KbioSessionData[]>([]);
  const [stats, setStats] = React.useState<KbioOverviewStats>({
    total_sessions: 0, active_sessions: 0, avg_drift_score: 0,
    anomaly_alerts: 0, bot_detections: 0, avg_trust_score: 0,
  });

  React.useEffect(() => {
    listKbioSessions({ limit: 50 })
      .then((res) => {
        if (res.ok && res.data) {
          const items = res.data.items ?? res.data as unknown as KbioSessionData[];
          setSessions(Array.isArray(items) ? items : []);
          setStats(deriveStats(Array.isArray(items) ? items : []));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
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
        />
        <StatCard
          icon={<Activity size={18} />}
          label="Active Sessions"
          value={String(stats.active_sessions)}
        />
        <StatCard
          icon={<Zap size={18} />}
          label="Avg Drift Score"
          value={formatScore(stats.avg_drift_score)}
        />
        <StatCard
          icon={<AlertTriangle size={18} />}
          label="Anomaly Alerts"
          value={String(stats.anomaly_alerts)}
        />
        <StatCard
          icon={<Bot size={18} />}
          label="Bot Detections"
          value={String(stats.bot_detections)}
        />
        <StatCard
          icon={<ShieldCheck size={18} />}
          label="Avg Trust Score"
          value={formatScore(stats.avg_trust_score)}
        />
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
        </CardHeader>
        {sessions.length === 0 ? (
          <div className="px-6 py-10 text-center text-foreground-muted text-sm">
            No sessions yet. Start the demo site to generate behavioral data.
          </div>
        ) : (
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
              {sessions.slice(0, 10).map((s) => (
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
        )}
      </Card>
    </div>
  );
}
