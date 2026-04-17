"use client";

import { useState } from "react";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  useCampaigns,
  useCreateCampaign,
  useDeleteCampaign,
  useUpdateCampaign,
} from "@/features/notify/hooks/use-campaigns";
import { useTemplates } from "@/features/notify/hooks/use-templates";
import type { Campaign, CampaignStatusCode, NotifyChannelCode } from "@/types/api";

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

function CampaignActions({
  campaign,
  orgId,
}: {
  campaign: Campaign;
  orgId: string | null;
}) {
  const update = useUpdateCampaign(orgId);
  const del    = useDeleteCampaign(orgId);
  const [confirming, setConfirming] = useState(false);

  const canCancel  = campaign.status_code === "scheduled" || campaign.status_code === "draft";
  const canDelete  = campaign.status_code !== "running";

  return (
    <div className="flex items-center justify-end gap-2">
      {canCancel && campaign.status_code !== "cancelled" && (
        <button
          type="button"
          className="text-xs text-zinc-500 underline hover:text-zinc-700 dark:hover:text-zinc-300"
          disabled={update.isPending}
          onClick={() =>
            update.mutate({ id: campaign.id, patch: { status: "cancelled" } })
          }
        >
          Cancel
        </button>
      )}
      {canDelete && (
        <>
          {confirming ? (
            <span className="flex items-center gap-1 text-xs">
              <button
                type="button"
                className="font-medium text-red-600 underline hover:text-red-800"
                disabled={del.isPending}
                onClick={() => {
                  del.mutate(campaign.id);
                  setConfirming(false);
                }}
              >
                Confirm delete
              </button>
              <button
                type="button"
                className="text-zinc-400"
                onClick={() => setConfirming(false)}
              >
                ×
              </button>
            </span>
          ) : (
            <button
              type="button"
              className="text-xs text-red-500 underline hover:text-red-700"
              onClick={() => setConfirming(true)}
            >
              Delete
            </button>
          )}
        </>
      )}
    </div>
  );
}

function NewCampaignDialog({
  open,
  onClose,
  orgId,
}: {
  open: boolean;
  onClose: () => void;
  orgId: string;
}) {
  const templates = useTemplates(orgId);
  const create = useCreateCampaign(orgId);
  const [form, setForm] = useState({
    name: "",
    template_id: "",
    channel_code: "email" as NotifyChannelCode,
    scheduled_at: "",
    throttle_per_minute: 60,
  });
  const [err, setErr] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setErr(null);
    if (!form.name || !form.template_id) {
      setErr("Name and template are required.");
      return;
    }
    create.mutate(
      {
        org_id: orgId,
        name: form.name,
        template_id: form.template_id,
        channel_code: form.channel_code,
        scheduled_at: form.scheduled_at || null,
        throttle_per_minute: form.throttle_per_minute,
      },
      {
        onSuccess: () => onClose(),
        onError: (e) => setErr(e.message),
      },
    );
  }

  return (
    <Modal open={open} onClose={onClose} title="New Campaign" size="md">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <Field label="Name" htmlFor="camp-name">
          <Input
            id="camp-name"
            data-testid="input-campaign-name"
            placeholder="e.g. April newsletter"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
        </Field>
        <Field label="Template" htmlFor="camp-template">
          <Select
            id="camp-template"
            data-testid="select-campaign-template"
            value={form.template_id}
            onChange={(e) => setForm((f) => ({ ...f, template_id: e.target.value }))}
          >
            <option value="">Select a template…</option>
            {(templates.data?.items ?? []).map((t) => (
              <option key={t.id} value={t.id}>
                {t.key} — {t.subject}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Channel" htmlFor="camp-channel">
          <Select
            id="camp-channel"
            value={form.channel_code}
            onChange={(e) => setForm((f) => ({ ...f, channel_code: e.target.value as NotifyChannelCode }))}
          >
            <option value="email">Email</option>
            <option value="webpush">Web Push</option>
            <option value="in_app">In-app</option>
          </Select>
        </Field>
        <Field label="Schedule (optional)" htmlFor="camp-scheduled" hint="Leave blank to save as draft">
          <Input
            id="camp-scheduled"
            type="datetime-local"
            value={form.scheduled_at}
            onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))}
          />
        </Field>
        <Field label="Throttle (per min)" htmlFor="camp-throttle">
          <Input
            id="camp-throttle"
            type="number"
            min={1}
            max={1000}
            value={form.throttle_per_minute}
            onChange={(e) => setForm((f) => ({ ...f, throttle_per_minute: Number(e.target.value) }))}
          />
        </Field>
        {err && <p className="text-xs text-red-500">{err}</p>}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            data-testid="btn-create-campaign"
            disabled={create.isPending || templates.isLoading}
          >
            {create.isPending ? "Creating…" : "Create campaign"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export default function CampaignsPage() {
  const me = useMe();
  const session = me.data?.session ?? null;
  const orgId = session?.org_id ?? null;

  const { data, isLoading, isError, error, refetch } = useCampaigns(orgId);
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <PageHeader
        title="Campaigns"
        description="Broadcast notifications to a filtered audience on a schedule. Draft → schedule → run. Critical templates fan out across all channels."
        testId="heading-notify-campaigns"
        actions={
          <Button
            data-testid="btn-new-campaign"
            onClick={() => setDialogOpen(true)}
          >
            + New campaign
          </Button>
        }
      />

      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="notify-campaigns-body"
      >
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        )}

        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {data && data.items.length === 0 && (
          <EmptyState
            title="No campaigns yet"
            description="Create a campaign to broadcast a template to your org users on a schedule."
          />
        )}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Name</TH>
                <TH>Channel</TH>
                <TH>Status</TH>
                <TH>Scheduled</TH>
                <TH>Throttle</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((c) => (
                <TR key={c.id}>
                  <TD>
                    <span
                      className="font-medium text-zinc-900 dark:text-zinc-50"
                      data-testid={`campaign-row-${c.id}`}
                    >
                      {c.name}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone="zinc">{c.channel_label}</Badge>
                  </TD>
                  <TD>
                    <Badge tone={statusTone(c.status_code)}>{c.status_label}</Badge>
                  </TD>
                  <TD>
                    {c.scheduled_at ? (
                      <span className="text-xs text-zinc-600 dark:text-zinc-400">
                        {c.scheduled_at.slice(0, 16).replace("T", " ")}
                      </span>
                    ) : (
                      <span className="text-zinc-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
                      {c.throttle_per_minute}/min
                    </span>
                  </TD>
                  <TD className="text-right">
                    <CampaignActions campaign={c} orgId={orgId} />
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      {orgId && (
        <NewCampaignDialog
          open={dialogOpen}
          onClose={() => setDialogOpen(false)}
          orgId={orgId}
        />
      )}
    </>
  );
}
