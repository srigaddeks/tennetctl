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
import { useMe } from "@/features/auth/hooks/use-auth";
import { EditGroupDialog } from "@/features/notify/_components/edit-group-dialog";
import { EditSMTPDialog } from "@/features/notify/_components/edit-smtp-dialog";
import { NewGroupDialog } from "@/features/notify/_components/new-group-dialog";
import { NewSMTPDialog } from "@/features/notify/_components/new-smtp-dialog";
import { SubscriptionsSection } from "@/features/notify/_components/subscriptions-section";
import {
  useDeleteSMTPConfig,
  useDeleteTemplateGroup,
  useSMTPConfigs,
  useTemplateGroupList,
} from "@/features/notify/hooks/use-notify-settings";
import type {
  NotifySMTPConfig,
  NotifyTemplateGroup,
} from "@/types/api";

export default function NotifySettingsPage() {
  const me = useMe();
  const orgId = me.data?.session?.org_id ?? null;

  const smtp = useSMTPConfigs(orgId);
  const groups = useTemplateGroupList(orgId);
  const deleteSMTP = useDeleteSMTPConfig(orgId);
  const deleteGroup = useDeleteTemplateGroup(orgId);

  const [smtpOpen, setSmtpOpen] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);
  const [smtpEdit, setSmtpEdit] = useState<NotifySMTPConfig | null>(null);
  const [groupEdit, setGroupEdit] = useState<NotifyTemplateGroup | null>(null);

  const smtpItems = smtp.data?.items ?? [];
  const groupItems = groups.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Notify Settings"
        description="SMTP servers and template groups. Configure these first before creating templates."
        testId="heading-notify-settings"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-10" data-testid="notify-settings-body">
        {/* SMTP Configs */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">SMTP Configs</h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Email server credentials stored in vault.</p>
            </div>
            <Button data-testid="btn-new-smtp" onClick={() => setSmtpOpen(true)} disabled={!orgId}>
              + New SMTP
            </Button>
          </div>
          {smtp.isLoading && <Skeleton className="h-16 w-full" />}
          {smtp.isError && <ErrorState message={smtp.error instanceof Error ? smtp.error.message : "Load failed"} />}
          {!smtp.isLoading && smtpItems.length === 0 && (
            <EmptyState title="No SMTP configs yet" description="Add a config to send email templates." />
          )}
          {smtpItems.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Key</TH>
                  <TH>Label</TH>
                  <TH>Host</TH>
                  <TH>Username</TH>
                  <TH>TLS</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {smtpItems.map((s) => (
                  <TR key={s.id} data-testid={`smtp-row-${s.id}`}>
                    <TD><span className="font-mono text-xs">{s.key}</span></TD>
                    <TD>{s.label}</TD>
                    <TD><span className="text-xs">{s.host}:{s.port}</span></TD>
                    <TD><span className="text-xs">{s.username}</span></TD>
                    <TD><Badge tone={s.tls ? "emerald" : "zinc"}>{s.tls ? "Yes" : "No"}</Badge></TD>
                    <TD>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          data-testid={`smtp-edit-${s.id}`}
                          onClick={() => setSmtpEdit(s)}
                          className="text-xs text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          data-testid={`smtp-delete-${s.id}`}
                          disabled={deleteSMTP.isPending}
                          onClick={() => {
                            if (confirm(`Delete SMTP config "${s.label}"?`)) deleteSMTP.mutate(s.id);
                          }}
                          className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>

        {/* Template Groups */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">Template Groups</h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">Group templates by purpose (onboarding, billing, etc.). Each group binds to one SMTP config.</p>
            </div>
            <Button data-testid="btn-new-group" onClick={() => setGroupOpen(true)} disabled={!orgId}>
              + New Group
            </Button>
          </div>
          {groups.isLoading && <Skeleton className="h-16 w-full" />}
          {groups.isError && <ErrorState message={groups.error instanceof Error ? groups.error.message : "Load failed"} />}
          {!groups.isLoading && groupItems.length === 0 && (
            <EmptyState title="No template groups yet" description="Create a group before adding templates." />
          )}
          {groupItems.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Key</TH>
                  <TH>Label</TH>
                  <TH>Category</TH>
                  <TH>SMTP</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {groupItems.map((g) => (
                  <TR key={g.id} data-testid={`group-row-${g.id}`}>
                    <TD><span className="font-mono text-xs">{g.key}</span></TD>
                    <TD>{g.label}</TD>
                    <TD><Badge tone="blue">{g.category_label}</Badge></TD>
                    <TD><span className="text-xs">{g.smtp_config_key ?? "—"}</span></TD>
                    <TD>
                      <div className="flex gap-3">
                        <button
                          type="button"
                          data-testid={`group-edit-${g.id}`}
                          onClick={() => setGroupEdit(g)}
                          className="text-xs text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-zinc-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          data-testid={`group-delete-${g.id}`}
                          disabled={deleteGroup.isPending}
                          onClick={() => {
                            if (confirm(`Delete group "${g.label}"?`)) deleteGroup.mutate(g.id);
                          }}
                          className="text-xs text-red-600 hover:text-red-700 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </section>

        {/* Subscriptions */}
        <SubscriptionsSection orgId={orgId} />
      </div>

      {orgId && (
        <>
          <NewSMTPDialog open={smtpOpen} onClose={() => setSmtpOpen(false)} orgId={orgId} />
          <NewGroupDialog open={groupOpen} onClose={() => setGroupOpen(false)} orgId={orgId} smtpConfigs={smtpItems.map((s) => ({ id: s.id, label: s.label, key: s.key }))} />
          <EditSMTPDialog
            open={smtpEdit !== null}
            onClose={() => setSmtpEdit(null)}
            orgId={orgId}
            row={smtpEdit}
          />
          <EditGroupDialog
            open={groupEdit !== null}
            onClose={() => setGroupEdit(null)}
            orgId={orgId}
            row={groupEdit}
            smtpConfigs={smtpItems.map((s) => ({ id: s.id, label: s.label, key: s.key }))}
          />
        </>
      )}
    </>
  );
}
