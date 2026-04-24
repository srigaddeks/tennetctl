"use client";

import { use } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { AlertRuleEditor } from "@/features/monitoring/_components/alert-rule-editor";
import { useAlertRule } from "@/features/monitoring/hooks/use-alert-rules";

export default function EditAlertRulePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { data } = useAlertRule(id);

  return (
    <>
      <PageHeader
        title="Edit alert rule"
        description="Update the DSL query, threshold, severity, or notification template."
        testId="heading-monitoring-alert-rule-edit"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts", href: "/monitoring/alerts" },
          { label: "Rules", href: "/monitoring/alerts/rules" },
          { label: data?.name ?? "Edit rule" },
        ]}
      />
      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {/* Rule identity strip */}
        {data && (
          <div
            className="mb-5 rounded border px-4 py-3 flex items-center gap-3"
            style={{
              background: "var(--bg-surface)",
              borderColor: "var(--border)",
              borderLeft: "3px solid #9d6ef8",
            }}
          >
            <div className="flex-1">
              <div
                className="text-[13px] font-semibold"
                style={{ color: "var(--text-primary)" }}
              >
                {data.name}
              </div>
              <div
                className="font-mono-data text-[11px]"
                style={{ color: "var(--text-muted)" }}
              >
                {id}
              </div>
            </div>
            {data.labels?.application_id && (
              <Link
                href={`/iam/applications/${data.labels.application_id}`}
                className="font-mono-data text-[11px] hover:underline"
                style={{ color: "var(--accent)" }}
                data-testid="alert-rule-application-link"
              >
                app {data.labels.application_id.slice(0, 8)} →
              </Link>
            )}
            <div
              className="label-caps"
              style={{
                color: data.is_active ? "var(--success)" : "var(--text-muted)",
              }}
            >
              {data.is_active ? "● active" : "○ disabled"}
            </div>
          </div>
        )}

        <AlertRuleEditor ruleId={id} />
      </div>
    </>
  );
}
