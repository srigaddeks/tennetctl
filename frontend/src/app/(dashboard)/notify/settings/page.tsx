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

function SectionHeader({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 16,
        marginBottom: 16,
      }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <span
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 36,
            height: 36,
            borderRadius: 8,
            background: "var(--accent-muted)",
            color: "var(--accent)",
            flexShrink: 0,
            marginTop: 2,
          }}
        >
          {icon}
        </span>
        <div>
          <h2
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: 3,
            }}
          >
            {title}
          </h2>
          <p style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 480 }}>
            {description}
          </p>
        </div>
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  );
}

function SMTPIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="4" width="14" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M1 5.5l7 5 7-5" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
    </svg>
  );
}

function GroupIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M2 3h12M2 8h8M2 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

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
        description="SMTP providers and template groups. Configure delivery infrastructure before creating templates."
        testId="heading-notify-settings"
      />
      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px", display: "flex", flexDirection: "column", gap: 32 }}
        data-testid="notify-settings-body"
      >
        {/* SMTP Configs */}
        <section
          style={{
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
            padding: 24,
          }}
        >
          <SectionHeader
            icon={<SMTPIcon />}
            title="SMTP Configurations"
            description="Email server credentials stored in vault. Each SMTP config is referenced by one or more template groups."
            action={
              <Button data-testid="btn-new-smtp" onClick={() => setSmtpOpen(true)} disabled={!orgId}>
                + New SMTP
              </Button>
            }
          />

          {smtp.isLoading && <Skeleton className="h-16 w-full" />}
          {smtp.isError && (
            <ErrorState message={smtp.error instanceof Error ? smtp.error.message : "Load failed"} />
          )}
          {!smtp.isLoading && smtpItems.length === 0 && (
            <EmptyState
              title="No SMTP configs yet"
              description="Add a config to send email templates."
            />
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
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 12,
                          color: "var(--info)",
                        }}
                      >
                        {s.key}
                      </span>
                    </TD>
                    <TD>
                      <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>
                        {s.label}
                      </span>
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 12,
                          color: "var(--text-secondary)",
                        }}
                      >
                        {s.host}:{s.port}
                      </span>
                    </TD>
                    <TD>
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                        {s.username}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={s.tls ? "emerald" : "default"} dot={s.tls}>
                        {s.tls ? "TLS" : "Plain"}
                      </Badge>
                    </TD>
                    <TD>
                      <div style={{ display: "flex", gap: 12 }}>
                        <button
                          type="button"
                          data-testid={`smtp-edit-${s.id}`}
                          onClick={() => setSmtpEdit(s)}
                          style={{
                            fontSize: 12,
                            fontWeight: 500,
                            color: "var(--accent)",
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: 0,
                          }}
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
                          style={{
                            fontSize: 12,
                            fontWeight: 500,
                            color: "var(--danger)",
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: 0,
                            opacity: deleteSMTP.isPending ? 0.5 : 1,
                          }}
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
        <section
          style={{
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
            padding: 24,
          }}
        >
          <SectionHeader
            icon={<GroupIcon />}
            title="Template Groups"
            description="Group templates by purpose (onboarding, billing, security). Each group is bound to one SMTP config and defines a notification category."
            action={
              <Button data-testid="btn-new-group" onClick={() => setGroupOpen(true)} disabled={!orgId}>
                + New Group
              </Button>
            }
          />

          {groups.isLoading && <Skeleton className="h-16 w-full" />}
          {groups.isError && (
            <ErrorState message={groups.error instanceof Error ? groups.error.message : "Load failed"} />
          )}
          {!groups.isLoading && groupItems.length === 0 && (
            <EmptyState
              title="No template groups yet"
              description="Create a group before adding templates."
            />
          )}
          {groupItems.length > 0 && (
            <Table>
              <THead>
                <tr>
                  <TH>Key</TH>
                  <TH>Label</TH>
                  <TH>Category</TH>
                  <TH>SMTP Config</TH>
                  <TH>Actions</TH>
                </tr>
              </THead>
              <TBody>
                {groupItems.map((g) => (
                  <TR key={g.id} data-testid={`group-row-${g.id}`}>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 12,
                          color: "var(--info)",
                        }}
                      >
                        {g.key}
                      </span>
                    </TD>
                    <TD>
                      <span style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 500 }}>
                        {g.label}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone="cyan">{g.category_label}</Badge>
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 12,
                          color: g.smtp_config_key ? "var(--text-secondary)" : "var(--text-muted)",
                        }}
                      >
                        {g.smtp_config_key ?? "—"}
                      </span>
                    </TD>
                    <TD>
                      <div style={{ display: "flex", gap: 12 }}>
                        <button
                          type="button"
                          data-testid={`group-edit-${g.id}`}
                          onClick={() => setGroupEdit(g)}
                          style={{
                            fontSize: 12,
                            fontWeight: 500,
                            color: "var(--accent)",
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: 0,
                          }}
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
                          style={{
                            fontSize: 12,
                            fontWeight: 500,
                            color: "var(--danger)",
                            background: "none",
                            border: "none",
                            cursor: "pointer",
                            padding: 0,
                            opacity: deleteGroup.isPending ? 0.5 : 1,
                          }}
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
        <section
          style={{
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
            padding: 24,
          }}
        >
          <SubscriptionsSection orgId={orgId} />
        </section>
      </div>

      {orgId && (
        <>
          <NewSMTPDialog open={smtpOpen} onClose={() => setSmtpOpen(false)} orgId={orgId} />
          <NewGroupDialog
            open={groupOpen}
            onClose={() => setGroupOpen(false)}
            orgId={orgId}
            smtpConfigs={smtpItems.map((s) => ({ id: s.id, label: s.label, key: s.key }))}
          />
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
