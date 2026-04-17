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

// Use the default org — in a real app this would come from context/session
const DEFAULT_ORG_ID = process.env.NEXT_PUBLIC_DEFAULT_ORG_ID ?? "";

const STATUS_LABELS: Record<number, string> = {
  1: "Pending",
  2: "Accepted",
  3: "Cancelled",
  4: "Expired",
};

const STATUS_VARIANTS: Record<number, "default" | "success" | "warning" | "danger"> = {
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

export default function InvitesPage() {
  const [orgId] = useState<string>(DEFAULT_ORG_ID);
  const [showForm, setShowForm] = useState(false);
  const toast = useToast();

  const { data: invites, isLoading, isError, error } = useInvites(orgId || null);
  const createInvite = useCreateInvite(orgId);
  const cancelInvite = useCancelInvite(orgId);

  const form = useForm<InviteForm>({ resolver: zodResolver(inviteSchema) });

  async function handleInvite(values: InviteForm) {
    try {
      await createInvite.mutateAsync({
        email: values.email,
        role_id: values.role_id || null,
      });
      toast.success(`Invite sent to ${values.email}`);
      form.reset();
      setShowForm(false);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to send invite";
      toast.error(msg);
    }
  }

  async function handleCancel(inviteId: string, email: string) {
    try {
      await cancelInvite.mutateAsync(inviteId);
      toast.success(`Invite for ${email} cancelled`);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to cancel invite";
      toast.error(msg);
    }
  }

  return (
    <>
      <PageHeader
        title="Invites"
        description="Invite users to join your organization. Invites expire after 72 hours."
        testId="heading-invites"
      >
        <Button
          variant="primary"
          onClick={() => setShowForm((s) => !s)}
          data-testid="btn-invite-user"
        >
          {showForm ? "Cancel" : "Invite User"}
        </Button>
      </PageHeader>

      {showForm && (
        <div className="mb-6 rounded-lg border bg-white p-5 shadow-sm" data-testid="invite-form">
          <h2 className="mb-4 text-sm font-semibold text-gray-700">Send Invite</h2>
          <form onSubmit={form.handleSubmit(handleInvite)} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Field label="Email" className="flex-1">
              <Input
                {...form.register("email")}
                type="email"
                placeholder="colleague@example.com"
                data-testid="input-invite-email"
              />
              {form.formState.errors.email && (
                <p className="mt-1 text-xs text-red-600">{form.formState.errors.email.message}</p>
              )}
            </Field>
            <Button
              type="submit"
              variant="primary"
              isLoading={createInvite.isPending}
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
            error instanceof ApiClientError
              ? error.message
              : "Failed to load invites"
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
                    <Badge variant={STATUS_VARIANTS[invite.status]}>
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
                        isLoading={cancelInvite.isPending}
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
