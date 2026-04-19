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
  useCreatePartner,
  useDeletePartner,
  usePartners,
} from "@/features/product-ops/hooks/use-partners";

const TIERS = [
  { id: 1, code: "standard", label: "Standard" },
  { id: 2, code: "silver", label: "Silver" },
  { id: 3, code: "gold", label: "Gold" },
  { id: 4, code: "platinum", label: "Platinum" },
];

const TIER_TONE: Record<string, "zinc" | "blue" | "amber" | "purple"> = {
  standard: "zinc",
  silver: "blue",
  gold: "amber",
  platinum: "purple",
};

function formatCents(cents: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(cents / 100);
}

export default function PartnersPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [tierFilter, setTierFilter] = useState<string>("");
  const [showForm, setShowForm] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = usePartners(workspaceId, tierFilter || undefined);
  const del = useDeletePartner();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Partners"
        description="B2B affiliate program. Tiered partners (standard / silver / gold / platinum) own referral + promo codes; payouts logged to evt_partner_payouts."
        actions={
          <div className="flex items-center gap-2">
            <Select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              data-testid="partners-tier-filter"
            >
              <option value="">All tiers</option>
              {TIERS.map((t) => (
                <option key={t.code} value={t.code}>{t.label}</option>
              ))}
            </Select>
            <Button variant="primary" onClick={() => setShowForm((v) => !v)} data-testid="partners-new-toggle">
              {showForm ? "Cancel" : "New partner"}
            </Button>
          </div>
        }
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view partners."
        />
      )}

      {workspaceId && showForm && (
        <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />
      )}

      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed to load partners"}
          retry={() => {
            void list.refetch();
          }}
        />
      )}

      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState
          title="No partners yet"
          description="Recruit your first partner above. Partners can own multiple referral + promo codes."
        />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Partner</TH>
                <TH>Tier</TH>
                <TH>Codes</TH>
                <TH>Conversions</TH>
                <TH>Conversion value</TH>
                <TH>Paid out</TH>
                <TH>Pending</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map((p) => (
                <TR key={p.id} data-testid={`partner-row-${p.id}`}>
                  <TD>
                    <div className="flex flex-col">
                      <span className="font-medium">{p.display_name}</span>
                      <code className="text-[10px] text-zinc-500">{p.slug}</code>
                    </div>
                  </TD>
                  <TD>
                    <Badge tone={TIER_TONE[p.tier_code] ?? "zinc"}>
                      {p.tier_label} · {(p.default_payout_bp / 100).toFixed(0)}%
                    </Badge>
                  </TD>
                  <TD>{p.code_count}</TD>
                  <TD>{p.conversion_count.toLocaleString()}</TD>
                  <TD>{formatCents(p.conversion_value_cents_total)}</TD>
                  <TD>{formatCents(p.payout_paid_cents)}</TD>
                  <TD className="text-amber-700 dark:text-amber-400">
                    {p.payout_pending_cents > 0 ? formatCents(p.payout_pending_cents) : "—"}
                  </TD>
                  <TD>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete partner ${p.slug}?`)) del.mutate(p.id);
                      }}
                      data-testid={`partner-delete-${p.slug}`}
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
  const create = useCreatePartner();
  const [slug, setSlug] = useState<string>("");
  const [displayName, setDisplayName] = useState<string>("");
  const [contactEmail, setContactEmail] = useState<string>("");
  const [tierId, setTierId] = useState<number>(1);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await create.mutateAsync({
      slug,
      display_name: displayName,
      contact_email: contactEmail,
      tier_id: tierId,
      workspace_id: workspaceId,
    });
    setSlug("");
    setDisplayName("");
    setContactEmail("");
    setTierId(1);
    onDone();
  };

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
      data-testid="partner-create-form"
    >
      <div className="grid grid-cols-2 gap-4">
        <Field label="Slug (URL-safe)" required htmlFor="partner-slug">
          <Input id="partner-slug" value={slug} onChange={(e) => setSlug(e.target.value)} required placeholder="acme-agency" />
        </Field>
        <Field label="Display name" required htmlFor="partner-name">
          <Input id="partner-name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} required placeholder="Acme Agency" />
        </Field>
        <Field label="Contact email" required htmlFor="partner-email">
          <Input id="partner-email" type="email" value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} required placeholder="hello@acme.com" />
        </Field>
        <Field label="Tier" htmlFor="partner-tier">
          <Select id="partner-tier" value={String(tierId)} onChange={(e) => setTierId(Number(e.target.value))}>
            {TIERS.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </Select>
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
