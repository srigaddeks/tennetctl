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
import { baselineQualityVariant } from "@/lib/kbio-utils";
import { getKbioProfile } from "@/lib/api";
import type { KbioUserProfileData } from "@/types/api";

export default function UserDetailPage() {
  const params = useParams<{ hash: string }>();
  const router = useRouter();
  const [loading, setLoading] = React.useState(true);
  const [profile, setProfile] = React.useState<KbioUserProfileData | null>(null);

  React.useEffect(() => {
    if (!params.hash) return;
    getKbioProfile(params.hash)
      .then((res) => {
        if (res.ok && res.data) setProfile(res.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [params.hash]);

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

  if (!profile) {
    return (
      <div className="px-8 py-8 max-w-[1100px]">
        <Button variant="ghost" size="sm" className="mb-4 -ml-2" onClick={() => router.push("/kbio/users")}>
          <ArrowLeft size={14} /> Back to Users
        </Button>
        <div className="text-center py-10 text-foreground-muted text-sm">
          Profile not found for {params.hash}. It may not have been created yet.
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

      {profile.centroids.length > 0 && (
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
      )}
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
