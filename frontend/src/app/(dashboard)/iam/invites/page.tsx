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

type BadgeTone = "zinc" | "emerald" | "amber" | "red";
const STATUS_TONES: Record<number, BadgeTone> = {
  1: "amber",
  2: "emerald",
  3: "red",
  4: "zinc",
};

const inviteSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  role_id: z.string().optional(),
});
type InviteForm = z.infer<typeof inviteSchema>;

export default function InvitesPage() {
  const [orgId] = useState<string>(DEFAULT_ORG_ID);
  const [showForm, setShowForm] = useState(false);
  const { toast } = useToast();

  const { data: invites, isLoading, isError, error } = useInvites(orgId || null);
  const createInvite = useCreateInvite(orgId);
  const cancelInvite = useCancelInvite(orgId);

  const form = useForm<InviteForm>({ resolver: zodResolver(inviteSchema) });

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

      {showForm && (
        <div className="mb-6 rounded-lg border bg-white p-5 shadow-sm" data-testid="invite-form">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Send Invite</h2>
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
                <p className="mt-1 text-xs text-red-600">{form.formState.errors.email.message}</p>
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

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <ErrorState
          message={
            error instanceof ApiClientError ? error.message : "Failed to load invites"
          }
        />
      )}

      {!isLoading && !isError && invites !== undefined && (
        invites.length === 0 ? (
          <EmptyState
            title="No invites yet"
            description="Send an invite to bring a teammate into your organization."
          />
        ) : (
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
              {invites.map((invite) => (
                <TR key={invite.id} data-testid={`invite-row-${invite.id}`}>
                  <TD>{invite.email}</TD>
                  <TD>{invite.inviter_display_name ?? invite.inviter_email ?? invite.invited_by}</TD>
                  <TD>
                    <Badge tone={STATUS_TONES[invite.status]}>
                      {STATUS_LABELS[invite.status] ?? String(invite.status)}
                    </Badge>
                  </TD>
                  <TD>
                    {invite.expires_at
                      ? new Date(invite.expires_at).toLocaleString()
                      : "—"}
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
              ))}
            </TBody>
          </Table>
        )
      )}
    </>
  );
}
