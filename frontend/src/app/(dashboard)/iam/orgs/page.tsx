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
import { CreateOrgDialog } from "@/features/iam-orgs/create-org-dialog";
import { useOrgs } from "@/features/iam-orgs/hooks/use-orgs";
import { OrgDetailDrawer } from "@/features/iam-orgs/org-detail-drawer";

export default function OrgsPage() {
  const [openCreate, setOpenCreate] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const { data, isLoading, isError, error, refetch } = useOrgs({ limit: 100 });

  return (
    <>
      <PageHeader
        title="Organisations"
        description="Tenant boundaries. Top-level resource; workspaces, users, roles, groups, and applications nest under an org."
        testId="heading-orgs"
        actions={
          <Button
            data-testid="open-create-org"
            onClick={() => setOpenCreate(true)}
          >
            + New org
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="orgs-body">
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
            title="No organisations yet"
            description="Create your first org to get started. Everything else — workspaces, users, roles — lives under an org."
            action={
              <Button onClick={() => setOpenCreate(true)}>
                + Create first org
              </Button>
            }
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Slug</TH>
                <TH>Name</TH>
                <TH>Status</TH>
                <TH>Created</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((org) => (
                <TR
                  key={org.id}
                  onClick={() => setSelectedOrgId(org.id)}
                >
                  <TD>
                    <span
                      className="font-mono text-xs text-zinc-900 dark:text-zinc-50"
                      data-testid={`org-slug-${org.slug}`}
                    >
                      {org.slug}
                    </span>
                  </TD>
                  <TD>
                    {org.display_name ?? (
                      <span className="text-zinc-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <Badge tone={org.is_active ? "emerald" : "zinc"}>
                      {org.is_active ? "active" : "inactive"}
                    </Badge>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
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
      <OrgDetailDrawer
        orgId={selectedOrgId}
        onClose={() => setSelectedOrgId(null)}
      />
    </>
  );
}
