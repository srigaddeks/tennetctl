/**
 * Flows list page.
 * Plan 44-01 implementation.
 */

import { Metadata } from "next";
import { FlowList } from "@/features/catalog/components/flow-list";

export const metadata: Metadata = {
  title: "Flows - Catalog",
};

export default function FlowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Flows</h1>
        <p className="mt-1 text-sm text-gray-600">
          Visualize and trace your workflow definitions
        </p>
      </div>

      <FlowList />
    </div>
  );
}
