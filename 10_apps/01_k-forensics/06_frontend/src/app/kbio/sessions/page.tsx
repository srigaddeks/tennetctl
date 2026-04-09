"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Cpu } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/cn";
import { scoreColor, trustColor, formatScore, truncateId } from "@/lib/kbio-utils";
import type { KbioSessionData } from "@/types/api";

const MOCK_SESSIONS: KbioSessionData[] = [
  { id: "sess-a1b2c3d4-e5f6-7890-abcd-ef1234567890", sdk_session_id: "sdk-001", user_hash: "usr_h4sh_001_abc", device_uuid: "dev-uuid-001", status: "active", trust_level: "high", drift_score: 0.12, anomaly_score: 0.08, trust_score: 0.91, bot_score: 0.02, baseline_quality: "strong", pulse_count: 342, created_at: "2026-04-09T08:00:00Z", last_active_at: "2026-04-09T14:32:00Z" },
  { id: "sess-b2c3d4e5-f6a7-8901-bcde-f12345678901", sdk_session_id: "sdk-002", user_hash: "usr_h4sh_002_def", device_uuid: "dev-uuid-002", status: "active", trust_level: "medium", drift_score: 0.45, anomaly_score: 0.32, trust_score: 0.67, bot_score: 0.05, baseline_quality: "established", pulse_count: 128, created_at: "2026-04-09T09:15:00Z", last_active_at: "2026-04-09T14:28:00Z" },
  { id: "sess-c3d4e5f6-a7b8-9012-cdef-123456789012", sdk_session_id: "sdk-003", user_hash: "usr_h4sh_003_ghi", device_uuid: "dev-uuid-003", status: "terminated", trust_level: "low", drift_score: 0.78, anomaly_score: 0.65, trust_score: 0.35, bot_score: 0.12, baseline_quality: "forming", pulse_count: 56, created_at: "2026-04-09T07:30:00Z", last_active_at: "2026-04-09T12:45:00Z" },
  { id: "sess-d4e5f6a7-b8c9-0123-defa-234567890123", sdk_session_id: "sdk-004", user_hash: "usr_h4sh_004_jkl", device_uuid: "dev-uuid-004", status: "active", trust_level: "high", drift_score: 0.05, anomaly_score: 0.03, trust_score: 0.95, bot_score: 0.01, baseline_quality: "strong", pulse_count: 891, created_at: "2026-04-08T22:00:00Z", last_active_at: "2026-04-09T14:30:00Z" },
  { id: "sess-e5f6a7b8-c9d0-1234-efab-345678901234", sdk_session_id: "sdk-005", user_hash: "usr_h4sh_005_mno", device_uuid: "dev-uuid-005", status: "terminated", trust_level: "critical", drift_score: 0.92, anomaly_score: 0.88, trust_score: 0.11, bot_score: 0.85, baseline_quality: "insufficient", pulse_count: 14, created_at: "2026-04-09T10:00:00Z", last_active_at: "2026-04-09T10:12:00Z" },
  { id: "sess-f6a7b8c9-d0e1-2345-fabc-456789012345", sdk_session_id: "sdk-006", user_hash: "usr_h4sh_006_pqr", device_uuid: "dev-uuid-006", status: "active", trust_level: "high", drift_score: 0.09, anomaly_score: 0.04, trust_score: 0.89, bot_score: 0.01, baseline_quality: "strong", pulse_count: 567, created_at: "2026-04-08T18:00:00Z", last_active_at: "2026-04-09T14:25:00Z" },
  { id: "sess-a7b8c9d0-e1f2-3456-abcd-567890123456", sdk_session_id: "sdk-007", user_hash: "usr_h4sh_007_stu", device_uuid: "dev-uuid-007", status: "active", trust_level: "medium", drift_score: 0.38, anomaly_score: 0.22, trust_score: 0.72, bot_score: 0.06, baseline_quality: "established", pulse_count: 203, created_at: "2026-04-09T06:00:00Z", last_active_at: "2026-04-09T14:20:00Z" },
  { id: "sess-b8c9d0e1-f2a3-4567-bcde-678901234567", sdk_session_id: "sdk-008", user_hash: "usr_h4sh_008_vwx", device_uuid: "dev-uuid-008", status: "terminated", trust_level: "low", drift_score: 0.67, anomaly_score: 0.55, trust_score: 0.42, bot_score: 0.18, baseline_quality: "forming", pulse_count: 89, created_at: "2026-04-09T04:00:00Z", last_active_at: "2026-04-09T11:30:00Z" },
  { id: "sess-c9d0e1f2-a3b4-5678-cdef-789012345678", sdk_session_id: "sdk-009", user_hash: "usr_h4sh_009_yza", device_uuid: "dev-uuid-009", status: "active", trust_level: "high", drift_score: 0.15, anomaly_score: 0.10, trust_score: 0.88, bot_score: 0.03, baseline_quality: "strong", pulse_count: 445, created_at: "2026-04-08T20:00:00Z", last_active_at: "2026-04-09T14:18:00Z" },
  { id: "sess-d0e1f2a3-b4c5-6789-defa-890123456789", sdk_session_id: "sdk-010", user_hash: "usr_h4sh_010_bcd", device_uuid: "dev-uuid-010", status: "active", trust_level: "medium", drift_score: 0.52, anomaly_score: 0.41, trust_score: 0.58, bot_score: 0.09, baseline_quality: "established", pulse_count: 167, created_at: "2026-04-09T11:00:00Z", last_active_at: "2026-04-09T14:15:00Z" },
  { id: "sess-e1f2a3b4-c5d6-7890-efab-901234567890", sdk_session_id: "sdk-011", user_hash: "usr_h4sh_011_efg", device_uuid: "dev-uuid-011", status: "terminated", trust_level: "medium", drift_score: 0.55, anomaly_score: 0.48, trust_score: 0.52, bot_score: 0.11, baseline_quality: "forming", pulse_count: 72, created_at: "2026-04-08T16:00:00Z", last_active_at: "2026-04-09T09:00:00Z" },
  { id: "sess-f2a3b4c5-d6e7-8901-fabc-012345678901", sdk_session_id: "sdk-012", user_hash: "usr_h4sh_012_hij", device_uuid: "dev-uuid-012", status: "active", trust_level: "high", drift_score: 0.08, anomaly_score: 0.06, trust_score: 0.93, bot_score: 0.01, baseline_quality: "strong", pulse_count: 612, created_at: "2026-04-08T14:00:00Z", last_active_at: "2026-04-09T14:10:00Z" },
];

