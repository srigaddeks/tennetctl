"use client";

import { useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, X } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Input,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { CreateOrgDialog } from "@/features/iam-orgs/create-org-dialog";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";

// ─── Welcome banner ───────────────────────────────────────────────────────────

function WelcomeBanner({ onDismiss }: { onDismiss: () => void }) {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(onDismiss, 10_000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      className="flex items-start gap-4 rounded-xl px-5 py-4 mb-6 animate-fade-in"
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border)",
        borderLeft: "4px solid var(--success)",
      }}
      data-testid="welcome-banner"
    >
      <div
        className="shrink-0 flex h-8 w-8 items-center justify-center rounded-full mt-0.5"
        style={{ background: "var(--success-muted)", border: "1px solid var(--success)" }}
      >
        <CheckCircle2 className="h-4 w-4" style={{ color: "var(--success)" }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold" style={{ color: "var(--success)" }}>
          Platform initialized.
        </p>
        <p className="mt-0.5 text-xs" style={{ color: "var(--text-secondary)" }}>
          Create your first organisation to get started. An organisation is the top-level tenant boundary.
          Workspaces, users, roles, and all resources are scoped under orgs.
        </p>
      </div>
      <div className="shrink-0 flex items-center gap-2 mt-0.5">
        <Button
          variant="primary"
          size="sm"
          onClick={() => {
            onDismiss();
            // trigger create dialog — parent reads this via callback
            router.push("/iam/orgs?welcome=true&create=true");
          }}
          data-testid="welcome-create-org"
        >
          Create org →
        </Button>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-md p-1 transition"
          style={{ color: "var(--text-muted)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text-muted)")}
          data-testid="welcome-dismiss"
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

// ─── Inner page (needs useSearchParams) ───────────────────────────────────────

function OrgsPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isWelcome = searchParams.get("welcome") === "true";
  const shouldOpenCreate = searchParams.get("create") === "true";

  const [showWelcome, setShowWelcome] = useState(isWelcome);
  const [openCreate, setOpenCreate] = useState(shouldOpenCreate);
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error, refetch } = useOrgs({ limit: 500 });

  const allItems = data?.items ?? [];

  const filtered = allItems.filter((o) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      o.slug.toLowerCase().includes(q) ||
      (o.display_name ?? "").toLowerCase().includes(q)
    );
  });

  const totalOrgs = allItems.length;
  const activeOrgs = allItems.filter((o) => o.is_active && !o.is_test).length;
  const testOrgs = allItems.filter((o) => o.is_test).length;

  function handleDismissWelcome() {
    setShowWelcome(false);
    // Clean up URL params without navigation
    const url = new URL(window.location.href);
    url.searchParams.delete("welcome");
    url.searchParams.delete("create");
    router.replace(url.pathname + (url.searchParams.toString() ? `?${url.searchParams}` : ""));
  }

  return (
    <>
      <PageHeader
        title="Organisations"
        description="Tenant boundaries. Top-level resource; workspaces, users, roles, groups, and applications nest under an org."
        testId="heading-orgs"
        actions={
          <Button
            variant="primary"
            data-testid="open-create-org"
            onClick={() => setOpenCreate(true)}
          >
            + New org
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="orgs-body">
        {/* Welcome banner */}
        {showWelcome && (
          <WelcomeBanner onDismiss={handleDismissWelcome} />
        )}

        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard
              label="Total Orgs"
              value={totalOrgs}
              sub="all tenants"
              accent="blue"
            />
            <StatCard
              label="Active"
              value={activeOrgs}
              sub="production tenants"
              accent="green"
            />
            <StatCard
              label="Test"
              value={testOrgs}
              sub="sandbox tenants"
              accent="amber"
            />
          </div>
        )}

        {/* Search + count */}
        {data && data.items.length > 0 && (
          <div className="mb-4 flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <span
                className="absolute left-3 top-1/2 -translate-y-1/2 label-caps pointer-events-none"
                style={{ color: "var(--text-muted)" }}
              >
                FILTER
              </span>
              <Input
                type="search"
                placeholder="slug or name…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-16"
                data-testid="search-orgs"
              />
            </div>
            <span
              className="ml-auto rounded px-2 py-0.5 text-xs font-mono"
              style={{
                background: "var(--bg-elevated)",
                color: "var(--text-secondary)",
                border: "1px solid var(--border)",
              }}
            >
              {filtered.length} / {data.items.length}
            </span>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {/* Empty — no orgs at all */}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No organisations yet"
            description="Create your first org to get started. Everything else — workspaces, users, roles — lives under an org."
            action={
              <Button variant="primary" onClick={() => setOpenCreate(true)}>
                + Create first org
              </Button>
            }
          />
        )}

        {/* Empty — search no matches */}
        {data && data.items.length > 0 && filtered.length === 0 && (
          <EmptyState
            title="No matches"
            description="Try a different search term."
          />
        )}

        {/* Table */}
        {data && filtered.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Display Name</TH>
                <TH>Status</TH>
                <TH>Type</TH>
                <TH>Created</TH>
              </tr>
            </THead>
            <TBody>
              {filtered.map((org) => (
                <TR
                  key={org.id}
                  onClick={() => router.push(`/iam/orgs/${org.id}`)}
                  data-testid={`org-row-${org.id}`}
                >
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--accent)" }}
                      data-testid={`org-slug-${org.slug}`}
                    >
                      {org.slug}
                    </span>
                  </TD>
                  <TD>
                    {org.display_name ? (
                      <span style={{ color: "var(--text-primary)" }}>
                        {org.display_name}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </TD>
                  <TD>
                    <Badge tone={org.is_active ? "success" : "default"} dot={org.is_active}>
                      {org.is_active ? "active" : "inactive"}
                    </Badge>
                  </TD>
                  <TD>
                    {org.is_test ? (
                      <Badge tone="amber">TEST</Badge>
                    ) : (
                      <Badge tone="default">production</Badge>
                    )}
                  </TD>
                  <TD>
                    <span className="font-mono-data text-xs" style={{ color: "var(--text-secondary)" }}>
                      {org.created_at.slice(0, 10)}
                    </span>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <CreateOrgDialog
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />
    </>
  );
}

// ─── Page export with Suspense boundary ──────────────────────────────────────

export default function OrgsPage() {
  return (
    <Suspense fallback={
      <div
        className="flex items-center justify-center p-8"
        style={{ color: "var(--text-muted)" }}
      >
        Loading organisations…
      </div>
    }>
      <OrgsPageInner />
    </Suspense>
  );
}
