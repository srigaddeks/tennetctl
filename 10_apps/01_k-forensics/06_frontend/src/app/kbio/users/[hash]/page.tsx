"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Fingerprint } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { baselineQualityVariant, truncateId } from "@/lib/kbio-utils";
import type { KbioUserProfileData, KbioCentroidData } from "@/types/api";

const MOCK_CENTROIDS: KbioCentroidData[] = [
  { id: "cen-001", modality: "keystroke", platform: "windows", input_method: "physical_keyboard", weight: 0.35, sample_count: 4820, created_at: "2026-03-01T10:00:00Z" },
  { id: "cen-002", modality: "mouse", platform: "windows", input_method: "optical_mouse", weight: 0.25, sample_count: 8120, created_at: "2026-03-01T10:00:00Z" },
  { id: "cen-003", modality: "touch", platform: "android", input_method: "capacitive_touch", weight: 0.20, sample_count: 2340, created_at: "2026-03-15T08:00:00Z" },
  { id: "cen-004", modality: "scroll", platform: "windows", input_method: "scroll_wheel", weight: 0.10, sample_count: 1560, created_at: "2026-03-01T10:00:00Z" },
  { id: "cen-005", modality: "accelerometer", platform: "android", input_method: "device_sensor", weight: 0.10, sample_count: 980, created_at: "2026-03-15T08:00:00Z" },
];

const MOCK_PROFILE: KbioUserProfileData = {
  user_hash: "usr_h4sh_001_abc",
  baseline_quality: "strong",
  profile_maturity: 0.95,
  total_sessions: 87,
  total_events: 124500,
  last_seen_at: "2026-04-09T14:32:00Z",
  centroids: MOCK_CENTROIDS,
  credential_profiles: 3,
  device_count: 2,
};

const MOCK_DEVICES = [
  { device_uuid: "dev-uuid-001-abcdef", platform: "Windows 11", trust_status: "trusted", last_seen_at: "2026-04-09T14:32:00Z" },
  { device_uuid: "dev-uuid-005-ghijkl", platform: "Android 14", trust_status: "trusted", last_seen_at: "2026-04-08T18:45:00Z" },
];

export default function UserDetailPage() {
  const params = useParams<{ hash: string }>();
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);

  const profile = { ...MOCK_PROFILE, user_hash: params.hash ?? MOCK_PROFILE.user_hash };

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
        <Skeleton className="h-40 rounded-md mb-8" />
        <Skeleton className="h-60 rounded-md" />
      </div>
    );
  }

  return (
    <div className="px-8 py-8 max-w-[1100px]">
      <Button
        variant="ghost"
        size="sm"
        className="mb-4 -ml-2"
        onClick={() => router.push("/kbio/users")}
      >
        <ArrowLeft size={14} /> Back to Users
      </Button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">User Profile</h1>
        <p className="text-xs text-foreground-muted mt-1 font-mono">
          {profile.user_hash}
        </p>
      </div>

      {/* Profile overview */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint size={14} className="text-foreground-muted" />
            Profile Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-x-6 gap-y-4">
            <MetaField label="User Hash" value={profile.user_hash} mono />
            <MetaField label="Baseline Quality">
              <Badge variant={baselineQualityVariant(profile.baseline_quality)}>
                {profile.baseline_quality}
              </Badge>
            </MetaField>
            <MetaField label="Profile Maturity">
              <div className="flex items-center gap-2 mt-0.5">
                <div className="h-1.5 w-20 rounded-full bg-surface-3 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-foreground transition-all"
                    style={{ width: `${(profile.profile_maturity * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-xs text-foreground-muted">
                  {(profile.profile_maturity * 100).toFixed(0)}%
                </span>
              </div>
            </MetaField>
            <MetaField label="Total Sessions" value={String(profile.total_sessions)} />
            <MetaField label="Total Events" value={profile.total_events.toLocaleString()} />
            <MetaField label="Credential Profiles" value={String(profile.credential_profiles)} />
            <MetaField label="Device Count" value={String(profile.device_count)} />
            <MetaField label="Last Seen" value={new Date(profile.last_seen_at).toLocaleString()} />
          </div>
        </CardContent>
      </Card>

      {/* Centroids table */}
      <Card className="mb-8 overflow-hidden">
        <CardHeader>
          <CardTitle>Behavioral Centroids</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Modality</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Input Method</TableHead>
              <TableHead>Weight</TableHead>
              <TableHead>Samples</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {profile.centroids.map((c) => (
              <TableRow key={c.id}>
                <TableCell className="font-medium capitalize">{c.modality}</TableCell>
                <TableCell className="text-xs text-foreground-muted capitalize">{c.platform}</TableCell>
                <TableCell className="text-xs text-foreground-muted">{c.input_method.replace(/_/g, " ")}</TableCell>
                <TableCell className="text-xs font-mono">{(c.weight * 100).toFixed(0)}%</TableCell>
                <TableCell className="text-xs text-foreground-muted">{c.sample_count.toLocaleString()}</TableCell>
                <TableCell className="text-xs text-foreground-muted">{new Date(c.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {/* Linked devices */}
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle>Linked Devices</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Device UUID</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Trust Status</TableHead>
              <TableHead>Last Seen</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {MOCK_DEVICES.map((d) => (
              <TableRow
                key={d.device_uuid}
                className="cursor-pointer"
                onClick={() => router.push(`/kbio/devices`)}
              >
                <TableCell>
                  <span className="font-mono text-xs">{truncateId(d.device_uuid, 16)}</span>
                </TableCell>
                <TableCell className="text-xs">{d.platform}</TableCell>
                <TableCell>
                  <Badge variant={d.trust_status === "trusted" ? "success" : "warning"}>
                    {d.trust_status}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-foreground-muted">
                  {new Date(d.last_seen_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
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
        <span className={`text-sm${mono ? " font-mono text-xs break-all" : ""}`}>
          {value}
        </span>
      )}
    </div>
  );
}
