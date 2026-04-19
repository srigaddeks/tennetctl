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
  Select,
  Skeleton,
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui";
import {
  useCreatePromo,
  useDeletePromo,
  usePromos,
} from "@/features/product-ops/hooks/use-promos";
import type { PromoStatus } from "@/types/api";

const STATUS_TONE: Record<PromoStatus, "emerald" | "blue" | "red" | "zinc" | "amber"> = {
  active: "emerald",
  scheduled: "blue",
  expired: "red",
  inactive: "zinc",
  exhausted: "amber",
};

export default function PromosPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState<PromoStatus | "">("");
  const [showForm, setShowForm] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = usePromos(workspaceId, statusFilter || undefined);
  const del = useDeletePromo();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Promo Codes"
        description="Coupon codes with usage caps + expiry. Distinct from Referrals (which credit a referrer); promos discount the redeemer."
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as PromoStatus | "")}
              data-testid="promos-status-filter"
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="scheduled">Scheduled</option>
              <option value="expired">Expired</option>
              <option value="exhausted">Exhausted</option>
              <option value="inactive">Inactive</option>
            </Select>
            <Button variant="primary" onClick={() => setShowForm((v) => !v)} data-testid="promos-new-toggle">
              {showForm ? "Cancel" : "New promo"}
            </Button>
          </div>
        }
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view promos."
        />
      )}

      {workspaceId && showForm && (
        <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />
      )}

      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed to load promos"}
          retry={() => {
            void list.refetch();
          }}
        />
      )}

      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState
          title="No promo codes match"
          description="Create one above or clear the status filter."
        />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Code</TH>
                <TH>Reward</TH>
                <TH>Status</TH>
                <TH>Redemptions</TH>
                <TH>Cap</TH>
                <TH>Expires</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map((p) => (
                <TR key={p.id} data-testid={`promo-row-${p.id}`}>
                  <TD>
                    <code className="text-xs">{p.code}</code>
                  </TD>
                  <TD className="text-xs">
                    <Badge tone="blue">{p.redemption_kind}</Badge>{" "}
                    <span className="text-zinc-500">
                      {JSON.stringify(p.redemption_config)}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone={STATUS_TONE[p.status]}>{p.status}</Badge>
                  </TD>
                  <TD>
                    {p.redemption_count.toLocaleString()}
                    {p.rejection_count > 0 && (
                      <span className="ml-2 text-xs text-zinc-500">({p.rejection_count} rejected)</span>
                    )}
                  </TD>
                  <TD className="text-xs">{p.max_total_uses ?? "∞"}</TD>
                  <TD className="text-xs">{p.ends_at ?? "—"}</TD>
                  <TD>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete promo ${p.code}?`)) del.mutate(p.id);
                      }}
                      data-testid={`promo-delete-${p.code}`}
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
  const create = useCreatePromo();
  const [code, setCode] = useState<string>("");
  const [kind, setKind] = useState<"discount_pct" | "discount_cents" | "free_trial_days" | "custom">("discount_pct");
  const [value, setValue] = useState<string>("20");
  const [maxTotal, setMaxTotal] = useState<string>("");
  const [maxPer, setMaxPer] = useState<string>("1");
  const [endsAt, setEndsAt] = useState<string>("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const config: Record<string, unknown> =
      kind === "discount_pct" ? { value: Number(value) }
      : kind === "discount_cents" ? { amount_cents: Number(value) }
      : kind === "free_trial_days" ? { days: Number(value) }
      : (value ? JSON.parse(value) : {});

    await create.mutateAsync({
      code,
      workspace_id: workspaceId,
      redemption_kind: kind,
      redemption_config: config,
      max_total_uses: maxTotal ? Number(maxTotal) : null,
      max_uses_per_visitor: Number(maxPer || 1),
      ends_at: endsAt || null,
    });
    setCode("");
    setValue("20");
    setMaxTotal("");
    setMaxPer("1");
    setEndsAt("");
    onDone();
  };

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
      data-testid="promo-create-form"
    >
      <div className="grid grid-cols-3 gap-4">
        <Field label="Code" required htmlFor="promo-code">
          <Input id="promo-code" value={code} onChange={(e) => setCode(e.target.value)} required placeholder="LAUNCH20" />
        </Field>
        <Field label="Kind" htmlFor="promo-kind">
          <Select id="promo-kind" value={kind} onChange={(e) => setKind(e.target.value as typeof kind)}>
            <option value="discount_pct">Discount %</option>
            <option value="discount_cents">Discount (cents)</option>
            <option value="free_trial_days">Free trial days</option>
            <option value="custom">Custom (JSON)</option>
          </Select>
        </Field>
        <Field
          label={
            kind === "discount_pct" ? "% off"
            : kind === "discount_cents" ? "Cents off"
            : kind === "free_trial_days" ? "Days"
            : "Custom JSON"
          }
          htmlFor="promo-value"
        >
          <Input
            id="promo-value"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={kind === "custom" ? '{"foo":"bar"}' : "20"}
          />
        </Field>
        <Field label="Max total uses (blank = ∞)" htmlFor="promo-maxtotal">
          <Input id="promo-maxtotal" type="number" value={maxTotal} onChange={(e) => setMaxTotal(e.target.value)} placeholder="100" />
        </Field>
        <Field label="Max uses per visitor" htmlFor="promo-maxper">
          <Input id="promo-maxper" type="number" min={1} value={maxPer} onChange={(e) => setMaxPer(e.target.value)} />
        </Field>
        <Field label="Ends at (ISO 8601, optional)" htmlFor="promo-ends">
          <Input id="promo-ends" type="datetime-local" value={endsAt} onChange={(e) => setEndsAt(e.target.value)} />
        </Field>
      </div>
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
