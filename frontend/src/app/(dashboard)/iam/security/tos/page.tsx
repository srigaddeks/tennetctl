"use client";

import { useState } from "react";

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
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
  Textarea,
} from "@/components/ui";
import {
  useCreateTosVersion,
  useMarkTosEffective,
  useTosVersions,
} from "@/features/iam-security/hooks/use-tos";
import { ApiClientError } from "@/lib/api";
import type { TosVersion } from "@/types/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "Terms of Service" },
];

export default function TosPage() {
  const { data: versions = [], isLoading, isError, error, refetch } =
    useTosVersions();
  const [createOpen, setCreateOpen] = useState(false);
  const [effectiveTarget, setEffectiveTarget] = useState<TosVersion | null>(
    null,
  );

  return (
    <>
      <PageHeader
        title="Terms of Service"
        description="Publish new Terms of Service versions. Users must re-accept when a new version goes into effect."
        testId="heading-iam-tos"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            data-testid="btn-new-tos"
            onClick={() => setCreateOpen(true)}
          >
            + New version
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="iam-tos-body">
        {isLoading && (
          <div className="flex flex-col gap-2">
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
        {!isLoading && !isError && versions.length === 0 && (
          <EmptyState
            title="No ToS versions"
            description="Draft and publish a version to capture user acceptance."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + New version
              </Button>
            }
          />
        )}
        {versions.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Version</TH>
                <TH>Title</TH>
                <TH>Status</TH>
                <TH>Effective</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {versions.map((v) => (
                <TR key={v.id} data-testid={`tos-row-${v.id}`}>
                  <TD>
                    <span className="font-mono text-xs">{v.version}</span>
                  </TD>
                  <TD>{v.title}</TD>
                  <TD>
                    {v.effective_at ? (
                      <Badge tone="emerald">active</Badge>
                    ) : (
                      <Badge tone="zinc">draft</Badge>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {v.effective_at
                        ? new Date(v.effective_at).toLocaleDateString()
                        : "—"}
                    </span>
                  </TD>
                  <TD className="text-right">
                    {!v.effective_at && (
                      <Button
                        variant="ghost"
                        size="sm"
                        type="button"
                        data-testid={`tos-activate-${v.id}`}
                        onClick={() => setEffectiveTarget(v)}
                      >
                        Activate
                      </Button>
                    )}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <CreateTosDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      <ActivateTosDialog
        version={effectiveTarget}
        onClose={() => setEffectiveTarget(null)}
      />
    </>
  );
}

function CreateTosDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateTosVersion();
  const [form, setForm] = useState({
    version: "",
    title: "",
    body_markdown: "",
  });
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await create.mutateAsync(form);
      toast(`Published version "${form.version}"`, "success");
      setForm({ version: "", title: "", body_markdown: "" });
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="New ToS version" size="md">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="create-tos-form"
      >
        <Field label="Version" htmlFor="tos-version" required hint="e.g. 2026-04">
          <Input
            id="tos-version"
            value={form.version}
            onChange={(e) =>
              setForm((f) => ({ ...f, version: e.target.value }))
            }
            placeholder="2026-04"
            autoFocus
            required
            data-testid="create-tos-version"
          />
        </Field>
        <Field label="Title" htmlFor="tos-title" required>
          <Input
            id="tos-title"
            value={form.title}
            onChange={(e) =>
              setForm((f) => ({ ...f, title: e.target.value }))
            }
            placeholder="Terms of Service — April 2026"
            required
            data-testid="create-tos-title"
          />
        </Field>
        <Field
          label="Body (Markdown)"
          htmlFor="tos-body"
          hint="Rendered in-app when a user is asked to accept."
        >
          <Textarea
            id="tos-body"
            value={form.body_markdown}
            onChange={(e) =>
              setForm((f) => ({ ...f, body_markdown: e.target.value }))
            }
            rows={8}
            className="font-mono"
            data-testid="create-tos-body"
          />
        </Field>
        {err && <p className="text-xs text-red-600">{err}</p>}
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={create.isPending}
            disabled={!form.version || !form.title}
            data-testid="create-tos-submit"
          >
            Publish draft
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function ActivateTosDialog({
  version,
  onClose,
}: {
  version: TosVersion | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const mark = useMarkTosEffective();
  const [effectiveAt, setEffectiveAt] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!version) return;
    setErr(null);
    try {
      await mark.mutateAsync({
        id: version.id,
        effective_at: new Date(effectiveAt).toISOString(),
      });
      toast(`Version "${version.version}" activated`, "success");
      setEffectiveAt("");
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal
      open={version !== null}
      onClose={onClose}
      title="Activate ToS version"
      description={
        version
          ? `Set the effective date for "${version.version}". All users will be required to re-accept.`
          : undefined
      }
      size="sm"
    >
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="activate-tos-form"
      >
        <Field label="Effective at" htmlFor="tos-effective-at" required>
          <Input
            id="tos-effective-at"
            type="datetime-local"
            value={effectiveAt}
            onChange={(e) => setEffectiveAt(e.target.value)}
            required
            data-testid="activate-tos-datetime"
          />
        </Field>
        {err && <p className="text-xs text-red-600">{err}</p>}
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={mark.isPending}
            disabled={!effectiveAt}
            data-testid="activate-tos-submit"
          >
            Activate
          </Button>
        </div>
      </form>
    </Modal>
  );
}
