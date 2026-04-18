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
  useUsers,
} from "@/features/iam-users/hooks/use-users";
import { ApiClientError } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
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
  const [filterType, setFilterType] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [openCreate, setOpenCreate] = useState(false);

  const { data, isLoading, isError, error, refetch } = useUsers({
    limit: 500,
    account_type: filterType || undefined,
  });

  const filtered = (data?.items ?? []).filter((u) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (u.email ?? "").toLowerCase().includes(q) ||
      (u.display_name ?? "").toLowerCase().includes(q)
    );
  });

  return (
    <>
      <PageHeader
        title="Users"
        description="Human & service identities. account_type drives auth. Email / display_name / avatar stored as EAV attrs."
        testId="heading-users"
        actions={
          <>
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
              onClick={() => setOpenCreate(true)}
              data-testid="open-create-user"
            >
              + New user
            </Button>
          </>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="users-body">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label className="text-xs text-zinc-500">Type</label>
            <Select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-56"
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
          <Input
            type="search"
            placeholder="Search email or name…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
            data-testid="search-users"
          />
          <span className="ml-auto text-xs text-zinc-500">
            {filtered.length} {filtered.length === 1 ? "user" : "users"}
          </span>
        </div>
        {isLoading && <Skeleton className="h-12 w-full" />}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
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
                <Button onClick={() => setOpenCreate(true)}>+ New user</Button>
              ) : undefined
            }
          />
        )}
        {filtered.length > 0 && (
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
              {filtered.map((u) => {
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
                    onClick={() => router.push(`/iam/users/${u.id}`)}
                    data-testid={`user-row-${u.id}`}
                  >
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
                            {initial}
                          </div>
                        )}
                        <span>
                          {hasName ? (
                            u.display_name
                          ) : (
                            <span className="font-mono text-xs text-zinc-500">
                              user-{shortId}
                            </span>
                          )}
                        </span>
                      </div>
                    </TD>
                    <TD>
                      {hasEmail ? (
                        <span className="text-xs text-zinc-500">{u.email}</span>
                      ) : (
                        <span className="text-xs text-zinc-400 italic">
                          no email set
                        </span>
                      )}
                    </TD>
                    <TD>
                      <Badge tone="blue">
                        {ACCOUNT_TYPE_LABEL[u.account_type] ?? u.account_type}
                      </Badge>
                    </TD>
                    <TD>
                      <Badge tone={u.is_active ? "emerald" : "zinc"}>
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
