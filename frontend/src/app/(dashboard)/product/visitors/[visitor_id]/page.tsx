"use client";

import { use } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge, ErrorState, Skeleton } from "@/components/ui";
import { useProductVisitor } from "@/features/product-ops/hooks/use-product-events";

type Props = { params: Promise<{ visitor_id: string }> };

export default function VisitorDetailPage({ params }: Props) {
  const { visitor_id } = use(params);
  const query = useProductVisitor(visitor_id);

  if (query.isLoading) return <Skeleton className="h-72 w-full" />;
  if (query.isError) {
    return (
      <ErrorState
        message={query.error instanceof Error ? query.error.message : "Failed to load visitor"}
        retry={() => {
          void query.refetch();
        }}
      />
    );
  }
  const v = query.data;
  if (!v) return null;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Visitor"
        description={`anonymous_id: ${v.anonymous_id}`}
      />
      <section className="grid grid-cols-2 gap-6">
        <Card title="Identity">
          <KV k="ID" v={<code className="text-xs">{v.id}</code>} />
          <KV k="Anonymous" v={<code className="text-xs">{v.anonymous_id}</code>} />
          <KV k="User" v={v.user_id ? <code>{v.user_id}</code> : <span className="text-zinc-400">unidentified</span>} />
          <KV k="Workspace" v={<code className="text-xs">{v.workspace_id}</code>} />
          <KV k="First seen" v={v.first_seen} />
          <KV k="Last seen" v={v.last_seen} />
          <KV k="Active" v={v.is_active ? <Badge tone="emerald">active</Badge> : <Badge tone="zinc">inactive</Badge>} />
          {v.is_deleted && <KV k="Deleted" v={<Badge tone="red">{v.deleted_at ?? "yes"}</Badge>} />}
        </Card>

        <Card title="First touch (sticky)">
          {v.first_utm_source || v.first_referrer ? (
            <>
              <KV k="UTM source" v={v.first_utm_source ?? "—"} />
              <KV k="UTM medium" v={v.first_utm_medium ?? "—"} />
              <KV k="UTM campaign" v={v.first_utm_campaign ?? "—"} />
              <KV k="UTM term" v={v.first_utm_term ?? "—"} />
              <KV k="UTM content" v={v.first_utm_content ?? "—"} />
              <KV k="Referrer" v={v.first_referrer ?? "—"} />
              <KV k="Landing URL" v={<span className="text-xs break-all">{v.first_landing_url ?? "—"}</span>} />
            </>
          ) : (
            <p className="text-sm text-zinc-500">No first-touch attribution captured.</p>
          )}
        </Card>

        <Card title="Last touch">
          {v.last_touch ? (
            <>
              <KV k="Occurred at" v={v.last_touch.occurred_at ?? "—"} />
              <KV k="UTM source" v={v.last_touch.utm_source ?? "—"} />
              <KV k="UTM campaign" v={v.last_touch.utm_campaign ?? "—"} />
              <KV k="Referrer" v={v.last_touch.referrer ?? "—"} />
              <KV k="Landing URL" v={<span className="text-xs break-all">{v.last_touch.landing_url ?? "—"}</span>} />
            </>
          ) : (
            <p className="text-sm text-zinc-500">No touches recorded.</p>
          )}
        </Card>

        <Card title={`Aliases (${v.aliases.length})`}>
          {v.aliases.length === 0 ? (
            <p className="text-sm text-zinc-500">No cross-device aliases linked.</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {v.aliases.map((a) => (
                <li key={a.alias_anonymous_id} className="flex items-center justify-between">
                  <code className="text-xs">{a.alias_anonymous_id}</code>
                  <span className="text-xs text-zinc-500">{a.linked_at}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <h3 className="mb-3 text-sm font-semibold">{title}</h3>
      <dl className="space-y-2 text-sm">{children}</dl>
    </section>
  );
}

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-zinc-500">{k}</dt>
      <dd className="break-all text-right">{v}</dd>
    </div>
  );
}
