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
import { listKbioSessions } from "@/lib/api";
import type { KbioSessionData } from "@/types/api";

const STATUS_OPTIONS = ["all", "active", "terminated"] as const;
const PAGE_SIZE = 10;

export default function KbioSessionsPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [sessions, setSessions] = React.useState<KbioSessionData[]>([]);
  const [filter, setFilter] = React.useState<string>("all");
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    listKbioSessions({ limit: 100 })
      .then((res) => {
        if (res.ok && res.data) {
          const items = res.data.items ?? res.data as unknown as KbioSessionData[];
          setSessions(Array.isArray(items) ? items : []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all"
    ? sessions
    : sessions.filter((s) => s.status === filter);

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
        {paginated.length === 0 ? (
          <div className="px-6 py-10 text-center text-foreground-muted text-sm">
            No sessions found. Start the demo site to generate behavioral data.
          </div>
        ) : (
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
        )}
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
