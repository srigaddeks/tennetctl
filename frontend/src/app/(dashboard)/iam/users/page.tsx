"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useCreateUser,
  useDeleteUser,
  useUpdateUser,
  useUser,
  useUsers,
} from "@/features/iam-users/hooks/use-users";
import { ApiClientError } from "@/lib/api";
import type { AccountType } from "@/types/api";

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "email_password", label: "Email + Password" },
  { value: "magic_link", label: "Magic Link" },
  { value: "google_oauth", label: "Google OAuth" },
  { value: "github_oauth", label: "GitHub OAuth" },
];

const createSchema = z.object({
  account_type: z.enum([
    "email_password",
    "magic_link",
    "google_oauth",
    "github_oauth",
  ]),
  email: z.email("invalid email"),
  display_name: z.string().min(1),
  avatar_url: z.string().url().optional().or(z.literal("")),
});
type CreateForm = z.infer<typeof createSchema>;

const updateSchema = z.object({
  email: z.email().optional().or(z.literal("")),
  display_name: z.string().min(1).optional(),
  avatar_url: z.string().url().optional().or(z.literal("")),
  is_active: z.boolean().optional(),
});
type UpdateForm = z.infer<typeof updateSchema>;

export default function UsersPage() {
  const [filterType, setFilterType] = useState<string>("");
  const [openCreate, setOpenCreate] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useUsers({
    limit: 100,
    account_type: filterType || undefined,
  });

  return (
    <>
      <PageHeader
        title="Users"
        description="Human & service identities. account_type drives auth. Email / display_name / avatar stored as EAV attrs."
        testId="heading-users"
        actions={
          <Button
            onClick={() => setOpenCreate(true)}
            data-testid="open-create-user"
          >
            + New user
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="users-body">
        <div className="mb-4 flex items-center gap-2">
          <label className="text-xs text-zinc-500">Filter by type</label>
          <Select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="w-64"
          >
            <option value="">All account types</option>
            {ACCOUNT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </div>
        {isLoading && <Skeleton className="h-12 w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No users"
            description="Create your first user. Email & display_name go into EAV."
            action={<Button onClick={() => setOpenCreate(true)}>+ New user</Button>}
          />
        )}
        {data && data.items.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>User</TH>
                <TH>Email</TH>
                <TH>Type</TH>
                <TH>Status</TH>
              </tr>
            </THead>
            <TBody>
              {data.items.map((u) => (
                <TR key={u.id} onClick={() => setSelected(u.id)}>
                  <TD>
                    <div className="flex items-center gap-2.5">
                      {u.avatar_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={u.avatar_url}
                          alt=""
                          className="h-7 w-7 rounded-full object-cover"
                        />
                      ) : (
                        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-zinc-200 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                          {(u.display_name ?? u.email ?? "?")
                            .slice(0, 1)
                            .toUpperCase()}
                        </div>
                      )}
                      <span>
                        {u.display_name ?? (
                          <span className="text-zinc-400">—</span>
                        )}
                      </span>
                    </div>
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500">
                      {u.email ?? "—"}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone="blue">{u.account_type}</Badge>
                  </TD>
                  <TD>
                    <Badge tone={u.is_active ? "emerald" : "zinc"}>
                      {u.is_active ? "active" : "inactive"}
                    </Badge>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      {openCreate && (
        <CreateUserDialog
          open={openCreate}
          onClose={() => setOpenCreate(false)}
        />
      )}
      <UserDetailDrawer
        userId={selected}
        onClose={() => setSelected(null)}
      />
    </>
  );
}

function CreateUserDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateUser();
  const form = useForm<CreateForm>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      account_type: "email_password",
      email: "",
      display_name: "",
      avatar_url: "",
    },
  });

  async function onSubmit(values: CreateForm) {
    try {
      const user = await create.mutateAsync({
        account_type: values.account_type,
        email: values.email,
        display_name: values.display_name,
        ...(values.avatar_url ? { avatar_url: values.avatar_url } : {}),
      });
      toast(`Created user ${user.email}`, "success");
      form.reset();
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New user">
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className="flex flex-col gap-4"
        data-testid="create-user-form"
      >
        <Field
          label="Account type"
          required
          error={form.formState.errors.account_type?.message}
        >
          <Select
            {...form.register("account_type")}
            data-testid="create-user-account-type"
          >
            {ACCOUNT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Email"
          required
          error={form.formState.errors.email?.message}
        >
          <Input
            type="email"
            autoComplete="off"
            placeholder="alice@example.com"
            {...form.register("email")}
            data-testid="create-user-email"
          />
        </Field>
        <Field
          label="Display name"
          required
          error={form.formState.errors.display_name?.message}
        >
          <Input
            placeholder="Alice"
            {...form.register("display_name")}
            data-testid="create-user-display-name"
          />
        </Field>
        <Field
          label="Avatar URL"
          hint="optional"
          error={form.formState.errors.avatar_url?.message}
        >
          <Input
            placeholder="https://…"
            {...form.register("avatar_url")}
          />
        </Field>
        <div className="mt-2 flex justify-end gap-2">
          <Button variant="secondary" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            data-testid="create-user-submit"
          >
            Create
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function UserDetailDrawer({
  userId,
  onClose,
}: {
  userId: string | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const { data: user, isLoading } = useUser(userId);
  const update = useUpdateUser();
  const del = useDeleteUser();

  const form = useForm<UpdateForm>({
    resolver: zodResolver(updateSchema),
    defaultValues: {
      email: "",
      display_name: "",
      avatar_url: "",
      is_active: true,
    },
  });

  useEffect(() => {
    if (user) {
      form.reset({
        email: user.email ?? "",
        display_name: user.display_name ?? "",
        avatar_url: user.avatar_url ?? "",
        is_active: user.is_active,
      });
    }
  }, [user, form]);

  async function onSubmit(values: UpdateForm) {
    if (!userId) return;
    const dirty = form.formState.dirtyFields;
    const body: UpdateForm = {};
    if (dirty.email) body.email = values.email;
    if (dirty.display_name) body.display_name = values.display_name;
    if (dirty.avatar_url) body.avatar_url = values.avatar_url;
    if (dirty.is_active) body.is_active = values.is_active;
    if (Object.keys(body).length === 0) {
      toast("No changes", "info");
      return;
    }
    try {
      await update.mutateAsync({ id: userId, body });
      toast("Saved", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  async function onDelete() {
    if (!userId) return;
    if (!confirm(`Delete user "${user?.email ?? userId}"?`)) return;
    try {
      await del.mutateAsync(userId);
      toast("Deleted", "success");
      onClose();
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={userId !== null}
      onClose={onClose}
      title={user?.display_name ?? "User"}
      description={user?.email ?? undefined}
    >
      {isLoading && <p className="text-sm text-zinc-500">Loading…</p>}
      {user && (
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="flex flex-col gap-4"
        >
          <div className="flex items-center gap-3">
            {user.avatar_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={user.avatar_url}
                alt=""
                className="h-10 w-10 rounded-full object-cover"
              />
            )}
            <div>
              <Badge tone="blue">{user.account_type}</Badge>
              <div className="mt-1 text-xs text-zinc-500 font-mono">
                id: {user.id.slice(0, 8)}…
              </div>
            </div>
          </div>
          <Field label="Email" error={form.formState.errors.email?.message}>
            <Input type="email" {...form.register("email")} />
          </Field>
          <Field
            label="Display name"
            error={form.formState.errors.display_name?.message}
          >
            <Input {...form.register("display_name")} />
          </Field>
          <Field label="Avatar URL">
            <Input {...form.register("avatar_url")} />
          </Field>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...form.register("is_active")} />
            Active
          </label>
          <div className="mt-2 flex justify-between border-t border-zinc-200 pt-4 dark:border-zinc-800">
            <Button
              variant="danger"
              type="button"
              size="sm"
              onClick={onDelete}
              loading={del.isPending}
            >
              Delete
            </Button>
            <div className="flex gap-2">
              <Button variant="secondary" type="button" onClick={onClose}>
                Close
              </Button>
              <Button
                type="submit"
                loading={update.isPending}
                disabled={!form.formState.isDirty}
              >
                Save
              </Button>
            </div>
          </div>
        </form>
      )}
    </Modal>
  );
}
