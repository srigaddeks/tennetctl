"use client";

import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui";
import { AlertList } from "@/features/monitoring/_components/alert-list";

export default function AlertsPage() {
  return (
    <>
      <PageHeader
        title="Alerts"
        description="Active and recent alerts. Filter by state or severity. Silence to suppress notifications."
        testId="heading-monitoring-alerts"
        actions={
          <Link href="/monitoring/alerts/rules">
            <Button variant="secondary" data-testid="alerts-goto-rules">
              Manage rules
            </Button>
          </Link>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <AlertList />
      </div>
    </>
  );
}
