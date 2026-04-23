"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  Checkbox,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Select,
  Skeleton,
  StatCard,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { ConfirmDialog } from "@/components/confirm-dialog";
import {
  useCreateUser,
  useDeleteUser,
  useUsers,
} from "@/features/iam-users/hooks/use-users";
import { ApiClientError } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import { useTableSort } from "@/lib/table-sort";
import type { AccountType } from "@/types/api";

const ACCOUNT_TYPES: { value: AccountType; label: string }[] = [
  { value: "email_password", label: "Email + Password" },
  { value: "magic_link", label: "Magic Link" },
  { value: "google_oauth", label: "Google OAuth" },
  { value: "github_oauth", label: "GitHub OAuth" },
];

const ACCOUNT_TYPE_LABEL: Record<AccountType, string> = ACCOUNT_TYPES.reduce(
  (acc, t) => ({ ...acc, [t.value]: t.label }),
  {} as Record<AccountType, string>,
);

type BadgeToneType = "default" | "blue" | "purple" | "cyan" | "success" | "warning" | "danger" | "info" | "emerald" | "red" | "amber";

const ACCOUNT_TYPE_TONE: Record<AccountType, BadgeToneType> = {
  email_password: "default",
  google_oauth: "blue",
  github_oauth: "default",
  magic_link: "purple",
};

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

