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
import { listKbioDevices } from "@/lib/api";
import type { KbioDeviceData } from "@/types/api";

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
  const [devices, setDevices] = React.useState<KbioDeviceData[]>([]);
  const [page, setPage] = React.useState(0);
  const [expanded, setExpanded] = React.useState<string | null>(null);

  React.useEffect(() => {
    listKbioDevices({ limit: 100 })
      .then((res) => {
        if (res.ok && res.data) {
          const items = res.data.items ?? res.data as unknown as KbioDeviceData[];
          setDevices(Array.isArray(items) ? items : []);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const totalPages = Math.ceil(devices.length / PAGE_SIZE);
  const paginated = devices.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

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
        {paginated.length === 0 ? (
          <div className="px-6 py-10 text-center text-foreground-muted text-sm">
            No devices found. Start the demo site to generate device data.
          </div>
        ) : (
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
            <span className="text-[10px] uppercase tracking-wider text-foreground-muted font-semibold">Session Count</span>
            <span className="text-xs">{device.session_count}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
