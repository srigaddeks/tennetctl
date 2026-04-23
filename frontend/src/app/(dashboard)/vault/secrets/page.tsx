"use client";

import { Suspense, useMemo, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { KeyRound, Globe, Building2, Layers, ShieldAlert, Lock, X } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { CreateSecretDialog } from "@/features/vault/secrets/_components/create-secret-dialog";
import { SecretRowActions } from "@/features/vault/secrets/_components/secret-row-actions";
import { useSecrets } from "@/features/vault/secrets/hooks/use-secrets";

function scopeTone(scope: string) {
  switch (scope) {
    case "global":    return "amber"  as const;
    case "org":       return "blue"   as const;
    case "workspace": return "purple" as const;
    default:          return "default" as const;
  }
}

type StatCardData = {
  label: string;
  value: number;
  icon: typeof Globe;
  accentColor: string;
  testId: string;
};

function StatCards({ cards }: { cards: StatCardData[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 mb-6">
      {cards.map(({ label, value, icon: Icon, accentColor, testId }) => (
        <div
          key={label}
          className="flex items-center gap-3 rounded-xl px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border)",
            borderLeft: `3px solid ${accentColor}`,
          }}
          data-testid={testId}
        >
          <div
            className="shrink-0 rounded-lg p-2"
            style={{ background: "var(--bg-elevated)" }}
          >
            <Icon className="h-4 w-4" style={{ color: accentColor }} />
          </div>
          <div className="min-w-0">
            <span
              className="block text-2xl font-bold tabular-nums leading-none font-mono-data"
              style={{ color: accentColor }}
            >
              {value}
            </span>
            <span
              className="mt-0.5 block truncate text-[11px] label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              {label}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Scope filter banner ──────────────────────────────────────────────────────

function ScopeFilterBanner({
  orgId,
  workspaceId,
  onClear,
}: {
  orgId: string;
  workspaceId: string | null;
  onClear: () => void;
}) {
  return (
    <div
      className="flex items-center gap-3 rounded-xl px-4 py-3 mb-5"
      style={{
        background: "var(--accent-muted)",
        border: "1px solid var(--accent-dim)",
      }}
      data-testid="scope-filter-banner"
    >
      <Building2 className="h-4 w-4 shrink-0" style={{ color: "var(--accent)" }} />
      <div className="flex-1 min-w-0 text-xs" style={{ color: "var(--text-secondary)" }}>
        <span className="font-medium" style={{ color: "var(--accent)" }}>Scope filter active. </span>
        Showing secrets for org:{" "}
        <code
          className="rounded px-1.5 py-0.5 text-[11px]"
          style={{
            background: "var(--bg-elevated)",
            color: "var(--text-primary)",
            fontFamily: "var(--font-mono)",
          }}
        >
          {orgId}
        </code>
        {workspaceId && (
          <>
            {" "}· workspace:{" "}
            <code
              className="rounded px-1.5 py-0.5 text-[11px]"
              style={{
                background: "var(--bg-elevated)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
              }}
            >
              {workspaceId}
            </code>
          </>
        )}
      </div>
      <button
        type="button"
        onClick={onClear}
        className="shrink-0 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition"
        style={{
          background: "var(--bg-elevated)",
          border: "1px solid var(--border-bright)",
          color: "var(--text-secondary)",
        }}
        data-testid="clear-scope-filter"
      >
        <X className="h-3 w-3" />
        Clear scope filter
      </button>
    </div>
  );
}

// ─── Inner page (needs useSearchParams) ──────────────────────────────────────

function SecretsPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlOrgId = searchParams.get("org_id");
  const urlWorkspaceId = searchParams.get("workspace_id");

  const [openCreate, setOpenCreate] = useState(false);
  const { data, isLoading, isError, error, refetch } = useSecrets({
    org_id: urlOrgId ?? undefined,
    workspace_id: urlWorkspaceId ?? undefined,
  });

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    return {
      total:     items.length,
      global:    items.filter((s) => s.scope === "global").length,
      org:       items.filter((s) => s.scope === "org").length,
      workspace: items.filter((s) => s.scope === "workspace").length,
    };
  }, [data]);

  const statCards: StatCardData[] = [
    { label: "Total Secrets",    value: stats.total,     icon: KeyRound,  accentColor: "var(--warning)",  testId: "stat-secrets-total"     },
    { label: "Global Scope",     value: stats.global,    icon: Globe,     accentColor: "var(--warning)",  testId: "stat-secrets-global"    },
    { label: "Org Scope",        value: stats.org,       icon: Building2, accentColor: "var(--accent)",   testId: "stat-secrets-org"       },
    { label: "Workspace Scope",  value: stats.workspace, icon: Layers,    accentColor: "#a855f7",         testId: "stat-secrets-workspace" },
  ];

  function clearScopeFilter() {
    const url = new URL(window.location.href);
    url.searchParams.delete("org_id");
    url.searchParams.delete("workspace_id");
    router.replace(url.pathname + (url.searchParams.toString() ? `?${url.searchParams}` : ""));
  }

  return (
    <>
      <PageHeader
        title="Secrets"
        description="Envelope-encrypted. Values are shown exactly once at create or rotate — never re-displayed."
        testId="heading-vault-secrets"
        actions={
          <Button
            variant="primary"
            data-testid="open-create-secret"
            onClick={() => setOpenCreate(true)}
          >
            + New secret
          </Button>
        }
      />

      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="vault-secrets-body"
      >
        {/* Scope filter banner */}
        {urlOrgId && (
          <ScopeFilterBanner
            orgId={urlOrgId}
            workspaceId={urlWorkspaceId}
            onClear={clearScopeFilter}
          />
        )}

        {/* Warning banner */}
        <div
          className="flex items-start gap-3 rounded-xl px-4 py-3 mb-5"
          style={{
            background: "var(--warning-muted)",
            border: "1px solid var(--warning)",
          }}
        >
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" style={{ color: "var(--warning)" }} />
          <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
            <span className="font-semibold" style={{ color: "var(--warning)" }}>All reads and writes are audit-logged. </span>
            Secret values are envelope-encrypted. Once created, values cannot be retrieved — only rotated.
            Same key can exist at multiple scopes (global default + per-org override).
          </p>
        </div>

        {/* Stat cards */}
        {!isLoading && !isError && data && <StatCards cards={statCards} />}

        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
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
            title="No secrets yet"
            description="Create your first secret. Values are envelope-encrypted and revealed exactly once."
            action={
              <Button
                variant="primary"
                onClick={() => setOpenCreate(true)}
                data-testid="empty-create-secret"
              >
                + Create first secret
              </Button>
            }
          />
        )}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Key</TH>
                <TH>Value</TH>
                <TH>Version</TH>
                <TH>Scope</TH>
                <TH>Description</TH>
                <TH>Updated</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((s) => (
                <TR key={`${s.scope}-${s.org_id ?? ""}-${s.workspace_id ?? ""}-${s.key}`}>
                  <TD>
                    <span
                      className="font-mono-data text-xs font-semibold"
                      style={{ color: "var(--warning)", fontFamily: "var(--font-mono)" }}
                      data-testid={`secret-row-${s.key}`}
                    >
                      {s.key}
                    </span>
                  </TD>
                  <TD>
                    <div className="flex items-center gap-1.5">
                      <Lock className="h-3 w-3 shrink-0" style={{ color: "var(--warning)" }} />
                      <span
                        className="font-mono-data text-xs tracking-widest"
                        style={{ color: "var(--warning)" }}
                      >
                        ••••••••••••
                      </span>
                    </div>
                  </TD>
                  <TD>
                    <Badge tone="amber">v{s.version}</Badge>
                  </TD>
                  <TD>
                    <Badge tone={scopeTone(s.scope)}>{s.scope}</Badge>
                    {s.org_id && (
                      <div
                        className="mt-0.5 text-[10px]"
                        style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                      >
                        org:{s.org_id.slice(0, 8)}
                        {s.workspace_id && ` · ws:${s.workspace_id.slice(0, 8)}`}
                      </div>
                    )}
                  </TD>
                  <TD>
                    {s.description ? (
                      <span style={{ color: "var(--text-secondary)" }}>{s.description}</span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </TD>
                  <TD>
                    <span
                      className="text-xs font-mono-data"
                      style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                    >
                      {s.updated_at.slice(0, 19).replace("T", " ")}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <SecretRowActions secret={s} />
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <CreateSecretDialog
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />
    </>
  );
}

// ─── Page export with Suspense boundary ──────────────────────────────────────

export default function SecretsPage() {
  return (
    <Suspense fallback={
      <div
        className="flex items-center justify-center p-8"
        style={{ color: "var(--text-muted)" }}
      >
        Loading secrets…
      </div>
    }>
      <SecretsPageInner />
    </Suspense>
  );
}
