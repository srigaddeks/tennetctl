"use client";

import { useMemo, useState } from "react";
import { SlidersHorizontal, Globe, Building2, Layers, ToggleLeft } from "lucide-react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
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
import { ConfigRowActions } from "@/features/vault/configs/_components/config-row-actions";
import { CreateConfigDialog } from "@/features/vault/configs/_components/create-config-dialog";
import { useConfigs } from "@/features/vault/configs/hooks/use-configs";
import { stringifyValue } from "@/features/vault/configs/schema";
import { useWorkspaceContext } from "@/lib/workspace-context";

function scopeTone(scope: string) {
  switch (scope) {
    case "global":    return "amber"  as const;
    case "org":       return "blue"   as const;
    case "workspace": return "purple" as const;
    default:          return "default" as const;
  }
}

function typeTone(valueType: string) {
  switch (valueType) {
    case "boolean": return "emerald" as const;
    case "number":  return "amber"   as const;
    case "json":    return "purple"  as const;
    default:        return "default" as const;
  }
}

function typeAccent(valueType: string): string {
  switch (valueType) {
    case "boolean": return "var(--success)";
    case "number":  return "var(--warning)";
    case "json":    return "#a855f7";
    default:        return "var(--accent)";
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

export default function ConfigsPage() {
  const [openCreate, setOpenCreate] = useState(false);
  const [appId, setAppId] = useState<string | null>(null);
  const { orgId, workspaceId } = useWorkspaceContext();
  const { data, isLoading, isError, error, refetch } = useConfigs({
    org_id: orgId,
    workspace_id: workspaceId,
  });

  const stats = useMemo(() => {
    const items = data?.items ?? [];
    return {
      total:     items.length,
      global:    items.filter((c) => c.scope === "global").length,
      org:       items.filter((c) => c.scope === "org").length,
      workspace: items.filter((c) => c.scope === "workspace").length,
    };
  }, [data]);

  const statCards: StatCardData[] = [
    { label: "Total Configs",    value: stats.total,     icon: SlidersHorizontal, accentColor: "var(--accent)",  testId: "stat-configs-total"     },
    { label: "Global Scope",     value: stats.global,    icon: Globe,             accentColor: "var(--warning)", testId: "stat-configs-global"    },
    { label: "Org Scope",        value: stats.org,       icon: Building2,         accentColor: "var(--accent)",  testId: "stat-configs-org"       },
    { label: "Workspace Scope",  value: stats.workspace, icon: Layers,            accentColor: "#a855f7",        testId: "stat-configs-workspace" },
  ];

  return (
    <>
      <PageHeader
        title="Configs"
        description="Plaintext typed configuration values. Always viewable and editable. Scoped global / org / workspace."
        testId="heading-vault-configs"
        actions={
          <Button
            variant="primary"
            data-testid="open-create-config"
            onClick={() => setOpenCreate(true)}
          >
            + New config
          </Button>
        }
      />

      {/* Scope context bar */}
      <div
        className="flex items-center gap-2 px-8 py-2 text-xs"
        style={{
          background: "var(--bg-surface)",
          borderBottom: "1px solid var(--border)",
          color: "var(--text-secondary)",
        }}
        data-testid="scope-context-bar"
      >
        <span style={{ color: "var(--text-muted)" }}>Viewing:</span>
        {orgId || workspaceId ? (
          <>
            <span
              className="rounded px-1.5 py-0.5 font-mono text-[11px]"
              style={{
                background: "var(--accent-muted)",
                color: "var(--accent)",
                fontFamily: "var(--font-mono)",
              }}
            >
              {orgId ? orgId.slice(0, 12) : "—"}
            </span>
            {workspaceId && (
              <>
                <span style={{ color: "var(--text-muted)" }}>/</span>
                <span
                  className="rounded px-1.5 py-0.5 font-mono text-[11px]"
                  style={{
                    background: "var(--bg-elevated)",
                    color: "var(--text-secondary)",
                    border: "1px solid var(--border)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {workspaceId.slice(0, 12)}
                </span>
              </>
            )}
          </>
        ) : (
          <span style={{ color: "var(--text-muted)" }}>All scopes</span>
        )}
      </div>

      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="vault-configs-body"
      >
        {/* Stat cards */}
        {!isLoading && !isError && data && <StatCards cards={statCards} />}

        {/* Application scope bar */}
        <div className="mb-4">
          <ApplicationScopeBar
            appId={appId}
            orgId={orgId ?? undefined}
            label="Scope configs to application"
            onChange={setAppId}
          />
        </div>

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
            title="No configs yet"
            description="Create your first config. Values are stored as plaintext JSONB and visible to anyone with read access at this scope."
            action={
              <Button
                variant="primary"
                onClick={() => setOpenCreate(true)}
                data-testid="empty-create-config"
              >
                + Create first config
              </Button>
            }
          />
        )}

        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Key</TH>
                <TH>Type</TH>
                <TH>Value</TH>
                <TH>Scope</TH>
                <TH>Description</TH>
                <TH>Updated</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((c) => (
                <TR key={c.id}>
                  <TD>
                    <span
                      className="font-mono-data text-xs font-semibold"
                      style={{ color: "var(--accent)", fontFamily: "var(--font-mono)" }}
                      data-testid={`config-row-${c.key}`}
                    >
                      {c.key}
                    </span>
                  </TD>
                  <TD>
                    <div className="flex items-center gap-1.5">
                      {c.value_type === "boolean" && (
                        <ToggleLeft className="h-3.5 w-3.5" style={{ color: "var(--success)" }} />
                      )}
                      <Badge tone={typeTone(c.value_type)}>{c.value_type}</Badge>
                    </div>
                  </TD>
                  <TD>
                    <code
                      className="break-all text-xs font-mono-data"
                      style={{ color: typeAccent(c.value_type), fontFamily: "var(--font-mono)" }}
                      data-testid={`config-value-${c.key}`}
                    >
                      {stringifyValue(c.value, c.value_type)}
                    </code>
                  </TD>
                  <TD>
                    <Badge tone={scopeTone(c.scope)}>{c.scope}</Badge>
                    {c.org_id && (
                      <div
                        className="mt-0.5 text-[10px]"
                        style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                      >
                        org:{c.org_id.slice(0, 8)}
                        {c.workspace_id && ` · ws:${c.workspace_id.slice(0, 8)}`}
                      </div>
                    )}
                  </TD>
                  <TD>
                    {c.description ? (
                      <span style={{ color: "var(--text-secondary)" }}>{c.description}</span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </TD>
                  <TD>
                    <span
                      className="text-xs font-mono-data"
                      style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                    >
                      {c.updated_at.slice(0, 19).replace("T", " ")}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <ConfigRowActions config={c} />
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <CreateConfigDialog
        open={openCreate}
        onClose={() => setOpenCreate(false)}
      />
    </>
  );
}
