"use client";

import Link from "next/link";
import { use } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge, ErrorState, Skeleton } from "@/components/ui";
import { useCampaign } from "@/features/notify/hooks/use-campaigns";
import { useCampaignStats } from "@/features/notify/hooks/use-deliveries";
import type { CampaignStatusCode } from "@/types/api";

function statusTone(
  code: CampaignStatusCode,
): "zinc" | "blue" | "emerald" | "amber" | "red" | "purple" {
  switch (code) {
    case "draft":      return "zinc";
    case "scheduled":  return "blue";
    case "running":    return "amber";
    case "paused":     return "purple";
    case "completed":  return "emerald";
    case "cancelled":  return "zinc";
    case "failed":     return "red";
  }
}

function StatCard({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-700 dark:bg-zinc-900">
      <p className="text-xs text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value.toLocaleString()}</p>
      {sub && <p className="mt-0.5 text-xs text-zinc-400">{sub}</p>}
    </div>
  );
}

function pct(num: number, denom: number): string {
  if (!denom) return "–";
  return `${((num / denom) * 100).toFixed(1)}%`;
}

export default function CampaignDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const { data: campaign, isLoading: loadingCampaign, isError: campaignError, error: campaignErr } =
    useCampaign(id);
  const { data: stats, isLoading: loadingStats } = useCampaignStats(id);

  const byStatus = stats?.by_status ?? {};
  const total    = stats?.total ?? 0;
  const sent      = (byStatus["sent"] ?? 0) + (byStatus["delivered"] ?? 0) +
                    (byStatus["opened"] ?? 0) + (byStatus["clicked"] ?? 0);
  const delivered = byStatus["delivered"] ?? 0;
  const opened    = byStatus["opened"] ?? 0;
  const clicked   = byStatus["clicked"] ?? 0;
  const bounced   = byStatus["bounced"] ?? 0;
  const failed    = byStatus["failed"] ?? 0;

  return (
    <>
      <PageHeader
        title={campaign?.name ?? "Campaign"}
        description={
          campaign
            ? `Channel: ${campaign.channel_label} · Throttle: ${campaign.throttle_per_minute}/min`
            : "Loading campaign details…"
        }
        testId="heading-campaign-detail"
        actions={
          <Link
            href="/notify/campaigns"
            className="text-sm text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
            data-testid="back-to-campaigns"
          >
            ← Back to campaigns
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="campaign-detail-body">
        {loadingCampaign && <Skeleton className="mb-4 h-8 w-64" />}
        {campaignError && <ErrorState message={(campaignErr as Error).message} />}

        {campaign && (
          <div className="mb-6 flex items-center gap-3">
            <Badge tone={statusTone(campaign.status_code)}>{campaign.status_label}</Badge>
            {campaign.scheduled_at && (
              <span className="text-sm text-zinc-500">
                Scheduled: {new Date(campaign.scheduled_at).toLocaleString()}
              </span>
            )}
          </div>
        )}

        {/* Stats */}
        <h2 className="mb-3 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          Delivery stats
        </h2>
        {loadingStats && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
        )}
        {!loadingStats && (
          <div
            className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6"
            data-testid="campaign-stats"
          >
            <StatCard label="Total" value={total} />
            <StatCard label="Sent" value={sent} sub={pct(sent, total)} />
            <StatCard label="Delivered" value={delivered} sub={pct(delivered, sent)} />
            <StatCard label="Opened" value={opened} sub={pct(opened, delivered)} />
            <StatCard label="Clicked" value={clicked} sub={pct(clicked, opened)} />
            <StatCard label="Bounced / Failed" value={bounced + failed} sub={pct(bounced + failed, sent)} />
          </div>
        )}

        {/* Raw by-status breakdown */}
        {!loadingStats && total > 0 && (
          <div className="mt-8">
            <h2 className="mb-3 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
              Breakdown by status
            </h2>
            <div className="flex flex-wrap gap-2">
              {Object.entries(byStatus).map(([code, cnt]) => (
                <div
                  key={code}
                  className="rounded border border-zinc-200 bg-zinc-50 px-3 py-1 text-xs dark:border-zinc-700 dark:bg-zinc-900"
                >
                  <span className="font-medium capitalize">{code}</span>
                  <span className="ml-2 tabular-nums text-zinc-500">{cnt}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
