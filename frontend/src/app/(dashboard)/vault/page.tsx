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
import { CreateSecretDialog } from "@/features/vault/_components/create-secret-dialog";
import { SecretRowActions } from "@/features/vault/_components/secret-row-actions";
import { useSecrets } from "@/features/vault/hooks/use-secrets";

export default function VaultPage() {
  const [openCreate, setOpenCreate] = useState(false);
  const { data, isLoading, isError, error, refetch } = useSecrets();

  return (
    <>
      <PageHeader
        title="Vault"
        description="Envelope-encrypted secret storage. Values are shown once at create / rotate and never re-displayed."
        testId="heading-vault"
        actions={
          <Button
            data-testid="open-create-secret"
            onClick={() => setOpenCreate(true)}
          >
            + New secret
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="vault-body"
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
            title="No secrets yet"
            description="Create your first secret. Values are envelope-encrypted and revealed exactly once."
            action={
              <Button
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
                <TH>Version</TH>
                <TH>Description</TH>
                <TH>Updated</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((s) => (
                <TR key={s.key}>
                  <TD>
                    <span
                      className="font-mono text-xs text-zinc-900 dark:text-zinc-50"
                      data-testid={`secret-row-${s.key}`}
                    >
                      {s.key}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone="zinc">v{s.version}</Badge>
                  </TD>
                  <TD>
                    {s.description ?? (
                      <span className="text-zinc-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
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
