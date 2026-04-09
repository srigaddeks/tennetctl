"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Zap, AlertTriangle, ShieldCheck, Bot } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import {
  scoreColor, trustColor, formatScore, scoreBg, baselineQualityVariant,
} from "@/lib/kbio-utils";
import type { KbioSessionData } from "@/types/api";

type ModalityBreakdown = {
  modality: string;
  drift_score: number;
  events: number;
  fusion_weight: number;
};

const MOCK_SESSION: KbioSessionData = {
  id: "sess-a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  sdk_session_id: "sdk-001",
  user_hash: "usr_h4sh_001_abc",
  device_uuid: "dev-uuid-001-abcdef",
  status: "active",
  trust_level: "high",
  drift_score: 0.12,
  anomaly_score: 0.08,
  trust_score: 0.91,
  bot_score: 0.02,
  baseline_quality: "strong",
  pulse_count: 342,
  created_at: "2026-04-09T08:00:00Z",
  last_active_at: "2026-04-09T14:32:00Z",
};

const MOCK_MODALITIES: ModalityBreakdown[] = [
  { modality: "keystroke", drift_score: 0.10, events: 1842, fusion_weight: 0.35 },
  { modality: "mouse", drift_score: 0.14, events: 3205, fusion_weight: 0.25 },
  { modality: "touch", drift_score: 0.08, events: 612, fusion_weight: 0.20 },
  { modality: "scroll", drift_score: 0.18, events: 445, fusion_weight: 0.10 },
  { modality: "accelerometer", drift_score: 0.06, events: 289, fusion_weight: 0.10 },
];

type ScoreCardProps = {
  icon: React.ReactNode;
  label: string;
  score: number;
  colorFn: (s: number) => string;
};

function ScoreCard({ icon, label, score, colorFn }: ScoreCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <div className={cn("w-10 h-10 rounded-md flex items-center justify-center shrink-0", scoreBg(score))}>
          {icon}
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">
            {label}
          </span>
          <span className={cn("text-2xl font-bold tracking-tight", colorFn(score))}>
            {formatScore(score)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export default function SessionDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);

  const session = { ...MOCK_SESSION, id: params.id ?? MOCK_SESSION.id };
  const modalities = MOCK_MODALITIES;

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  if (loading) {
    return (
      <div className="px-8 py-8 max-w-[1100px]">
        <Skeleton className="h-5 w-24 mb-4" />
        <Skeleton className="h-7 w-64 mb-2" />
        <Skeleton className="h-4 w-48 mb-6" />
        <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-md" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-[1100px]">
      <Button
        variant="ghost"
        size="sm"
        className="mb-4 -ml-2"
        onClick={() => router.push("/kbio/sessions")}
      >
        <ArrowLeft size={14} /> Back to Sessions
      </Button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Session Detail</h1>
        <p className="text-xs text-foreground-muted mt-1 font-mono">
          {session.id}
        </p>
      </div>

      {/* Score cards */}
      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5 mb-8">
        <ScoreCard
          icon={<Zap size={18} className={scoreColor(session.drift_score)} />}
          label="Drift Score"
          score={session.drift_score}
          colorFn={scoreColor}
        />
        <ScoreCard
          icon={<AlertTriangle size={18} className={scoreColor(session.anomaly_score)} />}
          label="Anomaly Score"
          score={session.anomaly_score}
          colorFn={scoreColor}
        />
        <ScoreCard
          icon={<ShieldCheck size={18} className={trustColor(session.trust_score)} />}
          label="Trust Score"
          score={session.trust_score}
          colorFn={trustColor}
        />
        <ScoreCard
          icon={<Bot size={18} className={scoreColor(session.bot_score)} />}
          label="Bot Score"
          score={session.bot_score}
          colorFn={scoreColor}
        />
      </div>

      {/* Session metadata */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Session Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-x-6 gap-y-4">
            <MetaField label="Session ID" value={session.id} mono />
            <MetaField label="SDK Session ID" value={session.sdk_session_id} mono />
            <MetaField label="User Hash" value={session.user_hash} mono />
            <MetaField label="Device UUID" value={session.device_uuid} mono />
            <MetaField label="Status">
              <Badge variant={session.status === "active" ? "success" : "default"}>
                {session.status}
              </Badge>
            </MetaField>
            <MetaField label="Trust Level">
              <Badge variant={
                session.trust_level === "high" ? "success"
                  : session.trust_level === "critical" ? "danger"
                    : session.trust_level === "low" ? "warning"
                      : "default"
              }>
                {session.trust_level}
              </Badge>
            </MetaField>
            <MetaField label="Baseline Quality">
              <Badge variant={baselineQualityVariant(session.baseline_quality)}>
                {session.baseline_quality}
              </Badge>
            </MetaField>
            <MetaField label="Pulse Count" value={String(session.pulse_count)} />
            <MetaField label="Created" value={new Date(session.created_at).toLocaleString()} />
            <MetaField label="Last Active" value={new Date(session.last_active_at).toLocaleString()} />
          </div>
        </CardContent>
      </Card>

      {/* Drift trend placeholder */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Drift Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 rounded-md border border-dashed border-border bg-surface-2 text-foreground-muted text-xs">
            Chart: Drift over time — will be added when charting library is integrated
          </div>
        </CardContent>
      </Card>

      {/* Modality breakdown */}
      <Card className="mb-8 overflow-hidden">
        <CardHeader>
          <CardTitle>Per-Modality Breakdown</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Modality</TableHead>
              <TableHead>Drift Score</TableHead>
              <TableHead>Events</TableHead>
              <TableHead>Fusion Weight</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {modalities.map((m) => (
              <TableRow key={m.modality}>
                <TableCell className="font-medium capitalize">{m.modality}</TableCell>
                <TableCell>
                  <span className={cn("font-mono text-xs font-semibold", scoreColor(m.drift_score))}>
                    {formatScore(m.drift_score)}
                  </span>
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {m.events.toLocaleString()}
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {(m.fusion_weight * 100).toFixed(0)}%
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Alerts section */}
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
        </CardHeader>
        <EmptyState
          icon={<AlertTriangle />}
          title="No alerts"
          description="No anomaly or policy alerts have been triggered for this session."
        />
      </Card>
    </div>
  );
}

function MetaField({
  label,
  value,
  mono,
  children,
}: {
  label: string;
  value?: string;
  mono?: boolean;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">
        {label}
      </span>
      {children ?? (
        <span className={cn("text-sm", mono && "font-mono text-xs break-all")}>
          {value}
        </span>
      )}
    </div>
  );
}
