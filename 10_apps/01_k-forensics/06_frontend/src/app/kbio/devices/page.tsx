"use client";

import * as React from "react";
import { Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { truncateId } from "@/lib/kbio-utils";
import type { KbioDeviceData } from "@/types/api";

const MOCK_DEVICES: KbioDeviceData[] = [
  { device_uuid: "dev-uuid-001-abcdef-123456", fingerprint_hash: "fp_a1b2c3d4e5f6", user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0", platform: "Windows", trust_status: "trusted", first_seen_at: "2026-02-15T10:00:00Z", last_seen_at: "2026-04-09T14:32:00Z", session_count: 87 },
  { device_uuid: "dev-uuid-002-ghijkl-789012", fingerprint_hash: "fp_b2c3d4e5f6a7", user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) Safari/17.4", platform: "macOS", trust_status: "trusted", first_seen_at: "2026-03-01T14:00:00Z", last_seen_at: "2026-04-09T14:28:00Z", session_count: 45 },
  { device_uuid: "dev-uuid-003-mnopqr-345678", fingerprint_hash: "fp_c3d4e5f6a7b8", user_agent: "Mozilla/5.0 (Linux; Android 14) Chrome/124.0 Mobile", platform: "Android", trust_status: "untrusted", first_seen_at: "2026-04-01T09:00:00Z", last_seen_at: "2026-04-09T12:45:00Z", session_count: 12 },
  { device_uuid: "dev-uuid-004-stuvwx-901234", fingerprint_hash: "fp_d4e5f6a7b8c9", user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/125.0", platform: "Windows", trust_status: "trusted", first_seen_at: "2026-01-10T08:00:00Z", last_seen_at: "2026-04-09T14:30:00Z", session_count: 156 },
  { device_uuid: "dev-uuid-005-yzabcd-567890", fingerprint_hash: "fp_e5f6a7b8c9d0", user_agent: "Mozilla/5.0 (Linux; Android 14) Chrome/124.0 Mobile", platform: "Android", trust_status: "blocked", first_seen_at: "2026-04-09T10:00:00Z", last_seen_at: "2026-04-09T10:12:00Z", session_count: 2 },
  { device_uuid: "dev-uuid-006-efghij-123456", fingerprint_hash: "fp_f6a7b8c9d0e1", user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) Chrome/124.0", platform: "macOS", trust_status: "trusted", first_seen_at: "2026-02-20T16:00:00Z", last_seen_at: "2026-04-09T14:25:00Z", session_count: 103 },
  { device_uuid: "dev-uuid-007-klmnop-789012", fingerprint_hash: "fp_a7b8c9d0e1f2", user_agent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) Safari/604.1", platform: "iOS", trust_status: "trusted", first_seen_at: "2026-03-10T12:00:00Z", last_seen_at: "2026-04-09T14:20:00Z", session_count: 38 },
  { device_uuid: "dev-uuid-008-qrstuv-345678", fingerprint_hash: "fp_b8c9d0e1f2a3", user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/124.0", platform: "Windows", trust_status: "untrusted", first_seen_at: "2026-04-05T06:00:00Z", last_seen_at: "2026-04-09T11:30:00Z", session_count: 9 },
];

function trustStatusVariant(status: string): "success" | "warning" | "danger" | "default" {
  switch (status) {
    case "trusted": return "success";
    case "untrusted": return "warning";
    case "blocked": return "danger";
    default: return "default";
  }
}

const PAGE_SIZE = 10;

export default function KbioDevicesPage() {
  const [loading, setLoading] = React.useState(true);
  const [page, setPage] = React.useState(0);
  const [expanded, setExpanded] = React.useState<string | null>(null);

  React.useEffect(() => {
    const t = setTimeout(() => setLoading(false), 300);
    return () => clearTimeout(t);
  }, []);

  const totalPages = Math.ceil(MOCK_DEVICES.length / PAGE_SIZE);
  const paginated = MOCK_DEVICES.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

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
        <h1 className="text-2xl font-bold tracking-tight">Device Registry</h1>
        <p className="text-xs text-foreground-muted mt-1">
          All devices observed in behavioral biometrics sessions
        </p>
      </div>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={14} className="text-foreground-muted" />
            Devices
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device UUID</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Trust Status</TableHead>
              <TableHead>Sessions</TableHead>
              <TableHead>First Seen</TableHead>
              <TableHead>Last Seen</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginated.map((d) => (
              <React.Fragment key={d.device_uuid}>
                <TableRow
                  className="cursor-pointer"
                  onClick={() => setExpanded(expanded === d.device_uuid ? null : d.device_uuid)}
                >
                  <TableCell>
                    <span className="font-mono text-xs">{truncateId(d.device_uuid, 16)}</span>
                  </TableCell>
                  <TableCell className="text-xs">{d.platform}</TableCell>
                  <TableCell>
                    <Badge variant={trustStatusVariant(d.trust_status)}>
                      {d.trust_status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-foreground-muted">
                    {d.session_count}
                  </TableCell>
                  <TableCell className="text-xs text-foreground-muted">
                    {new Date(d.first_seen_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-xs text-foreground-muted">
                    {new Date(d.last_seen_at).toLocaleString()}
                  </TableCell>
                </TableRow>
                {expanded === d.device_uuid && (
                  <TableRow>
                    <TableCell colSpan={6} className="bg-surface-2">
                      <DeviceDetail device={d} />
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
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

function DeviceDetail({ device }: { device: KbioDeviceData }) {
  return (
    <Card className="border-0 shadow-none bg-transparent">
      <CardContent className="p-3">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-x-6 gap-y-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Device UUID</span>
            <span className="text-xs font-mono break-all">{device.device_uuid}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Fingerprint Hash</span>
            <span className="text-xs font-mono break-all">{device.fingerprint_hash}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">User Agent</span>
            <span className="text-xs break-all">{device.user_agent}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Platform</span>
            <span className="text-xs">{device.platform}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Trust Status</span>
            <Badge variant={trustStatusVariant(device.trust_status)} className="w-fit">
              {device.trust_status}
            </Badge>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Session Count</span>
            <span className="text-xs">{device.session_count}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">First Seen</span>
            <span className="text-xs">{new Date(device.first_seen_at).toLocaleString()}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Last Seen</span>
            <span className="text-xs">{new Date(device.last_seen_at).toLocaleString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
