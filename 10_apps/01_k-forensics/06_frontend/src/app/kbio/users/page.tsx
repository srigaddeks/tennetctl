"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Fingerprint } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { truncateId, baselineQualityVariant } from "@/lib/kbio-utils";
import type { KbioUserProfileData } from "@/types/api";

const MOCK_USERS: KbioUserProfileData[] = [
  { user_hash: "usr_h4sh_001_abc", baseline_quality: "strong", profile_maturity: 0.95, total_sessions: 87, total_events: 124500, last_seen_at: "2026-04-09T14:32:00Z", centroids: [], credential_profiles: 3, device_count: 2 },
  { user_hash: "usr_h4sh_002_def", baseline_quality: "established", profile_maturity: 0.72, total_sessions: 45, total_events: 67200, last_seen_at: "2026-04-09T14:28:00Z", centroids: [], credential_profiles: 2, device_count: 3 },
  { user_hash: "usr_h4sh_003_ghi", baseline_quality: "forming", profile_maturity: 0.35, total_sessions: 12, total_events: 8400, last_seen_at: "2026-04-09T12:45:00Z", centroids: [], credential_profiles: 1, device_count: 1 },
  { user_hash: "usr_h4sh_004_jkl", baseline_quality: "strong", profile_maturity: 0.98, total_sessions: 156, total_events: 289000, last_seen_at: "2026-04-09T14:30:00Z", centroids: [], credential_profiles: 4, device_count: 3 },
  { user_hash: "usr_h4sh_005_mno", baseline_quality: "insufficient", profile_maturity: 0.08, total_sessions: 2, total_events: 340, last_seen_at: "2026-04-09T10:12:00Z", centroids: [], credential_profiles: 1, device_count: 1 },
  { user_hash: "usr_h4sh_006_pqr", baseline_quality: "strong", profile_maturity: 0.91, total_sessions: 103, total_events: 198000, last_seen_at: "2026-04-09T14:25:00Z", centroids: [], credential_profiles: 3, device_count: 2 },
  { user_hash: "usr_h4sh_007_stu", baseline_quality: "established", profile_maturity: 0.68, total_sessions: 38, total_events: 52100, last_seen_at: "2026-04-09T14:20:00Z", centroids: [], credential_profiles: 2, device_count: 2 },
  { user_hash: "usr_h4sh_008_vwx", baseline_quality: "forming", profile_maturity: 0.28, total_sessions: 9, total_events: 5600, last_seen_at: "2026-04-09T11:30:00Z", centroids: [], credential_profiles: 1, device_count: 1 },
  { user_hash: "usr_h4sh_009_yza", baseline_quality: "strong", profile_maturity: 0.88, total_sessions: 92, total_events: 167000, last_seen_at: "2026-04-09T14:18:00Z", centroids: [], credential_profiles: 3, device_count: 2 },
  { user_hash: "usr_h4sh_010_bcd", baseline_quality: "established", profile_maturity: 0.55, total_sessions: 28, total_events: 31200, last_seen_at: "2026-04-09T14:15:00Z", centroids: [], credential_profiles: 2, device_count: 3 },
];

const PAGE_SIZE = 10;

export default function KbioUsersPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  const totalPages = Math.ceil(MOCK_USERS.length / PAGE_SIZE);
  const paginated = MOCK_USERS.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

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
        <h1 className="text-2xl font-bold tracking-tight">User Profiles</h1>
        <p className="text-xs text-foreground-muted mt-1">
          Behavioral biometrics profiles for tracked users
        </p>
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint size={14} className="text-foreground-muted" />
            User Profiles
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User Hash</TableHead>
              <TableHead>Baseline Quality</TableHead>
              <TableHead>Sessions</TableHead>
              <TableHead>Profile Maturity</TableHead>
              <TableHead>Devices</TableHead>
              <TableHead>Last Seen</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginated.map((u) => (
              <TableRow
                key={u.user_hash}
                className="cursor-pointer"
                onClick={() => router.push(`/kbio/users/${u.user_hash}`)}
              >
                <TableCell>
                  <span className="font-mono text-xs">{truncateId(u.user_hash, 14)}</span>
                </TableCell>
                <TableCell>
                  <Badge variant={baselineQualityVariant(u.baseline_quality)}>
                    {u.baseline_quality}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {u.total_sessions}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 w-16 rounded-full bg-surface-3 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-foreground transition-all"
                        style={{ width: `${(u.profile_maturity * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="text-xs text-foreground-muted">
                      {(u.profile_maturity * 100).toFixed(0)}%
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {u.device_count}
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {new Date(u.last_seen_at).toLocaleString()}
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
