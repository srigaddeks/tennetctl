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
import { listKbioSessions } from "@/lib/api";
import type { KbioUserProfileData, KbioSessionData } from "@/types/api";

const PAGE_SIZE = 10;

/** Derive user profiles from session data until a dedicated list-users endpoint exists. */
function deriveProfiles(sessions: KbioSessionData[]): KbioUserProfileData[] {
  const byUser = new Map<string, KbioSessionData[]>();
  for (const s of sessions) {
    const list = byUser.get(s.user_hash) ?? [];
    list.push(s);
    byUser.set(s.user_hash, list);
  }
  const profiles: KbioUserProfileData[] = [];
  for (const [hash, userSessions] of byUser) {
    const sorted = userSessions.sort((a, b) => new Date(b.last_active_at).getTime() - new Date(a.last_active_at).getTime());
    const devices = new Set(userSessions.map((s) => s.device_uuid));
    const bestQuality = userSessions.reduce((best, s) => {
      const order = ["strong", "established", "forming", "insufficient"];
      return order.indexOf(s.baseline_quality) < order.indexOf(best) ? s.baseline_quality : best;
    }, "insufficient" as string);
    profiles.push({
      user_hash: hash,
      baseline_quality: bestQuality as KbioUserProfileData["baseline_quality"],
      profile_maturity: Math.min(userSessions.length * 0.1, 1),
      total_sessions: userSessions.length,
      total_events: userSessions.reduce((a, s) => a + s.pulse_count * 50, 0),
      last_seen_at: sorted[0].last_active_at,
      centroids: [],
      credential_profiles: 1,
      device_count: devices.size,
    });
  }
  return profiles.sort((a, b) => new Date(b.last_seen_at).getTime() - new Date(a.last_seen_at).getTime());
}

export default function KbioUsersPage() {
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [users, setUsers] = React.useState<KbioUserProfileData[]>([]);
  const [page, setPage] = React.useState(0);

  React.useEffect(() => {
    listKbioSessions({ limit: 200 })
      .then((res) => {
        if (res.ok && res.data) {
          const items = res.data.items ?? res.data as unknown as KbioSessionData[];
          setUsers(deriveProfiles(Array.isArray(items) ? items : []));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalPages = Math.ceil(users.length / PAGE_SIZE);
  const paginated = users.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

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
        {paginated.length === 0 ? (
          <div className="px-6 py-10 text-center text-foreground-muted text-sm">
            No user profiles found. Start the demo site to generate behavioral data.
          </div>
        ) : (
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
        )}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-border">
            <span className="text-xs text-foreground-muted">
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
                Previous
              </Button>
              <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
