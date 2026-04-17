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
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <AlertRuleEditor ruleId={null} />
      </div>
    </>
  );
}