const STATUS_OPTIONS = ["all", "active", "terminated"] as const;
const PAGE_SIZE = 10;

export default function KbioSessionsPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [filter, setFilter] = React.useState<string>("all");
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  const filtered = filter === "all"
    ? MOCK_SESSIONS
    : MOCK_SESSIONS.filter((s) => s.status === filter);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  if (loading) {
    return (
      <div className="px-8 py-8 max-w-[1100px]">
        <Skeleton className="h-7 w-40 mb-2" />
        <Skeleton className="h-4 w-64 mb-6" />
        <Skeleton className="h-[400px] rounded-md" />
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-[1100px]">
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Sessions</h1>
        <p className="text-xs text-foreground-muted mt-1">
          All behavioral biometrics sessions across the platform
        </p>
      </div>

      <div className="flex items-center gap-2 mb-4">
        {STATUS_OPTIONS.map((opt) => (
          <Button
            key={opt}
            variant={filter === opt ? "default" : "outline"}
            size="sm"
            onClick={() => { setFilter(opt); setPage(0); }}
          >
            {opt.charAt(0).toUpperCase() + opt.slice(1)}
          </Button>
        ))}
        <span className="text-xs text-foreground-muted ml-2">
          {filtered.length} session{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu size={14} className="text-foreground-muted" />
            Session List
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Session ID</TableHead>
              <TableHead>User Hash</TableHead>
              <TableHead>Drift</TableHead>
              <TableHead>Anomaly</TableHead>
              <TableHead>Trust</TableHead>
              <TableHead>Bot</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Pulses</TableHead>
              <TableHead>Last Active</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginated.map((s) => (
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
                  <span className={cn("font-mono text-xs font-semibold", scoreColor(s.anomaly_score))}>
                    {formatScore(s.anomaly_score)}
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
                <TableCell className="text-xs text-foreground-muted">
                  {s.pulse_count}
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {new Date(s.last_active_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-border">
            <span className="text-xs text-foreground-muted">
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
