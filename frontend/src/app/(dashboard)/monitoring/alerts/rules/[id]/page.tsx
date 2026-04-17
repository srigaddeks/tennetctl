"use client";

import { use } from "react";

import { PageHeader } from "@/components/page-header";
import { AlertRuleEditor } from "@/features/monitoring/_components/alert-rule-editor";

export default function EditAlertRulePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <>
      <PageHeader
        title="Edit alert rule"
        description="Update the DSL query, threshold, severity, or notification template."
        testId="heading-monitoring-alert-rule-edit"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <AlertRuleEditor ruleId={id} />
      </div>
    </>
  );
}
