"use client";

import { PageHeader } from "@/components/page-header";
import { AlertRuleEditor } from "@/features/monitoring/_components/alert-rule-editor";

export default function NewAlertRulePage() {
  return (
    <>
      <PageHeader
        title="New alert rule"
        description="Define a DSL query, threshold condition, severity, and notification template."
        testId="heading-monitoring-alert-rule-new"
        breadcrumbs={[
          { label: "Monitoring", href: "/monitoring" },
          { label: "Alerts", href: "/monitoring/alerts" },
          { label: "Rules", href: "/monitoring/alerts/rules" },
          { label: "New rule" },
        ]}
      />
      <div className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in">
        {/* Section header */}
        <div
          className="mb-5 rounded border px-4 py-3"
          style={{
            background: "var(--bg-surface)",
            borderColor: "var(--border)",
            borderLeft: "3px solid #9d6ef8",
          }}
        >
          <div
            className="text-[13px] font-semibold mb-0.5"
            style={{ color: "var(--text-primary)" }}
          >
            Alert rule configuration
          </div>
          <div
            className="text-[12px]"
            style={{ color: "var(--text-muted)" }}
          >
            Rules evaluate a Monitoring DSL query on a schedule. When the condition is met for the configured duration, an alert event fires and notifications are sent.
          </div>
        </div>

        <AlertRuleEditor ruleId={null} />
      </div>
    </>
  );
}
