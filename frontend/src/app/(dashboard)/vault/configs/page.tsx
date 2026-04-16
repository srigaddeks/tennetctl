"use client";

import { useState } from "react";

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

function scopeTone(scope: string) {
  switch (scope) {
    case "global":
      return "blue" as const;
    case "org":
      return "purple" as const;
    case "workspace":
      return "amber" as const;
    default:
      return "zinc" as const;
  }
}

function typeTone(valueType: string) {
  switch (valueType) {
    case "boolean":
      return "emerald" as const;
    case "number":
      return "amber" as const;
    case "json":
      return "purple" as const;
    default:
      return "zinc" as const;
  }
}

export default function ConfigsPage() {
  const [openCreate, setOpenCreate] = useState(false);
  const { data, isLoading, isError, error, refetch } = useConfigs();

  return (
    <>
      <PageHeader
        title="Configs"
        description="Plaintext typed configuration values. Unlike secrets, configs are always viewable + editable. Scoped global / org / workspace."
        testId="heading-vault-configs"
        actions={
          <Button
            data-testid="open-create-config"
            onClick={() => setOpenCreate(true)}
          >
            + New config
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="vault-configs-body"
      >
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
                      className="font-mono text-xs text-zinc-900 dark:text-zinc-50"
                      data-testid={`config-row-${c.key}`}
                    >
                      {c.key}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone={typeTone(c.value_type)}>{c.value_type}</Badge>
                  </TD>
                  <TD>
                    <code
                      className="break-all font-mono text-xs text-zinc-700 dark:text-zinc-300"
                      data-testid={`config-value-${c.key}`}
                    >
                      {stringifyValue(c.value, c.value_type)}
                    </code>
                  </TD>
                  <TD>
                    <Badge tone={scopeTone(c.scope)}>{c.scope}</Badge>
                    {c.org_id && (
                      <div className="mt-0.5 font-mono text-[10px] text-zinc-500">
                        org:{c.org_id.slice(0, 8)}
                        {c.workspace_id && ` · ws:${c.workspace_id.slice(0, 8)}`}
                      </div>
                    )}
                  </TD>
                  <TD>
                    {c.description ?? (
                      <span className="text-zinc-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
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