export default function UsersPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [filterType, setFilterType] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [openCreate, setOpenCreate] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const del = useDeleteUser();

  const { data, isLoading, isError, error, refetch } = useUsers({
    limit: 500,
    account_type: filterType || undefined,
  });

  const allItems = data?.items ?? [];

  const filtered = allItems.filter((u) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (u.email ?? "").toLowerCase().includes(q) ||
      (u.display_name ?? "").toLowerCase().includes(q)
    );
  });

  const { sorted, toggle, dirFor } = useTableSort(filtered, {
    display_name: (u) => u.display_name ?? u.email ?? u.id,
    email: (u) => u.email ?? "",
    account_type: (u) => u.account_type,
    is_active: (u) => u.is_active,
  });

  const visibleIds = sorted.map((u) => u.id);
  const allSelected =
    visibleIds.length > 0 && visibleIds.every((id) => selectedIds.has(id));

  // Stats
  const totalUsers = allItems.length;
  const activeUsers = allItems.filter((u) => u.is_active).length;
  const verifiedUsers = allItems.filter((u) => !!u.email).length;

  function toggleRow(id: string, checked: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleAll(checked: boolean) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) visibleIds.forEach((id) => next.add(id));
      else visibleIds.forEach((id) => next.delete(id));
      return next;
    });
  }

  async function handleBulkDelete() {
    const ids = Array.from(selectedIds);
    let ok = 0;
    let err = 0;
    for (const id of ids) {
      try {
        await del.mutateAsync(id);
        ok += 1;
      } catch {
        err += 1;
      }
    }
    setBulkDeleteOpen(false);
    setSelectedIds(new Set());
    if (err === 0) toast(`Deleted ${ok} user${ok === 1 ? "" : "s"}`, "success");
    else toast(`Deleted ${ok}, failed ${err}`, err === ids.length ? "error" : "warning");
  }

  return (
    <>
      <PageHeader
        title="Users"
        description="Human & service identities. account_type drives auth. Email / display_name / avatar stored as EAV attrs."
        testId="heading-users"
        actions={
          <>
            {selectedIds.size > 0 && (
              <Button
                variant="danger"
                onClick={() => setBulkDeleteOpen(true)}
                data-testid="users-bulk-delete"
              >
                Delete {selectedIds.size}
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() =>
                downloadCsv("users", filtered, [
                  { key: "id", accessor: (u) => u.id },
                  { key: "email", accessor: (u) => u.email ?? "" },
                  { key: "display_name", accessor: (u) => u.display_name ?? "" },
                  { key: "account_type", accessor: (u) => u.account_type },
                  { key: "is_active", accessor: (u) => u.is_active },
                  { key: "created_at", accessor: (u) => u.created_at },
                ])
              }
              disabled={filtered.length === 0}
              data-testid="users-export-csv"
            >
              Export CSV
            </Button>
            <Button
              variant="primary"
              onClick={() => setOpenCreate(true)}
              data-testid="open-create-user"
            >
              + New user
            </Button>
          </>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 animate-fade-in" data-testid="users-body">

        {/* Stat cards */}
        {!isLoading && !isError && (
          <div className="mb-6 grid grid-cols-3 gap-4">
            <StatCard
              label="Total Users"
              value={totalUsers}
              sub="all identities"
              accent="blue"
            />
            <StatCard
              label="Active"
              value={activeUsers}
              sub="can sign in"
              accent="green"
            />
            <StatCard
              label="With Email"
              value={verifiedUsers}
              sub="have email address"
              accent="blue"
            />
          </div>
        )}

        {/* Filter bar */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className="label-caps"
              style={{ color: "var(--text-muted)" }}
            >
              TYPE
            </span>
            <Select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-52"
              data-testid="filter-user-type"
            >
              <option value="">All account types</option>
              {ACCOUNT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="relative">
            <span
              className="absolute left-3 top-1/2 -translate-y-1/2 label-caps pointer-events-none"
              style={{ color: "var(--text-muted)" }}
            >
              FILTER
            </span>
            <Input
              type="search"
              placeholder="email or name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-72 pl-16"
              data-testid="search-users"
            />
          </div>
          <span
            className="ml-auto rounded px-2 py-0.5 text-xs font-mono"
            style={{
              background: "var(--bg-elevated)",
              color: "var(--text-secondary)",
              border: "1px solid var(--border)",
            }}
          >
            {filtered.length} {filtered.length === 1 ? "user" : "users"}
          </span>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        )}

        {/* Error */}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}

        {/* Empty */}
        {!isLoading && filtered.length === 0 && (
          <EmptyState
            title={data && data.items.length === 0 ? "No users" : "No matches"}
            description={
              data && data.items.length === 0
                ? "Create your first user. Email & display_name go into EAV."
                : "Try a different filter or search term."
            }
            action={
              data && data.items.length === 0 ? (
                <Button variant="primary" onClick={() => setOpenCreate(true)}>+ New user</Button>
              ) : undefined
            }
          />
        )}

        {/* Table */}
        {sorted.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH className="w-8">
                  <Checkbox
                    checked={allSelected}
                    onChange={(e) => toggleAll(e.target.checked)}
                    aria-label="Select all visible users"
                    data-testid="users-select-all"
                  />
                </TH>
                <TH
                  sortable
                  sortDir={dirFor("display_name")}
                  onSort={() => toggle("display_name")}
                  testId="sort-user-name"
                >
                  User
                </TH>
                <TH
                  sortable
                  sortDir={dirFor("email")}
                  onSort={() => toggle("email")}
                  testId="sort-user-email"
                >
                  Email
                </TH>
                <TH
                  sortable
                  sortDir={dirFor("account_type")}
                  onSort={() => toggle("account_type")}
                  testId="sort-user-type"
                >
                  Auth Type
                </TH>
                <TH
                  sortable
                  sortDir={dirFor("is_active")}
                  onSort={() => toggle("is_active")}
                  testId="sort-user-status"
                >
                  Status
                </TH>
              </tr>
            </THead>
            <TBody>
              {sorted.map((u) => {
                const initial = (
                  u.display_name?.trim() ||
                  u.email?.trim() ||
                  u.id
                )
                  .slice(0, 1)
                  .toUpperCase();
                const shortId = u.id.slice(0, 8);
                const hasName = !!u.display_name?.trim();
                const hasEmail = !!u.email?.trim();
                return (
                  <TR
                    key={u.id}
                    onClick={((e: React.MouseEvent<HTMLTableRowElement>) => {
                      if ((e.target as HTMLElement).closest('[data-row-select="true"]')) {
                        return;
                      }
                      router.push(`/iam/users/${u.id}`);
                    }) as unknown as () => void}
                    data-testid={`user-row-${u.id}`}
                  >
                    <TD className="w-8">
                      <span data-row-select="true">
                        <Checkbox
                          checked={selectedIds.has(u.id)}
                          onChange={(e) => toggleRow(u.id, e.target.checked)}
                          aria-label={`Select ${u.display_name ?? u.email ?? u.id}`}
                          data-testid={`user-select-${u.id}`}
                        />
                      </span>
                    </TD>
                    <TD>
                      <div className="flex items-center gap-2.5">
                        {u.avatar_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={u.avatar_url}
                            alt=""
                            className="h-7 w-7 rounded-full object-cover"
                            style={{ border: "1px solid var(--border)" }}
                          />
                        ) : (
                          <div
                            className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold"
                            style={{
                              background: "var(--accent-muted)",
                              color: "var(--accent)",
                              border: "1px solid var(--accent-dim)",
                            }}
                          >
                            {initial}
                          </div>
                        )}
                        <span style={{ color: "var(--text-primary)" }}>
                          {hasName ? (
                            u.display_name
                          ) : (
                            <span className="font-mono-data text-xs" style={{ color: "var(--text-muted)" }}>
                              user-{shortId}
                            </span>
                          )}
                        </span>
                      </div>
                    </TD>
                    <TD>
                      {hasEmail ? (
                        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>{u.email}</span>
                      ) : (
                        <span className="text-xs italic" style={{ color: "var(--text-muted)" }}>
                          no email
                        </span>
                      )}
                    </TD>
                    <TD>
                      <Badge tone={ACCOUNT_TYPE_TONE[u.account_type] ?? "default"}>
                        {ACCOUNT_TYPE_LABEL[u.account_type] ?? u.account_type}
                      </Badge>
                    </TD>
                    <TD>
                      <Badge tone={u.is_active ? "success" : "default"} dot={u.is_active}>
                        {u.is_active ? "active" : "inactive"}
                      </Badge>
                    </TD>
                  </TR>
                );
              })}
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
      <ConfirmDialog
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        onConfirm={handleBulkDelete}
        title={`Delete ${selectedIds.size} user${selectedIds.size === 1 ? "" : "s"}?`}
        description="This permanently deletes the selected users. Their email + display_name are pseudonymized; audit history is preserved."
        confirmLabel={`Delete ${selectedIds.size}`}
        tone="danger"
        loading={del.isPending}
        testId="users-bulk-delete-confirm"
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
  const router = useRouter();
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
      router.push(`/iam/users/${user.id}`);
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
            variant="primary"
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
