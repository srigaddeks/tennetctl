"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui";
import {
  useCreateReferral,
  useDeleteReferral,
  useReferrals,
} from "@/features/product-ops/hooks/use-referrals";

export default function ReferralsPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [showForm, setShowForm] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = useReferrals(workspaceId);
  const del = useDeleteReferral();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Referrals"
        description="Codes that attach a referrer to incoming visitors. Auto-emit utm_source=referral so referrals show in standard UTM funnels."
        actions={
          <Button variant="primary" onClick={() => setShowForm((v) => !v)} data-testid="referrals-new-toggle">
            {showForm ? "Cancel" : "New code"}
          </Button>
        }
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view referrals."
        />
      )}

      {workspaceId && showForm && (
        <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />
      )}

      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed to load referrals"}
          retry={() => {
            void list.refetch();
          }}
        />
      )}

      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState
          title="No referral codes yet"
          description="Create one above to start tracking acquisition."
        />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Code</TH>
                <TH>Referrer</TH>
                <TH>Conversions</TH>
                <TH>Value (¢)</TH>
                <TH>Status</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map((r) => (
                <TR key={r.id} data-testid={`referral-row-${r.id}`}>
                  <TD>
                    <code className="text-xs">{r.code}</code>
                  </TD>
                  <TD>
                    <code className="text-xs">{r.referrer_user_id.slice(0, 8)}…</code>
                  </TD>
                  <TD>{r.conversion_count.toLocaleString()}</TD>
                  <TD>{r.conversion_value_cents_total.toLocaleString()}</TD>
                  <TD>{r.is_active ? <Badge tone="emerald">active</Badge> : <Badge tone="zinc">inactive</Badge>}</TD>
                  <TD>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete referral code ${r.code}?`)) del.mutate(r.id);
                      }}
                      data-testid={`referral-delete-${r.code}`}
                    >
                      Delete
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function CreateForm({ workspaceId, onDone }: { workspaceId: string; onDone: () => void }) {
  const create = useCreateReferral();
  const [code, setCode] = useState<string>("");
  const [referrerUserId, setReferrerUserId] = useState<string>("");
  const [rewardJson, setRewardJson] = useState<string>("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let reward: Record<string, unknown> = {};
    if (rewardJson.trim()) {
      try {
        reward = JSON.parse(rewardJson) as Record<string, unknown>;
      } catch {
        alert("reward_config must be valid JSON or empty");
        return;
      }
    }
    await create.mutateAsync({
      code,
      referrer_user_id: referrerUserId,
      workspace_id: workspaceId,
      reward_config: reward,
    });
    setCode("");
    setReferrerUserId("");
    setRewardJson("");
    onDone();
  };

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
      data-testid="referral-create-form"
    >
      <div className="grid grid-cols-2 gap-4">
        <Field label="Code" required htmlFor="ref-code">
          <Input
            id="ref-code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            required
            placeholder="alice123"
          />
        </Field>
        <Field label="Referrer User ID" required htmlFor="ref-user">
          <Input
            id="ref-user"
            value={referrerUserId}
            onChange={(e) => setReferrerUserId(e.target.value)}
            required
            placeholder="usr_…"
          />
        </Field>
      </div>
      <Field label="Reward config (JSON, optional)" htmlFor="ref-reward">
        <Input
          id="ref-reward"
          value={rewardJson}
          onChange={(e) => setRewardJson(e.target.value)}
          placeholder='{"kind":"credit","amount_cents":1000}'
        />
      </Field>
      {create.isError && (
        <p className="text-sm text-red-600">
          {create.error instanceof Error ? create.error.message : "Create failed"}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" variant="primary" disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </div>
    </form>
  );
}
