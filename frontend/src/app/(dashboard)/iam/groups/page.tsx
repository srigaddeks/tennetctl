"use client";

import { OrgScopedResourcePage } from "@/components/org-scoped-resource-page";
import {
  useCreateGroup,
  useDeleteGroup,
  useGroup,
  useGroups,
  useUpdateGroup,
} from "@/features/iam-groups/hooks/use-groups";

export default function GroupsPage() {
  return (
    <OrgScopedResourcePage
      title="Groups"
      description="Org-scoped user collections for bulk role assignment."
      resourceNoun="group"
      pageTestId="heading-groups"
      testPrefix="group"
      hooks={{
        useList: useGroups,
        useOne: useGroup,
        useCreate: useCreateGroup,
        useUpdate: useUpdateGroup,
        useDelete: useDeleteGroup,
      }}
    />
  );
}
