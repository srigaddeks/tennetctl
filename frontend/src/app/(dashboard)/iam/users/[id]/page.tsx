"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  ErrorState,
  Field,
  Input,
  Skeleton,
} from "@/components/ui";
import { Modal } from "@/components/modal";
import {
  useUser,
  useUpdateUser,
  useDeleteUser,
} from "@/features/iam-users/hooks/use-users";
import { ApiClientError } from "@/lib/api";

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = typeof params.id === "string" ? params.id : "";
  const { showToast } = useToast();

  const { data: user, isLoading, isError, error } = useUser(userId);
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleteEmailInput, setDeleteEmailInput] = useState("");
  const [confirmStatusOpen, setConfirmStatusOpen] = useState(false);
  const [pendingStatus, setPendingStatus] = useState<"active" | "inactive" | null>(null);

  function openDeactivate() {
    setPendingStatus("inactive");
    setConfirmStatusOpen(true);
  }

  function openReactivate() {
    setPendingStatus("active");
    setConfirmStatusOpen(true);
  }

  async function handleStatusChange() {
    if (!user || !pendingStatus) return;
    try {
      await updateUser.mutateAsync({ id: user.id, body: { status: pendingStatus } });
      showToast(
        pendingStatus === "active"
          ? "User reactivated successfully."
          : "User deactivated. All sessions revoked.",
        "success",
      );
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to update user status.";
      showToast(msg, "error");
    } finally {
      setConfirmStatusOpen(false);
      setPendingStatus(null);
    }
  }

  async function handleDelete() {
    if (!user) return;
    try {
      await deleteUser.mutateAsync(user.id);
      showToast("User permanently deleted and pseudonymized.", "success");
      router.push("/iam/users");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : "Failed to delete user.";
      showToast(msg, "error");
    } finally {
      setConfirmDeleteOpen(false);
      setDeleteEmailInput("");
    }
  }

  if (isLoading) {
    return (
      <>
        <PageHeader title="User" description="Loading…" testId="heading-user-detail" />
        <div className="px-8 py-6 space-y-3">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-6 w-64" />
          <Skeleton className="h-6 w-32" />
        </div>
      </>
    );
  }

  if (isError || !user) {
    return (
      <>
        <PageHeader title="User" description="Not found" testId="heading-user-detail" />
        <div className="px-8 py-6">
          <ErrorState
            message={error instanceof Error ? error.message : "User not found."}
          />
        </div>
      </>
    );
  }

  const deleteEmailMatches =
    deleteEmailInput === (user.email ?? "");

  return (
    <>
      <PageHeader
        title={user.display_name ?? user.id}
        description={user.email ?? "No email"}
        testId="heading-user-detail"
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-8">
        {/* Status section */}
        <section className="flex items-center gap-4" data-testid="user-status-section">
          <span className="text-sm text-zinc-500">Status</span>
          <Badge
            variant={user.is_active ? "success" : "warning"}
            data-testid="user-status-badge"
          >
            {user.is_active ? "Active" : "Inactive"}
          </Badge>

          {user.is_active ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={openDeactivate}
              data-testid="btn-deactivate"
            >
              Deactivate
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={openReactivate}
              data-testid="btn-reactivate"
            >
              Reactivate
            </Button>
          )}

          <Button
            variant="danger"
            size="sm"
            onClick={() => {
              setDeleteEmailInput("");
              setConfirmDeleteOpen(true);
            }}
            data-testid="btn-delete"
          >
            Delete
          </Button>
        </section>

        {/* Info section */}
        <section className="grid grid-cols-2 gap-4 max-w-xl">
          <div>
            <p className="text-xs text-zinc-500 mb-1">ID</p>
            <p className="text-sm font-mono" data-testid="user-id">{user.id}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Account Type</p>
            <p className="text-sm" data-testid="user-account-type">{user.account_type}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Email</p>
            <p className="text-sm" data-testid="user-email">{user.email ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Display Name</p>
            <p className="text-sm" data-testid="user-display-name">{user.display_name ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Created</p>
            <p className="text-sm">{user.created_at}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500 mb-1">Last Updated</p>
            <p className="text-sm">{user.updated_at}</p>
          </div>
        </section>
      </div>

      {/* Deactivate / Reactivate confirmation modal */}
      <Modal
        open={confirmStatusOpen}
        onClose={() => setConfirmStatusOpen(false)}
        title={pendingStatus === "active" ? "Reactivate user?" : "Deactivate user?"}
      >
        <div className="space-y-4">
          {pendingStatus === "inactive" ? (
            <p className="text-sm text-zinc-700">
              Deactivating will immediately revoke all active sessions. The user
              will be blocked from signing in until reactivated. Their data is
              preserved.
            </p>
          ) : (
            <p className="text-sm text-zinc-700">
              The user will be able to sign in again. No sessions are restored
              automatically.
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => setConfirmStatusOpen(false)}
              data-testid="btn-cancel-status"
            >
              Cancel
            </Button>
            <Button
              variant={pendingStatus === "inactive" ? "warning" : "primary"}
              onClick={handleStatusChange}
              loading={updateUser.isPending}
              data-testid="btn-confirm-status"
            >
              {pendingStatus === "active" ? "Reactivate" : "Deactivate"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete confirmation modal — requires typing email */}
      <Modal
        open={confirmDeleteOpen}
        onClose={() => setConfirmDeleteOpen(false)}
        title="Permanently delete user"
      >
        <div className="space-y-4">
          <p className="text-sm text-zinc-700">
            This action is <strong>irreversible</strong>. The user&apos;s email and
            display name will be pseudonymized. Audit history is preserved.
          </p>
          <p className="text-sm text-zinc-700">
            Type the user&apos;s email address to confirm:
          </p>
          <Field label={`Email: ${user.email ?? "—"}`}>
            <Input
              value={deleteEmailInput}
              onChange={(e) => setDeleteEmailInput(e.target.value)}
              placeholder={user.email ?? ""}
              data-testid="input-confirm-email"
            />
          </Field>
          <div className="flex justify-end gap-2">
            <Button
              variant="secondary"
              onClick={() => {
                setConfirmDeleteOpen(false);
                setDeleteEmailInput("");
              }}
              data-testid="btn-cancel-delete"
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={!deleteEmailMatches}
              loading={deleteUser.isPending}
              data-testid="btn-confirm-delete"
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
}
