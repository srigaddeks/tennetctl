"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
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
import {
  useCancelInvite,
  useCreateInvite,
  useInvites,
} from "@/features/iam/hooks/use-invites";
import { ApiClientError } from "@/lib/api";

const DEFAULT_ORG_ID = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID ?? "";

const STATUS_LABELS: Record<number, string> = {
  1: "Pending",
  2: "Accepted",
  3: "Cancelled",
  4: "Expired",
};

type BadgeTone = "default" | "success" | "warning" | "danger" | "info" | "emerald" | "red" | "amber" | "blue" | "purple" | "cyan";

const STATUS_TONES: Record<number, BadgeTone> = {
  1: "warning",
  2: "success",
  3: "danger",
  4: "default",
};

const inviteSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  role_id: z.string().optional(),
});
type InviteForm = z.infer<typeof inviteSchema>;

function getExpiryState(expiresAt: string | null | undefined): "overdue" | "soon" | "ok" | "none" {
  if (!expiresAt) return "none";
  const now = Date.now();
  const exp = new Date(expiresAt).getTime();
  if (exp < now) return "overdue";
  if (exp - now < 24 * 60 * 60 * 1000) return "soon";
  return "ok";
}

function formatExpiry(expiresAt: string | null | undefined): string {
  if (!expiresAt) return "—";
  return new Date(expiresAt).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function InvitesPage() {
  const [orgId] = useState<string>(DEFAULT_ORG_ID);
  const [showForm, setShowForm] = useState(false);
  const { toast } = useToast();

  const { data: invites, isLoading, isError, error } = useInvites(orgId || null);
  const createInvite = useCreateInvite(orgId);
  const cancelInvite = useCancelInvite(orgId);

  const form = useForm<InviteForm>({ resolver: zodResolver(inviteSchema) });

  const allInvites = invites ?? [];
  const pending = allInvites.filter((i) => i.status === 1).length;
  const accepted = allInvites.filter((i) => i.status === 2).length;
  const expired = allInvites.filter((i) => i.status === 4 || i.status === 3).length;

  async function handleInvite(values: InviteForm) {
    try {
      await createInvite.mutateAsync({
        email: values.email,
        role_id: values.role_id ?? null,
      });
      toast(`Invite sent to ${values.email}`, "success");
      form.reset();
      setShowForm(false);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to send invite";
      toast(msg, "error");
    }
  }

  async function handleCancel(inviteId: string, email: string) {
    try {
      await cancelInvite.mutateAsync(inviteId);
      toast(`Invite for ${email} cancelled`, "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to cancel invite";
      toast(msg, "error");
    }
  }

  return (
    <>
      <PageHeader
        title="Invites"
        description="Invite users to join your organization. Invites expire after 72 hours."
        testId="heading-invites"
        actions={
          <Button
            variant="primary"
            onClick={() => setShowForm((s) => !s)}
            data-testid="btn-invite-user"
          >
            {showForm ? "Cancel" : "Invite User"}
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in">

        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard
              label="Pending Invites"
              value={pending}
              sub="awaiting acceptance"
              accent="amber"
            />
            <StatCard
              label="Accepted"
              value={accepted}
              sub="successfully joined"
              accent="green"
            />
            <StatCard
              label="Expired / Cancelled"
              value={expired}
              sub="no longer active"
              accent="red"
            />
          </div>
        )}

        {/* Inline invite form */}
        {showForm && (
          <div
            className="mb-6 rounded-lg p-5 animate-slide-up"
            style={{
              background: "var(--bg-surface)",
              border: "1px solid var(--border-bright)",
            }}
            data-testid="invite-form"
          >
            <h2
              className="label-caps mb-4"
              style={{ color: "var(--text-secondary)" }}
            >
              Send Invite
            </h2>
            <form
              onSubmit={form.handleSubmit(handleInvite)}
              className="flex flex-col gap-3 sm:flex-row sm:items-end"
            >
              <div className="flex-1">
                <Field label="Email">
                  <Input
                    {...form.register("email")}
                    type="email"
                    placeholder="colleague@example.com"
                    data-testid="input-invite-email"
                  />
                </Field>
                {form.formState.errors.email && (
                  <p
                    className="mt-1 text-xs"
                    style={{ color: "var(--danger)" }}
                  >
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                variant="primary"
                loading={createInvite.isPending}
                data-testid="btn-send-invite"
              >
                Send Invite
              </Button>
            </form>
          </div>
        )}

        {/* Loading */}
        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-11 w-full" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={
              error instanceof ApiClientError ? error.message : "Failed to load invites"
            }
          />
        )}

        {/* Empty */}
        {!isLoading && !isError && invites !== undefined && invites.length === 0 && (
          <EmptyState
            title="No invites yet"
            description="Send an invite to bring a teammate into your organization."
          />
        )}

        {/* Table */}
        {!isLoading && !isError && invites !== undefined && invites.length > 0 && (
          <Table data-testid="invites-table">
            <THead>
              <TR>
                <TH>Email</TH>
                <TH>Invited By</TH>
                <TH>Status</TH>
                <TH>Expires</TH>
                <TH />
              </TR>
            </THead>
            <TBody>
              {invites.map((invite) => {
                const expiryState = getExpiryState(invite.expires_at);
                return (
                  <TR key={invite.id} data-testid={`invite-row-${invite.id}`}>
                    <TD>
                      <span style={{ color: "var(--text-primary)" }}>
                        {invite.email}
                      </span>
                    </TD>
                    <TD>
                      <span style={{ color: "var(--text-secondary)" }}>
                        {invite.inviter_display_name ?? invite.inviter_email ?? (
                          <span className="font-mono-data text-xs" style={{ color: "var(--text-muted)" }}>
                            {invite.invited_by.slice(0, 8)}…
                          </span>
                        )}
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={STATUS_TONES[invite.status]} dot={invite.status === 1}>
                        {STATUS_LABELS[invite.status] ?? String(invite.status)}
                      </Badge>
                    </TD>
                    <TD>
                      {invite.status === 1 ? (
                        <span className="flex items-center gap-1.5">
                          {expiryState === "overdue" && (
                            <Badge tone="danger">OVERDUE</Badge>
                          )}
                          {expiryState === "soon" && (
                            <Badge tone="warning">EXPIRING SOON</Badge>
                          )}
                          <span
                            className="font-mono-data text-xs"
                            style={{ color: expiryState === "overdue" ? "var(--danger)" : expiryState === "soon" ? "var(--warning)" : "var(--text-secondary)" }}
                          >
                            {formatExpiry(invite.expires_at)}
                          </span>
                        </span>
                      ) : (
                        <span className="font-mono-data text-xs" style={{ color: "var(--text-muted)" }}>
                          {formatExpiry(invite.expires_at)}
                        </span>
                      )}
                    </TD>
                    <TD>
                      {invite.status === 1 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCancel(invite.id, invite.email)}
                          loading={cancelInvite.isPending}
                          data-testid={`btn-cancel-invite-${invite.id}`}
                        >
                          Cancel
                        </Button>
                      )}
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
        )}
      </div>
    </>
  );
}
