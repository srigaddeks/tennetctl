"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  Table,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui";
import {
  useCreateShortLink,
  useDeleteShortLink,
  useShortLinks,
} from "@/features/product-ops/hooks/use-short-links";

export default function LinkShortenerPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [showForm, setShowForm] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = useShortLinks(workspaceId);
  const del = useDeleteShortLink();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Link Shortener"
        description="Slug → target URL with optional UTM preset. /l/{slug} redirects + emits a click event into the product event stream."
        actions={
          <Button
            variant="primary"
            onClick={() => setShowForm((v) => !v)}
            data-testid="link-shortener-new-toggle"
          >
            {showForm ? "Cancel" : "New link"}
          </Button>
        }
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to view & manage links."
        />
      )}

      {workspaceId && showForm && (
        <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />
      )}

      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && list.isError && (
        <ErrorState
          message={list.error instanceof Error ? list.error.message : "Failed to load links"}
          retry={() => {
            void list.refetch();
          }}
        />
      )}

      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState
          title="No short links yet"
          description="Create one above to get started."
        />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Slug</TH>
                <TH>Target</TH>
                <TH>UTM</TH>
                <TH>Status</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map((l) => (
                <TR key={l.id} data-testid={`short-link-row-${l.id}`}>
                  <TD>
                    <code className="text-xs">{l.slug}</code>
                  </TD>
                  <TD>
                    <span className="break-all text-xs">{l.target_url}</span>
                  </TD>
                  <TD className="text-xs">
                    {l.utm_source && <Badge tone="blue">{l.utm_source}</Badge>}{" "}
                    {l.utm_campaign && <span>{l.utm_campaign}</span>}
                  </TD>
                  <TD>
                    {l.is_active ? <Badge tone="emerald">active</Badge> : <Badge tone="zinc">inactive</Badge>}
                  </TD>
                  <TD>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        if (confirm(`Delete /l/${l.slug}?`)) {
                          del.mutate(l.id);
                        }
                      }}
                      data-testid={`short-link-delete-${l.slug}`}
                    >
                      Delete
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function CreateForm({ workspaceId, onDone }: { workspaceId: string; onDone: () => void }) {
  const create = useCreateShortLink();
  const [slug, setSlug] = useState<string>("");
  const [targetUrl, setTargetUrl] = useState<string>("");
  const [utmSource, setUtmSource] = useState<string>("");
  const [utmCampaign, setUtmCampaign] = useState<string>("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await create.mutateAsync({
      workspace_id: workspaceId,
      slug: slug || undefined,
      target_url: targetUrl,
      utm_source: utmSource || undefined,
      utm_campaign: utmCampaign || undefined,
    });
    setSlug("");
    setTargetUrl("");
    setUtmSource("");
    setUtmCampaign("");
    onDone();
  };

  return (
    <form
      onSubmit={onSubmit}
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
      data-testid="short-link-create-form"
    >
      <div className="grid grid-cols-2 gap-4">
        <Field label="Slug (optional — auto-mints if blank)" htmlFor="slug">
          <Input
            id="slug"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="launch"
            data-testid="short-link-slug"
          />
        </Field>
        <Field label="Target URL" required htmlFor="target">
          <Input
            id="target"
            type="url"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            required
            placeholder="https://example.com/landing"
            data-testid="short-link-target"
          />
        </Field>
        <Field label="UTM Source (optional)" htmlFor="utm-source">
          <Input
            id="utm-source"
            value={utmSource}
            onChange={(e) => setUtmSource(e.target.value)}
            placeholder="twitter"
          />
        </Field>
        <Field label="UTM Campaign (optional)" htmlFor="utm-campaign">
          <Input
            id="utm-campaign"
            value={utmCampaign}
            onChange={(e) => setUtmCampaign(e.target.value)}
            placeholder="launch_2026"
          />
        </Field>
      </div>
      {create.isError && (
        <p className="text-sm text-red-600">
          {create.error instanceof Error ? create.error.message : "Create failed"}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onDone}>
          Cancel
        </Button>
        <Button type="submit" variant="primary" disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </div>
    </form>
  );
}
