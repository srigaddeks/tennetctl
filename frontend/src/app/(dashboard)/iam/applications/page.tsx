"use client";

import { OrgScopedResourcePage } from "@/components/org-scoped-resource-page";
import {
  useApplication,
  useApplications,
  useCreateApplication,
  useDeleteApplication,
  useUpdateApplication,
} from "@/features/iam-applications/hooks/use-applications";

export default function ApplicationsPage() {
  return (
    <OrgScopedResourcePage
      title="Applications"
      description="External products or services using the API with scoped credentials. Always org-scoped."
      resourceNoun="application"
      pageTestId="heading-applications"
      testPrefix="application"
      hooks={{
        useList: useApplications,
        useOne: useApplication,
        useCreate: useCreateApplication,
        useUpdate: useUpdateApplication,
        useDelete: useDeleteApplication,
      }}
    />
  );
}
